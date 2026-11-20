// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The state machine in closed loop against a modeled tuner: elements whose true values are off their
// encoder calibration, a bridge with residual errors, a motion layer and a 300 ms measurement. Every
// tick also checks the PTT rules of §8B.3: no move with the vote up, none within 30 ms of it dropping,
// none under the bypass key.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string_view>
#include <vector>

#include "harness.hpp"
#include "vectors.hpp"
#include "tuner/fsm.hpp"
#include "tuner/seed.hpp"

using namespace tuner;

namespace {
constexpr double pF = 1e-12, uH = 1e-6;
const Parts kParts{25 * pF, 700 * pF, 20 * pF, 675 * pF, 0.2 * uH, 32.4 * uH};

using vec::kVecs;
using vec::Vec;
constexpr int kVecCount = vec::kCount;

const Vec& vec_at(double mhz) {
    for (const Vec& v : kVecs)
        if (std::fabs(v.mhz - mhz) < 1e-9) return v;
    return kVecs[0];
}

constexpr uint32_t kTickMs = 10;
constexpr int kGateTicks = 30;     // 200 ms gate plus the bridge read (§8B.3a)
constexpr int kMoveTicks = 40;

Config config() {
    Config c;
    c.parts = kParts;
    return c;
}

struct Plant {
    double mhz = 14.0;
    cplx z_load{50, 0};                           // at the tuner, after the feeder
    Setting pos{300 * pF, 5 * uH, 300 * pF};      // what the encoders report
    double err_c1 = 0, err_l = 0, err_c2 = 0;     // true value = reported * (1 + err)
    double mag_err_db = 0, phs_err_deg = 0;       // bridge residuals after calibration
    double trip_swr = 2.0;                        // the over-SWR comparator
    double drift = 0;                             // the load's R grows this much with every move
    bool carrier = true, bypass = false, limit = false, over_temp = false;
    bool mismatch = false, stall = false, self_test_ok = true;
    bool ack = false, local_clear = false, tune_request = false;   // one-tick pulses
    bool tune_path = true, relay_mismatch = false, jog = false;   // the last two one-tick
    Setting jog_target;
    uint32_t now = 5000;

    uint32_t running = 0, done = 0;               // the motion layer
    int left = 0;
    Setting to;
    int gate = kGateTicks;                        // the bridge

    bool trace = false;                           // print every state change (TRACE_MHZ=1.8 ./test_fsm)
    bool permit = false, ever_permit = false;     // what the checks saw
    uint32_t permit_down = 0;
    int violations = 0, moves = 0;
    std::vector<State> visited;

    void load(const Vec& v) {
        mhz = v.mhz;
        z_load = {v.r, v.x};
    }
    Setting actual() const { return {pos.c1 * (1 + err_c1), pos.l * (1 + err_l), pos.c2 * (1 + err_c2)}; }
    cplx gamma() const { return gamma_from_z(input_impedance(mhz * 1e6, actual(), z_load)); }
    double swr() const { return swr_from_mag(std::abs(gamma())); }
    GammaReading read() const {
        double vm, vp;
        ad8302_from_gamma(gamma(), vm, vp);
        return gamma_from_ad8302(vm + mag_err_db * 0.030, vp - phs_err_deg * 0.010);
    }
    bool saw(State s) const {
        for (State v : visited)
            if (v == s) return true;
        return false;
    }

