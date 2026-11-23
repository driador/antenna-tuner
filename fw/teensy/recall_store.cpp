// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "recall_store.hpp"

#include <LittleFS.h>

namespace hw {

namespace {
LittleFS_Program g_fs;
uint8_t g_image[tuner::Recall::image_size(tuner::kRecallMax)];
const char* const kFile = "/recall.bin";
const char* const kTemp = "/recall.tmp";
}  // namespace

bool RecallStore::begin(tuner::Recall& r) {
    ok_ = g_fs.begin(kBytes);            // formats a blank or foreign area itself
    if (!ok_) return false;
    File f = g_fs.open(kFile, FILE_READ);
    if (f) {
        const size_t n = f.read(g_image, sizeof g_image);
        f.close();
        r.load(g_image, n);              // a damaged file leaves the memory empty
    }
    saved_ = seen_ = r.changes();
    return true;
}

void RecallStore::tick(const tuner::Recall& r, uint32_t now_ms) {
    if (!ok_) return;
    if (r.changes() != seen_) {
        seen_ = r.changes();
        changed_ms_ = now_ms;
        return;
    }
    if (seen_ == saved_ || now_ms - changed_ms_ < kQuietMs) return;
    save(r);
}

void RecallStore::save(const tuner::Recall& r) {
    if (!ok_ || r.changes() == saved_) return;
    // The whole file, then a rename: a power cut mid-write leaves the last good copy.
    const size_t n = r.save(g_image, sizeof g_image);
    File f = g_fs.open(kTemp, FILE_WRITE_BEGIN);
    if (!f) return;
    const bool whole = f.write(g_image, n) == n;
    f.close();
    if (whole && g_fs.rename(kTemp, kFile)) saved_ = seen_ = r.changes();
}

}  // namespace hw
