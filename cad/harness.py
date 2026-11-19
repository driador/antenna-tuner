"""Harness routing for the 1500 W tuner enclosure (TUNER-E-212 to E-214).

Every run is a 3-D centerline through waypoints (inches, enclosure frame: X depth with the front
negative, +Y = left facing the front, Z up from the floor underside). Runs are checked as bundles
against the populated model, measured for the cut list, and projected to color-coded SVG views
that drawings_enclosure.py places on the sheets.
"""

import json
import math

from build123d import Compound, Cylinder, Pos, Sphere, Vector

import enclosure as E
import roller as R

OUT = R.OUT

# group: (label, color, stroke width mm on the sheet)
GROUPS = {
    "mains": ("120 VAC MAINS", "#d62728", 0.80),
    "dc": ("24 V / 12 V DC POWER", "#ff7f0e", 0.80),
    "logic": ("LOGIC: STEP/DIR/EN, SPI, LIM (J-A)", "#1f77b4", 0.70),
    "analog": ("SAMPLER / ANALOG (J-S, J-B)", "#2ca02c", 0.70),
    "rftank": ("RF-TANK SENSORS (J-E, SHELF FT1-4)", "#9467bd", 0.70),
    "prescaler": ("PRESCALER RG-316 (FT-P)", "#17becf", 0.70),
    "coax": ("RF COAX RG-393", "#111111", 1.10),
    "network": ("ETHERNET / POF", "#7f7f7f", 0.70),
    "fan": ("BLOWER LEAD (DE-9)", "#8c564b", 0.70),
    "bond": ("GROUND / BOND", "#bcbd22", 0.90),
}

XB0, XB1 = E.X_BULK, E.X_BULK + E.T12          # bulkhead faces
XP0, XP1 = E.X_PART, E.X_PART + E.T12          # partition faces
SERVICE = 6.0                                   # service loop on runs to the sliding cassette
# input choke (Rev 3.7c): W18 is one RG-400 piece, shelf bulkhead -> 15 t on the stack -> C1; the wound part is
# represented by the choke's own envelope, so its length is added to the cut list separately
CH_Z0 = E.Z_SH1 + E.CHOKE_SO + E.CHOKE_BASE + E.CHOKE_PAD          # winding bottom
CH_Z1 = CH_Z0 + E.CHOKE_H                                           # winding top
CH_XE = E.CHOKE_X - E.CHOKE_OD / 2 + 0.05                           # lead entry / exit at the winding gap
WOUND = {"W18": E.CHOKE_TURNS * E.CHOKE_TURN_LEN}

