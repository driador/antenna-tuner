// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/alarm.hpp"

namespace tuner {

bool Alarm::step(const In& in) {
    // Forget what has cleared, so that it sounds again if it comes back.
    quiet_c_ &= in.latched_c;
    quiet_b_ &= in.unacked_b;
    quiet_hot_ = quiet_hot_ && in.over_temp;
    quiet_derate_ = quiet_derate_ && in.derate;
    if (in.silence) {
        quiet_c_ = in.latched_c;
        quiet_b_ = in.unacked_b;
        quiet_hot_ = in.over_temp;
        quiet_derate_ = in.derate;
    }
    const AlarmLevel l = in.latched_c & ~quiet_c_                                      ? AlarmLevel::Fast
                         : in.unacked_b & ~quiet_b_                                    ? AlarmLevel::Slow
                         : (in.over_temp && !quiet_hot_) || (in.derate && !quiet_derate_) ? AlarmLevel::Chirp
                                                                                        : AlarmLevel::None;
    if (l != level_) {
        level_ = l;
        since_ = in.now_ms;
    }
    const uint32_t t = in.now_ms - since_;
    switch (level_) {
        case AlarmLevel::Fast: return t % kFastPeriodMs < kFastOnMs;
        case AlarmLevel::Slow: return t % kSlowPeriodMs < kSlowOnMs;
        case AlarmLevel::Chirp: return t % kChirpPeriodMs < kChirpOnMs;
        case AlarmLevel::None: break;
    }
    return false;
}

}  // namespace tuner
