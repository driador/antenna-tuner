// The Teensy layer's top: the boot sequence of §8B.4b, then a fixed 10 ms tick that reads the hardware
// into tuner::Inputs, steps the state machine and carries out its Outputs. Until the panel and the web
// UI exist, a USB console at the box gives the local actions (§8B.4f): ack, clear, tune and the mode.
#include <Arduino.h>

#include <cmath>
#include <cstring>
#include <new>

#include "board.hpp"
#include "config.hpp"
#include "motion.hpp"
#include "persist.hpp"
#include "sensors.hpp"
#include "tuner/fsm.hpp"
#include "tuner/pins.hpp"
#include "tuner/seed.hpp"

namespace iox = tuner::pins::iox;

namespace {
hw::Motion g_motion;
hw::Sensors g_sensors;
alignas(tuner::Tuner) unsigned char g_tuner_mem[sizeof(tuner::Tuner)];
tuner::Tuner* g_tuner = nullptr;
hw::Persisted g_saved;                 // what the EEPROM holds now
tuner::Outputs g_out;
uint32_t g_issued = 0, g_finished = 0, g_last_tick = 0, g_last_second = 0;
bool g_self_test = false;
bool g_ack = false, g_clear = false, g_tune = false;   // console actions, taken on the next tick

const char* mode_name(tuner::Mode m) {
    return m == tuner::Mode::Commissioning ? "COMMISSIONING" : m == tuner::Mode::Strict ? "STRICT" : "PERMISSIVE";
}

// Bring the EEPROM up to date; hw::save writes only what changed. Element positions are taken only
// when a move finishes, so encoder jitter at rest never rewrites flash.
void persist() {
    g_saved.faults = g_tuner->faults().persist();
    for (int s = 0; s < tuner::kSegments; ++s) {
        g_saved.priors[s] = tuner::Prior{};
        g_saved.prior_ok[s] = g_tuner->prior(s, g_saved.priors[s]);
    }
    hw::save(g_saved);
}

double blower_duty(double tank_c) {
    if (std::isnan(tank_c) || tank_c >= hw::kBlowerFullC) return 1.0;
    if (tank_c <= hw::kBlowerRampC) return hw::kBlowerMinDuty;
    return hw::kBlowerMinDuty + (1 - hw::kBlowerMinDuty) * (tank_c - hw::kBlowerRampC) / (hw::kBlowerFullC - hw::kBlowerRampC);
}

void status() {
    if (Serial.availableForWrite() < 200) return;          // nobody reading: never block the tick
    const tuner::Setting at = g_motion.position();
    const tuner::FaultRecord f = g_tuner->faults().persist();
    Serial.printf("%-9s %8.4f MHz %s  |G| %.3f /%5.1f deg  C1 %5.1f pF  C2 %5.1f pF  L %6.3f uH  tank %5.1f C  "
                  "vote %d permit %d  iox %04X  lim %02X  C %04X B %04X  %s\n",
                  tuner::state_name(g_out.state), g_sensors.mhz(), g_sensors.carrier() ? "carrier" : "-      ",
                  g_sensors.gamma().mag, g_sensors.gamma().theta_deg, at.c1 * 1e12, at.c2 * 1e12, at.l * 1e6,
                  g_sensors.tank_c(), g_out.mcu_permit, hw::permit(), g_sensors.iox_word(), hw::limits(),
                  f.latched_c, f.unacked_b, mode_name(g_tuner->faults().mode()));
}

void command(const char* s) {
    if (!std::strcmp(s, "ack")) g_ack = true;
    else if (!std::strcmp(s, "clear")) g_clear = true;     // local clear of B and C, after a look (§8B.4f)
    else if (!std::strcmp(s, "tune")) g_tune = true;
    else if (!std::strcmp(s, "status")) status();
    else if (!std::strcmp(s, "mode commissioning") || !std::strcmp(s, "mode strict")) {
        const tuner::Mode m = s[5] == 'c' ? tuner::Mode::Commissioning : tuner::Mode::Strict;
        Serial.printf("mode %s -> %s at %lu ms\n", mode_name(g_tuner->faults().mode()), mode_name(m), millis());
        g_tuner->faults().set_mode(m);
    } else if (!std::strcmp(s, "mode permissive")) {
        Serial.println("PERMISSIVE needs the 8B.4a-1 qualification, which is not tracked yet");
    } else {
        Serial.println("commands: status, ack, clear, tune, mode commissioning|strict");
    }
}

void console() {
    static char line[48];
    static size_t n = 0;
    while (Serial.available()) {
        const char c = char(Serial.read());
        if (c == '\r') continue;
        if (c != '\n') {
            if (n < sizeof line - 1) line[n++] = c;
            continue;
        }
        line[n] = 0;
        n = 0;
        command(line);
    }
}

void tick(uint32_t now) {
    g_sensors.read_iox();
    if (!g_motion.busy()) g_motion.read_encoders();

    tuner::Inputs in;
    in.now_ms = now;
    in.self_test_ok = g_self_test;
    in.bypass = g_sensors.iox(iox::BYPASS_KEY);
    in.carrier = g_sensors.carrier();
    uint32_t gate_start;
    if (g_sensors.take_gate(in.m, gate_start))             // only a gate that began after the last move
        in.have_measurement = !g_motion.busy() && int32_t(gate_start - g_motion.stopped_ms()) >= 0;
    in.position = g_motion.position();
    in.move_done = g_motion.done_id();
    in.encoder_mismatch = g_motion.mismatch();
    in.limit_hit = hw::limits() != 0;
    in.over_temp = g_sensors.over_temp();
    in.swr_trip = !g_sensors.iox(iox::SWR_OK);
    in.tune_request = g_tune;
    in.ack = g_ack;
    in.local_clear = g_clear;
    g_tune = g_ack = g_clear = false;

    g_out = g_tuner->step(in);

    if (g_out.move_id != g_issued) {
        g_issued = g_out.move_id;
        g_sensors.restart_bridge();
        g_motion.start(g_out.move_id, g_out.target, now);
    }
    hw::set_permit(g_out.mcu_permit);
    hw::set_blower(g_out.blower_full ? 1.0 : blower_duty(g_sensors.tank_c()));

    if (g_motion.done_id() != g_finished && !g_motion.busy()) {   // a move finished: remember where
        g_finished = g_motion.done_id();
        for (int i = 0; i < 3; ++i) g_saved.last_turns[i] = float(g_motion.turns(i));
        persist();
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
    const bool stored = hw::load(g_saved);
    tuner::Config cfg;
    cfg.parts = g_motion.parts();
    g_tuner = new (g_tuner_mem) tuner::Tuner(cfg, stored ? g_saved.faults : tuner::FaultRecord{});
    if (stored) {
        for (int s = 0; s < tuner::kSegments; ++s)
            if (g_saved.prior_ok[s]) g_tuner->set_prior(s, g_saved.priors[s]);
    } else {
        tuner::seed_priors(*g_tuner);
        for (int i = 0; i < 3; ++i) g_saved.last_turns[i] = float(g_motion.turns(i));
    }
    // Step 4 compares against the stored positions before persist() can replace them.
    float was[3];
    std::memcpy(was, g_saved.last_turns, sizeof was);
    persist();

    Serial.printf("tuner firmware: %s%s%s\n", watchdog_reset ? "WATCHDOG RESET, " : "",
                  recovery ? "recovery button held (recovery mode is not built yet), " : "",
                  stored ? "state restored" : "first boot, factory priors");
    Serial.printf("self-test %s: iox %d encoders %d bridge %d (VREF %.2f V) limits %02X permit %d\n",
                  g_self_test ? "pass" : "FAIL", iox_ok, encoders, bridge, vref, lim, permit);
    // Step 4: where the elements are against where they were left. Logged, never a fault: someone may
    // have serviced the box.
    for (int i = 0; i < 3 && stored; ++i)
        if (std::fabs(g_motion.turns(i) - was[i]) > 0.1)
            Serial.printf("%s moved since power-down: %.2f -> %.2f turns\n", hw::kAxes[i].name, was[i],
                          g_motion.turns(i));
    hw::watchdog_feed();
    g_last_tick = g_last_second = millis();
}

void loop() {
    const uint32_t now = millis();
    g_sensors.poll(now);
    g_motion.service(now, g_out.motion_enable);
    console();
    if (now - g_last_tick >= hw::kTickMs) {
        g_last_tick = now;
        tick(now);
    }
}
