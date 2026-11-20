// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

#include "tuner/json.hpp"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace tuner {

JsonWriter::JsonWriter(char* buf, size_t cap) : buf_(buf), cap_(cap) {
    if (cap_) buf_[0] = 0;
}

void JsonWriter::put(const char* s, size_t len) {
    if (n_ + len + 1 > cap_) {
        overflow_ = true;
        return;
    }
    std::memcpy(buf_ + n_, s, len);
    n_ += len;
    buf_[n_] = 0;
}

void JsonWriter::put(const char* s) { put(s, std::strlen(s)); }

void JsonWriter::quoted(const char* v) {
    put("\"");
    for (const char* p = v; *p; ++p) {
        if (*p == '"' || *p == '\\') put("\\");
        if (static_cast<unsigned char>(*p) >= 0x20) put(p, 1);
    }
    put("\"");
}

void JsonWriter::item(const char* key) {
    if (depth_ > 0) {
        if (!first_[depth_]) put(",");
        first_[depth_] = false;
    }
    if (key) {
        quoted(key);
        put(":");
    }
}

JsonWriter& JsonWriter::open(const char* key) {
    item(key);
    put("{");
    if (depth_ < 23) first_[++depth_] = true;
    return *this;
}

JsonWriter& JsonWriter::close() {
    put("}");
    if (depth_ > 0) --depth_;
    return *this;
}

JsonWriter& JsonWriter::open_array(const char* key) {
    item(key);
    put("[");
    if (depth_ < 23) first_[++depth_] = true;
    return *this;
}

JsonWriter& JsonWriter::close_array() {
    put("]");
    if (depth_ > 0) --depth_;
    return *this;
}

JsonWriter& JsonWriter::str(const char* key, const char* v) {
    item(key);
    quoted(v);
    return *this;
}

JsonWriter& JsonWriter::num(const char* key, double v, int digits) {
    item(key);
    if (!std::isfinite(v)) {
        put("null");
        return *this;
    }
    char b[32];
    std::snprintf(b, sizeof b, "%.*g", digits, v);
    put(b);
    return *this;
}

JsonWriter& JsonWriter::integer(const char* key, long long v) {
    item(key);
    char b[24];
    std::snprintf(b, sizeof b, "%lld", v);
    put(b);
    return *this;
}

JsonWriter& JsonWriter::boolean(const char* key, bool v) {
    item(key);
    put(v ? "true" : "false");
    return *this;
}

JsonWriter& JsonWriter::null(const char* key) {
    item(key);
    put("null");
    return *this;
}

namespace {
const char* ws(const char* p) {
    while (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t') ++p;
    return p;
}

const char* skip_string(const char* p) {   // p at the opening quote; returns past the closing one
    for (++p; *p && *p != '"'; ++p)
        if (*p == '\\' && p[1]) ++p;
    return *p ? p + 1 : nullptr;
}

const char* skip_value(const char* p) {
    p = ws(p);
    if (*p == '"') return skip_string(p);
    if (*p == '{' || *p == '[') {
        const char open = *p, shut = open == '{' ? '}' : ']';
        int depth = 0;
        for (; *p; ++p) {
            if (*p == '"') {
                p = skip_string(p);
                if (!p) return nullptr;
                --p;
            } else if (*p == open) {
                ++depth;
            } else if (*p == shut && --depth == 0) {
                return p + 1;
            }
        }
        return nullptr;
    }
    while (*p && *p != ',' && *p != '}' && *p != ']' && *p != ' ' && *p != '\n') ++p;
    return p;
}

// Within the object or array at p, the value for one path component.
const char* member(const char* p, const char* name, size_t name_len) {
    p = ws(p);
    if (*p == '{') {
        p = ws(p + 1);
        while (*p == '"') {
            const char* k = p + 1;
            const char* end = skip_string(p);
            if (!end) return nullptr;
            const size_t klen = size_t(end - 1 - k);
            p = ws(end);
            if (*p != ':') return nullptr;
            p = ws(p + 1);
            if (klen == name_len && std::strncmp(k, name, klen) == 0) return p;
            p = skip_value(p);
            if (!p) return nullptr;
            p = ws(p);
            if (*p != ',') return nullptr;
            p = ws(p + 1);
        }
        return nullptr;
    }
    if (*p == '[') {
        char* stop;
        const long index = std::strtol(name, &stop, 10);
        if (stop != name + name_len || index < 0) return nullptr;
        p = ws(p + 1);
        for (long i = 0; *p && *p != ']'; ++i) {
            if (i == index) return p;
            p = skip_value(p);
            if (!p) return nullptr;
            p = ws(p);
            if (*p == ',') p = ws(p + 1);
        }
    }
    return nullptr;
}
}  // namespace

const char* json_find(const char* doc, const char* path, size_t& len) {
    const char* p = doc;
    while (p && *path) {
        const char* dot = std::strchr(path, '.');
        const size_t n = dot ? size_t(dot - path) : std::strlen(path);
        p = member(p, path, n);
        path += n + (dot ? 1 : 0);
    }
    if (!p) return nullptr;
    p = ws(p);
    const char* end = skip_value(p);
    if (!end) return nullptr;
    len = size_t(end - p);
    return p;
}

bool json_number(const char* doc, const char* path, double& out) {
    size_t len;
    const char* v = json_find(doc, path, len);
    if (!v || len == 0 || (*v != '-' && (*v < '0' || *v > '9'))) return false;
    out = std::strtod(v, nullptr);
    return true;
}

bool json_bool(const char* doc, const char* path, bool& out) {
    size_t len;
    const char* v = json_find(doc, path, len);
    if (!v) return false;
    if (len == 4 && !std::strncmp(v, "true", 4)) out = true;
    else if (len == 5 && !std::strncmp(v, "false", 5)) out = false;
    else return false;
    return true;
}

bool json_string(const char* doc, const char* path, char* out, size_t cap) {
    size_t len;
    const char* v = json_find(doc, path, len);
    if (!v || *v != '"' || cap == 0) return false;
    size_t n = 0;
    for (const char* p = v + 1; p < v + len - 1 && n + 1 < cap; ++p) {
        if (*p == '\\' && p + 1 < v + len - 1) ++p;
        out[n++] = *p;
    }
    out[n] = 0;
    return true;
}

}  // namespace tuner
