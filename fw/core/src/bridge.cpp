#include "tuner/bridge.hpp"

#include <cmath>

namespace tuner {

namespace {
constexpr double kPi = 3.14159265358979323846;
double clamp(double v, double lo, double hi) { return v < lo ? lo : (v > hi ? hi : v); }
}  // namespace

GammaReading gamma_from_ad8302(double v_mag, double v_phs, const Ad8302Scale& k) {
    // INPA = REF, INPB = FWD, so the ratio is |Gamma|: 20 log10 |Gamma| = (V_MAG - 0.9) / 0.03 (§6A.6).
    // The part spans +/-30 dB about the center; a reflection is never above 0 dB.
    const double db = clamp((v_mag - k.v_center) / k.v_per_db, -30.0, 0.0);
    GammaReading g;
    g.mag = std::pow(10.0, db / 20.0);
    g.theta_deg = clamp((k.v_phs_zero - v_phs) / k.v_per_deg, 0.0, 180.0);
    return g;
}

void ad8302_from_gamma(cplx gamma, double& v_mag, double& v_phs, const Ad8302Scale& k) {
    const double mag = std::abs(gamma);
    const double db = clamp(mag > 0 ? 20 * std::log10(mag) : -30.0, -30.0, 30.0);
    v_mag = k.v_center + db * k.v_per_db;
    const double deg = std::abs(std::arg(gamma)) * 180 / kPi;       // the part reports 0..180 only
    v_phs = k.v_phs_zero - deg * k.v_per_deg;
}

OnePortCal OnePortCal::from_standards(cplx m_open, cplx m_short, cplx m_load) {
    // Ideal standards: open +1, short -1, load 0.
    OnePortCal c;
    c.e00 = m_load;
    const cplx a = m_open - c.e00;       // = t / (1 - e11)
    const cplx b = m_short - c.e00;      // = -t / (1 + e11)
    c.e11 = (a + b) / (a - b);
    c.t = a * (1.0 - c.e11);
    return c;
}

}  // namespace tuner
