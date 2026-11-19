#include "tuner/motion.hpp"

#include <cmath>

namespace tuner {

bool MovePlan::plan(const int32_t start[kAxes], const int32_t target[kAxes], const AxisMotion m[kAxes]) {
    double a = HUGE_VAL;
    bool moving = false;
    for (int i = 0; i < kAxes; ++i) {
        start_[i] = start[i];
        delta_[i] = target[i] - start[i];
        if (delta_[i] == 0) continue;
        if (!(m[i].v_max > 0) || !(m[i].a_max > 0)) return false;
        moving = true;
        a = std::fmin(a, m[i].a_max / std::fabs(double(delta_[i])));
    }
    for (int k = 0; k <= kN; ++k) t_[k] = v_[k] = 0;
    a_ = moving ? a : 0;
    if (!moving) return true;

    // The speed cap at each sample: every axis within its limit there. The slow zone is widened by one
    // sample so that no segment enters it fast.
    const double ds = 1.0 / kN;
    double cap[kN + 1];
    for (int k = 0; k <= kN; ++k) {
        cap[k] = HUGE_VAL;
        for (int i = 0; i < kAxes; ++i) {
            if (delta_[i] == 0) continue;
            const double d = std::fabs(double(delta_[i]));
            double v = m[i].v_max;
            if (m[i].v_slow > 0) {
                const double pos = start_[i] + delta_[i] * (double(k) / kN), margin = d * ds;
                if (pos < m[i].slow_lo + margin || pos > m[i].slow_hi - margin) v = std::fmin(v, m[i].v_slow);
            }
            cap[k] = std::fmin(cap[k], v / d);
        }
    }
    // Accelerate as hard as allowed going forward, decelerate likewise coming back from the end.
    for (int k = 0; k < kN; ++k) v_[k + 1] = std::fmin(cap[k + 1], std::sqrt(v_[k] * v_[k] + 2 * a * ds));
    v_[kN] = 0;
    for (int k = kN - 1; k > 0; --k) v_[k] = std::fmin(v_[k], std::sqrt(v_[k + 1] * v_[k + 1] + 2 * a * ds));
    for (int k = 0; k < kN; ++k) t_[k + 1] = t_[k] + 2 * ds / (v_[k] + v_[k + 1]);
    return true;
}

void MoveExecutor::start(const MovePlan* p) {
    p_ = p;
    k_ = 0;
    tau_ = 0;
    s_ = 0;
    v_ = 0;
    stopping_ = false;
    done_ = p->duration() <= 0;
    if (done_) s_ = 1;
}

void MoveExecutor::stop() {
    if (running()) stopping_ = true;
}

double MoveExecutor::advance(double dt) {
    if (!running()) return s_;
    if (stopping_) {
        // The plan never moves faster than it can stop before s = 1, so this never overruns the target.
        const double a = p_->accel();
        const double used = v_ > a * dt ? dt : v_ / a;
        s_ = std::fmin(1.0, s_ + v_ * used - 0.5 * a * used * used);
        v_ -= a * used;
        if (v_ <= 0) {
            v_ = 0;
            done_ = true;
        }
        return s_;
    }
    tau_ += dt;
    while (k_ < MovePlan::kN && tau_ >= p_->t(k_ + 1) - p_->t(k_)) {
        tau_ -= p_->t(k_ + 1) - p_->t(k_);
        ++k_;
    }
    if (k_ >= MovePlan::kN) {
        s_ = 1;
        v_ = 0;
        done_ = true;
        return s_;
    }
    const double v0 = p_->v(k_), v1 = p_->v(k_ + 1);
    const double acc = (v1 - v0) / (p_->t(k_ + 1) - p_->t(k_));   // constant within a segment
    s_ = double(k_) / MovePlan::kN + v0 * tau_ + 0.5 * acc * tau_ * tau_;
    v_ = v0 + acc * tau_;
    return s_;
}

}  // namespace tuner
