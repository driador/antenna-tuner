#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Tuning-time estimate (design log §8B, §10.14 M-2) from the Rev 3.7b network solutions.

Element settings at every band edge come from cap_demand.py (bare network, CVDD-500-15S C1,
UCSX-740-10 C2, single 34 uH roller, lowest-roller-current policy, but with L capped so 40 m uses
the smallest workable L rather than the policy's maximum). Settings -> shaft turns:
  roller : L(k) per wheel turn from the NEC sweep (out/roller_vna_k<k>.csv at 1 MHz) if present,
           else Wheeler for a k-turn section of the 5.2" / 3 TPI helix; 22 turns full travel
  caps   : capacitance linear in shaft turns, CAP_TURNS turns full range (ASSUMED ~30, §10.14 M-1)
Motion (all three axes move together, §8B.3): trapezoidal profile, ACCEL_S to full speed.
  M-2 A : NEMA 23 direct, 1 kHz full steps -> 5.0 rev/s at the element
  M-2 B : NEMA 17 + 3:1 belt, 1 kHz           -> 1.67 rev/s at the element
Sequence overhead (§5.5, §6A, §8B): PTT drop + 30 ms RF decay, 25 ms settle + encoder verify,
measurement 0.30 s (200 ms frequency gate + bridge), refine = REFINE_STEPS x (small move + measure).
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cap_demand as C

HERE = os.path.dirname(os.path.abspath(__file__))
uH, pF = C.uH, C.pF
ROLLER_TURNS, CAP_TURNS = 22, 30.0
C1R, C2R = C.C1_PARTS["CVDD-500-15S"], C.C2R
OPTIONS = {"A (NEMA 23 direct)": 5.0, "B (NEMA 17 + 3:1)": 1000 / 600}
ACCEL_S = 0.25
T_PTT, T_SETTLE, T_MEAS = 0.030, 0.025 + 0.020, 0.30
REFINE_STEPS = 3


def roller_curve():
    """[(k, L_uH)] for k = 0..22, from the NEC sweep if available, else Wheeler."""
    pts = [(0, 0.0)]
    for k in range(1, ROLLER_TURNS + 1):
        f = os.path.join(HERE, "out", f"roller_vna_k{k}.csv")
        if os.path.exists(f):
            row = open(f).read().splitlines()[1].split(",")
            pts.append((k, float(row[3])))
        else:
            r, l = 2.6, k / 3
            pts.append((k, r * r * k * k / (9 * r + 10 * l)))
    return pts


CURVE = roller_curve()
SRC = "NEC sweep" if os.path.exists(os.path.join(HERE, "out", "roller_vna_k22.csv")) else "Wheeler"


def turns_for_L(L):
    Lu = L / uH
    for (k0, l0), (k1, l1) in zip(CURVE, CURVE[1:]):
        if l0 <= Lu <= l1:
            return k0 + (Lu - l0) / (l1 - l0) * (k1 - k0)
    return float(ROLLER_TURNS)


def cap_turns(c, rng):
    return (c - rng[0]) / (rng[1] - rng[0]) * CAP_TURNS


def move_time(d, speed):
    """Trapezoidal move of d turns at peak `speed` rev/s, ACCEL_S ramp each end."""
    d = abs(d)
    a = speed / ACCEL_S
    if d <= speed * ACCEL_S:                      # triangular: never reaches full speed
        return 2 * math.sqrt(d / a)
    return d / speed + ACCEL_S


def settings():
    """Element positions (turns) at each band edge, smallest-L solution that matches."""
    out = []
    for band, f, ZL in C.pts:
        if f in (1.85, 1.95):
            continue
        Z = C.zin(f, ZL, 40.0, 0.95)
        sols = [s for L in C.lgrid(C.L_MAX) for s in C.solutions(f, Z, L)
                if C1R[0] <= s['C1'] <= C1R[1] and C2R[0] <= s['C2'] <= C2R[1]]
        if not sols:
            continue
        # lowest current among solutions within 10 % of the smallest workable L (avoids the 40 m max-L pick)
        lmin = min(s['L'] for s in sols)
        s = min((s for s in sols if s['L'] <= 1.10 * lmin), key=lambda s: s['IL'])
        out.append((band, f, turns_for_L(s['L']), cap_turns(s['C1'], C1R), cap_turns(s['C2'], C2R), s))
    return out


def band_moves(rows, speed):
    """Worst move between any two band edges of different bands, and the typical (median)."""
    times = []
    for a in rows:
        for b in rows:
            if a[0] != b[0]:
                t = max(move_time(b[i] - a[i], speed) for i in (2, 3, 4))
                times.append((t, a, b))
    times.sort(key=lambda x: x[0])
    return times


if __name__ == "__main__":
    rows = settings()
    print(f"Roller L(turns) from: {SRC};  caps {CAP_TURNS:.0f} turns full range (ASSUMED)")
    print(f"{'band':5} {'MHz':>7} {'roller t':>8} {'C1 t':>6} {'C2 t':>6}  {'L uH':>6} {'C1 pF':>6} {'C2 pF':>6}")
    for band, f, kr, k1, k2, s in rows:
        print(f"{band:5} {f:7.3f} {kr:8.1f} {k1:6.1f} {k2:6.1f}  {s['L']/uH:6.2f} {s['C1']/pF:6.0f} {s['C2']/pF:6.0f}")
    print()
    for name, sp in OPTIONS.items():
        t = band_moves(rows, sp)
        worst, med = t[-1], t[len(t) // 2]
        full = max(move_time(ROLLER_TURNS, sp), move_time(CAP_TURNS, sp))
        refine = REFINE_STEPS * (move_time(0.3, sp) + T_MEAS)
        recall = T_PTT + worst[0] + T_SETTLE
        cold = T_PTT + T_MEAS + worst[0] + T_SETTLE + refine
        print(f"M-2 {name}: element speed {sp:.2f} rev/s, full travel {full:.1f} s")
        print(f"  band change, stored profile : typical {T_PTT + med[0] + T_SETTLE:4.1f} s, worst {recall:4.1f} s "
              f"({worst[1][0]} {worst[1][1]} -> {worst[2][0]} {worst[2][1]})")
        print(f"  band change, cold tune      : typical {T_PTT + T_MEAS + med[0] + T_SETTLE + refine:4.1f} s, "
              f"worst {cold:4.1f} s (measure + compute + move + {REFINE_STEPS}-step refine)")
        # in-band: the 0.5 % retune window; largest per-edge step inside one band
        steps = []
        for a, b in zip(rows, rows[1:]):
            if a[0] == b[0]:
                frac = 0.005 / abs(b[1] / a[1] - 1)      # fraction of the edge-to-edge move per 0.5 % step
                steps.append(max(move_time((b[i] - a[i]) * frac, sp) for i in (2, 3, 4)))
        print(f"  in-band 0.5 % QSY retune    : {T_PTT + T_MEAS + max(steps) + T_SETTLE + refine:4.1f} s worst "
              f"(move {max(steps):.2f} s + measure + refine)")
        print()
