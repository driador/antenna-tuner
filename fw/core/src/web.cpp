// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/web.hpp"

#include <cstdio>
#include <cstring>
#include <strings.h>

namespace tuner::web {

namespace {
uint32_t rol(uint32_t v, int s) { return (v << s) | (v >> (32 - s)); }

// Finds a header's value in a request head (case-insensitive name); copies it trimmed.
bool header(const char* head, size_t n, const char* name, char* out, size_t cap) {
    const size_t len = std::strlen(name);
    for (const char* p = head; p < head + n;) {
        const char* eol = static_cast<const char*>(std::memchr(p, '\n', size_t(head + n - p)));
        if (!eol) break;
        if (size_t(eol - p) > len && p[len] == ':' && strncasecmp(p, name, len) == 0) {
            const char* v = p + len + 1;
            while (v < eol && *v == ' ') ++v;
            const char* e = eol;
            while (e > v && (e[-1] == '\r' || e[-1] == ' ')) --e;
            const size_t m = size_t(e - v) < cap - 1 ? size_t(e - v) : cap - 1;
            std::memcpy(out, v, m);
            out[m] = 0;
            return true;
        }
        p = eol + 1;
    }
    return false;
}
}  // namespace

void sha1(const uint8_t* data, size_t n, uint8_t out[20]) {
    uint32_t h[5] = {0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0};
    const uint64_t bits = uint64_t(n) * 8;
    const size_t total = ((n + 8) / 64 + 1) * 64;
    for (size_t off = 0; off < total; off += 64) {
        uint32_t w[80];
        for (int i = 0; i < 16; ++i) {
            uint32_t v = 0;
            for (int j = 0; j < 4; ++j) {
                const size_t k = off + size_t(i * 4 + j);
                uint8_t b = k < n ? data[k] : k == n ? 0x80 : 0;
                if (k >= total - 8) b = uint8_t(bits >> (8 * (total - 1 - k)));
                v = (v << 8) | b;
            }
            w[i] = v;
        }
        for (int i = 16; i < 80; ++i) w[i] = rol(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1);
        uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4];
        for (int i = 0; i < 80; ++i) {
            const uint32_t f = i < 20 ? (b & c) | (~b & d) : i < 40 ? b ^ c ^ d : i < 60 ? (b & c) | (b & d) | (c & d) : b ^ c ^ d;
            const uint32_t k = i < 20 ? 0x5A827999 : i < 40 ? 0x6ED9EBA1 : i < 60 ? 0x8F1BBCDC : 0xCA62C1D6;
            const uint32_t t = rol(a, 5) + f + e + k + w[i];
            e = d;
            d = c;
            c = rol(b, 30);
            b = a;
            a = t;
        }
        h[0] += a;
        h[1] += b;
        h[2] += c;
        h[3] += d;
        h[4] += e;
    }
    for (int i = 0; i < 20; ++i) out[i] = uint8_t(h[i / 4] >> (24 - 8 * (i % 4)));
}

