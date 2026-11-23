// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Constant data a target should leave in program flash. The Teensy 4.1 otherwise copies every constant
// into its tightly coupled RAM at boot (its linker script puts .rodata in DTCM), where the web pages
// alone would take 16 KB. Read in place from flash, they cost none.
#pragma once

#ifdef ARDUINO_TEENSY41
#define TUNER_FLASH_DATA __attribute__((section(".progmem")))
#else
#define TUNER_FLASH_DATA
#endif
