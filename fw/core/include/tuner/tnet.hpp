// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// High-pass T network: series C1 at the 50 ohm input, shunt roller L, series C2 to the load (§5, §6A.9).
// The closed-form solution is the one validated in nec/tnet.py and nec/cap_demand.py.
#pragma once
#include <complex>

namespace tuner {

using cplx = std::complex<double>;

struct Parts {                 // usable ranges of the installed elements, F and H (§5.1, Rev 3.7b)
    double c1_min = 25e-12, c1_max = 700e-12;     // UCSX-700-15S
    double c2_min = 20e-12, c2_max = 675e-12;     // UCSX-740-10
    double l_min = 0.20e-6, l_max = 32.4e-6;      // the roller as installed
};

struct Setting {               // one network state
    double c1 = 0, l = 0, c2 = 0;
};

struct Solution {
    Setting s;
    double i_l = 0;            // roller current, A RMS, at the rated power
    double v_c1 = 0, v_c2 = 0, v_l = 0;   // peak volts at the rated power
    bool ok = false;
};

struct SolveOptions {
    double power_w = 1500;     // for the stresses only; the setting does not depend on it
    double z_source = 50;
    int grid = 4000;           // roller values, log-spaced over [l_min, l_max] as cap_demand.py
    // §8B.3a: among solutions whose roller current is within this fraction of the lowest, take the
    // one nearest 'from' (the elements' present setting). 0 = pure lowest current.
    double near_tolerance = 0.0;
    const Setting* from = nullptr;
};

// Both closed-form branches at one roller value; returns how many were written (0-2). Unconstrained in C.
int solve_at(double f_hz, cplx z_load, double l, const SolveOptions& o, Solution out[2]);

// The best solution inside the part ranges, or one with ok == false when none exists.
Solution solve(double f_hz, cplx z_load, const Parts& parts, const SolveOptions& o = {});

// How far apart two settings are for the motors: each axis as a share of its own range, and the
// largest of the three, because the axes move together and the slowest sets the time (§8B.3).
double setting_distance(const Setting& a, const Setting& b, const Parts& p);

// Settings that match a spread of loads at f_hz, the likeliest first: where a cold start (no prior, and a
// reading too far off to use) looks for a readable neighborhood. Near-duplicates are left out. Returns
// how many it wrote.
int reference_settings(double f_hz, const Parts& p, Setting* out, int cap);

// What the network presents at its input with a given load, and the inverse: the load that the
// network must be seeing, given what the bridge measured at the input (de-embedding).
cplx input_impedance(double f_hz, const Setting& s, cplx z_load);
cplx load_from_input(double f_hz, const Setting& s, cplx z_in);

// What the elements and the output carry when p_in_w enters the network at any setting, matched or
// not: the over-voltage watch (§8D.7). Lossless, so a little high, which errs the safe way.
struct Stress {
    double v_out = 0;          // peak volts across the load: the balanced output, terminal to terminal
    double v_c1 = 0, v_c2 = 0; // peak volts across each capacitor
    double i_l = 0;            // roller current, A RMS
};
Stress stresses(double f_hz, const Setting& s, cplx z_load, double p_in_w);

}  // namespace tuner