    Outputs tick(Tuner& tu) {
        Inputs in;
        in.now_ms = now;
        in.self_test_ok = self_test_ok;
        in.bypass = bypass;
        in.carrier = carrier;
        in.position = pos;
        in.move_done = done;
        in.encoder_mismatch = mismatch;
        in.limit_hit = limit;
        in.over_temp = over_temp;
        in.swr_trip = carrier && swr() > trip_swr;
        in.tune_request = tune_request;
        in.ack = ack;
        in.local_clear = local_clear;
        in.tune_path = tune_path;
        in.relay_mismatch = relay_mismatch;
        in.jog = jog;
        in.jog_target = jog_target;
        if (left == 0 && carrier) {
            if (--gate == 0) {
                in.have_measurement = true;
                in.m.mhz = mhz;
                in.m.gamma = read();
                gate = kGateTicks;
            }
        } else {
            gate = kGateTicks;                    // a gate never spans a move or a gap in the carrier
        }

        const Outputs o = tu.step(in);
        tune_request = ack = local_clear = relay_mismatch = jog = false;
        if (visited.empty() || visited.back() != o.state) {
            visited.push_back(o.state);
            if (trace) {
                const GammaReading g = read();
                std::printf("        %6u ms %-9s att %d  SWR %7.2f  read %.3f/%5.1f  at %5.1f pF %6.3f uH %5.1f pF  "
                            "-> %5.1f %6.3f %5.1f\n", unsigned(now), state_name(o.state), o.attempt, swr(), g.mag,
                            g.theta_deg, pos.c1 / pF, pos.l / uH, pos.c2 / pF, o.target.c1 / pF, o.target.l / uH,
                            o.target.c2 / pF);
            }
        }

        if (permit && !o.mcu_permit) permit_down = now;
        permit = o.mcu_permit;
        ever_permit = ever_permit || permit;
        if (o.move_id != running) {
            running = o.move_id;
            to = o.target;
            left = kMoveTicks;
            ++moves;
            if (o.mcu_permit || now - permit_down < 30 || bypass) ++violations;
        }
        if (left > 0) {
            if (o.mcu_permit) ++violations;
            if (!o.motion_enable) {               // stopped short, where it was
                left = 0;
                done = running;
            } else if (!stall && --left == 0) {
                pos = to;
                done = running;
                z_load = cplx(z_load.real() * (1 + drift), z_load.imag());
            }
        }
        now += kTickMs;
        return o;
    }
};

Outputs run_for(Tuner& tu, Plant& p, int ticks) {
    Outputs o;
    for (int i = 0; i < ticks; ++i) o = p.tick(tu);
    return o;
}

Outputs run_until(Tuner& tu, Plant& p, bool (*done)(const Outputs&, const Plant&), int max_ticks = 4000) {
    Outputs o;
    for (int i = 0; i < max_ticks; ++i) {
        o = p.tick(tu);
        if (done(o, p)) break;
    }
    return o;
}

bool settled(const Outputs& o, const Plant&) { return o.state == State::Matched || o.state == State::Fault; }
bool moving(const Outputs& o, const Plant& p) { return o.state == State::Move && p.left > 0; }

// Un-key, key a carrier, and run to MATCHED or FAULT.
Outputs key(Tuner& tu, Plant& p, int max_ticks = 4000) {
    p.carrier = false;
    run_for(tu, p, 2);
    p.carrier = true;
    return run_until(tu, p, settled, max_ticks);
}

// Scale the load's R until the tuner, as it stands, shows at least this SWR.
void detune(Plant& p, double target) {
    const cplx z0 = p.z_load;
    for (double k = 1.0; k < 20 && p.swr() < target; k *= 1.002) p.z_load = cplx(z0.real() * k, z0.imag());
}

struct Errors {
    double c1, l, c2, db, deg;
};

enum class Start { Mid, Upward, Downward };

struct Antenna {                   // how the real antenna differs from the NEC model the seeds came from
    double feet = 40, vf = 0.95;   // the feeder as built
    double r_scale = 1, x_shift = 0;   // at the feedpoint, 10 m only (§9 item 10)
};

// Every band edge in turn, each on a fresh Tuner: from mid-range, or from wherever the last edge left
// the elements (a band change), going up or down. Returns how many did not match.
int sweep(const Errors& e, Start start, bool seeded, const Antenna& a = {}) {
    int matched = 0, cases = 0, worst_attempts = 0;
    double worst_swr = 0, worst_s = 0;
    Setting prev{300 * pF, 5 * uH, 300 * pF};
    for (int i = 0; i < kVecCount; ++i) {
        const Vec& v = kVecs[start == Start::Downward ? kVecCount - 1 - i : i];
        const bool ten = std::string_view(v.band) == "10m";
        const cplx zl(v.zl_r * (ten ? a.r_scale : 1), v.zl_x + (ten ? a.x_shift : 0));
        const cplx z = vec::at_tuner(v.mhz, zl, a.feet, a.vf);
        // Out of the network's reach: what the elements really span is the calibrated range moved by the
        // calibration error, and a load at the edge of the nominal range can fall outside it (§9 item 10).
        const Parts reach{kParts.c1_min * (1 + e.c1), kParts.c1_max * (1 + e.c1), kParts.c2_min * (1 + e.c2),
                          kParts.c2_max * (1 + e.c2), kParts.l_min * (1 + e.l), kParts.l_max * (1 + e.l)};
        if (!solve(v.mhz * 1e6, z, kParts).ok || !solve(v.mhz * 1e6, z, reach).ok) continue;
        Plant p;
        p.mhz = v.mhz;
        p.z_load = z;
        p.err_c1 = e.c1, p.err_l = e.l, p.err_c2 = e.c2, p.mag_err_db = e.db, p.phs_err_deg = e.deg;
        if (start != Start::Mid) p.pos = prev;
        const char* t = std::getenv("TRACE_MHZ");
        p.trace = t && std::fabs(std::atof(t) - v.mhz) < 1e-6;
        Tuner tu(config());
        if (seeded) seed_priors(tu);
        const uint32_t t0 = p.now;
        const Outputs o = key(tu, p);
        const bool ok = o.state == State::Matched && p.swr() <= 1.25 && p.violations == 0;
        ++cases;
        matched += ok;
        if (!ok)
            std::printf("      %s %.3f MHz: %s (%s), attempt %d, SWR %.2f, violations %d\n", v.band, v.mhz,
                        state_name(o.state), fault_name(o.fault), o.attempt, p.swr(), p.violations);
        worst_attempts = std::max(worst_attempts, o.attempt);
        worst_swr = std::fmax(worst_swr, p.swr());
        worst_s = std::fmax(worst_s, (p.now - t0) / 1000.0);
        prev = p.pos;
    }
    std::printf("    C1 %+2.0f%% L %+2.0f%% C2 %+2.0f%%, bridge %+.2f dB %+.0f deg, %-9s %2d/%-2d  worst: %d attempts, "
                "SWR %.2f, %.1f s\n",
                e.c1 * 100, e.l * 100, e.c2 * 100, e.db, e.deg,
                start == Start::Mid ? "mid:" : start == Start::Upward ? "upward:" : "downward:", matched, cases,
                worst_attempts, worst_swr, worst_s);
    return cases - matched;
}

const Errors kErrors[] = {{0, 0, 0, 0, 0},
                          {+0.03, -0.03, +0.03, +0.25, +2},
                          {-0.03, +0.03, -0.03, -0.25, -2},
                          {+0.03, +0.03, +0.03, +0.25, -2},
                          {-0.03, -0.03, -0.03, -0.25, +2}};

}  // namespace

