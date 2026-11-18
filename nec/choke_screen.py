#!/usr/bin/env python3
"""Physically constrained re-screen of a #61 ferrite input choke (design log §6, option B).

Candidates are RG-400 (0.195", PTFE, stranded center; RG-142B is electrically the same) wound on
stacks of Fair-Rite 5961003801 (FT-240-61) cores. The stack axis is vertical, so it stands in the
standoff space under the deck (5.5" from Rev 3.7c; it was 3.5"). Each candidate is checked for:

  fit       turns that fit the bore in one layer against the wall (exact chord), worst-case ID (-0.75 mm)
            less tape, leaving >= 7 mm between the first and last turn (they differ by the full V_cm);
            stack height with the coax arcing over each face (rise r + d/2, r = (w + d)/2, w = (OD-ID)/2)
            and worst-case core height <= standoff - 1.0" (0.5" to the shelf and to the deck). Pulled
            tighter (r ~ d) the rise drops to ~7.4 mm a face, at the cost of a sharper bend
  balance   |Z_choke| against the deck's reactance per band (§6: the choke must be the higher one); the
            deck capacitance is the §2.2 budget with its deck-to-shelf plate term rescaled to the standoff
  heat      CM core loss with the full V_cm across the choke (Z_a -> 0, the worst case), as the larger of
            small-signal mu'' and Fair-Rite large-signal Pv(B) interpolated log-log between the fits;
            plus DM coax loss at the operating power (RG-142B basis 0.367*sqrt(f) dB/100 ft, as in §6);
            choke + network loss (cap_demand, roller Q 150) against the 200 W RF-bay budget (§8)
  cost      cores at ~$11 (DigiKey $13.37 each, TME $8.85 at 20), coax at ~$2.50/ft, ~$15 hardware

  python3 choke_screen.py              summary of all candidates, then per-band detail of the picks
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cap_demand as C
import choke_split as S

IN = 25.4
D_C = 0.195 * IN                     # coax OD, mm
W_CORE = (S.OD - S.ID) / 2           # core radial width, mm
STANDOFF_H = 5.5                     # in, shelf top to deck underside (Rev 3.7c; was 3.5)
C_DECK = (7.43 * 3.5 / STANDOFF_H + 6.5 + 1.9 + 7.0) * 1e-12   # §2.2: plate 7.43 pF at 3.5", fringe, top, bodies
C_W = (2e-12, 4e-12, 6e-12)          # winding capacitance per stack: low / nominal / high
H_MAX = STANDOFF_H - 2 * 0.5         # in, 0.5" to the shelf and to the deck
PRICE_CORE, PRICE_FT, HARDWARE = 11.0, 2.50, 15.0
LEADS_FT = 0.75                      # shelf bulkhead -> chassis end, deck end -> C1
BEND_MIN = 1.0 * IN                  # RG-400 / RG-142 datasheet static minimum, ~5 x OD
BUDGET = C.BUDGET                    # 200 W RF bay
FITS = sorted(S.PV.items())          # [(MHz, (a, b))], Pv mW/cm^3 = a * Bpk(mT)^b


TOL_ID, TOL_HT, TAPE = 0.75, 0.38, 0.25   # Fair-Rite toroid tolerances (ASSUMED typical), tape per side, mm
GAP_MIN = 7.0                             # mm between the first and last turn's jackets at the bore
R_BEND = (W_CORE + D_C) / 2               # coax arcs over each face: centerline radius


def n_max():
    idd = S.ID - TOL_ID - 2 * TAPE
    step = 2 * math.asin(D_C / (idd - D_C))
    n = int(2 * math.pi / step)
    while n and (idd - D_C) / 2 * (2 * math.pi - n * step) - D_C < GAP_MIN:
        n -= 1
    return n


def turn_mm(k):
    """Coax centerline per turn: two runs along the stack plus two arcs over the faces."""
    return 2 * k * S.HT + math.pi * (W_CORE + D_C)


def height_in(k):
    return (k * (S.HT + TOL_HT) + 2 * (R_BEND + D_C / 2)) / IN


def coax_ft(n, k, stacks):
    return stacks * n * turn_mm(k) / 304.8 + LEADS_FT + (0.3 if stacks > 1 else 0)


def pv(fmhz, b_mt):
    """Large-signal core loss, mW/cm^3: log-log interpolation between Fair-Rite's fits (None above 20 MHz)."""
    if fmhz > FITS[-1][0]:
        return None
    if fmhz <= FITS[0][0]:
        a, e = FITS[0][1]
        return a * b_mt ** e
    for (f0, (a0, e0)), (f1, (a1, e1)) in zip(FITS, FITS[1:]):
        if f0 <= fmhz <= f1:
            t = math.log(fmhz / f0) / math.log(f1 / f0)
            p0, p1 = a0 * b_mt ** e0, a1 * b_mt ** e1
            return math.exp((1 - t) * math.log(p0) + t * math.log(p1))


