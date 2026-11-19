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
from drawings import (  # noqa: E402
    App, IN, OUT, TechDrawGui, label, load, log, note, overall, pump, settle, table, tag, view,
)

D.SUBTITLE = "ENCLOSURE - DRAFT"
D.N_SHEETS = 17
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
    "VIEWS FROM OUTSIDE. HOLE POSITIONS FROM THE LOWER-LEFT CORNER AS VIEWED.",
    "5052-H32 ALUMINUM. FASTENER HOLES 8-32 CLEARANCE 0.177; CAPTIVE SCREWS ON SERVICE PANELS: USE THE",
    "RETAINER'S HOLE SIZE. MATCH-DRILL THE FRAME FROM THE PANELS AND FIT 8-32 RIVNUTS (4).",
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
    if kind == "dsub":
        return f"{size[0]:.3f} x {size[1]:.3f} + 2x⌀0.120, {size[2]:.3f} APART"
    if kind == "conn":
        return f"⌀{size:.3f} + 4x⌀0.125 ON {ENC['p']['CONN_PITCH']:.3f} SQ"
    if kind == "fan":
        return f"⌀{ENC['p']['BLOWER']['hole']:.2f} + 4x⌀{ENC['p']['BLOWER']['screw']:.2f} ON {ENC['p']['BLOWER']['pitch']:.3f} SQ"
    return f"⌀{size:.3f}"


def panel_view(doc, page, name, x, y, scale, vname):
    pm = PANELS[name]
    src = load(doc, "enc-panel-" + name.replace("/", "-").replace(" ", "-") + ".step")
    return view(doc, page, src, tuple(pm["n"]), scale, x, y, vname, tuple(pm["U"])), pm


def panel_overall(doc, page, v, gap=6, gap_x=None, gap_y=None):
    """Overall width and height from the outermost edges (robust to notched corners). gap_x / gap_y push
    the width / height dimension out past a row of callout bubbles."""
    from drawings import bbox, dim, extreme
    x0, x1, y0, y1 = bbox(v)
    dim(doc, page, v, "DistanceX", [extreme(v, -1, 0), extreme(v, 1, 0)], (x0 + x1) / 2, y0 - (gap_x or gap))
    dim(doc, page, v, "DistanceY", [extreme(v, 0, -1), extreme(v, 0, 1)], x1 + (gap_y or gap), (y0 + y1) / 2)


def tag_rows(pm, cutouts):
    """Group cutouts by the panel edge nearest each one."""
    L, Hh = pm["L"], pm["H"]
    rows = {"bottom": [], "top": [], "left": [], "right": []}
    for t, _kind, u, vv, _size, _nt in cutouts:
        d = {"left": u, "right": L - u, "bottom": vv, "top": Hh - vv}
        rows[min(d, key=d.get)].append((t, u, vv))
    return rows


def place_tags(doc, page, v, pm, sc, rows):
    """Callout bubbles just outside the panel edge nearest each cutout, spaced along that edge, inside
    the overall dimensions (panel_overall pushes those out) so no leader crosses a dimension."""
    L, Hh = pm["L"], pm["H"]
    k = IN * sc
    for edge, items in rows.items():
        horiz = edge in ("bottom", "top")
        # along the edge; ties (cutouts stacked in line) put the one nearest the edge first so leaders don't cross
        near = {"bottom": lambda it: it[2], "top": lambda it: -it[2], "left": lambda it: it[1], "right": lambda it: -it[1]}
        items.sort(key=lambda it: (round(it[1] if horiz else it[2], 3), near[edge](it)))
        pos, last, prev = [], -1e9, ""
        for t, u, vv in items:
            # bubbles grow with the label; a horizontal row also has to clear each leader's shoulder
            n = max(len(t), len(prev))
            gap = 17 + 3 * n if horiz else 12 + 1.5 * n
            along = max((u - L / 2) * k if horiz else (vv - Hh / 2) * k, last + gap)
            pos.append(along)
            last, prev = along, t
        over = (pos[-1] - (L if horiz else Hh) / 2 * k - 6) if pos else 0
        if over > 0:                        # ran off the far end: slide the row back
            pos = [p - over for p in pos]
        for (t, u, vv), along in zip(items, pos):
            px, py = (u - L / 2) * k, (vv - Hh / 2) * k
            if edge == "bottom":
                bx, by = along, -Hh / 2 * k - 9
            elif edge == "top":
                bx, by = along, Hh / 2 * k + 9
            elif edge == "left":
                bx, by = -L / 2 * k - 9, along
            else:
                bx, by = L / 2 * k + 9, along
            tag(doc, page, v, t, (u, vv), (L / 2, Hh / 2), (bx - px, by - py))