TEST(tunes_every_band_edge_from_the_factory_priors) {
    // The first-boot case: the NEC seed table (§6A.7 option 2), 3 % element and AD8302 residuals.
    for (const Errors& e : kErrors)
        for (Start s : {Start::Mid, Start::Upward, Start::Downward}) CHECK(sweep(e, s, true) == 0);
}

TEST(factory_priors_tolerate_a_different_antenna) {
    // The antenna is not the model the seeds came from: the feeder spread cap_demand.py sweeps, and on
    // 10 m the feedpoint uncertainty of §9 item 10 (R x 0.8-1.2, X +/- 250 ohm).
    const Errors e{+0.03, -0.03, +0.03, +0.25, +2};
    for (double feet : {39.0, 42.0})
        for (double vf : {0.93, 0.97}) {
            std::printf("    feeder %.0f ft, VF %.2f:\n", feet, vf);
            Antenna a;
            a.feet = feet, a.vf = vf;
            for (Start s : {Start::Mid, Start::Upward, Start::Downward}) CHECK(sweep(e, s, true, a) == 0);
        }
    for (double r : {0.8, 1.2})
        for (double x : {-250.0, +250.0}) {
            std::printf("    10 m feedpoint R x %.1f, X %+.0f ohm:\n", r, x);
            Antenna a;
            a.r_scale = r, a.x_shift = x;
            CHECK(sweep(e, Start::Mid, true, a) == 0);
        }
}

