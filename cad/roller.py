# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Parametric model of the homebuilt roller inductor (design log §5.3a, Rev 3.7 target).

Inches throughout. Coil axis is +Z (the roller stands upright in the vertical stack);
z = 0 is the outer face of end disc A (bottom, cold end). The bus rod and wiper sit
on the +X side. Values marked ASSUMED are not fixed by the design log.

Writes true-size STEP files (mm) to out/:
  roller.step            assembled, every part
  roller-exploded.step   same parts, exploded for the isometric
  part-<name>.step       each distinct part in its own drawing orientation
and out/parts.json (item list + hole tables) for drawings.py.
Drawings: xvfb-run -a freecad drawings.py
"""
import json
import math
from pathlib import Path

from build123d import (
    Box, Circle, Compound, Cylinder, Edge, Helix, Plane, Pos, Rot, Torus, Vector, export_step, sweep,
)

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

# ---- Winding (§5.3a Rev 3.7 build target) ----
WIRE_D = 0.204          # #4 AWG solid
PITCH = 1 / 3           # 3 TPI
TURNS = 22              # wound: Wheeler 33.8 uH free air, ~32.5 installed (deck) - no series link (Rev 3.7a)
NOTCHES = 24            # notch for 2 spare turns (~+3.4 uH)
COIL_D = 5.20           # to wire center
N_RIBS = 10             # polygon bump r(1 - cos pi/n) = 0.13" if wound under tension - pre-form the wire round

# ---- Rib (§5.3a, rescaled) ----
RIB_T = 0.375
NOTCH_R = 0.110                 # doc ~0.105; 0.110 + seat lets the curved, climbing wire drop in
NOTCH_DEPTH = 0.14
NOTCH_SEAT = 0.015              # notch bottom this far below the wire seat: wire dips ~0.008" at the rib faces
RIB_SOLID = 1.0
RIB_H = NOTCH_DEPTH + RIB_SOLID                 # 1.14
NOTCH_BOTTOM_R = COIL_D / 2 - WIRE_D / 2        # wire rests on notch bottom
RIB_OUTER_R = NOTCH_BOTTOM_R + NOTCH_DEPTH
RIB_INNER_R = RIB_OUTER_R - RIB_H
END_MARGIN = 0.18
STAGGER = PITCH / N_RIBS                # helix advance from one rib to the next
SPAN = (NOTCHES - 1) * PITCH + (N_RIBS - 1) * STAGGER + 2 * NOTCH_R + 2 * END_MARGIN   # between end discs
TAB_LEN = 0.40          # ASSUMED
TAB_H = 0.50            # ASSUMED

# ---- Cage end discs, center hub, tie rods ----
DISC_T = 0.50
DISC_D = round(2 * (RIB_OUTER_R + 0.25) * 8) / 8
SLOT_W = RIB_T + 0.005                  # rib-tab slot, light push fit
SLOT_DEPTH = TAB_LEN + 0.01             # blind, from the inner face
SLOT_R0, SLOT_R1 = RIB_INNER_R - 0.005, RIB_INNER_R + TAB_H + 0.01
TIE_D, TIE_R = 0.375, 0.85              # 3/8" Ultem tie rods on 0.85" radius (§5.3a: inside the rib circle)
TIE_HOLE = 0.391                        # 25/64 clearance
TIE_ANGLES = (45, 135, 225, 315)        # between rib positions, clear of the slots
TERM_HOLE, TERM_R = 0.25, COIL_D / 2    # wire terminal post hole at the winding start
HUB_T = 0.75                            # ASSUMED (doc gives only ~1-3/4" dia for the 3.5" form)
HUB_D = 2 * (RIB_INNER_R + 0.125)       # 1/8"-deep slots key the rib inner edges (§5.3a)
HUB_SLOT_DEPTH = 0.125
SHAFT_D = 0.50
BORE = 0.502                            # Ultem parts slip on the 1/2" shaft; only the hub is pinned
PIN_D, PIN_ANG = 0.125, 18             # brass cross-pin through hub + shaft, between rib slots 0 and 1
WASHER_T, WASHER_OD = 0.031, 1.00      # PTFE thrust washers either side of bearing A
COLLAR_OD = 1.25                       # contact/bond collar: finger track OD, lug face, upper thrust face
COLLAR_GAP = 0.02                      # collar to disc A, room for the cage's thermal growth
THRUST_OD, THRUST_W = 1.125, 0.4375    # standard 1/2" split collar below plate A
OLDHAM_ENGAGE = 0.65                   # shaft below the thrust collar: 0.595 hub engagement + 0.05; a
                                        # longer stub only lowers the brass tip and cuts shelf creepage

# ---- End plates (brackets), vertical stack: A at the bottom, B on top (§5.3a Rev 3.7) ----
PLATE_T = 0.50
PLATE_W = 5.50                          # across Y (coil OD 5.40)
PLATE_L = 7.50                          # along X; 1" past the doc's 6.5 for bus-rod pillar creepage (below)
PLATE_X0 = -2.25                        # plate spans X = -2.25 .. 4.25 (shaft axis 2.25 from the -X end)
GAP_A = 0.75                            # plate A to disc A: contact collar + BeCu fingers (ASSUMED; doc diagram 1")
GAP_B = 0.25                            # disc B to plate B: thrust washer only
R8_OD = 1.125                           # R8 bearing bore (press, A fixed; B sliding on shaft)
BUS_R = COIL_D / 2 + WIRE_D / 2 + 1.25  # bus rod ~1-1/4" outside the wire surface (§5.3a)
BUS_D = 0.375                           # ASSUMED: silver-plated C360 brass
GUIDE_DY = 0.75                         # anti-rotation guide rod beside the bus rod (ASSUMED)
GUIDE_D = 0.375                         # Ultem
POST_D = 0.75                           # Ultem frame posts tie A to B (ASSUMED)
POST_XY = ((2.60, 2.05), (2.60, -2.05)) # outside the disc radius and the wiper's path
POST_TAP = "1/4-20 x 0.75 DP"
ROD_STICKOUT = 0.375                    # bus/guide rod beyond each plate for collar + nut

# ---- Coupler B: Delrin Oldham, roller shaft to 0.375" G10 drive shaft (§7.1a) ----
OLD_OD = 1.000                          # 1" acetal homopolymer rod stock (§10.6)
OLD_HUB_L = 0.75
OLD_SLOT_W, OLD_SLOT_D = 0.3125, 0.125  # 5/16 end mill across each hub face
OLD_TONGUE_W = 0.3115                   # fitted to the slot: 0.0005-0.001 clearance sets backlash (§9 item 21)
OLD_TONGUE_H = 0.115                    # 0.010 short of the slot depth so only the flanks drive
OLD_CORE_T = 0.145                      # center-disc web between the two tongues
OLD_GAP = 0.010                         # hub face to disc web, each side
G10_D = 0.375
OLD_PIN = {"roller": 0.125, "g10": 0.094}   # transverse roll pins (§7.1a: flat + roll pin, never set screws)

# ---- Wiper (§5.3a contact system; all geometry ASSUMED) ----
WHEEL_OD = 0.75
WHEEL_W = 0.375
GROOVE_R = 0.110                        # matched to the 0.204" wire with a little clearance
GROOVE_DEPTH = 0.045                    # flanges reach (wire top - depth); must stay above the rib tops,
                                        # which sit 1/16" under the wire top (§5.3a)
AXLE_D = 0.1875
WIPER_Y = -0.55                         # wheel line, offset so the fork clears the bus-rod bore
FORK_TRAVEL = 0.10                      # radial spring travel between fork bridge and carriage
CARR_Y = (-0.85, GUIDE_DY + 0.30)
CARR_T = 0.75                           # along Z
FORK_BAR = (0.25, 0.50)                 # bar section (Y, Z), slides radially in the carriage
CHEEK_T = 0.0625
CHEEK_GAP = 0.03

z_disc_b = DISC_T + SPAN                       # inner face of disc B
Z_TOP_CAGE = 2 * DISC_T + SPAN
Z_PLATE_A = (-GAP_A - PLATE_T, -GAP_A)
Z_PLATE_B = (Z_TOP_CAGE + GAP_B, Z_TOP_CAGE + GAP_B + PLATE_T)
INNER_SPAN = Z_PLATE_B[0] - Z_PLATE_A[1]       # plate to plate
COLLAR_Z = (Z_PLATE_A[1] + WASHER_T, -COLLAR_GAP)
THRUST_Z = (Z_PLATE_A[0] - WASHER_T - THRUST_W, Z_PLATE_A[0] - WASHER_T)
SHAFT_Z = (THRUST_Z[0] - OLDHAM_ENGAGE, Z_PLATE_B[1] + 0.25)
SHAFT_LEN = round((SHAFT_Z[1] - SHAFT_Z[0]) * 8) / 8
SHAFT_Z = (SHAFT_Z[0], SHAFT_Z[0] + SHAFT_LEN)
ROD_Z = (Z_PLATE_A[0] - ROD_STICKOUT, Z_PLATE_B[1] + ROD_STICKOUT)
ROD_LEN = ROD_Z[1] - ROD_Z[0]
# Guide rod (Ultem): threads into a blind tapped hole in plate A, so plate A's underside sits flat on
# the deck; passes through plate B with a PEEK nut on top.
GUIDE_TAP, GUIDE_TAP_DP = 0.3125, 0.40           # 3/8-16 tap drill / thread depth
GUIDE_Z0 = Z_PLATE_A[1] - GUIDE_TAP_DP
GUIDE_LEN = ROD_Z[1] - GUIDE_Z0
# Bus rod (hot, up to 9.3 kV pk to the deck) spans only the wheel's travel and stands on Ultem pillars:
# §3.2 wants >= 1.5" air and >= 2.0" creepage from it to the deck, and to the lid.
Z_W0 = DISC_T + END_MARGIN + NOTCH_R           # first turn center
Z_WTOP = Z_W0 + (NOTCHES - 1) * PITCH + (N_RIBS - 1) * PITCH / N_RIBS   # highest notch
BUS_Z = (Z_W0 - CARR_T / 2 - 0.10, Z_WTOP + CARR_T / 2 + 0.10)
BUS_LEN = BUS_Z[1] - BUS_Z[0]
PILLAR_D, PILLAR_THREAD_DP = 0.75, 0.40        # Ultem, tapped 3/8-24 for the rod end
PILLAR_STUD = (0.375, PLATE_T)                 # turned stud through the plate, PEEK nut in a counterbore
PILLAR_LO = BUS_Z[0] - Z_PLATE_A[1]            # stands on plate A
PILLAR_HI = Z_PLATE_B[0] - BUS_Z[1]            # hangs from plate B
TIE_RECESS = 0.010                             # short of each disc face so the screws clamp the ribs
TIE_LEN = Z_TOP_CAGE - 2 * TIE_RECESS
HUB_Z = DISC_T + SPAN / 2                      # hub center
PIN_LEN = HUB_D - 0.06                         # 0.03 below the hub surface each side

# wheel sits on the wire: groove bottom on the wire's outer surface
WHEEL_AXIS_R = COIL_D / 2 + WIRE_D / 2 + (WHEEL_OD / 2 - GROOVE_DEPTH)
WHEEL_X = math.sqrt(WHEEL_AXIS_R ** 2 - WIPER_Y ** 2)


def wire_z_at(angle_deg, turn):
    z0 = DISC_T + END_MARGIN + NOTCH_R
    return z0 + PITCH * (turn + (angle_deg % 360) / 360)


WIPER_Z = wire_z_at(math.degrees(math.atan2(WIPER_Y, WHEEL_X)), 8)
BRIDGE_X = WHEEL_X + WHEEL_OD / 2 + 0.08                  # fork bridge, just clear of the wheel rim
CARR_X = (BRIDGE_X + 0.125 + FORK_TRAVEL, BUS_R + 0.40)   # carriage block extent along X


# ------------------------------------------------------------------ parts (local coords)
def rib(n=0):
    """Rib n along X (length), Y thickness 0..RIB_T, notches in the +Z (outer) edge.
    Rib n's notch pattern starts n x STAGGER further along, following the helix."""
    body = Box(SPAN, RIB_T, RIB_H, align=None)
    for sx in (-TAB_LEN, SPAN):
        body += Pos(sx, 0, 0) * Box(TAB_LEN, RIB_T, TAB_H, align=None)
    x0 = END_MARGIN + NOTCH_R + n * STAGGER
    notch_z = RIB_SOLID - NOTCH_SEAT + NOTCH_R
    for i in range(NOTCHES):
        x = x0 + i * PITCH
        body -= Pos(x, RIB_T / 2, notch_z) * Rot(90, 0, 0) * Cylinder(NOTCH_R, RIB_T + 0.2)
        body -= Pos(x - NOTCH_R, -0.1, notch_z) * Box(2 * NOTCH_R, RIB_T + 0.2, 1, align=None)
    return body


