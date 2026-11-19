// The Teensy layer's top: the boot sequence of §8B.4b, then a fixed 10 ms tick that reads the hardware
// into tuner::Inputs, steps the state machine and carries out its Outputs, with the RF path (§6B.2),
// calibration (§6A.8) and the local panel (§7.5) around it. A USB console at the box offers the same
// local actions as the panel (§8B.4f).
#include <Arduino.h>

#include <cctype>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <new>

#include "board.hpp"
#include "calib.hpp"
#include "config.hpp"
#include "motion.hpp"
#include "panel_hw.hpp"
#include "persist.hpp"
#include "sensors.hpp"
#include "tuner/fsm.hpp"
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
bool g_ack = false, g_clear = false, g_tune = false, g_jog = false;   // taken on the next tick
tuner::Setting g_jog_target;
const char* g_note = nullptr;          // the last result, on the console and the panel for a while
uint32_t g_note_ms = 0;

void note(const char* msg) {
    if (!msg) return;
    g_note = msg;
    g_note_ms = millis();
    Serial.println(msg);
}

const char* mode_name(tuner::Mode m) {
    return m == tuner::Mode::Commissioning ? "COMMISSIONING" : m == tuner::Mode::Strict ? "STRICT" : "PERMISSIVE";
}

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
    hw::save(g_conv);
}

void set_mode(tuner::Mode m) {                         // local only, logged (§8B.4a-1)
    if (m == tuner::Mode::Permissive) {
        note("PERMISSIVE needs the 8B.4a-1 qualification, not tracked yet");
        return;
    }
    Serial.printf("mode %s -> %s at %lu ms\n", mode_name(g_tuner->faults().mode()), mode_name(m), millis());
    g_tuner->faults().set_mode(m);
    note(m == tuner::Mode::Commissioning ? "mode COMMISSIONING" : "mode STRICT");
}

void set_path(tuner::Path p) {                         // allowed remotely too, like a band change (§6B.4)
    if (!quiet()) note("path: finish what is running first");
    else if (!g_path.request(p, millis())) note("path: a change is under way");
    else note(p == tuner::Path::Tune ? "path TUNE" : p == tuner::Path::Aux ? "path AUX" : "path CAL");
}

void jog(int axis, double turns) {                     // §7.5 manual override, through the state machine
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

double blower_duty(double tank_c) {
    if (std::isnan(tank_c) || tank_c >= hw::kBlowerFullC) return 1.0;
    if (tank_c <= hw::kBlowerRampC) return hw::kBlowerMinDuty;
    return hw::kBlowerMinDuty + (1 - hw::kBlowerMinDuty) * (tank_c - hw::kBlowerRampC) / (hw::kBlowerFullC - hw::kBlowerRampC);
}

void cal_step(hw::Calibration::Step s, double watts = 0) {
    const char* why = g_cal.start(s, g_path.path(), g_sensors.carrier(), g_sensors.mhz(), watts);
    note(why ? why : "calibrating: hold the carrier");
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
    v.over_temp = g_sensors.over_temp();
    v.bypass = g_sensors.iox(iox::BYPASS_KEY);
    const tuner::Band* b = tuner::band_of(v.mhz);
    v.cal_valid = b && g_auth.bridge[b - tuner::kBands].valid;
    v.cal_have = g_cal.have(v.mhz);
    v.note = g_note && millis() - g_note_ms < 4000 ? g_note : nullptr;
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
        case tuner::PanelAction::CalSave: note(g_cal.save()); break;
        case tuner::PanelAction::Jog: jog(r.arg, r.detents * hw::kJogTurns); break;
    }
}

