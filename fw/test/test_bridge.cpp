// The AD8302 extraction (§6A.6), its sign ambiguity (§6A.7) and the one-port calibration (§6A.8).
#include <cmath>

#include "harness.hpp"
#include "tuner/bridge.hpp"

using namespace tuner;

TEST(sign_is_lost_as_the_log_shows) {
    // §6A.7: 91 +/- j65 give identical outputs, 0.717 V and 1.470 V.
    double vm1, vp1, vm2, vp2;
    ad8302_from_gamma(gamma_from_z(cplx(91, 65)), vm1, vp1);
    ad8302_from_gamma(gamma_from_z(cplx(91, -65)), vm2, vp2);
    CHECK_NEAR(vm1, 0.717, 0.0005);
    CHECK_NEAR(vp1, 1.470, 0.0005);
    CHECK_NEAR(vm1, vm2, 1e-12);
    CHECK_NEAR(vp1, vp2, 1e-12);
}

TEST(round_trip_at_the_tuners_own_impedances) {
    // §6A.6: recovery is exact once the sign is known.
    const cplx zs[] = {{9.6, 174}, {2587, 984}, {600, -1127}, {91, 65}, {91, -65}, {12, -3}};
    for (const cplx& z : zs) {
        double vm, vp;
        ad8302_from_gamma(gamma_from_z(z), vm, vp);
        const GammaReading g = gamma_from_ad8302(vm, vp);
        const cplx back = z_from_gamma(gamma_of(g, z.imag() >= 0 ? +1 : -1));
        CHECK_NEAR(std::abs(back - z) / std::abs(z), 0.0, 1e-9);
    }
}

TEST(floor_and_ceiling) {
    // Below -30 dB the part reads its floor: SWR 1.07, "the tune is done" (§6A.6).
    double vm, vp;
    ad8302_from_gamma(gamma_from_z(cplx(50.5, 0)), vm, vp);
    const GammaReading g = gamma_from_ad8302(vm, vp);
    CHECK_NEAR(g.mag, std::pow(10.0, -1.5), 1e-12);
    CHECK_NEAR(swr_from_mag(g.mag), 1.065, 0.001);
    // A reading above 0 dB is noise on a total reflection, never more than |Gamma| = 1.
    CHECK_NEAR(gamma_from_ad8302(0.95, 1.8).mag, 1.0, 1e-12);
    CHECK(swr_from_mag(0.999) == 999.0);
    CHECK_NEAR(gamma_from_ad8302(0.9, -0.2).theta_deg, 180.0, 1e-12);
}

TEST(one_port_calibration_recovers_the_error_terms) {
    // A plausible fixture: some directivity leak, a port match error, a gain/phase tracking error.
    OnePortCal truth;
    truth.e00 = {0.05, 0.02};
    truth.e11 = {0.10, -0.05};
    truth.t = {0.90, 0.10};
    const OnePortCal cal =
        OnePortCal::from_standards(truth.distort(1.0), truth.distort(-1.0), truth.distort(0.0));
    CHECK_NEAR(std::abs(cal.e00 - truth.e00), 0.0, 1e-12);
    CHECK_NEAR(std::abs(cal.e11 - truth.e11), 0.0, 1e-12);
    CHECK_NEAR(std::abs(cal.t - truth.t), 0.0, 1e-12);
    const cplx gs[] = {{0, 0}, {0.3, 0.4}, {-0.7, 0.1}, {0.05, -0.9}};
    for (const cplx& g : gs) CHECK_NEAR(std::abs(cal.correct(truth.distort(g)) - g), 0.0, 1e-12);
}