def end_disc():
    """Cage end disc, inner face at z = DISC_T (slots open upward), outer face at z = 0."""
    d = Pos(0, 0, DISC_T / 2) * Cylinder(DISC_D / 2, DISC_T)
    d -= Cylinder(BORE / 2, 2)
    for k in range(N_RIBS):
        a = 360 * k / N_RIBS
        d -= Rot(0, 0, a) * Pos((SLOT_R0 + SLOT_R1) / 2, 0, DISC_T - SLOT_DEPTH / 2 + 0.01) * \
            Box(SLOT_R1 - SLOT_R0, SLOT_W, SLOT_DEPTH + 0.02)
    for a in TIE_ANGLES:
        d -= Rot(0, 0, a) * Pos(TIE_R, 0, 0) * Cylinder(TIE_HOLE / 2, 2)
    d -= Pos(TERM_R, 0, 0) * Cylinder(TERM_HOLE / 2, 2)
    return d


def center_hub():
    h = Cylinder(HUB_D / 2, HUB_T)
    h -= Cylinder(BORE / 2, 2)
    for k in range(N_RIBS):
        h -= Rot(0, 0, 360 * k / N_RIBS) * Pos(HUB_D / 2 - HUB_SLOT_DEPTH / 2 + 0.05, 0, 0) * \
            Box(HUB_SLOT_DEPTH + 0.1, SLOT_W, HUB_T + 0.1)
    for a in TIE_ANGLES:
        h -= Rot(0, 0, a) * Pos(TIE_R, 0, 0) * Cylinder(TIE_HOLE / 2, 2)
    h -= cross_pin(PIN_D + 0.003, HUB_D + 0.2)
    return h


def cross_pin(d=PIN_D, length=None):
    """Diametral pin along PIN_ANG, centered on the axis at z = 0."""
    return Rot(0, 0, PIN_ANG) * Rot(0, 90, 0) * Cylinder(d / 2, length or PIN_LEN)


