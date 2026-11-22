# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""FreeCAD TechDraw sheets for the tuner enclosure (TUNER-E-200 and up).

Run headless after enclosure.py:  xvfb-run -a freecad cad/drawings_enclosure.py
Reuses the helpers in drawings.py (imported with TD_IMPORT=1 so the roller set does not run).
Writes out/E-*.pdf / .svg and out/enclosure-drawings.FCStd.
"""
import json
import math
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["TD_IMPORT"] = "1"
os.environ["TD_LOG"] = "drawings-enc.log"
sys.path.insert(0, HERE)
import drawings as D  # noqa: E402
import ordinate  # noqa: E402
from drawings import (  # noqa: E402
    App, IN, OUT, TechDrawGui, label, load, log, note, overall, pump, settle, table, tag, view,
)

D.SUBTITLE = "ENCLOSURE - DRAFT"
D.N_SHEETS = 20
ENC = json.load(open(os.path.join(OUT, "enclosure.json")))
DRAFT = "DRAFT - DERIVED FROM DESIGN LOG 3.0 / 4 / 6 / 8 / 8D / 8E REV 3.7c. NOT FOR FABRICATION."
UNITS = "DIMENSIONS IN INCHES."

FRONT = ((-1, 0, 0), (0, -1, 0))     # seen from the front: right = -Y
LEFT = ((0, 1, 0), (-1, 0, 0))       # seen from the left (+Y): right = front
PLAN = ((0, 0, 1), (0, -1, 0))       # from above, front at the bottom
ISO = ((-1, 1, 0.8), (-1, -1, 0))    # front-left, above


def vw(doc, page, src, orient, scale, x, y, name, **kw):
    """view() with an (direction, x-direction) pair."""
    return view(doc, page, src, orient[0], scale, x, y, name, orient[1], **kw)


def sheet_overview(doc):
    page = D.new_page(doc, "E200", "ENCLOSURE OVERVIEW - WALL MOUNT", "TUNER-E-200", 1)
    asm = load(doc, "enc-assembly.step")
    cut = load(doc, "enc-cutaway.step")
    s = 0.15
    fr = vw(doc, page, asm, FRONT, s, 62, 190, "Front")
    lf = vw(doc, page, asm, LEFT, s, 150, 190, "Left")
    pl = vw(doc, page, asm, PLAN, s, 238, 196, "Plan")
    iso = vw(doc, page, cut, ISO, 0.14, 345, 175, "Cutaway")
    doc.recompute()
    settle([fr, lf, pl, iso])
    # front: width only. Its height pair picked the wall flange's foot (z 1.0) against the box top, reading
    # H - 1; the left view carries the true overall height
    overall(doc, page, fr, y=False, gap=6)
    overall(doc, page, lf, gap=6)
    overall(doc, page, pl, gap=6)
    label(doc, page, "FRONT  1:6.7", 62, 132)
    label(doc, page, "LEFT SIDE (WALL AT LEFT)", 150, 132)
    label(doc, page, "TOP (WALL AT TOP)", 238, 146)
    label(doc, page, "CUTAWAY: RF + LEFT PANELS OFF", 345, 118)
    note(doc, page, [
        "LAYOUT (REV 3.7c):",
        "1. VERTICAL STACK 16 W x 16 D x 24 H, REAR FLUSH ON THE WALL ON TWO 2 x 2 L-FLANGES.",
        "2. FRONT UPPER: RF BAY SERVICE PANEL. FRONT LOWER: CONTROL CASSETTE FACE + UI;",
        "   THE CASSETTE SLIDES OUT, THEN THE BULKHEAD AND EACH MOTOR AXIS MODULE COME OUT FRONT.",
        "3. TOP (FIXED): TWO >= 10 kV CERAMIC OUTPUT FEEDTHROUGHS, 6.03 APART, NEAR THE WALL.",
        "4. FLOOR: ALL LOW-VOLTAGE I/O - MAINS, ETHERNET, POF, COAX IN, AUX, GROUND STUD.",
        "5. AIR: INTAKE LOW-FRONT ON THE RIGHT SIDE, 120 mm EXHAUST HIGH-REAR ON THE LEFT.",
        "6. SAMPLER FIXED AT THE REAR, SERVICED THROUGH THE LEFT LOWER PANEL.",
        "7. SIDE PANELS SPLIT AT THE SHELF; CONDUCTIVE-ELASTOMER GASKETS (G-1).",
        f"8. CASSETTE PARTS <= {ENC['report']['cassette component height limit']:.2f} TALL TO PASS THE FRONT OPENING.",
        f"9. ALUMINUM ~{ENC['report']['aluminum weight, enclosure (lb)']:.0f} LB BEFORE ELECTRONICS.",
        DRAFT, UNITS,
    ], 128, 70, 2.4)


PANELS = {p["name"]: p for p in ENC["panels"]}
NEST_SC = 0.085
STD_NOTES = [
    "VIEWS FROM OUTSIDE. ORDINATES TO EACH CENTER FROM THE LOWER-LEFT CORNER AS VIEWED (0).",
    "5052-H32 ALUMINUM. PERIMETER HOLES 8-32 CLEARANCE 0.177, EACH ROW AN EQUAL SPREAD (TABLE: FROM, TO, AT);",
    "CAPTIVE SCREWS ON SERVICE PANELS: THE RETAINER'S HOLE SIZE. MATCH-DRILL THE FRAME FROM THE PANELS, 8-32 RIVNUTS (4).",
    "CONDUCTIVE-ELASTOMER GASKET ON EVERY FRAME FLANGE UNDER A PANEL (8E.6, G-1). DEBURR, BREAK EDGES.",
]


def size_text(kind, size):
    if kind.endswith("+"):
        return size_text(kind[:-1], size[0]) + " + " + size[2]
    if kind == "dflat":
        return f"⌀{size[0]:.3f}, FLAT AT {size[1]:.3f}"
    if kind == "ddflat":
        return f"⌀{size[0]:.3f}, FLATS {size[1]:.3f} APART"
    if kind == "rect":
        return f"{size[0]:.3f} x {size[1]:.3f}"
    if kind == "hole4":
        return ordinate.hole4_text(size)
    if kind == "dsub":
        return f"{size[0]:.3f} x {size[1]:.3f} + 2x⌀0.120, {size[2]:.3f} APART"
    if kind == "conn":
        return f"⌀{size:.3f} + 4x⌀0.125 ON {ENC['p']['CONN_PITCH']:.3f} SQ"
    if kind == "fan":
        return f"⌀{ENC['p']['BLOWER']['hole']:.2f} + 4x⌀{ENC['p']['BLOWER']['screw']:.2f} ON {ENC['p']['BLOWER']['pitch']:.3f} SQ"
    return f"⌀{size:.3f}"


PARTS = {p["name"]: p for p in ENC.get("parts", [])}


def part_face(doc, page, name, x, y, scale, vname):
    """A small part's flat face (enclosure.json "parts": its own plate, seen from +Z, u = X), to dimension like a
    panel."""
    src = load(doc, f"enc-part-{name.replace(' ', '-')}.step")
    return view(doc, page, src, (0, 0, 1), scale, x, y, vname, (1, 0, 0)), PARTS[name]


def ordinates(doc, page, v, pm, sc, x, y, name, det=None, labels=True):
    """The ordinate overlay (ordinate.py) on view v of panel or part pm at (x, y), and its overall size."""
    ov = ordinate.Overlay(pm, sc, ENC["p"]["CONN_PITCH"], ENC["p"]["BLOWER"], detail_of=det or {},
                          screw=ENC["p"]["SCREW_D"], labels=labels)
    sym = doc.addObject("TechDraw::DrawViewSymbol", name)
    sym.Symbol = ov.svg()
    page.addView(sym)
    sym.X, sym.Y = x, y
    panel_overall(doc, page, v, gap_x=ov.ext["below"] + 6, gap_y=ov.ext["right"] + 6)
    return ov


def panel_view(doc, page, name, x, y, scale, vname):
    pm = PANELS[name]
    src = load(doc, "enc-panel-" + name.replace("/", "-").replace(" ", "-") + ".step")
    return view(doc, page, src, tuple(pm["n"]), scale, x, y, vname, tuple(pm["U"])), pm


def panel_overall(doc, page, v, gap=6, gap_x=None, gap_y=None):
    """Overall width and height from the outermost edges (robust to notched corners). gap_x / gap_y push
    the width / height dimension out past whatever sits between it and the panel."""
    from drawings import bbox, dim, extreme
    x0, x1, y0, y1 = bbox(v)
    dim(doc, page, v, "DistanceX", [extreme(v, -1, 0), extreme(v, 1, 0)], (x0 + x1) / 2, y0 - (gap_x or gap))
    dim(doc, page, v, "DistanceY", [extreme(v, 0, -1), extreme(v, 0, 1)], x1 + (gap_y or gap), (y0 + y1) / 2)


# ------------------------------------------------------------------ dimensions on detail views
LOC_FONT = 3.0       # small dimensions: text height, mm


def _wait_vertices(v, n, timeout=120):
    import time
    t0 = time.time()
    while len(v.getVisibleVertexes()) < n and time.time() - t0 < timeout:
        pump(5)


def _small(d):
    if d.ViewObject and hasattr(d.ViewObject, "Fontsize"):
        d.ViewObject.Fontsize = LOC_FONT


def center_of(v, model_min):
    """The model point (in, view plane) TechDraw centered view v on, from where its geometry's lower-left
    extreme landed and where that extreme is in the model."""
    from drawings import bbox
    x0, _x1, y0, _y1 = bbox(v)
    k = IN * v.Scale
    return model_min[0] - x0 / k, model_min[1] - y0 / k


def points(doc, v, pts, center):
    """{name: 'VertexN'} for model points (in, view plane) of a view centered on `center` (in): a cosmetic
    vertex at each, so a dimension lands exactly there whatever the geometry offers."""
    n0 = len(v.getVisibleVertexes())
    for _name, (px, py) in pts.items():
        v.makeCosmeticVertex(App.Vector((px - center[0]) * IN, (py - center[1]) * IN, 0))
    v.touch()
    doc.recompute()
    _wait_vertices(v, n0 + len(pts))
    return {name: f"Vertex{n0 + i}" for i, name in enumerate(pts)}


def pdim(doc, page, v, kind, a, b, x, y, fmt="%.3f", small=True):
    """A dimension between two of points()'s vertices, its text at page (x, y) from the view's center."""
    from drawings import dim
    d = dim(doc, page, v, kind, [a, b], x, y, fmt)
    if small:
        _small(d)
    return d


DETAIL_KINDS = ("rect+", "dsub", "hole+")          # cutouts whose companion holes need a 1:1 detail


def _slug(name):
    return name.replace("/", "-").replace(" ", "-")


def cutout_detail(doc, page, pm, tags, kind, size, x, y, scale=1.0):
    """A compound cutout at `scale`, cut from the panel's own solid, with every size: the opening (or the
    main hole), the companion holes' spacing, where they sit relative to the opening, and their size."""
    import Part
    from drawings import circles, dim
    _t, _k, u, vv, _s, nt = next(cu for cu in pm["cutouts"] if cu[0] == tags[0])
    rect, main = None, None
    if kind == "dsub":
        w, h, pitch = size
        rect, holes = (w, h), [(-pitch / 2, 0.0, 0.120), (pitch / 2, 0.0, 0.120)]
    elif kind == "rect+":
        rect, holes = tuple(size[0]), [tuple(q) for q in size[1]]
    else:
        main, holes = size[0], [tuple(q) for q in size[1]]
    hx, hy = ordinate.extent(kind, size, ENC["p"]["CONN_PITCH"], ENC["p"]["BLOWER"])
    m = 0.25
    hx, hy = hx + m, hy + m
    o, U, V, n = (App.Vector(*pm[key]) for key in ("o", "U", "V", "n"))
    corners = [o + U * a + V * b - n * d for a in (u - hx, u + hx) for b in (vv - hy, vv + hy)
               for d in (-0.05, pm["t"] + 0.05)]
    lo = App.Vector(min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)) * IN
    hi = App.Vector(max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)) * IN
    src = load(doc, f"enc-panel-{_slug(pm['name'])}.step")
    name = f"Det_{_slug(pm['name']).replace('-', '_')}_{tags[0]}"
    piece = doc.addObject("Part::Feature", name)
    piece.Shape = src.Shape.common(Part.makeBox(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, lo))
    if piece.ViewObject:
        piece.ViewObject.Visibility = False
    v = view(doc, page, piece, tuple(pm["n"]), scale, x, y, name + "V", tuple(pm["U"]))
    doc.recompute()
    settle([v])
    k = IN * scale
    # the holes each dimension reaches for, on the side it sits: spacing below and right, offsets above
    # and left, so no extension line crosses the opening
    L = min(holes, key=lambda q: (q[0], q[1]))
    R = max(holes, key=lambda q: (q[0], -q[1]))
    B = min(holes, key=lambda q: (q[1], -q[0]))
    T = max(holes, key=lambda q: (q[1], q[0]))
    TL = min(holes, key=lambda q: (q[0], -q[1]))
    BL = min(holes, key=lambda q: (q[1], q[0]))
    pts = {f"h{n}": (u + q[0], vv + q[1]) for n, q in (("L", L), ("R", R), ("B", B), ("T", T), ("TL", TL), ("BL", BL))}
    if rect:
        w, h = rect
        pts.update({"tl": (u - w / 2, vv + h / 2), "tr": (u + w / 2, vv + h / 2), "bl": (u - w / 2, vv - h / 2),
                    "eL": (u - w / 2, vv + TL[1]), "eB": (u + BL[0], vv - h / 2)})
    else:
        pts.update({"cL": (u, vv + TL[1]), "cB": (u + BL[0], vv)})
    q = points(doc, v, pts, (u, vv))

    def mid(a, b, axis):
        return ((pts[a][axis] + pts[b][axis]) / 2 - (u, vv)[axis]) * k

    up, dn, lf, rt = hy * k, -hy * k, -hx * k, hx * k
    if rect:                                          # the opening
        pdim(doc, page, v, "DistanceX", q["tl"], q["tr"], mid("tl", "tr", 0), up + 5, small=False)
        pdim(doc, page, v, "DistanceY", q["bl"], q["tl"], lf - 5, mid("bl", "tl", 1), small=False)
    else:                                             # the main hole
        r = round(main / 2 * IN, 2)
        e = _circle_near(v, r, (0.0, 0.0))
        if e:
            dim(doc, page, v, "Diameter", [e], rt + 8, up + 6, fmt="⌀%.3f")
    if R[0] - L[0] > 1e-6:                            # the companion holes: their spacing...
        pdim(doc, page, v, "DistanceX", q["hL"], q["hR"], mid("hL", "hR", 0), dn - 5, small=False)
    if T[1] - B[1] > 1e-6:
        pdim(doc, page, v, "DistanceY", q["hB"], q["hT"], rt + 5, mid("hB", "hT", 1), small=False)
    a, b = ("eL", "hTL") if rect else ("cL", "hTL")   # ...and where they sit
    if abs(pts[a][0] - pts[b][0]) > 1e-6:
        pdim(doc, page, v, "DistanceX", q[a], q[b], mid(a, b, 0), up + 14, fmt="%.4f", small=False)
    a, b = ("eB", "hBL") if rect else ("cB", "hBL")
    if abs(pts[a][1] - pts[b][1]) > 1e-6:
        pdim(doc, page, v, "DistanceY", q[a], q[b], lf - 14, mid(a, b, 1), fmt="%.4f", small=False)
    r = round(R[2] / 2 * IN, 2)                       # their size: out to the right at the hole's height,
    e = _circle_near(v, r, (R[0] * k, R[1] * k))      # past any spacing dimension there
    if e:
        dim(doc, page, v, "Diameter", [e], rt + (22 if T[1] - B[1] > 1e-6 else 10), R[1] * k - 4,
            fmt=f"{len(holes)}X ⌀%.3f")
    what = nt.split(",")[0].split(";")[0]
    label(doc, page, f"DETAIL {', '.join(tags)}: {what}  {scale:g}:1", x, y + dn - 19)
    return v


