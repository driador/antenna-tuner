// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Where the fine recall memory lives (§8B.3c): a small LittleFS at the top of program flash, below the
// 256 KB the Teensy reserves for EEPROM emulation. It survives a power cycle and, with bootloader 1.07
// or later (Teensyduino 1.56), a code upload. It is convenience data: a missing or damaged file starts
// the memory empty, and use fills it again. A firmware update over the network stages its image below
// this area (update.hpp).
#pragma once
#include <cstdint>

#include "tuner/recall.hpp"

namespace hw {

class RecallStore {
public:
    static constexpr uint32_t kBytes = 256 * 1024;   // the filesystem's share of program flash
    // Mounts the area (formatting it if it holds no filesystem) and loads the memory. False if the
    // program leaves no room for it; the memory then lives in RAM only.
    bool begin(tuner::Recall& r);
    // A changed memory is saved once it has been unchanged for kQuietMs, so a run of tunes is one write.
    void tick(const tuner::Recall& r, uint32_t now_ms);
    void save(const tuner::Recall& r);         // a change not yet written, now (before an install)
    bool mounted() const { return ok_; }

private:
    static constexpr uint32_t kQuietMs = 10000;
    bool ok_ = false;
    uint32_t saved_ = 0, seen_ = 0, changed_ms_ = 0;
};

}  // namespace hw
