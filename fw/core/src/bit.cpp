// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/bit.hpp"

#include <cmath>
#include <cstdio>

#include "tuner/pins.hpp"

namespace tuner::bit {

namespace {
const char* const kNames[] = {"expander",       "encoders",      "bridge reference",      "limits",
                              "permit stuck high", "fault record", "bridge idle",       "forward detector idle",
                              "cal-load detector idle", "thermistor", "C1 axis",         "C2 axis",
                              "roller axis",    "K1",            "K2",                    "hold latch",
                              "permit rise"};
static_assert(sizeof kNames / sizeof kNames[0] == unsigned(Check::Count), "a name for every check");

const Path kRelaySteps[] = {Path::Aux, Path::Cal, Path::Tune};

bool inside(double v, double lo, double hi) { return v >= lo && v <= hi; }   // NaN is outside

// Which relay a failed step names: AUX proves K1, CAL then K2, and the way back to TUNE either.
uint32_t relay_checks(int step) {
    return step == 0 ? mask(Check::RelayK1) : step == 1 ? mask(Check::RelayK2)
                                                        : mask(Check::RelayK1) | mask(Check::RelayK2);
}
}  // namespace

Grade grade(Check c) {
    switch (c) {
        case Check::BridgeIdle:
        case Check::FwdIdle:
        case Check::CalIdle:
        case Check::RelayK1:
        case Check::RelayK2:
            return Grade::B;
        case Check::AxisC1:
        case Check::AxisC2:
        case Check::AxisL:
            return Grade::Mechanical;
        case Check::Thermistor:
        case Check::PermitRise:
            return Grade::Warn;
        default:
            return Grade::C;   // the original passive checks, and the hold latch
    }
}

const char* name(Check c) { return unsigned(c) < unsigned(Check::Count) ? kNames[unsigned(c)] : "?"; }

Fault fault_of(Check c) {
    switch (grade(c)) {
        case Grade::C: return Fault::SelfTestFail;
        case Grade::Mechanical: return Fault::EncoderMismatch;
        case Grade::B: return c == Check::RelayK1 || c == Check::RelayK2 ? Fault::RelayMismatch : Fault::BuiltInTest;
        case Grade::Warn: break;
    }
    return Fault::Count;
}

uint32_t behind(uint32_t failed, Fault f) {
    if (f == Fault::LimitHit) f = Fault::EncoderMismatch;
    uint32_t m = 0;
    for (unsigned i = 0; i < unsigned(Check::Count); ++i)
        if (fault_of(Check(i)) == f) m |= mask(Check(i));
    return failed & m;
}

size_t names(uint32_t m, char out[], size_t cap) {
    if (cap == 0) return 0;
    size_t n = 0;
    out[0] = 0;
    for (unsigned i = 0; i < unsigned(Check::Count) && n + 1 < cap; ++i)
        if (m & mask(Check(i))) n += size_t(std::snprintf(out + n, cap - n, "%s%s", n ? ", " : "", kNames[i]));
    return n < cap ? n : cap - 1;
}

const char* permit_blocker(uint16_t iox_word) {
    namespace iox = pins::iox;
    // The inputs first, then the gates: BYP_OK is SWR_OK and the vote, HARD_OK the four never bypassed,
    // and the permit both (board_control.py, §7.4).
    struct Term {
        uint8_t bit;
        const char* name;
    };
    static const Term kTerms[] = {{iox::SWR_OK, "SWR_OK"},       {iox::CALDET_OK, "CALDET_OK"},
                                  {iox::CALTH_OK, "CALTH_OK"},   {iox::PANEL_OK, "PANEL_OK"},
                                  {iox::LIMIT_OK, "LIMIT_OK"},   {iox::BYP_OK, "BYP_OK (vote gate)"},
                                  {iox::HARD_OK, "HARD_OK (gate)"}};
    for (const Term& t : kTerms)
        if (!(iox_word & (1u << t.bit))) return t.name;
    return nullptr;
}

uint32_t rest_checks(const Rest& r, const Windows& w) {
    uint32_t f = 0;
    if (!inside(r.v_mag, w.mag_lo, w.mag_hi) || !inside(r.v_phs, w.phs_lo, w.phs_hi)) f |= mask(Check::BridgeIdle);
    if (!(r.v_fwd < w.fwd_max)) f |= mask(Check::FwdIdle);
    if (!inside(r.v_cal, w.cal_lo, w.cal_hi)) f |= mask(Check::CalIdle);
    // An open or shorted thermistor reads NaN and is already an over-temperature; this catches a drifted one.
    if (!std::isnan(r.tank_c) && !inside(r.tank_c, w.tank_lo, w.tank_hi)) f |= mask(Check::Thermistor);
    return f;
}

void Active::start(uint32_t now_ms, const Windows& w) {
    phase_ = Phase::Wait;
    windows_ = w;
    t0_ = now_ms;
    failed_ = untested_ = 0;
    completed_ = false;
    issued_ = false;
}

void Active::end(bool completed) {
    phase_ = Phase::Idle;
    completed_ = completed;
    issued_ = false;
}

void Active::stop(const In& in) {
    // Conditions turned unsafe, or a request was refused: stop, and put the path back to TUNE once the
    // relays may move again.
    if (in.path == Path::Tune) {
        end(false);
    } else {
        phase_ = Phase::Restore;
        issued_ = false;
    }
}

Active::Out Active::step(const In& in) {
    Out o;
    if (phase_ == Phase::Idle) return o;
    // A fault the run raised is its result; the state machine or the path switch has already acted on it.
    if (phase_ == Phase::Axis && in.axis_fault) {
        failed_ |= mask(Check(unsigned(Check::AxisC1) + axis_));
        end(true);
        return o;
    }
    if (phase_ == Phase::Relay && in.relay_fault) {
        failed_ |= relay_checks(relay_);
        end(true);
        return o;
    }
    if (!in.safe && phase_ != Phase::Wait && phase_ != Phase::Restore) {
        stop(in);
        if (phase_ == Phase::Idle) return o;
    }

    switch (phase_) {
        case Phase::Wait:
            if (in.safe && in.clear && in.quiet && in.path == Path::Tune) {
                failed_ = rest_checks(in.rest, windows_);   // the detectors with no RF, before anything moves
                phase_ = Phase::Axis;
                axis_ = leg_ = 0;
                issued_ = false;
            } else if (in.now_ms - t0_ > kStartMs) {
                end(false);
            }
            break;

        case Phase::Axis:                   // one turn away from the nearer end, then back
            if (!issued_) {
                if (!in.quiet) break;
                if (leg_ == 0) dir_ = in.turns[axis_] < in.travel[axis_] / 2 ? +1 : -1;
                o.jog_axis = axis_;
                o.jog_turns = (leg_ == 0 ? dir_ : -dir_) * kTurns;
                issued_ = true;
                busy_seen_ = false;
                t0_ = in.now_ms;
                break;
            }
            if (!in.quiet) {
                busy_seen_ = true;
                break;
            }
            if (!busy_seen_) {               // nothing moved: the jog was refused
                if (in.now_ms - t0_ > kGraceMs) stop(in);
                break;
            }
            issued_ = false;
            if (++leg_ == 2) {
                leg_ = 0;
                if (++axis_ == 3) {
                    phase_ = Phase::Relay;
                    relay_ = 0;
                }
            }
            break;

        case Phase::Relay: {                // AUX, CAL, then TUNE again (§5.5, each confirmed by coil current)
            const Path want = kRelaySteps[relay_];
            if (!issued_) {
                if (!in.quiet) break;
                o.path_request = true;
                o.path = want;
                issued_ = true;
                busy_seen_ = false;
                t0_ = in.now_ms;
                break;
            }
            if (!in.quiet) {
                busy_seen_ = true;
                break;
            }
            if (!busy_seen_) {
                if (in.now_ms - t0_ > kGraceMs) stop(in);
                break;
            }
            issued_ = false;
            if (in.path != want) {
                failed_ |= relay_checks(relay_);
                end(true);
            } else if (++relay_ == 3) {
                phase_ = Phase::Latch;
                driving_ = false;
                t0_ = in.now_ms;
            }
            break;
        }

        case Phase::Latch:                  // the permit up: K1 driven, and the latch must hold it off
            if (!(in.vote && in.permit)) {
                if (driving_) {             // the permit fell: let go before the latch opens (39 ms, §5.5)
                    untested_ |= mask(Check::Latch);
                    phase_ = Phase::LatchOff;
                    t0_ = in.now_ms;
                } else if (in.now_ms - t0_ >= kLatchMs) {   // it follows the vote within a tick or two
                    untested_ |= mask(Check::Latch);
                    if (in.vote) failed_ |= mask(Check::PermitRise);
                    else untested_ |= mask(Check::PermitRise);
                    end(true);
                }
                break;
            }
            if (!driving_) {
                driving_ = true;
                t0_ = in.now_ms;
            }
            o.drive_k1 = true;
            if (in.now_ms - t0_ >= kLatchMs) {
                if (in.k1_current) failed_ |= mask(Check::Latch);
                phase_ = Phase::LatchOff;
                t0_ = in.now_ms;
            }
            break;

        case Phase::LatchOff:               // let a coil that wrongly drew let go
            if (in.now_ms - t0_ >= kLatchMs) end(true);
            break;

        case Phase::Restore:
            if (in.path == Path::Tune) {
                end(false);
                break;
            }
            if (!issued_) {
                if (!in.quiet || !in.safe) break;   // the path switch refuses under RF anyway
                o.path_request = true;
                o.path = Path::Tune;
                issued_ = true;
                busy_seen_ = false;
                t0_ = in.now_ms;
                break;
            }
            if (!in.quiet) {
                busy_seen_ = true;
                break;
            }
            if (busy_seen_ || in.now_ms - t0_ > kGraceMs) issued_ = false;   // done or refused: look again
            break;

        case Phase::Idle:
            break;
    }
    return o;
}

}  // namespace tuner::bit
