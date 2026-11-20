#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Capacitance, voltage and roller-loss demand for the T-network — design log Rev 3.7b (§5.1, §1.7,
§9 item 45). The Rev 3.6 version (pad + link, Jennings C1) is kept as cap_demand_rev36.py.

Run:  python3 cap_demand.py

Inputs
  zant_edges.json   NEC-2 feedpoint Z at 27 band edges (sweep_edges.py, nominal geometry:
                    apex 37.5 ft, ends 10 ft, 1200 segments, Sommerfeld-Norton ground)
  Feeder            600 ohm, lossless, VF 0.95, 40 ft (also swept 39-42 ft, VF 0.93-0.97)
  Network           50 ohm -- series C1 -- node -- shunt L -- series C2 -- Z_tuner
                    lossless closed form (tnet.py), swept over L; losses added afterwards
  Parts (Rev 3.7b)  C1: 15 kV class — UCSX-700-15S 25-700 pF, or CVDD-500-15S 20-500 pF
                    C2: UCSX-740-10 (in hand) 20-675 pF, no pad
                    L : single homebuilt roller, 0.20 uH to 32.4 uH installed (33.8 free air,
                        deck image loss ~4 %); no series link
  Power             1500 W into 50 ohm
  Ratings           C1 9 kV pk working (15 kV test x 0.6), C2 6 kV pk working

Selection policy
  Among all (L, C1, C2) inside the part ranges, choose the LOWEST ROLLER CURRENT (dominant loss).
  Roller loss = I_L^2 * X_L / Q, at Q = 250 (clean contact) and 150 (realistic).
  Derate (§1.7.1): continuous power that keeps roller loss at Q = 150 within a 200 W budget.
  The 1.850 and 1.950 MHz points are interpolated linearly in Z between the 1.8/1.9/2.0 edges.