def z_choke(fmhz, n, k, stacks, cw):
    return stacks * S.section(fmhz * 1e6, n, k, cw)


def choke_loss(fmhz, vcm, n, k, stacks, cw, p_rf):
    """(core W, coax W, B mT) for one operating point."""
    z = z_choke(fmhz, n, k, stacks, cw)
    p_ss = vcm ** 2 * (1 / z).real
    v_stack = vcm / stacks
    b = v_stack * math.sqrt(2) / (2 * math.pi * fmhz * 1e6 * n * k * S.AE) * 1e3
    p_l = pv(fmhz, b)
    core = max(p_ss, (p_l * S.VE * k * stacks / 1000) if p_l is not None else 0.0)
    alpha = 0.367 * math.sqrt(fmhz) / 100                  # dB/ft
    coax = p_rf * (1 - 10 ** (-alpha * coax_ft(n, k, stacks) / 10))
    return core, coax, b


def operating_points():
    """[(band, MHz, Z_tuner, P_op, net_loss_at_P_op)] with the §8 derating already applied."""
    c1r = next(v for key, v in C.C1_PARTS.items() if "500" in key)
    rows, _ = C.analyse(c1r, verbose=False)
    segs = C.derate(rows)
    out = []
    for band, f, Z, s in rows:
        if not s or f in (1.85, 1.95):
            continue
        if f < 2.1:
            seg = [pw for name, pw, _w in segs if name[0].isdigit()
                   and float(name.split("-")[0]) <= f <= float(name.split("-")[1])]
        else:
            seg = [pw for name, pw, _w in segs if name.startswith("all")]
        p = min([C.P] + seg)
        out.append((band, f, Z, p, s["loss150"] * p / C.P))
    return out


def vcm_at(Z, p):
    return math.sqrt(p / Z.real) * abs(Z) / 2


def screen(pts, n, k, stacks, cw):
    worst_ratio, worst_band, rows = 1e9, "", []
    for band, f, Z, p, net in pts:
        vcm = vcm_at(Z, p)
        z = z_choke(f, n, k, stacks, cw)
        xd = 1 / (2 * math.pi * f * 1e6 * C_DECK)
        core, coax, b = choke_loss(f, vcm, n, k, stacks, cw, p)
        rows.append((band, f, p, vcm, abs(z), xd, core, coax, b, net))
        if abs(z) / xd < worst_ratio:
            worst_ratio, worst_band = abs(z) / xd, f"{band} {f:.2f}"
    return worst_ratio, worst_band, rows


def derate_with_choke(f, Z, net150, n, k, stacks, cw):
    """Largest P <= 1500 W with network + choke loss <= the RF-bay budget at this point."""
    lo, hi = 0.0, C.P
    for _ in range(40):
        p = (lo + hi) / 2
        core, coax, _b = choke_loss(f, vcm_at(Z, p), n, k, stacks, cw, p)
        if net150 * p / C.P + core + coax <= BUDGET:
            lo = p
        else:
            hi = p
    return lo


def segment_derates(n, k, stacks, cw):
    """§1.7.1 segments with the choke's heat in the RF bay: [(segment, network-only W, with-choke W, binding MHz)],
    every solved point of the segment (the interpolated 1.850 / 1.950 MHz points included), as cap_demand.derate."""
    c1r = next(v for key, v in C.C1_PARTS.items() if "500" in key)
    rows, _ = C.analyse(c1r, verbose=False)
    out = []
    for name, a, b in (("1.800-1.850", 1.80, 1.85), ("1.850-1.950", 1.85, 1.95), ("1.950-2.000", 1.95, 2.00)):
        seg = [(f, Z, s["loss150"]) for _b, f, Z, s in rows if s and a <= f <= b]
        old = min(C.P, C.P * BUDGET / max(loss for _f, _Z, loss in seg))
        lim = [(derate_with_choke(f, Z, loss, n, k, stacks, cw), f) for f, Z, loss in seg]
        out.append((name, old, *min(lim)))
    return out


CANDIDATES = [  # (label, turns, cores per stack, stacks)
    ("1x3 / 15t", 15, 3, 1), ("1x4 / 15t", 15, 4, 1), ("1x5 / 14t", 14, 5, 1), ("1x5 / 15t", 15, 5, 1),
    ("1x5 / 16t", 16, 5, 1), ("1x6 / 15t", 15, 6, 1), ("1x7 / 15t", 15, 7, 1), ("1x7 / 16t", 16, 7, 1),
    ("1x8 / 15t", 15, 8, 1), ("2x3 / 14t", 14, 3, 2),
]
ADOPTED = "1x5 / 15t"                # Rev 3.7c


