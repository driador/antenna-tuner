// The local panel (§7.5, §8B.4f): a text screen on the Nextion, driven by the two panel encoders. The
// display is only a terminal; every screen is drawn here, so the panel's behavior is tested on the host.
//
//   left knob    turn: move the cursor     push: open, or confirm
//   right knob   turn: change a value (jog) push: back
//
// Anything that changes the tuner is a request for the caller to carry out, the same way the console
// and the web UI will. A class C latch is cleared only after its detail has been scrolled through to
// the end, which is what unlocks Confirm (§8B.4f.1).
#pragma once
#include <cstdint>

#include "tuner/faults.hpp"
#include "tuner/fsm.hpp"
#include "tuner/path.hpp"

namespace tuner {

struct PanelView {                         // what the panel shows; the Teensy layer fills it every tick
    State state = State::Idle;
    Mode mode = Mode::Strict;
    Path path = Path::Tune;
    bool path_busy = false;
    double mhz = 0;
    bool carrier = false;
    double swr = 0;
    double fwd_w = -1;                     // below zero: the band's power curve is not calibrated
    Setting at;
    double tank_c = 0;
    uint16_t latched_c = 0, unacked_b = 0;
    bool over_temp = false, bypass = false;
    bool cal_valid = false;                // this band's bridge calibration
    uint8_t cal_have = 0;                  // standards taken this session: 1 load, 2 open, 4 short
    const char* note = nullptr;            // a result to show in place of the hint for a while
};

enum class PanelAction : uint8_t {
    None, Ack, ClearLocal, Tune, SetMode, SetPath, CalLoad, CalOpen, CalShort, CalSave, Jog
};

struct PanelRequest {
    PanelAction action = PanelAction::None;
    int arg = 0;                           // the mode, the path, or the jog axis
    int detents = 0;                       // jog: signed, the caller sets the step size
};

class Panel {
public:
    static constexpr int kRows = 10, kCols = 32;

    void show(const PanelView& v) { view_ = v; }   // before input and render, every tick
    void turn(int knob, int detents);
    void push(int knob);
    PanelRequest take();                   // the pending request, once
    // The screen: kRows lines of up to kCols characters, and the row to highlight (-1: none).
    void render(char rows[kRows][kCols + 1], int& highlight) const;

private:
    enum class Screen : uint8_t { Monitor, Menu, Faults, Path, Policy, Cal, Jog };
    static constexpr int kWindow = kRows - 2;   // rows between the title and the hint

    int items() const;                     // selectable lines on this screen
    bool selectable(int i) const;
    void open(Screen s);
    void request(PanelAction a, int arg = 0, int detents = 0);

    PanelView view_;
    Screen screen_ = Screen::Monitor;
    int cursor_ = 0;
    int deepest_ = 0;                      // the furthest line reached on the fault screen
    int menu_cursor_ = 0;                  // where the menu was left, to come back to
    PanelRequest req_;
};

}  // namespace tuner
