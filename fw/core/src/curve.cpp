// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/curve.hpp"

#include <cmath>

namespace tuner {

namespace {
// The segment to use for a value along a monotonic sequence: the one containing it, else the end one.
int segment(const double* v, int n, double p) {
    const bool rising = v[n - 1] > v[0];
    for (int i = 1; i < n - 1; ++i)
        if (rising ? p < v[i] : p > v[i]) return i - 1;
    return n - 2;
}

const double kRoller[][2] = {
#include "roller_model.inc"
};
}  // namespace

Curve Curve::line(double x0, double y0, double x1, double y1) {
    Curve c;
    c.add(x0, y0);
    c.add(x1, y1);
    return c;
}

bool Curve::add(double px, double py) {
    if (n >= kMax) return false;
    x[n] = px;
    y[n] = py;
    ++n;
    return true;
}

bool Curve::insert(double px, double py) {
    for (int i = 0; i < n; ++i)
        if (std::fabs(px - x[i]) <= 0.02 * std::fabs(x[i])) {
            x[i] = px;
            y[i] = py;
            return true;
        }
    if (n >= kMax) return false;
    int i = n;
    while (i > 0 && x[i - 1] > px) {
        x[i] = x[i - 1];
        y[i] = y[i - 1];
        --i;
    }
    x[i] = px;
    y[i] = py;
    ++n;
    return true;
}

bool Curve::valid() const {
    if (n < 2) return false;
    const bool rising = y[n - 1] > y[0];
    for (int i = 1; i < n; ++i) {
        if (!(x[i] > x[i - 1])) return false;
        if (rising ? !(y[i] > y[i - 1]) : !(y[i] < y[i - 1])) return false;
    }
    return true;
}

double Curve::at(double px) const {
    const int i = segment(x, n, px);
    return y[i] + (y[i + 1] - y[i]) * (px - x[i]) / (x[i + 1] - x[i]);
}

double Curve::inverse(double py) const {
    const int i = segment(y, n, py);
    return x[i] + (x[i + 1] - x[i]) * (py - y[i]) / (y[i + 1] - y[i]);
}

Curve c1_model(double turns) { return Curve::line(0, 25e-12, turns, 700e-12); }
Curve c2_model(double turns) { return Curve::line(0, 20e-12, turns, 675e-12); }

Curve roller_model() {
    Curve c;
    for (const auto& p : kRoller) c.add(p[0], p[1]);
    return c;
}

}  // namespace tuner
