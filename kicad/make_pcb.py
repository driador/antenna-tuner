#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Build a board's PCB from its verified netlist: `python3 make_pcb.py <board>`.

Both boards are 4-layer with a solid GND plane on In1. The generator
(board_<board>.py) tags every part with a block; each block is skyline-packed
into a fixed region of the board, and connectors that must sit on an edge are
placed first, so the router starts from a sensible floor plan.
"""
import pcbnew, sexpr, io, os, sys

import sys, json
BOARD = sys.argv[1] if len(sys.argv) > 1 else 'measurement'
NET = f'{BOARD}.net'
OUT  = f'{BOARD}.kicad_pcb'
MM = pcbnew.FromMM

# Control board floor plan: board_control.py tags every part with a block; each
# column (x0, y0, x1, y1 in mm, 3 mm clear of the edge) takes its blocks in order.
# Left end = cabinet +Y, where the bulkhead ribbons, the POF and the blower lead
# arrive; right end = cabinet -Y, where the PSU's 24 V lead lands.
COLUMNS_CONTROL = [
    ((3, 3, 44, 88),    ['conn', 'ja', 'jb', 'je', 'fiber']),         # ribbons and their R/C
    ((44, 3, 106, 88),  ['teensy', 'logic', 'relay', 'cal', 'freq', 'panel']),
    ((106, 3, 136, 88), ['power', 'blower']),
]
ROT_CONTROL = {'A1': 90, 'U13': 90, 'J1': 90, 'J5': 90, 'J6': 90, 'J7': 90, 'J8': 90, 'J9': 90, 'J10': 90}
# Parts that must face out of an edge, placed before their column is packed:
# ref -> (column index, 'top' | 'bottom', courtyard left x in mm).
# - The Teensy (flat on its sockets, as always) is turned 90 deg in the board's
#   plane so its SD end is at the top edge. The board stands on edge in the
#   cassette, so that edge points up and is open once the cassette slides out:
#   the clear approach §8B.5.6 asks for. Its USB end faces a kept-clear strip.
# - The HFBR's fiber port faces the left end (the POF rises from the floor I/O
#   strip on that side).
# - The 24 V terminal block's wire entry faces the right end.
PINNED_CONTROL = {'A1': (1, 'top', 44.0), 'U13': (0, 'bottom', 0.5), 'J1': (2, 'top', None)}
# Strips no part may be packed into: (column index, x0, x1) from the top part down
# to the board edge. Below the Teensy's USB end, so a plug reaches it in place.
KEEPOUT_CONTROL = [(1, 44.0, 62.6)]
# wider tracks where current flows; everything else keeps the 0.15 mm default.
# name: (track width, nets[, clearance]) in mm
NETCLASS_CONTROL = {
    'Power':  (0.60, ['+24V_IN', '+24V', '+24V_5', '+24V_12', '+12V', 'BLOWER_LO',
                      'K1_PLUS', 'K2_PLUS', 'K1_LO', 'K2_LO', 'K1_SNS', 'K2_SNS', 'HFBR_A', 'HFBR_K']),
    'Supply': (0.40, ['+5V', '+3V3']),
}

# Measurement board floor plan (100 x 74 mm, inside the sampler's 4.0 x 3.0 in
# envelope). Seen from the component side the left edge faces cabinet -Y: the
# /1024 SMA is at its top, so its plug clears the solder-side envelope of the
# partition feedthrough FT-P below it, and the cal-load detector sits in the
# corner nearest the load (floor J). The FWD/REF inputs take the
# right edge, so the load node (up to ~390 V peak) is ~70 mm from the REF tap.
# The J-S ribbon header is top centre, under J-S on the partition.
COLUMNS_MEAS = [
    ((8.5, 3, 30, 22), ['freqout']),
    ((3, 22, 30, 44),  ['power']),
    ((3, 44, 30, 55),  ['cal']),
    ((3, 55, 30, 66),  ['hv']),         # the tap pad, its ground pad and the 1 kV disc
    ((30, 3, 64, 19),  ['conn']),
    ((30, 19, 64, 46), ['counter']),
    ((30, 46, 64, 71), ['swr']),
    ((64, 3, 92, 24),  ['rf_fwd']),
    ((64, 24, 92, 48), ['ad8302']),
    ((64, 48, 92, 71), ['rf_ref']),
]
ROT_MEAS = {'J4': 90}                 # the header's long side along the top edge
# the tap pad clears H3's grounded pad and its own ground pad by > 2.5 mm
PINNED_MEAS = {'J4': (4, 'top', 31.0), 'J5': (3, 'bottom', 10.0), 'J6': (3, 'bottom', 17.0)}
KEEPOUT_MEAS = []
# Absolute placements, x, y (mm, footprint origin) and rotation: the edge SMAs
# seated 0.35 mm in from the edge so their pads keep the 0.3 mm copper-edge
# clearance (the Molex 73251-1153's pads end 4.26 mm from its origin), and the
# four M3 holes in the corners.
EDGE_MEAS = {'J1': (95.39, 14.6, 180), 'J2': (95.39, 59.4, 180), 'J3': (4.61, 14.6, 0),
             'H1': (4.0, 4.0, 0), 'H2': (96.0, 4.0, 0), 'H3': (4.0, 70.0, 0), 'H4': (96.0, 70.0, 0)}
NETCLASS_MEAS = {
    'RF':     (0.50, ['FWD_RF', 'REF_RF']),
    'Supply': (0.40, ['+5V', '+3V3', '+3V3A', '+3V3D']),
    # the cal-load tap: 2.5 mm to everything (IPC-2221 B2, 301-500 V peak)
    'HV':     (0.50, ['CAL_TAP'], 2.5),
}

# control: fits the cassette's 5.5 x 3.6 in envelope (enclosure.py BOARD), standing upright
CFG = {'control':     dict(W=139.0, H=91.0, edge_m=2.5, plane_m=2.5, columns=COLUMNS_CONTROL, rot=ROT_CONTROL,
                           pinned=PINNED_CONTROL, keepout=KEEPOUT_CONTROL, fixed={}, netclass=NETCLASS_CONTROL),
       'measurement': dict(W=100.0, H=74.0, edge_m=1.0, plane_m=0.5, columns=COLUMNS_MEAS, rot=ROT_MEAS,
                           pinned=PINNED_MEAS, keepout=KEEPOUT_MEAS, fixed=EDGE_MEAS, netclass=NETCLASS_MEAS)}[BOARD]
W, H = CFG['W'], CFG['H']                         # board outline, mm
COLUMNS, ROT, PINNED, KEEPOUT, FIXED, NETCLASS = (CFG[k] for k in
                                                   ('columns', 'rot', 'pinned', 'keepout', 'fixed', 'netclass'))

def load_netlist(path):
    root = sexpr.parse(io.open(path).read())[0]
    comps = {}
    for c in sexpr.find(sexpr.find1(root, 'components'), 'comp'):
        ref = sexpr.sval(sexpr.find1(c, 'ref')[1])
        fpn = sexpr.find1(c, 'footprint')
        val = sexpr.find1(c, 'value')
        comps[ref] = dict(fp=sexpr.sval(fpn[1]) if fpn else '',
                          val=sexpr.sval(val[1]) if val else '')
    nets = {}
    for n in sexpr.find(sexpr.find1(root, 'nets'), 'net'):
        nm = sexpr.sval(sexpr.find1(n, 'name')[1]).lstrip('/')
        for node in sexpr.find(n, 'node'):
            r = sexpr.sval(sexpr.find1(node, 'ref')[1])
            p = sexpr.sval(sexpr.find1(node, 'pin')[1])
            nets.setdefault(nm, []).append((r, p))
    return comps, nets

def write_netclasses():
    """Net classes live in the project file, not the board: route.sh's DSN export
    and kicad-cli DRC both load them from <board>.kicad_pro, so write them there."""
    pro = f'{BOARD}.kicad_pro'
    p = json.load(open(pro))
    ns = p.setdefault('net_settings', {})
    base = next(c for c in ns['classes'] if c['name'] == 'Default')
    # Route at 0.2 mm: freerouting necks down to 75 % between pads, which lands at
    # 0.15 mm (6 mil), inside every fab's minimum (OSH Park 4-layer is 5 mil). One
    # clearance for every class, because freerouting does not apply the larger of
    # two classes' clearances and KiCad's DRC does (24 V needs only 0.1 mm, IPC-2221
    # B2). One via size everywhere (0.6 / 0.3 carries the ~1 A of the 24 V input),
    # so imported vias never mix padstacks.
    # A class may add its own larger clearance (the cal-load tap's 2.5 mm); KiCad's
    # DRC and zone fill apply the larger of the two classes' clearances.
    base.update(track_width=0.2, clearance=0.15, via_diameter=0.6, via_drill=0.3)
    ns['classes'] = [base] + [dict(base, name=cname, track_width=v[0], priority=i,
                                   **({'clearance': v[2]} if len(v) > 2 else {}))
                              for i, (cname, v) in enumerate(NETCLASS.items())]
    p['board']['design_settings']['rules']['min_track_width'] = 0.15
    ns['netclass_patterns'] = [{'netclass': cname, 'pattern': m}
                               for cname, v in NETCLASS.items() for m in v[1]]
    json.dump(p, open(pro, 'w'), indent=2)
    print(f'  net classes written to {pro}: ' +
          ', '.join(f'{c} {v[0]} mm ({len(v[1])} nets)' for c, v in NETCLASS.items()))

def gnd_fanout(b, gnd, edge_m):
    """4-layer board: every SMD ground pad gets its own locked via to the In1
    plane before routing. The router treats GND as a plane net and otherwise
    leaves these pads to the outer pours, which island; a via at each pad is also
    the right way to ground a decoupling capacitor. Candidate spots step outward
    from the pad, away from its footprint's center, until one clears every other
    pad and every via placed so far."""
    VIA_R, CLR, TW = 0.3, 0.2, 0.3                 # mm: via radius, clearance, stub width
    pads = list(b.GetPads())
    boxes = [(p, [pcbnew.ToMM(v) for v in (p.GetBoundingBox().GetLeft(), p.GetBoundingBox().GetTop(),
                                           p.GetBoundingBox().GetRight(), p.GetBoundingBox().GetBottom())])
             for p in pads]
    vias = []
    def dist_box(x, y, bb):
        dx = max(bb[0] - x, 0, x - bb[2]); dy = max(bb[1] - y, 0, y - bb[3])
        return (dx * dx + dy * dy) ** 0.5
    def clear(x, y, src, r):
        if not (edge_m + r < x < W - edge_m - r and edge_m + r < y < H - edge_m - r):
            return False
        if any(p is not src and dist_box(x, y, bb) < r + CLR for p, bb in boxes):
            return False
        return all(((x - vx) ** 2 + (y - vy) ** 2) ** 0.5 >= 2 * VIA_R + CLR for vx, vy in vias)
    placed_n, failed, bridged = 0, [], []
    for pad in pads:
        if pad.GetNetname() != 'GND' or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        fp = pad.GetParentFootprint()
        px, py = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
        cx, cy = pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)
        bb = next(bx for p, bx in boxes if p is pad)
        hw, hh = (bb[2] - bb[0]) / 2, (bb[3] - bb[1]) / 2
        import math
        base_a = math.atan2(py - cy, px - cx) if (px, py) != (cx, cy) else math.pi / 2
        spot = None
        for da in (0, 45, -45, 90, -90, 135, -135, 180):
            a = base_a + math.radians(da); ux, uy = math.cos(a), math.sin(a)
            d0 = abs(ux) * hw + abs(uy) * hh + CLR + VIA_R
            for extra in (0.0, 0.3, 0.6, 1.0, 1.5):
                x, y = px + ux * (d0 + extra), py + uy * (d0 + extra)
                # the stub from the pad edge to the via must clear other pads too
                steps = [(px + ux * s, py + uy * s) for s in
                         [abs(ux) * hw + abs(uy) * hh + k * 0.1 for k in range(int((d0 + extra) / 0.1))]]
                if clear(x, y, pad, VIA_R) and all(clear(sx, sy, pad, TW / 2) for sx, sy in steps):
                    spot = (x, y); break
            if spot: break
        if not spot:
            # tied-off gate inputs sit next to another ground pin that already
            # has its via: bridge to that pad instead
            mate = min((q for q in fp.Pads() if q is not pad and q.GetNetname() == 'GND'),
                       key=lambda q: (q.GetPosition() - pad.GetPosition()).EuclideanNorm(), default=None)
            if mate is not None and pcbnew.ToMM((mate.GetPosition() - pad.GetPosition()).EuclideanNorm()) < 2.6:
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pad.GetPosition()); t.SetEnd(mate.GetPosition())
                t.SetWidth(MM(TW)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); t.SetLocked(True)
                b.Add(t); bridged.append(f"{fp.GetReference()}.{pad.GetNumber()}")
            else:
                failed.append(f"{fp.GetReference()}.{pad.GetNumber()}")
            continue
        vias.append(spot)
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(MM(spot[0]), MM(spot[1])))
        v.SetWidth(MM(2 * VIA_R)); v.SetDrill(MM(0.3)); v.SetNet(gnd); v.SetLocked(True)
        b.Add(v)
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pad.GetPosition()); t.SetEnd(v.GetPosition())
        t.SetWidth(MM(TW)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); t.SetLocked(True)
        b.Add(t)
        placed_n += 1
    print(f'  GND fanout: {placed_n} vias placed' + (f', {len(bridged)} pads bridged to a neighbour' if bridged else '')
          + (f'; NO ROOM at {failed}' if failed else ''))

def courtyard(fp):
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    if bb.GetWidth() == 0:
        bb = fp.GetBoundingBox(False, False)
    return bb

def pack_blocks(placed, gap=0.7):            # > the relaxation's 0.6 mm GAP
    """Skyline-pack each column: blocks in the listed order, each block's parts
    tallest first, every part at the highest free spot (then leftmost), by real
    courtyards. A block therefore stays together, and small parts fill the space
    beside tall connectors. Anything that does not fit is reported and parked
    off-board, so the run fails loudly instead of routing an overlapping board."""
    blocks = json.load(open(f'{BOARD}.blocks.json'))
    by = {}
    for ref in placed:
        if ref not in FIXED:
            by.setdefault(blocks.get(ref, 'misc'), []).append(ref)
    def size(r):
        bb = courtyard(placed[r])
        return pcbnew.ToMM(bb.GetWidth()) + gap, pcbnew.ToMM(bb.GetHeight()) + gap
    def put(r, x, y):                         # courtyard top-left to (x, y) mm
        fp = placed[r]; bb = courtyard(fp); pos = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(MM(x) + pos.x - bb.GetLeft(), MM(y) + pos.y - bb.GetTop()))
    overflow, done = [], set()
    for ci, ((x0, y0, x1, y1), names) in enumerate(COLUMNS):
        sky = [(x0, x1, y0)]                  # (x start, x end, first free y) segments
        floor = []                            # (x start, x end, last usable y) under pinned parts
        for r, (col, edge, xl) in PINNED.items():
            if col != ci or r not in placed:
                continue
            w, h = size(r)
            xl = x1 - w if xl is None else xl
            if edge == 'top':
                put(r, xl, y0)
                sky = sorted([s_ for s_ in [(x0, xl, y0), (xl + w, x1, y0)] if s_[1] > s_[0]] + [(max(xl, x0), min(xl + w, x1), y0 + h)])
            else:
                put(r, xl, y1 - h + gap)
                floor.append((xl, xl + w, y1 - h))
        for col, kx0, kx1 in KEEPOUT:
            if col == ci:
                floor.append((kx0, kx1, y0))     # nothing may end below the top: blocked
        def limit(xs, w):
            return min([y1] + [y for a, b_, y in floor if a < xs + w - 1e-6 and b_ > xs + 1e-6])
        for name in names:
            done.add(name)
            for r in sorted(by.get(name, []), key=lambda r: (-size(r)[1], -size(r)[0], r)):
                if r in PINNED:
                    continue
                w, h = size(r)
                best = None
                # try every skyline step, and the edges of pinned parts and keep-outs,
                # so a sliver of overlap with one of them cannot block a whole row
                starts = sorted({s_[0] for s_ in sky} | {b_ for a, b_, y in floor if x0 <= b_ < x1})
                for xs in starts:
                    if xs + w > x1 + 1e-6:
                        continue
                    top = max(y for a, b_, y in sky if a < xs + w - 1e-6 and b_ > xs + 1e-6)
                    if top + h <= limit(xs, w) + 1e-6 and (best is None or (top, xs) < best):
                        best = (top, xs)
                if best is None:
                    overflow.append(r); continue
                top, xs = best
                fp = placed[r]; bb = courtyard(fp); pos = fp.GetPosition()
                fp.SetPosition(pcbnew.VECTOR2I(MM(xs) + pos.x - bb.GetLeft(), MM(top) + pos.y - bb.GetTop()))
                new = []
                for a, b_, y in sky:              # raise the skyline under the part
                    if b_ <= xs or a >= xs + w:
                        new.append((a, b_, y)); continue
                    if a < xs: new.append((a, xs, y))
                    if b_ > xs + w: new.append((xs + w, b_, y))
                new.append((xs, xs + w, top + h))
                sky = sorted(new)
    overflow += [r for n, refs in by.items() if n not in done for r in refs]
    if overflow:
        print(f'  OVERFLOW, {len(overflow)} parts did not fit their regions: {sorted(overflow)}')
        for i, r in enumerate(sorted(overflow)):
            placed[r].SetPosition(pcbnew.VECTOR2I(MM(W + 10 + 6 * (i % 10)), MM(10 + 6 * (i // 10))))
    else:
        print(f'  block packing: all {len(placed)} parts inside their regions')

def main():
    comps, nets = load_netlist(NET)
    b = pcbnew.BOARD()

    pcbnew.FOOTPRINT  # keep import used
    # nets first so pads can reference them
    netmap = {}
    for nm in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(b, nm)
        b.Add(ni); netmap[nm] = ni

    placed, skipped = {}, []
    for ref, c in sorted(comps.items()):
        if not c['fp']:
            skipped.append(ref); continue
        lib, name = c['fp'].split(':', 1)
        local = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{lib}.pretty')
        libpath = local if os.path.isdir(local) else f'/usr/share/kicad/footprints/{lib}.pretty'
        fp = pcbnew.FootprintLoad(libpath, name)
        if fp is None:
            skipped.append(ref + ' (load failed)'); continue
        fp.SetReference(ref); fp.SetValue(c['val'])
        if ref in FIXED:
            x, y, rot = FIXED[ref]
            fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        else:
            fp.SetOrientationDegrees(ROT.get(ref, 0))
        b.Add(fp); placed[ref] = fp

    pack_blocks(placed)

    # assign nets to pads: every pad with the number, not just the first, because
    # footprints repeat numbers (a SOT-223's tab, an SMA's ground legs, a mounting
    # hole's via ring). A repeat left on no net is never a DRC error, so this fails
    # silently: the tab or the leg is simply not connected.
    assigned = 0
    for nm, nodes in nets.items():
        for ref, pin in nodes:
            fp = placed.get(ref)
            if not fp: continue
            for pad in fp.Pads():
                if pad.GetNumber() == pin:
                    pad.SetNet(netmap[nm]); assigned += 1

    # --- courtyard separation --------------------------------------------
    # Footprint origins are not consistently at the centre (axial parts put it at
    # pad 1), so nominal coordinates alone do not guarantee clearance. Measure the
    # real courtyards and relax overlaps apart iteratively.
    def boxes():
        out = {}
        for ref, fp in placed.items():
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            if bb.GetWidth() == 0:
                bb = fp.GetBoundingBox(False, False)
            out[ref] = [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                        pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())]
        return out

    GAP = 0.6
    for it in range(400):
        bx = boxes(); moved = 0
        refs = sorted(bx)
        for i, a in enumerate(refs):
            for bref in refs[i+1:]:
                ax1, ay1, ax2, ay2 = bx[a]; bx1, by1, bx2, by2 = bx[bref]
                ox = min(ax2, bx2) - max(ax1, bx1) + GAP
                oy = min(ay2, by2) - max(ay1, by1) + GAP
                if ox <= 0 or oy <= 0:
                    continue
                acx, acy = (ax1+ax2)/2, (ay1+ay2)/2
                bcx, bcy = (bx1+bx2)/2, (by1+by2)/2
                if ox < oy:
                    d = ox/2 * (1 if acx <= bcx else -1)
                    shift = ((-d, 0), (d, 0))
                else:
                    d = oy/2 * (1 if acy <= bcy else -1)
                    shift = ((0, -d), (0, d))
                if a in FIXED or bref in FIXED:
                    shift = ((0, 0), (2 * shift[1][0], 2 * shift[1][1])) if a in FIXED else \
                            ((2 * shift[0][0], 2 * shift[0][1]), (0, 0))
                for ref, (dx, dy) in zip((a, bref), shift):
                    if ref in FIXED:
                        continue
                    pos = placed[ref].GetPosition()
                    nx = min(max(pcbnew.ToMM(pos.x) + dx, 6.0), W - 6.0)
                    ny = min(max(pcbnew.ToMM(pos.y) + dy, 6.0), H - 6.0)
                    placed[ref].SetPosition(pcbnew.VECTOR2I(MM(nx), MM(ny)))
                moved += 1
        if not moved:
            print(f'  courtyards separated after {it} relaxation passes')
            break
    else:
        print(f'  WARNING: still {moved} overlaps after 400 passes')

    # board outline on Edge.Cuts
    # Outline is drawn INSET by EDGE_M. route.sh restores the true outline after
    # the SES import; this is what keeps the router off the board edge.
    EDGE_M = CFG['edge_m']
    corners = ((EDGE_M, EDGE_M), (W-EDGE_M, EDGE_M), (W-EDGE_M, H-EDGE_M), (EDGE_M, H-EDGE_M))
    for (x1, y1), (x2, y2) in zip(corners, corners[1:] + corners[:1]):
        seg = pcbnew.PCB_SHAPE(b)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.15))
        b.Add(seg)

    # Both boards are 4-layer: on two layers the control board's pour broke into
    # islands at 51 % courtyard fill, and the measurement board's detectors need an
    # unbroken reference under every RF trace. In1 is a solid GND plane (a "power"
    # layer); it is the only pour the router sees, so every SMD ground pad gets its
    # own via down to it. route.sh pours F, In2 and B after the SES import.
    b.SetCopperLayerCount(4)
    b.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    pm = CFG['plane_m']
    z = pcbnew.ZONE(b)
    z.SetLayer(pcbnew.In1_Cu)
    z.SetNet(netmap['GND'])
    z.SetLocalClearance(MM(0.3))
    o = z.Outline(); o.NewOutline()
    for px, py in ((pm, pm), (W - pm, pm), (W - pm, H - pm), (pm, H - pm)):
        o.Append(MM(px), MM(py))
    b.Add(z)
    # design rules: 0.15 mm / 6 mil is inside standard fab capability and these
    # are all low-current signal nets. Set before export so the router honours it.
    ds = b.GetDesignSettings()
    ds.m_TrackMinWidth = MM(0.15)
    ds.m_CopperEdgeClearance = MM(0.3)
    # GetAllNetClasses() hands back copies in this binding, so setting the width
    # there does not persist. m_NetSettings holds the live object.
    nset = ds.m_NetSettings
    dflt = nset.GetDefaultNetclass() if hasattr(nset, 'GetDefaultNetclass') else None
    if dflt is not None:
        dflt.SetTrackWidth(MM(0.15))   # DRC treats netclass width as a hard minimum
        dflt.SetClearance(MM(0.2))
    else:
        nc = b.GetAllNetClasses()
        if 'Default' in nc:
            nc['Default'].SetTrackWidth(MM(0.15)); nc['Default'].SetClearance(MM(0.2))
    ds.m_MinResolvedSpokes = 1            # GND pour: one thermal spoke suffices
    for z in b.Zones():
        z.SetMinThickness(MM(0.2))
    gnd_fanout(b, netmap['GND'], EDGE_M)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

    pcbnew.SaveBoard(OUT, b)
    write_netclasses()
    print(f'placed {len(placed)} footprints, {assigned} pad-net assignments')
    print(f'skipped (no footprint): {skipped}')
    print(f'nets: {len(netmap)}  board: {W} x {H} mm  zones: {b.GetAreaCount()}')

main()