"""
import json, math, cmath, os

HERE = os.path.dirname(os.path.abspath(__file__))
Z0, P, ZS = 600.0, 1500.0, 50.0
pF, uH = 1e-12, 1e-6
BUDGET = 200.0                       # W, RF-bay dissipation (§8)

C1_PARTS = {"UCSX-700-15S": (25 * pF, 700 * pF), "CVDD-500-15S": (20 * pF, 500 * pF)}
C2R = (20 * pF, 675 * pF)            # UCSX-740-10
V_C1, V_C2 = 9000.0, 6000.0          # pk working
L_MAX = 32.4 * uH


def lgrid(lmax):
    lo = 0.20 * uH
    return [lo * (lmax / lo) ** (k / 3999) for k in range(4000)]


raw = sorted(((v[0], float(f), complex(v[1], v[2]))
              for f, v in json.load(open(os.path.join(HERE, 'zant_edges.json'))).items()),
             key=lambda p: p[1])


def with_midpoints(pts):
    """Add 1.850 and 1.950 MHz (160 m segment boundaries) by linear interpolation in Z."""
    z = {f: Z for _b, f, Z in pts}
    extra = [("160m", 1.85, (z[1.8] + z[1.9]) / 2), ("160m", 1.95, (z[1.9] + z[2.0]) / 2)]
    return sorted(pts + extra, key=lambda p: p[1])


pts = with_midpoints(raw)


def zin(f, ZL, Lft, vf):
    bl = 2 * math.pi * f * 1e6 * Lft * 0.3048 / (2.998e8 * vf)
    t = cmath.tan(bl)
    return Z0 * (ZL + 1j * Z0 * t) / (Z0 + 1j * ZL * t)


def solutions(f, Z, L):
    """Both closed-form T solutions at inductance L, unconstrained in C (tnet.t_solve's math)."""
    w = 2 * math.pi * f * 1e6
    R, Xl = Z.real, Z.imag
    XL = w * L
    disc = R * (XL * XL / ZS - R)
    if R <= 0 or disc < 0:
        return
    s = math.sqrt(disc)
    for X1 in (-XL + s, -XL - s):
        d = Xl - X1
        if d <= 0:
            continue
        den = R * R + (X1 + XL) ** 2
        imZ2 = XL * (X1 * (X1 + XL) + R * R) / den
        if imZ2 <= 0:
            continue
        C2, C1 = 1 / (w * d), 1 / (w * imZ2)
        Iin, Iload = math.sqrt(P / ZS), math.sqrt(P / R)        # RMS
        IL = Iload * abs(complex(R, X1)) / XL
        yield dict(L=L, XL=XL, C1=C1, C2=C2, IL=IL,
                   VC1=math.sqrt(2) * Iin / (w * C1),             # peak
                   VC2=math.sqrt(2) * Iload / (w * C2),
                   VL=math.sqrt(2) * IL * XL,                    # peak, across the winding in use
                   loss250=IL * IL * XL / 250, loss150=IL * IL * XL / 150)


def best(f, Z, c1r, lmax=L_MAX):
    ok = [s for L in lgrid(lmax) for s in solutions(f, Z, L)
          if c1r[0] <= s['C1'] <= c1r[1] and C2R[0] <= s['C2'] <= C2R[1]]
    return min(ok, key=lambda s: s['IL']) if ok else None


def analyse(c1r, Lft=40.0, vf=0.95, lmax=L_MAX, verbose=True):
    rows, gaps = [], []
    for band, f, ZL in pts:
        Z = zin(f, ZL, Lft, vf)
        s = best(f, Z, c1r, lmax)
        if not s and f not in (1.85, 1.95):
            gaps.append(f'{band} {f:.3f}')
        rows.append((band, f, Z, s))
    if verbose:
        print(f"{'band':5} {'MHz':>6} {'Z_tuner':>17} | {'L uH':>6} {'C1 pF':>6} {'C2 pF':>6} {'I_L A':>6} "
              f"{'VC1 kV':>6} {'VC2 kV':>6} {'VL kV':>6} {'W@250':>6} {'W@150':>6}")
        for band, f, Z, s in rows:
            if not s:
                print(f'{band:5} {f:6.3f} {Z.real:7.1f}{Z.imag:+9.1f}j | UNMATCHED')
                continue
            print(f'{band:5} {f:6.3f} {Z.real:7.1f}{Z.imag:+9.1f}j | {s["L"]/uH:6.2f} {s["C1"]/pF:6.0f} '
                  f'{s["C2"]/pF:6.0f} {s["IL"]:6.1f} {s["VC1"]/1e3:6.2f} {s["VC2"]/1e3:6.2f} '
                  f'{s["VL"]/1e3:6.2f} {s["loss250"]:6.0f} {s["loss150"]:6.0f}')
    return rows, gaps


def derate(rows):
    loss = {f: s['loss150'] for _b, f, _Z, s in rows if s}
    segs = [("1.800-1.850", 1.80, 1.85), ("1.850-1.950", 1.85, 1.95), ("1.950-2.000", 1.95, 2.00)]
    out = []
    for name, a, b in segs:
        worst = max(v for f, v in loss.items() if a <= f <= b)
        out.append((name, min(P, P * BUDGET / worst), worst))
    other = max(s['loss150'] for _b, f, _Z, s in rows if s and f > 2.1)
    out.append(("all other bands", min(P, P * BUDGET / other), other))
    return out


if __name__ == '__main__':
    for name, c1r in C1_PARTS.items():
        print(f'===== C1 = {name} ({c1r[0]/pF:.0f}-{c1r[1]/pF:.0f} pF), C2 = UCSX-740-10, '
              f'roller 0.20-{L_MAX/uH:.1f} uH, no pad, no link =====')
        rows, gaps = analyse(c1r)
        ch = [r[3] for r in rows if r[3]]
        print(f'Coverage: {27 - len(gaps)}/27  gaps: {", ".join(gaps) or "none"}')
        print(f'C1 used {min(s["C1"] for s in ch)/pF:.0f}-{max(s["C1"] for s in ch)/pF:.0f} pF, '
              f'C2 used {min(s["C2"] for s in ch)/pF:.0f}-{max(s["C2"] for s in ch)/pF:.0f} pF, '
              f'L used {min(s["L"] for s in ch)/uH:.2f}-{max(s["L"] for s in ch)/uH:.2f} uH')
        vc1 = max(s["VC1"] for s in ch); vc2 = max(s["VC2"] for s in ch); vl = max(s["VL"] for s in ch)
        print(f'Max VC1 {vc1/1e3:.2f} kV pk ({V_C1/vc1:.2f}x to 9 kV), max VC2 {vc2/1e3:.2f} kV pk '
              f'({V_C2/vc2:.2f}x to 6 kV), max V_L {vl/1e3:.2f} kV pk ({vl/1e3/math.sqrt(2):.2f} kV RMS), '
              f'max I_L {max(s["IL"] for s in ch):.1f} A RMS')
        for seg, p, w in derate(rows):
            print(f'  derate {seg:16s}: {p:5.0f} W   (worst loss at Q 150, 1500 W: {w:.0f} W)')
        print('Sensitivity, coverage vs feeder length / VF:')
        for vf in (0.93, 0.95, 0.97):
            line = []
            for Lft in (39, 40, 41, 42):
                _, g = analyse(c1r, Lft, vf, verbose=False)
                line.append(f'{Lft} ft {27-len(g)}/27' + (f' ({", ".join(g)})' if g else ''))
            print(f'  VF {vf}: ' + ' | '.join(line))
        print('Sensitivity, coverage vs installed roller maximum (40 ft, VF 0.95):')
        for lm in (28.0, 30.0, 31.0, 32.4, 35.8):
            _, g = analyse(c1r, lmax=lm * uH, verbose=False)
            print(f'  L max {lm:4.1f} uH: {27-len(g)}/27' + (f'  gaps: {", ".join(g)}' if g else ''))
        print()