def shaft():
    s = rod(SHAFT_D, SHAFT_LEN)
    return s - Pos(0, 0, HUB_Z - SHAFT_Z[0]) * cross_pin(PIN_D + 0.002, 1)


def ring(od, idia, w):
    return Pos(0, 0, w / 2) * Cylinder(od / 2, w) - Cylinder(idia / 2, 2 * w + 1)


def split_collar(od, w):
    """1/2" split clamp collar (slit only; clamp screw not modeled)."""
    return ring(od, SHAFT_D, w) - Pos(od / 4 + 0.1, 0, w / 2) * Box(od / 2, 0.03, w + 0.1)


PLATE_HOLES = [  # (name, x, y, dia, note) relative to the shaft axis
    ("A", 0.0, 0.0, R8_OD, "R8 BORE: PRESS (A) / SLIDE ON SHAFT (B)"),
    ("B", BUS_R, 0.0, PILLAR_STUD[0] + 0.016, "PILLAR STUD; CBORE ⌀0.88 x 0.25 OUTSIDE, 3/8-16 PEEK JAM NUT"),
    ("C", BUS_R, GUIDE_DY, GUIDE_D + 0.016, "GUIDE ROD: A - TAP 3/8-16 x 0.40 DP FROM TOP, BLIND; B - THRU"),
    ("D", POST_XY[0][0], POST_XY[0][1], 0.257, "POST SCREW 1/4-20 SHCS; CBORE ⌀0.44 x 0.27 OUTSIDE"),
    ("E", POST_XY[1][0], POST_XY[1][1], 0.257, "POST SCREW 1/4-20 SHCS; CBORE ⌀0.44 x 0.27 OUTSIDE"),
]
DECK_HOLES = [  # plate A only, blind from the bottom face; all >= 2.0 from the bus rod (hole B)
    ("F", -1.75, 1.90, 0.191, "A ONLY: #10-24 HEAT-SET INSERT, 0.38 DP"),
    ("G", -1.75, -1.90, 0.191, "A ONLY: #10-24 HEAT-SET INSERT, 0.38 DP"),
    ("H", 1.50, 1.90, 0.191, "A ONLY: #10-24 HEAT-SET INSERT, 0.38 DP"),
    ("J", 1.50, -1.90, 0.191, "A ONLY: #10-24 HEAT-SET INSERT, 0.38 DP"),
    ("K", -1.75, 0.00, 0.1865, "A ONLY: 3/16 DOWEL, PRESS, 0.38 DP"),
    ("L", 1.00, -1.00, 0.1865, "A ONLY: 3/16 DOWEL, PRESS, 0.38 DP"),
]
BLIND_DP = 0.38
# Counterbores on each plate's OUTSIDE face (bottom of A, top of B) so nothing stands proud of it
CBORE = {"B": (0.88, 0.25),             # 3/8-16 PEEK jam nut (0.219 thick) on the pillar stud
         "D": (0.44, 0.27), "E": (0.44, 0.27)}   # 1/4-20 SHCS head (0.375 x 0.250), 0.02 below the face
POST_SCREW_HEAD = (0.375, 0.250)
# Reference only: the floating deck under plate A (12 ga 5052, §3.0) and plate A's mounting hardware
DECK_T, DECK_HOLE = 0.081, 1.50                   # hole clears the shaft and the thrust collar
DECK_X, DECK_Y = (PLATE_X0 - 0.75, PLATE_X0 + PLATE_L + 0.75), (-PLATE_W / 2 - 0.75, PLATE_W / 2 + 0.75)
SCREW_D, SCREW_HEAD = (0.190, (0.312, 0.190))     # #10-24 SHCS, up through the deck into the inserts
DOWEL_D, DOWEL_L = 0.1865, 0.625
MOUNT = ("deck (ref)", "deck screw", "dowel", "post screw")   # drawn on L-100 / L-107, not in the exploded view
ASM_X = (min(-DISC_D / 2, PLATE_X0), PLATE_X0 + PLATE_L)            # roller alone (L-100)
ASM_X_MOUNT = (min(ASM_X[0], DECK_X[0]), max(ASM_X[1], DECK_X[1]))   # with the reference deck (L-107)


def end_plate(a=True):
    """End plate in plate coords: shaft axis at origin, plate z 0..PLATE_T. Plate A adds the deck holes."""
    p = Pos(PLATE_X0 + PLATE_L / 2, 0, PLATE_T / 2) * Box(PLATE_L, PLATE_W, PLATE_T)
    for name, x, y, d, _n in PLATE_HOLES:
        if a and name == "C":  # blind tapped from the top so nothing protrudes onto the deck
            p -= Pos(x, y, PLATE_T - GUIDE_TAP_DP / 2 + 0.01) * Cylinder(GUIDE_TAP / 2, GUIDE_TAP_DP + 0.02)
        else:
            p -= Pos(x, y, 0) * Cylinder(d / 2, 2)
        if name in CBORE:
            cd, cdp = CBORE[name]
            z = cdp / 2 - 0.01 if a else PLATE_T - cdp / 2 + 0.01
            p -= Pos(x, y, z) * Cylinder(cd / 2, cdp + 0.02)
    if a:
        for _, x, y, d, _n in DECK_HOLES:
            p -= Pos(x, y, BLIND_DP / 2 - 0.01) * Cylinder(d / 2, BLIND_DP + 0.02)
    for _, x, y, _d, _n in DECK_HOLES:
        assert math.hypot(x - BUS_R, y) >= 2.0, f"deck hole at ({x}, {y}) within 2.0 of the bus rod"
    return p


def rod(d, length):
    return Pos(0, 0, length / 2) * Cylinder(d / 2, length)


def guide_rod():
    """3/8 Ultem rod; the bottom GUIDE_TAP_DP is the 3/8-16 thread (modeled at the tap-drill diameter)."""
    return rod(GUIDE_TAP, GUIDE_TAP_DP) + Pos(0, 0, GUIDE_TAP_DP) * rod(GUIDE_D, GUIDE_LEN - GUIDE_TAP_DP)


def pillar(height):
    """Bus-rod pillar: body z 0..height on the plate face, stud below it through the plate,
    rod-end bore (tapped 3/8-24 in practice) in the top."""
    b = rod(PILLAR_D, height)
    b += Pos(0, 0, -PILLAR_STUD[1]) * rod(PILLAR_STUD[0], PILLAR_STUD[1])
    return b - Pos(0, 0, height - PILLAR_THREAD_DP) * rod(BUS_D, PILLAR_THREAD_DP + 0.01)


def wheel():
    w = Cylinder(WHEEL_OD / 2, WHEEL_W)
    w -= Torus(WHEEL_OD / 2 - GROOVE_DEPTH + GROOVE_R, GROOVE_R)
    w -= Cylinder(AXLE_D / 2 + 0.002, 1)
    return w


def fork():
    """Fork in wiper coords: wheel axis at the origin, bar running +X into the carriage."""
    x_join = BRIDGE_X - WHEEL_X
    x_end = CARR_X[1] - WHEEL_X + 0.30
    zc = WHEEL_W / 2 + CHEEK_GAP + CHEEK_T / 2
    f = None
    for s in (1, -1):
        # cheeks stop 0.2" inboard of the axle so they stay outside the neighboring turns
        c = Pos(x_join / 2, 0, s * zc) * Box(x_join, 0.4, CHEEK_T)
        c += Pos(0, 0, s * zc) * Cylinder(0.2, CHEEK_T)
        f = c if f is None else f + c
    f += Pos(x_join + 0.0625, 0, 0) * Box(0.125, 0.4, 2 * zc + CHEEK_T)          # bridge
    f += Pos((x_join + x_end) / 2, 0, 0) * Box(x_end - x_join, FORK_BAR[0], FORK_BAR[1])
    f -= Cylinder(AXLE_D / 2 + 0.002, 2)
    return f