def _circle_near(v, r_model_mm, at):
    """'EdgeN' of the circle of model radius r nearest page point `at` (mm from the view's center, +y up)."""
    best = None
    for i, e in enumerate(v.getVisibleEdges()):
        c = getattr(e, "Curve", None)
        if c is None or not hasattr(c, "Radius") or abs(c.Radius / v.Scale - r_model_mm) > 0.05:
            continue
        d = (c.Center.x - at[0]) ** 2 + (-c.Center.y - at[1]) ** 2
        if best is None or d < best[0]:
            best = (d, f"Edge{i}")
    return best[1] if best else None


def panel_sheet(doc, pid, title, dwg, no, entries, details=(), cut_xy=(318, None), fas_xy=None,
                notes_xy=(318, 100), skip=(), extra_notes=(), note_size=2.1):
    """entries: [(panel name, x, y, scale)]. Each view carries its features' positions as ordinate
    dimensions and their sizes in labels (ordinate.py), and its overall size. A compound cutout gets a
    detail, placed at the next of `details` [(x, y) or (x, y, scale)]. The table says what goes in each cutout."""
    page = D.new_page(doc, pid, title, dwg, no)
    views = []
    for i, (name, x, y, sc) in enumerate(entries):
        v, pm = panel_view(doc, page, name, x, y, sc, f"{pid}_{i}")
        views.append((v, pm, sc, x, y))
    doc.recompute()
    settle([v for v, *_ in views])
    groups = []                                       # [(pm, tags, kind, size)]: one detail each
    for _v, pm, *_ in views:
        for t, kind, _u, _vv, size, _nt in pm["cutouts"]:
            if kind not in DETAIL_KINDS:
                continue
            g = next((g for g in groups if g[0] is pm and g[2] == kind and g[3] == size), None)
            if g:
                g[1].append(t)
            else:
                groups.append((pm, [t], kind, size))
    multi = sum(1 for _v, pm, *_ in views if any(not (c[0].startswith("N") and c[0][1:].isdigit())
                                                for c in pm["cutouts"])) > 1
    cut_rows = [(("PANEL",) if multi else ()) + ("TAG", "WHAT GOES IN IT", "SIZE")]
    fas_rows = [("PANEL", "ROW", "HOLES", "FROM", "TO", "EQ PITCH", "AT", "OMIT")]
    fas_w = (22, 18, 11, 13, 13, 15, 13, 14)
    for i, (v, pm, sc, x, y) in enumerate(views):
        short = pm["name"].upper().replace(" PANEL", "")
        det = {t: g[1][0] for g in groups if g[0] is pm for t in g[1]}
        ordinates(doc, page, v, pm, sc, x, y, f"Ord{pid}_{i}", det)
        for t, kind, u, vv, size, nt in pm["cutouts"]:
            if (t.startswith("N") and t[1:].isdigit()) or any(t.startswith(q) and t[len(q):].isdigit() for q in skip):
                continue
            sz = f"DETAIL {det[t]}" if t in det else size_text(kind, size)
            cut_rows.append(((short,) if multi else ()) + (t, nt, sz))
        # each perimeter row or column: an even spread FROM-TO along it, AT across it (the view's ordinates)
        seen = {}
        for edge, horiz, at, a, b, n, gone in pm["fastener_rows"]:
            seen[edge] = seen.get(edge, 0) + 1
            nseg = sum(1 for r in pm["fastener_rows"] if r[0] == edge)
            name = edge + (f" {seen[edge]}/{nseg}" if nseg > 1 else "")
            fas_rows.append((short, name, str(n - len(gone)), ordinate._fmt(a), ordinate._fmt(b),
                             ordinate._fmt((b - a) / (n - 1)) if n > 1 else "-", ordinate._fmt(at),
                             ", ".join(ordinate._fmt(g) for g in gone)))
    for g, at in zip(groups, details):               # at: (x, y) or (x, y, scale)
        cutout_detail(doc, page, g[0], g[1], g[2], g[3], at[0], at[1], at[2] if len(at) > 2 else 1.0)
    if len(groups) > len(details):
        log("no room for details", pid, [g[1] for g in groups[len(details):]])
    tx, ty = cut_xy
    widths = ((24,) if multi else ()) + (10, 92, 40)
    if len(cut_rows) > 1:
        ty = ty if ty is not None else 257 - len(cut_rows) * 3.7 / 2      # its top under the frame
        table(doc, page, f"{pid}Cut", cut_rows, widths, tx, ty, size=6.5, row_px=14)
    nf = len(fas_rows)
    if nf > 1:
        # the PANEL column only where there are two panels, OMIT only where a row leaves a hole out
        keep = [c for c in range(len(fas_w)) if not (c == 0 and len(views) == 1) and
                not (c == 7 and not any(r[7] for r in fas_rows[1:]))]
        fas_rows = [tuple(r[c] for c in keep) for r in fas_rows]
        fas_w = tuple(fas_w[c] for c in keep)
        fx, fy = fas_xy if fas_xy else (tx - 20, (ty if len(cut_rows) > 1 else 257) - len(cut_rows) * 3.7 / 2
                                         - 6 - nf * 3.7 / 2)
        table(doc, page, f"{pid}Fas", fas_rows, fas_w, fx, fy, size=6.5, row_px=14)
    notes = []
    for _v, pm, *_ in views:
        notes += [f"{pm['name'].upper()}: {pm['gauge']}, {pm['L']:.3f} x {pm['H']:.3f}, {pm['fasteners']} FASTENER HOLES."]
        notes += pm["notes"]
    note(doc, page, ["NOTES:"] + notes + list(extra_notes) + STD_NOTES + [DRAFT, UNITS], notes_xy[0], notes_xy[1],
         note_size)
    return page, views


