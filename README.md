# 1500 W Automated Antenna Tuner

KF0OWR's homebuilt 1500 W remote balanced tuner for a doublet on 160–10 m. It uses a 34 µH
roller inductor, two vacuum capacitors and Tohtsu relays, and sits in a wall-mounted
16 × 16 × 24″ cabinet. The design log is the source of truth. Everything else in this repo
(CAD, drawings, NEC models, KiCad boards) supports it, and the log cites these files by their
repo paths.

## Layout

| Path | Contents |
|---|---|
| `doc/design-log.md` | **Design log** (current revision in its header). §9 is the open-item list; §11 holds superseded designs |
| `doc/design-review-rev3.2.md` | Independent design review of Rev 3.2 and its dispositions |
| `doc/vacuum-cap-testing.md` | Bench procedure for the used vacuum capacitors |
| `doc/diagrams/` | Graphviz sources (`*.dot`) and the rendered SVGs the log embeds |
| `doc/*.pdf` | Built log and review PDFs, plus a reference worksheet |
| `cad/` | build123d models (roller, enclosure, harness) and FreeCAD TechDraw sheet generators |
| `cad/out/*.pdf` | Drawing sheets: `L-100…109` roller, `E-200…215` enclosure, populated cabinet and harness |
| `nec/` | nec2++ and Python analyses: capacitor and inductor demand, roller and choke sweeps, tuning time |
| `nec/out/*.csv`, `*.txt` | Analysis summaries the log quotes |
| `nec/data/` | Fair-Rite #61 material data (complex permeability, Pv vs B) |
| `kicad/` | Control and measurement boards, generated from Python (schematic → netlist → PCB → freerouting → DRC, `route.sh`); fab zip from `fab.sh` |
| `archive/` | Early drafts and the Rev 3.3 / 3.4 log snapshots the log cites |

## Toolchain

| Area | Needs |
|---|---|
| Log / review PDF | `pandoc`, `weasyprint`, `poppler` (`pdftocairo`, `pdfinfo`), `python3`; `graphviz` only to re-render a diagram |
| CAD | Python 3.12 venv with `cad/requirements.txt` (build123d 0.13); FreeCAD 1.1 plus `xvfb-run` for the sheets |
| NEC | `nec2++` built statically at `~/src/necpp/build/src/nec2++` (scripts call that path); Python 3 stdlib only |
| KiCad | KiCad 10 (`kicad-cli`, `pcbnew` Python module), Java 25 and freerouting (`kicad/route.sh`) |

Set up the CAD environment:

```bash
uv venv cad/.venv --python 3.12
uv pip install --python cad/.venv/bin/python -r cad/requirements.txt
```

Build `nec2++` (the shared-library build breaks once `libnecpp.so` goes missing, so use the static build):

```bash
git clone https://github.com/tmolteno/necpp ~/src/necpp
cmake -S ~/src/necpp -B ~/src/necpp/build -DBUILD_SHARED_LIBS=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build ~/src/necpp/build -j
```

## Build order

When the geometry changes, regenerate the CAD and sheets **in this order**, then rebuild the log
so appendices A/B pick up the new sheets:

```bash
cd cad
.venv/bin/python roller.py          # roller model + interference check
.venv/bin/python enclosure.py       # cabinet, panels, fixtures + interference check
.venv/bin/python harness.py         # color-coded wire runs + clearance check
.venv/bin/python svgviews.py        # hidden-line SVG views used by the sheets
timeout 900 xvfb-run -a freecad drawings.py             # L-100…109
timeout 900 xvfb-run -a freecad drawings_enclosure.py   # E-200…215
cd ../doc && ./build.sh             # → doc/tuner-design-log.pdf
```

Always wrap the FreeCAD runs in `timeout`. A module-level exception in a sheet script leaves
FreeCAD hanging under xvfb with an empty log. Re-render a diagram with
`dot -Tsvg doc/diagrams/X.dot -o doc/diagrams/X.svg`. The review builds with `doc/build_review.sh`.

## What is tracked

- **Git LFS** (`.gitattributes`) holds every `*.pdf`, `*.png` and `*.jpg`: drawing sheets, built
  PDFs, KiCad plots and references. Run `git lfs install --local` after cloning.
- **Not tracked** (`.gitignore`) are outputs the scripts regenerate wholesale on every run:
  - STEP models and FreeCAD documents
  - sheet SVGs and logs in `cad/out/`
  - raw NEC decks and solver output (`nec/out/*.nec`, `*.out`, about 420 MB)
  - the HTML intermediates and `doc/sheets/`
  - the venv
  - `.*.pre-*` working backups, since git history replaces them
- The summaries that analyses produce (`nec/out/*.csv`, `*.txt`, `nec/cap_demand_rev37b.out`)
  **are** tracked, because the log quotes them.
