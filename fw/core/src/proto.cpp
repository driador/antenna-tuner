// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/proto.hpp"

#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace tuner::proto {

namespace {
const char* const kMode[] = {"COMMISSIONING", "STRICT", "PERMISSIVE"};

// The words of a command line, upper-cased, at most four.
int words(const char* line, size_t n, char w[4][16]) {
    int k = 0;
    size_t i = 0;
    while (i < n && k < 4) {
        while (i < n && line[i] == ' ') ++i;
        if (i >= n) break;
        size_t j = 0;
        while (i < n && line[i] != ' ') {
            if (j < 15) w[k][j++] = char(std::toupper(static_cast<unsigned char>(line[i])));
            ++i;
        }
        w[k++][j] = 0;
    }
    return k;
}

Request refuse(const char* why) {
    Request r;
    r.why = why;
    return r;
}

// A number that is the whole word and finite. "NAN", "INF" and "5X" are refused rather than read as 0.
bool number(const char* w, double& out) {
    char* end;
    out = std::strtod(w, &end);
    return end != w && *end == 0 && std::isfinite(out);
}
}  // namespace

uint8_t checksum(const char* s, size_t n) {
    uint8_t c = 0;
    for (size_t i = 0; i < n; ++i) c ^= uint8_t(s[i]);
    return c;
}

size_t seal(char* buf, size_t len, size_t cap) {
    if (len + 4 > cap) return 0;
    std::snprintf(buf + len, cap - len, "*%02X", checksum(buf, len));
    return len + 3;
}

Request parse(const char* line) {
    Request r;
    size_t n = std::strcspn(line, "\r\n");
    if (const char* star = static_cast<const char*>(std::memchr(line, '*', n))) {
        const size_t body = size_t(star - line);
        char* end;
        const unsigned long given = std::strtoul(star + 1, &end, 16);
        if (end != star + 3 || given != checksum(line, body)) {
            r.why = "checksum";
            return r;
        }
        n = body;
    }
    // NET carries key=value pairs, longer than the words below and with a hostname's case, so it is
    // taken first.
    if (n >= 3 && std::toupper(static_cast<unsigned char>(line[0])) == 'N' &&
        std::toupper(static_cast<unsigned char>(line[1])) == 'E' &&
        std::toupper(static_cast<unsigned char>(line[2])) == 'T' && (n == 3 || line[3] == ' ')) {
        static const char kUsage[] = "NET [mode=dhcp|static] [hostname=] [ip=] [netmask=] [gateway=] [dns=]";
        char buf[200];
        if (n >= sizeof buf) return refuse("NET: line too long");
        std::memcpy(buf, line, n);
        buf[n] = 0;
        r.cmd = Cmd::Net;
        for (size_t i = 3; i < n; ++i) {
            if (buf[i] == ' ') continue;
            char* key = buf + i;
            while (i < n && buf[i] != ' ') ++i;
            buf[i] = 0;                                  // buf[n] is already 0
            char* eq = std::strchr(key, '=');
            if (!eq) return refuse(kUsage);
            *eq = 0;
            uint8_t field = 0;
            if (const char* why = net::assign(key, eq + 1, r.net, field)) return refuse(why);
            r.net_fields |= field;
        }
        return r;
    }
    char w[4][16] = {};
    const int k = words(line, n, w);
    if (k == 0) {
        r.why = "empty";
        return r;
    }
    auto is = [&](int i, const char* s) { return i < k && !std::strcmp(w[i], s); };
    if (is(0, "TUNE")) r.cmd = Cmd::Tune;
    else if (is(0, "ACK")) r.cmd = Cmd::Ack;
    else if (is(0, "QUERY")) r.cmd = Cmd::Query;
    else if (is(0, "SUBSCRIBE")) {
        r.cmd = Cmd::Subscribe;
        r.value = 10;
        if (k > 1 && !number(w[1], r.value)) r = refuse("SUBSCRIBE [hz]");
    } else if (is(0, "GET_LOG")) {
        r.cmd = Cmd::GetLog;
        if (k > 1 && !number(w[1], r.value)) r = refuse("GET_LOG [from]");
    } else if (is(0, "PRESET")) {
        r.cmd = Cmd::Preset;
        if (k < 2 || !number(w[1], r.value)) r = refuse("PRESET <MHz>");
    } else if (is(0, "PATH")) {
        r.cmd = Cmd::Path;
        if (is(1, "TUNE")) r.path = Path::Tune;
        else if (is(1, "AUX")) r.path = Path::Aux;
        else if (is(1, "CAL")) r.path = Path::Cal;
        else r = refuse("PATH TUNE|AUX|CAL");
    } else if (is(0, "CAL")) {
        if (is(1, "LOAD")) r.cmd = Cmd::CalLoad;
        else if (is(1, "OPEN")) r.cmd = Cmd::CalOpen;
        else if (is(1, "SHORT")) r.cmd = Cmd::CalShort;
        else if (is(1, "SAVE")) r.cmd = Cmd::CalSave;
        else if (is(1, "WATTS") && k > 2 && number(w[2], r.value)) r.cmd = Cmd::CalWatts;
        else r = refuse("CAL LOAD|OPEN|SHORT|SAVE|WATTS <w>");
    } else if (is(0, "MODE") || is(0, "CLEAR") || is(0, "BYPASS") || is(0, "JOG") || is(0, "INSPECTED")) {
        r.cmd = Cmd::LocalOnly;
        r.why = "local only: at the box";
    } else {
        r.why = "unknown command";
    }
    return r;
}

size_t telemetry(const Telemetry& t, char* out, size_t cap) {
    char fwd[16];
    if (t.fwd_w >= 0) std::snprintf(fwd, sizeof fwd, "%.0f", t.fwd_w);
    else std::snprintf(fwd, sizeof fwd, "-");
    const int n = std::snprintf(out, cap,
                                "TLM state=%s path=%s mode=%s mhz=%.4f carrier=%d swr=%.2f fwd=%s c1=%.1f c2=%.1f "
                                "l=%.3f tank=%.1f c=%04X b=%04X permit=%d bypass=%d ev=%lu",
                                state_name(t.state), path_name(t.path), kMode[unsigned(t.mode) % 3], t.mhz,
                                t.carrier, t.swr, fwd, t.at.c1 * 1e12, t.at.c2 * 1e12, t.at.l * 1e6, t.tank_c,
                                t.latched_c, t.unacked_b, t.permit, t.bypass, static_cast<unsigned long>(t.next_event));
    if (n < 0 || size_t(n) >= cap) return 0;
    return seal(out, size_t(n), cap);
}

size_t event(const EventRecord& e, char* out, size_t cap) {
    if (cap < 8) return 0;
    std::memcpy(out, "EVT ", 4);
    const size_t n = EventLog::format(e, out + 4, cap - 4);
    return seal(out, 4 + n, cap);
}

size_t network(const NetConfig& saved, bool pending, const uint8_t now[4], char* out, size_t cap) {
    char cfg[160], ip[16];
    if (!net::format(saved, cfg, sizeof cfg)) return 0;
    net::ip_text(now, ip);
    const int n = std::snprintf(out, cap, "NET %s now=%s pending=%d", cfg, ip, pending ? 1 : 0);
    if (n < 0 || size_t(n) >= cap) return 0;
    return seal(out, size_t(n), cap);
}

size_t reply(bool ok, const char* text, char* out, size_t cap) {
    const int n = std::snprintf(out, cap, "%s %s", ok ? "OK" : "ERR", text);
    if (n < 0 || size_t(n) >= cap) return 0;
    return seal(out, size_t(n), cap);
}

}  // namespace tuner::proto
