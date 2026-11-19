#!/bin/bash
set -e
B=${1:-measurement}
J=/usr/lib/jvm/java-25-temurin/bin/java
FR="$J -Djava.awt.headless=true -jar /usr/lib/freerouting/freerouting-executable.jar"
python3 board_${B}.py
kicad-cli sch erc --output erc_${B}.rpt ${B}.kicad_sch >/dev/null 2>&1 || true
kicad-cli sch export netlist --output ${B}.net ${B}.kicad_sch >/dev/null 2>&1
# the netlist records the schematic's absolute path; keep home paths out of the repo
sed -i "s|(source \"[^\"]*/${B}.kicad_sch\")|(source \"${B}.kicad_sch\")|" ${B}.net
python3 make_pcb.py "$B"
B=$B python3 -c "
import os
import pcbnew; b=pcbnew.LoadBoard('${B}.kicad_pcb'); print('DSN:', pcbnew.ExportSpecctraDSN(b,'${B}.dsn'))"
$FR -de ${B}.dsn -do ${B}.ses -mp 40 -mt 6 2>&1 | grep -E 'Auto-routing stage completed|Optimization was completed'
python3 -u post_route.py "$B"
# The odd wide net can be left unfinished. Route again from the result, up to
# twice more, while DRC still finds unconnected items.
for pass in 2 3; do
  kicad-cli pcb drc --output drc.rpt --format report ${B}.kicad_pcb >/dev/null 2>&1 || true
  n=$(grep -oE 'Found [0-9]+ unconnected' drc.rpt | grep -oE '[0-9]+' || true)
  [ "${n:-0}" -eq 0 ] && break
  echo "pass $pass: $n unconnected, routing again"
  python3 -u reroute_prep.py "$B"
  $FR -de ${B}.dsn -do ${B}.ses -mp 30 -mt 6 2>&1 | grep -E 'Auto-routing stage completed|Optimization was completed'
  python3 -u post_route.py "$B"
done
kicad-cli pcb drc --output drc.rpt --format report ${B}.kicad_pcb 2>&1 | tail -2
