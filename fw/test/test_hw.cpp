// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The core's hardware-facing pieces: AS5048A frames, calibration curves, the coordinated-move planner,
// the steady-carrier test and the tank thermistor.
#include <algorithm>
#include <cmath>
#include <vector>

#include "harness.hpp"
#include "tuner/as5048.hpp"
#include "tuner/cal.hpp"
#include "tuner/curve.hpp"
#include "tuner/motion.hpp"
#include "tuner/path.hpp"
#include "tuner/sense.hpp"

using namespace tuner;

TEST(as5048_commands_and_replies) {
    using namespace as5048;
    CHECK(read_command(kRegAngle) == 0xFFFF);
    CHECK(read_command(kRegDiagAgc) == 0x7FFD);
    CHECK(read_command(kRegClearError) == 0x4001);
    const uint16_t good = with_parity(0x1234);
    Reply r = decode(good);
    CHECK(r.parity_ok && !r.error && r.data == 0x1234);
    CHECK(!decode(uint16_t(good ^ 0x0010)).parity_ok);      // one bit flipped on the cable
    r = decode(with_parity(0x4000 | 0x0005));
    CHECK(r.parity_ok && r.error && r.data == 0x0005);
    CHECK(diagnostics((1u << 8) | 0x80).ok());
    CHECK(diagnostics((1u << 8) | 0x80).agc == 0x80);
    CHECK(!diagnostics((1u << 8) | (1u << 11)).ok());         // magnet too far
    CHECK(!diagnostics(0x80).ok());                           // offset compensation not finished
}

TEST(calibration_curves) {
    const Curve c = Curve::line(0, 25e-12, 30, 700e-12);
    CHECK(c.valid());
    CHECK_NEAR(c.at(15), 362.5e-12, 1e-24);
    CHECK_NEAR(c.inverse(362.5e-12), 15, 1e-9);
    CHECK_NEAR(c.at(31), 722.5e-12, 1e-24);                   // past the end, along the last segment
    const Curve down = Curve::line(0, 700e-12, 30, 25e-12);   // a part that winds the other way
    CHECK(down.valid());
    CHECK_NEAR(down.inverse(362.5e-12), 15, 1e-9);
    Curve bad = Curve::line(0, 1, 1, 2);
    bad.add(2, 1.5);
    CHECK(!bad.valid());

    const Curve roller = roller_model();
    CHECK(roller.valid() && roller.n == 23);
    CHECK_NEAR(roller.at(22), 30.0373e-6, 1e-12);             // nec/out/roller_vna_k22_deck.csv
    for (double turns : {0.5, 3.3, 7.3, 15.0, 21.5}) CHECK_NEAR(roller.inverse(roller.at(turns)), turns, 1e-9);
}

namespace {
// Runs a plan through the executor at the timer's rate, recording each axis's position.
struct Trace {
    std::vector<double> t, pos[kAxes];
};

Trace run(const MovePlan& p, double dt = 20e-6, double stop_at = -1) {
    MoveExecutor e;
    e.start(&p);
    Trace tr;
    double t = 0;
    for (int n = 0; e.running() && n < 10000000; ++n) {
        if (stop_at >= 0 && t >= stop_at) e.stop();
        const double s = e.advance(dt);
        t += dt;
        tr.t.push_back(t);
        for (int i = 0; i < kAxes; ++i) tr.pos[i].push_back(p.start(i) + p.delta(i) * s);
    }
    return tr;
}

// Largest speed and acceleration of one axis, from differences over a window w (samples).
void peaks(const Trace& tr, int axis, double& v, double& a, int w = 50) {
    v = a = 0;
    const double dt = tr.t[1] - tr.t[0];
    double prev = NAN;
    for (size_t k = w; k < tr.t.size(); k += w) {
        const double vel = (tr.pos[axis][k] - tr.pos[axis][k - w]) / (w * dt);
        v = std::max(v, std::fabs(vel));
        if (!std::isnan(prev)) a = std::max(a, std::fabs(vel - prev) / (w * dt));
        prev = vel;
    }
}
}  // namespace

TEST(move_single_axis_is_a_trapezoid) {
    // 7.5 rev/s and a 0.4 s ramp at 1600 steps/rev (§8B.3a), 10 turns and then 1.25 turns.
    AxisMotion m[kAxes];
    m[0] = {12000, 30000};
    m[1] = m[2] = {1, 1};
    const int32_t a[kAxes] = {0, 0, 0}, b[kAxes] = {16000, 0, 0}, c[kAxes] = {2000, 0, 0};
    MovePlan p;
    CHECK(p.plan(a, b, m));
    CHECK_NEAR(p.duration(), 16000.0 / 12000 + 12000.0 / 30000, 0.01 * p.duration());
    CHECK(p.plan(a, c, m));
    CHECK_NEAR(p.duration(), 2 * std::sqrt(2000.0 / 30000), 0.01 * p.duration());
}

