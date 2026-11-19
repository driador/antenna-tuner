#include "harness.hpp"

int main() {
    int failed = 0;
    for (const t::Case& c : t::cases()) {
        const int before = t::failures();
        c.fn();
        const bool ok = t::failures() == before;
        std::printf("%s  %s\n", ok ? "pass" : "FAIL", c.name);
        failed += ok ? 0 : 1;
    }
    std::printf("%zu cases, %d failed\n", t::cases().size(), failed);
    return failed ? 1 : 0;
}