size_t base64(const uint8_t* data, size_t n, char* out, size_t cap) {
    static const char kA[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    const size_t need = (n + 2) / 3 * 4;
    if (need + 1 > cap) return 0;
    size_t o = 0;
    for (size_t i = 0; i < n; i += 3) {
        const uint32_t v = uint32_t(data[i]) << 16 | (i + 1 < n ? uint32_t(data[i + 1]) << 8 : 0) |
                           (i + 2 < n ? data[i + 2] : 0);
        out[o++] = kA[v >> 18 & 63];
        out[o++] = kA[v >> 12 & 63];
        out[o++] = i + 1 < n ? kA[v >> 6 & 63] : '=';
        out[o++] = i + 2 < n ? kA[v & 63] : '=';
    }
    out[o] = 0;
    return o;
}

bool accept_key(const char* client_key, char out[29]) {
    static const char kGuid[] = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
    char joined[96];
    const int n = std::snprintf(joined, sizeof joined, "%s%s", client_key, kGuid);
    if (n < 0 || size_t(n) >= sizeof joined) return false;
    uint8_t digest[20];
    sha1(reinterpret_cast<const uint8_t*>(joined), size_t(n), digest);
    return base64(digest, 20, out, 29) == 28;
}

bool parse_request(const char* head, size_t n, Request& r) {
    r = Request{};
    const char* end = nullptr;
    for (size_t i = 0; i + 4 <= n; ++i)
        if (!std::memcmp(head + i, "\r\n\r\n", 4)) {
            end = head + i + 4;
            break;
        }
    if (!end) return false;
    const size_t len = size_t(end - head);
    if (std::sscanf(head, "%7s %63s", r.method, r.path) != 2) return false;
    char upgrade[16] = {}, key[32] = {};
    if (header(head, len, "Upgrade", upgrade, sizeof upgrade) && strcasecmp(upgrade, "websocket") == 0 &&
        header(head, len, "Sec-WebSocket-Key", key, sizeof key) && key[0]) {
        r.websocket = true;
        std::memcpy(r.key, key, sizeof r.key);
    }
    return true;
}

size_t response_head(char* out, size_t cap, int status, const char* type, size_t length) {
    const char* reason = status == 200 ? "OK" : status == 404 ? "Not Found" : "Bad Request";
    const int n = std::snprintf(out, cap,
                                "HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %lu\r\n"
                                "Cache-Control: no-store\r\nConnection: close\r\n\r\n",
                                status, reason, type, static_cast<unsigned long>(length));
    return n < 0 || size_t(n) >= cap ? 0 : size_t(n);
}

size_t upgrade_head(char* out, size_t cap, const char* accept) {
    const int n = std::snprintf(out, cap,
                                "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                                "Sec-WebSocket-Accept: %s\r\n\r\n",
                                accept);
    return n < 0 || size_t(n) >= cap ? 0 : size_t(n);
}

size_t control_frame(uint8_t opcode, const uint8_t* payload, size_t n, uint8_t* out, size_t cap) {
    if (n > 125 || n + 2 > cap) return 0;
    out[0] = uint8_t(0x80 | (opcode & 0x0F));
    out[1] = uint8_t(n);
    if (n) std::memcpy(out + 2, payload, n);
    return n + 2;
}

size_t text_frame(const char* payload, size_t n, uint8_t* out, size_t cap) {
    const size_t head = n < 126 ? 2 : n < 65536 ? 4 : 10;
    if (head + n > cap) return 0;
    out[0] = 0x81;
    if (head == 2) {
        out[1] = uint8_t(n);
    } else if (head == 4) {
        out[1] = 126;
        out[2] = uint8_t(n >> 8);
        out[3] = uint8_t(n);
    } else {
        out[1] = 127;
        for (int i = 0; i < 8; ++i) out[2 + i] = uint8_t(uint64_t(n) >> (56 - 8 * i));
    }
    std::memcpy(out + head, payload, n);
    return head + n;
}

Parse parse_frame(uint8_t* buf, size_t n, Frame& f) {
    if (n < 2) return Parse::Need;
    f.fin = buf[0] & 0x80;
    f.opcode = buf[0] & 0x0F;
    const bool masked = buf[1] & 0x80;
    if (!masked) return Parse::Bad;                  // a client must mask (§5.1)
    size_t len = buf[1] & 0x7F, pos = 2;
    if (len == 126) {
        if (n < 4) return Parse::Need;
        len = size_t(buf[2]) << 8 | buf[3];
        pos = 4;
    } else if (len == 127) {
        return Parse::Bad;                           // nothing the tuner accepts is that long
    }
    if (n < pos + 4 + len) return Parse::Need;
    const uint8_t* mask = buf + pos;
    f.payload = buf + pos + 4;
    for (size_t i = 0; i < len; ++i) f.payload[i] ^= mask[i % 4];
    f.len = len;
    f.consumed = pos + 4 + len;
    return Parse::Ok;
}

}  // namespace tuner::web