def carriage():
    """Carriage in wiper coords (wheel axis at origin)."""
    x0, x1 = CARR_X[0] - WHEEL_X, CARR_X[1] - WHEEL_X
    y0, y1 = CARR_Y[0] - WIPER_Y, CARR_Y[1] - WIPER_Y
    c = Pos((x0 + x1) / 2, (y0 + y1) / 2, 0) * Box(x1 - x0, y1 - y0, CARR_T)
    bx = BUS_R - WHEEL_X
    c -= Pos(bx, -WIPER_Y, 0) * Cylinder((BUS_D + 0.01) / 2, 2)
    c -= Pos(bx, GUIDE_DY - WIPER_Y, 0) * Cylinder((GUIDE_D + 0.02) / 2, 2)
    c -= Pos((x0 + x1) / 2, 0, 0) * Box(x1 - x0 + 0.2, FORK_BAR[0] + 0.01, FORK_BAR[1] + 0.01)
    return c


def oldham_hub(bore, pin):
    """Hub, slotted face at z = OLD_HUB_L, bore along Z, roll-pin hole across Y at mid-length."""
    h = Pos(0, 0, OLD_HUB_L / 2) * Cylinder(OLD_OD / 2, OLD_HUB_L)
    h -= Cylinder(bore / 2 + 0.001, 4)
    h -= Pos(0, 0, OLD_HUB_L - OLD_SLOT_D / 2 + 0.01) * Box(OLD_OD + 0.1, OLD_SLOT_W, OLD_SLOT_D + 0.02)
    h -= Pos(0, 0, OLD_HUB_L / 2 - 0.1) * Rot(90, 0, 0) * Cylinder(pin / 2, OLD_OD + 0.1)
    return h


def oldham_disc():
    """Center disc: web at z 0..CORE, tongue along X below, tongue along Y above (90 deg apart)."""
    d = Pos(0, 0, OLD_CORE_T / 2) * Cylinder(OLD_OD / 2, OLD_CORE_T)
    d += Pos(0, 0, -OLD_TONGUE_H / 2) * Box(OLD_OD, OLD_TONGUE_W, OLD_TONGUE_H) & \
        Pos(0, 0, -OLD_TONGUE_H / 2) * Cylinder(OLD_OD / 2, OLD_TONGUE_H)
    d += Pos(0, 0, OLD_CORE_T + OLD_TONGUE_H / 2) * Box(OLD_TONGUE_W, OLD_OD, OLD_TONGUE_H) & \
        Pos(0, 0, OLD_CORE_T + OLD_TONGUE_H / 2) * Cylinder(OLD_OD / 2, OLD_TONGUE_H)
    return d


def oldham_parts():
    """[(name, shape, explode)] with the roller-side hub on top (slot down), G10 hub below (slot up)."""
    lo = oldham_hub(G10_D, OLD_PIN["g10"])                       # z 0..HUB_L, slot up
    z_disc = OLD_HUB_L + OLD_GAP
    disc = Pos(0, 0, z_disc) * oldham_disc()                     # lower tongue along X into the G10 hub slot
    z_hi = z_disc + OLD_CORE_T + OLD_GAP + OLD_HUB_L
    # flipped slot-down, then turned 90 deg so its slot takes the upper (Y) tongue
    hi = Rot(0, 0, 90) * Pos(0, 0, z_hi) * Rot(180, 0, 0) * oldham_hub(SHAFT_D, OLD_PIN["roller"])
    engage = OLD_HUB_L - OLD_SLOT_D - 0.03                         # shaft ends stop short of the slot
    g10 = Pos(0, 0, -1.25) * rod(G10_D, 1.25 + engage)
    roller_stub = Pos(0, 0, z_hi - engage) * rod(SHAFT_D, engage + 1.0)
    return [("g10 shaft", g10, (0, 0, -1.2)), ("hub g10", lo, (0, 0, -0.6)), ("disc", disc, (0, 0, 0)),
            ("hub roller", hi, (0, 0, 0.6)), ("roller shaft", roller_stub, (0, 0, 1.4))]


def winding_rings():
    """Drafting stand-in for the exploded view: one torus per turn. Hidden-line removal on the
    swept helix takes minutes; at 1:4 the 1.3 deg pitch angle is invisible."""
    return Compound([Pos(0, 0, Z_W0 + k * PITCH) * Torus(COIL_D / 2, WIRE_D / 2) for k in range(TURNS)])


def winding():
    z_w0 = DISC_T + END_MARGIN + NOTCH_R
    path = Helix(PITCH, TURNS * PITCH, COIL_D / 2, center=(0, 0, z_w0))
    prof = Plane(origin=path @ 0, z_dir=path % 0) * Circle(WIRE_D / 2)
    return sweep(prof, path, is_frenet=True)


