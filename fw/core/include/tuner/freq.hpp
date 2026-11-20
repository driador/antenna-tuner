// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Operating frequency from the /1024 prescaler (§6A.10, §8B.0.1) and the tune-initiation window (§8B.2).
#pragma once
#include <cstdint>

namespace tuner {

struct Band {
    const char* name;
    double lo_mhz, hi_mhz;      // US amateur allocations, as the NEC band-edge model (§1)
};

constexpr int kBandCount = 10;
extern const Band kBands[kBandCount];

// FreqCount's gate count of the /1024 output -> MHz. 200 ms gives 5.1 kHz resolution.
inline double mhz_from_count(uint32_t count, double gate_s, uint32_t divider = 1024) {
    return count * double(divider) / gate_s / 1e6;
}

const Band* band_of(double mhz);    // nullptr outside every band

// Profile segments: each band cut into steps of 1 % of its lower edge, so a stored setting is never
// used more than about 1 % of frequency from where it was found (§7.6, §8B.5). 50 in all.
constexpr int kSegments = 50;
int segment_of(double mhz);         // -1 outside every band
int band_of_segment(int seg);       // index into kBands
double segment_center(int seg);     // MHz

// §8B.2: a solution stays valid while the frequency is within +/-frac of where it was solved and on
// the same band, whichever is tighter.
bool solution_valid(double solved_mhz, double now_mhz, double frac = 0.005);

}  // namespace tuner
