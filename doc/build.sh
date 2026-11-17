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

pandoc "$SRC" -f gfm -t html5 --standalone --toc --toc-depth=3 \
  --math-method=mathml --metadata title="1500W Automated Antenna Tuner" \
  --css print.css -o doc.html

python3 titlepage.py doc.html "$SRC"
python3 inject_diagrams.py doc.html diagrams
weasyprint doc.html "$OUT" 2>&1 | grep -v 'user-select' || true
echo "built $OUT  ($(pdfinfo "$OUT" | awk '/^Pages/{print $2}') pages)"
