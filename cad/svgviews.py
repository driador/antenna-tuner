"""Hidden-line SVG views of the populated cabinet for TUNER-E-212 / E-213.

TechDraw cannot color a view's lines, so these sheets are drawn here: build123d's hidden-line
projection for the hardware, the harness centerlines and balloons drawn on top, written as SVG in
page millimeters and placed on the TechDraw sheet as a symbol (colors survive the PDF export).
Run under the build123d venv; writes out/svg-*.svg and out/svgviews.json (placement data).
"""

import json
import math
import sys
import time

from build123d import Box, Compound, Pos, Vector

import enclosure as E
import harness as HN
import roller as R

OUT = R.OUT
IN = 25.4

# view: camera direction (from the model toward the viewer) and up
VIEWS = {
    "front": ((-1, 0, 0), (0, 0, 1)),
    "left": ((0, 1, 0), (0, 0, 1)),
    "plan": ((0, 0, 1), (1, 0, 0)),
    "iso": ((-1, 1, 0.8), (0, 0, 1)),
}


def basis(view):
    d, up = (Vector(*v).normalized() for v in VIEWS[view])
    up = (up - d * up.dot(d)).normalized()
    right = up.cross(d)                     # viewer looks along -d
    return d, up, right


def to2d(view, p):
    _d, up, right = basis(view)
    v = Vector(*p)
    return v.dot(right), v.dot(up)


def project(view, shapes):
    """Visible edges as 2-D polylines (inches, view plane)."""
    d, up, _r = basis(view)
    comp = Compound([s for _, s in shapes])
    vis, _hid = comp.project_to_viewport(tuple(d * 200), tuple(up), (0, 0, 0))
    lines = []
    for e in vis:
        n = 2 if e.geom_type.name == "LINE" else max(6, min(48, int(e.length * 8)))
        pts = [e.position_at(i / (n - 1)) for i in range(n)]
        lines.append([(p.X, p.Y) for p in pts])
    return lines


def check_mapping():
    """build123d's viewport coordinates must equal to2d() — the overlays depend on it."""
    probe = [("p", Pos(1, 2, 3) * Box(0.2, 0.2, 0.2))]
    for v in VIEWS:
        ls = project(v, probe)
        cx = sum(p[0] for l in ls for p in l) / sum(len(l) for l in ls)
        cy = sum(p[1] for l in ls for p in l) / sum(len(l) for l in ls)
        ex = to2d(v, (1, 2, 3))
        assert abs(cx - ex[0]) < 0.05 and abs(cy - ex[1]) < 0.05, (v, (cx, cy), ex)


def clip_below(shapes, z):
    """Utility-layer plan: everything below z (the shelf underside), cut there."""
    keep = []
    cutter = Pos(0, 0, z - 50) * Box(100, 100, 100)
    for n, s in shapes:
        bb = s.bounding_box()
        if bb.min.Z >= z:
            continue
        keep.append((n, s if bb.max.Z <= z else s & cutter))
    return keep


