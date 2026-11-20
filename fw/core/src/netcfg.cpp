// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/netcfg.hpp"

#include <cctype>
#include <cstdio>
#include <cstring>

namespace tuner::net {

namespace {
uint32_t word(const uint8_t a[4]) { return uint32_t(a[0]) << 24 | uint32_t(a[1]) << 16 | uint32_t(a[2]) << 8 | a[3]; }

// A unicast host address: not in 0/8 or loopback, not multicast or the reserved 240/4.
bool host(uint32_t a) { return (a >> 24) != 0 && (a >> 24) != 127 && (a >> 28) < 14; }

// s in lower case into out; false if it does not fit.
bool lower(const char* s, char* out, size_t cap) {
    size_t i = 0;
    for (; s[i]; ++i) {
        if (i + 1 >= cap) return false;
        out[i] = char(std::tolower(static_cast<unsigned char>(s[i])));
    }
    out[i] = 0;
    return true;
}
}  // namespace

bool parse_ip(const char* s, uint8_t out[4]) {
    unsigned v[4];
    char tail;
    if (std::sscanf(s, "%u.%u.%u.%u%c", &v[0], &v[1], &v[2], &v[3], &tail) != 4) return false;
    for (unsigned x : v)
        if (x > 255) return false;
    for (int i = 0; i < 4; ++i) out[i] = uint8_t(v[i]);
    return true;
}

void ip_text(const uint8_t a[4], char out[16]) { std::snprintf(out, 16, "%u.%u.%u.%u", a[0], a[1], a[2], a[3]); }

const char* assign(const char* key, const char* value, NetConfig& n, uint8_t& field) {
    char k[12], v[40];
    if (!lower(key, k, sizeof k)) return "keys are mode, hostname, ip, netmask, gateway, dns";
    if (!lower(value, v, sizeof v)) return "value too long";
    if (!std::strcmp(k, "mode")) {
        if (std::strcmp(v, "dhcp") && std::strcmp(v, "static")) return "mode is dhcp or static";
        n.dhcp = !std::strcmp(v, "dhcp");
        field = kMode;
        return nullptr;
    }
    if (!std::strcmp(k, "hostname")) {
        if (!v[0] || std::strlen(v) >= sizeof n.hostname) return "hostname is 1 to 31 characters";
        std::memset(n.hostname, 0, sizeof n.hostname);  // whole, so equal settings compare equal byte for byte
        std::memcpy(n.hostname, v, std::strlen(v));
        field = kHostname;
        return nullptr;
    }
    uint8_t* to = !std::strcmp(k, "ip") ? n.ip : !std::strcmp(k, "netmask") ? n.netmask
                : !std::strcmp(k, "gateway") ? n.gateway : !std::strcmp(k, "dns") ? n.dns : nullptr;
    if (!to) return "keys are mode, hostname, ip, netmask, gateway, dns";
    if (!parse_ip(v, to)) return "an address is four numbers 0-255, as 192.168.1.50";
    field = to == n.ip ? kIp : to == n.netmask ? kNetmask : to == n.gateway ? kGateway : kDns;
    return nullptr;
}

void merge(NetConfig& into, const NetConfig& from, uint8_t fields) {
    if (fields & kMode) into.dhcp = from.dhcp;
    if (fields & kHostname) std::memcpy(into.hostname, from.hostname, sizeof into.hostname);
    if (fields & kIp) std::memcpy(into.ip, from.ip, 4);
    if (fields & kNetmask) std::memcpy(into.netmask, from.netmask, 4);
    if (fields & kGateway) std::memcpy(into.gateway, from.gateway, 4);
    if (fields & kDns) std::memcpy(into.dns, from.dns, 4);
}

const char* check(const NetConfig& n) {
    const size_t len = std::strlen(n.hostname);
    if (len == 0 || len >= sizeof n.hostname) return "hostname is 1 to 31 characters";
    for (size_t i = 0; i < len; ++i)
        if (!std::isalnum(static_cast<unsigned char>(n.hostname[i])) && n.hostname[i] != '-')
            return "hostname takes letters, digits and hyphens only";
    if (n.hostname[0] == '-' || n.hostname[len - 1] == '-') return "hostname cannot start or end with a hyphen";
    if (n.dhcp) return nullptr;
    const uint32_t ip = word(n.ip), mask = word(n.netmask), gw = word(n.gateway), dns = word(n.dns), hosts = ~mask;
    if ((hosts & (hosts + 1)) != 0 || hosts < 3 || hosts > 0x00FFFFFFu) return "netmask is contiguous, /8 to /30, as 255.255.255.0";
    if (!host(ip)) return "ip is not a host address";
    if ((ip & hosts) == 0 || (ip & hosts) == hosts) return "ip is the subnet's network or broadcast address";
    if (gw && ((gw & mask) != (ip & mask) || (gw & hosts) == 0 || (gw & hosts) == hosts))
        return "gateway must be a host on the tuner's subnet, or 0.0.0.0 for none";
    if (gw == ip) return "gateway cannot be the tuner's own address";
    if (dns && !host(dns)) return "dns is not a host address";
    return nullptr;
}

bool same(const NetConfig& a, const NetConfig& b) {
    if (a.dhcp != b.dhcp || std::strcmp(a.hostname, b.hostname)) return false;
    return a.dhcp || (!std::memcmp(a.ip, b.ip, 4) && !std::memcmp(a.netmask, b.netmask, 4) &&
                      !std::memcmp(a.gateway, b.gateway, 4) && !std::memcmp(a.dns, b.dns, 4));
}

size_t format(const NetConfig& n, char* out, size_t cap) {
    char ip[16], mask[16], gw[16], dns[16];
    ip_text(n.ip, ip);
    ip_text(n.netmask, mask);
    ip_text(n.gateway, gw);
    ip_text(n.dns, dns);
    const int k = std::snprintf(out, cap, "mode=%s hostname=%s ip=%s netmask=%s gateway=%s dns=%s",
                                n.dhcp ? "dhcp" : "static", n.hostname, ip, mask, gw, dns);
    return k < 0 || size_t(k) >= cap ? 0 : size_t(k);
}

}  // namespace tuner::net