void status() {
    if (Serial.availableForWrite() < 220) return;          // nobody reading: never block the tick
    const tuner::Setting at = g_motion.position();
    const tuner::FaultRecord f = g_tuner->faults().persist();
    Serial.printf("%-9s %-4s %8.4f MHz %s  |G| %.3f /%5.1f deg  C1 %5.1f pF  C2 %5.1f pF  L %6.3f uH  tank %5.1f C  "
                  "vote %d permit %d  iox %04X  lim %02X  C %04X B %04X  %s\n",
                  tuner::state_name(g_out.state), tuner::path_name(g_path.path()), g_sensors.mhz(),
                  g_sensors.carrier() ? "carrier" : "-      ", g_sensors.gamma().mag, g_sensors.gamma().theta_deg,
                  at.c1 * 1e12, at.c2 * 1e12, at.l * 1e6, g_sensors.tank_c(), g_out.mcu_permit && !g_path_out.hold_vote,
                  hw::permit(), g_sensors.iox_word(), hw::limits(), f.latched_c, f.unacked_b,
                  mode_name(g_tuner->faults().mode()));
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
    else if (!std::strcmp(s, "cal save")) note(g_cal.save());
    else if (!std::strncmp(s, "cal watts ", 10)) cal_step(hw::Calibration::Step::Power, std::atof(s + 10));
    else if (!std::strncmp(s, "jog ", 4)) {
        const char* a = s + 4;
        const int axis = !std::strncmp(a, "c1 ", 3) ? 0 : !std::strncmp(a, "c2 ", 3) ? 1 : !std::strncmp(a, "l ", 2) ? 2 : -1;
        if (axis < 0) note("jog c1|c2|l <turns>");
        else jog(axis, std::atof(a + (axis == 2 ? 2 : 3)));
    } else {
        Serial.println("commands: status, ack, clear, tune, mode commissioning|strict, path tune|aux|cal,");
        Serial.println("          cal load|open|short|save, cal watts <W>, jog c1|c2|l <turns>");
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

    // The relay checks start once SELF-TEST is over, so that a coil reading wrong at power-up reaches
    // the state machine as a fault rather than during the one state that ignores it.
    if (g_out.state != tuner::State::SelfTest) {
        tuner::PathSwitch::In pin;
        pin.now_ms = now;
        pin.k1_current = g_sensors.k1_on();
        pin.k2_current = g_sensors.k2_on();
        pin.carrier = g_sensors.carrier();
        pin.load_rf = g_sensors.load_rf();
        g_path_out = g_path.step(pin);
    }
    hw::set_relays(g_path_out.k1, g_path_out.k2);

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
    g_tune = g_ack = g_clear = g_jog = false;

    g_out = g_tuner->step(in);

    if (g_out.move_id != g_issued) {
        g_issued = g_out.move_id;
        g_sensors.restart_bridge();
        g_motion.start(g_out.move_id, g_out.target, now);
    }
    hw::set_permit(g_out.mcu_permit && !g_path_out.hold_vote);
    hw::set_blower(g_out.blower_full ? 1.0 : blower_duty(g_sensors.tank_c()));

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
    if (now - g_last_second >= 1000) {
        g_last_second = now;
        persist();
        status();
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

    // Step 3, what was persisted; the SELF-TEST state turns a latch or an unacknowledged B into FAULT.
    const bool auth = hw::load(g_auth);
    const bool conv = hw::load(g_conv);
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

    Serial.printf("tuner firmware: %s%s%s%s\n", watchdog_reset ? "WATCHDOG RESET, " : "",
                  recovery ? "recovery button held (recovery mode is not built yet), " : "",
                  auth ? "faults and calibration restored, " : "no fault record or calibration, ",
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
    g_last_tick = g_last_second = g_last_panel = millis();
}

void loop() {
    const uint32_t now = millis();
    g_sensors.poll(now);
    g_motion.service(now, g_out.motion_enable);
    if (digitalReadFast(tuner::pins::IOX_INT) == LOW && g_sensors.read_iox())   // a knob moved
        g_panel_hw.input(g_sensors.iox_word(), now, g_panel);
    g_panel_hw.poll();
    console();
    if (now - g_last_tick >= hw::kTickMs) {
        g_last_tick = now;
        tick(now);
    }
}