TEST(tunes_every_band_edge_cold) {
    // No priors at all: the probe decides the sign and coarse moves find the neighborhood.
    for (const Errors& e : kErrors)
        for (Start s : {Start::Mid, Start::Upward, Start::Downward}) CHECK(sweep(e, s, false) == 0);
}

TEST(random_antennas_errors_and_starts) {
    // Draws anywhere inside the bounds the corner sweeps use: an edge, the feeder spread, element and
    // bridge errors, a starting setting anywhere in range, factory priors or none. Fixed seed.
    // With priors every draw must match. Cold, from an arbitrary setting, a reading can sit at the top
    // of the AD8302's range through every coarse move; those few must end in a fault, never anything
    // unsafe, and the in-band tuner always has its seeds (seed.hpp).
    uint64_t state = 0x7475'6e65'7231ULL;
    auto uni = [&](double lo, double hi) {
        state = state * 6364136223846793005ULL + 1442695040888963407ULL;
        return lo + (hi - lo) * double(state >> 11) / double(1ULL << 53);
    };
    int cases = 0, matched = 0, marginal = 0, worst_attempts = 0, cold = 0, cold_matched = 0, violations = 0;
    double worst_s = 0;
    for (int i = 0; i < 1000; ++i) {
        const Vec& v = kVecs[std::min(kVecCount - 1, int(uni(0, kVecCount)))];
        const Errors e{uni(-0.03, 0.03), uni(-0.03, 0.03), uni(-0.03, 0.03), uni(-0.25, 0.25), uni(-2, 2)};
        const cplx z = vec::at_tuner(v.mhz, {v.zl_r, v.zl_x}, uni(39, 42), uni(0.93, 0.97));
        const Parts reach{kParts.c1_min * (1 + e.c1), kParts.c1_max * (1 + e.c1), kParts.c2_min * (1 + e.c2),
                          kParts.c2_max * (1 + e.c2), kParts.l_min * (1 + e.l), kParts.l_max * (1 + e.l)};
        const Setting start{uni(kParts.c1_min, kParts.c1_max),
                            kParts.l_min * std::pow(kParts.l_max / kParts.l_min, uni(0, 1)),
                            uni(kParts.c2_min, kParts.c2_max)};
        const bool seeded = uni(0, 1) < 0.5;
        if (!solve(v.mhz * 1e6, z, kParts).ok || !solve(v.mhz * 1e6, z, reach).ok) continue;
        Plant p;
        p.mhz = v.mhz;
        p.z_load = z;
        p.err_c1 = e.c1, p.err_l = e.l, p.err_c2 = e.c2, p.mag_err_db = e.db, p.phs_err_deg = e.deg;
        p.pos = start;
        const char* t = std::getenv("TRACE_CASE");
        p.trace = t && std::atoi(t) == i;
        Tuner tu(config());
        if (seeded) seed_priors(tu);
        const uint32_t t0 = p.now;
        const Outputs o = key(tu, p);
        const bool ok = o.state == State::Matched && p.swr() <= 1.55 && p.violations == 0;
        ++cases;
        matched += ok;
        marginal += ok && p.swr() > 1.25;
        cold += !seeded;
        cold_matched += !seeded && ok;
        violations += p.violations;
        CHECK(ok || !seeded);
        CHECK(ok || o.state == State::Fault);
        worst_attempts = std::max(worst_attempts, o.attempt);
        worst_s = std::fmax(worst_s, (p.now - t0) / 1000.0);
        if (!ok || p.swr() > 1.25)
            std::printf("      #%d %s %.3f MHz %s: %s (%s), attempt %d, SWR %.2f\n", i, v.band, v.mhz,
                        seeded ? "seeded" : "cold", state_name(o.state), fault_name(o.fault), o.attempt, p.swr());
    }
    std::printf("    %d/%d matched, %d/%d of them cold (%d between 1.25 and 1.5 after the last attempt), "
                "worst %d attempts, %.1f s\n",
                matched, cases, cold_matched, cold, marginal, worst_attempts, worst_s);
    CHECK(cold_matched >= 0.99 * cold);
    CHECK(violations == 0);
}

