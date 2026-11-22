// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The Teensy layer's top: the boot sequence of §8B.4b, then a fixed 10 ms tick that reads the hardware
// into tuner::Inputs, steps the state machine and carries out its Outputs, with the RF path (§6B.2),
// calibration (§6A.8), the local panel (§7.5), the event log, the PERMISSIVE qualification (§8B.4a-1),
// the built-in test (§8B.4h) and the SD mirror (§8B.5) around it. A USB console at the box offers the
// same local actions as the panel (§8B.4f).
#include <Arduino.h>
#include <Entropy.h>

#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>

#include "board.hpp"
#include "calib.hpp"
#include "config.hpp"
#include "motion.hpp"
#include "net.hpp"
#include "panel_hw.hpp"
#include "persist.hpp"
#include "sensors.hpp"
#include "storage.hpp"
#include "tuner/alarm.hpp"
#include "tuner/bit.hpp"
#include "tuner/derate.hpp"
#include "tuner/events.hpp"
#include "tuner/fsm.hpp"
#include "tuner/mirror.hpp"
#include "tuner/panel.hpp"
#include "tuner/path.hpp"
#include "tuner/pins.hpp"
#include "tuner/seed.hpp"

namespace iox = tuner::pins::iox;

namespace {
hw::Motion g_motion;
hw::Sensors g_sensors;
hw::Calibration g_cal;
hw::PanelHw g_panel_hw;
tuner::Panel g_panel;
tuner::PathSwitch g_path;
alignas(tuner::Tuner) unsigned char g_tuner_mem[sizeof(tuner::Tuner)];
tuner::Tuner* g_tuner = nullptr;
hw::Authoritative g_auth;              // what the authoritative record should hold
hw::Convenience g_conv;
tuner::Outputs g_out;
tuner::PathSwitch::Out g_path_out;
uint32_t g_issued = 0, g_finished = 0, g_last_tick = 0, g_last_second = 0, g_last_panel = 0;
bool g_self_test = false;
bool g_ack = false, g_clear = false, g_tune = false, g_jog = false, g_preset = false;   // taken on the next tick
tuner::Setting g_jog_target;
double g_preset_mhz = 0;
const char* g_note = nullptr;          // the last result, on the console and the panel for a while
uint32_t g_note_ms = 0;
hw::Storage g_store;
hw::Net g_net;
tuner::EventLog g_events;
tuner::Derate g_derate(hw::kDerateTauS);   // §1.7.1: a warning, never an inhibit
tuner::Qualification g_qual;           // live; g_auth.qual is its snapshot, taken on events and every 10 min
uint16_t g_raised[unsigned(tuner::Fault::Count)] = {};
tuner::State g_prev_state = tuner::State::SelfTest;
tuner::Path g_prev_path = tuner::Path::Tune;
uint32_t g_cal_changes = 0, g_last_ten_min = 0;
bool g_restorable = false;             // the flash was blank or corrupt at boot: a restore may replace it
bool g_recovery = false;               // §8B.4f.3 stage 1: DHCP, STRICT, transmit inhibited until reboot
bool g_profiles_dirty = false;
// The built-in test (§8B.4h).
tuner::bit::Active g_bit;
uint32_t g_bit_failed = 0;             // the checks failed at boot, or in the last run (TLM bit=, the panel)
uint32_t g_bit_axis0 = 0;              // the raised counts as the run began: its own faults are the new ones
uint16_t g_bit_relay0 = 0;
uint16_t g_raise = 0;                  // what the last run found, raised on the next tick
bool g_bit_due = hw::kBitAtPowerUp;    // the run at power-up, once the boot has settled
uint32_t g_boot_ms = 0, g_last_rf_ms = 0;
tuner::Alarm g_alarm;                  // §8B.4i
uint32_t g_presses = 0;                // the panel's knob presses seen so far: each silences the alarm

void note(const char* msg) {
    if (!msg) return;
    g_note = msg;
    g_note_ms = millis();
    Serial.println(msg);
}

// Event time: Unix seconds once the RTC has been set (the loader sets it), else seconds since boot.
void stamp(uint32_t& t, bool& wall) {
    const uint32_t rtc = rtc_get();
    wall = rtc > 1735689600UL;                         // 2025-01-01: anything earlier was never set
    t = wall ? rtc : millis() / 1000;
}

void log_event(tuner::EventKind k, uint8_t arg = 0) {
    uint32_t t;
    bool wall;
    stamp(t, wall);
    g_events.add(t, wall, k, arg, g_out.state, g_sensors.mhz());
}

const char* saved_time(char* buf, size_t cap) {
    uint32_t t;
    bool wall;
    stamp(t, wall);
    if (wall) tuner::iso8601(t, buf, cap);
    else buf[0] = 0;
    return buf;
}

const char* mode_name(tuner::Mode m) {
    return m == tuner::Mode::Commissioning ? "COMMISSIONING" : m == tuner::Mode::Strict ? "STRICT" : "PERMISSIVE";
}

// The MCU's vote in the permissive (§7.4): the state machine's, held down through a path change and in
// recovery.
bool vote() { return g_out.mcu_permit && !g_path_out.hold_vote && !g_recovery; }

// Nothing in progress, so a path change or a jog may start.
bool quiet() {
    const tuner::State s = g_out.state;
    return (s == tuner::State::Idle || s == tuner::State::Matched || s == tuner::State::Fault) && !g_motion.busy() &&
           !g_path.busy();
}

// Bring the EEPROM up to date; hw::save writes only what changed. Element positions are taken only
// when a move finishes, so encoder jitter at rest never rewrites flash.
void persist() {
    g_auth.faults = g_tuner->faults().persist();
    hw::save(g_auth);
    for (int s = 0; s < tuner::kSegments; ++s) {
        g_conv.priors[s] = tuner::Prior{};
        g_conv.prior_ok[s] = g_tuner->prior(s, g_conv.priors[s]);
    }
    g_profiles_dirty = hw::save(g_conv) || g_profiles_dirty;
}

void qual_save() {
    g_auth.qual = g_qual;
    persist();
}

// Everything the SD card mirrors (§8B.5.4d).
const tuner::Settings& settings() {
    static tuner::Settings s;
    s.tuner_id = g_auth.tuner_id;
    s.net = g_auth.net;
    s.policy = g_tuner->faults().mode();
    s.qual = g_qual;
    for (int b = 0; b < tuner::kBandCount; ++b) {
        s.bridge[b] = g_auth.bridge[b];
        s.power[b] = g_auth.power[b];
    }
    for (int i = 0; i < tuner::kSegments; ++i) {
        s.prior_ok[i] = g_conv.prior_ok[i];
        s.priors[i] = g_conv.priors[i];
    }
    return s;
}

void backup_now() {                                    // an administrative change: a new version (§8B.5.4a)
    char t[24];
    if (g_store.present() && !g_store.backup(settings(), saved_time(t, sizeof t))) note("SD: backup failed");
}

void set_mode(tuner::Mode m) {                         // local only, logged (§8B.4a-1)
    if (m == tuner::Mode::Permissive && !g_qual.met()) {
        note("PERMISSIVE: not qualified yet (policy screen)");
        return;
    }
    if (m == g_tuner->faults().mode()) return;
    Serial.printf("mode %s -> %s\n", mode_name(g_tuner->faults().mode()), mode_name(m));
    g_tuner->faults().set_mode(m);
    log_event(tuner::EventKind::Mode, uint8_t(m));
    persist();
    backup_now();
    note(m == tuner::Mode::Commissioning ? "mode COMMISSIONING" : m == tuner::Mode::Strict ? "mode STRICT" : "mode PERMISSIVE");
}

void inspected() {                                     // §8B.4a-1: roller wheel and bus rod, at the box
    g_qual.record_inspection();
    qual_save();
    log_event(tuner::EventKind::Inspected);
    backup_now();
    note("roller inspection recorded");
}

// §8B.5.4b: a version from this tuner's own card restores at any time (a rollback). A board that came
// up blank or corrupt may take any card's backup, and adopts that card. Another tuner's card on a
// working board needs `adopt` first. A restore never promotes the fault policy.
void restore(uint32_t n) {
    static tuner::Settings s;
    if (!quiet()) return note("restore: finish what is running first");
    if (g_store.foreign() && !g_restorable) return note("restore: another tuner's card; adopt it first");
    if (const char* why = g_store.read(n, s)) return note(why);
    if (!g_restorable && s.tuner_id != g_auth.tuner_id) return note("restore: that backup is another tuner's");
    g_auth.net = s.net;
    for (int b = 0; b < tuner::kBandCount; ++b) {
        g_auth.bridge[b] = s.bridge[b];
        g_auth.power[b] = s.power[b];
    }
    g_qual = s.qual;
    for (int i = 0; i < tuner::kSegments; ++i)
        if (s.prior_ok[i]) g_tuner->set_prior(i, s.priors[i]);
    if (s.policy == tuner::Mode::Permissive && g_tuner->faults().mode() != tuner::Mode::Permissive)
        Serial.println("restore: PERMISSIVE in the backup refused; a restore cannot promote the policy");
    else if (s.policy != g_tuner->faults().mode())
        g_tuner->faults().set_mode(s.policy);
    if (g_restorable) {
        g_auth.tuner_id = s.tuner_id;
        g_store.adopt(s.tuner_id);
        g_restorable = false;
    }
    qual_save();
    log_event(tuner::EventKind::Restore, uint8_t(n & 0xFF));
    note("restored from the card");
}

// bit: the built-in test's own request; anyone else's waits until its run is over.
const char* set_path(tuner::Path p, bool bit = false) {   // allowed remotely too, like a band change (§6B.4)
    // §5.5: the relays switch with no RF at all, and the permit holds off only the amplifier.
    const char* why = g_bit.running() && !bit ? "path: the self-test is running"
                      : g_sensors.carrier() || g_sensors.rf_now() ? "path: only while receiving"
                      : !quiet() ? "path: finish what is running first"
                      : !g_path.request(p, millis()) ? "path: a change is under way" : nullptr;
    note(why ? why : p == tuner::Path::Tune ? "path TUNE" : p == tuner::Path::Aux ? "path AUX" : "path CAL");
    return why;
}

void jog(int axis, double turns, bool bit = false) {   // §7.5 manual override, through the state machine
    if (!std::isfinite(turns)) {
        note("jog c1|c2|l <turns>");
        return;
    }
    if (g_bit.running() && !bit) {
        note("jog: the self-test is running");
        return;
    }
    if (g_out.state != tuner::State::Idle || g_motion.busy()) {
        note("jog: from IDLE only");
        return;
    }
    tuner::Setting t = g_motion.position();
    const double v = hw::axis_curve(axis).at(g_motion.turns(axis) + turns);
    if (axis == 0) t.c1 = v;
    else if (axis == 1) t.c2 = v;
    else t.l = v;
    g_jog = true;
    g_jog_target = t;
}

uint32_t axis_raised() {
    return uint32_t(g_tuner->faults().raised(tuner::Fault::EncoderMismatch)) +
           g_tuner->faults().raised(tuner::Fault::LimitHit);
}

// §8B.4h, at power-up or on demand. The plain refusals are said at once; the sequencer itself waits a
// few seconds for the rest (a move finishing, the RF gone long enough).
const char* start_selftest() {
    if (g_bit.running()) return "self-test: already running";
    if (g_sensors.carrier() || g_sensors.rf_now()) return "self-test: only while receiving";
    if (g_sensors.iox(iox::BYPASS_KEY)) return "self-test: the bypass is engaged";
    if (!g_sensors.iox(iox::PANEL_OK)) return "self-test: the RF service panel is open";
    if (g_tuner->faults().any_blocking()) return "self-test: clear the faults first";
    if (g_path.path() != tuner::Path::Tune) return "self-test: on the TUNE path only";
    tuner::bit::Windows w;
    w.fwd_max = hw::kFwdRfVolts;
    g_bit.start(millis(), w);
    g_bit_failed = 0;
    g_bit_axis0 = axis_raised();
    g_bit_relay0 = g_tuner->faults().raised(tuner::Fault::RelayMismatch);
    return nullptr;
}

const char* selftest() {                               // the panel, the console and the link
    const char* why = start_selftest();
    note(why ? why : "self-test running");
    return why;
}

tuner::bit::Active::In bit_in(uint32_t now) {
    tuner::bit::Active::In b;
    b.now_ms = now;
    b.safe = !g_sensors.carrier() && !g_sensors.rf_now() && now - g_last_rf_ms >= hw::kBitRfQuietMs &&
             !g_sensors.iox(iox::BYPASS_KEY) && g_sensors.iox(iox::PANEL_OK);
    b.clear = !g_tuner->faults().any_blocking();
    b.quiet = quiet();
    for (int a = 0; a < 3; ++a) {
        b.turns[a] = g_motion.turns(a);
        b.travel[a] = hw::kAxes[a].full_turns;
    }
    b.axis_fault = axis_raised() != g_bit_axis0;
    b.relay_fault = g_tuner->faults().raised(tuner::Fault::RelayMismatch) != g_bit_relay0;
    b.path = g_path.path();
    b.k1_current = g_sensors.k1_on();
    b.vote = vote();
    b.permit = hw::permit();
    b.rest = g_sensors.rest();
    return b;
}

// A run ended (§8B.4h): an event for each failed check, the faults behind them that nothing has raised
// yet, and the result on the console and the panel.
void bit_report() {
    using tuner::bit::Check;
    using tuner::bit::mask;
    const uint32_t failed = g_bit.failed(), untested = g_bit.untested();
    uint32_t hard = 0;
    g_bit_failed = failed;
    for (unsigned i = 0; i < unsigned(Check::Count); ++i) {
        const Check c = Check(i);
        if (!(failed & mask(c))) continue;
        log_event(tuner::EventKind::SelfTest, uint8_t(i));
        const tuner::Fault f = tuner::bit::fault_of(c);
        if (f == tuner::Fault::Count) continue;            // a warning
        hard |= mask(c);
        // An axis fails on the move check's own fault, and a relay usually on the path switch's.
        const bool raised = f == tuner::Fault::EncoderMismatch ||
                            (f == tuner::Fault::RelayMismatch && g_tuner->faults().raised(f) != g_bit_relay0);
        if (!raised) g_raise |= uint16_t(1u << unsigned(f));
    }
    if (!g_bit.completed()) log_event(tuner::EventKind::SelfTest, tuner::kSelfTestStopped);
    else if (!hard) log_event(tuner::EventKind::SelfTest, tuner::kSelfTestPassed);

    static char msg[128];
    char list[96];
    if (hard) {
        tuner::bit::names(hard, list, sizeof list);
        std::snprintf(msg, sizeof msg, "self-test FAILED: %s", list);
        note(msg);
    } else {
        note(!g_bit.completed() ? "self-test stopped: run it again"
             : failed           ? "self-test passed, with warnings"
                                : "self-test passed");
    }
    if (failed & mask(Check::PermitRise)) {
        const char* term = tuner::bit::permit_blocker(g_sensors.iox_word());
        Serial.printf("self-test warning: the permit did not rise with the vote: %s\n",
                      term ? term : "every term reads high, so the read-back");
    }
    if (failed & mask(Check::Thermistor))
        Serial.printf("self-test warning: the tank thermistor reads %.1f C at rest\n", g_sensors.tank_c());
    if (untested) {
        tuner::bit::names(untested, list, sizeof list);
        Serial.printf("self-test: not judged: %s (%s)\n", list,
                      g_tuner->faults().mode() == tuner::Mode::Commissioning ? "COMMISSIONING withholds the vote"
                                                                              : "the permit was not up");
    }
}

double blower_duty(double tank_c) {
    if (std::isnan(tank_c) || tank_c >= hw::kBlowerFullC) return 1.0;
    if (tank_c <= hw::kBlowerRampC) return hw::kBlowerMinDuty;
    return hw::kBlowerMinDuty + (1 - hw::kBlowerMinDuty) * (tank_c - hw::kBlowerRampC) / (hw::kBlowerFullC - hw::kBlowerRampC);
}

const char* cal_step(hw::Calibration::Step s, double watts = 0) {
    const char* why = g_cal.start(s, g_path.path(), g_sensors.carrier(), g_sensors.mhz(), watts);
    note(why ? why : "calibrating: hold the carrier");
    return why;
}

const char* cal_save() {
    const uint32_t before = g_cal.changes();
    const char* msg = g_cal.save();
    note(msg);
    return g_cal.changes() != before ? nullptr : msg;
}

tuner::PanelView view() {
    tuner::PanelView v;
    v.state = g_out.state;
    v.mode = g_tuner->faults().mode();
    v.path = g_path.path();
    v.path_busy = g_path.busy();
    v.mhz = g_sensors.mhz();
    v.carrier = g_sensors.carrier();
    v.swr = tuner::swr_from_mag(g_sensors.gamma().mag);
    v.fwd_w = g_sensors.forward_watts();
    v.at = g_motion.position();
    v.tank_c = g_sensors.tank_c();
    for (unsigned i = 0; i < unsigned(tuner::Fault::Count); ++i) {
        if (g_tuner->faults().latched(tuner::Fault(i))) v.latched_c |= uint16_t(1u << i);
        if (g_tuner->faults().unacked(tuner::Fault(i))) v.unacked_b |= uint16_t(1u << i);
    }
    v.bit_failed = g_bit_failed;
    v.over_temp = g_sensors.over_temp();
    v.bypass = g_sensors.iox(iox::BYPASS_KEY);
    const tuner::Band* b = tuner::band_of(v.mhz);
    v.cal_valid = b && g_auth.bridge[b - tuner::kBands].valid;
    v.cal_have = g_cal.have(v.mhz);
    v.note = g_note && millis() - g_note_ms < 4000 ? g_note : g_bit.running() ? "self-test running" : nullptr;
    v.card = g_store.present() ? (g_store.foreign() ? -1 : 1) : 0;
    v.q_tunes = g_qual.tunes;
    v.q_bands = g_qual.band_count();
    v.q_hours = g_qual.hours();
    v.q_inspected = g_qual.inspected;
    v.q_met = g_qual.met();
    return v;
}

void panel_request() {
    const tuner::PanelRequest r = g_panel.take();
    switch (r.action) {
        case tuner::PanelAction::None: break;
        case tuner::PanelAction::Ack: g_ack = true; break;
        case tuner::PanelAction::ClearLocal: g_clear = true; break;
        case tuner::PanelAction::Tune: g_tune = true; break;
        case tuner::PanelAction::SetMode: set_mode(tuner::Mode(r.arg)); break;
        case tuner::PanelAction::SetPath: set_path(tuner::Path(r.arg)); break;
        case tuner::PanelAction::CalLoad: cal_step(hw::Calibration::Step::Load); break;
        case tuner::PanelAction::CalOpen: cal_step(hw::Calibration::Step::Open); break;
        case tuner::PanelAction::CalShort: cal_step(hw::Calibration::Step::Short); break;
        case tuner::PanelAction::CalSave: cal_save(); break;
        case tuner::PanelAction::Jog: jog(r.arg, r.detents * hw::kJogTurns); break;
        case tuner::PanelAction::Inspected: inspected(); break;
        case tuner::PanelAction::SelfTest: selftest(); break;
    }
}

// Pre-positioning (§8B.3a): the remote head's band select, while the rig still receives. The state
// machine checks the same conditions again on the next tick, and the tune at key-down measures the
// real frequency, so a wrong preset only costs a longer move.
const char* preset(double mhz) {
    if (!(mhz > 0) || tuner::segment_of(mhz) < 0) return "preset: not on an amateur band";
    if (g_sensors.carrier()) return "preset: only while receiving";
    if (g_bit.running()) return "preset: the self-test is running";
    if (g_path.path() != tuner::Path::Tune) return "preset: on the TUNE path only";
    if (g_sensors.iox(iox::BYPASS_KEY)) return "preset: the bypass is engaged";
    if (g_out.state != tuner::State::Idle || g_motion.busy()) return "preset: only in IDLE";
    g_preset = true;
    g_preset_mhz = mhz;
    return nullptr;
}

// Network settings (§8B.5.4): checked, saved to flash and the card as one administrative change, and
// used from the next restart, so the connection that made the change never drops under it.
const char* set_net(const tuner::proto::Request& r) {
    tuner::NetConfig n = g_auth.net;
    tuner::net::merge(n, r.net, r.net_fields);
    if (const char* why = tuner::net::check(n)) return why;
    if (!std::memcmp(&n, &g_auth.net, sizeof n)) return nullptr;     // nothing to save
    g_auth.net = n;
    log_event(tuner::EventKind::Network, n.dhcp ? 1 : 0);
    persist();
    backup_now();
    note("network settings saved: used from the next restart");
    return nullptr;
}

// The link (§8C.5): what it may ask, through the same paths as the console and the panel.
const char* link_command(const tuner::proto::Request& r) {
    using tuner::proto::Cmd;
    switch (r.cmd) {
        case Cmd::Tune: g_tune = true; return nullptr;
        case Cmd::Ack: g_ack = true; return nullptr;
        case Cmd::Path: return set_path(r.path);
        case Cmd::CalLoad: return cal_step(hw::Calibration::Step::Load);
        case Cmd::CalOpen: return cal_step(hw::Calibration::Step::Open);
        case Cmd::CalShort: return cal_step(hw::Calibration::Step::Short);
        case Cmd::CalSave: return cal_save();
        case Cmd::CalWatts: return cal_step(hw::Calibration::Step::Power, r.value);
        case Cmd::Preset: return preset(r.value);
        case Cmd::SelfTest: return selftest();
        case Cmd::Net: return set_net(r);
        default: return "not on the link";
    }
}

void link_network(tuner::NetConfig& n) { n = g_auth.net; }

// "net" shows the saved settings and the address in use; "net key=value ..." changes them, as NET does.
void net_console(const char* s) {
    const tuner::proto::Request r = tuner::proto::parse(s);
    if (r.cmd != tuner::proto::Cmd::Net) return note(r.why ? r.why : "net [mode=dhcp|static] [hostname=] [ip=] ...");
    if (r.net_fields)
        if (const char* why = set_net(r)) return note(why);
    char text[160], addr[20];
    tuner::net::format(g_auth.net, text, sizeof text);
    g_net.address(addr, sizeof addr);
    Serial.printf("saved:  %s\nin use: %s%s\n", text, addr,
                  tuner::net::same(g_auth.net, g_net.running()) ? "" : " (the saved settings apply at the next restart)");
}

void link_telemetry(tuner::proto::Telemetry& t) {
    t.state = g_out.state;
    t.path = g_path.path();
    t.mode = g_tuner->faults().mode();
    t.mhz = g_sensors.mhz();
    t.carrier = g_sensors.carrier();
    t.swr = tuner::swr_from_mag(g_sensors.gamma().mag);
    t.fwd_w = g_sensors.forward_watts();
    t.at = g_motion.position();
    t.tank_c = g_sensors.tank_c();
    t.over_temp = g_sensors.over_temp();
    for (unsigned i = 0; i < unsigned(tuner::Fault::Count); ++i) {
        if (g_tuner->faults().latched(tuner::Fault(i))) t.latched_c |= uint16_t(1u << i);
        if (g_tuner->faults().unacked(tuner::Fault(i))) t.unacked_b |= uint16_t(1u << i);
    }
    t.permit = hw::permit();
    t.bypass = g_sensors.iox(iox::BYPASS_KEY);
    t.loss_w = g_derate.loss_w();
    t.limit_w = g_derate.limit_w();
    t.derate = g_derate.warning();
    t.bit_failed = g_bit_failed;
    t.bit_running = g_bit.running();
}

void status() {
    if (Serial.availableForWrite() < 260) return;          // nobody reading: never block the tick
    const tuner::Setting at = g_motion.position();
    const tuner::FaultRecord f = g_tuner->faults().persist();
    char addr[20];
    if (g_net.link()) g_net.address(addr, sizeof addr);
    else std::snprintf(addr, sizeof addr, "no link");
    Serial.printf("%-9s %-4s %8.4f MHz %s  |G| %.3f /%5.1f deg  C1 %5.1f pF  C2 %5.1f pF  L %6.3f uH  tank %5.1f C  "
                  "vote %d permit %d  iox %04X  lim %02X  C %04X B %04X  %s  card %s  net %s%s%s%s\n",
                  tuner::state_name(g_out.state), tuner::path_name(g_path.path()), g_sensors.mhz(),
                  g_sensors.carrier() ? "carrier" : "-      ", g_sensors.gamma().mag, g_sensors.gamma().theta_deg,
                  at.c1 * 1e12, at.c2 * 1e12, at.l * 1e6, g_sensors.tank_c(),
                  vote(), hw::permit(), g_sensors.iox_word(), hw::limits(), f.latched_c, f.unacked_b,
                  mode_name(g_tuner->faults().mode()),
                  g_store.present() ? (g_store.foreign() ? "FOREIGN" : "ok") : "NONE", addr, g_recovery ? "  RECOVERY" : "",
                  g_derate.warning() ? "  DERATE" : "", g_bit.running() ? "  SELFTEST" : "");
}

void command(const char* s) {
    if (!std::strcmp(s, "ack")) g_ack = true;
    else if (!std::strcmp(s, "clear")) g_clear = true;     // local clear of B and C, after a look (§8B.4f)
    else if (!std::strcmp(s, "tune")) g_tune = true;
    else if (!std::strcmp(s, "status")) status();
    else if (!std::strcmp(s, "mode commissioning")) set_mode(tuner::Mode::Commissioning);
    else if (!std::strcmp(s, "mode strict")) set_mode(tuner::Mode::Strict);
    else if (!std::strcmp(s, "mode permissive")) set_mode(tuner::Mode::Permissive);
    else if (!std::strcmp(s, "path tune")) set_path(tuner::Path::Tune);
    else if (!std::strcmp(s, "path aux")) set_path(tuner::Path::Aux);
    else if (!std::strcmp(s, "path cal")) set_path(tuner::Path::Cal);
    else if (!std::strcmp(s, "cal load")) cal_step(hw::Calibration::Step::Load);
    else if (!std::strcmp(s, "cal open")) cal_step(hw::Calibration::Step::Open);
    else if (!std::strcmp(s, "cal short")) cal_step(hw::Calibration::Step::Short);
    else if (!std::strcmp(s, "cal save")) cal_save();
    else if (!std::strncmp(s, "cal watts ", 10)) cal_step(hw::Calibration::Step::Power, std::atof(s + 10));
    else if (!std::strcmp(s, "inspected")) inspected();
    else if (!std::strcmp(s, "selftest")) selftest();
    else if (!std::strcmp(s, "qual"))
        Serial.printf("qualification: %lu/100 tunes, %d/4 bands, %.1f/50 h, inspected %s: %s\n",
                      static_cast<unsigned long>(g_qual.tunes), g_qual.band_count(), g_qual.hours(),
                      g_qual.inspected ? "yes" : "no", g_qual.met() ? "met" : "not met");
    else if (!std::strcmp(s, "backups")) {
        uint32_t n[64];
        const int k = g_store.list(n, 64);
        Serial.printf("card %s, %d backups:", g_store.present() ? (g_store.foreign() ? "FOREIGN" : "ok") : "NONE", k);
        for (int i = 0; i < k; ++i) Serial.printf(" %lu", static_cast<unsigned long>(n[i]));
        Serial.println();
    } else if (!std::strncmp(s, "restore ", 8)) restore(uint32_t(std::atol(s + 8)));
    else if (!std::strcmp(s, "adopt")) note(g_store.adopt(g_auth.tuner_id) ? "card adopted" : "adopt: no card");
    else if (!std::strncmp(s, "net", 3) && (s[3] == 0 || s[3] == ' ')) net_console(s);
    else if (!std::strncmp(s, "preset ", 7)) {
        const char* why = preset(std::atof(s + 7));
        note(why ? why : "preset: moving to the stored setting");
    }
    else if (!std::strncmp(s, "jog ", 4)) {
        const char* a = s + 4;
        const int axis = !std::strncmp(a, "c1 ", 3) ? 0 : !std::strncmp(a, "c2 ", 3) ? 1 : !std::strncmp(a, "l ", 2) ? 2 : -1;
        if (axis < 0) note("jog c1|c2|l <turns>");
        else jog(axis, std::atof(a + (axis == 2 ? 2 : 3)));
    } else {
        Serial.println("commands: status, ack, clear, tune, mode commissioning|strict, path tune|aux|cal,");
        Serial.println("          cal load|open|short|save, cal watts <W>, jog c1|c2|l <turns>, preset <MHz>, selftest,");
        Serial.println("          inspected, qual, backups, restore <n>, adopt,");
        Serial.println("          net [mode=dhcp|static hostname= ip= netmask= gateway= dns=]");
    }
}

void console() {
    static char line[48];
    static size_t n = 0;
    while (Serial.available()) {
        const char c = char(Serial.read());
        if (c == '\r') continue;
        if (c != '\n') {
            if (n < sizeof line - 1) line[n++] = char(std::tolower(c));
            continue;
        }
        line[n] = 0;
        n = 0;
        command(line);
    }
}

void tick(uint32_t now) {
    if (g_sensors.read_iox()) g_panel_hw.input(g_sensors.iox_word(), now, g_panel);
    if (!g_motion.busy()) g_motion.read_encoders();
    if (g_sensors.carrier() || g_sensors.rf_now()) g_last_rf_ms = now;

    // The relay checks start once SELF-TEST is over, so that a coil reading wrong at power-up reaches
    // the state machine as a fault rather than during the one state that ignores it.
    if (g_out.state != tuner::State::SelfTest) {
        tuner::PathSwitch::In pin;
        pin.now_ms = now;
        pin.k1_current = g_sensors.k1_on();
        pin.k2_current = g_sensors.k2_on();
        pin.carrier = g_sensors.carrier();
        pin.rf_now = g_sensors.rf_now();
        pin.load_rf = g_sensors.load_rf();
        g_path_out = g_path.step(pin);
        if (g_path_out.canceled) note("path: keyed mid-change; retry");
    }

    // The built-in test (§8B.4h) asks for its jogs and path changes as the operator does. Only the latch
    // check drives K1 itself, past the path switch, and only while the permit is up.
    if (g_bit_due && now - g_boot_ms >= hw::kBitSettleMs) {
        g_bit_due = false;
        selftest();
    }
    bool bit_k1 = false;
    if (g_bit.running()) {
        const tuner::bit::Active::Out b = g_bit.step(bit_in(now));
        if (b.jog_axis >= 0) jog(b.jog_axis, b.jog_turns, true);
        if (b.path_request) set_path(b.path, true);
        bit_k1 = b.drive_k1;
        if (!g_bit.running()) bit_report();
    }
    hw::set_relays(g_path_out.k1 || bit_k1, g_path_out.k2);

    tuner::Inputs in;
    in.now_ms = now;
    in.self_test_ok = g_self_test;
    in.bypass = g_sensors.iox(iox::BYPASS_KEY);
    in.carrier = g_sensors.carrier();
    uint32_t gate_start;
    if (g_sensors.take_gate(in.m, gate_start)) {           // only a gate that began after the last move
        in.have_measurement = !g_motion.busy() && int32_t(gate_start - g_motion.stopped_ms()) >= 0;
        if (in.have_measurement) note(g_cal.gate(g_sensors.standard(), g_sensors.v_fwd(), in.m.mhz, in.carrier));
    }
    in.position = g_motion.position();
    in.move_done = g_motion.done_id();
    in.encoder_mismatch = g_motion.mismatch();
    in.limit_hit = hw::limits() != 0;
    in.over_temp = g_sensors.over_temp();
    in.swr_trip = !g_sensors.iox(iox::SWR_OK);
    in.tune_request = g_tune;
    in.ack = g_ack;
    in.local_clear = g_clear;
    in.tune_path = g_path.path() == tuner::Path::Tune && !g_path.busy();
    in.relay_mismatch = g_path_out.mismatch;
    in.jog = g_jog;
    in.jog_target = g_jog_target;
    in.preset = g_preset;
    in.preset_mhz = g_preset_mhz;
    in.raise = g_raise;
    g_tune = g_ack = g_clear = g_jog = g_preset = false;
    g_raise = 0;

    g_out = g_tuner->step(in);

    // The event log: faults as they are raised, acknowledgements and clears, finished tunes and path
    // changes. A mechanical fault also starts the PERMISSIVE qualification over (§8B.4a-1).
    for (unsigned i = 0; i < unsigned(tuner::Fault::Count); ++i) {
        const tuner::Fault f = tuner::Fault(i);
        if (g_tuner->faults().raised(f) == g_raised[i]) continue;
        g_raised[i] = g_tuner->faults().raised(f);
        log_event(tuner::EventKind::Fault, uint8_t(i));
        if (f == tuner::Fault::LimitHit || f == tuner::Fault::EncoderMismatch) {
            g_qual.mechanical_fault();
            qual_save();
        }
    }
    if (in.ack) log_event(tuner::EventKind::Ack);
    if (in.local_clear) log_event(tuner::EventKind::Clear);
    if (g_prev_state == tuner::State::Verify && g_out.state == tuner::State::Matched) {
        const tuner::Band* b = tuner::band_of(g_sensors.mhz());
        g_qual.tune_completed(b ? int(b - tuner::kBands) : -1);
        qual_save();
        log_event(tuner::EventKind::Tuned);
    }
    g_prev_state = g_out.state;
    if (g_path.path() != g_prev_path) {
        g_prev_path = g_path.path();
        log_event(tuner::EventKind::Path, uint8_t(g_prev_path));
    }
    // §1.7.1: the RF bay's averaged loss against its cooling. Over it, warn and log; PTT is untouched.
    if (g_derate.update(g_sensors.mhz(), g_sensors.forward_watts(),
                        g_sensors.carrier() && g_path.path() == tuner::Path::Tune, hw::kTickMs / 1000.0)) {
        static char msg[40];
        std::snprintf(msg, sizeof msg, "derate: keep under %.0f W here", g_derate.limit_w());
        log_event(tuner::EventKind::Derate);
        note(msg);
    }
    if (g_cal.changes() != g_cal_changes) {               // a band saved or a power point taken
        g_cal_changes = g_cal.changes();
        persist();
        log_event(tuner::EventKind::CalSaved);
        backup_now();
    }

    if (g_out.move_id != g_issued) {
        g_issued = g_out.move_id;
        g_sensors.restart_bridge();
        g_motion.start(g_out.move_id, g_out.target, now);
    }
    hw::set_permit(vote());
    hw::set_blower(g_out.blower_full ? 1.0 : blower_duty(g_sensors.tank_c()));

    // The alarm (§8B.4i). A knob press at the box silences what is sounding; anything new sounds again.
    tuner::Alarm::In al;
    al.now_ms = now;
    const tuner::FaultRecord fr = g_tuner->faults().persist();
    al.latched_c = fr.latched_c;
    al.unacked_b = fr.unacked_b;
    al.over_temp = g_sensors.over_temp();
    al.derate = g_derate.warning();
    al.silence = g_panel.presses() != g_presses;
    g_presses = g_panel.presses();
    g_sensors.set_sounder(g_alarm.step(al) && hw::kSounder);

    if (g_motion.done_id() != g_finished && !g_motion.busy()) {   // a move finished: remember where
        g_finished = g_motion.done_id();
        for (int i = 0; i < 3; ++i) g_conv.last_turns[i] = float(g_motion.turns(i));
        persist();
    }
    panel_request();
    if (now - g_last_panel >= hw::kPanelMs) {
        g_last_panel = now;
        g_panel.show(view());
        g_panel_hw.draw(g_panel);
    }
    const int card = g_store.poll(now, g_events);        // §8B.5.3: a condition, never a fault
    if (card > 0) {
        log_event(tuner::EventKind::CardIn);
        char t[24];
        g_store.current(settings(), saved_time(t, sizeof t));
    } else if (card < 0) {
        log_event(tuner::EventKind::CardOut);
    }
    if (now - g_last_second >= 1000) {
        g_last_second = now;
        g_qual.powered(1);
        persist();
        status();
    }
    if (now - g_last_ten_min >= 600000) {                // powered hours and profiles: slowly (§8B.5.5)
        g_last_ten_min = now;
        qual_save();
        char t[24];
        if (g_profiles_dirty && g_store.present() && g_store.current(settings(), saved_time(t, sizeof t)))
            g_profiles_dirty = false;
    }
    hw::watchdog_feed();
}
}  // namespace

