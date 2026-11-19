// The control board's direct I/O (§8B.0.4, §10.5): the safe state, the MCU's vote in the permissive, the
// relay commands, the blower, the limit senses, the recovery button and the watchdog.
#pragma once
#include <cstdint>

namespace hw {

// First thing at boot (§8B.4b step 1): vote down, drivers off, relays in TUNE (both off, §6B.2),
// blower on. The hardware already holds all of this while the pins float; this makes it explicit.
void safe_outputs();

bool recovery_held();             // §8B.4f.2: the recessed button, sampled before anything else

void set_permit(bool on);         // MCU_PERMIT, pulled down on the board
bool permit();                    // the permissive as built (read-back)
void set_drivers(bool on);
void set_blower(double duty);     // 0-1; the gate is pulled up, so a dead MCU leaves it running
uint32_t tach_pulses();           // since boot; 2 a revolution, meaningful only while the fan is on

uint8_t limits();                 // LIM1-LIM6, bit 0 = LIM1; set = tripped or an open lead

// RTWDOG (§7.4.1, §8B.0.3): armed before MCU_PERMIT is first raised, so a hung MCU drops out of the
// permissive by being reset.
void watchdog_begin(uint32_t timeout_ms);
void watchdog_feed();
bool reset_by_watchdog();         // the last reset was the watchdog's; clears the flag

}  // namespace hw
