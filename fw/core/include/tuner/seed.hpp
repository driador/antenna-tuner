// The factory priors (§6A.7 option 2, §7.6): for each profile segment, the NEC model's load at the
// tuner and the setting that matches it. The storage layer loads them at first boot; a good tune
// replaces its segment's entry (Tuner::set_prior), and the stored copy follows it.
#pragma once
#include "tuner/fsm.hpp"

namespace tuner {

struct SeedPrior {
    double mhz;
    double r, x;                   // ohms at the tuner
    double c1, l, c2;              // F, H, F
    bool ok;                       // the model's load is matchable there
};

extern const SeedPrior kSeedPriors[kSegments];

void seed_priors(Tuner& t);

}  // namespace tuner
