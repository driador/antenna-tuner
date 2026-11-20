// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The link protocol (§8C.5): line-oriented text, one record per line, each ending in an NMEA-style
// checksum, "*" and two hex digits of the XOR of every character before it. The same lines travel over
// TCP and inside WebSocket frames, so `nc` and the browser speak one protocol.
//
//   to the tuner     TUNE | ACK | QUERY | SUBSCRIBE [hz] | GET_LOG [from] | PATH TUNE|AUX|CAL
//                    | CAL LOAD|OPEN|SHORT|SAVE | CAL WATTS <w>
//                    | NET [mode=dhcp|static] [hostname=] [ip=] [netmask=] [gateway=] [dns=]
//   from the tuner   OK <command> | ERR <reason> | TLM <fields> | EVT <event> | NET <settings>
//
// NET alone asks for the network settings; with keys it changes the ones named. A change is checked,
// saved as an administrative change (§8B.5.4) and used from the next restart.
//
// A command may omit its checksum (typed by hand); one that has a checksum must match it. Deliberately
// absent, and refused by name so the refusal is visible: mode changes (§8B.4a-1), class C clears
// (§8B.4f), the bypass (§8B.4d) and jogging (§7.5) are all local.
#pragma once
#include <cstddef>
#include <cstdint>

#include "tuner/events.hpp"
#include "tuner/faults.hpp"
#include "tuner/fsm.hpp"
#include "tuner/netcfg.hpp"
#include "tuner/path.hpp"

namespace tuner::proto {

enum class Cmd : uint8_t {
    Invalid, Tune, Ack, Query, Subscribe, GetLog, Path, CalLoad, CalOpen, CalShort, CalSave, CalWatts, Net, LocalOnly
};

struct Request {
    Cmd cmd = Cmd::Invalid;
    double value = 0;              // SUBSCRIBE rate, GET_LOG start, CAL WATTS
    Path path = Path::Tune;
    const char* why = nullptr;     // for Invalid and LocalOnly: the reason to send back
    NetConfig net;                 // NET: the values given, and which fields they are (net::Field bits)
    uint8_t net_fields = 0;
};

uint8_t checksum(const char* s, size_t n);
// Appends "*HH" to the line of length len in buf; returns the new length, or 0 if it does not fit.
size_t seal(char* buf, size_t len, size_t cap);
Request parse(const char* line);

struct Telemetry {
    State state = State::Idle;
    Path path = Path::Tune;
    Mode mode = Mode::Strict;
    double mhz = 0;
    bool carrier = false;
    double swr = 0, fwd_w = -1;    // fwd_w below zero: this band's power curve is not calibrated
    Setting at;
    double tank_c = 0;
    uint16_t latched_c = 0, unacked_b = 0;
    bool permit = false, bypass = false;
    uint32_t next_event = 0;       // a client that has seen less than this asks GET_LOG
};

// "TLM state=MATCHED path=TUNE mode=STRICT mhz=14.2051 carrier=1 swr=1.12 fwd=812 c1=123.4 c2=456.7
//  l=5.123 tank=31.2 c=0000 b=0000 permit=1 bypass=0 ev=12*HH" (pF, uH, W, °C)
size_t telemetry(const Telemetry& t, char* out, size_t cap);
size_t event(const EventRecord& e, char* out, size_t cap);         // "EVT seq=... *HH"
size_t reply(bool ok, const char* text, char* out, size_t cap);    // "OK TUNE*HH" / "ERR ...*HH"
// "NET mode=static hostname=tuner ip=... netmask=... gateway=... dns=... now=192.168.1.37 pending=1*HH":
// the saved settings, the address in use now, and whether the saved ones wait for a restart.
size_t network(const NetConfig& saved, bool pending, const uint8_t now[4], char* out, size_t cap);

}  // namespace tuner::proto
