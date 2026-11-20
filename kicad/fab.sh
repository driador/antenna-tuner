#!/bin/bash
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

# Fabrication outputs for a routed board: Gerbers (copper, mask, paste, silk,
# outline), Excellon drill files, and one zip ready for a fab's upload form.
# Usage: ./fab.sh control   ->  fab/control/ and fab/control-fab.zip
set -e
B=${1:-control}
OUT=fab/$B
rm -rf "$OUT" && mkdir -p "$OUT"
n=$(python3 -c "import pcbnew; print(pcbnew.LoadBoard('${B}.kicad_pcb').GetCopperLayerCount())")
CU="F.Cu,B.Cu"
[ "$n" -eq 4 ] && CU="F.Cu,In1.Cu,In2.Cu,B.Cu"
kicad-cli pcb export gerbers --output "$OUT/" \
  --layers "$CU,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts" \
  --subtract-soldermask "${B}.kicad_pcb" >/dev/null
kicad-cli pcb export drill --output "$OUT/" --format excellon --excellon-units mm \
  --generate-map --map-format gerberx2 "${B}.kicad_pcb" >/dev/null
rm -f "fab/${B}-fab.zip"
(cd "$OUT" && zip -q "../${B}-fab.zip" ./*)
echo "$n-layer $B: $(ls "$OUT" | wc -l) files -> fab/${B}-fab.zip"
