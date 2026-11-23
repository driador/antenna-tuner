// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "net.hpp"

#include <Arduino.h>
#include <QNEthernet.h>
#include <qnethernet/QNDNSClient.h>

#include <cstdio>
#include <cstring>

#include "config.hpp"
#include "tuner/sntp.hpp"
#include "tuner/web.hpp"

using namespace qindesign::network;

namespace hw {

namespace {
enum class Kind : uint8_t { Free, Line, Http, Socket };

struct Session {
    Kind kind = Kind::Free;
    EthernetClient c;
    uint8_t rx[512];
    size_t n = 0;
    const char* page = nullptr;     // the page still to send, in pieces as the window allows
    size_t page_left = 0;
    float hz = 0;                   // SUBSCRIBE rate; 0 = none
    uint32_t next_tlm = 0, next_event = 0, opened_ms = 0;
};

constexpr int kSessions = 6;        // of lwIP's 8 TCP connections (listeners have their own); 2 for closing ones
constexpr uint32_t kHttpTimeoutMs = 5000, kPageTimeoutMs = 20000;

Session g_s[kSessions];
EthernetServer g_line(kLinePort), g_http(80);
EthernetUDP g_udp;
Net::Hooks g_hooks;
tuner::NetConfig g_running;          // what begin() was given; saved changes wait for a restart
const tuner::EventLog* g_log = nullptr;
enum class Ntp : uint8_t { Idle, Resolving, Waiting };
Ntp g_ntp = Ntp::Idle;
volatile bool g_resolved = false;    // the DNS callback has run; it never runs once its timeout passes
volatile uint32_t g_ntp_server = 0;  // what it found, or 0
uint32_t g_ntp_next = 0, g_ntp_since = 0;
bool g_udp_bound = false;

int who(const Session& s) { return int(&s - g_s); }

void drop(Session& s) {
    s.c.close();                    // close(), never stop(): stop() waits for the peer
    s = Session{};
    g_hooks.closed(who(s));
}

// §8C.7: the tuner's own subnet only, which also turns away anything port-forwarded in from outside.
bool local_peer(EthernetClient& c) {
    const uint32_t mask = uint32_t(Ethernet.subnetMask()), me = uint32_t(Ethernet.localIP());
    return me != 0 && (me & mask) == (uint32_t(c.remoteIP()) & mask);
}

// One protocol line, whole or not at all: as text on the TCP port, as a text frame on the WebSocket.
bool send_line(Session& s, const char* line, size_t n) {
    if (s.kind == Kind::Socket) {
        uint8_t frame[tuner::proto::kLineMax + 4];     // a 2- or 4-byte head
        const size_t m = tuner::web::text_frame(line, n, frame, sizeof frame);
        if (!m || s.c.availableForWrite() < int(m)) return false;
        return s.c.write(frame, m) == m;
    }
    if (s.c.availableForWrite() < int(n + 2)) return false;
    return s.c.write(reinterpret_cast<const uint8_t*>(line), n) == n && s.c.write("\r\n", 2) == 2;
}

void reply(Session& s, bool ok, const char* text) {
    char out[160];
    const size_t n = tuner::proto::reply(ok, text, out, sizeof out);
    if (n) send_line(s, out, n);     // a reply that does not fit is lost; the next QUERY tells
}

void handle(Session& s, const char* line, uint32_t now_ms) {
    using tuner::proto::Cmd;
    const tuner::proto::Request r = tuner::proto::parse(line);
    char out[tuner::proto::kLineMax];
    switch (r.cmd) {
        case Cmd::Query: {
            tuner::proto::Telemetry t;
            g_hooks.telemetry(t);
            t.next_event = g_log->next();
            const size_t n = tuner::proto::telemetry(t, out, sizeof out);
            if (n) send_line(s, out, n);
            return;
        }
        case Cmd::Subscribe:            // §8C.5: up to 20 Hz, at least one every 10 s; 0 stops it
            s.hz = r.value <= 0 ? 0 : r.value > 20 ? 20 : r.value < 0.1 ? 0.1f : float(r.value);
            s.next_tlm = now_ms;
            reply(s, true, "SUBSCRIBE");
            return;
        case Cmd::GetLog:               // from the oldest the ring still holds, up to the next to come
            s.next_event = r.value < 1 ? 1 : r.value > g_log->next() ? g_log->next() : uint32_t(r.value);
            reply(s, true, "GET_LOG");
            return;
        case Cmd::Net: {                // §8B.5.4: a change is saved for the next restart, never applied live
            if (r.net_fields) {
                const char* why = g_hooks.command(r);
                reply(s, !why, why ? why : "NET saved; the tuner uses it from the next restart");
                if (why) return;
            }
            tuner::NetConfig saved;
            g_hooks.network(saved);
            const IPAddress ip = Ethernet.localIP();
            const uint8_t now[4] = {ip[0], ip[1], ip[2], ip[3]};
            const size_t n = tuner::proto::network(saved, !tuner::net::same(saved, g_running), now, out, sizeof out);
            if (n) send_line(s, out, n);
            return;
        }
        case Cmd::UpdateStatus:
        case Cmd::UpdateBegin:
        case Cmd::UpdateEnd:
        case Cmd::UpdateAbort:
        case Cmd::UpdateRecord: {       // §8C.8: a record is answered only when it is refused
            bool ok = false;
            if (const char* text = g_hooks.update(r, who(s), ok)) reply(s, ok, text);
            return;
        }
        case Cmd::Invalid:
        case Cmd::LocalOnly:
            reply(s, false, r.why ? r.why : "refused");
            return;
        default: {
            const char* why = g_hooks.command(r);
            char name[48];                           // the command as given, without its checksum
            const size_t k = std::strcspn(line, "*");
            std::snprintf(name, sizeof name, "%.*s", int(k < sizeof name ? k : sizeof name - 1), line);
            reply(s, !why, why ? why : name);
            return;
        }
    }
}

// Lines from the TCP port: each ends in a newline; a carriage return before it is dropped.
void read_lines(Session& s, uint32_t now_ms) {
    while (s.c.available() > 0 && s.n < sizeof s.rx) s.rx[s.n++] = uint8_t(s.c.read());
    size_t start = 0;
    for (size_t i = 0; i < s.n; ++i) {
        if (s.rx[i] != '\n') continue;
        size_t end = i;
        if (end > start && s.rx[end - 1] == '\r') --end;
        s.rx[end] = 0;
        if (end > start) handle(s, reinterpret_cast<const char*>(s.rx + start), now_ms);
        start = i + 1;
    }
    std::memmove(s.rx, s.rx + start, s.n - start);
    s.n -= start;
    if (s.n == sizeof s.rx) {
        reply(s, false, "line too long");
        s.n = 0;
    }
}

void read_http(Session& s, uint32_t now_ms) {
    while (s.c.available() > 0 && s.n < sizeof s.rx - 1) s.rx[s.n++] = uint8_t(s.c.read());
    tuner::web::Request req;
    if (!tuner::web::parse_request(reinterpret_cast<const char*>(s.rx), s.n, req)) {
        if (s.n >= sizeof s.rx - 1 || now_ms - s.opened_ms > kHttpTimeoutMs) drop(s);
        return;
    }
    char head[256];
    if (req.websocket && !std::strcmp(req.path, "/ws")) {
        char accept[29];
        const size_t n = tuner::web::accept_key(req.key, accept) ? tuner::web::upgrade_head(head, sizeof head, accept) : 0;
        if (!n || s.c.write(reinterpret_cast<const uint8_t*>(head), n) != n) return drop(s);
        s.kind = Kind::Socket;
        s.n = 0;
        s.next_event = g_log->next();          // new events from now on; GET_LOG for the past
        return;
    }
    const bool get = !std::strcmp(req.method, "GET");
    const char* page = !get ? nullptr
                       : !std::strcmp(req.path, "/")      ? tuner::web::kPage
                       : !std::strcmp(req.path, "/meter") ? tuner::web::kMeter
                                                          : nullptr;
    const size_t len = page == tuner::web::kPage ? tuner::web::kPageLength : page ? tuner::web::kMeterLength : 0;
    const size_t n = tuner::web::response_head(head, sizeof head, page ? 200 : 404, "text/html; charset=utf-8", len);
    if (!n || s.c.write(reinterpret_cast<const uint8_t*>(head), n) != n || !page) return drop(s);   // Connection: close
    s.page = page;
    s.page_left = len;
    s.n = 0;
}

void read_frames(Session& s, uint32_t now_ms) {
    while (s.c.available() > 0 && s.n < sizeof s.rx) s.rx[s.n++] = uint8_t(s.c.read());
    for (;;) {
        tuner::web::Frame f;
        const tuner::web::Parse p = tuner::web::parse_frame(s.rx, s.n, f);
        if (p == tuner::web::Parse::Need) {
            if (s.n == sizeof s.rx) drop(s);          // nothing the tuner takes is that long
            return;
        }
        if (p == tuner::web::Parse::Bad || f.opcode == 0x8) {   // malformed, or a close
            uint8_t close[4];
            const size_t m = tuner::web::control_frame(0x8, nullptr, 0, close, sizeof close);
            if (s.c.availableForWrite() >= int(m)) s.c.write(close, m);
            return drop(s);
        }
        if (f.opcode == 0x9) {                       // ping: pong the same payload
            uint8_t pong[130];
            const size_t m = tuner::web::control_frame(0xA, f.payload, f.len, pong, sizeof pong);
            if (m && s.c.availableForWrite() >= int(m)) s.c.write(pong, m);
        } else if (f.opcode == 0x1) {                // text: one or more protocol lines
            char line[256];
            size_t k = 0;
            for (size_t i = 0; i <= f.len; ++i) {
                const char ch = i < f.len ? char(f.payload[i]) : '\n';
                if (ch == '\n' || k == sizeof line - 1) {
                    line[k] = 0;
                    if (k) handle(s, line, now_ms);
                    k = 0;
                } else if (ch != '\r') {
                    line[k++] = ch;
                }
            }
        }
        std::memmove(s.rx, s.rx + f.consumed, s.n - f.consumed);
        s.n -= f.consumed;
    }
}

// Events go out as they happen, by sequence, so nothing is skipped while the window is full (§8C.5).
void push(Session& s, uint32_t now_ms) {
    char out[tuner::proto::kLineMax];                // a TLM line is over 200 bytes
    while (s.next_event < g_log->next()) {
        tuner::EventRecord e;
        if (g_log->since(s.next_event, &e, 1) != 1) break;
        const size_t n = tuner::proto::event(e, out, sizeof out);
        if (!n || !send_line(s, out, n)) break;
        s.next_event = e.seq + 1;                    // past any the ring had already let go
    }
    if (s.hz > 0 && int32_t(now_ms - s.next_tlm) >= 0) {
        tuner::proto::Telemetry t;
        g_hooks.telemetry(t);
        t.next_event = g_log->next();
        const size_t n = tuner::proto::telemetry(t, out, sizeof out);
        if (n) send_line(s, out, n);                 // a full window drops one record, never an event
        s.next_tlm = now_ms + uint32_t(1000 / s.hz);
    }
}

void accept(EthernetServer& server, Kind kind, uint32_t now_ms) {
    EthernetClient c = server.accept();
    if (!c) return;
    if (!local_peer(c)) {
        c.close();
        return;
    }
    for (Session& s : g_s) {
        if (s.kind != Kind::Free) continue;
        s = Session{};
        s.kind = kind;
        s.c = c;
        s.opened_ms = now_ms;
        s.next_event = g_log->next();
        c.setNoDelay(true);
        return;
    }
    c.close();                                       // all sessions in use
}
}  // namespace

void Net::begin(const tuner::NetConfig& cfg, const tuner::EventLog* log, const Hooks& h) {
    g_log = log;
    g_hooks = h;
    g_running = cfg;
    Ethernet.setHostname(cfg.hostname);              // DHCP hostname; "tuner" unless configured (§8B.5.3)
    if (cfg.dhcp) {
        Ethernet.begin();                            // returns at once; the lease arrives later
    } else {
        Ethernet.begin(IPAddress(cfg.ip), IPAddress(cfg.netmask), IPAddress(cfg.gateway), IPAddress(cfg.dns));
    }
    g_line.begin();
    g_http.begin();
    MDNS.begin(cfg.hostname);                        // http://tuner.local/
    MDNS.addService("_http", "_tcp", 80);
}

bool Net::link() const { return Ethernet.linkState(); }

const tuner::NetConfig& Net::running() const { return g_running; }

void Net::address(char* out, size_t cap) const {
    const IPAddress ip = Ethernet.localIP();
    if (uint32_t(ip) == 0) std::snprintf(out, cap, "none");
    else std::snprintf(out, cap, "%u.%u.%u.%u", ip[0], ip[1], ip[2], ip[3]);
}

void Net::poll(uint32_t now_ms) {
    Ethernet.loop();
    accept(g_line, Kind::Line, now_ms);
    accept(g_http, Kind::Http, now_ms);
    for (Session& s : g_s) {
        if (s.kind == Kind::Free) continue;
        if (!s.c.connected() && s.c.available() <= 0) {
            drop(s);
            continue;
        }
        switch (s.kind) {
            case Kind::Line:
                read_lines(s, now_ms);
                if (s.kind == Kind::Line) push(s, now_ms);
                break;
            case Kind::Http:
                if (now_ms - s.opened_ms > kPageTimeoutMs) {   // a client that stopped reading
                    drop(s);
                } else if (s.page_left) {            // the page, as the window allows
                    const int room = s.c.availableForWrite();
                    const size_t m = room > 0 ? (size_t(room) < s.page_left ? size_t(room) : s.page_left) : 0;
                    if (m) {
                        const size_t w = s.c.write(reinterpret_cast<const uint8_t*>(s.page), m);
                        s.page += w;
                        s.page_left -= w;
                    }
                    if (!s.page_left) drop(s);       // Connection: close
                } else {
                    read_http(s, now_ms);
                }
                break;
            case Kind::Socket:
                read_frames(s, now_ms);
                if (s.kind == Kind::Socket) push(s, now_ms);
                break;
            case Kind::Free:
                break;
        }
    }
    ntp(now_ms);
}

void Net::ntp(uint32_t now_ms) {
    // The RTC, from pool.ntp.org: every minute until it is set, then every six hours. The name is looked up
    // each time, since the pool hands out a different server each time.
    constexpr uint32_t kRetryMs = 60000, kResyncMs = 6 * 3600000UL, kDnsMs = 5000, kReplyMs = 3000;
    if (uint32_t(Ethernet.localIP()) == 0) return;
    const auto next = [&](uint32_t ms) {
        g_ntp = Ntp::Idle;
        g_ntp_next = now_ms + ms;
    };
    switch (g_ntp) {
        case Ntp::Idle:
            if (int32_t(now_ms - g_ntp_next) < 0) return;
            g_resolved = false;
            g_ntp_server = 0;
            g_ntp_since = now_ms;
            g_ntp = Ntp::Resolving;                  // first: a cached name calls back before this returns
            if (!DNSClient::getHostByName("pool.ntp.org", [](const ip_addr_t* a) {
                    g_ntp_server = a ? ip_addr_get_ip4_u32(a) : 0;
                    g_resolved = true;
                }, kDnsMs))
                next(kRetryMs);
            return;
        case Ntp::Resolving: {
            if (!g_resolved) {
                if (now_ms - g_ntp_since > kDnsMs + 1000) next(kRetryMs);
                return;
            }
            uint8_t q[tuner::sntp::kPacket];
            tuner::sntp::request(q);
            if (!g_udp_bound) g_udp_bound = g_udp.begin(kNtpLocalPort);
            if (!g_ntp_server || !g_udp_bound || !g_udp.beginPacket(IPAddress(g_ntp_server), 123) ||
                g_udp.write(q, sizeof q) != sizeof q || !g_udp.endPacket())
                return next(kRetryMs);
            g_ntp = Ntp::Waiting;
            g_ntp_since = now_ms;
            return;
        }
        case Ntp::Waiting:
            // Only the server's own reply counts; anything else that reaches the port is dropped.
            for (int size; (size = g_udp.parsePacket()) >= 0;) {
                uint8_t reply[tuner::sntp::kPacket];
                if (uint32_t(g_udp.remoteIP()) != g_ntp_server || g_udp.remotePort() != 123 ||
                    size < int(sizeof reply) || g_udp.read(reply, sizeof reply) != int(sizeof reply))
                    continue;
                uint32_t t;
                if (!tuner::sntp::unix_time(reply, sizeof reply, t)) return next(kRetryMs);
                rtc_set(t);
                clock_set_ = true;
                return next(kResyncMs);
            }
            if (now_ms - g_ntp_since > kReplyMs) next(kRetryMs);
            return;
    }
}

}  // namespace hw
