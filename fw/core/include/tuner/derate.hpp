// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The continuous power limit (§1.7.1). The cooling carries 200 W of loss in the RF bay; only the bottom of
// 160 m loses more than that at full power, and only on key-down: CW, RTTY, FT8 and tuning carriers. The
// limit is a warning and a logged event, never a PTT inhibit, because a 160 m contest sprint should be
// told, not cut off. The tank NTC's over-temperature fault (§8B.4) stays the hard stop.
#pragma once

namespace tuner {

constexpr double kCoolingW = 200;    // the RF bay's continuous dissipation budget (§1.7.1, §8)

// The continuous power limit at mhz: about 502 / 600 / 882 W in the 160 m segments 1.800-1.850, -1.950 and
// -2.000 MHz (a boundary takes the lower), 1500 W on every other band.
double continuous_limit_w(double mhz);
// The share of the forward power the RF bay dissipates at mhz, at the worst point of its segment: 200 W
// at each 160 m limit, and 166 W at 1500 W elsewhere (4.00 MHz, network and input choke).
double loss_fraction(double mhz);

class Derate {
public:
    // tau_s: how quickly the bay's temperature follows its loss (a first-order lag).
    explicit Derate(double tau_s) : tau_s_(tau_s) {}
    // Each tick: the forward power (W; below zero, an uncalibrated band, counts as none), whether it is
    // going through the network (a carrier on the TUNE path), and the seconds since the last call.
    // Returns true when the warning starts, for the event log. It clears below 90 % of the budget.
    bool update(double mhz, double fwd_w, bool through_network, double dt_s);
    double loss_w() const { return loss_w_; }      // the bay's loss, averaged as its temperature sees it
    double limit_w() const { return limit_w_; }    // the continuous limit where it last transmitted
    bool warning() const { return warn_; }

private:
    double tau_s_;
    double loss_w_ = 0, limit_w_ = 1500;
    bool warn_ = false;
};

}  // namespace tuner
