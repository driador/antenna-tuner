# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Ordinate dimensions and feature labels for a panel view, as an SVG overlay in page mm. TechDraw places it
centered on the view (drawings_enclosure.py), so (0, 0) here is the view's center and y runs down.

- Ordinates: each feature's center as a plain number from the panel's lower-left corner, the datum, marked
  0. X values sit on a baseline below the panel for features in its lower half and above it for the upper
  half; Y values left and right likewise. Values too close to read apart spread along the baseline, and
  their extension lines jog to meet them.
- Labels: each feature's tag and size beside it, inside the panel, clear of the other features, the labels
  and the extension lines. A compound cutout's label points to its detail.
- The perimeter holes: each row or column is an even spread, so its two end holes carry the ordinates (which
  also gives the row's position across the panel), and a label inward of it says how many, "EQ SP", and any
  position the spread leaves out. A forced hole (a wall-flange bolt, WF) is a feature of its own.

Pure geometry from out/enclosure.json; no FreeCAD, so the layout can be checked on its own.
"""
import math

IN = 25.4
TEXT = 3.0          # value and label text height, mm
CHAR = 0.56         # osifont's advance per character, in text heights (measured from a render, a touch wide)
PITCH = 4.6         # least spacing between values along a baseline, mm
GAP = 1.2           # an extension line starts this far off its feature, mm
OUT = 2.0           # a jog starts this far outside the panel's edge...
JOG = 4.5           # ...and ends this much further out, where the value's text begins after a small gap
LINE = 0.18         # line weight, mm
SIDES = ("below", "above", "left", "right")


def _fmt(x):
    """3 places, or 4 where the fourth is real (0.3125), so no value reads a rounding off its table."""
    if abs(x) < 5e-5:
        return "0"
    return f"{x:.4f}" if abs(round(x, 3) - x) > 1e-6 else f"{x:.3f}"


def extent(kind, size, conn_pitch, blower):
    """Half width and half height (in) of a cutout with everything it drills."""
    k = kind.rstrip("+")
    if kind.endswith("+"):
        main, extra = size[0], size[1]
        hx, hy = extent(k, main, conn_pitch, blower)
        for du, dv, d in extra:
            hx, hy = max(hx, abs(du) + d / 2), max(hy, abs(dv) + d / 2)
        return hx, hy
    if k in ("hole",):
        return size / 2, size / 2
    if k == "hole4":                    # (dia, d, a, b): a hole with four around it on a centered a x b
        return max(size[0] / 2, size[2] / 2 + size[1] / 2), max(size[0] / 2, size[3] / 2 + size[1] / 2)
    if k in ("dflat", "ddflat"):
        return size[0] / 2, size[0] / 2
    if k == "conn":
        h = max(size / 2, conn_pitch / 2 + 0.0625)
        return h, h
    if k == "fan":
        h = max(blower["hole"] / 2, blower["pitch"] / 2 + blower["screw"] / 2)
        return h, h
    if k == "rect":
        return size[0] / 2, size[1] / 2
    if k == "dsub":
        return max(size[0] / 2, size[2] / 2 + 0.06), size[1] / 2
    return 0.1, 0.1


def _wrap(lines, width=26):
    """Break a long size line at ' + ' or ', ' (or, narrower, ' ON ') so a label stays compact."""
    out = []
    for s in lines:
        while len(s) > width:
            cut = max(s.rfind(" + ", 0, width + 2), s.rfind(", ", 0, width + 1),
                      s.rfind(" ON ", 0, width + 1) if width < 26 else -1)
            if cut <= 0:
                break
            out.append(s[:cut + (1 if s[cut] == "," else 0)].rstrip())
            s = s[cut + (2 if s[cut] == "," else 1):].lstrip()
        out.append(s)
    return out


def label_lines(tag, kind, size, conn_pitch, blower, detail_of):
    """The label's text lines: the tag, and the size wherever it fits in words."""
    return _wrap(_label_lines(tag, kind, size, conn_pitch, blower, detail_of))


def label_forms(tag, kind, size, conn_pitch, blower, detail_of):
    """The label's text as label_lines gives it, and a one-line label also stacked in two (the tag or name,
    then the size or the detail), for where that fits better."""
    first = label_lines(tag, kind, size, conn_pitch, blower, detail_of)
    if len(first) > 1:
        narrow = _wrap(_label_lines(tag, kind, size, conn_pitch, blower, detail_of), 14)
        return [first] + ([narrow] if narrow != first else [])
    s = first[0]
    for sep in (" (", " ⌀", " "):
        if sep in s:
            head, tail = s.split(sep, 1)
            tail = tail.rstrip(")") if sep == " (" else "⌀" + tail if sep == " ⌀" else tail
            # a detail's cutout may go by its tag alone where it is crowded: the table names the detail
            return [first, [head, tail]] + ([[tag]] if kind in ("rect+", "dsub", "hole+") else [])
    return [first]


def _label_lines(tag, kind, size, conn_pitch, blower, detail_of):
    lines = _size_lines(tag, kind, size, conn_pitch, blower, detail_of)
    return [s.strip() for s in lines if s.strip()]          # an untagged feature: its size alone


def hole4_text(size):
    main, d, a, b = size
    on = f"{a:.3f} SQ" if abs(a - b) < 1e-6 else f"{a:.3f} x {b:.3f}"
    return f"⌀{main:.3f} + 4X ⌀{d:.3f} ON {on}"


def _size_lines(tag, kind, size, conn_pitch, blower, detail_of):
    if kind == "hole":
        return [f"{tag} ⌀{size:.3f}"]
    if kind == "hole4":
        return [tag, hole4_text(size)]
    if kind == "dflat":
        return [tag, f"⌀{size[0]:.3f}, FLAT {size[1]:.3f}"]
    if kind == "ddflat":
        return [tag, f"⌀{size[0]:.3f}, FLATS {size[1]:.3f}"]
    if kind == "conn":
        return [tag, f"⌀{size:.3f} + 4X ⌀0.125 ON {conn_pitch:.3f} SQ"]
    if kind == "fan":
        return [tag, f"⌀{blower['hole']:.3f} + 4X ⌀{blower['screw']:.3f} ON {blower['pitch']:.3f} SQ"]
    if kind == "rect":
        return [f"{tag} {size[0]:.3f} x {size[1]:.3f}"]
    if kind in ("rect+", "dsub", "hole+"):                  # sized in a 1:1 detail
        return [f"{tag} (DETAIL {detail_of.get(tag, tag)})"]
    return [tag]


def _box_dist(a, b):
    """Gap between two boxes (x0, y0, x1, y1), 0 if they touch or overlap."""
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


class Overlay:
    def __init__(self, pm, scale, conn_pitch, blower, detail_of=None, notch_label=True, screw=0.177, labels=True):
        self.pm, self.k = pm, IN * scale
        self.with_labels = labels                  # False: ordinates only, the sizes said elsewhere (a caption)
        self.screw = screw
        self.L, self.H = pm["L"], pm["H"]
        self.conn_pitch, self.blower = conn_pitch, blower
        self.detail_of = detail_of or {}
        self.notch_label = notch_label
        self.items = []
        self.ext = {s: 0.0 for s in SIDES}         # how far past each edge the overlay reaches, mm
        self.segs = []                             # extension-line segments inside the panel, for the labels
        self.placed = []                           # label boxes placed so far

    # panel (u, v) in -> page mm from the view's center, y down
    def px(self, u):
        return (u - self.L / 2) * self.k

    def py(self, v):
        return -(v - self.H / 2) * self.k

    def edge(self, side):
        return {"below": self.py(0), "above": self.py(self.H), "left": self.px(0), "right": self.px(self.L)}[side]

    def _path(self, pts):
        self.items.append('<path d="M' + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
                          + f'" stroke="#000000" stroke-width="{LINE}" fill="none" stroke-linecap="round"/>')

    def _text(self, x, y, s, anchor="start", rotate=False, size=TEXT):
        rot = f' transform="rotate(-90 {x:.2f} {y:.2f})"' if rotate else ""
        self.items.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="osifont, sans-serif" font-size="{size}" '
                          f'text-anchor="{anchor}" fill="#000000"{rot}>{s}</text>')

    # ---------------------------------------------------------------- ordinates
    def features(self):
        out = []
        for t, kind, u, v, size, nt in self.pm["cutouts"]:
            hx, hy = extent(kind, size, self.conn_pitch, self.blower)
            out.append(dict(tag=t, kind=kind, u=u, v=v, size=size, hx=hx, hy=hy, note=nt,
                            notch=t.startswith("N") and t[1:].isdigit(), perim=False))
        r = self.screw / 2
        for _edge, horiz, at, a, b, _n, gone in self.pm.get("fastener_rows", []):
            for x in (a, b):                            # each row's ends carry its ordinates
                if any(abs(x - g) < 1e-6 for g in gone):
                    continue
                u, v = (x, at) if horiz else (at, x)
                out.append(dict(tag="", kind="hole", u=u, v=v, size=self.screw, hx=r, hy=r, notch=False, perim=True))
        for u, v in self.pm.get("forced", []):
            out.append(dict(tag="WF", kind="hole", u=u, v=v, size=self.screw, hx=r, hy=r, notch=False,
                            perim=False))
        return out

    def perimeter(self):
        """Every perimeter hole's box (page mm, y down), the ones between each row's ends too."""
        r = self.screw / 2 * self.k + 0.6
        out = []
        for _edge, horiz, at, a, b, n, gone in self.pm.get("fastener_rows", []):
            for j in range(n):
                x = a + (b - a) * j / (n - 1) if n > 1 else a
                if any(abs(x - g) < 1e-6 for g in gone):
                    continue
                cx, cy = (self.px(x), self.py(at)) if horiz else (self.px(at), self.py(x))
                out.append((cx - r, cy - r, cx + r, cy + r))
        return out

    def _crossings(self, feats, own, a0, a1, b0, b1):
        """Features other than `own` whose boxes the segment from (a0, b0) to (a1, b1) passes through (an
        axis-parallel segment, panel inches)."""
        n = 0
        for f in feats:
            if f in own:
                continue
            if (min(a0, a1) - f["hx"] < f["u"] < max(a0, a1) + f["hx"]) and \
                    (min(b0, b1) - f["hy"] < f["v"] < max(b0, b1) + f["hy"]):
                n += 1
        return n

    def ordinates(self, feats):
        L, H = self.L, self.H
        groups = {"x": {}, "y": {}}
        for f in feats:
            if f["notch"]:
                continue
            groups["x"].setdefault(round(f["u"], 3), []).append(f)
            groups["y"].setdefault(round(f["v"], 3), []).append(f)
        per = {s: [] for s in SIDES}
        # each value goes to the side its extension line crosses the fewest other features on the way to,
        # then the nearer
        for u, g in groups["x"].items():
            lo, hi = min(g, key=lambda f: f["v"]), max(g, key=lambda f: f["v"])
            down = (self._crossings(feats, g, u, u, 0, lo["v"]) * 1000 + lo["v"], "below")
            up = (self._crossings(feats, g, u, u, hi["v"], H) * 1000 + H - hi["v"], "above")
            if min(down, up)[1] == "below":
                per["below"].append((u, self.px(u), self.py(lo["v"]) + lo["hy"] * self.k + GAP))
            else:
                per["above"].append((u, self.px(u), self.py(hi["v"]) - hi["hy"] * self.k - GAP))
        for v, g in groups["y"].items():
            lt, rt = min(g, key=lambda f: f["u"]), max(g, key=lambda f: f["u"])
            left = (self._crossings(feats, g, 0, lt["u"], v, v) * 1000 + lt["u"], "left")
            right = (self._crossings(feats, g, rt["u"], L, v, v) * 1000 + L - rt["u"], "right")
            if min(left, right)[1] == "left":
                per["left"].append((v, self.py(v), self.px(lt["u"]) - lt["hx"] * self.k - GAP))
            else:
                per["right"].append((v, self.py(v), self.px(rt["u"]) + rt["hx"] * self.k + GAP))
        for side, items in per.items():
            if not items:
                continue
            horiz = side in ("below", "above")
            # the datum, 0, at the panel's corner on this baseline
            if horiz:
                items.append((0.0, self.px(0), self.edge(side)))
            else:
                items.append((0.0, self.py(0), self.edge(side)))
            self._baseline(side, items)

    def _baseline(self, side, items):
        """items: [(value, along, start)] - along the baseline (x for below/above, y for left/right), and
        where the extension line starts on the other axis."""
        horiz = side in ("below", "above")
        sgn = 1 if side in ("below", "right") else -1          # outward, in page mm (y down)
        e = self.edge(side)
        # the along-axis runs left to right for below/above, and bottom to top (y decreasing) for left/right
        key = (lambda it: it[1]) if horiz else (lambda it: -it[1])
        items = sorted(items, key=key)
        want = [it[1] if horiz else -it[1] for it in items]
        pos = []
        for w in want:
            pos.append(max(w, pos[-1] + PITCH) if pos else w)
        lim = (self.px(self.L) if horiz else -self.py(self.H)) + 10.0   # may run a little past the far corner
        if pos and pos[-1] > lim:
            over = pos[-1] - lim
            pos = [p - over for p in pos]
            for i in range(len(pos) - 2, -1, -1):
                pos[i] = min(pos[i], pos[i + 1] - PITCH)
        j0, j1 = e + sgn * OUT, e + sgn * (OUT + JOG)
        t0 = e + sgn * (OUT + JOG + 1.0)
        longest = 0.0
        for (val, along, start), p in zip(items, pos):
            a = along
            b = p if horiz else -p
            if horiz:
                pts = [(a, start), (a, j0)] + ([(b, j1)] if abs(b - a) > 0.05 else [(a, j1)]) + [(b, t0 - sgn * 0.6)]
                self._path(pts)
                self.segs.append(((a, start), (a, e)))
            else:
                pts = [(start, a), (j0, a)] + ([(j1, b)] if abs(b - a) > 0.05 else [(j1, a)]) + [(t0 - sgn * 0.6, b)]
                self._path(pts)
                self.segs.append(((start, a), (e, a)))
            s = _fmt(val)
            w = len(s) * CHAR * TEXT
            longest = max(longest, w)
            if side == "below":       # vertical text, reading up, running down from t0
                self._text(b + 0.35 * TEXT, t0, s, anchor="end", rotate=True)
            elif side == "above":     # vertical text, reading up, running up from t0
                self._text(b + 0.35 * TEXT, t0, s, anchor="start", rotate=True)
            elif side == "left":
                self._text(t0, b + 0.35 * TEXT, s, anchor="end")
            else:
                self._text(t0, b + 0.35 * TEXT, s, anchor="start")
        self.ext[side] = OUT + JOG + 1.0 + longest

    # ---------------------------------------------------------------- labels
    def labels(self, feats):
        k = self.k
        x0, x1, y0, y1 = self.px(0), self.px(self.L), self.py(self.H), self.py(0)   # y0 < y1 (y down)
        band = 0.85 * k                                 # the perimeter fastener rows: avoid, not forbid
        boxes = list(self.placed)                       # placed labels, the rows' among them
        solid, core = [], []                            # every feature with a little room, and without
        for f in feats:
            cx, cy = self.px(f["u"]), self.py(f["v"])
            core.append((cx - f["hx"] * k, cy - f["hy"] * k, cx + f["hx"] * k, cy + f["hy"] * k))
            solid.append((cx - f["hx"] * k - 0.6, cy - f["hy"] * k - 0.6, cx + f["hx"] * k + 0.6, cy + f["hy"] * k + 0.6))
        leaders = []                                    # the leaders drawn so far
        rows = self.perimeter()

        def overlap(a, b):
            return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))

        def crosses(p0, p1, s):
            """Does the leader p0-p1 cross the axis-parallel segment s?"""
            (ax, ay), (bx2, by2) = s
            def orient(a, b, c):
                return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            d1, d2 = orient(p0, p1, (ax, ay)), orient(p0, p1, (bx2, by2))
            d3, d4 = orient((ax, ay), (bx2, by2), p0), orient((ax, ay), (bx2, by2), p1)
            return d1 * d2 < 0 and d3 * d4 < 0

        def through(p0, p1, b, pad=-0.2):
            """Does the leader p0-p1 pass through box b, grown by pad (shrunk, if negative)?"""
            for t in (i / 24 for i in range(1, 24)):
                x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
                if b[0] - pad < x < b[2] + pad and b[1] - pad < y < b[3] + pad:
                    return True
            return False

        def hits_seg(bx, s):
            (ax, ay), (bx2, by2) = s
            lo_x, hi_x = min(ax, bx2) - 0.3, max(ax, bx2) + 0.3
            lo_y, hi_y = min(ay, by2) - 0.3, max(ay, by2) + 0.3
            return not (bx[2] < lo_x or bx[0] > hi_x or bx[3] < lo_y or bx[1] > hi_y)

        def cost(bx, own, leader=False):
            c = 0.0
            if bx[0] < x0 + 0.5 or bx[2] > x1 - 0.5 or bx[1] < y0 + 0.5 or bx[3] > y1 - 0.5:
                c += 1e6                                 # outside the panel
            for i, s in enumerate(solid):
                if i != own:                            # on a feature, or only in the room around it
                    c += 1e4 * overlap(bx, core[i]) + 50.0 * overlap(bx, s)
            for rb in rows:                             # nor on any perimeter hole
                c += 1e4 * overlap(bx, (rb[0] + 0.6, rb[1] + 0.6, rb[2] - 0.6, rb[3] - 0.6)) + 50.0 * overlap(bx, rb)
            for p0, p1 in leaders:
                if through(p0, p1, bx):
                    c += 2500.0
            for b in boxes:
                c += 1e5 * overlap(bx, b)
            for s in self.segs:
                if hits_seg(bx, s):
                    c += 2500.0
            inner = (x0 + band, y0 + band, x1 - band, y1 - band)
            out_area = (bx[2] - bx[0]) * (bx[3] - bx[1]) - overlap(bx, inner)
            c += 2.0 * max(0.0, out_area)
            if leader:                                  # its leader says whose it is
                return c
            # a label nearer another feature than its own reads as that one's, and one between its own and
            # a near neighbor, level with both, reads as either
            own_d = near(bx, own)
            ox, oy = (core[own][0] + core[own][2]) / 2, (core[own][1] + core[own][3]) / 2
            for j in range(len(feats)):
                if j == own or feats[j]["notch"]:
                    continue
                if near(bx, j) < own_d - 0.5:
                    c += 2000.0
                q = core[j]
                # level with it: sharing a good part of its height (width), not a sliver
                lv = min(bx[3], q[3]) - max(bx[1], q[1]) > min(2.0, 0.25 * (q[3] - q[1]))
                ab = min(bx[2], q[2]) - max(bx[0], q[0]) > min(2.0, 0.25 * (q[2] - q[0]))
                if lv and q[0] - bx[2] < 8.0 and bx[0] - q[2] < 8.0 and \
                        (ox < bx[0] < bx[2] < q[0] or q[2] < bx[0] < bx[2] < ox):
                    c += 60.0 + 80.0 * max(0.0, 2.0 - max(q[0] - bx[2], bx[0] - q[2])) / 2.0   # the more, touching
                if ab and q[1] - bx[3] < 8.0 and bx[1] - q[3] < 8.0 and \
                        (oy < bx[1] < bx[3] < q[1] or q[3] < bx[1] < bx[3] < oy):
                    c += 60.0
            # nor so close under, over or beside another label that the two read as one
            for b in boxes:
                if min(bx[2], b[2]) - max(bx[0], b[0]) > 0 and -0.01 < max(b[1] - bx[3], bx[1] - b[3]) < 1.5:
                    c += 20.0
                if min(bx[3], b[3]) - max(bx[1], b[1]) > 0 and -0.01 < max(b[0] - bx[2], bx[0] - b[2]) < 1.5:
                    c += 20.0
            return c

        def near(bx, j):
            """How far box bx is from feature j: from its circle if it is round, else from its box."""
            f = feats[j]
            if f["kind"] != "hole":
                return _box_dist(bx, solid[j])
            cx, cy = self.px(f["u"]), self.py(f["v"])
            return max(0.0, _box_dist(bx, (cx, cy, cx, cy)) - f["hx"] * k - 0.6)

        notch_done = False

        def crowd(i):                                   # neighbors within 1.5 in: the crowded pick first
            f = feats[i]
            return sum(1 for g in feats if g is not f and abs(g["u"] - f["u"]) < 1.5 and abs(g["v"] - f["v"]) < 1.5)
        order = sorted(range(len(feats)), key=lambda i: (-crowd(i), -len(label_lines(
            feats[i]["tag"], feats[i]["kind"], feats[i]["size"], self.conn_pitch, self.blower, self.detail_of)[0])))
        notches = [j for j, g in enumerate(feats) if g["notch"]]
        alike = {}                                      # untagged features alike (a part's slots): one label too
        for j, g in enumerate(feats):
            if not g["tag"] and not g["perim"] and not g["notch"]:
                alike.setdefault((g["kind"], repr(g["size"])), []).append(j)
        said = set()
        for i in order:
            f = feats[i]
            if f.get("perim"):
                continue
            key = (f["kind"], repr(f["size"]))
            if f["notch"]:
                if notch_done or not self.notch_label:
                    continue
                notch_done = True
                lines = [f"{len(notches)}X NOTCH {f['size'][0]:.3f} x {f['size'][1]:.3f}"]
                around = notches                       # one label for them all, by whichever has room
                forms = [lines]
            elif not f["tag"] and len(alike.get(key, ())) > 1:
                if key in said:
                    continue
                said.add(key)
                text = label_lines("", f["kind"], f["size"], self.conn_pitch, self.blower, self.detail_of)
                lines = [f"{len(alike[key])}X {f['note'] + ' ' if f.get('note') else ''}{text[0]}"] + text[1:]
                around = alike[key]
                forms = [lines]
            else:
                forms = label_forms(f["tag"], f["kind"], f["size"], self.conn_pitch, self.blower, self.detail_of)
                around = [i]
            best = None
            for lines in forms:
                w = max(len(s) for s in lines) * CHAR * TEXT + 1.0     # and a little room either side
                h = len(lines) * TEXT * 1.25
                # the fewest lines where they fit as well, and the tag alone only where nothing else does
                tag_only = len(forms) > 2 and lines == forms[-1] and len(lines) == 1
                stack = (40.0 if tag_only else 2.0 * (len(lines) - len(forms[0]))) if len(forms) > 1 else 0.0
                for d, i2 in ((d, i2) for d in (1.0, 2.5, 4.5, 7.0, 10.0, 14.0, 19.0) for i2 in around):
                    f2 = feats[i2]
                    cx, cy = self.px(f2["u"]), self.py(f2["v"])
                    rx, ry = f2["hx"] * k, f2["hy"] * k
                    # right of it and level reads best, then centered above or below, then the corners;
                    # left of it only where the right has no room
                    for dx, dy in ((1, 0), (0, -1), (0, 1), (1, -1), (1, 1), (0.5, -1), (0.5, 1),
                                   (-1, 0), (-1, -1), (-1, 1), (-0.5, -1), (-0.5, 1)):
                        # the label's nearest corner or edge sits d off the feature's box in that direction
                        lx = cx + dx * (rx + d) + (0 if dx > 0.6 else -w if dx < -0.6 else -w / 2 + dx * w / 2)
                        ly = cy + dy * (ry + d) + (0 if dy > 0 else -h if dy < 0 else -h / 2)
                        bx = (lx, ly, lx + w, ly + h)
                        c = cost(bx, i2, d > 4.0) + d * 3.0 + (0.6 if dy else 0.0) + (0.3 if dx < 0 else 0.0) + stack
                        if d > 4.0:                     # a leader: only where the label cannot sit beside
                            c += 150.0
                        else:
                            if dx and dy:               # off a corner, between its own and another above or
                                oc = core[i2]           # below it, it reads as either
                                for j, q in enumerate(core):
                                    if j != i2 and not feats[j]["notch"] and max(q[0] - bx[2], bx[0] - q[2]) < 6.0 \
                                            and (oc[3] <= bx[1] and bx[3] <= q[1] or q[3] <= bx[1] and bx[3] <= oc[1]):
                                        c += 60.0
                            if tag_only or dy:          # a bare tag, or a label off its feature's corner or end,
                                gap = min((near(bx, j) for j in range(len(feats))   # must sit clearly nearer its own
                                           if j != i2 and not feats[j]["notch"]), default=99.0)   # than any other
                                c += (400.0 if tag_only else 300.0) * max(0.0, near(bx, i2) + 1.5 - gap) / 1.5
                        if d > 4.0:                     # it will need a leader: one that crosses lines or
                            nx, ny = min(max(cx, bx[0]), bx[2]), min(max(cy, bx[1]), bx[3])   # labels costs
                            c += 1500.0 * sum(1 for sg in self.segs if crosses((nx, ny), (cx, cy), sg))
                            c += 1500.0 * sum(1 for b in boxes if through((nx, ny), (cx, cy), b, 0.4))
                            c += 1500.0 * sum(1 for j, sb in enumerate(solid)
                                              if j != i2 and through((nx, ny), (cx, cy), sb))   # or holes
                            c += 1500.0 * sum(1 for sb in rows if through((nx, ny), (cx, cy), sb))
                        if best is None or c < best[0]:
                            best = (c, bx, d, cx, cy, rx, ry, lines, dx)
            _c, bx, d, cx, cy, rx, ry, lines, dx = best
            boxes.append(bx)
            self.placed.append(bx)
            # the text hugs its feature whatever its true width: from the left edge of a label to the right,
            # to the right edge of one to the left, and centered over or under it
            tx, anchor = (bx[0] + 0.5, "start") if dx > 0.6 else (bx[2] - 0.5, "end") if dx < -0.6 else \
                ((bx[0] + bx[2]) / 2, "middle")
            if d > 4.0:                                  # with a leader, toward where the leader meets the box
                nx = min(max(cx, bx[0]), bx[2])
                tx, anchor = (bx[0] + 0.5, "start") if nx <= bx[0] + 0.01 else (bx[2] - 0.5, "end") \
                    if nx >= bx[2] - 0.01 else ((bx[0] + bx[2]) / 2, "middle")
            for j, s in enumerate(lines):
                self._text(tx, bx[1] + TEXT * (1.0 + 1.25 * j) - 0.25 * TEXT, s, anchor=anchor,
                           size=TEXT if j == 0 else TEXT * 0.9)
            if d > 4.0:                                  # far from its feature: a leader to it
                nx = min(max(cx, bx[0]), bx[2])
                ny = min(max(cy, bx[1]), bx[3])
                ang = math.atan2(ny - cy, nx - cx)
                ex, ey = cx + math.cos(ang) * min(rx, ry), cy + math.sin(ang) * min(rx, ry)
                self._path([(nx, ny), (ex, ey)])
                leaders.append(((nx, ny), (ex, ey)))

    def row_labels(self, feats):
        """'8X EQ SP' inward of each perimeter row or column, at whichever point along it has room, and under
        it any position the spread leaves out. They go first: each has only its own row to sit beside."""
        k = self.k
        x0, x1, y0, y1 = self.px(0), self.px(self.L), self.py(self.H), self.py(0)
        solid = [(self.px(f["u"]) - f["hx"] * k - 0.6, self.py(f["v"]) - f["hy"] * k - 0.6,
                  self.px(f["u"]) + f["hx"] * k + 0.6, self.py(f["v"]) + f["hy"] * k + 0.6) for f in feats]
        named = [sb for sb, f in zip(solid, feats) if not f["perim"] and not f["notch"]]
        solid += self.perimeter()                       # and every other row's holes

        def overlap(a, b):
            return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
        for _edge, horiz, at, a, b, n, gone in self.pm.get("fastener_rows", []):
            lines = [f"{n}X EQ SP"] + (["OMIT AT " + ", ".join(_fmt(g) for g in gone)] if gone else [])
            w, h = max(len(s) for s in lines) * CHAR * TEXT * 0.9 + 1.0, len(lines) * TEXT * 1.15
            best = None
            for frac in (0.5, 0.35, 0.65, 0.2, 0.8):
                x = a + (b - a) * frac
                # inward of the row, or (a row inside the panel, with room) the other side of it
                if horiz:
                    cx, cy = self.px(x), self.py(at)
                    inward = -1 if at < self.H / 2 else 1         # page y runs down
                    for side, d in ((s_, d_) for s_ in (inward, -inward) for d_ in (1.8, 3.5, 6.0)):
                        top = cy - d - h if side < 0 else cy + d
                        bx = (cx - w / 2, top, cx + w / 2, top + h)
                        c = self._row_cost(bx, solid, named, overlap, x0, x1, y0, y1) + d + (4.0 if side != inward else 0)
                        if best is None or c < best[0]:
                            best = (c, bx)
                else:
                    cx, cy = self.px(at), self.py(x)
                    inward = 1 if at < self.L / 2 else -1
                    for side, d in ((s_, d_) for s_ in (inward, -inward) for d_ in (1.8, 3.5, 6.0)):
                        left = cx + d if side > 0 else cx - d - w
                        bx = (left, cy - h / 2, left + w, cy + h / 2)
                        c = self._row_cost(bx, solid, named, overlap, x0, x1, y0, y1) + d + (4.0 if side != inward else 0)
                        if best is None or c < best[0]:
                            best = (c, bx)
            _c, bx = best
            self.placed.append(bx)
            for j, s in enumerate(lines):
                self._text(bx[0], bx[1] + TEXT * (0.9 + 1.15 * j), s, anchor="start", size=TEXT * 0.9)

    def _row_cost(self, bx, solid, named, overlap, x0, x1, y0, y1):
        c = 0.0
        if bx[0] < x0 + 0.3 or bx[2] > x1 - 0.3 or bx[1] < y0 + 0.3 or bx[3] > y1 - 0.3:
            c += 1e6
        for sb in solid:
            c += 1e4 * overlap(bx, sb)
        for sb in named:                                # leave a named feature room for its own label
            c += 300.0 * max(0.0, 5.0 - _box_dist(bx, sb))
        for pb in self.placed:
            c += 1e5 * overlap(bx, pb)
        for (ax, ay), (bx2, by2) in self.segs:
            if not (bx[2] < min(ax, bx2) - 0.3 or bx[0] > max(ax, bx2) + 0.3 or
                    bx[3] < min(ay, by2) - 0.3 or bx[1] > max(ay, by2) + 0.3):
                c += 2500.0
        return c

    # ---------------------------------------------------------------- the SVG
    def svg(self):
        feats = self.features()
        self.ordinates(feats)
        self.row_labels(feats)
        if self.with_labels:
            self.labels(feats)
        hw = self.L / 2 * self.k + max(self.ext["left"], self.ext["right"]) + 3
        hh = self.H / 2 * self.k + max(self.ext["below"], self.ext["above"]) + 3
        body = "\n".join(self.items)
        # a symmetric box, its corners marked with specks, so the view's center is the overlay's center
        specks = "".join(f'<circle cx="{sx * hw:.2f}" cy="{sy * hh:.2f}" r="0.01" fill="#ffffff"/>'
                         for sx in (-1, 1) for sy in (-1, 1))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{2 * hw:.2f}mm" height="{2 * hh:.2f}mm" '
                f'viewBox="{-hw:.2f} {-hh:.2f} {2 * hw:.2f} {2 * hh:.2f}">\n{specks}\n{body}\n</svg>\n')


