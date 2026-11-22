# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""FreeCAD TechDraw sheets for the homebuilt roller (design log §5.3a, Rev 3.7 target).

Run headless after roller.py:  xvfb-run -a freecad cad/drawings.py
Reads the STEP files and parts.json written by roller.py and writes
out/roller-drawings.FCStd plus a PDF and SVG per sheet. Dimensions are associative to
the imported geometry and display in inches through the document's unit system (no
change to global FreeCAD preferences). Views that include the swept winding use
CoarseView: exact hidden-line removal leaves a phantom circle from the helix.
"""
import json
import math
import os
import time
import traceback

import FreeCAD as App
import Part
import TechDrawGui
from PySide import QtGui

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
LOG = open(os.path.join(OUT, os.environ.get("TD_LOG", "drawings.log")), "w")
TEMPLATE = "/usr/share/freecad/Mod/TechDraw/Templates/ASME/ANSIB_Landscape.svg"
IN = 25.4
T0 = time.time()
META = json.load(open(os.path.join(OUT, "parts.json")))
P = META["p"]
N_SHEETS = 10
SUBTITLE = "ROLLER INDUCTOR R-1 C - DRAFT"   # title-block line 2; drawings_enclosure.py overrides


def log(*a):
    print(*a, file=LOG, flush=True)


def pump(n=20):
    for _ in range(n):
        QtGui.QApplication.processEvents()
        time.sleep(0.05)


def settle(views, timeout=300):
    """TechDraw runs hidden-line removal on worker threads; pump events until every view has geometry."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        pump(1)
        try:
            if all(v.getVisibleVertexes() for v in views):
                pump(10)
                return
        except Exception:
            pass
    log("WARNING: views not finished:", [v.Name for v in views])


# ------------------------------------------------------------------ geometry picking
# getVisibleVertexes()/getVisibleEdges() are in scaled view coordinates with +y DOWN;
# everything below converts to +y UP to match dimension X/Y offsets on the page.

def verts(view):
    return view.getVisibleVertexes()


def extreme(view, sx, sy):
    """'VertexN' furthest in the (sx, sy) direction, page sense (+y up)."""
    vs = verts(view)
    i = max(range(len(vs)), key=lambda k: sx * vs[k].x - sy * vs[k].y)
    return f"Vertex{i}"


def bbox(view):
    vs = verts(view)
    xs, ys = [p.x for p in vs], [-p.y for p in vs]
    return min(xs), max(xs), min(ys), max(ys)


def circles(view):
    """{radius_model_mm: 'EdgeN'}, one edge per distinct circle radius."""
    out = {}
    for i, e in enumerate(view.getVisibleEdges()):
        c = getattr(e, "Curve", None)
        if c is not None and hasattr(c, "Radius"):
            out.setdefault(round(c.Radius / view.Scale, 2), f"Edge{i}")
    return out


# ------------------------------------------------------------------ drawing objects
def dim(doc, page, view, kind, refs, x, y, fmt="%.3f"):
    d = doc.addObject("TechDraw::DrawViewDimension", "Dim")
    d.Type = kind
    d.MeasureType = "Projected"
    d.References2D = [(view, r) for r in refs]
    d.FormatSpec = fmt
    if "%" not in fmt:          # plain label (e.g. a tabulated "A"): show the text, not the value
        d.Arbitrary = True
    page.addView(d)
    d.X, d.Y = x, y
    return d


def overall(doc, page, view, x=True, y=True, gap=10):
    """Overall width (below the view) and height (right of the view)."""
    x0, x1, y0, y1 = bbox(view)
    if x:
        dim(doc, page, view, "DistanceX", [extreme(view, -1, -1), extreme(view, 1, -1)], (x0 + x1) / 2, y0 - gap)
    if y:
        dim(doc, page, view, "DistanceY", [extreme(view, 1, -1), extreme(view, 1, 1)], x1 + gap, (y0 + y1) / 2)


def diameters(doc, page, view, start=35):
    """One diameter callout per distinct circle size, fanned around the view."""
    for k, (r, e) in enumerate(sorted(circles(view).items(), reverse=True)):
        ang = math.radians(start + 50 * k)
        dist = r * view.Scale + 12
        dim(doc, page, view, "Diameter", [e], dist * math.cos(ang), dist * math.sin(ang), fmt="⌀%.3f")


def note(doc, page, lines, x, y, size=3.5):
    a = doc.addObject("TechDraw::DrawViewAnnotation", "Note")
    a.Text = lines
    a.TextSize = size
    a.TextStyle = "Normal"
    page.addView(a)
    a.X, a.Y = x, y
    return a


def table(doc, page, name, rows, widths_mm, x, y, size=11.0, row_px=None):
    """Rows of strings -> Spreadsheet + TechDraw spreadsheet view (real columns)."""
    sh = doc.addObject("Spreadsheet::Sheet", name)
    cols = "ABCDEFGH"
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            sh.set(f"{cols[c]}{r}", "'" + str(val))  # leading ' keeps numbers as text
    for c, w in enumerate(widths_mm):
        sh.setColumnWidth(cols[c], int(w * 3.78))  # px at 96 dpi
    if row_px:
        for r in range(1, len(rows) + 1):
            sh.setRowHeight(str(r), row_px)
    doc.recompute()
    v = doc.addObject("TechDraw::DrawViewSpreadsheet", name + "View")
    v.Source = sh
    v.CellStart = "A1"
    v.CellEnd = f"{cols[len(rows[0]) - 1]}{len(rows)}"
    v.TextSize = size
    page.addView(v)
    v.X, v.Y = x, y
    return v


def label(doc, page, text, x, y):
    return note(doc, page, [text], x, y, 4)


def new_page(doc, name, title, dwg, sheet_no):
    page = doc.addObject("TechDraw::DrawPage", name)
    t = doc.addObject("TechDraw::DrawSVGTemplate", name + "Tpl")
    t.Template = TEMPLATE
    page.Template = t
    fields = {  # editable fields of the ASME ANSIB_Landscape template
        "DrawingTitle1": title, "DrawingTitle2": SUBTITLE, "DrawingTitle3": "",
        "drawing_number": dwg, "revision_index": "A", "scale": "AS NOTED",
        "Sheet": f"{sheet_no} OF {N_SHEETS}", "DrawnBy": "R. A. Popp", "CheckedBy": "",
        "Approved1": "", "Approved2": "", "CompanyName": "1500 W AUTOMATED ANTENNA TUNER",
        "CompanyAddress": "R. A. POPP, KF0OWR", "Code": "", "Weight": "",
    }
    texts = dict(t.EditableTexts)
    texts.update({k: v for k, v in fields.items() if k in texts})
    t.EditableTexts = texts
    # the license and Source Location (CERN-OHL-W v2 §4.1), centered in the title block's empty top-left cell
    note(doc, page, ["LICENSE: CERN-OHL-W-2.0", "GITHUB.COM/DRIADOR/ANTENNA-TUNER"], 288.5, 59.6, 2.0)
    return page


def view(doc, page, src, direction, scale, x, y, name, xdir=None, coarse=False, hidden=False):
    v = doc.addObject("TechDraw::DrawViewPart", name)
    page.addView(v)
    v.Source = [src]
    v.Direction = App.Vector(*direction)
    if xdir:
        v.XDirection = App.Vector(*xdir)
    v.ScaleType = "Custom"
    v.Scale = scale
    v.CoarseView = coarse
    v.HardHidden = hidden
    v.X, v.Y = x, y
    return v


def load(doc, path):
    """STEP file -> one Part::Feature (compounds stay one shape, so a view sees every part)."""
    shape = Part.Shape()
    shape.read(os.path.join(OUT, path))
    obj = doc.addObject("Part::Feature", os.path.splitext(path)[0].replace("-", "_"))
    obj.Shape = shape
    if obj.ViewObject:  # drawing source only; keep the 3-D view uncluttered
        obj.ViewObject.Visibility = False
    return obj


DRAFT = "DRAFT - DERIVED FROM DESIGN LOG 5.3a REV 3.7c. NOT FOR FABRICATION."
UNITS = "DIMENSIONS IN INCHES. BREAK SHARP EDGES 0.01 UNLESS NOTED."


# ------------------------------------------------------------------ sheets
def overlay(doc, page, base, step, name, scale=None, x=None, y=None):
    """Section hatching: a view of the hatch-line STEP laid exactly over `base` (same direction,
    scale and position; the overlay's corner anchors give it the same centering), in thin lines."""
    ov = view(doc, page, load(doc, step), tuple(base.Direction), scale or base.Scale,
              base.X if x is None else x, base.Y if y is None else y, name, tuple(base.XDirection))
    if ov.ViewObject:
        ov.ViewObject.LineWidth = 0.13
    return ov


