# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Output balance on 160 / 80 m with the real antenna system's common mode (log §9 item 50, §2.2).

The input choke was rated with the whole common-mode voltage across it (Z_a -> 0). Here the
antenna system supplies Z_a: the inverted-V (apex 37.5 ft, ends 10 ft) on 40 ft of real 600 ohm
two-wire line (#12 at 6 in), dropping from the apex to the tuner 6 ft up at the entry box. At the
tuner a differential source drives the two feeder ends. Each end has its own shunt to the chassis
node, which a 6 ft bond takes to ground:
  leg 1 (deck):  the input choke's common-mode impedance (choke_screen.py) || C_deck, 20.1 pF (§2.2)
  leg 2:         3 pF plus the 0-30 pF trimming vane
The §2.2 imbalance is read straight off the two leg currents at the tuner:
  | |I1| - |I2| | / ((|I1| + |I2|) / 2)  <= 0.05
Perfect ground bounds it (lossless ground gives the lowest Z_a); Sommerfeld ground (sigma 0.005,
eps_r 13) is the realistic case. Also printed: |Z_cm|, the antenna system seen from the chassis
with both feeder conductors tied together.

    python3 cm_balance.py        # writes out/cm_balance.txt
"""
import math
import os
import re
import subprocess
import tempfile

import choke_screen as CS

NEC = os.path.expanduser("~/src/necpp/build/src/nec2++")   # static build (README)
FT = 0.3048
RAD = 0.0808 * 0.0254 / 2.0                                 # #12 AWG
CU = 5.8001e7
LEG = 85 * FT
HP, HE, HT = 37.5 * FT, 10 * FT, 6 * FT                     # apex, leg ends, tuner height
S = 6 * 0.0254                                              # 600 ohm ladder line: #12 at 6 in
YT = 40 * FT - (HP - HT)                                    # horizontal run to the tuner (40 ft feeder)
HORIZ = math.sqrt(LEG ** 2 - (HP - HE) ** 2)
GROUNDS = {"perfect": "GN 1", "real": "GN 2 0 0 0 13.0 0.005"}
FREQS = (1.8, 1.9, 2.0, 3.5, 3.75, 4.0)
TRIMS = (0, 5, 10, 15, 20, 25, 30)                          # pF of trimming vane on leg 2
CHOKES = {"1x5 / 15t (adopted)": (15, 5, 1), "1x7 / 15t": (15, 7, 1)}
CW = CS.C_W[1]                                              # nominal winding capacitance


def deck(fmhz, ground, z1, z2, mode):
    """mode 'diff': differential drive with the two leg shunts; 'cm': feeder ends tied to the chassis,
    driven at the bond's foot (the antenna system's common mode)."""
    a, b = (-S / 2, YT, HT), (S / 2, YT, HT)
    c = (0.0, YT + 0.15, HT - 0.15)                         # chassis node
    w = [
        f"GW 1 52 {-S / 2:.4f} 0 {HP:.4f} {-S / 2 - HORIZ:.4f} 0 {HE:.4f} {RAD:.6f}",    # leg 1
        f"GW 2 52 {S / 2:.4f} 0 {HP:.4f} {S / 2 + HORIZ:.4f} 0 {HE:.4f} {RAD:.6f}",      # leg 2
        f"GW 3 48 {-S / 2:.4f} 0 {HP:.4f} {-S / 2:.4f} 0 {HT:.4f} {RAD:.6f}",            # feeder A down
        f"GW 4 13 {-S / 2:.4f} 0 {HT:.4f} {-S / 2:.4f} {YT:.4f} {HT:.4f} {RAD:.6f}",     # feeder A across
        f"GW 5 48 {S / 2:.4f} 0 {HP:.4f} {S / 2:.4f} 0 {HT:.4f} {RAD:.6f}",              # feeder B down
        f"GW 6 13 {S / 2:.4f} 0 {HT:.4f} {S / 2:.4f} {YT:.4f} {HT:.4f} {RAD:.6f}",       # feeder B across
        f"GW 7 3 {a[0]:.4f} {a[1]:.4f} {a[2]:.4f} {b[0]:.4f} {b[1]:.4f} {b[2]:.4f} {RAD:.6f}",   # tuner output
        f"GW 8 1 {a[0]:.4f} {a[1]:.4f} {a[2]:.4f} {c[0]:.4f} {c[1]:.4f} {c[2]:.4f} {RAD:.6f}",   # leg 1 shunt
        f"GW 9 1 {b[0]:.4f} {b[1]:.4f} {b[2]:.4f} {c[0]:.4f} {c[1]:.4f} {c[2]:.4f} {RAD:.6f}",   # leg 2 shunt
        f"GW 10 8 {c[0]:.4f} {c[1]:.4f} {c[2]:.4f} {c[0]:.4f} {c[1]:.4f} 0 {0.002:.6f}",          # bond to ground
    ]
    ld = [f"LD 5 {t} 0 0 {CU:.4E}" for t in range(1, 8)]
    if mode == "diff":
        ld += [f"LD 4 8 1 1 {z1.real:.6E} {z1.imag:.6E}", f"LD 4 9 1 1 {z2.real:.6E} {z2.imag:.6E}"]
        ex = "EX 0 7 2 0 1.0 0.0"
    else:                                                   # both shunts shorted: the pair is one conductor
        ex = "EX 0 10 8 0 1.0 0.0"
    return "\n".join(["CM item 50 balance", "CE", *w, "GE 1", *ld, GROUNDS[ground], ex,
                      f"FR 0 1 0 0 {fmhz} 0", "XQ", "EN", ""])


def run(text):
    with tempfile.TemporaryDirectory() as d:
        i, o = os.path.join(d, "in.nec"), os.path.join(d, "out.txt")
        open(i, "w").write(text)
        subprocess.run([NEC, f"-i{i}", f"-o{o}"], capture_output=True, text=True, timeout=600)
        return open(o).read()


def currents(txt, want):
    """{(tag, seg): complex current} for the wanted segments, from the CURRENTS AND LOCATION table."""
    out = {}
    blk = txt.split("CURRENTS AND LOCATION")[-1]
    for line in blk.splitlines():
        p = line.split()
        if len(p) >= 10 and p[0].isdigit() and p[1].isdigit():
            seg, tag = int(p[0]), int(p[1])
            # SEG TAG X Y Z LENGTH REAL IMAG MAG PHASE
            if (tag, seg) in want:
                out[(tag, seg)] = complex(float(p[6]), float(p[7]))
    return out


def zin(txt):
    m = re.search(r"ANTENNA INPUT PARAMETERS(.*?)(?:\n\s*\n\s*\n|$)", txt, re.S)
    n = re.findall(r"-?\d+\.\d+E[+-]\d+", m.group(1) if m else "")
    return complex(float(n[4]), float(n[5])) if len(n) >= 8 else None


def seg_index(txt, tag, k):
    """Absolute segment number of the k-th segment (1-based) of a tag, from the geometry table."""
    segs = [int(p.split()[0]) for p in txt.splitlines()
            if len(p.split()) == 12 and p.split()[0].isdigit() and p.split()[-1] == str(tag)]
    return segs[k - 1] if segs else None


def imbalance(fmhz, ground, choke, trim_pf):
    w = 2 * math.pi * fmhz * 1e6
    n, k, st = CHOKES[choke]
    zch = CS.z_choke(fmhz, n, k, st, CW)
    z1 = 1 / (1 / zch + 1j * w * CS.C_DECK)
    z2 = 1 / (1j * w * (3e-12 + trim_pf * 1e-12))
    txt = run(deck(fmhz, ground, z1, z2, "diff"))
    sa, sb = seg_index(txt, 4, 13), seg_index(txt, 6, 13)       # feeder segments at the tuner
    cur = currents(txt, {(4, sa), (6, sb)})
    ia, ib = cur[(4, sa)], cur[(6, sb)]
    imb = abs(abs(ia) - abs(ib)) / ((abs(ia) + abs(ib)) / 2)
    cm = abs(ia + ib) / (abs(ia - ib) / 2)                        # common-mode / differential current
    return imb, cm, zch


if __name__ == "__main__":
    lines = ["Item 50: output imbalance |I1|-|I2| over the mean (spec <= 5 %), and common-mode / differential",
             "current, at the tuner end of 40 ft of 600 ohm line; trim = vane pF added to leg 2's 3 pF"]
    for ground in GROUNDS:
        lines.append(f"\n{ground} ground: antenna system common-mode impedance at the chassis (pair tied):")
        lines.append("  " + "  ".join(f"{f:5.2f} MHz {abs(zin(run(deck(f, ground, 0, 0, 'cm')))):6.0f} ohm" for f in FREQS))
        for choke in CHOKES:
            lines.append(f"  choke {choke}:")
            lines.append(f"  {'MHz':>6} {'|Z choke|':>10} " + " ".join(f"{t:>4}pF" for t in TRIMS) + "   best")
            for f in FREQS:
                res = [imbalance(f, ground, choke, t) for t in TRIMS]
                zch = res[0][2]
                best = min(range(len(TRIMS)), key=lambda i: res[i][0])
                lines.append(f"  {f:6.2f} {abs(zch):9.0f}  " + " ".join(f"{r[0] * 100:5.1f}%" for r in res)
                             + f"   {TRIMS[best]} pF: {res[best][0] * 100:.1f}% (cm/diff {res[best][1] * 100:.1f}%)")
                print(lines[-1], flush=True)
    # The vane is set once, by hand: the best single setting for 160 and 80 m together, in 1 pF steps.
    lines.append("\nOne vane setting for both bands (worst imbalance over all six frequencies):")
    for ground in GROUNDS:
        for choke in CHOKES:
            worst = {t: max(imbalance(f, ground, choke, t)[0] for f in FREQS) for t in range(0, 31)}
            t0 = min(worst, key=worst.get)
            per = "  ".join(f"{f:.2f} {imbalance(f, ground, choke, t0)[0] * 100:.1f}%" for f in FREQS)
            lines.append(f"  {ground:7} {choke:20} best {t0:2d} pF -> worst {worst[t0] * 100:.1f}%   ({per})")
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"), exist_ok=True)
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "cm_balance.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[-5:]))
