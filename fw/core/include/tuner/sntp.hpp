// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Simple network time (RFC 4330) for the event log and the backups' timestamps: one 48-byte request,
// one reply. The tuner keeps time without it; this only sets the RTC when a server answers.
#pragma once
#include <cstddef>
#include <cstdint>

namespace tuner::sntp {

constexpr size_t kPacket = 48;
void request(uint8_t out[kPacket]);   // a version 3 client request
// The server's transmit time as Unix seconds, if the reply is a usable one: a server (mode 4) that is
// synchronized (leap indicator not 3), not a kiss-of-death (stratum 0), with a time no earlier than 2026.
// Good past the NTP rollover in 2036, to 2106.
bool unix_time(const uint8_t* reply, size_t n, uint32_t& unix_s);

}  // namespace tuner::sntp
