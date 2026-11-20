# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""10 m reactance convergence (log §9 item 10).

The band-edge model (run_vee.py, 600 segments per leg) feeds the inverted-V with a delta gap on
the first segment of one leg. That source sits half a segment off the apex, and its gap is one
segment long, so both move every time the legs are refined. At 10 m the feed is near a voltage
antinode (|Z| 0.6-2.9 kohm), where the gap's capacitance dominates X. This compares that feed
with a fixed 5 cm feed wire at the apex (the source on its single segment), refining only the
legs. If X settles with the fixed gap, the old drift was the feed model, not the antenna.

    python3 conv10.py          # writes out/conv10.txt
"""
import math
import os
import re
import subprocess
import tempfile

NEC = os.path.expanduser("~/src/necpp/build/src/nec2++")   # static build (README)
FT = 0.3048
RAD = 0.0808 * 0.0254 / 2.0          # #12 AWG
EPSR, SIGMA, CU = 13.0, 0.005, 5.8001e7
LEG = 85 * FT                        # wire per leg
HP, HE = 37.5 * FT, 10 * FT          # apex and end heights (log §1)
GAP = 0.05                           # fixed feed wire, m
HORIZ = math.sqrt(LEG ** 2 - (HP - HE) ** 2)


def deck(nseg, fmhz, fixed):
    if not fixed:                     # as run_vee.py: legs from the apex, source on leg 1 segment 1
        geo = (f"GW 1 {nseg} 0 0 {HP:.6f} 0 {-HORIZ:.6f} {HE:.6f} {RAD:.8f}\n"
               f"GW 2 {nseg} 0 0 {HP:.6f} 0 {HORIZ:.6f} {HE:.6f} {RAD:.8f}\n")
        ex, ld = "EX 0 1 1 0 1.0 0.0", "LD 5 1 0 0 {cu}\nLD 5 2 0 0 {cu}"
    else:                             # 5 cm feed wire across the apex; legs start at its ends
        g = GAP / 2
        geo = (f"GW 3 1 0 {-g:.6f} {HP:.6f} 0 {g:.6f} {HP:.6f} {RAD:.8f}\n"
               f"GW 1 {nseg} 0 {-g:.6f} {HP:.6f} 0 {-g - HORIZ:.6f} {HE:.6f} {RAD:.8f}\n"
               f"GW 2 {nseg} 0 {g:.6f} {HP:.6f} 0 {g + HORIZ:.6f} {HE:.6f} {RAD:.8f}\n")
        ex, ld = "EX 0 3 1 0 1.0 0.0", "LD 5 1 0 0 {cu}\nLD 5 2 0 0 {cu}\nLD 5 3 0 0 {cu}"
    return (f"CM 170 ft inverted-V, apex 37.5 ft, ends 10 ft; {'fixed 5 cm feed' if fixed else 'leg feed'}\nCE\n"
            f"{geo}GE 1\n{ld.format(cu=f'{CU:.6E}')}\nGN 2 0 0 0 {EPSR} {SIGMA}\n{ex}\n"
            f"FR 0 1 0 0 {fmhz} 0\nXQ\nEN\n")


def run(nseg, fmhz, fixed):
    with tempfile.TemporaryDirectory() as d:
        i, o = os.path.join(d, "in.nec"), os.path.join(d, "out.txt")
        open(i, "w").write(deck(nseg, fmhz, fixed))
        subprocess.run([NEC, f"-i{i}", f"-o{o}"], capture_output=True, text=True, timeout=3600)
        txt = open(o).read()
    m = re.search(r"ANTENNA INPUT PARAMETERS(.*?)(?:\n\s*\n\s*\n|$)", txt, re.S)
    nums = re.findall(r"-?\d+\.\d+E[+-]\d+", m.group(1) if m else "")
    return (float(nums[4]), float(nums[5])) if len(nums) >= 8 else None


if __name__ == "__main__":
    lines = ["10 m feedpoint Z vs segments per leg: leg-segment feed (as run) vs fixed 5 cm feed wire",
             f"{'MHz':>6} {'seg/leg':>7} {'leg feed R':>11} {'X':>9} {'fixed feed R':>13} {'X':>9}"]
    for f in (28.0, 28.5, 29.0, 29.7):
        for n in (300, 600, 900, 1200):
            a, b = run(n, f, False), run(n, f, True)
            fmt = lambda z: (f"{z[0]:11.1f} {z[1]:+9.1f}" if z else f"{'fail':>11} {'':>9}")
            lines.append(f"{f:6.2f} {n:7d} {fmt(a)}  {fmt(b)}")
            print(lines[-1], flush=True)
    # Does the network still reach 10 m across the uncertainty? R x 0.8-1.2 and X +/-250 ohm on every
    # 10 m edge (wider than both feed models' extrapolated limits), across the cap_demand.py feeder
    # sweep (39-42 ft, VF 0.93-0.97) and both C1 parts; within the part ranges and voltage ratings.
    import json
    import cap_demand as CD
    edges = {float(k): complex(v[1], v[2]) for k, v in json.load(open(os.path.join(CD.HERE, "zant_edges.json"))).items()
             if v[0] == "10m"}
    worst = dict(VC1=0.0, VC2=0.0, IL=0.0, loss150=0.0)
    misses, cases = [], 0
    for f, Z0 in sorted(edges.items()):
        for kr in (0.8, 1.0, 1.2):
            for dx in (-250, 0, 250):
                ZL = complex(Z0.real * kr, Z0.imag + dx)
                for Lft in (39.0, 40.0, 42.0):
                    for vf in (0.93, 0.95, 0.97):
                        for part, c1r in CD.C1_PARTS.items():
                            cases += 1
                            s = CD.best(f, CD.zin(f, ZL, Lft, vf), c1r)
                            if not s or s["VC1"] > CD.V_C1 or s["VC2"] > CD.V_C2:
                                misses.append((f, kr, dx, Lft, vf, part))
                                continue
                            for k in worst:
                                worst[k] = max(worst[k], s[k])
    lines += ["", f"Reachability, 10 m: R x0.8-1.2, X +/-250 ohm, 39-42 ft, VF 0.93-0.97, both C1 parts: "
                  f"{cases - len(misses)}/{cases} matched within the part ranges and voltage ratings",
              f"  worst VC1 {worst['VC1'] / 1e3:.2f} kV pk (rating {CD.V_C1 / 1e3:.0f}), VC2 {worst['VC2'] / 1e3:.2f} kV pk "
              f"(rating {CD.V_C2 / 1e3:.0f}), roller {worst['IL']:.1f} A, loss {worst['loss150']:.0f} W at Q 150"]
    lines += [f"  MISS {f:.3f} MHz R x{kr} X {dx:+d} {Lft:.0f} ft VF {vf} {part}" for f, kr, dx, Lft, vf, part in misses[:20]]
    print("\n".join(lines[-2 - min(len(misses), 20):]))
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"), exist_ok=True)
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "conv10.txt"), "w").write("\n".join(lines) + "\n")