if __name__ == "__main__":
    pts = operating_points()
    nm = n_max()
    r_bend = (W_CORE + D_C) / 2
    print(f"FT-240-61 bore (worst case, taped) holds {nm} turns of 0.195\" coax with >= {GAP_MIN:.0f} mm first-to-last; "
          f"face bend r = {r_bend:.1f} mm = {r_bend / D_C:.1f} x OD (5 x OD guideline ~{BEND_MIN:.0f} mm)")
    print(f"Standoff {STANDOFF_H}\": stack height allowance {H_MAX:.2f} in; worst-case height " +
          ", ".join(f"{k} cores {height_in(k):.2f}" for k in range(3, 9)) +
          f"; deck {C_DECK * 1e12:.1f} pF = {1 / (2 * math.pi * 1.8e6 * C_DECK):.0f} ohm at 1.8 MHz")
    print(f"Operating power after the §8 derate: " + ", ".join(
        f"{f:.2f} MHz {p:.0f} W" for _b, f, _Z, p, _n in pts if f < 2.1))
    hdr = (f"{'candidate':10} {'cores':>5} {'ft':>5} {'$':>5} {'H in':>5} {'L uH':>5} {'SRF':>5} | "
           f"{'|Z| 1.8':>7} {'|Z| 3.5':>7} {'Z/Xdeck min':>16} | {'160m W':>6} {'80m W':>6} {'40m W':>6} "
           f"{'10m W':>6} | {'bay worst':>14} {'160m P':>11}")
    print("\n" + hdr + "\n" + "-" * len(hdr))
    for label, n, k, stacks in CANDIDATES:
        cw = C_W[1]
        L = S.mu(1e6)[0] * S.MU0 * n * n * k * S.AE / S.LE * stacks
        srf = 1 / (2 * math.pi * math.sqrt(L / stacks * cw)) / 1e6
        ratio, wb, rows = screen(pts, n, k, stacks, cw)
        z18 = next(r[4] for r in rows if r[1] == 1.80)
        z35 = next(r[4] for r in rows if r[1] == 3.50)
        heat = {}
        for band, f, p, vcm, z, xd, core, coax, b, net in rows:
            heat[band] = max(heat.get(band, 0), core + coax)
        bay = max(rows, key=lambda r: r[6] + r[7] + r[9])
        p160 = min(derate_with_choke(f, Z, net * C.P / p, n, k, stacks, cw) for _b, f, Z, p, net in pts if f < 2.1)
        cost = k * stacks * PRICE_CORE + coax_ft(n, k, stacks) * PRICE_FT + HARDWARE
        flag = "" if (n <= nm and height_in(k) <= H_MAX) else "  NO FIT"
        print(f"{label:10} {k * stacks:5d} {coax_ft(n, k, stacks):5.1f} {cost:5.0f} {height_in(k):5.2f} "
              f"{L * 1e6:5.0f} {srf:5.1f} | {z18:7.0f} {z35:7.0f} {ratio:6.2f} ({wb:>8}) | "
              f"{heat['160m']:6.0f} {heat['80m']:6.0f} {heat['40m']:6.0f} {heat['10m']:6.0f} | "
              f"{bay[6] + bay[7] + bay[9]:4.0f} W {bay[0]:>4} {bay[1]:5.2f} {p160:6.0f} W{flag}")

    picks = [c for c in CANDIDATES if c[0] in sys.argv[1:]] or [c for c in CANDIDATES if c[0] == ADOPTED]
    for label, n, k, stacks in picks:
        print(f"\n== {label}: {n} t RG-400 on {stacks} x {k} FT-240-61, {coax_ft(n, k, stacks):.1f} ft coax; "
              f"C_w {C_W[1] * 1e12:.0f} pF per stack (|Z| at 2 / 6 pF in brackets)")
        print(f"{'band':5} {'MHz':>6} {'P W':>5} {'Vcm':>5} | {'|Z| choke':>17} {'X deck':>6} | "
              f"{'B mT':>5} {'core W':>6} {'coax W':>6} {'net W':>6} {'bay W':>6}")
        for (band, f, p, vcm, z, xd, core, coax, b, net) in screen(pts, n, k, stacks, C_W[1])[2]:
            zlo = abs(z_choke(f, n, k, stacks, C_W[0]))
            zhi = abs(z_choke(f, n, k, stacks, C_W[2]))
            mark = " <" if z < xd else ""
            print(f"{band:5} {f:6.2f} {p:5.0f} {vcm:5.0f} | {z:6.0f} ({zlo:5.0f}/{zhi:5.0f}) {xd:6.0f}{mark:2}| "
                  f"{b:5.1f} {core:6.1f} {coax:6.1f} {net:6.0f} {core + coax + net:6.0f}")
        print(f"§1.7.1 160 m limits with this choke in the {BUDGET:.0f} W RF-bay budget:")
        for name, old, new, f in segment_derates(n, k, stacks, C_W[1]):
            print(f"  {name} MHz: {old:5.0f} W network only -> {new:5.0f} W (binding at {f:.3f} MHz)")
