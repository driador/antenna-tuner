// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The audible alarm (§8B.4i): the pattern for each class, what silences it, and what sounds again.
#include "harness.hpp"
#include "tuner/alarm.hpp"
#include "tuner/faults.hpp"

using namespace tuner;

namespace {
uint16_t bit(Fault f) { return uint16_t(1u << unsigned(f)); }

// Run the alarm for ms milliseconds in 10 ms ticks; returns the time the sounder was on.
uint32_t run(Alarm& a, Alarm::In& in, uint32_t ms) {
    uint32_t on = 0;
    for (uint32_t t = 0; t < ms; t += 10) {
        if (a.step(in)) on += 10;
        in.now_ms += 10;
        in.silence = false;
    }
    return on;
}
}  // namespace

TEST(alarm_patterns_by_class) {
    Alarm a;
    Alarm::In in;
    in.now_ms = 5000;
    CHECK(run(a, in, 1000) == 0 && a.level() == AlarmLevel::None);
    in.unacked_b = bit(Fault::NoSolution);
    CHECK(a.step(in));                                    // the first beep at once
    CHECK(run(a, in, 4000) == 2 * Alarm::kSlowOnMs && a.level() == AlarmLevel::Slow);
    in.latched_c = bit(Fault::SelfTestFail);              // C outranks B
    CHECK(run(a, in, 3000) == 10 * Alarm::kFastOnMs && a.level() == AlarmLevel::Fast);
    in.latched_c = in.unacked_b = 0;
    in.derate = true;                                     // a warning chirps
    CHECK(run(a, in, 30000) == 2 * Alarm::kChirpOnMs && a.level() == AlarmLevel::Chirp);
    in.derate = false;
    CHECK(run(a, in, 1000) == 0 && a.level() == AlarmLevel::None);
}

TEST(alarm_ack_and_silence) {
    Alarm a;
    Alarm::In in;
    in.unacked_b = bit(Fault::TuneFailed);
    run(a, in, 500);
    in.unacked_b = 0;                                     // an ACK, from either end
    CHECK(run(a, in, 4000) == 0);

    in.latched_c = bit(Fault::EncoderMismatch);
    run(a, in, 500);
    in.silence = true;                                    // a knob press: the latch stays, the sound stops
    CHECK(run(a, in, 4000) == 0 && a.level() == AlarmLevel::None);
    in.unacked_b = bit(Fault::OverSwr);                   // something new sounds again, at its own level
    CHECK(run(a, in, 2000) == Alarm::kSlowOnMs && a.level() == AlarmLevel::Slow);
    in.silence = true;
    run(a, in, 100);
    in.latched_c |= bit(Fault::RelayMismatch);            // a second C sounds fast, as any new one does
    CHECK(run(a, in, 600) == 2 * Alarm::kFastOnMs);
    in.silence = true;
    run(a, in, 100);
    in.latched_c = in.unacked_b = 0;                      // cleared at the box...
    run(a, in, 100);
    in.latched_c = bit(Fault::EncoderMismatch);           // ...and back: it sounds again
    CHECK(run(a, in, 600) == 2 * Alarm::kFastOnMs);
}

TEST(alarm_silences_the_warnings_until_they_clear) {
    Alarm a;
    Alarm::In in;
    in.over_temp = true;
    CHECK(run(a, in, 100) == Alarm::kChirpOnMs);
    in.silence = true;
    CHECK(run(a, in, 30000) == 0);
    in.derate = true;                                     // a different warning is new
    CHECK(run(a, in, 100) == Alarm::kChirpOnMs);
    in.silence = true;
    run(a, in, 100);
    in.over_temp = in.derate = false;
    run(a, in, 100);
    in.over_temp = true;
    CHECK(run(a, in, 100) == Alarm::kChirpOnMs);
}
