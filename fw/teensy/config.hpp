// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Hardware constants for the Teensy layer. ASSUMED marks a value the log has not fixed yet: a part
// still to choose, a count to make, or a curve to measure at commissioning (§9 items 30, 44, 48, 54).
// Everything else cites where it comes from.
#pragma once
#include <cstdint>

#include "tuner/curve.hpp"

namespace hw {

constexpr uint32_t kTickMs = 10;            // state machine tick
constexpr uint32_t kStepIsrHz = 50000;      // step generator: an axis can pulse at most every other tick
constexpr uint32_t kGateUs = 200000;        // FreqCount gate (§6A.10, §8B.0.1); microseconds on Teensy 4
constexpr uint32_t kWatchdogMs = 500;       // RTWDOG timeout (§7.4.1, §8B.0.3)
constexpr uint32_t kDriverWakeMs = 20;      // drivers enabled before the first step
constexpr uint32_t kSettleMs = 50;          // after the last step, before the encoders are read (§8B.3a)

// ---- motion (§7.1, §7.2, §8B.3a, §10.6) ----
// DM542T-class drivers: STEP/DIR/EN, one EN line for all three (§8B.0.4).
constexpr double kStepsPerTurn = 200 * 8;   // full steps x microsteps; ASSUMED 8 (the drivers' DIP switches)
constexpr bool kDriverEnableHigh = true;    // ASSUMED: the motor-chamber driver board is not drawn yet

struct Axis {
    const char* name;
    double full_turns;           // element travel, end to end
    double reduction;            // element turns per encoder turn: the sensing module's belt ratio (§7.1)
    int dir_sign;                // +1: DIR high moves toward the high end
    int enc_sign;                // +1: encoder counts rise toward the high end
    uint16_t enc_zero;           // encoder count at the low end, set at commissioning
    double soft_margin_turns;    // firmware stops this far short of each end (§7.2 layer 1)
    double v_max_rps, a_max_rps2;
    double slow_zone_turns, v_slow_rps;   // §7.2: the roller's slow zone near each end; 0 = none
    double verify_turns;         // encoder against steps after a move, beyond which it is a fault (§8B.3)
};

// Capacitor turns are ASSUMED ~30 until counted (§9 item 48); 32:1 and 25:1 are the §10.6 reductions.
// 7.5 rev/s is the 1.5 kHz full-step choice of §8B.3a; the capacitors ramp in 0.25 s, the roller's
// ~30 lb·in² rotor in about 1 s (§8B.3a). Directions and zeros are set at commissioning.
inline constexpr Axis kAxes[3] = {
    {"C1", 30, 32, +1, +1, 0, 0.5, 7.5, 30, 0, 0, 0.05},
    {"C2", 30, 32, +1, +1, 0, 0.5, 7.5, 30, 0, 0, 0.05},
    {"L", 22, 25, +1, +1, 0, 0.5, 7.5, 7.5, 3, 2, 0.05},
};

// Value against turns from the low end. C1 is ASSUMED to be the UCSX-700-15S (25-700 pF); the
// CVDD-500-15S is the alternative (§10.1). All three are models until measured (§9 item 54).
inline tuner::Curve axis_curve(int axis) {
    switch (axis) {
        case 0: return tuner::c1_model(kAxes[0].full_turns);
        case 1: return tuner::c2_model(kAxes[1].full_turns);
        default: return tuner::roller_model();
    }
}

// LIM1-LIM6 (§8B.0.4) as low and high end of C1, C2, roller. ASSUMED: the driver board is not drawn.
inline constexpr uint8_t kLimitAxis[6] = {0, 0, 1, 1, 2, 2};

// ---- the 160 m derate (§1.7.1) ----
constexpr double kDerateTauS = 120;         // ASSUMED: how quickly the RF bay's temperature follows its loss;
                                            // the §9 item 30 thermal run measures it

// ---- measurement (§6A.5, §6A.6, §6A.8) ----
constexpr double kAdVref = 1.80;            // AD8302 VREF; V_MAG and V_PHS are read against it
constexpr int kCalGates = 5;                // gates averaged for each calibration standard or power point
constexpr int kPowerPoints = 8;             // wattmeter points kept per band
constexpr double kMaxCalWatts = 2000;       // a reading above this is a typo: the tuner is rated 1500 W

// ---- RF path (§5.5, §6B) ----
constexpr double kCoilOnVolts = 0.03;       // ASSUMED: across the 1 ohm sense, a CX600N-24 coil draws more
constexpr double kFwdRfVolts = 0.05;        // ASSUMED: V_FWD in any 1 ms sample above this is RF at the tuner;
                                            // the Schottky detector idles near 0 V. Set from its idle and a few watts
constexpr double kLoadRfVolts = 0.70;       // ASSUMED: CAL_ADC (the detector halved) with ~5 W in the load;
                                            // it idles near 0.5 V (§6B.3a: 1.03 V bias)

// ---- built-in test (§8B.4h) ----
constexpr bool kBitAtPowerUp = true;        // the active run once the boot has settled; off, it runs on demand only
constexpr uint32_t kBitSettleMs = 3000;     // after setup, so the detectors have been read at rest for a few gates
constexpr uint32_t kBitRfQuietMs = 500;     // no RF for this long first: the last gate's averages hold none

// ---- audible alarm (§8B.4i) ----
constexpr bool kSounder = true;             // the sounder at the box; false leaves the page's tone alone

// ---- data link (§8C.5) ----
constexpr uint16_t kLinePort = 4600;        // the line protocol for nc and scripts; the page is on 80
constexpr uint16_t kNtpLocalPort = 4123;

// ---- local panel (§7.5) ----
constexpr uint32_t kNextionBaud = 115200;   // set the same in the HMI's program.s (fw/README.md)
constexpr uint32_t kPanelMs = 100;          // screen refresh
constexpr int kEdgesPerDetent = 4;          // ASSUMED: the 62V15 gives one quadrature cycle per detent
constexpr double kJogTurns = 0.05;          // element turns per detent on the jog screen

// ---- thermal (§8, §8B.4a) ----
constexpr double kNtcBeta = 3950;           // ASSUMED: any 10 k NTC; the part is not chosen
constexpr double kOverTempC = 65;           // ASSUMED: set by the §9 item 30 thermal check
constexpr double kOverTempClearC = 55;
constexpr uint32_t kBlowerPwmHz = 25;       // ASSUMED: a 3-wire fan switched on its supply wants a slow PWM
constexpr double kBlowerMinDuty = 0.4;      // ASSUMED: below kBlowerRampC
constexpr double kBlowerRampC = 35, kBlowerFullC = 55;

}  // namespace hw
