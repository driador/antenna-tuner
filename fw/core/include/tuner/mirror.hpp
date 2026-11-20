// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// What the SD card mirrors (§8B.5.4d), the one file it may feed back (§8B.5.4c), and how its versioned
// backups are named and pruned (§8B.5.4a). Internal flash stays the source of truth; nothing here is
// read in normal operation.
#pragma once
#include <cstddef>
#include <cstdint>

#include "tuner/cal.hpp"
#include "tuner/curve.hpp"
#include "tuner/faults.hpp"
#include "tuner/freq.hpp"
#include "tuner/fsm.hpp"
#include "tuner/netcfg.hpp"
#include "tuner/qualify.hpp"

namespace tuner {

struct Settings {
    uint64_t tuner_id = 0;             // random at first boot; restore is gated on it (§8B.5.4b)
    NetConfig net;
    double retune_swr = 1.5, window_pct = 0.5;
    Mode policy = Mode::Strict;
    Qualification qual;
    BridgeCal bridge[kBandCount];
    Curve power[kBandCount];
    bool prior_ok[kSegments] = {};
    Prior priors[kSegments];
};

// The mirror document; `saved` is an ISO 8601 time or empty. Returns the length, 0 if out is too small.
size_t write_mirror(const Settings& s, const char* saved, char* out, size_t cap);
// Parses a mirror document into s. Returns nullptr, or what is wrong with it.
const char* read_mirror(const char* doc, Settings& s);

// /recovery.cfg: "key = value" lines, # comments. Only the network keys (net.mode dhcp|static,
// hostname, ip, netmask, gateway, dns) are taken; anything else is refused and listed in report,
// because recovery may restore reachability and nothing more. A result the tuner could not run on
// (net::check) is refused whole, and net is left as it was.
bool read_recovery(const char* text, NetConfig& net, char* report, size_t cap);

// Backups are /backup/NNNNNN.json or /backup/NNNNNN-YYYYMMDDTHHMMSS.json, numbered so they sort even
// when the clock was never set.
constexpr int kKeepBackups = 20;
bool backup_number(const char* name, uint32_t& n);   // the number a backup file name starts with
// Given the numbers present (any order), the ones to delete so that the newest kKeepBackups remain.
int backups_to_prune(const uint32_t* have, int n, uint32_t* drop, int cap);

}  // namespace tuner
