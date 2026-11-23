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
//
// A converged setting is also kept in the fine recall memory (recall.hpp, §8B.3c). A tune near where one
// was found goes there first, as a coarse move, and measures: usually that is the match, with no probe.
// A preset goes there too when it can.
//
// With no prior (in practice, off the bands), a tune that would end in NO SOLUTION, its coarse moves
// spent and still nothing to solve from, first makes a cold-start search. The elements step through
// reference settings, each a match for a different likely load at the frequency (tnet.hpp), until one
// reads within trust_swr; the tune goes on from there, or from the best reading if none does. These moves
// are neither attempts nor coarse moves, and a tune that a coarse move rescues never searches.
#pragma once
#include <cstdint>

#include "tuner/bridge.hpp"
#include "tuner/faults.hpp"
#include "tuner/freq.hpp"
#include "tuner/recall.hpp"
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
    int max_search = 6;            // reference settings a cold start may step through
    double gamma_ceiling = 0.98;   // |Gamma| is taken as at most this when de-embedding
    uint32_t rf_decay_ms = 100;    // permit down this long before anything moves: the RF's 30 ms (§5.5, §7.4.5)
                                   // and the step gate's 39-67 ms (§7.4.6), as the path switch waits
    uint32_t move_timeout_ms = 15000;   // a move still running after this is a position fault
    // §8B.3b: an element moves only with the exciter's carrier inside the tune window, and the forward
    // power must stay within the tuner's rating whenever it transmits. ASSUMED until bring-up.
    double tune_max_w = 120;       // a move waits while the forward power is above this...
    uint32_t tune_hold_ms = 2000;  // ...and faults if it is still above it after this long
    double over_power_w = 1650;    // the 1500 W rating with 10 % for the detector's error
    uint32_t over_power_ms = 300;  // above it this long, in any state: a fault, and the vote goes down
    uint32_t want_ms = 30000;      // how long a TUNE with no carrier keeps asking for one (want_carrier)
    // §8D.7: the output's voltage, estimated from the load the bridge sees through the network and the
    // power going in. Over this, peak and terminal to terminal, for two gates in a row, is a fault.
    double over_volts = 5000;      // the 4,191 V envelope (§8D.1) and 20 %
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
    double fwd_w = -1;             // forward power, W; below zero: this band's power curve is not calibrated
    bool have_measurement = false;
    Measurement m;
    Setting position;              // the elements now, from the encoders through their calibration curves
    uint32_t move_done = 0;        // the move_id of the last move that has stopped, reached or not
    bool encoder_mismatch = false; // with move_done: encoders disagree with the steps commanded (§8B.3)
    bool limit_hit = false;        // any limit switch open
    bool over_temp = false;        // with hysteresis applied
    bool swr_trip = false;         // the over-SWR term of the permissive is down
    bool output_trip = false;      // the output's arc and imbalance trip holds HARD_OK down (§8D.7)
    bool tune_request = false;     // manual, from either end
    bool ack = false;              // either end
    bool local_clear = false;      // at the box (§8B.4f)
    // The RF path (§6B.2). Only TUNE, confirmed and not changing, puts the network in circuit; in AUX
    // and CAL nothing tunes, and an over-SWR trip is a fault as it is once MATCHED.
    bool tune_path = true;
    bool relay_mismatch = false;   // K1/K2 failed their coil-current or RF check
    uint16_t raise = 0;            // bit per Fault: what the built-in test found (§8B.4h), raised as if here
    // Manual override (§7.5): one move to jog_target, taken only in IDLE, under the same PTT rules as a
    // tune's moves.
    bool jog = false;
    Setting jog_target;
    // Pre-positioning (§8B.3a): the band the remote head selected while the rig still receives. Taken
    // only in IDLE with no carrier, on the TUNE path: one move to the stored setting for preset_mhz's
    // segment, so the wait at the next key-down is the refine alone. That tune measures the real
    // frequency as always, so a wrong preset costs a longer move and nothing else.
    bool preset = false;
    double preset_mhz = 0;
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
    // A TUNE asked for with no carrier: IDLE on the TUNE path, nothing blocking, waiting for the rig to
    // send one. A CAT bridge on the bench keys a low-power carrier when it sees this (§8C, one-button tune).
    bool want_carrier = false;
    bool power_hold = false;       // a move is waiting for the forward power to come into the tune window
    double v_out = -1;             // the output's estimated peak volts (§8D.7); below zero: no estimate
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
    Recall& recall() { return recall_; }        // the storage layer loads and saves it (§8B.3c)
    const Recall& recall() const { return recall_; }

private:
    void enter(State s);
    void fault(Fault f);
    void begin_tune(const Inputs& in);
    bool run_move(const Inputs& in);
    cplx load_estimate(const Measurement& m, int sign, const Setting& at) const;
    bool prior_near(double mhz, Prior& p) const;
    bool stored_setting(double mhz, Setting& s) const;
    int prior_sign(const Measurement& m, const Setting& at, const Prior& p);
    void start_probe();
    bool next_reference(const Setting& here);
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
    bool jogging_ = false;         // the move in progress is a jog or a preset: it ends in IDLE
    bool searching_ = false;       // the move in progress is to a cold start's reference setting
    Setting search_[10];           // the reference settings for this tune, computed when first needed
    int search_n_ = -1, search_i_ = 0;
    bool probed_ = false;          // PROBE: the C2 step is done, waiting for its reading
    bool move_pending_ = false;    // a move has been asked for and has not finished
    bool move_issued_ = false;     // ...and has gone out to the motion layer
    Setting move_target_;
    uint32_t move_started_ms_ = 0;
    bool permit_up_ = false;       // the vote as last output
    uint32_t permit_down_ms_ = 0;  // when it last went down
    bool limit_was_hit_ = false;
    bool power_held_ = false;      // the move waiting to go out is held for the tune window, since...
    uint32_t power_held_ms_ = 0;
    bool over_ = false, over_raised_ = false;   // forward power over the rating, since...
    uint32_t over_ms_ = 0;
    int over_v_ = 0;               // gates in a row with the output over over_volts...
    bool over_v_raised_ = false;   // ...and whether this excursion has raised its fault
    double v_out_ = -1;
    uint32_t request_ms_ = 0;      // when the last TUNE request came
    Prior prior_[kSegments];
    bool prior_ok_[kSegments] = {};
    Recall recall_;
};

}  // namespace tuner
