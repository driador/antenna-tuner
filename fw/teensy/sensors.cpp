// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "sensors.hpp"

#include <Arduino.h>
#include <FreqCount.h>
#include <Wire.h>

#include <cmath>

#include "config.hpp"
#include "tuner/bridge.hpp"
#include "tuner/freq.hpp"
#include "tuner/pins.hpp"

namespace pins = tuner::pins;

namespace hw {

namespace {
// MCP23017, IOCON.BANK = 0
constexpr uint8_t kIodirA = 0x00, kIodirB = 0x01, kGpintenA = 0x04, kIocon = 0x0A, kGpioA = 0x12, kOlatA = 0x14;
constexpr uint8_t kGpa7 = 0x80;       // the sounder
constexpr uint8_t kIoconMirror = 0x40, kIoconOdr = 0x04;

bool iox_write(uint8_t reg, uint8_t value) {
    Wire.beginTransmission(pins::iox::ADDR);
    Wire.write(reg);
    Wire.write(value);
    return Wire.endTransmission() == 0;
}

double volts(uint8_t pin) { return analogRead(pin) * 3.3 / 4095; }
}  // namespace

bool Sensors::begin() {
    analogReadResolution(12);
    analogReadAveraging(4);
    hot_ = tuner::Hysteresis(kOverTempC, kOverTempClearC);
    FreqCount.begin(kGateUs);
    Wire.begin();
    Wire.setClock(400000);
    // INTA mirrors both ports, open drain (10 k pull-up on the board), and fires on any change of the
    // panel encoders' lines. GPA7 and GPB7 are output-only on current silicon, so they stay outputs:
    // GPA7 drives the sounder, off from the start (a watchdog reset leaves the expander as it was), and
    // GPB7 is unused. Everything else is an input with its pull-up on the board.
    return iox_write(kIocon, kIoconMirror | kIoconOdr) && iox_write(kOlatA, 0) && iox_write(kIodirA, 0x7F) &&
           iox_write(kIodirB, 0x7F) && iox_write(kGpintenA, 0x3F) && read_iox();
}

double Sensors::forward_watts() const {
    const tuner::Band* b = tuner::band_of(mhz_);
    if (!cal_ || !b) return -1;
    const tuner::Curve& c = cal_->power[b - tuner::kBands];
    return c.valid() ? c.at(v_fwd_) : -1;
}

void Sensors::poll(uint32_t now_ms) {
    if (now_ms != last_sample_ms_) {                       // the bridge and forward detector, each millisecond
        last_sample_ms_ = now_ms;
        sum_mag_ += analogRead(pins::V_MAG);
        sum_phs_ += analogRead(pins::V_PHS);
        sum_ref_ += analogRead(pins::AD_VREF);
        const int fwd = analogRead(pins::V_FWD);
        sum_fwd_ += fwd;
        fwd_now_ = fwd * 3.3 / 4095;
        ++n_;
    }
    if (now_ms - last_slow_ms_ >= 10) {
        last_slow_ms_ = now_ms;
        k1_v_ = volts(pins::K_I[0]);
        k2_v_ = volts(pins::K_I[1]);
        cal_v_ = volts(pins::CAL_ADC);
        tank_c_ = tuner::ntc_celsius(analogRead(pins::THERM) / 4095.0, tuner::Ntc{10e3, kNtcBeta, 10e3});
        over_temp_ = std::isnan(tank_c_) || hot_.update(tank_c_);
    }
    if (FreqCount.available()) {
        const uint32_t count = FreqCount.read();
        mhz_ = tuner::mhz_from_count(count, kGateUs * 1e-6);
        carrier_.update(mhz_);
        if (n_ > 0 && sum_ref_ > 0) {
            // V_MAG and V_PHS against the AD8302's own VREF, which also corrects the 3.3 V scale.
            vref_ = sum_ref_ / n_ * 3.3 / 4095;
            raw_.v_mag = sum_mag_ / sum_ref_ * kAdVref;
            raw_.v_phs = sum_phs_ / sum_ref_ * kAdVref;
            v_fwd_ = sum_fwd_ / n_ * 3.3 / 4095;
            const tuner::Band* b = tuner::band_of(mhz_);
            const tuner::BridgeCal* bc = cal_ && b ? &cal_->bridge[b - tuner::kBands] : nullptr;
            gamma_ = bc && bc->valid ? tuner::calibrated(*bc, raw_.v_mag, raw_.v_phs)
                                     : tuner::gamma_from_ad8302(raw_.v_mag, raw_.v_phs);
            pending_.mhz = mhz_;
            pending_.gamma = gamma_;
            pending_start_ = now_ms - kGateUs / 1000;
            fresh_ = true;
        }
        sum_mag_ = sum_phs_ = sum_ref_ = sum_fwd_ = 0;
        n_ = 0;
    }
}

bool Sensors::take_gate(tuner::Measurement& m, uint32_t& start_ms) {
    if (!fresh_) return false;
    fresh_ = false;
    m = pending_;
    start_ms = pending_start_;
    return true;
}

void Sensors::restart_bridge() {
    sum_mag_ = sum_phs_ = sum_ref_ = sum_fwd_ = 0;
    n_ = 0;
    fresh_ = false;
}

void Sensors::set_sounder(bool on) {
    if (on != sounder_ && iox_write(kOlatA, on ? kGpa7 : 0)) sounder_ = on;   // a failed write tries again
}

bool Sensors::read_iox() {
    Wire.beginTransmission(pins::iox::ADDR);
    Wire.write(kGpioA);
    if (Wire.endTransmission(false) != 0 || Wire.requestFrom(int(pins::iox::ADDR), 2) != 2) return false;
    const uint8_t a = Wire.read(), b = Wire.read();
    iox_ = uint16_t(a | (b << 8));
    return true;
}

}  // namespace hw
