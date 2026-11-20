// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// tnet.cpp against the validated Python solver: every band edge, the same choice, the same numbers.
#include <cmath>

#include "harness.hpp"
#include "vectors.hpp"
#include "tuner/tnet.hpp"

using namespace tuner;

namespace {
constexpr double pF = 1e-12, uH = 1e-6;
const Parts kParts{25 * pF, 700 * pF, 20 * pF, 675 * pF, 0.2 * uH, 32.4 * uH};   // UCSX-700-15S, UCSX-740-10, roller

using vec::kVecs;
using vec::Vec;

void check_rel(double got, double want, double rel) { CHECK_NEAR(got, want, std::fabs(want) * rel); }
}  // namespace

TEST(matches_cap_demand_at_every_band_edge) {
    for (const Vec& v : kVecs) {
        const Solution s = solve(v.mhz * 1e6, cplx(v.r, v.x), kParts);
        CHECK(s.ok == v.ok);
        if (!s.ok || !v.ok) continue;
        check_rel(s.s.l, v.l, 1e-9);
        check_rel(s.s.c1, v.c1, 1e-9);
        check_rel(s.s.c2, v.c2, 1e-9);
        check_rel(s.i_l, v.i_l, 1e-9);
        check_rel(s.v_c1, v.v_c1, 1e-9);
        check_rel(s.v_c2, v.v_c2, 1e-9);
        check_rel(s.v_l, v.v_l, 1e-9);
    }
}

TEST(every_solution_presents_fifty_ohms) {
    for (const Vec& v : kVecs) {
        const double f = v.mhz * 1e6;
        Solution two[2];
        const int n = solve_at(f, cplx(v.r, v.x), v.l, SolveOptions{}, two);
        CHECK(n >= 1);
        for (int i = 0; i < n; ++i) {
            const cplx z = input_impedance(f, two[i].s, cplx(v.r, v.x));
            CHECK_NEAR(z.real(), 50.0, 1e-6);
            CHECK_NEAR(z.imag(), 0.0, 1e-6);
        }
    }
}

TEST(de_embedding_inverts_the_network) {
    // At the solution and well away from it: the bridge sees the input; the load comes back exactly.
    for (const Vec& v : kVecs) {
        const double f = v.mhz * 1e6;
        const cplx zl(v.r, v.x);
        const Setting at[] = {{v.c1, v.l, v.c2}, {v.c1 * 1.4, v.l * 0.7, v.c2 * 0.8}, {300 * pF, 5 * uH, 300 * pF}};
        for (const Setting& s : at) {
            const cplx back = load_from_input(f, s, input_impedance(f, s, zl));
            CHECK_NEAR(std::abs(back - zl) / std::abs(zl), 0.0, 1e-9);
        }
    }
}

TEST(nearest_solution_stays_within_tolerance) {
    // §8B.3a: inside the current tolerance, never farther from the present setting than the lowest.
    for (const Vec& v : kVecs) {
        const double f = v.mhz * 1e6;
        const cplx zl(v.r, v.x);
        const Solution lowest = solve(f, zl, kParts);
        const Setting from[] = {{600 * pF, 2 * uH, 600 * pF}, {40 * pF, 20 * uH, 40 * pF}, lowest.s};
        for (const Setting& at : from) {
            SolveOptions o;
            o.near_tolerance = 0.03;
            o.from = &at;
            const Solution s = solve(f, zl, kParts, o);
            CHECK(s.ok);
            CHECK(s.i_l <= lowest.i_l * 1.03 * (1 + 1e-12));
            auto dist = [&](const Setting& a) {
                return std::fmax(std::fabs(a.c1 - at.c1) / (kParts.c1_max - kParts.c1_min),
                                 std::fmax(std::fabs(a.c2 - at.c2) / (kParts.c2_max - kParts.c2_min),
                                           std::fabs(a.l - at.l) / (kParts.l_max - kParts.l_min)));
            };
            CHECK(dist(s.s) <= dist(lowest.s));
        }
    }
}

TEST(refuses_what_cannot_be_matched) {
    CHECK(!solve(1.8e6, cplx(5, -2000), kParts).ok);          // needs a roller of ~130 uH
    CHECK(!solve(14.2e6, cplx(0, 50), kParts).ok);            // lossless: nothing to match
    CHECK(!solve(14.2e6, cplx(-3, 20), kParts).ok);           // an impossible reading
    CHECK(!solve(14.2e6, cplx(std::nan(""), 0), kParts).ok);  // a failed de-embedding
}

TEST(reference_settings_span_the_range) {
    // A cold start's search (fsm.hpp): distinct settings, all inside the parts, each a real match for a
    // load on the chart, on every band.
    for (double mhz : {1.8, 3.75, 7.15, 14.175, 21.2, 29.7}) {
        Setting s[10];
        const int n = reference_settings(mhz * 1e6, kParts, s, 10);
        CHECK(n >= 4);
        for (int i = 0; i < n; ++i) {
            CHECK(s[i].c1 >= kParts.c1_min && s[i].c1 <= kParts.c1_max && s[i].c2 >= kParts.c2_min &&
                  s[i].c2 <= kParts.c2_max && s[i].l >= kParts.l_min && s[i].l <= kParts.l_max);
            for (int k = 0; k < i; ++k) CHECK(setting_distance(s[i], s[k], kParts) >= 0.05);
        }
        CHECK(reference_settings(mhz * 1e6, kParts, s, 2) == 2);   // cap respected
    }
}
