#!/usr/bin/env python3
"""Capacitance demand and pad necessity for the T-network (design log §5.1, §10.15 item 4).

Archived so the §5.1 figures can be regenerated. Run:  python3 cap_demand.py

Inputs
  zant_edges.json   NEC-2 feedpoint Z at 27 band edges (sweep_edges.py, nominal geometry:
                    apex 37.5 ft, ends 10 ft, 1200 segments, Sommerfeld-Norton ground)
  Feeder            600 ohm, lossless, VF 0.95, 40 ft (also swept 39-42 ft, VF 0.93-0.97)
  Network           50 ohm -- series C1 -- node -- shunt L -- series C2 -- Z_tuner
                    lossless; closed-form solution from tnet.py, swept over L
  Parts             C1: Jennings 20-675 pF
                    C2: Jennings 20-675 pF bare, or +200 pF pad (220-875 pF);
                        KP1-4 20-1000 pF for comparison
                    L : measured roller 0.20-24.40 uH, +10 uH link -> 0.20-34.40 uH
  Power             1500 W into 50 ohm

Selection policy
  Among all (L, C1, C2) that reach a match within the part ranges, choose the one with the
  LOWEST ROLLER CURRENT (dominant loss, §1.7). Ties are not an issue: I_L varies smoothly with L.
  "Demand" figures below are for that chosen solution. Pad necessity is decided separately:
  a point needs the pad only if NO solution exists with C2 inside the bare range.
"""
import json, math, cmath, os, sys


HERE = os.path.dirname(os.path.abspath(__file__))
Z0, P, ZS = 600.0, 1500.0, 50.0
pF, uH = 1e-12, 1e-6

C1R = (20 * pF, 675 * pF)
BARE = (20 * pF, 675 * pF)
PAD = 200 * pF
PADDED = (BARE[0] + PAD, BARE[1] + PAD)
KP14 = (20 * pF, 1000 * pF)
LR = (0.20 * uH, 34.40 * uH)
LGRID = [LR[0] * (LR[1] / LR[0]) ** (k / 3999) for k in range(4000)]

pts = sorted(((v[0], float(f), complex(v[1], v[2]))
              for f, v in json.load(open(os.path.join(HERE, 'zant_edges.json'))).items()),
             key=lambda p: p[1])


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
        yield dict(L=L, C1=C1, C2=C2, IL=IL,
                   VC1=math.sqrt(2) * Iin / (w * C1),             # peak
                   VC2=math.sqrt(2) * Iload / (w * C2),
                   VL=math.sqrt(2) * IL * XL)


def best(f, Z, c2r):
    ok = [s for L in LGRID for s in solutions(f, Z, L)
          if C1R[0] <= s['C1'] <= C1R[1] and c2r[0] <= s['C2'] <= c2r[1]]
    return min(ok, key=lambda s: s['IL']) if ok else None


def analyse(Lft=40.0, vf=0.95, verbose=True):
    rows, gaps_bare, gaps_kp = [], [], []
    for band, f, ZL in pts:
        Z = zin(f, ZL, Lft, vf)
        b = best(f, Z, BARE)
        p = best(f, Z, PADDED)
        k = best(f, Z, (KP14[0], KP14[1]))
        if not b:
            gaps_bare.append(f'{band} {f:.3f}')
        if not k:
            gaps_kp.append(f'{band} {f:.3f}')
        # Chosen operating solution: bare if it exists, else padded; min roller current wins
        cands = [s for s in (b, p) if s]
        ch = min(cands, key=lambda s: s['IL']) if cands else None
        rows.append((band, f, Z, b, p, ch))
    if verbose:
        print(f'Feeder {Lft:.0f} ft, VF {vf}')
        print(f"{'band':5} {'MHz':>6} {'Z_tuner':>17} | {'pad':>3} {'L uH':>6} {'C1 pF':>6} "
              f"{'C2 pF':>6} {'I_L A':>6} {'VC1 kV':>6} {'VC2 kV':>6} {'VL kV':>6}")
        for band, f, Z, b, p, ch in rows:
            if not ch:
                print(f'{band:5} {f:6.3f} {Z.real:7.1f}{Z.imag:+9.1f}j | UNMATCHED')
                continue
            pad = 'yes' if ch is p and ch is not b else 'no'
            print(f'{band:5} {f:6.3f} {Z.real:7.1f}{Z.imag:+9.1f}j | {pad:>3} {ch["L"]/uH:6.2f} '
                  f'{ch["C1"]/pF:6.0f} {ch["C2"]/pF:6.0f} {ch["IL"]:6.1f} {ch["VC1"]/1e3:6.2f} '
                  f'{ch["VC2"]/1e3:6.2f} {ch["VL"]/1e3:6.2f}')
    return rows, gaps_bare, gaps_kp


if __name__ == '__main__':
    rows, gb, gk = analyse()
    ch = [r[5] for r in rows if r[5]]
    print()
    print(f'Coverage, bare Jennings C2 : {27 - len(gb)}/27  gaps: {", ".join(gb) or "none"}')
    print(f'Coverage, KP1-4 as C2      : {27 - len(gk)}/27  gaps: {", ".join(gk) or "none"}')
    print(f'Coverage, with 200 pF pad  : {sum(1 for r in rows if r[5])}/27')
    print(f'C1 demanded  : {min(s["C1"] for s in ch)/pF:.0f} - {max(s["C1"] for s in ch)/pF:.0f} pF')
    print(f'C2 demanded  : {min(s["C2"] for s in ch)/pF:.0f} - {max(s["C2"] for s in ch)/pF:.0f} pF (total, incl. pad)')
    print(f'L demanded   : {min(s["L"] for s in ch)/uH:.2f} - {max(s["L"] for s in ch)/uH:.2f} uH')
    print(f'Max VC1 {max(s["VC1"] for s in ch)/1e3:.2f} kV pk, max VC2 {max(s["VC2"] for s in ch)/1e3:.2f} kV pk, '
          f'max I_L {max(s["IL"] for s in ch):.1f} A RMS')
    print()
    print('Sensitivity: bare-Jennings coverage vs feeder length and VF')
    for vf in (0.93, 0.95, 0.97):
        line = []
        for Lft in (39, 40, 41, 42):
            _, g, _ = analyse(Lft, vf, verbose=False)
            line.append(f'{Lft} ft {27-len(g)}/27' + (f' ({", ".join(g)})' if g else ''))
        print(f'  VF {vf}: ' + ' | '.join(line))
