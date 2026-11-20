// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The band-edge vectors from nec/cap_demand.py (fw/tools/gen_tables.py), shared by the tests.
#pragma once
#include <cmath>

#include "tuner/tnet.hpp"

namespace vec {

struct Vec {
    const char* band;
    double mhz;
    double zl_r, zl_x;             // NEC feedpoint
    double r, x;                   // at the tuner, 40 ft of 600 ohm line at VF 0.95
    bool ok;
    double l, c1, c2, i_l, v_c1, v_c2, v_l;
};

inline const Vec kVecs[] = {
#include "tnet_vectors.inc"
};
constexpr int kCount = int(sizeof(kVecs) / sizeof(kVecs[0]));

// The feedpoint carried through a lossless 600 ohm feeder, as cap_demand.zin().
inline tuner::cplx at_tuner(double mhz, tuner::cplx zl, double feet = 40, double vf = 0.95) {
    const double bl = 2 * 3.14159265358979323846 * mhz * 1e6 * feet * 0.3048 / (2.998e8 * vf);
    const tuner::cplx jt(0, std::tan(bl)), z0(600, 0);
    return z0 * (zl + z0 * jt) / (z0 + zl * jt);
}

}  // namespace vec
