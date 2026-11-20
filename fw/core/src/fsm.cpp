// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/fsm.hpp"

#include <cmath>

namespace tuner {

const char* state_name(State s) {
    switch (s) {
        case State::SelfTest: return "SELF-TEST";
        case State::Idle: return "IDLE";
        case State::Measure: return "MEASURE";
        case State::Probe: return "PROBE";
        case State::Solve: return "SOLVE";
        case State::Move: return "MOVE";
        case State::Verify: return "VERIFY";
        case State::Matched: return "MATCHED";
        case State::Fault: return "FAULT";
    }
    return "?";
}

namespace {
constexpr double kAtSetting = 0.01;   // within 1 % of every axis's range: already there
constexpr double kDecisive = 0.5;     // a prior decides the sign when one hypothesis is this much nearer
constexpr double kSignMatters = 0.05; // below this |Gamma+ - Gamma-| the sign makes no difference
constexpr double kWorse = 2.0;        // a move that multiplies the best SWR by this has gone the wrong way

double swr_of(const Measurement& m) { return swr_from_mag(m.gamma.mag); }

bool sign_matters(const GammaReading& g) {
    return 2 * g.mag * std::sin(g.theta_deg * 3.14159265358979323846 / 180) >= kSignMatters;
}
}  // namespace

Tuner::Tuner(const Config& c, const FaultRecord& restored) : cfg_(c), faults_(restored.mode) {
    faults_.restore(restored);
    faults_.new_session();
}

void Tuner::set_prior(int seg, const Prior& p) {
    if (seg < 0 || seg >= kSegments) return;
    prior_[seg] = p;
    prior_ok_[seg] = true;
}

bool Tuner::prior(int seg, Prior& p) const {
    if (seg < 0 || seg >= kSegments || !prior_ok_[seg]) return false;
    p = prior_[seg];
    return true;
}

bool Tuner::prior_near(double mhz, Prior& p) const {
    // This segment's, else the nearer neighbor's on the same band.
    const int seg = segment_of(mhz);
    if (seg < 0) return false;
    if (prior(seg, p)) return true;
    int best = -1;
    for (int n : {seg - 1, seg + 1}) {
        if (n < 0 || n >= kSegments || !prior_ok_[n] || band_of_segment(n) != band_of_segment(seg)) continue;
        if (best < 0 || std::fabs(segment_center(n) - mhz) < std::fabs(segment_center(best) - mhz)) best = n;
    }
    return prior(best, p);
}

int Tuner::prior_sign(const Measurement& m, const Setting& at, const Prior& p) {
    // The hypothesis whose load is clearly nearer the prior's, or 0 when neither is or the prior has
    // already had its say this tune: a wrong prior must not steer twice.
    if (!sign_matters(m.gamma)) return +1;
    if (prior_used_) return 0;
    prior_used_ = true;
    const double dp = std::abs(load_estimate(m, +1, at) - p.z_load), dn = std::abs(load_estimate(m, -1, at) - p.z_load);
    if (dp < kDecisive * dn) return +1;
    if (dn < kDecisive * dp) return -1;
    return 0;
}

void Tuner::start_probe() {
    // Step C2 the way that stays in range; m_ and at_ are the reading and setting before the step.
    enter(State::Probe);
    move_target_ = at_;
    const double up = at_.c2 * (1 + cfg_.probe_step);
    move_target_.c2 = up <= cfg_.parts.c2_max ? up : at_.c2 * (1 - cfg_.probe_step);
    move_pending_ = true;
}

void Tuner::enter(State s) {
    if (s != State::Move) jogging_ = false;
    state_ = s;
    probed_ = false;
    move_pending_ = false;
    move_issued_ = false;
    if (s == State::Idle) armed_ = false;
    if (s == State::Fault) pending_request_ = false;
}

void Tuner::fault(Fault f) {
    out_.fault = f;
    // COMMISSIONING logs a mechanical fault without latching it; the permit is withheld in that mode
    // anyway, so stop and hold in IDLE.
    enter(faults_.raise(f) == FaultClass::None ? State::Idle : State::Fault);
}

cplx Tuner::load_estimate(const Measurement& m, int sign, const Setting& at) const {
    GammaReading g = m.gamma;                // at the top of the range the reading says little about R
    g.mag = std::fmin(g.mag, cfg_.gamma_ceiling);
    return load_from_input(m.mhz * 1e6, at, z_from_gamma(gamma_of(g, sign)));
}

int Tuner::resolve_sign(const Measurement& m0, const Setting& p0, const Measurement& m1, const Setting& p1) const {
    // Two readings of one load at two settings (§6A.7 option 1). Each hypothesis for the first predicts
    // what the bridge should read at the second; the closest prediction names the second's sign.
    const double f = m1.mhz * 1e6;
    double best = HUGE_VAL;
    int sign = +1;
    for (int h0 : {+1, -1}) {
        const cplx predicted = gamma_from_z(input_impedance(f, p1, load_estimate(m0, h0, p0)));
        for (int h1 : {+1, -1}) {
            const double d = std::abs(predicted - gamma_of(m1.gamma, h1));
            if (d < best) {
                best = d;
                sign = h1;
            }
        }
    }
    return sign;
}

void Tuner::begin_tune(const Inputs& in) {
    // MEASURE's decision (§8B.1, §8B.2), from MEASURE or from MATCHED when a retune is due.
    const double swr = swr_from_mag(in.m.gamma.mag);
    const bool valid = solved_ && solution_valid(solved_mhz_, in.m.mhz, cfg_.window_frac);
    if (!pending_request_ && (swr <= cfg_.match_swr || (valid && swr <= cfg_.retune_swr))) {
        if (!valid) {                       // matched here as it stands: the window follows
            solved_mhz_ = in.m.mhz;
            solved_ = true;
        }
        enter(State::Matched);
        return;
    }
    pending_request_ = false;
    m_ = in.m;
    at_ = in.position;
    best_m_ = m_;
    best_at_ = at_;
    attempts_ = 0;
    coarse_ = 0;
    prior_used_ = false;
    Prior p;
    const bool have = prior_near(in.m.mhz, p);
    if (have && swr > cfg_.trust_swr && setting_distance(at_, p.at, cfg_.parts) > kAtSetting) {
        enter(State::Move);                 // too far off to measure: the stored setting first, as a coarse move
        ++coarse_;
        move_target_ = p.at;
        move_pending_ = true;
        return;
    }
    const int s = !sign_matters(m_.gamma) ? +1 : have ? prior_sign(m_, at_, p) : 0;
    if (s == 0) {
        start_probe();
        return;
    }
    sign_ = s;
    enter(State::Solve);
}

void Tuner::note_best(const Measurement& m, const Setting& at) {
    if (swr_of(m) >= swr_of(best_m_)) return;
    best_m_ = m;
    best_at_ = at;
}

bool Tuner::run_move(const Inputs& in) {
    // One requested move: the permit is already down; wait out the RF decay, issue the move, and
    // report true once it has stopped where it was sent.
    if (!move_issued_) {
        if (permit_up_ || in.now_ms - permit_down_ms_ < cfg_.rf_decay_ms) return false;
        ++out_.move_id;
        out_.target = move_target_;
        move_issued_ = true;
        move_started_ms_ = in.now_ms;
        return false;
    }
    if (in.move_done != out_.move_id) {
        if (in.now_ms - move_started_ms_ > cfg_.move_timeout_ms) fault(Fault::EncoderMismatch);
        return false;
    }
    move_pending_ = false;
    if (in.encoder_mismatch) {
        fault(Fault::EncoderMismatch);
        return false;
    }
    return true;
}

Outputs Tuner::step(const Inputs& in) {
    // Conditions and operator actions that apply in every state.
    faults_.condition(Fault::OverTemp, in.over_temp);
    if (in.ack) faults_.ack();
    if (in.local_clear) faults_.clear_local();
    if (in.tune_request) pending_request_ = true;
    // A trip while tuning is expected: the tune starts from a mismatch and the comparator keeps the
    // amplifier off meanwhile. A trip once MATCHED, or on the AUX or CAL path, is §8B.4's over-SWR in
    // transmit.
    if ((state_ == State::Matched || !in.tune_path) && in.swr_trip && permit_up_) fault(Fault::OverSwr);
    if (in.relay_mismatch && state_ != State::SelfTest) fault(Fault::RelayMismatch);
    if (state_ != State::SelfTest && state_ != State::Fault && in.limit_hit && !limit_was_hit_)
        fault(Fault::LimitHit);
    limit_was_hit_ = in.limit_hit;
    // The bypass key holds the permissive up, so nothing may move: abandon a tune and hold (§8B.4d). Off
    // the TUNE path the network is out of circuit, so a tune means nothing there either.
    const bool tuning = state_ == State::Measure || state_ == State::Probe || state_ == State::Move ||
                        state_ == State::Verify || state_ == State::Matched;
    if ((in.bypass && tuning && state_ != State::Matched) || (!in.tune_path && tuning && !jogging_))
        enter(State::Idle);

    switch (state_) {
        case State::SelfTest:
            if (!in.self_test_ok) fault(Fault::SelfTestFail);
            else if (faults_.any_blocking()) enter(State::Fault);   // restored from NVRAM (§8B.4b)
            else enter(State::Idle);
            break;

        case State::Idle:
            // Every tune starts on a fresh key-down: after a fault clears, "re-attempt on next carrier".
            if (in.jog && !in.bypass && !faults_.any_blocking()) {
                enter(State::Move);
                jogging_ = true;
                move_target_ = in.jog_target;
                move_pending_ = true;
            } else if (!in.carrier) {
                armed_ = true;
            } else if (armed_ && in.tune_path && !in.bypass && !in.limit_hit && !faults_.any_blocking()) {
                enter(State::Measure);
            }
            break;

        case State::Measure:
            if (!in.carrier) enter(State::Idle);                    // carrier lost: hold position
            else if (in.have_measurement) begin_tune(in);
            break;

        case State::Probe:
            if (!probed_) {
                probed_ = run_move(in);                             // a move finishes regardless of carrier
            } else if (!in.carrier) {
                enter(State::Idle);
            } else if (in.have_measurement) {
                sign_ = resolve_sign(m_, at_, in.m, in.position);
                note_best(in.m, in.position);
                m_ = in.m;
                at_ = in.position;
                enter(State::Solve);
            }
            break;

        case State::Move:
            if (run_move(in)) enter(jogging_ ? State::Idle : State::Verify);
            break;

        case State::Verify:
            if (!in.carrier) {
                enter(State::Idle);
            } else if (in.have_measurement) {
                // The move itself is the probe: the readings before and after it fix the sign. A reading
                // from too far off predicts nothing, so after a coarse move the prior decides if it can,
                // and PROBE if it cannot.
                Prior p;
                const int s = !sign_matters(in.m.gamma) ? +1
                              : swr_from_mag(m_.gamma.mag) <= cfg_.trust_swr
                                  ? resolve_sign(m_, at_, in.m, in.position)
                                  : prior_near(in.m.mhz, p) ? prior_sign(in.m, in.position, p) : 0;
                // Converged; or out of attempts but under the retune threshold, which §8B.2 would not
                // retune anyway, so it is used rather than faulted.
                const bool done = attempts_ >= cfg_.max_attempts;
                const bool worse = swr_of(in.m) > cfg_.trust_swr && swr_of(in.m) > kWorse * swr_of(best_m_);
                note_best(in.m, in.position);
                if (swr_of(in.m) <= cfg_.match_swr || (done && swr_of(in.m) <= cfg_.retune_swr)) {
                    solved_mhz_ = in.m.mhz;
                    solved_ = true;
                    set_prior(segment_of(in.m.mhz), {load_estimate(in.m, s ? s : +1, in.position), in.position});
                    enter(State::Matched);
                } else if (done) {
                    fault(Fault::TuneFailed);
                } else if (worse && coarse_ < cfg_.max_coarse) {
                    // Much worse, and too far off to refine from: back to the best setting seen, with the
                    // probe's C2 step folded into the same move.
                    ++coarse_;
                    m_ = best_m_;
                    at_ = best_at_;
                    start_probe();
                } else {
                    m_ = in.m;
                    at_ = in.position;
                    if (s == 0) {
                        start_probe();
                    } else {
                        sign_ = s;
                        enter(State::Solve);
                    }
                }
            }
            break;

        case State::Matched:
            if (!in.carrier) {
                enter(State::Idle);
            } else if (in.have_measurement && !in.bypass) {
                const bool valid = solution_valid(solved_mhz_, in.m.mhz, cfg_.window_frac);
                if (pending_request_ || !valid || swr_from_mag(in.m.gamma.mag) > cfg_.retune_swr) begin_tune(in);
            }
            break;

        case State::Fault:
            if (!faults_.any_blocking()) enter(State::Idle);
            break;

        case State::Solve:
            break;
    }

    // SOLVE is immediate: the closed form, then MOVE in the same tick.
    if (state_ == State::Solve) {
        const bool coarse = swr_of(m_) > cfg_.trust_swr && coarse_ < cfg_.max_coarse;
        SolveOptions o;
        o.near_tolerance = cfg_.near_tolerance;
        o.from = &at_;
        last_load_ = load_estimate(m_, sign_, at_);
        Solution sol = solve(m_.mhz * 1e6, last_load_, cfg_.parts, o);
        if (!sol.ok && sign_matters(m_.gamma)) {   // a wrong sign can ask the impossible: try the other
            sign_ = -sign_;
            last_load_ = load_estimate(m_, sign_, at_);
            sol = solve(m_.mhz * 1e6, last_load_, cfg_.parts, o);
        }
        if (!sol.ok && coarse) {
            // Nothing fits a reading this far off, which proves little: back to the best setting seen
            // and probe from there.
            ++coarse_;
            m_ = best_m_;
            at_ = best_at_;
            start_probe();
        } else if (!sol.ok) {
            fault(Fault::NoSolution);
        } else {
            if (coarse) ++coarse_;
            else ++attempts_;
            enter(State::Move);
            move_target_ = sol.s;
            move_pending_ = true;
        }
    }

    // PTT is down for every move and the probe around it (§8B.3), in FAULT, and whenever the fault
    // policy withholds it. A move goes out only after the vote has been down rf_decay_ms (run_move).
    // It also stays down until the motion layer reports the last move stopped, so a tune abandoned
    // mid-move never raises it over a moving roller.
    const bool permit = state_ != State::SelfTest && state_ != State::Fault && state_ != State::Probe &&
                        state_ != State::Move && in.move_done == out_.move_id && !faults_.transmit_inhibited();
    if (permit_up_ && !permit) permit_down_ms_ = in.now_ms;
    permit_up_ = permit;

    out_.state = state_;
    out_.mcu_permit = permit;
    out_.motion_enable = move_pending_ && move_issued_ && !in.bypass;
    out_.blower_full = faults_.blower_full();
    out_.attempt = attempts_;
    return out_;
}

}  // namespace tuner
