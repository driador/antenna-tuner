// A monotonic piecewise-linear map. Each element's calibration is one: shaft turns from its low end to
// farads or henries (§9 item 54). Outside the points it extends the end segments.
#pragma once

namespace tuner {

struct Curve {
    static constexpr int kMax = 24;
    int n = 0;
    double x[kMax] = {}, y[kMax] = {};

    static Curve line(double x0, double y0, double x1, double y1);
    bool add(double px, double py);    // appends a point; false when full
    bool valid() const;                // two or more points, x rising, y strictly monotonic
    double at(double px) const;
    double inverse(double py) const;
    double y_lo() const { return y[0] < y[n - 1] ? y[0] : y[n - 1]; }
    double y_hi() const { return y[0] < y[n - 1] ? y[n - 1] : y[0]; }
};

// The element models until commissioning measures the real curves (§9 item 54). The capacitors are
// linear over their turns; the roller is the NEC model of the wound roller on the deck at 1 MHz
// (nec/out/roller_vna_k*_deck.csv), 0-22 turns.
Curve c1_model(double turns);
Curve c2_model(double turns);
Curve roller_model();

}  // namespace tuner
