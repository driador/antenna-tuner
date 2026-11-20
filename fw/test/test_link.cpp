// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The link (§8C.4, §8C.5): the line protocol and what it refuses, the WebSocket handshake and frames,
// the HTTP head, and the page.
#include <cstring>
#include <string>

#include "harness.hpp"
#include "tuner/proto.hpp"
#include "tuner/sntp.hpp"
#include "tuner/web.hpp"

using namespace tuner;

namespace {
std::string hex(const uint8_t* d, size_t n) {
    static const char k[] = "0123456789abcdef";
    std::string s;
    for (size_t i = 0; i < n; ++i) s += {k[d[i] >> 4], k[d[i] & 15]};
    return s;
}
std::string sha(const char* m) {
    uint8_t d[20];
    web::sha1(reinterpret_cast<const uint8_t*>(m), std::strlen(m), d);
    return hex(d, 20);
}
}  // namespace

TEST(protocol_commands_and_refusals) {
    using proto::Cmd;
    CHECK(proto::checksum("TUNE", 4) == 0x0A);
    CHECK(proto::parse("TUNE*0A").cmd == Cmd::Tune);
    CHECK(proto::parse("TUNE*0B").cmd == Cmd::Invalid && std::string(proto::parse("TUNE*0B").why) == "checksum");
    CHECK(proto::parse("tune\r\n").cmd == Cmd::Tune);                // by hand, with nc: no checksum
    CHECK(proto::parse("ack").cmd == Cmd::Ack && proto::parse("QUERY").cmd == Cmd::Query);
    CHECK(proto::parse("SUBSCRIBE").value == 10 && proto::parse("subscribe 20").value == 20);
    CHECK(proto::parse("GET_LOG 17").cmd == Cmd::GetLog && proto::parse("GET_LOG 17").value == 17);
    proto::Request r = proto::parse("path aux");
    CHECK(r.cmd == Cmd::Path && r.path == Path::Aux);
    CHECK(proto::parse("PATH HOME").cmd == Cmd::Invalid);
    r = proto::parse("CAL WATTS 100");
    CHECK(r.cmd == Cmd::CalWatts && r.value == 100);
    CHECK(proto::parse("cal save").cmd == Cmd::CalSave);
    // A number must be the whole word and finite, or the command is refused with its usage.
    for (const char* bad : {"SUBSCRIBE NAN", "SUBSCRIBE 5X", "GET_LOG INF", "GET_LOG X", "CAL WATTS NAN",
                            "CAL WATTS INF", "CAL WATTS 1E999", "CAL WATTS", "cal watts 100w"}) {
        r = proto::parse(bad);
        CHECK(r.cmd == Cmd::Invalid && r.why != nullptr);
    }
    CHECK(proto::parse("subscribe 0.5").value == 0.5 && proto::parse("CAL WATTS 1.5E3").value == 1500);
    for (const char* local : {"MODE PERMISSIVE", "CLEAR", "BYPASS", "JOG C1 1", "INSPECTED"})
        CHECK(proto::parse(local).cmd == Cmd::LocalOnly);
    CHECK(proto::parse("REBOOT").cmd == Cmd::Invalid && proto::parse("").cmd == Cmd::Invalid);
}

TEST(protocol_lines_carry_checksums) {
    proto::Telemetry t;
    t.state = State::Matched;
    t.mhz = 14.2051;
    t.carrier = true;
    t.swr = 1.12;
    t.at = {123.4e-12, 5.123e-6, 456.7e-12};
    t.latched_c = 0x0020;
    t.next_event = 12;
    char line[256];
    const size_t n = proto::telemetry(t, line, sizeof line);
    CHECK(n > 0);
    const std::string s(line, n);
    CHECK(s.rfind("TLM state=MATCHED path=TUNE mode=STRICT mhz=14.2051 carrier=1 swr=1.12 fwd=- c1=123.4 c2=456.7 "
                  "l=5.123", 0) == 0);
    CHECK(s.find(" c=0020 ") != std::string::npos && s.find(" ev=12*") != std::string::npos);
    CHECK(proto::parse(line).cmd == proto::Cmd::Invalid);              // a tuner line is not a command...
    CHECK(std::string(proto::parse(line).why) == "unknown command");   // ...but its checksum is good
    EventRecord e;
    e.seq = 3;
    e.kind = EventKind::Ack;
    char ev[128];
    CHECK(proto::event(e, ev, sizeof ev) > 0 && std::string(ev).rfind("EVT seq=3 t=+0s event=ack", 0) == 0);
    CHECK(proto::reply(false, "local only: at the box", ev, sizeof ev) > 0);
    CHECK(std::string(ev).rfind("ERR local only: at the box*", 0) == 0);
}

