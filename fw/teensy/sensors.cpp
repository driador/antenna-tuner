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
constexpr uint8_t kIodirA = 0x00, kIodirB = 0x01, kIocon = 0x0A, kGpioA = 0x12;
constexpr uint8_t kIoconMirror = 0x40, kIoconOdr = 0x04;

bool iox_write(uint8_t reg, uint8_t value) {
    Wire.beginTransmission(pins::iox::ADDR);
    Wire.write(reg);
    Wire.write(value);
    return Wire.endTransmission() == 0;
}
}  // namespace

bool Sensors::begin() {
    analogReadResolution(12);
    analogReadAveraging(4);
    hot_ = tuner::Hysteresis(kOverTempC, kOverTempClearC);
    FreqCount.begin(kGateUs);
    Wire.begin();
    Wire.setClock(400000);
    // INTA mirrors both ports, open drain (10 k pull-up on the board). GPA7 and GPB7 are output-only on
    // current silicon, so they stay outputs; everything else is an input with its pull-up on the board.
    return iox_write(kIocon, kIoconMirror | kIoconOdr) && iox_write(kIodirA, 0x7F) && iox_write(kIodirB, 0x7F) &&
           read_iox();
}

void Sensors::poll(uint32_t now_ms) {
    if (now_ms != last_sample_ms_) {                       // the bridge, once a millisecond
        last_sample_ms_ = now_ms;
        sum_mag_ += analogRead(pins::V_MAG);
        sum_phs_ += analogRead(pins::V_PHS);
        sum_ref_ += analogRead(pins::AD_VREF);
        ++n_;
    }
    if (now_ms - last_therm_ms_ >= 100) {
        last_therm_ms_ = now_ms;
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
            const double v_mag = sum_mag_ / sum_ref_ * kAdVref, v_phs = sum_phs_ / sum_ref_ * kAdVref;
            gamma_ = tuner::gamma_from_ad8302(v_mag, v_phs);
            pending_.mhz = mhz_;
            pending_.gamma = gamma_;
            pending_start_ = now_ms - kGateUs / 1000;
            fresh_ = true;
        }
        sum_mag_ = sum_phs_ = sum_ref_ = 0;
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
    sum_mag_ = sum_phs_ = sum_ref_ = 0;
    n_ = 0;
    fresh_ = false;
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
