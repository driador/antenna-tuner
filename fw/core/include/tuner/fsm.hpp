// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The tuning state machine (§8B.1 to §8B.3), as a pure function of its inputs: the Teensy layer reads
// the hardware into Inputs once per tick and carries out Outputs. Nothing here touches a pin.
//
//   SELF-TEST --> IDLE --(fresh carrier)--> MEASURE --+-- matched already -----------------> MATCHED
//      |           ^                                  +-- far off, stored setting --> MOVE --> VERIFY
//      v           |                                  +-- sign known --> SOLVE --> MOVE --> VERIFY
//    FAULT --------+  (cleared; next carrier)          +-- sign in doubt --> PROBE --> SOLVE
//
//   VERIFY: converged --> MATCHED; attempts left --> SOLVE (or PROBE when the sign is in doubt);
//           exhausted --> MATCHED if under the retune threshold, else FAULT.
//   MATCHED: retune (§8B.2) --> MEASURE's decision. Carrier gone --> IDLE from MEASURE, PROBE, VERIFY
//   or MATCHED, holding position; a move in progress finishes first. The bypass key, or the RF path
//   leaving TUNE, --> IDLE at once. IDLE --(jog)--> MOVE --> IDLE is the manual override.
//
// The bridge cannot tell +theta from -theta (§6A.7). A stored prior for the frequency decides when it
// clearly favors one hypothesis (option 2), once per tune; otherwise PROBE steps C2 a little and keeps
// the hypothesis that predicts the new reading (option 1). VERIFY repeats that test across every move,
// so a wrong prior costs one attempt, not the tune.
//
// A reading far from match (|Gamma| near 1) cannot be de-embedded well: a fraction of a dB moves R
// by a large factor. If a stored setting exists for the frequency, MEASURE first drives there (§7.6,
// §8B.3a) and measures again. A solve from such a reading is a coarse move, not an attempt, and a move
// that leaves a reading like that, much worse than the best so far, is undone.
#pragma once
#include <cstdint>

#include "tuner/bridge.hpp"
#include "tuner/faults.hpp"
#include "tuner/freq.hpp"
#include "tuner/tnet.hpp"

namespace tuner {

enum class State : uint8_t { SelfTest, Idle, Measure, Probe, Solve, Move, Verify, Matched, Fault };
const char* state_name(State s);

struct Config {
    Parts parts;
    double match_swr = 1.2;        // converged; well under the retune threshold, so a match holds
    double retune_swr = 1.5;       // §8B.2: retune above this with a carrier present
    int max_attempts = 3;          // §8B.3
    double window_frac = 0.005;    // §8B.2 validity window
    double probe_step = 0.10;      // §6A.7: C2 step for the sign probe, as a fraction of C2
    double near_tolerance = 0.03;  // §8B.3a: prefer the nearest solution within 3 % of the lowest current
    double trust_swr = 5.0;        // a reading above this is too far from match to refine from
    int max_coarse = 3;            // coarse moves per tune, on top of the attempts
    double gamma_ceiling = 0.98;   // |Gamma| is taken as at most this when de-embedding
    uint32_t rf_decay_ms = 30;     // §5.5, §7.4.5: permit down this long before anything moves
    uint32_t move_timeout_ms = 15000;   // a move still running after this is a position fault
};

struct Measurement {               // one complete MEASURE: the 200 ms frequency gate plus the bridge
    double mhz = 0;
    GammaReading gamma;            // at the network's 50 ohm input
};

// What the Teensy layer reports each tick. have_measurement is set only for a measurement whose gate
// started after the last move finished, so nothing taken mid-move is ever used.
struct Inputs {
    uint32_t now_ms = 0;           // free-running; wraps
    bool self_test_ok = true;      // read in SELF-TEST only
    bool bypass = false;           // §8B.4d key: the permissive is held up, so nothing may move
    bool carrier = false;          // a steady count above threshold (§6A.10)
    bool have_measurement = false;
    Measurement m;
    Setting position;              // the elements now, from the encoders through their calibration curves
    uint32_t move_done = 0;        // the move_id of the last move that has stopped, reached or not
    bool encoder_mismatch = false; // with move_done: encoders disagree with the steps commanded (§8B.3)
    bool limit_hit = false;        // any limit switch open
    bool over_temp = false;        // with hysteresis applied
    bool swr_trip = false;         // the over-SWR term of the permissive is down
    bool tune_request = false;     // manual, from either end
    bool ack = false;              // either end
    bool local_clear = false;      // at the box (§8B.4f)
    // The RF path (§6B.2). Only TUNE, confirmed and not changing, puts the network in circuit; in AUX
    // and CAL nothing tunes, and an over-SWR trip is a fault as it is once MATCHED.
    bool tune_path = true;
    bool relay_mismatch = false;   // K1/K2 failed their coil-current or RF check
    // Manual override (§7.5): one move to jog_target, taken only in IDLE, under the same PTT rules as a
    // tune's moves.
    bool jog = false;
    Setting jog_target;
};

// What the Teensy layer carries out. A new move_id starts one coordinated move to target (§8B.3);
// motion_enable gates the steppers, and a move in progress stops when it falls.
struct Outputs {
    State state = State::SelfTest;
    bool mcu_permit = false;       // the MCU's vote in the hardware permissive (§7.4)
    uint32_t move_id = 0;
    Setting target;
    bool motion_enable = false;
    bool blower_full = false;
    Fault fault = Fault::Count;    // the last fault raised, for the report
    int attempt = 0;
};

struct Prior {
    cplx z_load;                   // at the tuner, de-embedded
    Setting at;
};

class Tuner {
public:
    explicit Tuner(const Config& c, const FaultRecord& restored = {});
    Outputs step(const Inputs& in);

