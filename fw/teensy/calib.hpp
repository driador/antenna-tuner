// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The calibration procedure (§6A.8), one band at a time, from the console or the panel:
//   load    CAL path, a low-power carrier into the internal 50 ohm load
//   open    AUX path, an open on the rear N connector, carrier
//   short   AUX path, a short there, carrier
//   save    computes the band's bridge calibration from the three
//   watts W AUX or CAL, a carrier at W watts as a wattmeter reads it: one point of the band's
//           forward-power curve, which is stored at once
// Each step averages kCalGates gates. Changing band starts the band's session over.
#pragma once
#include <cstdint>

#include "persist.hpp"
#include "tuner/cal.hpp"
#include "tuner/path.hpp"

namespace hw {

class Calibration {
public:
    enum class Step : uint8_t { Load, Open, Short, Power };

    void attach(Authoritative* a) { auth_ = a; }
    // Starts a step on the band being transmitted on. Returns nullptr, or why it cannot start.
    const char* start(Step s, tuner::Path path, bool carrier, double mhz, double watts = 0);
    // One finished gate. Returns a message when a step completes or fails, else nullptr.
    const char* gate(const tuner::Standard& raw, double v_fwd, double mhz, bool carrier);
    const char* save();                // what to show: the band saved, or why the standards will not do
    bool busy() const { return n_ > 0; }
    uint32_t changes() const { return changes_; }   // counts saves and power points: each is backed up
    uint8_t have(double mhz) const;    // standards taken on this band: 1 load, 2 open, 4 short

private:
    Authoritative* auth_ = nullptr;
    int band_ = -1;
    uint8_t have_ = 0;
    tuner::Standard load_, open_, short_;
    Step step_ = Step::Load;
    double watts_ = 0;
    int n_ = 0;                        // gates still to take
    uint32_t changes_ = 0;
    tuner::Standard sum_;
    double sum_fwd_ = 0;
    char msg_[48] = {};
};

}  // namespace hw