TEST(prior_skips_the_probe_and_a_wrong_one_is_caught) {
    Tuner tu(config());
    Plant p;
    p.load(vec_at(14.0));
    p.err_c1 = 0.03, p.err_l = -0.03;
    CHECK(key(tu, p).state == State::Matched);
    CHECK(p.saw(State::Probe));
    Prior learned;
    CHECK(tu.prior(segment_of(14.0), learned));

    p.mhz = 14.1;                                  // the same segment, from a far setting: no probe
    p.pos = {600 * pF, 2 * uH, 100 * pF};
    p.visited.clear();
    Outputs o = key(tu, p);
    CHECK(o.state == State::Matched && !p.saw(State::Probe) && o.attempt <= 3);

    Tuner wrong(config());                         // the conjugate: the prior's sign is the wrong one
    for (const Vec& v : kVecs) {
        Plant q;
        q.load(v);
        wrong.set_prior(segment_of(v.mhz), {std::conj(cplx(v.r, v.x)), {v.c1, v.l, v.c2}});
        o = key(wrong, q);
        CHECK(o.state == State::Matched && o.attempt <= 3);
        if (o.state != State::Matched) std::printf("    %s %.3f MHz: %s\n", v.band, v.mhz, fault_name(o.fault));
    }
}

TEST(window_and_retune_threshold) {
    Tuner tu(config());
    Plant p;
    p.load(vec_at(14.0));
    CHECK(key(tu, p).state == State::Matched);
    int moves = p.moves;

    detune(p, 1.4);                                // in the window and under 1.5: hold
    p.mhz = 14.05;
    Outputs o = run_for(tu, p, 120);
    CHECK(o.state == State::Matched && p.moves == moves);

    detune(p, 1.6);                                // over 1.5 with a carrier: retune (§8B.2)
    o = run_until(tu, p, [](const Outputs& x, const Plant& q) { return x.state == State::Matched && q.swr() < 1.2; });
    CHECK(o.state == State::Matched && p.moves > moves && p.swr() <= 1.25);
    moves = p.moves;

    p.mhz = 14.2;                                  // out of the window, SWR between 1.2 and 1.5: retune
    detune(p, 1.3);
    CHECK(p.swr() > 1.2 && p.swr() < 1.5);
    o = run_until(tu, p, [](const Outputs& x, const Plant& q) { return x.state == State::Matched && q.swr() < 1.2; });
    CHECK(o.state == State::Matched && p.moves > moves);
}

TEST(manual_request_retunes) {
    Tuner tu(config());
    Plant p;
    p.load(vec_at(7.0));
    CHECK(key(tu, p).state == State::Matched);
    const int moves = p.moves;
    p.tune_request = true;
    run_for(tu, p, 300);
    CHECK(tu.state() == State::Matched && p.moves > moves);
}

TEST(carrier_lost_mid_tune_finishes_the_move_and_holds) {
    Tuner tu(config());
    Plant p;
    p.load(vec_at(3.5));
    p.carrier = false;
    run_for(tu, p, 2);
    p.carrier = true;
    run_until(tu, p, moving);
    const Setting target = p.to;
    p.carrier = false;                             // un-keyed during the move
    Outputs o = run_for(tu, p, 200);
    CHECK(o.state == State::Idle && p.left == 0);
    CHECK(p.pos.c1 == target.c1 && p.pos.l == target.l && p.pos.c2 == target.c2);
    const int moves = p.moves;
    run_for(tu, p, 200);
    CHECK(p.moves == moves && p.violations == 0);
}

