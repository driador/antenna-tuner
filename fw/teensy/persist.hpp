// What survives a power cycle (§8B.4b, §8B.5.2), in the Teensy's flash-backed EEPROM under a CRC: the
// fault record and policy mode, the priors (the internal copy of the tuning profiles), and where the
// elements were, so boot can say whether someone moved them (§8B.4b step 4).
#pragma once
#include <cstdint>

#include "tuner/faults.hpp"
#include "tuner/freq.hpp"
#include "tuner/fsm.hpp"

namespace hw {

struct Persisted {
    tuner::FaultRecord faults;
    float last_turns[3] = {};
    bool prior_ok[tuner::kSegments] = {};
    tuner::Prior priors[tuner::kSegments] = {};
};

bool load(Persisted& p);           // false when blank, from another layout, or corrupt
// Stored field by field with no padding, so an unchanged state compares equal and writes nothing; a
// changed one rewrites only the bytes that differ.
void save(const Persisted& p);

}  // namespace hw
