#include "tuner/sense.hpp"

#include <cmath>

namespace tuner {

bool CarrierDetector::update(double mhz) {
    if (!(mhz >= cfg_.min_mhz && mhz <= cfg_.max_mhz)) run_ = 0;
    else if (run_ > 0 && std::fabs(mhz - last_) <= cfg_.agree_mhz) run_ = run_ < cfg_.gates ? run_ + 1 : run_;
    else run_ = 1;
    last_ = mhz;
    return present();
}

double ntc_celsius(double ratio, const Ntc& n) {
    if (!(ratio > 0.01 && ratio < 0.99)) return NAN;
    const double r = n.r_bias * ratio / (1 - ratio);
    return 1 / (1 / 298.15 + std::log(r / n.r25) / n.beta) - 273.15;
}

bool Hysteresis::update(double v) {
    if (v >= on_) state_ = true;
    else if (v <= off_) state_ = false;
    return state_;
}

}  // namespace tuner
