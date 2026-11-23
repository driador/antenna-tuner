#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""General load rating of the T network: which loads at the output terminals it matches, at what power
(design log §1.7, §1.7.1, §5, §6, §8D). The doublet's own band edges are the check (cap_demand.py,
choke_screen.py).

Run:  python3 rating.py          prints the tables and writes rating.out (about two minutes on eight cores)

Network   50 ohm -- series C1 -- node -- shunt L -- series C2 -- load R + jX, the balanced load at the
          output terminals. Lossless closed form (tnet.py, cap_demand.solutions), both branches. The family
          of settings that match a load is sampled two ways and pooled: on a log grid of L (as
          cap_demand.py) and on a log grid of C2, solving the same match condition for X_L. High-R loads
          match only inside a sliver of roller travel while C2 sweeps its whole range, and low-R loads
          the reverse, so one grid alone misses settings. A setting counts when C1, C2 and L are all in
          range. Losses are added afterwards, as in cap_demand.py. Power is what enters the 50 ohm input,
          all of it delivered to the load.
Parts     As cap_demand.py (Rev 3.7b): C1 CVDD-500-15S 20-500 pF (preferred, §9 item 45) or UCSX-700-15S
          25-700 pF (the firmware's Parts default); C2 UCSX-740-10 20-675 pF; roller 0.20-32.4 uH installed.
Limits    C1 9 kV pk and C2 6 kV pk working (§5.1); roller 18.4 A RMS (§5.3a) and 9.3 kV pk across the
          winding (§5.3a, §10.1 item 1); output 10 kV pk differential, the feedthrough rating (§8D.1).
          Key-down only: roller loss at Q = 150 plus the input choke's heat must fit the RF bay's 200 W
          (§1.7.1, §8). The choke is the adopted 1x5 / 15t at 4 pF (choke_screen.py): core loss with the
          whole V_cm = V_out / 2 across it, as §6 works it, plus its coax loss.
Watch     §8D.7's firmware over-voltage watch faults a steady carrier above 5 kV pk at the output. That is a
          protection setting, not a part rating, so it is applied separately: V_out depends only on the load
          and the power, so it cuts the key-down window exactly at |Z|^2 / R <= V^2 / 2P (8.3 kohm at
          1500 W). Tables 1 and 2 list what it changes.
Rating    A load's rating is the best setting's: the most power any in-range setting carries within every
          limit. The firmware takes the lowest roller current on a 4000-point L grid instead (tnet.cpp
          solve(), cap_demand.best()); where that carries less, Table 3 says so.
Bands     kBands (fw/core/src/freq.cpp). Each band is solved at its two edges and its center, and the worst
          of the three is the band's figure.
Grids     Scans use 1000 L + 500 C2 points; every boundary is then bisected on 4000 L + 2000 C2 points.
          SWR circles: 180 rays, each bisected on the coarse grid; the rays within 3 % of the smallest are
          refined at 2/3-degree steps on the fine grid (checked against a 360-ray fine sweep: identical).

Output (rating.out)
  CHECK 1-3  the doublet's 29 points against cap_demand_rev37b.out, the §1.7.1 160 m limits, and the most
             power at each point
  TABLE 1    per band, 1500 W key-down: the R span at X = 0 (and at PEP), and the X span at R = 10, 50,
             200 and 1000 ohm, each boundary with what stops it
  TABLE 2    per band: the largest SWR re 50 ohm matched at every phase at 1500 / 500 / 100 W key-down and
             1500 W PEP, and re 600 ohm at 1500 W; the limiting load, what limits it, and its roller loss.
             Where that loss is a large share of the power (100 W on 80-20 m, R near 0.3 ohm), the lossless
             model no longer gives a fair picture: read those figures as "more than 50:1".
  TABLE 3    (preferred C1) the most power for a grid of loads, and where the firmware's setting falls short
"""
import math
import os
import re
import sys
import textwrap
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cap_demand as CD    # noqa: E402  part ranges, working voltages, feeder, the doublet's points
import choke_screen as CS  # noqa: E402  the input choke's heat
import choke_split as SP   # noqa: E402  FT-240-61 constants

ZS, P_FULL = CD.ZS, CD.P                       # 50 ohm, 1500 W
C1_PARTS = {"CVDD-500-15S": CD.C1_PARTS["CVDD-500-15S"], "UCSX-700-15S": CD.C1_PARTS["UCSX-700-15S"]}
PREFERRED = "CVDD-500-15S"
C2R, LR = CD.C2R, (0.20e-6, CD.L_MAX)          # F, H
V_C1, V_C2 = CD.V_C1, CD.V_C2                  # V pk working (§5.1)
I_LMAX = 18.4                                  # A RMS, roller design current (§5.3a)
V_LMAX = 9.3e3                                 # V pk across the winding (§5.3a, §10.1 item 1)
V_OUT = 10e3                                   # V pk, output feedthroughs (§8D.1)
V_WATCH = 5e3                                  # V pk, the firmware's over-voltage watch on steady carriers (§8D.7)
Q = 150.0                                      # roller Q, the §1.7.1 derate basis
BUDGET = CD.BUDGET                             # W, RF bay (§1.7.1, §8)
CHOKE = next(c for c in CS.CANDIDATES if c[0] == CS.ADOPTED)[1:]   # turns, cores, stacks: 15, 5, 1
C_W = CS.C_W[1]                                # F, winding capacitance (nominal)

BANDS = [("160m", 1.800, 2.000), ("80m", 3.500, 4.000), ("60m", 5.330, 5.406), ("40m", 7.000, 7.300),
         ("30m", 10.100, 10.150), ("20m", 14.000, 14.350), ("17m", 18.068, 18.168), ("15m", 21.000, 21.450),
         ("12m", 24.890, 24.990), ("10m", 28.000, 29.700)]                       # kBands, freq.cpp
COARSE, FINE, FW = (1000, 500), (4000, 2000), (4000, 0)                         # (L points, C2 points)
CHUNK = 30000                                  # array elements per batch: small enough to stay in cache
R_COLS = (10.0, 50.0, 200.0, 1000.0)           # Table 1: X span at these R
GRID_R = (10, 25, 50, 100, 200, 500, 1000, 2000)
GRID_X = (-1000, -500, -200, -100, 0, 100, 200, 500, 1000)
SWR_CASES = [("1500 W", 1500.0, True, 50.0), ("500 W", 500.0, True, 50.0), ("100 W", 100.0, True, 50.0),
             ("1500 W PEP", 1500.0, False, 50.0), ("1500 W/600", 1500.0, True, 600.0)]   # name, W, key-down, z0
CODES = {"VC1": "C1 voltage", "VC2": "C2 voltage", "IL": "roller current", "VL": "roller voltage",
         "Vout": "output voltage", "heat-L": "200 W budget, mostly roller loss",
         "heat-ch": "200 W budget, mostly choke heat", "C1min": "C1 minimum", "C1max": "C1 maximum",
         "C2min": "C2 minimum", "C2max": "C2 maximum", "Lmin": "roller minimum", "Lmax": "roller maximum",
         "ranges": "C and L ranges together"}


# ---------------------------------------------------------------------------------------------------------
# The network, vectorized: loads [B] x settings
# ---------------------------------------------------------------------------------------------------------
def network(f, R, X, c1r, c2r=C2R, lr=LR, grid=FINE):
    """Every closed-form T solution for each load, sampled on an L grid (both branches, cap_demand.solutions'
    math) and on a C2 grid (X1 = X - 1/wC2, then (1 - R/50) XL^2 + 2 X1 XL + X1^2 + R^2 = 0 for XL).
    Arrays [B, M]: ok (a solution with C1, C2 and L in range), and at 1500 W: IL (A RMS), VC1, VC2, VL
    (V pk), loss (W at Q 150). The first 2 * nl columns are the L grid."""
    nl, nc = grid
    w = 2 * math.pi * f * 1e6
    R = np.asarray(R, float).reshape(-1, 1)
    X = np.asarray(X, float).reshape(-1, 1)
    lo, hi = max(lr[0], 1e-9), min(lr[1], 1e-2)
    lg = np.array(CD.lgrid(CD.L_MAX)) if (lr == LR and nl == 4000) else lo * (hi / lo) ** (np.arange(nl) / (nl - 1))
    xlg = np.broadcast_to((w * lg)[None, :], (len(R), nl))
    disc = R * (xlg * xlg / ZS - R)
    s = np.sqrt(np.maximum(disc, 0.0))
    x1s, xls, oks = [-xlg + s, -xlg - s], [xlg, xlg], [disc >= 0, disc >= 0]
    if nc:
        clo, chi = max(c2r[0], 1e-13), min(c2r[1], 1e-6)
        cg = clo * (chi / clo) ** (np.arange(nc) / (nc - 1))
        x1c = X - 1 / (w * cg)[None, :]
        c = x1c * x1c + R * R
        qq = R * (c / ZS - R)
        q = np.sqrt(np.maximum(qq, 0.0))
        with np.errstate(divide="ignore", invalid="ignore"):
            for xl in (c / (-x1c - q), c / (-x1c + q)):
                good = (qq >= 0) & np.isfinite(xl) & (xl > 0)
                x1s.append(x1c)
                xls.append(np.where(good, xl, 1.0))
                oks.append(good)
    X1, XL, valid = np.concatenate(x1s, 1), np.concatenate(xls, 1), np.concatenate(oks, 1)
    d = X - X1                                         # what C2 supplies
    imz2 = XL * (X1 * (X1 + XL) + R * R) / (R * R + (X1 + XL) ** 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        C1, C2 = 1 / (w * imz2), 1 / (w * d)
    L = XL / w
    ok = (valid & (d > 0) & (imz2 > 0) & (C1 >= c1r[0]) & (C1 <= c1r[1]) & (C2 >= c2r[0]) & (C2 <= c2r[1])
          & (L >= lr[0] * (1 - 1e-12)) & (L <= lr[1] * (1 + 1e-12)))
    i_load = np.sqrt(P_FULL / R)
    il = i_load * np.sqrt(R * R + X1 * X1) / XL
    return dict(ok=ok, L=L, C1=C1, C2=C2, IL=il, VC1=math.sqrt(2) * math.sqrt(P_FULL / ZS) * imz2,
                VC2=math.sqrt(2) * i_load * d, VL=math.sqrt(2) * il * XL, loss=il * il * XL / Q)


def stress_powers(net):
    """Per setting, the power at which each rating is reached (W)."""
    with np.errstate(divide="ignore"):
        return {k: P_FULL * (lim / net[k]) ** 2 for k, lim in
                (("VC1", V_C1), ("VC2", V_C2), ("IL", I_LMAX), ("VL", V_LMAX))}


def load_terms(R, X):
    """Per load: the power at which the output reaches 10 kV pk, and V_cm per sqrt(W)."""
    R, X = np.asarray(R, float), np.asarray(X, float)
    zz = R * R + X * X
    return V_OUT ** 2 * R / (2 * zz), np.sqrt(zz) / (2 * np.sqrt(R))


# ---------------------------------------------------------------------------------------------------------
# The input choke's heat, vectorized (choke_screen.choke_loss at one frequency)
# ---------------------------------------------------------------------------------------------------------
class Choke:
    """core = max(G vcm^2, K vcm^e) and coax = A P: choke_screen.choke_loss, whose large-signal Pv is a power
    law in B at any one frequency (log-log interpolation between Fair-Rite's fits)."""

    def __init__(self, f, on=True):
        n, k, st = CHOKE
        self.on = on
        self.G = (1 / CS.z_choke(f, n, k, st, C_W)).real
        cb = math.sqrt(2) / (2 * math.pi * f * 1e6 * n * k * SP.AE) * 1e3 / st      # mT per volt
        p1, p2 = CS.pv(f, cb), CS.pv(f, 10 * cb)
        self.e = math.log10(p2 / p1) if p1 else 2.0
        self.K = p1 * SP.VE * k * st / 1000 if p1 else 0.0
        self.A = CS.choke_loss(f, 1.0, n, k, st, C_W, 1.0)[1]

    def heat(self, vcm, p):
        vcm = np.asarray(vcm, float)
        if not self.on:
            return 0.0 * vcm
        return np.maximum(self.G * vcm * vcm, self.K * vcm ** self.e) + self.A * p


def choke_selfcheck():
    rng = np.random.default_rng(7)
    worst = 0.0
    for _b, lo, hi in BANDS:
        for f in (lo, hi):
            ch = Choke(f)
            for _ in range(50):
                vcm, p = 10 ** rng.uniform(0, 3.8), rng.uniform(1, 1500)
                a = sum(CS.choke_loss(f, vcm, *CHOKE, C_W, p)[:2])
                worst = max(worst, abs(float(ch.heat(vcm, p)) - a) / a)
    return worst


# ---------------------------------------------------------------------------------------------------------
# Feasibility, maximum power, and what limits it
# ---------------------------------------------------------------------------------------------------------
def _setup(f, R, X, c1r, grid, policy):
    net = network(f, R, X, c1r, grid=FW if policy == "lowest" else grid)
    pv = np.where(net["ok"], np.minimum.reduce(list(stress_powers(net).values())), -1.0)
    loss = np.where(net["ok"], net["loss"], np.inf)
    if policy == "lowest":                             # only the lowest-current setting (tnet.cpp solve())
        j = np.argmin(np.where(net["ok"], net["IL"], np.inf), axis=1)[:, None]
        keep = np.zeros_like(net["ok"])
        np.put_along_axis(keep, j, True, 1)
        pv, loss = np.where(keep, pv, -1.0), np.where(keep, loss, np.inf)
    return pv, loss


def feasible(f, R, X, c1r, cases, grid=COARSE, policy="best"):
    """cases: [(P, thermal)] -> bool [B, K]: whether the load matches at P within every limit."""
    R, X = np.atleast_1d(np.asarray(R, float)), np.atleast_1d(np.asarray(X, float))
    ch = Choke(f)
    out = np.zeros((len(R), len(cases)), bool)
    step = max(1, CHUNK // (2 * (grid[0] + grid[1])))
    for i in range(0, len(R), step):
        sl = slice(i, min(len(R), i + step))
        pv, loss = _setup(f, R[sl], X[sl], c1r, grid, policy)
        p_out, g = load_terms(R[sl], X[sl])
        for k, (P, thermal) in enumerate(cases):
            allowed = (BUDGET - ch.heat(g * math.sqrt(P), P)) * P_FULL / P if thermal else np.full(g.shape, np.inf)
            out[sl, k] = (P <= p_out) & np.any((pv >= P) & (loss <= allowed[:, None]), axis=1)
    return out


def pmax(f, R, X, c1r, policy="best", thermal=True, choke_on=True, grid=FINE, iters=24):
    """The most power (<= 1500 W) each load takes within every limit, W."""
    R, X = np.atleast_1d(np.asarray(R, float)), np.atleast_1d(np.asarray(X, float))
    ch = Choke(f, choke_on)
    out = np.zeros(len(R))
    step = max(1, CHUNK // (2 * (grid[0] + grid[1])))
    for i in range(0, len(R), step):
        sl = slice(i, min(len(R), i + step))
        pv, loss = _setup(f, R[sl], X[sl], c1r, grid, policy)
        p_out, g = load_terms(R[sl], X[sl])

        def ok(P):
            allowed = (BUDGET - ch.heat(g * np.sqrt(P), P)) * P_FULL / P if thermal else np.full(P.shape, np.inf)
            return (P <= p_out) & np.any((pv >= P[:, None]) & (loss <= allowed[:, None]), axis=1)

        full = ok(np.full(g.shape, P_FULL))
        lo, hi = np.zeros(g.shape), np.full(g.shape, P_FULL)
        for _ in range(iters):
            mid = (lo + hi) / 2
            m = ok(mid)
            lo, hi = np.where(m, mid, lo), np.where(m, hi, mid)
        out[sl] = np.where(full, P_FULL, lo)
    return out


def diagnose(f, R, X, P, c1r, thermal=True):
    """What stops the load (R, X) at P: the binding limit(s) of the best setting, or the part range(s) whose
    relaxation alone would give a setting."""
    net = network(f, [R], [X], c1r)
    ok = net["ok"][0]
    if not ok.any():                                    # each range widened by 25 % on its own
        tries = {"C1min": dict(c1r=(c1r[0] / 1.25, c1r[1])), "C1max": dict(c1r=(c1r[0], c1r[1] * 1.25)),
                 "C2min": dict(c2r=(C2R[0] / 1.25, C2R[1])), "C2max": dict(c2r=(C2R[0], C2R[1] * 1.25)),
                 "Lmin": dict(lr=(LR[0] / 1.25, LR[1])), "Lmax": dict(lr=(LR[0], LR[1] * 1.25))}
        hits = [k for k, kw in tries.items()
                if network(f, [R], [X], kw.pop("c1r", c1r), **kw, grid=(6000, 3000))["ok"].any()]
        return hits or ["ranges"]
    ch = Choke(f)
    sp = {k: v[0][ok] for k, v in stress_powers(net).items()}
    p_out, g = load_terms(R, X)
    sp["Vout"] = np.full(int(ok.sum()), float(p_out))
    loss = net["loss"][0][ok]
    if thermal:                                         # per setting: the power where the bay reaches 200 W
        lo, hi = np.zeros(loss.shape), np.full(loss.shape, 8 * P_FULL)
        for _ in range(40):
            mid = (lo + hi) / 2
            m = loss * mid / P_FULL + ch.heat(float(g) * np.sqrt(mid), mid) <= BUDGET
            lo, hi = np.where(m, mid, lo), np.where(m, hi, mid)
        sp["heat"] = lo
    names = list(sp)
    mat = np.vstack([sp[k] for k in names])
    per = mat.min(axis=0)
    b = int(np.argmax(per))
    if per[b] >= P:
        return []
    out = [k for k, v in zip(names, mat[:, b]) if v <= per[b] * 1.01]
    if "heat" in out:
        pt = sp["heat"][b]
        share_ch = float(ch.heat(float(g) * math.sqrt(pt), pt))
        out[out.index("heat")] = "heat-ch" if share_ch > loss[b] * pt / P_FULL else "heat-L"
    return out


STEPS = (0.002, 0.01, 0.03)                    # how far past a boundary to look for its reason


def diagnose_first(f, points, P, c1r, thermal=True):
    """diagnose() at each point in turn (just past a boundary, stepping out) until a reason shows."""
    for R, X in points:
        w = diagnose(f, R, X, P, c1r, thermal)
        if w:
            return w
    return ["?"]


# ---------------------------------------------------------------------------------------------------------
# Scans
# ---------------------------------------------------------------------------------------------------------
def band_freqs(lo, hi):
    return (lo, round((lo + hi) / 2, 4), hi)


def bisect(f, c1r, path, a, b, case, n=14, geometric=True):
    """a matches and b did not on the coarse scan: bisect along path(t) -> (R, X) on the fine grid. If b
    matches on the fine grid, step outward first until a point fails. Returns (a, b)."""
    ok = lambda t: feasible(f, [path(t)[0]], [path(t)[1]], c1r, [case], grid=FINE)[0, 0]   # noqa: E731
    for _ in range(30):
        if not ok(b):
            break
        a, b = b, (b * b / a if geometric else 2 * b - a)
    for _ in range(n):
        m = math.sqrt(a * b) if geometric else (a + b) / 2
        if ok(m):
            a = m
        else:
            b = m
    return a, b


def r_span(f, c1r, case=(P_FULL, True)):
    """At X = 0: [(R_lo, R_hi, why_lo, why_hi)] for each matchable run of R."""
    rs = np.geomspace(0.25, 2e5, 600)
    okv = feasible(f, rs, 0 * rs, c1r, [case])[:, 0]
    runs, i = [], 0
    while i < len(rs):
        if okv[i]:
            j = i
            while j + 1 < len(rs) and okv[j + 1]:
                j += 1
            runs.append((i, j))
            i = j + 1
        else:
            i += 1
    out = []
    path = lambda r: (r, 0.0)                                       # noqa: E731
    for i, j in runs:
        lo = rs[i] if i == 0 else bisect(f, c1r, path, rs[i], rs[i - 1], case)[0]
        hi = rs[j] if j == len(rs) - 1 else bisect(f, c1r, path, rs[j], rs[j + 1], case)[0]
        why_lo = (["(scan floor)"] if i == 0 else
                  diagnose_first(f, [(lo / (1 + k), 0.0) for k in STEPS], case[0], c1r, case[1]))
        why_hi = (["(scan top)"] if j == len(rs) - 1 else
                  diagnose_first(f, [(hi * (1 + k), 0.0) for k in STEPS], case[0], c1r, case[1]))
        out.append((lo, hi, why_lo, why_hi))
    return out


def x_span(f, R, c1r, case=(P_FULL, True)):
    """At this R: [(X_lo, X_hi, why_lo, why_hi)] for each matchable run of X (normally one), or []."""
    pos = np.geomspace(0.5, 1e5, 500)
    xs = np.concatenate([-pos[::-1], [0.0], pos])
    okv = feasible(f, R + 0 * xs, xs, c1r, [case])[:, 0]
    out, i = [], 0
    while i < len(xs):
        if not okv[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(xs) and okv[j + 1]:
            j += 1
        ends = []
        for k, step in ((i, -1), (j, 1)):
            if k + step < 0 or k + step >= len(xs):
                ends.append((xs[k], ["(scan end)"]))
                continue
            a, _b = bisect(f, c1r, lambda x: (R, x), xs[k], xs[k + step], case, n=16, geometric=False)
            pts = [(R, a + step * kk * max(abs(a), 50.0)) for kk in STEPS]
            ends.append((a, diagnose_first(f, pts, case[0], c1r, case[1])))
        out.append((ends[0][0], ends[1][0], ends[0][1], ends[1][1]))
        i = j + 1
    return out


def gamma_z(s, th, z0=ZS):
    rho = (s - 1) / (s + 1)
    gm = rho * np.exp(1j * th)
    return z0 * (1 + gm) / (1 - gm)


def ray_limits(f, c1r, case, th, a, b, z0, grid, n=12):
    """Bisect each ray th[i] between SWR a[i] (matches) and b[i] (does not, or inf for none), together."""
    a, b = a.copy(), b.copy()
    live = np.isfinite(b)
    for _ in range(n):
        if not live.any():
            break
        m = np.sqrt(a[live] * b[live])
        zm = gamma_z(m, th[live], z0)
        okm = feasible(f, zm.real, zm.imag, c1r, [case], grid=grid)[:, 0]
        a[live] = np.where(okm, m, a[live])
        b[live] = np.where(okm, b[live], m)
    return a, b


def first_fail(f, c1r, case, th, lo, hi, z0, grid, n=12):
    """For each ray, scan SWR lo..hi: (last matching, first failing) around the first failure; (hi, inf) if
    none fails, (1, lo) if lo already fails."""
    ss = np.geomspace(lo, hi, n, axis=-1)
    z = gamma_z(ss, th[:, None], z0)
    okm = feasible(f, z.real.ravel(), z.imag.ravel(), c1r, [case], grid=grid).reshape(ss.shape)
    bad = ~okm
    k = np.argmax(bad, 1)
    rows = np.arange(len(th))
    a = np.where(bad.any(1), np.where(k > 0, ss[rows, np.maximum(k - 1, 0)], 1.0), ss[:, -1])
    b = np.where(bad.any(1), ss[rows, k], np.inf)
    return a, b


def swr_limits(f, c1r, cases, z0=ZS, n_th=180, n_s=64):
    """For each (P, thermal) case: the largest SWR re z0 whose whole circle (every phase, and every smaller
    SWR on the same ray) matches; with the limiting load and what limits it there. Every ray is bisected
    on the coarse grid; the rays within 3 % of the smallest are then refined at finer angles on the fine
    grid."""
    th = np.linspace(0, 2 * math.pi, n_th, endpoint=False)
    ss = np.geomspace(1.02, 400.0, n_s)
    Z = gamma_z(ss[None, :], th[:, None], z0)
    okm = feasible(f, Z.real.ravel(), Z.imag.ravel(), c1r, cases).reshape(n_th, n_s, -1)
    out = []
    for k, (P, thermal) in enumerate(cases):
        bad = ~okm[:, :, k]
        first = np.where(bad.any(1), np.argmax(bad, 1), n_s)
        if first.min() == n_s:
            out.append((ss[-1], None, None, ["none below SWR 400"], None))
            continue
        a = np.where(first > 0, ss[np.maximum(first - 1, 0)], 1.0)
        b = np.where(first < n_s, ss[np.minimum(first, n_s - 1)], np.inf)
        a, b = ray_limits(f, c1r, (P, thermal), th, a, b, z0, COARSE, n=10)
        lim = np.where(np.isfinite(b), a, np.inf)
        pick = np.nonzero(lim <= lim.min() * 1.03)[0]
        pick = pick[np.argsort(lim[pick])][:8]
        tf = (th[pick][:, None] + np.linspace(-1, 1, 7)[None, :] * 2 * math.pi / n_th).ravel()
        r0 = np.repeat(lim[pick], 7)
        top = 1.1
        for _ in range(4):                              # widen the window if no refined ray fails inside it
            fa, fb = first_fail(f, c1r, (P, thermal), tf, np.maximum(r0 / 1.15, 1.0001), r0 * top, z0, FINE)
            low = fa <= 1.0                             # already failing at the bottom of the window: rescan
            if low.any():
                la, lb = first_fail(f, c1r, (P, thermal), tf[low], np.full(low.sum(), 1.0001),
                                    np.maximum(r0[low] / 1.15, 1.0002), z0, FINE, n=40)
                fa[low], fb[low] = la, lb
            if np.isfinite(fb).any():
                break
            top *= 2
        fa, fb = ray_limits(f, c1r, (P, thermal), tf, fa, fb, z0, FINE, n=12)
        flim = np.where(np.isfinite(fb), fa, np.inf)
        j = int(np.argmin(flim))
        s_max, t = float(flim[j]), float(tf[j])
        pts = [(gamma_z(s_max * (1 + kk), t, z0).real, gamma_z(s_max * (1 + kk), t, z0).imag) for kk in STEPS]
        zl = gamma_z(s_max, t, z0)
        net = network(f, [zl.real], [zl.imag], c1r)
        loss = float(np.min(np.where(net["ok"][0], net["loss"][0], np.inf))) / P_FULL
        out.append((s_max, t, zl, diagnose_first(f, pts, P, c1r, thermal), loss))
    return out


# ---------------------------------------------------------------------------------------------------------
# The doublet: the repo's known points
# ---------------------------------------------------------------------------------------------------------
def parse_rev37b():
    """cap_demand_rev37b.out: {(part, MHz): [L uH, C1 pF, C2 pF, I_L, VC1 kV, VC2 kV, VL kV, W@250, W@150]}."""
    out, part = {}, None
    for line in open(os.path.join(HERE, "cap_demand_rev37b.out")):
        m = re.match(r"===== C1 = (\S+)", line)
        if m:
            part = m.group(1)
            continue
        m = re.match(r"(\d+m)\s+([\d.]+)\s+\S+\s+\S+j \|\s+(.*)$", line)
        if m and part:
            out[(part, float(m.group(2)))] = [float(v) for v in m.group(3).split()]
    return out


def doublet(lines):
    ref = parse_rev37b()
    dec = [2, 0, 0, 1, 2, 2, 2, 0, 0]
    lines += ["", "=" * 110,
              "CHECK 1 - the doublet's 29 points (27 NEC band edges + 1.850 / 1.950 MHz), 40 ft of 600 ohm at VF 0.95,",
              "lowest-current setting on the 4000-point L grid, against nec/cap_demand_rev37b.out", "=" * 110]
    for part, c1r in C1_PARTS.items():
        agree, cells, worst = 0, 0, (0.0, "")
        for band, f, ZL in CD.pts:
            Z = CD.zin(f, ZL, 40.0, 0.95)
            net = network(f, [Z.real], [Z.imag], c1r, grid=FW)
            j = int(np.argmin(np.where(net["ok"][0], net["IL"][0], np.inf)))
            mine = [net["L"][0, j] * 1e6, net["C1"][0, j] * 1e12, net["C2"][0, j] * 1e12, net["IL"][0, j],
                    net["VC1"][0, j] / 1e3, net["VC2"][0, j] / 1e3, net["VL"][0, j] / 1e3,
                    net["loss"][0, j] * Q / 250, net["loss"][0, j]]
            for k, (a, b, dd) in enumerate(zip(mine, ref[(part, round(f, 3))], dec)):
                cells += 1
                d = abs(round(a, dd) - b)
                agree += d < 0.5 * 10 ** -dd
                if d > worst[0]:
                    worst = (d, f"{band} {f:.3f} column {k}: {a:.4g} vs {b:g}")
        lines.append(f"  C1 {part}: {agree}/{cells} printed values reproduced exactly"
                     + (f"; largest difference {worst[1]}" if agree < cells else ""))
    c1r = C1_PARTS[PREFERRED]
    lines += ["", "CHECK 2 - 160 m continuous limits (§1.7.1): worst point of each segment, key-down, every limit,",
              f"  C1 {PREFERRED}",
              f"  {'segment MHz':12} {'fw setting,':>13} {'fw setting,':>12} {'log':>8} "
              f"{'choke_screen':>13} {'best':>9}",
              f"  {'':12} {'network only':>13} {'with choke':>12} {'§1.7.1':>8} {'.py':>13} {'setting':>9}"]
    cs = {name: new for name, _old, new, _f in CS.segment_derates(*CHOKE, C_W)}
    for name, a, b, logv in (("1.800-1.850", 1.80, 1.85, 502), ("1.850-1.950", 1.85, 1.95, 600),
                             ("1.950-2.000", 1.95, 2.00, 882)):
        vals = {k: [] for k in ("net", "ch", "best")}
        for _band, f, ZL in CD.pts:
            if a <= f <= b:
                Z = CD.zin(f, ZL, 40.0, 0.95)
                vals["net"].append(pmax(f, Z.real, Z.imag, c1r, "lowest", choke_on=False)[0])
                vals["ch"].append(pmax(f, Z.real, Z.imag, c1r, "lowest")[0])
                vals["best"].append(pmax(f, Z.real, Z.imag, c1r, "best")[0])
        lines.append(f"  {name:12} {min(vals['net']):11.1f} W {min(vals['ch']):10.1f} W {logv:6d} W "
                     f"{cs[name]:11.1f} W {min(vals['best']):7.1f} W")
    lines += ["  The log's network-only limits (Rev 3.7b): 527 / 630 / 935 W.", "",
              f"CHECK 3 - each doublet point: the most power within every limit (W), C1 {PREFERRED}",
              f"  {'band':5} {'MHz':>6} {'Z at tuner':>18} {'SWR50':>6} | {'key-down':>8} {'(fw)':>6} | "
              f"{'PEP':>6} {'(fw)':>6} | limit"]
    for band, f, ZL in CD.pts:
        Z = CD.zin(f, ZL, 40.0, 0.95)
        gm = abs((Z - ZS) / (Z + ZS))
        p = [pmax(f, Z.real, Z.imag, c1r, pol, th)[0] for th in (True, False) for pol in ("best", "lowest")]
        why = diagnose(f, Z.real, Z.imag, P_FULL, c1r, True) if p[0] < P_FULL else []
        whyp = diagnose(f, Z.real, Z.imag, P_FULL, c1r, False) if p[2] < P_FULL else []
        note = "/".join(why) + (f"; PEP: {'/'.join(whyp)}" if whyp else "")
        lines.append(f"  {band:5} {f:6.3f} {Z.real:8.1f}{Z.imag:+9.1f}j {(1 + gm) / (1 - gm):6.1f} | {p[0]:8.0f} "
                     f"{p[1]:6.0f} | {p[2]:6.0f} {p[3]:6.0f} | {note}")
    z = CD.zin(1.8, CD.pts[0][2], 40.0, 0.95)
    net = network(1.8, [z.real], [z.imag], c1r)
    il = float(np.min(np.where(net["ok"][0], net["IL"][0], np.inf)))
    lines.append(f"  At 1.800 MHz the lowest roller current at 1500 W is {il:.2f} A, just over the {I_LMAX} A rating, "
                 f"hence {P_FULL * (I_LMAX / il) ** 2:.0f} W PEP there.")


# ---------------------------------------------------------------------------------------------------------
# Work units (run in parallel) and the report
# ---------------------------------------------------------------------------------------------------------
def freq_task(args):
    """Everything Tables 1 and 2 need at one frequency."""
    part, f = args
    c1r = C1_PARTS[part]
    out = dict(r=r_span(f, c1r), r_pep=r_span(f, c1r, (P_FULL, False)), x=[x_span(f, r, c1r) for r in R_COLS])
    res = {}
    for z0 in sorted({c[3] for c in SWR_CASES}):
        idx = [k for k, c in enumerate(SWR_CASES) if c[3] == z0]
        for k, r in zip(idx, swr_limits(f, c1r, [SWR_CASES[k][1:3] for k in idx], z0=z0)):
            res[k] = r
    out["swr"] = [res[k] for k in range(len(SWR_CASES))]
    return part, f, out


def grid_task(args):
    """Table 3 for one band: per grid load, the most power by the best and by the firmware's setting, at the
    band's tightest frequency, with the reason when under 1500 W."""
    part, band, lo, hi = args
    c1r = C1_PARTS[part]
    fs = band_freqs(lo, hi)
    RR, XX = np.meshgrid(np.array(GRID_R, float), np.array(GRID_X, float), indexing="ij")
    pb_all = np.array([pmax(f, RR.ravel(), XX.ravel(), c1r) for f in fs])
    pl_all = np.array([pmax(f, RR.ravel(), XX.ravel(), c1r, "lowest") for f in fs])
    pb, at = pb_all.min(0).reshape(RR.shape), pb_all.argmin(0).reshape(RR.shape)
    pl = pl_all.min(0).reshape(RR.shape)
    whys = {(i, j): diagnose(fs[at[i, j]], RR[i, j], XX[i, j], P_FULL, c1r)
            for i in range(len(GRID_R)) for j in range(len(GRID_X)) if pb[i, j] < P_FULL}
    return part, band, pb, pl, whys


def fmt_r(v):
    return f"{v:,.1f}" if v < 10 else f"{v:,.0f}"


def fmt_x(v):
    return f"{v:+,.0f}" if abs(v) >= 0.5 else "0"


def fmt_s(v):
    return f"{v:.1f}" if v < 10 else f"{v:.0f}"


def why(w):
    return "/".join(w) if w else "-"


def band_span(per_f):
    """[(MHz, runs)] -> (lo, hi, why_lo, why_hi, MHz_lo, MHz_hi), the band's common run, when every frequency
    has exactly one run and they overlap; else None."""
    if not all(len(r) == 1 for _f, r in per_f):
        return None
    lo = max(per_f, key=lambda p: p[1][0][0])
    hi = min(per_f, key=lambda p: p[1][0][1])
    if lo[1][0][0] >= hi[1][0][1]:
        return None
    return lo[1][0][0], hi[1][0][1], lo[1][0][2], hi[1][0][3], lo[0], hi[0]


def table1(res, part, lines):
    lines += ["", "TABLE 1 - 1500 W key-down: the R span at X = 0 (and at PEP), and the X span at four values of R",
              "(ohm). Each boundary is followed by what stops it and the frequency (MHz) where the band is tightest."]
    for band, lo, hi in BANDS:
        per = [(f, res[(part, f)]) for f in band_freqs(lo, hi)]
        rows = [("R at X = 0", [(f, o["r"]) for f, o in per], fmt_r),
                ("  PEP", [(f, o["r_pep"]) for f, o in per], fmt_r)]
        rows += [(f"X at R = {fmt_r(r)}", [(f, o["x"][k]) for f, o in per], fmt_x) for k, r in enumerate(R_COLS)]
        spans = []
        for label, per_f, fx in rows:
            sp = band_span(per_f)
            spans.append(sp)
            if sp:
                lines.append(f"  {band:5} {label:12}: {fx(sp[0]):>7} ({why(sp[2])}, {sp[4]:g}) to "
                             f"{fx(sp[1])} ({why(sp[3])}, {sp[5]:g})")
            else:
                lines.append(f"  {band:5} {label:12}: " + " | ".join(
                    f"{f:g}: " + ("; ".join(f"{fx(a)} ({why(wa)}) to {fx(b)} ({why(wb)})" for a, b, wa, wb in runs)
                                  or "none") for f, runs in per_f))
            band = ""
        k = V_WATCH ** 2 / (2 * P_FULL)               # §8D.7: |Z|^2 / R at which a steady carrier trips
        cut = []
        if spans[0] and spans[0][1] > k:
            cut.append(f"R at X = 0 to {fmt_r(k)}")
        for r, sp in zip(R_COLS, spans[2:]):
            if sp:
                xk = math.sqrt(max(k * r - r * r, 0.0))
                lo_x, hi_x = max(sp[0], -xk), min(sp[1], xk)
                if (lo_x, hi_x) != (sp[0], sp[1]):
                    cut.append(f"X at R = {fmt_r(r)}: {fmt_x(lo_x)} to {fmt_x(hi_x)}")
        lines += textwrap.wrap("; ".join(cut) if cut else "no change", 106,
                               initial_indent=f"  {'':5} §8D.7 watch : ", subsequent_indent=" " * 22)


def table2(res, part, lines):
    lines += ["", "TABLE 2 - the largest SWR that matches at every phase: re 50 ohm, key-down unless PEP; '1500 W/600'",
              "is re 600 ohm, where every phase is some length of lossless 600 ohm line. For each case: the",
              "limiting load at the band's tightest frequency, what limits it there, and the least roller loss",
              "(Q 150) of any setting there, as a share of the power.",
              f"  {'band':5} " + "".join(f"{c[0]:>12}" for c in SWR_CASES)]
    over = []
    for band, lo, hi in BANDS:
        per = [(f, res[(part, f)]["swr"]) for f in band_freqs(lo, hi)]
        worst = [min(((p[1][k], p[0]) for p in per), key=lambda v: v[0][0]) for k in range(len(SWR_CASES))]
        lines.append(f"  {band:5} " + "".join(f"{fmt_s(w[0][0]) + ':1':>12}" for w in worst))
        for (name, P, thermal, z0), ((s, _t, z, wy, loss), f) in zip(SWR_CASES, worst):
            zt = f"{z.real:.1f} {'+' if z.imag >= 0 else '-'} j{abs(z.imag):.1f}" if z is not None else "-"
            lt = f", roller loss {100 * loss:.0f} %" if loss is not None and np.isfinite(loss) else ""
            lines.append(f"  {'':5}   {name:11} {fmt_s(s):>5}:1 at {f:g} MHz, load {zt}: {why(wy)}{lt}")
            # §8D.7: on an SWR circle re z0, |Z|^2 / R peaks at z0 * SWR, so a steady carrier trips past this
            if thermal and s > V_WATCH ** 2 / (2 * P * z0):
                over.append(f"{band} {name} {fmt_s(s)}:1 -> {fmt_s(V_WATCH ** 2 / (2 * P * z0))}:1")
    lines += textwrap.wrap(
        f"§8D.7 watch (5 kV pk, steady carriers): bounds a circle at SWR V^2 / (2 P z0): "
        f"{V_WATCH ** 2 / (2 * P_FULL * 50):.0f}:1 re 50 ohm and {V_WATCH ** 2 / (2 * P_FULL * 600):.1f}:1 "
        f"re 600 ohm at 1500 W. " + ("It cuts: " + "; ".join(over) if over else "No figure above changes."),
        106, initial_indent="  ", subsequent_indent="  ")


def table3(grids, part, lines):
    lines += ["", "TABLE 3 - the most power at key-down for a grid of loads (W, at the band's tightest frequency),",
              "by the best setting, with what limits it when under 1500 W. Below each band: grid loads where the",
              "firmware's lowest-current setting (4000-point L grid) carries less."]
    short = 0
    for band, _lo, _hi in BANDS:
        _p, _b, pb, pl, whys = grids[(part, band)]
        lines += ["", f"  {band:4} R \\ X" + "".join(f"{x:>13d}" for x in GRID_X)]
        for i, r in enumerate(GRID_R):
            cells = ["1500" if pb[i, j] >= P_FULL else (f"{pb[i, j]:.0f} " if pb[i, j] > 0 else "") + why(whys[(i, j)])
                     for j in range(len(GRID_X))]
            lines.append(f"  {r:>10d}" + "".join(f"{c:>13}" for c in cells))
        fw = [(r, x, pb[i, j], pl[i, j]) for i, r in enumerate(GRID_R) for j, x in enumerate(GRID_X)
              if pl[i, j] < pb[i, j] - 1]
        short += len(fw)
        if fw:
            lines.append("        firmware's setting: " + "; ".join(
                f"{r} {'+' if x >= 0 else '-'} j{abs(x)}: {'none' if b <= 0 else f'{b:.0f} W'} (best {a:.0f} W)"
                for r, x, a, b in fw))
    lines += ["", f"  The firmware's setting carries less than the best on {short} of "
                  f"{len(GRID_R) * len(GRID_X) * len(BANDS)} grid loads."]


def main():
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time()
    lines = ["# SPDX-FileCopyrightText: 2026 Reuben A. Popp", "# SPDX-License-Identifier: CERN-OHL-W-2.0", "",
             "General load rating of the T network - nec/rating.py (design log §1.7, §1.7.1, §5, §6, §8D)", "",
             "Loads are R + jX at the balanced output terminals. 'Key-down' applies every limit, including the RF",
             "bay's 200 W (roller loss at Q 150 plus the input choke); 'PEP' drops only the 200 W budget. A band's",
             "figure is the worst of its two edges and its center (kBands, fw/core/src/freq.cpp).",
             *textwrap.wrap(
                 f"Limits: C1 {V_C1 / 1e3:.0f} kV pk, C2 {V_C2 / 1e3:.0f} kV pk, roller {I_LMAX} A RMS and "
                 f"{V_LMAX / 1e3:.1f} kV pk, output {V_OUT / 1e3:.0f} kV pk; ranges C2 {C2R[0] * 1e12:.0f}-"
                 f"{C2R[1] * 1e12:.0f} pF, roller {LR[0] * 1e6:.2f}-{LR[1] * 1e6:.1f} uH, C1 per part below.", 106),
             *textwrap.wrap("Codes: " + "; ".join(f"{k} = {v}" for k, v in CODES.items()) + ".", 106),
             f"Self-check: vectorized choke heat against choke_screen.choke_loss, worst relative difference "
             f"{choke_selfcheck():.0e}."]
    doublet(lines)
    ftasks = [(part, f) for part in C1_PARTS for _b, lo, hi in BANDS for f in band_freqs(lo, hi)]
    gtasks = [(PREFERRED, band, lo, hi) for band, lo, hi in BANDS]
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as ex:
        res, grids = {}, {}
        for n, (part, f, out) in enumerate(ex.map(freq_task, ftasks), 1):
            res[(part, f)] = out
            print(f"  {n}/{len(ftasks)} frequencies, {time.time() - t0:.0f} s", file=sys.stderr, flush=True)
        for part, band, *rest in ex.map(grid_task, gtasks):
            grids[(part, band)] = (part, band, *rest)
    for part, c1r in C1_PARTS.items():
        lines += ["", "=" * 110, f"C1 = {part} ({c1r[0] * 1e12:.0f}-{c1r[1] * 1e12:.0f} pF)"
                  + ("  - preferred, §9 item 45" if part == PREFERRED else "  - the firmware's Parts default"),
                  "=" * 110]
        table1(res, part, lines)
        table2(res, part, lines)
        if part == PREFERRED:
            table3(grids, part, lines)
    text = "\n".join(lines) + "\n"
    with open(os.path.join(HERE, "rating.out"), "w") as fh:
        fh.write(text)
    print(text)
    print(f"Run time {time.time() - t0:.0f} s.", file=sys.stderr)


if __name__ == "__main__":
    main()
