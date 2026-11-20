// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The three axes (§7.1, §7.2, §8B.3): AS5048A encoders on SPI, step and direction pulses from a 50 kHz
// timer interrupt following a tuner::MovePlan, one enable line for the drivers. The encoders are the
// truth: every move starts from them and ends with them checked against the steps sent.
#pragma once
#include <cstdint>

#include "tuner/tnet.hpp"

namespace hw {

class Motion {
public:
    bool begin();                          // SPI, the step timer, a first read; false if an encoder fails
    bool read_encoders();                  // false if any reply fails parity or carries the error flag
    bool magnets_ok();                     // AS5048A diagnostics: offset compensated, field in range
    double turns(int axis) const { return turns_[axis]; }   // from the low end, by the encoder
    uint16_t raw(int axis) const { return raw_[axis]; }
    tuner::Setting position() const;       // the elements now, through their curves
    tuner::Parts parts() const;            // what they can reach inside the soft limits

    // One coordinated move to target, clamped to the soft limits. A move that cannot start reports
    // itself done at once with the mismatch flag set, so the state machine faults instead of waiting.
    void start(uint32_t id, const tuner::Setting& target, uint32_t now_ms);
    // Runs the move's phases. enable false stops a move in progress, ramping down (Outputs::motion_enable).
    void service(uint32_t now_ms, bool enable);

    bool busy() const { return phase_ != Phase::Idle; }
    uint32_t done_id() const { return done_id_; }
    bool mismatch() const { return mismatch_; }
    uint32_t stopped_ms() const { return stopped_ms_; }   // when the last move finished, verify included

private:
    enum class Phase : uint8_t { Idle, Waking, Running, Settling };
    void finish(uint32_t now_ms, bool mismatch);

    double turns_[3] = {};
    uint16_t raw_[3] = {};
    Phase phase_ = Phase::Idle;
    uint32_t id_ = 0, done_id_ = 0, phase_ms_ = 0, stopped_ms_ = 0;
    bool mismatch_ = false;
};

}  // namespace hw
