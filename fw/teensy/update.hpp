// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The firmware update over the network (§8C.8). The image arrives on the link as Intel HEX and is
// written to a staging area in program flash, above the running firmware and below the recall memory
// (§8B.3c). It is then checked there as a whole: every record's checksum, the length and CRC-32 the
// sender gives, the CRC read back from the flash, and the Teensy 4.1's own boot header. Only then does
// the panel offer it, and only a push at the box installs it. The install runs from RAM with interrupts
// off, copies the staged image over the running one a 4 KB sector at a time, and restarts.
//
// A power cut mid-install leaves a board that the Teensy's own loader still programs over USB. The
// recall memory and the EEPROM area are above everything the install writes.
//
// Writing flash stops interrupts for up to a sector erase (45 ms typical), so the vote stays down from
// UPDATE BEGIN until the image is installed or dropped, and nothing moves meanwhile.
#pragma once
#include <cstdint>

#include "tuner/hexfile.hpp"

namespace hw {

class Updater {
public:
    enum class Stage : uint8_t {
        Idle,
        Receiving,     // records arriving from the session that began it
        Failed,        // a record was refused: the rest of that sender's records are dropped quietly
        Ready,         // staged and checked: the panel asks
    };

    void begin();
    // UPDATE BEGIN from session `who`. nullptr, or why not.
    const char* start(int who, uint32_t now_ms);
    // One record line. nullptr, or why it was refused, which ends the transfer.
    const char* record(int who, const char* line, uint32_t now_ms);
    // UPDATE END: nullptr when the image is staged and checked, else why not.
    const char* finish(int who, uint32_t bytes, uint32_t crc, uint32_t now_ms);
    void abort();
    // The session went away. True if it dropped a transfer it had not finished.
    bool closed(int who);
    // 30 s without a record ends a transfer; a staged image unanswered for 10 min is dropped. True when
    // either happens.
    bool poll(uint32_t now_ms);

    Stage stage() const { return stage_; }
    bool busy() const { return stage_ == Stage::Receiving || stage_ == Stage::Ready; }
    uint32_t received() const { return next_; }        // bytes of image so far, gaps included
    uint32_t bytes() const { return bytes_; }          // the staged image's length
    uint32_t crc() const { return crc_; }              // and its CRC-32, which the sender printed
    uint32_t capacity() const { return limit_ - stage_at_; }
    const char* why() const { return why_; }

    // Copies the staged image over the running one and restarts, never returning. Does nothing unless Ready.
    void install();

private:
    const char* fail(const char* why);
    void put(uint32_t offset, const uint8_t* data, uint32_t n);
    void flush();

    Stage stage_ = Stage::Idle;
    int owner_ = -1;
    uint32_t stage_at_ = 0, limit_ = 0;    // the staging area, as flash addresses
    tuner::hex::Image image_{0, 0};
    uint32_t next_ = 0;                    // the image's next byte; gaps up to a record read as 0xFF
    uint32_t crc_ = 0;                     // the CRC of the image so far, gaps included
    uint32_t page_at_ = 0;                 // the buffered page's flash address, 0 for none
    uint32_t erased_to_ = 0;               // every sector below this address is erased
    uint32_t bytes_ = 0;
    uint32_t last_ms_ = 0, ready_ms_ = 0;
    const char* why_ = nullptr;
};

}  // namespace hw
