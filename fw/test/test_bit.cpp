// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The built-in test (§8B.4h): the passive windows, and the active sequencer against a small stand-in for
// the tuner that moves axes and switches paths a few ticks after it is asked.
#include <cmath>
#include <string>
#include <vector>

#include "harness.hpp"
#include "tuner/bit.hpp"
#include "tuner/pins.hpp"

using namespace tuner;
using bit::Check;
using bit::mask;

namespace {
struct Env {
    double turns[3] = {10, 25, 5};      // C1, C2 near its high end, L
    double travel[3] = {30, 30, 22};
    Path path = Path::Tune;
    int busy = 0, pending_axis = -1;
    double pending_turns = 0;
    Path pending_path = Path::Tune;
    bool axis_fault = false, relay_fault = false;
    bool carrier = false, panel_ok = true, vote = true;
    bool stuck_axis[3] = {}, latch_transparent = false, permit_dead = false, refuse = false;
    bool gate_open = false, gate_silent = false;   // the step gate passes steps; the burst never reports
    uint32_t gate_runs = 0;
    bool gate_moved = false;
    int bursts = 0;
    Path broken_path = Path::Tune;      // a path whose relay never answers (TUNE: none)
    bit::Rest rest{0.9, 0.9, 0.0, 0.5, 22};
    bool drive_k1 = false;
    uint32_t permit_lag_ms = 0, path_done_ms = 0;   // the permit pin trails the vote after a path change
    uint32_t now = 1000;
    std::vector<std::string> asked;

    bool k1_current() const { return path != Path::Tune || (drive_k1 && latch_transparent); }
    bit::Active::In in() const {
        bit::Active::In i;
        i.now_ms = now;
        i.safe = !carrier && panel_ok;
        i.clear = !axis_fault && !relay_fault;
        i.quiet = busy == 0;
        for (int a = 0; a < 3; ++a) {
            i.turns[a] = turns[a];
            i.travel[a] = travel[a];
        }
        i.axis_fault = axis_fault;
        i.relay_fault = relay_fault;
        i.path = path;
        i.k1_current = k1_current();
        i.vote = vote;
        i.permit = vote && !permit_dead && now - path_done_ms >= permit_lag_ms;
        i.rest = rest;
        i.gate_runs = gate_runs;
        i.gate_judged = true;
        i.gate_moved = gate_moved;
        return i;
    }
    void apply(const bit::Active::Out& o) {
        drive_k1 = o.drive_k1;
        if (o.gate_burst) {                 // the Teensy layer: steps, settle, the encoders again
            ++bursts;
            const bool permit_up = vote && !permit_dead;
            gate_moved = gate_open || !permit_up;   // with the permit down the gate is open anyway
            if (gate_moved) turns[2] += 1.0 / 16;
            if (!gate_silent) ++gate_runs;
        }
        if (o.jog_axis >= 0) {
            asked.push_back("jog " + std::to_string(o.jog_axis) + (o.jog_turns > 0 ? " +" : " -"));
            if (!refuse && busy == 0) {
                busy = 20;
                pending_axis = o.jog_axis;
                pending_turns = o.jog_turns;
            }
        }
        if (o.path_request) {
            asked.push_back(std::string("path ") + path_name(o.path));
            if (!refuse && !carrier && busy == 0) {   // the path switch refuses a change under RF (§5.5)
                busy = 13;
                pending_path = o.path;
            }
        }
    }
    void tick() {
        now += 10;
        if (busy == 0 || --busy > 0) return;
        if (pending_axis >= 0) {
            if (stuck_axis[pending_axis]) axis_fault = true;   // the state machine's move check
            else turns[pending_axis] += pending_turns;
            pending_axis = -1;
        } else if (pending_path == broken_path && broken_path != Path::Tune) {
            relay_fault = true;                               // the coil current disagreed: back to TUNE
            path = Path::Tune;
        } else {
            path = pending_path;
            path_done_ms = now;
        }
    }
    bit::Active run(int max_ticks = 3000) {
        bit::Active a;
        a.start(now);
        for (int t = 0; t < max_ticks && a.running(); ++t) {
            apply(a.step(in()));
            tick();
        }
        return a;
    }
};
}  // namespace

