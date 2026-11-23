// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/recall.hpp"

#include <cmath>
#include <cstring>

#include "tuner/freq.hpp"

namespace tuner {

namespace {
constexpr double kBase = 1.8;             // MHz: bin 0
constexpr uint32_t kMagic = 0x314C4352;   // "RCL1"

uint32_t crc32(const uint8_t* p, size_t n) {
    uint32_t c = 0xFFFFFFFF;
    while (n--) {
        c ^= *p++;
        for (int k = 0; k < 8; ++k) c = (c >> 1) ^ (0xEDB88320 & (0 - (c & 1)));
    }
    return ~c;
}

template <typename T>
void put(uint8_t*& p, const T& v) {
    std::memcpy(p, &v, sizeof v);
    p += sizeof v;
}

template <typename T>
void get(const uint8_t*& p, T& v) {
    std::memcpy(&v, p, sizeof v);
    p += sizeof v;
}
}  // namespace

int Recall::bin_of(double mhz) {
    if (!band_of(mhz)) return -1;
    return int(std::lround(std::log(mhz / kBase) / std::log(1 + kRecallStep)));
}

bool Recall::find(double mhz, Setting& s) const {
    // The bands are 45 bins or more apart, so anything within reach is on mhz's band.
    const int b = bin_of(mhz);
    if (b < 0) return false;
    int best = -1, best_d = kRecallReach + 1;
    for (int i = 0; i < n_; ++i) {
        const int d = std::abs(int(e_[i].bin) - b);
        if (d < best_d) {
            best = i;
            best_d = d;
        }
    }
    if (best < 0) return false;
    s = Setting{e_[best].c1, e_[best].l, e_[best].c2};
    return true;
}

void Recall::store(double mhz, const Setting& s, double swr) {
    const int b = bin_of(mhz);
    if (b < 0) return;
    int slot = -1;
    for (int i = 0; i < n_ && slot < 0; ++i)
        if (e_[i].bin == b) slot = i;
    if (slot < 0 && n_ < cap_) slot = n_++;
    if (slot < 0) {                       // full: the oldest goes
        slot = 0;
        for (int i = 1; i < n_; ++i)
            if (e_[i].seq < e_[slot].seq) slot = i;
    }
    RecallEntry& e = e_[slot];
    e.bin = uint16_t(b);
    e.c1 = float(s.c1);
    e.l = float(s.l);
    e.c2 = float(s.c2);
    e.swr = float(swr);
    e.seq = ++seq_;
}

void Recall::clear() {
    n_ = 0;
    seq_ = 0;
}

size_t Recall::save(uint8_t* out, size_t cap) const {
    const size_t need = image_size(n_);
    if (cap < need) return 0;
    uint8_t* p = out;
    put(p, kMagic);
    put(p, uint32_t(n_));
    put(p, seq_);
    for (int i = 0; i < n_; ++i) {
        const RecallEntry& e = e_[i];
        put(p, e.bin);
        put(p, e.c1);
        put(p, e.l);
        put(p, e.c2);
        put(p, e.swr);
        put(p, e.seq);
    }
    put(p, crc32(out, size_t(p - out)));
    return need;
}

bool Recall::load(const uint8_t* in, size_t n) {
    clear();
    if (n < image_size(0)) return false;
    const uint8_t* p = in;
    uint32_t magic, count, seq;
    get(p, magic);
    get(p, count);
    get(p, seq);
    if (magic != kMagic || count > uint32_t(cap_) || n < image_size(int(count))) return false;
    uint32_t crc;
    std::memcpy(&crc, in + image_size(int(count)) - 4, 4);
    if (crc != crc32(in, image_size(int(count)) - 4)) return false;
    for (uint32_t i = 0; i < count; ++i) {
        RecallEntry& e = e_[i];
        get(p, e.bin);
        get(p, e.c1);
        get(p, e.l);
        get(p, e.c2);
        get(p, e.swr);
        get(p, e.seq);
    }
    n_ = int(count);
    seq_ = seq;
    return true;
}

}  // namespace tuner
