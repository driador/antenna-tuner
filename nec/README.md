# NEC-2 model — 170 ft doublet

Built from https://github.com/tmolteno/necpp (CMake, Release). Self-tests: 708/708 pass.

- `nec2++`            — OLD binary: needs a libnecpp.so.2 that no longer exists. Use the static build at
                        `~/src/necpp/build/src/nec2++` (rebuilt 2026-11-16, `-DBUILD_SHARED_LIBS=OFF`)
- `cap_demand.py`     — Rev 3.7b network demand (no pad, single roller, 15 kV C1); Rev 3.6 kept as `cap_demand_rev36.py`
- `roller_vna.py`     — NEC wire model of the roller, simulated VNA sweep per wheel position (`--deck` adds a PEC deck)
- `roller_bands.py`   — maps band edges onto the roller sweep (Q, copper loss, idle-turn resonance flags)
- `tune_time.py`      — tuning-time estimate (M-2 A/B, stored profile vs cold tune vs in-band)
- `choke_vna.py`      — NEC model of the Guanella choke's common mode (shield helix between grounded baseplate
                        and shelf); `python3 choke_vna.py NAME FORMER TURNS PITCH GAP_BELOW GAP_ABOVE` runs one design
- `run_nec.py`        — deck generator + runner + parser; `python3 run_nec.py` reruns convergence
- `doublet_170ft_*.nec/.out` — sample deck and raw NEC output

## Model parameters
170 ft #12 AWG copper flattop, center-fed, 55 ft AGL.
Real ground: sigma = 0.005 S/m, eps_r = 13 (Sommerfeld-Norton, `GN 2`).
Wire loss included (`LD 5`, copper 5.8001e7 S/m).
**1201 segments** — required for convergence; see note below.

## Segmentation
R converges by ~400 segments on every band. X does NOT at the top end: at 28.5 MHz
(4.93 lambda, near a voltage antinode) X is still drifting -24 ohm per refinement step
at 1201 segments. |Z| is stable to 0.3% but the phase moves ~4.5 deg, which propagates
into the line transform. Treat 10m as +/-10% on reactance; all other bands are converged.

## AUR note
`necpp-git` in the AUR is stale twice over: it fetches over the dead `git://` protocol,
AND upstream moved from autotools to CMake. The PKGBUILD at
`~/.cache/paru/clone/necpp-git/PKGBUILD` has the protocol fixed (original saved as
`PKGBUILD.orig`) but `build()` still calls `make -f Makefile.git`, which no longer exists.
Build straight from the repo with CMake instead.