TEST(bit_rest_windows) {
    bit::Rest r{0.9, 0.9, 0.0, 0.5, 22};
    CHECK(bit::rest_checks(r) == 0);
    r.v_mag = 0.05;                                       // V_MAG on a rail
    CHECK(bit::rest_checks(r) == mask(Check::BridgeIdle));
    r = {0.9, 1.79, 0.0, 0.5, 22};                        // V_PHS on VREF
    CHECK(bit::rest_checks(r) == mask(Check::BridgeIdle));
    r = {0.9, 0.9, 0.05, 0.5, 22};                        // the forward detector at its RF threshold
    CHECK(bit::rest_checks(r) == mask(Check::FwdIdle));
    r = {0.9, 0.9, 0.0, 0.0, 22};                         // the cal-load detector's bias gone
    CHECK(bit::rest_checks(r) == mask(Check::CalIdle));
    r = {0.9, 0.9, 0.0, 0.5, 85};                         // a drifted thermistor
    CHECK(bit::rest_checks(r) == mask(Check::Thermistor));
    r.tank_c = std::nan("");                              // open: already an over-temperature
    CHECK(bit::rest_checks(r) == 0);
    for (unsigned c = 0; c < unsigned(Check::Count); ++c) CHECK(std::string(bit::name(Check(c))) != "?");
    CHECK(bit::grade(Check::Latch) == bit::Grade::C && bit::grade(Check::AxisL) == bit::Grade::Mechanical &&
          bit::grade(Check::RelayK2) == bit::Grade::B && bit::grade(Check::PermitRise) == bit::Grade::Warn);
    CHECK(bit::fault_of(Check::Expander) == Fault::SelfTestFail && bit::fault_of(Check::Latch) == Fault::SelfTestFail);
    CHECK(bit::fault_of(Check::AxisC2) == Fault::EncoderMismatch && bit::fault_of(Check::RelayK1) == Fault::RelayMismatch);
    CHECK(bit::fault_of(Check::CalIdle) == Fault::BuiltInTest && bit::fault_of(Check::Thermistor) == Fault::Count);
    const uint32_t f = mask(Check::AxisL) | mask(Check::FwdIdle) | mask(Check::CalIdle) | mask(Check::Thermistor);
    CHECK(bit::behind(f, Fault::LimitHit) == mask(Check::AxisL) && bit::behind(f, Fault::SelfTestFail) == 0);
    char out[24];
    CHECK(bit::names(bit::behind(f, Fault::BuiltInTest), out, sizeof out) == 23);   // cut to fit
    CHECK(std::string(out) == "forward detector idle, ");
    CHECK(bit::names(0, out, sizeof out) == 0 && out[0] == 0);
}

TEST(bit_names_the_permit_term) {
    namespace iox = pins::iox;
    const uint16_t all = 0x7F00;                          // GPB0-6 high
    CHECK(bit::permit_blocker(all) == nullptr);
    CHECK(std::string(bit::permit_blocker(all & ~(1u << iox::PANEL_OK))) == "PANEL_OK");
    // An input low names the input, not the gate it drops.
    CHECK(std::string(bit::permit_blocker(all & ~(1u << iox::LIMIT_OK) & ~(1u << iox::HARD_OK))) == "LIMIT_OK");
    CHECK(std::string(bit::permit_blocker(all & ~(1u << iox::BYP_OK))) == "BYP_OK (vote gate)");
}

TEST(bit_clean_run) {
    Env e;
    const bit::Active a = e.run();
    CHECK(a.completed() && a.failed() == 0 && e.path == Path::Tune);
    // Each axis away from its nearer end and back (C2 sits near its high end), then AUX, CAL, TUNE.
    const std::vector<std::string> want = {"jog 0 +", "jog 0 -", "jog 1 -", "jog 1 +", "jog 2 +",
                                           "jog 2 -", "path AUX", "path CAL", "path TUNE"};
    CHECK(e.asked == want);
    CHECK(e.turns[0] == 10 && e.turns[1] == 25 && e.turns[2] == 5);
}

