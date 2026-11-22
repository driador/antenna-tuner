// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The audible alarm (§8B.4i): one pattern, for the worst thing sounding. A class C latch beeps fast, an
// unacknowledged class B slowly, and an over-temperature or the 160 m derate warning chirps. An ACK
// clears the B faults and so their sound. A knob press at the box silences everything sounding at that
// moment, C latches included, which stay latched; anything new sounds again, and so does anything that
// clears and comes back. The page's tone follows the same rules with its own silence (web_page.cpp).
#pragma once
#include <cstdint>

namespace tuner {

enum class AlarmLevel : uint8_t { None, Chirp, Slow, Fast };

class Alarm {
public:
    struct In {
        uint32_t now_ms = 0;
        uint16_t latched_c = 0, unacked_b = 0;   // bit per Fault
        bool over_temp = false, derate = false;
        bool silence = false;                    // a knob press at the box since the last step
    };
    // Each pattern starts with its first beep the moment its level begins.
    static constexpr uint32_t kFastOnMs = 150, kFastPeriodMs = 300;       // class C
    static constexpr uint32_t kSlowOnMs = 150, kSlowPeriodMs = 2000;      // class B
    static constexpr uint32_t kChirpOnMs = 60, kChirpPeriodMs = 15000;    // the warnings

    bool step(const In& in);                     // the sounder, on or off, this tick
    AlarmLevel level() const { return level_; }

private:
    uint16_t quiet_c_ = 0, quiet_b_ = 0;         // silenced, until each clears
    bool quiet_hot_ = false, quiet_derate_ = false;
    AlarmLevel level_ = AlarmLevel::None;
    uint32_t since_ = 0;
};

}  // namespace tuner
