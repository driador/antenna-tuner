// The panel's two low-level pieces (§7.5): the Grayhill 62V15 encoders' quadrature, sampled through
// the MCP23017, and the Nextion NX4832K035's serial protocol on Serial8.
#pragma once
#include <cstddef>
#include <cstdint>

namespace tuner {

// One quadrature cycle per detent (24 a turn). A table decoder: both lines changing between two
// samples is noise, and is ignored.
class Quadrature {
public:
    explicit Quadrature(int edges_per_detent = 4) : per_(edges_per_detent) {}
    int update(bool a, bool b);    // detents since the last call, signed

private:
    uint8_t last_ = 0;
    bool started_ = false;
    int acc_ = 0, per_;
};

namespace nextion {

// Instructions are ASCII, ended by three 0xFF bytes. Each writer returns the length written, or 0
// when it does not fit.
size_t command(char* out, size_t cap, const char* instruction);
size_t set_text(char* out, size_t cap, const char* object, const char* text);   // escapes " and \ .
size_t set_number(char* out, size_t cap, const char* object, const char* attribute, long value);

// What the display sends back. Touch events (0x65) carry page, component and press (1) or release
// (0); everything else is a status code.
struct Event {
    uint8_t code = 0;
    uint8_t page = 0, component = 0, press = 0;
};

class Parser {
public:
    bool feed(uint8_t byte, Event& e);   // true when byte completes an event

private:
    uint8_t buf_[12] = {};
    size_t n_ = 0;
    int ff_ = 0;
};

}  // namespace nextion
}  // namespace tuner
