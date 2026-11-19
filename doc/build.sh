#!/bin/bash
# Build the design log into a presentable PDF.
#   pandoc (gfm -> html5) -> post-process -> WeasyPrint -> PDF
# LaTeX was rejected: the document has ~370 table rows and several wide tables
# that overflow \textwidth; CSS table layout handles them without manual tuning.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
SRC=$(realpath "${1:-$HERE/design-log.md}")
OUT=${2:-tuner-design-log.pdf}
cd "$HERE"

# Appendices A/B: vector SVGs of the latest drawing sheets (../cad/out, from drawings*.py)
mkdir -p sheets
for f in ../cad/out/L-*.pdf ../cad/out/E-*.pdf; do
  if [ -e "$f" ]; then pdftocairo -svg "$f" "sheets/$(basename "${f%.pdf}").svg"; fi
done

# Appendix C: the boards, rendered straight from the routed KiCad files. The 3D
# views are the bare board (no component models installed): mask, silkscreen,
# pads and vias, which is what assembly reads. Plus the silkscreen as the fab
# prints it (with the pad openings, vector) and each copper layer.
for b in control measurement; do
  pcb=../kicad/$b.kicad_pcb
  [ -e "$pcb" ] || continue
  for side in top bottom; do
    kicad-cli pcb render --side $side --quality high --zoom 1.45 --width 2400 --height 1600 \
      --background transparent --use-board-stackup-colors -o "sheets/pcb-$b-$side.png" "$pcb" >/dev/null 2>&1
  done
  kicad-cli pcb export svg --layers F.Silkscreen,F.Mask,Edge.Cuts \
    --black-and-white --mode-single --fit-page-to-board --exclude-drawing-sheet \
    -o "sheets/pcb-$b-silk.svg" "$pcb" >/dev/null 2>&1
  layers="F.Cu B.Cu"; grep -q '"In1.Cu"' "$pcb" && layers="F.Cu In1.Cu In2.Cu B.Cu"
  for L in $layers; do
    kicad-cli pcb export svg --layers "$L,Edge.Cuts" --mode-single --fit-page-to-board \
      --exclude-drawing-sheet -o "sheets/pcb-$b-${L%.Cu}.svg" "$pcb" >/dev/null 2>&1
  done
done

pandoc "$SRC" -f gfm -t html5 --standalone --toc --toc-depth=3 \
  --math-method=mathml --metadata title="1500W Automated Antenna Tuner" \
  --css print.css -o doc.html

python3 titlepage.py doc.html "$SRC"
python3 inject_diagrams.py doc.html diagrams
weasyprint doc.html "$OUT" 2>&1 | grep -v 'user-select' || true
echo "built $OUT  ($(pdfinfo "$OUT" | awk '/^Pages/{print $2}') pages)"
