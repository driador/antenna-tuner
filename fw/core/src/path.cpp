// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/path.hpp"

namespace tuner {

const char* path_name(Path p) {
    switch (p) {
        case Path::Tune: return "TUNE";
        case Path::Aux: return "AUX";
        case Path::Cal: return "CAL";
    }
    return "?";
}

bool PathSwitch::request(Path p, uint32_t now_ms) {
    if (busy()) return false;
    if (p == path_) return true;
    target_ = p;
    phase_ = Phase::Blanking;
    t0_ = now_ms;
    return true;
}

PathSwitch::Out PathSwitch::step(const In& in) {
    Out o;
    switch (phase_) {
        case Phase::Steady: {
            o.k1 = k1_for(path_);
            o.k2 = k2_for(path_);
            // A coil that stops drawing (or starts) on its own is reported once, as it happens.
            const bool ok = in.k1_current == o.k1 && in.k2_current == o.k2;
            if (!ok && coils_ok_) o.mismatch = true;
            coils_ok_ = ok;
            if (rf_check_ && in.carrier) {
                rf_check_ = false;
                if (in.load_rf != (path_ == Path::Cal)) o.mismatch = true;
            }
            break;
        }
        case Phase::Blanking:                     // the old relay state, vote down, waiting
            o.k1 = k1_for(path_);
            o.k2 = k2_for(path_);
            if (in.carrier || in.rf_now) {           // keyed before the relays moved: drop the change
                phase_ = Phase::Steady;
                o.canceled = true;
                break;
            }
            o.hold_vote = true;
            if (in.now_ms - t0_ >= cfg_.blank_ms) {
                phase_ = Phase::Settling;
                t0_ = in.now_ms;
                o.k1 = k1_for(target_);
                o.k2 = k2_for(target_);
            }
            break;
        case Phase::Settling:
            o.hold_vote = true;
            o.k1 = k1_for(target_);
            o.k2 = k2_for(target_);
            if (in.now_ms - t0_ < cfg_.settle_ms) break;
            phase_ = Phase::Steady;
            if (in.k1_current == o.k1 && in.k2_current == o.k2) {
                path_ = target_;
                rf_check_ = true;
                coils_ok_ = true;
            } else {
                o.mismatch = true;                // back to the de-energized state
                path_ = Path::Tune;
                o.k1 = o.k2 = false;
                coils_ok_ = false;
                // The vote stays held this tick: the relays were just commanded back.
            }
            break;
    }
    return o;
}

}  // namespace tuner