# ---------------------------------------------------------------- SVG writing
class Sheet:
    """One SVG symbol: model content at `scale` (page mm per model mm), page-mm coordinates."""

    def __init__(self, view, scale):
        self.view, self.k = view, IN * scale
        self.items = []          # svg fragments in page mm (y down)
        self.bbox = [1e9, 1e9, -1e9, -1e9]

    def _xy(self, u, v):
        return u * self.k, -v * self.k

    def _grow(self, x, y):
        b = self.bbox
        b[0], b[1], b[2], b[3] = min(b[0], x), min(b[1], y), max(b[2], x), max(b[3], y)

    def lines(self, polylines, color="#333333", width=0.18):
        segs = []
        for pl in polylines:
            pts = [self._xy(*p) for p in pl]
            for x, y in pts:
                self._grow(x, y)
            segs.append("M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts))
        self.items.append(f'<path d="{" ".join(segs)}" stroke="{color}" stroke-width="{width}" fill="none" '
                          f'stroke-linecap="round" stroke-linejoin="round"/>')

    def run(self, pts3, color, width):
        self.lines([[to2d(self.view, p) for p in pts3]], color, width)

    def text(self, x, y, s, size=2.5, anchor="middle", color="#000000"):
        self._grow(x - size * len(s) * 0.3, y - size)
        self._grow(x + size * len(s) * 0.3, y + size * 0.3)
        self.items.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="osifont, sans-serif" font-size="{size}" '
                          f'text-anchor="{anchor}" fill="{color}">{s}</text>')

    def balloons(self, anchors, r=2.6, gap=6.2, side_pad=8.0):
        """anchors: [(label, (x, y, z))]. Bubbles in columns left and right of the view, spread
        vertically, leaders to the anchor."""
        x0, y0, x1, y1 = self.bbox
        cx = (x0 + x1) / 2
        cols = {"L": [], "R": []}
        for lab, p in anchors:
            ax, ay = self._xy(*to2d(self.view, p))
            cols["L" if ax < cx else "R"].append((ay, ax, lab))
        for side, items in cols.items():
            items.sort()
            bx = (x0 - side_pad) if side == "L" else (x1 + side_pad)
            last, ys = -1e9, []
            for ay, _ax, _lab in items:
                y = max(ay, last + gap)
                ys.append(y)
                last = y
            over = (ys[-1] - y1) if ys else 0
            if over > 0:
                ys = [y - over for y in ys]
            for (ay, ax, lab), by in zip(items, ys):
                ex = bx + (r if side == "L" else -r)
                self.items.append(f'<path d="M{ex:.2f} {by:.2f} L{ax:.2f} {ay:.2f}" stroke="#000000" '
                                  f'stroke-width="0.18" fill="none"/>')
                self.items.append(f'<circle cx="{ax:.2f}" cy="{ay:.2f}" r="0.45" fill="#000000"/>')
                self.items.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{r}" stroke="#000000" '
                                  f'stroke-width="0.25" fill="#ffffff"/>')
                self.text(bx, by + 0.9, lab, size=2.6)
                self._grow(bx - r, by - r)
                self._grow(bx + r, by + r)

    def svg(self, pad=1.0):
        x0, y0, x1, y1 = self.bbox
        x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        w, h = x1 - x0, y1 - y0
        body = "\n".join(self.items)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h:.2f}mm" '
                f'viewBox="{x0:.2f} {y0:.2f} {w:.2f} {h:.2f}">\n{body}\n</svg>\n'), (w, h)


def legend(groups, used):
    s = Sheet("front", 1 / IN)
    y = 0
    s.text(0, y, "HARNESS COLOR CODE", size=3.0, anchor="start")
    y += 6
    for g in used:
        label, color, width = groups[g]
        s.items.append(f'<path d="M0 {y - 1:.2f} L12 {y - 1:.2f}" stroke="{color}" stroke-width="{max(width, 1.2)}" '
                       f'fill="none"/>')
        s._grow(0, y - 3)
        s._grow(12, y)
        s.text(15, y, label, size=2.6, anchor="start")
        y += 5.2
    return s


