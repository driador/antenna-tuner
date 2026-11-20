// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The SD card (§8B.5): a write-through mirror of internal flash, never a source, except /recovery.cfg
// read once at boot. With the panel-mount extender the Teensy's socket always holds the extender's
// plug, so its card-detect reads "inserted" whatever is in the panel slot. The card's presence is
// learned by using it: a failed operation marks it gone, and while it is gone it is re-mounted every
// few seconds.
//
//   /backup/NNNNNN[-YYYYMMDDTHHMMSS].json   versioned, the newest 20 kept (§8B.5.4a)
//   /backup/current.json                    the latest state, profiles included
//   /backup/tuner.id                        whose card this is (§8B.5.4b)
//   /log/events.log                         the event log, appended (§8B.5.5)
#pragma once
#include <cstddef>
#include <cstdint>

#include "tuner/events.hpp"
#include "tuner/mirror.hpp"

namespace hw {

class Storage {
public:
    void begin(uint64_t tuner_id);
    // Re-mounts a missing card, checks a present one, and appends new events to the log. Returns +1
    // when a card arrived, -1 when one went, else 0.
    int poll(uint32_t now_ms, const tuner::EventLog& log);
    bool present() const { return present_; }
    bool foreign() const { return foreign_; }      // another tuner's card: nothing is written to it

    bool backup(const tuner::Settings& s, const char* saved);    // a new version and current.json
    bool current(const tuner::Settings& s, const char* saved);   // current.json only
    int list(uint32_t numbers[], int cap);                       // the versions on the card, newest last
    // Reads a version into out. Returns nullptr, or why it will not do; restoring is the caller's call.
    const char* read(uint32_t number, tuner::Settings& out);
    bool adopt(uint64_t tuner_id);                 // the explicit "this card is ours now" (§8B.5.4b)
    // /recovery.cfg (§8B.5.4c): applied to net once, then renamed. True when it changed something.
    bool recovery(tuner::NetConfig& net, char* report, size_t cap);

private:
    bool mount();
    void lost();
    bool write(const char* path, const char* data, size_t n);   // a temporary file, then a rename
    bool flush(const tuner::EventLog& log);

    uint64_t id_ = 0;
    bool present_ = false, foreign_ = false;
    uint32_t next_backup_ = 1, logged_ = 1, last_try_ms_ = 0, last_flush_ms_ = 0, last_probe_ms_ = 0;
};

}  // namespace hw