TEST(websocket_handshake) {
    CHECK(sha("") == "da39a3ee5e6b4b0d3255bfef95601890afd80709");
    CHECK(sha("abc") == "a9993e364706816aba3e25717850c26c9cd0d89d");
    CHECK(sha("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq") ==
          "84983e441c3bd26ebaae4aa1f95129e5e54670f1");                // padding runs into a second block
    char b[16];
    CHECK(web::base64(reinterpret_cast<const uint8_t*>("Man"), 3, b, sizeof b) == 4 && std::string(b) == "TWFu");
    web::base64(reinterpret_cast<const uint8_t*>("Ma"), 2, b, sizeof b);
    CHECK(std::string(b) == "TWE=");
    char accept[29];
    CHECK(web::accept_key("dGhlIHNhbXBsZSBub25jZQ==", accept));          // RFC 6455 §1.3's example
    CHECK(std::string(accept) == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=");
}

TEST(http_and_frames) {
    const char* up = "GET /ws HTTP/1.1\r\nHost: tuner\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                     "sec-websocket-key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n";
    web::Request r;
    CHECK(web::parse_request(up, std::strlen(up), r));
    CHECK(std::string(r.method) == "GET" && std::string(r.path) == "/ws" && r.websocket);
    CHECK(std::string(r.key) == "dGhlIHNhbXBsZSBub25jZQ==");
    CHECK(!web::parse_request(up, 40, r));                             // not all here yet
    const char* page = "GET / HTTP/1.1\r\nHost: tuner\r\n\r\n";
    CHECK(web::parse_request(page, std::strlen(page), r) && !r.websocket && std::string(r.path) == "/");

    uint8_t f[16] = {0x81, 0x84, 0x11, 0x22, 0x33, 0x44};               // "TUNE", masked as a browser sends it
    const char* msg = "TUNE";
    for (int i = 0; i < 4; ++i) f[6 + i] = uint8_t(msg[i] ^ f[2 + i % 4]);
    web::Frame fr;
    CHECK(web::parse_frame(f, 5, fr) == web::Parse::Need);
    CHECK(web::parse_frame(f, 10, fr) == web::Parse::Ok);
    CHECK(fr.opcode == 1 && fr.fin && fr.len == 4 && fr.consumed == 10 && !std::memcmp(fr.payload, "TUNE", 4));
    uint8_t plain[] = {0x81, 0x01, 'x'};
    CHECK(web::parse_frame(plain, 3, fr) == web::Parse::Bad);           // clients must mask
    uint8_t out[300];
    const std::string body(200, 'a');
    CHECK(web::text_frame(body.c_str(), body.size(), out, sizeof out) == 204 && out[1] == 126 && out[3] == 200);
    char head[256];
    CHECK(web::upgrade_head(head, sizeof head, "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=") > 0);
    CHECK(std::string(head).find("Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n\r\n") != std::string::npos);
}

TEST(page_speaks_only_what_the_link_may_carry) {
    const std::string page(web::kPage, web::kPageLength);
    CHECK(page.find("new WebSocket(\"ws://\"+location.host+\"/ws\")") != std::string::npos);
    CHECK(page.find("send(\"SUBSCRIBE") != std::string::npos && page.find("GET_LOG") != std::string::npos);
    for (const char* never : {"\"MODE", "\"CLEAR", "\"BYPASS", "\"JOG"}) CHECK(page.find(never) == std::string::npos);
    CHECK(page.find("href=\"https://github.com/driador/antenna-tuner\"") != std::string::npos);   // AGPL s13
}

TEST(network_time) {
    uint8_t q[sntp::kPacket];
    sntp::request(q);
    CHECK(q[0] == 0x1B && q[1] == 0 && q[47] == 0);
    uint8_t r[sntp::kPacket] = {};
    r[0] = 0x24;                                        // LI 0, version 4, mode 4: a server
    r[1] = 2;                                           // stratum 2
    const uint32_t ntp = 1795183391UL + 2208988800UL;   // 2026-11-20T14:03:11Z
    for (int i = 0; i < 4; ++i) r[40 + i] = uint8_t(ntp >> (24 - 8 * i));
    uint32_t t = 0;
    CHECK(sntp::unix_time(r, sizeof r, t) && t == 1795183391UL);
    r[1] = 0;                                           // kiss-of-death
    CHECK(!sntp::unix_time(r, sizeof r, t));
    r[1] = 2;
    r[0] = 0xE4;                                        // leap indicator 3: not synchronized
    CHECK(!sntp::unix_time(r, sizeof r, t));
    CHECK(!sntp::unix_time(r, 40, t));
    r[0] = 0x24;
    const auto at = [&](uint32_t s) {                   // the transmit time's seconds, as sent
        for (int i = 0; i < 4; ++i) r[40 + i] = uint8_t(s >> (24 - 8 * i));
    };
    at(123010304UL);                                    // 2040-01-01T00:00:00Z: past the 2036 rollover
    CHECK(sntp::unix_time(r, sizeof r, t) && t == 2208988800UL);
    at(0);                                              // no transmit time
    CHECK(!sntp::unix_time(r, sizeof r, t));
    at(978307200UL + 2208988800UL);                     // 2001: not a real answer now
    CHECK(!sntp::unix_time(r, sizeof r, t));
}