def sheet_front(doc):
    panel_sheet(doc, "E202", "FRONT PANELS", "TUNER-E-202", 3,
                [("cassette face", 145, 196, 0.5), ("RF service panel", 345, 216, 0.10)],
                details=[(98, 83, 1.0)], cut_xy=(244, 85), fas_xy=(355, 161.5), notes_xy=(340, 122), note_size=1.8)


def sheet_left(doc):
    panel_sheet(doc, "E203", "LEFT SIDE PANELS (+Y)", "TUNER-E-203", 4,
                [("left upper panel", 95, 180, 0.25), ("left lower panel", 95, 72, 0.25)],
                details=[(300, 160, 1.0)], fas_xy=(318, 222), notes_xy=(318, 96))


def sheet_right(doc):
    panel_sheet(doc, "E204", "RIGHT SIDE PANELS (-Y)", "TUNER-E-204", 5,
                [("right upper panel", 95, 180, 0.25), ("right lower panel", 95, 72, 0.25)],
                fas_xy=(318, 222), notes_xy=(318, 96))


def sheet_top_rear(doc):
    panel_sheet(doc, "E205", "TOP AND REAR PANELS", "TUNER-E-205", 6,
                [("top panel", 78, 186, 0.18), ("rear panel", 178, 150, 0.18)])


def sheet_floor(doc):
    panel_sheet(doc, "E206", "FLOOR - LOW-VOLTAGE I/O", "TUNER-E-206", 7, [("floor", 122, 142, 0.38)],
                details=[(276, 116, 0.75), (348, 116, 0.75)], skip=("W", "SB"), cut_xy=(338, None), fas_xy=(360, 160),
                notes_xy=(338, 188.5), note_size=1.8,
                extra_notes=["W1-W8: THE BULKHEAD AND PARTITION CLIP HOLES (E-208, E-218, E-217).",
                             "SB1-SB6: THE SAMPLER BASEPLATE'S STANDOFFS (E-209)."])


def sheet_shelf(doc):
    panel_sheet(doc, "E207", "GROUNDED SHELF", "TUNER-E-207", 8, [("shelf", 122, 142, 0.38)],
                skip=("W",), cut_xy=(338, None), fas_xy=(360, 160), notes_xy=(338, 112), note_size=1.8,
                extra_notes=["W1-W8: THE BULKHEAD AND PARTITION CLIP HOLES (E-208, E-218, E-217)."])


WEND = ((0, -1, 0), (1, 0, 0))      # wall clip along its length: the L, heel at lower left
WBOX = ((0, 0, 1), (0, 1, 0))       # its floor / shelf leg face-on, length across the page
WPLT = ((-1, 0, 0), (0, -1, 0))     # its plate leg face-on
WDET = ((0, -1, 0), (1, 0, 0))      # typical mounting seen along Y: control side left, motor side right


def plate_sheet(doc, pname, plate, pid, title, dwg, no):
    """TUNER-E-208 (bulkhead) and E-218 (partition): the plate with its ordinates, labels and connector
    details, what goes in each cutout, and where its clips go (E-217 has the clip itself)."""
    clip_note = ["CLIPS (E-217): EACH CLIP'S HOLES LINE UP WITH ITS PLATE HOLE (W) AND ITS FLOOR OR SHELF HOLE",
                 "(E-206 / E-207, CLIP TABLE). DRILL ALL THREE TO THEIR POSITIONS, OR FIX THE CLIPS AND MATCH-DRILL."]
    page, _views = panel_sheet(doc, pid, title, dwg, no, [(pname, 150, 192, 0.5)],
                               details=[(72, 74, 1.0), (178, 74, 1.0)], skip=("W",), cut_xy=(322, 104),
                               notes_xy=(346, 196), note_size=1.7, extra_notes=clip_note)
    side = {("bulkhead", 1): "MOTOR SIDE", ("bulkhead", -1): "CONTROL SIDE",
            ("partition", 1): "SAMPLER SIDE", ("partition", -1): "MOTOR SIDE"}
    # where each clip goes, in the plate's own view: its hole's tag and position here, and the floor or
    # shelf hole its other leg takes (E-206 / E-207)
    rows = [("EDGE", "CLIPS ON", "PLATE HOLES", "CENTERS FROM LEFT, ⌀0.177", "FROM BOTTOM", "MATES")]
    w = [cu for cu in PANELS[pname]["cutouts"] if cu[0].startswith("W")]
    for i, edge in enumerate(("floor", "shelf")):
        cl = [(s_, y) for e, s_, y in ENC["p"]["WALL_CLIPS"][plate] if e == edge]
        mine = w[4 * i:4 * i + 4]
        j = 0 if plate == "bulkhead" else 4
        rows.append((edge.upper(), side[(plate, cl[0][0])], f"{mine[0][0]}-{mine[-1][0]}",
                     ", ".join(f"{cu[2]:.3f}" for cu in mine), f"{mine[0][3]:.4f}",
                     f"{'E-206' if edge == 'floor' else 'E-207'} W{j + 1}-W{j + 4}"))
    table(doc, page, f"{pid}Clips", rows, (11, 20, 14, 38, 14, 21), 330, 80, size=6.5, row_px=14)


def sheet_bulkhead(doc):
    plate_sheet(doc, "bulkhead", "bulkhead", "E208", "BULKHEAD", "TUNER-E-208", 9)


def sheet_partition(doc):
    plate_sheet(doc, "motor/sampler partition", "partition", "E218", "MOTOR / SAMPLER PARTITION", "TUNER-E-218", 19)