TEST(limit_hit_latches_under_strict) {
    Tuner tu(config());
    Plant p;
    p.load(vec_at(21.0));
    p.carrier = false;
    run_for(tu, p, 2);
    p.carrier = true;
    run_until(tu, p, moving);
    p.limit = true;
    Outputs o = p.tick(tu);
    CHECK(o.state == State::Fault && !o.mcu_permit && !o.motion_enable);
    CHECK(tu.faults().latched(Fault::LimitHit));
    p.limit = false;
    p.ack = true;                                  // a remote ACK cannot clear class C
    o = run_for(tu, p, 10);
    CHECK(o.state == State::Fault);
    const int moves = p.moves;
    p.local_clear = true;
    o = run_for(tu, p, 100);                       // cleared, but no re-attempt on the same carrier
    CHECK(o.state == State::Idle && p.moves == moves);
    CHECK(key(tu, p).state == State::Matched);
}

TEST(commissioning_tunes_with_the_vote_withheld) {
    FaultRecord r;
    r.mode = Mode::Commissioning;
    Tuner tu(config(), r);
    Plant p;
    p.load(vec_at(10.1));
    CHECK(key(tu, p).state == State::Matched);
    p.tune_request = true;
    run_until(tu, p, moving);
    p.limit = true;                                // logged, not latched
    Outputs o = p.tick(tu);
    CHECK(o.state == State::Idle && !tu.faults().latched(Fault::LimitHit));
    CHECK(!p.ever_permit && p.violations == 0);
}

TEST(position_faults) {
    Tuner a(config());
    Plant p;
    p.load(vec_at(18.068));
    p.mismatch = true;                             // the encoders disagree once the move stops
    CHECK(key(a, p).state == State::Fault && a.faults().latched(Fault::EncoderMismatch));

    Tuner b(config());
    Plant q;
    q.load(vec_at(18.068));
    q.stall = true;                                // the move never finishes
    const uint32_t t0 = q.now;
    CHECK(key(b, q).state == State::Fault && b.faults().latched(Fault::EncoderMismatch));
    CHECK(q.now - t0 >= 15000 && !q.permit);
}

TEST(no_solution_waits_for_ack_and_the_next_carrier) {
    Tuner tu(config());
    Plant p;
    p.mhz = 1.8;
    p.z_load = {5, -2000};                         // needs ~130 uH
    Outputs o = key(tu, p);
    CHECK(o.state == State::Fault && tu.faults().unacked(Fault::NoSolution) && !o.mcu_permit);
    const int moves = p.moves;
    p.ack = true;
    o = run_for(tu, p, 100);
    CHECK(o.state == State::Idle && p.moves == moves);
    CHECK(key(tu, p).state == State::Fault);
}

TEST(tune_failed_after_three_attempts) {
    Tuner tu(config());
    Plant p;
    p.load(vec_at(24.89));
    p.drift = 0.5;                                 // a load that will not sit still
    const Outputs o = key(tu, p);
    CHECK(o.state == State::Fault && o.fault == Fault::TuneFailed && o.attempt == 3);
    CHECK(tu.faults().unacked(Fault::TuneFailed));
}

TEST(over_swr_trip_matters_only_once_matched) {
    Tuner tu(config());
    Plant p;
    p.load(vec_at(28.0));                          // the comparator trips all through the cold tune
    CHECK(key(tu, p).state == State::Matched);
    detune(p, 2.5);                                // then something happens at the antenna
    Outputs o = p.tick(tu);
    CHECK(o.state == State::Fault && tu.faults().unacked(Fault::OverSwr) && !o.mcu_permit);
    p.ack = true;
    o = run_for(tu, p, 10);
    CHECK(o.state == State::Idle);
}

TEST(over_temperature_inhibits_until_it_clears) {
    Tuner tu(config());
    Plant p;
    p.load(vec_at(5.33));
    CHECK(key(tu, p).state == State::Matched);
    p.over_temp = true;
    Outputs o = p.tick(tu);
    CHECK(o.state == State::Matched && !o.mcu_permit && o.blower_full);
    p.over_temp = false;
    o = p.tick(tu);
    CHECK(o.mcu_permit && !o.blower_full);

    p.over_temp = true;                            // nor does a new tune start while it is hot
    p.carrier = false;
    run_for(tu, p, 2);
    p.carrier = true;
    o = run_for(tu, p, 100);
    CHECK(o.state == State::Idle);
}

