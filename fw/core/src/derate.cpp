// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/derate.hpp"

#include <cmath>

namespace tuner {

namespace {
bool on_160m(double mhz) { return mhz >= 1.800 && mhz <= 2.000; }
}  // namespace

double continuous_limit_w(double mhz) {
    if (!on_160m(mhz)) return 1500;
    return mhz <= 1.850 ? 502 : mhz <= 1.950 ? 600 : 882;
}

double loss_fraction(double mhz) { return on_160m(mhz) ? kCoolingW / continuous_limit_w(mhz) : 166.0 / 1500.0; }

bool Derate::update(double mhz, double fwd_w, bool through_network, double dt_s) {
    const double loss = through_network && fwd_w > 0 ? fwd_w * loss_fraction(mhz) : 0;
    if (through_network) limit_w_ = continuous_limit_w(mhz);
    // The loss is averaged rather than the power, so a hot bay stays hot across a band change.
    loss_w_ += (loss - loss_w_) * (1 - std::exp(-dt_s / tau_s_));
    const bool was = warn_;
    if (loss_w_ > kCoolingW) warn_ = true;
    else if (loss_w_ < 0.9 * kCoolingW) warn_ = false;
    return warn_ && !was;
}

}  // namespace tuner
