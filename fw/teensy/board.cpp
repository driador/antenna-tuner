// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "board.hpp"

#include <Arduino.h>

#include "config.hpp"
#include "tuner/pins.hpp"

namespace pins = tuner::pins;

// RTWDOG (WDOG3) is not in the Teensy core's register headers: i.MX RT1060 reference manual, chapter 57.
#define RTWDOG_CS (*(volatile uint32_t*)0x400BC000)
#define RTWDOG_CNT (*(volatile uint32_t*)0x400BC004)
#define RTWDOG_TOVAL (*(volatile uint32_t*)0x400BC008)
#define RTWDOG_WIN (*(volatile uint32_t*)0x400BC00C)
#define RTWDOG_CS_UPDATE (1u << 5)
#define RTWDOG_CS_EN (1u << 7)
#define RTWDOG_CS_CLK_LPO (1u << 8)
#define RTWDOG_CS_RCS (1u << 10)
#define RTWDOG_CS_ULK (1u << 11)
#define RTWDOG_CS_CMD32EN (1u << 13)

namespace hw {

namespace {
volatile uint32_t g_tach = 0;
void tach_isr() { ++g_tach; }
}  // namespace

void safe_outputs() {
    pinMode(pins::MCU_PERMIT, OUTPUT);
    digitalWriteFast(pins::MCU_PERMIT, LOW);
    pinMode(pins::DRV_EN, OUTPUT);
    set_drivers(false);
    for (int i = 0; i < 3; ++i) {
        pinMode(pins::STEP[i], OUTPUT);
        digitalWriteFast(pins::STEP[i], LOW);
        pinMode(pins::DIR[i], OUTPUT);
        digitalWriteFast(pins::DIR[i], LOW);
    }
    for (uint8_t p : pins::RLY_CMD) {
        pinMode(p, OUTPUT);
        digitalWriteFast(p, LOW);
    }
    pinMode(pins::BLOWER_PWM, OUTPUT);
    digitalWriteFast(pins::BLOWER_PWM, HIGH);
    pinMode(pins::PERMIT, INPUT);
    for (uint8_t p : pins::LIM) pinMode(p, INPUT);     // 10 k pull-ups on the board
    pinMode(pins::BTN_RECOVERY, INPUT);                // 10 k pull-up on the board
    pinMode(pins::IOX_INT, INPUT);                     // open drain, 10 k pull-up on the board
    pinMode(pins::TACH, INPUT);
    attachInterrupt(digitalPinToInterrupt(pins::TACH), tach_isr, FALLING);
}

bool recovery_held() { return digitalReadFast(pins::BTN_RECOVERY) == LOW; }

void set_permit(bool on) { digitalWriteFast(pins::MCU_PERMIT, on ? HIGH : LOW); }
bool permit() { return digitalReadFast(pins::PERMIT); }

void set_drivers(bool on) { digitalWriteFast(pins::DRV_EN, on == kDriverEnableHigh ? HIGH : LOW); }

void set_relays(bool k1, bool k2) {
    digitalWriteFast(pins::RLY_CMD[0], k1 ? HIGH : LOW);
    digitalWriteFast(pins::RLY_CMD[1], k2 ? HIGH : LOW);
}

void set_blower(double duty) {
    static bool configured = false;
    if (!configured) {
        analogWriteResolution(12);
        analogWriteFrequency(pins::BLOWER_PWM, kBlowerPwmHz);
        configured = true;
    }
    duty = duty < 0 ? 0 : duty > 1 ? 1 : duty;
    analogWrite(pins::BLOWER_PWM, int(duty * 4095 + 0.5));
}

uint32_t tach_pulses() { return g_tach; }

uint8_t limits() {
    uint8_t m = 0;
    for (int i = 0; i < 6; ++i)
        if (digitalReadFast(pins::LIM[i])) m |= uint8_t(1u << i);
    return m;
}

void watchdog_begin(uint32_t timeout_ms) {
    CCM_CCGR5 |= CCM_CCGR5_WDOG3(3);
    __disable_irq();
    if (RTWDOG_CS & RTWDOG_CS_CMD32EN) {               // unlock, then reconfigure within 255 bus clocks
        RTWDOG_CNT = 0xD928C520;
    } else {
        RTWDOG_CNT = 0xC520;
        RTWDOG_CNT = 0xD928;
    }
    while (!(RTWDOG_CS & RTWDOG_CS_ULK)) {}
    RTWDOG_WIN = 0;
    RTWDOG_TOVAL = uint32_t(timeout_ms * 32.768);      // the 32.768 kHz LPO clock
    RTWDOG_CS = RTWDOG_CS_CMD32EN | RTWDOG_CS_CLK_LPO | RTWDOG_CS_UPDATE | RTWDOG_CS_EN;
    while (!(RTWDOG_CS & RTWDOG_CS_RCS)) {}
    __enable_irq();
}

void watchdog_feed() { RTWDOG_CNT = 0xB480A602; }

bool reset_by_watchdog() {
    const bool wd = SRC_SRSR & SRC_SRSR_WDOG3_RST_B;
    SRC_SRSR = SRC_SRSR_WDOG3_RST_B;                   // write 1 to clear
    return wd;
}

}  // namespace hw
