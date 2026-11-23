// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The fine recall memory (§8B.3c). Every converged setting is kept by frequency in bins of a quarter of a
// percent, so a retune near where the tuner has matched before starts from a setting proven there, not
// from the 1 % segment's prior. A recalled setting is only a starting point: the tune measures at it
// and goes on from there as from any move, so a stale entry costs one move.
//
// The bins run on a log scale from 1.8 MHz, so each is the same fraction of its frequency, and only
// inside the bands: 175 of them in all, so the memory holds every one. Should it ever fill (a finer
// step, more bands), a new bin replaces the oldest.
#pragma once
#include <cstddef>
#include <cstdint>

#include "tuner/tnet.hpp"

namespace tuner {

constexpr double kRecallStep = 0.0025;   // a bin is 0.25 % of frequency
constexpr int kRecallReach = 2;           // bins either side a recall may come from: within §8B.2's 0.5 %
constexpr int kRecallMax = 192;           // every bin of every band (175)

struct RecallEntry {
    uint16_t bin = 0;
    float c1 = 0, l = 0, c2 = 0;   // F, H
    float swr = 0;                 // at the match
    uint32_t seq = 0;              // the order stored, for replacing the oldest
};

class Recall {
public:
    explicit Recall(int capacity = kRecallMax) : cap_(capacity < kRecallMax ? capacity : kRecallMax) {}
    // The bin for mhz, or -1 outside every band.
    static int bin_of(double mhz);
    // The setting stored for mhz's bin, else the nearest within kRecallReach bins on the same band.
    bool find(double mhz, Setting& s) const;
    void store(double mhz, const Setting& s, double swr);
    void clear();
    int count() const { return n_; }
    uint32_t changes() const { return seq_; }   // grows with every store; persist when it moves
    const RecallEntry& at(int i) const { return e_[i]; }

    // A flat image for storage: "RCL1", the count and the entries, then a CRC-32. save() returns the
    // bytes written, 0 if cap is too small; load() leaves the memory empty and returns false if the
    // image is not whole.
    static constexpr size_t image_size(int n) { return 4 + 4 + 4 + size_t(n) * 22 + 4; }
    size_t save(uint8_t* out, size_t cap) const;
    bool load(const uint8_t* in, size_t n);

private:
    RecallEntry e_[kRecallMax];
    int cap_;
    int n_ = 0;
    uint32_t seq_ = 0;
};

}  // namespace tuner