def near_vertex(view, pt, center):
    """'VertexN' nearest the model point pt (in, view plane) for a view centered on `center` (in)."""
    vs = verts(view)
    tx, ty = (pt[0] - center[0]) * IN * view.Scale, (pt[1] - center[1]) * IN * view.Scale
    return "Vertex%d" % min(range(len(vs)), key=lambda k: (vs[k].x - tx) ** 2 + (-vs[k].y - ty) ** 2)


def tag(doc, page, view, letter, pt, center, offset, kink=None):
    """Lettered balloon on `view`: leader from model point `pt` (in, view plane), bubble `offset` page mm away.
    `center` is the model point (in) TechDraw centers the view on (its 2-D bounding-box center). kink: the
    leader's horizontal shoulder, mm (0: none, so it cannot run under a neighboring bubble)."""
    b = doc.addObject("TechDraw::DrawViewBalloon", "Tag")
    b.SourceView = view
    page.addView(b)  # adding to the page resets the position, so set it afterwards
    k = 1 / view.Scale  # balloon coordinates are unscaled view units
    ox, oy = (pt[0] - center[0]) * IN, (pt[1] - center[1]) * IN
    b.OriginX, b.OriginY = ox, oy
    b.X, b.Y = ox + offset[0] * k, oy + offset[1] * k
    b.Text = letter
    b.BubbleShape = "Circular"
    if kink is not None:
        b.KinkLength = kink
    return b


def polar(r, deg):
    return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))


def sheet_assembly(doc):
    asm = load(doc, "roller.step")
    cut = load(doc, "roller-section-bb.step")
    page = new_page(doc, "S100", "ROLLER ASSEMBLY", "TUNER-L-100", 1)
    front = view(doc, page, asm, (0, -1, 0), 0.5, 95, 150, "AsmFront", (1, 0, 0), coarse=True)
    sec = view(doc, page, cut, (0, 0, 1), 0.5, 215, 195, "SectionBB", (1, 0, 0), coarse=True)
    hbb = overlay(doc, page, sec, "hatch-bb.step", "HatchBB")
    doc.recompute()
    settle([front, sec, hbb])
    overall(doc, page, front, gap=12)
    # item balloons on the elevation (view x = model x, view y = model z, centered on the 2-D bbox)
    ec = ((P["ASM_X"][0] + P["ASM_X"][1]) / 2,
          (P["SHAFT_Z"][0] + max(P["ROD_Z"][1], P["SHAFT_Z"][1])) / 2)

    def at(item, x, z, bx, by, kink=None):  # leader from model (x, z) to a bubble at page (bx, by)
        px, py = 95 + (x - ec[0]) * IN * 0.5, 150 + (z - ec[1]) * IN * 0.5
        tag(doc, page, front, str(item), (x, z), ec, (bx - px, by - py), kink)

    zA, zB = P["Z_PLATE_A"], P["Z_PLATE_B"]
    # The top row: leaders straight out of their bubbles (a shoulder runs under the next bubble), 16 apart.
    # 30, 9 and 8 all end on the bus-rod line (x 130 on the page): on each side of it the bubble further out
    # takes the lower end, so no two leaders cross.
    top = 247
    at(10, P["POST_XY"][0][0], 5.5, 96, top, kink=0)             # frame post, in front of the wiper
    at(30, P["BUS_R"], (zA[1] + P["BUS_Z"][0]) / 2, 112, top, kink=0)
    # guide rod sits directly behind the bus rod here; only its stub above plate B is visible
    at(9, P["BUS_R"], zB[1] + 0.2, 128, top, kink=0)
    at(8, P["BUS_R"], 5.0, 144, top, kink=0)
    at(14, P["CARR_X"][1] - 0.05, P["WIPER_Z"], 160, top, kink=0)
    at(1, -1.8, (zB[0] + zB[1]) / 2, 34, 222)
    at(4, -2.5, P["Z_TOP_CAGE"] - 0.25, 34, 208)
    at(3, -2.0, 6.8, 34, 194)
    at(2, -2.4, 3.5, 34, 180)
    at(15, 0.55, (P["COLLAR_Z"][0] + P["COLLAR_Z"][1]) / 2, 34, 103)
    at(1, -1.8, (zA[0] + zA[1]) / 2, 34, 89)
    at(16, 0.5, (P["THRUST_Z"][0] + P["THRUST_Z"][1]) / 2, 34, 75)
    at(7, 0.0, P["SHAFT_Z"][0] + 0.4, 50, 62)
    # B-B cutting-plane markers on the elevation, at the wheel center
    z_lo, z_hi = P["SHAFT_Z"][0], max(P["ROD_Z"][1], P["SHAFT_Z"][1])
    y_b = 150 + (P["WIPER_Z"] - (z_lo + z_hi) / 2) * IN * 0.5
    # the letters outside the part: the right one clear of the carriage, short of the height dimension
    note(doc, page, ["B ——"], 95 - 52, y_b, 4)
    note(doc, page, ["—— B"], 95 + 52, y_b, 4)
    # detail D: the wiper corner of B-B, pre-cut in roller.py (a TechDraw detail of B-B never finishes)
    wcut = load(doc, "roller-section-bb-wiper.step")
    d = view(doc, page, wcut, (0, 0, 1), 1.3, 335, 207, "DetailD", (1, 0, 0), coarse=True)
    hd = overlay(doc, page, d, "hatch-bbw.step", "HatchD")
    doc.recompute()
    settle([d, hd], timeout=120)
    # balloons in detail D; the cut window is filled by plate A, so the view centers on the window
    wx, wy = P["WHEEL_X"], P["WIPER_Y"]
    dc = ((wx - 0.75 + P["CARR_X"][1] + 0.15) / 2, (P["CARR_Y"][0] + P["CARR_Y"][1]) / 2)
    # wheel (11) and fork (13) are ballooned on B-B, either side of the wiper, clear of the labels
    bc = ((P["ASM_X"][0] + P["ASM_X"][1]) / 2, 0)

    def on_bb(item, x, y, bx, by):  # leader from model (x, y) on B-B to a bubble at page (bx, by)
        px, py = 215 + (x - bc[0]) * IN * 0.5, 195 + (y - bc[1]) * IN * 0.5
        tag(doc, page, sec, item, (x, y), bc, (bx - px, by - py))

    on_bb("11", wx - 0.2, wy - 0.25, 266, 160)   # below 13, in the gap between B-B and detail D
    on_bb("13", P["BRIDGE_X"] + 0.4, wy, 273, 178)
    tag(doc, page, d, "14", (P["CARR_X"][1] - 0.08, P["CARR_Y"][0] + 0.08), dc, (14, -4))
    tag(doc, page, d, "8", (P["BUS_R"] + 0.19, 0), dc, (17, -4))
    tag(doc, page, d, "9", (P["BUS_R"] + 0.19, P["GUIDE_DY"]), dc, (17, 3))
    xw = math.sqrt((P["COIL_D"] / 2) ** 2 - 0.6 ** 2)
    tag(doc, page, d, "2", (xw, 0.6), dc, (-12, 12))
    names = {int(k): v[0] for k, v in META["items"].items()}
    shown = (1, 2, 3, 4, 7, 8, 9, 10, 11, 13, 14, 15, 16, 30)
    table(doc, page, "ItemIndex", [("ITEM", "ON THIS SHEET")] + [(str(i), names[i]) for i in shown],
          (11, 56), 203, 108, size=7.5, row_px=16)
    label(doc, page, "ELEVATION  SCALE 1:2", 95, 32)
    label(doc, page, "SECTION B-B  SCALE 1:2", 205, 147)
    label(doc, page, "DETAIL D - WIPER ON THE WINDING (B-B)  1.3:1", 335, 147)
    note(doc, page, [
        "NOTES:",
        f"1. {P['TURNS']} T #4 AWG SOLID Cu, Ag PLATED, 3 TPI, ON {P['COIL_D']:.2f} DIA TO WIRE CENTER.",
        f"2. PLATE TO PLATE {P['INNER_SPAN']:.3f}, OVERALL {P['Z_PLATE_B'][1] - P['Z_PLATE_A'][0]:.3f}"
        " (INCL. HELIX STAGGER +0.30, NOTCH +0.01).",
        f"3. BUS ROD {P['BUS_R']:.3f} FROM AXIS, HOT UP TO 9.3 kV PK, ON ULTEM PILLARS:",
        f"   {META['install']['BUS ROD TO DECK (AIR)']:.2f} AIR TO THE DECK, {META['install']['BUS ROD TO TOP PANEL (AIR)']:.2f}"
        " TO THE TOP PANEL (3.2).",
        "4. B-B CUTS AT THE WHEEL CENTER: THE WHEEL RIDES THE WIRE TOP, THE FORK SLIDES IN THE",
        "   CARRIAGE ON THE BUS + GUIDE RODS, AND THE WIRE DRAGS IT ALONG THE AXIS (TUNER-L-105).",
        "5. THE FRONT FRAME POST (10) HIDES THE WIPER IN THE ELEVATION - SEE B-B AND DETAIL D.",
        "6. MOUNTING: TUNER-L-109. HOLES: L-102. RETENTION: L-107. PARTS LIST: L-106.",
        DRAFT, UNITS,
    ], 318, 112, 2.3)


