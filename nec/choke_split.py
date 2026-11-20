#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Option B screening (design log §6, choke loss): a #61 ferrite section for the low bands.

For each band edge: the deck's common-mode voltage (≈ half the differential output voltage for a
balanced feeder, from cap_demand's Z_tuner at 1500 W), the ferrite section's impedance from
Fair-Rite's complex permeability (data/61-Material-Fair-Rite.csv) with a lumped winding capacitance,
the current and dissipation if the ferrite section alone held the full V_cm (worst case), the peak
flux per core, and the core loss from Fair-Rite's Pv(Bpk) fits as a cross-check. Plus the coax
length the section adds (differential loss is length-driven).

  python3 choke_split.py [N_TURNS] [N_CORES] [C_WINDING_pF]
"""
import csv, cmath, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cap_demand as C

HERE = os.path.dirname(os.path.abspath(__file__))
MU = [(float(r[0]), float(r[1]), float(r[2]))
      for r in list(csv.reader(open(os.path.join(HERE, "data", "61-Material-Fair-Rite.csv"), encoding="latin-1")))[2:]
      if r and r[0].strip()]
# FT-240-61 (Fair-Rite 5961003801): Ae 1.58 cm^2, le 14.4 cm, Ve 22.8 cm^3; 61.0 x 35.55 x 12.7 mm
AE, LE, VE, HT, OD, ID = 1.58e-4, 0.144, 22.8, 12.7, 61.0, 35.55
PV = {2: (0.1035, 2.6545), 5: (0.3018, 2.7423), 7: (0.4589, 2.7988), 10: (2.0960, 2.5473),
      15: (4.6529, 2.6294), 20: (17.4360, 2.3241)}          # Pv mW/cm^3 = a * Bpk(mT)^b
MU0 = 4e-7 * math.pi


def mu(f):
    return min(MU, key=lambda r: abs(r[0] - f))[1:]


def pv(fmhz, b_mt):
    k = min(PV, key=lambda x: abs(x - fmhz))
    a, e = PV[k]
    return a * b_mt ** e


def section(f, n, k, cw):
    m1, m2 = mu(f)
    w = 2 * math.pi * f
    zl = 1j * w * MU0 * (m1 - 1j * m2) * n * n * k * AE / LE      # = R + jX
    zc = 1 / (1j * w * cw)
    return zl * zc / (zl + zc)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    cw = (float(sys.argv[3]) if len(sys.argv) > 3 else 3.0) * 1e-12
    turn_len = 2 * k * HT + (OD - ID) + 2 * 6.0          # mm per turn, coax around the stack
    print(f"Ferrite section: {n} turns through {k} x FT-240-61, winding C {cw * 1e12:.0f} pF; "
          f"coax {n * turn_len / 304.8:.1f} ft")
    print(f"{'band':5} {'MHz':>6} {'|Zt|':>6} {'Vcm':>6} | {'|Zf|':>7} {'Rf':>7} | {'P(Vcm all on ferrite)':>21} {'Bpk mT':>7} {'core-loss W':>11}")
    for band, f, ZL in C.pts:
        if f in (1.85, 1.95):
            continue
        Zt = C.zin(f, ZL, 40.0, 0.95)
        vdiff = math.sqrt(1500 / Zt.real) * abs(Zt)
        vcm = vdiff / 2
        zf = section(f * 1e6, n, k, cw)
        i = vcm / abs(zf)
        p = i * i * zf.real
        b = vcm * math.sqrt(2) / (2 * math.pi * f * 1e6 * n * k * AE) * 1e3        # mT peak, per core
        core = pv(f, b) * VE * k / 1000
        print(f"{band:5} {f:6.2f} {abs(Zt):6.0f} {vcm:6.0f} | {abs(zf):7.0f} {zf.real:7.0f} | {p:21.0f} {b:7.1f} {core:11.0f}")