def sheet_wall_clips(doc):
    """TUNER-E-217: the bulkhead and partition clip, its holes dimensioned, and how it mounts."""
    page = D.new_page(doc, "E217", "BULKHEAD AND PARTITION CLIPS", "TUNER-E-217", 18)
    sc = 3.0
    wc = load(doc, "enc-wall-clip.step")
    we = vw(doc, page, wc, WEND, sc, 62, 196, "WClipEnd")
    wb = vw(doc, page, wc, WBOX, sc, 160, 196, "WClipBox")
    wp = vw(doc, page, wc, WPLT, sc, 280, 196, "WClipPlate")
    wf = vw(doc, page, load(doc, "enc-wall-clip-floor.step"), WDET, 1.5, 100, 104, "WClipFloor")
    ws = vw(doc, page, load(doc, "enc-wall-clip-shelf.step"), WDET, 1.5, 210, 104, "WClipShelf")
    doc.recompute()
    settle([we, wb, wp, wf, ws])
    for v in (wb, wp):
        overall(doc, page, v, gap=5)
    # each leg's hole: mid-length, on the middle of its flat (WCLIP_MID from the heel's outside face)
    leg, t, cl = ENC["p"]["WCLIP"]
    mid = ENC["p"]["WCLIP_MID"]
    k = IN * sc
    # the end: the L (page x = x, page y = z; heel at the lower left)
    pe = points(doc, we, {"heel": (0, 0), "x": (leg, 0), "z": (0, leg), "t": (t, leg)}, (leg / 2, leg / 2))
    pdim(doc, page, we, "DistanceX", pe["heel"], pe["x"], 0, -leg / 2 * k - 7, small=False)
    pdim(doc, page, we, "DistanceY", pe["heel"], pe["z"], -leg / 2 * k - 7, 0, small=False)
    pdim(doc, page, we, "DistanceX", pe["z"], pe["t"], -leg / 2 * k + 6, leg / 2 * k + 6, small=False)
    # the floor / shelf leg face-on (page x = length, page y = -distance from the heel: heel at the top)
    pb = points(doc, wb, {"end": (0, 0), "hole": (cl / 2, -mid)}, (cl / 2, -leg / 2))
    pdim(doc, page, wb, "DistanceX", pb["end"], pb["hole"], -cl / 4 * k, leg / 2 * k + 8, small=False)
    pdim(doc, page, wb, "DistanceY", pb["end"], pb["hole"], -cl / 2 * k - 8, (leg / 2 - mid / 2) * k, fmt="%.4f",
         small=False)
    from drawings import circles, dim
    for _r, e in circles(wb).items():
        dim(doc, page, wb, "Diameter", [e], 30, 30)
    # the plate leg face-on (page x = -length, page y = up from the heel: heel at the bottom)
    pp = points(doc, wp, {"end": (-cl, 0), "hole": (-cl / 2, mid)}, (-cl / 2, leg / 2))
    pdim(doc, page, wp, "DistanceX", pp["end"], pp["hole"], -cl / 4 * k, leg / 2 * k + 8, small=False)
    pdim(doc, page, wp, "DistanceY", pp["end"], pp["hole"], -cl / 2 * k - 8, (mid / 2 - leg / 2) * k, fmt="%.4f",
         small=False)
    for _r, e in circles(wp).items():
        dim(doc, page, wp, "Diameter", [e], 30, 30, fmt="⌀%.3f TAP 8-32")
    # where the clip sits: its floor or shelf hole WCLIP_MID out from the plate's face, and the plate's hole
    # WCLIP_MID from the floor or the shelf (control face at x = 0, floor top at z = 0)
    t12, h = ENC["p"]["T12"], ENC["p"]["Z_SH0"] - ENC["p"]["Z_FLOOR"]
    kd = IN * 1.5
    for v, z0, zs, lo in ((wf, 0.0, -1, True), (ws, h, 1, False)):
        c = center_of(v, (-0.7, -ENC["p"]["T12"] if lo else h - 0.9))
        q = points(doc, v, {"face": (t12, z0 - zs * 0.7), "leg": (t12 + mid, z0 + zs * 0.04),
                            "edge": (-0.6, z0), "plate": (-0.05, z0 - zs * mid)}, c)
        y_top = (z0 - zs * 0.7 - c[1]) * kd
        pdim(doc, page, v, "DistanceX", q["face"], q["leg"], (t12 + mid / 2 - c[0]) * kd,
             y_top + (9 if lo else -9), fmt="%.4f", small=False)
        pdim(doc, page, v, "DistanceY", q["edge"], q["plate"], (-0.7 - c[0]) * kd - 6, (z0 - zs * mid / 2 - c[1]) * kd,
             fmt="%.4f", small=False)
    label(doc, page, "END", 62, 160)
    label(doc, page, "FLOOR / SHELF LEG", 160, 162)
    label(doc, page, "PLATE LEG", 280, 162)
    label(doc, page, "BULKHEAD / PARTITION CLIP (16)  3:1", 170, 150)
    label(doc, page, "AT FLOOR  1.5:1", 100, 66)
    label(doc, page, "AT SHELF  1.5:1", 210, 66)
    note(doc, page, [
        "NOTES:",
        "1. CLIPS (16): 1/2 x 1/2 x 1/8 6061-T6 x 1.00, SQUARE-CUT. ONE HOLE PER LEG, MID-LENGTH,",
        "   ON THE MIDDLE OF THE LEG'S FLAT. FLOOR / SHELF LEG ⌀0.177. PLATE LEG: BULKHEAD CLIPS ⌀0.136",
        "   TAPPED 8-32 (PEM CLS-832-1 IF IT COMES OFF OFTEN); PARTITION CLIPS ⌀0.177.",
        "2. FLOOR LEG: 8-32 x 1/2 BUTTON HEAD UP THROUGH THE FLOOR, NYLOC ON THE CLIP.",
        "   SHELF LEG: 8-32 x 1/2 DOWN FROM THE RF BAY, NYLOC UNDER THE CLIP.",
        "3. BULKHEAD: 8-32 x 1/4 FROM THE CONTROL SIDE INTO THE TAPPED LEG - IT COMES OUT",
        "   WITHOUT TOUCHING THE CLIPS. PARTITION: 8-32 x 3/8 + NYLOC.",
        "4. WHERE EACH CLIP GOES: THE CLIP TABLES ON E-208 AND E-218 (PLATE HOLES W) AND E-206 / E-207",
        "   (FLOOR AND SHELF HOLES W). THE HEEL SITS AGAINST THE PLATE; EACH HOLE LINES UP WITH ITS MATES.",
        "5. AT FLOOR / AT SHELF: BULKHEAD, SECTION ON THE SCREW PLANE, HOLES IN LINE. THE CLIP'S HEEL",
        "   SITS ON THE PLATE'S FACE AND ON THE FLOOR OR UNDER THE SHELF.",
        DRAFT, UNITS,
    ], 322, 112, 2.3)


JISO = ((-1, -1, 0.9), (1, -1, 0))  # into a rear-left corner from inside the box, above (Z up on the page)
CPLAN = ((0, 0, 1), (-1, 0, 0))     # corner clip from above: the L, heel at lower left
JWALL = ((0, -1, 0), (1, 0, 0))     # a junction's left wall from inside the box: the corner at the right
CFACE = ((0, 1, 0), (-1, 0, 0))     # corner clip, one leg face-on


def sheet_frame(doc):
    page = D.new_page(doc, "E201", "FRAME - 6061-T6 ANGLE", "TUNER-E-201", 2)
    fr = vw(doc, page, load(doc, "enc-frame.step"), ISO, 0.13, 62, 182, "FrameIso")
    jt = vw(doc, page, load(doc, "enc-frame-joint.step"), JISO, 0.6, 152, 190, "JointIso")
    jx = vw(doc, page, load(doc, "enc-frame-joint-exploded.step"), JISO, 0.4, 152, 124, "JointExploded")
    clip = load(doc, "enc-corner-clip.step")
    cp = vw(doc, page, clip, CPLAN, 1.0, 44, 62, "ClipPlan")
    cf = vw(doc, page, clip, CFACE, 1.0, 100, 60, "ClipFace")
    jw = vw(doc, page, load(doc, "enc-frame-joint.step"), JWALL, 0.5, 192, 56, "JointWall")
    doc.recompute()
    settle([fr, jt, jx, cp, cf, jw])
    p = ENC["p"]
    cleg, ct, ch = p["CLIP_LEG"], p["ANG_T"], p["CLIP_H"]
    h1, h2 = (c - ct for c in p["CLIP_HOLES"])         # the holes from the clip's heel
    k = IN
    # plan (page x = -x, page y = -y; heel at the lower left): the legs and their thickness
    pc = points(doc, cp, {"heel": (-cleg, -cleg), "a": (0, -cleg), "b": (-cleg, 0), "b_in": (-cleg + ct, 0)},
                (-cleg / 2, -cleg / 2))
    pdim(doc, page, cp, "DistanceX", pc["heel"], pc["a"], 0, -cleg / 2 * k - 5, small=False)
    pdim(doc, page, cp, "DistanceY", pc["heel"], pc["b"], cleg / 2 * k + 5, 0, small=False)   # right: the frame
    pdim(doc, page, cp, "DistanceX", pc["b"], pc["b_in"], -cleg / 2 * k + 8, cleg / 2 * k + 4)
    # the leg face-on (page x = -x, heel at the left; page y = z): the holes from the heel, on the centerline
    pf = points(doc, cf, {"heel": (-cleg, 0), "h1": (-cleg + h1, ch / 2), "h2": (-cleg + h2, ch / 2)},
                (-cleg / 2, ch / 2))
    overall(doc, page, cf, gap=4)
    pdim(doc, page, cf, "DistanceX", pf["heel"], pf["h1"], (-cleg / 2 + h1 / 2) * k, ch / 2 * k + 4)
    pdim(doc, page, cf, "DistanceX", pf["heel"], pf["h2"], (-cleg / 2 + h2 / 2) * k, ch / 2 * k + 9)
    pdim(doc, page, cf, "DistanceY", pf["heel"], pf["h1"], -cleg / 2 * k - 5, 0, fmt="%.4f")
    from drawings import circles, dim
    label(doc, page, f"2X ⌀{p['CLIP_SCREW']:.3f}", 100, 40)
    # placement: one junction's wall from inside, true size. The clip's heel in the post's inside corner,
    # its edge on the ring's flange; the screws at CLIP_HOLES from the frame's outer corner, mid-band.
    zm = (ct + 1.0) / 2
    jc = center_of(jw, (-4.0, 0.0))                    # the stubs: the ring cut 4.0 from the corner, on the floor
    pj = points(doc, jw, {"corner": (0, 0), "s1": (-p["CLIP_HOLES"][0], zm), "s2": (-p["CLIP_HOLES"][1], zm),
                          "clip_lo": (-ct - 1.5 - 0.05, ct), "clip_hi": (-ct - 1.5 - 0.05, 1.0)}, jc)
    kj = IN * 0.5
    y_lo = (0 - jc[1]) * kj
    pdim(doc, page, jw, "DistanceX", pj["corner"], pj["s1"], (-p["CLIP_HOLES"][0] / 2 - jc[0]) * kj, y_lo - 5)
    pdim(doc, page, jw, "DistanceX", pj["corner"], pj["s2"], (-p["CLIP_HOLES"][1] / 2 - jc[0]) * kj, y_lo - 10)
    pdim(doc, page, jw, "DistanceY", pj["corner"], pj["s1"], (0 - jc[0]) * kj + 6, (zm / 2 - jc[1]) * kj, fmt="%.4f")
    pdim(doc, page, jw, "DistanceY", pj["clip_lo"], pj["clip_hi"], (-ct - 1.55 - jc[0]) * kj - 5,
         ((ct + 1.0) / 2 - jc[1]) * kj)
    label(doc, page, "JUNCTION (16), FROM INSIDE  0.6:1", 152, 151)
    label(doc, page, "JUNCTION, EXPLODED  0.4:1", 152, 97)
    label(doc, page, "CORNER CLIP (16): PLAN, LEG  1:1", 72, 28)
    label(doc, page, "JUNCTION WALL  0.5:1", 190, 81)
    rows = [("MEMBER", "QTY", "STOCK", "LENGTH", "NOTE")]
    total = {}
    for name, q, length, leg in ENC["frame_cut_list"]:
        stock = "1 x 1 x 1/8" if leg >= 0.99 else "1/2 x 1/2 x 1/8"
        note_ = {"post": "VERTICAL CORNERS, FLOOR TO TOP", "top ring": "UNDER THE TOP PANEL",
                 "shelf ring upper": "ON THE SHELF; RF SERVICE PANEL FLANGE AT FRONT",
                 "shelf ring lower": "UNDER THE SHELF; 1/2 AT FRONT FOR THE CASSETTE",
                 "bottom ring": "ON THE FLOOR; 1/2 AT FRONT FOR THE CASSETTE"}.get(name, "")
        rows.append((name.upper(), str(q), stock + " 6061-T6", f"{length:.3f}", note_))
        total[stock] = total.get(stock, 0) + q * (length + 0.125)
    for name, q, length, leg in ENC["frame_extra"]:
        rows.append((name.upper(), str(q), "6061-T6", f"{length:.3f}", ""))
        st = name[name.index("(") + 1:name.index(")")]
        total[st] = total.get(st, 0) + q * (length + 0.125)
    table(doc, page, "FrameCut", rows, (62, 10, 40, 16, 70), 300, 200, size=6.5, row_px=15)
    buy = [f"{k}: {v / 12:.1f} FT INCL. KERF" for k, v in sorted(total.items())]
    p = ENC["p"]
    n_screw = ENC["report"]["junction screws"]
    note(doc, page, ["NOTES:",
        "1. 6061-T6 ANGLE, SQUARE-CUT ENDS. FOUR POSTS RUN FLOOR TO TOP; RING MEMBERS BUTT THE POST LEGS WITH",
        "   EVERY OUTER FACE FLUSH (PANEL AND GASKET FACES). BOLTED, NOT WELDED (4): NO WARP, NO HAZ LOSS.",
        "2. JUNCTIONS (16): A CORNER CLIP NESTS IN THE POST'S INSIDE CORNER, IN THE 7/8 BAND BETWEEN THE RING",
        f"   FLANGE AND THE LEG EDGES. PER WALL, A #6-32 x 1/2 FLAT HEAD (82°, FLUSH OUTSIDE) INTO THE POST AT "
        f"{p['CLIP_HOLES'][0]:.2f}",
        f"   FROM THE CORNER AND ONE INTO THE RING MEMBER AT {p['CLIP_HOLES'][1]:.2f}, MID-BAND, NYLOC INSIDE: "
        f"{n_screw} SCREWS + {n_screw} NYLOCS.",
        f"3. CLIP: 1-1/2 x 1-1/2 x 1/8 6061-T6 x 7/8. ⌀{p['CLIP_SCREW']:.3f} HOLES "
        f"{p['CLIP_HOLES'][0] - p['ANG_T']:.3f} AND {p['CLIP_HOLES'][1] - p['ANG_T']:.3f} FROM THE HEEL, ON",
        "   THE CENTERLINE. BREAK THE HEEL TO CLEAR THE POST'S ROOT FILLET. CASSETTE RINGS (BOTTOM, SHELF LOWER),",
        "   FRONT CORNERS (4): FRONT LEG CUT TO 7/8, POST HOLE ONLY - THE TRAY SLIDES PAST; THEIR 1/2 FRONT",
        "   MEMBERS RIDE ON THE FLOOR AND SHELF SCREWS.",
        "4. BUILD: DRILL THE CLIPS ON A JIG. SQUARE EACH JUNCTION ON A FLAT TABLE (CHECK BOTH DIAGONALS), CLAMP",
        "   THE CLIP, MATCH-DRILL THE FRAME FROM INSIDE THROUGH IT, COUNTERSINK FROM OUTSIDE, BOLT UP.",
        "5. PANEL FLANGE HOLES: MATCH-DRILL FROM EACH PANEL (E-202 TO E-208), THEN 8-32 RIVNUTS. PANEL ROWS",
        f"   START {p['CORNER_C']:.2f} FROM EVERY CORNER AND SKIP THE CLIP BANDS: NO RIVNUT SITS BEHIND A CLIP.",
        "6. THE SHELF IS CLAMPED BETWEEN THE LOWER AND UPPER SHELF RINGS; SCREWS THROUGH ALL THREE.",
        "7. GROUND STUD (FLOOR TAG L) LANDS ON THE REAR-LEFT BOTTOM RING: SINGLE-POINT BOND (8A.2).",
        "8. BUY: " + "; ".join(buy[:2]) + ";",
        "   " + "; ".join(buy[2:]) + ".",
        DRAFT, UNITS], 305, 122, 2.3)
    label(doc, page, "FRAME, ISOMETRIC  1:8", 62, 118)