def sheet_rib(doc):
    rib = load(doc, "part-rib.step")
    page = new_page(doc, "S101", "ROLLER RIB - ULTEM 1000", "TUNER-L-101", 2)
    front = view(doc, page, rib, (0, -1, 0), 1.0, 165, 175, "RibFront", (1, 0, 0))
    top = view(doc, page, rib, (0, 0, 1), 1.0, 165, 120, "RibTop", (1, 0, 0))
    doc.recompute()
    settle([front, top])
    x0, x1, y0, y1 = bbox(front)
    tab = P["TAB_LEN"] * IN
    bl, br = extreme(front, -1, -1), extreme(front, 1, -1)
    vs = verts(front)

    def near(x, y):
        return "Vertex%d" % min(range(len(vs)), key=lambda k: (vs[k].x - x) ** 2 + (-vs[k].y - y) ** 2)

    tl, tr = near(x0 + tab, y1), near(x1 - tab, y1)
    tops = sorted((p.x, i) for i, p in enumerate(vs) if abs(-p.y - y1) < 0.01 and x0 + tab + 1 < p.x < x1 - tab - 1)
    n1, n2, nl = tops[0], tops[2], tops[-2]
    center_h = (P["RIB_SOLID"] - P["NOTCH_SEAT"] + P["NOTCH_R"]) * IN
    nc = near(n1[0], y0 + center_h)
    tabtop = near(x1, y0 + P["TAB_H"] * IN)
    dim(doc, page, front, "DistanceX", [bl, br], 0, y0 - 22)
    dim(doc, page, front, "DistanceX", [tl, tr], 0, y1 + 24)
    dim(doc, page, front, "DistanceX", [tl, f"Vertex{n1[1]}"], -(x1 - x0) / 2 + tab - 12, y1 + 12, fmt="A")
    a0 = (n1[0] - (x0 + tab)) / IN                      # dimension A on rib -01 (n = 0)
    dim(doc, page, front, "DistanceX", [f"Vertex{n1[1]}", f"Vertex{n2[1]}"], -(x1 - x0) / 2 + tab + 14, y1 + 12)
    dim(doc, page, front, "DistanceX", [f"Vertex{n1[1]}", f"Vertex{nl[1]}"], 0, y1 + 36)
    dim(doc, page, front, "DistanceY", [br, tr], x1 + 16, 0)
    dim(doc, page, front, "DistanceY", [br, tabtop], x1 + 6, -6)
    dim(doc, page, front, "DistanceY", [bl, nc], x0 - 12, 0)
    dim(doc, page, top, "DistanceY", [extreme(top, -1, -1), extreme(top, -1, 1)], x0 - 10, 0)

    det = doc.addObject("TechDraw::DrawViewDetail", "NotchDetail")
    page.addView(det)
    det.BaseView = front
    det.Source = front.Source
    det.Direction = front.Direction
    det.XDirection = front.XDirection
    det.AnchorPoint = App.Vector(n1[0] + P["NOTCH_R"] * IN, y0 + center_h, 0)
    det.Radius = 0.45 * IN
    det.ScaleType = "Custom"
    det.Scale = 3.0
    det.Reference = "A"
    det.X, det.Y = 362, 185
    doc.recompute()
    settle([det], timeout=60)
    e = circles(det).get(round(P["NOTCH_R"] * IN, 2))
    if e:
        dim(doc, page, det, "Radius", [e], 18, 18, fmt="R%.3f")

    depth = P["NOTCH_DEPTH"] + P["NOTCH_SEAT"]
    note(doc, page, [
        "NOTES:",
        f"1. MATERIAL ULTEM 1000 (PEI), 0.375 PLATE. QTY {P['N_RIBS']}.",
        f"2. {P['NOTCHES']} NOTCHES, R{P['NOTCH_R']:.3f} ROUND BOTTOM, {depth:.3f} DEEP. BREAK ALL CORNERS.",
        "   (DOC: R0.105 x 0.140. WIDER + DEEPER SO THE CURVED, CLIMBING WIRE SEATS",
        "   AT BOTH RIB FACES - CHECKED IN THE 3-D MODEL.)",
        f"3. FOR {P['COIL_D']:.2f} DIA TO WIRE CENTER, #4 AWG SOLID, {P['TURNS']} TURNS WOUND.",
        f"4. TABULATED PART: {P['N_RIBS']} RIBS -01 TO -{P['N_RIBS']:02d}. DIM A PER TABLE (HELIX STAGGER, {P['STAGGER']:.4f}",
        "   PER RIB); ALL OTHER DIMENSIONS COMMON. -01 SHOWN. ENGRAVE THE DASH NO. ON THE TAB;",
        "   FIT IN ORDER AROUND THE DISC, -01 IN THE L-103 SLOT ON +X.",
        "5. END TAB SIZE ASSUMED - MATCHES THE SLOTS ON TUNER-L-103.",
        "6. WIRE LOCKED IN EACH NOTCH WITH RTV SILICONE, MIL-A-46146 - SEE TUNER-L-107 NOTE 5.",
        DRAFT, UNITS,
    ], 150, 60, 2.6)
    label(doc, page, "DETAIL A  SCALE 3:1", 362, 140)
    label(doc, page, "FRONT (RIB -01 SHOWN)  SCALE 1:1", 165, 240)
    rows = [("DASH", "RIB n", "DIM A", "ENGRAVE")]
    for n in range(P["N_RIBS"]):
        rows.append((f"-{n + 1:02d}", str(n), f"{a0 + n * P['STAGGER']:.3f}", f"R{n + 1:02d}"))
    table(doc, page, "RibTab", rows, (16, 14, 20, 22), 362, 102, size=8.0, row_px=14)
    label(doc, page, "TOP  SCALE 1:1", 165, 108)


def sheet_end_plate(doc):
    plate = load(doc, "part-end-plate.step")
    page = new_page(doc, "S102", "END PLATE (BRACKET) A AND B", "TUNER-L-102", 3)
    sc = 0.8
    plan = view(doc, page, plate, (0, 0, 1), sc, 115, 170, "PlatePlan", (1, 0, 0), hidden=True)
    edge = view(doc, page, plate, (0, -1, 0), sc, 115, 85, "PlateEdge", (1, 0, 0), hidden=True)
    doc.recompute()
    settle([plan, edge])
    overall(doc, page, plan, gap=14)
    overall(doc, page, edge, x=False, gap=10)
    x_off = -P["PLATE_X0"]
    rows = [("HOLE", "X", "Y", "DIA", "X FROM -X EDGE, Y FROM CL")]
    for name, x, y, d, n in META["plate_holes"]:
        rows.append((name, f"{x + x_off:.3f}", f"{y:.3f}", f"{d:.3f}", n))
    table(doc, page, "HoleTable", rows, (12, 16, 16, 16, 78), 330, 212, size=9.0, row_px=18)
    # hole letters beside each hole (plan view is centered on the plate's bbox center)
    xc = P["PLATE_X0"] + P["PLATE_L"] / 2
    for name, x, y, d, _n in META["plate_holes"]:
        note(doc, page, [name], 115 + ((x - xc) * IN + d * IN / 2) * sc + 4, 170 + (y * IN + d * IN / 2) * sc + 3, 4)
    note(doc, page, [
        "NOTES:",
        "1. MATERIAL ULTEM 1000, 0.50 PLATE. QTY 2: A (BOTTOM, COLD END) AND B (TOP).",
        "2. LINE-BORE: CLAMP A AND B TOGETHER, DRILL + REAM ALL HOLES IN ONE SETUP.",
        "3. HOLE A: R8 (1.125 OD) - PLATE A LIGHT PRESS, BEARING FIXED WITH THRUST",
        "   COLLARS; PLATE B SAME BORE, BEARING SLIDES ON THE SHAFT (THERMAL GROWTH).",
        f"4. HOLE B TAKES THE BUS-ROD PILLAR (HOT ROD ABOVE). PLATE IS {P['PLATE_L']:.2f} LONG (DOC 6.5) FOR CREEPAGE -",
        "   PILLAR + PLATE TOP + EDGE = 2.74 TO THE DECK. >= 2.0 TO HOLES A, D-L ALSO HOLDS.",
        "8. EVERY CBORE IS ON THE OUTSIDE FACE (A: BOTTOM, B: TOP); HEADS AND NUTS SIT 0.02+ BELOW IT.",
        "5. HOLES F-L PLATE A ONLY (BLIND FROM BOTTOM): BOLTS UP THROUGH THE DECK, 2 DOWELS.",
        "6. METAL (INSERTS, DOWELS, SCREWS) >= 2.0 FROM HOLE B. D, E: CBORE OUTSIDE FACE.",
        "7. RETENTION OF BOTH ENDS: SEE TUNER-L-107.",
        DRAFT, UNITS,
    ], 318, 118, 2.5)
    label(doc, page, "PLAN (HIDDEN SHOWN)  SCALE 0.8:1", 115, 232)
    label(doc, page, "EDGE  SCALE 0.8:1", 115, 65)


