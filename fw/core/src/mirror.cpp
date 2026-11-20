// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/mirror.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "tuner/json.hpp"

namespace tuner {

namespace {
const char* const kPolicy[] = {"commissioning", "strict", "permissive"};

void ip_text(const uint8_t a[4], char* out) { std::sprintf(out, "%u.%u.%u.%u", a[0], a[1], a[2], a[3]); }

bool parse_ip(const char* s, uint8_t out[4]) {
    unsigned v[4];
    char tail;
    if (std::sscanf(s, "%u.%u.%u.%u%c", &v[0], &v[1], &v[2], &v[3], &tail) != 4) return false;
    for (int i = 0; i < 4; ++i) {
        if (v[i] > 255) return false;
        out[i] = uint8_t(v[i]);
    }
    return true;
}

// "calibration.ad8302.20m.v_center" and the like, built in one place.
const char* path(char* buf, size_t cap, const char* a, const char* b = nullptr, const char* c = nullptr,
                 const char* d = nullptr) {
    std::snprintf(buf, cap, "%s%s%s%s%s%s%s", a, b ? "." : "", b ? b : "", c ? "." : "", c ? c : "", d ? "." : "",
                  d ? d : "");
    return buf;
}
}  // namespace

size_t write_mirror(const Settings& s, const char* saved, char* out, size_t cap) {
    JsonWriter w(out, cap);
    char id[20], a[16];
    std::snprintf(id, sizeof id, "%016llx", static_cast<unsigned long long>(s.tuner_id));
    w.open().str("tuner_id", id).str("saved", saved ? saved : "");
    w.open("network").str("mode", s.net.dhcp ? "dhcp" : "static").str("hostname", s.net.hostname);
    ip_text(s.net.ip, a);
    w.str("ip", a);
    ip_text(s.net.netmask, a);
    w.str("netmask", a);
    ip_text(s.net.gateway, a);
    w.str("gateway", a);
    ip_text(s.net.dns, a);
    w.str("dns", a).close();
    w.open("thresholds").num("retune_swr", s.retune_swr).num("retune_freq_pct", s.window_pct).close();
    w.open("fault").str("policy", kPolicy[unsigned(s.policy) < 3 ? unsigned(s.policy) : 1]).close();
    w.open("qualification")
        .integer("tunes", s.qual.tunes)
        .integer("bands", s.qual.bands)
        .integer("powered_s", s.qual.powered_s)
        .boolean("inspected", s.qual.inspected)
        .close();
    w.open("calibration").open("ad8302");
    for (int b = 0; b < kBandCount; ++b) {
        const BridgeCal& c = s.bridge[b];
        w.open(kBands[b].name)
            .boolean("valid", c.valid)
            .num("v_center", c.scale.v_center)
            .num("v_per_db", c.scale.v_per_db)
            .num("v_phs_zero", c.scale.v_phs_zero)
            .num("v_per_deg", c.scale.v_per_deg)
            .num("floor_db", c.floor_db)
            .close();
    }
    w.close().open("detector_curves");
    for (int b = 0; b < kBandCount; ++b) {
        w.open_array(kBands[b].name);
        for (int i = 0; i < s.power[b].n; ++i)
            w.open_array().num(nullptr, s.power[b].x[i]).num(nullptr, s.power[b].y[i]).close_array();
        w.close_array();
    }
    w.close().close();
    w.open_array("profiles");
    for (int i = 0; i < kSegments; ++i) {
        if (!s.prior_ok[i]) continue;
        const Prior& p = s.priors[i];
        w.open()
            .integer("seg", i)
            .num("z_re", p.z_load.real())
            .num("z_im", p.z_load.imag())
            .num("c1", p.at.c1)
            .num("l", p.at.l)
            .num("c2", p.at.c2)
            .close();
    }
    w.close_array().close();
    return w.ok() ? w.size() : 0;
}

const char* read_mirror(const char* doc, Settings& s) {
    Settings r;
    char buf[64], p[64], idx[12];
    if (!json_string(doc, "tuner_id", buf, sizeof buf) || !(r.tuner_id = std::strtoull(buf, nullptr, 16)))
        return "no tuner_id";
    if (json_string(doc, "network.mode", buf, sizeof buf)) r.net.dhcp = std::strcmp(buf, "static") != 0;
    json_string(doc, "network.hostname", r.net.hostname, sizeof r.net.hostname);
    const struct {
        const char* key;
        uint8_t* ip;
    } ips[] = {{"network.ip", r.net.ip}, {"network.netmask", r.net.netmask}, {"network.gateway", r.net.gateway},
               {"network.dns", r.net.dns}};
    for (const auto& e : ips)
        if (json_string(doc, e.key, buf, sizeof buf) && !parse_ip(buf, e.ip)) return "bad address in network";
    json_number(doc, "thresholds.retune_swr", r.retune_swr);
    json_number(doc, "thresholds.retune_freq_pct", r.window_pct);
    if (json_string(doc, "fault.policy", buf, sizeof buf))
        for (int m = 0; m < 3; ++m)
            if (!std::strcmp(buf, kPolicy[m])) r.policy = Mode(m);
    double v;
    if (json_number(doc, "qualification.tunes", v)) r.qual.tunes = uint32_t(v);
    if (json_number(doc, "qualification.bands", v)) r.qual.bands = uint16_t(v);
    if (json_number(doc, "qualification.powered_s", v)) r.qual.powered_s = uint32_t(v);
    json_bool(doc, "qualification.inspected", r.qual.inspected);
    for (int b = 0; b < kBandCount; ++b) {
        BridgeCal& c = r.bridge[b];
        const char* n = kBands[b].name;
        json_bool(doc, path(p, sizeof p, "calibration.ad8302", n, "valid"), c.valid);
        json_number(doc, path(p, sizeof p, "calibration.ad8302", n, "v_center"), c.scale.v_center);
        json_number(doc, path(p, sizeof p, "calibration.ad8302", n, "v_per_db"), c.scale.v_per_db);
        json_number(doc, path(p, sizeof p, "calibration.ad8302", n, "v_phs_zero"), c.scale.v_phs_zero);
        json_number(doc, path(p, sizeof p, "calibration.ad8302", n, "v_per_deg"), c.scale.v_per_deg);
        json_number(doc, path(p, sizeof p, "calibration.ad8302", n, "floor_db"), c.floor_db);
        for (int i = 0; i < Curve::kMax; ++i) {
            std::snprintf(idx, sizeof idx, "%d", i);
            double x, y;
            if (!json_number(doc, path(p, sizeof p, "calibration.detector_curves", n, idx, "0"), x) ||
                !json_number(doc, path(p, sizeof p, "calibration.detector_curves", n, idx, "1"), y))
                break;
            r.power[b].add(x, y);
        }
    }
    for (int i = 0;; ++i) {
        std::snprintf(idx, sizeof idx, "%d", i);
        double seg, re, im, c1, l, c2;
        if (!json_number(doc, path(p, sizeof p, "profiles", idx, "seg"), seg)) break;
        if (!json_number(doc, path(p, sizeof p, "profiles", idx, "z_re"), re) ||
            !json_number(doc, path(p, sizeof p, "profiles", idx, "z_im"), im) ||
            !json_number(doc, path(p, sizeof p, "profiles", idx, "c1"), c1) ||
            !json_number(doc, path(p, sizeof p, "profiles", idx, "l"), l) ||
            !json_number(doc, path(p, sizeof p, "profiles", idx, "c2"), c2))
            return "incomplete profile";
        const int k = int(seg);
        if (k < 0 || k >= kSegments) return "profile segment out of range";
        r.prior_ok[k] = true;
        r.priors[k] = Prior{cplx(re, im), Setting{c1, l, c2}};
    }
    s = r;
    return nullptr;
}

bool read_recovery(const char* text, NetConfig& net, char* report, size_t cap) {
    NetConfig n = net;
    bool any = false;
    size_t used = 0;
    if (cap) report[0] = 0;
    for (const char* line = text; *line;) {
        const char* end = std::strchr(line, '\n');
        if (!end) end = line + std::strlen(line);
        char buf[96];
        size_t len = size_t(end - line) < sizeof buf - 1 ? size_t(end - line) : sizeof buf - 1;
        std::memcpy(buf, line, len);
        buf[len] = 0;
        line = *end ? end + 1 : end;
        if (char* hash = std::strchr(buf, '#')) *hash = 0;
        char* eq = std::strchr(buf, '=');
        if (!eq) continue;
        *eq = 0;
        char key[48], value[48];
        if (std::sscanf(buf, " %47s", key) != 1) continue;
        if (std::sscanf(eq + 1, " %47s", value) != 1) value[0] = 0;
        bool ok = true;
        if (!std::strcmp(key, "net.mode")) {
            ok = !std::strcmp(value, "dhcp") || !std::strcmp(value, "static");
            if (ok) n.dhcp = !std::strcmp(value, "dhcp");
        } else if (!std::strcmp(key, "hostname")) {
            ok = value[0] != 0;
            if (ok) std::snprintf(n.hostname, sizeof n.hostname, "%s", value);
        } else if (!std::strcmp(key, "ip")) {
            ok = parse_ip(value, n.ip);
        } else if (!std::strcmp(key, "netmask")) {
            ok = parse_ip(value, n.netmask);
        } else if (!std::strcmp(key, "gateway")) {
            ok = parse_ip(value, n.gateway);
        } else if (!std::strcmp(key, "dns")) {
            ok = parse_ip(value, n.dns);
        } else {
            ok = false;                                // not a network key: recovery cannot touch it
        }
        if (ok) {
            any = true;
        } else if (used + std::strlen(key) + 12 < cap) {
            used += size_t(std::snprintf(report + used, cap - used, "%srefused %s", used ? "; " : "", key));
        }
    }
    if (any) net = n;
    return any;
}

bool backup_number(const char* name, uint32_t& n) {
    char* end;
    const unsigned long v = std::strtoul(name, &end, 10);
    if (end == name || (*end != '.' && *end != '-')) return false;
    n = uint32_t(v);
    return true;
}

int backups_to_prune(const uint32_t* have, int n, uint32_t* drop, int cap) {
    int out = 0;
    for (int i = 0; i < n; ++i) {
        int newer = 0;                                 // how many backups are newer than this one
        for (int j = 0; j < n; ++j) newer += have[j] > have[i];
        if (newer >= kKeepBackups && out < cap) drop[out++] = have[i];
    }
    return out;
}

}  // namespace tuner
