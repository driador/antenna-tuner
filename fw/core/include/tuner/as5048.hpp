// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// AS5048A magnetic encoder frames (§7.1): SPI mode 1, 16 bits, MSB first. Bit 15 is even parity over
// the frame and bit 14 is the read bit (command) or the error flag (reply); bits 13-0 carry the
// register or the data. Each transfer returns the reply to the previous command.
#pragma once
#include <cstdint>

namespace tuner::as5048 {

constexpr uint16_t kRegClearError = 0x0001;   // reading it clears the error flag
constexpr uint16_t kRegDiagAgc = 0x3FFD;
constexpr uint16_t kRegAngle = 0x3FFF;
constexpr uint16_t kCounts = 16384;           // 14 bits a turn

constexpr uint16_t with_parity(uint16_t f) {
    f &= 0x7FFF;
    unsigned ones = 0;
    for (int i = 0; i < 15; ++i) ones += (f >> i) & 1u;
    return uint16_t(f | ((ones & 1u) << 15));
}

constexpr uint16_t read_command(uint16_t reg) { return with_parity(uint16_t(0x4000 | (reg & 0x3FFF))); }

struct Reply {
    bool parity_ok = false;
    bool error = false;            // the device flagged the previous command (framing, invalid, parity)
    uint16_t data = 0;
};

Reply decode(uint16_t frame);

struct Diagnostics {
    uint8_t agc = 0;               // 0 = strong field ... 255 = weak
    bool offset_done = false;      // OCF
    bool cordic_overflow = false;  // COF
    bool field_strong = false;     // COMP low: magnet too close
    bool field_weak = false;       // COMP high: magnet too far
    bool ok() const { return offset_done && !cordic_overflow && !field_strong && !field_weak; }
};

Diagnostics diagnostics(uint16_t data);

}  // namespace tuner::as5048