def sheet_disc_hub(doc):
    disc = load(doc, "part-end-disc.step")
    hub = load(doc, "part-center-hub.step")
    page = new_page(doc, "S103", "CAGE END DISC AND CENTER HUB", "TUNER-L-103", 4)
    dplan = view(doc, page, disc, (0, 0, 1), 0.85, 102, 170, "DiscPlan", (1, 0, 0))
    dsec = load(doc, "part-end-disc-section.step")
    dedge = view(doc, page, dsec, (0, -1, 0), 1.0, 95, 70, "DiscSectionEE", (1, 0, 0))
    hee = overlay(doc, page, dedge, "hatch-ee.step", "HatchEE")
    hplan = view(doc, page, hub, (0, 0, 1), 1.0, 215, 200, "HubPlan", (1, 0, 0), hidden=True)
    hedge = view(doc, page, hub, (0, -1, 0), 1.0, 215, 140, "HubEdge", (1, 0, 0), hidden=True)
    doc.recompute()
    settle([dplan, dedge, hplan, hedge, hee])
    overall(doc, page, dedge, x=False, gap=8)
    overall(doc, page, hedge, x=False, gap=8)
    # section E-E: slot depth and the web left under it (view x = model x, y = model z, center (0, T/2))
    vs = verts(dedge)
    sc = (0, P["DISC_T"] / 2)

    def vtx(x, z):
        tx, ty = (x - sc[0]) * IN, (z - sc[1]) * IN
        return "Vertex%d" % min(range(len(vs)), key=lambda k: (vs[k].x - tx) ** 2 + (-vs[k].y - ty) ** 2)

    top_in, slot_bot, outer = vtx(P["SLOT_R0"], P["DISC_T"]), vtx(P["SLOT_R0"], P["DISC_T"] - P["SLOT_DEPTH"]), \
        vtx(P["BORE"] / 2, 0)  # any vertex on the outer face; the bottom face has none under the slot
    dim(doc, page, dedge, "DistanceY", [top_in, slot_bot], (P["SLOT_R0"] - 0.35) * IN, 14)
    dim(doc, page, dedge, "DistanceY", [slot_bot, outer], (P["SLOT_R0"] - 0.35) * IN, -14)
    tag(doc, page, dedge, "E", ((P["SLOT_R0"] + P["SLOT_R1"]) / 2, P["DISC_T"] - 0.1), sc, (8, 16))
    tag(doc, page, dedge, "B", (P["BORE"] / 2, P["DISC_T"] / 2), sc, (-6, 16))
    tag(doc, page, dedge, "D", (P["TERM_R"], P["DISC_T"] / 2), sc, (8, 16))
    for x in (95 - 70, 95 + 70):  # cutting plane E-E is the plan view's horizontal centerline
        note(doc, page, ["E"], x, 172, 4)
    o = (0, 0)
    tie = polar(P["TIE_R"], 45)
    tag(doc, page, dplan, "A", polar(P["DISC_D"] / 2, 150), o, (-10, 6))
    tag(doc, page, dplan, "B", (0, P["BORE"] / 2), o, (0, (2.15 - P["BORE"] / 2) * IN))
    tag(doc, page, dplan, "C", tie, o, tuple((a - b) * IN for a, b in zip(polar(2.15, 54), tie)))
    tag(doc, page, dplan, "D", (P["TERM_R"] + P["TERM_HOLE"] / 2, 0), o, (12, 9))
    slot = polar((P["SLOT_R0"] + P["SLOT_R1"]) / 2, 36)
    tag(doc, page, dplan, "E", slot, o, tuple((a - b) * IN for a, b in zip(polar(2.2, 18), slot)))
    tag(doc, page, hplan, "A", polar(P["HUB_D"] / 2, 150), o, (-9, 6))
    tag(doc, page, hplan, "B", (0, P["BORE"] / 2), o, (0, (1.8 - P["BORE"] / 2) * IN))
    tag(doc, page, hplan, "C", polar(P["TIE_R"], 45), o, (12, 12))
    tag(doc, page, hplan, "D", (P["HUB_D"] / 2 - 0.06, 0), o, (12, -6))
    tag(doc, page, hedge, "E", (0.9, 0), o, (10, 9))
    widths = (9, 30, 48, 44, 9)
    table(doc, page, "DiscTable", [
        ("TAG", "END DISC (QTY 2)", "SIZE", "LOCATION", "QTY"),
        ("A", "OD", f"⌀{P['DISC_D']:.3f}", "-", "1"),
        ("B", "BORE", f"⌀{P['BORE']:.3f} SLIP, NO KEY", "CENTER", "1"),
        ("C", "TIE-ROD HOLE", f"⌀{P['TIE_HOLE']:.3f} THRU, CSK #10 FH OUT", f"⌀{2 * P['TIE_R']:.3f} BC, 45 + n90 DEG", "4"),
        ("D", "TERMINAL HOLE", f"⌀{P['TERM_HOLE']:.3f} THRU", f"R{P['TERM_R']:.3f} ON +X", "1"),
        ("E", "RIB SLOT, BLIND", f"{P['SLOT_W']:.3f} W x {P['SLOT_DEPTH']:.3f} DP, INNER FACE",
         f"R{P['SLOT_R0']:.3f}-R{P['SLOT_R1']:.3f}, 36 DEG, 1ST ON +X", "10"),
        ("-", "THICKNESS", f"{P['DISC_T']:.3f}", "ULTEM 1000 PLATE", "-"),
    ], widths, 338, 222, size=8.0, row_px=18)
    table(doc, page, "HubTable", [
        ("TAG", "CENTER HUB (QTY 1)", "SIZE", "LOCATION", "QTY"),
        ("A", "OD", f"⌀{P['HUB_D']:.3f}", "-", "1"),
        ("B", "BORE", f"⌀{P['BORE']:.3f} SLIP", "CENTER", "1"),
        ("C", "TIE-ROD HOLE", f"⌀{P['TIE_HOLE']:.3f} THRU", f"⌀{2 * P['TIE_R']:.3f} BC, 45 + n90 DEG", "4"),
        ("D", "RIB SLOT, THRU", f"{P['SLOT_W']:.3f} W x {P['HUB_SLOT_DEPTH']:.3f} DP", "36 DEG, 1ST ON +X", "10"),
        ("E", "PIN CROSS-HOLE", f"⌀{P['PIN_D'] + 0.003:.3f} THRU, MATCH-DRILL", f"{P['PIN_ANG']} DEG FROM +X, MID-THK", "1"),
        ("-", "THICKNESS", f"{P['HUB_T']:.3f} (ASSUMED)", "ULTEM 1000 OR PTFE", "-"),
    ], widths, 338, 165, size=8.0, row_px=18)
    note(doc, page, [
        "NOTES:",
        "1. RIB TABS ARE A SLIP FIT IN THE SLOTS AND ARE CLAMPED BY THE TIE RODS - NO PRESS FIT.",
        "2. THE CAGE IS LOCATED ON THE SHAFT ONLY BY THE HUB PIN (E); DISC BORES ARE SLIP.",
        "3. MATCH-DRILL E WITH THE SHAFT IN PLACE AND THE CAGE CLAMPED - TUNER-L-107.",
        "4. DISC A: TERMINAL HOLE TAKES THE COLD END TO THE COLLAR LUG. DISC B: OPEN END,",
        "   BEAD OF RTV SILICONE (TUNER-L-107 NOTE 5).",
        DRAFT, UNITS,
    ], 338, 108, 2.5)
    label(doc, page, "END DISC - INNER FACE  SCALE 0.85:1", 102, 247)
    note(doc, page, ["SECTION E-E (AXIS, ON +X)  1:1", "SLOTS BLIND, HOLES THROUGH"], 95, 40, 4)
    label(doc, page, "CENTER HUB  SCALE 1:1", 300, 247)
    label(doc, page, "HUB EDGE (HIDDEN SHOWN)", 215, 122)


