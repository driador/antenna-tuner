// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/qualify.hpp"

namespace tuner {

void Qualification::tune_completed(int band) {
    ++tunes;
    if (band >= 0 && band < 16) bands |= uint16_t(1u << band);
}

int Qualification::band_count() const {
    int n = 0;
    for (uint16_t b = bands; b; b &= uint16_t(b - 1)) ++n;
    return n;
}

bool Qualification::met() const {
    return tunes >= kTunes && band_count() >= kBands && powered_s >= kHours * 3600 && inspected;
}

}  // namespace tuner
