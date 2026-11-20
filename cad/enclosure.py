# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Parametric model of the tuner enclosure: vertical stack, modular utility layer, wall mount.

Inches throughout. Enclosure frame (shared with roller.py's installation sheet):
  X = depth, front -, rear + (the rear is flush on the garage wall)
  Y = width, +Y is the LEFT side as you face the front
  Z = up from the underside of the floor
Design basis: design log §3.0 (vertical stack), §3.2 (clearances), §4 (bolted 6061 angle frame,
5052 panels), §8 (air path), §8D (output feedthroughs), §8E (sealing), Rev 3.7a decisions:
split upper/lower side panels, conductive-elastomer gaskets (G-1), wall mount on L-bracket
flanges, front service panels, control cassette, motor axis modules. Values marked ASSUMED are
component envelopes or choices not yet fixed in the log.

Writes true-size STEP files (mm) to out/ with the prefix enc-, and out/enclosure.json.
"""
import json
import math

from build123d import Align, Compound, Cone, Plane, Polygon, RegularPolygon, Torus, Vector, export_step, extrude

import roller as R
from roller import Box, Cylinder, Pos, Rot, rod

OUT = R.OUT

# ---- envelope and sheet stock (§3.0, §4) ----
W = D = R.ENC                                    # 16.00 x 16.00
H = R.ENC_H                                      # 24.00 (Rev 3.7c)
T14, T12 = 0.064, 0.081                          # 5052-H32 14 ga walls, 12 ga floor / top / shelf / partitions
F = W / 2 - T14                                  # frame outer corner, inside the 14 ga walls (7.936)
ANG, ANG_T = 1.0, 0.125                          # 1 x 1 x 1/8 6061-T6 angle
SANG = 0.5                                       # 1/2 x 1/2 x 1/8 where a full leg would block a module
Z_FLOOR = R.FLOOR_T                              # top of the floor panel; frame starts here
Z_TOP = H - R.LID_T                              # underside of the top panel; frame ends here
Z_SH0, Z_SH1 = R.Z_SHELF, R.Z_SHELF + R.SHELF_T  # internal grounded shelf
Z_SPLIT = (Z_SH0 + Z_SH1) / 2                    # lower / upper panel seam (over the shelf edge)

# ---- utility layer chambers along X (§3.0, re-centered under the motors) ----
X_IN = F                                         # inside faces of the front / rear walls (= frame corner)
CTRL_D, MOTOR_D, SAMP_D = 3.10, 7.75, 4.86       # chamber depths (motor chamber spans both cap motors)
X_BULK = -X_IN + CTRL_D                          # control / motor bulkhead plate (removable)
X_PART = X_BULK + T12 + MOTOR_D                  # motor / sampler partition (fixed)

# ---- drive axes (from roller.py's installation) ----
AXES = {"C1": (R.CAP_X[0], R.CAP_Y), "C2": (R.CAP_X[1], R.CAP_Y), "ROLLER": (R.ROLLER_X, R.ROLLER_Y)}
MOTOR_SQ, MOTOR_L = R.MOTOR_BODY                 # NEMA 23 body, length per DECISION M-2
Z_MOTOR_FACE = R.Z_SHELF - 1.75                  # motor face: encoder pulley 0.6 + coupler A 1.0 + plate below the shelf
ENC_MODULE = {"C1": (+1, 1.20), "C2": (-1, 1.20), "ROLLER": (+1, 1.20)}   # side (+/-X) and length of each
                                                  # encoder / limit-cam module beside its bracket (7.1, 7.2)

# ---- cassette (control chamber, slides out the front) ----
CASS_RAIL = SANG                                 # floor rails, 1/2 angle
Y_STRIP = 3.6                                    # tray stops here; the +Y strip beyond is the floor I/O strip
Z_TRAY = Z_FLOOR + CASS_RAIL                     # tray underside
CASS_CLEAR = (Z_SH0 - SANG) - (Z_TRAY + T12)     # component height that clears the front opening
PSU = (7.64, 1.02, 2.17)                         # Mean Well UHP-200-24 on edge (W x D x H), 9 item 39
BOARD = (5.5, 0.75, 3.6)                         # ASSUMED control board on standoffs, upright
DISPLAY = (3.957, 2.163, 0.55)                   # Nextion NX4832K035 board + standoffs (7.5)

# ---- front panel UI (cassette face), positions from the face's lower-left corner seen from the front ----
DISPLAY_OFF = 0.095   # NX4832K035: active-area center sits 2.42 mm off the board center, away from the ribbon end


def pattern(dx, dy, d, cx=0.0, cy=0.0):
    """Four holes on a dx x dy rectangle centered at (cx, cy) relative to a cutout."""
    return [(cx + sx * dx / 2, cy + sy * dy / 2, d) for sx in (-1, 1) for sy in (-1, 1)]


# kind "rect+" / "hole+": size = (main size, [(du, dv, dia), ...] companion holes, table text)
UI = [  # (tag, kind, x_from_left, z_from_bottom, size, note)
    ("A", "rect+", 4.20, 2.55, ((2.95, 1.99), pattern(3.705, 1.911, 0.130, cx=-DISPLAY_OFF),
                                "4x⌀0.130 ON 3.705x1.911"),
     "DISPLAY WINDOW, NX4832K035; HOLE PATTERN 0.095 LEFT OF WINDOW, RIBBON END LEFT (7.5)"),
    ("B", "hole", 9.40, 2.55, 0.380, "ENCODER 1, GRAYHILL 62V15-02-080CH, 3/8-32 (NO TAB, KEYWAY)"),
    ("C", "hole", 11.40, 2.55, 0.380, "ENCODER 2, GRAYHILL 62V15-02-080CH, 3/8-32 (NO TAB, KEYWAY)"),
    ("D", "dflat", 13.40, 3.30, (0.748, 0.669), "KEYED BYPASS SWITCH, E-SWITCH KO128A2007, KEY OUT IN OFF (8B.4d)"),
    ("E", "hole", 13.40, 1.60, 0.630, "RECOVERY BUTTON, E-SWITCH PV6F240SS, FLUSH + GUARD RING (8B.4f)"),
    ("F", "hole", 10.60, 1.20, 1.000, "MICRO SD, ADAFRUIT 6070 PANEL-MOUNT EXTENDER (8B.5.6); CONFIRM HOLE IN HAND"),
]
SD_EXT = (1.18, 0.55)   # Adafruit 6070 behind the face: 30 mm nut (worst case), depth ASSUMED until in hand

# ---- floor I/O (all low-voltage I/O enters through the floor) ----
FLOOR_IO = [  # (tag, kind, x, y, size, note); x, y in enclosure coords
    ("A", "rect+", -6.30, 4.60, ((1.140, 1.299), [(0, -0.709, 0.138), (0, 0.709, 0.138)], "2x⌀0.138, 1.417 APART"),
     "IEC INLET, TE CORCOM 3EGG1-2, 2 x T2.5 A (8A.1) - CHECK TE DWG F7386D"),
    ("B", "hole+", -6.30, 6.15, (0.945, [(-0.374, -0.472, 0.138), (0.374, 0.472, 0.138)], "2x⌀0.138 CSK, DIAG 0.748 x 0.945"),
     "RJ45, SWITCHCRAFT EHRJ45P5E, UNSHIELDED (8C.3.1)"),
    ("C", "hole", -5.15, 4.25, 0.375, "POF TX FIBER, HEYCO 2020 SNAP BUSHING; HFBR-1521Z ON THE BOARD (8C.3.3)"),
    ("D", "hole", -5.15, 4.95, 0.375, "POF SPARE FIBER, HEYCO 2020 (PLUG IF UNUSED)"),
    ("E", "hole", -5.30, 6.20, 0.480, "MEMBRANE VENT, GORE PMF100320 M12x1.5, CONTROL CHAMBER (8E.3)"),
    ("F", "hole", 0.00, -6.60, 0.480, "MEMBRANE VENT, GORE PMF100320, MOTOR CHAMBER"),
    ("G", "conn", 3.55, -5.20, 0.625, "COAX INPUT, SO-239 AMPHENOL 83-798, PTFE (7.3)"),
    ("H", "conn", 3.55, -2.60, 0.688, "AUX / DUMMY LOAD, N AMPHENOL 82-97, PTFE (6B.4)"),
    ("J", "rect", 4.60, 1.00, (0.50, 1.00), "CAL LOAD TTM G150N50W4E ON WAKEFIELD 441K SINK BELOW, GASKETED (6B.3)"),
    ("K", "hole", 4.60, 6.00, 0.480, "MEMBRANE VENT, GORE PMF100320, SAMPLER CHAMBER"),
    ("L", "hole", 7.30, 7.30, 0.257, "GROUND STUD 1/4-20, INTO THE REAR LEFT POST (8A.2)"),
]
CONN_PITCH = 0.718                               # 4-hole flange pattern for SO-239 / N bulkheads

# ---- top: output feedthroughs (§8D), parallel to the wall, near the rear ----
FT_X, FT_SPACING, FT_HOLE = 5.0, 6.03, 1.00      # FT hole ASSUMED for a >= 10 kV single-hole ceramic
FT_Y = (-FT_SPACING / 2, FT_SPACING / 2)

# ---- RF bay air path (§8 Rev 3.7a: intake low-front on the right, exhaust high-rear on the left) ----
# intake straddles the deck (0.41 above its underside) so air sweeps under it past the choke and over it;
# the blower stays 5.0 below the top. Both follow the deck / box height (Rev 3.7c: +2.0)
INTAKE = dict(x=-3.0, z=R.Z_DECK - 0.41, w=8.0, h=4.0)      # right (-Y) upper side panel, honeycomb + filter
BLOWER = dict(x=3.40, z=H - 5.0, hole=4.57, pitch=4.134, screw=0.18)   # 120 mm, left (+Y) upper side

# ---- wall flanges (L-brackets on the two rear corners) ----
WF_LEG, WF_T, WF_Z = 2.0, 0.1875, (1.0, H - 2.0)   # 2 x 2 x 3/16 6061 angle, H - 3 long (21" at 24")
WF_SLOTS = (2.5, H / 2 - 0.5, H - 3.5)           # lag slots up the wall leg (Z)


def angle(origin, u, v, length, axis, a=ANG, b=ANG, t=ANG_T):
    """L-angle with its heel at `origin`, legs along unit vectors u and v, extruded `length` along
    unit vector `axis` (u, v swapped as needed so the extrusion runs along +axis)."""
    u, v, axis = Vector(*u), Vector(*v), Vector(*axis)
    if u.cross(v).dot(axis) < 0:
        u, v, a, b = v, u, b, a
    pl = Plane(origin=origin, x_dir=u, z_dir=u.cross(v))
    prof = pl * Polygon((0, 0), (a, 0), (a, t), (t, t), (t, b), (0, b), align=None)
    return extrude(prof, amount=length)


RINGS = [  # (heel z, vertical leg up?, 1/2 front member for the cassette?, name)
    (Z_FLOOR, True, True, "bottom ring"),        # front: 1/2 lip so the cassette slides
    (Z_SH0, False, True, "shelf ring lower"),    # under the shelf; 1/2 front leg
    (Z_SH1, True, False, "shelf ring upper"),    # on the shelf; RF service panel flange
    (Z_TOP, False, False, "top ring"),
]
# ring-to-post junctions (16, TUNER-E-201): a 1-1/2 x 1-1/2 x 1/8 clip nests in each post's inside corner, in the
# clear band between the ring flange and the ring legs' free edge. Per wall, a #6-32 flat head (82 deg, flush
# outside, nyloc inside) into the post at 0.55 from the corner and one into the ring member at 1.35. The cassette
# rings' front legs stop at the post (the tray slides past); their 1/2 front members are held by the floor / shelf.
CLIP_LEG, CLIP_T = 1.50, ANG_T
CLIP_H = ANG - ANG_T                             # 0.875: the clear band on a 1" ring leg
CLIP_SHORT = ANG - ANG_T                         # front leg at the cassette rings: ends at the post's edge
CLIP_HOLES = (0.55, 1.35)                        # from the frame's outer corner: post, ring member
CLIP_SCREW, CLIP_CSK = 0.144, (0.28, 0.078)      # #6 clearance; 82 deg countersink dia, depth in the 1/8 leg
JUNCTION_BANDS = [((z + ANG_T, z + ANG) if up else (z - ANG, z - ANG_T)) for z, up, _s, _n in RINGS]
JKEEP = 0.30                                     # rivnut blind-side radius 0.225 + margin, around each clip band


def junction_holes():
    """[(center on the outer wall face, outward axis)] for every junction screw (60)."""
    out = []
    for z, up, small_front, _n in RINGS:
        zm = z + (ANG_T + ANG) / 2 if up else z - (ANG_T + ANG) / 2
        for sx in (-1, 1):
            for sy in (-1, 1):
                for d in CLIP_HOLES:
                    out.append(((sx * (F - d), sy * F, zm), (0, sy, 0)))           # side wall
                    if not (small_front and sx < 0 and d > ANG):
                        out.append(((sx * F, sy * (F - d), zm), (sx, 0, 0)))       # front / rear wall
    return out


def junction_tool(c, o, csk):
    """(center, tool): the through hole for one junction screw (frame leg + clip); with csk, its countersink."""
    r = Pos(*c) * _rot_z_to(o)
    tool = r * Pos(0, 0, -0.25) * Cylinder(CLIP_SCREW / 2, 0.8)
    if csk:
        d, h = CLIP_CSK
        tool += r * Pos(0, 0, -h) * Cone(CLIP_SCREW / 2, d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        tool += r * Cylinder(d / 2, 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Vector(*c), tool


def _drill(shape, tools, pad=0.3):
    bb = shape.bounding_box()
    for c, t in tools:
        if (bb.min.X - pad <= c.X <= bb.max.X + pad and bb.min.Y - pad <= c.Y <= bb.max.Y + pad
                and bb.min.Z - pad <= c.Z <= bb.max.Z + pad):
            shape = shape - t
    return shape


def frame():
    """[(name, shape)]: 4 corner posts and the horizontal rings (bottom, shelf lower/upper, top), drilled and
    countersunk for the junction clips (clips())."""
    out = []
    zlen = Z_TOP - Z_FLOOR
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(("post", angle((sx * F, sy * F, Z_FLOOR), (0, -sy, 0), (-sx, 0, 0), zlen, (0, 0, 1))))
    span = 2 * (F - ANG)
    for z, up, small_front, name in RINGS:
        vz = (0, 0, 1 if up else -1)
        for sy in (-1, 1):   # side members along X
            out.append((name, angle((-F + ANG, sy * F, z), vz, (0, -sy, 0), span, (1, 0, 0))))
        for sx in (-1, 1):   # front / rear members along Y
            leg = SANG if (sx < 0 and small_front) else ANG
            out.append((name, angle((sx * F, -F + ANG, z), vz, (-sx, 0, 0), span, (0, 1, 0), a=leg, b=leg)))
    tools = [junction_tool(c, o, csk=True) for c, o in junction_holes()]
    return [(n, _drill(s, tools)) for n, s in out]


def clips(drilled=True):
    """[(name, shape)]: the 16 junction clips, nested in the posts' inside corners (TUNER-E-201)."""
    tools = [junction_tool(c, o, csk=False) for c, o in junction_holes()] if drilled else []
    out = []
    for z, up, small_front, _n in RINGS:
        z0 = z + ANG_T if up else z - ANG
        for sx in (-1, 1):
            for sy in (-1, 1):
                ly = CLIP_SHORT if (small_front and sx < 0) else CLIP_LEG
                c = angle((sx * (F - ANG_T), sy * (F - ANG_T), z0), (-sx, 0, 0), (0, -sy, 0), CLIP_H, (0, 0, 1),
                          a=CLIP_LEG, b=ly, t=CLIP_T)
                out.append(("corner clip", _drill(c, tools)))
    return out


def wall_clips():
    """[(name, shape)]: the bulkhead and partition clip angles (TUNER-E-208), one hole per leg."""
    leg, t, L = WCLIP
    mid = t + (leg - t) / 2                          # hole on each leg's flat
    out = []
    for plate, x0 in (("bulkhead", X_BULK), ("partition", X_PART)):
        for edge, s, y in WALL_CLIPS[plate]:
            xf = x0 + T12 if s > 0 else x0
            z, vz = (Z_FLOOR, 1) if edge == "floor" else (Z_SH0, -1)
            c = angle((xf, y - L / 2, z), (s, 0, 0), (0, 0, vz), L, (0, 1, 0), a=leg, b=leg, t=t)
            c -= Pos(xf + s * mid, y, z + vz * t / 2) * Cylinder(WCLIP_HOLE / 2, 1)                 # floor / shelf leg
            dp = WCLIP_TAP if plate == "bulkhead" else WCLIP_HOLE
            c -= Pos(xf + s * t / 2, y, z + vz * mid) * Rot(0, 90, 0) * Cylinder(dp / 2, 1)          # plate leg
            out.append((f"{plate} clip", c))
    return out


def wall_clip_detail():
    """Typical bulkhead mounting for TUNER-E-208, seen along Y: floor and shelf stubs, the bulkhead, a floor clip
    and a shelf clip on its motor side, all drilled; cut on the screw plane it reads as a section with the holes
    lined up (the screws are in the sheet's note). Control face at x = 0, floor top at z = 0."""
    leg, t, L = WCLIP
    mid = t + (leg - t) / 2
    xb, xf, w = X_BULK, X_BULK + T12, 0.6
    floor = plate(xb - 1.2, xb + 1.6, -w, w, Z_FLOOR - R.FLOOR_T, Z_FLOOR)
    shelf = plate(xb - 1.2, xb + 1.6, -w, w, Z_SH0, Z_SH1)
    bulk = plate(xb, xf, -w, w, Z_FLOOR, Z_SH0)
    out = []
    for z, vz in ((Z_FLOOR, 1), (Z_SH0, -1)):
        c = angle((xf, -L / 2, z), (1, 0, 0), (0, 0, vz), L, (0, 1, 0), a=leg, b=leg, t=t)
        vert = Pos(xf + mid, 0, z) * Cylinder(WCLIP_HOLE / 2, 2)                          # floor / shelf screw
        horiz = Pos(xb, 0, z + vz * mid) * Rot(0, 90, 0) * Cylinder(WCLIP_HOLE / 2, 2)    # bulkhead screw
        out.append(c - vert - Pos(xf + t / 2, 0, z + vz * mid) * Rot(0, 90, 0) * Cylinder(WCLIP_TAP / 2, 1))
        floor, shelf, bulk = floor - vert, shelf - vert, bulk - horiz
    out += [floor, shelf, bulk]
    return [Pos(-xb, 0, -Z_FLOOR) * s for s in out]


def junction_detail(explode=False):
    """Typical junction for TUNER-E-201 — bottom ring, rear-left corner (+X rear, +Y left) — cut to stubs,
    with its #6 flat heads and nylocs, the corner moved to the origin. explode pulls clip, screws and nuts apart."""
    zr = Z_FLOOR
    box = plate(F - 4.0, F + 0.1, F - 4.0, F + 0.1, zr - 0.1, zr + 2.6)
    out = []
    for _n, s in frame():
        bb = s.bounding_box()
        if bb.max.X > F - 4 and bb.max.Y > F - 4 and bb.min.Z < zr + 2.6:
            stub = s & box
            if stub.volume > 1e-6:
                out.append(stub)
    clip = next(s for _n, s in clips() if s.bounding_box().min.X > 0 and s.bounding_box().min.Y > 0
                and abs(s.bounding_box().min.Z - (zr + ANG_T)) < 1e-6)
    out.append(Pos(-1.0, -1.0, 0) * clip if explode else clip)
    zm = zr + (ANG_T + ANG) / 2
    for c, o in junction_holes():
        if not (c[0] > 0 and c[1] > 0 and abs(c[2] - zm) < 1e-6):
            continue
        r = Pos(*c) * _rot_z_to(o)
        screw = r * Pos(0, 0, -0.065) * Cone(0.069, 0.131, 0.065, align=(Align.CENTER, Align.CENTER, Align.MIN))
        screw += r * Pos(0, 0, -0.5) * Cylinder(0.069, 0.436, align=(Align.CENTER, Align.CENTER, Align.MIN))
        nut = r * Pos(0, 0, -2 * ANG_T - 0.23) * extrude(RegularPolygon(0.3125 / math.sqrt(3), 6), 0.23)
        if explode:
            screw = Pos(o[0] * 0.9, o[1] * 0.9, o[2] * 0.9) * screw
            nut = Pos(o[0] * -1.4, o[1] * -1.4, o[2] * -1.4) * nut
        out += [screw, nut]
    return [Pos(-F, -F, -zr) * s for s in out]


def plate(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def connector_flange(cx, cy, z, pitch=CONN_PITCH, d=0.125):
    return [Pos(cx + sx * pitch / 2, cy + sy * pitch / 2, z) * Cylinder(d / 2, 2) for sx in (-1, 1) for sy in (-1, 1)]


# ------------------------------------------------------------------ panels as specifications
# Each panel is described once: outline, which frame legs its edges land on, and its cutouts. The
# solid, the perimeter fastener holes, the hole tables and the drawing view all come from this.
SCREW_D = 0.177                  # 8-32 clearance; captive panel screws use the retainer's hole size
PITCH_MAX = 1.75                 # §4: 8-32 on <= 1.75" centers
CORNER_C = 2.00                  # first hole from a corner along an edge: past the post leg and the junction clip,
                                 # so every hole lands on a ring flange (the 1" corner squares have none) and the
                                 # clip zone stays free of rivnuts; corner diagonal to the first post hole ~1.70"
KEEP_OUT = 0.30                  # perimeter holes stay this far from any cutout
FAN_FRAME = 4.72                 # 120 mm blower frame


def _rot_to(n):
    n = tuple(round(c) for c in n)
    return {(1, 0, 0): Rot(0, 90, 0), (-1, 0, 0): Rot(0, 90, 0), (0, 1, 0): Rot(90, 0, 0),
            (0, -1, 0): Rot(90, 0, 0)}.get(n, Rot(0, 0, 0))


def _rot_z_to(o):
    """Rotation taking +Z onto the axis o exactly (sign kept, unlike _rot_to): for countersinks and heads."""
    return {(1, 0, 0): Rot(0, 90, 0), (-1, 0, 0): Rot(0, -90, 0), (0, 1, 0): Rot(-90, 0, 0),
            (0, -1, 0): Rot(90, 0, 0), (0, 0, 1): Rot(0, 0, 0), (0, 0, -1): Rot(180, 0, 0)}[tuple(round(c) for c in o)]


class Panel:
    """A flat panel seen from outside: origin = lower-left corner on the outside face; U to the right,
    V up, n outward; thickness t inward. edges: inset of the fastener line from each edge, or None.
    cutouts: (tag, kind, u, v, size, note) with kind rect | hole | conn | fan | dsub | dflat | ddflat | rect+ | hole+."""

    def __init__(self, name, origin, U, V, n, L, Hh, t, edges, cutouts=(), rows=(), forced=(), gauge="14 GA",
                 notes=()):
        self.name, self.o = name, Vector(*origin)
        self.U, self.V, self.n = Vector(*U), Vector(*V), Vector(*n)
        self.L, self.H, self.t = L, Hh, t
        self.edges, self.cutouts, self.rows, self.forced = edges, list(cutouts), list(rows), list(forced)
        self.gauge, self.notes = gauge, list(notes)

    def p3(self, u, v, depth=0.0):
        return self.o + self.U * u + self.V * v - self.n * depth

    def _blocked(self, u, v):
        for _t, kind, cu, cv, size, _n in self.cutouts:
            if kind.endswith("+"):
                if any(math.hypot(u - cu - du, v - cv - dv) <= d / 2 + KEEP_OUT for du, dv, d in size[1]):
                    return True
                kind, size = kind[:-1], size[0]
            if kind in ("rect", "dsub", "fan"):
                w, h = (FAN_FRAME, FAN_FRAME) if kind == "fan" else size[:2]   # fan: its 120 mm square frame
                if abs(u - cu) <= w / 2 + KEEP_OUT and abs(v - cv) <= h / 2 + KEEP_OUT:
                    return True
            elif math.hypot(u - cu, v - cv) <= (size[0] if kind in ("dflat", "ddflat") else size) / 2 + KEEP_OUT:
                return True
        return False

    @staticmethod
    def _spread(a, b):
        span = b - a
        if span <= 0:
            return []
        n = max(2, math.ceil(span / PITCH_MAX) + 1)
        return [a + i * span / (n - 1) for i in range(n)]

    def _post_segments(self, lo, hi):
        """[lo, hi] along a vertical panel's side edges (they land on the posts) minus the junction-clip bands,
        so no rivnut sits behind a clip; each free stretch is spread on its own, keeping the pitch."""
        if abs(self.V.Z) < 0.99:
            return [(lo, hi)]
        blocks = sorted(tuple(sorted(((z0 - JKEEP - self.o.Z) / self.V.Z, (z1 + JKEEP - self.o.Z) / self.V.Z)))
                        for z0, z1 in JUNCTION_BANDS)
        free, a = [], lo
        for v0, v1 in blocks:
            if v1 <= a or v0 >= hi:
                continue
            if v0 > a:
                free.append((a, v0))
            a = max(a, v1)
        if a < hi:
            free.append((a, hi))
        return [(x, y) for x, y in free if y - x >= 0.6]

    def fastener_holes(self):
        e = self.edges
        pts = []
        if e.get("bottom") is not None:
            pts += [(u, e["bottom"]) for u in self._spread(CORNER_C, self.L - CORNER_C)]
        if e.get("top") is not None:
            pts += [(u, self.H - e["top"]) for u in self._spread(CORNER_C, self.L - CORNER_C)]
        for v in self.rows:
            pts += [(u, v) for u in self._spread(CORNER_C, self.L - CORNER_C)]
        lo = (e.get("bottom") or 0) + 0.9
        hi = self.H - (e.get("top") or 0) - 0.9
        segs = self._post_segments(lo, hi)
        if e.get("left") is not None:
            pts += [(e["left"], v) for a, b in segs for v in self._spread(a, b)]
        if e.get("right") is not None:
            pts += [(self.L - e["right"], v) for a, b in segs for v in self._spread(a, b)]
        out = []
        for u, v in pts:
            if self._blocked(u, v) or any(math.hypot(u - fu, v - fv) < 0.6 for fu, fv in self.forced):
                continue
            if any(math.hypot(u - a, v - b) < 0.5 for a, b in out):
                continue
            out.append((u, v))
        return out + list(self.forced)

    def edge_summary(self):
        """[(edge, count, pitch, inset)] for the drawing notes."""
        holes = self.fastener_holes()
        rows = []
        for edge, test in (("BOTTOM", lambda u, v: abs(v - (self.edges.get("bottom") or -9)) < 1e-6),
                           ("TOP", lambda u, v: abs(v - (self.H - (self.edges.get("top") or -9))) < 1e-6),
                           ("LEFT", lambda u, v: abs(u - (self.edges.get("left") or -9)) < 1e-6),
                           ("RIGHT", lambda u, v: abs(u - (self.L - (self.edges.get("right") or -9))) < 1e-6)):
            pts = sorted(p for p in holes if test(*p))
            if not pts:
                continue
            key = 0 if edge in ("BOTTOM", "TOP") else 1
            gaps = [b[key] - a[key] for a, b in zip(pts, pts[1:])]
            inset = self.edges[edge.lower()]
            rows.append((edge, len(pts), max(gaps) if gaps else 0, inset))
        for v in self.rows:
            pts = [p for p in holes if abs(p[1] - v) < 1e-6]
            gaps = [b[0] - a[0] for a, b in zip(sorted(pts), sorted(pts)[1:])]
            rows.append((f"ROW AT {v:.3f}", len(pts), max(gaps) if gaps else 0, v))
        return rows

    def _cut_hole(self, u, v, d):
        return Pos(*self.p3(u, v, self.t / 2)) * _rot_to(self.n) * Cylinder(d / 2, self.t + 0.4)

    def _cut_rect(self, u, v, w, h):
        dims = [abs(self.U.X) * w + abs(self.V.X) * h + abs(self.n.X) * (self.t + 0.4),
                abs(self.U.Y) * w + abs(self.V.Y) * h + abs(self.n.Y) * (self.t + 0.4),
                abs(self.U.Z) * w + abs(self.V.Z) * h + abs(self.n.Z) * (self.t + 0.4)]
        return Pos(*self.p3(u, v, self.t / 2)) * Box(*dims)

    def shape(self):
        a, b = self.p3(0, 0, self.t), self.p3(self.L, self.H, 0)
        lo = [min(a.X, b.X), min(a.Y, b.Y), min(a.Z, b.Z)]
        hi = [max(a.X, b.X), max(a.Y, b.Y), max(a.Z, b.Z)]
        p = plate(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
        for _t, kind, u, v, size, _n in self.cutouts:
            if kind.endswith("+"):
                for du, dv, d in size[1]:
                    p -= self._cut_hole(u + du, v + dv, d)
                kind, size = kind[:-1], size[0]
            if kind in ("rect", "dsub"):
                p -= self._cut_rect(u, v, *size[:2])
                if kind == "dsub":
                    for du in (-size[2] / 2, size[2] / 2):
                        p -= self._cut_hole(u + du, v, 0.120)
            elif kind == "dflat":           # round hole with one flat: size = (dia, across the flat)
                d, f = size
                p -= self._cut_hole(u, v, d) & self._cut_rect(u, v - d / 2 + f / 2, d, f)
            elif kind == "ddflat":          # round hole with two flats: size = (dia, across the flats)
                d, f = size
                p -= self._cut_hole(u, v, d) & self._cut_rect(u, v, f, d)
            else:
                d = {"fan": BLOWER["hole"]}.get(kind, size if kind != "fan" else 0)
                p -= self._cut_hole(u, v, d)
                if kind == "conn":
                    for du in (-CONN_PITCH / 2, CONN_PITCH / 2):
                        for dv in (-CONN_PITCH / 2, CONN_PITCH / 2):
                            p -= self._cut_hole(u + du, v + dv, 0.125)
                if kind == "fan":
                    for du in (-BLOWER["pitch"] / 2, BLOWER["pitch"] / 2):
                        for dv in (-BLOWER["pitch"] / 2, BLOWER["pitch"] / 2):
                            p -= self._cut_hole(u + du, v + dv, BLOWER["screw"])
        for u, v in self.fastener_holes():
            p -= self._cut_hole(u, v, SCREW_D)
        return p

    def meta(self):
        return {"name": self.name, "L": self.L, "H": self.H, "t": self.t, "gauge": self.gauge,
                "n": tuple(self.n), "U": tuple(self.U), "cutouts": self.cutouts,
                "edges": self.edge_summary(), "fasteners": len(self.fastener_holes()),
                "perimeter": 2 * (self.L + self.H), "notes": self.notes}


E1 = W / 2 - (F - ANG / 2)                       # 0.564: fastener line on a 1" leg, from the panel edge
SIDE_E = ANG / 2                                 # side panels end at the frame corner: 0.500
V_SPLIT_UP = Z_SH1 + ANG / 2 - Z_SPLIT           # upper panels' bottom row, on the upper shelf ring
V_SPLIT_LO = Z_SPLIT - (Z_SH0 - ANG / 2)         # lower panels' top row, on the lower shelf ring
FLANGE_Z = (3.0, H / 2 - 0.5, H - 4.0)           # wall-flange bolts through the rear posts


def panels():
    P = []
    P.append(Panel("RF service panel", (-W / 2, D / 2, Z_SPLIT), (0, -1, 0), (0, 0, 1), (-1, 0, 0),
                   W, Z_TOP - Z_SPLIT, T14, dict(left=E1, right=E1, bottom=V_SPLIT_UP, top=ANG / 2),
                   notes=["RF BAY SERVICE PANEL: CAPTIVE SCREWS, CONDUCTIVE-ELASTOMER GASKET ON THE FRAME"]))
    face_cut = [(t, k, xl, zb, sz, nt) for t, k, xl, zb, sz, nt in UI]
    P.append(Panel("cassette face", (-W / 2, D / 2, Z_FLOOR), (0, -1, 0), (0, 0, 1), (-1, 0, 0),
                   W, Z_SPLIT - Z_FLOOR, T14,
                   dict(left=E1, right=E1, bottom=SANG / 2, top=Z_SPLIT - (Z_SH0 - SANG / 2)), face_cut,
                   notes=["CONTROL CASSETTE FACE: CARRIES THE UI; 100-MESH Cu SCREEN BONDED BEHIND THE DISPLAY (7.5)"]))
    rear_rows = [Z_SH0 - ANG / 2 - Z_FLOOR, Z_SH1 + ANG / 2 - Z_FLOOR]
    P.append(Panel("rear panel", (W / 2, -D / 2, Z_FLOOR), (0, 1, 0), (0, 0, 1), (1, 0, 0),
                   W, Z_TOP - Z_FLOOR, T14, dict(left=E1, right=E1, bottom=ANG / 2, top=ANG / 2), rows=rear_rows,
                   notes=["ON THE WALL; NOT REMOVED IN SERVICE. NO CUTOUTS"]))
    for side, sy in (("left", 1), ("right", -1)):
        # seen from outside: left side's left edge is the rear (+X); right side's left edge is the front
        U = (-1, 0, 0) if sy > 0 else (1, 0, 0)
        ox = F if sy > 0 else -F
        rear_u = 0.0 if sy > 0 else 2 * F        # u of the rear edge, where the wall flange bolts go
        rear_line = SIDE_E if sy > 0 else 2 * F - SIDE_E
        for zone, z0, z1, eb, et in (("lower", Z_FLOOR, Z_SPLIT, ANG / 2, V_SPLIT_LO),
                                     ("upper", Z_SPLIT, Z_TOP, V_SPLIT_UP, ANG / 2)):
            cut = []
            if side == "right" and zone == "upper":
                cut.append(("A", "rect", INTAKE["x"] + F, INTAKE["z"] - z0, (INTAKE["w"], INTAKE["h"]),
                            "INTAKE: FILTER + 1/8 HONEYCOMB + 30-40 MESH SCREEN OUTSIDE (8, 8E.3)"))
            if side == "left" and zone == "lower":     # blower lead enters at the control chamber
                cut.append(("B", "dsub", F + FAN_ENTRY[0], FAN_ENTRY[1] - z0, DE9,
                            "FILTERED DE-9, 5600 pF: BLOWER +12 V / GND / TACH - FCE17-E09SM-290; LEAD IN FLEX CONDUIT"))
            if side == "left" and zone == "upper":
                cut.append(("A", "fan", F - BLOWER["x"], BLOWER["z"] - z0, BLOWER["hole"],
                            "120 mm BLOWER, EXHAUSTING; HONEYCOMB + SCREEN BEHIND (8)"))
            forced = [(rear_line, z - z0) for z in FLANGE_Z if z0 + eb < z < z1 - et]
            P.append(Panel(f"{side} {zone} panel", (ox, sy * W / 2, z0), U, (0, 0, 1), (0, sy, 0),
                           2 * F, z1 - z0, T14, dict(left=SIDE_E, right=SIDE_E, bottom=eb, top=et), cut,
                           forced=forced,
                           notes=[f"WALL-FLANGE BOLTS AT THE REAR POST LINE ({', '.join(f'{z:.1f}' for z in FLANGE_Z if z0 < z < z1)} ABOVE THE FLOOR) USE LONGER SCREWS"]
                           if forced else []))
    top_cut = [(f"F{i + 1}", "hole", W / 2 - y, FT_X + D / 2, FT_HOLE,
                ">= 10 kV CERAMIC OUTPUT FEEDTHROUGH (8D); INSULATING DUST COVER OVER BOTH (8D.6)")
               for i, y in enumerate(FT_Y)]
    P.append(Panel("top panel", (-D / 2, W / 2, H), (0, -1, 0), (1, 0, 0), (0, 0, 1), W, D, T12,
                   dict(left=E1, right=E1, bottom=E1, top=E1), top_cut, gauge="12 GA",
                   notes=["FIXED. FEEDTHROUGHS 6.03 APART, PARALLEL TO THE WALL"]))
    fl_cut = [(t, k, y + W / 2, x + D / 2, sz, nt) for t, k, x, y, sz, nt in FLOOR_IO]
    P.append(Panel("floor", (-D / 2, -W / 2, 0), (0, 1, 0), (1, 0, 0), (0, 0, -1), W, D, T12,
                   dict(left=E1, right=E1, bottom=W / 2 - (F - SANG / 2), top=E1), fl_cut, gauge="12 GA",
                   notes=["SEEN FROM BELOW, REAR AT THE TOP. ALL LOW-VOLTAGE I/O"]))
    sh_cut = [(t, "hole", F - y, x + F, d, nt) for t, x, y, d, nt in shelf_holes()]
    nn = ANG + 0.03
    for i, (cu, cv) in enumerate(((nn / 2, nn / 2), (2 * F - nn / 2, nn / 2), (nn / 2, 2 * F - nn / 2),
                                  (2 * F - nn / 2, 2 * F - nn / 2))):
        sh_cut.append((f"N{i + 1}", "rect", cu, cv, (nn, nn), "CORNER NOTCH FOR THE POST"))
    P.append(Panel("shelf", (-F, F, Z_SH1), (0, -1, 0), (1, 0, 0), (0, 0, 1), 2 * F, 2 * F, R.SHELF_T,
                   dict(left=ANG / 2, right=ANG / 2, bottom=ANG / 2, top=ANG / 2), sh_cut, gauge="12 GA",
                   notes=["GROUNDED SHELF: CLAMPED BETWEEN THE LOWER AND UPPER SHELF RINGS, GASKET BOTH FACES",
                          "SEEN FROM ABOVE, FRONT AT THE BOTTOM"]))
    yh = F - ANG_T - 0.01
    notch = [("N1", "rect", (ANG + 0.04) / 2, (ANG_T + 0.02) / 2, (ANG + 0.04, ANG_T + 0.02), "RING-LEG NOTCH"),
             ("N2", "rect", 2 * yh - (ANG + 0.04) / 2, (ANG_T + 0.02) / 2, (ANG + 0.04, ANG_T + 0.02), "RING-LEG NOTCH"),
             ("N3", "rect", (ANG + 0.04) / 2, Z_SH0 - Z_FLOOR - (ANG_T + 0.02) / 2, (ANG + 0.04, ANG_T + 0.02),
              "RING-LEG NOTCH"),
             ("N4", "rect", 2 * yh - (ANG + 0.04) / 2, Z_SH0 - Z_FLOOR - (ANG_T + 0.02) / 2,
              (ANG + 0.04, ANG_T + 0.02), "RING-LEG NOTCH")]
    bio = [(t, k, yh - y, z - Z_FLOOR, sz, nt) for t, k, y, z, sz, nt in BULKHEAD_IO]
    pio = [(t, k, yh - y, z - Z_FLOOR, sz, nt) for t, k, y, z, sz, nt in PARTITION_IO]
    P.append(Panel("bulkhead", (X_BULK, yh, Z_FLOOR), (0, -1, 0), (0, 0, 1), (-1, 0, 0), 2 * yh, Z_SH0 - Z_FLOOR,
                   T12, {}, bio + notch, gauge="12 GA",
                   notes=["REMOVABLE: 8 CLIP ANGLES ON ITS MOTOR SIDE (4 FLOOR, 4 SHELF); 8-32 FROM THE CONTROL SIDE",
                          "INTO THE TAPPED CLIP LEGS. HOLES MATCH-DRILLED FROM THE CLIPS (CLIP TABLE). GASKETED"]))
    P.append(Panel("motor/sampler partition", (X_PART, yh, Z_FLOOR), (0, -1, 0), (0, 0, 1), (-1, 0, 0), 2 * yh,
                   Z_SH0 - Z_FLOOR, T12, {}, pio + notch, gauge="12 GA",
                   notes=["FIXED: 8 CLIP ANGLES (4 FLOOR ON THE MOTOR SIDE, 4 SHELF ON THE SAMPLER SIDE), 8-32 + NYLOC,",
                          "MATCH-DRILLED FROM THE CLIPS (CLIP TABLE). SAMPLER LINES PER 7.3 / 9 ITEM 38"]))
    return P


DB25, DA15, DE9 = (1.744, 0.512, 1.852), (1.200, 0.512, 1.312), (0.875, 0.512, 0.984)   # cutout w x h, hole pitch
FAN_ENTRY = (-6.0, 3.6)                          # (x, z) of the blower-lead DE-9 on the left lower panel
BULKHEAD_IO = [  # (tag, kind, y, z, size, note) on the control/motor bulkhead, world y / z: the +y half is clear of
    # the C1 axis module on the motor side and of the PSU on the control side; plugs mate from the control side
    ("A", "dsub", 4.0, 4.2, DB25, "FILTERED DB-25, 1000 pF: CONTROL -> MOTOR (STEP/DIR/EN, SPI, LIM) - FCE17-B25SM-250"),
    ("B", "dsub", 4.0, 3.15, DB25, "FILTERED DB-25, 5600 pF: SAMPLER GROUP (7.3, 9.38) - FCE17-B25SM-290"),
    ("E", "dsub", 4.0, 2.1, DE9, "FILTERED DE-9, 5600 pF: THERMAL, CT, RF PANEL SW - FCE17-E09SM-290"),
    ("C", "hole", 1.9, 4.0, 0.221, "24 V FILTERED FEEDTHROUGH, 0.30 uF 15 A, 12-32 - SPECTRUM 9910-381-6002"),
    ("D", "hole", 1.9, 3.3, 0.221, "24 V RETURN, SAME PART"),
    ("P", "hole", 1.9, 2.5, 0.221, "PRESCALER FEEDTHROUGH 1000 pF, 12-28 - TUSONIX 2499-003-X5U0-102PLF"),
]
PARTITION_IO = [  # same convention, on the motor / sampler partition; the sampler-cable plug mates from the motor side
    ("A", "dsub", 3.2, 4.3, DB25, "FILTERED DB-25, 5600 pF: SAMPLER GROUP, BELDEN 8112 TO BULKHEAD B - FCE17-B25SM-290"),
    ("X", "ddflat", -6.3, 4.4, (0.634, 0.540), "COAX N-N BULKHEAD, AMPHENOL RF 172124, PTFE, 5/8-24 JAM NUT: CHOKE -> SHELF COAX"),
    ("P", "hole", 0.8, 1.9, 0.221, "PRESCALER FEEDTHROUGH 1000 pF, RG-316 TO BULKHEAD P - TUSONIX 2499-003-X5U0-102PLF"),
]

# bulkhead / partition mounting (TUNER-E-208): 1/2 x 1/2 x 1/8 x 1.0 clip angles, four at the floor and four at
# the shelf per plate. The removable bulkhead's clips sit on its motor side, so it unscrews from the control side
# (8-32 into tapped clip legs) and comes out without touching them. The fixed partition's floor clips are on its
# motor side (the sampler baseplate fills the other) and its shelf clips on the sampler side (the C2 bracket and
# the plugs own the motor side's top edge). Every position clears the axis modules, connector envelopes, the
# baseplate and the assumed driver board (interference-checked).
WALL_CLIPS = {  # plate: [(edge, side, y)]; side +1 = toward +X (bulkhead's motor side, partition's sampler side)
    "bulkhead": [("floor", 1, y) for y in (-5.75, -1.75, 1.75, 5.75)] + [("shelf", 1, y) for y in (-6.2, -0.9, 1.9, 6.2)],
    "partition": [("floor", -1, y) for y in (-6.2, -3.4, -0.6, 1.2)] + [("shelf", 1, y) for y in (-5.0, -2.6, -0.2, 5.8)],
}
WCLIP = (SANG, ANG_T, 1.00)                      # leg, thickness, length
WCLIP_HOLE, WCLIP_TAP = 0.177, 0.136             # 8-32 clearance; 8-32 tap drill (bulkhead plate legs)

SHELF_EXTRA = [  # (tag, x, y, dia, note) beyond the drive-axis bushings
    ("COAX", -4.0, R.CAP_Y + 2.4, 0.625, "COAX BULKHEAD, SAMPLER -> C1 (3.0); OVER THE MOTOR CHAMBER, NOT CONTROL"),
]
SHELF_FT = [(0.3 + 0.55 * i, -6.5, 0.221) for i in range(4)]   # 12-28 nut + lockwasher needs 0.55
PANEL_SW_Y = -5.15     # RF service-panel reed sensor (FT4): centered between the panel's rivnuts at y -5.78 / -4.51


def shelf_holes():
    rows = []
    for tag, (x, y) in AXES.items():
        rows.append((tag if tag != "ROLLER" else "R", x, y, R.SHELF_HOLE, "G10 SHAFT BUSHING, FLANGED BRONZE 3/8 BORE"))
    rows += SHELF_EXTRA
    for i, (x, y, d) in enumerate(SHELF_FT):
        rows.append((f"FT{i + 1}", x, y, d, "FEEDTHROUGH 0.01 uF 12-28, TUSONIX 2499-003-X5W0-103ZLF: THERMAL 1, CT 2, RETURN 3, PANEL SW 4"))
    s = R.DECK_SIZE / 2 - 0.5
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        rows.append((f"S{i + 1}", sx * s, sy * s, 0.201, "DECK STANDOFF, #10 SCREW FROM BELOW"))
    for i in range(3):                               # input choke mount (6, Rev 3.7c)
        a = math.radians(90 + 120 * i)
        rows.append((f"CH{i + 1}", CHOKE_X + CHOKE_BC / 2 * math.cos(a), CHOKE_Y + CHOKE_BC / 2 * math.sin(a), 0.177,
                     "CHOKE MOUNT: G10 STANDOFF, 8-32 SCREW FROM BELOW"))
    return rows


def cassette():
    """[(name, shape)]: face (front lower panel with the UI), tray, rails and component envelopes."""
    out = []   # the face itself is a Panel (panels())
    x0, x1 = -X_IN + SANG + 0.02, X_BULK - 0.15   # behind the front 1/2 lip
    yw = F - ANG - 0.15                          # tray clears the side bottom-ring legs
    out.append(("cassette tray", plate(x0, x1, -yw, Y_STRIP, Z_TRAY, Z_TRAY + T12)))
    for sy, y in ((-1, -yw + 0.6), (1, Y_STRIP - 0.6)):
        out.append(("cassette rail", angle((x0, y, Z_FLOOR), (0, 0, 1), (0, -sy, 0),
                                           x1 - x0, (1, 0, 0), a=SANG, b=SANG)))
    zc = Z_TRAY + T12
    out.append(("PSU envelope", plate(x1 - PSU[1] - 0.1, x1 - 0.1, -yw + 0.3, -yw + 0.3 + PSU[0], zc, zc + PSU[2])))
    out.append(("control board envelope", plate(x1 - BOARD[1] - 1.5, x1 - 1.5, Y_STRIP - 0.1 - BOARD[0], Y_STRIP - 0.1, zc + 0.2,
                                                zc + 0.2 + BOARD[2])))
    yd, zd = D / 2 - (UI[0][2] - DISPLAY_OFF), Z_FLOOR + UI[0][3]
    out.append(("display envelope", plate(-F + 0.02, -F + 0.02 + DISPLAY[2], yd - DISPLAY[0] / 2,
                                          yd + DISPLAY[0] / 2, zd - DISPLAY[1] / 2, zd + DISPLAY[1] / 2)))
    t, _k, xs, zs, _sz, _nt = UI[-1]                     # the SD extender's body and nut behind the face
    out.append(("SD extender envelope", Pos(-F + 0.02, D / 2 - xs, Z_FLOOR + zs)
                * Rot(0, 90, 0) * Cylinder(SD_EXT[0] / 2, SD_EXT[1], align=(Align.CENTER, Align.CENTER, Align.MIN))))
    return out


def axis_module(name, x, y):
    """[(name, shape)]: hanging bracket under the shelf, motor plate, coupler A, motor, G10 stub."""
    out = []
    t = 0.125
    hx = MOTOR_SQ / 2 + 0.02                      # bracket no longer than the motor along X
    top = plate(x - hx, x + hx, y - 1.5, y + 1.5, Z_SH0 - t, Z_SH0) - Pos(x, y, Z_SH0) * Cylinder(0.75, 1)
    mp_z = Z_MOTOR_FACE
    mplate = plate(x - hx, x + hx, y - 1.5, y + 1.5, mp_z, mp_z + t) - Pos(x, y, mp_z) * Cylinder(0.76, 1)
    for dx in (-0.928, 0.928):
        for dy in (-0.928, 0.928):
            mplate -= Pos(x + dx, y + dy, mp_z) * Cylinder(0.105, 1)
    sides = [plate(x - hx, x + hx, y + sy * 1.5 - (t if sy > 0 else 0), y + sy * 1.5 + (0 if sy > 0 else t),
                   mp_z + t, Z_SH0 - t) for sy in (-1, 1)]
    bracket = top + mplate + sides[0] + sides[1]
    out.append((f"{name} axis bracket", bracket))
    out.append((f"{name} motor", plate(x - MOTOR_SQ / 2, x + MOTOR_SQ / 2, y - MOTOR_SQ / 2, y + MOTOR_SQ / 2,
                                       mp_z - MOTOR_L, mp_z)))
    out.append((f"{name} coupler A", Pos(x, y, mp_z + t + 0.05) * rod(1.0, 1.0)))
    # encoder takeoff: GT2 pulley on the G10 shaft above coupler A, belt out through the bracket's open side
    out.append((f"{name} takeoff pulley", Pos(x, y, mp_z + t + 1.15) * (rod(0.65, 0.40) - rod(R.G10_D + 0.002, 0.40))))
    side, ln = ENC_MODULE[name]
    x0 = x + side * (hx + 0.05)
    out.append((f"{name} encoder / limit-cam module", plate(min(x0, x0 + side * ln), max(x0, x0 + side * ln),
                                                           y - 0.8, y + 0.8, mp_z + 0.25, Z_SH0 - 0.10)))
    return out


# Measurement board (Rev 3.7c, kicad/measurement.kicad_pcb, log 10.4): 100 x 74 mm on edge, its back
# 0.3 in off the partition, centered under J-S. Component side toward +X; seen from it the board's
# left edge is at -Y and its top is up, so KiCad x runs along +Y and KiCad y down -Z.
Z_SAMP_BASE = Z_FLOOR + 0.25 + T12               # top of the sampler baseplate
MEAS_W, MEAS_H = 100 / 25.4, 74 / 25.4
MEAS_X = X_PART + T12 + 0.4                      # board back face
MEAS_Y0 = 3.2 - MEAS_W / 2                       # left (-Y) edge, centered on J-S
MEAS_Z0 = Z_SAMP_BASE + 0.2                      # bottom edge


def meas_pt(xk, yk):
    """KiCad board mm (from the top-left corner, y down) -> enclosure (y, z), inches."""
    return MEAS_Y0 + xk / 25.4, MEAS_Z0 + MEAS_H - yk / 25.4


MEAS_SMA_X = MEAS_X + 0.062 + 0.06               # edge-SMA centerline, just above the component face
MEAS_SMA_Z = {"J1": meas_pt(95.39, 14.6)[1], "J2": meas_pt(95.39, 59.4)[1], "J3": meas_pt(4.61, 14.6)[1]}
MEAS_PLUG = 0.95                                 # SMA body past the edge + mated plug and cable exit
MEAS_J4 = (meas_pt(31.0, 0)[0], meas_pt(64.0, 0)[0], meas_pt(0, 12.4)[1], meas_pt(0, 3.0)[1])   # y0, y1, z0, z1
MEAS_CAL_TAP = meas_pt(11.79, 64.2)              # wire pad for the cal-load tap (6B.3a)

# Coupler box (Rev 3.7c, log 6A.3b / 10.3): Hammond 1590A on the baseplate between the coax input
# (floor G) and K1. SO-239 in on its -Y end and out on its +Y end; the FWD / REF SMA jacks on its
# top near the +Y end, for the two equal-length RG-316 jumpers to the board's J1 / J2.
CPL_L, CPL_W, CPL_H = 3.646, 1.516, 1.22
CPL_X0, CPL_Y0 = 5.0, -4.6
CPL_IN = (CPL_X0 + CPL_W / 2, CPL_Y0, Z_SAMP_BASE + CPL_H / 2)            # SO-239 faces, centers
CPL_OUT = (CPL_X0 + CPL_W / 2, CPL_Y0 + CPL_L, Z_SAMP_BASE + CPL_H / 2)
CPL_SMA = {"FWD": (CPL_X0 + 0.45, CPL_Y0 + CPL_L - 0.45, Z_SAMP_BASE + CPL_H),
           "REF": (CPL_X0 + CPL_W - 0.45, CPL_Y0 + CPL_L - 0.45, Z_SAMP_BASE + CPL_H)}


def sampler():
    """Fixed sampler baseplate with reference envelopes; serviced in place via the left lower panel."""
    x0, x1 = X_PART + T12 + 0.1, X_IN - 0.15
    base = plate(x0, x1 - 0.15, -6.6, 6.6, Z_FLOOR + 0.25, Z_FLOOR + 0.25 + T12)   # rear edge clear of the
    # bottom-rear junction clips (E-201); the parts on it keep their positions
    for t, _k, x, y, _sz, _nt in FLOOR_IO:           # clearance over the floor connectors below
        if x > X_PART and t in FLOOR_BODY:
            _kind, wy, dx, _h = FLOOR_BODY[t]
            base -= plate(x - dx / 2 - 0.15, x + dx / 2 + 0.15, y - wy / 2 - 0.15, y + wy / 2 + 0.15, 0, 1)
    zb = Z_SAMP_BASE
    # (the input choke left this chamber in Rev 3.7c: its deck side must not cross grounded bulkheads, see choke())
    # board, tallest part 0.45 in (the 100 uF); the J-S ribbon's IDC socket on J4; each edge SMA's plug
    out = [("sampler baseplate", base),
           ("measurement board envelope", plate(MEAS_X, MEAS_X + 0.55, MEAS_Y0, MEAS_Y0 + MEAS_W,
                                                MEAS_Z0, MEAS_Z0 + MEAS_H)),
           ("measurement board J4 plug envelope", plate(MEAS_X + 0.55, MEAS_X + 0.8, MEAS_J4[0], MEAS_J4[1],
                                                        MEAS_J4[2], MEAS_J4[3]))]
    for ref, z in MEAS_SMA_Z.items():
        y0 = MEAS_Y0 + MEAS_W if ref != "J3" else MEAS_Y0 - MEAS_PLUG
        out.append((f"measurement board {ref} plug envelope",
                    plate(MEAS_SMA_X - 0.25, MEAS_SMA_X + 0.25, y0, y0 + MEAS_PLUG, z - 0.25, z + 0.25)))
    out.append(("coupler box envelope", plate(CPL_X0, CPL_X0 + CPL_W, CPL_Y0, CPL_Y0 + CPL_L, zb, zb + CPL_H)))
    relays = [plate(x1 - 2.6, x1 - 0.6, y0, y0 + 2.0, zb, zb + 2.3) for y0 in (1.0, 3.4)]
    return out + [("K1 envelope", relays[0]), ("K2 envelope", relays[1])]


def choke():
    """Input choke (§6, Rev 3.7c) on its all-insulating mount, in the RF bay under the deck at the shelf crossing.

    Three G10 standoffs (8-32 up through the shelf) carry a G10 base disc; the winding's bottom crossings sit on a
    silicone pad; a 1/2-13 FRP rod through the open bore center and a G10 spider over the top crossings clamp it."""
    out = []
    z = Z_SH1
    for i in range(3):
        a = math.radians(90 + 120 * i)
        out.append(("choke standoff", Pos(CHOKE_X + CHOKE_BC / 2 * math.cos(a), CHOKE_Y + CHOKE_BC / 2 * math.sin(a), z)
                    * rod(0.375, CHOKE_SO)))
    rod_d, nut_d = CHOKE_ROD
    z_bot_nut = z + CHOKE_SO - CHOKE_NUT
    z += CHOKE_SO
    base = Pos(CHOKE_X, CHOKE_Y, z) * rod(CHOKE_BASE_D, CHOKE_BASE)
    for i in range(6):                              # vent holes inside the open bore center
        a = math.radians(30 + 60 * i)
        base -= Pos(CHOKE_X + 0.36 * math.cos(a), CHOKE_Y + 0.36 * math.sin(a), 0) * Cylinder(0.075, 60)
    # nylon 8-32 flat heads down into the standoffs, countersunk flush: the bottom crossings sit right over
    # them, so no metal head (a floating electrode next to kV turns) and nothing standing proud of the disc
    csk_d, csk_h = CHOKE_CSK
    for i in range(3):
        a = math.radians(90 + 120 * i)
        hx, hy = CHOKE_X + CHOKE_BC / 2 * math.cos(a), CHOKE_Y + CHOKE_BC / 2 * math.sin(a)
        base -= Pos(hx, hy, 0) * Cylinder(0.177 / 2, 60)
        base -= Pos(hx, hy, z + CHOKE_BASE - csk_h) * Cone(0.177 / 2, csk_d / 2, csk_h,
                                                          align=(Align.CENTER, Align.CENTER, Align.MIN))
    out.append(("choke base", base - Pos(CHOKE_X, CHOKE_Y, 0) * Cylinder(rod_d / 2 + 0.01, 60)))
    z += CHOKE_BASE + CHOKE_PAD
    winding = Pos(CHOKE_X, CHOKE_Y, z) * (rod(CHOKE_OD, CHOKE_H) - Pos(0, 0, -0.01) * rod(CHOKE_BORE, CHOKE_H + 0.02))
    out.append(("choke winding envelope", winding))
    z += CHOKE_H + CHOKE_PAD
    t_sp = CHOKE_SPIDER[1]
    r_end = CHOKE_SPIDER[0] / 2 - CHOKE_ARM / 2     # arm-end centers: round ends reach the tip circle
    sp = rod(CHOKE_HUB, t_sp)
    for i in range(3):                              # arms between the standoffs
        arm = Pos(r_end / 2, 0, t_sp / 2) * Box(r_end, CHOKE_ARM, t_sp) + Pos(r_end, 0, 0) * rod(CHOKE_ARM, t_sp)
        sp += Rot(0, 0, 30 + 120 * i) * arm
    spider = Pos(CHOKE_X, CHOKE_Y, z) * sp
    out.append(("choke spider", spider - Pos(CHOKE_X, CHOKE_Y, 0) * Cylinder(rod_d / 2 + 0.01, 60)))
    z += CHOKE_SPIDER[1]
    nut = rod(nut_d, CHOKE_NUT) - Pos(0, 0, -0.01) * rod(rod_d + 0.002, CHOKE_NUT + 0.02)
    out.append(("choke nut", Pos(CHOKE_X, CHOKE_Y, z) * nut))
    out.append(("choke nut", Pos(CHOKE_X, CHOKE_Y, z_bot_nut) * nut))
    out.append(("choke rod", Pos(CHOKE_X, CHOKE_Y, z_bot_nut) * rod(rod_d, z + CHOKE_NUT - z_bot_nut)))
    return out


# ---- the choke turn by turn, for TUNER-E-216 (§6). choke() keeps the winding as an envelope for the
# interference checks; this draws what goes inside it.


def choke_detail():
    """[(item, name, shape)] in place: the mount from choke() with the envelope replaced by five cores and
    fifteen turns, plus the leads, silicone pads and screws. Item numbers key the E-216 parts list."""
    parts = {n: [] for n in ("choke standoff", "choke base", "choke spider", "choke nut", "choke rod")}
    for n, s in choke():
        if n in parts:
            parts[n].append(s)
    z_w0 = Z_SH1 + CHOKE_SO + CHOKE_BASE + CHOKE_PAD           # bottom of the winding envelope
    zc0 = z_w0 + CHOKE_R_BEND + RG400_D / 2                     # bottom face of the core stack
    hc = CHOKE_CORES * CHOKE_CORE_H
    out = [(1, "core", Pos(CHOKE_X, CHOKE_Y, zc0 + i * CHOKE_CORE_H)
            * (rod(FT240[0], CHOKE_CORE_H) - Pos(0, 0, -0.01) * rod(FT240[1], CHOKE_CORE_H + 0.02)))
           for i in range(CHOKE_CORES)]
    # one turn: up the bore, over the top face, down the outside, under the bottom face. Rods and half-tori
    # only (no sweeps), so a section cuts clean circles. Drawn as closed loops at a fixed angle.
    r_mid, tube = (CHOKE_R_IN + CHOKE_R_OUT) / 2, RG400_D / 2
    turn = (Pos(CHOKE_R_IN, 0, 0) * rod(RG400_D, hc) + Pos(CHOKE_R_OUT, 0, 0) * rod(RG400_D, hc)
            + Pos(r_mid, 0, hc) * Rot(90, 0, 0) * Torus(CHOKE_R_BEND, tube, major_angle=180, align=None)
            + Pos(r_mid, 0, 0) * Rot(-90, 0, 0) * Torus(CHOKE_R_BEND, tube, major_angle=180, align=None))
    angles = [(k - (CHOKE_TURNS - 1) / 2) * CHOKE_PITCH for k in range(CHOKE_TURNS)]   # gap centered on -X
    out += [(2, "turn", Pos(CHOKE_X, CHOKE_Y, zc0) * Rot(0, 0, a) * turn) for a in angles]
    # leads off the first and last turns, both toward -X: the chassis lead down to the shelf coax
    # bulkhead, the deck lead up to C1 (§6, harness W18)
    rb, run = 0.35, 0.55
    for a, z, down, end in ((angles[0], zc0, True, Z_SH1 + 0.45), (angles[-1], zc0 + hc, False, R.Z_DECK - 0.35)):
        x0 = CHOKE_X + CHOKE_R_OUT * math.cos(math.radians(a))
        y0 = CHOKE_Y + CHOKE_R_OUT * math.sin(math.radians(a))
        xe = x0 - run
        lead = Pos(xe, y0, z) * Rot(0, -90, 0) * rod(RG400_D, run)
        if down:
            lead += Pos(xe, y0, z - rb) * Rot(90, 0, 0) * Rot(0, 0, 90) * Torus(rb, tube, major_angle=90, align=None)
            lead += Pos(xe - rb, y0, end) * rod(RG400_D, z - rb - end)
        else:
            lead += Pos(xe, y0, z + rb) * Rot(90, 0, 0) * Rot(0, 0, 180) * Torus(rb, tube, major_angle=90, align=None)
            lead += Pos(xe - rb, y0, z + rb) * rod(RG400_D, end - z - rb)
        out.append((2, "lead", lead))
    out += [(3, "base disc", s) for s in parts["choke base"]]
    out += [(4, "standoff", s) for s in parts["choke standoff"]]
    out += [(5, "spider", s) for s in parts["choke spider"]]
    out += [(6, "rod", s) for s in parts["choke rod"]]
    out += [(7, "nut", s) for s in parts["choke nut"]]
    pad = rod(CHOKE_OD, CHOKE_PAD) - Pos(0, 0, -0.01) * rod(CHOKE_BORE, CHOKE_PAD + 0.02)
    out += [(8, "pad", Pos(CHOKE_X, CHOKE_Y, z) * pad) for z in (z_w0 - CHOKE_PAD, z_w0 + CHOKE_H)]
    (d9, l9), (d10, l10) = CHOKE_SCREWS
    csk_d, csk_h = CHOKE_CSK
    z_base_top = Z_SH1 + CHOKE_SO + CHOKE_BASE
    for i in range(3):
        a = math.radians(90 + 120 * i)
        hx, hy = CHOKE_X + CHOKE_BC / 2 * math.cos(a), CHOKE_Y + CHOKE_BC / 2 * math.sin(a)
        head = Pos(hx, hy, z_base_top - csk_h) * Cone(d9 / 2, csk_d / 2, csk_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        out.append((9, "flat head", head + Pos(hx, hy, z_base_top - l9) * rod(d9, l9 - csk_h)))
        out.append((10, "shelf screw", Pos(hx, hy, Z_SH0 - 0.10) * rod(0.30, 0.10)
                    + Pos(hx, hy, Z_SH0) * rod(d10, l10)))
    return out


CHOKE_ITEMS = {   # E-216 parts list: description, qty, material / part, reference
    1: ("FERRITE CORE 61.0 x 35.6 x 12.7, RTV-BONDED STACK", "5", "FAIR-RITE 5961003801 (FT-240-61)", "6"),
    2: ("WINDING, 15 T, LEADS AS NOTE 4", "9.6 ft", "RG-400 (M17/128), ORDER 12 ft", "6, W18"),
    3: ("BASE DISC ⌀3.40 x 1/4", "1", "G10", "E-209"),
    4: ("STANDOFF ⌀3/8 x 5/8, 8-32 F-F", "3", "G10", "E-207"),
    5: ("SPIDER, 3 ARMS, 1/8", "1", "G10", "E-209"),
    6: ("THREADED ROD 1/2-13", "1", "FIBERGLASS (FRP)", "-"),
    7: ("NUT 1/2-13", "2", "FRP", "-"),
    8: ("PAD ⌀2.81 / ⌀0.96 x 1/16", "2", "SILICONE SHEET", "-"),
    9: ("FLAT HEAD 82° 8-32 x 1/2", "3", "NYLON", "-"),
    10: ("PAN HEAD 8-32 x 3/8", "3", "STAINLESS", "-"),
    11: ("LACING CORD", "AR", "PTFE", "NOTE 4"),
    12: ("TAPE / RTV", "AR", "GLASS CLOTH / HIGH-TEMP RTV", "NOTE 2"),
}


def export_choke_detail():
    """TUNER-E-216 sources: the choke half-sectioned (front-right quarter removed, seen from -Y), sectioned
    at mid-winding (seen from above), each with its hatching, and exploded along its axis. Returns the parts list and balloon anchors (mm)."""
    det = choke_detail()
    screws = Compound([s for i, _, s in det if i in (9, 10)])
    det = [(i, n, s - screws if n == "standoff" else s) for i, n, s in det]   # tapped: screws show engaged
    stub = 2.3
    shelf = plate(CHOKE_X - stub, CHOKE_X + stub, CHOKE_Y - stub, CHOKE_Y + stub, Z_SH0, Z_SH1)
    deck = plate(CHOKE_X - stub, CHOKE_X + stub, CHOKE_Y - stub, CHOKE_Y + stub, R.Z_DECK, R.Z_DECK + R.DECK_T)
    quarter = Pos(CHOKE_X + 5, CHOKE_Y - 5, 5) * Box(10, 10, 20)
    cut = [c for c in ((s - quarter) for s in [s for _, _, s in det] + [shelf, deck]) if c.volume > 1e-9]
    export_step(mm(Compound(cut)), str(OUT / "enc-choke-halfsection.step"))
    export_step(mm(R.hatch_overlay(cut, (0, -1, 0), (0, CHOKE_Y, 0), 1.6 / 25.4)), str(OUT / "hatch-choke.step"))
    # section B-B at mid-winding, looking down: the turns packed at the bore, the gap toward -X
    z_cut = Z_SH1 + CHOKE_SO + CHOKE_BASE + CHOKE_PAD + CHOKE_H / 2
    below = Pos(CHOKE_X, CHOKE_Y, z_cut - 5) * Box(20, 20, 10)
    cut_b = [c for c in ((s & below) for _, n, s in det if n != "shelf screw") if c.volume > 1e-9]
    export_step(mm(Compound(cut_b)), str(OUT / "enc-choke-plansection.step"))
    export_step(mm(R.hatch_overlay(cut_b, (0, 0, 1), (0, 0, z_cut), 1.6 / 25.4 / 0.75)),
                str(OUT / "hatch-choke-plan.step"))
    # exploded along the axis in assembly order; the rod stands aside
    z_mid = (Z_SH1 + R.Z_DECK) / 2
    lift = {1: 2.6, 2: 2.6, 3: 0.6, 4: 0.0, 5: 4.3, 9: 1.3, 10: -1.3}
    ex, anchors = [], {}
    c45 = math.cos(math.radians(135)), math.sin(math.radians(135))   # toward the iso viewer
    for i, n, s in det:
        top = s.center().Z > z_mid
        v = ((0, -3.2, 1.2) if i == 6 else (0, 0, (4.9 if top else -0.55)) if i == 7
             else (0, 0, (3.7 if top else 1.9)) if i == 8 else (0, 0, lift[i]))
        ex.append(Pos(*v) * s)
        bb = (Pos(*v) * s).bounding_box()
        cx, cy = CHOKE_X + v[0], CHOKE_Y + v[1]
        pt = None
        if i == 3:
            pt = (cx + CHOKE_BASE_D / 2 * c45[0], cy + CHOKE_BASE_D / 2 * c45[1], bb.center().Z)
        elif i == 4 and bb.center().Y > CHOKE_Y + 1:
            pt = (bb.center().X - 0.19 * 0.7071, bb.center().Y + 0.19 * 0.7071, bb.center().Z)
        elif i == 5:
            a = math.radians(150)
            pt = (cx + 1.2 * math.cos(a), cy + 1.2 * math.sin(a), bb.max.Z)
        elif i == 6:
            pt = (cx, cy, bb.max.Z)
        elif (i == 7 or i == 8) and top:
            r = CHOKE_ROD[1] / 2 if i == 7 else CHOKE_OD / 2
            pt = (cx + r * c45[0], cy + r * c45[1], bb.max.Z)
        elif i in (9, 10) and bb.center().Y > CHOKE_Y + 1:
            pt = (bb.center().X, bb.center().Y, bb.max.Z if i == 9 else bb.min.Z)
        if pt and i not in anchors:
            anchors[i] = [round(c * 25.4, 3) for c in pt]
    # cores: the gap (no turns) faces the viewer, so the middle core shows there; the winding: the outer
    # run of the turn nearest the viewer
    zc = Z_SH1 + CHOKE_SO + CHOKE_BASE + CHOKE_PAD + CHOKE_H / 2 + lift[2]
    anchors[1] = [round(c * 25.4, 3) for c in (CHOKE_X + FT240[0] / 2 * c45[0], CHOKE_Y + FT240[0] / 2 * c45[1], zc)]
    k = max(range(CHOKE_TURNS), key=lambda k: math.cos(math.radians((k - (CHOKE_TURNS - 1) / 2) * CHOKE_PITCH - 135)))
    a = math.radians((k - (CHOKE_TURNS - 1) / 2) * CHOKE_PITCH)
    anchors[2] = [round(c * 25.4, 3) for c in (CHOKE_X + (CHOKE_R_OUT + RG400_D / 2) * math.cos(a),
                                                 CHOKE_Y + (CHOKE_R_OUT + RG400_D / 2) * math.sin(a), zc + 0.6)]
    export_step(mm(Compound(ex)), str(OUT / "enc-choke-exploded.step"))
    bb = Compound(cut).bounding_box()
    return {"items": {str(k): list(v) for k, v in CHOKE_ITEMS.items()}, "anchors": {str(k): v for k, v in anchors.items()},
            "section_center": [(bb.min.X + bb.max.X) / 2, (bb.min.Z + bb.max.Z) / 2],
            "pitch": CHOKE_PITCH, "bend_mm": CHOKE_R_BEND * 25.4, "core_h": CHOKE_CORE_H}


def wall_flanges():
    out = []
    for sy in (-1, 1):
        heel = (W / 2, sy * W / 2, WF_Z[0])
        ang = angle(heel, (-1, 0, 0), (0, sy, 0), WF_Z[1] - WF_Z[0], (0, 0, 1), a=WF_LEG, b=WF_LEG, t=WF_T)
        # one leg lies on the side panel (bolted through it into the corner post), the other in the
        # wall plane, flush with the rear panel and reaching past the side for the lag slots
        for z in WF_SLOTS:
            ang -= Pos(W / 2 - WF_T / 2, sy * (W / 2 + WF_LEG * 0.6), z) * Box(1, 0.40, 0.75)
        for z in FLANGE_Z:
            ang -= Pos(W / 2 - 0.55, sy * W / 2, z) * Rot(90, 0, 0) * Cylinder(0.105, 1)
        out.append(("wall flange", ang))
    return out


def internals():
    """Roller, caps, deck, standoffs, drive train from roller.install_parts (enclosure parts dropped)."""
    keep = []
    for name, shp in R.install_parts():
        if name in ("floor", "lid", "wall", "shelf", "motor", "coupler A"):
            continue
        keep.append((name, shp))
    for tag in ("C1", "C2"):   # cap drive trains to match the roller's (G10 stub + bushing + coupler B)
        x, y = AXES[tag]
        keep.append((f"{tag} G10 shaft", Pos(x, y, Z_MOTOR_FACE + 0.6) * rod(R.G10_D, R.Z_DECK - 0.3 - (Z_MOTOR_FACE + 0.6))))
        bush = Pos(x, y, R.Z_SHELF) * rod(R.BUSHING_OD, R.SHELF_T) + \
            Pos(x, y, R.Z_SHELF + R.SHELF_T) * rod(R.BUSHING_FLANGE[0], R.BUSHING_FLANGE[1])
        keep.append((f"{tag} bushing", bush - Pos(x, y, 0) * rod(R.G10_D + 0.002, 60)))
    return keep + choke()


# input choke, Rev 3.7c (§6): 15 t RG-400 on 5 x FT-240-61, axis vertical, under the deck near the shelf coax
CHOKE_X, CHOKE_Y = -1.5, -1.0
CHOKE_TURNS, CHOKE_CORES = 15, 5
CHOKE_OD, CHOKE_H = 2.81, 3.47                   # winding envelope: core OD + 2 coax + tape; worst-case height
CHOKE_BORE = 0.96                                # open center left by one layer of turns (worst-case bore)
CHOKE_TURN_LEN = 2 * CHOKE_CORES * 0.5 + math.pi * (0.501 + 0.195)   # in per turn: core stack + arcs over the faces
CHOKE_SO, CHOKE_BASE, CHOKE_PAD = 0.625, 0.25, 0.0625   # G10 standoffs, G10 base disc, silicone pads
CHOKE_BASE_D, CHOKE_BC = 3.40, 2.60              # base disc, standoff bolt circle
CHOKE_SPIDER = (2.60, 0.125)                     # G10 three-arm spider: tip circle, thickness
CHOKE_HUB, CHOKE_ARM = 1.00, 0.50                # spider hub dia, arm width (round ends)
CHOKE_CSK = (0.34, 0.094)                        # 82 deg countersink for #8 flat heads: dia, depth
CHOKE_ROD, CHOKE_NUT = (0.50, 0.85), 0.44        # FRP 1/2-13 rod dia, nut across corners; nut height
# the choke turn by turn (choke_detail(), TUNER-E-216)
FT240 = (2.402, 1.400)                            # Fair-Rite 5961003801 (FT-240-61): OD, ID
RG400_D, CHOKE_TAPE = 0.195, 0.010                # coax OD; glass-cloth tape on the bore and core edges
CHOKE_R_IN = FT240[1] / 2 - CHOKE_TAPE - RG400_D / 2      # turn centerline up the bore, against the wall
CHOKE_R_OUT = FT240[0] / 2 + CHOKE_TAPE + RG400_D / 2     # and down the outside
CHOKE_R_BEND = (CHOKE_R_OUT - CHOKE_R_IN) / 2             # arc over each face (§6: ~8.8 mm centerline)
# cores drawn at the height that makes the turns fill the worst-case envelope exactly
CHOKE_CORE_H = (CHOKE_H - 2 * (CHOKE_R_BEND + RG400_D / 2)) / CHOKE_CORES
CHOKE_PITCH = math.degrees(RG400_D / CHOKE_R_IN)          # turns packed side by side at the bore
CHOKE_SCREWS = ((0.164, 0.50), (0.164, 0.375))            # nylon 8-32 flat heads; SS 8-32 up through the shelf
FLOOR_BODY = {  # inside body above the floor per FLOOR_IO tag: (kind, w_y, d_x, h) incl. mating plug / tail zone
    "A": ("box", 1.14, 1.30, 1.50),   # IEC body 29 x 33 mm + quick-connect tabs - ASSUMED depth
    "B": ("box", 1.00, 1.00, 2.40),   # RJ45 coupler + patch-cord plug from above
    "C": ("cyl", 0.45, 0.45, 0.20), "D": ("cyl", 0.45, 0.45, 0.20),   # snap bushings
    "E": ("cyl", 0.63, 0.63, 0.50), "F": ("cyl", 0.63, 0.63, 0.50), "K": ("cyl", 0.63, 0.63, 0.50),  # vent + nut
    "G": ("cyl", 0.625, 0.625, 0.95), "H": ("cyl", 0.625, 0.625, 0.95),   # 5/8 rear body + tail, coax leaves sideways
    "J": ("box", 0.40, 0.90, 0.70),   # termination body + tab / jumper zone
}


def fixtures():
    """Populated-cabinet bodies that are not structure: floor connector bodies inside, exterior blower,
    intake filter, cal-load heatsink, and the ASSUMED driver-board placeholder. Used by the interference check and the populated drawing."""
    out = []
    zf = Z_FLOOR
    for t, _k, x, y, _sz, nt in FLOOR_IO:
        if t not in FLOOR_BODY:
            continue
        kind, wy, dx, h = FLOOR_BODY[t]
        shp = (Pos(x, y, zf) * Cylinder(wy / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN)) if kind == "cyl"
               else plate(x - dx / 2, x + dx / 2, y - wy / 2, y + wy / 2, zf, zf + h))
        out.append((f"floor {t} body", shp))
    jx, jy = next((x, y) for t, _k, x, y, _s, _n in FLOOR_IO if t == "J")
    out.append(("cal-load heatsink", plate(jx - 2.375, jx + 2.375, jy - 2.75, jy + 2.75, -4.5, 0)))   # 441K, fins down
    yb = W / 2 + T14
    bx, bz = BLOWER["x"], BLOWER["z"]
    out.append(("blower", plate(bx - 2.36, bx + 2.36, yb, yb + 1.5, bz - 2.36, bz + 2.36)))           # 120 x 38 mm
    out.append(("intake filter", plate(INTAKE["x"] - INTAKE["w"] / 2 - 0.3, INTAKE["x"] + INTAKE["w"] / 2 + 0.3,
                                       -yb - 0.75, -yb, INTAKE["z"] - INTAKE["h"] / 2 - 0.3,
                                       INTAKE["z"] + INTAKE["h"] / 2 + 0.3)))
    fx, fz = FAN_ENTRY                                    # blower-lead DE-9: harness inside, plug + conduit outside
    out.append(("fan entry harness envelope", plate(fx - 0.7, fx + 0.7, F - 0.65, F - 0.01, fz - 0.35, fz + 0.35)))
    out.append(("fan entry plug envelope", plate(fx - 0.7, fx + 0.7, yb + 0.01, yb + 1.3, fz - 0.4, fz + 0.4)))
    out.append(("driver board envelope", plate(-3.2, 2.8, 2.0, 6.0, zf + 0.12, zf + 0.92)))   # ASSUMED, 3 axes, under the motors
    # RF service-panel interlock (7.4, Rev 3.7c): reed sensor on the inner face of the front shelf-ring flange,
    # between two of the panel's rivnuts; its magnet on the panel's inner face just above the flange
    sy = PANEL_SW_Y
    out.append(("RF panel switch", plate(-F + ANG_T, -F + ANG_T + 0.25, sy - 0.475, sy + 0.475, Z_SH1 + 0.74, Z_SH1 + 0.99)))
    out.append(("RF panel switch magnet", plate(-F, -F + 0.236, sy - 0.453, sy + 0.453, Z_SH1 + 1.06, Z_SH1 + 1.296)))
    # pad doorknob, link coil and their two vacuum relays have no RF-bay position yet (9 item 42): not modeled
    return out


def harness():
    """Keep-out envelopes for mated plugs and solder-cup harnesses at the bulkhead and partition."""
    out = []
    for name, x_plate, io, mate in (("bulkhead", X_BULK, BULKHEAD_IO, -1), ("partition", X_PART, PARTITION_IO, -1)):
        for t, kind, y, z, size, _nt in io:
            hw, hh = ((size[0] / 2 + 0.25, 0.4) if kind == "dsub" else (0.25, 0.25))
            for side, depth in ((mate, 1.3 if kind == "dsub" else 0.6), (-mate, 0.8 if kind == "dsub" else 0.6)):
                xa = x_plate - 0.01 if side < 0 else x_plate + T12 + 0.01
                out.append((f"{name} {t} {'plug' if side == mate else 'harness'} envelope",
                            plate(min(xa, xa + side * depth), max(xa, xa + side * depth), y - hw, y + hw, z - hh, z + hh)))
    return out


def rivnut_envelopes():
    """[(panel, (u, v), shape)]: the blind-side body of each panel-hole rivnut behind its 1/8 frame flange."""
    out = []
    for p in panels():
        for u, v in p.fastener_holes():
            c = p.p3(u, v, p.t + ANG_T + 0.175)
            out.append((p.name, (u, v), Pos(c.X, c.Y, c.Z) * _rot_to(p.n) * Cylinder(0.225, 0.35)))
    return out


def orphan_holes():
    """Panel fastener holes with no frame metal in the 0.10" behind the panel (bulkhead / partition excluded:
    their 1/2 clip angles are match-drilled, not modeled)."""
    fr = [(s, s.bounding_box()) for _n, s in frame()] + [(s, s.bounding_box()) for _n, s in clips(drilled=False)]
    out = []
    for p in panels():
        if p.name in ("bulkhead", "motor/sampler partition"):
            continue
        for u, v in p.fastener_holes():
            m = p.p3(u, v, p.t + 0.07)
            probe = Pos(m.X, m.Y, m.Z) * _rot_to(p.n) * Cylinder(0.02, 0.10)
            if not any(bb.min.X - 0.1 < m.X < bb.max.X + 0.1 and bb.min.Y - 0.1 < m.Y < bb.max.Y + 0.1
                       and bb.min.Z - 0.1 < m.Z < bb.max.Z + 0.1 and (probe & s).volume > 1e-6 for s, bb in fr):
                out.append((p.name, round(u, 3), round(v, 3)))
    return out


def assembly():
    parts = frame() + clips()
    parts += [(p.name, p.shape()) for p in panels()]
    parts += cassette()
    for tag, (x, y) in AXES.items():
        parts += axis_module(tag, x, y)
    parts += sampler()
    parts += wall_flanges()
    parts += wall_clips()
    return parts


def check(parts, skip_pairs=()):
    import itertools
    bad = []
    for (n1, s1), (n2, s2) in itertools.combinations(parts, 2):
        a, b = s1.bounding_box(), s2.bounding_box()
        if a.max.X < b.min.X or b.max.X < a.min.X or a.max.Y < b.min.Y or b.max.Y < a.min.Y or \
                a.max.Z < b.min.Z or b.max.Z < a.min.Z:
            continue
        v = (s1 & s2).volume
        shaft_in_coupler = ("coupler A" in n1 + n2) and ("G10" in n1 + n2)   # G10 seated in its bore
        if abs(v) > 1e-5 and not shaft_in_coupler:
            bad.append((n1, n2, round(v, 4)))
    return bad


# ------------------------------------------------------------------ cut list and nesting
KERF = 0.125
STOCK = [(36, 48), (48, 48), (48, 96)]           # common 5052 sheet sizes, W x L


def flat_parts():
    """(name, gauge, w, h) for every sheet-metal part, flat. Axis-bracket and tray blanks include bends."""
    out = [(p.name, p.gauge, p.L, p.H) for p in panels()]
    out.append(("deck (L-109)", "12 GA", R.DECK_SIZE, R.DECK_SIZE))
    x0, x1 = -X_IN + SANG + 0.02, X_BULK - 0.15
    out.append(("cassette tray", "12 GA", x1 - x0, F - ANG - 0.15 + Y_STRIP))
    out.append(("sampler baseplate", "12 GA", X_IN - 0.15 - (X_PART + T12 + 0.1), 13.2))
    blank = (MOTOR_SQ + 0.04, 3.0 + 2 * (Z_SH0 - Z_MOTOR_FACE))   # top + two sides + motor plate, unfolded
    for tag in AXES:
        out.append((f"{tag} axis bracket (blank)", "1/8 6061", *blank))
    return out


def nest(parts, sheet):
    """Shelf packing: rows across the sheet width, tallest first. Returns placements or None."""
    sw, sl = sheet
    rows, y, placed = [], 0.0, []
    for name, w, h in sorted(parts, key=lambda p: -max(p[1], p[2])):
        w, h = (w, h) if w >= h else (h, w)          # long side across the sheet
        if w > sw:
            w, h = h, w
        if w > sw or h > sl:
            return None
        for row in rows:
            if row["x"] + w <= sw and h <= row["h"]:
                placed.append((name, row["x"], row["y"], w, h))
                row["x"] += w + KERF
                break
        else:
            if y + h > sl:
                return None
            rows.append({"x": w + KERF, "y": y, "h": h})
            placed.append((name, 0.0, y, w, h))
            y += h + KERF
    return placed


def nesting():
    """{gauge: (sheet, placements, used area)} choosing the smallest stock sheet that holds the set."""
    res = {}
    groups = {}
    for name, gauge, w, h in flat_parts():
        if gauge.startswith("1/8"):
            continue
        groups.setdefault(gauge, []).append((name, w, h))
    for gauge, items in groups.items():
        for sheet in STOCK:
            pl = nest(items, sheet)
            if pl:
                res[gauge] = (sheet, pl, sum(w * h for _, w, h in items))
                break
    return res


def mm(shape):
    return shape.scale(25.4)


def main():
    parts = assembly()
    inner = internals()
    report = {
        "cassette component height limit": round(CASS_CLEAR, 3),
        "C1 motor to bulkhead": round(AXES["C1"][0] - MOTOR_SQ / 2 - (X_BULK + T12), 3),
        "C2 motor to partition": round(X_PART - (AXES["C2"][0] + MOTOR_SQ / 2), 3),
        "intake area (in2)": INTAKE["w"] * INTAKE["h"],
        "aluminum weight, enclosure (lb)": round(sum(s.volume for n, s in parts
                                                      if "envelope" not in n and not n.endswith("motor")) * 0.0975, 1),
    }
    ch = {}
    for n, s in choke():
        ch.setdefault(n, s)
    wb = ch["choke winding envelope"].bounding_box()
    report["choke winding above the shelf"] = round(wb.min.Z - Z_SH1, 3)
    report["choke winding below the deck"] = round(R.Z_DECK - wb.max.Z, 3)
    report["choke rod length"] = round(max(s.bounding_box().max.Z for n, s in choke() if n == "choke rod")
                                       - min(s.bounding_box().min.Z for n, s in choke() if n == "choke rod"), 2)
    # frame junctions: no panel rivnut may sit under a clip, and every panel hole needs frame metal behind it
    cl_bb = [(c, c.bounding_box()) for _n, c in clips()]
    hits = []
    for pn, (u, v), s in rivnut_envelopes():
        sb = s.bounding_box()
        for c, cb in cl_bb:
            if (sb.max.X > cb.min.X and cb.max.X > sb.min.X and sb.max.Y > cb.min.Y and cb.max.Y > sb.min.Y
                    and sb.max.Z > cb.min.Z and cb.max.Z > sb.min.Z and (s & c).volume > 1e-6):
                hits.append(f"{pn} {u:.2f},{v:.2f}")
    report["junction screws"] = len(junction_holes())
    report["clip / rivnut conflicts"] = hits
    report["panel holes with no frame behind"] = orphan_holes()
    export_step(mm(Compound([s for _, s in parts])), str(OUT / "enc-assembly.step"))
    export_step(mm(Compound([s for _, s in parts] + [s for _, s in inner])), str(OUT / "enc-with-internals.step"))
    opened = ("RF service panel", "left upper panel", "left lower panel")
    export_step(mm(Compound([s for n, s in parts if n not in opened] + [s for _, s in inner])),
                str(OUT / "enc-cutaway.step"))
    # per-part STEPs for the drawings (true size, in their assembled position)
    def slug(n):
        return n.replace("/", "-").replace(" ", "-")
    P = panels()
    for p in P:
        export_step(mm(p.shape()), str(OUT / f"enc-panel-{slug(p.name)}.step"))
    export_step(mm(Compound([s for n, s in frame() + clips()])), str(OUT / "enc-frame.step"))
    # junction detail (E-201): bottom ring, rear-left corner, cut to stubs, with screws and nylocs; and the clips
    for name, explode in (("enc-frame-joint", False), ("enc-frame-joint-exploded", True)):
        export_step(mm(Compound(junction_detail(explode))), str(OUT / f"{name}.step"))
    cl = clips()
    std = next(s for s in cl if s[1].bounding_box().min.X > 0 and s[1].bounding_box().min.Y > 0)[1]
    short = next(s for s in cl if s[1].bounding_box().max.X < 0 and s[1].bounding_box().max.Y < 0)[1]
    leg, t, L = WCLIP                                # bulkhead clip (E-208), heel at the origin, length along Y
    mid = t + (leg - t) / 2
    wc = angle((0, 0, 0), (1, 0, 0), (0, 0, 1), L, (0, 1, 0), a=leg, b=leg, t=t)
    wc -= Pos(mid, L / 2, t / 2) * Cylinder(WCLIP_HOLE / 2, 1)
    wc -= Pos(t / 2, L / 2, mid) * Rot(0, 90, 0) * Cylinder(WCLIP_TAP / 2, 1)
    export_step(mm(wc), str(OUT / "enc-wall-clip.step"))
    det = wall_clip_detail()                         # control face x = 0, floor top z = 0, shelf underside z = h
    h = Z_SH0 - Z_FLOOR
    for name, box in (("floor", plate(-0.7, 1.0, 0, 1, -0.3, 0.9)),               # y >= 0: cut on the screw plane,
                      ("shelf", plate(-0.7, 1.0, 0, 1, h - 0.9, h + R.SHELF_T + 0.3))):   # seen from -Y it reads as a section
        cut = [s & box for s in det]
        export_step(mm(Compound([s for s in cut if s.volume > 1e-9])), str(OUT / f"enc-wall-clip-{name}.step"))
    for name, s in (("enc-corner-clip", std), ("enc-corner-clip-short", short)):
        bb = s.bounding_box()
        export_step(mm(Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * s), str(OUT / f"{name}.step"))
    named = dict()
    for n, s in parts:
        named.setdefault(n, s)
    for n in ("cassette tray", "cassette rail", "C1 axis bracket", "sampler baseplate", "wall flange"):
        export_step(mm(named[n]), str(OUT / f"enc-{slug(n)}.step"))
    # input choke mount (E-209): base disc, spider, and the stack with shelf / deck stubs for the elevation
    export_step(mm(ch["choke base"]), str(OUT / "enc-choke-base.step"))
    export_step(mm(ch["choke spider"]), str(OUT / "enc-choke-spider.step"))
    stub = 2.3
    ref = [plate(CHOKE_X - stub, CHOKE_X + stub, CHOKE_Y - stub, CHOKE_Y + stub, Z_SH0, Z_SH1),
           plate(CHOKE_X - stub, CHOKE_X + stub, CHOKE_Y - stub, CHOKE_Y + stub, R.Z_DECK, R.Z_DECK + R.DECK_T)]
    export_step(mm(Compound([s for _, s in choke()] + ref)), str(OUT / "enc-choke-assembly.step"))
    choke_meta = export_choke_detail()
    explode = {"RF service panel": (-6, 0, 2), "cassette face": (-9, 0, -1), "cassette tray": (-9, 0, -1),
               "cassette rail": (-9, 0, -1), "rear panel": (6, 0, 0), "top panel": (0, 0, 6), "floor": (0, 0, -6),
               "wall flange": (9, 0, 0), "bulkhead": (-5, 0, -1)}
    ex = []
    for n, s in parts:
        if "envelope" in n:
            continue
        v = explode.get(n)
        if v is None and ("left" in n or "right" in n):
            v = (0, 6 if "left" in n else -6, 0)
        if v is None and ("axis bracket" in n or n.endswith("motor") or "coupler A" in n):
            v = (-3, 0, -2.5)
        ex.append(Pos(*(v or (0, 0, 0))) * s)
    export_step(mm(Compound(ex)), str(OUT / "enc-exploded.step"))
    fr = frame()
    cut_list = {}
    for n, s in fr:
        bb = s.bounding_box()
        length = round(max(bb.size.X, bb.size.Y, bb.size.Z), 3)
        leg = round(sorted([bb.size.X, bb.size.Y, bb.size.Z])[1], 3)
        key = (n, length, leg)
        cut_list[key] = cut_list.get(key, 0) + 1
    nest_res = nesting()
    for gauge, (sheet, pl, area) in nest_res.items():   # nest diagram: sheet outline + part rectangles
        g = gauge.replace(" ", "")
        shapes = [plate(0, sheet[0], 0, sheet[1], -0.02, 0)]
        shapes += [plate(x + 0.02, x + w - 0.02, y + 0.02, y + h - 0.02, 0, 0.01) for _, x, y, w, h in pl]
        export_step(mm(Compound(shapes)), str(OUT / f"enc-nest-{g}.step"))
    rails = X_BULK - 0.15 - (-X_IN + SANG + 0.02)
    extra = [["cassette rail (1/2 x 1/2 x 1/8)", 2, round(rails, 3), SANG],
             ["wall flange (2 x 2 x 3/16)", 2, WF_Z[1] - WF_Z[0], WF_LEG],
             ["corner clip (1-1/2 x 1-1/2 x 1/8)", 16, CLIP_H, CLIP_LEG],
             ["bulkhead / partition clip (1/2 x 1/2 x 1/8)", 16, 1.0, SANG]]
    meta = {"report": report, "panels": [p.meta() for p in P], "choke": choke_meta,
            "frame_extra": extra,
            "nesting": {g: {"sheet": sh, "parts": pl, "area": a} for g, (sh, pl, a) in nest_res.items()},
            "flat_parts": flat_parts(),
            "frame_cut_list": [[n, q, length, leg] for (n, length, leg), q in sorted(cut_list.items())],
            "p": {k: v for k, v in globals().items() if k.isupper() and isinstance(v, (int, float, tuple, dict, list))}}
    json.dump(meta, open(OUT / "enclosure.json", "w"), indent=1, default=str)
    print(json.dumps(report, indent=1))
    print("enclosure clashes:", check(parts + harness() + fixtures()))
    print("with internals:", check(parts + harness() + fixtures() + [(n, s) for n, s in inner if n != "winding"]))


if __name__ == "__main__":
    main()
