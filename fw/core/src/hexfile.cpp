// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/hexfile.hpp"

#include <cstring>

namespace tuner::hex {

namespace {
int nibble(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return -1;
}

bool byte_at(const char* s, uint8_t& out) {
    const int h = nibble(s[0]), l = h < 0 ? -1 : nibble(s[1]);
    if (l < 0) return false;
    out = uint8_t(h << 4 | l);
    return true;
}

uint32_t le32(const uint8_t* p) { return p[0] | uint32_t(p[1]) << 8 | uint32_t(p[2]) << 16 | uint32_t(p[3]) << 24; }
}  // namespace

bool parse(const char* line, Record& r) {
    if (!line || line[0] != ':') return false;
    size_t n = std::strlen(line);
    while (n && (line[n - 1] == '\r' || line[n - 1] == ' ')) --n;
    uint8_t len, ah, al, type;
    if (n < 11 || !byte_at(line + 1, len) || n != 11 + 2 * size_t(len)) return false;
    if (!byte_at(line + 3, ah) || !byte_at(line + 5, al) || !byte_at(line + 7, type)) return false;
    uint8_t sum = uint8_t(len + ah + al + type);
    for (int i = 0; i < len; ++i) {
        if (!byte_at(line + 9 + 2 * i, r.data[i])) return false;
        sum = uint8_t(sum + r.data[i]);
    }
    uint8_t check;
    if (!byte_at(line + 9 + 2 * len, check) || uint8_t(sum + check) != 0) return false;
    r.type = type;
    r.addr = uint16_t(ah << 8 | al);
    r.len = len;
    return true;
}

Image::Step Image::bad(const char* why) {
    why_ = why;
    failed_ = true;
    return Step::Bad;
}

Image::Step Image::feed(const Record& r, uint32_t& at) {
    if (failed_) return Step::Bad;
    if (done_) return bad("a record after the end of the file");
    switch (r.type) {
        case 0: {
            const uint32_t abs = upper_ + r.addr;
            if (abs < base_ || abs - base_ + r.len > size_) return bad("data outside the flash");
            if (abs - base_ < high_) return bad("records out of order");
            at = abs;
            high_ = abs - base_ + r.len;
            return r.len ? Step::Data : Step::Skip;
        }
        case 1:
            done_ = true;
            return Step::Done;
        case 2:                    // extended segment address: (value << 4)
            if (r.len != 2) return bad("a bad address record");
            upper_ = uint32_t(r.data[0] << 8 | r.data[1]) << 4;
            return Step::Skip;
        case 4:                    // extended linear address: the upper 16 bits
            if (r.len != 2) return bad("a bad address record");
            upper_ = uint32_t(r.data[0] << 8 | r.data[1]) << 16;
            return Step::Skip;
        case 3:
        case 5:                    // start address: the boot header has its own
            return Step::Skip;
        default:
            return bad("an unknown record type");
    }
}

uint32_t crc32(uint32_t crc, const void* p, size_t n) {
    const uint8_t* b = static_cast<const uint8_t*>(p);
    crc = ~crc;
    while (n--) {
        crc ^= *b++;
        for (int k = 0; k < 8; ++k) crc = (crc >> 1) ^ (0xEDB88320 & (0 - (crc & 1)));
    }
    return ~crc;
}

bool teensy41_header(const uint8_t* first, size_t n) {
    if (n < 0x1000 + 4) return false;
    return le32(first) == 0x42464346          // "FCFB": the FlexSPI configuration block
           && le32(first + 0x50) == 0x00800000   // sflashA1Size: the 4.1's 8 MB
           && le32(first + 0x1000) == 0x432000D1;   // the image vector table's header
}

}  // namespace tuner::hex
