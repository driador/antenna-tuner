// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "persist.hpp"

#include <EEPROM.h>

#include <cstring>

#include "config.hpp"

namespace hw {

namespace {
constexpr uint32_t kMagic = 0x544E5233;   // "TNR3"
constexpr uint16_t kVersion = 3;
constexpr int kHeader = 16;               // magic, version, body length, CRC, sequence
constexpr int kAuthBody = 8 + 5 + 11 + 49 + tuner::kBandCount * (1 + 5 * 4 + 1 + kPowerPoints * 2 * 4);
constexpr int kConvBody = 3 * 4 + tuner::kSegments * (1 + 5 * 4);
constexpr int kAuthSlot = kHeader + kAuthBody;
constexpr int kConvAt = 2 * kAuthSlot;    // after the two authoritative copies
static_assert(kConvAt + kHeader + kConvBody <= 4284, "Teensy 4.1 EEPROM");

uint32_t crc32(const uint8_t* p, int n) {
    uint32_t c = 0xFFFFFFFF;
    while (n--) {
        c ^= *p++;
        for (int k = 0; k < 8; ++k) c = (c >> 1) ^ (0xEDB88320 & (0 - (c & 1)));
    }
    return ~c;
}

struct Writer {
    uint8_t* p;
    template <typename T>
    void put(const T& v) {
        std::memcpy(p, &v, sizeof v);
        p += sizeof v;
    }
    void f(double v) { put(float(v)); }
};

struct Reader {
    const uint8_t* p;
    template <typename T>
    void get(T& v) {
        std::memcpy(&v, p, sizeof v);
        p += sizeof v;
    }
    double f() {
        float v;
        get(v);
        return v;
    }
};

// One stored record: magic, version, body length, CRC, sequence, then the body. The sequence sits
// right before the body so that the CRC covers both as one run.
struct Record {
    int at, body;
    uint8_t image[kHeader + (kAuthBody > kConvBody ? kAuthBody : kConvBody)];
    uint32_t seq;

