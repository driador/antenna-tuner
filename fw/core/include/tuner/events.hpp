// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The event log (§8B.5.3, §8C.5, §8C.6): faults raised, acknowledged and cleared, mode and path changes,
// tunes, calibration, boots and resets, card and restore events. Every event has a sequence number, so
// the SD log and each network client take only what they have not seen, and a link that drops loses
// nothing still in the ring when it comes back.
#pragma once
#include <cstddef>
#include <cstdint>

#include "tuner/fsm.hpp"

namespace tuner {

enum class EventKind : uint8_t {
    Boot, WatchdogReset, Fault, Ack, Clear, Mode, Path, Tuned, CalSaved, Inspected, CardIn, CardOut, Restore, Recovery,
    Network, Derate, SelfTest
};

constexpr uint8_t kSelfTestPassed = 255, kSelfTestStopped = 254;

struct EventRecord {
    uint32_t seq = 0;
    uint32_t time_s = 0;       // Unix time when the clock is set, else seconds since boot
    bool wall = false;         // which of the two time_s is
    EventKind kind = EventKind::Boot;
    uint8_t arg = 0;           // the fault, mode or path, by kind; for Network, 1 for DHCP; for SelfTest,
                               // the check that failed (bit.hpp), or kSelfTestPassed / kSelfTestStopped
    State state = State::SelfTest;
    float mhz = 0;
};

class EventLog {
public:
    static constexpr int kSize = 128;

    void add(uint32_t time_s, bool wall, EventKind kind, uint8_t arg, State state, double mhz);
    uint32_t next() const { return next_; }    // the number the next event will get
    // The events numbered `from` or later that are still held, oldest first, at most cap.
    int since(uint32_t from, EventRecord out[], int cap) const;
    // One event as text: "seq=7 t=2026-11-20T14:03:11Z event=fault fault=limit_hit state=MOVE mhz=14.2051"
    static size_t format(const EventRecord& e, char* out, size_t cap);

private:
    EventRecord ring_[kSize];
    uint32_t next_ = 1;
};

// Unix seconds as ISO 8601 UTC ("2026-11-20T14:03:11Z"). The clock is the Teensy's RTC.
size_t iso8601(uint32_t unix_s, char* out, size_t cap);

}  // namespace tuner