# ---------------------------------------------------------------- content
# populated items: (number, description, part / ref, anchor point)
ITEMS = [
    (1, "ROLLER INDUCTOR 34 uH, 5.2 in", "TUNER-L-100", (R.ROLLER_X - 2.0, R.ROLLER_Y, R.Z_DECK_TOP + 5.25)),
    (2, "C1 VACUUM VARIABLE (ENVELOPE)", "15 kV CLASS, 5.1", (R.CAP_X[0], R.CAP_Y, R.Z_DECK_TOP + 4.25)),
    (3, "C2 VACUUM VARIABLE (ENVELOPE)", "UCSX-740-10, 5.1", (R.CAP_X[1], R.CAP_Y, R.Z_DECK_TOP + 4.25)),
    (4, "FLOATING DECK + STANDOFFS", "L-109", (4.0, -4.9, R.Z_DECK_TOP)),
    (5, "GROUNDED SHELF", "E-207", (5.5, 5.5, E.Z_SH1)),
    (6, "AXIS MODULE C1 (MOTOR, BRACKET)", "E-209, M-2", (-3.5, -3.25, 2.5)),
    (7, "AXIS MODULE C2", "E-209, M-2", (1.75, -3.25, 2.5)),
    (8, "AXIS MODULE ROLLER", "E-209, M-2", (-1.5, 2.625, 2.5)),
    (9, "G10 SHAFTS + OLDHAM COUPLERS B", "L-108", (R.ROLLER_X, R.ROLLER_Y, R.Z_DECK - 1.66)),
    (10, "24 V SUPPLY", "MEAN WELL UHP-200-24", (-5.6, -3.0, 1.8)),
    (11, "CONTROL BOARD (ASSUMED ENVELOPE)", "TEENSY 4.1, DC-DCs", (-6.85, 0.5, 3.0)),
    (12, "DISPLAY", "NEXTION NX4832K035", (-7.6, 3.9, 2.6)),
    (13, "CASSETTE TRAY + RAILS", "E-209", (-6.0, -4.0, 0.62)),
    (14, "BULKHEAD: J-A, J-B, J-E, FT-C/D/P", "E-208, 7.3a", (E.X_BULK, 4.0, 3.15)),
    (15, "PARTITION: J-S, FT-P, COAX X", "E-208, 7.3a", (E.X_PART, 3.2, 4.3)),
    (16, "DRIVER BOARD (ASSUMED ENVELOPE)", "3 AXES", (0.0, 4.0, 0.8)),
    (17, "INPUT CHOKE, 5 x FT-240-61, ON G10 MOUNT", "6", (E.CHOKE_X - E.CHOKE_OD / 2, E.CHOKE_Y,
                                                            E.Z_SH1 + E.CHOKE_SO + E.CHOKE_BASE + E.CHOKE_H / 2)),
    (18, "MEASUREMENT BOARD + COUPLER", "6A, 6B.3a", (3.78, 3.2, 2.0)),
    (19, "K1 / K2 COAX RELAYS", "TOHTSU CX600N-24", (6.2, 3.2, 1.6)),
    (20, "CAL LOAD + THERMOSTAT", "G150N50W4E, F20A085", (4.6, 1.0, 0.5)),
    (21, "CAL-LOAD HEATSINK (BELOW FLOOR)", "WAKEFIELD 441K", (4.6, 1.0, -2.5)),
    (22, "IEC INLET", "TE CORCOM 3EGG1-2", (-6.3, 4.6, 0.9)),
    (23, "RJ45 FEEDTHROUGH", "SWITCHCRAFT EHRJ45P5E", (-6.3, 6.15, 1.5)),
    (24, "COAX INPUT SO-239 / AUX N", "83-798 / 82-97", (3.55, -3.9, 0.6)),
    (25, "BLOWER + GUARD (EXTERIOR)", "DELTA AFB1212VHE-F00", (3.4, 9.0, E.BLOWER["z"])),
    (26, "INTAKE FILTER + HONEYCOMB", "8", (-3.0, -8.4, E.INTAKE["z"])),
    (27, "WALL FLANGE (x2)", "E-209", (7.0, 8.1, 10.0)),
    (28, "OUTPUT FEEDTHROUGHS (TOP)", "8D", (E.FT_X, 0.0, E.H - 0.5)),
    (29, "SHELF FEEDTHROUGHS FT1-FT4", "TUSONIX 2499", (1.125, -6.5, E.Z_SH1)),
    (30, "BLOWER-LEAD DE-9", "FCE17-E09SM-290", (E.FAN_ENTRY[0], E.F, E.FAN_ENTRY[1])),
    (31, "ENCODER / LIMIT-CAM MODULE (x3)", "7.1, 7.2 - FABRICATE", (-1.72, -3.25, 4.3)),
]

VIEW_ITEMS = {   # which balloons each populated view carries
    "front": [1, 2, 4, 5, 9, 12, 13, 14, 17, 25, 26, 28],
    "left": [1, 5, 6, 7, 8, 10, 14, 15, 17, 18, 19, 21, 27, 29, 30, 31],
    "plan": [10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 22, 23, 24],
}

OPEN_LAYOUT = ("NOT SHOWN: IMBALANCE CT ON THE OUTPUT LEADS AT THE TOP FEEDTHROUGHS, TANK THERMAL PROBE. "
               "NO PAD, NO LINK, NO VACUUM RELAYS (5.2, 5.4 SUPERSEDED REV 3.7b).")