TEST(bit_failures_are_named) {
    {
        Env e;
        e.stuck_axis[1] = true;                           // C2 does not move
        const bit::Active a = e.run();
        CHECK(a.completed() && a.failed() == mask(Check::AxisC2) && e.asked.size() == 3);
    }
    {
        Env e;
        e.broken_path = Path::Cal;                        // K2 never pulls in
        const bit::Active a = e.run();
        CHECK(a.completed() && a.failed() == mask(Check::RelayK2) && e.path == Path::Tune);
    }
    {
        Env e;
        e.latch_transparent = true;                       // the hold latch lets K1 change with the permit up
        CHECK(e.run().failed() == mask(Check::Latch));
    }
    {
        Env e;                                            // a permit a few ticks behind the vote: still tested
        e.latch_transparent = true;
        e.permit_lag_ms = 20;
        const bit::Active a = e.run();
        CHECK(a.failed() == mask(Check::Latch) && a.untested() == 0);
    }
    {
        Env e;
        e.permit_dead = true;                             // the vote is up but the permit never rises
        const bit::Active a = e.run();
        CHECK(a.completed() && a.failed() == mask(Check::PermitRise) &&
              a.untested() == (mask(Check::Latch) | mask(Check::StepGate)) && e.bursts == 0);
    }
    {
        Env e;
        e.vote = false;                                   // COMMISSIONING withholds the vote: nothing to judge
        const bit::Active a = e.run();
        CHECK(a.completed() && a.failed() == 0 &&
              a.untested() == (mask(Check::Latch) | mask(Check::PermitRise) | mask(Check::StepGate)));
    }
    {
        Env e;                                            // the step gate passes steps with the permit up
        e.gate_open = true;
        const bit::Active a = e.run();
        CHECK(a.completed() && a.failed() == mask(Check::StepGate) && a.untested() == 0 && e.bursts == 1);
        CHECK(bit::grade(Check::StepGate) == bit::Grade::C && bit::fault_of(Check::StepGate) == Fault::SelfTestFail);
    }
    {
        Env e;                                            // the gate holds: one burst, nothing moved
        const bit::Active a = e.run();
        CHECK(a.completed() && a.failed() == 0 && a.untested() == 0 && e.bursts == 1 && e.turns[2] == 5);
    }
    {
        Env e;                                            // a burst that never reports is not judged
        e.gate_silent = true;
        const bit::Active a = e.run();
        CHECK(a.completed() && a.failed() == 0 && a.untested() == mask(Check::StepGate));
    }
    {
        Env e;
        e.rest.v_fwd = 0.2;                               // the forward detector off its idle: named, and the
        const bit::Active a = e.run();                    // run goes on to the end
        CHECK(a.completed() && a.failed() == mask(Check::FwdIdle) && e.asked.size() == 9 && a.untested() == 0);
    }
}

TEST(bit_stops_safely) {
    {
        Env e;                                            // keyed while the path is AUX: stop, then TUNE again
        bit::Active a;
        a.start(e.now);
        bool keyed = false;
        for (int t = 0; t < 3000 && a.running(); ++t) {
            if (!keyed && e.path == Path::Aux) e.carrier = keyed = true;
            if (keyed && t % 200 == 0) e.carrier = false;   // the operator unkeys
            e.apply(a.step(e.in()));
            e.tick();
        }
        CHECK(keyed && !a.running() && !a.completed() && a.failed() == 0 && e.path == Path::Tune);
    }
    {
        Env e;                                            // the vote falls while K1 is driven: let go at once
        bit::Active a;
        a.start(e.now);
        bool fell = false;
        for (int t = 0; t < 3000 && a.running(); ++t) {
            const bit::Active::Out o = a.step(e.in());
            if (fell) CHECK(!o.drive_k1);
            if (o.drive_k1 && !fell) e.vote = !(fell = true);
            e.apply(o);
            e.tick();
        }
        CHECK(fell && a.completed() && a.failed() == 0 && a.untested() == (mask(Check::Latch) | mask(Check::StepGate)) &&
              e.bursts == 0);                             // no burst once the permit is down: the gate is open
    }
    {
        Env e;                                            // never safe to start: gives up, asks for nothing
        e.carrier = true;
        const bit::Active a = e.run();
        CHECK(!a.completed() && e.asked.empty());
    }
    {
        Env e;                                            // a jog that is refused ends the run
        e.refuse = true;
        const bit::Active a = e.run();
        CHECK(!a.completed() && e.asked.size() == 1);
    }
}
