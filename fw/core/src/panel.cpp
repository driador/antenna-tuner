// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/panel.hpp"

#include <cstdarg>
#include <cstdio>

#include "tuner/bit.hpp"
#include "tuner/freq.hpp"

namespace tuner {

namespace {
const char* const kMenu[] = {"Faults", "Tune now", "RF path", "Fault policy", "Calibrate this band",
                             "Jog elements", "Self-test", "< back"};
const char* const kModes[] = {"COMMISSIONING", "STRICT", "PERMISSIVE"};
const char* const kPaths[] = {"TUNE", "AUX", "CAL"};
const char* const kCalSteps[] = {"1 load: CAL, key ~10 W", "2 open at AUX, key", "3 short at AUX, key",
                                 "4 save this band"};
constexpr int kMenuItems = 8, kChoices = 4, kPolicyItems = 7, kCalItems = 5, kJogItems = 4;
constexpr int kMaxEntries = 2 * int(Fault::Count) + 1;   // every fault as C or B, and the over-temperature

const char* explain(Fault f) {
    switch (f) {
        case Fault::OverTemp: return "tank hot: blower full, PTT off";
        case Fault::NoSolution: return "no setting fits: band? antenna?";
        case Fault::TuneFailed: return "three attempts did not match";
        case Fault::OverSwr: return "SWR trip while transmitting";
        case Fault::LimitHit: return "look at the axis first";
        case Fault::EncoderMismatch: return "check coupler, belt, magnet";
        case Fault::SelfTestFail: return "see the USB console report";
        case Fault::RelayMismatch: return "K1/K2 did not follow command";
        case Fault::BuiltInTest: return "a detector is off at rest";
        default: return "";
    }
}

struct Entry {
    char cls;
    Fault f;
};

// The faults to show, latched first: C, then unacknowledged B, then an active over-temperature.
int entries(const PanelView& v, Entry out[]) {
    int n = 0;
    for (unsigned i = 0; i < unsigned(Fault::Count); ++i)
        if (v.latched_c & (1u << i)) out[n++] = {'C', Fault(i)};
    for (unsigned i = 0; i < unsigned(Fault::Count); ++i)
        if (v.unacked_b & (1u << i)) out[n++] = {'B', Fault(i)};
    if (v.over_temp) out[n++] = {'A', Fault::OverTemp};
    return n;
}

void put(char row[], const char* fmt, ...) __attribute__((format(printf, 2, 3)));
void put(char row[], const char* fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    std::vsnprintf(row, Panel::kCols + 1, fmt, ap);
    va_end(ap);
}
}  // namespace

int Panel::items() const {
    switch (screen_) {
        case Screen::Monitor: return 0;
        case Screen::Menu: return kMenuItems;
        case Screen::Faults: {
            Entry e[kMaxEntries];
            const int n = entries(view_, e);
            return 2 * n + (n > 0 && (view_.latched_c || view_.unacked_b) ? 1 : 0);
        }
        case Screen::Path: return kChoices;
        case Screen::Policy: return kPolicyItems;
        case Screen::Cal: return kCalItems;
        case Screen::Jog: return kJogItems;
    }
    return 0;
}

bool Panel::selectable(int i) const {
    // The fault list's last line is Confirm, reached only by scrolling through every line above it.
    if (screen_ == Screen::Faults && i == items() - 1 && (view_.latched_c || view_.unacked_b))
        return deepest_ >= i - 1;
    return i >= 0 && i < items();
}

void Panel::open(Screen s) {
    if (screen_ == Screen::Menu) menu_cursor_ = cursor_;
    screen_ = s;
    cursor_ = deepest_ = s == Screen::Menu ? menu_cursor_ : 0;
}

void Panel::request(PanelAction a, int arg, int detents) {
    req_.action = a;
    req_.arg = arg;
    req_.detents = detents;
}

void Panel::turn(int knob, int detents) {
    if (detents == 0) return;
    if (knob == 1) {                                   // right knob: jog the selected axis
        if (screen_ != Screen::Jog || cursor_ > 2) return;
        if (req_.action == PanelAction::Jog && req_.arg == cursor_) req_.detents += detents;
        else request(PanelAction::Jog, cursor_, detents);
        return;
    }
    const int step = detents > 0 ? 1 : -1;
    for (int k = 0; k != detents; k += step) {         // one line per detent, so nothing is skipped
        const int next = cursor_ + step;
        if (!selectable(next)) break;
        cursor_ = next;
        if (cursor_ > deepest_) deepest_ = cursor_;
    }
}

void Panel::push(int knob) {
    ++presses_;
    if (knob == 1) {                                   // right push: back
        open(screen_ == Screen::Menu || screen_ == Screen::Monitor ? Screen::Monitor : Screen::Menu);
        return;
    }
    switch (screen_) {
        case Screen::Monitor:
            open(Screen::Menu);
            break;
        case Screen::Menu: {
            static const Screen kTo[] = {Screen::Faults, Screen::Monitor, Screen::Path, Screen::Policy,
                                         Screen::Cal, Screen::Jog, Screen::Monitor, Screen::Monitor};
            if (cursor_ == 1) request(PanelAction::Tune);
            if (cursor_ == 6) request(PanelAction::SelfTest);   // §8B.4h, from the box
            open(kTo[cursor_]);
            break;
        }
        case Screen::Faults:
            if (cursor_ == items() - 1 && (view_.latched_c || view_.unacked_b)) {
                request(view_.latched_c ? PanelAction::ClearLocal : PanelAction::Ack);
                open(Screen::Monitor);
            }
            break;
        case Screen::Path:
            if (cursor_ < 3) request(PanelAction::SetPath, cursor_);
            open(cursor_ < 3 ? Screen::Monitor : Screen::Menu);
            break;
        case Screen::Policy:                           // 3 and 4 are the qualification, read only
            if (cursor_ < 3) {
                request(PanelAction::SetMode, cursor_);
                open(Screen::Monitor);
            } else if (cursor_ == 5) {
                request(PanelAction::Inspected);
            } else if (cursor_ == 6) {
                open(Screen::Menu);
            }
            break;
        case Screen::Cal: {
            static const PanelAction kStep[] = {PanelAction::CalLoad, PanelAction::CalOpen, PanelAction::CalShort,
                                                PanelAction::CalSave};
            if (cursor_ < 4) request(kStep[cursor_]);
            else open(Screen::Menu);
            break;
        }
        case Screen::Jog:
            if (cursor_ == 3) open(Screen::Menu);
            break;
    }
}

PanelRequest Panel::take() {
    const PanelRequest r = req_;
    req_ = PanelRequest{};
    return r;
}

void Panel::render(char rows[kRows][kCols + 1], int& highlight) const {
    for (int r = 0; r < kRows; ++r) rows[r][0] = 0;
    const PanelView& v = view_;
    const Band* band = band_of(v.mhz);
    const char* band_name = band ? band->name : "--";
    char lines[2 * kMaxEntries + 1][kCols + 1] = {};
    int n = 0;
    const char* title = "";
    const char* hint = "left: select  right push: back";

    switch (screen_) {
        case Screen::Monitor: {
            put(rows[0], "%s %s %s%s", state_name(v.state), v.mode == Mode::Commissioning ? "COMMISSION"
                                                            : v.mode == Mode::Strict      ? "STRICT"
                                                                                          : "PERMISSIVE",
                path_name(v.path), v.bypass ? " BYPASS" : "");
            put(rows[1], "%.4f MHz %s %s", v.mhz, band_name, v.carrier ? "carrier" : "");
            if (v.fwd_w >= 0) put(rows[2], "SWR %.2f  fwd %.0f W", v.swr, v.fwd_w);
            else put(rows[2], "SWR %.2f  fwd --", v.swr);
            put(rows[3], "C1 %.1f pF  C2 %.1f pF", v.at.c1 * 1e12, v.at.c2 * 1e12);
            put(rows[4], "L %.3f uH", v.at.l * 1e6);
            put(rows[5], "tank %.1f C%s", v.tank_c, v.over_temp ? "  HOT" : "");
            Entry e[kMaxEntries];
            const int nf = entries(v, e);
            if (nf == 0) put(rows[6], "faults: none");
            else put(rows[6], "faults: %d (Menu > Faults)", nf);
            put(rows[7], "bridge cal %s  card %s", v.cal_valid ? "ok" : "not done",
                v.card > 0 ? "ok" : v.card < 0 ? "FOREIGN" : "NONE");
            put(rows[kRows - 1], "%s", v.note ? v.note : "left push: menu");
            highlight = -1;
            return;
        }
        case Screen::Menu:
            title = "MENU";
            for (; n < kMenuItems; ++n) put(lines[n], "%s", kMenu[n]);
            break;
        case Screen::Faults: {
            title = "FAULTS";
            Entry e[kMaxEntries];
            const int nf = entries(v, e);
            for (int i = 0; i < nf; ++i) {
                char named[kCols + 1];
                put(lines[n++], "%c  %s", e[i].cls, fault_name(e[i].f));
                put(lines[n++], "   %s", bit::names(bit::behind(v.bit_failed, e[i].f), named, sizeof named) ? named
                                                                                                      : explain(e[i].f));
            }
            if (v.latched_c || v.unacked_b) {
                const bool ready = deepest_ >= n - 1;
                put(lines[n++], "%s", !ready ? "(scroll to the end)"
                                      : v.latched_c ? "[ clear at the box ]" : "[ acknowledge ]");
            }
            if (nf == 0) put(lines[n++], "no faults");
            break;
        }
        case Screen::Path:
            title = v.path_busy ? "RF PATH (changing)" : "RF PATH";
            for (; n < 3; ++n) put(lines[n], "%c %s", int(v.path) == n ? '*' : ' ', kPaths[n]);
            put(lines[n++], "< back");
            break;
        case Screen::Policy:                           // §8B.4f.1: the criteria, and whether they are met
            title = "FAULT POLICY (at the box only)";
            for (; n < 3; ++n) put(lines[n], "%c %s%s", int(v.mode) == n ? '*' : ' ', kModes[n],
                                   n == 2 && !v.q_met ? " (not qualified)" : "");
            put(lines[n++], "  tunes %lu/100, bands %d/4", static_cast<unsigned long>(v.q_tunes), v.q_bands);
            put(lines[n++], "  hours %.1f/50, inspected %s", v.q_hours, v.q_inspected ? "yes" : "no");
            put(lines[n++], "Record roller inspection");
            put(lines[n++], "< back");
            break;
        case Screen::Cal:
            title = "CALIBRATE";
            for (; n < 4; ++n)
                put(lines[n], "%c %s", n < 3 && (v.cal_have & (1 << n)) ? '+' : ' ', kCalSteps[n]);
            put(lines[n++], "< back");
            break;
        case Screen::Jog:
            title = "JOG  (right knob turns)";
            put(lines[n++], "C1 %.1f pF", v.at.c1 * 1e12);
            put(lines[n++], "C2 %.1f pF", v.at.c2 * 1e12);
            put(lines[n++], "L  %.3f uH", v.at.l * 1e6);
            put(lines[n++], "< back");
            break;
    }
    if (screen_ == Screen::Cal) put(rows[0], "%s %s: %s", title, band_name, v.cal_valid ? "ok" : "not done");
    else put(rows[0], "%s", title);
    const int top = cursor_ >= kWindow ? cursor_ - kWindow + 1 : 0;
    for (int r = 0; r < kWindow && top + r < n; ++r) put(rows[1 + r], "%s", lines[top + r]);
    put(rows[kRows - 1], "%s", v.note ? v.note : hint);
    highlight = 1 + cursor_ - top;
}

}  // namespace tuner
