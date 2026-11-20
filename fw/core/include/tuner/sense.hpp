// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Small conditioning steps between the Teensy's inputs and the state machine: the steady-carrier test on
// the frequency counter (§6A.10), the tank thermistor (§8B.0.4) and the hysteresis the over-temperature
// fault clears on (§8B.4a).
#pragma once

namespace tuner {

// A carrier is present when n successive counter gates fall in range and agree within agree_mhz. SSB
// speech and noise never hold still that long, so a tune waits for a key-down carrier (§8B.2). One
// count of the /1024 over a 200 ms gate is 5.12 kHz, so 0.011 MHz allows two.
class CarrierDetector {
public:
    struct Config {
        double min_mhz = 1.7, max_mhz = 30.0;
        double agree_mhz = 0.011;
        int gates = 2;
    };
    CarrierDetector() = default;
    explicit CarrierDetector(const Config& c) : cfg_(c) {}

    bool update(double mhz);   // one gate; returns present()
    bool present() const { return run_ >= cfg_.gates; }
    void reset() { run_ = 0; }

private:
    Config cfg_;
    double last_ = 0;
    int run_ = 0;
};

// The tank NTC: 10 k at 25 °C to chassis, biased by r_bias from the same rail the ADC measures against.
// Returns NaN for an open or shorted sensor, which the caller treats as over-temperature, so a broken
// lead fails toward inhibit like every other input (§7.4).
struct Ntc {
    double r25 = 10e3, beta = 3950, r_bias = 10e3;
};
double ntc_celsius(double ratio, const Ntc& n = {});   // ratio = V / V_rail

class Hysteresis {
public:
    Hysteresis(double on, double off) : on_(on), off_(off) {}
    bool update(double v);
    bool state() const { return state_; }

private:
    double on_, off_;
    bool state_ = false;
};

}  // namespace tuner
