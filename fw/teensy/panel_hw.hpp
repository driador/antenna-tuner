// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The local panel's hardware (§7.5): the Nextion NX4832K035 on Serial8 and the two Grayhill 62V15
// encoders through the MCP23017. The display is a terminal; its HMI is one page of ten text rows,
// t0-t9 (fw/README.md, "The panel's HMI"), and every screen is drawn by tuner::Panel.
#pragma once
#include <cstdint>

#include "config.hpp"
#include "tuner/panel.hpp"
#include "tuner/panel_io.hpp"

namespace hw {

class PanelHw {
public:
    void begin();
    // A fresh MCP23017 sample: the knobs' quadrature and their pushes, debounced, into the panel.
    void input(uint16_t iox, uint32_t now_ms, tuner::Panel& p);
    void draw(const tuner::Panel& p);   // sends only the rows, and the highlight, that changed
    void poll();                        // drains the display's replies
    void flush();                       // waits until what was drawn has gone out

private:
    tuner::Quadrature knob_[2] = {tuner::Quadrature(kEdgesPerDetent), tuner::Quadrature(kEdgesPerDetent)};
    bool raw_[2] = {}, pressed_[2] = {};
    uint32_t since_[2] = {};
    char sent_[tuner::Panel::kRows][tuner::Panel::kCols + 1] = {};
    int sent_highlight_ = -2;
    bool stale_ = true;
    tuner::nextion::Parser parser_;
};

}  // namespace hw
