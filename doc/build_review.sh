#!/bin/bash
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
SRC=$(realpath "${1:-$HERE/design-review-rev3.2.md}")
OUT=${2:-tuner-design-review.pdf}
cd "$HERE"
pandoc "$SRC" -f gfm+tex_math_dollars -t html5 --standalone --toc --toc-depth=3 \
  --math-method=plain --metadata title="Design Review" --css review.css -o rev.html
python3 review_post.py rev.html "$SRC"
weasyprint rev.html "$OUT" 2>&1 | grep -v 'user-select' || true
echo "built $OUT  ($(pdfinfo "$OUT" | awk '/^Pages/{print $2}') pages)"
