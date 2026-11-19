// A minimal test harness. The build host has no test framework, and the core must build with nothing
// but a C++17 compiler, so this is all there is: TEST registers a case, CHECK and CHECK_NEAR count
// failures, and test_main.cpp runs every case and returns non-zero if any failed.
#pragma once
#include <cmath>
#include <cstdio>
#include <vector>

namespace t {

struct Case {
    const char* name;
    void (*fn)();
};

inline std::vector<Case>& cases() {
    static std::vector<Case> v;
    return v;
}

inline int& failures() {
    static int n = 0;
    return n;
}

struct Register {
    Register(const char* name, void (*fn)()) { cases().push_back({name, fn}); }
};

inline bool near(double a, double b, double tol) { return std::fabs(a - b) <= tol; }

}  // namespace t

#define TEST(name)                                     \
    static void name();                                \
    static const t::Register name##_reg(#name, name);  \
    static void name()

#define CHECK(cond)                                                            \
    do {                                                                       \
        if (!(cond)) {                                                         \
            ++t::failures();                                                   \
            std::printf("  %s:%d: CHECK(%s)\n", __FILE__, __LINE__, #cond);   \
        }                                                                      \
    } while (0)

#define CHECK_NEAR(a, b, tol)                                                                    \
    do {                                                                                         \
        const double a_ = (a), b_ = (b), tol_ = (tol);                                           \
        if (!t::near(a_, b_, tol_)) {                                                            \
            ++t::failures();                                                                     \
            std::printf("  %s:%d: %s = %.9g, expected %.9g +/- %.3g\n", __FILE__, __LINE__, #a, \
                        a_, b_, tol_);                                                           \
        }                                                                                        \
    } while (0)
