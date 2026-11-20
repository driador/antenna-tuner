// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/panel_io.hpp"

#include <cstdio>

namespace tuner {

int Quadrature::update(bool a, bool b) {
    static const int8_t kStep[16] = {0, +1, -1, 0, -1, 0, 0, +1, +1, 0, 0, -1, 0, -1, +1, 0};
    const uint8_t now = uint8_t((a ? 2 : 0) | (b ? 1 : 0));
    if (!started_) {
        started_ = true;
        last_ = now;
        return 0;
    }
    acc_ += kStep[(last_ << 2) | now];
    last_ = now;
    int detents = 0;
    while (acc_ >= per_) {
        acc_ -= per_;
        ++detents;
    }
    while (acc_ <= -per_) {
        acc_ += per_;
        --detents;
    }
    return detents;
}

namespace nextion {

namespace {
size_t terminate(char* out, size_t cap, size_t n) {
    if (n + 3 > cap) return 0;
    out[n] = out[n + 1] = out[n + 2] = char(0xFF);
    return n + 3;
}
}  // namespace

size_t command(char* out, size_t cap, const char* instruction) {
    const int n = std::snprintf(out, cap, "%s", instruction);
    return n < 0 || size_t(n) >= cap ? 0 : terminate(out, cap, size_t(n));
}

size_t set_text(char* out, size_t cap, const char* object, const char* text) {
    int n = std::snprintf(out, cap, "%s.txt=\"", object);
    if (n < 0 || size_t(n) >= cap) return 0;
    size_t i = size_t(n);
    for (const char* p = text; *p; ++p) {
        const bool esc = *p == '"' || *p == '\\';
        if (i + (esc ? 2 : 1) + 1 + 3 > cap) break;     // room for the closing quote and terminator
        if (esc) out[i++] = '\\';
        out[i++] = *p;
    }
    out[i++] = '"';
    return terminate(out, cap, i);
}

size_t set_number(char* out, size_t cap, const char* object, const char* attribute, long value) {
    const int n = std::snprintf(out, cap, "%s.%s=%ld", object, attribute, value);
    return n < 0 || size_t(n) >= cap ? 0 : terminate(out, cap, size_t(n));
}

bool Parser::feed(uint8_t byte, Event& e) {
    if (byte == 0xFF) {
        if (++ff_ < 3) return false;
        const bool done = n_ > 0;
        if (done) {
            e = Event{};
            e.code = buf_[0];
            if (e.code == 0x65 && n_ >= 4) {
                e.page = buf_[1];
                e.component = buf_[2];
                e.press = buf_[3];
            }
        }
        n_ = 0;
        ff_ = 0;
        return done;
    }
    // A stray 0xFF inside a frame belongs to it: put back what the terminator count swallowed.
    while (ff_ > 0 && n_ < sizeof buf_) {
        buf_[n_++] = 0xFF;
        --ff_;
    }
    ff_ = 0;
    if (n_ < sizeof buf_) buf_[n_++] = byte;
    return false;
}

}  // namespace nextion
}  // namespace tuner