def sheet_small_parts(doc):
    """TUNER-E-209: the motor axis bracket (its plates face-on, dimensioned like the panels), the sampler baseplate,
    and the input choke mount's base disc and spider (bolt circles called out)."""
    page = D.new_page(doc, "E209", "BRACKET, BASEPLATE, CHOKE PARTS", "TUNER-E-209", 10)
    br_src = load(doc, "enc-C1-axis-bracket.step")
    br_iso = vw(doc, page, br_src, ISO, 0.45, 56, 230, "BracketIso")
    br_side = vw(doc, page, br_src, FRONT, 0.75, 140, 232, "BracketSide")
    faces = [part_face(doc, page, "axis bracket top plate", 62, 156, 0.75, "BracketTop") + (62, 156, 0.75),
             part_face(doc, page, "axis bracket motor plate", 172, 156, 0.75, "BracketMotor") + (172, 156, 0.75),
             part_face(doc, page, "sampler baseplate", 118, 76, 0.45, "Baseplate") + (118, 76, 0.45)]
    cb_src, cs_src = load(doc, "enc-choke-base.step"), load(doc, "enc-choke-spider.step")
    cb = vw(doc, page, cb_src, PLAN, 0.5, 236, 222, "ChokeBase")
    cs = vw(doc, page, cs_src, PLAN, 0.5, 242, 150, "ChokeSpider")
    ca = vw(doc, page, load(doc, "enc-choke-assembly.step"), FRONT, 0.35, 386, 222, "ChokeAsm", hidden=True)
    doc.recompute()
    settle([br_iso, br_side, cb, cs, ca] + [f[0] for f in faces])
    overall(doc, page, br_side, gap=5)
    for i, (v, pm, x, y, sc) in enumerate(faces):      # the plates' one feature is said in their captions
        ordinates(doc, page, v, pm, sc, x, y, f"OrdE209_{i}", labels=pm["name"] == "sampler baseplate")
    # the base disc and the spider: their outer sizes, and each pattern's circle and callout (ordinate.Polar). In
    # PLAN (right = -Y, up = +X) a pattern at model angle a sits at page angle atan2(cos a, -sin a)
    p = ENC["p"]
    for v, (dx, dy), fmt in ((cb, (-24, 22), "⌀%.3f"), (cs, (16, 20), "HUB ⌀%.3f")):
        circ = D.circles(v)
        if circ:
            D.dim(doc, page, v, "Diameter", [circ[max(circ)]], dx, dy, fmt=fmt)
    rod = p["CHOKE_ROD"][0] + 0.02
    csk_d = p["CHOKE_CSK"][0]
    base = ordinate.Polar(0.5, p["CHOKE_BASE_D"] / 2, [
        (p["CHOKE_BC"], 60, 0.177 / 2, [f"3X ⌀0.177 CSK 82° x ⌀{csk_d:.3f}", f"EQ SP ON ⌀{p['CHOKE_BC']:.3f} (CH1-CH3)"]),
        (0.72, 0, 0.075, ["6X ⌀0.150 EQ SP", "ON ⌀0.720 (VENTS)"]),
        (None, 300, rod / 2, [f"⌀{rod:.3f} (ROD)"])])
    tip, hub, arm = p["CHOKE_SPIDER"][0], p["CHOKE_HUB"], p["CHOKE_ARM"]
    bb = cs_src.Shape.BoundBox                       # the spider's arms put its view's center off the hub
    k = IN * 0.5
    off = (-(p["CHOKE_Y"] - (bb.YMin + bb.YMax) / 2 / IN) * k, (p["CHOKE_X"] - (bb.XMin + bb.XMax) / 2 / IN) * k)
    spider = ordinate.Polar(0.5, tip / 2, [
        (tip, 0, 0.0, [f"3X ARM {arm:.3f} WIDE, R{arm / 2:.3f} END,", f"TIPS ON ⌀{tip:.3f}, MIDWAY", "BETWEEN THE STANDOFFS"]),
        (None, 300, rod / 2, [f"⌀{rod:.3f} (ROD)"])], off=off)
    for name, ov, (x, y) in (("PolE209_base", base, (236, 222)), ("PolE209_spider", spider, (242, 150))):
        sym = doc.addObject("TechDraw::DrawViewSymbol", name)
        sym.Symbol = ov.svg()
        page.addView(sym)
        sym.X, sym.Y = x, y
    top, mot = (ordinate.hole4_text(f[1]["cutouts"][0][4]) for f in faces[:2])
    label(doc, page, "MOTOR AXIS BRACKET (x3)", 56, 199)
    label(doc, page, "FRONT  0.75:1", 140, 199)
    label(doc, page, "TOP PLATE, FROM ABOVE  0.75:1", 62, 120)
    note(doc, page, [top], 62, 114, 2.6)
    label(doc, page, "MOTOR PLATE, FROM BELOW  0.75:1", 172, 120)
    note(doc, page, [mot], 172, 114, 2.6)
    label(doc, page, "SAMPLER BASEPLATE (12 GA), FROM ABOVE  0.45:1", 118, 108)
    label(doc, page, "CHOKE BASE (G10 1/4)  0.5:1", 236, 190)
    label(doc, page, "CHOKE SPIDER (G10 1/8)  0.5:1", 242, 124)
    label(doc, page, "CHOKE MOUNT  0.35:1", 386, 190)
    rep = ENC["report"]
    note(doc, page, ["NOTES:",
        "1. AXIS BRACKET (3): 1/8 6061, FORMED OR WELDED U - TOP PLATE, TWO SIDES, MOTOR PLATE;",
        "   1.75 TALL. TOP PLATE TO THE SHELF: 4 x #10-32 x 1/2 DOWN FROM THE RF BAY (E-207: C1, C2, R),",
        "   NYLOCS UNDER IT, REACHED THROUGH THE OPEN SIDES; ⌀1.50 CLEARS THE BUSHING. MOTOR PLATE:",
        "   NEMA 23, 23HS22-2804S (M-2). TAKEOFF PULLEY + COUPLER A INSIDE; THE ENCODER / LIMIT-CAM",
        "   MODULE (7.1, 7.2) BOLTS TO THE OPEN SIDE. LOOSEN COUPLER A'S G10 CLAMP AND THE 4 NYLOCS:",
        "   IT DROPS AND SLIDES OUT FORWARD.",
        "2. SAMPLER BASEPLATE: 12 GA 5052 ON 6 HEX STANDOFFS 1/4, 8-32 F-F (SB1-SB6, THE FLOOR'S SB",
        "   HOLES ON E-206), 8-32 x 3/8 BUTTON HEADS UP THROUGH THE FLOOR AND DOWN THROUGH THE PLATE.",
        "   G, H, J, K CLEAR THE FLOOR CONNECTORS' BODIES. COUPLER BOX, BOARD BRACKET AND K1 / K2 HOLES",
        "   MATCH THE PARTS (E-212). PARTITION SIDE AT THE BOTTOM. SERVICED THROUGH THE LEFT LOWER PANEL.",
        "3. CHOKE MOUNT (6): ALL INSULATING, NOTHING METAL IN OR ON THE WINDING. NYLON 8-32 FLAT HEADS,",
        "   FLUSH, INTO 3 G10 STANDOFFS 3/8 x 5/8, 8-32 F-F; SS 8-32 UP THROUGH THE SHELF (E-207 CH1-CH3).",
        f"   BASE HOLES CLOCKED TO CH1-CH3. ROD 1/2-13 FIBERGLASS x {rep['choke rod length']:.2f}, FRP NUTS. WINDING (15 t",
        f"   RG-400, 5 x FT-240-61) ON 1/16 SILICONE PADS: {rep['choke winding above the shelf']:.2f} ABOVE THE SHELF, "
        f"{rep['choke winding below the deck']:.2f} BELOW THE DECK.",
        DRAFT, UNITS], 341, 107, 1.9)


