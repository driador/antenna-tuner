#!/usr/bin/env python3
"""Build the measurement board PCB from the verified netlist.

Placement follows signal flow: RF in (left) -> splitter -> detector -> AD8302
(centre) -> control/logic (right) -> connectors (far right). Forward channel on
the top half, reflected channel on the bottom half, mirrored.
"""
import pcbnew, sexpr, io, os, sys

import sys, json
BOARD = sys.argv[1] if len(sys.argv) > 1 else 'measurement'
NET = f'{BOARD}.net'
OUT  = f'{BOARD}.kicad_pcb'
# control: fits the cassette's 5.5 x 3.6 in envelope (enclosure.py BOARD), standing upright
W, H = (215.0, 145.0) if BOARD == 'measurement' else (139.0, 91.0)          # board outline, mm
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
# wider tracks where current flows; everything else keeps the 0.15 mm default
NETCLASS_CONTROL = {
    'Power':  (0.60, ['+24V_IN', '+24V', '+24V_5', '+24V_12', '+12V', 'BLOWER_LO',
                      'K1_PLUS', 'K2_PLUS', 'K1_LO', 'K2_LO', 'K1_SNS', 'K2_SNS', 'HFBR_A', 'HFBR_K']),
    'Supply': (0.40, ['+5V', '+3V3']),
}

PLACE = {
 # --- forward channel (top) ---
 'J1': (14, 22),  'R1': (32, 22),  'R2': (46, 13),  'R3': (46, 31),
 'J2': (60, 31),  'D1': (60, 13),  'R7': (72, 13),  'C1': (84, 13),
 'J3': (100, 22),
 # --- reflected channel (bottom) ---
 'J4': (14, 78),  'R4': (32, 78),  'R5': (46, 69),  'R6': (46, 87),
 'J5': (60, 87),  'D2': (60, 69),  'R8': (72, 69),  'C2': (84, 69),
 'J6': (100, 78),
 # --- AD8302 and its network (centre) ---
 'U1': (120, 50),
 'C3': (106, 60), 'C4': (113, 60), 'C5': (127, 60), 'C6': (134, 60),
 'C7': (113, 38), 'C8': (127, 38),
 # --- frequency counter front end ---
 'R9': (84, 26),  'D3': (92, 21),  'D4': (92, 31),
 'U2': (104, 34), 'R10': (104, 26),
 'R11': (84, 33), 'R12': (84, 40),
 # --- protection comparator + permissive ---
 'U3': (120, 72), 'R13': (104, 70), 'R14': (104, 77),
 'R15': (136, 70), 'R16': (136, 77),
 # --- power and connectors ---
 'FB1': (120, 88), 'C9': (136, 88), 'C10': (144, 88),
 'J7': (163, 88),  'J8': (163, 22),  'J9': (158, 48),
}

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
    base.update(track_width=0.2, clearance=0.15, via_diameter=0.6, via_drill=0.3)
    ns['classes'] = [base] + [dict(base, name=cname, track_width=width, priority=i)
                              for i, (cname, (width, _)) in enumerate(NETCLASS_CONTROL.items())]
    p['board']['design_settings']['rules']['min_track_width'] = 0.15
    ns['netclass_patterns'] = [{'netclass': cname, 'pattern': m}
                               for cname, (_, members) in NETCLASS_CONTROL.items() for m in members]
    json.dump(p, open(pro, 'w'), indent=2)
    print(f'  net classes written to {pro}: ' +
          ', '.join(f'{c} {w} mm ({len(m)} nets)' for c, (w, m) in NETCLASS_CONTROL.items()))

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
        by.setdefault(blocks.get(ref, 'misc'), []).append(ref)
    def size(r):
        bb = courtyard(placed[r])
        return pcbnew.ToMM(bb.GetWidth()) + gap, pcbnew.ToMM(bb.GetHeight()) + gap
    def put(r, x, y):                         # courtyard top-left to (x, y) mm
        fp = placed[r]; bb = courtyard(fp); pos = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(MM(x) + pos.x - bb.GetLeft(), MM(y) + pos.y - bb.GetTop()))
    overflow, done = [], set()
    for ci, ((x0, y0, x1, y1), names) in enumerate(COLUMNS_CONTROL):
        sky = [(x0, x1, y0)]                  # (x start, x end, first free y) segments
        floor = []                            # (x start, x end, last usable y) under pinned parts
        for r, (col, edge, xl) in PINNED_CONTROL.items():
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
        for col, kx0, kx1 in KEEPOUT_CONTROL:
            if col == ci:
                floor.append((kx0, kx1, y0))     # nothing may end below the top: blocked
        def limit(xs, w):
            return min([y1] + [y for a, b_, y in floor if a < xs + w - 1e-6 and b_ > xs + 1e-6])
        for name in names:
            done.add(name)
            for r in sorted(by.get(name, []), key=lambda r: (-size(r)[1], -size(r)[0], r)):
                if r in PINNED_CONTROL:
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
        if BOARD == 'measurement':
            x, y = PLACE.get(ref, (W - 14, H - 14))
            fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        else:
            fp.SetOrientationDegrees(ROT_CONTROL.get(ref, 0))
        b.Add(fp); placed[ref] = fp

    if BOARD != 'measurement':
        pack_blocks(placed)

    # assign nets to pads
    assigned = 0
    for nm, nodes in nets.items():
        for ref, pin in nodes:
            fp = placed.get(ref)
            if not fp: continue
            pad = fp.FindPadByNumber(pin)
            if pad:
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
                for ref, (dx, dy) in zip((a, bref), shift):
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
    EDGE_M = 2.5
    corners = ((EDGE_M, EDGE_M), (W-EDGE_M, EDGE_M), (W-EDGE_M, H-EDGE_M), (EDGE_M, H-EDGE_M))
    for (x1, y1), (x2, y2) in zip(corners, corners[1:] + corners[:1]):
        seg = pcbnew.PCB_SHAPE(b)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.15))
        b.Add(seg)

    # ground pour on both layers -- RF detectors need a solid reference. The control
    # board is 4-layer: at 51 % courtyard fill two layers chopped the pour into
    # islands. In1 is a solid GND plane (a "power" layer); it is the only pour the
    # router sees, so every SMD ground pad gets its own via down to it. route.sh
    # pours F, In2 and B after the SES import.
    copper = (pcbnew.B_Cu, pcbnew.F_Cu)
    if BOARD != 'measurement':
        b.SetCopperLayerCount(4)
        b.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
        copper = (pcbnew.In1_Cu,)
    for layer in copper:
        z = pcbnew.ZONE(b)
        z.SetLayer(layer)
        z.SetNet(netmap['GND'])
        z.SetLocalClearance(MM(0.3))
        o = z.Outline(); o.NewOutline()
        for px, py in ((2.5,2.5),(W-2.5,2.5),(W-2.5,H-2.5),(2.5,H-2.5)):
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
    if b.GetCopperLayerCount() == 4:
        gnd_fanout(b, netmap['GND'], EDGE_M)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

    pcbnew.SaveBoard(OUT, b)
    if BOARD != 'measurement':
        write_netclasses()
    print(f'placed {len(placed)} footprints, {assigned} pad-net assignments')
    print(f'skipped (no footprint): {skipped}')
    print(f'nets: {len(netmap)}  board: {W} x {H} mm  zones: {b.GetAreaCount()}')

main()