    bool blank() const {                  // nothing ever written here: the magic is absent
        uint32_t magic;
        std::memcpy(&magic, image, 4);
        return magic != kMagic;
    }
    bool read() {
        for (int i = 0; i < kHeader + body; ++i) image[i] = EEPROM.read(at + i);
        Reader h{image};
        uint32_t magic, crc;
        uint16_t version, length;
        h.get(magic);
        h.get(version);
        h.get(length);
        h.get(crc);
        h.get(seq);
        return magic == kMagic && version == kVersion && length == body && crc == crc32(image + 12, 4 + body);
    }
    void write(const uint8_t* new_body, uint32_t new_seq) {
        seq = new_seq;
        std::memcpy(image + 12, &seq, 4);
        std::memcpy(image + kHeader, new_body, body);
        Writer h{image};
        h.put(kMagic);
        h.put(kVersion);
        h.put(uint16_t(body));
        h.put(crc32(image + 12, 4 + body));
        // The body first and the header last: a reset between them leaves a bad CRC, not a record
        // that looks good and is not.
        for (int i = kHeader; i < kHeader + body; ++i) EEPROM.update(at + i, image[i]);
        for (int i = 0; i < kHeader; ++i) EEPROM.update(at + i, image[i]);
    }
};

Record g_auth[2] = {{0, kAuthBody, {}, 0}, {kAuthSlot, kAuthBody, {}, 0}};
Record g_conv = {kConvAt, kConvBody, {}, 0};
int g_auth_current = -1;                  // the good copy with the newer sequence, -1 when none
bool g_conv_valid = false;

void encode(const Authoritative& a, uint8_t* out) {
    Writer w{out};
    w.put(a.tuner_id);
    w.put(a.faults.latched_c);
    w.put(a.faults.unacked_b);
    w.put(uint8_t(a.faults.mode));
    w.put(a.qual.tunes);
    w.put(a.qual.bands);
    w.put(a.qual.powered_s);
    w.put(uint8_t(a.qual.inspected));
    w.put(uint8_t(a.net.dhcp));
    for (char c : a.net.hostname) w.put(c);
    for (const uint8_t* ip : {a.net.ip, a.net.netmask, a.net.gateway, a.net.dns})
        for (int i = 0; i < 4; ++i) w.put(ip[i]);
    for (int b = 0; b < tuner::kBandCount; ++b) {
        const tuner::BridgeCal& c = a.bridge[b];
        w.put(uint8_t(c.valid));
        for (double v : {c.scale.v_center, c.scale.v_per_db, c.scale.v_phs_zero, c.scale.v_per_deg, c.floor_db}) w.f(v);
        const tuner::Curve& p = a.power[b];
        const int n = p.n < kPowerPoints ? p.n : kPowerPoints;
        w.put(uint8_t(n));
        for (int i = 0; i < kPowerPoints; ++i) {
            w.f(i < n ? p.x[i] : 0);
            w.f(i < n ? p.y[i] : 0);
        }
    }
}

void decode(const uint8_t* in, Authoritative& a) {
    Reader r{in};
    uint8_t mode, valid, n, flag;
    r.get(a.tuner_id);
    r.get(a.faults.latched_c);
    r.get(a.faults.unacked_b);
    r.get(mode);
    a.faults.mode = tuner::Mode(mode);
    r.get(a.qual.tunes);
    r.get(a.qual.bands);
    r.get(a.qual.powered_s);
    r.get(flag);
    a.qual.inspected = flag;
    r.get(flag);
    a.net.dhcp = flag;
    for (char& c : a.net.hostname) r.get(c);
    a.net.hostname[sizeof a.net.hostname - 1] = 0;
    for (uint8_t* ip : {a.net.ip, a.net.netmask, a.net.gateway, a.net.dns})
        for (int i = 0; i < 4; ++i) r.get(ip[i]);
    for (int b = 0; b < tuner::kBandCount; ++b) {
        tuner::BridgeCal& c = a.bridge[b];
        r.get(valid);
        c.valid = valid;
        c.scale.v_center = r.f();
        c.scale.v_per_db = r.f();
        c.scale.v_phs_zero = r.f();
        c.scale.v_per_deg = r.f();
        c.floor_db = r.f();
        r.get(n);
        tuner::Curve& p = a.power[b];
        p = tuner::Curve{};
        for (int i = 0; i < kPowerPoints; ++i) {
            const double x = r.f(), y = r.f();
            if (i < n) p.add(x, y);
        }
    }
}

void encode(const Convenience& c, uint8_t* out) {
    Writer w{out};
    for (float t : c.last_turns) w.put(t);
    for (int i = 0; i < tuner::kSegments; ++i) {
        w.put(uint8_t(c.prior_ok[i]));
        const tuner::Prior& p = c.priors[i];
        for (double v : {p.z_load.real(), p.z_load.imag(), p.at.c1, p.at.l, p.at.c2}) w.f(v);
    }
}

void decode(const uint8_t* in, Convenience& c) {
    Reader r{in};
    uint8_t ok;
    for (float& t : c.last_turns) r.get(t);
    for (int i = 0; i < tuner::kSegments; ++i) {
        r.get(ok);
        c.prior_ok[i] = ok;
        const double re = r.f(), im = r.f(), c1 = r.f(), l = r.f(), c2 = r.f();
        c.priors[i] = tuner::Prior{tuner::cplx(re, im), tuner::Setting{c1, l, c2}};
    }
}
}  // namespace

Loaded load(Authoritative& a) {
    const bool ok0 = g_auth[0].read(), ok1 = g_auth[1].read();
    if (ok0 && ok1) g_auth_current = int32_t(g_auth[1].seq - g_auth[0].seq) > 0 ? 1 : 0;
    else g_auth_current = ok0 ? 0 : ok1 ? 1 : -1;
    if (g_auth_current < 0) return g_auth[0].blank() && g_auth[1].blank() ? Loaded::Blank : Loaded::Corrupt;
    decode(g_auth[g_auth_current].image + kHeader, a);
    return Loaded::Ok;
}

bool load(Convenience& c) {
    g_conv_valid = g_conv.read();
    if (g_conv_valid) decode(g_conv.image + kHeader, c);
    return g_conv_valid;
}

void save(const Authoritative& a) {
    uint8_t body[kAuthBody];
    encode(a, body);
    if (g_auth_current >= 0 && std::memcmp(body, g_auth[g_auth_current].image + kHeader, kAuthBody) == 0) return;
    const uint32_t seq = g_auth_current >= 0 ? g_auth[g_auth_current].seq + 1 : 1;
    const int next = g_auth_current == 0 ? 1 : 0;     // the older copy, or the first when there is none
    g_auth[next].write(body, seq);
    g_auth_current = next;
}

bool save(const Convenience& c) {
    uint8_t body[kConvBody];
    encode(c, body);
    if (g_conv_valid && std::memcmp(body, g_conv.image + kHeader, kConvBody) == 0) return false;
    g_conv.write(body, g_conv.seq + 1);
    g_conv_valid = true;
    return true;
}

}  // namespace hw