# (id, group, from, to, cable, conductors, cassette?, [waypoints], bundle dia, endpoint parts to ignore)
RUNS = [
    ("W1", "mains", "IEC inlet (floor A)", "PSU AC in, via CM toroid", "SJT 18/3 pigtail + inline disconnect", 3, True,
     [(-6.3, 4.6, 1.65), (-6.3, 4.6, 2.0), (-6.3, 1.4, 2.0), (-5.6, 1.4, 1.9), (-5.6, 1.25, 1.9)], 0.30,
     ("floor A body", "PSU envelope")),
    ("W2", "dc", "PSU DC out, via CM toroid", "Control board (DC-DCs)", "16 AWG pair", 2, True,
     [(-5.6, -6.6, 1.9), (-5.6, -6.6, 3.2), (-5.6, -1.0, 3.2), (-6.45, -1.0, 3.2)], 0.25,
     ("PSU envelope", "control board envelope")),
    ("W3", "dc", "PSU DC out", "FT-C / FT-D (bulkhead)", "16 AWG pair + inline disconnect", 2, True,
     [(-5.6, -1.0, 3.2), (-5.6, 1.9, 3.3), (-4.9, 1.9, 3.3)], 0.25,
     ("bulkhead C plug envelope", "bulkhead D plug envelope")),
    ("W4", "dc", "FT-C / FT-D (motor side)", "Driver board", "16 AWG pair", 2, False,
     [(-4.6, 1.9, 3.3), (-4.4, 1.3, 3.3), (-4.4, 1.3, 1.4), (-3.0, 2.3, 1.4)], 0.25,
     ("bulkhead C harness envelope", "bulkhead D harness envelope", "driver board envelope")),
    ("W5", "logic", "Control board", "J-A (bulkhead, control side)", "26-way ribbon / IDC to DB-25 plug", 25, True,
     [(-6.45, 2.6, 4.2), (-6.2, 4.0, 4.2)], 0.30,
     ("control board envelope", "bulkhead A plug envelope")),
    ("W6", "logic", "J-A (motor side)", "Driver board, 3 encoders, 6 limits", "Shielded 4-cond pairs, branched", 20, False,
     [(-4.7, 4.0, 4.2), (-3.75, 4.4, 4.4), (-3.75, 0.4, 4.4), (-2.1, 0.4, 4.4), (-1.75, -2.35, 4.3)], 0.30,
     ("bulkhead A harness envelope", "C1 encoder / limit-cam module")),
    ("W6b", "logic", "W6 branch", "C2 encoder + limit cams", "Shielded 8-cond", 7, False,
     [(-2.1, 0.4, 4.4), (-0.05, 0.4, 4.4), (-0.05, -2.35, 4.3)], 0.25, ("C2 encoder / limit-cam module",)),
    ("W6c", "logic", "W6 branch", "Roller encoder + limit cams", "Shielded 8-cond", 7, False,
     [(-3.75, 4.4, 4.4), (0.3, 4.4, 4.4), (0.3, 3.5, 4.3)], 0.25, ("ROLLER encoder / limit-cam module",)),
    ("W6d", "logic", "W6 branch", "Driver board STEP/DIR/EN", "Shielded 8-cond", 7, False,
     [(-3.75, 5.5, 4.4), (-3.75, 5.5, 1.4), (-3.0, 5.5, 1.4)], 0.25, ("driver board envelope",)),
    ("W7", "analog", "J-B (control side)", "Control board", "26-way ribbon / IDC to DB-25 plug", 25, True,
     [(-6.2, 4.0, 3.15), (-6.45, 2.8, 3.4)], 0.30, ("bulkhead B plug envelope", "control board envelope")),
    ("W8", "analog", "J-B (motor side)", "J-S (partition, motor side)", "Alpha Wire M13197, DB-25 plugs both ends", 16,
     False, [(-4.7, 4.0, 3.15), (-3.6, 6.4, 3.15), (-3.6, 6.4, 1.6), (1.5, 6.4, 1.6), (1.5, 6.4, 4.3),
             (1.65, 3.2, 4.3)], 0.33, ("bulkhead B harness envelope", "partition A plug envelope")),
    ("W9", "analog", "J-S (sampler side)", "Measurement board", "22 AWG, solder cups", 8, False,
     [(3.95, 3.2, 4.3), (3.8, 3.2, 3.75)], 0.25, ("partition A harness envelope", "measurement board envelope")),
    ("W9b", "analog", "J-S (sampler side)", "K1 / K2 coils (diodes at relay)", "22 AWG twisted pairs", 4, False,
     [(3.95, 3.2, 4.3), (6.2, 3.2, 3.2), (6.2, 2.0, 2.85)], 0.25, ("partition A harness envelope", "K1 envelope")),
    ("W9c", "analog", "J-S (sampler side)", "Cal-load thermostat (inside, on the floor at J)", "22 AWG pair", 2,
     False, [(3.95, 3.2, 4.3), (4.45, 3.2, 4.0), (4.45, 1.45, 1.4), (4.45, 1.45, 0.45)], 0.20,
     ("partition A harness envelope",)),
    ("W10", "prescaler", "Measurement board", "FT-P (partition)", "RG-316", 1, False,
     [(3.6, 1.15, 1.9), (3.2, 0.8, 1.9)], 0.20, ("measurement board envelope", "partition P harness envelope")),
    ("W10b", "prescaler", "FT-P (partition, motor side)", "FT-P (bulkhead, motor side)", "RG-316", 1, False,
     [(2.85, 0.8, 1.9), (2.6, 1.0, 2.5), (-4.4, 1.0, 2.5), (-4.6, 1.9, 2.5)], 0.20,
     ("partition P plug envelope", "bulkhead P harness envelope")),
    ("W10c", "prescaler", "FT-P (bulkhead, control side)", "Control board", "RG-316 + SMA/U.FL", 1, True,
     [(-4.95, 1.9, 2.5), (-6.3, 1.9, 2.5), (-6.45, 1.6, 2.5)], 0.20,
     ("bulkhead P plug envelope", "control board envelope")),
    ("W11", "rftank", "J-E (bulkhead, control side)", "Control board", "10-way ribbon / IDC to DE-9 plug", 9, True,
     [(-6.2, 4.0, 2.1), (-6.45, 3.0, 2.4)], 0.25, ("bulkhead E plug envelope", "control board envelope")),
    ("W12", "rftank", "J-E (motor side)", "Shelf FT1-FT4 (underside)", "22 AWG, 4 cond, shielded", 4, False,
     [(-4.7, 4.0, 2.1), (-3.8, 4.0, 2.1), (-3.8, 1.6, 2.1), (-3.8, 1.6, 0.8), (-3.8, -6.45, 0.8),
      (1.125, -6.45, 0.8), (1.125, -6.45, 4.95)], 0.25, ("bulkhead E harness envelope",)),
    ("W12b", "rftank", "Shelf FT1-FT4 (top)", "Tank thermal probe + imbalance CT; FT4 to the RF panel switch (run TBD)", "PTFE 22 AWG", 4,
     False, [(1.125, -6.45, 5.25), (1.125, -6.45, 6.2)], 0.25, ()),
    ("W13", "coax", "Coax input, SO-239 (floor G)", "Sampler / coupler (measurement board)", "RG-393", 1, False,
     [(3.55, -5.2, 1.05), (3.33, -5.2, 1.35), (3.33, 1.0, 1.35), (3.6, 1.15, 1.35)], 0.40,
     ("floor G body", "measurement board envelope")),
    ("W14", "coax", "Sampler / coupler", "K1 COM", "RG-393", 1, False,
     [(4.1, 1.6, 2.0), (5.15, 1.6, 1.6)], 0.40, ("measurement board envelope", "K1 envelope")),
    # W16 deleted Rev 3.7c: the choke left the sampler chamber, so K1 NC runs straight to adapter X (all chassis side)
    ("W15", "coax", "K1 NC", "Partition adapter X (sampler side)", "RG-393", 1, False,
     [(6.2, 0.95, 1.6), (5.48, 0.95, 2.75), (5.48, -7.3, 2.75), (3.75, -7.3, 2.75), (3.75, -6.3, 4.4)], 0.40,
     ("K1 envelope", "partition X harness envelope")),
    ("W17", "coax", "Partition adapter X (motor side)", "Shelf COAX bulkhead (underside)", "RG-393", 1, False,
     [(2.85, -6.3, 4.4), (2.55, -6.3, 4.4), (2.55, -5.9, 0.75), (-4.0, -5.9, 0.75), (-4.0, -0.85, 0.75),
      (-4.0, -0.85, 4.95)], 0.40, ("partition X plug envelope",)),
    ("W18", "coax", "Shelf COAX (top)", "C1 lower terminal",
     "RG-400, 15 t on the input choke (6); shield floats at the deck after the choke", 1, False,
     [(-4.0, -0.85, 5.3), (-4.0, -0.85, 5.85), (CH_XE, -1.0, CH_Z0 + 0.1), (CH_XE, -1.0, CH_Z1 - 0.1),
      (-3.45, -1.35, R.Z_DECK - 0.55), (-3.6, -1.5, R.Z_DECK - 0.26)], 0.20, ("cap envelope", "choke")),
    ("W19", "coax", "K1 NO", "K2 COM", "RG-393 jumper", 1, False,
     [(6.2, 3.0, 1.6), (6.2, 3.4, 1.6)], 0.40, ("K1 envelope", "K2 envelope")),
    ("W20", "coax", "K2 NC", "AUX N (floor H)", "RG-393", 1, False,
     [(5.15, 4.4, 1.2), (4.6, 4.4, 1.2), (4.6, 1.2, 1.0), (4.3, 1.2, 1.0), (4.3, 1.0, 1.0), (3.3, 1.0, 0.95),
      (3.3, -2.6, 0.95),
      (3.55, -2.6, 1.05)],
     0.40, ("K2 envelope", "floor H body")),
    ("W21", "coax", "K2 NO", "Cal load (floor J)", "RG-393", 1, False,
     [(5.15, 3.6, 1.0), (4.6, 3.6, 1.0), (4.6, 1.3, 0.9), (4.6, 1.0, 0.85)], 0.40, ("K2 envelope", "floor J body")),
    ("W22", "network", "RJ45 coupler (floor B)", "Control board (Ethernet carrier)", "Cat5e patch, 1 ft", 8, True,
     [(-6.3, 6.15, 2.5), (-6.3, 5.0, 3.9), (-6.6, 3.45, 3.9)], 0.25, ("floor B body", "control board envelope")),
    ("W23", "network", "POF (floor C)", "HFBR-1521Z on the control board", "1 mm POF", 1, True,
     [(-5.15, 4.25, 0.3), (-5.15, 4.25, 1.0), (-6.4, 3.0, 1.0), (-6.45, 3.0, 1.2)], 0.15,
     ("floor C body", "control board envelope")),
    ("W24", "fan", "Blower (exterior, left upper)", "DE-9 at the left lower panel", "3-cond in flex conduit", 3, False,
     [(3.4, 9.7, E.BLOWER["z"] - 2.0), (3.4, 8.4, E.BLOWER["z"] - 2.4), (3.4, 8.4, 3.6), (-6.0, 8.4, 3.6)], 0.35,
     ("blower", "fan entry plug envelope")),
    ("W25", "fan", "DE-9 (inside)", "Control board (12 V DC-DC, tach)", "22 AWG x 3", 3, True,
     [(-6.0, 7.3, 3.6), (-6.6, 3.4, 4.2)], 0.22, ("fan entry harness envelope", "control board envelope")),
    ("W26", "bond", "Ground stud (floor L, rear-left post)", "Arrestor baseplate (8A.2)", "1\" tinned braid", 1, False,
     [(7.3, 7.3, 0.0), (7.3, 7.3, -3.0)], 0.40, ()),
]


