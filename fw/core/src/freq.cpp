#include "tuner/freq.hpp"

#include <cmath>

namespace tuner {

const Band kBands[kBandCount] = {
    {"160m", 1.800, 2.000},   {"80m", 3.500, 4.000},   {"60m", 5.330, 5.406},  {"40m", 7.000, 7.300},
    {"30m", 10.100, 10.150},  {"20m", 14.000, 14.350}, {"17m", 18.068, 18.168}, {"15m", 21.000, 21.450},
    {"12m", 24.890, 24.990},  {"10m", 28.000, 29.700},
};

namespace {
int segments_in(const Band& b) { return int(std::ceil((b.hi_mhz - b.lo_mhz) / (0.01 * b.lo_mhz) - 1e-9)); }
}  // namespace

int segment_of(double mhz) {
    int base = 0;
    for (const Band& b : kBands) {
        const int n = segments_in(b);
        if (mhz >= b.lo_mhz && mhz <= b.hi_mhz) {
            const int k = int((mhz - b.lo_mhz) / (0.01 * b.lo_mhz));
            return base + (k < n ? k : n - 1);
        }
        base += n;
    }
    return -1;
}

int band_of_segment(int seg) {
    for (int i = 0; i < kBandCount; ++i) {
        const int n = segments_in(kBands[i]);
        if (seg < n) return i;
        seg -= n;
    }
    return -1;
}

double segment_center(int seg) {
    for (const Band& b : kBands) {
        const int n = segments_in(b);
        if (seg < n) return std::fmin(b.lo_mhz + (seg + 0.5) * 0.01 * b.lo_mhz, (b.lo_mhz * (1 + 0.01 * seg) + b.hi_mhz) / 2);
        seg -= n;
    }
    return 0;
}

const Band* band_of(double mhz) {
    for (const Band& b : kBands)
        if (mhz >= b.lo_mhz && mhz <= b.hi_mhz) return &b;
    return nullptr;
}

bool solution_valid(double solved_mhz, double now_mhz, double frac) {
    if (std::fabs(now_mhz - solved_mhz) > frac * solved_mhz) return false;
    return band_of(now_mhz) == band_of(solved_mhz);
}

}  // namespace tuner
