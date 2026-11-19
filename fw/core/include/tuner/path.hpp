// The RF path (§6B.2): TUNE (no relay), AUX (K1) or CAL (K1 + K2). A change follows §5.5: the vote is
// held down, the relays change once the RF has decayed and the hold latch has opened, the coil
// currents confirm them, and only then is the vote given back. The first key-down after a change is
// checked at the cal-load detector: RF there in CAL, none in TUNE or AUX (§6B.3a). Any disagreement is
// a class B fault, and the relays go back to TUNE, their de-energized state.
#pragma once
#include <cstdint>

namespace tuner {

enum class Path : uint8_t { Tune, Aux, Cal };
const char* path_name(Path p);

class PathSwitch {
public:
    struct Config {
        uint32_t blank_ms = 100;   // vote down this long first: RF decay and the amp's relay (§7.4.5),
                                   // and the latch's 39-67 ms (§5.5)
        uint32_t settle_ms = 25;   // contact bounce, then the coil currents are read (§5.5)
    };
    struct In {
        uint32_t now_ms = 0;
        bool k1_current = false, k2_current = false;   // each driver channel's coil-current sense
        bool carrier = false;                          // a steady key-down
        bool load_rf = false;                          // the cal-load detector sees RF
    };
    struct Out {
        bool hold_vote = false;    // the MCU's vote must stay down
        bool k1 = false, k2 = false;
        bool mismatch = false;     // this tick: raise the class B fault
    };

    PathSwitch() = default;
    explicit PathSwitch(const Config& c) : cfg_(c) {}

    bool request(Path p, uint32_t now_ms);   // false while a change is under way
    Out step(const In& in);
    Path path() const { return path_; }      // the confirmed path
    bool busy() const { return phase_ != Phase::Steady; }

private:
    enum class Phase : uint8_t { Steady, Blanking, Settling };
    static bool k1_for(Path p) { return p != Path::Tune; }
    static bool k2_for(Path p) { return p == Path::Cal; }

    Config cfg_;
    Phase phase_ = Phase::Steady;
    Path path_ = Path::Tune, target_ = Path::Tune;
    uint32_t t0_ = 0;
    bool rf_check_ = false;
    bool coils_ok_ = true;
};

}  // namespace tuner
