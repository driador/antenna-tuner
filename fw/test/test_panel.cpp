// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The local panel (§7.5, §8B.4f): the encoders' quadrature, the Nextion protocol and the screens.
#include <cstring>
#include <string>

#include "harness.hpp"
#include "tuner/bit.hpp"
#include "tuner/panel.hpp"
#include "tuner/panel_io.hpp"

using namespace tuner;

namespace {
// Feeds a quadrature sequence and totals the detents.
int spin(Quadrature& q, const char* seq) {
    int d = 0;
    for (const char* p = seq; *p; p += 2) d += q.update(p[0] == '1', p[1] == '1');
    return d;
}

std::string screen(const Panel& p, int& hl) {
    char rows[Panel::kRows][Panel::kCols + 1];
    p.render(rows, hl);
    std::string s;
    for (auto& r : rows) s += std::string(r) + "\n";
    return s;
}

std::string row(const Panel& p, int i) {
    char rows[Panel::kRows][Panel::kCols + 1];
    int hl;
    p.render(rows, hl);
    return rows[i];
}
}  // namespace

TEST(quadrature_counts_detents) {
    Quadrature q;
    CHECK(spin(q, "00") == 0);                          // the first sample only sets the state
    CHECK(spin(q, "01111000") == 1);                    // one cycle clockwise
    CHECK(spin(q, "01111000011110") == 1);              // and most of another
    CHECK(spin(q, "00") == 1);
    CHECK(spin(q, "1011010010110100") == -2);           // two back
    CHECK(spin(q, "0100010001000100") == 0);            // contact bounce nets nothing
    CHECK(spin(q, "11") == 0);                          // both lines at once: ignored
}

TEST(nextion_frames) {
    char buf[64];
    size_t n = nextion::set_text(buf, sizeof buf, "t3", "say \"hi\"");
    CHECK(n == std::strlen("t3.txt=\"say \\\"hi\\\"\"") + 3);
    CHECK(std::memcmp(buf, "t3.txt=\"say \\\"hi\\\"\"", n - 3) == 0);
    CHECK(uint8_t(buf[n - 1]) == 0xFF && uint8_t(buf[n - 2]) == 0xFF && uint8_t(buf[n - 3]) == 0xFF);
    n = nextion::set_number(buf, sizeof buf, "t1", "pco", 65535);
    CHECK(n == std::strlen("t1.pco=65535") + 3);
    CHECK(nextion::set_text(buf, 12, "t0", "far too long to fit") > 0);   // cut, still terminated
    CHECK(uint8_t(buf[11]) == 0xFF);
    nextion::Parser p;
    nextion::Event e;
    const uint8_t touch[] = {0x1A, 0xFF, 0xFF, 0xFF, 0x65, 0x00, 0x02, 0x01, 0xFF, 0xFF, 0xFF};
    int events = 0;
    for (uint8_t b : touch)
        if (p.feed(b, e)) ++events;
    CHECK(events == 2 && e.code == 0x65 && e.page == 0 && e.component == 2 && e.press == 1);
}

TEST(panel_monitor_and_menu) {
    Panel p;
    PanelView v;
    v.mhz = 14.2051;
    v.carrier = true;
    v.swr = 1.12;
    v.at = {123.4e-12, 5.123e-6, 456.7e-12};
    p.show(v);
    int hl;
    const std::string s = screen(p, hl);
    CHECK(hl == -1);
    CHECK(s.find("14.2051 MHz 20m carrier") != std::string::npos);
    CHECK(s.find("C1 123.4 pF  C2 456.7 pF") != std::string::npos);
    CHECK(s.find("fwd --") != std::string::npos);       // no power curve yet
    p.push(0);
    CHECK(row(p, 0) == "MENU");
    p.turn(0, 1);
    p.push(0);                                          // "Tune now"
    CHECK(p.take().action == PanelAction::Tune);
    CHECK(p.take().action == PanelAction::None);        // once
    const uint32_t pressed = p.presses();
    p.push(0);                                          // the menu reopens where it was, on "Tune now"
    CHECK(p.presses() == pressed + 1);
    p.turn(0, 5);
    p.push(0);                                          // "Self-test" (§8B.4h), and back to the monitor
    CHECK(p.take().action == PanelAction::SelfTest && row(p, 0).rfind("IDLE", 0) == 0);
    CHECK(row(p, 0).rfind("IDLE", 0) == 0);
    v.note = "CAL: carrier needed";
    p.show(v);
    CHECK(row(p, Panel::kRows - 1) == "CAL: carrier needed");
}