def panel_sheet(doc, pid, title, dwg, no, entries, tables_x=318, table_y=None):
    """entries: [(panel name, x, y, scale)]. Views left, tables and notes right."""
    page = D.new_page(doc, pid, title, dwg, no)
    views = []
    for i, (name, x, y, sc) in enumerate(entries):
        v, pm = panel_view(doc, page, name, x, y, sc, f"{pid}_{i}")
        views.append((v, pm, sc, x, y))
    doc.recompute()
    settle([v for v, *_ in views])
    cut_rows = [("PANEL", "TAG", "FEATURE", "SIZE", "FROM LEFT", "FROM BOTTOM")]
    fas_rows = [("PANEL", "EDGE", "QTY", "MAX PITCH", "INSET")]
    for v, pm, sc, x, y in views:
        short = pm["name"].upper().replace(" PANEL", "")
        shown = [cu for cu in pm["cutouts"] if not cu[0].startswith("N")]
        rows = tag_rows(pm, [cu for cu in shown if not (cu[0].startswith("FT") and cu[0] not in ("FT1", "FT7"))])
        panel_overall(doc, page, v, gap_x=26 if rows["bottom"] else None, gap_y=26 if rows["right"] else None)
        for t, kind, u, vv, size, nt in pm["cutouts"]:
            if t.startswith("N") and t[1:].isdigit():
                continue
            cut_rows.append((short, t, nt, size_text(kind, size), f"{u:.3f}", f"{vv:.3f}"))
        place_tags(doc, page, v, pm, sc, rows)
        for edge, n, pitch, inset in pm["edges"]:
            fas_rows.append((short, edge, str(n), f"{pitch:.2f}", f"{inset:.3f}"))
    ty = table_y if table_y is not None else 228
    if len(cut_rows) > 1:
        table(doc, page, f"{pid}Cut", cut_rows, (24, 10, 74, 36, 16, 18), tables_x, ty, size=6.5, row_px=14)
        ty -= len(cut_rows) * 3.7 / 2 + 6
    nf = len(fas_rows)
    if nf > 1:
        table(doc, page, f"{pid}Fas", fas_rows, (30, 22, 10, 18, 14), tables_x - 28, ty - nf * 3.7 / 2, size=6.5,
              row_px=14)
    notes = []
    for _v, pm, *_ in views:
        notes += [f"{pm['name'].upper()}: {pm['gauge']}, {pm['L']:.3f} x {pm['H']:.3f}, {pm['fasteners']} FASTENER HOLES."]
        notes += pm["notes"]
    note(doc, page, ["NOTES:"] + notes + STD_NOTES + [DRAFT, UNITS], 318, 100, 2.1)
    return page, views


def sheet_front(doc):
    panel_sheet(doc, "E202", "FRONT PANELS", "TUNER-E-202", 3,
                [("RF service panel", 78, 190, 0.22), ("cassette face", 78, 92, 0.22)])


def sheet_left(doc):
    panel_sheet(doc, "E203", "LEFT SIDE PANELS (+Y)", "TUNER-E-203", 4,
                [("left upper panel", 78, 168, 0.22), ("left lower panel", 78, 62, 0.22)])


def sheet_right(doc):
    panel_sheet(doc, "E204", "RIGHT SIDE PANELS (-Y)", "TUNER-E-204", 5,
                [("right upper panel", 78, 168, 0.22), ("right lower panel", 78, 62, 0.22)])


def sheet_top_rear(doc):
    panel_sheet(doc, "E205", "TOP AND REAR PANELS", "TUNER-E-205", 6,
                [("top panel", 62, 190, 0.18), ("rear panel", 172, 150, 0.18)])


def sheet_floor(doc):
    panel_sheet(doc, "E206", "FLOOR - LOW-VOLTAGE I/O", "TUNER-E-206", 7, [("floor", 88, 150, 0.30)])


def sheet_shelf(doc):
    panel_sheet(doc, "E207", "GROUNDED SHELF", "TUNER-E-207", 8, [("shelf", 88, 150, 0.30)])