class Polar:
    """Bolt circles and callouts for a round part seen face-on, as an SVG overlay centered on its view (TechDraw
    puts it on the view's center; `off` (mm, +y up) is where the part's own center sits from there): a dashed
    circle for each pattern, and a leader from one of its holes out past the rim to its callout."""

    def __init__(self, scale, rim, items, off=(0.0, 0.0)):
        # rim: the part's outer radius, in; items: [(bc, angle, r, lines)] - the pattern's circle diameter (in,
        # None: none), the page angle (deg, counterclockwise from +x) of the hole the leader starts from, at bc / 2
        # from the center (0 for the center hole), that hole's radius (in), and the callout's lines
        self.k, self.rim, self.items, self.off = IN * scale, rim, items, off

    def svg(self):
        k, cx, cy = self.k, self.off[0], -self.off[1]
        out, reach = [], self.rim * k
        for bc, ang, r, lines in self.items:
            a = math.radians(ang)
            ux, uy = math.cos(a), -math.sin(a)
            if bc:
                out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{bc / 2 * k:.2f}" fill="none" stroke="#000000" '
                           f'stroke-width="{LINE}" stroke-dasharray="3 1 0.6 1"/>')
            d0 = (bc or 0) / 2 * k + r * k
            x0, y0 = cx + ux * d0, cy + uy * d0
            x1, y1 = cx + ux * (self.rim * k + 4.0), cy + uy * (self.rim * k + 4.0)
            side = 1 if ux >= 0 else -1
            x2 = x1 + side * 3.0
            out.append(f'<path d="M{x0:.2f} {y0:.2f} L{x1:.2f} {y1:.2f} L{x2:.2f} {y1:.2f}" stroke="#000000" '
                       f'stroke-width="{LINE}" fill="none"/>')
            for j, s in enumerate(lines):
                out.append(f'<text x="{x2 + side * 1.0:.2f}" y="{y1 + 1.0 + (j - (len(lines) - 1) / 2) * TEXT * 1.2:.2f}" '
                           f'font-family="osifont, sans-serif" font-size="{TEXT}" fill="#000000" '
                           f'text-anchor="{"start" if side > 0 else "end"}">{s}</text>')
                reach = max(reach, abs(x2 - cx) + 2 + len(s) * CHAR * TEXT, abs(y1 - cy) + len(lines) * TEXT)
        hw = hh = reach + abs(self.off[0]) + abs(self.off[1]) + 3
        specks = "".join(f'<circle cx="{sx * hw:.2f}" cy="{sy * hh:.2f}" r="0.01" fill="#ffffff"/>'
                         for sx in (-1, 1) for sy in (-1, 1))
        body = "\n".join(out)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{2 * hw:.2f}mm" height="{2 * hh:.2f}mm" '
                f'viewBox="{-hw:.2f} {-hh:.2f} {2 * hw:.2f} {2 * hh:.2f}">\n{specks}\n{body}\n</svg>\n')


if __name__ == "__main__":                   # write each panel's overlay alone, for a look outside FreeCAD
    import json
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    enc = json.load(open(os.path.join(here, "out", "enclosure.json")))
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    for p in enc["panels"]:
        o = Overlay(p, 0.4, enc["p"]["CONN_PITCH"], enc["p"]["BLOWER"])
        slug = p["name"].replace("/", "-").replace(" ", "-")
        open(os.path.join(out, f"ord-{slug}.svg"), "w").write(o.svg())
        print(slug, {s: round(v, 1) for s, v in o.ext.items()})