ROD_NOTES = {
    "shaft": ["SHAFT - QTY 1, C360 BRASS 1/2, Ag PLATED. NON-MAGNETIC ONLY.",
              f"1/8 CROSS-HOLE {P['HUB_Z'] - P['SHAFT_Z'][0]:.3f} FROM BOTTOM, MATCH-DRILL WITH HUB. "
              "BOTTOM 1.00 INTO OLDHAM HUB."],
    "bus-rod": ["BUS ROD - QTY 1, C360 BRASS 3/8, Ag PLATED, POLISHED. HOT. SPANS THE WHEEL TRAVEL ONLY.",
                "3/8-24 x 0.40 BOTH ENDS INTO THE PILLARS. STOP COLLARS; LUG UNDER A BRASS NUT AT TOP."],
    "pillar-lower": ["BUS-ROD PILLARS - QTY 2 (LOWER ON PLATE A, UPPER UNDER PLATE B), ULTEM 1000 3/4.",
                     "TAP 3/8-24 x 0.40 TOP. 3/8 x 0.50 STUD THROUGH THE PLATE, 3/8-16 PEEK NUT IN CBORE."],
    "guide-rod": ["GUIDE ROD - QTY 1, ULTEM 1000 3/8. CARRIAGE ANTI-ROTATION. BOTTOM 3/8-16 x 0.40",
                  "INTO PLATE A (BLIND TAP - NOTHING BELOW PLATE A); TOP 3/8-16, PEEK NUT ON PLATE B."],
    "tie-rod": ["TIE ROD - QTY 4, ULTEM 1000 3/8. 0.010 SHORT OF EACH DISC FACE SO THE",
                "SCREWS CLAMP THE RIBS. TAP #10-24 x 0.50 DP BOTH ENDS. MATCHED SET +/-0.002."],
    "frame-post": ["FRAME POST - QTY 2, ULTEM 1000 3/4. TAP 1/4-20 x 0.75 DP BOTH ENDS.",
                   "SETS PLATE A TO B SPACING - FACE BOTH POSTS TOGETHER."],
}


def sheet_rods(doc):
    page = new_page(doc, "S104", "SHAFT, RODS AND FRAME POSTS", "TUNER-L-104", 5)
    names = ["shaft", "bus-rod", "guide-rod", "tie-rod", "frame-post", "pillar-lower", "pillar-upper"]
    pos = {n: (115, 248 - k * 34) for k, n in enumerate(names[:5])}
    pos.update({"pillar-lower": (70, 78), "pillar-upper": (150, 78)})
    views = []
    for n in names:
        src = load(doc, f"part-{n}.step")
        sc = 1.0 if n.startswith("pillar") else 0.5
        views.append(view(doc, page, src, (0, -1, 0), sc, *pos[n], f"Rod_{n}", (0, 0, 1)))
    doc.recompute()
    settle(views)
    for k, (n, v) in enumerate(zip(names, views)):
        x0, x1, y0, y1 = bbox(v)
        dim(doc, page, v, "DistanceX", [extreme(v, -1, -1), extreme(v, 1, -1)], 0, y0 - 7)
        dim(doc, page, v, "DistanceY", [extreme(v, 1, -1), extreme(v, 1, 1)], x1 + 9, 0, fmt="⌀%.3f")
        if n in ROD_NOTES:
            note(doc, page, ROD_NOTES[n], 325, pos[n][1] if not n.startswith("pillar") else 78, 2.8)
    note(doc, page, ["RODS 1:2, PILLARS 1:1.", DRAFT, UNITS], 110, 42, 3.0)


def sheet_wiper(doc):
    page = new_page(doc, "S105", "WIPER - WHEEL, FORK, CARRIAGE", "TUNER-L-105", 6)
    wheel = load(doc, "part-wheel.step")
    fork = load(doc, "part-fork.step")
    carr = load(doc, "part-carriage.step")
    wp = view(doc, page, wheel, (0, 0, 1), 2.0, 50, 215, "WheelPlan", (1, 0, 0))
    we = view(doc, page, wheel, (0, -1, 0), 2.0, 50, 160, "WheelEdge", (1, 0, 0))
    fp = view(doc, page, fork, (0, 0, 1), 2.0, 160, 215, "ForkPlan", (1, 0, 0))
    fe = view(doc, page, fork, (0, -1, 0), 2.0, 160, 160, "ForkEdge", (1, 0, 0))
    cp = view(doc, page, carr, (0, 0, 1), 1.5, 280, 200, "CarrPlan", (1, 0, 0), hidden=True)
    ce = view(doc, page, carr, (0, -1, 0), 1.5, 345, 200, "CarrEdge", (1, 0, 0), hidden=True)
    doc.recompute()
    settle([wp, we, fp, fe, cp, ce])
    overall(doc, page, we, x=False, gap=8)
    overall(doc, page, fp, gap=8)
    overall(doc, page, fe, x=False, gap=8)
    overall(doc, page, cp, gap=8)
    overall(doc, page, ce, x=False, gap=8)
    wx, wy = P["WHEEL_X"], P["WIPER_Y"]
    r = P["WHEEL_OD"] / 2
    tag(doc, page, wp, "A", polar(r, 135), (0, 0), (-8, 8))
    tag(doc, page, wp, "B", (0, P["AXLE_D"] / 2), (0, 0), (10, 14))
    tag(doc, page, we, "C", (-r + 0.02, 0), (0, 0), (-10, 8))
    x_end = P["CARR_X"][1] - wx + 0.30
    fc = ((x_end - 0.2) / 2, 0)
    tag(doc, page, fp, "A", (0, 0), fc, (-9, -19))
    tag(doc, page, fp, "B", (0.25, 0.2), fc, (2, 10))
    tag(doc, page, fp, "C", (1.2, P["FORK_BAR"][0] / 2), fc, (0, 12))
    tag(doc, page, fe, "D", (P["BRIDGE_X"] - wx + 0.06, 0.2), (fc[0], 0), (0, 12))
    # fork arms (cheeks): thickness, gap, length, bridge, width, end radius
    zc, t = P["WHEEL_W"] / 2 + P["CHEEK_GAP"] + P["CHEEK_T"] / 2, P["CHEEK_T"]
    xj = P["BRIDGE_X"] - wx
    ec = (fc[0], 0)
    up, lo = zc + t / 2, zc - t / 2
    xl = (-0.2 - ec[0]) * IN * fe.Scale              # left edge of the edge view, page mm from its center
    dim(doc, page, fe, "DistanceY", [near_vertex(fe, (-0.2, up), ec), near_vertex(fe, (-0.2, lo), ec)],
        xl - 7, zc * IN * fe.Scale + 4)
    dim(doc, page, fe, "DistanceY", [near_vertex(fe, (-0.2, lo), ec), near_vertex(fe, (-0.2, -lo), ec)],
        xl - 16, 0)
    # arm length and bridge thickness below the edge view, clear of balloon D above it
    dim(doc, page, fe, "DistanceX", [near_vertex(fe, (-0.2, -up), ec), near_vertex(fe, (xj, -up), ec)],
        (xj / 2 - 0.1 - ec[0]) * IN * fe.Scale, -(up * IN * fe.Scale + 7))
    dim(doc, page, fe, "DistanceX", [near_vertex(fe, (xj, -up), ec), near_vertex(fe, (xj + 0.125, -up), ec)],
        (xj + 0.06 - ec[0]) * IN * fe.Scale + 8, -(up * IN * fe.Scale + 15))
    dim(doc, page, fp, "DistanceY", [near_vertex(fp, (xj + 0.125, 0.2), fc), near_vertex(fp, (xj + 0.125, -0.2), fc)],
        (-0.2 - fc[0]) * IN * fp.Scale - 20, 0)
    e_r = circles(fp).get(round(0.2 * IN, 2))
    if e_r:
        dim(doc, page, fp, "Radius", [e_r], (-0.2 - fc[0]) * IN * fp.Scale - 4, 14, fmt="R%.3f")
    cc = ((P["CARR_X"][0] + P["CARR_X"][1]) / 2 - wx, (P["CARR_Y"][0] + P["CARR_Y"][1]) / 2 - wy)
    tag(doc, page, cp, "A", (P["BUS_R"] - wx, -wy), cc, (-16, 0))
    tag(doc, page, cp, "B", (P["BUS_R"] - wx, P["GUIDE_DY"] - wy), cc, (-16, 0))
    tag(doc, page, cp, "C", (cc[0], 0), cc, (-16, -4))
    gap = 2 * (P["WHEEL_W"] / 2 + P["CHEEK_GAP"])
    table(doc, page, "WiperTable", [
        ("PART", "TAG", "FEATURE", "SIZE", "NOTE"),
        ("WHEEL", "A", "OD", f"⌀{P['WHEEL_OD']:.3f}", "BRASS OR Cu, Ag PLATED"),
        ("WHEEL", "B", "BORE", f"⌀{P['AXLE_D'] + 0.004:.4f}", "RUNS ON THE 3/16 AXLE"),
        ("WHEEL", "C", "GROOVE", f"R{P['GROOVE_R']:.3f} x {P['GROOVE_DEPTH']:.3f} DP", "CENTERED; DEPTH CAPPED (NOTE 1)"),
        ("WHEEL", "-", "WIDTH", f"{P['WHEEL_W']:.3f}", ""),
        ("FORK", "A", "AXLE HOLE", f"⌀{P['AXLE_D'] + 0.004:.4f} THRU BOTH CHEEKS", "ON THE WHEEL AXIS"),
        ("FORK", "B", "CHEEK", f"0.400 W x {P['CHEEK_T']:.4f} T, R0.200 END", f"2 PLACES, {gap:.3f} APART"),
        ("FORK", "C", "BAR", f"{P['FORK_BAR'][0]:.3f} x {P['FORK_BAR'][1]:.3f}", f"SLIDES IN CARRIAGE, {P['FORK_TRAVEL']:.2f} TRAVEL"),
        ("FORK", "D", "BRIDGE", "0.125 x 0.400", f"{P['BRIDGE_X'] - wx:.3f} FROM THE AXLE"),
        ("CARRIAGE", "A", "BUS-ROD BORE", f"⌀{P['BUS_D'] + 0.01:.3f} THRU", "Ag PLATED - CURRENT PATH"),
        ("CARRIAGE", "B", "GUIDE-ROD BORE", f"⌀{P['GUIDE_D'] + 0.02:.3f} THRU", f"{P['GUIDE_DY']:.3f} FROM A"),
        ("CARRIAGE", "C", "FORK SLOT", f"{P['FORK_BAR'][0] + 0.01:.3f} x {P['FORK_BAR'][1] + 0.01:.3f} THRU",
         f"ON THE WHEEL LINE, {abs(wy):.3f} FROM A"),
    ], (22, 9, 34, 56, 72), 140, 85, size=8.0, row_px=18)
    note(doc, page, [
        "NOTES - ALL WIPER GEOMETRY ASSUMED; 5.3a SPECIFIES FUNCTION ONLY.",
        "1. FLANGES REACH (WIRE TOP - GROOVE DEPTH) AND MUST CLEAR THE RIB TOPS 1/16",
        f"   BELOW THE WIRE: {P['WHEEL_AXIS_R'] - P['WHEEL_OD'] / 2 - P['RIB_OUTER_R']:.3f} AS DRAWN.",
        "2. CHEEKS STOP 0.20 INBOARD OF THE AXLE TO CLEAR THE NEIGHBORING TURNS.",
        "3. CURRENT: Ag SHOE ON THE WHEEL FACE + FLAT BRAID TO THE CARRIAGE.",
        "   NEVER THROUGH THE AXLE OR SPRING (5.3a). AXLE 303 SST, 3/16 x 0.60.",
        "4. 3-5 LB COMPRESSION SPRING BEHIND THE FORK BAR - NOT DRAWN. IT ACTS",
        f"   ~11 DEG OFF RADIAL (WHEEL LINE {abs(wy):.2f} OFF THE BUS-ROD RADIUS).",
        "5. HOW IT RUNS ON THE COIL: TUNER-L-100 SECTION B-B, DETAIL D.",
        DRAFT, UNITS,
    ], 338, 105, 2.5)
    label(doc, page, "WHEEL  2:1", 50, 245)
    label(doc, page, "FORK  2:1", 160, 245)
    label(doc, page, "CARRIAGE  1.5:1 (HIDDEN SHOWN)", 312, 245)