TEST(latches_survive_the_power_cycle) {
    FaultRecord r;
    r.latched_c = uint16_t(1u << unsigned(Fault::EncoderMismatch));
    Tuner tu(config(), r);
    Plant p;
    p.load(vec_at(14.0));
    Outputs o = key(tu, p, 200);
    CHECK(o.state == State::Fault && !p.ever_permit && p.moves == 0);
    p.local_clear = true;
    run_for(tu, p, 2);
    CHECK(key(tu, p).state == State::Matched);

    Tuner bad(config());
    Plant q;
    q.self_test_ok = false;
    o = run_for(bad, q, 5);
    CHECK(o.state == State::Fault && bad.faults().latched(Fault::SelfTestFail));
}

TEST(bypass_key_stops_everything) {
    Tuner tu(config());
    Plant p;
    p.load(vec_at(10.15));
    p.bypass = true;                               // the permissive is held up: never move
    Outputs o = key(tu, p, 300);
    CHECK(o.state == State::Idle && p.moves == 0);

    p.bypass = false;
    p.carrier = false;
    run_for(tu, p, 2);
    p.carrier = true;
    run_until(tu, p, moving);
    p.bypass = true;                               // turned mid-move: the move stops, the tune is abandoned
    o = p.tick(tu);
    CHECK(!o.motion_enable && o.state == State::Idle && p.left == 0);
    CHECK(p.violations == 0);
}

TEST(aux_and_cal_paths_never_tune) {
    // §6B.2: off the TUNE path the network is out of circuit; metering and the over-SWR trip stay.
    Tuner tu(config());
    Plant p;
    p.load(vec_at(14.0));
    p.tune_path = false;
    p.trip_swr = 99;                                   // whatever is on AUX is fine, for now
    Outputs o = key(tu, p, 300);
    CHECK(o.state == State::Idle && p.moves == 0 && o.mcu_permit);
    p.trip_swr = 1.0;                                  // the external load or antenna is bad
    o = p.tick(tu);
    CHECK(o.state == State::Fault && tu.faults().unacked(Fault::OverSwr));

    Tuner t2(config());                                // leaving TUNE drops a match and a tune alike
    Plant q;
    q.load(vec_at(14.0));
    CHECK(key(t2, q).state == State::Matched);
    q.tune_path = false;
    CHECK(q.tick(t2).state == State::Idle);
}

TEST(relay_mismatch_is_class_b) {
    Tuner tu(config());
    Plant p;
    run_for(tu, p, 3);
    p.relay_mismatch = true;
    Outputs o = p.tick(tu);
    CHECK(o.state == State::Fault && tu.faults().unacked(Fault::RelayMismatch) && !o.mcu_permit);
    p.ack = true;
    CHECK(run_for(tu, p, 5).state == State::Idle);
}

TEST(jog_moves_under_the_ptt_rules) {
    // §7.5 manual override: one move, the vote down 30 ms first, back to IDLE, never under bypass.
    Tuner tu(config());
    Plant p;
    p.carrier = false;
    run_for(tu, p, 5);
    const Setting to{200e-12, 3e-6, 400e-12};
    p.jog = true;
    p.jog_target = to;
    Outputs o = p.tick(tu);
    CHECK(o.state == State::Move && !o.mcu_permit);
    o = run_until(tu, p, [](const Outputs& x, const Plant& q) { return x.state == State::Idle && q.left == 0; });
    CHECK(o.state == State::Idle && p.moves == 1 && p.violations == 0);
    CHECK(p.pos.c1 == to.c1 && p.pos.l == to.l && p.pos.c2 == to.c2);
    p.bypass = true;
    p.jog = true;
    p.jog_target = Setting{100e-12, 2e-6, 300e-12};
    run_for(tu, p, 50);
    CHECK(p.moves == 1);
}
