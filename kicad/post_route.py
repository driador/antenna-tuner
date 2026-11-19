#!/usr/bin/env python3
"""After freerouting: import the SES, tidy the result, pour, fill, save.

Called by route.sh as `python3 post_route.py <board>`.
"""
import collections, sys
import pcbnew

B = sys.argv[1]
MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(f'{B}.kicad_pcb')
print('SES:', pcbnew.ImportSpecctraSES(b, f'{B}.ses'))

# Freerouting necks tracks down to 75 % of their class width between pads and
# writes those widths exactly; widening them afterwards breaks the clearance it
# kept. Only anything under the board's minimum width is raised to it.
before = collections.Counter(round(TOMM(t.GetWidth()), 4) for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T)
W = b.GetDesignSettings().m_TrackMinWidth
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_TRACE_T and t.GetWidth() < W:
        t.SetWidth(W)
print('widths from freerouting:', dict(before), ' board minimum', TOMM(W))

# freerouting leaves a few vias with copper on one layer only, and the stubs
# that led to them. Strip both until nothing dangles. GND vias are kept: they
# land on the In1 plane, which is a zone, not a track.
def dangling_cleanup():
    removed_v = removed_t = 0
    while True:
        tracks = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
        vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
        pads = list(b.GetPads())
        by_net = collections.defaultdict(lambda: ([], [], []))
        for t in tracks: by_net[t.GetNetCode()][0].append(t)
        for v in vias:   by_net[v.GetNetCode()][1].append(v)
        for p in pads:   by_net[p.GetNetCode()][2].append(p)
        kill = []
        for v in vias:
            if v.GetNetname() == 'GND':
                continue
            tr, _, pd = by_net[v.GetNetCode()]
            layers = {t.GetLayer() for t in tr if v.HitTest(t.GetStart()) or v.HitTest(t.GetEnd())}
            layers |= {l for p in pd if p.HitTest(v.GetPosition()) for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)}
            if len(layers) < 2:
                kill.append(v)
        for t in tracks:
            tr, vi, pd = by_net[t.GetNetCode()]
            for end in (t.GetStart(), t.GetEnd()):
                ok = any(p.IsOnLayer(t.GetLayer()) and p.HitTest(end) for p in pd) \
                     or any(v.HitTest(end) for v in vi if v not in kill) \
                     or any(o is not t and o.GetLayer() == t.GetLayer() and o.HitTest(end) for o in tr)
                if not ok:
                    kill.append(t); break
        if not kill:
            return removed_v, removed_t
        for k in kill:
            if k.Type() == pcbnew.PCB_VIA_T: removed_v += 1
            else: removed_t += 1
            b.Delete(k)          # Delete, not Remove: a removed item left to Python's GC crashes at exit
        del kill, tracks, vias, pads, by_net
print('removed dangling: %d vias, %d track stubs' % dangling_cleanup())

ds = b.GetDesignSettings(); ds.m_MinResolvedSpokes = 1   # GND pour: 1 spoke is fine
# restore the true outline: make_pcb drew it inset so the router stayed clear
EDGE_M = 2.5
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
        for get, set_ in ((d.GetStart, d.SetStart), (d.GetEnd, d.SetEnd)):
            p_ = get(); x, y = TOMM(p_.x), TOMM(p_.y)
            x = x - EDGE_M if abs(x - EDGE_M) < 0.01 else x + EDGE_M
            y = y - EDGE_M if abs(y - EDGE_M) < 0.01 else y + EDGE_M
            set_(pcbnew.VECTOR2I(MM(x), MM(y)))

# 4-layer boards route against the In1 plane only; pour the other layers now.
# New zones are built as make_pcb.py builds them: ZONE.Duplicate() hands back a
# temporary wrapper that owns the copy, and Python frees it under the board.
if b.GetCopperLayerCount() == 4:
    plane = next(z for z in b.Zones() if z.GetLayer() == pcbnew.In1_Cu)
    pts = [plane.Outline().CVertex(i) for i in range(plane.Outline().TotalVertices())]
    for layer in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b)
        z.SetLayer(layer); z.SetNet(plane.GetNet())
        z.SetLocalClearance(plane.GetLocalClearance()); z.SetMinThickness(plane.GetMinThickness())
        o = z.Outline(); o.NewOutline()
        for p_ in pts:
            o.Append(p_.x, p_.y)
        b.Add(z)
# dense boards: 0.8 mm reference text (KiCad's 1.0 mm default overlaps itself
# and the pads at 1206 spacing); still readable for hand assembly
if b.GetCopperLayerCount() == 4:
    for fp in b.GetFootprints():
        ref = fp.Reference()
        ref.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8))); ref.SetTextThickness(MM(0.12))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(f'{B}.kicad_pcb', b)
tr = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
vi = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
print(f'tracks {len(tr)}  vias {len(vi)}  copper {sum(TOMM(t.GetLength()) for t in tr):.0f} mm  '
      f'layers {b.GetCopperLayerCount()}  zones {b.GetAreaCount()}')
