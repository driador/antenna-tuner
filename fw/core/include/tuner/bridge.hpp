// The vector bridge: AD8302 on the coupler's FWD (INPB, reference) and REF (INPA) ports (§6A.5).
// It reports |Gamma| and |theta| at the network's 50 ohm input; the sign of theta is lost (§6A.7).
#pragma once
#include <complex>

namespace tuner {

using cplx = std::complex<double>;

struct Ad8302Scale {            // measurement mode, datasheet defaults (§6A.5)
    double v_center = 0.900;    // V at 0 dB ratio and at 90 degrees
    double v_per_db = 0.030;
    double v_phs_zero = 1.800;  // V at 0 degrees, falling to 0 V at 180
    double v_per_deg = 0.010;
};

struct GammaReading {
    double mag = 0;             // |Gamma|, clamped to the AD8302's range
    double theta_deg = 0;       // |arg Gamma|, 0..180
};

GammaReading gamma_from_ad8302(double v_mag, double v_phs, const Ad8302Scale& k = {});
// The forward model, for simulation and tests.
void ad8302_from_gamma(cplx gamma, double& v_mag, double& v_phs, const Ad8302Scale& k = {});

inline cplx gamma_of(const GammaReading& g, int sign) {
    return std::polar(g.mag, sign * g.theta_deg * 3.14159265358979323846 / 180);
}
inline cplx z_from_gamma(cplx gamma, double z0 = 50) { return z0 * (1.0 + gamma) / (1.0 - gamma); }
inline cplx gamma_from_z(cplx z, double z0 = 50) { return (z - z0) / (z + z0); }
inline double swr_from_mag(double m) { return m >= 0.999 ? 999.0 : (1 + m) / (1 - m); }

// One-port error correction from open, short and load standards at the AUX port (§6A.8):
// measured = e00 + t * G / (1 - e11 * G). Built per band from the three raw readings.
struct OnePortCal {
    cplx e00{0, 0}, e11{0, 0}, t{1, 0};
    static OnePortCal from_standards(cplx m_open, cplx m_short, cplx m_load);
    cplx correct(cplx measured) const { return (measured - e00) / (t + e11 * (measured - e00)); }
    cplx distort(cplx actual) const { return e00 + t * actual / (1.0 - e11 * actual); }
};

}  // namespace tuner
