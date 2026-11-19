#include "tuner/cal.hpp"

#include <cmath>

namespace tuner {

namespace {
constexpr double kNominalPerDb = 0.030, kNominalPerDeg = 0.010;   // AD8302 datasheet (§6A.5)
}  // namespace

const char* cal_error_text(CalError e) {
    switch (e) {
        case CalError::None: return "ok";
        case CalError::OpenShortDisagree: return "open and short differ by over 2 dB: check both standards";
        case CalError::PhaseSpanSmall: return "open and short phases too close: is the short a short?";
        case CalError::LoadNotLow: return "load reads above -20 dB: is CAL selected?";
        case CalError::SlopeOutOfRange: return "known standard gives a slope over 20 % off 30 mV/dB";
    }
    return "?";
}

CalError bridge_cal(const Standard& open, const Standard& shorted, const Standard& load, BridgeCal& out) {
    BridgeCal c;
    if (std::fabs(open.v_mag - shorted.v_mag) > 2 * kNominalPerDb) return CalError::OpenShortDisagree;
    c.scale.v_center = (open.v_mag + shorted.v_mag) / 2;    // both are |Γ| = 1, which is 0 dB
    c.scale.v_per_db = kNominalPerDb;
    const double span = open.v_phs - shorted.v_phs;           // 0° reads high, 180° low
    if (span < 90 * kNominalPerDeg) return CalError::PhaseSpanSmall;
    c.scale.v_phs_zero = open.v_phs;
    c.scale.v_per_deg = span / 180;
    c.floor_db = (load.v_mag - c.scale.v_center) / c.scale.v_per_db;
    if (c.floor_db > -20) return CalError::LoadNotLow;
    c.valid = true;
    out = c;
    return CalError::None;
}

CalError bridge_cal_slope(const Standard& known, double known_mag, const Standard& load, BridgeCal& cal) {
    const double slope = (known.v_mag - cal.scale.v_center) / (20 * std::log10(known_mag));
    if (!(std::fabs(slope / kNominalPerDb - 1) <= 0.2)) return CalError::SlopeOutOfRange;
    cal.scale.v_per_db = slope;
    cal.floor_db = (load.v_mag - cal.scale.v_center) / slope;
    return CalError::None;
}

GammaReading calibrated(const BridgeCal& c, double v_mag, double v_phs) {
    GammaReading g = gamma_from_ad8302(v_mag, v_phs, c.scale);
    const double floor = std::pow(10.0, c.floor_db / 20);
    if (g.mag < floor) g.mag = floor;
    return g;
}

}  // namespace tuner