TEST(axes_finish_together_inside_their_limits) {
    AxisMotion m[kAxes] = {{12000, 30000}, {12000, 30000}, {12000, 16000}};   // the roller ramps gently
    const int32_t a[kAxes] = {1000, 40000, 30000}, b[kAxes] = {45000, 2000, 6000};
    MovePlan p;
    CHECK(p.plan(a, b, m));
    const Trace tr = run(p);
    for (int i = 0; i < kAxes; ++i) {
        CHECK_NEAR(tr.pos[i].back(), b[i], 1e-6);
        double v, acc;
        peaks(tr, i, v, acc);
        CHECK(v <= m[i].v_max * 1.01);
        CHECK(acc <= m[i].a_max * 1.05);
    }
    // Every axis is on the line between its ends at all times, so they start and stop together.
    for (size_t k = 0; k < tr.t.size(); k += 997) {
        const double s0 = (tr.pos[0][k] - a[0]) / double(b[0] - a[0]);
        for (int i = 1; i < kAxes; ++i) CHECK_NEAR((tr.pos[i][k] - a[i]) / double(b[i] - a[i]), s0, 1e-9);
    }
}

TEST(roller_slow_zone) {
    // §7.2: at most 2 rev/s within 3 turns of either end; full speed elsewhere. 1600 steps a turn, 22 turns.
    AxisMotion m[kAxes];
    m[0] = m[1] = {1, 1};
    m[2] = {12000, 16000, 3 * 1600, 19 * 1600, 3200};
    const int32_t a[kAxes] = {0, 0, 18 * 1600}, b[kAxes] = {0, 0, 1 * 1600};
    MovePlan p;
    CHECK(p.plan(a, b, m));
    const Trace tr = run(p);
    double fastest = 0, in_zone = 0;
    const double dt = tr.t[1] - tr.t[0];
    for (size_t k = 50; k < tr.t.size(); ++k) {
        const double vel = std::fabs(tr.pos[2][k] - tr.pos[2][k - 50]) / (50 * dt);
        fastest = std::max(fastest, vel);
        if (std::max(tr.pos[2][k], tr.pos[2][k - 50]) < m[2].slow_lo) in_zone = std::max(in_zone, vel);
    }
    CHECK(fastest > 2 * m[2].v_slow);
    CHECK(in_zone <= m[2].v_slow * 1.01);
    CHECK_NEAR(tr.pos[2].back(), b[2], 1e-6);
}

TEST(a_stopped_move_ramps_down) {
    AxisMotion m[kAxes] = {{12000, 30000}, {12000, 30000}, {12000, 16000}};
    const int32_t a[kAxes] = {0, 0, 0}, b[kAxes] = {40000, 20000, 30000};
    MovePlan p;
    CHECK(p.plan(a, b, m));
    const Trace tr = run(p, 20e-6, p.duration() / 2);
    for (int i = 0; i < kAxes; ++i) {
        double v, acc;
        peaks(tr, i, v, acc);
        CHECK(acc <= m[i].a_max * 1.05);
        CHECK(std::fabs(tr.pos[i].back() - a[i]) < std::fabs(double(b[i] - a[i])));   // stopped short
    }
    const int32_t z[kAxes] = {5, 6, 7};
    CHECK(p.plan(z, z, m) && p.duration() == 0);
    MoveExecutor e;
    e.start(&p);
    CHECK(!e.running() && e.s() == 1);
}

TEST(steady_carrier) {
    CarrierDetector d;
    CHECK(!d.update(14.20000));
    CHECK(d.update(14.20512));                                 // one count apart
    CHECK(d.update(14.20000));
    CHECK(!d.update(14.30000));                                // a QSY starts over
    CHECK(d.update(14.30512));
    CHECK(!d.update(0.0));                                     // gone
    CHECK(!d.update(1.80000));
    CHECK(d.update(1.80512));                                  // 160 m: one count is 0.28 %
    CarrierDetector ssb;
    int present = 0;
    for (int i = 0; i < 50; ++i) present += ssb.update(7.15 + ((i * 37) % 11 - 5) * 0.02);
    CHECK(present == 0);
}

TEST(tank_thermistor) {
    CHECK_NEAR(ntc_celsius(0.5), 25.0, 1e-9);
    const double r60 = 10e3 * std::exp(3950 * (1 / 333.15 - 1 / 298.15));
    CHECK_NEAR(ntc_celsius(r60 / (r60 + 10e3)), 60.0, 1e-6);
    CHECK(std::isnan(ntc_celsius(0.995)));                     // open lead
    CHECK(std::isnan(ntc_celsius(0.002)));                     // shorted
    Hysteresis h(65, 55);
    CHECK(!h.update(60));
    CHECK(h.update(66));
    CHECK(h.update(60));
    CHECK(!h.update(54));
}