def sheet_tray_flange(doc):
    """TUNER-E-219: the cassette tray and its rails, and the wall flange (both legs face-on, dimensioned like the
    panels, and its end)."""
    page = D.new_page(doc, "E219", "CASSETTE TRAY, RAILS, WALL FLANGE", "TUNER-E-219", 20)
    tray = vw(doc, page, load(doc, "enc-cassette-tray.step"), PLAN, 0.3, 80, 222, "Tray")
    rail = vw(doc, page, load(doc, "enc-cassette-rail.step"), FRONT, 1.0, 170, 222, "RailEnd")
    fl_end = vw(doc, page, load(doc, "enc-wall-flange.step"), ((0, 0, 1), (0, -1, 0)), 1.0, 250, 222, "FlangeEnd")
    faces = [part_face(doc, page, "wall flange wall leg", 120, 140, 0.32, "FlangeWall") + (120, 140, 0.32),
             part_face(doc, page, "wall flange side leg", 120, 66, 0.32, "FlangeSide") + (120, 66, 0.32)]
    doc.recompute()
    settle([tray, rail, fl_end] + [f[0] for f in faces])
    for v in (tray, rail):
        overall(doc, page, v, gap=5)
    panel_overall(doc, page, fl_end, gap=5)
    for i, (v, pm, x, y, sc) in enumerate(faces):
        ordinates(doc, page, v, pm, sc, x, y, f"OrdE219_{i}")
    label(doc, page, "CASSETTE TRAY (12 GA), FROM ABOVE  0.3:1", 80, 196)
    label(doc, page, "RAIL END (x2)  1:1", 170, 196)
    label(doc, page, "WALL FLANGE, END  1:1", 250, 182)
    label(doc, page, "WALL FLANGE (x2): WALL LEG  0.32:1", 120, 112)
    label(doc, page, "WALL FLANGE: SIDE LEG  0.32:1", 120, 80)
    rails = ENC["p"]["X_BULK"] - 0.15 - (-ENC["p"]["X_IN"] + ENC["p"]["SANG"] + 0.02)
    note(doc, page, ["NOTES:",
        "1. CASSETTE TRAY: 12 GA 5052, RIDES TWO 1/2 x 1/2 x 1/8 RAILS ON THE FLOOR, BEHIND THE FRONT LIP.",
        f"   RAILS: 6061 ANGLE x {rails:.3f}. COMPONENT HOLES MATCH THE PARTS FITTED: PSU (ON EDGE), CONTROL",
        f"   BOARD, DC-DCs. EVERYTHING ON THE TRAY <= {ENC['report']['cassette component height limit']:.2f} TALL TO PASS THE OPENING.",
        "2. WALL FLANGE (2, ONE A SIDE): 2 x 2 x 3/16 6061 x 21, HEEL ON THE REAR CORNER. THE SIDE LEG BOLTS",
        "   THROUGH THE SIDE PANEL INTO THE REAR POST: 3 x 8-32, LONGER SCREWS, IN THE PANELS' WF HOLES",
        "   (E-203 / E-204). THE WALL LEG LIES FLUSH WITH THE REAR: 3 SLOTS FOR 3/8 LAGS INTO A 3/4 PLYWOOD",
        "   BACKER ACROSS THE STUDS. LEG VIEWS: HEEL AT THE BOTTOM, LOWER END AT THE LEFT.",
        DRAFT, UNITS], 322, 112, 2.1)


def sheet_exploded(doc):
    page = D.new_page(doc, "E210", "EXPLODED VIEW AND PARTS LIST", "TUNER-E-210", 11)
    ex = vw(doc, page, load(doc, "enc-exploded.step"), ISO, 0.14, 112, 150, "Exploded")
    doc.recompute()
    settle([ex])
    P = ENC["panels"]
    screws = sum(p["fasteners"] for p in P)
    gasket_ft = sum(p["perimeter"] for p in P if p["name"] not in ("bulkhead", "motor/sampler partition")) / 12
    gasket_ft += 2 * (P[[p["name"] for p in P].index("shelf")]["perimeter"]) / 12 / 2
    capt = sum(p["fasteners"] for p in P if p["name"] in ("RF service panel", "cassette face"))
    rows = [("ITEM", "QTY", "DESCRIPTION", "MATERIAL / SPEC", "DWG")]
    items = [
        ("1", "1 SET", "FRAME: POSTS, RINGS, CLIPS", "6061-T6 ANGLE", "E-201"),
        ("2", "1", "RF SERVICE PANEL", "5052-H32 14 GA", "E-202"),
        ("3", "1", "CASSETTE FACE (UI)", "5052-H32 14 GA", "E-202"),
        ("4", "2", "SIDE UPPER PANELS (INTAKE / EXHAUST)", "5052-H32 14 GA", "E-203/204"),
        ("5", "2", "SIDE LOWER PANELS", "5052-H32 14 GA", "E-203/204"),
        ("6", "1", "REAR PANEL", "5052-H32 14 GA", "E-205"),
        ("7", "1", "TOP PANEL (FEEDTHROUGHS)", "5052-H32 12 GA", "E-205"),
        ("8", "1", "FLOOR (I/O)", "5052-H32 12 GA", "E-206"),
        ("9", "1", "SHELF (GROUNDED)", "5052-H32 12 GA", "E-207"),
        ("10", "1", "BULKHEAD (FILTERED CONNECTORS)", "5052-H32 12 GA", "E-208"),
        ("11", "1", "MOTOR / SAMPLER PARTITION", "5052-H32 12 GA", "E-218"),
        ("12", "1", "CASSETTE TRAY + 2 RAILS", "12 GA / 1/2 ANGLE", "E-219"),
        ("13", "3", "MOTOR AXIS BRACKET", "1/8 6061", "E-209"),
        ("14", "1", "SAMPLER BASEPLATE", "5052-H32 12 GA", "E-209"),
        ("15", "2", "WALL FLANGE", "2 x 2 x 3/16 6061", "E-219"),
        ("16", str(screws + 40), "8-32 SS BUTTON HEAD, 1/2", f"{screws} HOLES + SPARES", "-"),
        ("17", str(screws + 40), "8-32 RIVNUT, ALUMINUM", "IN THE FRAME FLANGES", "-"),
        ("18", str(capt), "8-32 CAPTIVE PANEL SCREW", "RF PANEL + CASSETTE FACE", "-"),
        ("19", f"{gasket_ft:.0f} FT", "CONDUCTIVE-ELASTOMER GASKET", "G-1, ~0.25 WIDE", "-"),
        ("20", "6", "3/8 x 3 LAG + WASHER", "INTO 3/4 PLYWOOD BACKER", "-"),
        ("21", "1 + 1", "HONEYCOMB VENT: INTAKE 8 x 4, EXHAUST 4.7 SQ", "1/8 CELL x 1/2 Al", "-"),
        ("22", "2", "30-40 MESH SS SCREEN + INTAKE FILTER", "8E.3", "-"),
        ("23", "3", "MEMBRANE VENT M12", "ONE PER SEALED CHAMBER", "-"),
        ("24", str(ENC["report"]["junction screws"]), "#6-32 x 1/2 FLAT HEAD 82°, SS", "FRAME JUNCTIONS, FLUSH", "E-201"),
        ("25", str(ENC["report"]["junction screws"]), "#6-32 NYLOC NUT, SS", "FRAME JUNCTIONS, INSIDE", "E-201"),
        ("26", "32", "8-32 SS BUTTON HEAD: 16 x 1/2, 8 x 3/8, 8 x 1/4", "BULKHEAD / PARTITION CLIPS", "E-208"),
        ("27", "24", "8-32 NYLOC NUT, SS", "BULKHEAD / PARTITION CLIPS", "E-208"),
        ("28", "12 + 12", "#10-32 x 1/2 SS SCREW + NYLOC", "AXIS BRACKETS TO THE SHELF", "E-209"),
        ("29", "6 + 12", "1/4 HEX STANDOFF 8-32 F-F + 8-32 x 3/8 BUTTON", "SAMPLER BASEPLATE TO FLOOR", "E-209"),
    ]
    rows += items
    table(doc, page, "EncParts", rows, (10, 14, 66, 50, 18), 308, 170, size=6.5, row_px=14)
    note(doc, page, ["NOTES:",
        "1. EXPLODED IN SERVICE ORDER: RF SERVICE PANEL AND CASSETTE OUT THE FRONT, THEN THE BULKHEAD",
        "   AND THE MOTOR AXIS MODULES. TOP, FLOOR AND REAR STAY ON IN SERVICE.",
        "2. ELECTRONICS, FEEDTHROUGHS, BLOWER AND CONNECTORS ARE IN THE DESIGN-LOG BOM (10).",
        DRAFT], 308, 100, 2.2)
    label(doc, page, "EXPLODED  1:7", 112, 36)