def sheet_exploded(doc):
    ex = load(doc, "roller-exploded.step")
    page = new_page(doc, "S106", "EXPLODED VIEW AND PARTS LIST", "TUNER-L-106", 7)
    iso = view(doc, page, ex, (1, -1, 0.8), 0.25, 125, 150, "Iso", (1, 1, 0))
    doc.recompute()
    settle([iso])
    # balloons: TechDraw's projection of each item's anchor, re-centered the way TechDraw
    # centers the view (on the 2-D bounding box of the projected geometry)
    pts = [iso.projectPoint(vx.Point) for vx in ex.Shape.Vertexes]
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    placed = []
    for item, a in sorted(META["anchors"].items(), key=lambda t: int(t[0])):
        pt = iso.projectPoint(App.Vector(*a))
        placed.append((item, (pt.x - cx) * iso.Scale, (pt.y - cy) * iso.Scale))
    # balloons in two tidy columns, left and right of the view, ordered top to bottom
    half_w = (max(p.x for p in pts) - min(p.x for p in pts)) * iso.Scale / 2
    for side in (-1, 1):
        col = sorted((t for t in placed if (t[1] >= 0) == (side > 0)), key=lambda t: -t[2])
        for n, (item, u, v) in enumerate(col):
            b = doc.addObject("TechDraw::DrawViewBalloon", "Balloon")
            b.SourceView = iso
            page.addView(b)  # adding to the page resets the position, so set it afterwards
            k = 1 / iso.Scale  # balloon coordinates are unscaled view units
            b.OriginX, b.OriginY = u * k, v * k
            b.X = side * (half_w + 14) * k
            b.Y = (60 - n * 120 / max(len(col) - 1, 1)) * k
            b.Text = str(item)
            b.BubbleShape = "Circular"
    rows = [("ITEM", "QTY", "DESCRIPTION", "MATERIAL", "DWG")]
    for k in sorted(META["items"], key=int):
        name, qty, mat, dwg = META["items"][k]
        rows.append((k, qty, name, mat, dwg))
    table(doc, page, "PartsList", rows, (11, 10, 64, 66, 26), 322, 192, size=8.5, row_px=16)
    note(doc, page, [
        "NOTES:",
        "1. EXPLODED ALONG THE ASSEMBLY ORDER: CAGE (3-6) ON THE SHAFT (7), WINDING (2)",
        "   THREADED INTO THE NOTCHES, THEN PLATES (1), RODS (8-10) AND WIPER (11-14).",
        "2. ONE OF EACH REPEATED PART IS BALLOONED. HARDWARE (19-28) NOT SHOWN.",
        "3. WINDING (2) DRAWN AS 18 RINGS FOR CLARITY; TRUE HELIX ON TUNER-L-100.",
        DRAFT,
    ], 322, 105, 2.8)
    label(doc, page, "ISOMETRIC, EXPLODED  SCALE 1:4", 125, 32)


RETENTION = [
    ("JOINT", "METHOD", "FIT / HARDWARE"),
    ("RIB TAB IN END-DISC SLOT", "SLIP FIT, CLAMPED BY TIE RODS - NOT A PRESS FIT",
     "0.375 TAB / 0.380 SLOT. TAB 0.010 SHORT OF SLOT BOTTOM; RIB SHOULDERS BEAR ON DISC"),
    ("DISC A TO DISC B (CAGE)", "4 TIE RODS IN TENSION; THE 10 RIBS ARE THE SPACERS",
     "RODS 0.010 SHORT EACH END. #10-24 PEEK FLAT HEAD x 8. RIBS A MATCHED SET +/-0.002"),
    ("RIB INNER EDGE TO HUB", "HUB SLOTS KEY THE RIBS TANGENTIALLY", "0.380 x 0.125 SLOTS, SLIP"),
    ("CAGE TO SHAFT", "1/8 BRASS CROSS-PIN THROUGH HUB AND SHAFT", "ONLY FIXED POINT: TORQUE + AXIAL. CAGE GROWS BOTH WAYS"),
    ("END DISCS TO SHAFT", "SLIP, NO KEY", "0.502 BORE ON 0.500 SHAFT"),
    ("COIL COLD END (DISC A)", "RING LUG TO THE CONTACT COLLAR FACE", "#8-32 BRASS SCREW. COLLAR 0.02 BELOW DISC A"),
    ("COIL OPEN END (DISC B)", "INTO THE 0.250 TERMINAL HOLE", "BEAD OF RTV SILICONE (NOTE 5)"),
    ("WIRE IN RIB NOTCHES", "A DAB OF RTV SILICONE AT EVERY RIB CROSSING", "OR PTFE LACING. NOT CERAMIC CEMENT (NOTE 5)"),
    ("SHAFT AT PLATE A (FIXED)", "R8 LIGHT PRESS IN PLATE; COLLAR ABOVE, THRUST COLLAR BELOW",
     "PTFE WASHER 1/32 EACH SIDE. SETS THE SHAFT AXIALLY"),
    ("SHAFT AT PLATE B (FREE)", "R8 LIGHT PRESS IN PLATE; INNER RACE SLIDES ON SHAFT", "THERMAL GROWTH ALLOWED"),
    ("PLATE A TO DECK", "4 x #10-24 SHCS UP THROUGH THE DECK + 2 x 3/16 DOWELS",
     "BRASS HEAT-SET INSERTS IN PLATE A. ALL >= 2.0 FROM BUS ROD"),
    ("PLATE B TO PLATE A", "2 FRAME POSTS, 1/4-20 SHCS EACH END", "POSTS SET THE SPACING; FACE AS A PAIR"),
    ("BUS ROD (HOT)", "THREADED INTO TWO ULTEM PILLARS; PILLAR STUDS + PEEK NUTS IN THE PLATES",
     f"{META['install']['BUS ROD TO DECK (AIR)']:.2f} AIR TO DECK, {META['install']['BUS ROD TO TOP PANEL (AIR)']:.2f} TO TOP PANEL"),
    ("GUIDE ROD (ULTEM)", "THREADED INTO PLATE A (BLIND); PEEK NUT ON PLATE B, SNUG ONLY",
     "NOTHING PROTRUDES BELOW PLATE A. NEVER SET SPACING WITH RODS"),
    ("PLATE A UNDERSIDE", "FLAT ON THE DECK: STUD + POST SCREWS IN CBORES, ROD BLIND",
     "FIT POST SCREWS, PILLAR NUT, GUIDE ROD BEFORE BOLTING DOWN"),
]