TEST(rf_path_switch_follows_the_relay_sequence) {
    PathSwitch ps;
    PathSwitch::In in;
    in.now_ms = 1000;
    CHECK(ps.request(Path::Cal, in.now_ms));
    PathSwitch::Out o = ps.step(in);
    CHECK(o.hold_vote && !o.k1 && !o.k2);               // the vote first, the relays later
    in.now_ms += 99;
    CHECK(!ps.step(in).k1);
    CHECK(!ps.request(Path::Aux, in.now_ms));           // one change at a time
    in.now_ms += 1;
    o = ps.step(in);
    CHECK(o.hold_vote && o.k1 && o.k2);                 // 100 ms: RF decayed, the latch open
    in.k1_current = in.k2_current = true;
    in.now_ms += 25;
    o = ps.step(in);
    CHECK(!o.mismatch && ps.path() == Path::Cal && !ps.busy());
    in.now_ms += 10;
    CHECK(!ps.step(in).hold_vote);                      // confirmed: the vote is given back
    in.carrier = true;
    in.load_rf = true;                                  // CAL: the load sees the first key-down
    CHECK(!ps.step(in).mismatch);

    PathSwitch weld;                                    // AUX, but RF still reaches the load: K2 welded
    PathSwitch::In w;
    w.now_ms = 0;
    weld.request(Path::Aux, 0);
    for (w.now_ms = 0; weld.busy(); w.now_ms += 10) {
        w.k1_current = true;
        weld.step(w);
    }
    w.carrier = true;
    w.load_rf = true;
    CHECK(weld.step(w).mismatch);

    PathSwitch dead;                                    // a coil that never draws
    PathSwitch::In d;
    dead.request(Path::Aux, 0);
    bool flagged = false;
    for (d.now_ms = 0; d.now_ms < 300; d.now_ms += 10) flagged = dead.step(d).mismatch || flagged;
    CHECK(flagged && dead.path() == Path::Tune);
}

TEST(bridge_calibration_from_open_short_load) {
    // A part 0.8 dB high and 4 deg off, with a coupler whose directivity floor is -28 dB.
    Ad8302Scale truth;
    truth.v_center = 0.924;
    truth.v_phs_zero = 1.76;
    truth.v_per_deg = 0.0098;
    auto read = [&](cplx g) {
        double vm, vp;
        ad8302_from_gamma(g, vm, vp, truth);
        return Standard{vm, vp};
    };
    BridgeCal cal;
    CHECK(bridge_cal(read(cplx(1, 0)), read(cplx(-1, 0)), read(cplx(0.0398, 0)), cal) == CalError::None);
    CHECK(cal.valid);
    CHECK_NEAR(cal.scale.v_center, truth.v_center, 1e-9);
    CHECK_NEAR(cal.scale.v_phs_zero, truth.v_phs_zero, 1e-9);
    CHECK_NEAR(cal.scale.v_per_deg, truth.v_per_deg, 1e-9);
    CHECK_NEAR(cal.floor_db, -28.0, 0.01);
    for (cplx g : {cplx(0.5, 0.3), cplx(-0.2, 0.6), cplx(0.1, -0.05)}) {
        const Standard s = read(g);
        const GammaReading r = calibrated(cal, s.v_mag, s.v_phs);
        CHECK_NEAR(r.mag, std::max(std::abs(g), std::pow(10.0, -28.0 / 20)), 1e-6);
        CHECK_NEAR(r.theta_deg, std::fabs(std::arg(g)) * 180 / 3.14159265358979323846, 1e-6);
    }
    // 150 ohm reads |Γ| = 0.5: a measured slope replaces the datasheet's.
    truth.v_per_db = 0.032;
    BridgeCal c2;
    CHECK(bridge_cal(read(cplx(1, 0)), read(cplx(-1, 0)), read(cplx(0.0398, 0)), c2) == CalError::None);
    CHECK(bridge_cal_slope(read(cplx(0.5, 0)), 0.5, read(cplx(0.0398, 0)), c2) == CalError::None);
    CHECK_NEAR(c2.scale.v_per_db, 0.032, 1e-9);
    CHECK_NEAR(c2.floor_db, -28.0, 0.01);

    BridgeCal bad;                                      // the mistakes the procedure can make
    CHECK(bridge_cal(read(cplx(1, 0)), read(cplx(0.5, 0)), read(cplx(0.04, 0)), bad) == CalError::OpenShortDisagree);
    CHECK(bridge_cal(read(cplx(1, 0)), read(cplx(1, 0)), read(cplx(0.04, 0)), bad) == CalError::PhaseSpanSmall);
    CHECK(bridge_cal(read(cplx(1, 0)), read(cplx(-1, 0)), read(cplx(0.3, 0)), bad) == CalError::LoadNotLow);
    CHECK(!bad.valid);
}

TEST(power_curve_points) {
    Curve c;                                            // wattmeter readings in any order, one repeated
    CHECK(c.insert(1.20, 100));
    CHECK(c.insert(0.40, 10));
    CHECK(c.insert(2.60, 500));
    CHECK(c.insert(1.21, 102));                         // within 2 %: replaces the 100 W point
    CHECK(c.n == 3 && c.valid());
    CHECK_NEAR(c.at(1.21), 102, 1e-9);
    CHECK_NEAR(c.at(0.805), 56, 1e-9);
}
