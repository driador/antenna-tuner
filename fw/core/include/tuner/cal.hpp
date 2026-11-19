// Calibration of the measurement chain, per band (§6A.8).
//
// The vector path: an open and a short at the AUX port give the AD8302's 0 dB point and its phase
// endpoints (0° and 180°), and the internal load in CAL gives the floor, the directivity limit below
// which a reading means "matched" and nothing more. The part reports only |θ| (§6A.7), so a full
// complex one-port correction cannot be fitted to it; what is calibrated is the scalar transfer the
// part actually has, volts to dB and volts to degrees. A resistive standard of known |Γ| optionally
// replaces the datasheet's 30 mV/dB with a measured slope.
//
// The magnitude path is a Curve (curve.hpp) per band: the forward detector's volts against the watts
// a wattmeter reads, at several drive levels into the load. A curve, because the diodes go from square
// law to linear across the range (§6A.8: "a curve, not a scale factor").
#pragma once

#include "tuner/bridge.hpp"

namespace tuner {

struct Standard {                     // AD8302 outputs averaged over a gate or more, volts against VREF
    double v_mag = 0, v_phs = 0;
};

struct BridgeCal {
    bool valid = false;
    Ad8302Scale scale;
    double floor_db = -30;            // what the load reads: nothing below it means anything
};

enum class CalError : unsigned char { None, OpenShortDisagree, PhaseSpanSmall, LoadNotLow, SlopeOutOfRange };
const char* cal_error_text(CalError e);

CalError bridge_cal(const Standard& open, const Standard& shorted, const Standard& load, BridgeCal& out);
CalError bridge_cal_slope(const Standard& known, double known_mag, const Standard& load, BridgeCal& cal);

// A reading through the band's calibration, held at its floor.
GammaReading calibrated(const BridgeCal& c, double v_mag, double v_phs);

}  // namespace tuner
