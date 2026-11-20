// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "calib.hpp"

#include <cstdio>

#include "config.hpp"
#include "tuner/freq.hpp"

namespace hw {

namespace {
int band_index(double mhz) {
    const tuner::Band* b = tuner::band_of(mhz);
    return b ? int(b - tuner::kBands) : -1;
}
}  // namespace

uint8_t Calibration::have(double mhz) const { return band_index(mhz) == band_ ? have_ : 0; }

const char* Calibration::start(Step s, tuner::Path path, bool carrier, double mhz, double watts) {
    if (busy()) return "a calibration step is running";
    if (!carrier) return "key a steady carrier first";
    const int b = band_index(mhz);
    if (b < 0) return "not on an amateur band";
    if (s == Step::Load && path != tuner::Path::Cal) return "select the CAL path for the load";
    if ((s == Step::Open || s == Step::Short) && path != tuner::Path::Aux) return "select AUX, standard on the N jack";
    if (s == Step::Power && path == tuner::Path::Tune) return "power points need AUX or CAL";
    if (s == Step::Power && !(watts > 0 && watts <= kMaxCalWatts)) return "wattmeter reading, up to 2000 W";
    if (b != band_) {                  // a new band: its own session
        band_ = b;
        have_ = 0;
    }
    step_ = s;
    watts_ = watts;
    n_ = kCalGates;
    sum_ = tuner::Standard{};
    sum_fwd_ = 0;
    return nullptr;
}

const char* Calibration::gate(const tuner::Standard& raw, double v_fwd, double mhz, bool carrier) {
    if (!busy()) return nullptr;
    if (!carrier || band_index(mhz) != band_) {
        n_ = 0;
        return "step abandoned: carrier or band changed";
    }
    sum_.v_mag += raw.v_mag;
    sum_.v_phs += raw.v_phs;
    sum_fwd_ += v_fwd;
    if (--n_ > 0) return nullptr;
    const tuner::Standard avg{sum_.v_mag / kCalGates, sum_.v_phs / kCalGates};
    const char* name = tuner::kBands[band_].name;
    switch (step_) {
        case Step::Load:
            load_ = avg;
            have_ |= 1;
            break;
        case Step::Open:
            open_ = avg;
            have_ |= 2;
            break;
        case Step::Short:
            short_ = avg;
            have_ |= 4;
            break;
        case Step::Power: {
            tuner::Curve& c = auth_->power[band_];
            tuner::Curve trial = c;
            if (!trial.insert(sum_fwd_ / kCalGates, watts_) || trial.n > kPowerPoints) return "power curve full";
            if (trial.n >= 2 && !trial.valid()) return "point out of order: watts must rise with volts";
            c = trial;
            ++changes_;
            std::snprintf(msg_, sizeof msg_, "%s: %.0f W at %.3f V (%d points)", name, watts_, sum_fwd_ / kCalGates,
                          c.n);
            return msg_;
        }
    }
    std::snprintf(msg_, sizeof msg_, "%s: %s taken (V_MAG %.3f V_PHS %.3f)", name,
                  step_ == Step::Load ? "load" : step_ == Step::Open ? "open" : "short", avg.v_mag, avg.v_phs);
    return msg_;
}

const char* Calibration::save() {
    if (busy()) return "a calibration step is running";
    if (band_ < 0 || have_ != 7) return "take load, open and short on this band first";
    tuner::BridgeCal c;
    const tuner::CalError e = tuner::bridge_cal(open_, short_, load_, c);
    if (e != tuner::CalError::None) return tuner::cal_error_text(e);
    auth_->bridge[band_] = c;
    ++changes_;
    std::snprintf(msg_, sizeof msg_, "%s saved: floor %.1f dB", tuner::kBands[band_].name, c.floor_db);
    return msg_;
}

}  // namespace hw