def sheet_nesting(doc):
    page = D.new_page(doc, "E211", "SHEET-METAL NESTING AND STOCK", "TUNER-E-211", 12)
    views = []
    xs = {"14 GA": 85, "12 GA": 220}
    for gauge, n in ENC["nesting"].items():
        g = gauge.replace(" ", "")
        v = vw(doc, page, load(doc, f"enc-nest-{g}.step"), ((0, 0, 1), (1, 0, 0)), NEST_SC, xs[gauge], 165, "Nest" + g)
        views.append((gauge, n, v))
    doc.recompute()
    settle([v for _, _, v in views])
    for gauge, n, v in views:
        overall(doc, page, v, gap=5)
        sw, sl = n["sheet"]
        k = IN * NEST_SC
        for name, x, y, w, h in n["parts"]:   # label each part at its center (view centered on the sheet)
            note(doc, page, [name.upper().replace("MOTOR/SAMPLER PARTITION", "PARTITION")[:18]], xs[gauge] + (x + w / 2 - sw / 2) * k,
                 165 + (y + h / 2 - sl / 2) * k, 1.6)
        label(doc, page, f"{gauge}: ONE {sw} x {sl} SHEET  ({n['area'] / (sw * sl) * 100:.0f}% USED)",
              xs[gauge], 165 - sl / 2 * k - 14)
    note(doc, page, ["NOTES:",
        "1. 5052-H32. LONG SIDE OF EACH PART ACROSS THE SHEET; 0.125 KERF BETWEEN PARTS. SHEAR OR SAW,",
        "   THEN CUT HOLES PER E-202 TO E-209. A 48 x 96 SHEET OF EACH GAUGE COVERS BOTH WITH ROOM",
        "   FOR A SPARE PANEL; MANY SUPPLIERS CUT 48 x 48.",
        "2. THE DECK (L-109) IS NESTED WITH THE 12 GA PARTS. AXIS-BRACKET BLANKS ARE 1/8 6061, SEPARATE.",
        "3. SUPERSEDES THE SIDE-COLUMN CUT LIST AND NESTING IN DESIGN LOG 4 (9 ITEM 29).",
        DRAFT, UNITS], 97, 72, 2.2)


def symbol(doc, page, stem, x, y):
    """Place out/<stem>.svg (written by svgviews.py, page mm at 1:1) centered at (x, y)."""
    s = doc.addObject("TechDraw::DrawViewSymbol", stem.replace("-", "_"))
    s.Symbol = open(os.path.join(OUT, stem + ".svg")).read()
    page.addView(s)
    s.X, s.Y = x, y
    return s


SV = json.load(open(os.path.join(OUT, "svgviews.json"))) if os.path.exists(os.path.join(OUT, "svgviews.json")) else {}
HJ = json.load(open(os.path.join(OUT, "harness.json"))) if os.path.exists(os.path.join(OUT, "harness.json")) else {}


def sheet_populated(doc):
    page = D.new_page(doc, "E212", "POPULATED CABINET - FRONT, LEFT", "TUNER-E-212", 13)
    symbol(doc, page, "svg-pop-front", 72, 152)
    symbol(doc, page, "svg-pop-left", 188, 152)
    label(doc, page, "FRONT, FRONT PANELS OFF 1:6", 72, 86)
    label(doc, page, "LEFT, LEFT PANELS OFF 1:6", 188, 86)
    rows = [("ITEM", "DESCRIPTION", "PART / REF")] + [(str(n), d, r) for n, d, r in SV.get("items", [])]
    table(doc, page, "PopItems", rows, (10, 66, 46), 349, 168, size=6.2, row_px=13)
    note(doc, page, ["NOTES:",
        "1. " + SV.get("open_layout", ""),
        "2. ENVELOPES: CONTROL BOARD, DRIVER BOARD, C1 / C2 (REFERENCE), CHOKE + G10 MOUNT (RF BAY), RELAYS,",
        "   MEASUREMENT BOARD AND COUPLER BOX (SAMPLER). HARNESS: E-213 / E-214, WIRE LIST E-215.",
        "3. HIDDEN LINES OMITTED. GENERATED FROM enclosure.py + svgviews.py; INTERFERENCE-CHECKED WITH PLUG ENVELOPES AND RUNS.",
        DRAFT], 128, 64, 2.1)


def sheet_populated_plan(doc):
    page = D.new_page(doc, "E213", "UTILITY LAYER - POPULATED + HARNESS", "TUNER-E-213", 14)
    symbol(doc, page, "svg-pop-plan", 98, 188)
    symbol(doc, page, "svg-har-plan", 285, 188)
    label(doc, page, "UTILITY LAYER, SHELF AND ABOVE OFF, REAR AT TOP 1:5", 98, 134)
    label(doc, page, "SAME VIEW, HARNESS RUNS 1:5", 285, 134)
    symbol(doc, page, "svg-legend", 330, 100)
    note(doc, page, ["NOTES:",
        "1. ITEM NUMBERS AS E-212. RUN IDs (W#) AND CUT LENGTHS ON E-215.",
        "2. THE CASSETTE RUNS (MAINS, DC, J-A/J-B/J-E PLUGS, ETHERNET, POF, BLOWER LEAD) END IN DISCONNECTS",
        "   WITH A 6 in SERVICE LOOP SO THE CASSETTE SLIDES OUT FRONT (3.0).",
        "3. FLOOR I/O STRIP AT THE LEFT OF THE CONTROL CHAMBER: THE TRAY STOPS AT Y = 3.6 (REV 3.7a).",
        DRAFT], 130, 112, 2.1)


def sheet_harness(doc):
    page = D.new_page(doc, "E214", "HARNESS ROUTING - LEFT, FRONT", "TUNER-E-214", 15)
    symbol(doc, page, "svg-har-left_low", 108, 206)
    symbol(doc, page, "svg-har-front_low", 108, 114)
    label(doc, page, "LEFT, LEFT PANELS OFF, FLOOR TO SHELF 1:3", 108, 168)
    label(doc, page, "FRONT, FRONT PANELS OFF, FLOOR TO SHELF 1:3", 108, 76)
    symbol(doc, page, "svg-legend", 330, 215)
    note(doc, page, ["NOTES:",
        "1. RUNS DRAWN AS CENTERLINES OVER THE HARDWARE (NO HIDDEN-LINE REMOVAL ON WIRES).",
        "2. NO WIRE FOLLOWS A DRIVE TRAIN; THE ONLY SHELF CROSSINGS ARE FT1-FT4 AND THE COAX BULKHEAD (7.1, 7.3).",
        "3. ROUTE THE SAMPLER CABLE (W8) LOW ALONG THE LEFT WALL, AWAY FROM THE STEPPERS (7.3a).",
        "4. BLOWER LEAD RUNS OUTSIDE THE LEFT PANELS IN FLEX CONDUIT TO THE FILTERED DE-9 (E-203).",
        "5. PURPLE RUN CONTINUES IN THE RF BAY: TANK THERMAL, IMBALANCE CT, RF PANEL SWITCH (NOT DRAWN).",
        DRAFT], 318, 150, 2.1)


def sheet_wirelist(doc):
    page = D.new_page(doc, "E215", "WIRE LIST", "TUNER-E-215", 16)
    gl = {k: v[0].split(" (")[0] for k, v in HJ.get("groups", {}).items()}
    rows = [("RUN", "GROUP", "FROM", "TO", "CABLE", "COND", "CUT (in)")]
    for r in HJ.get("runs", []):
        rows.append((r["id"], gl.get(r["group"], r["group"])[:22], r["frm"][:44], r["to"][:44], r["cable"][:42],
                     str(r["n"]), f"{r['length_in']:.0f}"))
    table(doc, page, "WireList", rows, (11, 40, 76, 76, 70, 11, 16), 216, 182, size=5.6, row_px=12)
    total = sum(r["length_in"] for r in HJ.get("runs", [])) / 12
    note(doc, page, ["NOTES:",
        f"1. CUT LENGTH = 3-D ROUTE (harness.py) x 1.15, PLUS 6 in SERVICE LOOP ON CASSETTE RUNS. TOTAL {total:.0f} ft.",
        "2. J-A / J-B / J-E PINOUTS: CONTROL BOARD (kicad/board_control.py, LOG 8B.0.4); CONNECTOR GRADES PER 7.3a.",
        "3. COLOR CODE ON E-213 / E-214. COAX RG-393 PTFE; PRESCALER AND COUPLER SAMPLES RG-316; W27 = W28 IN LENGTH.",
        DRAFT], 185, 92, 2.1)
    symbol(doc, page, "svg-legend", 62, 72)



