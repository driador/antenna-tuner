#include "persist.hpp"

#include <EEPROM.h>

#include <cstring>

namespace hw {

namespace {
constexpr uint32_t kMagic = 0x544E5231;   // "TNR1"
constexpr uint16_t kVersion = 1;
constexpr int kHeader = 12;               // magic, version, length, CRC
constexpr int kBody = 2 + 2 + 1 + 3 * 4 + tuner::kSegments * (1 + 5 * 8);
static_assert(kHeader + kBody <= 4284, "Teensy 4.1 EEPROM");

uint8_t g_image[kHeader + kBody];         // what the EEPROM holds
bool g_valid = false;

uint32_t crc32(const uint8_t* p, int n) {
    uint32_t c = 0xFFFFFFFF;
    while (n--) {
        c ^= *p++;
        for (int k = 0; k < 8; ++k) c = (c >> 1) ^ (0xEDB88320 & (0 - (c & 1)));
    }
    return ~c;
}

struct Writer {
    uint8_t* p;
    template <typename T>
    void put(const T& v) {
        std::memcpy(p, &v, sizeof v);
        p += sizeof v;
    }
};

struct Reader {
    const uint8_t* p;
    template <typename T>
    void get(T& v) {
        std::memcpy(&v, p, sizeof v);
        p += sizeof v;
    }
};

void encode(const Persisted& s, uint8_t* image) {
    Writer w{image + kHeader};
    w.put(s.faults.latched_c);
    w.put(s.faults.unacked_b);
    w.put(uint8_t(s.faults.mode));
    for (float t : s.last_turns) w.put(t);
    for (int i = 0; i < tuner::kSegments; ++i) {
        w.put(uint8_t(s.prior_ok[i]));
        const tuner::Prior& p = s.priors[i];
        for (double v : {p.z_load.real(), p.z_load.imag(), p.at.c1, p.at.l, p.at.c2}) w.put(v);
    }
    Writer h{image};
    h.put(kMagic);
    h.put(kVersion);
    h.put(uint16_t(kBody));
    h.put(crc32(image + kHeader, kBody));
}
}  // namespace

bool load(Persisted& s) {
    for (int i = 0; i < kHeader + kBody; ++i) g_image[i] = EEPROM.read(i);
    Reader h{g_image};
    uint32_t magic, crc;
    uint16_t version, length;
    h.get(magic);
    h.get(version);
    h.get(length);
    h.get(crc);
    if (magic != kMagic || version != kVersion || length != kBody || crc != crc32(g_image + kHeader, kBody))
        return false;
    Reader r{g_image + kHeader};
    uint8_t mode, ok;
    r.get(s.faults.latched_c);
    r.get(s.faults.unacked_b);
    r.get(mode);
    s.faults.mode = tuner::Mode(mode);
    for (float& t : s.last_turns) r.get(t);
    for (int i = 0; i < tuner::kSegments; ++i) {
        r.get(ok);
        s.prior_ok[i] = ok;
        double v[5];
        for (double& x : v) r.get(x);
        s.priors[i] = tuner::Prior{tuner::cplx(v[0], v[1]), tuner::Setting{v[2], v[3], v[4]}};
    }
    g_valid = true;
    return true;
}

void save(const Persisted& s) {
    uint8_t image[kHeader + kBody];
    encode(s, image);
    if (g_valid && std::memcmp(image, g_image, sizeof image) == 0) return;
    // The body first, the header with its CRC last: a reset between them leaves a bad CRC, not a
    // record that looks good and is not.
    for (int i = kHeader; i < kHeader + kBody; ++i) EEPROM.update(i, image[i]);
    for (int i = 0; i < kHeader; ++i) EEPROM.update(i, image[i]);
    std::memcpy(g_image, image, sizeof image);
    g_valid = true;
}

}  // namespace hw
