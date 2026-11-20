// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// Enough JSON for the SD mirror (§8B.5.4d) and the web UI, without the heap: a writer into a fixed
// buffer that records whether anything was cut, and a reader that finds one value by its dotted path
// ("calibration.20m.v_center", "profiles.12.z_re": a number indexes an array).
#pragma once
#include <cstddef>

namespace tuner {

class JsonWriter {
public:
    JsonWriter(char* buf, size_t cap);
    JsonWriter& open(const char* key = nullptr);         // {
    JsonWriter& close();                                 // }
    JsonWriter& open_array(const char* key = nullptr);   // [
    JsonWriter& close_array();                           // ]
    JsonWriter& str(const char* key, const char* v);     // a null key writes an array element
    JsonWriter& num(const char* key, double v, int digits = 7);
    JsonWriter& integer(const char* key, long long v);
    JsonWriter& boolean(const char* key, bool v);
    JsonWriter& null(const char* key);
    bool ok() const { return !overflow_ && depth_ == 0; }
    size_t size() const { return n_; }

private:
    void item(const char* key);            // the separator, then the key when there is one
    void quoted(const char* v);
    void put(const char* s, size_t len);
    void put(const char* s);
    char* buf_;
    size_t cap_, n_ = 0;
    bool overflow_ = false;
    int depth_ = 0;
    bool first_[24] = {true};
};

// The value at path: its first character and its length, or nullptr.
const char* json_find(const char* doc, const char* path, size_t& len);
bool json_number(const char* doc, const char* path, double& out);
bool json_bool(const char* doc, const char* path, bool& out);
bool json_string(const char* doc, const char* path, char* out, size_t cap);   // unescapes \" and \\.

}  // namespace tuner
