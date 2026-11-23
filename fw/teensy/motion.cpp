// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "motion.hpp"

#include <Arduino.h>
#include <SPI.h>

#include <cmath>

#include "board.hpp"
#include "config.hpp"
#include "tuner/as5048.hpp"
#include "tuner/curve.hpp"
#include "tuner/motion.hpp"
#include "tuner/pins.hpp"

namespace pins = tuner::pins;
namespace as = tuner::as5048;

namespace hw {

namespace {
const SPISettings kEncoderSpi(1000000, MSBFIRST, SPI_MODE1);   // AS5048A: mode 1, up to 10 MHz
constexpr double kDt = 1.0 / kStepIsrHz;

// Shared with the step interrupt. The plan and directions are written only while g_run is false.
tuner::MovePlan g_plan;
tuner::MoveExecutor g_exec;
volatile bool g_run = false, g_stop = false;
volatile int32_t g_pos[3];        // step position from the low end of travel
int32_t g_dir[3];
bool g_high[3];
IntervalTimer g_timer;

void step_isr() {
    // A pulse is high for one tick and low for at least one: 20 us each, against the DM542T's 2.5 us.
    bool lowered[3];
    for (int i = 0; i < 3; ++i) {
        lowered[i] = g_high[i];
        if (g_high[i]) {
            digitalWriteFast(pins::STEP[i], LOW);
            g_high[i] = false;
        }
    }
    if (!g_run) return;
    if (g_stop) g_exec.stop();
    const double s = g_exec.advance(kDt);
    bool arrived = !g_exec.running();
    for (int i = 0; i < 3; ++i) {
        const int32_t want = g_plan.start(i) + int32_t(std::lround(g_plan.delta(i) * s));
        if (want == g_pos[i]) continue;
        arrived = false;
        if (lowered[i]) continue;
        digitalWriteFast(pins::STEP[i], HIGH);
        g_high[i] = true;
        g_pos[i] = g_pos[i] + g_dir[i];
    }
    if (arrived) g_run = false;
}

uint16_t transfer(int axis, uint16_t command) {
    SPI.beginTransaction(kEncoderSpi);
    digitalWriteFast(pins::ENC_CS[axis], LOW);
    const uint16_t reply = SPI.transfer16(command);
    digitalWriteFast(pins::ENC_CS[axis], HIGH);
    SPI.endTransaction();
    delayNanoseconds(400);                                     // CSn high at least 350 ns between frames
    return reply;
}

// The encoder's count as element turns from the low end. The part of the encoder's turn that the
// element never uses is split between the ends, so a reading just past either end stays near it.
double counts_to_turns(int axis, uint16_t raw) {
    const Axis& a = kAxes[axis];
    int32_t rel = (int32_t(raw) - int32_t(a.enc_zero)) * a.enc_sign;
    rel = ((rel % as::kCounts) + as::kCounts) % as::kCounts;
    double t = rel * a.reduction / as::kCounts;
    if (t > a.full_turns + (a.reduction - a.full_turns) / 2) t -= a.reduction;
    return t;
}

double clamp_turns(int axis, double t) {
    const Axis& a = kAxes[axis];
    const double lo = a.soft_margin_turns, hi = a.full_turns - a.soft_margin_turns;
    return t < lo ? lo : t > hi ? hi : t;
}

double value(const tuner::Setting& s, int axis) { return axis == 0 ? s.c1 : axis == 1 ? s.c2 : s.l; }
}  // namespace

bool Motion::begin() {
    for (uint8_t cs : pins::ENC_CS) {
        pinMode(cs, OUTPUT);
        digitalWriteFast(cs, HIGH);
    }
    SPI.begin();
    const bool ok = read_encoders();
    for (int i = 0; i < 3; ++i) g_pos[i] = int32_t(std::lround(turns_[i] * kStepsPerTurn));
    g_timer.priority(64);                                      // above USB and the serial ports
    g_timer.begin(step_isr, 1e6 / kStepIsrHz);
    return ok;
}

bool Motion::read_encoders() {
    bool ok = true;
    for (int i = 0; i < 3; ++i) {
        transfer(i, as::read_command(as::kRegAngle));
        const as::Reply r = as::decode(transfer(i, as::read_command(as::kRegAngle)));
        if (!r.parity_ok || r.error) {
            transfer(i, as::read_command(as::kRegClearError));   // and keep the last good reading
            ok = false;
            continue;
        }
        raw_[i] = r.data;
        turns_[i] = counts_to_turns(i, r.data);
    }
    return ok;
}

bool Motion::magnets_ok() {
    bool ok = true;
    for (int i = 0; i < 3; ++i) {
        transfer(i, as::read_command(as::kRegDiagAgc));
        const as::Reply r = as::decode(transfer(i, as::read_command(as::kRegAngle)));
        ok = ok && r.parity_ok && !r.error && as::diagnostics(r.data).ok();
    }
    return ok;
}

tuner::Setting Motion::position() const {
    tuner::Setting s;
    s.c1 = axis_curve(0).at(turns_[0]);
    s.c2 = axis_curve(1).at(turns_[1]);
    s.l = axis_curve(2).at(turns_[2]);
    return s;
}

tuner::Parts Motion::parts() const {
    double lo[3], hi[3];
    for (int i = 0; i < 3; ++i) {
        const tuner::Curve c = axis_curve(i);
        const double a = c.at(clamp_turns(i, 0)), b = c.at(clamp_turns(i, kAxes[i].full_turns));
        lo[i] = a < b ? a : b;
        hi[i] = a < b ? b : a;
    }
    tuner::Parts p;
    p.c1_min = lo[0], p.c1_max = hi[0];
    p.c2_min = lo[1], p.c2_max = hi[1];
    p.l_min = lo[2], p.l_max = hi[2];
    return p;
}

void Motion::start(uint32_t id, const tuner::Setting& target, uint32_t now_ms) {
    if (busy()) return;                                        // the state machine never overlaps moves
    id_ = id;
    if (!read_encoders()) {
        finish(now_ms, true);
        return;
    }
    int32_t from[3], to[3];
    tuner::AxisMotion m[3];
    for (int i = 0; i < 3; ++i) {
        const Axis& a = kAxes[i];
        from[i] = int32_t(std::lround(turns_[i] * kStepsPerTurn));      // the encoder is the truth
        to[i] = int32_t(std::lround(clamp_turns(i, axis_curve(i).inverse(value(target, i))) * kStepsPerTurn));
        m[i].v_max = a.v_max_rps * kStepsPerTurn;
        m[i].a_max = a.a_max_rps2 * kStepsPerTurn;
        if (a.slow_zone_turns > 0) {
            m[i].slow_lo = a.slow_zone_turns * kStepsPerTurn;
            m[i].slow_hi = (a.full_turns - a.slow_zone_turns) * kStepsPerTurn;
            m[i].v_slow = a.v_slow_rps * kStepsPerTurn;
        }
    }
    if (!g_plan.plan(from, to, m)) {
        finish(now_ms, true);
        return;
    }
    for (int i = 0; i < 3; ++i) {
        g_pos[i] = from[i];
        g_dir[i] = to[i] >= from[i] ? +1 : -1;
        const bool high_end = g_dir[i] > 0;
        digitalWriteFast(pins::DIR[i], (high_end == (kAxes[i].dir_sign > 0)) ? HIGH : LOW);
    }
    set_drivers(true);
    mismatch_ = false;
    phase_ = Phase::Waking;
    phase_ms_ = now_ms;
}

void Motion::gate_test(int axis, uint32_t now_ms) {
    if (busy() || axis < 0 || axis > 2) return;
    gate_axis_ = axis;
    gate_judged_ = read_encoders();
    gate_from_ = turns_[axis];
    const bool high_end = turns_[axis] < kAxes[axis].full_turns / 2;   // away from the nearer end
    digitalWriteFast(pins::DIR[axis], (high_end == (kAxes[axis].dir_sign > 0)) ? HIGH : LOW);
    set_drivers(true);
    phase_ = Phase::GateWaking;
    phase_ms_ = now_ms;
}

void Motion::service(uint32_t now_ms, bool enable) {
    switch (phase_) {
        case Phase::Idle:
            break;
        case Phase::GateWaking: {                              // the burst: 1/16 turn in 4 ms, the ISR idle
            if (now_ms - phase_ms_ < kDriverWakeMs) break;
            const uint32_t n = uint32_t(kStepsPerTurn / 16);
            for (uint32_t i = 0; i < n; ++i) {
                digitalWriteFast(pins::STEP[gate_axis_], HIGH);
                delayMicroseconds(20);
                digitalWriteFast(pins::STEP[gate_axis_], LOW);
                delayMicroseconds(20);
            }
            phase_ = Phase::GateSettling;
            phase_ms_ = now_ms;
            break;
        }
        case Phase::GateSettling:                              // then the encoder: a held gate moved nothing
            if (now_ms - phase_ms_ < kSettleMs) break;
            gate_judged_ = read_encoders() && gate_judged_;
            gate_moved_ = std::fabs(turns_[gate_axis_] - gate_from_) > 1.0 / 48;   // a third of the burst
            set_drivers(false);
            ++gate_runs_;
            phase_ = Phase::Idle;
            break;
        case Phase::Waking:                                    // DIR is set; give the drivers time to energize
            if (!enable) finish(now_ms, false);
            else if (now_ms - phase_ms_ >= kDriverWakeMs) {
                g_exec.start(&g_plan);
                g_stop = false;
                g_run = true;
                phase_ = Phase::Running;
            }
            break;
        case Phase::Running:
            if (!enable) g_stop = true;
            if (!g_run) {
                phase_ = Phase::Settling;
                phase_ms_ = now_ms;
            }
            break;
        case Phase::Settling: {                                // holding, then the encoder check (§8B.3)
            if (now_ms - phase_ms_ < kSettleMs) break;
            bool bad = !read_encoders();
            for (int i = 0; i < 3; ++i)
                bad = bad || std::fabs(turns_[i] * kStepsPerTurn - g_pos[i]) > kAxes[i].verify_turns * kStepsPerTurn;
            finish(now_ms, bad);
            break;
        }
    }
}

void Motion::finish(uint32_t now_ms, bool mismatch) {
    set_drivers(false);                                        // de-energized at idle (§8A.1)
    mismatch_ = mismatch;
    done_id_ = id_;
    stopped_ms_ = now_ms;
    phase_ = Phase::Idle;
}

}  // namespace hw