def sheet_retention(doc):
    page = new_page(doc, "S107", "END RETENTION - SECTION A-A", "TUNER-L-107", 8)
    # pre-cut in roller.py at the plane through the axis and the bus rod (y = 0), viewed from -Y
    sec = view(doc, page, load(doc, "roller-section-aa.step"), (0, -1, 0), 0.4, 75, 150, "SectionAA",
               (1, 0, 0), coarse=True)
    haa = overlay(doc, page, sec, "hatch-aa.step", "HatchAA")
    doc.recompute()
    settle([sec])
    # details of each end, anchored on the section (view coords centered on its 2-D bbox, +y up)
    # the section is centered on the cut shape's 2-D bounding box (model X across, Z up)
    xmin, xmax = P["ASM_X_MOUNT"]
    xc = (xmin + xmax) / 2 * IN
    zc = (P["SHAFT_Z"][0] + max(P["ROD_Z"][1], P["SHAFT_Z"][1])) / 2 * IN
    dets = []
    for ref, z, y in (("B", P["Z_TOP_CAGE"] + 0.3, 205), ("C", -0.75, 95)):
        d = doc.addObject("TechDraw::DrawViewDetail", "Detail" + ref)
        page.addView(d)
        d.BaseView = sec
        d.Source = sec.Source
        d.Direction = sec.Direction
        d.XDirection = sec.XDirection
        d.AnchorPoint = App.Vector(0.6 * IN - xc, z * IN - zc, 0)
        d.Radius = 1.25 * IN
        d.ScaleType = "Custom"
        d.Scale = 1.0
        d.Reference = ref
        d.X, d.Y = 185, y
        dets.append(d)
    hdet = [overlay(doc, page, dd, f"hatch-aa-{dd.Reference}.step", "Hatch" + dd.Reference) for dd in dets]
    doc.recompute()
    settle(dets + hdet + [haa], timeout=120)
    label(doc, page, "SECTION A-A (AXIS + BUS ROD)  1:2.5", 75, 32)
    label(doc, page, "DETAIL B - TOP END  1:1", 185, 248)
    label(doc, page, "DETAIL C - BOTTOM END  1:1", 185, 52)
    table(doc, page, "Retention", RETENTION, (36, 62, 70), 322, 205, size=6.5, row_px=20)
    note(doc, page, [
        "NOTES:",
        "1. NO PRESS OR INTERFERENCE FITS IN ULTEM EXCEPT THE R8 BEARINGS (LIGHT) AND DOWELS:",
        "   ULTEM IS NOTCH-SENSITIVE AND GROWS ~2.8x AS MUCH AS BRASS (CTE).",
        "2. ASSEMBLY: RIBS INTO DISC A, HUB ON, DISC B ON, TIE RODS + SCREWS (SNUG, ~10 IN-LB).",
        "   SLIDE CAGE ON SHAFT, MATCH-DRILL 1/8 THROUGH HUB + SHAFT, PIN. THREAD + CEMENT WINDING.",
        "3. CONTACT COLLAR (15): 1.25 OD x 0.70, SPLIT, Ag PLATED. FINGER TRACK ON OD, #8-32 TAP",
        "   IN TOP FACE FOR THE COLD-END LUG, UNDERSIDE IS THE UPPER THRUST FACE FOR BEARING A.",
        f"4. HUB PIN (17): 1/8 BRASS x {P['PIN_LEN']:.3f}, 0.03 BELOW THE HUB SURFACE EACH SIDE.",
        "5. CEMENT: NEUTRAL-CURE ELECTRONIC RTV SILICONE TO MIL-A-46146 (DOWSIL 3145 OR MOMENTIVE",
        "   RTV162). FLEXIBLE ACROSS THE Cu/ULTEM CTE MISMATCH, LOW RF LOSS, TRACKING RESISTANT.",
        "   SMALL DAB ONLY - DO NOT FILL THE NOTCH. CLEAN WITH IPA. DO NOT USE: ACETOXY (VINEGAR)",
        "   RTV - CORRODES Cu, TARNISHES Ag; CERAMIC CEMENT - RIGID, POROUS; EPOXY - LOSSY,",
        "   CARBONISES; CYANOACRYLATE; ANAEROBIC THREADLOCKER ON PEEK OR ULTEM (STRESS-CRAZES).",
        DRAFT, UNITS,
    ], 322, 118, 2.3)


def sheet_coupler(doc):
    asm = load(doc, "oldham.step")
    ex = load(doc, "oldham-exploded.step")
    hub = load(doc, "part-oldham-hub-roller.step")
    disc = load(doc, "part-oldham-disc.step")
    page = new_page(doc, "S108", "COUPLER B - DELRIN OLDHAM (REF)", "TUNER-L-108", 9)
    a = view(doc, page, asm, (0, -1, 0), 1.0, 60, 168, "OldhamElev", (1, 0, 0))
    e = view(doc, page, ex, (1, -1, 0.8), 0.8, 150, 165, "OldhamIso", (1, 1, 0))
    hp = view(doc, page, hub, (0, 0, 1), 2.0, 255, 215, "HubFace", (1, 0, 0))
    he = view(doc, page, hub, (0, -1, 0), 2.0, 330, 215, "HubSide", (1, 0, 0), hidden=True)
    dp = view(doc, page, disc, (0, 0, 1), 2.0, 255, 158, "DiscFace", (1, 0, 0))
    de = view(doc, page, disc, (0, -1, 0), 2.0, 330, 158, "DiscSide", (1, 0, 0))
    doc.recompute()
    settle([a, e, hp, he, dp, de])
    overall(doc, page, he, x=False, gap=8)
    overall(doc, page, de, x=False, gap=8)
    tag(doc, page, hp, "A", (-0.18, 0.18), (0, 0), (-16, 10))
    tag(doc, page, hp, "B", (0.4, P["OLD_SLOT_W"] / 2), (0, 0), (10, 10))
    pin_from_back = P["OLD_HUB_L"] / 2 - 0.1
    tag(doc, page, he, "C", (0.45, pin_from_back), (0, P["OLD_HUB_L"] / 2), (-6, -22))  # below, clear of the 0.750 dim
    tag(doc, page, dp, "D", (P["OLD_TONGUE_W"] / 2, 0.4), (0, 0), (10, 10))  # upper tongue runs along Y
    table(doc, page, "OldhamTable", [
        ("PART", "TAG", "FEATURE", "SIZE", "NOTE"),
        ("HUB, ROLLER", "A", "BORE", "⌀0.501", "1/2 BRASS ROLLER SHAFT, SLIP"),
        ("HUB, G10", "A", "BORE", "⌀0.376", "3/8 G10 DRIVE SHAFT, SLIP"),
        ("BOTH HUBS", "B", "SLOT ACROSS FACE", f"{P['OLD_SLOT_W']:.4f} W x {P['OLD_SLOT_D']:.3f} DP", "5/16 END MILL"),
        ("HUB, ROLLER", "C", "ROLL-PIN HOLE", f"⌀{P['OLD_PIN']['roller']:.3f} THRU HUB + SHAFT",
         f"{pin_from_back:.3f} FROM BACK FACE, MATCH-DRILL"),
        ("HUB, G10", "C", "ROLL-PIN HOLE", f"⌀{P['OLD_PIN']['g10']:.3f} THRU HUB + G10", "SAME, MATCH-DRILL"),
        ("BOTH HUBS", "-", "OD x LENGTH", f"⌀{P['OLD_OD']:.3f} x {P['OLD_HUB_L']:.3f}", "DELRIN 150 (ACETAL HOMOPOLYMER)"),
        ("DISC", "D", "TONGUES", f"{P['OLD_TONGUE_W']:.4f} W x {P['OLD_TONGUE_H']:.3f} H",
         "BOTH FACES, 90 DEG APART; LAP TO SLOT"),
        ("DISC", "-", "WEB", f"⌀{P['OLD_OD']:.3f} x {P['OLD_CORE_T']:.3f}", f"{P['OLD_GAP']:.3f} GAP TO EACH HUB"),
    ], (24, 9, 30, 52, 66), 140, 62, size=8.0, row_px=18)
    note(doc, page, [
        "COUPLER B (7.1a): DELRIN OLDHAM, ROLLER SHAFT TO 0.375 G10 SHAFT, UNDER THE DECK.",
        "SAME DESIGN ON C1/C2, BORE TO SUIT (NEVER DRILL A JENNINGS SHAFT - CLAMP OR USE ITS FLAT).",
        "1. RETENTION: ROLL PINS ONLY - NO SET SCREWS OR PRESS FIT (ACETAL CREEPS, ~110 PPM/C).",
        "2. BACKLASH = TONGUE/SLOT CLEARANCE 0.0005-0.001 (9 ITEM 21); DIAL-INDICATE AT ELEMENT.",
        "3. TAKES PARALLEL OFFSET, ~0.5-1 DEG ANGULAR ONLY. ROUGH, LET REST, THEN FINISH.",
        "4. LOAD 0.4-1.26 N-m: TONGUE BEARING < 3 MPa vs ~70 MPa YIELD.",
        "5. COUPLER A (MOTOR SIDE, REF): COMMERCIAL ALUMINUM ZERO-BACKLASH HELICAL OR",
        "   BELLOWS, CLAMP HUBS, 1/4 (NEMA 23) x 3/8 (G10), IN THE UTILITY LAYER.",
        DRAFT, UNITS,
    ], 330, 103, 2.3)
    label(doc, page, "ASSEMBLED  1:1", 60, 245)
    label(doc, page, "EXPLODED  0.8:1", 150, 245)
    label(doc, page, "HUB (ROLLER SIDE SHOWN)  2:1", 292, 245)
    label(doc, page, "CENTER DISC  2:1", 330, 140)


