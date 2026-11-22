// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/events.hpp"

#include <cstdio>

#include "tuner/bit.hpp"

namespace tuner {

namespace {
const char* const kKinds[] = {"boot", "watchdog_reset", "fault", "ack", "clear", "mode", "path",
                              "tuned", "cal_saved", "inspected", "card_in", "card_out", "restore", "recovery",
                              "network", "derate", "selftest"};
const char* const kFaults[] = {"over_temp", "carrier_lost", "no_solution", "tune_failed", "over_swr",
                               "limit_hit", "encoder_mismatch", "self_test_fail", "relay_mismatch",
                               "built_in_test"};
const char* const kModes[] = {"commissioning", "strict", "permissive"};
const char* const kPaths[] = {"tune", "aux", "cal"};
static_assert(sizeof kFaults / sizeof kFaults[0] == unsigned(Fault::Count), "a name for every fault");
}  // namespace

void EventLog::add(uint32_t time_s, bool wall, EventKind kind, uint8_t arg, State state, double mhz) {
    EventRecord& e = ring_[(next_ - 1) % kSize];
    e.seq = next_++;
    e.time_s = time_s;
    e.wall = wall;
    e.kind = kind;
    e.arg = arg;
    e.state = state;
    e.mhz = float(mhz);
}

int EventLog::since(uint32_t from, EventRecord out[], int cap) const {
    const uint32_t oldest = next_ > uint32_t(kSize) ? next_ - kSize : 1;
    int n = 0;
    for (uint32_t s = from > oldest ? from : oldest; s < next_ && n < cap; ++s) out[n++] = ring_[(s - 1) % kSize];
    return n;
}

size_t iso8601(uint32_t unix_s, char* out, size_t cap) {
    // Days to civil date (H. Hinnant's algorithm), valid for every date a uint32_t can hold.
    const uint32_t days = unix_s / 86400, sod = unix_s % 86400;
    const int64_t z = int64_t(days) + 719468, era = z / 146097;
    const unsigned doe = unsigned(z - era * 146097);
    const unsigned yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    const unsigned doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    const unsigned mp = (5 * doy + 2) / 153, d = doy - (153 * mp + 2) / 5 + 1, m = mp < 10 ? mp + 3 : mp - 9;
    const long y = long(yoe) + long(era) * 400 + (m <= 2);
    const int n = std::snprintf(out, cap, "%04ld-%02u-%02uT%02u:%02u:%02uZ", y, m, d, unsigned(sod / 3600),
                                unsigned(sod / 60 % 60), unsigned(sod % 60));
    return n < 0 ? 0 : size_t(n);
}

size_t EventLog::format(const EventRecord& e, char* out, size_t cap) {
    char t[24];
    if (e.wall) iso8601(e.time_s, t, sizeof t);
    else std::snprintf(t, sizeof t, "+%lus", static_cast<unsigned long>(e.time_s));
    const char* kind = unsigned(e.kind) < sizeof kKinds / sizeof kKinds[0] ? kKinds[unsigned(e.kind)] : "?";
    char what[40] = "";
    if (e.kind == EventKind::Fault && e.arg < unsigned(Fault::Count)) std::snprintf(what, sizeof what, " fault=%s", kFaults[e.arg]);
    else if (e.kind == EventKind::Mode && e.arg < 3) std::snprintf(what, sizeof what, " mode=%s", kModes[e.arg]);
    else if (e.kind == EventKind::Path && e.arg < 3) std::snprintf(what, sizeof what, " path=%s", kPaths[e.arg]);
    else if (e.kind == EventKind::Network) std::snprintf(what, sizeof what, " net=%s", e.arg ? "dhcp" : "static");
    else if (e.kind == EventKind::SelfTest && (e.arg == kSelfTestPassed || e.arg == kSelfTestStopped))
        std::snprintf(what, sizeof what, " result=%s", e.arg == kSelfTestPassed ? "passed" : "stopped");
    else if (e.kind == EventKind::SelfTest) {
        std::snprintf(what, sizeof what, " check=%s", bit::name(bit::Check(e.arg)));
        for (char* c = what + 7; *c; ++c)   // one token, as every field of the line is
            if (*c == ' ') *c = '_';
    }
    const int n = std::snprintf(out, cap, "seq=%lu t=%s event=%s%s state=%s mhz=%.4f",
                                static_cast<unsigned long>(e.seq), t, kind, what, state_name(e.state), double(e.mhz));
    return n < 0 ? 0 : size_t(n) < cap ? size_t(n) : cap - 1;
}

}  // namespace tuner
