// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The data link (§8C.3-§8C.7) on the Teensy 4.1's Ethernet, through QNEthernet. The line protocol
// (proto.hpp) is served on TCP port kLinePort for `nc`. Port 80 serves the page, whose WebSocket at
// /ws carries the same lines. Only hosts on the tuner's own subnet are served (§8C.7).
//
// Nothing here can reach the transmit permissive, which has its own fiber (§7.4). The worst a hostile
// or hung network can do is ask for a tune, and a tune drops PTT before anything moves (§8C.7). Every
// call here returns at once: writes go out only when they fit, and connections close without waiting,
// so the link can never hold up the tick or starve the watchdog.
#pragma once
#include <cstddef>
#include <cstdint>

#include "tuner/events.hpp"
#include "tuner/mirror.hpp"
#include "tuner/proto.hpp"

namespace hw {

class Net {
public:
    struct Hooks {
        // Carries out a command the link may give. Returns nullptr, or why it was not done.
        const char* (*command)(const tuner::proto::Request& r);
        void (*telemetry)(tuner::proto::Telemetry& t);
        void (*network)(tuner::NetConfig& saved);    // the saved settings, which NET reports
    };

    void begin(const tuner::NetConfig& cfg, const tuner::EventLog* log, const Hooks& h);
    void poll(uint32_t now_ms);
    bool link() const;
    bool clock_set() const { return clock_set_; }
    void address(char* out, size_t cap) const;     // the tuner's address, or "none"
    const tuner::NetConfig& running() const;       // the settings it started with, in use until a restart

private:
    void ntp(uint32_t now_ms);
    bool clock_set_ = false;
};

}  // namespace hw
