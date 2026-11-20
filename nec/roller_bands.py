#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Map each band edge onto the simulated roller (roller_vna.py output) — design log §9 item 44.

For every band edge, take the required L and roller current from tune_time.settings() (smallest-L
lowest-current solution), find the wheel position whose NEC reactance at that frequency gives that
L (interpolating between whole turns), and read the roller's R there. Reports copper-only loss at
1500 W and flags points where R sits well above the trend of the neighbouring wheel positions
(an idle-turn resonance at the operating frequency).

  python3 roller_bands.py           free-space sweep
  python3 roller_bands.py --deck    PEC-deck sweep
"""
import csv, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tune_time as T

HERE = os.path.dirname(os.path.abspath(__file__))
SUF = "_deck" if "--deck" in sys.argv else ""


def load(k):
    with open(os.path.join(HERE, "out", f"roller_vna_k{k}{SUF}.csv")) as fh:
        return {round(float(r["MHz"]), 2): (float(r["R_ohm"]), float(r["X_ohm"])) for r in csv.DictReader(fh)}


SW = {k: load(k) for k in range(1, 23)}


def at(k, f):
    """R, X at wheel turn k, frequency f (MHz), linear between the 0.1 MHz sweep points."""
    lo = math.floor(f * 10) / 10
    hi = round(lo + 0.1, 2)
    lo = round(lo, 2)
    a, b = SW[k][lo], SW[k].get(hi, SW[k][lo])
    t = (f - lo) / 0.1
    return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])


if __name__ == "__main__":
    print(f"Band edges on the simulated roller ({'PEC deck' if SUF else 'free space'}), copper loss only, 1500 W")
    print(f"{'band':5} {'MHz':>7} {'L req':>6} {'wheel':>6} {'R ohm':>7} {'Q':>6} {'I A':>5} {'Cu W':>6}  note")
    for band, f, _kr, _k1, _k2, s in T.settings():
        w = 2 * math.pi * f * 1e6
        Lreq = s['L'] * 1e6
        prev = (0, 0.0, 0.0)            # wheel at the winding's end: no inductance, no resistance
        hit = None
        for k in range(1, 23):
            R, X = at(k, f)
            L = X / w * 1e6
            if prev and prev[2] <= Lreq <= L:
                t = (Lreq - prev[2]) / (L - prev[2])
                hit = (prev[0] + t, prev[1] + t * (R - prev[1]), Lreq)
                kk = k
                break
            prev = (k, R, L)
        if not hit:
            print(f"{band:5} {f:7.3f} {Lreq:6.2f}  -- not reachable on the simulated roller (X < 0 or L too high)")
            continue
        kw, R, _ = hit
        # trend: R at the same frequency, two turns either side, scaled by L
        nb = [at(j, f) for j in (kk - 3, kk + 2, kk + 3) if 1 <= j <= 22]
        trend = [r / (x / w * 1e6) for r, x in nb if x > 0]
        ratio = (R / Lreq) / (sum(trend) / len(trend)) if trend else 1
        I = s['IL']
        note = f"R {ratio:.1f}x trend — idle-turn resonance" if ratio > 2 else ""
        print(f"{band:5} {f:7.3f} {Lreq:6.2f} {kw:6.1f} {R:7.3f} {w * Lreq * 1e-6 / R:6.0f} {I:5.1f} {I * I * R:6.1f}  {note}")
