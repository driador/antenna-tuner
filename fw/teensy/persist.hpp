// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// What survives a power cycle (§8B.4b, §8B.5.2), in the Teensy's flash-backed EEPROM, as two records
// with their own CRCs so that a profile update can never touch the calibration:
//   authoritative  the tuner's identity, the fault record and policy mode, the PERMISSIVE qualification,
//                  the network settings and the calibration. Kept twice and written to the older copy
//                  with a sequence number, so power lost mid-write leaves the other good.
//   convenience    the priors (the internal copy of the tuning profiles) and where the elements were,
//                  so boot can say whether someone moved them (§8B.4b step 4).
// Both are stored field by field with no padding: an unchanged state compares equal and writes nothing,
// and a changed one rewrites only the bytes that differ.
#pragma once

#include "tuner/cal.hpp"
#include "tuner/curve.hpp"
#include "tuner/faults.hpp"
#include "tuner/freq.hpp"
#include "tuner/fsm.hpp"
#include "tuner/mirror.hpp"
#include "tuner/qualify.hpp"

namespace hw {

struct Authoritative {
    uint64_t tuner_id = 0;
    tuner::FaultRecord faults;
    tuner::Qualification qual;
    tuner::NetConfig net;
    tuner::BridgeCal bridge[tuner::kBandCount];
    tuner::Curve power[tuner::kBandCount];   // forward detector volts to watts, at most kPowerPoints
};

struct Convenience {
    float last_turns[3] = {};
    bool prior_ok[tuner::kSegments] = {};
    tuner::Prior priors[tuner::kSegments] = {};
};

// Blank: never written (a new board). Corrupt: written, but neither copy checks out, which §8B.5.4b
// treats as a fault rather than something to restore over.
enum class Loaded : uint8_t { Ok, Blank, Corrupt };
Loaded load(Authoritative& a);
bool load(Convenience& c);
void save(const Authoritative& a);
bool save(const Convenience& c);   // true when it changed (the profiles moved on)

}  // namespace hw
