// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Network settings (§8B.5.3, §8B.5.4): what the tuner is told to use, the check a change must pass
// before it is saved, and the "key=value" text that the link (NET), the console and /recovery.cfg share.
// A saved change is used from the next restart; recovery mode (§8B.4f.3) is the way back from a bad one.
#pragma once
#include <cstddef>
#include <cstdint>

namespace tuner {

struct NetConfig {
    bool dhcp = true;
    char hostname[32] = "tuner";
    uint8_t ip[4] = {}, netmask[4] = {255, 255, 255, 0}, gateway[4] = {}, dns[4] = {};
};

namespace net {

// The fields a change names, as bits.
enum Field : uint8_t { kMode = 1, kHostname = 2, kIp = 4, kNetmask = 8, kGateway = 16, kDns = 32 };

bool parse_ip(const char* s, uint8_t out[4]);       // "192.168.1.50"; out is untouched on failure
void ip_text(const uint8_t a[4], char out[16]);
// One key (mode, hostname, ip, netmask, gateway, dns; any case) and its value into n. Returns nullptr
// and sets field, or why the key or value cannot be taken. A hostname is kept in lower case.
const char* assign(const char* key, const char* value, NetConfig& n, uint8_t& field);
void merge(NetConfig& into, const NetConfig& from, uint8_t fields);
// nullptr if a tuner could run on n, else why not: a hostname a resolver takes, and for a static
// address a contiguous /8 to /30 mask, a host address that is neither the subnet's network nor its
// broadcast address, and a gateway (0.0.0.0 for none) on the same subnet.
const char* check(const NetConfig& n);
// Whether a and b put the tuner on the network the same way; the addresses do not matter under DHCP.
bool same(const NetConfig& a, const NetConfig& b);
// "mode=dhcp hostname=tuner ip=0.0.0.0 netmask=255.255.255.0 gateway=0.0.0.0 dns=0.0.0.0": every field,
// so a page can offer the static ones while DHCP is in use. Returns the length, 0 if out is too small.
size_t format(const NetConfig& n, char* out, size_t cap);

}  // namespace net
}  // namespace tuner