WEND = ((0, -1, 0), (1, 0, 0))      # wall clip along its length: the L, heel at lower left
WBOX = ((0, 0, 1), (0, 1, 0))       # its floor / shelf leg face-on, length across the page
WPLT = ((-1, 0, 0), (0, -1, 0))     # its plate leg face-on
WDET = ((0, -1, 0), (1, 0, 0))      # typical mounting seen along Y: control side left, motor side right


def sheet_bulkhead(doc):
    page, _views = panel_sheet(doc, "E208", "BULKHEAD AND PARTITION", "TUNER-E-208", 9,
                               [("bulkhead", 92, 180, 0.3), ("motor/sampler partition", 92, 86, 0.3)])
    wc = load(doc, "enc-wall-clip.step")
    we = vw(doc, page, wc, WEND, 1.5, 182, 192, "WClipEnd")
    wb = vw(doc, page, wc, WBOX, 1.5, 218, 192, "WClipBox")
    wp = vw(doc, page, wc, WPLT, 1.5, 264, 192, "WClipPlate")
    wf = vw(doc, page, load(doc, "enc-wall-clip-floor.step"), WDET, 1.0, 181, 146, "WClipFloor")
    ws = vw(doc, page, load(doc, "enc-wall-clip-shelf.step"), WDET, 1.0, 226, 146, "WClipShelf")
    doc.recompute()
    settle([we, wb, wp, wf, ws])
    for v in (wb, wp):
        overall(doc, page, v, gap=3)
    label(doc, page, "BULKHEAD / PARTITION CLIP (16)  1.5:1", 226, 168)
    label(doc, page, "AT FLOOR  1:1", 181, 125)
    label(doc, page, "AT SHELF  1:1", 228, 125)
    side = {("bulkhead", 1): "MOTOR SIDE", ("bulkhead", -1): "CONTROL SIDE",
            ("partition", 1): "SAMPLER SIDE", ("partition", -1): "MOTOR SIDE"}
    rows = [("PLATE", "EDGE", "CLIPS ON", "CLIP CENTERS, Y (+ = LEFT)")]
    for plate in ("bulkhead", "partition"):
        for edge in ("floor", "shelf"):
            cl = [(s, y) for e, s, y in ENC["p"]["WALL_CLIPS"][plate] if e == edge]
            rows.append((plate.upper(), edge.upper(), side[(plate, cl[0][0])], ", ".join(f"{y:+.2f}" for _s, y in cl)))
    table(doc, page, "WClips", rows, (22, 12, 24, 46), 356, 190, size=6.5, row_px=14)
    note(doc, page, [
        "CLIPS (16): 1/2 x 1/2 x 1/8 6061-T6 x 1.00. ONE HOLE PER LEG, MID-LENGTH,",
        "ON THE LEG FLAT. FLOOR / SHELF LEG ⌀0.177. PLATE LEG: BULKHEAD CLIPS ⌀0.136",
        "TAPPED 8-32 (PEM CLS-832-1 IF IT COMES OFF OFTEN); PARTITION CLIPS ⌀0.177.",
        "FLOOR LEG: 8-32 x 1/2 BUTTON HEAD UP THROUGH THE FLOOR, NYLOC ON THE CLIP.",
        "SHELF LEG: 8-32 x 1/2 DOWN FROM THE RF BAY, NYLOC UNDER THE CLIP.",
        "BULKHEAD: 8-32 x 1/4 FROM THE CONTROL SIDE INTO THE TAPPED LEG - IT COMES OUT",
        "WITHOUT TOUCHING THE CLIPS. PARTITION: 8-32 x 3/8 + NYLOC.",
        "FIX THE CLIPS AT THE TABLE POSITIONS, THEN MATCH-DRILL THROUGH THEM.",
        "AT FLOOR / AT SHELF: BULKHEAD, SECTION ON THE SCREW PLANE, HOLES IN LINE.",
    ], 337, 153, 2.0)


JISO = ((-1, -1, 0.9), (1, -1, 0))  # into a rear-left corner from inside the box, above (Z up on the page)
CPLAN = ((0, 0, 1), (-1, 0, 0))     # corner clip from above: the L, heel at lower left
CFACE = ((0, 1, 0), (-1, 0, 0))     # corner clip, one leg face-on