def sheet_choke(doc):
    """TUNER-E-216: the input choke (§6) itself - every turn - and how it mounts between shelf and deck."""
    page = D.new_page(doc, "E216", "INPUT CHOKE ASSEMBLY", "TUNER-E-216", 17)
    ch, rep, p = ENC["choke"], ENC["report"], ENC["p"]
    sec = vw(doc, page, load(doc, "enc-choke-halfsection.step"), ((0, -1, 0), (1, 0, 0)), 1.0, 78, 150, "ChokeSection")
    hat = D.overlay(doc, page, sec, "hatch-choke.step", "ChokeHatch")
    plan = vw(doc, page, load(doc, "enc-choke-plansection.step"), PLAN, 0.75, 208, 205, "ChokePlan")
    hat_b = D.overlay(doc, page, plan, "hatch-choke-plan.step", "ChokePlanHatch")
    ex = load(doc, "enc-choke-exploded.step")
    iso = vw(doc, page, ex, ISO, 0.4, 208, 98, "ChokeIso")
    doc.recompute()
    settle([sec, hat, plan, hat_b, iso])
    # stack-up chained up the right of the section: shelf top / winding bottom / winding top / deck underside
    cx, cz = ch["section_center"]
    x_st, x_w = p["CHOKE_X"] + 2.3, p["CHOKE_X"] + p["CHOKE_OD"] / 2
    z_sh, z_w0 = ENC["p"]["Z_SH1"], ENC["p"]["Z_SH1"] + p["CHOKE_SO"] + p["CHOKE_BASE"] + p["CHOKE_PAD"]
    z_w1, z_dk = z_w0 + p["CHOKE_H"], z_w0 + p["CHOKE_H"] + rep["choke winding below the deck"]
    v = {k: D.near_vertex(sec, pt, (cx, cz)) for k, pt in
         (("sh", (x_st, z_sh)), ("w0", (x_w, z_w0)), ("w1", (x_w, z_w1)), ("dk", (x_st, z_dk)))}
    sc = IN * sec.Scale
    for a, b, off in (("sh", "w0", 64), ("w0", "w1", 64), ("w1", "dk", 64), ("sh", "dk", 78)):
        za = {"sh": z_sh, "w0": z_w0, "w1": z_w1, "dk": z_dk}
        D.dim(doc, page, sec, "DistanceY", [v[a], v[b]], off, ((za[a] + za[b]) / 2 - cz) * sc)
    # section B-B: base disc, core OD and bore (FT-240: 2.402 / 1.400)
    circ = D.circles(plan)
    for r_in, (dx, dy) in ((p["CHOKE_BASE_D"] / 2, (44, 32)), (2.402 / 2, (-44, 34)), (1.400 / 2, (-40, -30))):
        hit = [r for r in circ if abs(r - r_in * IN) < 0.3]
        if hit:
            D.dim(doc, page, plan, "Diameter", [circ[hit[0]]], dx, dy, fmt="⌀%.3f")
    # balloons: anchors projected the way TechDraw centers the view (2-D bounding box of the projection)
    pts = [iso.projectPoint(vx.Point) for vx in ex.Shape.Vertexes]
    mx = (min(q.x for q in pts) + max(q.x for q in pts)) / 2
    my = (min(q.y for q in pts) + max(q.y for q in pts)) / 2
    half_w = (max(q.x for q in pts) - min(q.x for q in pts)) * iso.Scale / 2
    placed = []
    for item, a in ch["anchors"].items():
        q = iso.projectPoint(App.Vector(*a))
        placed.append((item, (q.x - mx) * iso.Scale, (q.y - my) * iso.Scale))
    k = 1 / iso.Scale
    for side in (-1, 1):
        col = sorted((t for t in placed if (t[1] >= 0) == (side > 0)), key=lambda t: -t[2])
        for n, (item, u, w) in enumerate(col):
            b = doc.addObject("TechDraw::DrawViewBalloon", "Balloon")
            b.SourceView = iso
            page.addView(b)  # adding to the page resets the position, so set it afterwards
            b.OriginX, b.OriginY = u * k, w * k
            b.X = side * (half_w + 12) * k
            b.Y = (46 - n * 92 / max(len(col) - 1, 1)) * k
            b.Text = item
            b.BubbleShape = "Circular"
    rows = [("ITEM", "QTY", "DESCRIPTION", "MATERIAL / PART", "REF")]
    for item in sorted(ch["items"], key=int):
        desc, qty, mat, ref = ch["items"][item]
        if item == "6":
            desc += f" x {rep['choke rod length']:.2f}"
        rows.append((item, qty, desc, mat, ref))
    table(doc, page, "ChokeParts", rows, (8, 11, 55, 49, 14), 338, 212, size=7.2, row_px=15)
    label(doc, page, "SECTION A-A: HALF SECTION  1:1", 82, 62)
    label(doc, page, "SECTION B-B AT MID-WINDING  3:4", 208, 166)
    label(doc, page, "EXPLODED, ASSEMBLY ORDER  2:5", 208, 40)
    note(doc, page, [
        "NOTES:",
        "1. ALL INSULATING (6): NOTHING METAL IN OR ON THE WINDING; ONLY THE SS SCREWS (10) UNDER THE SHELF.",
        "   A-A: FRONT-RIGHT QUARTER REMOVED, SEEN FROM -Y. B-B: LOOKING DOWN, -X (GAP AND LEADS) DOWN.",
        "2. STACK: BOND THE 5 CORES WITH THIN BEADS OF HIGH-TEMPERATURE RTV; WRAP THE BORE AND THE CORE",
        "   EDGES IN GLASS-CLOTH TAPE.",
        f"3. WIND 15 TURNS RG-400 IN ONE LAYER, PACKED AGAINST THE BORE WALL ({ch['pitch']:.0f}° PITCH), THE FIRST-TO-",
        f"   LAST GAP FACING -X (BULKHEAD AND C1). BEND OVER EACH FACE ~{ch['bend_mm']:.0f} mm CENTERLINE: RG-400",
        "   (STRANDED CENTER) ONLY; DO NOT FLEX THE WINDING ONCE MADE. TURNS DRAWN AS CLOSED LOOPS.",
        "4. LEADS: THE CHASSIS LEAD LEAVES THE BOTTOM FOR THE SHELF COAX BULKHEAD (PL-259); THE DECK",
        "   LEAD LEAVES THE TOP FOR C1'S LOWER TERMINAL, SHIELD CLAMPED TO THE DECK (W18). LACE BOTH",
        "   TO THE BASE (11).",
        "5. CLAMP: ROD (6) THROUGH THE OPEN CENTER, NUTS (7) ABOVE AND BELOW; SPIDER (5) OVER THE TOP",
        "   PAD, SNUG BY HAND. ITS ARMS SIT BETWEEN THE STANDOFFS, CROSSINGS LEFT IN THE AIRFLOW.",
        f"6. STACK FROM THE SHELF: STANDOFF {p['CHOKE_SO']:.3f}, BASE {p['CHOKE_BASE']:.3f}, PAD {p['CHOKE_PAD']:.3f},"
        f" WINDING {p['CHOKE_H']:.2f}",
        f"   (WORST-CASE CORES + ARCS), PAD, SPIDER. WINDING {rep['choke winding above the shelf']:.2f} ABOVE THE SHELF,"
        f" {rep['choke winding below the deck']:.2f}",
        "   BELOW THE DECK. ~1.7 lb.",
        "7. BASE AND SPIDER DETAILS: E-209. SHELF HOLES CH1-CH3: E-207. VERIFY INSTALLED: LOG 9 ITEM 49.",
        DRAFT, UNITS], 338, 128, 2.2)


STEMS = {"E200": "E-200-overview", "E202": "E-202-front", "E203": "E-203-left", "E204": "E-204-right",
         "E205": "E-205-top-rear", "E206": "E-206-floor", "E207": "E-207-shelf", "E208": "E-208-bulkhead",
         "E201": "E-201-frame", "E209": "E-209-small-parts", "E210": "E-210-exploded", "E211": "E-211-nesting",
         "E212": "E-212-populated", "E213": "E-213-utility-plan", "E214": "E-214-harness", "E215": "E-215-wire-list",
         "E216": "E-216-choke", "E217": "E-217-wall-clips", "E218": "E-218-partition", "E219": "E-219-tray-flange"}


def main():
    doc = App.newDocument("EnclosureDrawings")
    for sname in doc.getEnumerationsOfProperty("UnitSystem"):
        if sname.lower().startswith("imperial decimal"):
            doc.UnitSystem = sname
    only = [n for n in os.environ.get("ONLY", "").split(",") if n]
    for fn in (sheet_overview, sheet_frame, sheet_front, sheet_left, sheet_right, sheet_top_rear, sheet_floor,
               sheet_shelf, sheet_bulkhead, sheet_small_parts, sheet_exploded, sheet_nesting,
               sheet_populated, sheet_populated_plan, sheet_harness, sheet_wirelist, sheet_choke, sheet_wall_clips,
               sheet_partition, sheet_tray_flange):
        if only and fn.__name__ not in only:
            continue
        try:
            fn(doc)
            log("ok", fn.__name__)
        except Exception:
            log("FAILED", fn.__name__, traceback.format_exc())
    doc.recompute()
    pump(40)
    doc.saveAs(os.path.join(OUT, "enclosure-drawings.FCStd"))
    for p in [o for o in doc.Objects if o.TypeId == "TechDraw::DrawPage"]:
        p.ViewObject.show()
        pump(40)
        TechDrawGui.exportPageAsPdf(p, os.path.join(OUT, STEMS[p.Name] + ".pdf"))
        TechDrawGui.exportPageAsSvg(p, os.path.join(OUT, STEMS[p.Name] + ".svg"))
    log("done")


try:
    main()
except Exception:
    log(traceback.format_exc())
finally:
    D.LOG.close()
    os._exit(0)
