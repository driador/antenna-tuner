// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "update.hpp"

#include <Arduino.h>

#include <cstdio>
#include <cstring>

#include "board.hpp"
#include "recall_store.hpp"

extern "C" {
extern unsigned long _flashimagelen;              // the running image's length, from the linker script
// The Teensy core's own flash routines (eeprom.c), which EEPROM emulation and LittleFS_Program use. Each
// stops interrupts while the flash is busy and starts them again when it is done.
void eepromemu_flash_write(void* addr, const void* data, uint32_t len);
void eepromemu_flash_erase_sector(void* addr);
}

namespace hw {

namespace {
constexpr uint32_t kFlash = 0x60000000;
// The 4.1's 8 MB, less the top 256 KB that the core keeps for EEPROM emulation and the restore program.
constexpr uint32_t kUsable = 0x7C0000;
constexpr uint32_t kSector = 4096;
constexpr uint32_t kChunk = 128;                  // one program operation, the size LittleFS_Program writes
constexpr uint32_t kRecordMs = 30000, kReadyMs = 600000;
static_assert(RecallStore::kBytes % 0x10000 == 0, "LittleFS_Program rounds its area up to 64 KB");

DMAMEM uint8_t g_chunk[kChunk];
DMAMEM uint8_t g_sector[kSector];                 // the install's copy of one staged sector
uint8_t g_blank[64];                              // 0xFF, for the CRC of a gap

FASTRUN bool blank(const uint8_t* p, uint32_t n) {
    for (uint32_t i = 0; i < n; ++i)
        if (p[i] != 0xFF) return false;
    return true;
}

// The install: from RAM, with every interrupt source off, and never returning. All code runs from RAM
// unless marked FLASHMEM, and neither this nor what it calls (blank(), watchdog_feed(), the core's two
// flash routines) is. The copy goes up through the flash, so a new image long enough to reach the
// staging area only overwrites staged sectors already copied.
FASTRUN [[noreturn]] void copy_and_restart(uint32_t from, uint32_t bytes) {
    __disable_irq();
    NVIC_ICER0 = NVIC_ICER1 = NVIC_ICER2 = NVIC_ICER3 = NVIC_ICER4 = 0xFFFFFFFF;
    SYST_CSR = 0;
    SCB_ICSR = SCB_ICSR_PENDSTCLR | SCB_ICSR_PENDSVCLR;
    for (uint32_t off = 0; off < bytes; off += kSector) {
        const uint32_t* src = reinterpret_cast<const uint32_t*>(from + off);
        uint32_t* dst = reinterpret_cast<uint32_t*>(g_sector);
        for (uint32_t i = 0; i < kSector / 4; ++i) dst[i] = src[i];
        watchdog_feed();                          // an erase takes up to 400 ms, a sector's writes 100 ms
        eepromemu_flash_erase_sector(reinterpret_cast<void*>(kFlash + off));
        watchdog_feed();
        for (uint32_t p = 0; p < kSector && off + p < bytes; p += kChunk)
            if (!blank(g_sector + p, kChunk)) eepromemu_flash_write(reinterpret_cast<void*>(kFlash + off + p), g_sector + p, kChunk);
    }
    SCB_AIRCR = 0x05FA0004;                       // SYSRESETREQ
    for (;;) {}
}
}  // namespace

void Updater::begin() {
    std::memset(g_blank, 0xFF, sizeof g_blank);
    const uint32_t image = uint32_t(&_flashimagelen);
    stage_at_ = kFlash + (image + kSector - 1) / kSector * kSector;
    limit_ = kFlash + kUsable - RecallStore::kBytes;
    if (limit_ < stage_at_) limit_ = stage_at_;     // no room: every image is too big
}

const char* Updater::start(int who, uint32_t now_ms) {
    if (stage_ == Stage::Receiving && who != owner_) return "update: another connection is sending one";
    if (stage_ == Stage::Ready) return "update: one is staged; install it at the panel or UPDATE ABORT";
    stage_ = Stage::Receiving;
    owner_ = who;
    image_ = tuner::hex::Image(kFlash, capacity());
    next_ = crc_ = page_at_ = bytes_ = 0;
    erased_to_ = stage_at_;
    last_ms_ = now_ms;
    why_ = nullptr;
    return nullptr;
}

const char* Updater::fail(const char* why) {
    static char text[80];
    std::snprintf(text, sizeof text, "update: %s", why);
    stage_ = Stage::Failed;
    page_at_ = 0;
    why_ = text;
    return why_;
}

const char* Updater::record(int who, const char* line, uint32_t now_ms) {
    if (stage_ == Stage::Failed && who == owner_) return nullptr;   // refused once already: the rest quietly
    if (stage_ != Stage::Receiving) return "update: none in progress; UPDATE BEGIN first";
    if (who != owner_) return "update: another connection is sending one";
    last_ms_ = now_ms;
    tuner::hex::Record r;
    if (!tuner::hex::parse(line, r)) return fail("a record that does not check out");
    uint32_t at;
    const tuner::hex::Image::Step step = image_.feed(r, at);
    if (step == tuner::hex::Image::Step::Bad) return fail(image_.why());
    if (step == tuner::hex::Image::Step::Data) put(at - kFlash, r.data, r.len);
    return nullptr;
}

void Updater::put(uint32_t offset, const uint8_t* data, uint32_t n) {
    while (next_ < offset) {                       // a gap reads as erased flash
        const uint32_t k = offset - next_ < sizeof g_blank ? offset - next_ : sizeof g_blank;
        crc_ = tuner::hex::crc32(crc_, g_blank, k);
        next_ += k;
    }
    crc_ = tuner::hex::crc32(crc_, data, n);
    next_ = offset + n;
    for (uint32_t i = 0; i < n; ++i) {
        const uint32_t a = stage_at_ + offset + i, chunk = a & ~(kChunk - 1);
        if (chunk != page_at_) {
            flush();
            page_at_ = chunk;
            std::memset(g_chunk, 0xFF, kChunk);
        }
        g_chunk[a - chunk] = data[i];
    }
}

void Updater::flush() {
    if (!page_at_) return;
    while (erased_to_ <= page_at_) {               // every sector up to here, gaps too, so they read 0xFF
        watchdog_feed();                           // an erase stops interrupts, and the tick with them
        eepromemu_flash_erase_sector(reinterpret_cast<void*>(erased_to_));
        erased_to_ += kSector;
    }
    watchdog_feed();
    if (!blank(g_chunk, kChunk)) eepromemu_flash_write(reinterpret_cast<void*>(page_at_), g_chunk, kChunk);
    page_at_ = 0;
}

const char* Updater::finish(int who, uint32_t bytes, uint32_t crc, uint32_t now_ms) {
    if (stage_ == Stage::Failed && who == owner_) {   // the sender hears why once more, and it is over
        stage_ = Stage::Idle;
        return why_;
    }
    if (stage_ != Stage::Receiving) return "update: none in progress";
    if (who != owner_) return "update: another connection is sending one";
    flush();
    const char* why = !image_.done() ? "the file has no end record"
                      : bytes != next_ ? "the length is not the one sent: records are missing"
                      : crc != crc_ ? "the CRC is not the one sent: the transfer was damaged"
                      : nullptr;
    if (!why) {
        arm_dcache_delete(reinterpret_cast<void*>(stage_at_), bytes);   // read the flash itself, not the cache
        uint32_t back = 0;
        for (uint32_t off = 0; off < bytes; off += 0x10000) {
            watchdog_feed();
            const uint32_t n = bytes - off < 0x10000 ? bytes - off : 0x10000;
            back = tuner::hex::crc32(back, reinterpret_cast<const void*>(stage_at_ + off), n);
        }
        if (back != crc) why = "the flash did not take it: the CRC read back differs";
        else if (!tuner::hex::teensy41_header(reinterpret_cast<const uint8_t*>(stage_at_), bytes))
            why = "not a Teensy 4.1 image";
    }
    if (why) {
        fail(why);
        stage_ = Stage::Idle;
        return why_;
    }
    stage_ = Stage::Ready;
    owner_ = -1;
    bytes_ = bytes;
    ready_ms_ = now_ms;
    return nullptr;
}

void Updater::abort() {
    stage_ = Stage::Idle;
    owner_ = -1;
    page_at_ = 0;
}

bool Updater::closed(int who) {
    if (who != owner_ || (stage_ != Stage::Receiving && stage_ != Stage::Failed)) return false;
    const bool dropped = stage_ == Stage::Receiving;
    abort();
    return dropped;
}

bool Updater::poll(uint32_t now_ms) {
    if ((stage_ == Stage::Receiving || stage_ == Stage::Failed) && now_ms - last_ms_ > kRecordMs) {
        const bool dropped = stage_ == Stage::Receiving;
        abort();
        return dropped;
    }
    if (stage_ == Stage::Ready && now_ms - ready_ms_ > kReadyMs) {
        abort();
        return true;
    }
    return false;
}

void Updater::install() {
    if (stage_ != Stage::Ready) return;
    copy_and_restart(stage_at_, bytes_);
}

}  // namespace hw