# ------------------------------------------------------------------ assembly
def placed_parts():
    """[(item, name, shape_in_assembly, explode_vector)] — item numbers match the parts list.
    Rods and wiper explode along (1, 1, 0), across the iso line of sight (1, -1, 0.8)."""
    P = []
    seat = Plane(origin=(RIB_INNER_R, RIB_T / 2, DISC_T), x_dir=(0, 0, 1), z_dir=(1, 0, 0)).location
    for k in range(N_RIBS):
        a = 360 * k / N_RIBS
        r = rib(k)
        out = (2.2 * math.cos(math.radians(a)), 2.2 * math.sin(math.radians(a)), 0)
        P.append((3, "rib", Rot(0, 0, a) * seat * r, out))
    disc = end_disc()
    P.append((4, "end disc A", disc, (0, 0, -3.0)))
    P.append((4, "end disc B", Pos(0, 0, Z_TOP_CAGE) * Rot(180, 0, 0) * disc, (0, 0, 3.0)))
    P.append((5, "center hub", Pos(0, 0, DISC_T + SPAN / 2) * center_hub(), (0, 0, 0)))
    for a in TIE_ANGLES:
        P.append((6, "tie rod", Rot(0, 0, a) * Pos(TIE_R, 0, TIE_RECESS) * rod(TIE_D, TIE_LEN), (0, 0, 5.5)))
    P.append((17, "hub pin", Pos(0, 0, HUB_Z) * cross_pin(), (0, 0, 0)))
    P.append((2, "winding", winding(), (0, 0, 0)))
    P.append((7, "shaft", Pos(0, 0, SHAFT_Z[0]) * shaft(), (0, 0, -8.5)))
    P.append((1, "end plate A", Pos(0, 0, Z_PLATE_A[0]) * end_plate(True), (0, 0, -5.5)))
    P.append((1, "end plate B", Pos(0, 0, Z_PLATE_B[0]) * end_plate(False), (0, 0, 5.0)))
    P.append((15, "contact collar", Pos(0, 0, COLLAR_Z[0]) * split_collar(COLLAR_OD, COLLAR_Z[1] - COLLAR_Z[0]),
              (0, 0, -3.9)))
    P.append((16, "thrust collar", Pos(0, 0, THRUST_Z[0]) * split_collar(THRUST_OD, THRUST_W), (0, 0, -7.0)))
    P.append((18, "PTFE washer", Pos(0, 0, Z_PLATE_A[1]) * ring(WASHER_OD, SHAFT_D + 0.01, WASHER_T), (0, 0, -4.6)))
    deck = Pos((DECK_X[0] + DECK_X[1]) / 2, (DECK_Y[0] + DECK_Y[1]) / 2, Z_PLATE_A[0] - DECK_T / 2) * \
        Box(DECK_X[1] - DECK_X[0], DECK_Y[1] - DECK_Y[0], DECK_T)
    deck -= Cylinder(DECK_HOLE / 2, 10)
    for name, x, y, d, _n in DECK_HOLES:
        clear = 0.201 if name in "FGHJ" else d + 0.002          # screw clearance; dowels slip
        deck -= Pos(x, y, 0) * Cylinder(clear / 2, 10)
    P.append((31, "deck (ref)", deck, (0, 0, 0)))
    for x, y in POST_XY:  # post screw heads, recessed in both plates' outside faces
        hd, hh = POST_SCREW_HEAD
        cdp = CBORE["D"][1]
        P.append((21, "post screw", Pos(x, y, Z_PLATE_A[0] + cdp - hh) * rod(hd, hh), (1.5, 2.5 * (1 if y > 0 else -1), -5.5)))
        P.append((21, "post screw", Pos(x, y, Z_PLATE_B[1] - cdp) * rod(hd, hh), (1.5, 2.5 * (1 if y > 0 else -1), 5.0)))
    z_deck_bot = Z_PLATE_A[0] - DECK_T
    for name, x, y, _d, _n in DECK_HOLES:
        if name in "FGHJ":
            sc = Pos(x, y, z_deck_bot - SCREW_HEAD[1]) * rod(SCREW_HEAD[0], SCREW_HEAD[1])
            sc += Pos(x, y, z_deck_bot) * rod(SCREW_D, DECK_T + BLIND_DP - 0.03)
            P.append((22, "deck screw", sc, (0, 0, 0)))
        else:
            P.append((23, "dowel", Pos(x, y, Z_PLATE_A[0] + BLIND_DP - 0.01 - DOWEL_L) * rod(DOWEL_D, DOWEL_L), (0, 0, 0)))
    P.append((18, "PTFE washer", Pos(0, 0, Z_PLATE_A[0] - WASHER_T) * ring(WASHER_OD, SHAFT_D + 0.01, WASHER_T),
              (0, 0, -6.3)))
    P.append((8, "bus rod", Pos(BUS_R, 0, BUS_Z[0] - PILLAR_THREAD_DP) * rod(BUS_D, BUS_LEN + 2 * PILLAR_THREAD_DP),
              (2.0, 2.0, 0)))
    P.append((30, "bus-rod pillar lower", Pos(BUS_R, 0, Z_PLATE_A[1]) * pillar(PILLAR_LO), (2.0, 2.0, -1.0)))
    P.append((30, "bus-rod pillar upper", Pos(BUS_R, 0, Z_PLATE_B[0]) * Rot(180, 0, 0) * pillar(PILLAR_HI),
              (2.0, 2.0, 1.0)))
    P.append((9, "guide rod", Pos(BUS_R, GUIDE_DY, GUIDE_Z0) * guide_rod(), (2.7, 2.7, 0)))
    for x, y in POST_XY:
        P.append((10, "frame post", Pos(x, y, Z_PLATE_A[1]) * rod(POST_D, INNER_SPAN), (1.5, 2.5 * (1 if y > 0 else -1), 0)))
    wl = Pos(WHEEL_X, WIPER_Y, WIPER_Z)
    P.append((11, "wheel", wl * wheel(), (6.6, 6.6, 0)))
    P.append((12, "axle", wl * Pos(0, 0, -0.3) * rod(AXLE_D, 0.6), (6.6, 6.6, 1.6)))
    P.append((13, "fork", wl * fork(), (5.4, 5.4, 0)))
    P.append((14, "carriage", wl * carriage(), (4.0, 4.0, 0)))
    return P


ITEMS = {
    1: ("END PLATE (A BOTTOM, B TOP)", 2, "ULTEM 1000, 1/2 PLATE", "TUNER-L-102"),
    2: (f"WINDING, {TURNS} T #4 AWG", 1, "Cu, ANNEALED, SILVER PLATED", "TUNER-L-100"),
    3: ("RIB", N_RIBS, "ULTEM 1000, 3/8 PLATE", "TUNER-L-101"),
    4: ("CAGE END DISC", 2, "ULTEM 1000, 1/2 PLATE", "TUNER-L-103"),
    5: ("CENTER HUB", 1, "ULTEM 1000 (OR PTFE)", "TUNER-L-103"),
    6: ("TIE ROD", 4, "ULTEM 1000, 3/8 ROD", "TUNER-L-104"),
    7: ("SHAFT", 1, "C360 BRASS, 1/2 ROD, Ag PLATED", "TUNER-L-104"),
    8: ("BUS ROD", 1, "C360 BRASS, 3/8 ROD, Ag PLATED", "TUNER-L-104"),
    9: ("GUIDE ROD", 1, "ULTEM 1000, 3/8 ROD", "TUNER-L-104"),
    10: ("FRAME POST", 2, "ULTEM 1000, 3/4 ROD", "TUNER-L-104"),
    11: ("WIPER WHEEL", 1, "BRASS OR Cu, Ag PLATED", "TUNER-L-105"),
    12: ("WHEEL AXLE", 1, "STAINLESS 303, 3/16", "TUNER-L-105"),
    13: ("WIPER FORK", 1, "BRASS, Ag PLATED", "TUNER-L-105"),
    14: ("WIPER CARRIAGE", 1, "BRASS, Ag PLATED BORE", "TUNER-L-105"),
    15: ("CONTACT / BOND COLLAR, 1.25 OD", 1, "C360 BRASS, Ag PLATED, SPLIT", "TUNER-L-107"),
    16: ("THRUST COLLAR, 1/2 BORE", 1, "BRASS SPLIT COLLAR, STD", "COMMERCIAL"),
    17: ("HUB CROSS PIN, 1/8", 1, "BRASS ROD", "TUNER-L-107"),
    18: ("THRUST WASHER, 1/2 x 1.0 x 1/32", 2, "PTFE", "COMMERCIAL"),
    19: ("BEARING R8, 1/2 x 1-1/8 x 5/16", 2, "SEALED BALL (OR RULON J SLEEVE)", "COMMERCIAL"),
    20: ("FLAT HEAD SCREW #10-24 x 1/2", 8, "PEEK - TIE RODS TO DISCS", "COMMERCIAL"),
    21: ("SHCS 1/4-20 x 3/4", 4, "STAINLESS - FRAME POSTS", "COMMERCIAL"),
    22: ("SHCS #10-24 + HEAT-SET INSERT", 4, "STAINLESS / BRASS - PLATE A TO DECK", "COMMERCIAL"),
    23: ("DOWEL PIN 3/16 x 5/8", 2, "STAINLESS - PLATE A TO DECK", "COMMERCIAL"),
    24: ("NUT 3/8-24 + STOP COLLAR", 2, "BRASS, Ag PLATED - BUS ROD", "COMMERCIAL"),
    25: ("NUT 3/8-16", 2, "PEEK - GUIDE ROD", "COMMERCIAL"),
    26: ("SCREW #8-32 + RING LUG FOR #4", 1, "BRASS - COLD END TO COLLAR", "COMMERCIAL"),
    27: ("SPRING, Ag SHOE, FLAT BRAID", 1, "WIPER - SEE L-105 NOTE 5", "TBD"),
    28: ("RTV SILICONE, NEUTRAL CURE", 1, "MIL-A-46146: DOWSIL 3145 / RTV162", "COMMERCIAL"),
    29: ("COUPLER B, OLDHAM (REFERENCE)", 1, "DELRIN 150 + ROLL PINS", "TUNER-L-108"),
    30: ("BUS-ROD PILLAR (LOWER, UPPER)", 2, "ULTEM 1000, 3/4 ROD + PEEK NUT", "TUNER-L-104"),
    31: ("FLOATING DECK (REFERENCE, PARTIAL)", 1, "12 GA 5052-H32 ALUMINUM", "DESIGN LOG 3.0"),
}


