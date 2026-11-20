#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Simulated common-mode sweep of the Guanella input choke (design log §6, §9 item 3) with nec2++.

The choke's common-mode conductor is the outside of the RG-142B shield: a 30-turn helix, 4.0" G10
former (wire center diameter 4.195"), pitch 0.195" (close-wound), axis horizontal. End A (chassis end)
is bonded to the grounded baseplate; end B (deck end) is the port — the source sits in a short lead
from end B down to the baseplate, so Z_in is what the deck sees to chassis through the choke,
including the turns' distributed capacitance to the grounded metal around them.

Grounded surroundings (Sampler chamber, TUNER-E-200): a PEC plane under the choke (the baseplate,
GN 1) at gap G_BELOW, and a wire-grid plate over it (the shelf underside) at gap G_ABOVE. Side walls
are not modeled. Wire radius is reduced to R_MODEL (0.06") so NEC's thin-wire kernel stays valid for
the close-wound turns — this underestimates turn-to-turn capacitance a little (SRF reads high).

The deck's own capacitance to chassis (§2.2, ~23 pF) is added in parallel afterwards.

  python3 choke_vna.py                 real gaps (0.05" below, 0.37" above) and comparison cases
"""
import cmath, math, os, re, subprocess, sys

NEC = os.path.expanduser("~/src/necpp/build/src/nec2++")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
IN = 0.0254
TURNS, D, PITCH = 30, 4.195 * IN, 0.195 * IN
R_MODEL = 0.06 * IN
COAX_R = 0.0975 * IN
NSEG = 16
C_DECK = 23e-12
CU = 5.8e7
F0, F1, DF = 1.0, 31.0, 0.05
BANDS = [("160m", 1.8, 2.0), ("80m", 3.5, 4.0), ("60m", 5.332, 5.405), ("40m", 7.0, 7.3), ("30m", 10.1, 10.15),
         ("20m", 14.0, 14.35), ("17m", 18.068, 18.168), ("15m", 21.0, 21.45), ("12m", 24.89, 24.99),
         ("10m", 28.0, 29.7)]


def deck(g_below, g_above, plates=True):
    rad = R_MODEL
    zc = g_below + COAX_R + D / 2                   # helix axis height above the baseplate
    L = []
    pts = []
    for i in range(TURNS * NSEG + 1):
        a = 2 * math.pi * i / NSEG
        y = PITCH * i / NSEG                        # axis along Y
        pts.append((D / 2 * math.cos(a), y, zc + D / 2 * math.sin(a)))
    tag = 0
    for a, b in zip(pts, pts[1:]):
        tag += 1
        L.append("GW %d 1 %.6f %.6f %.6f %.6f %.6f %.6f %.6f" % (tag, *a, *b, rad))
    eA, eB = pts[0], pts[-1]
    # end A to ground (bond), end B down to ground through the source segment
    for (x, y, z), src in ((eA, False), (eB, True)):
        tag += 1
        n = max(3, int(z / 0.01))
        L.append("GW %d %d %.6f %.6f %.6f %.6f %.6f %.6f %.6f" % (tag, n, x, y, z, x, y, 0.0, rad))
        if src:
            stag, sseg = tag, n
    if plates:                                       # shelf above: wire grid, 1" mesh, covers the choke
        zt = zc + D / 2 + COAX_R + g_above
        xs = [i * IN for i in range(-3, 4)]
        ys = [j * IN for j in range(-1, 8)]
        for x in xs:
            tag += 1
            L.append("GW %d %d %.6f %.6f %.6f %.6f %.6f %.6f 0.001" % (tag, len(ys) - 1, x, ys[0], zt, x, ys[-1], zt))
        for y in ys:
            tag += 1
            L.append("GW %d %d %.6f %.6f %.6f %.6f %.6f %.6f 0.001" % (tag, len(xs) - 1, xs[0], y, zt, xs[-1], y, zt))
        # shelf is grounded: two posts down to the plane at opposite corners
        for x, y in ((xs[0], ys[0]), (xs[-1], ys[-1])):
            tag += 1
            L.append("GW %d %d %.6f %.6f %.6f %.6f %.6f %.6f 0.002" % (tag, 6, x, y, zt, x, y, 0.0))
        L.append("GE 1")
        L.append("GN 1")
    else:
        L.append("GE 1")
        L.append("GN 1")
    nf = int(round((F1 - F0) / DF)) + 1
    L = ["CM Guanella choke CM model", "CE"] + L + [
        "LD 5 0 0 0 %.4E" % CU, "EX 0 %d %d 0 1.0 0.0" % (stag, sseg), "PT -1",
        "FR 0 %d 0 0 %.4f %.4f" % (nf, F0, DF), "XQ", "EN"]
    return "\n".join(L) + "\n"


def run(name, g_below, g_above, plates=True):
    i, o = os.path.join(OUT, f"ck_{name}.nec"), os.path.join(OUT, f"ck_{name}.out")
    open(i, "w").write(deck(g_below, g_above, plates))
    subprocess.run([NEC, f"-i{i}", f"-o{o}"], capture_output=True, text=True, timeout=3600)
    txt = open(o).read()
    freqs = [float(x) for x in re.findall(r"FREQUENCY\s*[:=]\s*([0-9.E+-]+)\s*MHZ", txt)]
    blocks = re.findall(r"ANTENNA INPUT PARAMETERS(.*?)(?:\n\s*\n)", txt, re.S)
    rows = []
    for f, blk in zip(freqs, blocks):
        nums = re.findall(r"-?\d+\.\d+E[+-]\d+", blk)
        rows.append((f, complex(float(nums[4]), float(nums[5]))))
    with open(os.path.join(OUT, f"choke_vna_{name}.csv"), "w") as fh:
        fh.write("MHz,R,X,ZcmR,ZcmX\n")
        for f, z in rows:
            zc = 1 / (1 / z + 1j * 2 * math.pi * f * 1e6 * C_DECK)
            fh.write(f"{f:.3f},{z.real:.2f},{z.imag:.2f},{zc.real:.2f},{zc.imag:.2f}\n")
    return rows


def report(name, rows):
    w = lambda f: 2 * math.pi * f * 1e6
    L1 = rows[0][1].imag / w(rows[0][0]) * 1e6
    res = []
    for (f0, z0), (f1, z1) in zip(rows, rows[1:]):
        if z0.imag > 0 >= z1.imag:
            res.append(f"parallel {0.5 * (f0 + f1):.2f}")
        if z0.imag < 0 <= z1.imag:
            res.append(f"series {0.5 * (f0 + f1):.2f}")
    print(f"\n== {name}: L(1 MHz) {L1:.1f} uH; resonances (MHz): {', '.join(res[:6]) or 'none'}")
    print(f"   {'band':5} {'MHz':>13}   |Z choke| min   |Z_cm| min (with 23 pF deck)   R_cm at worst")
    for b, fa, fb in BANDS:
        seg = [(f, z) for f, z in rows if fa - 0.026 <= f <= fb + 0.026]
        if not seg:
            continue
        zch = min(abs(z) for _f, z in seg)
        zcm = [(f, 1 / (1 / z + 1j * w(f) * C_DECK)) for f, z in seg]
        fm, zm = min(zcm, key=lambda t: abs(t[1]))
        print(f"   {b:5} {fa:6.3f}-{fb:6.3f}   {zch:9.0f} ohm   {abs(zm):9.0f} ohm at {fm:.2f}            {zm.real:8.0f}")


if __name__ == "__main__" and len(sys.argv) > 1:
    # single variant: choke_vna.py NAME FORMER_IN TURNS PITCH_IN GAP_BELOW GAP_ABOVE
    import builtins
    name, former, turns, pitch, gb, ga = sys.argv[1], *map(float, sys.argv[2:7])
    TURNS, D, PITCH = int(turns), (former + 2 * 0.0975) * IN, pitch * IN
    NSEG, DF = 12, 0.1
    os.makedirs(OUT, exist_ok=True)
    rows = run(name, gb, ga, True)
    print(f"\n### {name}: former {former} in, {int(turns)} turns, pitch {pitch} in, gaps {gb}/{ga} in, "
          f"coax {TURNS * math.pi * D / IN / 12:.1f} ft, winding {TURNS * pitch:.2f} in")
    report(name, rows)
    sys.exit(0)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cases = [("free", 0, 0, False, "choke alone over a distant plane (reference)"),
             ("real", 0.05, 0.37, True, "as installed: 0.05 in over the baseplate, 0.37 in under the shelf"),
             ("raised", 0.50, 0.37, True, "baseplate gap 0.50 in"),
             ]
    for name, gb, ga, pl, desc in cases:
        if name == "free":
            rows = run(name, 6.0, 0, False)
        else:
            rows = run(name, gb, ga, pl)
        print(f"\n### {desc}")
        report(name, rows)
