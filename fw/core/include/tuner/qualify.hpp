// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The PERMISSIVE qualification (§8B.4a-1). The mechanical-fault policy may be relaxed only after
//   at least 100 completed tunes across at least four bands, and
//   at least 50 hours of powered service, with
//   no mechanical fault (limit hit, encoder mismatch) in that time, and
//   the roller wheel and bus rod inspected and found clean, recorded at the box.
// A mechanical fault starts the count over. It is kept with the fault record (authoritative tier).
#pragma once
#include <cstdint>

namespace tuner {

struct Qualification {
    static constexpr uint32_t kTunes = 100, kHours = 50;
    static constexpr int kBands = 4;

    uint32_t tunes = 0;            // completed tunes this period
    uint16_t bands = 0;            // a bit per band (kBands order) with a completed tune
    uint32_t powered_s = 0;
    bool inspected = false;

    void tune_completed(int band);
    void powered(uint32_t seconds) { powered_s += seconds; }
    void mechanical_fault() { *this = Qualification{}; }
    void record_inspection() { inspected = true; }
    int band_count() const;
    double hours() const { return powered_s / 3600.0; }
    bool met() const;
};

}  // namespace tuner
