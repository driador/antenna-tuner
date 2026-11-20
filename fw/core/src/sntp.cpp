// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/sntp.hpp"

#include <cstring>

namespace tuner::sntp {

namespace {
constexpr uint32_t kNtpToUnix = 2208988800UL;   // 1900-01-01 to 1970-01-01
constexpr uint32_t kEarliest = 1767225600UL;    // 2026-01-01: an answer before this is not a real time
}  // namespace

void request(uint8_t out[kPacket]) {
    std::memset(out, 0, kPacket);
    out[0] = 0x1B;                              // LI 0, version 3, mode 3 (client)
}

bool unix_time(const uint8_t* reply, size_t n, uint32_t& unix_s) {
    if (n < kPacket) return false;
    const unsigned li = reply[0] >> 6, mode = reply[0] & 7, stratum = reply[1];
    if (mode != 4 || li == 3 || stratum == 0) return false;
    const uint32_t ntp = uint32_t(reply[40]) << 24 | uint32_t(reply[41]) << 16 | uint32_t(reply[42]) << 8 | reply[43];
    if (ntp == 0) return false;                 // no transmit time: discard (RFC 4330 §5)
    // The seconds wrap in February 2036 (RFC 4330 §3). Modulo 2^32 the same subtraction covers both
    // eras, which carries the 32-bit Unix time through 2106.
    const uint32_t t = ntp - kNtpToUnix;
    if (t < kEarliest) return false;
    unix_s = t;
    return true;
}

}  // namespace tuner::sntp
