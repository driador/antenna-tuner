// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The frequency counter, the tune window (§6A.10, §8B.2) and the fault policy (§8B.4a to §8B.4b).
#include <string_view>

#include "harness.hpp"
#include "tuner/faults.hpp"
#include "tuner/freq.hpp"

using namespace tuner;

TEST(counter_resolution) {
    // 14.2 MHz through /1024 over a 200 ms gate: 2773 counts, 5.12 kHz a count (§8B.0.1).
    const uint32_t n = uint32_t(14.2e6 * 0.2 / 1024);
    CHECK(n == 2773);
    CHECK_NEAR(mhz_from_count(n, 0.2), 14.2, 0.00512);
    CHECK_NEAR(mhz_from_count(n + 1, 0.2) - mhz_from_count(n, 0.2), 0.00512, 1e-9);
}

TEST(bands_and_window) {
    CHECK(band_of(14.2) && std::string_view(band_of(14.2)->name) == "20m");
    CHECK(band_of(1.8) && band_of(29.7));      // edges inclusive
    CHECK(band_of(13.9) == nullptr);
    CHECK(solution_valid(14.2, 14.25));        // 0.35 %
    CHECK(!solution_valid(14.2, 14.3));        // 0.70 %
    CHECK(!solution_valid(7.299, 7.301));      // a band-edge crossing is tighter than 0.5 %
    CHECK(solution_valid(3.6, 3.617));
}

TEST(classes_under_strict) {
    FaultPolicy p;
    CHECK(p.mode() == Mode::Strict);
    CHECK(p.raise(Fault::NoSolution) == FaultClass::B);
    CHECK(p.raise(Fault::TuneFailed) == FaultClass::B);
    CHECK(p.raise(Fault::OverSwr) == FaultClass::B);
    CHECK(p.raise(Fault::LimitHit) == FaultClass::C);
    CHECK(p.raise(Fault::EncoderMismatch) == FaultClass::C);
    CHECK(p.raise(Fault::SelfTestFail) == FaultClass::C);
    CHECK(p.any_blocking());
    p.ack();                                   // remote ACK clears B, never C
    CHECK(!p.unacked(Fault::NoSolution) && p.latched(Fault::LimitHit) && p.any_blocking());
    p.clear_local();                           // at the box, after a look
    CHECK(!p.any_blocking() && !p.transmit_inhibited());
}

TEST(over_temperature_follows_its_condition) {
    FaultPolicy p;
    p.condition(Fault::OverTemp, true);
    CHECK(p.any_blocking() && p.blower_full() && p.transmit_inhibited());
    p.condition(Fault::OverTemp, false);
    CHECK(!p.any_blocking() && !p.blower_full());
}

TEST(commissioning_logs_but_never_permits) {
    FaultPolicy p(Mode::Commissioning);
    CHECK(p.transmit_inhibited());
    CHECK(p.raise(Fault::LimitHit) == FaultClass::None);
    CHECK(p.raise(Fault::EncoderMismatch) == FaultClass::None);
    CHECK(!p.any_blocking() && p.transmit_inhibited());
}

TEST(permissive_escalates_and_tightens) {
    FaultPolicy p(Mode::Permissive);
    CHECK(p.raise(Fault::LimitHit) == FaultClass::B);
    p.ack();
    CHECK(!p.any_blocking());
    CHECK(p.raise(Fault::EncoderMismatch) == FaultClass::C);   // a repeat in one session
    CHECK(p.mode() == Mode::Strict);
    p.clear_local();
    CHECK(p.raise(Fault::LimitHit) == FaultClass::C);          // and STRICT from now on

    FaultPolicy q(Mode::Permissive);                            // the count is per session
    CHECK(q.raise(Fault::LimitHit) == FaultClass::B);
    q.ack();
    q.new_session();
    CHECK(q.raise(Fault::LimitHit) == FaultClass::B);
}

TEST(what_survives_a_power_cycle) {
    // §8B.4b: events are restored, conditions are measured again, and the mode survives.
    FaultPolicy p(Mode::Permissive);
    p.raise(Fault::NoSolution);
    p.raise(Fault::OverSwr);
    p.condition(Fault::OverTemp, true);
    p.raise(Fault::LimitHit);
    p.raise(Fault::LimitHit);                                    // escalated: C, mode now STRICT
    const FaultRecord r = p.persist();

    FaultPolicy q(Mode::Commissioning);
    q.restore(r);
    CHECK(q.unacked(Fault::NoSolution));
    CHECK(!q.unacked(Fault::OverSwr));
    CHECK(!q.active(Fault::OverTemp));
    CHECK(q.latched(Fault::LimitHit));
    CHECK(q.mode() == Mode::Strict);
    CHECK(q.any_blocking());
}
