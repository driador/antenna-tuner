// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The built-in test (§8B.4h), built from the failure-mode table of §8B.4g. The passive checks need only
// readings. The active check is a sequencer the Teensy layer steps every tick: it asks for jogs and path
// changes through the same routes as an operator, so the state machine and the path switch keep their
// own rules and grade what they find, and it drives K1 directly only for the hold-latch check.
#pragma once
#include <cstddef>
#include <cstdint>

#include "tuner/faults.hpp"
#include "tuner/path.hpp"

namespace tuner::bit {

enum class Check : uint8_t {
    Expander, Encoders, BridgeRef, Limits, PermitStuck, Record,   // passive: the original §8B.4b step 2
    BridgeIdle, FwdIdle, CalIdle, Thermistor,                      // passive: the detectors at rest
    AxisC1, AxisC2, AxisL, RelayK1, RelayK2, Latch, PermitRise,    // active
    Count
};
// C latches SELF-TEST FAILURE; B raises BUILT-IN TEST; Mechanical is graded by the policy, as the encoder
// mismatch it raises (§8B.4a-1); the relay checks raise RELAY MISMATCH, also B; Warn inhibits nothing.
enum class Grade : uint8_t { C, B, Mechanical, Warn };
Grade grade(Check c);
const char* name(Check c);
constexpr uint32_t mask(Check c) { return 1u << unsigned(c); }
// The fault a failed check stands behind, for naming it beside that fault: SELF-TEST FAILURE, BUILT-IN
// TEST, ENCODER MISMATCH (an axis) or RELAY MISMATCH. Fault::Count for the warnings.
Fault fault_of(Check c);
// The checks in `failed` behind fault f. An axis check fails on an encoder mismatch or a limit hit, so it
// is behind either.
uint32_t behind(uint32_t failed, Fault f);
// The names of the checks in m, joined with ", " and cut to fit; returns how many characters it wrote.
size_t names(uint32_t m, char out[], size_t cap);

// The term holding the permit down while the vote is given (§7.4): the first of the MCP23017's GPB
// inputs that reads low, else the gate after them. nullptr if every term reads high.
const char* permit_blocker(uint16_t iox_word);

// The detectors with no RF. The windows are ASSUMED until bring-up reads the real idle levels.
struct Rest {
    double v_mag = 0, v_phs = 0;   // the AD8302's outputs, against its VREF
    double v_fwd = 0, v_cal = 0;   // the forward and cal-load detectors
    double tank_c = 0;             // NaN: open or shorted, already an over-temperature
};
struct Windows {
    double mag_lo = 0.2, mag_hi = 1.6;   // away from both rails
    double phs_lo = 0.05, phs_hi = 1.75;
    double fwd_max = 0.05;               // the forward detector's RF threshold
    double cal_lo = 0.3, cal_hi = 0.65;  // the cal-load detector idles near 0.5 V on its bias
    double tank_lo = -20, tank_hi = 60;  // °C
};
uint32_t rest_checks(const Rest& r, const Windows& w = {});   // the failed bits, BridgeIdle to Thermistor

class Active {
public:
    struct In {
        uint32_t now_ms = 0;
        bool safe = false;          // no carrier or RF, the bypass off, the RF service panel closed
        bool clear = false;         // nothing latched or awaiting ACK: needed to start
        bool quiet = false;         // IDLE, nothing moving, no path change under way
        double turns[3] = {};       // C1, C2, L: from each axis's low end, in its own turns
        double travel[3] = {};      // ...and each axis's travel, end to end
        bool axis_fault = false;    // an encoder mismatch or a limit hit was raised since the run began
        bool relay_fault = false;   // a relay mismatch was raised since the run began
        Path path = Path::Tune;     // as confirmed by the path switch
        bool k1_current = false;    // K1's coil draws
        bool vote = false;          // the MCU's vote is up (the policy may withhold it)
        bool permit = false;        // the permit reads high
        Rest rest;                  // the detectors now: judged once, as the run starts
    };
    struct Out {
        int jog_axis = -1;          // a jog this tick: which axis...
        double jog_turns = 0;       // ...and how far, in that axis's turns
        bool path_request = false;  // a path change this tick
        Path path = Path::Tune;
        bool drive_k1 = false;      // drive K1 past the path switch: with the permit up, the latch holds it
    };
    static constexpr double kTurns = 1.0;            // each axis's move, out and back
    static constexpr uint32_t kStartMs = 10000;      // a run that cannot start in this long does not
    static constexpr uint32_t kGraceMs = 500;        // a request that starts nothing in this long was refused
    static constexpr uint32_t kLatchMs = 50;         // K1 driven this long; also the permit's wait, and the let-go

    void start(uint32_t now_ms, const Windows& w = {});
    Out step(const In& in);
    bool running() const { return phase_ != Phase::Idle; }
    bool completed() const { return completed_; }    // the last run went to the end
    uint32_t failed() const { return failed_; }
    uint32_t untested() const { return untested_; }  // checks it could not judge: no vote, no latch test

private:
    enum class Phase : uint8_t { Idle, Wait, Axis, Relay, Latch, LatchOff, Restore };
    void end(bool completed);
    void stop(const In& in);

    Phase phase_ = Phase::Idle;
    Windows windows_;
    int axis_ = 0, leg_ = 0, relay_ = 0, dir_ = +1;
    bool issued_ = false, busy_seen_ = false, completed_ = false, driving_ = false;
    uint32_t t0_ = 0, failed_ = 0, untested_ = 0;
};

}  // namespace tuner::bit