def clip_run(pts, zmax):
    """Polylines of a run kept below zmax (segments crossing it are cut at the plane)."""
    out, cur = [], []
    for a, b in zip(pts, pts[1:]):
        ia, ib = a[2] <= zmax, b[2] <= zmax
        if ia and not cur:
            cur = [a]
        if ia and ib:
            cur.append(b)
        elif ia != ib:
            t = (zmax - a[2]) / (b[2] - a[2])
            m = tuple(a[i] + t * (b[i] - a[i]) for i in range(3))
            if ia:
                cur.append(m)
                out.append(cur)
                cur = []
            else:
                cur = [m, b]
    if len(cur) > 1:
        out.append(cur)
    return out


LOW_Z = 5.6       # harness close-ups: floor to just above the shelf (the utility layer)


def view_shapes(view, model):
    if view.endswith("_low"):
        keep = [(n, s) for n, s in view_shapes(view[:-4], model) if n != "cal-load heatsink"]
        return clip_below(keep, LOW_Z)
    if view == "front":
        drop = ("RF service panel", "cassette face", "intake filter")
        return [(n, s) for n, s in model if n not in drop]
    if view == "left":
        drop = ("left upper panel", "left lower panel", "blower", "fan entry plug envelope")
        return [(n, s) for n, s in model if n not in drop and not (n == "wall flange" and s.bounding_box().min.Y > 0)]
    if view == "plan":
        drop = ("shelf",)
        return clip_below([(n, s) for n, s in model if n not in drop], E.Z_SH0 - 0.02)
    return model


def build(which):
    t0 = time.time()
    model = HN.populated()
    meta = {}
    items = {n: (d, p, a) for n, d, p, a in ITEMS}
    for view, scale in which:
        base = view.replace("_low", "")
        shapes = view_shapes(view, model)
        polylines = project(base, shapes)
        wh = None
        if not view.endswith("_low"):   # populated sheet (black hardware + balloons)
            sp = Sheet(base, scale)
            sp.lines(polylines, "#222222", 0.18)
            if view in VIEW_ITEMS:
                sp.balloons([(str(i), items[i][2]) for i in VIEW_ITEMS[view]])
            svg, wh = sp.svg()
            (OUT / f"svg-pop-{view}.svg").write_text(svg)
        # harness sheet (grey hardware + colored runs)
        sh = Sheet(base, scale)
        sh.lines(polylines, "#a8a8a8", 0.13)
        zmax = E.Z_SH0 if view == "plan" else (LOW_Z if view.endswith("_low") else 99)
        for rid, grp, _f, _t, _c, _n, _cas, pts, _d, _i in HN.RUNS:
            label, color, width = HN.GROUPS[grp]
            for seg in clip_run(pts, zmax):
                if view.endswith("_low"):          # drop the exterior stub below the floor
                    seg = [p for p in seg if p[2] >= -0.05]
                if len(seg) > 1:
                    sh.run(seg, color, width)
        svg2, wh2 = sh.svg()
        (OUT / f"svg-har-{view}.svg").write_text(svg2)
        meta[view] = dict(pop=wh, har=wh2, scale=scale)
        print(f"{view}: {len(polylines)} edges, {time.time() - t0:.0f} s", flush=True)
    used = list(dict.fromkeys(r[1] for r in HN.RUNS))
    lg, _ = legend(HN.GROUPS, used).svg()
    (OUT / "svg-legend.svg").write_text(lg)
    old = json.loads((OUT / "svgviews.json").read_text()) if (OUT / "svgviews.json").exists() else {}
    old.update(meta)
    old["items"] = [[n, d, p] for n, d, p, _a in ITEMS]
    old["open_layout"] = OPEN_LAYOUT
    (OUT / "svgviews.json").write_text(json.dumps(old, indent=1))


if __name__ == "__main__":
    check_mapping()
    sel = sys.argv[1:] or ["front", "left", "plan", "left_low", "front_low"]
    scales = {"front": 1 / 6, "left": 1 / 6, "plan": 1 / 5, "iso": 1 / 7, "front_low": 1 / 3, "left_low": 1 / 3}
    build([(v, scales[v]) for v in sel])
