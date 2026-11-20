// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Teensy 4.1 pin allocation, Rev 3.7c: log §8B.0.4, transcribed from kicad/board_control.py PINMAP.
// Change the board first; this file follows it.
#pragma once
#include <cstdint>

namespace tuner::pins {

// motion (J-A), 47 ohm series on every line (§7.3)
constexpr uint8_t STEP[3] = {0, 2, 4};       // C1, C2, roller
constexpr uint8_t DIR[3] = {1, 3, 7};
constexpr uint8_t DRV_EN = 8;

constexpr uint8_t FREQ_DIV = 9;              // /1024 count from the measurement board; FreqCount's fixed input

// AS5048A encoder SPI (J-A); MOSI carries the command frames (diagnostics/AGC, error clear)
constexpr uint8_t ENC_SCK = 13, ENC_MOSI = 11, ENC_MISO = 12;
constexpr uint8_t ENC_CS[3] = {10, 5, 6};

// ADC, all behind 1 k + 10 nF on the control board
constexpr uint8_t V_MAG = 14, V_PHS = 15, V_FWD = 16, V_REF_DET = 17, AD_VREF = 20;   // J-B
constexpr uint8_t THERM = 21, CT_DC = 22;                                         // J-E
constexpr uint8_t CAL_ADC = 23;              // cal-load detector, buffered and halved (§6B.3a)
constexpr uint8_t K_I[2] = {38, 39};         // K1, K2 coil current, 1 ohm sense (§6B.2)

constexpr uint8_t LIM[6] = {24, 25, 26, 27, 28, 29};   // high = tripped or open (NC contacts)
constexpr uint8_t RLY_CMD[2] = {30, 31};     // to the hold latch: effective only after the permissive
                                             // has been down >= 30 ms (§5.5)
constexpr uint8_t MCU_PERMIT = 32;           // the MCU's vote in the hardware permissive (out, pulled down)
constexpr uint8_t PERMIT = 36;               // the permissive as built (read-back)
constexpr uint8_t BLOWER_PWM = 33;           // gate pulled up: a reset or dead MCU leaves the blower on
constexpr uint8_t TACH = 40;                 // 2 pulses/rev, true only while the PWM switch is on
constexpr uint8_t NEX_RX = 34, NEX_TX = 35;  // Serial8
constexpr uint8_t I2C_SDA = 18, I2C_SCL = 19, IOX_INT = 41;
constexpr uint8_t BTN_RECOVERY = 37;         // sampled at boot (§8B.4f.2)

// MCP23017 at 0x20: bit numbers on its 16-bit GPIO word (GPA = bits 0-7, GPB = bits 8-15)
namespace iox {
constexpr uint8_t ADDR = 0x20;
constexpr uint8_t ENC1_A = 0, ENC1_B = 1, ENC1_PUSH = 2;
constexpr uint8_t ENC2_A = 3, ENC2_B = 4, ENC2_PUSH = 5;
constexpr uint8_t BYPASS_KEY = 6;
// GPB0-6: every term of the hardware permissive, so the firmware can name which one dropped it
constexpr uint8_t SWR_OK = 8, CALDET_OK = 9, CALTH_OK = 10, PANEL_OK = 11, LIMIT_OK = 12, HARD_OK = 13,
                  BYP_OK = 14;
// GPA7 and GPB7 are output-only on current silicon: unused
}  // namespace iox

}  // namespace tuner::pins
