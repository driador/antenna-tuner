// The core's hardware-facing pieces: AS5048A frames, calibration curves, the coordinated-move planner,
// the steady-carrier test and the tank thermistor.
#include <algorithm>
#include <cmath>
#include <vector>

#include "harness.hpp"
#include "tuner/as5048.hpp"
#include "tuner/curve.hpp"
#include "tuner/motion.hpp"
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
