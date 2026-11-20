// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/seed.hpp"

namespace tuner {

const SeedPrior kSeedPriors[kSegments] = {
#include "seed_priors.inc"
};

void seed_priors(Tuner& t) {
    for (int i = 0; i < kSegments; ++i) {
        const SeedPrior& s = kSeedPriors[i];
        if (s.ok) t.set_prior(i, {cplx(s.r, s.x), Setting{s.c1, s.l, s.c2}});
    }
}

}  // namespace tuner
