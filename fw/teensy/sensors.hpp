// The measured inputs (§6A.4-§6A.10, §8): the AD8302 bridge averaged over each frequency-counter gate,
// the frequency and the steady-carrier test, the MCP23017 (panel encoders, bypass key, every term of
// the permissive), and the tank thermistor.
#pragma once
#include <cstdint>

#include "tuner/fsm.hpp"
#include "tuner/sense.hpp"

namespace hw {

class Sensors {
public:
    bool begin();                     // the counter, the ADC and the MCP23017; false if it does not answer
    void poll(uint32_t now_ms);       // every loop: bridge samples, the thermistor, finished gates

    // A gate finished since the last call: its frequency, and the bridge averaged over it. start_ms is
    // when it began, so the caller can refuse one that overlaps a move.
    bool take_gate(tuner::Measurement& m, uint32_t& start_ms);
    void restart_bridge();            // drop the samples so far: a move started or ended
    bool carrier() const { return carrier_.present(); }
    double mhz() const { return mhz_; }
    const tuner::GammaReading& gamma() const { return gamma_; }   // the last gate's

    bool read_iox();                  // false if it did not answer
    bool iox(uint8_t bit) const { return iox_ & (1u << bit); }
    uint16_t iox_word() const { return iox_; }

    double tank_c() const { return tank_c_; }            // NaN: open or shorted thermistor
    bool over_temp() const { return over_temp_; }        // a failed sensor counts as hot
    double vref() const { return vref_; }                // AD_VREF on the Teensy's 3.3 V scale
    bool bridge_alive() const { return vref_ > 1.6 && vref_ < 2.0; }   // the measurement board answers

private:
    tuner::CarrierDetector carrier_;
    tuner::Hysteresis hot_{0, 0};
    uint32_t last_sample_ms_ = 0, last_therm_ms_ = 0;
    double sum_mag_ = 0, sum_phs_ = 0, sum_ref_ = 0;
    uint32_t n_ = 0;
    bool fresh_ = false;
    tuner::Measurement pending_;
    uint32_t pending_start_ = 0;
    double mhz_ = 0, tank_c_ = 0, vref_ = 0;
    tuner::GammaReading gamma_;
    uint16_t iox_ = 0;
    bool over_temp_ = true;
};

}  // namespace hw
