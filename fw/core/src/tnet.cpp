// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/tnet.hpp"

#include <cmath>

namespace tuner {

namespace {
constexpr double kPi = 3.14159265358979323846;
constexpr double kSqrt2 = 1.41421356237309504880;
}  // namespace

int solve_at(double f_hz, cplx z_load, double l, const SolveOptions& o, Solution out[2]) {
    const double w = 2 * kPi * f_hz;
    const double r = z_load.real(), x = z_load.imag();
    const double xl = w * l;
    const double disc = r * (xl * xl / o.z_source - r);
    if (!(r > 0) || !(disc >= 0)) return 0;          // also refuses a NaN from a bad de-embedding
    const double sq = std::sqrt(disc);
    int n = 0;
    for (double x1 : {-xl + sq, -xl - sq}) {
        const double d = x - x1;                       // C2 must supply this reactance
        if (d <= 0) continue;
        const double den = r * r + (x1 + xl) * (x1 + xl);
        const double im_z2 = xl * (x1 * (x1 + xl) + r * r) / den;
        if (im_z2 <= 0) continue;
        Solution& s = out[n++];
        s.s.c2 = 1 / (w * d);
        s.s.c1 = 1 / (w * im_z2);
        s.s.l = l;
        const double i_in = std::sqrt(o.power_w / o.z_source), i_load = std::sqrt(o.power_w / r);
        s.i_l = i_load * std::abs(cplx(r, x1)) / xl;
        s.v_c1 = kSqrt2 * i_in / (w * s.s.c1);
        s.v_c2 = kSqrt2 * i_load / (w * s.s.c2);
        s.v_l = kSqrt2 * s.i_l * xl;
        s.ok = true;
    }
    return n;
}

namespace {
bool inside(const Solution& s, const Parts& p) {
    return s.s.c1 >= p.c1_min && s.s.c1 <= p.c1_max && s.s.c2 >= p.c2_min && s.s.c2 <= p.c2_max;
}
}  // namespace

double setting_distance(const Setting& a, const Setting& b, const Parts& p) {
    const double d1 = std::abs(a.c1 - b.c1) / (p.c1_max - p.c1_min);
    const double d2 = std::abs(a.c2 - b.c2) / (p.c2_max - p.c2_min);
    const double dl = std::abs(a.l - b.l) / (p.l_max - p.l_min);
    return std::fmax(d1, std::fmax(d2, dl));
}

int reference_settings(double f_hz, const Parts& p, Setting* out, int cap) {
    // Points on the Smith chart (|Gamma|, degrees, against 50 ohm). First the right-hand side, where a
    // doublet on open-wire line sits at the tuner on every band (high impedance, either reactance), then
    // the rest of the chart for whatever a frequency off the bands brings.
    static const double kPoints[][2] = {{0.9, 0},  {0.9, -30}, {0.9, 20},  {0.6, -45}, {0.6, 20},
                                        {0.97, -10}, {0, 0},   {0.8, 90},  {0.8, -90}, {0.8, 180}};
    int n = 0;
    for (const auto& pt : kPoints) {
        if (n >= cap) break;
        const cplx g = std::polar(pt[0], pt[1] * kPi / 180);
        const Solution sol = solve(f_hz, 50.0 * (1.0 + g) / (1.0 - g), p);
        if (!sol.ok) continue;
        bool near = false;
        for (int k = 0; k < n && !near; ++k) near = setting_distance(out[k], sol.s, p) < 0.05;
        if (!near) out[n++] = sol.s;
    }
    return n;
}

Solution solve(double f_hz, cplx z_load, const Parts& parts, const SolveOptions& o) {
    Solution lowest{};
    // First pass: the lowest roller current (the §5.1 policy the loss and derate figures assume).
    auto scan = [&](auto&& visit) {
        const double lo = parts.l_min, ratio = parts.l_max / parts.l_min;
        for (int k = 0; k < o.grid; ++k) {
            const double l = lo * std::pow(ratio, double(k) / (o.grid - 1));
            Solution two[2];
            const int n = solve_at(f_hz, z_load, l, o, two);
            for (int i = 0; i < n; ++i)
                if (inside(two[i], parts)) visit(two[i]);
        }
    };
    scan([&](const Solution& s) {
        if (!lowest.ok || s.i_l < lowest.i_l) lowest = s;
    });
    if (!lowest.ok || o.near_tolerance <= 0 || o.from == nullptr) return lowest;
    // Second pass: within the tolerance, the solution nearest the present setting.
    Solution nearest = lowest;
    double best_d = setting_distance(lowest.s, *o.from, parts);
    const double limit = lowest.i_l * (1 + o.near_tolerance);
    scan([&](const Solution& s) {
        if (s.i_l > limit) return;
        const double d = setting_distance(s.s, *o.from, parts);
        if (d < best_d) {
            best_d = d;
            nearest = s;
        }
    });
    return nearest;
}

cplx input_impedance(double f_hz, const Setting& s, cplx z_load) {
    const double w = 2 * kPi * f_hz;
    const cplx zc1(0, -1 / (w * s.c1)), zc2(0, -1 / (w * s.c2)), zl(0, w * s.l);
    const cplx zb = z_load + zc2;                      // C2 in series with the load
    return zc1 + zl * zb / (zl + zb);                  // the roller across it, then C1
}

cplx load_from_input(double f_hz, const Setting& s, cplx z_in) {
    const double w = 2 * kPi * f_hz;
    const cplx zc1(0, -1 / (w * s.c1)), zc2(0, -1 / (w * s.c2)), zl(0, w * s.l);
    const cplx za = z_in - zc1;                        // take C1 off
    const cplx zb = 1.0 / (1.0 / za - 1.0 / zl);       // take the roller off
    return zb - zc2;                                   // take C2 off
}

}  // namespace tuner
