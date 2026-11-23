// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Intel HEX for the network update (§8C.8): records, the image they build, and the board check.
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "harness.hpp"
#include "tuner/hexfile.hpp"

using namespace tuner;

namespace {
constexpr uint32_t kBase = 0x60000000, kSize = 0x7C0000;

// A record line for type, address and data, with its checksum.
std::string line(uint8_t type, uint16_t addr, const std::vector<uint8_t>& data) {
    char buf[600];
    int n = std::snprintf(buf, sizeof buf, ":%02X%04X%02X", unsigned(data.size()), addr, type);
    uint8_t sum = uint8_t(data.size() + (addr >> 8) + (addr & 0xFF) + type);
    for (uint8_t b : data) {
        n += std::snprintf(buf + n, sizeof buf - n, "%02X", b);
        sum = uint8_t(sum + b);
    }
    std::snprintf(buf + n, sizeof buf - n, "%02X", uint8_t(-sum));
    return buf;
}

hex::Image::Step feed(hex::Image& im, const std::string& s, uint32_t& at) {
    hex::Record r;
    if (!hex::parse(s.c_str(), r)) return hex::Image::Step::Bad;
    return im.feed(r, at);
}
}  // namespace

TEST(hex_records_parse_and_check) {
    hex::Record r;
    CHECK(hex::parse(":0200000460009A", r) && r.type == 4 && r.len == 2 && r.data[0] == 0x60);
    CHECK(hex::parse(":100000004643464200000156000000000101020084", r) && r.type == 0 && r.len == 16 &&
          r.addr == 0 && r.data[0] == 0x46 && r.data[14] == 0x02 && r.data[15] == 0x00);
    CHECK(hex::parse(":00000001FF\r", r) && r.type == 1);
    CHECK(!hex::parse(":0200000460009B", r));                 // checksum
    CHECK(!hex::parse(":02000004600", r));                    // short
    CHECK(!hex::parse(":0200000460G09A", r));                 // not hex
    CHECK(!hex::parse("0200000460009A", r));                  // no colon
    CHECK(!hex::parse(":0300000460009A", r));                 // length disagrees with the line
}

TEST(hex_image_is_in_range_and_in_order) {
    hex::Image im(kBase, kSize);
    uint32_t at = 0;
    CHECK(feed(im, line(4, 0, {0x60, 0x00}), at) == hex::Image::Step::Skip);
    CHECK(feed(im, line(0, 0x0000, {1, 2, 3, 4}), at) == hex::Image::Step::Data && at == kBase);
    CHECK(feed(im, line(0, 0x1000, {5, 6}), at) == hex::Image::Step::Data && at == kBase + 0x1000);
    CHECK(im.extent() == 0x1002);
    CHECK(feed(im, line(5, 0, {0x60, 0, 0x10, 0}), at) == hex::Image::Step::Skip);
    CHECK(feed(im, line(1, 0, {}), at) == hex::Image::Step::Done && im.done());
    CHECK(feed(im, line(0, 0x2000, {7}), at) == hex::Image::Step::Bad);       // after the end

    hex::Image back(kBase, kSize);                    // going back over written flash
    feed(back, line(4, 0, {0x60, 0x00}), at);
    feed(back, line(0, 0x0100, {1, 2}), at);
    CHECK(feed(back, line(0, 0x00F0, {3}), at) == hex::Image::Step::Bad && std::string(back.why()) == "records out of order");

    hex::Image out(kBase, kSize);                     // below the flash, and past its end
    CHECK(feed(out, line(0, 0x0000, {1}), at) == hex::Image::Step::Bad);
    hex::Image past(kBase, kSize);
    feed(past, line(4, 0, {0x60, 0x7C}), at);
    CHECK(feed(past, line(0, 0x0000, {1}), at) == hex::Image::Step::Bad);
}

TEST(hex_crc_and_board_header) {
    CHECK(hex::crc32(0, "123456789", 9) == 0xCBF43926);
    const uint32_t part = hex::crc32(0, "12345", 5);
    CHECK(hex::crc32(part, "6789", 4) == 0xCBF43926);         // incremental

    std::vector<uint8_t> img(0x2000, 0xFF);
    auto put = [&](size_t at, uint32_t v) { std::memcpy(&img[at], &v, 4); };
    put(0, 0x42464346);
    put(0x50, 0x00800000);
    put(0x1000, 0x432000D1);
    CHECK(hex::teensy41_header(img.data(), img.size()));
    put(0x50, 0x00200000);                                    // a Teensy 4.0 image: 2 MB
    CHECK(!hex::teensy41_header(img.data(), img.size()));
    CHECK(!hex::teensy41_header(img.data(), 0x100));
}
