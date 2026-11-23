// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The fine recall memory (§8B.3c): bins, lookup within reach, replacing the oldest, and its stored image.
#include <cmath>
#include <vector>

#include "harness.hpp"
#include "tuner/recall.hpp"

using namespace tuner;

namespace {
constexpr double pF = 1e-12, uH = 1e-6;
const Setting kA{100 * pF, 4 * uH, 200 * pF};
const Setting kB{300 * pF, 9 * uH, 50 * pF};

bool same(const Setting& a, const Setting& b) {
    return std::fabs(a.c1 - b.c1) < 1e-15 && std::fabs(a.l - b.l) < 1e-12 && std::fabs(a.c2 - b.c2) < 1e-15;
}
}  // namespace

TEST(recall_bins_follow_frequency) {
    CHECK(Recall::bin_of(1.8) == 0);
    CHECK(Recall::bin_of(1.7) < 0 && Recall::bin_of(15.0) < 0);          // outside every band
    const int k = Recall::bin_of(14.1);
    const double center = 1.8 * std::pow(1 + kRecallStep, k);
    CHECK(Recall::bin_of(center * 1.001) == k && Recall::bin_of(center / 1.001) == k);   // within the bin
    CHECK(Recall::bin_of(center * (1 + kRecallStep)) == k + 1);                          // the next one
    CHECK(Recall::bin_of(29.7) > Recall::bin_of(28.0));
    int bins = 0;                                         // every bin of every band fits
    for (double f = 1.8; f < 30; f *= 1 + kRecallStep / 4)
        if (Recall::bin_of(f) >= 0 && Recall::bin_of(f) != Recall::bin_of(f / (1 + kRecallStep / 4))) ++bins;
    CHECK(bins + 1 <= kRecallMax);
}

TEST(recall_finds_within_reach) {
    Recall r;
    Setting s;
    CHECK(!r.find(14.0, s));
    r.store(14.0, kA, 1.1);
    CHECK(r.find(14.02, s) && same(s, kA));               // the same bin
    CHECK(r.find(14.06, s) && same(s, kA));               // two bins over
    CHECK(!r.find(14.12, s));                             // too far
    r.store(14.10, kB, 1.05);
    CHECK(r.find(14.09, s) && same(s, kB));               // the nearer of two
    r.store(14.0, kB, 1.0);                               // the same bin again replaces it
    CHECK(r.count() == 2 && r.find(14.0, s) && same(s, kB));
    CHECK(r.find(29.7, s) == false);
    r.store(29.7, kA, 1.2);                               // the top band edge is a bin like any other
    CHECK(r.find(29.69, s) && same(s, kA));
}

TEST(recall_replaces_the_oldest_when_full) {
    Recall r(8);                                          // a small memory, so 80 m's bins overfill it
    double f = 3.5;
    for (int i = 0; i < 12; ++i, f *= 1 + kRecallStep) r.store(f, i < 4 ? kA : kB, 1.1);
    Setting s;
    CHECK(r.count() == 8);
    CHECK(!r.find(3.5, s));                               // the oldest went first...
    CHECK(r.find(f / (1 + kRecallStep), s) && same(s, kB));   // ...and the newest stayed
}

TEST(recall_image_round_trips) {
    Recall r;
    r.store(1.85, kA, 1.15);
    r.store(7.15, kB, 1.05);
    std::vector<uint8_t> buf(Recall::image_size(kRecallMax));
    const size_t n = r.save(buf.data(), buf.size());
    CHECK(n == Recall::image_size(2));
    CHECK(r.save(buf.data(), n - 1) == 0);                // too small: nothing written
    Recall q;
    CHECK(q.load(buf.data(), n) && q.count() == 2 && q.changes() == r.changes());
    Setting s;
    CHECK(q.find(7.15, s) && same(s, kB));
    buf[20] ^= 0x40;                                      // one flipped bit: refused, and empty
    CHECK(!q.load(buf.data(), n) && q.count() == 0);
    CHECK(!q.load(buf.data(), 3));
}
