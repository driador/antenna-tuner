// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Storage and records (§8B.4a-1, §8B.5, §8C.6): the qualification, the event log, JSON, the SD mirror,
// /recovery.cfg and backup rotation.
#include <cstring>
#include <string>

#include "harness.hpp"
#include "tuner/events.hpp"
#include "tuner/json.hpp"
#include "tuner/mirror.hpp"
#include "tuner/qualify.hpp"

using namespace tuner;

TEST(qualification_gates_permissive) {
    Qualification q;
    for (int i = 0; i < 100; ++i) q.tune_completed(i % 3);     // three bands only
    q.powered(50 * 3600);
    q.record_inspection();
    CHECK(!q.met() && q.band_count() == 3);
    q.tune_completed(5);                                      // a fourth
    CHECK(q.met());
    q.mechanical_fault();                                     // a limit hit starts the period over
    CHECK(!q.met() && q.tunes == 0 && q.powered_s == 0 && !q.inspected);
    Qualification r;
    for (int i = 0; i < 99; ++i) r.tune_completed(i % 4);
    r.powered(50 * 3600);
    r.record_inspection();
    CHECK(!r.met());                                          // 99 is not 100
}

TEST(event_log_replays_what_a_client_missed) {
    EventLog log;
    for (int i = 0; i < 10; ++i) log.add(1000 + i, false, EventKind::Fault, uint8_t(Fault::OverSwr), State::Matched, 14.2);
    EventRecord got[16];
    CHECK(log.since(8, got, 16) == 3 && got[0].seq == 8 && got[2].seq == 10);
    CHECK(log.since(11, got, 16) == 0);
    for (int i = 0; i < 200; ++i) log.add(2000 + i, false, EventKind::Tuned, 0, State::Matched, 7.1);
    CHECK(log.next() == 211);
    CHECK(log.since(1, got, 16) == 16 && got[0].seq == 211 - EventLog::kSize);   // only what the ring holds
    char line[128];
    EventRecord e;
    e.seq = 7;
    e.time_s = 1795183391;                                    // 2026-11-20T14:03:11Z
    e.wall = true;
    e.kind = EventKind::Fault;
    e.arg = uint8_t(Fault::LimitHit);
    e.state = State::Move;
    e.mhz = 14.2051f;
    EventLog::format(e, line, sizeof line);
    CHECK(std::string(line) == "seq=7 t=2026-11-20T14:03:11Z event=fault fault=limit_hit state=MOVE mhz=14.2051");
    char t[24];
    iso8601(0, t, sizeof t);
    CHECK(std::string(t) == "1970-01-01T00:00:00Z");
    iso8601(951782400, t, sizeof t);                          // a leap day
    CHECK(std::string(t) == "2000-02-29T00:00:00Z");
}

TEST(json_writes_and_finds) {
    char buf[256];
    JsonWriter w(buf, sizeof buf);
    w.open().str("name", "say \"hi\"").num("x", 1.5).open("inner").integer("n", -3).boolean("b", true).close();
    w.open_array("list").num(nullptr, 1).num(nullptr, 2).open().str("k", "v").close().close_array().null("z").close();
    CHECK(w.ok());
    CHECK(std::string(buf) ==
          "{\"name\":\"say \\\"hi\\\"\",\"x\":1.5,\"inner\":{\"n\":-3,\"b\":true},\"list\":[1,2,{\"k\":\"v\"}],\"z\":null}");
    double v;
    bool b;
    char s[32];
    CHECK(json_number(buf, "inner.n", v) && v == -3);
    CHECK(json_bool(buf, "inner.b", b) && b);
    CHECK(json_number(buf, "list.1", v) && v == 2);
    CHECK(json_string(buf, "list.2.k", s, sizeof s) && std::string(s) == "v");
    CHECK(json_string(buf, "name", s, sizeof s) && std::string(s) == "say \"hi\"");
    CHECK(!json_number(buf, "list.3", v) && !json_number(buf, "nothing", v) && !json_number(buf, "z", v));
    char small[16];
    JsonWriter t(small, sizeof small);
    t.open().str("long", "too long to fit").close();
    CHECK(!t.ok());
}

