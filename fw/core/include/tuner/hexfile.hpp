// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Intel HEX, for the firmware update over the network (§8C.8): one record per protocol line, checked as
// it arrives, and the image it builds checked as a whole before anything is installed. Pure code: the
// Teensy layer writes the data to its staging area in flash (teensy/update.cpp).
#pragma once
#include <cstddef>
#include <cstdint>

namespace tuner::hex {

struct Record {
    uint8_t type = 0;              // 0 data, 1 end of file, 2 / 4 extended address, 3 / 5 start address
    uint16_t addr = 0;
    uint8_t len = 0;
    uint8_t data[255] = {};
};

// ":LLAAAATT<data>CC" -> r. False if malformed, or the checksum does not add to zero.
bool parse(const char* line, Record& r);

// The records of one file in order. Each data record comes out as an absolute address inside
// [base, base + size), in ascending order, so the staging area can be written once without going back.
class Image {
public:
    Image(uint32_t base, uint32_t size) : base_(base), size_(size) {}
    enum class Step : uint8_t { Data, Skip, Done, Bad };
    // Data: r.data[0 .. r.len) goes to `at`. Skip: nothing to write. Done: the end-of-file record.
    // Bad: why() says what was wrong, and the image is finished with.
    Step feed(const Record& r, uint32_t& at);
    bool done() const { return done_; }
    uint32_t extent() const { return high_; }   // one past the highest byte, from base
    const char* why() const { return why_; }

private:
    Step bad(const char* why);
    uint32_t base_, size_;
    uint32_t upper_ = 0;           // the extended address in force
    uint32_t high_ = 0;            // the next byte, from base: records may skip ahead, never go back
    bool done_ = false, failed_ = false;
    const char* why_ = nullptr;
};

// CRC-32 (IEEE 802.3), incremental: crc32(0, p, n) for a whole buffer.
uint32_t crc32(uint32_t crc, const void* p, size_t n);

// The Teensy 4.1's own boot header in an image's first 8 KB: the FlexSPI configuration ("FCFB") with
// an 8 MB flash, and the image vector table at 0x1000. An image without them is not for this board.
bool teensy41_header(const uint8_t* first, size_t n);

}  // namespace tuner::hex