# ------------------------------------------------------------------ installation in the RF bay (§3.0)
# Enclosure frame: X = depth (front -), Y = width, Z = up from the underside of the floor.
ENC = 16.00
WALL_T, FLOOR_T, SHELF_T, LID_T = 0.064, 0.081, 0.081, 0.081   # top is 12 ga (carries the output feedthroughs)
UTILITY_H, STANDOFF_H = 5.00, 5.50             # standoffs +2.0 Rev 3.7c: the input choke stands under the deck
DECK_SIZE = 10.75
BAY_IN = ENC - 2 * WALL_T                       # 15.87 interior
Z_SHELF = FLOOR_T + UTILITY_H                   # shelf underside
Z_DECK = Z_SHELF + SHELF_T + STANDOFF_H         # deck underside
Z_DECK_TOP = Z_DECK + DECK_T
ENC_H = 24.00                                   # +1.0 for the 22-turn roller (Rev 3.7a), +2.0 deck raise (Rev 3.7c)
Z_LID = ENC_H - LID_T                           # lid underside
CAP_D, CAP_H = 3.75, 8.6                        # C1/C2 reference envelopes above the deck (§3.0)
CAP_Y = -DECK_SIZE / 2 + CAP_D / 2              # cap column across the width (at the deck edge: 3.75 + 1.5 + 5.5 = 10.75)
CAP_SHIFT = -0.875                             # cap column forward on the deck (uses its 1.75" depth slack)
                                                # so both cap motors fall inside the motor chamber (E-200)
CAP_X = (-(CAP_D + 1.5) / 2 + CAP_SHIFT, (CAP_D + 1.5) / 2 + CAP_SHIFT)   # C1 front, C2 rear, 1.5 hot-to-hot
# PROPOSED roller location: plate A 1.5 across from the cap column, centered on the deck in depth
ROLLER_Y = CAP_Y + CAP_D / 2 + 1.5 + PLATE_W / 2
ROLLER_X = -(PLATE_X0 + PLATE_L / 2)            # plate centered in depth; bus rod toward mid-depth
ROLLER_DZ = Z_DECK_TOP - Z_PLATE_A[0]           # roller model z -> enclosure z
BUSHING_OD, BUSHING_FLANGE = 0.500, (0.750, 0.094)   # flanged bronze bushing, 3/8 bore (§7.1)
MOTOR_BODY = (2.22, 2.20)                       # NEMA 23 short stack 23HS22-2804S (56 mm), direct - M-2 Rev 3.7b
SHELF_HOLE = BUSHING_OD + 0.002


def install_parts():
    """[(label, shape)] in enclosure coords. Winding drawn as rings (fast hidden-line removal)."""
    out = []
    to_enc = Pos(ROLLER_X, ROLLER_Y, ROLLER_DZ)
    for item, name, shp, _v in placed_parts():
        if name == "deck (ref)":
            continue
        out.append((name, to_enc * (winding_rings() if name == "winding" else shp)))
    # deck, full size, with the roller's holes and generous clearance holes for the cap shafts
    deck = Pos(0, 0, Z_DECK + DECK_T / 2) * Box(DECK_SIZE, DECK_SIZE, DECK_T)
    deck -= Pos(ROLLER_X, ROLLER_Y, 0) * Cylinder(DECK_HOLE / 2, 60)
    for name, x, y, d, _n in DECK_HOLES:
        clear = 0.201 if name in "FGHJ" else d + 0.002
        deck -= Pos(ROLLER_X + x, ROLLER_Y + y, 0) * Cylinder(clear / 2, 60)
    for cx in CAP_X:
        deck -= Pos(cx, CAP_Y, 0) * Cylinder(0.75, 60)
    out.append(("deck", deck))
    for sx in (-1, 1):                          # 4 standoffs, inset 0.5 from the deck corners
        for sy in (-1, 1):
            out.append(("standoff", Pos(sx * (DECK_SIZE / 2 - 0.5), sy * (DECK_SIZE / 2 - 0.5), Z_SHELF + SHELF_T)
                        * rod(0.75, STANDOFF_H)))
    for cx in CAP_X:                            # C1 / C2 reference envelopes
        out.append(("cap envelope", Pos(cx, CAP_Y, Z_DECK_TOP) * rod(CAP_D, CAP_H)))
    # shelf (grounded) with the roller axis bushing hole and the cap axes
    shelf = Pos(0, 0, Z_SHELF + SHELF_T / 2) * Box(BAY_IN, BAY_IN, SHELF_T)
    for x, y in [(ROLLER_X, ROLLER_Y)] + [(cx, CAP_Y) for cx in CAP_X]:
        shelf -= Pos(x, y, 0) * Cylinder(SHELF_HOLE / 2, 60)
    out.append(("shelf", shelf))
    out.append(("floor", Pos(0, 0, FLOOR_T / 2) * Box(ENC, ENC, FLOOR_T)))
    out.append(("lid", Pos(0, 0, Z_LID + LID_T / 2) * Box(ENC, ENC, LID_T)))
    for sx in (-1, 1):                          # front and rear walls (cut by the section)
        out.append(("wall", Pos(sx * (ENC / 2 - WALL_T / 2), 0, (FLOOR_T + Z_LID) / 2) * Box(WALL_T, ENC, Z_LID - FLOOR_T)))
    # drive train on the roller axis: coupler B (Oldham), G10 shaft, bushing, coupler A, motor
    ox, oy = ROLLER_X, ROLLER_Y
    z_shaft_bot = SHAFT_Z[0] + ROLLER_DZ
    engage = OLD_HUB_L - OLD_SLOT_D - 0.03
    z_old_top = z_shaft_bot + engage            # back face of the roller-side hub
    z_old_bot = z_old_top - (2 * OLD_HUB_L + OLD_CORE_T + 2 * OLD_GAP)
    for n, shp, _v in oldham_parts():
        if n in ("hub g10", "disc", "hub roller"):
            # oldham_parts() stacks from z = 0 (G10 hub bottom) upward
            out.append(("coupler B", Pos(ox, oy, z_old_bot) * shp))
    z_g10_top = z_old_bot + engage
    z_cplA_top = Z_SHELF - 0.25
    cpl_bore = 0.5                              # G10 shaft engagement in coupler A
    out.append(("G10 shaft", Pos(ox, oy, z_cplA_top - cpl_bore) * rod(G10_D, z_g10_top - (z_cplA_top - cpl_bore))))
    bushing = Pos(ox, oy, Z_SHELF) * rod(BUSHING_OD, SHELF_T) + \
        Pos(ox, oy, Z_SHELF + SHELF_T) * rod(BUSHING_FLANGE[0], BUSHING_FLANGE[1])
    out.append(("bushing", bushing - Pos(ox, oy, 0) * rod(G10_D + 0.002, 60)))
    out.append(("coupler A", Pos(ox, oy, z_cplA_top - 1.0) * rod(1.0, 1.0) -
                Pos(ox, oy, z_cplA_top - cpl_bore) * rod(G10_D + 0.001, cpl_bore + 0.01)))
    mb, ml = MOTOR_BODY
    out.append(("motor", Pos(ox, oy, z_cplA_top - 1.0 - ml / 2) * Box(mb, mb, ml)))
    return out