def length(pts):
    return sum((Vector(*b) - Vector(*a)).length for a, b in zip(pts, pts[1:]))


def bundle(pts, d):
    """Solid stand-in for a run: a cylinder per segment plus a ball at each corner."""
    parts = []
    for a, b in zip(pts, pts[1:]):
        va, vb = Vector(*a), Vector(*b)
        L = (vb - va).length
        if L < 1e-6:
            continue
        c = Cylinder(d / 2, L)
        # orient the Z-axis cylinder from va to vb
        z = Vector(0, 0, 1)
        axis = (vb - va).normalized()
        rot_axis = z.cross(axis)
        ang = math.degrees(math.acos(max(-1, min(1, z.dot(axis)))))
        if rot_axis.length > 1e-9:
            c = c.rotate(__import__("build123d").Axis((0, 0, 0), rot_axis), ang)
        elif axis.Z < 0:
            c = c.rotate(__import__("build123d").Axis.X, 180)
        parts.append(Pos(*((va + vb) * 0.5)) * c)
    for p in pts[1:-1]:
        parts.append(Pos(*p) * Sphere(d / 2))
    return Compound(parts)


def cut_list():
    rows = []
    for rid, grp, frm, to, cable, n, cas, pts, _d, _ign in RUNS:
        L = length(pts) * 1.15 + (SERVICE if cas else 0) + WOUND.get(rid, 0)
        rows.append(dict(id=rid, group=grp, frm=frm, to=to, cable=cable, n=n, cassette=cas,
                         length_in=round(L, 1)))
    return rows


