#!/usr/bin/env python3
"""Build the measurement board PCB from the verified netlist.

Placement follows signal flow: RF in (left) -> splitter -> detector -> AD8302
(centre) -> control/logic (right) -> connectors (far right). Forward channel on
the top half, reflected channel on the bottom half, mirrored.
"""
import pcbnew, sexpr, io, os, sys

import sys
BOARD = sys.argv[1] if len(sys.argv) > 1 else 'measurement'
NET = f'{BOARD}.net'
OUT  = f'{BOARD}.kicad_pcb'
W, H = (215.0, 145.0) if BOARD == 'measurement' else (240.0, 190.0)          # board outline, mm
MM = pcbnew.FromMM

# ref -> (x, y) in mm.  Two mirrored RF channels, logic to the right.
PLACE_CONTROL = {
 'A1': (118, 26),                                     # Teensy, 61 x 18 mm
 'J15':(206, 26), 'R13':(178, 26), 'C5':(178, 44),    # recovery button
 'J1': (26, 60),  'J2': (26, 88),  'U1': (62, 88),    # power in, buck, 3V3
 'C1': (62, 110), 'C2': (84, 110), 'C3': (106, 110), 'C4': (26, 110),
 'J3': (26, 136), 'J4': (26, 158), 'J5': (26, 168),   # stepper drivers
 'J6': (76, 136), 'J7': (76, 162),                    # encoders, limits
 'R1': (116, 140),'R2': (116, 160),'R3': (116, 168),  # limit pull-ups
 'R4': (140, 140),'R5': (140, 160),'R6': (140, 168),
 'Q1': (178, 70), 'D1': (202, 62), 'R7': (152, 62), 'R9': (152, 82),
 'Q2': (178, 100),'D2': (202, 92), 'R8': (152, 102),'R10':(152, 122),
 'Q3': (178, 130),'D3': (202, 122),'R11':(152, 142),'R12':(152, 162),
 'J8': (218, 70), 'J9': (218, 130),                   # relay coils, blower
 'J10':(206, 152),                                    # POF interlock
 'J11':(186, 168),                                    # bulkhead to measurement
 'J12':(96, 60),  'J13':(96, 36),                     # sensors, panel
 '#FLG1': (60, 20), '#FLG2': (60, 168), '#FLG3': (210, 168),
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
        table = PLACE if BOARD == 'measurement' else PLACE_CONTROL
        x, y = table.get(ref, (W - 14, H - 14))

        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        b.Add(fp); placed[ref] = fp

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

    # ground pour on both layers -- RF detectors need a solid reference
    for layer in (pcbnew.B_Cu, pcbnew.F_Cu):
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
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

    pcbnew.SaveBoard(OUT, b)
    print(f'placed {len(placed)} footprints, {assigned} pad-net assignments')
    print(f'skipped (no footprint): {skipped}')
    print(f'nets: {len(netmap)}  board: {W} x {H} mm  zones: {b.GetAreaCount()}')

main()
