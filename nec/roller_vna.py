#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Simulated VNA sweep of the homebuilt roller (design log §5.3a, §9 item 44) with nec2++.

Model: the 22-turn #4 copper helix (5.2" to wire center, 3 TPI) as straight wire segments,
16 per turn. The wheel taps the winding at turn k (always at angle 0, so the tap is a segment
end); a straight bus rod runs from the tap down to a lead below the winding, and the source sits in
that lead, between the bus rod and the winding's bottom end. Turns k..22 are the idle section,
open at the top - exactly as in the roller. Copper loss on every wire (LD 5); no proximity effect,
no contact resistance, free space (optionally a PEC plane at the deck, 1.94" below the first turn).

Port = what a VNA sees across the roller terminals (bottom end <-> bus rod) at that wheel setting.
Outputs out/roller_vna_k<k>.csv and a summary of resonances (X sign changes and R peaks).

  python3 roller_vna.py            free space
  python3 roller_vna.py --deck     PEC ground plane at the deck
"""
import math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
NEC = os.path.expanduser("~/src/necpp/build/src/nec2++")   # static build (Rev 3.7b)
IN = 0.0254
D, PITCH, TURNS, WIRE = 5.20 * IN, IN / 3, 22, 0.204 * IN
R0 = D / 2
NSEG = 16                       # segments per turn
BUS_R = 3.952 * IN              # bus rod radius from the axis (roller.py)
LEAD_Z = -0.75 * IN             # lead run below the first turn
DECK_GAP = 1.94 * IN            # deck top to first turn (TUNER-L-109)
CU = 5.8e7
F0, F1, DF = 1.0, 35.0, 0.1
OUT = os.path.join(HERE, "out")


def helix_pts(t0, t1):
    pts = []
    for i in range(int(round((t1 - t0) * NSEG)) + 1):
        a = 2 * math.pi * (t0 + i / NSEG)
        pts.append((R0 * math.cos(a), R0 * math.sin(a), PITCH * (t0 + i / NSEG)))
    return pts


def deck(k, ground):
    rad = WIRE / 2
    lines = ["CM homebuilt roller, 22 t, 5.2 in, #4 Cu, 3 TPI; wheel at turn %d" % k, "CE"]
    tag = 0
    for t0, t1 in ((0, k), (k, TURNS)):          # active, then idle (open top end)
        if t1 <= t0:
            continue
        p = helix_pts(t0, t1)
        for a, b in zip(p, p[1:]):
            tag += 1
            lines.append("GW %d 1 %.6f %.6f %.6f %.6f %.6f %.6f %.6f" % (tag, *a, *b, rad))
    zk = PITCH * k
    wires = [((R0, 0, zk), (BUS_R, 0, zk), 2),                 # wheel / fork to the bus rod
             ((BUS_R, 0, zk), (BUS_R, 0, LEAD_Z), max(3, int((zk - LEAD_Z) / 0.02))),   # bus rod
             ((BUS_R, 0, LEAD_Z), (R0, 0, LEAD_Z), 3),         # lead; source in its middle segment
             ((R0, 0, LEAD_Z), (R0, 0, 0), 2)]                 # up to the winding's bottom end
    src = None
    for a, b, n in wires:
        tag += 1
        lines.append("GW %d %d %.6f %.6f %.6f %.6f %.6f %.6f %.6f" % (tag, n, *a, *b, rad))
        if a == (BUS_R, 0, LEAD_Z):
            src = tag
    if ground:
        lines.append("GM 0 0 0 0 0 0 0 %.6f 0" % (DECK_GAP - LEAD_Z + 0.005))   # lift all above the plane
        lines.append("GE 1")
        lines.append("GN 1")
    else:
        lines.append("GE 0")
    nf = int(round((F1 - F0) / DF)) + 1
    lines += ["LD 5 0 0 0 %.4E" % CU, "EX 0 %d 2 0 1.0 0.0" % src,
              "PT -1", "FR 0 %d 0 0 %.4f %.4f" % (nf, F0, DF), "XQ", "EN"]
    return "\n".join(lines) + "\n"


def run(k, ground):
    tag = f"k{k}{'_deck' if ground else ''}"
    i, o = os.path.join(OUT, f"rv_{tag}.nec"), os.path.join(OUT, f"rv_{tag}.out")
    open(i, "w").write(deck(k, ground))
    subprocess.run([NEC, f"-i{i}", f"-o{o}"], capture_output=True, text=True, timeout=1200)
    txt = open(o).read()
    freqs = [float(x) for x in re.findall(r"FREQUENCY\s*[:=]\s*([0-9.E+-]+)\s*MHZ", txt)]
    blocks = re.findall(r"ANTENNA INPUT PARAMETERS(.*?)(?:\n\s*\n)", txt, re.S)
    rows = []
    for f, blk in zip(freqs, blocks):
        nums = re.findall(r"-?\d+\.\d+E[+-]\d+", blk)
        rows.append((f, float(nums[4]), float(nums[5])))
    with open(os.path.join(OUT, f"roller_vna_{tag}.csv"), "w") as fh:
        fh.write("MHz,R_ohm,X_ohm,L_uH,Q\n")
        for f, r, x in rows:
            w = 2 * math.pi * f * 1e6
            fh.write(f"{f:.3f},{r:.4f},{x:.4f},{x / w * 1e6:.4f},{(x / r if r > 0 else 0):.1f}\n")
    return rows


def summarize(k, rows):
    w = lambda f: 2 * math.pi * f * 1e6
    l1 = rows[0][2] / w(rows[0][0]) * 1e6
    events = []
    for (f0, r0, x0), (f1, r1, x1) in zip(rows, rows[1:]):
        if x0 > 0 >= x1:
            events.append(f"parallel resonance ~{(f0 + f1) / 2:.1f} MHz")
        if x0 < 0 <= x1:
            events.append(f"series resonance ~{(f0 + f1) / 2:.1f} MHz")
    # R spikes: local maxima more than 3x the smoothed neighbours (idle-section absorption)
    for j in range(2, len(rows) - 2):
        r = rows[j][1]
        nb = (rows[j - 2][1] + rows[j + 2][1]) / 2
        if r > 3 * nb and r > rows[j - 1][1] and r > rows[j + 1][1]:
            events.append(f"R spike {r:.1f} ohm at {rows[j][0]:.1f} MHz")
    return l1, events


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    ground = "--deck" in sys.argv
    taps = [int(a) for a in sys.argv[1:] if a.isdigit()] or [1, 2, 3, 4, 6, 8, 12, 16, 20, 22]
    print(f"Roller sweep {F0}-{F1} MHz, {'PEC deck plane' if ground else 'free space'}")
    for k in taps:
        rows = run(k, ground)
        l1, ev = summarize(k, rows)
        q2 = next((x / r for f, r, x in rows if abs(f - 1.8) < 0.051), 0)
        print(f"  wheel at turn {k:2d}: L(1 MHz) {l1:6.2f} uH, Q(1.8 MHz, Cu only) {q2:5.0f}; "
              + ("; ".join(ev[:6]) or "no resonance below 35 MHz"))