void setup() {
    hw::safe_outputs();                                    // §8B.4b step 1
    const bool recovery = hw::recovery_held();             // §8B.4f.2, before anything else
    hw::watchdog_begin(hw::kWatchdogMs);                   // before MCU_PERMIT can first rise (§8B.0.3)
    const bool watchdog_reset = hw::reset_by_watchdog();
    Serial.begin(115200);
    hw::set_blower(1.0);

    // Step 2, self-test: the encoders and their magnets, the MCP23017, the measurement board (AD8302
    // VREF), the limit senses, and the permissive down while the vote is (unless the bypass key holds it).
    const bool iox_ok = g_sensors.begin();
    const bool encoders = g_motion.begin() && g_motion.magnets_ok();
    const double vref = analogRead(tuner::pins::AD_VREF) * 3.3 / 4095;
    const bool bridge = vref > 1.6 && vref < 2.0;
    const uint8_t lim = hw::limits();
    const bool permit = !hw::permit() || g_sensors.iox(iox::BYPASS_KEY);
    g_self_test = iox_ok && encoders && bridge && lim == 0 && permit;
    using tuner::bit::Check;                               // each failure named (§8B.4h)
    using tuner::bit::mask;
    g_bit_failed = (iox_ok ? 0 : mask(Check::Expander)) | (encoders ? 0 : mask(Check::Encoders)) |
                   (bridge ? 0 : mask(Check::BridgeRef)) | (lim == 0 ? 0 : mask(Check::Limits)) |
                   (permit ? 0 : mask(Check::PermitStuck));

    // Step 3, what was persisted; the SELF-TEST state turns a latch or an unacknowledged B into FAULT.
    const hw::Loaded auth = hw::load(g_auth);
    const bool conv = hw::load(g_conv);
    if (auth != hw::Loaded::Ok) {                         // a new board, or a record that does not check out
        Entropy.Initialize();
        g_auth.tuner_id = (uint64_t(Entropy.random()) << 32) | Entropy.random();
        g_restorable = true;                              // §8B.5.4b: a restore is offered, never automatic
        if (auth == hw::Loaded::Corrupt) {               // and a corrupt one is a fault first
            g_self_test = false;
            g_bit_failed |= mask(Check::Record);
        }
    }
    g_qual = g_auth.qual;
    tuner::Config cfg;
    cfg.parts = g_motion.parts();
    g_tuner = new (g_tuner_mem) tuner::Tuner(cfg, g_auth.faults);
    if (conv) {
        for (int s = 0; s < tuner::kSegments; ++s)
            if (g_conv.prior_ok[s]) g_tuner->set_prior(s, g_conv.priors[s]);
    } else {
        tuner::seed_priors(*g_tuner);
    }
    g_sensors.use_calibration(&g_auth);
    g_cal.attach(&g_auth);
    g_panel_hw.begin();
    log_event(watchdog_reset ? tuner::EventKind::WatchdogReset : tuner::EventKind::Boot);
    for (unsigned i = 0; i < unsigned(Check::Count); ++i)
        if (g_bit_failed & (1u << i)) log_event(tuner::EventKind::SelfTest, uint8_t(i));

    // The SD card (§8B.5): /recovery.cfg once, if present (§8B.5.4c), and the restore offer.
    g_store.begin(g_auth.tuner_id);
    char report[96] = "";
    if (g_store.recovery(g_auth.net, report, sizeof report)) {
        log_event(tuner::EventKind::Recovery);
        Serial.printf("RECOVERY.CFG APPLIED (network only)%s%s\n", report[0] ? ": " : "", report);
    } else if (report[0]) {
        Serial.printf("RECOVERY.CFG NOT APPLIED: %s\n", report);
    }
    if (recovery) {                                       // §8B.4f.3 stage 1: reachable, strict, inhibited
        g_recovery = true;
        g_auth.net = tuner::NetConfig{};                  // DHCP as "tuner"; fix it from the web UI
        g_tuner->faults().set_mode(tuner::Mode::Strict);
        log_event(tuner::EventKind::Recovery);
        Serial.println("RECOVERY MODE: DHCP as 'tuner', policy STRICT, transmit inhibited until a reboot");
    }
    g_net.begin(g_auth.net, &g_events, hw::Net::Hooks{link_command, link_telemetry, link_network});   // never blocks
    if (g_restorable && g_store.present()) {
        uint32_t n[64];
        const int k = g_store.list(n, 64);
        if (k) Serial.printf("%s flash: the card holds %d backups, newest %lu. 'restore <n>' to load one\n",
                             auth == hw::Loaded::Blank ? "BLANK" : "CORRUPT", k, static_cast<unsigned long>(n[k - 1]));
    }

    Serial.printf("tuner firmware: %s%s%s%s\n", watchdog_reset ? "WATCHDOG RESET, " : "",
                  recovery ? "recovery button held (recovery mode is not built yet), " : "",
                  auth == hw::Loaded::Ok ? "faults and calibration restored, "
                  : auth == hw::Loaded::Blank ? "BLANK flash (new board), "
                                              : "CORRUPT flash record: self-test fails, nothing restored, ",
                  conv ? "profiles restored" : "factory priors");
    Serial.printf("self-test %s: iox %d encoders %d bridge %d (VREF %.2f V) limits %02X permit %d\n",
                  g_self_test ? "pass" : "FAIL", iox_ok, encoders, bridge, vref, lim, permit);
    // Step 4: where the elements are against where they were left. Logged, never a fault: someone may
    // have serviced the box.
    for (int i = 0; i < 3 && conv; ++i)
        if (std::fabs(g_motion.turns(i) - g_conv.last_turns[i]) > 0.1)
            Serial.printf("%s moved since power-down: %.2f -> %.2f turns\n", hw::kAxes[i].name, g_conv.last_turns[i],
                          g_motion.turns(i));
    for (int i = 0; i < 3; ++i) g_conv.last_turns[i] = float(g_motion.turns(i));
    persist();
    hw::watchdog_feed();
    g_last_tick = g_last_second = g_last_panel = g_boot_ms = millis();
}

void loop() {
    const uint32_t now = millis();
    g_sensors.poll(now);
    g_motion.service(now, g_out.motion_enable);
    if (digitalReadFast(tuner::pins::IOX_INT) == LOW && g_sensors.read_iox())   // a knob moved
        g_panel_hw.input(g_sensors.iox_word(), now, g_panel);
    g_panel_hw.poll();
    g_net.poll(now);
    console();
    if (now - g_last_tick >= hw::kTickMs) {
        g_last_tick = now;
        tick(now);
    }
}
