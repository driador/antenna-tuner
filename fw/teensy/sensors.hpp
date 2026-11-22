// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The measured inputs (§6A.4-§6A.10, §6B, §8): the AD8302 bridge and the forward detector averaged over
// each frequency-counter gate, the frequency and the steady-carrier test, the MCP23017 (panel encoders,
// bypass key, every term of the permissive), the relay coil currents, the cal-load detector and the
// tank thermistor.
#pragma once
#include <cstdint>

#include "config.hpp"
#include "persist.hpp"
#include "tuner/bit.hpp"
#include "tuner/cal.hpp"
#include "tuner/fsm.hpp"
#include "tuner/sense.hpp"

namespace hw {

class Sensors {
public:
    bool begin();                     // the counter, the ADC and the MCP23017; false if it does not answer
    void use_calibration(const Authoritative* a) { cal_ = a; }
    void poll(uint32_t now_ms);       // every loop: bridge samples, slow inputs, finished gates

    // A gate finished since the last call: its frequency, and the bridge averaged over it through the
    // band's calibration. start_ms is when it began, so the caller can refuse one that overlaps a move.
    bool take_gate(tuner::Measurement& m, uint32_t& start_ms);
    void restart_bridge();            // drop the samples so far: a move started or ended
    bool carrier() const { return carrier_.present(); }
    double mhz() const { return mhz_; }
    const tuner::GammaReading& gamma() const { return gamma_; }   // the last gate's, calibrated
    const tuner::Standard& standard() const { return raw_; }     // ...and as raw volts, for calibration
    double v_fwd() const { return v_fwd_; }                      // the forward detector over that gate
    bool rf_now() const { return fwd_now_ > kFwdRfVolts; }       // ...and RF in its latest 1 ms sample
    double forward_watts() const;                                // below zero: this band is not calibrated

    bool read_iox();                  // false if it did not answer
    bool iox(uint8_t bit) const { return iox_ & (1u << bit); }
    uint16_t iox_word() const { return iox_; }
    void set_sounder(bool on);        // the alarm's sounder on GPA7 (§8B.4i); written only when it changes

    bool k1_on() const { return k1_v_ > kCoilOnVolts; }    // coil current sensed (§6B.2)
    bool k2_on() const { return k2_v_ > kCoilOnVolts; }
    bool load_rf() const { return cal_v_ > kLoadRfVolts; } // the cal-load detector sees RF (§6B.3a)
    double tank_c() const { return tank_c_; }         // NaN: open or shorted thermistor
    bool over_temp() const { return over_temp_; }     // a failed sensor counts as hot
    double vref() const { return vref_; }             // AD_VREF on the Teensy's 3.3 V scale
    // The detectors as the built-in test judges them at rest (§8B.4h): the bridge and the forward
    // detector over the last gate, the cal-load detector and the tank as last read.
    tuner::bit::Rest rest() const { return {raw_.v_mag, raw_.v_phs, v_fwd_, cal_v_, tank_c_}; }

private:
    const Authoritative* cal_ = nullptr;
    tuner::CarrierDetector carrier_;
    tuner::Hysteresis hot_{0, 0};
    uint32_t last_sample_ms_ = 0, last_slow_ms_ = 0;
    double sum_mag_ = 0, sum_phs_ = 0, sum_ref_ = 0, sum_fwd_ = 0;
    uint32_t n_ = 0;
    bool fresh_ = false;
    tuner::Measurement pending_;
    uint32_t pending_start_ = 0;
    double mhz_ = 0, tank_c_ = 0, vref_ = 0, v_fwd_ = 0, fwd_now_ = 0;
    double k1_v_ = 0, k2_v_ = 0, cal_v_ = 0;
    tuner::GammaReading gamma_;
    tuner::Standard raw_;
    uint16_t iox_ = 0;
    bool over_temp_ = true;
    bool sounder_ = false;
};

}  // namespace hw
