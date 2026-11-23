// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The web side of the link (§8C.4): GET / serves the page, GET /meter the bench meter, and GET /ws
// upgrades to a WebSocket that carries the same lines as the TCP port (proto.hpp). Just enough HTTP/1.1
// and RFC 6455 for that, without the heap.
#pragma once
#include <cstddef>
#include <cstdint>

namespace tuner::web {

void sha1(const uint8_t* data, size_t n, uint8_t out[20]);
size_t base64(const uint8_t* data, size_t n, char* out, size_t cap);
// Sec-WebSocket-Accept for a client's Sec-WebSocket-Key (RFC 6455 §4.2.2): 28 characters.
bool accept_key(const char* client_key, char out[29]);

struct Request {
    char method[8] = {};
    char path[64] = {};
    bool websocket = false;        // Upgrade: websocket, with a key
    char key[32] = {};             // Sec-WebSocket-Key
};

// Parses a request head; false until the blank line that ends it has arrived (or it is malformed).
bool parse_request(const char* head, size_t n, Request& r);
size_t response_head(char* out, size_t cap, int status, const char* type, size_t length);
size_t upgrade_head(char* out, size_t cap, const char* accept);

// Frames. The tuner sends unmasked text frames; a client's frames are masked (§5.3) and are unmasked in
// place. Control frames (close, ping) are reported with their opcode.
size_t text_frame(const char* payload, size_t n, uint8_t* out, size_t cap);
size_t control_frame(uint8_t opcode, const uint8_t* payload, size_t n, uint8_t* out, size_t cap);
enum class Parse : uint8_t { Need, Ok, Bad };
struct Frame {
    uint8_t opcode = 0;
    bool fin = false;
    uint8_t* payload = nullptr;
    size_t len = 0;
    size_t consumed = 0;           // bytes of the buffer the frame used
};
Parse parse_frame(uint8_t* buf, size_t n, Frame& f);

extern const char kPage[];         // the UI page, served at /
extern const size_t kPageLength;
extern const char kMeter[];        // the bench meter, served at /meter
extern const size_t kMeterLength;

}  // namespace tuner::web
