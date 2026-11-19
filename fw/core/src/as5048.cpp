#include "tuner/as5048.hpp"

namespace tuner::as5048 {

Reply decode(uint16_t frame) {
    unsigned ones = 0;
    for (int i = 0; i < 16; ++i) ones += (frame >> i) & 1u;
    Reply r;
    r.parity_ok = (ones & 1u) == 0;
    r.error = frame & 0x4000;
    r.data = frame & 0x3FFF;
    return r;
}

Diagnostics diagnostics(uint16_t data) {
    Diagnostics d;
    d.agc = uint8_t(data & 0xFF);
    d.offset_done = data & (1u << 8);
    d.cordic_overflow = data & (1u << 9);
    d.field_strong = data & (1u << 10);
    d.field_weak = data & (1u << 11);
    return d;
}

}  // namespace tuner::as5048