def install_holes():
    """Deck and shelf holes for the drive axes: (part, tag, dia, X from front edge, Y from left edge, note)."""
    h0 = DECK_SIZE / 2
    rows = [("DECK", "R", DECK_HOLE, ROLLER_X + h0, ROLLER_Y + h0, "ROLLER SHAFT + THRUST COLLAR CLEARANCE")]
    for name, x, y, d, _n in DECK_HOLES:
        if name in "FGHJ":
            rows.append(("DECK", name, 0.201, ROLLER_X + x + h0, ROLLER_Y + y + h0, "#10-24 CLEAR, SHCS UP INTO PLATE A"))
        else:
            rows.append(("DECK", name, d + 0.002, ROLLER_X + x + h0, ROLLER_Y + y + h0, "3/16 DOWEL, SLIP"))
    for tag, cx in zip(("C1", "C2"), CAP_X):
        rows.append(("DECK", tag, 1.50, cx + h0, CAP_Y + h0, "CAP SHAFT CLEARANCE, RADIUS THE EDGE (3.0)"))
    s0 = BAY_IN / 2
    rows.append(("SHELF", "R", SHELF_HOLE, ROLLER_X + s0, ROLLER_Y + s0, "FLANGED BRONZE BUSHING, 3/8 BORE"))
    for tag, cx in zip(("C1", "C2"), CAP_X):
        rows.append(("SHELF", tag, SHELF_HOLE, cx + s0, CAP_Y + s0, "FLANGED BRONZE BUSHING, 3/8 BORE"))
    return rows


def install_report():
    """Clearances for the installation sheet, inches."""
    r = {}
    first_turn = Z_W0 - WIRE_D / 2 + ROLLER_DZ
    last_turn = Z_W0 + TURNS * PITCH + WIRE_D / 2 + ROLLER_DZ
    r["DECK TOP TO FIRST TURN"] = first_turn - Z_DECK_TOP
    r["LAST TURN TO TOP PANEL"] = Z_LID - last_turn
    r["BUS ROD TO DECK (AIR)"] = BUS_Z[0] + ROLLER_DZ - Z_DECK_TOP
    r["BUS ROD TO TOP PANEL (AIR)"] = Z_LID - (BUS_Z[1] + ROLLER_DZ)
    r["PLATE B TOP TO TOP PANEL"] = Z_LID - (Z_PLATE_B[1] + ROLLER_DZ)
    coil_r = COIL_D / 2 + WIRE_D / 2
    r["COIL TO SIDE WALL"] = BAY_IN / 2 - (ROLLER_Y + coil_r)
    r["COIL TO FRONT WALL"] = (ROLLER_X - coil_r) + BAY_IN / 2
    r["COIL TO C1/C2 ENVELOPE"] = math.hypot(ROLLER_X - CAP_X[0], ROLLER_Y - CAP_Y) - coil_r - CAP_D / 2
    r["BUS ROD TO REAR WALL"] = BAY_IN / 2 - (ROLLER_X + BUS_R + PILLAR_D / 2)
    z_shaft_bot = SHAFT_Z[0] + ROLLER_DZ
    r["SHAFT TIP TO SHELF (CREEPAGE ALONG OLDHAM + G10)"] = z_shaft_bot - (Z_SHELF + SHELF_T + BUSHING_FLANGE[1])
    r["DECK UNDERSIDE TO SHELF"] = Z_DECK - (Z_SHELF + SHELF_T)
    return r


# ------------------------------------------------------------------ section hatching
# TechDraw only hatches its own section views (which hang on the helix), and its cosmetic lines
# always print dashed. So each pre-cut section gets an overlay: 45 deg hatch segments on the cut
# faces, nudged toward the viewer, plus two tiny anchor edges at the section's bounding-box corners
# so the overlay view centers exactly like the section view it sits on.
def hatch_overlay(solids, n, origin, spacing, clip=None):
    """n: unit normal facing the viewer; origin: a point on the cut plane; clip: (center, radius)
    to keep only segments inside a detail circle (in-plane), anchoring the overlay on that circle."""
    n = Vector(*n)
    u = Vector(1, 0, 0)
    v = n.cross(u)          # view "up": +Z for a view from -Y, +Y for a view from +Z
    d, p = (u + v).normalized(), (u - v).normalized()
    nudge = n * 0.002
    o0 = Vector(*origin)
    edges = []
    for sol in solids:
        for f in sol.faces():
            if f.normal_at().dot(n) < 0.999 or abs((f.center() - o0).dot(n)) > 1e-6:
                continue
            bb = f.bounding_box()
            c, R = bb.center(), bb.diagonal
            k = int(R / spacing) + 1
            base = round((c - o0).dot(p) / spacing)          # keep lines on a sheet-wide grid
            for i in range(base - k, base + k + 1):
                q = o0 + p * (i * spacing) + d * (c - o0).dot(d)
                for piece in f.intersect(Edge.make_line(q - d * R, q + d * R)) or []:
                    for ed in piece.edges():
                        a, b = ed.start_point(), ed.end_point()
                        if clip:
                            cc, rr = Vector(*clip[0]), clip[1]
                            ok = [(x - cc).length <= rr for x in (a, b)]
                            if not any(ok):
                                continue
                            if not all(ok):                  # trim to the circle
                                dirv = (b - a).normalized()
                                inside, outside = (a, b) if ok[0] else (b, a)
                                lo, hi = 0.0, (outside - inside).length
                                for _ in range(30):
                                    mid = (lo + hi) / 2
                                    if ((inside + (outside - inside).normalized() * mid) - cc).length <= rr:
                                        lo = mid
                                    else:
                                        hi = mid
                                a, b = inside, inside + (outside - inside).normalized() * lo
                        edges.append(Edge.make_line(a + nudge, b + nudge))
    if clip:
        cc, rr = Vector(*clip[0]), clip[1]
        corners = [cc - (u + v) * rr, cc + (u + v) * rr]
    else:
        bb = Compound(solids).bounding_box()
        corners = [bb.min, bb.max]
    for c in corners:
        edges.append(Edge.make_line(c, c + u * 1e-4))
    return Compound(edges)


def mm(shape):
    return shape.scale(25.4)


