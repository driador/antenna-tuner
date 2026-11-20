// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "storage.hpp"

#include <Arduino.h>
#include <SD.h>

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace hw {

namespace {
constexpr uint32_t kRetryMs = 5000, kProbeMs = 10000, kFlushMs = 60000;   // §8B.5.5: slow, never continuous
DMAMEM char g_doc[24576];                          // one mirror document at a time, in RAM2

bool read_file(const char* path, char* out, size_t cap) {
    File f = SD.open(path, FILE_READ);
    if (!f) return false;
    const size_t n = f.read(out, cap - 1);
    f.close();
    out[n] = 0;
    return n > 0;
}
}  // namespace

void Storage::begin(uint64_t tuner_id) {
    id_ = tuner_id;
    mount();
}

bool Storage::mount() {
    present_ = SD.begin(BUILTIN_SDCARD);
    if (!present_) return false;
    SD.mkdir("/backup");
    SD.mkdir("/log");
    char text[24];
    foreign_ = read_file("/backup/tuner.id", text, sizeof text) && std::strtoull(text, nullptr, 16) != id_;
    if (!foreign_ && !SD.exists("/backup/tuner.id")) adopt(id_);
    uint32_t numbers[64];
    const int n = list(numbers, 64);
    next_backup_ = n ? numbers[n - 1] + 1 : 1;
    return present_;
}

void Storage::lost() { present_ = false; }

int Storage::poll(uint32_t now_ms, const tuner::EventLog& log) {
    if (!present_) {
        if (now_ms - last_try_ms_ < kRetryMs) return 0;
        last_try_ms_ = now_ms;
        if (!mount()) return 0;
        flush(log);                                    // what was buffered while it was out
        return +1;
    }
    if (now_ms - last_probe_ms_ >= kProbeMs) {         // the extender hides a removal: look
        last_probe_ms_ = now_ms;
        if (!SD.exists("/backup")) {
            lost();
            return -1;
        }
    }
    if (log.next() != logged_ && (now_ms - last_flush_ms_ >= kFlushMs || log.next() - logged_ >= 8)) {
        last_flush_ms_ = now_ms;
        if (!flush(log)) return -1;
    }
    return 0;
}

bool Storage::flush(const tuner::EventLog& log) {
    if (!present_ || foreign_) return present_;
    tuner::EventRecord e[16];
    for (int n; (n = log.since(logged_, e, 16)) > 0;) {
        File f = SD.open("/log/events.log", FILE_WRITE);   // appends
        if (!f) {
            lost();
            return false;
        }
        char line[160];
        for (int i = 0; i < n; ++i) {
            const size_t len = tuner::EventLog::format(e[i], line, sizeof line - 1);
            line[len] = '\n';
            if (f.write(line, len + 1) != len + 1) {
                f.close();
                lost();
                return false;
            }
        }
        f.close();
        logged_ = e[n - 1].seq + 1;
    }
    return true;
}

bool Storage::write(const char* path, const char* data, size_t n) {
    if (!present_ || foreign_) return false;
    // §8B.5.5: a temporary file, flushed, then renamed. Power lost midway leaves the old file.
    static const char kTmp[] = "/backup/write.tmp";
    SD.remove(kTmp);                                    // FILE_WRITE_BEGIN does not truncate
    File f = SD.open(kTmp, FILE_WRITE_BEGIN);
    if (!f) {
        lost();
        return false;
    }
    const bool ok = f.write(data, n) == n;
    f.flush();
    f.close();
    if (!ok) {
        lost();
        return false;
    }
    SD.remove(path);
    if (!SD.rename(kTmp, path)) {
        lost();
        return false;
    }
    return true;
}

bool Storage::current(const tuner::Settings& s, const char* saved) {
    const size_t n = tuner::write_mirror(s, saved, g_doc, sizeof g_doc);
    return n && write("/backup/current.json", g_doc, n);
}

bool Storage::backup(const tuner::Settings& s, const char* saved) {
    const size_t n = tuner::write_mirror(s, saved, g_doc, sizeof g_doc);
    if (!n) return false;
    char name[64], stamp[24] = "";
    if (saved && saved[0]) {                            // 2026-11-20T14:03:11Z -> 20261120T140311
        int k = 0;
        for (const char* p = saved; *p && k < 15; ++p)
            if (*p != '-' && *p != ':' && *p != 'Z') stamp[k++] = *p;
        stamp[k] = 0;
    }
    std::snprintf(name, sizeof name, "/backup/%06lu%s%s.json", static_cast<unsigned long>(next_backup_),
                  stamp[0] ? "-" : "", stamp);
    if (!write(name, g_doc, n) || !write("/backup/current.json", g_doc, n)) return false;
    ++next_backup_;
    uint32_t have[64], drop[64];
    const int k = tuner::backups_to_prune(have, list(have, 64), drop, 64);
    char path[64];
    File dir = SD.open("/backup");
    for (File f = dir.openNextFile(); f; f = dir.openNextFile()) {
        uint32_t num;
        const bool gone = tuner::backup_number(f.name(), num) && std::find(drop, drop + k, num) != drop + k;
        std::snprintf(path, sizeof path, "/backup/%s", f.name());
        f.close();
        if (gone) SD.remove(path);
    }
    dir.close();
    return true;
}

int Storage::list(uint32_t numbers[], int cap) {
    if (!present_) return 0;
    File dir = SD.open("/backup");
    if (!dir) return 0;
    int n = 0;
    for (File f = dir.openNextFile(); f; f = dir.openNextFile()) {
        uint32_t num;
        if (n < cap && tuner::backup_number(f.name(), num)) numbers[n++] = num;
        f.close();
    }
    dir.close();
    std::sort(numbers, numbers + n);
    return n;
}

const char* Storage::read(uint32_t number, tuner::Settings& out) {
    if (!present_) return "no card";
    File dir = SD.open("/backup");
    char path[64] = "";
    for (File f = dir.openNextFile(); f; f = dir.openNextFile()) {
        uint32_t num;
        if (tuner::backup_number(f.name(), num) && num == number) std::snprintf(path, sizeof path, "/backup/%s", f.name());
        f.close();
    }
    dir.close();
    if (!path[0]) return "no such backup";
    if (!read_file(path, g_doc, sizeof g_doc)) return "unreadable";
    return tuner::read_mirror(g_doc, out);
}

bool Storage::adopt(uint64_t tuner_id) {
    if (!present_) return false;
    char text[24];
    const int n = std::snprintf(text, sizeof text, "%016llx\n", static_cast<unsigned long long>(tuner_id));
    foreign_ = false;
    id_ = tuner_id;
    return write("/backup/tuner.id", text, size_t(n));
}

bool Storage::recovery(tuner::NetConfig& net, char* report, size_t cap) {
    char text[512];
    if (!present_ || !read_file("/recovery.cfg", text, sizeof text)) return false;
    const bool changed = tuner::read_recovery(text, net, report, cap);
    SD.remove("/recovery.applied");
    SD.rename("/recovery.cfg", "/recovery.applied");   // once only
    return changed;
}

}  // namespace hw