TEST(mirror_round_trip) {
    static Settings s, r;                                     // large: keep them off the stack
    s.tuner_id = 0x1234abcd5678ef90ULL;
    s.net.dhcp = false;
    std::strcpy(s.net.hostname, "tuner-garage");
    const uint8_t ip[4] = {192, 168, 7, 20};
    std::memcpy(s.net.ip, ip, 4);
    s.retune_swr = 1.6;
    s.policy = Mode::Commissioning;
    s.qual.tunes = 42;
    s.qual.bands = 0x25;
    s.qual.inspected = true;
    s.bridge[5].valid = true;
    s.bridge[5].scale.v_center = 0.917;
    s.bridge[5].floor_db = -27.5;
    s.power[5].insert(0.4, 10);
    s.power[5].insert(1.2, 100);
    s.prior_ok[17] = true;
    s.priors[17] = Prior{cplx(143.8, 319.0), Setting{58.85e-12, 5.089e-6, 661.1e-12}};
    static char doc[16384];
    const size_t n = write_mirror(s, "2026-11-20T14:03:11Z", doc, sizeof doc);
    CHECK(n > 0);
    CHECK(read_mirror(doc, r) == nullptr);
    CHECK(r.tuner_id == s.tuner_id && !r.net.dhcp && std::string(r.net.hostname) == "tuner-garage");
    CHECK(std::memcmp(r.net.ip, ip, 4) == 0 && r.net.netmask[0] == 255);
    CHECK_NEAR(r.retune_swr, 1.6, 1e-9);
    CHECK(r.policy == Mode::Commissioning && r.qual.tunes == 42 && r.qual.bands == 0x25 && r.qual.inspected);
    CHECK(r.bridge[5].valid && !r.bridge[4].valid);
    CHECK_NEAR(r.bridge[5].scale.v_center, 0.917, 1e-6);
    CHECK_NEAR(r.bridge[5].floor_db, -27.5, 1e-6);
    CHECK(r.power[5].n == 2 && r.power[4].n == 0);
    CHECK_NEAR(r.power[5].at(1.2), 100, 1e-6);
    CHECK(r.prior_ok[17] && !r.prior_ok[16]);
    CHECK_NEAR(r.priors[17].at.l, 5.089e-6, 1e-12);
    CHECK_NEAR(r.priors[17].z_load.imag(), 319.0, 1e-4);
    CHECK(read_mirror("{\"saved\":\"x\"}", r) != nullptr);   // not a mirror of any tuner
    CHECK(write_mirror(s, "", doc, 64) == 0);                 // never a truncated file
}

TEST(recovery_restores_reachability_and_nothing_else) {
    NetConfig net;
    net.dhcp = false;
    std::strcpy(net.hostname, "wrong");
    char report[96];
    const char* cfg = "# /recovery.cfg\nnet.mode = dhcp\nhostname = tuner\nfault.policy = permissive\n"
                      "calibration = x\n";
    CHECK(read_recovery(cfg, net, report, sizeof report));
    CHECK(net.dhcp && std::string(net.hostname) == "tuner");
    CHECK(std::string(report) == "refused fault.policy; refused calibration");
    NetConfig keep = net;
    CHECK(!read_recovery("ip = 300.1.1.1\n", keep, report, sizeof report));   // nothing valid: untouched
    CHECK(keep.dhcp);
    CHECK(read_recovery("net.mode = static\nip = 192.168.7.20\nnetmask = 255.255.255.0\n", keep, report, sizeof report));
    CHECK(!keep.dhcp && keep.ip[0] == 192 && keep.ip[3] == 20);
    const NetConfig before = keep;                      // one the tuner could not run on: refused whole
    CHECK(!read_recovery("net.mode = static\nip = 10.0.0.5\nnetmask = 255.255.255.0\ngateway = 10.0.1.1\n",
                         keep, report, sizeof report));
    CHECK(std::string(report).find("unusable: gateway") == 0 && net::same(keep, before));
    CHECK(!read_recovery("mode = dhcp\n", keep, report, sizeof report));   // the key is net.mode here
}

TEST(backup_rotation) {
    uint32_t n;
    CHECK(backup_number("000123.json", n) && n == 123);
    CHECK(backup_number("000124-20261120T140311.json", n) && n == 124);
    CHECK(!backup_number("current.json", n) && !backup_number("tuner.id", n));
    uint32_t have[25], drop[25];
    for (int i = 0; i < 25; ++i) have[i] = uint32_t((i * 7) % 25 + 100);   // 100-124, shuffled
    const int k = backups_to_prune(have, 25, drop, 25);
    CHECK(k == 5);
    for (int i = 0; i < k; ++i) CHECK(drop[i] < 105);        // the five oldest
    CHECK(backups_to_prune(have, 20, drop, 25) == 0);
}