def check(model):
    """Bundle vs populated model, ignoring each run's own endpoint parts. Returns clashes."""
    out = []
    names = [(n, s, s.bounding_box()) for n, s in model]
    for rid, _g, _f, _t, _c, _n, _cas, pts, d, ign in RUNS:
        b = bundle(pts, d)
        bb = b.bounding_box()
        for n, s, sb in names:
            if any(n.startswith(i) for i in ign):
                continue
            if (bb.max.X < sb.min.X or sb.max.X < bb.min.X or bb.max.Y < sb.min.Y or sb.max.Y < bb.min.Y
                    or bb.max.Z < sb.min.Z or sb.max.Z < bb.min.Z):
                continue
            v = (b & s).volume
            if v > 1e-5:
                out.append((rid, n, round(v, 4)))
    return out


def populated(skip=()):
    """[(name, shape)] for the full populated cabinet (winding drawn as rings for hidden-line speed)."""
    parts = [(n, s) for n, s in E.assembly() if n not in skip]
    parts += [(n, s) for n, s in E.fixtures() if n not in skip]
    parts += E.internals()            # the roller's winding arrives as one torus per turn (install_parts)
    return parts


if __name__ == "__main__":
    model = populated() + E.harness()
    clashes = check(model)
    print("harness clashes:", clashes)
    rows = cut_list()
    json.dump(dict(groups=GROUPS, runs=rows), open(OUT / "harness.json", "w"), indent=1)
    print(f"{len(rows)} runs, {sum(r['length_in'] for r in rows) / 12:.1f} ft total")