def sheet_frame(doc):
    page = D.new_page(doc, "E201", "FRAME - 6061-T6 ANGLE", "TUNER-E-201", 2)
    fr = vw(doc, page, load(doc, "enc-frame.step"), ISO, 0.13, 62, 182, "FrameIso")
    jt = vw(doc, page, load(doc, "enc-frame-joint.step"), JISO, 0.6, 152, 190, "JointIso")
    jx = vw(doc, page, load(doc, "enc-frame-joint-exploded.step"), JISO, 0.5, 152, 112, "JointExploded")
    clip = load(doc, "enc-corner-clip.step")
    cp = vw(doc, page, clip, CPLAN, 1.0, 40, 74, "ClipPlan")
    cf = vw(doc, page, clip, CFACE, 1.0, 88, 74, "ClipFace")
    doc.recompute()
    settle([fr, jt, jx, cp, cf])
    overall(doc, page, cf, gap=4)            # the L plan has no clean extreme vertices: sizes are in note 3
    label(doc, page, "JUNCTION (16), FROM INSIDE  0.6:1", 152, 151)
    label(doc, page, "JUNCTION, EXPLODED  0.5:1", 158, 70)
    label(doc, page, "CORNER CLIP (16): PLAN, LEG  1:1", 64, 50)
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
    page = D.new_page(doc, "E209", "SMALL PARTS", "TUNER-E-209", 10)
    tray = vw(doc, page, load(doc, "enc-cassette-tray.step"), PLAN, 0.3, 75, 215, "Tray")
    rail = vw(doc, page, load(doc, "enc-cassette-rail.step"), FRONT, 1.0, 165, 215, "RailEnd")
    br_src = load(doc, "enc-C1-axis-bracket.step")
    br_iso = vw(doc, page, br_src, ISO, 0.6, 75, 150, "BracketIso")
    br_side = vw(doc, page, br_src, FRONT, 0.6, 150, 150, "BracketSide")
    base = vw(doc, page, load(doc, "enc-sampler-baseplate.step"), PLAN, 0.3, 75, 80, "Base")
    fl_src = load(doc, "enc-wall-flange.step")
    fl = vw(doc, page, fl_src, ((1, 0, 0), (0, 1, 0)), 0.18, 215, 120, "FlangeWall")
    # input choke mount (6, Rev 3.7c): base disc and spider in plan, the stack between shelf and deck stubs
    cb = vw(doc, page, load(doc, "enc-choke-base.step"), PLAN, 0.5, 232, 232, "ChokeBase")
    cs = vw(doc, page, load(doc, "enc-choke-spider.step"), PLAN, 0.5, 298, 232, "ChokeSpider")
    ca = vw(doc, page, load(doc, "enc-choke-assembly.step"), FRONT, 0.35, 368, 226, "ChokeAsm", hidden=True)
    doc.recompute()
    settle([tray, rail, br_iso, br_side, base, fl, cb, cs, ca])
    for v in (tray, rail, br_side, base, fl):
        overall(doc, page, v, gap=5)
    # overall() reads vertices, which a disc does not have at its extremes: dimension the outer circle instead
    for v, (dx, dy) in ((cb, (24, 22)), (cs, (20, 18))):
        circ = D.circles(v)
        if circ:
            D.dim(doc, page, v, "Diameter", [circ[max(circ)]], dx, dy, fmt="⌀%.3f")
    label(doc, page, "CHOKE BASE (G10 1/4)", 232, 199)
    label(doc, page, "CHOKE SPIDER (G10 1/8)", 298, 199)
    label(doc, page, "CHOKE MOUNT", 368, 195)
    rep = ENC["report"]
    note(doc, page, [
        "5. INPUT CHOKE MOUNT (6) - ALL INSULATING, NOTHING METAL IN OR ON THE WINDING. BASE DISC: G10 1/4,",
        "   ⌀3.40; ⌀0.52 CENTER; 6 x ⌀0.15 VENTS ON ⌀0.72; 3 x ⌀0.177 CSK 82° x ⌀0.34 ON ⌀2.60 FOR NYLON 8-32",
        "   FLAT HEADS, FLUSH. SPIDER: G10 1/8, HUB ⌀1.00, 3 ARMS 0.50 WIDE, ROUND ENDS ON ⌀2.60, ⌀0.52 CENTER,",
        "   ARMS BETWEEN THE STANDOFFS. STANDOFFS: 3 x G10 ⌀3/8 x 5/8, 8-32 F-F; SS 8-32 UP THROUGH THE SHELF",
        f"   (E-207 CH1-CH3). ROD: 1/2-13 FIBERGLASS x {rep['choke rod length']:.2f}, FRP NUTS. WINDING (15 t RG-400,",
        f"   5 x FT-240-61) ON 1/16 SILICONE PADS: {rep['choke winding above the shelf']:.2f} ABOVE THE SHELF,"
        f" {rep['choke winding below the deck']:.2f} BELOW THE DECK. PLANS 0.5:1; MOUNT 0.35:1, SHELF TO DECK, ROD HIDDEN.",
    ], 318, 179, 2.1)
    label(doc, page, "CASSETTE TRAY (12 GA)  0.3:1", 75, 237)
    label(doc, page, "RAIL END  1:1", 165, 237)
    label(doc, page, "MOTOR AXIS BRACKET (x3)", 112, 184)
    label(doc, page, "SAMPLER BASEPLATE (12 GA)  0.3:1", 75, 42)
    label(doc, page, "WALL FLANGE (x2), WALL LEG", 215, 42)
    note(doc, page, ["NOTES:",
        "1. CASSETTE TRAY: 12 GA 5052, RIDES TWO 1/2 x 1/2 x 1/8 RAILS ON THE FLOOR, BEHIND THE FRONT LIP.",
        "   COMPONENT HOLES MATCH THE PARTS FITTED: PSU (ON EDGE), CONTROL BOARD, DC-DCs. EVERYTHING",
        f"   ON THE TRAY <= {ENC['report']['cassette component height limit']:.2f} TALL TO PASS THE OPENING.",
        "2. AXIS BRACKET: 1/8 6061, FORMED OR WELDED U - TOP PLATE (4 x #10 TO THE SHELF UNDERSIDE, 1.50",
        "   CLEARANCE FOR THE BUSHING), TWO SIDES, MOTOR PLATE WITH NEMA 23 PATTERN 4 x 0.21 ON 1.856 SQ",
        "   AND 1.52 PILOT, FOR THE 23HS22-2804S (M-2). 1.75 TALL: TAKEOFF PULLEY + COUPLER A INSIDE; THE",
        "   ENCODER / LIMIT-CAM MODULE (7.1, 7.2) BOLTS TO THE OPEN SIDE. LOOSEN COUPLER A'S G10 CLAMP, DROP",
        "   AND SLIDE OUT FORWARD. QTY 3.",
        "3. SAMPLER BASEPLATE: 12 GA, FIXED TO THE FLOOR ON 1/4 SPACERS; COUPLER, MEASUREMENT BOARD,",
        "   K1/K2 MOUNT TO IT (THE CHOKE IS IN THE RF BAY, REV 3.7c). SERVICED THROUGH THE LEFT LOWER PANEL.",
        "4. WALL FLANGE: 2 x 2 x 3/16 6061 x 21. ONE LEG BOLTS THROUGH THE SIDE PANEL INTO THE REAR",
        "   POST (3 x 8-32, LONGER SCREWS, SHARED WITH THE PANEL LINE), THE OTHER LIES FLUSH WITH THE",
        "   REAR. 3 SLOTS 0.40 x 0.75 FOR 3/8 LAGS INTO A 3/4 PLYWOOD BACKER ACROSS THE STUDS.",
        DRAFT, UNITS], 322, 112, 2.3)


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
        ("11", "1", "MOTOR / SAMPLER PARTITION", "5052-H32 12 GA", "E-208"),
        ("12", "1", "CASSETTE TRAY + 2 RAILS", "12 GA / 1/2 ANGLE", "E-209"),
        ("13", "3", "MOTOR AXIS BRACKET", "1/8 6061", "E-209"),
        ("14", "1", "SAMPLER BASEPLATE", "5052-H32 12 GA", "E-209"),
        ("15", "2", "WALL FLANGE", "2 x 2 x 3/16 6061", "E-209"),
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
         "E216": "E-216-choke"}


def main():
    doc = App.newDocument("EnclosureDrawings")
    for sname in doc.getEnumerationsOfProperty("UnitSystem"):
        if sname.lower().startswith("imperial decimal"):
            doc.UnitSystem = sname
    only = [n for n in os.environ.get("ONLY", "").split(",") if n]
    for fn in (sheet_overview, sheet_frame, sheet_front, sheet_left, sheet_right, sheet_top_rear, sheet_floor,
               sheet_shelf, sheet_bulkhead, sheet_small_parts, sheet_exploded, sheet_nesting,
               sheet_populated, sheet_populated_plan, sheet_harness, sheet_wirelist, sheet_choke):
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
