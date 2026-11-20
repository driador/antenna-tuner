// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/faults.hpp"

namespace tuner {

namespace {
bool condition_based(Fault f) { return f == Fault::OverTemp || f == Fault::OverSwr || f == Fault::CarrierLost; }
}  // namespace

const char* fault_name(Fault f) {
    switch (f) {
        case Fault::OverTemp: return "over-temperature";
        case Fault::CarrierLost: return "carrier lost";
        case Fault::NoSolution: return "no feasible solution";
        case Fault::TuneFailed: return "tune failed after 3 attempts";
        case Fault::OverSwr: return "over-SWR trip";
        case Fault::LimitHit: return "limit switch hit";
        case Fault::EncoderMismatch: return "encoder / position mismatch";
        case Fault::SelfTestFail: return "self-test failure";
        case Fault::RelayMismatch: return "K1/K2 relay mismatch";
        default: return "?";
    }
}

FaultClass FaultPolicy::raise(Fault f) {
    if (f < Fault::Count) ++raised_[unsigned(f)];
    switch (f) {
        case Fault::OverTemp:
        case Fault::CarrierLost:
            condition(f, true);
            return FaultClass::A;
        case Fault::NoSolution:
        case Fault::TuneFailed:
        case Fault::OverSwr:
        case Fault::RelayMismatch:
            unacked_b_ |= mask(f);
            return FaultClass::B;
        case Fault::SelfTestFail:
            latched_c_ |= mask(f);
            return FaultClass::C;
        case Fault::LimitHit:
        case Fault::EncoderMismatch:
            switch (mode_) {
                case Mode::Commissioning:          // logged by the caller, never latched; PTT stays off
                    return FaultClass::None;
                case Mode::Strict:
                    latched_c_ |= mask(f);
                    return FaultClass::C;
                case Mode::Permissive:
                    if (mechanical_this_session_++ == 0) {   // first: remote ACK and re-home
                        unacked_b_ |= mask(f);
                        return FaultClass::B;
                    }
                    latched_c_ |= mask(f);          // a repeat escalates, and proven hardware that has
                    mode_ = Mode::Strict;          // started misbehaving tightens up by itself
                    return FaultClass::C;
            }
            break;
        default:
            break;
    }
    return FaultClass::None;
}

void FaultPolicy::condition(Fault f, bool on) {
    if (on) active_a_ |= mask(f);
    else active_a_ &= uint16_t(~mask(f));
}

void FaultPolicy::ack() { unacked_b_ = 0; }

void FaultPolicy::clear_local() {
    unacked_b_ = 0;
    latched_c_ = 0;
}

void FaultPolicy::new_session() { mechanical_this_session_ = 0; }

bool FaultPolicy::any_blocking() const {
    return latched_c_ != 0 || unacked_b_ != 0 || active(Fault::OverTemp);
}

FaultRecord FaultPolicy::persist() const {
    FaultRecord r;
    r.latched_c = latched_c_;
    r.unacked_b = unacked_b_;
    for (unsigned i = 0; i < unsigned(Fault::Count); ++i)       // conditions are re-measured, not restored
        if (condition_based(Fault(i))) r.unacked_b &= uint16_t(~(1u << i));
    r.mode = mode_;
    return r;
}

void FaultPolicy::restore(const FaultRecord& r) {
    latched_c_ = r.latched_c;
    unacked_b_ = r.unacked_b;
    mode_ = r.mode;
    active_a_ = 0;
    mechanical_this_session_ = 0;
}

}  // namespace tuner