def sheet_install(doc):
    page = new_page(doc, "S109", "ROLLER INSTALLATION IN THE RF BAY", "TUNER-L-109", 10)
    sec_src = load(doc, "install-section.step")
    plan_src = load(doc, "install-plan.step")
    sec = view(doc, page, sec_src, (0, -1, 0), 0.25, 76, 167, "InstallSection", (1, 0, 0))   # 24" box: clear the label
    hff = overlay(doc, page, sec, "hatch-ff.step", "HatchFF")
    plan = view(doc, page, plan_src, (0, 0, 1), 0.2, 192, 205, "InstallPlan", (1, 0, 0))
    doc.recompute()
    settle([sec, plan])
    overall(doc, page, sec, gap=8)
    overall(doc, page, plan, gap=8)
    # detail G: deck, Oldham coupler B, shelf bushing - the RF-bay / utility-layer boundary
    zc = P["ENC_H"] / 2
    zmid = (P["Z_SHELF"] + P["Z_DECK"]) / 2
    g = doc.addObject("TechDraw::DrawViewDetail", "DetailG")
    page.addView(g)
    g.BaseView = sec
    g.Source = sec.Source
    g.Direction = sec.Direction
    g.XDirection = sec.XDirection
    g.AnchorPoint = App.Vector(P["ROLLER_X"] * IN, (zmid - zc) * IN, 0)
    g.Radius = ((P["Z_DECK"] - P["Z_SHELF"]) / 2 + 0.7) * IN     # spans shelf and deck (3.49 at 5.50 standoffs)
    g.ScaleType = "Custom"
    g.Scale = 0.35
    g.Reference = "G"
    g.X, g.Y = 330, 215
    hg = overlay(doc, page, g, "hatch-ff-G.step", "HatchG")
    doc.recompute()
    settle([g, hg, hff], timeout=120)
    note(doc, page, ["SECTION F-F (ROLLER AXIS)  1:4", "FRONT AT LEFT"], 80, 66, 4)
    label(doc, page, "PLAN, TOP OFF, FRONT AT LEFT  1:5", 192, 146)
    label(doc, page, "DETAIL G - DECK / COUPLER B / SHELF  0.35:1", 330, 180)
    rows = [("PART", "TAG", "DIA", "X FROM FRONT", "Y FROM RIGHT*", "NOTE")]
    for part, tag_, d, x, y, n in META["install_holes"]:
        rows.append((part, tag_, f"{d:.3f}", f"{x:.3f}", f"{y:.3f}", n))
    table(doc, page, "InstallHoles", rows, (12, 8, 12, 19, 19, 58), 214, 112, size=6.5, row_px=15)
    crow = [("CLEARANCE", "IN")] + [(k, f"{v:.2f}") for k, v in META["install"].items()]
    table(doc, page, "InstallClear", crow, (68, 11), 350, 146, size=6.5, row_px=15)
    note(doc, page, [
        "NOTES:",
        "1. ROLLER LOCATION IS PROPOSED (3.0 FLOOR PLAN): CONFIRM IN THE MOCK-UP, 9 ITEM 5.",
        "2. DATUMS: DECK FRONT + RIGHT EDGES; SHELF INSIDE FRONT + RIGHT WALLS.",
        "   *RIGHT = FACING THE FRONT.",
        "3. ISOLATION: THE BRASS SHAFT (DECK POTENTIAL) ENDS ABOVE THE GROUNDED SHELF; ONLY THE",
        "   G10 SHAFT CROSSES IT (7.1). CREEPAGE TIP-TO-SHELF "
        f"{META['install']['SHAFT TIP TO SHELF (CREEPAGE ALONG OLDHAM + G10)']:.2f} vs 2.0 MIN (5.50 STANDOFFS,",
        "   REV 3.7c); KEEP THE BRASS STUB SHORT ANYWAY (0.65 BELOW THE THRUST COLLAR).",
        "4. WINDING SHOWN AS RINGS; C1/C2 ARE REFERENCE ENVELOPES. MOTOR PER DECISION M-2.",
        DRAFT, UNITS,
    ], 346, 94, 2.1)


STEMS = {"S100": "L-100-assembly", "S101": "L-101-rib", "S102": "L-102-end-plate",
         "S103": "L-103-end-disc-hub", "S104": "L-104-rods", "S105": "L-105-wiper",
         "S106": "L-106-exploded", "S107": "L-107-retention", "S108": "L-108-coupler",
         "S109": "L-109-install"}


def main():
    doc = App.newDocument("RollerDrawings")
    for sname in doc.getEnumerationsOfProperty("UnitSystem"):
        if sname.lower().startswith("imperial decimal"):
            doc.UnitSystem = sname
    # ONLY=sheet_coupler (comma-separated) regenerates just those sheets' PDF/SVG and leaves the
    # combined .FCStd alone, which only a full run rewrites
    only = [n for n in os.environ.get("ONLY", "").split(",") if n]
    for fn in (sheet_assembly, sheet_rib, sheet_end_plate, sheet_disc_hub, sheet_rods, sheet_wiper,
               sheet_exploded, sheet_retention, sheet_coupler, sheet_install):
        if only and fn.__name__ not in only:
            continue
        try:
            fn(doc)
            log("ok", fn.__name__)
        except Exception:
            log("FAILED", fn.__name__, traceback.format_exc())
        log("  t", round(time.time() - T0, 1))
    doc.recompute()
    pump(40)
    # saving is what makes the document's inch unit system take effect on the dimensions;
    # a partial run saves to a throwaway file so the full set's .FCStd is left alone
    scratch = os.path.join(OUT, ".partial.FCStd")
    doc.saveAs(scratch if only else os.path.join(OUT, "roller-drawings.FCStd"))
    for p in [o for o in doc.Objects if o.TypeId == "TechDraw::DrawPage"]:
        p.ViewObject.show()
        pump(40)
        TechDrawGui.exportPageAsPdf(p, os.path.join(OUT, STEMS[p.Name] + ".pdf"))
        TechDrawGui.exportPageAsSvg(p, os.path.join(OUT, STEMS[p.Name] + ".svg"))
        log("exported", STEMS[p.Name], round(time.time() - T0, 1))
    if only:
        os.remove(scratch)
    log("done")


# TD_IMPORT=1 lets drawings_enclosure.py reuse the helpers above without running the roller set
if not os.environ.get("TD_IMPORT"):
    try:
        main()
    except Exception:
        log(traceback.format_exc())
    finally:
        LOG.close()
        os._exit(0)