def main():
    parts = placed_parts()
    # L-100 shows the roller alone; the deck and its hardware are drawn on L-107 and L-109
    export_step(mm(Compound([s for _, n, s, _ in parts if n not in MOUNT[:3]])), str(OUT / "roller.step"))
    exp_parts = [p for p in parts if p[1] not in MOUNT]
    exploded = [Pos(*v) * (winding_rings() if n == "winding" else s) for _, n, s, v in exp_parts]
    export_step(mm(Compound(exploded)), str(OUT / "roller-exploded.step"))
    # one STEP per detail part, in drawing orientation
    singles = {
        "rib": rib(0), "end-disc": end_disc(), "center-hub": center_hub(), "end-plate": end_plate(True),
        "tie-rod": rod(TIE_D, TIE_LEN), "shaft": shaft(),
        "contact-collar": split_collar(COLLAR_OD, COLLAR_Z[1] - COLLAR_Z[0]),
        "bus-rod": rod(BUS_D, BUS_LEN + 2 * PILLAR_THREAD_DP), "guide-rod": guide_rod(),
        "pillar-lower": pillar(PILLAR_LO), "pillar-upper": pillar(PILLAR_HI),
        "frame-post": rod(POST_D, INNER_SPAN), "wheel": wheel(), "axle": rod(AXLE_D, 0.6),
        "fork": fork(), "carriage": carriage(),
    }
    for name, s in singles.items():
        export_step(mm(s), str(OUT / f"part-{name}.step"))
    # end disc cut through the axis along X (keeps y >= 0, viewed from -Y): shows blind slots vs through holes
    export_step(mm(end_disc() & Pos(0, 5, 0) * Box(10, 10, 10)), str(OUT / "part-end-disc-section.step"))
    # pre-cut sections (TechDraw's own section view hangs on the swept helix)
    big = 40
    keep_aa = Pos(0, big / 2, 0) * Box(big, big, big)                 # A-A: plane y = 0, viewed from -Y
    keep_bb = Pos(0, 0, WIPER_Z - big / 2) * Box(big, big, big)       # B-B: plane z = wheel center, from above
    cuts = {}
    for tag, keep in (("aa", keep_aa), ("bb", keep_bb)):
        src = parts if tag == "aa" else [p for p in parts if p[1] not in MOUNT[:3]]   # A-A keeps the mounting
        cut = [c for c in ((sh & keep) for _, _, sh, _ in src) if c.volume > 1e-9]
        export_step(mm(Compound(cut)), str(OUT / f"roller-section-{tag}.step"))
        cuts[tag] = cut
        if tag == "bb":  # just the wiper corner, for the enlarged detail on TUNER-L-100
            win = Pos((WHEEL_X - 0.75 + CARR_X[1] + 0.15) / 2, (CARR_Y[0] + CARR_Y[1]) / 2, WIPER_Z - big / 2) * \
                Box(CARR_X[1] + 0.15 - (WHEEL_X - 0.75), CARR_Y[1] - CARR_Y[0] + 0.3, big)
            w = [c for c in ((sh & win) for sh in cut) if c.volume > 1e-9]
            export_step(mm(Compound(w)), str(OUT / "roller-section-bb-wiper.step"))
            cuts["bbw"] = w
    # coupler B
    op = oldham_parts()
    export_step(mm(Compound([sh for _, sh, _ in op])), str(OUT / "oldham.step"))
    export_step(mm(Compound([Pos(*v) * sh for _, sh, v in op])), str(OUT / "oldham-exploded.step"))
    export_step(mm(oldham_hub(SHAFT_D, OLD_PIN["roller"])), str(OUT / "part-oldham-hub-roller.step"))
    export_step(mm(oldham_hub(G10_D, OLD_PIN["g10"])), str(OUT / "part-oldham-hub-g10.step"))
    export_step(mm(oldham_disc()), str(OUT / "part-oldham-disc.step"))
    # balloon anchors for the exploded iso: centroid of the first instance of each item
    anchors = {}
    for item, _, s, v in exp_parts:
        if item not in anchors:
            c = (Pos(*v) * s).center()
            anchors[item] = [c.X * 25.4, c.Y * 25.4, c.Z * 25.4]
    inst = install_parts()
    # section hatching overlays (paper spacing ~1.6 mm at each view's scale)
    def sp(scale):
        return 1.6 / 25.4 / scale
    disc_cut = end_disc() & Pos(0, 5, 0) * Box(10, 10, 10)
    hatches = {
        "aa": (cuts["aa"], (0, -1, 0), (0, 0, 0), sp(0.4), None),
        "aa-B": (cuts["aa"], (0, -1, 0), (0, 0, 0), sp(1.0), ((0.6, 0, Z_TOP_CAGE + 0.3), 1.25)),
        "aa-C": (cuts["aa"], (0, -1, 0), (0, 0, 0), sp(1.0), ((0.6, 0, -0.75), 1.25)),
        "bb": (cuts["bb"], (0, 0, 1), (0, 0, WIPER_Z), sp(0.5), None),
        "bbw": (cuts["bbw"], (0, 0, 1), (0, 0, WIPER_Z), sp(1.3), None),
        "ee": ([disc_cut], (0, -1, 0), (0, 0, 0), sp(1.0), None),
    }
    for tag, (sol, nrm, org, spc, clip) in hatches.items():
        export_step(mm(hatch_overlay(sol, nrm, org, spc, clip)), str(OUT / f"hatch-{tag}.step"))
    export_step(mm(Compound([sh for _, sh in inst])), str(OUT / "install.step"))
    export_step(mm(Compound([sh for n, sh in inst if n != "lid"])), str(OUT / "install-plan.step"))
    keep = Pos(0, ROLLER_Y + 20, 0) * Box(60, 40, 60)       # section F-F: through the roller axis, from -Y
    export_step(mm(Compound([c for c in ((sh & keep) for _, sh in inst) if c.volume > 1e-9])),
                str(OUT / "install-section.step"))
    ff = [c for c in ((sh & keep) for _, sh in inst) if c.volume > 1e-9]
    export_step(mm(hatch_overlay(ff, (0, -1, 0), (0, ROLLER_Y, 0), sp(0.25))), str(OUT / "hatch-ff.step"))
    zg = (Z_SHELF + Z_DECK) / 2
    export_step(mm(hatch_overlay(ff, (0, -1, 0), (0, ROLLER_Y, 0), sp(0.45), ((ROLLER_X, ROLLER_Y, zg), 2.6))),
                str(OUT / "hatch-ff-G.step"))
    meta = {
        "items": {k: list(v) for k, v in ITEMS.items()},
        "anchors": anchors,
        "plate_holes": PLATE_HOLES + DECK_HOLES,
        "install": install_report(),
        "install_holes": install_holes(),
        "p": {k: v for k, v in globals().items() if k.isupper() and isinstance(v, (int, float, tuple, dict))},
    }
    (OUT / "parts.json").write_text(json.dumps(meta, indent=1))
    print(f"span {SPAN:.3f}  disc {DISC_D:.3f}  hub {HUB_D:.3f}  bus R {BUS_R:.3f}  wheel axis R {WHEEL_AXIS_R:.3f}")
    print(f"plate-to-plate {INNER_SPAN:.3f}  overall (plates) {Z_PLATE_B[1] - Z_PLATE_A[0]:.3f}  "
          f"shaft {SHAFT_LEN:.3f}  rods {ROD_LEN:.3f}  tie {TIE_LEN:.3f}")
    print(f"wheel flange min R {WHEEL_AXIS_R - WHEEL_OD / 2:.3f} vs rib top R {RIB_OUTER_R:.3f}; "
          f"post surface R {math.hypot(*POST_XY[0]) - POST_D / 2:.3f} vs disc R {DISC_D / 2:.3f}")
    print("wrote", len(singles) + 2, "STEP files + parts.json")


if __name__ == "__main__":
    main()