TEST(panel_clear_unlocks_only_after_reading) {
    Panel p;
    PanelView v;
    v.latched_c = uint16_t(1u << unsigned(Fault::LimitHit));
    v.unacked_b = uint16_t(1u << unsigned(Fault::NoSolution));
    p.show(v);
    p.push(0);                                          // menu
    p.push(0);                                          // faults
    CHECK(row(p, 1) == "C  limit switch hit");
    CHECK(row(p, 5) == "(scroll to the end)");
    p.turn(0, 2);
    p.push(0);
    CHECK(p.take().action == PanelAction::None);        // not on Confirm yet
    p.turn(0, 10);                                      // to the end, one line at a time
    int hl;
    screen(p, hl);
    CHECK(hl == 5 && row(p, 5) == "[ clear at the box ]");
    p.push(0);
    CHECK(p.take().action == PanelAction::ClearLocal);

    Panel t;                                            // the built-in test names its checks (§8B.4h)
    PanelView vt;
    vt.latched_c = uint16_t(1u << unsigned(Fault::SelfTestFail));
    vt.unacked_b = uint16_t(1u << unsigned(Fault::BuiltInTest));
    vt.bit_failed = bit::mask(bit::Check::Latch) | bit::mask(bit::Check::BridgeIdle) |
                    bit::mask(bit::Check::FwdIdle) | bit::mask(bit::Check::AxisC2);   // C2 has no fault here
    t.show(vt);
    t.push(0);
    t.push(0);
    CHECK(row(t, 1) == "C  self-test failure" && row(t, 2) == "   hold latch");
    CHECK(row(t, 3) == "B  built-in test" && row(t, 4).rfind("   bridge idle, forward detector", 0) == 0);

    Panel b;                                            // B alone: acknowledge
    PanelView vb;
    vb.unacked_b = uint16_t(1u << unsigned(Fault::TuneFailed));
    b.show(vb);
    b.push(0);
    b.push(0);
    b.turn(0, 5);
    b.push(0);
    CHECK(b.take().action == PanelAction::Ack);
}

TEST(panel_path_policy_cal_and_jog) {
    Panel p;
    PanelView v;
    p.show(v);
    p.push(0);
    p.turn(0, 2);                                       // RF path
    p.push(0);
    p.turn(0, 2);                                       // CAL
    p.push(0);
    PanelRequest r = p.take();
    CHECK(r.action == PanelAction::SetPath && r.arg == int(Path::Cal));

    p.push(0);                                          // the menu, still on RF path
    p.turn(0, 2);                                       // Calibrate this band
    p.push(0);
    CHECK(row(p, 0).rfind("CALIBRATE", 0) == 0);
    p.turn(0, 1);
    p.push(0);
    CHECK(p.take().action == PanelAction::CalOpen);
    v.cal_have = 2;
    p.show(v);
    CHECK(row(p, 2).rfind("+ 2 open", 0) == 0);
    p.push(1);                                          // back to the menu, still on Calibrate

    p.turn(0, 1);                                       // Jog elements
    p.push(0);
    p.turn(0, 2);                                       // the roller
    p.turn(1, 3);
    p.turn(1, -1);
    r = p.take();
    CHECK(r.action == PanelAction::Jog && r.arg == 2 && r.detents == 2);
    p.turn(1, 1);                                       // a turn for another axis replaces a jog not
    p.turn(0, -2);                                      // yet taken; the caller takes one every tick
    p.turn(1, -4);
    r = p.take();
    CHECK(r.action == PanelAction::Jog && r.arg == 0 && r.detents == -4);
}

TEST(panel_policy_shows_the_qualification) {
    Panel p;
    PanelView v;
    v.q_tunes = 42;
    v.q_bands = 3;
    v.q_hours = 12.5;
    p.show(v);
    p.push(0);
    p.turn(0, 3);                                       // Fault policy
    p.push(0);
    CHECK(row(p, 3) == "  PERMISSIVE (not qualified)");
    CHECK(row(p, 4) == "  tunes 42/100, bands 3/4");
    CHECK(row(p, 5) == "  hours 12.5/50, inspected no");
    p.turn(0, 5);
    p.push(0);                                          // Record roller inspection
    CHECK(p.take().action == PanelAction::Inspected);
    p.turn(0, -3);                                      // PERMISSIVE: the caller refuses it unless met
    p.push(0);
    const PanelRequest r = p.take();
    CHECK(r.action == PanelAction::SetMode && r.arg == int(Mode::Permissive));
}

TEST(panel_asks_before_installing_firmware) {
    // §8C.8: a staged, checked update takes the whole screen; only a push at the box answers it.
    Panel p;
    PanelView v;
    v.update_ready = true;
    v.update_bytes = 419840;
    v.update_crc = 0x0DF6E497;
    p.show(v);
    CHECK(row(p, 0) == "FIRMWARE UPDATE READY" && row(p, 2) == "410 KB, CRC-32 0DF6E497");
    CHECK(row(p, 7) == "left push:  install now" && row(p, 8) == "right push: discard it");
    p.turn(0, 3);
    p.turn(1, -2);
    CHECK(p.take().action == PanelAction::None);       // turning does nothing
    p.push(1);
    CHECK(p.take().action == PanelAction::Discard);
    p.push(0);
    CHECK(p.take().action == PanelAction::Install);
    v.update_ready = false;                            // installing: the last screen, deaf to the knobs
    v.installing = true;
    p.show(v);
    CHECK(row(p, 0) == "INSTALLING FIRMWARE" && row(p, 2) == "Do not switch the tuner off.");
    p.push(0);
    p.turn(0, 1);
    CHECK(p.take().action == PanelAction::None);
    v.installing = false;                              // discarded instead: the panel is itself again
    p.show(v);
    CHECK(row(p, 0) != "FIRMWARE UPDATE READY" && row(p, 0) != "INSTALLING FIRMWARE");
}
