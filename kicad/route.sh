#!/bin/bash
set -e
B=${1:-measurement}
J=/usr/lib/jvm/java-25-temurin/bin/java
python3 board_${B}.py
kicad-cli sch erc --output erc_${B}.rpt ${B}.kicad_sch >/dev/null 2>&1 || true
kicad-cli sch export netlist --output ${B}.net ${B}.kicad_sch >/dev/null 2>&1
python3 make_pcb.py "$B"
B=$B python3 -c "
import os
import pcbnew; b=pcbnew.LoadBoard('${B}.kicad_pcb'); print('DSN:', pcbnew.ExportSpecctraDSN(b,'${B}.dsn'))"
$J -Djava.awt.headless=true -jar /usr/lib/freerouting/freerouting-executable.jar -de ${B}.dsn -do ${B}.ses -mp 40 -mt 6 2>&1 | grep -E 'Auto-routing stage completed|Optimization was completed'
B=$B python3 -c "
import os

import pcbnew
b=pcbnew.LoadBoard('${B}.kicad_pcb')
print('SES:', pcbnew.ImportSpecctraSES(b,'${B}.ses'))
# freerouting writes widths against a resolution KiCad reads differently, so
# tracks come back ~0.112 mm. Normalise to 0.15 mm (6 mil, standard fab) and
# let DRC prove the clearance still holds.
import collections
before=collections.Counter(round(pcbnew.ToMM(t.GetWidth()),4) for t in b.GetTracks() if t.Type()==pcbnew.PCB_TRACE_T)
W=b.GetDesignSettings().m_NetSettings.GetDefaultNetclass().GetTrackWidth()
for t in b.GetTracks():
    if t.Type()==pcbnew.PCB_TRACE_T and t.GetWidth() < W:
        t.SetWidth(W)
print('widths before normalise:', dict(before))
ds=b.GetDesignSettings(); ds.m_MinResolvedSpokes=1   # GND pour: 1 spoke is fine
# restore the true outline: make_pcb drew it inset so the router stayed clear
import re as _re
EDGE_M=2.5
for d in b.GetDrawings():
    if d.GetLayer()==pcbnew.Edge_Cuts and d.GetShape()==pcbnew.SHAPE_T_SEGMENT:
        for get,set_ in ((d.GetStart,d.SetStart),(d.GetEnd,d.SetEnd)):
            p_=get(); x,y=pcbnew.ToMM(p_.x),pcbnew.ToMM(p_.y)
            x = x-EDGE_M if abs(x-EDGE_M)<0.01 else x+EDGE_M
            y = y-EDGE_M if abs(y-EDGE_M)<0.01 else y+EDGE_M
            set_(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard('${B}.kicad_pcb', b)
tr=[t for t in b.GetTracks() if t.Type()==pcbnew.PCB_TRACE_T]
vi=[t for t in b.GetTracks() if t.Type()==pcbnew.PCB_VIA_T]
print(f'tracks {len(tr)}  vias {len(vi)}  copper {sum(pcbnew.ToMM(t.GetLength()) for t in tr):.0f} mm')
"
kicad-cli pcb drc --output drc.rpt --format report ${B}.kicad_pcb 2>&1 | tail -2
