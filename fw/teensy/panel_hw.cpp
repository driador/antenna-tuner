// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "panel_hw.hpp"

#include <Arduino.h>

#include <cstdio>
#include <cstring>

#include "tuner/pins.hpp"

namespace iox = tuner::pins::iox;

namespace hw {

namespace {
constexpr uint32_t kDebounceMs = 20;
constexpr long kWhite = 65535, kBlack = 0, kYellow = 65504;   // RGB565

void send(size_t n, const char* buf) {
    if (n) Serial8.write(reinterpret_cast<const uint8_t*>(buf), n);
}

void colors(int row, long bco, long pco) {
    char obj[12], buf[32];
    std::snprintf(obj, sizeof obj, "t%d", row);
    send(tuner::nextion::set_number(buf, sizeof buf, obj, "bco", bco), buf);
    send(tuner::nextion::set_number(buf, sizeof buf, obj, "pco", pco), buf);
}
}  // namespace

void PanelHw::begin() {
    // A whole screen is about 400 bytes: buffered, so drawing never waits on the UART in the tick.
    static uint8_t tx[1024];
    Serial8.addMemoryForWrite(tx, sizeof tx);
    Serial8.begin(kNextionBaud);
    char buf[16];
    send(tuner::nextion::command(buf, sizeof buf, "page 0"), buf);
    stale_ = true;
}

void PanelHw::input(uint16_t word, uint32_t now_ms, tuner::Panel& p) {
    static const uint8_t kA[2] = {iox::ENC1_A, iox::ENC2_A}, kB[2] = {iox::ENC1_B, iox::ENC2_B},
                         kPush[2] = {iox::ENC1_PUSH, iox::ENC2_PUSH};
    for (int k = 0; k < 2; ++k) {                      // knob 0 left, 1 right
        const int d = knob_[k].update(word & (1u << kA[k]), word & (1u << kB[k]));
        if (d) p.turn(k, d);
        const bool down = !(word & (1u << kPush[k]));   // pulled up: pressed reads low
        if (down != raw_[k]) {
            raw_[k] = down;
            since_[k] = now_ms;
        } else if (down != pressed_[k] && now_ms - since_[k] >= kDebounceMs) {
            pressed_[k] = down;
            if (down) p.push(k);
        }
    }
}

void PanelHw::draw(const tuner::Panel& p) {
    char rows[tuner::Panel::kRows][tuner::Panel::kCols + 1];
    int highlight;
    p.render(rows, highlight);
    char obj[12], buf[96];
    for (int r = 0; r < tuner::Panel::kRows; ++r) {
        if (!stale_ && std::strcmp(rows[r], sent_[r]) == 0) continue;
        std::snprintf(obj, sizeof obj, "t%d", r);
        send(tuner::nextion::set_text(buf, sizeof buf, obj, rows[r]), buf);
        std::memcpy(sent_[r], rows[r], sizeof rows[r]);
    }
    if (stale_ || highlight != sent_highlight_) {
        if (sent_highlight_ >= 0) colors(sent_highlight_, kBlack, kWhite);
        if (highlight >= 0) colors(highlight, kYellow, kBlack);
        sent_highlight_ = highlight;
    }
    stale_ = false;
}

void PanelHw::flush() { Serial8.flush(); }

void PanelHw::poll() {
    tuner::nextion::Event e;
    while (Serial8.available()) {
        // Replies are read and dropped: the panel is driven by the knobs. A display that restarted
        // announces itself (0x88, ready), so everything is sent again.
        if (parser_.feed(uint8_t(Serial8.read()), e) && e.code == 0x88) stale_ = true;
    }
}

}  // namespace hw