    State state() const { return state_; }
    FaultPolicy& faults() { return faults_; }
    const FaultPolicy& faults() const { return faults_; }
    // The priors (§6A.7 option 2, §7.6), one per profile segment (freq.hpp): the load at the end of the
    // last good tune there and the setting that matched it. The storage layer saves them and seeds them
    // at first boot from the NEC model (seed.hpp) until tunes replace them.
    void set_prior(int segment, const Prior& p);
    bool prior(int segment, Prior& p) const;
    cplx load() const { return last_load_; }   // what the last SOLVE worked from, for the tuning monitor

private:
    void enter(State s);
    void fault(Fault f);
    void begin_tune(const Inputs& in);
    bool run_move(const Inputs& in);
    cplx load_estimate(const Measurement& m, int sign, const Setting& at) const;
    bool prior_near(double mhz, Prior& p) const;
    int prior_sign(const Measurement& m, const Setting& at, const Prior& p);
    void start_probe();
    void note_best(const Measurement& m, const Setting& at);
    int resolve_sign(const Measurement& m0, const Setting& p0, const Measurement& m1, const Setting& p1) const;

    Config cfg_;
    FaultPolicy faults_;
    State state_ = State::SelfTest;
    Outputs out_;
    Measurement m_;                // the measurement being acted on
    Setting at_;                   // where the elements were when it was taken
    Measurement best_m_;           // the best reading this tune, and where
    Setting best_at_;
    int sign_ = +1;                // the phase sign chosen for m_
    cplx last_load_;               // the load the last SOLVE used
    int attempts_ = 0;
    int coarse_ = 0;
    double solved_mhz_ = 0;
    bool solved_ = false;
    bool pending_request_ = false;
    bool prior_used_ = false;      // the prior has chosen a sign once this tune; measurements decide after
    bool armed_ = false;           // IDLE has seen the carrier absent since it was entered
    bool jogging_ = false;         // the move in progress is a manual one
    bool probed_ = false;          // PROBE: the C2 step is done, waiting for its reading
    bool move_pending_ = false;    // a move has been asked for and has not finished
    bool move_issued_ = false;     // ...and has gone out to the motion layer
    Setting move_target_;
    uint32_t move_started_ms_ = 0;
    bool permit_up_ = false;       // the vote as last output
    uint32_t permit_down_ms_ = 0;  // when it last went down
    bool limit_was_hit_ = false;
    Prior prior_[kSegments];
    bool prior_ok_[kSegments] = {};
};

}  // namespace tuner
