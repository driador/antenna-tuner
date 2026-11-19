// One coordinated move (§8B.3): every axis travels the straight line from start to target in step
// space, so all three start and stop together. The plan is a speed profile along the path parameter s
// (0 to 1), sampled at kN points: within each axis's speed and acceleration, and within the roller's
// slow zone near either end of its travel (§7.2). Pure arithmetic: the Teensy layer turns s into step
// pulses in its timer interrupt.
#pragma once
#include <cstdint>

namespace tuner {

constexpr int kAxes = 3;   // C1, C2, roller

struct AxisMotion {
    double v_max = 0;      // steps/s
    double a_max = 0;      // steps/s^2
    // Below slow_lo or above slow_hi (step positions) the axis is held to v_slow; v_slow 0 = no zone.
    double slow_lo = 0, slow_hi = 0, v_slow = 0;
};

class MovePlan {
public:
    static constexpr int kN = 256;

    // False when a limit is not positive; a move of zero length plans with zero duration.
    bool plan(const int32_t start[kAxes], const int32_t target[kAxes], const AxisMotion m[kAxes]);

    double duration() const { return t_[kN]; }
    double accel() const { return a_; }            // along s, 1/s^2
    int32_t start(int axis) const { return start_[axis]; }
    int32_t delta(int axis) const { return delta_[axis]; }
    double t(int k) const { return t_[k]; }        // time at s = k / kN
    double v(int k) const { return v_[k]; }        // ds/dt there

private:
    int32_t start_[kAxes] = {}, delta_[kAxes] = {};
    double t_[kN + 1] = {}, v_[kN + 1] = {};
    double a_ = 0;
};

// Steps through a plan in time, as the timer interrupt does. stop() turns the rest of the move into a
// deceleration along the same path at the plan's acceleration, so an abandoned move still ramps down.
class MoveExecutor {
public:
    void start(const MovePlan* p);
    void stop();
    bool running() const { return p_ != nullptr && !done_; }
    double advance(double dt);                     // s after dt more seconds
    double s() const { return s_; }
    double v() const { return v_; }

private:
    const MovePlan* p_ = nullptr;
    int k_ = 0;
    double tau_ = 0;                               // time into segment k_
    double s_ = 0, v_ = 0;
    bool stopping_ = false, done_ = true;
};

}  // namespace tuner
