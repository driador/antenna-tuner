#!/usr/bin/env python3
"""Prepare a routed board for another freerouting pass.

Called by route.sh as `python3 reroute_prep.py <board>` when DRC still finds
unconnected items. Puts the board back the way the router first saw it: the
pours added after routing are removed (on 4-layer boards only the In1 plane is
a routing plane), and the outline is inset by EDGE_M again. post_route.py
undoes both after the pass.
"""
import sys
import pcbnew

B = sys.argv[1]
MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
EDGE_M = 2.5
b = pcbnew.LoadBoard(f'{B}.kicad_pcb')
if b.GetCopperLayerCount() == 4:
    for z in list(b.Zones()):
        if z.GetLayer() != pcbnew.In1_Cu:
            b.Delete(z)
segs = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT]
xs = [TOMM(p.x) for d in segs for p in (d.GetStart(), d.GetEnd())]
ys = [TOMM(p.y) for d in segs for p in (d.GetStart(), d.GetEnd())]
x0, y0 = min(xs), min(ys)
for d in segs:
    for get, set_ in ((d.GetStart, d.SetStart), (d.GetEnd, d.SetEnd)):
        p_ = get(); x, y = TOMM(p_.x), TOMM(p_.y)
        x = x + EDGE_M if abs(x - x0) < 0.01 else x - EDGE_M
        y = y + EDGE_M if abs(y - y0) < 0.01 else y - EDGE_M
        set_(pcbnew.VECTOR2I(MM(x), MM(y)))
pcbnew.SaveBoard(f'{B}.kicad_pcb', b)
print('DSN:', pcbnew.ExportSpecctraDSN(b, f'{B}.dsn'))
