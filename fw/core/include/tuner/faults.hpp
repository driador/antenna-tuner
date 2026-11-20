// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Fault classes, the mechanical-fault policy and what survives a power cycle (§8B.4 to §8B.4b).
//   A self-clearing   resolves on hysteresis
//   B acknowledge     operator ACK from either end
//   C latched         deliberate clear at the box only (§8B.4f); never by a power cycle
#pragma once
#include <cstdint>

namespace tuner {

enum class Fault : uint8_t {
    OverTemp,         // A: blower to full, PTT off until it clears
    CarrierLost,      // A: abort to IDLE, hold position; not really a fault
    NoSolution,       // B: stay put, inhibit; usually the wrong band or the antenna
    TuneFailed,       // B: 3 attempts without converging
    OverSwr,          // B: the hardware comparator dropped PTT in transmit
    LimitHit,         // mechanical: by mode
    EncoderMismatch,  // mechanical: by mode
    SelfTestFail,     // C, always
    RelayMismatch,    // B: K1/K2 did not do what was commanded (§6B.2)
    Count
};

enum class FaultClass : uint8_t { None, A, B, C };
enum class Mode : uint8_t { Commissioning, Strict, Permissive };   // §8B.4a-1; STRICT is the default

const char* fault_name(Fault f);

// What goes to NVRAM (§8B.4b). Event faults are restored; condition faults (over-temperature, over-SWR)
// are measured again instead, and the mode survives with them.
struct FaultRecord {
    uint16_t latched_c = 0;       // bit per Fault
    uint16_t unacked_b = 0;
    Mode mode = Mode::Strict;
};

class FaultPolicy {
public:
    explicit FaultPolicy(Mode m = Mode::Strict) : mode_(m) {}

    // Raise an event fault; returns the class it took under the present mode.
    FaultClass raise(Fault f);
    // Condition faults (class A) follow their condition, with the hysteresis applied by the caller.
    void condition(Fault f, bool active);

    void ack();                   // remote or local ACK: clears class B, never C
    void clear_local();           // at the box, after a look: clears B and C (§8B.4f)
    void new_session();           // PERMISSIVE counts repeats per powered session

    // Mode changes are local-only and logged by the caller; a class C latch while PERMISSIVE drops the
    // policy back to STRICT by itself (§8B.4a-1).
    void set_mode(Mode m) { mode_ = m; }
    Mode mode() const { return mode_; }

    // Every raise() counts, including the ones COMMISSIONING only logs; the counts are for the fault
    // log and the PERMISSIVE qualification, and start at zero each boot.
    uint16_t raised(Fault f) const { return raised_[unsigned(f)]; }

    bool latched(Fault f) const { return latched_c_ & mask(f); }
    bool unacked(Fault f) const { return unacked_b_ & mask(f); }
    bool active(Fault f) const { return active_a_ & mask(f); }
    bool any_blocking() const;    // a C latch, an unacknowledged B, or an active over-temperature
    // The MCU's vote in the hardware permissive must be withheld (COMMISSIONING always withholds it).
    bool transmit_inhibited() const { return mode_ == Mode::Commissioning || any_blocking(); }
    bool blower_full() const { return active(Fault::OverTemp); }

    FaultRecord persist() const;
    void restore(const FaultRecord& r);

private:
    static uint16_t mask(Fault f) { return uint16_t(1u << unsigned(f)); }
    Mode mode_;
    uint16_t latched_c_ = 0, unacked_b_ = 0, active_a_ = 0;
    uint8_t mechanical_this_session_ = 0;
    uint16_t raised_[unsigned(Fault::Count)] = {};
};

}  // namespace tuner
