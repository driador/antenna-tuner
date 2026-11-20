# 1500W Automated Antenna Tuner — Design Log
### Revision 3.7c — Vertical-Stack Architecture · Measured Parts · All-Band Band-Edge Basis

**License.** © 2026 Reuben A. Popp, KF0OWR. This design is open hardware under the CERN-OHL-W v2
and comes with no warranty; the firmware in `fw/` is GPL-3.0-or-later. `NOTICE` says what each
license covers and lists the third-party exceptions.
Source location: <https://github.com/driador/antenna-tuner>.

**Revision history**
- **Rev 1** — initial spec. Correct on materials/welding, chamber-crossing discipline, relay sequencing.
- **Rev 3.2** — *replacement, not revision*. Fixed several items; dropped four correct sections from
  Rev 1, which is how the encoder regression got in.
- **Rev 3.3** — cumulative consolidation; fixed three mechanical conflicts; real NEC-2 basis.
- **Rev 3.4** — **tuner relocated to the antenna entry box**, stress rebased on
  *all band edges* including 60 m, and the whole capacitor/inductor specification rebuilt around
  the **parts actually in hand** (measured, not catalog).
- **Rev 3.5 (2026-11-04)** — **capacitor complement corrected.** The parts in hand
  are **one Jennings UCSX-740-10 and one Soviet KP1-4 (20–1000 pF / 10 kV)**, not two Jennings.
  KP1-4 datasheet added (§5.1a). It is electrically adequate in either position but **does not fit
  the current RF bay** — new DECISION C-1 (§10.14) and §9 item 25 block fabrication.
  Used-cap acceptance testing added (§5.1b), including lead-screw cleaning and re-greasing.
- **Rev 3.6 (2026-11-12)** — **roller re-identified as 229-203 class, 5–10 A** against 18.4 A
  demanded, end plate broken (§5.3). New DECISION R-1 (keep / buy / build) and §9 item 27.
  **Homebuilt roller design added (§5.3a)**: Ultem rib cage, #4 solid, 26 turns at 3 TPI on 3.5″.
  Link inductor rises to 12.5 µH with a 22 µH roller (§5.4). Shaft, end brackets and bearings
  specified. **Orientation conflict found** — a 22 µH roller cannot fit across the bay width the
  drive train imposes (§9 item 28). Roller Q target ≥ 300 installed (§5.3a). **Enclosure raised
  to 12.00″ H** (§3, §4 cut list and nesting, §2.2 lid coupling, §7.5 panel, §10.13 tallies):
  14 ga stock becomes one 36″ × 48″ sheet, frame angle 22 ft. **§5.1 capacitance demand
  recalculated and archived** (`nec/cap_demand.py`): bare Jennings covers 27/27, the
  666 / 830 pF figures were solver artifacts, the 200 pF pad is optional (§5.2), and DECISION C-1
  now recommends A. §10.15 item 4 resolved.
- **Rev 3.7 (2026-11-13)** — **enclosure re-architected as a vertical stack** (§3.0): utility layer
  (control, motors, sampler) on the floor, grounded shelf, RF bay above it on the full footprint,
  every element **standing upright** on a straight vertical shaft. Box **16.00″ W × 16.00″ D ×
  21.00″ H** (12U). Resolves §9 item 28 (orientation) and DECISION C-1 without a right-angle drive.
  Standoffs 2.50″ → **3.50″**; deck 8.50″ × 13.00″ → **10.75″ × 10.75″**. **Capacitor voltage
  margins corrected:** Jennings suffixes are *peak test* voltage; RF working voltage is 60% of it
  (6 kV for a -10 part, 9 kV for a -15). Rev 3.4–3.6 margins of 1.36–1.70× were against the test
  rating (§5.1). **C1 becomes a 15 kV-class part** (UCSX-700-15 / "CB-154", or CVDD-500-15S);
  the **UCSX-740-10 in hand moves to C2** (measured 3.75″ × 7.0″). Roller for R-1 C becomes 22 µH
  at 4.7″ (§5.3a). Air path reversed to rise with convection (§8). Cut list, nesting and tallies
  for the new box are **not yet re-derived** (§9 item 29).
- **Rev 3.7a (2026-11-14)** — **consistency sweep**, plus the §5.3a roller drawing set, end
  retention and cement spec (see §5.3a), §6B dummy load / cal load / AUX passthrough, and the
  wall-mounted modular enclosure (§3.0, TUNER-E-200 to E-211, Appendix B), and parts selected for
  §9 items 16, 23, 34, 38–41 (graded bulkhead filtering §7.3/§7.3a, supply, relays, panel hardware); populated
  cabinet and color-coded harness (TUNER-E-212 to E-215), new items 42–43. Stale text brought in line
  with the current decisions: single-shaft motor with belt-takeoff encoder in §7.1 (as §10.6);
  link inductor 12.5 µH for R-1 B/C in the BOM; §1.3 capacitor voltages taken from the Rev 3.6
  `cap_demand.py` run (C1 6.54 kV, C2 2.40 kV); ÷1024 prescaler and its 1000 pF feedthrough
  carried into §6A.10, §7.3 and §10.11; Ethernet in §8B.0.3 and §8C.5; bench box per §8C.4(b);
  solver policy in §6A.9 set to lowest roller current; §10.11 stock marked for re-derivation;
  input choke lies flat (§6, §10.2); §5.3a roller notes for the 4.7″ re-scale; references and
  counts corrected. Two conflicts need an owner decision and are logged as §9 items 31–32.
  BOM gaps listed in §10.15 item 5.
- **Rev 3.7b (2026-11-16)** — **superseded material moved to the new Section 11**, so the body states
  only the current design. DECISION R-1 = C with a **single 34 µH homebuilt roller**; **output pad and
  series link deleted** (no vacuum relays in the RF tank); box **22.00″ H**. See *Changes in Rev 3.7b*.
- **Rev 3.7c (2026-11-17)** — **input choke rebuilt on #61 ferrite and moved into the RF bay**, under a
  deck raised 2.00″; box **24.00″ H**. Fixes a routing error that grounded the choke's deck side.
  Control and measurement boards rebuilt to the log (§10.5, §10.4); firmware begun (§8B.6). See
  *Changes in Rev 3.7c*.

**Changes in Rev 3.7c**
1. **Routing error fixed.** Through Rev 3.7b the choke sat in the sampler chamber, and its deck-side
   coax crossed two grounded connectors before reaching C1: partition adapter X and the shelf coax
   bulkhead (§7.3a; harness W16–W18). Both bodies bond to chassis, so the shield after the choke was
   grounded twice. The choke was bypassed and the deck could not float. The choke now stands at the
   shelf crossing: the shelf bulkhead is its chassis end, everything upstream (K1 → X → shelf) is
   chassis side, and its deck end goes straight to C1 (§3.0, §6, §7.3a).
2. **#61 ferrite choke replaces air-core design C** (§6). Design C's ~36 ft of RG-142B carries the
   full input power: its coax loss is **40–232 W** (160 m derated to 10 m), all inside the sealed
   sampler chamber. The new choke is **15 turns of RG-400 on 5 × Fair-Rite 5961003801 (FT-240-61)**:
   9.6 ft of coax, axis vertical, on an all-insulating G10 / FRP mount. |Z| is 2.4 kΩ at 1.8 MHz
   (4.5× design C) and exceeds the deck's reactance from 80 m up. It dissipates ≤ 69 W on 10 m and
   ~10 W on 160 m (`nec/choke_screen.py`). Design C and the "no ferrite in the high-stress path"
   argument move to §11.11.
3. **Deck raised 2.00″: standoffs 3.50″ → 5.50″, box 22.00″ → 24.00″** (§3.0, §3.2). A 4-core stack
   with the coax arcing over its faces is 2.95″ tall and did not fit the 2.50″ left under a 3.50″
   deck; the 5-core stack is 3.47″ and keeps 0.94″ to the shelf and 1.09″ to the deck. Everything
   above the deck keeps its clearances. Deck capacitance falls to ≈ 20.1 pF (§2.2); roller shaft
   creepage to the shelf rises to 4.37″ (§9 item 37); the longest G10 free span is 5.1″ (§3.1).
4. **The RF bay's 200 W budget now carries the choke** (§8): 160 m continuous limits **502 / 600 /
   882 W** (were 527 / 630 / 935 W, §1.7.1). Every other band stays at 1500 W (worst RF-bay total
   166 W at 4.00 MHz).
5. **Drawings regenerated:**
   - TUNER-L-100 to L-109. On L-109: 5.50″ standoffs, and detail G re-scaled to 0.35:1 to span the
     taller gap.
   - TUNER-E-200 to E-215:
     - 24″ panels, frame and wall flanges;
     - the choke and its mount in the populated views;
     - shelf holes CH1–CH3, and the choke mount detailed on E-209 (base disc, spider, mount between shelf and deck);
     - W15 runs straight to X, W16 is deleted, and W18 is the choke's RG-400;
     - the E-200 front-view height dimension is fixed (it read the flange foot, H − 1).
   - The intake and blower move up with the deck and box (§8).
6. **Frame joints detailed** (TUNER-E-201; §4):
   - **What was wrong:** the old note's single 1″ clip per junction could not join a post to both of
     its ring members.
   - **The new joint:** 16 corner clips (1-1/2 × 1-1/2 × 1/8 × 7/8″) nested in the post corners, with
     60 flush #6-32 flat heads and nylocs. The junction and the clip are drawn on E-201.
   - **Panel fastener rows:** they now start 2.00″ from each corner and skip the clip bands. Seven floor
     and top corner holes had no frame metal behind them; now every hole lands, and no rivnut sits behind
     a clip.
   - **Counts:** 344 panel holes (was 381); E-202 to E-210 regenerated.
7. **Bulkhead and partition mounting defined** (TUNER-E-208; §4):
   - 16 clip angles: four floor and four shelf clips per plate, at interference-checked positions,
     drawn with sections at the floor and the shelf.
   - The removable bulkhead's clips are on its motor side, with tapped legs, so it unscrews from the
     control side.
   - The old note's side clips are dropped.
8. **§9:**
   - Items 3, 28–31, 35, 37, 41, 45 and 46 updated.
   - New item **49:** verify the choke installed (VNA sweep, 10 m key-down thermal).
   - New item **50:** the antenna system's common-mode impedance, which sets how balanced 160 / 80 m
     really is.
   - New items **51** (the RF service-panel switch and its run) and **52** (the sampler cable needs
     11 pairs; M13197 has 8).
9. **Control board rebuilt to the log** (§10.5; the old board is in §11.13). The generator had not
   followed the log since Rev 3.4. It now carries:
   - **The §7.4 hardware permissive.** The bypass key overrides only the SWR trip and the MCU's
     vote. The 10 kHz tone comes from an LMC555, so the bypass works with a dead controller.
   - **The §6B additions:** K1/K2 coil-current sense, the cal-load window comparator and the
     cal-load thermal input.
   - **The §5.5 blanking latch.**
   - **Panel and blower:** the Nextion on Serial8, and the 3.3 V 62V15 encoders.
   - **On-board parts:** the 12 V and 5 V DC-DCs and the HFBR-1521Z.
   - **Wiring:** one ribbon per bulkhead D-sub, with the §7.3 series resistors; encoder MOSI; and
     the blower tach.
   - **Layout:** 139 × 91 mm, 4 layers, 1206/SOIC parts, so it fits the 5.5 × 3.6″ cassette
     envelope. Every new part was checked for stock and price (2026-11-19). New Teensy pin map
     §8B.0.4.
10. **New Appendix C:** both boards rendered from KiCad on every build (`doc/build.sh`: 3D views of
    the bare board with silkscreen, the silkscreen as line art, each copper layer).
11. **New sheet TUNER-E-216 — the input choke assembled** (§6, Appendix B):
    - Section A-A at 1:1, a half section: the five cores and the turns cut, the mount stack, and both
      leads leaving toward −X.
    - Section B-B at mid-winding: the 15 turns packed against the bore, and the gap.
    - An exploded view with a 12-item parts and hardware list.
    - The winding and clamp notes.
    The turns are modeled one by one (`enclosure.py` `choke_detail()`), and fill the worst-case 3.47″
    envelope that the interference checks use.
12. **PDF figures brought up to the text** (`doc/diagrams/`, `inject_diagrams.py`). The figures had
    not changed since Rev 3.6:
    - **§7.1 coupling train:** it had dropped out of the PDF when the Rev 3.7b wording changed. It is
      redrawn with the direct NEMA 23 drive, and the belt takeoff to the 2-stage reduction, encoder
      and limit cams.
    - **§7.4 interlock:** now the Rev 3.7c permissive. (SWR ∧ MCU) ∨ bypass, ANDed with HARD_OK
      (cal-load window, cal-load thermal, RF service-panel switch, limits), drives the LED keyed at
      10 kHz.
    - **§6A.3b crossing:** the 5600 pF D-sub filter, which replaces 0.01 µF.
    - **§6A counter:** the 1000 pF feedthroughs at both walls, with RG-316 between, into the control
      board's SMA.
13. **Measurement board rebuilt to the log** (§10.4; the old board is in §11.14). It had not changed
    since Rev 3.4:
    - **§9 item 35:** the cal-load RF detector (§6B.3a) is on it, and the ÷1024 count leaves on an
      edge SMA for the RG-316 run W10 instead of on the ribbon.
    - **Coupler:** in its own diecast box (§10.3, §9 item 53). The board takes FWD and REF on edge
      SMAs and terminates both ports: 2 × 105 Ω 1 W each, 50.2 / 50.7 Ω with the taps.
    - **Vector path corrected (§6A.5):** ~30 dB taps replace the ~60 dB pad, which left the AD8302 no
      range at tuning power. The AD8302 is now in measurement mode (MSET/PSET had been tied to VREF),
      AC-coupled and terminated, with its offset loop at 20 kHz instead of 2 MHz.
    - **Detectors:** 1N5711W (70 V) replaces the HSMS-2850, whose 3.8 V breakdown faced ~19 V reverse
      at 1500 W. The outputs are scaled to 2.9 V at 1500 W for the 3.3 V ADC.
    - **Counter:** AC-coupled and mid-biased, so it counts from ~1 W; the TLV3501's SHDN had been tied
      high, which disables it. The obsolete 74AC4040 becomes a 74LVC74 ÷4 and a 74HC4040 ÷256
      (§8B.0.1).
    - **SWR trip:** threshold on a trimmer (§6A.4).
    - **Board:** 100 × 74 mm, 4 layers, 1206/SOIC, inside the sampler's 4.0 × 3.0″ envelope (was
      215 × 145 mm, 2 layers, through-hole). Every part checked for stock and price (2026-11-19).
14. **Control board: SOT-223 tabs and SMA legs connected** (§10.5). `make_pcb.py` netted only the
    first pad with a given number, so the tabs of Q1–Q4 and U3 and three of J11's four ground legs
    were on no net. DRC cannot see it, because a no-net pad that touches nothing breaks no rule. Fixed in
    the generator. On the routed board each tab is tied to its middle pin, and J11's legs join the
    pours.
15. **Coupler box in the model** (§9 item 53; E-212 to E-215):
    - The Hammond 1590A sits on the sampler baseplate between the coax input and K1.
    - W13/W14 run to its SO-239s, and the new W27/W28 carry FWD/REF to the board on one length of
      RG-316.
    - W9 is 16 conductors.
    - The board envelope is the real 100 × 74 mm. Its ÷1024 SMA moved to the top of the left edge, so
      the plug clears FT-P.
16. **Analyses (§9 items 10, 50):**
    - The 10 m reactance uncertainty is wider than ±10 %, but the network covers it (`nec/conv10.py`).
    - The NEC common-mode model has the adopted choke meeting the §2.2 balance on 160 and 80 m with
      one vane setting (`nec/cm_balance.py`).
17. **Sampler cable** (§9 item 52, §7.3a): Belden 8112, 12.5 pairs, carries all 11 pairs the sampler
    group needs. W8 is soldered at J-B and has a DB-25 plug at J-S, as §7.3a has the walls; the
    harness had said plugs at both ends.
18. **RF service-panel interlock chosen and routed** (§9 item 51, §7.4): a Littelfuse 59140 reed sensor
    on the front shelf-ring flange with its magnet on the panel. That keeps the gasketed flange whole.
    Its lead W12c runs from shelf FT4 along the right wall; W12b now serves FT1–FT3 only.
19. **Firmware begun** (§8B.6, `fw/`): the tuning core and its closed-loop host tests. They settle
    how the sign of θ is resolved, put the stored profiles on 1 % segments, add coarse moves for
    far-off readings, and set the 1.2:1 convergence target. The over-SWR trip counts only once
    matched. Open item 54 is the commissioning bounds the firmware was tested to. The Teensy layer
    (boot, watchdog, motion, measurement, storage, a USB console) builds and waits for the boards.
    It also has per-band calibration, which is scalar because the AD8302 loses the phase sign
    (§6A.8), TUNE/AUX/CAL switching with coil and RF checks, the local panel and manual jog. It also
    has the PERMISSIVE qualification, the SD mirror with versioned backups and restore by identity,
    a numbered event log, and the link protocol and web page.
20. **microSD extender** (§8B.5.6): an Adafruit 6070 brings the Teensy's card to the cassette face, below
    the encoders (E-202, F; §10.7). Its plug stays in the Teensy's socket, so the firmware treats the
    card as present only while it answers.

**Changes in Rev 3.7b**
1. **New Section 11 — Superseded Designs and Decisions.** The side-column enclosure, the
   16 × 16 × 12″ cut list and tallies, the capacitor-complement history, the output pad, the Harris
   and earlier homebuilt roller sizings, the series link and tank vacuum relays, the old bulkhead
   filtering and gasket schemes, the direct-gate frequency counter, the hardware bench panel and the
   resolved §10.15 discrepancies moved out of the body; short pointers remain.
2. **DECISION R-1 = C:** homebuilt roller resized to a **single ~34 µH roller, no series link** —
   5.20″ to wire center, 22 turns #4 solid at 3 TPI (notched for 24), 10 ribs, 11.547″ over the end
   plates (§5.3a, `cad/roller.py`). Drawings TUNER-L-100 to L-109 regenerated. The Harris
   492-0309-000 / 229-class roller in hand is a spare.
3. **Output pad deleted** (§5.2) and **series link deleted** (§5.4): **no vacuum relays** anywhere in
   the RF tank; §5.5 now applies to the K1/K2 coax relays only. The roller carries the whole inductance (§9 item 45 later showed only ~22.3 µH is ever needed):
   ≈ 4.6 kV RMS at the 1.800 MHz worst-current point (≤ 6.6 kV RMS bound, §9 item 45), ≤ 300 V RMS turn to turn.
4. **Bare-network figures:** C1 6.54 kV pk (1.38× to 9 kV working), C2 2.40 kV (2.50×), roller loss
   ≈ 341 W at Q = 250 at 1.800 MHz, 160 m 1.800–1.850 MHz derate ≈ 530 W (§1.3, §1.7, §5.1, §8).
   V_L and the exact derate await a bare `cap_demand.py` re-run (§9 item 45).
5. **Box height 21.00″ → 22.00″** (§3.0 closure); deck plan fully used (cap column at the deck
   edge); installed clearances from TUNER-L-109 (§5.3a).
6. **RF-tank control crossing reduced to 3 lines** (tank thermal + imbalance CT): J-E becomes a
   filtered DE-9 (FCE17-E09SM-290); shelf feedthroughs FT1–FT4 (§7.3, §7.3a); §10.11 and §10.13
   quantities re-derived.
7. **§9:** items 16, 19, 24, 27, 28, 31, 32 updated; item 42 resolved; new items 44 (roller idle-turn
   self-resonance), 45 (bare `cap_demand.py` re-run) and 46 (output DC-path re-check). Wording:
   single-turn encoders (§7.1), left-side exhaust (§8), "lid" → top panel / RF service panel /
   cassette.

**Changes in Rev 3.4**
1. **Tuner sited at the entry box**, not the bench. Eliminates ~20 ft of indoor ladder line.
2. **Feeder 88 ft → ~40 ft** (outdoor run only), with the last foot deliberately adjustable.
3. **60 m added** and every band evaluated **at its edges**, not a spot frequency.
4. **Padding array 4-bit → one 200 pF capacitor on one relay.** Seven doorknobs and three relays deleted.
5. **85 pF capacitor travel clamp removed** — it protected against a voltage that does not exist.
6. **Roller inductor specified from measurement**: 0.20–24.40 µH, plus a **10 µH switchable series link**.
7. **Static-drain gap closed** by the existing entry-box bonding and arrestors.

---

## Section 1 — Antenna and System Basis

> **Two corrections carried into this revision.** (a) Rev 3.2 and all prior figures assumed a
> *"170 ft horizontal dipole at 55 ft AGL."* The installed antenna is an **inverted-V / sloper with
> an apex near 35–40 ft, cut for NVIS work.** (b) All prior figures were computed at **spot
> frequencies**; for all-band full-power service the envelope lives at the **band edges**, and
> **60 m — the classic NVIS band — was absent from every earlier table.**

**Modeled configuration**
- 170 ft total #12 AWG copper (85 ft per leg), center-fed
- Inverted-V, apex 37.5 ft, ends 10 ft AGL (horizontal run ≈ 80.4 ft per leg)
- Real ground: σ = 0.005 S/m, ε_r = 13 (Sommerfeld-Norton, `GN 2`)
- Copper wire loss included (`LD 5`)
- Feeder: **~40 ft** of 600 Ω open-wire ladder line, VF ≈ 0.95, **outdoor run only**
  (tuner sited at the entry box — see Section 1.6)

**Simulation provenance.** `nec2++` built from source (github.com/tmolteno/necpp, CMake, Release);
708/708 self-test assertions pass. Model run at **1200 segments**. Binary, deck generator and raw
output are archived in `nec/`.

> **Segmentation note.** R converges by ~400 segments on every band. X does **not** at the top end:
> at 28.5 MHz (≈4.9 λ, near a voltage antinode) X was still drifting ≈ −55 Ω per refinement at 1200
> segments. |Z| is stable to <0.5% but phase moves several degrees, which propagates into the line
> transform. **Treat 10 m reactance as ±10%; all other bands are converged.** *Rev 3.7c (§9 item 10):*
> the honest band is ±20% on R and ±250 Ω on X, because the feed geometry itself matters near the
> antinode. The network still covers it (`nec/conv10.py`).

### 1.1 NEC-2 feedpoint impedance

| Band | f (MHz) | Z_ant (Ω) |
|:--|--:|:--|
| 160 m | 1.85 | 18.7 − j632.5 |
| 80 m | 3.65 | 154.7 + j659.1 |
| 40 m | 7.15 | 147.4 − j895.5 |
| 30 m | 10.12 | 686.4 + j1237.9 |
| 20 m | 14.20 | 114.6 − j81.8 |
| 17 m | 18.12 | 511.6 − j1212.3 |
| 15 m | 21.30 | 446.8 + j728.2 |
| 12 m | 24.95 | 202.8 − j477.4 |
| 10 m | 28.50 | 2604.3 − j546.3 |

### 1.2 Tuner input impedance — spot frequencies, 88 ft line *(SUPERSEDED)*

> **Retained for reference only.** This table assumes the abandoned 88 ft bench-sited feeder and
> single spot frequencies. **The governing figures are in 1.2b and 1.3** (40 ft feeder, band
> edges). Do not size components from this table.

Derivation: `I_rms = sqrt(P/R_in)`, `V_rms = I_rms · |Z_in|`, `V_pk = sqrt(2) · V_rms`.

| Band | Z_in (Ω) | I_rms | V_pk | Dominant stress |
|:--|:--|--:|--:|:--|
| **160 m** | **9.6 + j174.2** | **12.51 A** | **3088 V** | **Current / kVAr** |
| 80 m | 70.2 − j80.1 | 4.62 A | 696 V | Low |
| 40 m | 45.5 + j60.0 | 5.74 A | 611 V | Low |
| 30 m | 271.0 + j706.8 | 2.35 A | 2519 V | Moderate |
| 20 m | 600.8 − j1127.3 | 1.58 A | 2854 V | Moderate |
| 17 m | 91.6 + j79.0 | 4.05 A | 692 V | Low |
| 15 m | 490.7 + j772.1 | 1.75 A | 2262 V | Moderate |
| 12 m | 2587.3 + j984.5 | 0.76 A | 2981 V | Voltage |
| 10 m | 150.4 − j217.2 | 3.16 A | 1180 V | Low |

### 1.2b All-band band-edge stress — the governing table

Twenty-seven band-edge points modeled. 60 m is the standout: 170 ft is 1.85 half-waves there,
close to a voltage antinode, giving Z_ant ≈ 7,100 Ω.

| Band | Edge freqs modeled | Worst Z_ant |
|:--|:--|:--|
| 160 m | 1.800 / 1.900 / 2.000 | 17.7 − j674.8 |
| 80 m | 3.500 / 3.750 / 4.000 | 262.3 + j1023.1 |
| **60 m** | **5.332 / 5.405** | **7058.3 + j405.9** |
| 40 m | 7.000 / 7.150 / 7.300 | 178.0 − j1025.8 |
| 30 m | 10.100 / 10.150 | 724.9 + j1274.0 |
| 20 m | 14.000 / 14.175 / 14.350 | 120.6 + j0.5 |
| 17 m | 18.068 / 18.168 | 550.7 − j1258.5 |
| 15 m | 21.000 / 21.225 / 21.450 | 558.6 + j851.0 |
| 12 m | 24.890 / 24.990 | 211.1 − j507.3 |
| 10 m | 28.000 / 28.500 / 29.000 / 29.700 | 2604.3 − j546.3 |

**Worst case at the 40 ft feeder: 4,191 V peak and ~14 A RMS.** Both limits fall on 160 m at the
band edges (1.800 MHz for current, 2.000 MHz for voltage) — *not* at 1.85 MHz, which is why spot
-frequency modeling understated them.

### 1.3 Design envelope

Apex and end height are both approximate, so the design figures are the **worst case across
apex 35–40 ft and ends 6–15 ft**, not the nominal:

| Quantity | Spot-frequency basis (superseded) | **Design envelope (band edges, 40 ft)** |
|:--|--:|--:|
| Peak RF voltage at tuner | 3,088 V | **4,191 V** |
| Peak RF current at tuner | 12.51 A | **~14 A** |
| Max voltage across C1 | — | **6.54 kV pk** (160 m @ 1.800 — §5.1) |
| Max voltage across C2 | — | **2.40 kV pk** (lowest-loss solution — §5.1) |
| Max roller current | — | **18.4 A RMS** (160 m) |

Geometry sensitivity remains small (apex 35–40 ft, ends 6–15 ft moved the result only a few
percent). **Both limits occur on 160 m at the band edges.**

#### 1.3.1 Actual operating power — the design basis is conservative

The station amplifier is a **Heathkit SB-220** (pair of 3-500Z), which delivers roughly
**1000–1200 W output**, not 1500 W. Retaining 1500 W as the design basis is deliberate headroom
against a future amplifier, but the real stress is lower. Voltage and current scale as √P:

| Actual power | Peak V at tuner | Peak I | 160 m loss @ 1.800 (Q = 150) |
|--:|--:|--:|--:|
| 1500 W *(design basis)* | 4,191 V | 14.0 A | 568 W |
| 1200 W | 3,749 V | 12.5 A | 454 W |
| **1100 W** *(realistic SB-220 max)* | **3,589 V** | **12.0 A** | **417 W** |
| 1000 W | 3,422 V | 11.4 A | 379 W |
| 100 W *(typical use)* | 1,082 V | 3.6 A | 38 W |

At ~1100 W the margins improve meaningfully: the worst-case C1 margin goes from
**1.38× to 1.61×** (9 kV working, 15 kV-class C1; §5.1), and the ≥10 kV output
feedthroughs sit at **2.79×**.

**The 160 m derate table in 1.7.1 does not change** — those limits are set by the 200 W dissipation
budget, not by amplifier capability. At ~1100 W the amp **exceeds all three 160 m limits**
(≈ 502 / 600 / 882 W since Rev 3.7c, with the input choke's heat in the RF bay; §1.7.1), so the
whole band is power-limited for key-down modes.

### 1.4 Feeder length — ~40 ft, and make the last foot adjustable

With the tuner at the entry box the feeder is the outdoor run only. Coverage of all 27 band-edge
points. The table below is the **Rev 3.4 parts set** (roller 0.20–24.40 µH, Jennings 20–675 pF,
with the since-deleted 200 pF pad and 10 µH link — §11.4, §11.6). The Rev 3.6 bare re-run (§5.1,
`cap_demand.py`: no pad, L 0.20–34.40 µH, the same range as the single 34 µH roller of §5.3a) gives
**27/27 at 39–41 ft for VF 0.93–0.97**, and 42 ft misses only 10 m @ 29.700 at VF 0.93. It does not
yet use the 15 kV-class C1 range (§9 item 45).

```
  37 ft   25/27      40 ft   27/27  <- target
  38 ft   25/27      41 ft   27/27
  39 ft   26/27      42 ft   26/27
                     43 ft   26/27
```

- **Target 40–41 ft.** Full coverage of every band edge.
- **Every near-miss is a single band-edge frequency**, never a whole band — 40 m at 7.000 or
  10 m at 29.700, depending which way the length errs.
- **VF tolerance is tight:** 27/27 at VF 0.95, 25–26/27 at 0.90–0.99. Real open-wire VF varies
  with construction and weather.

**Therefore: do not chase the predicted optimum.** Cut the run long, terminate the last ~2 ft as a
removable jumper section, and trim on the bench against measured SWR. The tuner itself reports
which band edges cannot be reached, so empirical trimming converges in one session. This
replaces a prediction that cannot survive VF uncertainty with a measurement that settles it.

### 1.5 Safety

- **Peak RF voltage up to ~4.2 kV** at the tuner terminals and **~6.5 kV across C1** (§1.3). Contact causes deep RF burns which are
  far more extensive than they appear at the surface. Note the mechanism: above ~100 kHz the hazard
  is **thermal, not electrocution** — HF RF does not induce ventricular fibrillation. The practical
  rule is unchanged: never open the cabinet with the amplifier keyed.
- **Circulating current up to ~18.4 A RMS** through the roller inductor on 160 m. Any oxidation or
  weak contact at the roller wheel becomes localized ohmic heating, pitting, or arcing.
- **160 m is the limiting band for both** voltage and current in this installation.

---

### 1.6 Siting — the tuner lives at the entry box, INSIDE the garage

> **Unambiguously: the tuner mounts on the *interior* face of the garage wall, immediately
> adjacent to the antenna isolation box.** It is sheltered — no rain, no direct sun, no UV. It is
> *not* an outdoor enclosure, and must not be built as one. Earlier drafts said only "at the entry
> box," which reads either way; this is the binding statement.
>
> The feeder is still the **outdoor run only**, because the wall penetration happens at the
> isolation box and the tuner sits directly behind it. That is the whole benefit of this
> architecture — the ~20 ft of indoor ladder line disappears without putting the tuner outside.
>
> Environmental design follows from this: see Section 8E (sealed chambers at IP5X, ventilated RF
> bay, condensation management). **If the tuner were ever relocated outdoors, Section 8E would need
> rewriting entirely** — IP65 throughout, sunshade for solar gain, hooded air intake, and far more
> demanding gasketing on hand-fabricated sheet metal.

The tuner is mounted at the **antenna entry / isolation box**, with coax running to the operating
position. This is an architecture decision, not a convenience:

- **The indoor run is not 600 Ω line.** Ladder line routed up a wall, across a ceiling and down the
  far side runs close to framing and house wiring the whole way; Z₀ and VF both shift
  unpredictably. The model cannot describe it.
- **It carries kilovolts past the entry panel.** At 1500 W the feeder sees voltage antinodes along
  its length — an RFI injector and a genuine hazard over a garage ceiling.
- **It defeats the existing protection.** Bonded grounding and arrestors already exist at the wall;
  running the hot balanced line 20 ft beyond them wastes that.

Consequences: the balanced line is **entirely outdoors**, its VF is well-behaved, and the stress
model is trustworthy. Coax to the bench is matched and any length. Requires a **remote control head
or network link** (see Section 7.5) and an enclosure rated for a **sealed, climate-controlled**
garage interior — see Section 8E.

### 1.7 Network loss, efficiency, and bandwidth — derived

The 200 W thermal figure inherited from Rev 3.2 was asserted, never derived. Computed here from
the actual network solutions, with roller Q at 250 (clean contact) and 150 (realistic with
contact resistance):

| Band | f (MHz) | L | I_roller | Loss @ Q=250 | Loss @ Q=150 | Efficiency | Q_loaded | 2:1 BW |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| **160 m** | **1.800** | **22.2 µH** | **18.4 A** | **342 W** | **569 W** | **77%** | 15.6 | 115 kHz |
| 160 m | 1.900 | 16.6 µH | 17.3 A | 236 W | 394 W | 84% | 11.3 | 168 kHz |
| 160 m | 2.000 | 11.7 µH | 16.2 A | 154 W | 256 W | 90% | 7.6 | 263 kHz |
| 80 m | 3.500 | 21.4 µH | 5.9 A | 67 W | 111 W | 96% | 10.3 | 340 kHz |
| 80 m | 4.000 | 12.9 µH | 8.0 A | 83 W | 138 W | 94% | 9.3 | 430 kHz |
| 60 m | 5.332 | 2.2 µH | 10.1 A | 30 W | 50 W | 98% | 2.4 | 2.3 MHz |
| 40 m | 7.000 | 22–32 µH‡ | 1.6 A | 14 W | 24 W | 99% | 7.9 | 887 kHz |
| 30 m | 10.100 | 8.4 µH | 2.9 A | 17 W | 29 W | 99% | 5.0 | 2.0 MHz |
| 20 m | 14.000 | 4.1 µH | 2.0 A | 6 W | 10 W | >99% | 2.1 | 6.6 MHz |
| 15 m | 21.000 | 1.1 µH | 3.6 A | 8 W | 13 W | >99% | 1.6 | 13 MHz |
| 12 m | 24.890 | 0.7 µH | 8.0 A | 26 W | 44 W | 98% | 2.8 | 8.8 MHz |
| 10 m | 28.000 | 0.7 µH | 7.7 A | 30 W | 50 W | 98% | 3.4 | 8.2 MHz |

L, current and losses: `cap_demand.py` **Rev 3.7b** (§9 item 45) — bare network, 15 kV-class C1,
UCSX-740-10 as C2, single roller, no pad, no link, 40 ft / VF 0.95, lowest-roller-current policy.
Q_loaded and bandwidth are still the Rev 3.4 estimates (they change little; the 160 m L and C barely
moved). ‡ On 40 m any L from ~22 µH upward matches; the policy picks the roller's maximum (24 W at
Q = 150), while the smallest workable L is lower loss (~17 W) — firmware should prefer it.

**The loss is confined to 160 m, and specifically its bottom end.** Every other band edge stays
under 140 W even at Q = 150. The 200 W figure was broadly right — but wrong where it matters.

*Rev 3.7c: the input choke adds its own loss ahead of the network (§6) — mostly RG-400 coax loss:
≈ 0.03 dB on 160 m rising to ≈ 0.2 dB (69 W of 1500 W) on 10 m. It is not in the table above, but it
is in the RF-bay budget (§1.7.1, §8).*

**Why 160 m is expensive.** At 1.800 MHz the antenna is 0.64 half-waves — electrically short, so
radiation resistance is low and the feeder presents R_in ≈ 8.9 Ω with −j226 of reactance. Matching
that to 50 Ω demands Q_loaded ≈ 15.6, which puts **18.4 A through the roller** and kilovolts across
it (**4.63 kV RMS, 6.55 kV pk** across the 22.2 µH in use, §9 item 45). The loss is `I²·ωL/Q`: the bare solution's
≈ 342 W at Q = 250 is ≈ 1.0 Ω of equivalent series resistance carrying 18.4 A.

**This is an antenna limitation, not a tuner defect.** No feeder length fixes it — R_in on 160 m
stays between 7.6 and 11.6 Ω across every length from 60 to 120 ft. A 170 ft wire on 160 m is short,
and a tuner cannot recover what a short antenna does not present.

#### 1.7.1 Continuous power limit by band

Loss scales linearly with power, so for a **200 W internal dissipation budget**:

| Band segment | Continuous power limit |
|:--|--:|
| **160 m, 1.800–1.850 MHz** | **≈ 502 W** |
| **160 m, 1.850–1.950 MHz** | **≈ 600 W** |
| **160 m, 1.950–2.000 MHz** | **≈ 882 W** |
| **All other bands** | **1500 W — no derate** |

*Rev 3.7c: the input choke now sits in the RF bay (§6), so its heat counts against the same 200 W.
The network-only limits (527 / 630 / 935 W, Rev 3.7b) become 502 / 600 / 882 W
(`nec/choke_screen.py`, output `nec/out/choke_screen_rev37c.txt`). Other bands peak at 166 W
(4.00 MHz: 138 W network + 28 W choke).*

*Rev 3.7b (§9 item 45): bare network, worst point of each segment at Q = 150. The 1.850 and 1.950 MHz
points are interpolated linearly in Z between the NEC band edges. The two upper segments are **lower
than the old padded figures (840 / 1325 W)** — the pad saved more loss mid-band than at 1.800 MHz.*

Three things keep this from being a real constraint in practice:

1. **At 100 W — the stated typical operating power — worst-case loss is 38 W.** Trivial anywhere.
2. **PEP is not average.** For SSB the average is well under a third of PEP, so 1500 W PEP voice on
   160 m sits comfortably inside budget. The derate binds for **key-down CW, RTTY, FT8 and tuning
   carriers**, which is exactly where it should.
3. The derate is firmware-enforceable: the tuner already knows the frequency (6A.10) and the
   element positions, so it can compute live dissipation and fold back power or warn.

**Firmware requirement:** implement the derate as a **warning plus a logged event**, not a hard
PTT inhibit. An operator running a 160 m contest sprint should be told, not silently cut off.

#### 1.7.2 Bandwidth and retune cadence

Loaded Q also sets how far you can move before the match degrades. The 2:1 SWR bandwidth is
narrowest where Q_loaded is highest — **115 kHz at the bottom of 160 m**, widening to megahertz on
the high bands.

Compare against the retune trigger in Section 8B.2 (±0.5% of frequency): at 1.8 MHz that is ±9 kHz
against ±57 kHz of available bandwidth. **The trigger is roughly 6× more conservative than
necessary.** That is deliberate and harmless, but if tuning proves slow in service the window can
be widened toward ±2% on the low bands without SWR penalty. Do not widen it above 20 m, where the
solution windows in capacitance are narrow even though the SWR bandwidth is broad.

## Section 2 — Topology and Antenna Balance

Conventional configurations placing a **4:1 voltage or current balun on the output stage are
rejected** — under high-Z reactive loads at several kV, core flux drives saturation, dielectric
overheating, and breakdown. (The rejection applies to an output-side *ferrite balun*, not to the
T-network itself, which has no core.)

**Adopted:** an **unbalanced T-network on an isolated floating sub-deck**, with a **1:1 Guanella
current choke on the 50 Ω input node**.

```
[50Ω Amp] -> [Stockton Coupler] -> [1:1 Input Choke] -> [Floating T-Network Deck] -> [600Ω Output]
```

**This is a compromise, adopted knowingly.** A 1:1 input choke provides common-mode isolation of the
coax from the shack; it does **not** by itself balance the antenna, because a T-network output is
single-ended. The floating deck is what creates the second output terminal, and it carries parasitic
capacitance to the surrounding chassis.

### 2.1 Alternatives evaluated and rejected on the record

| Topology | Verdict |
|:--|:--|
| **Link-coupled / Z-match** (Johnson Matchbox) | Truly balanced, no ferrite in the RF path. **Rejected:** automating variable link coupling plus multi-tap HV band switching needs rotary tap servos or multiple vacuum contactors. |
| **Differential balanced L/T** (Palstar BT1500A style) | Fully symmetric about ground, no floating-deck strays. **Documented as the gold-standard alternative; rejected** on cost — doubles the motorized elements and requires paired vacuum variables. |
| **Floating sub-deck** | **Adopted**, with the hard limits below. |

### 2.2 Balance specification

Balance is specified by **measured feeder current imbalance**, not by total deck capacitance —
total capacitance does not capture the structural asymmetry (leg 1 lands on the large deck plate,
leg 2 on a compact capacitor terminal):

```
    | I_leg1 - I_leg2 | / ( (I_leg1 + I_leg2)/2 )  <=  0.05
```

**Parasitic budget, derived** (vertical stack, §3.0); the deck faces the grounded shelf. *The
side-column (Rev 3.6) estimate, 27.0 pF, is superseded — see §11.1.*

| Contribution | Value |
|:--|--:|
| Deck plate to shelf, 10.75″ × 10.75″ at d = 5.50″ (`C = ε₀A/d`) | 4.73 pF |
| Fringing (perimeter 43.0″; Rev 3.6 figure, not re-derived for 5.50″) | ≈ 6.5 pF |
| Top coupling to top panel at ~13.2″ (24.00″ box; scaled from 2.1 pF at 12.2″) | ≈ 1.9 pF |
| Component bodies on deck | ≈ 7.0 pF |
| **Total C_deck-chassis** | **≈ 20 pF** |

*Rev 3.7c: deck raised 2.00″ for the input choke under it (§3.0, §6); at 3.50″ the plate term was
7.43 pF and the total ≈ 23 pF. The deck-to-top distance is unchanged — the box grew with the deck.*

The 0–30 pF trimming vane covers it. Balance is set by measurement regardless. *Rev 3.7c model (§9
item 50):* the input choke makes leg 1's shunt parallel-resonant near 1.8 MHz and ~18–19 pF on 80 m.
One vane setting near 11 pF holds ≤ 4.3 % on both bands. Past ~15 pF the vane approaches an 80 m
common-mode resonance with the antenna system, so set it on 80 m by the output CT, then check 160 m.

Leg 2 presents ≈ 3.0 pF. A **0 to 30 pF adjustable aluminum trimming vane** between leg 2 and
chassis provides mechanical calibration to equalize both legs.

**Verification instrument:** a bifilar current transformer on the balanced output feeds
real-time imbalance telemetry to the microcontroller. Balance is measured, not assumed.

---

## Section 3 — Enclosure Architecture

### 3.0 Vertical stack

**Why.** In the side-column layout every element shaft crosses the spine across the 10.42″ bay
width, so each element's *length* has to fit an 8.50″ deck. The UCSX-700-15 (9.62″) and any
full-size roller (9.9″ and up) do not; the fixes were a right-angle drive, a motor pod, or a smaller
roller (§9 item 28; §11.1, §11.5). Stacking the utility chambers *under* the RF bay turns every shaft vertical:
element lengths go into height, and only their diameters compete for floor area.

**Why the utility layer is at the bottom.** The roller dissipates up to ~200 W continuous (§8,
§1.7). With the RF bay on top, that heat rises out of the box instead of into the motors, encoders
and MCU (encoders and MCU are typically limited to ~85 °C).

```
  FRONT                                                       REAR
 +------------------------------------------------------------+  ^
 |  RF BAY  15.87" x 15.87" x 18.76" clear  (top panel above) |  |
 |                                                            |  |
 |     [C1] CB-154 / 15 kV class    (roller 34 uH, 5.2" dia,  |  |
 |      |   upright                  upright)                 |  |
 |     [C2] UCSX-740-10                    |                  |  |  24.00"
 |      |   upright                        |                  |  |
 |  ====|==== floating deck 10.75" sq =====|=======           |  |
 |      |  Delrin Oldham (coupler B), 5.50" standoffs         |  |
 |      |  [input choke, 5 x FT-240-61] at the shelf coax     |  |
 +======|=================================|===================+  |  grounded shelf
 |  UTILITY LAYER, 5.00" clear            |                   |  |
 |  CONTROL 3.0" D | MOTORS 7.5" D, shafts up | SAMPLER 5.0" D |  |
 |  display, MCU   | encoder takeoff (M-1)    | K1/K2, bridge  |  |
 +------------------------------------------------------------+  v
```

**Height closure (bottom to top):**

```
Floor 0.081 + utility 5.000 + shelf 0.081 + standoffs 5.500 + deck 0.081
  + roller over plates 11.547 + plate B to top 1.630 + top 0.081         = 24.00"
Specified 24.00" (Rev 3.7c: +2.00" standoff for the input choke, §6; 22.00" in Rev 3.7b, 21.00" / 12U before)
```

Every hot part of the roller keeps ≥ 2.25″ to the top panel (last turn 3.70″, bus rod 2.69″), so
both the §3.2 1.5″ air rule and the 2.25″ element-to-wall rule hold (§9 item 31).

The tallest element is the 34 µH, 5.2″ roller: **11.547″ over the end plates** (10.547″ plate to
plate, §5.3a). The CB-154 is 9.62″ ± 0.25″ overall including its 0.75″ shaft tip, of which about
1″ sits below the deck, so it stands about 8.9″ above it.

**Deck and floor plan.** Deck edge to side walls ≥ 2.50″ (§3.2) gives ≤ 10.87″; specified
**10.75″ × 10.75″**. Element layout, 1.5″ hot-to-hot between elements, cap column at the deck edge:

| Across the width | Inches | Along the depth | Inches |
|:--|--:|:--|--:|
| Cap column (C1, C2) | 3.75 | C1 + gap + C2 | 3.75 + 1.50 + 3.75 = 9.00 |
| Gap | 1.50 | Roller end-plate footprint | 7.50 |
| Roller end plate, 5.50″ across (coil OD 5.40″) | 5.50 | | |
| **Total** | **10.75** (0 spare — the deck is fully used) | **Deck depth needed** | **9.00** (1.75 spare) |

Coil to the C1/C2 envelopes is 1.55″ across the width (1.87″ diagonal), so the 1.5″ hot-to-hot rule
holds; deck edge to walls stays ≥ 2.5″.

C1 at the front, C2 at the rear near the balanced output feedthroughs (§8D). The input coax runs
from the sampler forward *inside the utility layer* and rises through one shelf bulkhead near C1,
straight into the input choke standing under the deck. The choke's deck end goes to C1 (Rev 3.7c, §6).

**Utility layer.** The same three chambers as before, now laid flat and full width:
- Control **3.00″** at the front (display on the bottom of the front panel).
- Motor **7.50″** in the middle. The C1 and C2 axes are 5.25″ apart in depth; with 2.22″ NEMA 23
  bodies they span 7.47″.
- Sampler **5.00″** at the rear: coupler, measurement board, K1/K2. The input choke left this
  chamber in Rev 3.7c (§6).

3.00 + 7.50 + 5.00 + 2 × 0.081 walls = 15.66″ of the 15.87″ inside depth. The **5.00″ height is
set by DECISION M-2**: it holds a motor body ≤ ~2.6″ plus encoder and coupler A. A longer motor
raises the box.

*Rev 3.7a populated model (TUNER-E-212 to E-215):* the control-chamber floor I/O (IEC, RJ45, POF,
vent) moved into a **3.2″ I/O strip along the left wall**: the cassette tray now stops at Y = 3.6″, so
the tray slides out without passing over connector bodies (it rode only 0.5″ above them). Sampler
floor connectors moved clear of the relays (and of the Rev 3.7a choke); the sampler baseplate has
clearance holes over them. The shelf coax bulkhead moved to X = −4.0″ — after the cap-column shift it
had landed over the **control** chamber. The coax from K1 to the shelf crosses the partition through
a new N-N bulkhead adapter (X, Amphenol RF 172124, §9 item 43). Since Rev 3.7c that whole run is chassis
side, ahead of the choke (§6).

**What crosses the shelf:** three G10 shafts in bushings, one coax bulkhead, and discrete filtered
feedthroughs FT1–FT4 for the tank thermal, imbalance-CT and RF service-panel switch lines (all four used, §7.3a). The §7.1
rule — no wires between the motors and the RF bay — still holds: no wire follows the drive train.

**Shaft geometry.** Each G10 shaft runs from coupler A (on the motor, in the utility layer)
through the shelf bushing to coupler B under the deck. Since Rev 3.7c that is about 4.8″ (roller)
and 6.4″ (C1, C2). The shelf bushing supports each shaft, so the longest free span — bushing to
coupler B on C1 / C2 — is ~5.1″, under the 6″ limit: no intermediate bearing block (§3.1). Windup at
0.42 N·m over 6.4″: ~1.2°. Each capacitor mounts
**variable (shaft) end down**, clamped to the deck, and its shaft passes through a clearance hole
in the deck. Make the hole generous with a rounded edge so it is not a creepage path.

**Why 5.50″ standoffs (Rev 3.7c).** The input choke stands under the deck at the shelf crossing
(§6). Its 5-core stack is 3.47″ tall with the coax arcing over the faces, and it keeps ≥ 0.5″ to the
grounded shelf and to the deck. Four cores needed 2.95″ against the 2.50″ left under a 3.50″ deck.
The 5.50″ standoff leaves the choke 0.94″ / 1.09″ and room for airflow. Two side effects:
- **Creepage grows.** The hot capacitor shaft tips hang ~0.75″ below the deck, so their creepage to
  the shelf rises from 2.75″ to 4.75″ (≥ 2″ rule, §5.3a).
- **Deck capacitance falls** to ≈ 20 pF (§2.2).

The roller shaft is at deck potential (§5.3a), so it needs only the deck's own clearance. *The
2.50″ → 3.50″ reasoning is kept in §11.12.*

**Still open with this layout:** the thermal re-check (§8, §9 item 30a) and the cardboard mock-up
(§9 item 5). Top-panel coupling and balance are re-estimated in §2.2.

> **Rev 3.7a — enclosure detailed (TUNER-E-200 to E-211, Appendix B).** Decisions taken with the
> owner and drawn from the parametric model (`cad/enclosure.py`, interference-checked
> against the roller, caps, deck and all three drive trains):
>
> - **Wall mount**, upright, rear flush on the garage wall below the entry panel, on two
>   2 × 2 × 3/16″ L-flanges bolted through the side panels into the rear posts, lagged (3/8″) into
>   a ¾″ plywood backer across the studs (the flange slots land 18″ apart, not on 16″ studs).
> - **Front service:** the front upper panel is the **RF-bay service panel**; the front lower is the
>   face of a **control cassette** that slides out on rails and carries the UI, control board,
>   24 V supply and DC-DCs. Behind it a **removable bulkhead** of pi-filtered connectors (§7.3);
>   behind that each **motor axis module** (motor, coupler A, encoder takeoff on a bracket hung
>   from the shelf) drops and slides out the front after loosening coupler A's G10 clamp.
> - **Sampler fixed** at the rear on its own baseplate, serviced through the left lower panel (fixed
>   because the Rev 3.7a 4.25″ choke could not pass a ~4″ module opening; that choke is gone — the
>   Rev 3.7c choke stands in the RF bay, §6).
> - **Chambers re-centered under the motors:** Control 3.10″, Motors 7.75″, Sampler 4.86″. The
>   **cap column moves 0.875″ forward on the deck** (it had 1.75″ of depth slack) so both cap
>   motors sit inside the motor chamber (~0.14″ each end); the column sits at the deck edge
>   (Rev 3.7b, deck plan above).
> - **I/O:** all low-voltage I/O through the **floor**; the balanced output leaves through the
>   **fixed top**, feedthroughs parallel to the wall near the rear (§8D). Side panels split at
>   the shelf; conductive-elastomer gaskets (G-1).
> - Cassette parts must be **≤ 3.92″ tall** to pass the front opening (§8A.1, §9 item 39).
> - Aluminum ~28 lb before electronics (24.00″ box, Rev 3.7c).

*The Rev 3.3–3.6 side-column layout (16 × 16 × 12″, spine and sub-walls) is superseded — see §11.1.*

### 3.1 Shaft geometry

In the vertical stack each G10 shaft is ~4.8″ (roller) or ~6.4″ (C1, C2) since the Rev 3.7c deck
raise (§3.0). The shelf bushing supports it, so the longest free span is ~5.1″. The windup figures
below still bound it.

Worst-case torsional windup, 0.375″ solid G10 at the 0.4 N·m operating torque of the vacuum
capacitor mechanism, `J = πd⁴/32 = 8.08e-10 m⁴`, G ≈ 4.0 GPa:

| Span | Windup θ = TL/GJ | ΔC at 0.075 pF/deg |
|:--|--:|--:|
| 5″ | 0.90° | 0.068 pF |
| 8″ | 1.44° | 0.108 pF |
| 10″ | 1.80° | 0.135 pF |

Negligible against a 60 pF variable span in every case. **Requirement:** any shaft over 6″ free
span gets an **intermediate G10 bearing block** — the constraint is sag and whip, not windup.

### 3.2 HV clearance — codified

| Requirement | Value |
|:--|--:|
| Minimum air clearance, any RF conductor or floating-deck edge to grounded chassis | **1.50″ (38 mm)** |
| Floating sub-deck standoff height (steatite or G10 pillars) | **5.50″** (Rev 3.7c; was 3.50″) |
| Lateral clearance, deck edge to side and rear walls | **≥ 2.50″** |
| Clearance, vacuum caps (3.75″) and roller (5.40″ OD, 5.50″ end plate) to any wall | **≥ 2.25″** (roller: 2.61″ side, 3.73″ front, 3.70″ top — §5.3a) |
| Edge radius on all HV conductors, busbars, lugs (corona suppression) | **≥ 1/16″** |

Standoff height is **5.50″ uniformly** across all sections, cut lists, and drawings.
Hot-to-hot spacing between elements on the deck: **≥ 1.50″**.

In the vertical stack, "walls" above means the RF bay side walls, the grounded shelf and the
top panel. Capacitor shaft tips hang below the deck toward the shelf; keep ≥ 2″ creepage along the
Delrin coupler and G10 shaft from tip to shelf bushing (4.75″ at 5.50″ standoffs; roller 4.37″,
TUNER-L-109). The input choke under the deck keeps ≥ 0.5″ to the shelf and the deck, and spans
deck-to-chassis potential end to end (§6).

> **Before cutting metal:** mock the RF bay up in cardboard with the actual components. The
> clearances above are necessary, not sufficient — final placement has not been proven in three
> dimensions.

---

## Section 4 — Materials and Cut List

*The 16 × 16 × 12″ side-column cut list, nesting, frame and BeCu gasket are superseded — see §11.2.*

**Sheet:** 5052-H32 aluminum — chosen over 6061-T6 for formability; it bends 90° without the
cracking 6061-T6 exhibits at tight radii.

**Box:** 16.00″ W × 16.00″ D × **24.00″ H** (Rev 3.7c; §3.0 height closure), wall-mounted vertical
stack. **Cut list, nesting and frame are on the drawings, not tabulated here:** **TUNER-E-201**
(6061-T6 angle cut list), **E-202 to E-209** (panels with cutouts and fastener patterns, small
parts), **E-210** (parts list and hardware counts) and **E-211** (nesting); stock quantities in
§10.11. Confirm every panel height and stock quantity against the E-sheets regenerated for the
24.00″ box (Rev 3.7c) before ordering.

**Assembly — bolted, not welded.** Continuous TIG seams across 16″ of 0.081″ aluminum cause severe
thermal warping and oil-canning, and seal the RF bay behind a permanent wall.


- **Frame junctions (TUNER-E-201, Rev 3.7c).**
  - **Clip:** each of the 16 ring-to-post junctions takes a 1-1/2 × 1-1/2 × 1/8 × 7/8″ clip, nested in
    the post's inside corner between the ring flange and the leg edges.
  - **Fasteners:** per wall, one #6-32 flat head (82°, flush outside) goes into the post at 0.55″ from
    the corner and one into the ring member at 1.35″, each with a nyloc inside — 60 in all.
  - **Faces:** outer faces stay flush for the panels and gasket.
  - **Cassette corners:** at the cassette rings' four front corners the clip's front leg stops at the
    post, because the tray slides past. Their 1/2″ front members ride on the floor and shelf screws.
- **Bulkhead and partition mounting (TUNER-E-208, Rev 3.7c).**
  - **Clips:** each 12 ga plate is held by eight 1/2 × 1/2 × 1/8 × 1.0″ clip angles, four at the floor
    and four at the shelf. Floor legs take 8-32 up through the floor and shelf legs 8-32 down from the
    RF bay, each with a nyloc on the clip.
  - **Bulkhead (removable):** its clips sit on its motor side, with tapped plate legs. It unscrews from
    the control side and comes out the front without touching them.
  - **Partition (fixed):** floor clips on its motor side, shelf clips on its sampler side, through holes
    with nylocs.
  - **Positions:** in E-208's table. They clear the axis modules, the connector plugs and harnesses,
    the sampler baseplate and the driver board (interference-checked). Match-drill the plates, floor
    and shelf through the clips.
  - **No side clips:** the earlier "to floor, shelf and sides" dropped the sides. The lower side panels
    are removable, and between the rings there is no frame member to land on.
- 8-32 stainless button-head screws into rivnuts in the frame flanges, pattern per **TUNER-E-210**
  (344 holes, Rev 3.7c).
  - **Corners:** every row starts 2.00″ from a corner and skips the clip bands. Every hole lands on frame
    metal — the floor and top panels' corner holes used to fall in the 1″ corner squares with nothing
    behind them — and no rivnut sits behind a clip. `enclosure.py` checks both. The earlier rule of 1.75″ centers is far inside λ/20 at 30 MHz (19.7″), so the
  pattern is more than sufficient for HF RF tightness
- **Conductive-elastomer gasket** on every frame flange under a panel and on both faces of the
  shelf (G-1, §8E.6) — seals RF and dust in one part while keeping the RF bay serviceable
- Shielding effectiveness: confirm for the chosen elastomer; the >85 dB HF figure of earlier
  revisions was stated for BeCu finger stock (§11.2)
- Bolting also avoids the **40–50% HAZ strength loss** welded 6061-T6 suffers, preserving full T6 temper

*If any welding is done on 5052 sheet: 5356 filler, pure argon, 4–5 s post-flow.*

---

## Section 5 — Capacitors and Inductor (As Measured)

Every value here is from the parts in hand, measured, not from a catalog.

### 5.1 Vacuum variables — existing Jennings UCSX, 20–675 pF / 10 kV

> **Rev 3.7 correction — voltage margins were against the wrong rating.** The Jennings model
> suffix (-7.5, -10, -15) is the **peak test voltage**. The RF **peak working voltage** is 60% of
> it (Jennings catalog, rating tables): 4.5 kV for -7.5, **6 kV for -10**, **9 kV for -15**. Every
> margin in Rev 3.4–3.6 (1.36×, 1.49×, 1.69×, "~8.9 kV derated") was taken against the 10 kV test
> figure. On the working-voltage basis, from the Rev 3.6 `cap_demand.py` run:
>
> | Position, part | Worst V pk @ 1500 W | Margin @ 1500 W | Margin @ 1100 W |
> |:--|--:|--:|--:|
> | C1, UCSX-740-10 (6 kV working) | 6.54 kV | **0.92×** | 1.07× |
> | **C1, 15 kV-class (9 kV working)** | 6.54 kV | **1.38×** | 1.61× |
> | **C2, UCSX-740-10 (6 kV working)** | 2.40 kV | **2.50×** | 2.9× |
>
> **Placement:** the UCSX-740-10 in hand goes to **C2**. **C1 is a purchased 15 kV-class part:**
>
> | C1 requirement | Value | Basis |
> |:--|:--|:--|
> | Minimum C | ≤ ~25–30 pF | A 40 pF minimum misses 10 m @ 28.000 at nominal feeder; 12 m too at some lengths |
> | Maximum C | ≥ 500 pF | 20–500 pF matched 27/27 at 39–41 ft and VF 0.93–0.97 |
> | Peak working voltage | ≥ 9 kV (15 kV test) | 6.54 kV worst case → 1.38× |
> | RF current | ≥ 6 A | 5.5 A RMS input current at 1500 W |
>
> Candidates: **UCSX-700-15S** (25–700 pF, 70 A, 9.62″ × 3.75″ glass, 3.7 in·lb; surplus units
> may be marked **"CB-154, 15,000 V"** on the body) or **CVDD-500-15S** (20–500 pF, 95 A,
> 7.53″ × 3.44″ ceramic, 1.8 in·lb). Both fit the §3.0 vertical stack. A 40–600 pF CADA-600-15S
> does not meet the minimum-C requirement.
>
> **UCSX-740-10, measured:** 3.75″ dia × 7.0″ long, with an OEM drive gear on the shaft. Shorter
> than the catalog UCSX-700 (9.62″), so it is an OEM variant; confirm whether 7.0″ includes the
> shaft and gear. The gear comes off for the Oldham coupler (§7.1a); do not drill the shaft.

*The KP1-4 in hand is a spare, not used (§5.1a; its analysis as C2 is in §11.3).*

**The 85 pF travel clamp introduced in Rev 3.2 is removed.** It existed to dodge a 9.5 kV stress
figure that the real NEC model shows does not occur. Both capacitors mesh freely across their
full range.

**Capacitance demand — recalculated and archived** (`nec/cap_demand.py`, Rev 3.6).

*Method.* NEC-2 feedpoint impedances at the 27 band edges (`zant_edges.json`, nominal geometry
apex 37.5 ft / ends 10 ft) are transformed through a lossless 600 Ω feeder, 40 ft, VF 0.95. At each
point the T network is solved in closed form (tnet.py's equations) on a 4,000-step log grid of L
across the roller range **0.20–34.40 µH** (the run used the Rev 3.6 roller-plus-link range, which is
the same range as the single 34 µH roller of §5.3a), keeping every solution with C1 in
20–675 pF and C2 in the range under test. Of those, the one with the **lowest roller current** is
taken as the operating point, since roller loss dominates (§1.7). Voltages are peak at 1500 W.

```
Coverage, bare Jennings C2 (20–675 pF)     : 27/27
Smallest C2 that reaches a match, worst pt : 270 pF  (160 m @ 1.800; 192 @ 1.900, 145 @ 2.000,
                                                      ≤ 24 pF on every other band)
Bare-Jennings coverage, 39–41 ft, VF 0.93–0.97 : 27/27 (42 ft @ VF 0.93 misses 10 m @ 29.700 only)
```

**Why earlier figures disagreed:** the lowest-loss T solution always runs C2 to the top of whatever
range it is given, so the 666 / 830 pF figures of earlier revisions were where the optimizer parks,
not requirements (§11.3). **The real requirement is the smallest C2 that matches, ≤ 270 pF.**

**Consequence of running bare (pad deleted, Rev 3.7b; §5.2).** At 160 m @ 1.800 MHz the roller
carries 18.4 A and dissipates **≈ 341 W at Q = 250 (~568 W at Q = 150)**; the 1.800–1.850 MHz derate
(§1.7.1) is **≈ 530 W**; C1 sees **6.54 kV pk**, **1.38×** against a 15 kV-class C1 (9 kV working);
C2 sees 2.40 kV pk, **2.50×**. The pad would have saved ~8% of roller loss on 160 m only; the
padded comparison is in §11.4.

**Demand under the lowest-loss policy, bare** (cf. §1.3, which used the geometry envelope):

| Quantity | Value |
|:--|--:|
| Coverage | **27/27** with either 15 kV C1; feeder 39–42 ft / VF 0.93–0.97: 26–27/27 (only 10 m 29.700 drops, at the extremes) |
| C1 range used | **25 – 286 pF** — both candidates cover; the **CVDD-500-15S**'s 20 pF minimum gives margin at 10 m 29.700, where C1 reaches 25 pF (the UCSX-700-15S's floor) |
| C2 range used | up to 675 pF — policy-driven, see above; ≤ 270 pF needed |
| L range | **0.46 – 22.3 µH required** (22.2 µH at 1.800 MHz). The run uses up to 32.4 µH on 40 m only because the policy picks the largest L there; 27/27 still holds with the roller capped at 23 µH. *The 31.70 µH carried since Rev 3.4 was this policy artifact, not a requirement* |
| Max V_C1 / V_C2, peak | 6.54 / 2.41 kV (1.38× / 2.49× to working) |
| Max V_L, peak | **6.55 kV pk (4.63 kV RMS)** at 1.800 MHz |
| Max roller current | 18.4 A RMS (160 m @ 1.800) |

*Limits of this run:* nominal geometry only (the §1.3 envelope across apex 35–40 ft / ends 6–15 ft
moved results "a few percent" and was not archived); lossless network and feeder; Rev 3.4's
mesh-dependent withstand curve is not re-derived.

*Rev 3.4 figures (26/27, 666 / 830 pF, 5,267 V) — superseded, see §11.3.*

### 5.1a KP1-4 (20–1000 pF / 10 kV) — spare, not used

In hand as a spare (DECISION C-1, §10.14). Its datasheet analysis as C2 (Rev 3.5–3.6) is in §11.3.

### 5.1b Acceptance test — both variables were bought used

The UCSX-740-10 is used and untested, and C1 may be bought used. Before assembly each passes, in order: mechanical inspection,
capacitance range, insulation sweep, glow test (any glass-envelope part — e.g. a UCSX-700-15S in C1), DC hi-pot at min and max
mesh, and a staged on-air test. *Rev 3.7 hi-pot targets:* **C1 (15 kV-class) ~10 kV** (1.5× the
6.54 kV worst case, below its 15 kV test rating); **C2 (UCSX-740-10) 6 kV** (its working rating;
2.5× the 2.40 kV C2 duty, below its 10 kV test rating). Rev 3.5's ~9.2 kV target assumed a 10 kV
part in C1 and would sit at 92% of that part's test rating.
Procedure, pass/fail criteria and test log: `doc/vacuum-cap-testing.md`. §9 item 26.

**Lead-screw re-grease.** Any used cap carries decades-old grease on the drive screw — the
UCSX-740-10, and C1 if bought used. The spare KP1-4 also has old grease packed in the cavity
inside the bellows. Strip it mechanically, not by
flooding with solvent, and re-grease with a thin film of a light, **non-tacky, non-conductive**
synthetic (PTFE-fortified, e.g. Super Lube). No graphite or MoS₂: the screw sits at or near
terminal potential. No silicone: it creeps onto the envelope and becomes a tracking path. No
tackified greases ("red and tacky"): they add drag. Measure drive torque before and after; the measured
figure replaces the datasheet value in the stepper and shaft sizing check. Repeat the glow test
after cleaning, since handling the bellows is the one step here that can damage the vacuum.

### 5.2 Output pad — deleted (Rev 3.7b)

No pad doorknob and no pad relay. The bare C2 covers all 27 band edges (§5.1); the cost is ~8% more
roller loss on 160 m only (§5.1, §1.7.1). History — the Rev 3.3 4-bit array and the Rev 3.4–3.7a
200 pF pad — is in §11.4.

### 5.3 Harris 492-0309-000 roller (in hand) — spare, not used

DECISION R-1 = C: the homebuilt roller (§5.3a) is the tank inductor. The Harris / 229-203-class
roller in hand (0.20–24.40 µH, 5–10 A, end plate broken) is kept as a spare; its measurements and
rating are in §11.5.

### 5.3a Homebuilt roller — Ultem rib cage, #4 solid (DECISION R-1 = C)

**Status: design, not built.** The structure follows AB6WP's homebuilt roller (qsl.net/ab6wp),
rebuilt for 18.4 A and up to 6.6 kV RMS. His PVC form was a 300 W design and does not scale: PVC has high
loss (tan δ ~0.01–0.02), softens near 70 °C and gives off HCl if it scorches.

**Electrical target** — a **single roller, no series link** (§5.4 deleted)

| Parameter | Value | Basis |
|:--|--:|:--|
| Maximum inductance | **≥ 22.3 µH installed required**; built at **34 µH** free air (≈ 32.4 installed): ~40% margin over the 23.1 µH worst case (feeder 39–42 ft, VF 0.93–0.97), kept for build tolerance and other antennas — §9 item 47 | §5.1 / §9 item 45: 22.2 µH at 1.800 MHz is the only point above ~22 µH |
| Minimum inductance | ≤ 0.46 µH | 10 m demand; one turn ≈ 0.28 µH, so ~2 turns in |
| Current | **18.4 A RMS** | §1.2b, 160 m @ 1.800 MHz |
| Voltage across winding | **4.63 kV RMS (6.55 kV pk)** across the turns in use at 1.800 MHz | §9 item 45: 18.4 A × X at 22.2 µH. Turns beyond the wheel float above that by mutual coupling — keep the full-winding clearances |
| Turn-to-turn voltage | ≈ 300 V RMS | 4.63 kV over the ~15 turns in use at 1.800 MHz, across ~0.13″ of air — comfortable |
| Taper | **Linear (uniform pitch)** | Stepper resolves ~0.001 µH/step; a log taper needs more turns and a longer form for the same inductance (~30 turns over ~12″ at 22 µH) |

**Winding**

| Parameter | Value |
|:--|--:|
| Conductor | **#4 AWG solid copper (0.204″)**, annealed, silver-plated |
| Pitch | **3 TPI (0.333″)** — ~0.13″ air between turns, room for the wheel flanges |
| Diameter | ≈ 5.0″ at notch bottom, **5.20″ to wire center** (coil OD 5.40″) |
| Turns | **22** wound (Wheeler: 33.8 µH free air); **notched for 24** — 2 spare turns ≈ +3.4 µH if the measured coil is short |
| Winding length | ≈ 7.33″ (22 turns) |
| Wire length / mass | ≈ 30 ft wound, ~32 ft with leads, ≈ 4.0 lb; rotating inertia ≈ 30 lb·in² (estimate) |

Wheeler's figure is for the coil end to end; AB6WP measured 27% under his calculation on his form.
**Measure before cutting the wire to length**, measure the wound helix again before final assembly,
and use the spare notches if short.

*Why #4 over 3/16″ tubing:* electrically equivalent (skin depth at 1.8 MHz is ~0.002″; #4 has ~8%
less RF resistance from its larger surface). #4 has 2.2× the copper section to conduct heat away
from the wheel contact (the hottest point in any roller), is 1.8× stiffer, cannot kink, and
terminates directly. Tubing halves rotor mass and is acceptable if a proper tubing bender is used.

**Form — skeleton rib cage, not a solid cylinder**

Ribs run **axially** (parallel to the shaft), standing radially on edge. The wire sits in a notch on
each rib and is open air everywhere else — minimum dielectric in the field and full blower access.

| Part | Qty | Material | Size |
|:--|--:|:--|:--|
| Rib | 10 | Ultem 1000, 3/8″ plate | 3/8″ thick, **8.547″ span** between end discs plus end tabs; depth and notch layout per TUNER-L-101 |
| End disc | 2 | Ultem 1000, ½″ plate | **Ø5.75″**; 10 radial slots for rib tabs; bearing hub; wire terminal post |
| Center hub | 1 | Ultem 1000 (or PTFE) | **Ø3.25″**, 10 slots ⅛″ deep keying the rib inner edges; on the shaft at mid-span |
| Tie rod | 4 | Ultem 1000, 3/8″ rod | **9.527″**; clamp the end discs; inside the rib circle, clear of the wire |

**Rib notches:** round-bottomed, **R0.110, 0.155″ deep**, at 0.333″ pitch, corners radiused. The rib
is flat but the wire curves through its 3/8″ thickness and climbs the helix, so at the rib faces it
sits slightly lower and off-center; a shallower R0.105 × 0.140 notch does not let it seat. Each rib's
notches also shift by pitch ÷ rib count (0.0333″ with 10 ribs) from its neighbor (helix stagger),
which adds 0.30″ to the span.
The rib edge must sit **about 1/16″ below the top of the wire**: the coil rotates under a fixed wheel,
so the wheel crosses every rib on every turn, and a rib flush with the wire makes the contact chatter.

**Rib geometry:** ten 3/8″ ribs would touch only at ~0.60″ radius; at 5.2″ they key into the Ø3.25″
center hub well outside that, so crowding no longer limits rib depth (per TUNER-L-101).

**Stiffness — the center hub is required, not optional.** Ultem's flexural modulus is ~480 ksi
(~80% retained at 150 °C). Winding tension presses each rib with ~0.62× the turn tension per turn
(10 ribs). Scaled from the Rev 3.6 figures (3/8″ × 1″ ribs, 8 ribs, ~9.7″ span) to ten ribs on the
8.547″ span, 5 lb residual tension sags a rib ~0.01″ (ends clamped) to ~0.04″ (ends pinned) with end
support only; the center hub halves the span and brings sag to ~0.0025″ even pinned. The wheel
spring itself is negligible (rib < 0.005″; #4 between ribs < 0.0001″). Bending stress stays under
4 ksi, so creep is not a concern. Re-check in `roller.py` if the rib section changes.

**Pre-form the wire round. Do not wind it tight onto the cage.** Wound under tension, wire pulls
straight between ribs into a polygon, and the wheel rides in and out by r(1 − cos π/n) at r = 2.6″:
0.20″ (8 ribs), **0.13″ (10)**, 0.09″ (12). Pre-forming also cuts the rib load ~5×.

1. Anneal the #4 (dull red, air cool).
2. Wind on a mandrel 10–15% under the finished ID (wind a 2–3 turn test piece first to measure
   springback), anchored through a cross-hole, fed through a rag in a vise for tension (W3JIP,
   QST Aug 1997).
3. Thread the formed helix into the open notches like a nut onto a screw.
4. Lock each turn at each rib with a small dab of **neutral-cure electronic RTV silicone to
   MIL-A-46146** (DOWSIL 3145 or Momentive RTV162), or PTFE lacing. *Rev 3.7a:* not ceramic
   cement — it is rigid across a ~3× Cu/Ultem CTE mismatch, porous (moisture, tracking) and lossy
   in the field. Not acetoxy RTV either (acetic acid corrodes copper and tarnishes silver), nor
   epoxy (tan δ 0.01–0.03, carbonizes). Dab only; do not fill the notch. Clean with IPA.
5. Caliper the finished coil for roundness and the wire for ovality before fitting the wheel.

**Material choices — and what is excluded**

| Material | tan δ (~1 MHz) | Max temp | Use |
|:--|--:|--:|:--|
| **Ultem 1000 (PEI)** | ~0.0013 | ~170 °C | **Ribs, discs, hub, tie rods** |
| PEEK | ~0.003 | ~250 °C | Equivalent substitute at 2–3× cost |
| PTFE | ~0.0002 | 260 °C | Center hub only (compression); cold-flows under wire/wheel load |
| Steatite, fired lava, Macor | ~0.001–0.005 | > 800 °C | Solid grooved form alternative (below) |
| Phenolic / Micarta | 0.03–0.06 | ~120 °C | **Out of the RF field only** (motor mount, encoder bracket). ~35–80× Ultem's dielectric heating, absorbs moisture, carbonizes into a conductive track |
| Delrin, polycarbonate, acrylic, PVC, G-10 | 0.005–0.02 | 60–130 °C | **Not in the coil** |

Any plastic of unknown pedigree near the coil gets the microwave screen first: 30–60 s beside a cup
of water; if it comes out warm, it is lossy.

*Solid-form alternative:* machine unfired **Grade A Lava** (McMaster 8479K79, 3½″ × 9½″ rod),
bore it, single-point the groove, then kiln-fire (~1,093 °C; obtain the supplier's schedule)
allowing **1–2% shrinkage** — test-fire an offcut first. Machine wet or under extraction; the SDS
lists respirable-dust hazards. Fired steatite tubes can only be diamond-ground and need ≥ ¼″ wall.

**Contact system — the hard part**

The form is the easy part of a roller; the rotating contact decides the current rating. Builders
consistently identify a low-resistance, dead-spot-free high-current contact as the obstacle.

- **Wheel:** silver-plated brass/copper, groove radius matched to 0.204″ wire; strong spring.
  Surplus Sales stocks wheel/bar assemblies and silver wheels as a starting point.
- **Current path from wheel to bus rod:** wide, flat, silver-plated shoe or braid. **No current
  through the axle or the spring** — AB6WP flags exactly those as his loss points.
- **Rotating-end connection:** BeCu spring fingers on a silver-plated shaft collar — see below.
- **End stops:** hard stops at both ends of the winding (as §7.2), independent of firmware.

> **Inspect the roller wheel contact surface before assembly.** At 18.4 A RMS on 160 m, oxidation
> or pitting on the wheel or its bus rod localizes into heat. This is the one failure mode that
> matters on any roller, and it is far more consequential than anything in the inductance spec.

**Shaft and cold-end connection**

**The shaft is cold.** The roller is the T's shunt element, junction to floating deck. The coil's
**deck end is bonded to the shaft** at end disc A, so the shaft is the lowest-potential part of the
roller and the **wheel and bus rod are the hot terminal**. The §7.1 drive train (G10 shaft, Delrin
Oldham) is unchanged and simply sees less voltage on this axis than on the capacitor axes.

**Metal on the axis is acceptable if it is non-magnetic.** The axial field inside the coil induces
surface eddy currents in the shaft. At the 160 m worst case (~2,200 A/m inside the coil):

| Shaft | Eddy loss | ΔL | Windup, 1.26 N·m over ~13″ |
|:--|--:|:--|--:|
| **Brass C360, ½″** | **~0.03 W** | −1.8% (calibrated out) | **0.3°** |
| Copper C110 | ~0.015 W | −1.8% | 0.2° |
| 304 stainless | ~0.1 W | −1.8% | 0.15° |
| Carbon steel, 416 / 17-4 stainless | ~0.5 W+ | concentrates flux, shifts L | 0.15° |
| G10 | — | — | ~2.5° |
| Ultem | — | — | ~8.5° |

Loss is negligible against ~341 W of roller loss at Q = 250 for any non-magnetic metal. **Plastic
fails on windup**, not loss: windup reverses with direction, so it behaves as backlash the
motor-side encoder (§7.1) cannot see. **Brass** is chosen over stainless because the shaft also
carries the cold-end current, and it machines and silver-plates easily. Aluminum oxidizes and is
hard to plate where the contact runs.

Field check: hot turns at r ≈ 2.7″ around a cold ½″ shaft, with 9.3 kV pk across the full winding,
give ~6.2 kV/cm peak at the shaft surface against ~30 kV/cm breakdown, ~5× margin (the larger radius
offsets most of the higher voltage). §3.2's 2.25″ rule governs component-to-wall, not spacing inside
a component.

```
 Oldham   bearing   contact   end disc A                        end disc B   bearing
  stub    bracket   collar    (coil cold end         coil         (open end,  bracket
          (Ultem)   + fingers  clamped to shaft)   8.55″ span      terminal post)  (Ultem)
 ──┤├──────╫────────▓▓────────┃══════════════════════════════════┃────────╫──
   1″      ¾″       1″         ½″                                 ½″       ¾″
```

| Feature | Specification |
|:--|:--|
| Stock | ½″ C360 brass, **12.875″** shaft (TUNER-L-104) |
| Through the coil | ½″. End discs slip on it; **one 1/8″ brass cross-pin through the center hub** is the cage's only torque and axial key, so the Ultem cage grows freely both ways from mid-span |
| Cold-end bond | Silver-plated brass split clamp collar at disc A; #4 coil end lugged to it. A set screw is never the only contact |
| **Rotating contact** | Silver-plated collar outboard of disc A, **4–6 BeCu spring fingers** in parallel to a strap to the deck |
| Bearings | **Insulated:** plain Ultem or PTFE-lined (Rulon) bushings in Ultem end brackets |
| Axial location | Thrust collar each side of one bearing; wheel spring load is radial, axial load small |
| Drive end | Stub into the Delrin Oldham (§7.1a), hub bored ½″, retention per §7.1a |

**The bearings must be insulated from the shaft.** Metal bearings bonded to the deck would sit in
parallel with the fingers and carry part of the 18.4 A through balls or bushing surfaces, which
pits them. Current goes through the fingers only.

Shaft sag under the coil and cage (≈ 4.0 lb of wire) is negligible at the wheel; running vertical,
the rotor weight goes into thrust at bearing A, at the bottom.
The **bus rod is now at full voltage**: mount it on the Ultem end brackets with §3.2 clearance to
everything grounded.

**End plates**

Two **½″ Ultem** plates, **5.50″ across × 7.50″ along the depth** (TUNER-L-102). **Plate A** is at the
bottom, bolted and doweled to the floating deck as the mounting flange (TUNER-L-109); **plate B** is
at the top, carried from plate A on two Ultem frame posts.

| Function | Plate A (bottom, drive / cold end) | Plate B (top, far end) |
|:--|:--|:--|
| Shaft bearing | Yes — **axially fixed** (thrust collars both sides, PTFE washers); takes rotor weight | Yes — **axially free** (sliding fit) for thermal growth |
| Bus rod (hot, up to 9.3 kV pk) | One end | Other end |
| Finger contact block + deck strap | Yes | — |
| Wheel-carriage end stop | Stop collar on bus rod | Stop collar on bus rod |

Creepage from the bus-rod mounting to any cold part on a plate: **≥ 2″** — Ultem's tracking index is
modest; slot the plate if a cold part comes closer. *The horizontal-shaft end-bracket sketch and
dimension table (Rev 3.6) are superseded — see §11.5.*

**Line-bore the plates:** clamp both together and drill and ream the bearing bores and bus-rod
holes in one setup, so they come out coaxial. Dowel plate A so it returns to the same place.

**Bearings**

Duty is light: ~73–220 rpm (22 turns in 6–18 s), a ~4 lb winding plus the cage and a 3–5 lb wheel
spring, and only carriage friction axially. **The Ultem plate is the insulator.** The bearing's outer ring
sits in plastic, so no current can reach the deck through it, and even a steel ball bearing is
acceptable provided nothing metallic bonds its outer ring to the deck.

| Option | Part | For | Against |
|:--|:--|:--|:--|
| **Sealed ball bearing, R8** (½″ × 1⅛″ × 5/16″) — **specified** | Commodity | Lowest drag (helps M-2); negligible play | Sealed grease; steel races, but outside the coil |
| Flanged Rulon J sleeve, ½″ ID | McMaster | Dry-running, no grease in the bay; Rulon J suits a soft brass shaft; flange takes thrust | 0.002–0.004″ clearance (harmless: wheel spring preloads one side) |
| Bore the Ultem directly | — | No parts | High friction and wear on brass |
| Full-ceramic ball bearing | Zirconia / PEEK cage | Wholly non-metallic | Costly; buys nothing, since the plate already insulates |

Press the R8s into reamed bores with a light interference fit, located at A and sliding on the
shaft at B. Use Rulon J instead if zero grease in the RF bay is preferred. **Excluded:** any
bushing with metal or carbon in it — bronze-filled PTFE, steel-backed DU, carbon-filled
"conductive" iglide grades.

**Build target (R-1 = C).** A **34 µH single roller, no series link**: 5.20″ to wire center, #4 solid
at 3 TPI, 22 turns wound (notched for 24), ≈ 7.33″ winding, ten ribs, standing **upright** on the deck
on a vertical shaft, so its length sets box height (§3.0), not deck width. The **fixed R8 bearing (A)
goes at the bottom**, taking rotor weight as well as thrust. Rib notches are not identical: on a
helix each successive rib's notch pattern shifts by pitch ÷ rib count (0.0333″ with 10 ribs).
Dimensions from the parametric model `cad/roller.py` (2026-11-16):

| Part / dimension | Value |
|:--|--:|
| Rib span | 8.547″ |
| End disc | Ø5.75″ |
| Center hub | Ø3.25″ |
| End plates | 5.50″ across × 7.50″ along the depth |
| Plate face to plate face | 10.547″ |
| Overall over the plates | **11.547″** |
| Shaft | 12.875″ |
| Guide rods | 12.297″ |
| Tie rods | 9.527″ |
| Wire | ≈ 30 ft wound, ~32 ft with leads, ≈ 4.0 lb |
| Rotor inertia | ≈ 30 lb·in² (estimate) |

*The side-column width-fit analysis, the coil-diameter table and the earlier 3.5″ / 26-turn and
4.7″ / 18-turn targets (with the 12.5 µH link) are superseded — see §11.5.*

> **Drawing set and end retention.** `cad/roller.py` (model) and `drawings.py` (FreeCAD
> TechDraw) produce sheets TUNER-L-100 to L-109 in `cad/out/` (regenerated 2026-11-16 for the
> 34 µH roller):
> assembly with a section through the wiper, rib, end plates, end disc + hub, rods, wiper,
> exploded view + parts list, end retention, coupler B, and the installation (L-109). The model checks every part pair for
> interference. How each end is held:
>
> | Joint | Method |
> |:--|:--|
> | Rib tab in end-disc slot | **Slip fit** (0.375 in 0.380), tab 0.010″ short of the slot bottom; clamped by the tie rods. No press fit — Ultem is notch-sensitive and grows ~2.8× brass |
> | Disc A to disc B | 4 Ultem tie rods, 0.010″ short each end, #10-24 PEEK flat heads; the 10 ribs (matched set ±0.002″) are the spacers |
> | Cage to shaft | Hub cross-pin only (above); discs slip |
> | Coil cold end | Ring lug, #8-32 brass screw, to a 1.25″ Ag-plated split collar 0.02″ below disc A; the collar's OD is the finger track and its underside the upper thrust face for bearing A |
> | Coil open end | Into disc B's 0.25″ terminal hole, RTV bead |
> | Shaft at plate A | R8 light press; collar above and a split thrust collar below, PTFE washers — axially fixed |
> | Shaft at plate B | R8 light press, inner race slides on the shaft (thermal growth) |
> | Plate A to deck | 4 × #10-24 up through the deck into brass heat-set inserts + 2 × 3/16″ dowels, all ≥ 2″ from the bus rod |
> | Plate B to plate A | Two 3/4″ Ultem frame posts, 1/4-20 each end; the posts set the spacing, rod nuts are snug only |
>
> Wiper (all assumed, §5.3a gives function only): 0.75″ wheel, R0.110 groove **capped at 0.045″
> deep** so its flanges clear the rib tops; fork slides radially in a carriage that rides the bus
> rod and an Ultem guide rod (12.297″). The roller is **10.547″ between plate faces** and **11.547″
> over the plates**, which sets the §3.0 height closure. Coupler B is drawn as reference on
> L-108 (§7.1a dimensions, roll-pinned hubs).
>
> **Clearance to the enclosure, vertical stack.** Metal across a coil end carries an opposing image
> current, lowering L and Q. Installed clearances (TUNER-L-109), 24.00″ box (Rev 3.7c):
>
> | Coil / part to… | Distance | HV (§3.2) | Magnetic (1 D ends, ½ D sides) |
> |:--|--:|:--|:--|
> | Deck top to first turn (cold-end potential) | 1.94″ | n/a | short: ≈ −3 to −5%, every setting (active turns start at the bottom) |
> | Last turn to top panel (grounded) | 3.70″ | ✓ (≥ 2.25″) | ≈ −1%, only with most turns in |
> | Coil to side wall | 2.61″ | ✓ | ≈ ½ D ✓ |
> | Coil to front wall | 3.73″ | ✓ | ✓ |
> | Coil to C1/C2 envelopes | 1.55″ across the width (1.87″ diagonal) | ✓ (≥ 1.5″ hot-to-hot) | — |
> | Bus rod to deck (air) | 1.56″ | ✓ | — |
> | Bus rod to top panel | 2.69″ | ✓ | — |
> | Plate B top to top panel | 1.63″ | — | — |
> | Brass shaft tip to shelf (creepage) | 4.37″ (2.37″ at 3.50″ standoffs) | ✓ (≥ 2″) | — |
> | Deck underside to shelf | 5.50″ (input choke between, §6) | ✓ | — |
>
> Net: **Wheeler 33.8 µH free air; deck image loss −3 to −5% gives ≈ 32.3–32.8 µH installed against
> 22.3 µH required** (§9 item 45) — about 45% margin. The two spare notches add ≈ +3.4 µH. **Measure the wound helix before final assembly** — AB6WP measured 27% under Wheeler on
> his form. The remaining shift is measured out in the installed calibration. The bus rod spans only
> the wheel travel, on Ultem pillars; a through-rod would have put its hot ends much closer to the
> deck and the top panel.
>
> **Installation (TUNER-L-109).** Plate A is the mounting flange: it sits flat on the deck,
> 4 × #10-24 SHCS up through deck clearance holes into brass heat-set inserts plus 2 × 3/16″
> dowels. Everything on plate A's underside is recessed — post-screw heads and the pillar's
> PEEK jam nut in counterbores, and the guide rod threads into a **blind** tapped hole — so nothing
> needs a deck clearance hole except the 1.50″ hole for the shaft and thrust collar. Proposed
> location (confirm in the mock-up, §9 item 5): plate A 1.5″ across from the C1/C2 column, which
> sits at the opposite deck edge (§3.0), centered in depth, bus rod toward mid-depth near the C1–C2
> junction. Coil to side wall 2.61″, to front wall 3.73″, to the C1/C2 envelopes 1.55″ across the
> width (1.87″ diagonal; ≥ 1.5″ hot-to-hot). **Isolation:** the brass
> shaft is at deck potential and ends above the grounded shelf; only the G10 shaft crosses
> the shelf (§7.1). Creepage from the brass tip to the shelf bushing is **2.37″** (≥ 2″). It is the
> axial distance between them, since every surface on the path runs along the axis, so it is set by
> how far the brass stub hangs below the deck: keep the stub at 0.65″ below the thrust collar (the
> Oldham hub uses 0.595″). Lengthening an Oldham hub would not add creepage.

**Q target — minimum, not optimum**

Loss in the roller is the reactive power through it divided by Q. On 160 m at 1.800 MHz the bare
network (§5.1) gives ≈ 341 W at Q = 250, i.e. ~85 kVA of reactive power, so Q sets the dominant tank
loss directly:

| Roller Q | Roller loss, 1500 W on 160 m | Share of output |
|--:|--:|--:|
| 100 | ~850 W | 57% |
| 150 (§1.7 pessimistic) | ~568 W | 38% |
| 250 (§1.7 optimistic) | ~341 W | 23% |
| **300 — target** | **~284 W** | **19%** |
| 400 | ~213 W | 14% |
| 600 | ~142 W | 9% |

*Scaled from the bare §5.1 figure; re-estimate after the bare `cap_demand.py` re-run (§9 item 45).*

There is no optimum. Higher Q only reduces loss and contact heating; network bandwidth is set by
the loaded Q of the match (~15.6 on 160 m), not by the coil's. Other bands carry 1.6–10 A, so their
roller loss is tens of watts at any reasonable Q. **Specification: Q ≥ 300 at 1.8 MHz, measured
installed in the bay** (not on the bench). Returns diminish above ~400–500: going from 400 to 600
saves ~71 W, on 160 m only.

Estimated for this coil (34 µH, 5.2″, #4, 22 turns at 3 TPI): X ≈ 251 Ω at 1.800 MHz for the 22.2 µH
in use. *Rev 3.7b NEC model (§9 item 44): copper-only Q ≈ 1,600 at 1.800 MHz over the deck — ≈ 53 W of the
342 W that Q = 250 assumes. The winding is not the loss driver: wheel contact resistance, rib dielectric and
proximity effect (not modeled) set the real Q, which is why the contact system gets the attention.* Resistance and Q: **re-estimate** for this coil (the Rev 3.6 estimate for the 3.7″ /
26-turn coil was ≈ 0.35–0.5 Ω and unloaded Q ≈ 500–700 in free air, 300–500 installed). Surplus #12
tinned rollers (229 class) are typically 150–250.

What sets Q, in order of leverage for this design:

1. **Metal near the coil.** Eddy currents in nearby metal appear as coil loss. Keep metal ≥ ½
   diameter from the sides and **≥ 1 diameter from the ends**, where the flux exits; a plate facing
   an end acts as a shorted turn. The 5052 aluminum deck at ~0.4 D below is tolerable side-on (a
   steel deck would not be). Standing upright puts the first turn **1.94″** over the deck and the
   last turn **3.70″** under the top panel, inside the 1-diameter rule at the deck end: ≈ −3 to −5%
   of L and a similar share of Q from the deck, ≈ −1% from the top panel (§9 item 32). Confirm with
   the installed Q measurement, or raise the roller on an insulating spacer, before relying on
   Q ≥ 300.
2. **Surface.** At 1.8 MHz the current is in the outer ~0.002″, at 28 MHz ~0.0005″. Oxide and
   tarnish sit exactly there. Tin is ~7× the resistivity of copper (small loss on 160 m, noticeable
   on 10 m). Silver improves conductivity only ~3%, but its tarnish stays conductive, so it holds Q
   over years.
3. **Wire and pitch — already near optimum.** Q peaks at a pitch of ~1.4–1.7 wire diameters; 3 TPI
   with #4 is 1.63. Relative Q from skin effect alone (illustrative, Rev 3.6 coil at 22 µH):

   | Variant | Turns | Length | Relative Q |
   |:--|--:|--:|--:|
   | **#4, 3 TPI, 3.7″ (baseline)** | 26 | 8.7″ | **1.00** |
   | #6, 3 TPI | 26 | 8.7″ | 0.79 |
   | #2, 2.5 TPI | 30 | 12.0″ | 1.10 |
   | ¼″ tubing, 2.25 TPI | 32 | 14.2″ | 1.00 |
   | #4, 2.5 TPI (looser) | 30 | 12.0″ | 0.87 |

   Bigger wire only helps if the pitch grows with it, which lengthens the coil and adds turns.
   Tighter pitch gains on wire length but loses more to proximity.
4. **Diameter.** Scaling the whole coil scales Q roughly with size, but at fixed wire and pitch the
   gain is modest: against the 3.7″ baseline, 4.2″ ≈ +4%, 4.7″ ≈ +14%, 6.2″ ≈ +19% (5.2″ lies
   between). A length/diameter of ~1–2 is mildly favorable (this coil: 7.33 / 5.2 ≈ 1.4).
5. **Contacts and dielectric.** Wheel and finger resistance barely move Q (10 mΩ is ~3.4 W at
   18.4 A) but concentrate heat at one point. Ultem ribs are a minor term, mostly on 10 m.

**Commissioning checks (§9 item 27)**

- Measure L end to end and at each turn on the LCR meter — **on the wound helix before final
  assembly**, and again installed; confirm ≥ 34 µH free air (≥ 23 µH needed installed) and ≤ 0.46 µH
  reachable. Use the spare notches if short.
- VNA-sweep the finished roller at several wheel positions for idle-turn resonances (§9 item 44:
  Medhurst estimate SRF ≈ 11 MHz for the full winding), and check for heating on a 10 m carrier.
- Measure breakaway and running torque (feeds DECISION M-2; rotor inertia ≈ 30 lb·in², estimate).
- Heat test on 160 m: key-down at 100 / 300 / 600 W, IR thermometer on the wheel contact, ribs
  and notches. Ribs must stay cool to the touch; any warm rib means dielectric heating. Include
  the shaft finger contact and collar.
- Measure roller Q (§9 item 12) **installed in the bay, RF service panel on**, at the 160 m settings;
  accept at **≥ 300**. The 160 m derate in §1.7.1 depends on it.

**Stock to buy (5.2″ / 22-turn / 34 µH design; sizes from `roller.py` — confirm against
TUNER-L-100 to L-109 before ordering):** 3/8″ Ultem plate for 10 ribs (8.547″ span plus tabs) and
the Ø3.25″ center hub; **½″ Ultem plate** for 2 end plates 5.50″ × 7.50″ and 2 end discs Ø5.75″;
3/8″ Ultem rod for 4 tie rods at 9.527″; Ultem rod for the guide rod (12.297″), frame posts and
bus-rod pillars; **#4 solid bare copper, ~32 ft with leads plus a 2–3 turn test piece**; wheel/bar
hardware; plating supplies; ½″ C360 brass rod for the 12.875″ shaft and collars; BeCu finger stock;
2 × R8 sealed bearings (or Rulon J flanged sleeves); PTFE thrust washers; neutral-cure RTV
(MIL-A-46146).

### 5.4 Series link inductor — deleted (Rev 3.7b)

No link coil and no link relay. The single 34 µH roller (§5.3a) covers the 0.46–22.3 µH requirement alone (§9 item 45). History
in §11.6.

### 5.5 Relay switching — break-before-make

Two relays: the K1/K2 coax relays (Tohtsu CX600N-24, §6B). There are no relays in the RF tank.
Neither may hot-switch:

1. PTT permissive is withdrawn (Section 7.4), dropping the bench-side keying switch
2. Hardware blanking timer enforces **30 ms RF decay** before any coil energizes
3. Relays transition under zero-RF conditions
4. **25 ms** post-switch settling for contact bounce
5. Amplifier keying re-enabled

> K1 and K2 are Tohtsu CX600N-24 coax relays with **no auxiliary contacts** (§9 item 34).
> Confirmation is coil-current sense on each driver channel plus the cal-load RF detector (§6B.2,
> §6B.3a).

*Rev 3.7c — the blanking timer as built (control board, §10.5).* The K1/K2 drivers are fed through a
74HC373 latch. Its enable is the permissive delayed by an RC: when the permissive rises, the latch
closes at once; after the permissive falls, it stays closed until 560 kΩ × 100 nF (C0G) has decayed
past the 74HC14's lower threshold. That takes 39–67 ms over the threshold spread, never under 30 ms.
While the permissive is up, the MCU can command anything and the relays do not move. With the bypass
key on, the permissive is held up, so the relays freeze in place. At power-up the permissive is down,
the latch is open, and the relay commands are pulled low: both relays are off, which is TUNE (§6B.2).

## Section 6 — Input Common-Mode Choke

*Rev 3.7c: a #61 ferrite choke standing in the RF bay, under the deck. It replaces air-core design C in
the sampler chamber; that design, and the reasoning that kept ferrite out of this position until now,
are in §11.11.*

**What it does.** The deck floats. Apart from the deck's own ≈ 20 pF (§2.2), the choke is the only
path from the network common (leg 1) to chassis, so it holds the deck-to-chassis common-mode
voltage: about half the differential output, **up to ≈ 1.48 kV RMS** (40 m, 7.30 MHz). The trim vane
can only balance capacitance, so the choke must present a **higher impedance than the deck's
reactance** on every band (§2.2). Heat below is worked with the whole V_cm across the choke — the
antenna system's common-mode impedance taken as zero, the worst case (§9 item 50).

**Why ferrite.**
- **Coax length is the heat.** The coax through the choke carries the full input power, so its loss
  grows with its length. Design C needed ~36 ft of RG-142B for 45 µH of air-core inductance, which
  meant **40–232 W** of coax loss (160 m derated to 10 m), all inside the sealed sampler chamber.
- **#61 does more with less.** It gives 4× the inductance from a quarter of the coax.
- **#61 holds the voltage reactively.** It is low-loss NiZn (µ ≈ 125, tan δ < 0.005 below ~10 MHz),
  and its large-signal core loss (Fair-Rite Pv data) is ≤ 6 W on any band.
- **The old objection doesn't apply.** §11.11 recorded that kV across ferrite dissipates hundreds of
  watts. That holds for lossy #31, not for #61.

**Adopted:**

| Parameter | Value |
|:--|--:|
| Cores | **5 × Fair-Rite 5961003801 (FT-240-61)** — 61.0 × 35.55 × 12.7 mm, A_L ≈ 172 nH, bonded into one stack |
| Winding | **15 turns RG-400** (M17/128: PTFE, stranded silver-plated center, double braid), one layer |
| Coax | **9.6 ft** with leads (≈ 9.0 ft wound) — order 12 ft |
| Inductance | **192 µH** small-signal; self-resonance ≈ 5.7 MHz at 4 pF winding capacitance |
| Stack | **2.81″ dia × 3.47″** (worst-case core tolerance, coax arcing over each face) |
| Location | RF bay, under the deck at **(−1.5, −1.0)**, between the shelf coax bulkhead and C1; axis vertical |
| Clearances | Winding 0.94″ to the shelf, 1.09″ to the deck; ≥ 0.64″ to every other part (interference-checked) |
| Mount | All insulating: G10 base, standoffs and spider, fiberglass rod (below) |
| Cost | ≈ $94 (cores ~$11 each, RG-400 ~$2.50/ft, mount) |

**Routing.**
- **Chassis side:** sampler → K1 (NC) → W15 → partition adapter X → W17 → shelf coax bulkhead.
  Every shield is grounded at every connector, as it should be.
- **The shelf bulkhead is the choke's chassis end.**
- **W18 is one piece of RG-400:**
  - a short lead from the bulkhead to the bottom of the stack;
  - 15 turns;
  - then from the top of the stack to C1's lower terminal, its shield clamped to the deck.
- **Deck side:** nothing on the deck side of the choke touches chassis (TUNER-E-212, E-215).

*Through Rev 3.7b the choke sat in the sampler chamber, and its deck-side coax crossed adapter X and
the shelf bulkhead — both grounded — which bypassed it (Changes in Rev 3.7c, item 1).*

**Fit, checked against the real turn shape** (`nec/choke_screen.py`):
- **Bore.** One layer against the bore wall. The worst-case bore (34.8 mm, less 0.25 mm of tape)
  holds 18.5 turns in a full ring. 15 turns leave a **69° gap (12.6 mm)** between the first and last
  turn, which differ by the full V_cm; 16 turns is the practical limit (7.6 mm).
- **Bend.** The coax arcs over each core face at a centerline radius of ≈ 8.8 mm (1.8 × OD). The
  core's 12.7 mm face width sets it, not the turn count. That is under the usual 5 × OD static
  guideline, as in every PTFE-coax balun on FT-240 cores. Use RG-400 (stranded center), tape the
  core edges, and do not flex the winding once it is made.
- **Height.** Each face adds ≈ 11.3 mm of arc: 3 cores stand 2.44″, 4 cores 2.95″, 5 cores 3.47″.
  Under the old 3.50″ standoffs only 3 cores fit (2.50″ allowed), so the deck went up 2.00″ (§3.0).

**Mount — nothing metal in or on the winding** (dimensioned on TUNER-E-207 and E-209; the assembled
choke, every turn, is drawn on **TUNER-E-216**):
1. **Stack.** Bond the five cores with thin beads of high-temperature RTV. Wrap the bore and the core
   edges in glass-cloth tape.
2. **Wind.** 15 turns in one layer against the bore wall, with the first-to-last gap facing −X
   (toward the bulkhead and C1). The open center (≥ 0.96″) takes the rod.
3. **Base.**
   - G10 disc, 1/4″ × Ø3.40″.
   - Three G10 standoffs, Ø3/8″ × 5/8″, screwed 8-32 up through the shelf at holes CH1–CH3
     (Ø2.60″ bolt circle, TUNER-E-207).
   - **Nylon** 8-32 flat heads hold the disc to the standoffs, countersunk flush. The bottom
     crossings sit right over them: a metal head there would be a floating electrode beside kV
     turns, and a raised head would dent the coax.
   - Six Ø0.15″ vent holes inside the bore circle let air rise up the bore.
   - A 1/16″ silicone pad sits under the bottom crossings.
4. **Clamp.**
   - 1/2″-13 fiberglass (FRP) threaded rod through the bore center, FRP nuts above and below.
   - A three-arm G10 spider (1/8″) over a silicone pad bears on the top crossings, snug by hand. Its
     open arms leave the crossings in the airflow.
5. **Leads.** The chassis lead leaves the bottom of the stack for the shelf bulkhead (PL-259). The
   deck lead leaves the top for C1, ~3.5″ above the chassis lead. Lace both to the base with PTFE cord.

The assembly weighs ≈ 1.7 lb. It sits in the intake air: the intake straddles the deck, with 2.4″ of
it below the deck's underside (§8).

**Performance** (`nec/choke_screen.py`, output `nec/out/choke_screen_rev37c.txt`; Fair-Rite #61
complex µ and large-signal Pv data in `nec/data/`). The table gives the minimum |Z| in each band
against the deck's reactance at the same frequency. Heat is core + coax at the operating power, with
the full V_cm across the choke:

| Band | \|Z\| at C_w 4 pF | at 2 / 6 pF | Deck X (20.1 pF) | Ratio | Choke heat |
|:--|--:|--:|--:|--:|--:|
| 160 m (1.800, derated) | **2.41 kΩ** | 2.28 / 2.54 kΩ | 4.39 kΩ | **0.55** | 11 W |
| 80 m (3.500) | 6.73 kΩ | 5.19 / 9.56 kΩ | 2.26 kΩ | 3.0 | 28 W |
| 60 m (5.332) | 49.5 kΩ | 11.5 / 21.4 kΩ | 1.48 kΩ | 33 | 28 W |
| 40 m (7.300) | 13.9 kΩ | 50.9 / 6.10 kΩ | 1.08 kΩ | 13 | 36 W |
| 30 m (10.150) | 5.66 kΩ | 20.3 / 3.29 kΩ | 0.78 kΩ | 7.3 | 40 W |
| 20 m (14.350) | 3.25 kΩ | 7.86 / 2.05 kΩ | 0.55 kΩ | 5.9 | 47 W |
| 17 m (18.168) | 2.40 kΩ | 5.29 / 1.55 kΩ | 0.44 kΩ | 5.5 | 53 W |
| 15 m (21.450) | 1.97 kΩ | 4.19 / 1.29 kΩ | 0.37 kΩ | 5.3 | 57 W |
| 12 m (24.990) | 1.66 kΩ | 3.45 / 1.09 kΩ | 0.32 kΩ | 5.2 | 61 W |
| 10 m (29.700) | 1.38 kΩ | 2.82 / 0.91 kΩ | 0.27 kΩ | 5.2 | **69 W** |

- **80 m and up.** Even at 6 pF every band keeps ≥ 3.4× the deck's reactance. Above the ~5.7 MHz
  self-resonance the choke looks like its few pF of winding capacitance — far less than the deck's
  20 pF.
- **160 m stays choke-limited** at 0.55×. For comparison, design C alone was 0.14×, and design C
  with its two-toroid #61 supplement was ≈ 0.5×.
- **The real spec is balance, not this ratio.** §2.2 specifies measured feeder-current imbalance
  ≤ 5%. How close 160 m gets depends on the antenna system's common-mode impedance (§9 item 50), and
  the output CT measures it in service.
- **Choke current.** At the 160 m limit, the worst-case current through the choke is ≈ 0.35 A
  (847 V / 2.41 kΩ at 502 W).

**Heat and flux.**
- **Flux.** Peak flux is 9.2 mT at 160 m (#61 saturates near 230 mT), and core loss is ≤ 6 W on any
  band.
- **The heat is the coax.** About 6.8 W per foot at 1500 W on 10 m — the same per foot as any
  RG-400 / RG-142 run at that power; design C had the same density over 36 ft.
- **Budget.** The total, ≤ 69 W, now counts in the RF-bay budget. The 160 m limits fall to
  502 / 600 / 882 W (§1.7.1, §8); every other band keeps 1500 W.

**Verify it installed (§9 item 49):**
- **VNA sweep**, deck end to chassis, with the choke installed and the deck connected.
  - Expect an impedance peak (parallel resonance) near 5–7 MHz, and |Z| ≥ ~1 kΩ across 10 m.
  - A sharp dip inside any band means the winding capacitance or a lead resonance is not what the
    model assumes: re-dress the leads first, then take off a turn.
- **Thermal check.** Run 1500 W key-down on 28.0 MHz for 10 minutes, with irreversible temperature
  labels (or a thermocouple read right after unkeying) on the bore bundle and the cores.
  - Below ~100 °C is comfortable for PTFE and #61.
  - If it runs hotter, add airflow under the deck before shortening the winding.

**Upgrade path.**
- **Two stacks** don't help. Two 3-core stacks reach the same 160 m impedance as this one with
  13.2 ft of coax and 91 W on 10 m; one taller stack is the efficient shape.
- **More cores** do. Seven cores (4.50″, still inside the 5.50″ standoffs at 0.5″ clearances) reach
  0.80× on 160 m for 84 W on 10 m. Keep that in reserve in case item 50 shows 160 m needs it.

---

## Section 6A — Directional Sampler and Impedance Measurement

Occupies the Sampler chamber with K1/K2 (the input choke moved to the RF bay in Rev 3.7c, §6). This subsystem was named in every prior
revision and specified in none.

### 6A.1 Two jobs, not one

The sampler must deliver two different things, and conflating them is why earlier revisions
specified hardware that could not feed the stated tuning algorithm:

| Job | Needs | Drives |
|:--|:--|:--|
| **Protection and display** | \|V_fwd\|, \|V_ref\| — magnitude only | SWR readout, power readout, fast fault trip |
| **Tuning solution** | R and X separately — magnitude **and phase** | Direct computation of element positions |

A conventional rectified directional coupler delivers only the first. Rectifying the samples
discards the phase relationship that carries the reactance sign, so a scalar bridge cannot
support a computed match — only a search.

### 6A.2 Topology — Stockton (Tandem Match) preferred over Bruene

Both are directional couplers; the Bruene combines a current-transformer sample with a capacitive
voltage-divider sample, while the Stockton uses two matched current transformers.

**Specify the Stockton / Tandem Match.** Its directivity holds better across 1.8–30 MHz, and
directivity is precisely what limits accuracy on a high-SWR load — which is the normal operating
condition for this tuner. A well-built Bruene works, but its capacitive divider is the harder half
to keep flat across a 16:1 frequency span.

Also known as the **Sontheimer coupler**; popularized for amateur use by Grebenkemper, KI6WX,
*QST* January 1987. **Critical construction note from that work: both termination resistors must
equal Z₀.** If they do not, the forward/reflected separation is simply wrong — this is the most
common build error in these couplers.

### 6A.3 Transformer design — derived

Two identical transformers, single-turn primary (the line conductor passing through the core),
N-turn secondary, each terminated in 50 Ω.

Coupling factor `C = 20·log10(N)`; coupled port voltage at 1500 W is `sqrt(50 × 1500)/N = 273.9/N` V RMS.

| N | Coupling | V at coupled port | Power in termination |
|--:|--:|--:|--:|
| 20 | 26.0 dB | 13.7 V | 3.75 W |
| 30 | 29.5 dB | 9.13 V | 1.67 W |
| **40** | **32.0 dB** | **6.85 V** | **0.94 W** |
| 50 | 34.0 dB | 5.48 V | 0.60 W |

**Specify N = 40.** Keeps termination dissipation under 1 W while leaving ample signal.

**Core: FT-82-61** (NiZn, µ ≈ 125) or equivalent. Verification at N = 40:

```
Magnetizing inductance   L = A_L x N^2 = 73 nH x 1600 = 117 uH
Reactance at 1.8 MHz     X_L = 1,321 ohm   -> 26x the 50 ohm termination   OK
Flux density at 1.8 MHz  B = V/(4.44 f N A_e) ~= 8.7 gauss                 negligible
```

The magnetizing reactance must stay well above the termination impedance at the **lowest**
frequency or low-band accuracy degrades; 26:1 is comfortable. Verify A_L against the actual core
datasheet — it varies between vendors and mixes.

**Terminations: 50 Ω non-inductive, 2 W minimum.** Metal film or carbon composition — **never
wirewound**, whose inductance destroys directivity. Both ports get identical parts; under high SWR
the reflected termination sees power comparable to the forward one.

*Rev 3.7c, as built (§10.4):* the terminations are on the measurement board, at the end of two
equal-length RG-316 jumpers from the coupler box. Each port gets 2 × 105 Ω 1 W 2512 thick film in
parallel (52.5 Ω, 2 W). With the detector and AD8302 taps across them, the ports see 50.2 Ω (FWD)
and 50.7 Ω (REF), a return loss above 40 dB.

### 6A.3b Physical placement — all detection happens in the Sampler chamber

**Conflict resolved.** Section 7.3 routes Sampler → Control crossings through 5600 pF filtered D-sub
contacts with a 1 kΩ series resistor — a lowpass with a **28 kHz corner**. An RF sample at 1.8–30 MHz
cannot survive that; it would be attenuated to nothing.

Therefore **both detectors live in the Sampler chamber, next to the coupler.** Only their DC
outputs cross into Control, where the existing feedthrough filtering works exactly as intended.

```
SAMPLER CHAMBER                              | CONTROL CHAMBER
  coupler -> pads -> Schottky detectors ----> | 5600pF + 1k -> ADC   (magnitude)
          -> pads -> AD8302 ----------------> | 5600pF + 1k -> ADC   (V_MAG, V_PHS)
                                              |
  (no RF crosses the bulkhead)                |
```

The AD8302, the Schottky detectors and the frequency path (TLV3501 comparator, 74LVC74 and 74HC4040 prescaler; §10.4) are the active devices in the Sampler chamber; give
them a local regulator fed through a filtered feedthrough, not a shared rail.

*Rev 3.7c:* the coupler is in its own small diecast box (§10.3). Its FWD and REF ports reach the
measurement board on two equal-length RG-316 jumpers, so the board carries low-level circuits only.
The board's AMS1117 runs from the J-S 5600 pF contact. Ferrite beads split its output into an
analog rail (AD8302) and a digital rail (counter).

### 6A.4 Magnitude path — protection and display

Coupled ports → Schottky envelope detectors (HSMS-282x class) → ADC.

*Rev 3.7c, as built (§10.4):*
- **Detector diode:** **1N5711W** (70 V). At 1500 W the port peaks at 9.7 V, so the diode sees ~19 V
  reverse. That is past the HSMS-282x's 15 V breakdown, and far past the 3.8 V of the Rev 3.4
  board's HSMS-2850.
- **Scaling:** a 22 k / 10 k load divides the ~9.4 V peak to 2.9 V for the 3.3 V ADC.
- **Trip:** an LM393 on the reflected detector, open collector, with a 4.7 k pull-up on the
  measurement board. Its threshold is set on a 3296W trimmer: 0.15–2.29 V, about 10–800 W
  reflected. 2:1 at 1500 W is 167 W reflected and reads ~0.92 V at TP1.

Yields forward power, reflected power and SWR. This path drives the **fast protection trip**
(reflected-power threshold → PTT drop, Section 5.5) and must remain functional and independent of
the vector path — protection cannot depend on a computation.

**The trip is a comparator, not an ADC read.** Section 7.4 requires PTT to drop in <2 ms; a
firmware polling loop cannot guarantee that. Put an analog comparator directly on the reflected
detector output, with its threshold set by a DAC or trimmer, and wire its output into the hardware
PTT loop. Firmware reads the same detector through the ADC for display and logging, but never
stands between a fault and the trip.

**Coupler primary.** The single-turn primary *is* the main RF path — the line conductor passes
through both cores. Size it as main-line conductor (≥ the input coax center conductor), keep it
straight through the cores, and do not rely on the core for mechanical support.

### 6A.5 Vector path — the R/X measurement

Coupled ports → ~30 dB resistive taps → **AD8302 gain-and-phase detector**.

```
Coupled port              : +29.7 dBm at 1500 W, +18 dBm at 100 W, +8 dBm at 10 W
AD8302, each input        : -60 to 0 dBm (re 50 ohm); absolute max -3 dBV (~ +10 dBm)
Ratio range               : +/-30 dB, so FWD (INPB, the reference) must sit at -30 dBm or more
                            for |Gamma| = 0.03 (REF 30 dB under FWD) to stay in range
Attenuation               : ~30 dB, a resistive tap on each port (1.62 k into 52.3 ohm)
  -> FWD at the AD8302    : -22 dBm at 10 W, -0.3 dBm at 1500 W; the full ratio range from ~2 W
```

*Corrected Rev 3.7c:* the earlier ~60 dB put the AD8302 mid-range (−30 dBm) at 1500 W. That leaves
REF no room under FWD. After the Rev 3.4 board's 6 dB splitter, FWD read −36 dBm at full power and
−58 dBm at 10 W. The vector path is what tuning uses, at tuning power. FWD therefore belongs near
the top of the range at the highest power, not mid-range. The 30 dB taps also fit on the board; the
external SMA attenuators the 60 dB needed were never in a BOM.

*As built (§10.4; AD8302 datasheet):*
- **Mode:** measurement mode, with MSET tied to VMAG and PSET to VPHS.
- **Inputs:** AC-coupled through 10 nF C0G, because all four input pins sit ~100 mV below VPOS.
- **Offset loop:** f_HP (MHz) = 2 / C (nF), so 100 nF on OFSA/OFSB puts the high-pass at 20 kHz.
- **Output filter:** 10 nF on MFLT/PFLT gives T (ns) = 3.3 × C (pF) = 33 µs.

Port assignment: **INPA = reflected sample, INPB = forward sample.** The AD8302 then reports
magnitude ratio and phase difference of the reflection coefficient directly.

Outputs: `V_MAG` 30 mV/dB about 900 mV; `V_PHS` 10 mV/degree, 1.800 V at 0° falling to 0 V at 180°.

### 6A.6 Extraction math — validated

```
|Gamma|  = 10 ^ ( (V_MAG - 0.900) / 0.600 )
theta    = (1.800 - V_PHS) / 0.010          [degrees, magnitude only]
Gamma    = |Gamma| * exp( j * sign * theta )
Z        = Z0 * (1 + Gamma) / (1 - Gamma)   ->  R + jX
```

Round-trip verified against the tuner's own operating impedances — recovery error is
floating-point only (< 1e-12 %) at every point tested, including 9.6 + j174 (160 m),
2587 + j984 (12 m) and 600 − j1127 (20 m).

**Measurement floor:** the AD8302 bottoms out near −30 dB, so |Γ| below about 0.03 (SWR 1.07)
reads as floor. That is the useful limit and is entirely adequate — at SWR 1.07 the tune is done.

### 6A.7 The sign ambiguity — and how to resolve it

**The AD8302 reports phase magnitude only, 0–180°. It cannot distinguish +θ from −θ.** Verified:

```
Z =  91 +65j  ->  V_MAG = 0.717 V, V_PHS = 1.470 V    (true phase +33 deg)
Z =  91 -65j  ->  V_MAG = 0.717 V, V_PHS = 1.470 V    (true phase -33 deg)
                  identical outputs
```

Inductive and capacitive loads of equal magnitude are indistinguishable. Without resolving this,
the solver cannot tell which way to move. Three options, in order of preference:

1. **Probe-and-observe (recommended, zero extra hardware).** Nudge C2 by a small known step and
   re-read. The direction |Γ| moves disambiguates the sign, because the network's sensitivity
   `d|Γ|/dC2` has opposite sign for inductive versus capacitive loads. Costs one small capacitor
   move at the start of each tune — negligible against roller travel time.
2. **Stored band prior.** The per-band R ± jX is already known from the NEC model in Section 1 and
   stored in EEPROM. Use the modeled sign as the initial hypothesis and confirm by method 1.
   Fastest in practice; relies on the antenna not having changed.
3. **I/Q demodulator instead of the AD8302.** Unambiguous phase over the full 360°, at the cost of
   more complex hardware and calibration. Specify only if 1 and 2 prove inadequate.

### 6A.8 Calibration

Diode detectors are nonlinear and the AD8302 has part-to-part offset, so both paths need
calibrating against known loads, stored in EEPROM:

- **Magnitude path:** known power into a 50 Ω dummy load, several levels per band.
- **Vector path:** 50 Ω (|Γ| = 0 reference), then open and short (|Γ| = 1 at 0° and 180°), then
  at least one known reactive standard per octave. The open and short establish the phase endpoints.
- Calibrate **per band** — both the coupler and the detectors drift across a 16:1 frequency span.
- Calibrate **across the power range, at low power.** Schottky detectors are square-law at low
  level and linear at high level, with a soft transition between; a single-point calibration will
  be wrong at the other end. Take several levels per band and store a curve, not a scale factor.
  Do not attempt calibration at 1500 W — establish the curve at safe power and verify at full
  power with a known dummy load, once.

*Rev 3.7c (firmware, §8B.6):* because the AD8302 gives |θ| only (§6A.7), the vector path cannot be
fitted as a complex one-port. It is calibrated per band as the part's scalar transfer: the open and
short give the 0 dB point and the 0° and 180° ends, the internal load (CAL) gives the directivity
floor, and a resistive standard of known |Γ| can replace the datasheet's 30 mV/dB. Known reactive
standards then check it. The forward detector's curve is taken in watts against a wattmeter.

### 6A.9 Integration with the solver

With R and X in hand, the firmware solves the T-network in closed form rather than searching. The
validated solver is archived in `nec/tnet.py`:

```
XL >= sqrt(50 R)                              feasibility test
X1  = -XL +/- sqrt( R (XL^2/50 - R) )          node reactance
C2  = 1 / (w (X - X1))                         output capacitor
Im(Z2) = XL (X1(X1+XL) + R^2) / (R^2 + (X1+XL)^2)
C1  = 1 / (w Im(Z2))                           input capacitor, requires Im(Z2) > 0
```

Sweep L across the roller range (~0.2–34 µH, the single roller of §5.3a), evaluate every feasible
solution, and take the one with the **lowest
roller current** — the policy §5.1 and the §1.7 loss and derate figures assume. Then drive all
three elements to the computed positions in one move. This is why the absolute encoders of Section 7.1 matter: a computed
solution is only as good as the positions you can actually command.

> **Dependency: every equation above contains ω.** The solver cannot run without knowing the
> operating frequency. See Section 6A.10.

### 6A.10 Frequency determination — required, and not yet specified elsewhere

The network solution, the per-band calibration curves, and the stored starting positions all
depend on knowing the operating frequency. Nothing in any revision says how the tuner learns it.

Three options:

1. **Frequency counter on the forward sample (recommended).** The signal is already present in the
   Sampler chamber at a useful level. A counter gated off the forward detector path is
   self-contained, needs no link to the rig, works with any radio, and keeps the tuner autonomous
   at the entry box. Resolution of ~1 kHz is ample for band-edge-aware calibration.
2. **CAT / CI-V from the transceiver.** Exact, but with the tuner at the entry box it must travel
   over the remote link (Section 7.5), ties the design to specific radios, and fails silently if
   the link drops.
3. **Manual band selection** from the remote head. Simplest; defeats the point of an automatic
   tuner and invites applying the wrong band's calibration.

**Specify option 1, with option 2 as an optional override** where CAT is available. Note that a
counter also gives the tuner a free interlock: no detected carrier means no tuning cycle.

**Counter design.** Tap the forward coupled port *ahead* of the 60 dB AD8302 pad, where the signal
is already strong. Level varies with operating power:

| Operating power | Forward port level |
|--:|--:|
| 1500 W | 6.85 V RMS |
| 100 W (typical) | 1.77 V RMS |
| 10 W | 0.56 V RMS |
| 1 W | 0.18 V RMS |

A ~32 dB range, so the front end must limit, not amplify linearly:

```
fwd port --> tap ------------> clamps -----------> comparator ---------> /4 ------> /256
             1 nF + 4.7 k,     BAT54S, to          TLV3501, mid-biased,   74LVC74    74HC4040
             10 k to 1.65 V    0 V and 3.3 V       ~10 mV hysteresis                  |
                                                                                      v
                                MCU timer input (~29 kHz) <-- FT-P x 2 <-- RG-316 <-- 1 k, SMA
```

**Counting:** the comparator drives a ÷1024 prescaler and the MCU counts ~29 kHz over a 200 ms
gate, for **5.1 kHz** resolution (§8B.0.1) — FreqCount is only documented to 8 MHz on the Teensy
4.x. That is still ten times finer than the 50 kHz derate segments need. *The earlier direct-gate
method is in §11.8.*

*Rev 3.7c, as built (§10.4):* the tap feeds 0.68 of the port voltage into a node held at mid-rail.
At 1 W (0.25 V peak) the comparator still swings ±170 mV against ~16 mV of hysteresis, and at 1500 W
the clamps carry ~1 mA. A 74LVC74 divides by 4 ahead of a 74HC4040 (§8B.0.1).

**Operational notes:**
- Requires a **steady carrier**. SSB speech gives intermittent, modulated output and will not
  produce a stable reading. Tuning on a carrier (CW or the rig's TUNE mode) is standard practice
  for any tuner — make it an explicit requirement, not an assumption.
- **Carrier-present interlock:** below a count threshold, declare no carrier and inhibit tuning.
  This is free and prevents the tuner acting on noise.
- The comparator sees the fundamental plus any harmonics; at the coupler the fundamental dominates
  and comparator hysteresis handles the rest. No input filter needed.

## Section 6B — Dummy Load, Calibration Load and AUX Passthrough *(Rev 3.7a)*

The "bypass" of §8B.4d is an **interlock** bypass: it forces the permissive closed with a dead
controller and routes no RF. This section adds the RF features.

### 6B.1 What is and is not possible

- **Full-power dummy load inside the box: no.** 1.5 kW into a load needs its own oil or forced-air
  cooling; the RF bay's whole budget is ~200 W (§8) and the utility layer is sealed IP5X (§8E).
- **Straight input-to-output passthrough: no.** The only output is the balanced ladder line to
  the doublet, which needs the network on every band; 50 Ω straight into it is a gross mismatch.
- **What fits:** two 50 Ω coax relays on the low-voltage side (≈ 274 V RMS at 1.5 kW, so no
  vacuum relay), right after the sampler, giving three paths:

```
                        K1 (SPDT)                K2 (SPDT)
  [sampler out] ---> COM  NC --> [choke] -> [T-network]           (TUNE, de-energized)
                          NO --> COM  NC --> [rear N: AUX / DUMMY LOAD]   (AUX, K1 only)
                                      NO --> [internal 50 Ω cal load]     (CAL, K1 + K2)
```

### 6B.2 Modes

| Mode | Relays | Use | Sampler / protection |
|:--|:--|:--|:--|
| **TUNE** (normal) | none energized | Matched doublet | Full metering, over-SWR trip, tuning |
| **AUX** | K1 | **Passthrough** to a coax-fed antenna, an **external full-power dummy load** (amp test; the one full-power verification §6A.8 asks for), or test gear | Metering and over-SWR trip stay active; tuning disabled |
| **CAL** | K1 + K2 | Internal 50 Ω load: **automatic per-band magnitude calibration (§6A.8)** and low-power tune-up of the amp | Hardware power limit (6B.3) |

- **De-energized = TUNE**, so a dead controller plus the §8B.4d keyed bypass still leaves a
  working station on the last band (the network holds its position).
- **CAL is the energized state of K2,** so a dead driver cannot select the small load. A *welded*
  K2 could, which is why the load is protected by measuring RF **at the load** (6B.3a), not by
  trusting relay state.
- **Switching follows §5.5:** withdraw the permissive, wait out the amplifier relay release
  (§7.4.5), switch, confirm, restore. *Rev 3.7a:* K1 and K2 are **Tohtsu** ham-market relays with no
  auxiliary contacts (§9 item 34). Confirmation is **coil-current sense** on each driver channel plus
  an **RF check** on the first low-power key-down: in CAL the load detector (6B.3a) must see RF, in
  TUNE and AUX it must not. A mismatch is a class B fault (§8B.4a).

### 6B.3 Internal calibration load

| Parameter | Value |
|:--|:--|
| Element | 50 Ω flanged thick-film RF termination, DC–30 MHz, VSWR ≤ 1.05 (return loss ≥ 32 dB) |
| Rating | ≥ 100 W part, **operated at ≤ 50 W** |
| Mounting | Flange through a cutout in the Sampler chamber **floor**, directly on an **external finned heatsink** (Wakefield-Vette 441K); load **TTM G150N50W4E**, gasketed so the chamber stays sealed (TUNER-E-206) |
| Power limit | **Hardware:** the **cal-load RF detector** (6B.3a) withdraws the permissive above ~60 W *at the load*, whatever K1 and K2 are doing. **Thermal:** NC 85 °C switch on the heatsink (Cantherm F20A085053600060), always in the permissive chain — it only opens if the load is hot |
| Firmware | CAL offered only below the limit; a calibration run steps the amp's drive through several levels per band (§6A.8) |

**Reference plane.** Keep the coax from K1 to the choke input and from K1 to the load the same
electrical length, or store the measured offset. Magnitude calibration does not care; vector (phase)
calibration does. The open and short standards of §6A.8 are still applied manually at the AUX port.
A third relay could make them automatic later.

### 6B.3a Cal-load RF detector *(Rev 3.7a — replaces the K2 auxiliary-contact interlock)*

The hazard is **RF power in the 100 W load**, so measure that, not the relay position. A welded K2 in
AUX, a miswired K1 or a firmware error all end the same way: full power into the load with a
perfect SWR, too fast for the thermal switch. The detector sees it directly.

```
  load node ──┤3.3 pF 1 kV NP0├──┬── BAT54S ──┬── 100 kΩ ─┬── to J-S / J-B (analog grade, §7.3a)
                                 │            │           │
                            100 pF NP0     2.2 nF      +1.0 V bias via 1 MΩ (idle level)
                                 │            │           │
                                GND          GND      33 V TVS clamp
```

| Item | Value |
|:--|:--|
| Divider | 3.3 pF / 100 pF capacitive, **1 : 31**, flat across 1.8–30 MHz (no resistor to dissipate full power) |
| At 60 W in the load | 77 V peak → 2.5 V peak at the diode → ≈ 2.2 V DC (+1.0 V bias) |
| At 1.5 kW in the load | 387 V peak → 12.5 V → clamped; the trip is long over by then |
| Response | ≈ 0.2 ms (100 kΩ × 2.2 nF), then ≈ 1.1 ms more as built, where the 100 kΩ source drives the two 5600 pF contacts (J-S, J-B). Still far inside the load's survival time at 1.5 kW |
| Comparator | **Window** on the control board's hardware permissive: trip **above** the 60 W level **or below** 0.5 V. An open or shorted detector line reads ≈ 0 V, so a broken detector **trips** instead of going blind. *Rev 3.7c, as built:* the 1 MΩ bias makes the node too weak to load, so it enters through 100 kΩ into an MCP6002 follower. A **10 MΩ pull-down** at the control board is what makes an open line read 0 V; it moves the idle level from 1.00 to 0.91 V. An LM393 runs on 5 V, keeping the ~2.1 V threshold inside its input range; the high trip is set with a 3296W trimmer (0.86–3.08 V), and the 0.50 V low trip is fixed |
| Calibration | Set the 60 W threshold once with a wattmeter in CAL; the firmware also logs the detector reading against forward power on every calibration run, so drift shows |

The detector sits on the measurement board beside the load (Sampler chamber). The 3.3 pF top
capacitor is a 1 kV NP0 part or a short gimmick; at the load's 50 Ω it loads the node by under
0.1 % at 30 MHz.

*Rev 3.7c, as built (§10.4):*
- **Top capacitor:** a Vishay 561R10TCCV33 disc (1 kV NP0, leads formed to 5 mm).
- **Tap:** a 22 AWG wire from the load's tab lands on a plated pad in the board corner nearest the
  load. The pad has 2.5 mm to every other conductor (IPC-2221 B2, 301–500 V), and the trace to the
  disc runs on an inner layer.
- **Bias:** a 22 k / 10 k divider from the analog 3.3 V, giving 1.03 V.
- **TVS:** SMF33A.

### 6B.4 AUX port

- Rear-panel **N bulkhead, PTFE**, beside the coax input. Rated as the relays.
- In AUX the input choke and the floating deck are **out of circuit**, so the port is ordinary
  grounded-shield coax. A coax antenna fed from it needs its own arrestor at the entry panel
  (§8A.2 single-point ground, §8D.5).
- The UI shows the mode at all times. The local panel and the web UI can select TUNE / AUX / CAL;
  like a band change, it is not a fault-policy action and is allowed remotely.

### 6B.5 Placement and wiring

K1, K2, the AUX bulkhead and the cal-load flange sit in the **Sampler chamber** (rear of the
utility layer, §3.0). The chamber is 5.00″ × 5.00″ × 15.87″; since the choke left it (Rev 3.7c, §6)
the two N-type coax relays (~2.5″ × 2″) have room to spare — confirm in the mock-up (§9 item 5). New crossings
Control → Sampler: K1 and K2 coil drive (4 lines), the thermal switch (2) and the cal-load
detector (1 + return), through the filtered sampler-group connectors (§7.3a). The control board
needs two more relay-driver channels with coil-current sense, the thermal input and the detector
window comparator (§9 item 35).

## Section 7 — Control, Position Feedback, and Interlocks

### 7.1 Position feedback — no wires cross into the RF bay

**The Rev 1 rule is restored and binding: NO WIRES between the Motor Chamber and the RF Tank
Chamber.** Rev 3.2 placed SPI encoders on the component side of the shaft, inside the RF bay — an
active digital device in a multi-kilovolt near field, with its signal lines crossing back out.

```
[23HS22-2804S NEMA 23 short stack, direct (DECISION M-2, Rev 3.7b)]
   |
   +-- shaft --> [zero-backlash helical coupler]
                    --> [0.375" OD heavy-wall G10 shaft]
                          +-- GT2 belt takeoff --> [2-stage belt reduction, >= (travel + 2):1]
                          |                          +-- single-turn absolute encoder (M-1 B)
                          |                          +-- 2 limit cams -> inner + outer microswitches
                          |                              per end (7.2)          (utility layer)
                          --> [flanged bronze bushing in shelf]
                               ===== SHELF - NO WIRES =====
                             --> [Delrin Oldham coupler - see 7.1a]
                                --> [C1 / C2 / roller]   (RF bay)
```

The encoder reads the G10 shaft through a belt takeoff, not the motor's rear shaft, so the motor is
**single shaft** (§10.6 depth table) and coupler A sits inside the measurement loop.

Open-loop step counting is rejected. Encoders are **single-turn absolute behind the belt reduction**
(full travel < 1 rev, DECISION M-1 B), so position survives power loss without a homing cycle; a
lost step cannot silently invalidate a stored profile.

**Drive path vs sensing path — two different things.** The **drive path is direct**: motor → coupler A
→ G10 shaft → Oldham → element, with **no belt or reduction** carrying torque (M-2, Rev 3.7b; the old
option-B 3:1 drive belt that tripled travel time is gone). The **sensing path has a small belt**: a
pulley on the G10 shaft turns the encoder / limit-cam module's input. It carries no load and adds no
time — it only lets a single-turn absolute encoder (M-1 B) and the §7.2 limit cams see full travel as
less than one revolution. A timing belt neither slips nor adds backlash at sensing loads; any error
shows up as an encoder / commanded-position mismatch, which §8B.3 treats as a fault.

**Encoder / limit-cam module** *(Rev 3.7b, one per axis, beside its bracket — `enclosure.py`)*: a GT2
pulley on the G10 shaft just above coupler A drives a two-stage belt reduction whose output turns
< 1 rev over full travel — **≥ 24:1 on the roller (22 turns), ≥ 32:1 on each capacitor (~30 turns,
ASSUMED — count them)**. The output shaft carries the AS5048A-class encoder magnet and two cams that
trip the §7.2 limit switches. Envelope 1.2″ × 1.6″ × 1.6″, in the motor chamber: cold, and no wire
follows the drive train.

**Module build — COTS, no machining on the shafts.** Because the output shaft turns < 1 rev over full
travel, the cams are clamped on and set by hand:

- **Trip dogs:** two-piece **clamp-style shaft collars** (6 mm bore), each with one radial tapped
  hole carrying a short socket set screw or dowel as the dog. Two per end — inner (gates STEP) and
  outer (drops EN), offset ≈ ¼ turn of element travel (≈ 4° of output at ≥ 24:1) — **four per axis**.
  Set a trip point by loosening the clamp, rotating, retightening (§9 item 48 supplies the angles).
  *Alternative:* a laser-cut 1/8″ aluminum or acetal cam disc on a clamping pattern hub.
- **Switches:** sub-miniature roller-lever microswitches (Omron SS / D2F class) on a slotted plate so
  the lever-to-dog gap can be trimmed.
- **Encoder:** AS5048A breakout over a diametric magnet in a shaft-end holder on the output shaft.
- **Reduction:** stock GT2 pulleys and belts in two stages, 6 mm shafts in flanged ball bearings.
- **Bracket:** one folded 1/8″ aluminum plate — the only fabricated part (drill and bend).

Industrial geared rotary limit switches (hoist/gate type) combine reduction and cams but are ~5–6″
long and their gear backlash rules them out for the encoder — not used.

### 7.1a Drive-train couplers — material and type

The shaft train in 7.1 has a coupler at each end, and they are **not** the same problem. One lives
entirely inside the Motor Chamber; the other sits in the RF Tank bolted to a rotor that may be at
4 kV. Specifying one part for both is how a metal bellows ended up next to a hot rotor in earlier
revisions.

| | Coupler A (motor side) | Coupler B (element side) |
|:--|:--|:--|
| Location | Motor Chamber | RF Tank Chamber |
| Joins | Stepper shaft → G10 shaft | G10 shaft → UCSX / roller shaft |
| Isolation required | **None** — G10 shaft provides it | Desirable, not load-bearing |
| **Specified** | **Commercial aluminum zero-backlash helical or bellows, 1/4″–3/8″** | **Shop-made Delrin (acetal homopolymer) Oldham** |

**Coupler A is a purchased part.** Both ends are in the same chamber at the same potential, and the
G10 shaft is the isolator. There is nothing a fabricated plastic coupler accomplishes here that a
$10–15 catalog helical does not do better, with a known torque rating and no creep.

**Coupler B is specified as Delrin, superseding the "flexible bellows coupler" of Rev 3.3.** A metal
bellows at that position is a floating conductor mechanically captive to a rotor at up to 4,191 V
peak (Section 1.3) — an unnecessary electrode in the highest-field region of the cabinet. Delrin
removes it. The loss penalty was checked rather than assumed, because a lossy dielectric in the
rotor-to-ground standoff path is a legitimate concern:

| Element in standoff path | C (end-to-end) | tan δ | Share of 4,191 V | P @ 30 MHz |
|:--|--:|--:|--:|--:|
| Delrin coupler, 20 mm OD × 25 mm | 0.412 pF | 0.005 | 4.8 % | **16 mW** |
| G10 shaft, 0.375″ × 6″ | 0.021 pF | 0.020 | 95.2 % | **1.25 W** |

The two are a capacitive divider from hot rotor to grounded bushing, and the *smaller* capacitance
takes the larger share of the voltage. The short fat coupler is the larger capacitance, so it sees
only ~200 V and dissipates nothing worth counting. Delrin there is effectively free.

> **Finding carried to Section 9:** the same calculation shows the **G10 shaft itself dissipates
> ~1.25 W** as a standoff insulator at 30 MHz and full voltage. Not a hazard — it is a fiberglass
> rod with a 130 °C service temperature and it is in open air — but it is the first identified
> dielectric loss inside the tank that is not the capacitors, and it scales as V². Worth confirming
> by touch after a long 10 m carrier run.

#### Why Oldham, not a solid hub

**This matters more than the material.** A rigid coupler forces the capacitor shaft to follow the
G10 shaft's axis exactly, dumping every bit of bushing-to-rotor misalignment into the vacuum
capacitor's bellows as radial side load. That is the same failure mode the limit switches of
Section 7.2 exist to prevent, reintroduced at the other end of the shaft.

An Oldham coupler — two slotted hubs and a center disc with tongues 90° apart — accommodates
parallel offset by design, is zero-backlash when the tongue/slot fit is close, and is the easiest
coupler type to machine. Acetal is the standard center-disc material in commercial Oldhams (Ruland,
Huco) precisely because of its low friction against the sliding tongue. Loading is trivial:

- Center disc, 0.4 N·m, 8 mm tongue × 20 mm engagement × 3 mm height, 7 mm mean arm
- **0.48 MPa bearing stress against ~70 MPa compressive yield — 145× margin**

Size the disc for convenient machining, not strength. Oldham handles parallel offset well and
angular misalignment poorly (~0.5–1°), which suits a bushing and a chassis-mounted capacitor whose
residual error is mostly positional. If the two axes end up with real angular error, machine a
helical beam slot in the Delrin instead — more work, accommodates both.

#### Retention — do not use set screws or a press fit

Two independent mechanisms loosen an acetal hub on a steel shaft, both slow and silent:

- **Creep.** Acetal relaxes under sustained preload. Expect 40–50 % loss of clamp force over time.
- **CTE mismatch.** Acetal is ~110 ppm/°C against steel's ~12. The bore grows **19 µm per 20 °C**
  relative to the shaft — 37 µm across the 40 °C operating envelope of Section 8E.

A set screw bottoming in plastic threads, or an interference fit, will be loose within a season.
**Specified retention: a milled flat plus a transverse roll pin**, or a split clamp with a steel
screw sized with margin. An M4 at 2.5 N·m gives 2.86 N·m capacity at µ = 0.20, falling to **1.43
N·m (3.6×) after full creep relaxation** — acceptable. Never drill the Jennings shaft; clamp or use
the existing flat on that end.

#### What stays G10

**Do not substitute Delrin for the 0.375″ shaft.** Torsionally it is survivable, but the bending
stiffness is not:

| | Windup, 6″ @ 0.4 N·m | Flexural modulus |
|:--|--:|--:|
| G10 | 1.08° (0.081 pF on a UCSX) | 17 GPa |
| Delrin | 3.59° (0.27 pF) | 2.9 GPa |

The 6× drop in flexural modulus is the disqualifier — a 6″+ unsupported span in acetal would sag
and whip, and Section 3.1 already requires an intermediate G10 bearing block at that length. Delrin
is a coupler material here, not a shaft material. The Section 7.5 panel encoder extensions remain
Delrin: short, unloaded, and chosen for isolation rather than stiffness.

#### Stock and machining notes

- **Delrin / acetal homopolymer**, natural or black. Avoid nylon — 2–3 % moisture uptake makes it
  dimensionally unstable; acetal takes 0.2 %.
- Acetal relieves internal stress when cut. Rough, let it sit, then finish to size.
- Delrin AF (PTFE-filled) lowers tongue friction further but is not necessary at 0.48 MPa.

### 7.2 Limits — layered overtravel protection *(Rev 3.7b)*

Nothing on a vacuum capacitor moves where a switch could see it (the plates travel inside the
envelope), and the roller carriage rides the hot bus rod. So the limits are sensed on the **cold,
reduced side**: the encoder / limit-cam module of §7.1, whose output shaft turns < 1 rev over full
travel. Five layers, each independent of the one above it:

| Layer | Mechanism | Catches |
|:--|:--|:--|
| 1 · Soft limits | Firmware stops each axis ~½ turn short of its ends (absolute encoder). **Roller slow zone:** ≤ 2 rev/s within 3 turns of either end — at 10 rev/s the rotor (~30 lb·in²) stores ~17 J and needs ~2 turns to stop | Normal operation |
| 2 · Limit cams | Two cams on the module output shaft trip **inner** and **outer** microswitches at each end | Firmware fault, encoder fault |
| 3 · Hardware response | **Inner switch gates STEP** (hardwired) while EN stays on — the motor holds and brakes instead of free-wheeling. **Outer switch, ~¼ turn further, drops EN** (the Rev 1 behavior). No firmware in either path | Runaway pulses, hung firmware |
| 4 · Torque ceiling | Driver current set so the motor stalls **below the capacitors' end-stop torque**; a stall shows as an encoder mismatch (§8B.3) | Anything that reaches a stop |
| 5 · Hard stops | Roller: stop collars on the bus rod, placed beyond the inner switch by more than the slow-zone stopping distance (~0.1 turn at 2 rev/s). Capacitors: their own internal stops, protected by layer 4 | Last resort |

Why two switches per end: dropping EN at speed lets a de-energized stepper free-wheel, and the
roller would coast several turns into its stops; gating STEP keeps holding torque on it. The
capacitor axes are light, so EN alone would do for them, but one scheme for all three keeps the
wiring and firmware uniform. **Settle by measurement (§9 item 48):** the capacitors' end-stop torque
rating (sets layer 4) and the roller's stopping distance (places its inner cam).

### 7.3 Bulkhead filtering

Every line crossing a chamber boundary passes a **feedthrough capacitor at the wall**, but the
capacitance is set by **what the line carries**, not one value for everything (parts per §9 items
16, 23, 38, 40). The highest signal-rated values in stocked filtered D-subs are 4000 pF pi / 5600 pF
C, and 0.01 µF with 1 kΩ is a 15.9 kHz corner, which would erase a 2.5 µs STEP pulse and a ~1 MHz
encoder SPI clock. *The earlier single-0.01 µF rule is in §11.7.*

| Grade | Lines | Part at the wall | Series element (board side) | Corner |
|:--|:--|:--|:--|:--|
| **Analog / slow** | Detector outputs, CT, thermal, relay read-backs, relay coils | 5600 pF C-filter D-sub contact | **1 kΩ carbon comp** on ADC inputs (Rev 3.7c board: 1206 anti-surge thick film) | 28 kHz |
| **Logic** | STEP/DIR/EN, encoder SPI (≤ 1 MHz), limit switches | 1000 pF C-filter D-sub contact | **47 Ω** source resistor | 3.4 MHz (47 Ω) |
| **Frequency** | ÷1024 prescaler (~29 kHz) | **Discrete 1000 pF** feedthrough at each wall | 1 kΩ | 159 kHz |
| **RF tank** (shelf) | Imbalance CT, tank thermal | **Discrete 0.01 µF** feedthrough (Tusonix 2499) | 1 kΩ on CT/thermal | 15.9 kHz |
| **Power** | 24 V to the motor chamber | 0.30 µF / 15 A bolt-in feedthrough | — | — |

The motor chamber carries no RF source (Motor → RF tank is an insulated shaft only), so the logic
grade there is about keeping the control chamber's own switching noise inside it. At 1.8 MHz the
analog grade gives ~36 dB from the RC alone, before the D-sub's shell bond to the bare-metal wall.

| Boundary | Method |
|:--|:--|
| Sampler → Control | Filtered DB-25 at the partition → **Belden 8112** (12.5 pr 24 AWG, overall foil + braid; Rev 3.7c, §9 item 52) across the motor chamber → filtered DB-25 at the bulkhead (§7.3a). Prescaler on **RG-316** between two discrete 1000 pF feedthroughs |
| Sampler → RF Tank | RG-393 PTFE coax, PTFE bulkhead (Amphenol 83-798 SO-239A) |
| Control → Motor | Filtered DB-25, logic grade (§7.3a), shielded harness on the motor side. **No glands** |
| Control → RF Tank | Filtered DE-9 J-E at the bulkhead, then discrete 0.01 µF feedthroughs FT1–FT4 in the shelf (all four used; item 16) |
| **Motor → RF Tank** | **Insulated shaft only. No wires.** |

### 7.3a Connector allocation *(Rev 3.7a — TUNER-E-208)*

All filtered D-subs are **Amphenol FCE17** (formerly FCC17), C-filter, solder cup, 0.120″ mounting
holes; front-mount cutouts DB-25 **1.744 × 0.512″, holes 1.852″ apart**; DE-9 (J-E, J-F) per the
FCE17 datasheet. The shell bonds to the wall through its dimples — **keep a 0.25″ band around each
cutout bare (mask it from powder coat), as for the gasket faces.** Plugs mate from the control side so the cassette
unplugs; solder cups face the motor chamber. Plug and harness envelopes are interference-checked
in `enclosure.py`.

| Ref | Wall | Part | Grade | Carries |
|:--|:--|:--|:--|:--|
| J-A | Bulkhead | FCE17-B25SM-250 (DB-25, 1000 pF) | Logic | STEP1–3, DIR1–3, DRV_EN, encoder SPI incl. MOSI + 3V3 (7), LIM1–6 — 20 + 5 GND |
| J-B | Bulkhead | FCE17-B25SM-290 (DB-25, 5600 pF) | Analog | Sampler group: 7 detector/sampler lines, K1/K2 coils (4), cal-load thermal (2), cal-load RF detector (1) — 14 + GND |
| J-E | Bulkhead | FCE17-E09SM-290 (DE-9, 5600 pF) | Analog | Tank thermal, imbalance CT, RF service-panel switch (3) + GND (blower on J-F) |
| J-S | Partition | FCE17-B25SM-290 (DB-25, 5600 pF) | Analog | Sampler group, as J-B |
| FT-C, FT-D | Bulkhead | Spectrum Control **9910-381-6002** (0.30 µF, 100 V, 15 A, 12-32) | Power | 24 V and return to the drivers |
| J-F | Left lower panel | FCE17-E09SM-290 (DE-9, 5600 pF) | Analog | Blower +12 V, GND, tach (exterior lead in conduit) |
| X | Partition | **Amphenol RF 172124** N-N bulkhead, PTFE, jam nut (§9 item 43) | RF | K1 NC (W15) → X → shelf coax bulkhead (W17), all chassis side; the choke starts at the shelf bulkhead (Rev 3.7c, §6) |
| FT-P | Bulkhead + partition | Tusonix **2499-003-X5U0-102PLF** (1000 pF, 500 V, 12-28) | Frequency | ÷1024 prescaler, RG-316 between |
| FT1–FT4 | Shelf | Tusonix **2499-003-X5W0-103ZLF** (0.01 µF, 500 V, 12-28), 0.55″ pitch | RF tank | FT1 tank thermal, FT2 CT, FT3 common return, FT4 RF service-panel switch (*Rev 3.7c*; was spare) |

**Sampler run (§9 items 38, 52).** Belden 8112, 12.5 pairs of 24 AWG under an overall foil and braid. The 8-pair M13197 of Rev 3.7a was
three pairs short of the 11 below. Pair each signal with a ground or return (relay coil +
with its own return), drain to the backshell at both ends, and keep the cable against the floor
away from the steppers. Relay coils on that cable carry **suppression diodes at the relay**, so
their switching edge never reaches the detector pairs. The FCE17 shells give the partition and
bulkhead their 360° bond; the cable shield only has to survive the motor chamber.

Alternate if the C-filter proves insufficient on the bench: **Spectrum Control 56F721-015**
(DB-25, 4000 pF **pi**, 50 V, ~$124) in place of J-B / J-S.

*Rev 3.7c, sampler side:*
- **W9:** J-S solder cups 1–16 run one to one to the measurement board's 2×8 header, 16 conductors,
  every line with its own ground. That header therefore carries pins 1–16 of the control board's
  J-B pinout.
- **W9b, W9c:** the relay coils (pins 20–23) and the cal-load thermostat (17–18) go from J-S
  straight to K1/K2 and to the switch.
- **W10:** the ÷1024 count leaves the board on an edge SMA for the RG-316 run.
- **W13, W14, W27, W28:** the RG-393 input runs to the coupler box (W13), and the box feeds K1 (W14).
  The box's FWD/REF SMAs reach the board's J1/J2 on one length of RG-316 each (W27, W28).

### 7.4 Amplifier interlock — optical permissive, fail-safe on loss of signal

*Rev 3.7a:* §6B adds two inputs to the hardware permissive: the cal-load RF detector (6B.3a, ~60 W at
the load) and the cal-load thermal switch. Both are in it at all times, whatever K1 and K2 are doing
(§6B.3). Relay changes K1/K2 follow the §5.5 sequence. *Rev 3.7c:* built on the control board as drawn
below (§10.5).

> **Corrected for entry-box siting.** Earlier revisions specified *"a hardware loop in series with
> the amplifier keying line"* at the tuner. That assumed tuner and amplifier were co-located. With
> the tuner at the entry box (Section 1.6) and the amplifier at the bench, the keying line is
> twenty-odd feet away and the loop cannot live at the tuner.

Two tempting fixes are both wrong: running the keying pair out to the box reintroduces the copper
ground path that Section 8A.3 exists to eliminate, and carrying the permissive over the data link
contradicts Section 8C.6 — protection must never depend on the link.

**The interlock is its own dedicated optical channel, independent of the data link.**

```
   AT THE TUNER (control board, all hardware)                       AT THE BENCH
   ------------------------------------------                       ------------
   over-SWR comparator (meas. bd) --+
                                    AND --+
   MCU_PERMIT (pulled down) --------+     OR --+
   bypass key (8B.4d) --------------------+    |
                                               AND --+
   cal-load window (6B.3a) -----+              |     AND --> LED --> [ fiber ] --> receiver
   cal-load thermal (6B.3) -----+-- AND -------+     |                                |
   RF service-panel switch -----+                    |                                v
   any limit switch open -------+        10 kHz LMC555                    opto-isolated switch
                                                                                      |
                                                           [ rig PTT ] -- E-STOP -----+- [ amp key in ]
```

- The permissive is the **logical AND** of every protective condition, formed in hardware, not
  computed by firmware.
- **The bypass key overrides exactly what §8B.4d says it defeats:** the over-SWR trip and the MCU's
  vote, which carries the relay sequencing. The cal-load window, the cal-load thermal switch, the RF
  service-panel switch and the limits stay in force, so the key cannot defeat personnel or load
  protection.
- Every input fails toward inhibit. A broken switch lead reads as a trip; an unplugged sampler
  ribbon pulls the SWR term low; an open detector line reads 0 V and trips the window (§6B.3a). The
  RF service-panel switch uses shelf feedthrough FT4 (§7.3a). It is a reed sensor on the front shelf-ring
  flange, closed by a magnet on the panel (§9 item 51).
- It drives an LED into a dedicated fiber strand — **not** the data link, no protocol, no software.
- At the bench a receiver drives an **opto-isolated switch in series with the keying line**, in
  series with the hardwired E-STOP of Section 8C.2.

#### 7.4.1 Fail-safe analysis

| Failure | Optical state | Result |
|:--|:--|:--|
| Fiber broken or disconnected | dark | **inhibit** ✓ |
| LED or its driver fails open | dark | **inhibit** ✓ |
| Tuner loses power | dark | **inhibit** ✓ |
| Bench receiver loses power | switch unpowered, NO contacts | **inhibit** ✓ |
| MCU hangs | its watchdog resets it, and MCU_PERMIT is pulled down through the reset | **inhibit** ✓ (unless the bypass key is on) |
| **LED driver fails shorted — stuck on** | **light present** | **permissive stuck closed — FAILS DANGEROUS** |

Every failure mode is safe except the last one, and the last one matters: a stuck-closed permissive
means the tuner can traverse the roller or switch K1/K2 while the amplifier is keyed at
1500 W.

#### 7.4.2 Dynamic permissive — closing the stuck-on hole

Do not send steady light. Send a **modulated permissive**: the tuner pulses the LED at a fixed
tone (10 kHz), and the bench receiver requires *that tone*, not merely the presence of light, before
closing the switch.

- Stuck-on LED → DC light, no tone → **inhibit** ✓
- Stuck-off, broken, dark → **inhibit** ✓
- A tone detector is a handful of parts.
- *Rev 3.7c:* **the tone comes from a hardware LMC555 on the control board, not from the MCU.** An
  MCU-generated tone dies with the controller, and the §8B.4d bypass exists precisely so a dead
  controller still leaves a working station (§6B.2). The MCU's vote is a level instead, MCU_PERMIT.

This converts the only dangerous failure mode into a safe one. It is standard practice in safety
interlocks and is proportionate here: the consequence of a stuck-closed permissive is hot-switching
a coax relay (K1/K2) or driving a roller under full power.

**If a steady-light permissive is built instead**, state it as an accepted risk and mitigate by
driving the LED from a push-pull output that cannot source current with the drive line stuck, and
by periodically self-testing the channel — the tuner can briefly interrupt the permissive and
confirm the bench switch opened, during IDLE with no carrier.

#### 7.4.3 Response time

<2 ms end to end. Optical propagation is irrelevant; the budget is the comparator, the tone
detector and the switching device. An **opto-MOSFET / PhotoMOS** switch meets it comfortably; a
mechanical relay at 5–10 ms does not, which is why the switch is solid-state.

#### 7.4.4 Amplifier keying interface — Heathkit SB-220

**Amplifier: Heathkit SB-220**, pair of 3-500Z, reported to carry most or all of the common modern
modifications.

**Stock behavior (for reference, and for the defensive rating below):** the SB-220 ANT RELAY jack
presents **+120 to +130 VDC positive** to the exciter on receive, because the relay coil is fed
from the 120 V relay supply. Opening that line produces **inductive kickback** from the coil. This
is the classic hazard that destroys modern solid-state T/R switching, and the reason the soft-key
modification exists.

**With the soft-key modification fitted**, the keying line drops to roughly **1.5 V on receive with
under 1 mA of keying current** — trivial for any switching device.

**Specify the bench-side switch for the UNMODIFIED case regardless.**

| Parameter | Specification |
|:--|:--|
| Device | Opto-MOSFET / PhotoMOS, normally-open |
| Load voltage rating | **≥ 250 V**, either polarity |
| Load current | ≥ 100 mA (ample for a relay coil) |
| Protection | **Flyback or TVS across the switched terminals** — mandatory |

A PhotoMOS rated 250–400 V costs effectively the same as one rated 60 V. Rating for the stock
condition means the interlock survives the amp being serviced, reverted, or replaced, and it
removes any dependence on correctly identifying which mods are actually present. **The kickback
suppressor is required either way** — the interlock switch is in series with the keying line and
sees whatever that line does when it opens.

> **Verify by measurement before building:** open-circuit voltage at the ANT RELAY jack on receive,
> and keyed current on transmit. Five minutes with a meter settles which keying regime is actually
> present and confirms the mod is doing what it should.

#### 7.4.5 The amplifier's own T/R relay is inside the timing budget

The SB-220 switches antenna and bias with a **mechanical T/R relay** (unless converted to QSK).
When the optical permissive is withdrawn, the sequence is: switch opens → amp relay releases → RF
actually ceases. The amp's relay release time is therefore *inside* the blanking period, not
additional to it.

The 30 ms RF-decay blanking of Section 5.5 should comfortably cover a Heathkit relay releasing in
10–20 ms, but **this is the number to confirm on the bench** rather than assume: key the amp, drop
the permissive, and scope the RF envelope to measure actual decay-to-zero. If it exceeds 30 ms,
lengthen the blanking — it costs nothing but tune time, and the consequence of getting it wrong is
hot-switching K1/K2.

### 7.5 User interface — local panel plus remote head

With the tuner at the entry box (Section 1.6) the operating position needs a **remote head or
network link**. The local panel is retained for setup, calibration and manual override at the box.

- **Local panel** — as specified below, on the Control chamber front face.
- **Remote link** — **Ethernet** to the operating position for data and the web UI, with a
  separate **POF strand for the interlock** (Section 8C.3), carrying SWR, forward/reflected
  power, band, element positions and feeder imbalance; accepting tune/bypass/manual commands.
  This is the one genuine addition that entry-box siting creates.
- Emergency stop must work **from both ends**; bypass is **local-only** — see Section 8C.1 for
  the correction and 8C.2 for why the bench stop needs no wire to the tuner.

Control-cassette face **~15.87″ W × 5.00″ H**; layout on TUNER-E-202. *The side-column panel fit
is in §11.1.*

- **Display shielding:** 100-mesh copper wire fabric laminated behind the panel cutout, **bonded
  continuously around the full perimeter** — an ungrounded mesh is decoration.
- **Manual controls:** two rotary optical encoders on non-conductive Delrin shaft extensions.
- **Selected parts (Rev 3.7a, TUNER-E-202):** display **Nextion NX4832K035** (board 3.957 × 2.163″,
  M3 holes on 3.705 × 1.911″; panel window **2.95 × 1.99″**, the active area plus 0.03″ a side, whose
  center sits 0.095″ off the board center away from the ribbon end; 1/8″ standoffs keep the panel
  edge off the resistive touch layer). Encoders **Grayhill 62V15-02-080CH** (optical, 24 detent, push,
  3/8-32 bushing, Ø0.380″ hole, keyway instead of a tab). *Rev 3.7c:* the 3.3 V version of the
  62A15-02-060C, in the same body behind the same cutout. Its outputs are push-pull, so the 5 V part
  would drive the Teensy past its 3.3 V limit. It has a 0.100″ connector on an 8″ cable that plugs
  straight into the control board. It is a factory order (Future, MOQ 1, ~$47, lead time unconfirmed,
  2026-11-19); the stocked 62V15-02-P (~$77, PC pins) is the fallback, with your own pigtail. Bypass key **E-Switch KO128A2007** (SPST,
  key removable in OFF only, Ø0.748″ hole with a flat at 0.669″). Recovery **E-Switch PV6F240SS**
  (flush, sealed, Ø0.630″) with a 1/4″ guard ring so it is not pressed by accident (§8B.4f.2).
- **Menu architecture:**
  - *Tuning Monitor* — SWR, forward/reflected PEP, band and frequency, step counts for Cap 1,
    Cap 2 and the roller, plus feeder current imbalance from the bifilar CT
  - *Manual Override* — maps front encoders directly to stepper pulses
  - *Utilities* — Find Home, Save Profile to EEPROM

### 7.6 Tuning algorithm

**PID control of SWR is rejected.** SWR as a function of element position is not a smooth
single-minimum surface — it has multiple local minima, and a PID loop will hunt or settle
confidently into a high-SWR local minimum.

**Adopted:** measure R and X directly at the bridge and *compute* target positions from the network
equations, then refine with a bounded local search. Per-band solutions are stored as starting
points in EEPROM.

---

## Section 8 — Thermal

**Derived, not assumed — see Section 1.7.** Worst case is **≈ 341 W at roller Q = 250, or ~568 W
at Q = 150** (bare network, §5.1), both on 160 m at 1.800 MHz where the roller carries 18.4 A. Every other band edge stays
under 140 W.

The cooling system below is sized for **200 W continuous**, which covers every band except the
bottom of 160 m. That segment is handled by the **power derate table in Section 1.7.1** rather than
by more airflow — cooling ~568 W out of a sealed 16″ enclosure is disproportionate for one band
segment used at full key-down power.

*Rev 3.7c: the input choke now dissipates in the RF bay too (§6). It adds ≤ 69 W on 10 m (coax loss),
≤ 28 W on 80 m and ~10 W on 160 m. The worst RF-bay total outside 160 m is 166 W (4.00 MHz: 138 W
network + 28 W choke). The §1.7.1 limits on 160 m now include it: 502 / 600 / 882 W.*

Natural convection through honeycomb cannot move 200 W. **Forced air required.**

| Element | Specification |
|:--|:--|
| Blower | **Delta AFB1212VHE-F00** — 120 × 38 mm, 12 V, two ball bearings (70,000 h at 40 °C), 130 CFM free air / 0.42 in H₂O, ~70 CFM at 4 mm H₂O through filter + two honeycombs; open-collector tach, 2 pulses/rev. Exterior, **left upper panel, high and toward the rear** (moved 1″ forward Rev 3.7a to clear the wall flange; center 5.0″ below the top, so up 2″ with the 24″ box in Rev 3.7c), Orion G109-15A guard. *Rev 3.7a populated model, TUNER-E-212* |
| Intake | *Rev 3.7a (wall mount): **right side panel, low and toward the front of the RF bay**, 8 × 4″ honeycomb + filter + screen* — still *not* the chassis floor. Air crosses the bay diagonally, past the caps and then the roller, rising with convection. *Rev 3.7c:* centered 0.41″ below the deck underside (up 2″ with the deck), so 2.4″ of it sweeps under the deck past the input choke (§6) |
| Intake filter | Washable electrostatic cartridge over hex-cell honeycomb |
| Exhaust | Left-side hex-cell aluminum honeycomb behind the blower, 1/8″ cell, 1/2″ thick (>90 dB to 1 GHz) — the rear is on the wall |
| Fan wiring | *Rev 3.7a:* **not through the RF bay.** The lead runs down the outside of the left panels in flex conduit to a **filtered DE-9 (FCE17-E09SM-290, 5600 pF)** in the left lower panel at the control chamber; +12 V from the control board's TSR 2-24120, tach to an MCU input (blower-fail fault). 4.7 µF across the fan supply per Delta. *Rev 3.7c:* speed is low-side PWM on the fan's return, with the gate pulled **up**, so a reset or dead MCU leaves the blower at full (the §8B.4d bypass relies on that). The tach reads true only while the switch is on, so measure it at 100 % or across an on-phase |

**Air path.** With the RF bay on top, cool air enters low at the front of the right side panel and
leaves high on the left side, toward the rear, so the forced flow runs with convection instead of
against it. The utility layer below has its own small vent path and must not draw air from the RF
bay. Check (§9 item 30a): with 200 W in the RF bay, the shelf and utility layer stay below ~60 °C.

A floor intake was rejected: it blocks on a bench, and ingested dust settling on HV standoffs is a
tracking and flashover path at kilovolt potentials.

---

## Section 8A — Power, Grounding, and Entry-Box Infrastructure

Entry-box siting (Section 1.6) puts mains power and a control link at the point where the antenna
enters the building. That has consequences beyond a power supply.

### 8A.1 Rails and budget

| Rail | Load | Budget |
|:--|:--|--:|
| **24 V main** | 3 × 23HS22 NEMA 23 via DM542T chopper drivers (≈ 0.6 A each while moving) | 5 A peak while slewing |
| | K1/K2 coax relay coils (Tohtsu CX600N-24) | per datasheet |
| **12 V** | cooling blower | 0.5 A |
| **5 V** | MCU, display, encoders, comparator | 2 A |
| **3.3 V** | AD8302, logic — local regulator in the Sampler chamber | 0.2 A |

Peak is non-simultaneous; **a 200 W 24 V supply is comfortable**, with DC-DC converters for the
lower rails. Size the stepper share from the actual driver datasheets — chopper drivers draw
considerably less from the supply than the per-phase current suggests.

*Rev 3.7a:* the 24 V supply rides on the control cassette and must be **≤ 3.92″ tall as
mounted** to pass the front opening. **Selected: Mean Well UHP-200-24** — 201.6 W, fanless, PFC,
EN55032 **Class B**, 194 × 55 × 26 mm; on edge it stands **2.17″** tall and 1.02″ deep (§9 item 39
resolved). Its rating assumes a conduction plate: bolt its base to the cassette's 12 ga tray, or
derate (100 % to 50 °C without the plate). Low rails: **TRACO TSR 2-24120N** (24 → 12 V, 2 A) for the
blower and **TRACO TSR 3-2450N** (24 → 5 V, 3 A, through-hole; give it an LC input filter and
treat its ~300 kHz switching harmonics as a 160 m source). *Rev 3.7c:* both are SIP-3 78xx
drop-ins on the control board. Each sits behind TRACO's reflected-ripple filter: 220 µF low-ESR,
1 µH, then 150 µF (5 V) or 100 µF (12 V). A 1.85 A PTC protects the 24 V input (§10.5). The 5-pin
TSR 3-2450 is still active but costs ~4× as much. Mains in through a **TE Corcom 3EGG1-2**
filtered, fused IEC inlet (3 A, 2 × T2.5 A, 5 × 20 mm; 36 dB at 1 MHz rising to ≥ 48 dB above 5 MHz), with a **Fair-Rite 2631803802** (31 material)
toroid wound 6–8 bifilar turns on both the AC and the 24 V leads.

**Cut stepper current when idle.** The roller leadscrew and the capacitor drives are self-locking,
so no holding torque is needed once positioned. This saves continuous dissipation inside a sealed
box and removes a standing heat source. It is only safe because position is held by **absolute**
encoders (Section 7.1) — with incremental encoders, de-energizing would lose position.

**Switching supply noise.** A switcher at the antenna entry point sits directly at the receive
signal path. Specify a supply with low conducted emissions, add common-mode chokes on both its
input and output leads, and keep it in the Control chamber — never the Sampler or RF chambers.

### 8A.2 Grounding — single point, and it is already defined

The entry box's **bonded baseplate with arrestors is the single-point ground.** The tuner chassis
bonds to it directly with a short, heavy strap — not through the mains safety conductor and not
through the coax shield.

This is the one place where the four-chamber partitioning and the station ground interact, so it
is worth stating explicitly:

- **All four chamber partitions bond to the chassis**, and the chassis bonds to the baseplate at
  **one point**, adjacent to the arrestors.
- **Do not create a second ground path.** The coax shield to the bench, the mains safety ground,
  and the control link are each a potential second path.
- Mains inlet gets a **fuse and a surge suppressor** — this enclosure is at the point where
  lightning energy arrives, not downstream of it.

### 8A.3 The ground loop this architecture creates — and how to break it

With the tuner bonded to the lightning ground at the wall and the transceiver bonded to house
safety ground at the bench, **the coax shield ties the two grounds together.** During a surge the
potential difference between them appears across that shield. This is exactly the condition
single-point grounding exists to prevent, and moving the tuner to the entry box creates it.

Mitigation, in order of effectiveness:

1. **Keep the safety path optical (Section 8C.3).** The interlock permissive runs on plastic
   optical fiber: a light path carries no DC ground reference, so it can never become a second
   ground path. The **data** link is Ethernet, which does bridge the grounds — but see 8C.3.1: the
   coax shield already does, so Ethernet adds a thinner parallel path rather than a new one.
   **Use UTP, not STP** — a bonded shield would bypass the magjack isolation — and fit an
   **Ethernet surge arrestor at the entry panel, bonded to the baseplate.**
2. **Bond the entry panel to the service ground** with a heavy conductor per NEC, so the two
   grounds are at the same potential by design rather than by accident through the coax.
3. **Common-mode choke on the coax** at the bench end, so RF and surge current on the shield does
   not enter the shack even if a potential difference exists.

Items 1 and 3 are design choices for this project. Item 2 is an installation matter and may
already be satisfied by the existing entry panel — **verify it rather than assume it.**

---

## Section 8B — Firmware Architecture

### 8B.0 Processor allocation — ONE MCU, Teensy 4.1

> **Corrected.** An earlier draft of this section argued that two microcontrollers were *forced*
> by the bulkhead constraint: a 29.7 MHz count cannot cross the 15.9 kHz feedthrough filter of
> Section 7.3, so counting had to happen in the Sampler chamber, and once an MCU was there the ADC
> went with it. **That reasoning rested on an unexamined premise — that the full-rate signal had to
> cross.** Divide it first and the constraint disappears, along with an entire microcontroller, its
> firmware image, and the inter-board protocol.

**Controller: Teensy 4.1** (NXP i.MX RT1062, Cortex-M7 @ 600 MHz), mounted on the Control board.

| Requirement | How it is met |
|:--|:--|
| Count the operating frequency | **÷1024 prescaler on the measurement board**, then count 29 kHz on the Teensy |
| ADC: V_MAG, V_PHS, V_FWD, V_REF_DET, AD_VREF | Filtered DC across the bulkhead (Section 7.3, as originally specified) |
| Network solver: sqrt, atan2, complex arithmetic | M7 with FPU at 600 MHz — the closed-form T solution is trivial |
| 42 control signals (Rev 3.7c, §8B.0.4) | all 42 edge pins used, plus an MCP23017 on I2C for the panel and status inputs; the MCU mounts directly, no ribbon |

#### 8B.0.1 Why a prescaler rather than a second MCU

The frequency signal must cross from Sampler to Control. Dividing before the crossing scales the
bandwidth requirement down with it:

| Divider | Max at the wall | Feedthrough that passes it | Resolution @ 200 ms gate |
|--:|--:|:--|--:|
| ÷1 | 29.7 MHz | none | — |
| ÷4 | 7.43 MHz | none | — |
| ÷256 | 116 kHz | 100 pF + 1 kΩ (1.59 MHz) | 1.3 kHz |
| **÷1024** | **29 kHz** | **1000 pF + 1 kΩ (159 kHz)** | **5.1 kHz** |

**÷1024 is specified.** It crosses through a 1000 pF feedthrough with real RF rejection still
intact, and 5.1 kHz resolution is **ten times finer** than needed to select the correct 50 kHz
derate segment on 160 m (Section 1.7.1).

Implementation *(Rev 3.7c)*:
- **Divider:** a **74LVC74** dual flip-flop divides by 4 (150 MHz at 3.3 V). A **74HC4040** then
  takes Q7 (÷256), so the total is ÷1024 and the HC part sees at most 7.4 MHz.
- **Why:** the **74AC4040** first specified is obsolete (Digi-Key: no longer manufactured,
  2026-11-19), and plain HC is marginal at 29.7 MHz on a 3.3 V rail.

#### 8B.0.2 What this costs

Section 6A.3b argued that digitizing locally is "strictly better" because the analog measurement
signals then never cross a boundary. **That remains true** — it simply is not worth a second
microcontroller. The RC-filtered DC crossing was the design's own specification from Rev 1 onward
and is adequate: a 15.9 kHz corner against a 1.8 MHz lowest operating frequency.

The measurement board therefore carries **no microcontroller at all**: port terminations,
detectors, AD8302, comparators, divider (the coupler is its own box, §10.3). Everything leaves as
filtered DC, plus one 29 kHz logic line on its own coax.

#### 8B.0.3 Teensy 4.1 notes

- **Not 5 V tolerant.** Every input must be held at or below 3.3 V. The counter front end already
  clamps (Section 6A.10). *Rev 3.7c:* everything else is 3.3 V by construction:
  - Limits and the encoder SPI run from the board's 3V3.
  - The panel encoders are the 3.3 V version, read through the MCP23017.
  - The Nextion's TX is 3.2 V.
  - The blower tach comes in through 10 kΩ with Schottky clamps.
- **Power.** The board feeds the Teensy's VIN from its 5 V rail and leaves the Teensy's own 3V3
  pins unconnected; the board's logic runs from its AMS1117. **Cut the VUSB–VIN pad** on the Teensy
  before programming it in place, or the PC's USB 5 V and the board's 5 V get tied together.
- **Watchdog is mandatory.** A hung MCU only drops out of the permissive when RTWDOG resets it
  (§7.4.1). The watchdog must be armed before MCU_PERMIT is first raised.
- **No built-in SWD debugger**, unlike an ST-Link-equipped Nucleo. Programming is over USB; add SWD
  via the pads if hardware debugging proves necessary for the state machine.
- **FreqCount is documented for 1 kHz–8 MHz on Teensy 4.x** (the 65 MHz figure on PJRC's page is
  scoped to the Teensy 3.0–3.6 family). At ÷1024 the input is 29 kHz, comfortably inside the
  documented range — this is why the prescaler is specified rather than relying on forum reports of
  higher rates.
- **Ethernet carries the data link** (Section 8C.3, as revised). The 4.1's MAC and PHY pads serve
  the web UI and telemetry; the interlock stays on its own POF strand. *(Earlier drafts left
  Ethernet unused and put data on fiber.)*

#### 8B.0.4 Pin allocation *(Rev 3.7c — `kicad/board_control.py` `PINMAP`)*

| Teensy pins | Signal | Notes |
|:--|:--|:--|
| 0, 2, 4 · 1, 3, 7 · 8 | STEP1–3 · DIR1–3 · DRV_EN → J-A | 47 Ω series (§7.3) |
| 9 | ÷1024 frequency, from the SMA | FreqCount's fixed input |
| 13, 11, 12 · 10, 5, 6 | Encoder SPI SCK, MOSI, MISO · CS1–3 → J-A | AS5048A; MOSI carries the command frames (diagnostics/AGC, error clear) |
| 14–17, 20 | V_MAG, V_PHS, V_FWD, V_REF_DET, AD_VREF ← J-B | ADC; 1 kΩ + 10 nF |
| 21, 22 | Tank thermal, imbalance CT ← J-E | ADC; 1 kΩ + 10 nF; thermal biased for a 10 kΩ NTC |
| 23 | Cal-load detector, buffered, ÷2 | ADC (§6B.3a) |
| 38, 39 | K1, K2 coil current | ADC; 1 Ω sense (§6B.2) |
| 24–29 | LIM1–6 ← J-A | high = tripped **or** open (NC contacts) |
| 30, 31 | K1, K2 commands → the hold latch | take effect only after the permissive has been down ≥ 30 ms (§5.5) |
| 32 · 36 | MCU_PERMIT (out, pulled down) · PERMIT read-back | the MCU's vote in the permissive (§7.4) |
| 33 · 40 | Blower PWM · blower tach | gate pulled up: a reset or dead MCU leaves the blower on; tach is 2 pulses/rev |
| 34, 35 | Nextion RX8, TX8 (Serial8) | 3.3 V UART, Teensy 4.1 only |
| 18, 19 · 41 | I2C SDA, SCL · MCP23017 interrupt | 4.7 kΩ pull-ups |
| 37 | Recovery button | sampled at boot (§8B.4f.2) |

**MCP23017 (address 0x20):**
- GPA0–2 and GPA3–5: encoder 1 and encoder 2 (A, B, push).
- GPA6: the bypass key.
- GPB0–6: SWR_OK, CALDET_OK, CALTH_OK, PANEL_OK, LIMIT_OK, HARD_OK and BYP_OK. The firmware can
  therefore name which term dropped the permissive.
- GPA7 and GPB7: unused; they are output-only on current silicon.

### 8B.1 State machine

```
        power on
           |
           v
    [ SELF-TEST ] -- fail --> [ FAULT ]
           |
           v
    [ IDLE ] <-------------------------------+
       | carrier detected (counter interlock) |
       v                                      |
    [ MEASURE ]  frequency + |Gamma| + phase   |
       |                                      |
       +-- SWR acceptable -----------------> [ MATCHED ]
       |                                      |
       +-- retune needed                      | carrier ends
       v                                      |
    [ SOLVE ]  closed-form T solution          |
       |  no feasible solution --> [ FAULT ]  |
       v                                      |
    [ MOVE ]  PTT dropped, elements driven     |
       |  limit hit / encoder mismatch --> [ FAULT ]
       v                                      |
    [ VERIFY ]  re-measure                     |
       |  converged ------------------------> [ MATCHED ]
       |  not converged, attempts < N --> [ SOLVE ]
       |  attempts exhausted --> [ FAULT ]     |
       +--------------------------------------+
```

### 8B.2 Tune initiation policy

Initiate a tuning cycle when **any** of:

- Measured frequency moves outside the current solution's validity window (recommend ±0.5% or a
  band-edge crossing, whichever is tighter)
- SWR exceeds the retune threshold (recommend 1.5:1) with a carrier present
- Manual request from either the local panel or the remote head

Do **not** initiate on SSB speech — see the carrier requirement in Section 6A.10.

### 8B.3 Element movement rules

- **PTT is dropped for the entire MOVE state.** Non-negotiable: relays must not hot-switch
  (Section 5.5) and the roller must not traverse under power.
- Drive to computed positions in **one coordinated move**, not sequentially — this is the payoff
  for vector measurement and absolute encoders.
- **Verify encoder against commanded position** after every move. Disagreement beyond tolerance is
  a fault, not something to retry silently.
- Cap retries. Recommend **3 attempts**, then FAULT — an oscillating tuner at 1500 W is worse than
  a tuner that stops and says so.

### 8B.3a Tuning time — modeled *(Rev 3.7b)*

`nec/tune_time.py` turns the §5.1 solutions into shaft travel and time. Roller: 22 turns full
travel, L per turn from the NEC sweep (§9 item 44). Capacitors: linear in turns, **~30 turns full range
(ASSUMED — count the UCSX-740-10's turns)**. All three axes move together (8B.3), trapezoidal profile with a
0.25 s ramp, at 1 kHz full steps. Overheads: PTT drop + 30 ms decay, settle + encoder verify, 0.30 s
measurement (200 ms frequency gate + bridge), 3-step bounded refine.

| Case | M-2 A (NEMA 23 direct, 5 rev/s) | M-2 B (NEMA 17 + 3:1, 1.67 rev/s) |
|:--|--:|--:|
| Band change, stored profile | ~5.7 s typical, 6.3 s worst | ~16 s typical, 18 s worst |
| Band change, cold tune (measure + compute + move + refine) | ~7.6 s, 8.2 s worst | ~19 s, 21 s worst |
| In-band retune, 0.5 % QSY | ≤ 3.5 s | ≤ 6.7 s |

**Chosen (M-2, Rev 3.7b): 23HS22-2804S direct on all three axes.** At 1.5 kHz full step (450 rpm,
~0.72 N·m at 24 V) band changes take **~3.9 s typical / 4.3 s worst**; at 2 kHz (600 rpm, ~0.60 N·m)
**~3.0 / 3.3 s**, cold tune ≤ 5.0 s. The roller axis gets its own gentler ramp — its ~30 lb·in²
rotor needs ~1 s to reach 10 rev/s on the available torque — which adds ~0.7 s to roller moves but
still leaves the capacitors as the slower axes. With **pre-positioning on band select** from the
remote head (drive to the stored profile while still receiving), the wait at key-down is the refine
alone, ~1–2 s.

**The capacitors, not the roller, set band-change time.** C2 sits near full mesh on 160 / 80 / 60 / 12 m
and near minimum on 40 m and up, so most band changes swing it end to end. Part of that is the solver: the
network often has two solution branches and the lowest-current policy picks between them (10 m: C2 539 →
45 pF between 28.5 and 29.0 MHz). **Firmware should prefer the solution nearest the current element
positions** when its loss is within a few percent — that removes most long moves and in-band jumps.
The 1 kHz step rate is conservative; times scale inversely with it, within the lead screws' limits.

### 8B.4 Fault handling

| Fault | Immediate action | Recovery |
|:--|:--|:--|
| Limit switch | Hardware already cut driver enable | Back off that axis, re-home, flag |
| Over-SWR in transmit | Hardware comparator drops PTT (Section 6A.4) | Require manual acknowledgement |
| Encoder / position mismatch | Stop all axes | Re-home, re-verify, flag |
| Over-temperature | Drop PTT, blower to full | Auto-clear on hysteresis |
| No feasible solution | Stay put, inhibit full power | Flag — likely antenna fault |
| Carrier lost mid-tune | Abort to IDLE, hold position | Normal, not a fault |

**Power loss mid-tune is safe by construction.** Absolute encoders (single-turn, behind the belt
reduction — §7.1) mean position is
known on restart with no homing cycle, so an interrupted tune resumes from a known state rather
than an unknown one.

**On any fault, the safe state is: elements where they are, PTT inhibited, fault latched and
reported at both ends.** Never move elements toward a guessed position to clear a fault.

### 8B.4a Fault classes and recovery

**Governing principle: power cycling is never the recovery path.** If removing power clears faults,
operators learn to reach for the breaker reflexively — which destroys the diagnostic record and
masks a recurring mechanical failure until it becomes expensive. It is also absurd UX for a box
mounted at the garage wall: the whole point of an automatic tuner is not walking to it.

Faults are therefore classified by **what the operator must actually do**, not by severity:

| Class | Meaning | Clears by | Reachable remotely |
|:--|:--|:--|:--|
| **A — self-clearing** | Transient condition, resolves itself | Automatic, on hysteresis | n/a |
| **B — acknowledge** | Operational cause; hardware believed sound | Operator ACK from either end | **yes** |
| **C — latched** | Implies possible mechanical damage; needs eyes on it | Deliberate clear **at the box** via the panel, see 8B.4f | **no** |

| Fault | Class | Recovery |
|:--|:--|:--|
| Over-temperature | **A** | Blower to full; auto-clears on hysteresis, logged |
| Carrier lost mid-tune | **A** | Abort to IDLE, hold position — not really a fault |
| No feasible solution | **B** | ACK; re-attempt on next carrier. Usually wrong band or an antenna problem |
| Tune failed after 3 attempts | **B** | ACK; re-attempt |
| Over-SWR trip in transmit | **B** | ACK required before PTT is re-enabled |
| Limit switch hit | **C** (STRICT default) | Latches on first occurrence. Local clear, after inspection |
| Encoder / position mismatch | **C** (STRICT default) | Latches on first occurrence. Local clear, after inspection |
| Self-test failure at boot | **C** | Local clear only |

### 8B.4a-1 Mechanical fault policy — three modes, conservative by default

Limit-switch hits and encoder mismatches are the two faults that can mean either a harmless
software edge case *or* real mechanical damage, and the correct response differs. Rather than
guessing, the behavior is an explicit policy with a **conservative default**:

| Mode | Limit hit / encoder mismatch | Transmit | Intended for |
|:--|:--|:--|:--|
| **COMMISSIONING** | Logged, does **not** latch | **Hard-inhibited** | Bring-up and debugging |
| **STRICT** *(default)* | **Latches on first occurrence**, class C, local clear | Normal | Normal service |
| **PERMISSIVE** | First occurrence → remote ACK + re-home. Repeat in one session → escalates to C | Normal | Qualified hardware only |

**STRICT is the shipped and default state**, and the one to run until the roller has hours on it.
Rationale: the homebuilt roller's wheel and bus-rod contact condition is unproven
(Section 5.3a). A slipping coupler, a binding leadscrew, or a roller riding off the winding all
present first as a limit hit or a lost count — and re-homing a jammed mechanism just grinds it.
Until the mechanism has demonstrated itself, **every mechanical fault is worth a look.**

**COMMISSIONING exists because STRICT is intolerable during bring-up.** Debugging motion control
means hitting limits repeatedly; latching hard on each one would mean a trip to the box every time.
In this mode mechanical faults log without latching — and that is only safe because **the PTT
permissive is hard-inhibited**, so the amplifier cannot be keyed at all. No RF, no protection
needed, free movement for debugging.

**Promotion to PERMISSIVE is gated, not casual.** Only after:

- **≥ 100 completed tune cycles** across at least four bands, and
- **≥ 50 hours** powered service, with
- **zero** mechanical faults in that period, and
- the roller wheel and bus rod inspected and found clean (Section 5.3a)

Mode changes are **local-only** — a configuration action at the box (Section 8B.4f), never a remote command — and
every change is logged with a timestamp. A class C latch in PERMISSIVE mode automatically reverts
the policy to STRICT, so proven hardware that starts misbehaving tightens up by itself rather than
continuing on an assumption that has just been falsified.

### 8B.4b Behavior across a power cycle

Fault state is **persisted in NVRAM and re-asserted on boot.** It does not unlatch.

```
power on
  |
  +-- 1. hardware PTT interlock asserts INHIBIT (default state, see 8B.4c)
  +-- 2. self-test: encoders respond, limits read sane, detectors answer
  +-- 3. read persisted fault record
  |      |
  |      +-- latched class C present --> enter FAULT, report, stay inhibited
  |      +-- class B unacknowledged   --> enter FAULT, report, remote ACK permitted
  |      +-- nothing latched          --> continue
  |
  +-- 4. read absolute encoders; compare against last stored positions
  |      |
  |      +-- agree within tolerance --> trust, no homing cycle needed
  |      +-- disagree              --> log it and flag; NOT automatically a fault
  |                                     (someone may have serviced the box)
  |
  +-- 5. release interlock --> IDLE
```

Two deliberate distinctions:

- **Condition-based faults are re-evaluated, not restored.** Over-temperature and over-SWR describe
  a state of the world; measure it again rather than trusting a stale flag.
- **Event-based faults are restored.** Encoder mismatch, limit hit and self-test failure describe
  something that *happened*. Power cycling did not un-happen it, and the latch must survive.

A **hardware watchdog** reset follows the identical path. A hung firmware that resets must not come
back with the interlock released and the fault forgotten.

**Position survives power loss by construction.** Absolute encoders (single-turn, behind the belt
reduction — §7.1) mean an interrupted
move resumes from a known state with no homing cycle — including a brownout that stops an element
mid-travel.

### 8B.4c Fail-safe direction of the interlock

The hardware PTT loop is **fail-safe inhibit**: the amplifier keying path requires an *active*
permissive from the tuner. Loss of tuner power, a hung MCU, a blown rail, or a disconnected
control cable all result in **transmit inhibited**, never transmit enabled.

This is the correct default for a 1500 W station, and it has one consequence worth stating plainly:
**with the tuner unpowered you cannot transmit**, even though the network itself is passive and the
self-locking leadscrews hold the last tuned position. Electrically the tuner would still match on
the band it was last set for — but with no SWR sensing, no over-SWR trip, and no way to know the
element positions, that is not a condition to allow by accident.

### 8B.4d Manual override

For emergency operation, provide a **physically distinct, clearly labeled local bypass** that
forces the permissive closed — a keyed switch or a guarded toggle at the box, not a menu item and
not remotely operable.

- Asserting it logs the event with a timestamp.
- Its state is reported at the remote head so nobody forgets it is engaged.
- It defeats the over-SWR trip and the relay sequencing interlock. It exists so a working station
  is possible with a dead controller, and for nothing else.

Making it local-only and physically awkward is deliberate: it must be reachable in an emergency and
inconvenient enough that it never becomes the normal way to clear a fault.

### 8B.4e Operator-facing summary

What the operator actually experiences:

| Situation | What happens |
|:--|:--|
| Tuner won't match a band | FAULT reported at the bench; press ACK; retry on next carrier |
| High SWR trips the amp | PTT drops in <2 ms; ACK at the bench; carry on |
| Something mechanical jams | Box latches immediately (STRICT). Transmit inhibited until you clear it at the box, after a look at the mechanism |
| Power outage | Comes back to IDLE on the band it was last tuned for, position intact, no homing cycle |
| Controller dies entirely | Transmit inhibited. Keyed bypass at the box restores a working station with no protection |

**At no point is power cycling the answer**, and nothing short of a deliberate local clear will
release a class C latch.

Under the STRICT default, a mechanical fault means a trip to the garage. That is the intended
trade while the mechanism is unproven: a walk to the box is cheap, and a roller inductor ground
down by repeated automatic re-homing against a jam is not. Relax it to PERMISSIVE once the
qualification in 8B.4a-1 is met.

### 8B.4f Local interaction — panel first, button as the escape hatch

Sections 8B.4a-1 and 8B.4b both require certain actions to be **local only**: clearing a latched
class-C fault, and changing the fault policy. Neither said what the local action *is*.

There are two local interfaces, and the division between them is about **what still works when
things are broken**:

| Interface | Role | Works when |
|:--|:--|:--|
| **Panel** — 3.5″ TFT + 2 rotary encoders (§7.5) | Everything that benefits from showing the operator what they are about to do | Firmware and display are healthy |
| **Recessed button** | One job: get into recovery mode at boot | Always — it is sampled before anything else |

#### 8B.4f.1 Panel: the primary local interface

A blind button gesture cannot show *which* fault is being cleared or *which* backup is being
restored. The panel can, so the consequential actions live there:

| Action | Panel behavior |
|:--|:--|
| Acknowledge class-B fault | Shows the fault, its timestamp, frequency and state, then ACK |
| **Clear a latched class-C fault** | Shows which axis, the encoder reading versus commanded position, and the trip count. **Requires scrolling through the detail before Confirm unlocks** |
| **Change fault policy** (8B.4a-1) | Displays the qualification criteria — cycles completed, hours, fault-free period — and whether they are met. Refuses promotion if not |
| Restore a backup | Lists the 20 versioned backups by timestamp, shows the tuner-ID match, previews the differences |

Making the operator *read the fault before the Confirm unlocks* is the point. That is what "needs
eyes on it" was always meant to achieve, and a 5 s button hold cannot enforce it.

**Hardware note:** at least one rotary encoder must have an integral push switch for Confirm, or
the panel needs a dedicated confirm button. Specify this when selecting the encoders — optical
encoders do not all include one.

#### 8B.4f.2 Button: recovery mode, and nothing else

**One recessed, sealed, panel-mount momentary switch** on the Control chamber exterior, wired to a
Teensy GPIO with a pull-up. Recessed so it cannot be pressed by a sleeve; sealed because it
penetrates an IP5X chamber (§8E). **Not** wired to the Teensy reset line — a hung firmware is the
watchdog's job (8B.4b).

**Held during power-up → recovery mode.** That is its only function. Standard hold-at-boot pattern,
no extra hardware, and it is sampled before the display is even initialized.

#### 8B.4f.3 Recovery mode

For one situation: **the tuner is unreachable and cannot be fixed over the network** — a mistyped
static IP, wrong subnet, hostname clash.

**Two stages, so it degrades gracefully if the display is also dead:**

**Stage 1 — immediate, unconditional, no UI required:**

| | Behavior |
|:--|:--|
| Network | **Forced DHCP, hostname `tuner`** — regardless of stored config or card |
| Fault policy | **Forced to STRICT** |
| Latched faults | **Preserved.** Recovery does not clear them |
| **Transmit** | **INHIBITED** |

Reachability is restored *before* any menu appears. **If the display is dead you still get DHCP**
and can reach the web UI — which is the whole point of the escape hatch.

**Stage 2 — the panel menu, if the display is working:**

- Choose a backup from the versioned list (8B.5.4a), with tuner-ID match shown
- Review and edit network settings directly with the encoder
- Preview what a restore would change before applying it
- `/recovery.cfg` is applied if present, then renamed (8B.5.4c)

#### 8B.4f.4 Why this does not undermine 8B.4b

Section 8B.4b insists power cycling must never clear a fault, and recovery mode is entered
*through* a power cycle — so the boundary matters:

- Recovery mode **restores reachability**: network settings, thresholds, hostname.
- It **does not clear latched faults**, does not promote the fault policy, and **does not permit
  transmit**.

A class-C latch still requires the panel sequence, performed by someone standing at the box who
has had to read the fault detail to unlock Confirm.

**Exiting recovery is explicit** — "apply and restart normally" in the panel or the web UI, never
another power cycle — so you cannot stumble out of recovery into a transmitting state. Signaled
throughout: fast LED flash at the box, banner in the web UI.

### 8B.5 Storage — two tiers, and the card may always be absent

The Teensy 4.1 carries a **built-in microSD socket** on dedicated SDIO pins, so removable storage
costs no hardware and no edge IO. But removable storage creates a hazard that has to be designed
against explicitly.

#### 8B.5.1 The conflict with Section 8B.4b

Section 8B.4b establishes that **power cycling must never clear a fault** — latched state is
persisted and re-asserted on boot, precisely so an operator cannot mask a recurring mechanical
failure by reaching for the breaker.

**If latched fault state lived on the SD card, pulling the card would clear it.** That reintroduces
exactly the failure mode 8B.4b exists to prevent, with a smaller gesture. Removable media and
safety-critical state are therefore kept apart.

#### 8B.5.2 What lives where

| Tier | Medium | Contents | If it is lost |
|:--|:--|:--|:--|
| **Authoritative** | **Teensy internal flash** | Latched class-C faults, fault-policy mode (8B.4a-1), calibration data, calibration checksum | Tuner will not operate correctly — treated as a fault |
| **Convenience** | **microSD, removable** | Network config, hostname, fault log, tuning profiles, calibration *backup*, NEC per-band table | Tuner runs on internal state and defaults |

**Calibration is authoritative in internal flash, with the SD holding a backup copy.** Detector
curves and AD8302 calibration (Section 6A.8) are too important to depend on a card that may
be out of the slot. The SD copy exists so calibration survives a board replacement and can be
transferred or inspected.

#### 8B.5.3 Behavior with no card present

**Full function.** The tuner boots, tunes, protects, and reports with an empty slot:

| Item | No-card behavior |
|:--|:--|
| Network | From internal flash; DHCP and hostname `tuner` if never configured |
| Calibration | Internal flash copy, as normal |
| Fault state | Internal flash, as normal — **a latched fault stays latched** |
| Fault log | Buffered in RAM, flushed when a card appears |
| Tuning profiles | Internal flash copy of the last-used set |
| Status | Web UI shows **NO CARD**, logged as an event, not a fault |

Card absence is a *condition*, not a fault. It never inhibits transmit.

#### 8B.5.4 The card is a write-through mirror, not a config source

> **Corrected.** An earlier draft had the card read at boot with its values overriding internal
> defaults. That made removable media a configuration *input*, contradicting 8B.5.2's rule that
> internal flash is authoritative — and it meant swapping a card could silently change how the
> tuner behaves.

**Internal flash is the single source of truth. The card mirrors it.**

```
admin changes a setting in the web UI
        |
        +--> written to internal flash        (authoritative, takes effect)
        +--> mirrored to the SD card          (backup, timestamped)
```

Every administrative change — network settings, thresholds, calibration entry, tuning profiles —
is committed to internal flash *and* written through to the card in the same operation. The card
is never consulted during normal operation. Writes are human-initiated and therefore rare, so
endurance is not a concern for this path (unlike logging, 8B.5.5).

#### 8B.5.4a Versioned backups

Each write-through creates a **new timestamped file**, retaining the last 20:

```
/backup/2026-10-21T163000_config.json
/backup/2026-10-21T174512_config.json
/backup/current.json          -> copy of the most recent
/backup/tuner.id              -> identity, see 8B.5.4b
```

Cheap on an SD card, and it makes a bad change recoverable: *"I widened the retune window and now
it hunts"* becomes a rollback rather than a re-derivation. The web UI lists the versions and can
restore any of them.

#### 8B.5.4b Restore, and why it is not automatic

The backup's purpose is surviving a board replacement or a flash failure. Restoring carries a real
hazard: **a card from a different tuner would load the wrong calibration**, and the tuner would
then compute matches from another antenna's measurements while reporting that all is well.

Both tiers therefore carry a **tuner identity**, and restore is gated on it:

| Internal flash state | Card present and ID matches | Behavior |
|:--|:--|:--|
| Valid | yes | Normal. Card is a mirror; nothing is read from it |
| **Blank** (new board, first boot) | yes | **Offer restore** in the web UI, logged prominently. Not silent |
| **Corrupt** (checksum fail) | yes | **Flag as a fault.** Do not auto-restore — a corrupt flash may indicate a hardware problem that restoring would mask |
| Any | ID mismatch | **Refuse.** Report the mismatch; require an explicit "adopt this card" action |

#### 8B.5.4c One deliberate exception: recovery

Making the card purely an output removes a useful escape hatch — *"I set a static IP wrong and can
now no longer reach the web UI."* With no config input path, the only remedy would be opening the
chamber and reflashing.

So: **one file, read once.** If `/recovery.cfg` exists at boot it is applied, logged loudly, and
then **renamed to `/recovery.applied`** so it cannot take effect twice.

```
# /recovery.cfg  -- applied once at boot, then renamed
net.mode      = dhcp
hostname      = tuner
```

Scope is limited to **network and hostname settings only**. It cannot set the fault policy
(8B.4a-1 requires that to be a local action at the box), cannot alter calibration, and cannot
clear a latched fault. It exists to restore reachability, nothing more.

#### 8B.5.4d Mirrored content

```json
{
  "tuner_id":   "...",
  "saved":      "2026-10-21T17:45:12Z",
  "network":    { "mode": "dhcp", "hostname": "tuner", "ip": null },
  "thresholds": { "retune_swr": 1.5, "retune_freq_pct": 0.5 },
  "fault":      { "policy": "strict" },
  "derate":     { "160m": true },
  "calibration":{ "detector_curves": [], "ad8302": {} },
  "profiles":   { "160m": {}, "80m": {} }
}
```

`fault.policy` is mirrored for the record and for restore, but **a restore cannot promote the
policy** — anything less strict than the internal value is refused and flagged (8B.4a-1).

#### 8B.5.5 Endurance and corruption

- **Do not write continuously.** Buffer the fault log in RAM and flush on fault events, on state
  transitions, and on a slow timer. A tuner that writes telemetry at 20 Hz will wear a card out.
- **Write atomically**: write to a temporary file, flush, then rename. Power loss mid-write then
  leaves the previous good file rather than a truncated one.
- **Treat a corrupt card as an absent card.** Mount failure, bad checksum or unparseable config all
  fall back to 8B.5.3 behavior, logged. Never halt on a storage problem.
- **Card removal is not hot-swap safe.** Pull it with the tuner idle, or accept a possibly
  truncated log.

#### 8B.5.6 Physical access

The Control chamber is sealed (Section 8E). Reaching the card means sliding out the control cassette, which is a
deliberate occasional operation rather than routine — acceptable, because **the web UI is the
normal way to change configuration.** The card is for backup, transfer, and inspection.

*Rev 3.7c:* a **panel-mount microSD extender (Adafruit 6070)** now brings the slot to the cassette face,
below the encoders (TUNER-E-202, F). The card is reached from outside without touching the cassette.
Three consequences:

- **No card detect.** The extender's plug stays in the Teensy's socket, so that socket's card-detect always
  reads "inserted". The firmware learns whether a card is there by using it. A failed operation marks it
  gone, and while it is gone it is re-mounted every 5 s (§8B.6).
- **Sealing.** The slot is an opening in the IP5X chamber (§8E). Seat the extender's flange on the panel
  gasket and keep a card in the slot, which closes most of it.
- **A longer SDIO path.** The card's lines now run through ~18 cm of ribbon. At commissioning, check that
  the card mounts and writes reliably; if it does not, bring the SDIO clock down.

Removal is still not hot-swap safe (§8B.5.5).

> **Placement constraint:** the Teensy's SD socket needs insertion and ejection clearance. Orient
> the module so the socket faces the cassette front or an edge, and keep that approach clear when
> laying out the Control board. *Met Rev 3.7c:* the Teensy lies flat on its sockets, parallel to the
> board, turned so its long axis runs down from the board's top edge with the SD socket at that edge.
> The board stands on edge in the cassette, so that edge points up and is open once the cassette
> slides out. Its USB end faces a strip kept
> free of parts. It plugs into two 1×24 socket strips, so it can also come out.

### 8B.6 Firmware — milestone 1 *(Rev 3.7c)*

`fw/` holds the portable core: §8B.1–§8B.4b in C++17, with no Arduino, heap, exceptions or RTTI. Its
host tests run the state machine in closed loop against a model of the tuner (`fw/README.md`). The
solver matches `nec/cap_demand.py` at all 29 band-edge points. The Teensy layer comes next.

The tests settled what §8B left open:

| Question | Decision |
|:--|:--|
| Sign of θ (§6A.7) | A stored prior decides only when one hypothesis is clearly nearer it, and only once per tune. Otherwise a 10 % C2 probe decides. Every VERIFY repeats the test across the move just made, so a wrong prior costs one attempt |
| Stored profiles (§7.6, §8B.5) | One per 1 % segment of each band, 50 in all. They are seeded from the NEC model and replaced by each good tune. One per band was tried and fails at the edges of 80 m and 10 m |
| Starting far off | Above 5:1 a fraction of a dB moves the R estimate several-fold, so the tuner drives to the stored setting first. Solves from such readings are coarse moves: at most 3, outside the 3 attempts. A move that more than doubles the best SWR is undone |
| Converged | 1.2:1. After the 3rd attempt a match under the 1.5:1 retune threshold is kept; above it, TUNE FAILED |
| Over-SWR trip | A fault only once MATCHED. A tune starts from a mismatch, and the comparator holds the amplifier off meanwhile |
| PTT and moves | The vote stays down through PROBE and MOVE, and until the motion layer reports stopped. A move goes out 30 ms after the vote drops. A move in progress finishes if the carrier ends; the bypass key stops it |
| Encoder verify (§8B.3) | Done in the motion layer, in counts, and reported when the move completes. A move still running after 15 s is a position fault |

**Tested envelope, and so the commissioning target** (§9 item 54):

- The elements are within ±3 % of their calibration curves.
- The AD8302 is within ±0.25 dB and ±2° after the §6A.8 calibration.
- The feeder can be anywhere in the 39–42 ft, VF 0.93–0.97 spread.
- On 10 m, the feedpoint can be anywhere in the item 10 uncertainty.

With the factory priors, every band edge tunes from every start: most in one attempt, none in more
than three. Over 1000 random draws inside those bounds, every seeded draw matches. Cold draws (no
prior, which in practice means out of band) match 99.4 %, and the rest end in a fault.

**The Teensy layer** (`fw/teensy/`, PlatformIO) builds but has not run: the boards are not built.

- **Boot** follows §8B.4b. RTWDOG is armed before MCU_PERMIT can rise.
- **Moves:** a 50 kHz timer interrupt steps all three axes along one planned path (§8B.3), held to
  2 rev/s in the roller's slow zone (§7.2). The encoders are checked after every move, and the drivers
  are off at idle.
- **Measurement:** the bridge is averaged over each 200 ms counter gate and read against the AD8302's
  VREF.
- **Storage:** the fault record, mode, profiles and last positions go to EEPROM under a CRC.
- **Local interface:** a USB console gives ack, clear, tune and the mode until the panel exists.
- **Before power-up,** set what the build fixes, all in `fw/teensy/config.hpp`:
  - microstepping, DRV_EN polarity and which limit input is which end;
  - each axis's direction and encoder zero;
  - the capacitors' turns (§9 item 48) and the element curves (§9 item 54).

  The roller's curve defaults to the NEC model (`nec/out/roller_vna_k*_deck.csv`).

**Calibration, the RF path and the local panel:**

- **RF path:** a change follows §5.5. The vote is held 100 ms, the relays switch, and the coil
  currents are read after 25 ms; only then is the vote given back. The first key-down is checked at
  the cal-load detector (§6B.3a). Any disagreement is a class B fault and returns the relays to TUNE.
- **Off TUNE:** nothing tunes in AUX or CAL, and an over-SWR trip there is a fault.
- **Calibration** runs one band at a time from the console or the panel, as §6A.8 above describes.
  It is stored with the fault record in an authoritative EEPROM record. That record is kept twice and
  written alternately, so a profile write or a power cut can never take the calibration with it.
- **Panel:** the Nextion is a text terminal (one page, ten rows, specified in `fw/README.md`), and
  every screen is drawn and tested in the core. A class C clear unlocks only once the fault list has
  been scrolled to its end (§8B.4f.1).
- **Manual override** (§7.5) jogs one element through the state machine, under the same PTT rules as a
  tune's moves.
- **Before power-up,** also set the K1/K2 coil-current threshold, the cal-load detector's RF
  threshold and the knob wiring.

**Records, storage and the link** (§8B.4a-1, §8B.5, §8C):

- **Qualification:** the PERMISSIVE counters are kept with the fault record. A mechanical fault starts
  them over, and promotion is refused until they are met.
- **Event log:** every fault, acknowledgement, clear, mode and path change, finished tune, calibration,
  boot and card event is numbered. The SD log and each link client read what they have not seen, so a
  dropped link loses nothing still in the log (§8C.6).
- **SD card:** it mirrors the flash as §8B.5.4 sets out. It keeps versioned backups and a tuner
  identity, writes atomically, applies `/recovery.cfg` once, and refuses a restore that would promote
  the policy.
- **Link protocol:** the commands of §8C.5 plus PATH and CAL, with mode changes, class C clears, the
  bypass and jogging refused as local only. A number that is not a plain finite one (`NAN`, `5X`) is
  refused rather than read as 0, and a calibration point above 2000 W is taken as a typo.
- **Transport:** on QNEthernet (§8C.3.3), with no call that waits.
  - The line protocol is on TCP 4600, and the page and its WebSocket are on port 80.
  - Only the tuner's own subnet is served (§8C.7), which also refuses anything port-forwarded in.
  - mDNS answers `tuner.local`, and SNTP from `pool.ntp.org` sets the RTC for the logs. It believes only
    the server it asked, and it handles the NTP rollover in 2036.

## Section 8C — Remote Head and Control Link

The tuner is autonomous. The remote head is a **monitor and convenience, never a dependency** —
every protective function lives at the box and works with the link dead.

### 8C.1 Correction to Section 7.5

Section 7.5 requires that *"bypass and emergency-stop must work from both ends."* **Half of that
was wrong.**

- **Emergency stop from both ends: correct, and retained.**
- **Bypass from both ends: withdrawn.** The manual bypass of 8B.4d defeats the over-SWR trip and
  the relay sequencing interlock. Making it remotely reachable directly contradicts the reason it
  is deliberately local, keyed, and physically awkward. **Bypass stays local-only.**

### 8C.2 The bench emergency stop needs no wire to the tuner

The obvious implementation — a stop button at the bench signalling the tuner — would run a
conductor between the two grounds and reintroduce exactly the loop Section 8A.3 exists to break.

Instead: **the bench-side stop breaks the amplifier keying line locally, at the bench.**

```
[ rig PTT out ] --> [ BENCH E-STOP (NC) ] --> [ amp keying in ]
                            |
                    no connection to the tuner
```

This is both safer and simpler. It needs no link, no power, and no firmware; it cannot be defeated
by a software fault or a dropped connection; and it acts at the source rather than asking a remote
device to act on your behalf. A normally-closed contact in series with the keying line is the most
direct stop available.

### 8C.3 Physical layer — Ethernet for data, optical fiber for the interlock

> **Revised twice.** An earlier draft specified Ethernet throughout; the next rejected copper to
> the bench outright on surge grounds. **Both were wrong at the edges.** The link carries two jobs
> with very different risk tolerance, and they should not share a medium.

| Job | Medium | Why |
|:--|:--|:--|
| **Data, telemetry, web UI** | **Ethernet** + surge arrestor at the entry | Losing it costs visibility, not safety. The Teensy 4.1 has the MAC |
| **Interlock permissive** | **POF, dedicated strand** | Safety-critical. Isolated, no protocol, no stack, nothing to destroy |

#### 8C.3.1 Correcting the surge argument

The earlier rejection of Ethernet overstated the marginal risk, and one of its implied remedies was
backwards:

- **Shielding does not help.** The concern is longitudinal potential difference between two
  grounding points, not RF ingress. **Shielded (STP) cable makes it worse** — the shield is a
  conductor bonded at both ends, a direct metallic path from the arrestor baseplate to house
  ground that bypasses the magjack transformers. **Specify UTP, not STP.**
- **The coax already bridges those grounds.** The shield runs from the tuner (bonded to the
  baseplate, Section 8A.2) to the rig at the bench. Ethernet adds a second, thinner path — it does
  not create the first one.
- The real exposure is therefore **PHY destruction in a surge event**, not a new safety hazard.
  Mitigate with an **Ethernet surge arrestor at the entry panel, bonded to the baseplate**, and
  accept the PHYs as sacrificial.

#### 8C.3.2 Why the interlock still stays optical

Not because of lightning. Because **a hardware permissive that software cannot forge is worth
keeping as hardware.** Section 7.4's permissive is the logical AND of the protective conditions,
modulated at 10 kHz, carried on its own light path. No network stack, hung or otherwise, can
assert it. That property is independent of the data link's medium and is the reason the two jobs
are separated at all.

#### 8C.3.3 Implementation

**Ethernet.** The Teensy 4.1 brings RMII out on a **separate 2×3 header, not the main edge pins**,
so Ethernet consumes **zero control IO**. External parts: an Ethernet magjack (Link-PP LPJ4012AHNL
or equivalent), a 0.1 µF capacitor, and a short ribbon. PJRC's Ethernet kit supplies these on a
small carrier board, which can mount on the chamber wall — **the Control board needs nothing for
Ethernet at all.** Libraries: QNEthernet (lwIP-based) or NativeEthernet. *Rev 3.7c:* **QNEthernet**
(§8B.6). NativeEthernet's static-address `begin()` waits for the link with no timeout, so an unplugged
cable would hang the boot. QNEthernet's DHCP and static starts both return at once. It is
AGPL-3.0-or-later, so a built image carries the AGPL's network clause, and the page the tuner serves
links to the source (`NOTICE`).

**Fiber.** One POF strand, HFBR-15xx/25xx class transceivers, carrying the modulated permissive.
Terminates with a razor blade and a crimp connector — no polishing, no fusion splicing.
*Rev 3.7a:* the HFBR-1521Z stays on the control board; the fiber enters through a **Ø0.375″ hole with a Heyco 2020
nylon snap bushing** in the floor (TUNER-E-206). Bare fiber is non-conductive, so the hole costs nothing in
shielding. Bulkhead adapters (HFBR-4505Z/4515Z) exist but carry long lead times. Ethernet enters
through a **Switchcraft EHRJ45P5E** (thermoplastic, unshielded — §8C.3.1), Ø0.945″ with two
countersunk screws.

**Rejected:** Wi-Fi, on its merits — an RF transmitter at the antenna entry point, inches from a
receive-path directional coupler.

### 8C.4 Two-part head

**(a) Bench box** — the E-STOP and a permissive-state LED only; everything else is in the web UI
(b). *The earlier physical bench panel with TUNE, ACK and status LEDs is in §11.9.*

**(b) Software UI — served directly from the tuner over Ethernet**

```
[ Teensy 4.1 ] --Ethernet--> LAN --> browser on any device
[ comparator ] --POF interlock--> [ bench keying box ]   (no software in this path)
```

With Ethernet carrying data, the web UI is served by the tuner itself and the bench-side
single-board computer disappears. What remains at the bench is a **small passive keying box**:
the POF receiver, the opto-MOSFET keying switch (Section 7.4), the hardwired E-STOP (Section
8C.2), and status LEDs driven from the interlock state. No processor, no firmware.

TUNE and ACK move into the web UI; the E-STOP stays physical and hardwired, as it must.

The UI provides:

- Live SWR, forward and reflected power, measured frequency
- Element positions — both capacitors and the roller — and the TUNE / AUX / CAL mode (§6B)
- **Feeder current imbalance** from the bifilar CT (Section 2.2) — the only place balance is visible
- **Live dissipation estimate and derate status** (Section 1.7.1), with a warning when the 160 m
  limit is approached
- Fault log with timestamp, frequency and state
- Calibration data entry (Section 6A.8)
- Current fault-policy mode — **read-only; mode changes are local (8B.4a-1)**

### 8C.5 Protocol and telemetry

Line-oriented text over TCP. Debuggable with `nc` or a terminal emulator from any machine on the
LAN, which matters when the thing is mounted on a garage wall.

| Aspect | Specification |
|:--|:--|
| Transport | **Ethernet (TCP for commands, WebSocket for telemetry)**; interlock is a separate POF strand carrying no protocol |
| Framing | Line-oriented text, one record per line, checksummed |
| Telemetry rate | 10–20 Hz SWR/power; 5 Hz frequency; positions on change |
| Fault events | **Pushed immediately**, never discovered by polling |
| Latency | < 100 ms end to end |
| Bandwidth | A few hundred bytes/second against 100 Mbit/s — negligible |

**Command set:** `TUNE`, `ACK`, `QUERY`, `SUBSCRIBE`, `GET_LOG`. Deliberately absent: fault-policy
mode changes, class C fault clears, and bypass — all local-only by design.

**Bandwidth is a non-issue on Ethernet** — a 20 Hz telemetry record of ~40 bytes is 800 bytes/s
against 100 Mbit/s. The point worth preserving from the serial design is that **fault events are
pushed, never polled**, so a congested or stalled link cannot delay a fault report. It can only
fail to deliver it, which the interlock strand makes safe.

**The interlock strand carries no protocol at all.** It is a 10 kHz tone, present or absent.

### 8C.6 Link loss behavior

**Link loss degrades visibility, not safety.** Every protective function — the over-SWR comparator,
the limit switches, the relay sequencing, the PTT permissive — is hardware at the tuner and
entirely independent of the link.

On link loss:

| | Behavior |
|:--|:--|
| Tuner | **Continues autonomously.** Holds its solution, retunes on frequency change as normal |
| Transmit | **Permitted.** Hardware protection is intact; the link was never in that path |
| Bench box | Web UI shows link lost; TUNE and ACK unavailable; E-STOP and permissive LED unaffected (hardwired / optical, Section 8C.2) |
| Interlock | **Unaffected — separate fiber strand.** Permissive continues or withdraws on its own merits |
| Telemetry | Buffered at the tuner, replayed on reconnect so no fault events are lost |
| Medium | Data loss is Ethernet; the interlock strand is **optical and unaffected** by it |

Deliberately **not** implemented: inhibiting transmit on link loss. That would couple a convenience
path to a safety function and create a new failure mode — a flaky cable grounding the station —
while adding nothing, since protection never depended on the link.

### 8C.7 Network exposure

**The tuner now holds a LAN address.** The earlier design kept it off the network entirely by
speaking serial to a bench adapter; adopting Ethernet for data trades that structural protection
for a policy one. That trade is acceptable **only because the interlock is on its own fiber
strand** — a compromised or hung network stack cannot assert the transmit permissive (Section
7.4). Were the permissive carried over Ethernet, this trade would not be acceptable.

Exposure therefore applies to the tuner directly:

- **Never port-forward it.** No remote access from outside the LAN.
- Prefer a dedicated VLAN, or a direct point-to-point run from the tuner to a second NIC at the
  bench, keeping it off the house LAN entirely.
- Bind the HTTP service to the tuner's own subnet, not `0.0.0.0`, if the library allows it.
- The practical risk is nuisance rather than danger: a spurious `TUNE` drops PTT before moving
  anything (Section 8B.3), so it cannot hot-switch a relay or move an element under power. It can
  waste a tuning cycle and some roller travel.

---

## Section 8D — Balanced Output Termination

Two feedthrough insulators on the **fixed top panel**, carrying the 600 Ω balanced output to the
entry panel: 6.03″ apart **parallel to the wall**, near the rear (TUNER-E-205), so the jumper rises
straight to the strain insulator at the entry panel above. Upward-facing ceramic collects dust: fit
an **insulating** dust cover over both (not a grounded hood, which would sit inside the 1.5″
clearance) and keep the §8D.6 cleaning interval. Named in every revision, specified in none.

### 8D.1 Voltage rating

From the band-edge envelope (Section 1.2b, 40 ft feeder):

```
differential, terminal to terminal  : 4,191 V peak  (2,964 V rms)
ideal balanced, each terminal to gnd:   2,096 V peak
design basis, assume full V on one  :   4,191 V peak
```

**Rate each feedthrough for the full differential voltage, not half.** In a perfectly balanced
system each terminal swings ±half, but this is a floating-deck approximation (Section 2.2) with
C_leg1-chassis ≈ 20 pF (§2.2, Rev 3.7c; ≈ 23 pF before the deck raise) against C_leg2-chassis ≈ 3.0 pF before trimming. The split is asymmetric by
construction, and a mistrimmed or drifted vane puts more of the swing on one terminal. Designing
for half the differential bets the insulator on a trim adjustment holding.

**Specify ≥10 kV peak** transmitter-grade ceramic or steatite feedthroughs — 2.4× over envelope.

**Creepage, not just air gap, is the binding constraint.** The failure path on a feedthrough is
along the insulator *surface*, where contamination and humidity reduce withstand far below the air
figure. Clean dry ceramic manages roughly 1–2 kV per inch of surface path, so 4.2 kV wants 2–4″ of
creepage. That is what the skirts and ribs on transmitter-grade ceramic exist to provide.

> **Do not substitute a bolt through a plastic or phenolic block.** It will have the air gap and
> none of the creepage, and if the garage climate control ever fails it will track and carbonize.

### 8D.2 Terminal spacing — match the feeder, do not pick a round number

Spacing the terminals arbitrarily creates a lumped impedance discontinuity right at the tuner
output. Match the feeder's own conductor spacing, from `Z₀ = 276·log₁₀(2S/d)`:

| Conductor | Diameter | Spacing for 600 Ω |
|:--|--:|--:|
| #10 AWG | 0.1019″ | 7.60″ |
| **#12 AWG** | **0.0808″** | **6.03″** |
| #14 AWG | 0.0641″ | 4.78″ |
| #16 AWG | 0.0508″ | 3.79″ |

**Measure the actual line and match it.** For #12 open-wire — the same gauge as the antenna — that
is ≈ 6″, which fits across the 15.87″ rear face of the RF bay with room for the clearance below.

Spacing also satisfies the differential breakdown requirement comfortably: 6″ of air at 4.2 kV is
an order of magnitude of margin.

### 8D.3 Clearance and current

- **Terminal to grounded chassis: 1.50″ minimum**, per Section 3.2. At 4.2 kV peak with edged
  electrodes this holds 3.5–7× margin, consistent with the rest of the HV layout.
- **Conductor current: 14 A RMS** worst case (160 m band edges, Section 1.2b). A ¼″–⅜″ brass or
  copper stud carries that trivially; size for mechanical robustness, not ampacity.
- **Radius every edge ≥ 1/16″** on the terminal hardware — corona suppression, same rule as the
  rest of the HV path.

### 8D.4 Strain relief — the feedthrough carries no mechanical load

Open-wire line is mechanically substantial and, outdoors, carries wind load. A ceramic feedthrough
in bending is a feedthrough that cracks.

```
[ entry panel ] --- anchored strain insulator --- [ short flexible jumper ] --- [ feedthroughs ]
       |                       |                          |
   arrestors,          takes ALL mechanical          maintains ~6" spacing,
   bonded baseplate    load; bolted to wall          slack enough to absorb movement
                       or enclosure frame
```

The line terminates on a strain insulator anchored to the wall or the enclosure frame. A short
flexible jumper — maintaining the same conductor spacing — runs from there to the feedthroughs.
**No tension reaches the ceramic.**

Keep the jumper short; it is an unshielded balanced run at 4.2 kV inside the garage. A foot or two
is acceptable, several feet is not.

### 8D.5 Static drain — the arrestors are load-bearing, not redundant

A design note worth stating explicitly, because it is easy to assume otherwise:

**DC paths through the tuner (Rev 3.7b, §9 item 46).** Earlier revisions said neither output
terminal has a DC path to ground, "both sitting behind series capacitors". That was never true — the
old pad sat *in parallel* with C2 (C2 + pad = one 220–875 pF range), never in series with leg 1:

| Point | DC path to chassis | Through |
|:--|:--|:--|
| **Leg 1** (the deck terminal) | **Yes, ≈ 0.05 Ω** | The input choke's braid — 9.6 ft of RG-400 (Rev 3.7c; was ~31 ft of RG-142B, ≈ 0.15 Ω), one continuous conductor from the deck end to the grounded shelf coax bulkhead. A choke blocks common-mode **RF**; at DC it is a short. The deck "floats" at RF only |
| Network node (C1 / roller / C2) | Yes | Roller (DC short) → deck → choke braid |
| **Leg 2** | **None — floats** | C2 is the only element between leg 2 and the grounded node |
| C1 input (choke center) | Amplifier-dependent | Through the coax center to the amp's output network |

Consequences: **static on leg 2 can only leave through the arrestors** — precipitation static on a
wire antenna builds to many kV, all of it across C2 (10 kV test) until something arcs; and **a surge on
leg 1 returns through the choke braid** into the shelf bulkhead and chassis, which is acceptable
only because the arrestors sit upstream.

**Leg 2 static bleed — across C2, not to ground.** Because the node is DC-grounded, a resistor
*across C2* drains leg 2, and it only ever sees C2's voltage (≤ 2.41 kV pk, §5.1) instead of the line
voltage: **100 MΩ dissipates ≈ 0.03 W** at 1500 W worst case (47 MΩ ≈ 0.06 W), against 8.8 W for a
1 MΩ output-to-ground bleeder (table below). Use a ≥ 10 kV-rated thick-film HV resistor (or a string
of two 50 MΩ / 5 kV), mounted between C2's two terminals on the deck. Leg 2's static then drains in a
fraction of a second, and C2 never accumulates it. **Commissioning ohmmeter checks:** deck and leg 1 to
chassis < 1 Ω; node to deck ≈ 0 Ω (roller); leg 2 to chassis ≈ 100 MΩ (the bleed, via the node);
nothing lower.

Static drain is specified to depend **entirely** on the arrestors and bonded baseplate at the entry
panel. That makes them load-bearing rather than belt-and-braces, and worth verifying rather than
assuming: confirm the arrestors are on the **antenna side** of the tuner, which they are in the
specified topology.

**Do not add a bleeder from an output terminal to ground.** It sees the full line voltage and
dissipates continuously at full power (the C2 bleed above avoids exactly this):

| Bleeder | Continuous dissipation at 1500 W |
|--:|--:|
| 1 MΩ | 8.8 W |
| 10 MΩ | 0.88 W |
| 47 MΩ | 0.19 W |

Any value low enough to drain static usefully also wastes real power and requires a high-voltage
resistor string. An RF choke to ground would drain DC without the dissipation, but it shunts the
output — roughly 11 kΩ at 1.8 MHz for 1 mH, a ~5% perturbation against the load on the band where
the match is already hardest. **Neither is justified when the entry panel already does the job.**

### 8D.6 Environment

The feedthroughs are indoors — the wall penetration happens at the entry panel, not at the tuner —
so they are not weather-exposed. But a garage condenses if its climate control fails, and condensation on ceramic
collapses creepage.

- Keep the enclosure sealed except for the filtered cooling path (Section 8).
- Fit a **drip loop** in the outdoor line before the entry panel so water does not track inward.
- Inspect and clean the feedthrough surfaces at the same interval as the roller contact
  (Section 5.3a). Both are surface-condition failures and both are invisible until they arc.

---

## Section 8E — Environmental Protection

Site: **interior of a sealed, climate-controlled garage** (in-wall AC/heat combination unit),
Missouri. Scratch-built aluminum enclosure, mounted on the inside wall at the isolation box.

> **Premise revised.** Earlier drafts of this section assumed an *unheated* garage tracking outdoor
> conditions — a −26 °C to +43 °C swing with uncontrolled humidity. With climate control the
> operating environment is far milder and most of that specification was over-engineered. What
> follows replaces it.

### 8E.1 Two envelopes, not one

Climate control is a **convenience that can fail**. The AC fails in August, the heat fails in
January, a breaker trips, or the unit is simply off during shoulder seasons. The design therefore
uses two envelopes, which map directly onto the operating and storage ratings on component
datasheets:

| Envelope | Range | Requirement |
|:--|:--|:--|
| **Operating** — climate control working | ~10 to 30 °C, humidity controlled | Full performance |
| **Survival** — climate control off or failed | −26 to +43 °C, uncontrolled humidity | **No damage.** Need not operate |

**Nothing in the design may depend on climate control being continuous.** But nothing needs to be
specified to work through its absence either.

### 8E.2 What this removes

Relative to the unheated-garage specification:

| Previously specified | Now |
|:--|:--|
| Thermostatic heater, 25–50 W | **Not required.** AC dehumidifies; interior stays above dew point. Retain the *provision* — a mounting point and a spare rail — in case monitoring shows otherwise |
| Industrial-temp (−40/+85 °C) fiber converters | **Commercial 0–50 °C is adequate** for operating; confirm storage rating covers survival |
| Low-temperature synthetic leadscrew grease | **Standard grease is fine.** The cold-start torque problem does not arise at 10 °C. Type is still constrained: non-tacky, non-conductive, non-silicone (§5.1b) |
| Cold-start commissioning check after a hard freeze | **Downgraded to optional.** Worth one check if the garage is ever left unconditioned over a winter |
| TFT display cold limit (−20 °C) | **Non-issue** in the operating envelope |
| Electrolytic cold-ESR derating | **Non-issue.** Normal temperature derating still applies for life |

### 8E.3 What still applies

Climate control does not make a garage a clean room.

**Dust — still real.** Vehicles, power tools, sawdust and drywall dust all live in garages
regardless of conditioning. **Keep the filtered intake** on the RF chamber (Section 8) and keep
**IP5X** as the target for the three sealed chambers.

**Insects — reduced, not eliminated.** A sealed garage still opens its overhead door, and mud
daubers specifically hunt for cavities. A mud nest bridging the 1.50″ HV clearance is a flashover
waiting to happen, and the mitigation costs almost nothing:

| Mesh | Aperture | Excludes |
|:--|--:|:--|
| 16 mesh | 1.6 mm | Mud daubers, wasps |
| **30–40 mesh** | **0.4–0.6 mm** | **Spiders, ants, small insects** |

**Keep 30–40 mesh stainless screen on every opening** — intake, exhaust, drain. It sits behind the
honeycomb EMI vents, not instead of them; 1/8″ honeycomb cells exclude nothing biological. Account
for the added pressure drop in blower selection: specify for **static pressure, not free-air CFM**.

**Membrane vents — keep them.** A PTFE pressure-equalizing vent per sealed chamber still earns its
place. They cost very little, they prevent the sealed chambers pumping dirty air through their
seams as the box heats and cools, and they are the one measure that keeps working when climate
control is not.

**Drain — now optional.** A screened low-point drain in the RF chamber remains cheap insurance, but
with conditioned air the case for it is much weaker. Fit it if convenient.

### 8E.4 IP targets

Unchanged in substance, and the reasoning still holds: **IP describes ingress from outside and does
not address condensation at all.**

| Chamber | Treatment | Target |
|:--|:--|:--|
| **RF Tank** | **Ventilated** — filtered intake, honeycomb exhaust, insect screen | IP not applicable |
| **Sampler** | Sealed, membrane vent | **IP5X** |
| **Control** | Sealed, membrane vent | **IP5X** |
| **Motor** | Sealed, membrane vent | **IP5X** |

Liquids digit is **IPX0** and that is correct — there is no water source in a conditioned garage
interior. The lip seals on the Motor → RF Tank shaft bushings remain, since they separate a sealed
chamber from a ventilated one.

> Still do not write "IP65" on the drawing. It is unachievable on the ventilated chamber and
> meaningless on the others.

### 8E.5 Heat rejected into the conditioned space

The tuner now dumps its dissipation into a space something is paying to cool:

| Tuner dissipation | Heat load | Share of an 8k BTU unit |
|--:|--:|--:|
| 38 W *(100 W operating, typical)* | 130 BTU/hr | 1.6% |
| 200 W *(cooling design point)* | 682 BTU/hr | 8.5% |
| 400 W | 1,365 BTU/hr | 17.1% |

At typical operating power this is **negligible**. At the 200 W design point it is noticeable but
minor. The ~400–568 W case occurs only on 160 m key-down at full power, which is already derated to
≈ 530 W output by Section 1.7.1 — so the worst sustained case is bounded well below it.

No action required; recorded so that a future "why is the garage warm during contests" question has
an answer.

### 8E.6 Gasketing a scratch-built box

**Decided (G-1): conductive-elastomer gasket** on every frame flange under a panel and on both faces
of the shelf (TUNER-E-202 to E-208). It does both jobs — RF and dust/moisture — in one part, but needs
a flat face to compress evenly: the bolted angle frame gives every panel a 1″ flange to seal against,
which removes the flatness objection. **Check each flange with a straightedge before fitting the
gasket** (fabrication QA); a plain sheared edge on 14 ga sheet would not seal.

*BeCu finger stock and the two-gasket option are superseded — see §11.7.*

---

## Section 9 — Open Items

| # | Item | Status |
|:--|:--|:--|
| 1 | **Feeder trim** — cut long, finish with a removable ~2 ft jumper, trim empirically against measured SWR (Section 1.4) | **BY DESIGN** |
| 2 | **Roller wheel / bus rod contact condition** — inspect and clean before assembly; 18.4 A RMS localizes at any oxidation | **REQUIRED** |
| 2a | **Mechanical fault policy qualification** — run STRICT until 100 tune cycles / 50 h / zero mechanical faults, then consider PERMISSIVE (Section 8B.4a-1) | **COMMISSIONING TASK** |
| 3 | ~~Choke self-resonance (design C)~~ — **SUPERSEDED Rev 3.7c:** the air-core choke gave way to the #61 ferrite choke in the RF bay (§6); its NEC series-resonance work is in §11.11. Verifying the new choke installed is item 49 | **SUPERSEDED** (→ item 49) |
| 4 | ~~Remote head / network link~~ — **CLOSED**, specified in Section 8C (Ethernet data, POF interlock, web UI, hardwired bench E-STOP) | **CLOSED** |
| 4a | ~~Frequency counter~~ — **CLOSED**, specified in Sections 6A.10 and 8B.0.1 (÷1024 prescaler, 200 ms gate, 5.1 kHz resolution) | **CLOSED** |
| 4b | ~~Tuner power supply~~ — **CLOSED**, specified in Section 8A. *New sub-item: verify entry-panel bonding to service ground (8A.3).* | **CLOSED** |
| 4c | ~~Firmware state machine~~ — **CLOSED**, specified in Section 8B | **CLOSED** |
| 5 | **RF bay 3-D mock-up** in cardboard with actual components before cutting metal | **REQUIRED** |
| 6 | ~~Balanced output feedthroughs~~ — **CLOSED**, specified in Section 8D (≥10 kV ceramic, spacing matched to feeder, strain relief off the ceramic) | **CLOSED** |
| 7 | ~~Bruene bridge design~~ — **CLOSED**, specified in Section 6A as a Stockton coupler with dual magnitude/vector paths | **CLOSED** |
| 8 | ~~Grounding scheme~~ — **CLOSED**, single-point at the arrestor baseplate (Section 8A.2); the Ethernet ground loop and how it is broken are in 8A.3 | **CLOSED** |
| 9 | **Antenna end height** assumed 10 ft; envelope covers 6–15 ft so this is confirmation, not a blocker | **OPEN (low risk)** |
| 10 | ~~10 m reactance ±10%~~ — *Closed Rev 3.7c* (`nec/conv10.py`, `nec/out/conv10.txt`). X still moves about −25 Ω per 300-segment step at 1200 per leg, about halving each step. The extrapolated limit and a fixed-gap feed model, which only refines the legs, differ from the design values by up to ~20 % in R and ~200 Ω in X: near the antinode the feedpoint depends on the feed geometry itself. Over R × 0.8–1.2, X ± 250 Ω, the 39–42 ft / VF 0.93–0.97 feeder sweep and both C1 parts, the network matches 611 of 648 cases within ratings (V_C1 ≤ 2.2 kV pk, V_C2 ≤ 1.0 kV pk, roller ≤ 8.3 A). Of the misses, 31 are the feeder corners `cap_demand.py` already finds at nominal Z. 6 come from the uncertainty, all at the X ± 250 Ω corner next to those feeder corners. Every miss is C1 asking ~15 pF against its 20–25 pF minimum, which the item 1 feeder trim moves out of. No part changes | **CLOSED** Rev 3.7c |
| 11 | ~~Network loss / efficiency~~ — **CLOSED**, derived in Section 1.7; 160 m derate table in 1.7.1 | **CLOSED** |
| 12 | **Measure actual roller Q** once assembled — the 150 vs 250 assumption swings the 160 m derate by 1.7× | **COMMISSIONING TASK** |
| 13 | ~~Enclosure environmental spec~~ — **CLOSED**, Section 8E revised for a climate-controlled garage interior: IP5X sealed chambers, ventilated RF bay, membrane vents, 30–40 mesh, heater provision only | **CLOSED** |
| 14 | **Amplifier keying interface** — SB-220 identified; confirm by measurement which keying regime is present (Section 7.4.4). Switch is spec'd defensively for the stock +120 V case either way | **OPEN — measurement only** |
| 15 | ~~Utility column re-order~~ to Sampler / Control / Motor, local UI to side panel | **SUPERSEDED** by the §3.0 utility layer (item 29) |
| 16 | ~~Crossings 6 and 7~~ — **Resolved Rev 3.7a, revised Rev 3.7b:** Control → RF tank row in §7.3; filtered DE-9 J-E (FCE17-E09SM-290) at the bulkhead, discrete 0.01 µF FT1–FT4 in the shelf (3 used + 1 spare; relay coils removed with the pad and link) (§7.3a) | **RESOLVED** |
| 17 | **Amplifier T/R relay release time** — scope RF decay after permissive withdrawal; confirm the 30 ms blanking covers it (Section 7.4.5) | **OPEN — bench measurement** |
| 18 | ~~Cold-start motion check~~ — **DOWNGRADED TO OPTIONAL**; garage is climate controlled (Section 8E.2). Worth one check only if left unconditioned over a winter | **OPTIONAL** |
| 19 | ~~Flange flatness / gasket selection~~ — **RESOLVED (G-1, Rev 3.7a):** conductive elastomer on the angle-frame flanges (§8E.6). Fabrication QA: straightedge-check each flange before fitting the gasket | **RESOLVED** |
| 20 | **G10 shaft dielectric dissipation** — calculated ~1.25 W per shaft at 30 MHz / 4,191 V (Section 7.1a). First identified tank loss that is not the capacitors; scales as V². Confirm by touch after a long 10 m carrier run | **OPEN — commissioning check** |
| 21 | **Oldham tongue/slot fit** — backlash is set entirely by this clearance. Measure total drive-train lash at the element with a dial indicator before trusting a stored profile (Section 7.1a) | **OPEN — fabrication QA** |
| 22 | ~~Chamber layout dimensioning~~ — §4 sub-wall 5.37″ vs §6 bay depth 5.00″. Superseded by the §3.0 utility layer; the 5.00″ layer height vs NEMA 23 + takeoff (5.22″) carries on as item 30(b) | **SUPERSEDED** (item 29) |
| 23 | ~~§7.3 contradiction~~ — **Resolved Rev 3.7a:** feedthroughs everywhere, graded by signal (§7.3); Control → Motor through the logic-grade filtered DB-25 J-A, no glands | **RESOLVED** |
| 24 | **Element breakaway torque unmeasured** — M-2 is now decided (23HS22, §10.14); measure breakaway and running torque on C2 now and on the roller when built, against the motor's 0.60 N·m pull-out at 2 kHz / 24 V. If the roller exceeds ~0.4 N·m running, slow its axis or add a 36 V motor supply | **OPEN — bench measurement** |
| 25 | ~~Capacitor complement~~ — **RESOLVED Rev 3.7**: UCSX-740-10 in hand → C2; C1 is a purchased 15 kV-class part (UCSX-700-15 "CB-154" or CVDD-500-15S, §5.1). KP1-4 becomes a spare. Both candidates fit the §3.0 vertical stack | **RESOLVED** (C1 to acquire) |
| 26 | **Used vacuum variable acceptance test** — both caps, per §5.1b and `doc/vacuum-cap-testing.md` | **OPEN — bench test** |
| 27 | **Homebuilt roller — R-1 = C decided (Rev 3.7b)** — build the 34 µH / 5.2″ / 22-turn roller, no series link (§5.3a); drawings TUNER-L-100 to L-109 regenerated for it (2026-11-16). Run the §5.3a commissioning checks. The Harris / 229-class roller in hand is a spare (§11.5) | **OPEN — blocks 160 m above ~145 W until built** |
| 28 | ~~Roller orientation~~ — **RESOLVED Rev 3.7** by the vertical stack (§3.0): every element stands upright on a vertical shaft, so element length goes into height. The 34 µH roller at 5.2″ (11.547″ over the plates, §5.3a) and the 9.62″ CB-154 both fit in the 24.00″ box (§3.0 closure; 22.00″ until Rev 3.7c); no right-angle drive. Confirm in the mock-up (item 5) | **RESOLVED** (mock-up to confirm) |
| 29 | ~~Enclosure re-derivation~~ — **Done Rev 3.7a, 24″ tall since Rev 3.7c (22″ in 3.7b)**: frame cut list (TUNER-E-201), every panel with cutouts and fastener pattern (E-202 to E-208), small parts (E-209), parts list with hardware counts (E-210), nesting — one 48 × 48 of 14 ga and one 36 × 48 of 12 ga (E-211). Supersedes the 16 × 16 × 12″ tables (now §11.2). Frame junctions detailed Rev 3.7c (E-201: corner clips, 60 flush #6 flat heads). Remaining: the mock-up (item 5) | **RESOLVED** (mock-up to confirm) |
| 30 | **Vertical-stack checks** — (a) §8 thermal: confirm the reversed air path and that the shelf and utility layer stay below ~60 °C with 200 W in the RF bay — the input choke under the deck is now part of that 200 W (Rev 3.7c, §6; its own key-down check is item 49); (b) ~~motor length~~ — settled by M-2 (23HS22, 2.20″ body, 1.05″ spare); (c) roller runs vertical: fixed R8 bearing at the bottom takes rotor weight and thrust (§5.3a); (d) capacitor mounts variable end down, clamped at the deck; consider a top steady bracket for the 3.6 lb CB-154 | **OPEN** |
| 31 | ~~Top-panel clearance rule~~ — **Resolved Rev 3.7a, re-verified Rev 3.7b (box 22.00″) and Rev 3.7c (24.00″ — the box grew with the deck, so nothing above it moved):** every hot part of the roller keeps ≥ 2.25″ to the top panel (last turn 3.70″, bus rod 2.69″; plate B top 1.63″), so both the 1.5″ and the 2.25″ rules hold | **RESOLVED** |
| 32 | ~~Upright roller Q~~ — estimated (§5.3a clearance table, Rev 3.7b): deck at 1.94″ costs ≈ 3–5% L and a similar share of Q, top panel at 3.70″ ≈ 1%. Accept, or add ~1″ of insulating spacer under plate A (≈ −1.7%). Confirm with the installed Q measurement (item 12) | **ESTIMATED — confirm at commissioning** |
| 33 | **Teensy 4.1 row spacing** — verify 15.24 mm with calipers before ordering control boards (§10.5) | **OPEN — check** |
| 34 | **Coax relay CW rating** — *Rev 3.7a:* **Tohtsu CX600N-24 for both K1 and K2** (owner decision: cost and stock; auxiliary contacts replaced by the cal-load detector, 6B.3a). K2 never carries more than 60 W — no issue. **K1 is published at 1 kW CW at 50 MHz only**, against 1.5 kW CW here; the rating should rise toward HF but no figure exists. Before running legal-limit key-down (tune, digital modes), either confirm with Tohtsu, measure K1's contact/connector temperature after a 10-minute 1.5 kW carrier into the AUX dummy load, or fit a factory-order high-power relay (Dow-Key 402A-280132, Ducommun 2NH6C31) or an open-frame vacuum SPDT (Gigavac GH1) as K1. *Searched Rev 3.7c (2026-11-19):* no HF CW figure for the CX600N anywhere. Distributors give 1.5 kW PEP / 1.0 kW CW at 50 MHz and 1.0 kW CW at 150 MHz; an unattributed sheet's 2 kW at 30 MHz is not trusted. Tohtsu's 1.5 kW CW, DC–30 MHz part is the CX-210N, a manual panel switch and not usable as a relay. The CX-520D is 350 W. So the commissioning temperature test stands as the way to close this. | **OPEN — K1 rating (measure)** |
| 35 | **Boards for §6B.** *Control board — **done Rev 3.7c** (§10.5):* K1/K2 drivers with coil-current sense, the thermal-switch input, and the cal-load window comparator in the hardware permissive. The two drivers are the former RF-tank relay channels; those relays were deleted Rev 3.7b. *Measurement board — **done Rev 3.7c** (§10.4):* the cal-load detector (6B.3a), and the ÷1024 output on an edge SMA for the RG-316 run (W10) | **CLOSED** Rev 3.7c |
| 36 | **CAL reference plane** — match the K1→choke and K1→load electrical lengths, or measure and store the offset, before trusting vector calibration (§6B.3) | **OPEN — commissioning** |
| 37 | ~~Roller shaft-to-shelf creepage~~ — was 2.02″ vs the 2″ rule. **Resolved Rev 3.7a:** brass stub below the thrust collar cut from 1.0″ to 0.65″ (Oldham engagement 0.595″) → 2.37″; **4.37″ since the Rev 3.7c deck raise**. A longer Oldham hub would not help: the path is the axial tip-to-bushing distance (TUNER-L-109) | **RESOLVED** |
| 38 | ~~Sampler → control signal path~~ — **Resolved Rev 3.7a (§7.3a):** filtered DB-25 J-S at the partition, Alpha Wire M13197 (≡ Belden 9508) across the motor chamber to J-B at the bulkhead; prescaler on RG-316 between discrete 1000 pF feedthroughs at both walls; relay-coil diodes at the relay | **RESOLVED** |
| 39 | ~~24 V supply height~~ — **Resolved Rev 3.7a: Mean Well UHP-200-24**, 2.17″ tall on edge, fanless, Class B (§8A.1) | **RESOLVED** |
| 40 | ~~Filtered bulkhead connectors~~ — **Resolved Rev 3.7a (§7.3a):** Amphenol FCE17 DB-25 1000 pF (J-A), DB-25 5600 pF (J-B, J-S), DE-9 5600 pF (J-E, Rev 3.7b; was DA-15); Spectrum Control 9910-381-6002 power feedthroughs; Tusonix 2499 discrete feedthroughs. Connectors moved to the +Y half, clear of the C1 axis module and the PSU; plug envelopes checked | **RESOLVED** |
| 41 | **Front-panel and floor cutouts** — **parts selected Rev 3.7a** and drawn to their datasheets (E-202, E-206): NX4832K035, Grayhill 62V15-02-080CH (Rev 3.7c, same cutout as the 62A15), KO128A2007, PV6F240SS, TE Corcom 3EGG1-2, EHRJ45P5E, Gore PMF100320, Heyco 2020, 83-798, 82-97, TTM G150N50W4E, Amphenol 172124 (partition). Remaining: check each against the part in hand before cutting; 82-97 panel hole (0.688″) from its body size, not a published cutout. *Rev 3.7c:* the Adafruit 6070 microSD extender's hole (1.00″) is likewise from its ~30 mm body. Also check its depth behind the face: the control board is 0.68″ back, and the model assumes 0.55″ | **OPEN — check in hand** |
| 42 | ~~Link coil has no RF-bay position~~ — **RESOLVED Rev 3.7b:** series link and pad deleted (§5.2, §5.4); the deck holds only C1, C2 and the roller. The imbalance CT rides the output conductors at the top feedthroughs and the tank thermal is a small probe — neither needs deck area. Original entry in §11.6 | **RESOLVED** |
| 43 | ~~Partition coax adapter~~ — **Resolved Rev 3.7a: Amphenol RF (Connex) 172124**, N jack–jack bulkhead, PTFE insulator, brass body, gold-plated contacts, 5/8-24 jam nut with lock washer and silicone gasket (leave the gasket off or trim it so the body bonds to the bare partition). Cutout **Ø0.634″ with two flats 0.540″ apart** (TUNER-E-208, hole X), panels to 0.255″. Digi-Key ACX1170-ND, ~$13, 6,325 in stock (2026-11-16). No published voltage rating; N is routinely used at 1.5 kW CW to 30 MHz, and the line here is 50 Ω (≈ 390 V pk). Not the 83-1F SO-239 barrel — polystyrene | **RESOLVED** |
| 44 | **Roller idle-turn self-resonance** — *modeled Rev 3.7b* (`nec/roller_vna.py`, nec2++ wire model of the 22-turn, 5.2″, #4 helix with wheel, bus rod and lead; every wheel position 1–22, free space and over a PEC deck; `roller_bands.py` maps the band edges). Full winding **30.6 µH at 1 MHz** (≈ 10% under Wheeler; ≈ 30.0 over the deck — still > 23.1 µH needed). Port resonances from the idle turns sit at **13.2–15.6 MHz** and **28.4–30.2 MHz** for every wheel position. Every band edge 160–10 m lands off them (copper-only Q 855–2,170 at 160–12 m); the exception is the **top of 10 m: wheel ≈ 1 turn, idle resonance ≈ 30.1 MHz, only 1.3% above 29.7 MHz → Q ≈ 185, ~11 W at 29.7 MHz**. The model omits the Ultem ribs, whose dielectric pulls the resonance *down*. **VNA-sweep the wound roller, wheel at turns 1–3, before final assembly: the 28–31 MHz resonance must sit above ~30.5 MHz.** If it lands in-band: slimmer rib contact at the notches, or fewer idle turns | **OPEN — bench check (modeled risk at 29.5–29.7 MHz)** |
| 45 | ~~Re-run `cap_demand.py` bare~~ — **RESOLVED Rev 3.7b** (`nec/cap_demand.py`, output `cap_demand_rev37b.out`): **27/27** with either 15 kV C1 (C1 25–286 pF, C2 up to 675 pF); V_C1 6.54 kV pk (1.38×), V_C2 2.41 kV pk (2.49×), **V_L 6.55 kV pk / 4.63 kV RMS**, I_L 18.4 A; 160 m derates **527 / 630 / 935 W** network only (§1.7.1; 502 / 600 / 882 W with the choke in the RF bay since Rev 3.7c); no other band derates (worst 138 W at Q = 150). **Inductance actually required: 22.3 µH** — the 31.70 µH figure was the lowest-current policy maxing L on 40 m. Prefer **CVDD-500-15S** for C1 (20 pF floor) | **RESOLVED** |
| 47 | ~~Roller size~~ — **DECIDED Rev 3.7b: keep the 34 µH roller** (5.2″, 22 turns). Required L is ≤ 23.1 µH across feeder 39–42 ft / VF 0.93–0.97 (always at 1.800 MHz), so the drawn coil still covers if it winds up to ~30% under Wheeler (AB6WP saw 27%), and leaves headroom for other antennas or feeders on 160 m. A ~26 µH coil (5.2″ × 18 t) would save ~1.3″ of height but keep only ~8% worst-case margin. Item 44 (idle-turn SRF) is settled by the VNA sweep, not by shrinking | **DECIDED** |
| 46 | ~~Output DC path re-check~~ — **RESOLVED Rev 3.7b (§8D.5):** leg 1 (deck) is DC-grounded through the input choke's braid (≈ 0.15 Ω; ≈ 0.05 Ω for the Rev 3.7c RG-400 choke); leg 2 floats behind C2 — and always did: the old pad was in parallel with C2, so the "both legs behind series capacitors" claim was never true. Added a **100 MΩ / ≥ 10 kV bleed across C2** (≈ 0.03 W) to drain leg 2's static into the grounded node. Ohmmeter checks listed in §8D.5 for commissioning | **RESOLVED** (ohmmeter check at commissioning) |
| 48 | **Overtravel settings (§7.2)** — (a) the vacuum capacitors' end-stop torque rating (Jennings data, or a careful spring-scale test on C2) sets the driver current ceiling; (b) count each capacitor's shaft turns stop to stop (sets the ≥ (turns + 2):1 module reduction and §8B.3a times; 30 assumed); (c) measure the roller's stopping distance at the slow-zone speed to place its inner cam | **OPEN — bench measurement** |
| 49 | **Input choke, verify installed** (§6, Rev 3.7c) — (a) VNA sweep deck end to chassis with the choke and deck installed: expect the impedance peak near 5–7 MHz and \|Z\| ≥ ~1 kΩ across 10 m; a sharp in-band dip means the winding capacitance or a lead resonance differs from the model — re-dress the leads, then take off a turn; (b) 1500 W key-down on 28.0 MHz for 10 min with temperature labels on the bore bundle and cores, < ~100 °C; (c) inspect the jackets at the core edges after winding | **OPEN — build / commissioning** |
| 50 | **Antenna-system common-mode impedance** — the choke is rated with the whole V_cm across it (Z_a → 0). The real 160 / 80 m balance against the §2.2 ≤ 5% spec depends on Z_a: model the doublet + 40 ft feeder + tuner common-mode path in NEC, and read the output imbalance CT in service. If 160 m falls short, the 7-core stack (0.80× the deck reactance) fits the 5.50″ standoffs (§6). *Modeled Rev 3.7c* (`nec/cm_balance.py`, `nec/out/cm_balance.txt`). The model is the inverted-V on 40 ft of real 600 Ω line dropping to the tuner 6 ft up. A differential source drives the two feeder ends, each with its own shunt to a chassis node bonded to ground. Results: **160 m meets ≤ 5 % with the adopted 5-core choke** (2.8 % at 1.800 MHz) with the vane at minimum, because leg 1's choke ∥ deck shunt is parallel-resonant near 1.8 MHz. **80 m is set by the vane:** leg 1 looks like ~18–19 pF there, and too much vane walks the tuner's shunt capacitance into a series resonance with the antenna system's inductive common mode. **One vane setting, ~11 pF, holds both bands at ≤ 4.3 % on real ground.** Perfect ground, the bound, gives 5.4 % at 3.5 MHz (7-core: 4.4 %). The 7-core stack is not needed on this model. Set the vane on 80 m by the output CT, then confirm 160 m | **OPEN — measure in service** (model done) |
| 51 | ~~RF service-panel interlock switch~~ — *Closed Rev 3.7c:* a **Littelfuse 59140-1-S-02-A** reed sensor (SPST-NO) sits on the inner face of the front shelf-ring flange at y = −5.15″, between two of the panel's rivnuts. Its **Littelfuse 57140-000** magnet is bonded to the panel's inner face just above the flange. A reed needs no hole through the gasketed flange, where a plunger switch would. Closed means panel on; a missing panel, a broken lead or an open reed all trip. W12c runs PTFE 22 AWG from FT4 along the right wall at shelf level, more than 4.5″ from every RF conductor (§3.2 asks 1.5″); the switch's other side is the chassis. Prices and stock in §10.11. E-212, E-214, E-215 | **CLOSED** Rev 3.7c |
| 52 | ~~Sampler cable pair count~~ — *Closed Rev 3.7c:* **Belden 8112**, 12.5 pairs of 24 AWG, overall foil + braid + drain, OD ≈ 0.44″ (fits the J-S plug's metal backshell). It carries the 11 pairs (5 detector lines, the cal-load detector, the SWR permissive and +5 V with grounds; K1, K2 and the thermostat as their own pairs), with one pair and the odd conductor spare. Cut to length at Nassau Electrical, $14.88/ft, in stock 2026-11-19; Digi-Key sells it only on 100 ft spools. About 2 ft for W8 | **CLOSED** Rev 3.7c |
| 53 | **Coupler box in the model.** *Done Rev 3.7c:* the Hammond 1590A sits on the sampler baseplate between the coax input (floor G) and K1 (`enclosure.py`, E-212/E-213). W13 and W14 run to its SO-239s. W27/W28 are the FWD/REF RG-316 jumpers to the board's J1/J2, cut to one length. W9 is 16 conductors to J4. The board envelope is 100 × 74 mm plus its SMA plugs and the J4 socket. J3 moved to the top of the left edge, so its plug clears FT-P's solder-side envelope. No interference or harness clashes; E-212 to E-215 regenerated | **CLOSED** Rev 3.7c |
| 54 | **Firmware tested bounds (§8B.6).** At commissioning, confirm: (a) each element's position-to-value curve is within ±3 % across its range (VNA against encoder counts); (b) the AD8302 residual after the §6A.8 calibration is within ±0.25 dB and ±2°, checked against known loads on each band; (c) the capacitors' turns over full range (§8B.3a, ASSUMED), which set move time. If any falls outside, rerun the `fw` tests with the measured values before trusting the 3-attempt budget | **OPEN — commissioning** |

**Closed in this revision:** static drain and lightning protection (existing entry-box bonded
baseplate and arrestors); capacitor adequacy (C2 position 2.50×; C1 needs a 15 kV-class part,
§5.1);
network topology (plain T confirmed sufficient — switchable T/Pi not required at 40 ft).

### 9.1 Parts summary — critical path

> **This is a summary of the components that drove the design, not a build list.**
> For a complete from-scratch bill of materials — assuming nothing in hand — see **Section 10**.


| Item | Source | Status |
|:--|:--|:--|
| 1 × Jennings UCSX-740-10, 20–675 pF / 10 kV test (6 kV working), 3.75″ × 7.0″ | **in hand** | **C2** — 2.50× at 1500 W (Rev 3.7 working-voltage basis); acceptance test (§5.1b) |
| 1 × 15 kV-class vacuum variable, ≤ 25–30 to ≥ 500 pF, 9 kV working (UCSX-700-15 / CB-154, or CVDD-500-15S) | **to buy** | **C1** — 1.38× at 1500 W (§5.1) |
| 1 × KP1-4, 20–1000 pF / 10 kV (glass) | **in hand** | spare — not used (§9 item 25) |
| 1 × Harris 492-0309-000 roller (229-203 class), 0.20–24.40 µH | **in hand** | spare — not used (R-1 = C; §11.5) |
| 1 × homebuilt roller, 34 µH, 5.2″, 22 turns #4 solid, Ultem rib cage | **to build** | tank inductor (§5.3a) |
| 3 × single-shaft stepper (frame per DECISION M-2) + absolute encoder (DECISION M-1) | to buy | §10.6 |
| 3 × aluminum zero-backlash helical coupler | to buy | motor side only (Section 7.1a) |
| Delrin rod stock, ~1" dia | to buy | Oldham couplers, element side (7.1a) |
| Sheet, angle, conductive-elastomer gasket, filtered D-subs, feedthroughs, blower | to buy | §10.11, §7.3a |

## Section 10 — Consolidated Bill of Materials

### 10.0 Scope and conventions

**This section assumes nothing is in hand.** Every part needed to build the tuner from bare stock
is listed, including items the original builder already owned. The purpose is reproducibility: a
second unit, or another builder working from this document alone, should be able to order from
Section 10 without reading Sections 1–9 first.

| Convention | Meaning |
|:--|:--|
| **Part** named | A specific orderable item, verified against a vendor datasheet |
| **Class** named | A specification with example parts; equivalents acceptable if the spec is met |
| **DECISION** | A genuine open selection — requirement stated, alternatives given, not yet chosen |
| **Fabricate** | Made from stock listed elsewhere in this section |

*Rev 3.7c:* prices and stock now appear where they drove a choice. They are qty-1 US distributor
prices with the date checked (2026-11-19, §10.5). They go stale and vary by territory, so re-check
before ordering; every part selected for the Rev 3.7c control board was checked for stock and
lifecycle. Three of the DECISION items span an order of magnitude in cost; those carry indicative
bands because the cost *is* the decision.

**One table per subsystem; each part is counted once.** Everything soldered to a board is in that
board's table (§10.4 measurement, §10.5 control). A part that also belongs to another subsystem is
listed there with Qty **—** and a pointer, so ordering section by section never buys it twice.

Reference designators (R1, U3, J7 …) refer to the KiCad schematics in `kicad/`.
Quantities are per tuner, excluding the bench panel of 10.9, which is one per operating position.

---

### 10.1 RF power path

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 2 | Vacuum variable capacitor | **C1:** 15 kV test / 9 kV working, ≤ 25–30 to ≥ 500 pF, ≥ 6 A — e.g. **Jennings UCSX-700-15S** or **CVDD-500-15S**. **C2:** 20–675 pF, 10 kV test / 6 kV working — **UCSX-740-10 in hand** | Class | §5.1 |
| 1 | Roller inductor | Homebuilt per §5.3a (DECISION R-1 = C): **≥ 34 µH** max, single roller, no series link; ≤ 0.46 µH min; **18.4 A RMS**; up to 9.3 kV pk across the winding. #4 solid at 3 TPI on 5.20″, 22 turns, Ultem rib cage | Fabricate | §5.3a |
| 1 | Floating sub-deck | **10.75″ × 10.75″**, 12 ga — cut from sheet stock | Fabricate | §3.0, E-211 |
| 4 | Sub-deck standoff insulator | Ceramic or PTFE, **5.50″** height (Rev 3.7c; was 3.50″), HV-rated | Class | §3.2 |
| — | Tank interconnect strap | Copper strip, 0.032″ × 0.75″, ~4 ft — radius all edges ≥1/16″ | Class | §3.2 |

> There are no relays in the RF tank (pad and series link deleted, Rev 3.7b; history in §11.6). The
> only RF relays are the K1/K2 coax relays of §10.3.

---

### 10.2 Input common-mode choke

*Rev 3.7c (§6). The design C former and RG-142B are in §11.11.*

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 5 | Ferrite toroid | **Fair-Rite 5961003801** (FT-240-61): #61, 61.0 × 35.55 × 12.7 mm, A_L ≈ 172 nH — ~$13 ea (DigiKey), ~$9 at 20+ (TME) | Part | §6 |
| 1 | Winding coax | **RG-400 (M17/128)**, **12 ft** (9.6 ft used: 15 turns ≈ 9.0 ft + leads) — ~$1.85–2.90/ft | Part | §6 |
| 1 | PL-259, chassis end | **Amphenol 83-1SP** (PTFE) + **UG-175/U** reducer for 0.195″ cable; mates the shelf coax bulkhead | Part | §6 |
| 1 | Base disc | G10, 1/4″ × Ø3.40″: Ø0.52″ center hole, six Ø0.15″ vents on Ø0.72″, three Ø0.177″ holes countersunk 82° × Ø0.34″ on Ø2.60″ | Fabricate | §6, E-209 |
| 1 | Top spider | G10, 1/8″: Ø1.00″ hub, three 0.50″ arms with round ends on Ø2.60″, Ø0.52″ center hole | Fabricate | §6, E-209 |
| 3 | Standoff | G10 (or glass-filled nylon), Ø3/8″ × 5/8″, 8-32 female both ends | Class | §6, E-207, E-209 |
| 3 | Flat-head screw | **Nylon 8-32 × 1/2″, 82°** — base disc to standoffs, countersunk flush (no metal under the winding) | Class | §6, E-209 |
| 3 | Machine screw | Stainless 8-32 × 3/8″ — up through the shelf into the standoffs (CH1–CH3) | Class | §6, E-207 |
| 1 | Center rod + 2 nuts | **1/2″-13 fiberglass (FRP) threaded rod**, ~5″ (cut to fit), with FRP nuts | Class | §6 |
| — | Pads, tape, bond | 1/16″ silicone rubber sheet; glass-cloth tape for the bore and core edges; high-temperature RTV between the cores; PTFE lacing cord | Class | §6 |
| 2 | SO-239 bulkhead connector | **Amphenol 83-798** (SO-239A), PTFE — **not 83-1R**, which is glass-filled PBT | Part | §7.3 |

> §9 item 49: VNA-sweep it installed and run the 10 m key-down thermal check. Twelve feet of RG-400
> leaves ~2 ft for re-dressing the leads or one more turn.

---

### 10.3 Directional sampler (Stockton / Tandem Match)

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 2 | Toroid core | **FT-82-61** NiZn, µ ≈ 125 — verify A_L against the actual vendor datasheet | Part | §6A.3 |
| — | Secondary winding wire | **40 turns each**, #26 AWG enameled, ~6 ft total | Class | §6A.3 |
| — | Primary conductor | The through-line itself — PTFE-insulated, rated 14 A RMS | Class | §6A.3 |
| — | Termination resistor | **50 Ω, 2 W, non-inductive** — on the measurement board: 2 × 105 Ω 1 W 2512 per port (§10.4) | Class | §6A.3 |
| 1 | Coupler enclosure | **Hammond 1590A**, diecast, 3.64 × 1.52 × 1.22″ ($10.42, 388 in stock, Digi-Key 2026-11-19). The two cores sit on the through-line between the SO-239s. On the sampler baseplate between floor G and K1 (E-212, E-213) | Part | §6A.3b |
| 2 | Coupler RF in / out | **Amphenol 83-798**, SO-239 PTFE, 4-hole, the same part as the coax input ($14.07, 1,580). W13 in, W14 out to K1 | Part | §6A.3b |
| 2 | Coupler FWD / REF out | **Molex 73251-3890**, SMA jack, 4-hole flange, solder ($7.09, 596), on the box top | Part | §6A.3b |
| 2 | Coax jumper, FWD / REF | RG-316, SMA plug both ends, **equal length** (the AD8302 reads their phase difference), coupler box → measurement board J1, J2: W27, W28 on E-215, cut to one length | Class | §6A.3b |
| 2 | Coax relay, K1 / K2 | **Tohtsu CX600N-24** — SPDT, N, 24 V, no auxiliary contacts; published 1 kW CW at 50 MHz (**K1 rating open, §9 item 34**); ≈ $130, RF Parts. Upgrade path for K1: Dow-Key 402A-280132 / Ducommun 2NH6C31 (factory order) | Part | §6B |
| — | Cal-load RF detector | 3.3 pF 1 kV NP0 + 100 pF NP0 divider, BAT54S, 100 kΩ / 2.2 nF, 1 MΩ bias, 33 V TVS — on the measurement board (§10.4); window comparator on the control board | Class | §6B.3a |
| 1 | Calibration load | **TTM/Anaren G150N50W4E** — 150 W, AlN, flange 0.870 × 0.375″, Ø0.161″ holes 0.560″ apart (G100N50W4 is obsolete). Sits through the floor cutout directly on the sink. **Thin stock — buy early** | Part | §6B.3 |
| 1 | Cal-load heatsink | **Wakefield-Vette 441K** (≈ 0.68 °C/W natural convection) under the floor, gasketed to it; flange ≈ 80–95 °C at 50 W in 30 °C air | Part | §6B.3 |
| 1 | Thermal switch | **Cantherm F20A085053600060** — NC, opens 85 °C, resets 55 °C; potted SIP, clip or thermally bond to the sink. (Airpax 67L085 TO-220 equivalent is on backorder; 67F085 is NO — wrong part) | Part | §6B.3 |
| 1 | AUX bulkhead | **Amphenol 82-97** (UG-58A/U), N female, PTFE, 4 holes on 0.718″ square — distributor stock unconfirmed (Digi-Key shows a 10-week lead); 82-97-RFX is the same part with gold contacts | Part | §6B.4 |
| 3 | Coax jumper | RG-393 or RG-142 (PTFE), N-to-N; K1→choke and K1→K2→load matched in electrical length | Class | §6B.3 |

---

### 10.4 Measurement board — 81 components *(Rev 3.7c)*

`kicad/measurement.kicad_sch` / `measurement.kicad_pcb`, generated by `kicad/board_measurement.py` and
`kicad/route.sh`. *The Rev 3.4 board it replaces is in §11.14.*

- **Outline:** 100 × 74 mm. The board stands on edge 0.3″ off the motor/sampler partition, inside
  the sampler's 4.0 × 3.0″ envelope. Four M3 holes, plated and bonded to GND, which reaches the
  chassis through the standoffs.
- **Stackup and rules:** as the control board (§10.5): 4 layers with In1 a solid GND plane; 0.2 mm
  tracks, 0.15 mm clearance, 0.6 / 0.3 mm vias. The FWD/REF RF nets are 0.5 mm and the supplies
  0.4 mm. The cal-load tap has its own net class, with 2.5 mm clearance to everything (IPC-2221 B2,
  301–500 V); its trace runs on In2.
- **Routing:** freerouting, then DRC shows 0 unconnected and no electrical errors; only silkscreen
  warnings remain. 594 tracks, 94 vias.
- **Mounting:** a folded 1/16″ aluminum L-plate is screwed to the sampler baseplate behind the board.
  Its upright leg carries the four corner holes on 5/16″ (8 mm) M3 standoffs, which sets the 0.3″
  gap to the partition. The plate also bonds the board's GND to the chassis.
- **Assembly:** 68 SMD parts (1206 passives, 2512 terminations, SOIC, TSSOP-14, SOT-223, SOT-23,
  SOD-123) and 13 through-hole (the edge SMAs' legs, header, electrolytic, trimmer, 1 kV disc, wire
  and test pads).
- **Floor plan** (component side; the left edge faces cabinet −Y):
  - **Right edge:** FWD (J1) and REF (J2) come in from the coupler box on two equal-length RG-316
    jumpers. Each port's termination, detector and AD8302 tap sit beside its SMA, with the AD8302
    between the two.
  - **Left edge, top:** the ÷1024 out (J3). Its plug clears the solder-side envelope of the
    partition feedthrough FT-P below it, and W10 drops ~1″ to FT-P.
  - **Bottom-left corner:** the cal-load tap pad (J5, 22 AWG from the load's tab), its ground pad
    (J6) and the 1 kV disc, ~70 mm from the REF tap.
  - **Top edge, center:** the J-S header (J4), under J-S on the partition.
- **J4 pinout:** W9 runs one to one to J-S, carrying pins 1–16 of the control board's J-B pinout.
  V_MAG, V_PHS, V_FWD, V_REF_DET, AD_VREF, CAL_DET, SWR_OK and +5 V are on the odd pins, each with its
  ground on the next even pin. 1 kΩ on each analog output isolates its driver from the 5600 pF
  contacts and sets the §7.3 28 kHz corner.
- **Commissioning:**
  - Set RV1 with a wattmeter (§6A.4): 2:1 at 1500 W, 167 W reflected, reads ~0.92 V at TP1.
  - TP2 is V_REF_DET, TP3 CAL_DET, TP4 GND.
  - The 60 W cal-load trip is set on the control board's RV1 (§6B.3a).
- **Rendered views:** Appendix C.
- **Fab outputs:** `kicad/fab.sh measurement` writes `kicad/fab/measurement-fab.zip`.
- **Off-board:** the coupler box and the RG-316 jumpers are in §10.3.

Prices are qty-1 Digi-Key prices checked 2026-11-19, with stock in brackets. Passives with no part
number are commodity: 1 %, X7R 50 V unless marked C0G.

| Qty | Part | Package | Refs | ≈ $ ea |
|--:|:--|:--|:--|--:|
| 1 | **AD8302ARUZ** gain/phase detector (3,233; 10 wk factory lead) | TSSOP-14 | U1 | 38.58 |
| 1 | **TLV3501AIDR** comparator (2,233) | SOIC-8 | U2 | 4.10 |
| 1 | **74LVC74AD,118** (Nexperia), ÷4 (20,520; TI SN74LVC74ADR had none) | SOIC-14 | U3 | 0.28 |
| 1 | **SN74HC4040DR**, ÷256 (25,475) | SOIC-16 | U4 | 0.72 |
| 1 | **AMS1117-3.3** | SOT-223 | U5 | — |
| 1 | **LM393DR**, over-SWR trip (83,479) | SOIC-8 | U6 | 0.23 |
| 2 | **1N5711W-7-F**, 70 V Schottky detector (26,399) | SOD-123 | D1, D2 | 0.26 |
| 2 | **BAT54SLT1G** (onsemi): counter clamp, cal-load doubler | SOT-23 | D3, D4 | 0.16 |
| 1 | **SMF33A** (Littelfuse), 33 V TVS (135,550) | SOD-123F | D5 | 0.57 |
| 4 | 105 Ω 1 % 1 W, **Panasonic ERJ-1TNF1050U**, two per port (4,399; not for new designs) | 2512 | R1, R2, R7, R8 | 0.84 |
| 1 | 3.3 pF 1 kV NP0 disc, **Vishay 561R10TCCV33** (325; alt. Johanson QCCT102Q3R3B1GV001E, 0805, $1.13) | radial 6.4 mm | C20 | 3.06 |
| 2 | Ferrite bead 600 Ω, **Murata BLM31PG601SN1L** | 1206 | FB1, FB2 | 0.50 |
| 3 | SMA jack, edge mount, **Molex 73251-1153** (6,774; Amphenol 132289 is $9.11) | edge | J1–J3 | 4.35 |
| 1 | Shrouded IDC header 2×8, **On Shore 302-S161** (42,763) | THT | J4 | 0.37 |
| 1 | 10 kΩ multi-turn trimmer, **Bourns 3296W-1-103LF** (SWR trip) | 3296W | RV1 | 2.56 |
| 1 | 100 µF 10 V electrolytic (AMS1117 output) | radial 6.3, 2.5 mm | C25 | — |
| 24 | 100 nF (11) · 10 nF (4) · 10 µF 16 V (3) · C0G: 10 nF (2), 100 pF (2), 1 nF, 2.2 nF | 1206 | C5, C6, C10, C13–C16, C18, C19, C23, C26 · C1, C3, C7, C8 · C11, C17, C24 · C2, C4 · C9, C21 · C12 · C22 | — |
| 27 | 10 kΩ (6) · 1 kΩ (6) · 22 kΩ (3) · 4.7 kΩ (3) · 1 MΩ (3) · 1.62 kΩ (2) · 52.3 Ω (2) · 680 Ω · 100 kΩ | 1206 | R4, R10, R14–R16, R26 · R18, R27–R31 · R3, R9, R25 · R13, R19, R22 · R17, R21, R24 · R5, R11 · R6, R12 · R20 · R23 | — |
| 6 | Wire pads J5 (cal-load tap) and J6 (its ground) · test points TP1 SWR TH, TP2 V REF, TP3 CAL DET, TP4 GND | THT pad | J5, J6, TP1–TP4 | — |

- **Parts for one board:** ≈ **$75** at qty-1 prices, with commodity passives estimated; the AD8302
  is half of it.
- **Bare boards** (JLCPCB quote, 2026-11-19, 5 pcs, 100 × 74 mm, 4-layer, 1.6 mm): **$8.00** with
  leaded HASL ($25.40 with ENIG). That is JLCPCB's flat 4-layer rate for boards within 100 × 100 mm.
  Ordered with the control board it ships in the same parcel.
- **Stencil:** about $7, as for the control board.

### 10.5 Control board — 166 components *(Rev 3.7c)*

`kicad/control.kicad_sch` / `control.kicad_pcb`, generated by `kicad/board_control.py` and
`kicad/route.sh`. *The Rev 3.4 board it replaces is in §11.13.*

- **Outline:** 139 × 91 mm, standing in the cassette's 5.5 × 3.6″ envelope.
- **Stackup:** 4 layers, 1.6 mm FR4. In1 is a solid GND plane; In2 is a third signal layer.
- **Rules:**
  - 0.2 mm tracks (the router necks down to 0.15 mm), 0.15 mm clearance.
  - 0.6 / 0.3 mm vias.
  - Power nets 0.6 mm, logic supplies 0.4 mm.
- **Routing:** freerouting, then DRC shows 0 unconnected and no electrical errors; only
  silkscreen-overlap warnings remain. 2,444 tracks, 295 vias.
- **Assembly:** sized for hot-air hand soldering. 141 SMD parts (1206 passives, SOIC, SOT-223,
  SMA/SOD-123 diodes, 1812/2920 PTCs) and 25 through-hole (Teensy, connectors, DC-DCs,
  electrolytics, inductors, trimmer, fiber transmitter).
- **Floor plan:**
  - The bulkhead ribbons, POF and blower lead are at the left end (cabinet +Y); the 24 V entry is at the
    right end.
  - The Teensy lies flat on two 1×24 socket strips, parallel to the board as usual. It is turned so
    its SD end sits at the board's top edge (§8B.5.6), which points up in the cassette. The socket
    strips also let it come out; verify the 15.24 mm row spacing with calipers before ordering boards (§9 item 33),
    and cut VUSB–VIN before programming in place (§8B.0.3).
  - Every SMD ground pad has its own via to the In1 plane.
- **Pin and connector map:** §8B.0.4. The J-A/J-B/J-E pinouts are in `board_control.py`.
- **Rendered views:** 3D top and bottom, the silkscreen and each copper layer are in **Appendix C**.
- **Fab outputs:** `kicad/fab.sh control` writes the Gerbers, drill files and paste layer (for the
  stencil) to `kicad/fab/control-fab.zip`.

Prices are qty-1 distributor prices checked 2026-11-19 (Digi-Key, Mouser, Arrow, Newark via
Octopart). Passives with no part number are commodity: 1 %, X7R 50 V, any maker.

| Qty | Part | Package | Refs | ≈ $ ea |
|--:|:--|:--|:--|--:|
| 1 | **Teensy 4.1** (PJRC / SparkFun DEV-16771) | 48 pins, 2 × 24 at 15.24 mm | A1 | 31.50 |
| 2 | 1×24 socket strip for A1, **Sullins PPPC241LFBN-RC** | 2.54 mm | — | 1.53 |
| 1 | **TRACO TSR 3-2450N**, 24 → 5 V 3 A | SIP-3 | U1 | 8.38 |
| 1 | **TRACO TSR 2-24120N**, 24 → 12 V 2 A | SIP-3 | U2 | 6.60 |
| 1 | **AMS1117-3.3** | SOT-223 | U3 | — |
| 1 each | **SN74HC08DR** · **SN74HC32DR** · **SN74HC21DR** · **SN74HC14DR** | SOIC-14 | U4 · U5 · U6 · U7 | 0.40–0.54 |
| 1 | **LMC555CMX/NOPB** (10 kHz interlock tone) | SOIC-8 | U8 | 1.15 |
| 1 | **SN74HC373DWR** (K1/K2 hold latch) | SOIC-20W | U9 | 0.96 |
| 1 | **MCP23017-E/SO** | SOIC-28W | U10 | 1.53 |
| 1 each | **LM393DR** · **MCP6002-I/SN** (cal-load window) | SOIC-8 | U11 · U12 | 0.23 · 0.89 |
| 1 | **Broadcom HFBR-1521Z**: single source, 18–20 wk factory lead; **order early** | Versatile Link | U13 | ~16 |
| 4 | **IRLL2705TRPBF**: 55 V, Vgs(th) 1–2 V, ≤ 65 mΩ at 4 V (alt. IRLL024NTRPBF, NDT3055L) | SOT-223 | Q1–Q4 | 0.99 |
| 2 · 1 | **S1M-E3/61T** · **SS14-E3/61T** | SMA | D7, D8 · D9 | 0.35 |
| 9 | **BAT42W-7-F**, I_R ≤ 0.5 µA | SOD-123 | D1–D6, D10–D12 | 0.19 |
| 1 | PTC 1.85 A / 33 V, **Littelfuse 2920L185DR** | 2920 | F1 | 1.05 |
| 2 | PTC 0.3 A / 60 V, **Bourns MF-MSMF030/60X-2** | 1812 | F2, F3 | 0.73 |
| 2 | 1 µH 7.5 A, **Fastron 07HCP-1R0M-50** (alt. Würth 744772010) | radial 7.8 mm, 5 mm | L1, L2 | 0.99 |
| 1 | 220 µF 35 V low-ESR, **Panasonic EEU-FR1V221** | radial 8 × 11.5, 3.5 mm | C1 | 0.71 |
| 1 | 150 µF 35 V, **Nichicon UHE1V151MPD** | radial 8 × 11.5, 3.5 mm | C2 | 0.60 |
| 1 | 100 µF 35 V, **Panasonic ECA-1VM101** | radial 6.3, 2.5 mm | C3 | 0.34 |
| 4 | 47 µF 10 V · 22 µF 25 V · 100 µF 10 V · 4.7 µF 25 V | radial 5–6.3 | C4 · C5 · C6 · C22 | — |
| 1 | 100 nF C0G (blanking timer), **TDK C3216C0G1H104J160AA** | 1206 | C27 | 0.18 |
| 1 | 10 nF C0G (tone timing), **KEMET C1206C103J5GACTU** | 1206 | C25 | 1.66 |
| 27 | 100 nF (17) · 10 nF (9) · 1 nF (1) | 1206 | C7, C8, C16–C19, C23, C24, C28–C36 · C9–C13, C15, C20, C21, C26 · C14 | — |
| 17 | 1 kΩ anti-surge, **Panasonic ERJ-P08J102V** (the §7.3 series element) | 1206 | R27–R31, R33, R35, R41, R48, R52, R54, R55, R57, R58, R67, R75, R80 | 0.17 |
| 19 | 47 Ω (§7.3 logic grade) | 1206 | R1–R19 | — |
| 25 | 10 kΩ | 1206 | R20–R25, R34, R38–R40, R44, R46, R50, R53, R56, R60–R62, R65, R66, R68–R71, R78 | — |
| 15 | 100 Ω (6) · 100 kΩ (5) · 4.7 kΩ (2) · 10 MΩ, 1 MΩ, 560 kΩ, 56 kΩ, 6.8 kΩ, 3.9 kΩ | 1206 | R45, R49, R59, R63, R64, R77 · R32, R37, R74, R82, R83 · R72, R73 · R36, R26, R81, R43, R76, R42 | — |
| 3 | 1 Ω 1 W (coil sense) · 56 Ω 1 W (fiber LED) | 2512 | R47, R51 · R79 | — |
| 1 | 10 kΩ multi-turn trimmer, **Bourns 3296W-1-103LF** (60 W trip) | 3296W | RV1 | 2.56 |
| 1 | SMA jack, vertical, **Cinch 142-0701-201** (Amphenol 132134-11 is $17) | THT | J11 | 6.53 |
| 1 | Terminal block 2-pos 5.08 mm, **Phoenix 1729128** (1715721 is out of stock) | THT | J1 | 0.95 |
| 2 · 1 | Shrouded IDC header 2×13 · 2×5, **On Shore 302-S261 · 302-S101** | THT | J2, J3 · J4 | 0.37 · 0.27 |
| 6 | Pin header 1×02 (2), 1×03, 1×04, 1×06 (2) | 2.54 mm | J5–J10 | — |

- **Parts for one board:** ≈ **$109** at qty-1 prices, with commodity passives estimated. The
  panel adds the Nextion ($39.90) and two encoders ($94–154, §7.5).
- **Bare boards** (JLCPCB quote, 2026-11-19, 5 pcs, 139 × 91 mm, 4-layer, 1.6 mm):
  - $32.80 with leaded HASL (+$18.10 for ENIG).
  - Top stencil, frameless, 200 × 150 mm custom size: $7.22. (The standard 380 × 280 mm stencil costs
    the same and roughly doubles the shipping weight.)
  - UPS DDP shipping: $31.07.
  - About **$71 delivered**, $89 with ENIG.
  - For comparison, OSH Park charges $196 for three 4-layer boards ($10/in²).
- **Paste:** Chip Quik SMD291AX10 (Sn63/Pb37, no-clean, 35 g) is ~$21.

---

### 10.6 Motion subsystem

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 3 | Stepper motor | **StepperOnline 23HS22-2804S** — NEMA 23 short stack, 1.20 N·m, 2.8 A, single 6.35 mm shaft, **direct** (M-2) | Part | §7.1 |
| 3 | Stepper driver | Chopper, 24 V, ≥3 A/phase, STEP/DIR/EN opto inputs — **StepperOnline DM542T** class | Class | §8A.1 |
| 3 | Motor-side coupler | Aluminum zero-backlash helical, **6.35 mm (1/4″) → 9.525 mm (0.375″)** bore for NEMA 23 direct; with NEMA 17 + belt, bore to the belt output shaft (M-2) | Class | §7.1a |
| 3 | Element-side coupler | **Delrin Oldham** — fabricate from rod stock below | Fabricate | §7.1a |
| 3 | Insulating drive shaft | **0.375″ OD heavy-wall G10 rod**, length per axis + 2″ | Class | §7.1, §3.1 |
| 3 | Flanged bushing | Bronze, 0.375″ bore, partition-mount | Class | §7.1 |
| 0 | Intermediate bearing block | Not needed in the vertical stack — longest free span ~5.1″ above the shelf bushing (shafts 4.8–6.4″ overall since Rev 3.7c), under the 6″ rule (§3.0, §3.1) | — | §3.0 |
| — | Delrin rod stock | Acetal **homopolymer**, 1.0″ dia × 12″ — Oldham hubs and discs | Class | §7.1a |
| 6 | Roll pin / dowel | 1/8″ × 0.75″, stainless — coupler retention, **not set screws** | Class | §7.1a |
| 12 | Limit microswitch | Sub-miniature SPDT, **roller lever** (Omron SS / D2F class), on a slotted plate — inner (gates STEP) and outer (drops EN) at each end of each axis | Class | §7.2 |
| 3 | Encoder / limit-cam module | Assembly per §7.1 — COTS parts below on one folded 1/8″ Al bracket (fabricate) | Fabricate | §7.1 |
| 3 | Takeoff pulley | GT2, bored to the 0.375″ G10 shaft, clamp hub | Class | §7.1 |
| 6 | Reduction pulley pairs | GT2 small/large pairs for two stages, ≥ 24:1 roller / ≥ 32:1 caps (e.g. 16T→80T × 20T→100T = 25:1; size after §9 item 48 counts the turns) | Class | §7.1 |
| 6 | GT2 belt | 6 mm wide closed loop, lengths per the module layout | Class | §7.1 |
| 6 | Shaft | 6 mm ground steel, short (intermediate and output) | Class | §7.1 |
| 12 | Flanged ball bearing | 6 mm bore (F686-class) | Class | §7.1 |
| 12 | Clamp shaft collar | Two-piece, 6 mm bore, one radial tapped hole — trip dogs (4 per axis) | Class | §7.2 |
| 12 | Trip-dog screw | Short socket set screw or dowel in the collar's radial hole | Class | §7.2 |
| 3 | Encoder | **AS5048A** breakout (SPI, 14-bit) | Class | §7.1, M-1 B |
| 3 | Encoder magnet | Diametric, in a shaft-end holder on the output shaft | Class | §7.1 |

**Rail check with the real motor (23HS22-2804S):** 2 phases × 2.8² A² × 0.90 Ω ≈ **14 W per motor**
while moving, ≈ 0.6 A from 24 V; three moving together ≈ 1.8 A against the 5 A budget of §8A.1.
De-energized at idle (§8A.1), otherwise ~42 W of standing heat in a sealed box.

> **Why single shaft, corrected.** An earlier reading of §7.1 — encoder on the rear shaft —
> implied a dual-shaft motor. **It does not fit.** Depth stack against the 5.00″ Motor Chamber:
>
> | Arrangement | Depth | Result |
> |:--|--:|:--|
> | 23HS30-2804**S** single shaft + coupler | 4.59″ | fits, 0.41″ spare |
> | 23HS30-2804**S** + encoder belt takeoff | 5.22″ | **over by 0.22″** |
> | 23HS30-2804**D** dual shaft + rear encoder | 5.81″ | **over by 0.81″** |
> | NEMA 17 + 3:1 belt + encoder takeoff | 3.54″ | fits, 1.46″ spare |
> | **23HS22-2804S (56 mm) + coupler + takeoff — chosen Rev 3.7b** | **3.93″** | **fits, 1.05″ spare** |
>
> Buying the dual-shaft variant would have forced a chamber redesign. The rear shaft was never
> the constraint — **chamber depth is**. Since the encoder must come off a belt takeoff in any
> case (DECISION M-1 option B), it does not care which end of the motor it is driven from, and
> taking it off the G10 shaft puts the motor-side coupler *inside* the measurement loop, which is
> strictly better than reading the motor's rear shaft.

---

### 10.7 Local panel (control-cassette face — ~15.87″ W × 5.00″ H; layout per TUNER-E-202)

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 1 | Display | **Nextion NX4832K035** (or T035, same outline) — window 2.95 × 1.99″; Itead stock, $39.90 (2026-11-19), on Itead's availability list to 2027 | Part | §7.5 |
| 2 | Rotary encoder | **Grayhill 62V15-02-080CH** — optical, 3.3 V, 24 detent, push, 3/8-32 bushing, 0.100″ connector on 8″ cable; factory order ~$47 (Future, MOQ 1); fallback 62V15-02-P ~$77, stocked | Part | §7.5 |
| 1 | Bypass keyswitch | **E-Switch KO128A2007** — SPST, key out in OFF only, Ø19 mm with flat | Part | §8B.4d |
| 2 | Encoder shaft extension | **Delrin**, short, unloaded — RF isolation, not stiffness | Fabricate | §7.1a |
| 1 | Recovery button | **E-Switch PV6F240SS** — flush, sealed, Ø16 mm, with a 1/4″ guard ring | Part | §8B.4f.2 |
| 1 | microSD card | 8–32 GB, industrial or high-endurance grade | Class | §8B.5.5 |
| 1 | microSD extender | **Adafruit 6070**, round panel mount, ~30 mm body, ~18 cm ribbon to the Teensy's socket; $9.50 at Adafruit, in stock (2026-11-20); also Digi-Key 1528-6070-ND | Part | §8B.5.6 |
| 1 | Panel gasket | Closed-cell elastomer behind display and control cutouts | Class | §8E.4 |

> §8B.5.6 constrains Control-board placement: the Teensy's SD socket needs insertion and ejection
> clearance, so orient the module with the socket facing the cassette front or an edge.

---

### 10.8 Interlock and remote link

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| — | POF transmitter | **Broadcom HFBR-1521Z**, 660 nm — on the control board, **counted in §10.5 (U13)**. Single source with thin US stock (Digi-Key quotes an 18–20 week factory lead): **order early** | Part | §8C.3.3 |
| 1 | POF receiver | **Broadcom HFBR-2521Z** class | Class | §8C.3.3 |
| — | Plastic optical fiber | 1 mm duplex POF, length = tuner to bench + 20 % | Class | §8C.3.3 |
| 4 | POF crimp connector | Simplex latching — razor-blade termination, no polishing | Class | §8C.3.3 |
| 2 | Fiber snap bushing | **Heyco 2020** (SB 375-3), Ø0.375″ hole, panels to 0.125″, 0.190″ bore — fiber to the board-mounted HFBR-1521Z | Part | §8C.3.3 |
| 1 | Opto-MOSFET switch | **Panasonic AQV252 / AQY212** PhotoMOS — <2 ms, solid-state | Class | §7.4.3 |
| 1 | Ethernet kit | **PJRC Teensy 4.1 Ethernet kit** — magjack carrier + ribbon | Part | §8C.3.3 |
| 1 | Ethernet bulkhead | **Switchcraft EHRJ45P5E** — thermoplastic, **unshielded** — see §8C.3.1 | Part | §8C.3.1 |

> **Unshielded is deliberate.** §8C.3.1 corrects an earlier overstatement: STP makes the surge case
> *worse* by bonding the bench and entry-box grounds, and the coax shield already bridges them.
> The interlock stays optical regardless, because protection must not depend on the data link
> (§8C.6).

---

### 10.9 Bench panel — one per operating position

Physically separate build (§8C.4b). No software in the E-STOP path.

| Qty | Item | Specification | Type |
|--:|:--|:--|:--|
| 1 | Enclosure | Diecast or ABS, desktop, ~6″ × 4″ × 2″ | Class |
| 1 | E-STOP switch | **Large, red, latching, mushroom head** — breaks amp keying locally | Class |
| 1 | Indicator LED | PERMISSIVE — driven from the interlock state; TUNE, ACK and status are in the web UI (§8C.4b) | Class |
| 1 | POF receiver | HFBR-2521Z class — the permissive arrives here | Class |
| 1 | Keying interface | Opto-MOSFET rated for the amplifier's keying regime | Class |
| 1 | Amp keying cable | To SB-220 relay jack — **see DECISION I-1, 10.14** | DECISION |

---

### 10.10 Power distribution

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 1 | Main supply | **Mean Well UHP-200-24** — 201.6 W, fanless, Class B, 2.17″ on edge | Part | §8A.1 |
| — | DC-DC converter | **TRACO TSR 2-24120N** — 24 → 12 V, 2 A, blower — on the control board, **counted in §10.5 (U2)** | Part | §8A.1 |
| — | DC-DC converter | **TRACO TSR 3-2450N** — 24 → 5 V, 3 A, with an LC input filter — on the control board, **counted in §10.5 (U1)**. (The 5-SIP TSR 3-2450 is ~4× the price; Recom RPMB5.0-3.0 is on a 17-week lead) | Part | §8A.1 |
| 2 | Common-mode choke | **Fair-Rite 2631803802** (31 material), 6–8 bifilar turns, on supply input **and** output leads | Part | §8A.1 |
| 1 | Ground strap | Tinned copper braid, 1″ wide × 18″ — chassis to arrestor baseplate | Class | §8A.2 |
| 1 | IEC inlet | **TE Corcom 3EGG1-2** — 3 A, fused (2 × 5 × 20, T2.5 A), filtered (≥ 48 dB line-to-ground 5–30 MHz, 36 dB at 1 MHz), screw flange; cutout 1.14 × 1.30″, Ø0.138″ holes 1.417″ apart (Schaffner FN9260-4-06 is on 21-week lead) | Part | §8A.1 |
| — | Hookup wire | 18 AWG (24 V), 22 AWG (signal), PTFE preferred | Class | §7.3 |

> The supply is a switcher sitting at the antenna entry point, directly on the receive path.
> §8A.1 requires it in the **Control chamber — never Sampler or RF**.

---

### 10.11 Enclosure, mechanical, EMI

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 1 | Aluminum sheet, 12 ga | **36 × 48″** 5052-H32 (0.081″), 65% used — floor, top, shelf, bulkhead, partition, deck, tray, sampler base (TUNER-E-211) | Part | E-211 |
| 1 | Aluminum sheet, 14 ga | **48 × 48″** 5052-H32 (0.064″), 66% used — RF service panel, cassette face, four side panels, rear (TUNER-E-211) | Part | E-211 |
| — | Angle stock | **6061-T6: 1 × 1 × 1/8 — 24.3 ft; 1-1/2 × 1-1/2 × 1/8 — 1.3 ft (corner clips); 1/2 × 1/2 × 1/8 — 4.3 ft; 2 × 2 × 3/16 — 3.5 ft** (incl. kerf; TUNER-E-201, Rev 3.7c) | Part | E-201 |
| 16 | Corner clip | 1-1/2 × 1-1/2 × 1/8 6061-T6 × 7/8″, two Ø0.144″ holes per leg (4 with the front leg cut to 7/8″, one hole) — fabricate on a drill jig | Fabricate | E-201 |
| 60 | Flat-head screw | **#6-32 × 1/2″, 82°, stainless** — frame junctions, countersunk flush in the frame legs | Part | E-201 |
| 60 | Nyloc nut | #6-32 stainless — frame junctions, inside | Part | E-201 |
| 16 | Bulkhead / partition clip | 1/2 × 1/2 × 1/8 6061-T6 × 1.0″, one hole per leg; bulkhead clips' plate legs tapped 8-32 (PEM CLS-832-1 alternative) | Fabricate | E-208 |
| 32 | Machine screw | **8-32 stainless button head** — 16 × 1/2″ (floor / shelf legs), 8 × 3/8″ (partition), 8 × 1/4″ (bulkhead, into the tapped legs) | Part | E-208 |
| 24 | Nyloc nut | 8-32 stainless — floor / shelf legs and the partition | Part | E-208 |
| 384 | Machine screw | **8-32 stainless button head**, 1/2″ — 344 panel holes (TUNER-E-210) + spares | Part | E-210 |
| 384 | Rivnut | 8-32, aluminum, in the frame flanges (match-drilled from the panels) | Part | E-210 |
| ~56 ft | Conductive-elastomer gasket | **G-1 resolved Rev 3.7a** — on every frame flange under a panel, both faces of the shelf; replaces BeCu finger + separate elastomer | Part | §8E.6, E-210 |
| 60 | Captive panel screw | 8-32, RF service panel (38) and cassette face (22) | Class | §8E.6 |
| 6 | Feedthrough capacitor | **Tusonix 2499-003-X5W0-103ZLF** — 0.01 µF, 500 V, 12-28 nut mount; shelf FT1–FT4 (all four used) + 2 spares | Part | §7.3a |
| 1 | RF service-panel interlock | **Littelfuse 59140-1-S-02-A** reed sensor, SPST-NO, with leads ($3.76, 18,012 in stock, Digi-Key 2026-11-19), on the front shelf-ring flange; **Littelfuse 57140-000** magnet ($2.11, 5,208) bonded (VHB) to the panel's inner face above it | Part | §7.4, §9 item 51 |
| 1 | Filtered DB-25 | **Amphenol FCE17-B25SM-250** — 1000 pF, J-A | Part | §7.3a |
| 2 | Filtered DB-25 | **Amphenol FCE17-B25SM-290** — 5600 pF, J-B and J-S | Part | §7.3a |
| 2 | Filtered DE-9 | **Amphenol FCE17-E09SM-290** — 5600 pF; J-E (tank thermal + CT, bulkhead) and J-F (blower, left lower panel) — verify stock | Part | §7.3a, §8 |
| 5 | D-sub plug + metal backshell | Mating DB-25 (3) and DE-9 (2) | Class | §7.3a |
| 2 | Power feedthrough | **Spectrum Control 9910-381-6002** — 0.30 µF, 15 A, 12-32 | Part | §7.3a |
| 2 ft | Shielded cable (W8) | **Belden 8112** — 12.5 pr 24 AWG, overall foil + braid + drain, OD ≈ 0.44″; cut to length, Nassau Electrical $14.88/ft, in stock 2026-11-19 (Digi-Key: 100 ft spools only). Rev 3.7c, §9 item 52; was the 8-pair M13197 | Part | §7.3a |
| — | Coax | **RG-316** — prescaler, partition → bulkhead | Class | §7.3a |
| 3 | Feedthrough capacitor | **Tusonix 2499-003-X5U0-102PLF** — 1000 pF, 500 V, 12-28; prescaler at partition and bulkhead + spare | Part | §8B.0.1 |
| — | Series resistor | *Rev 3.7c:* the 1 kΩ ADC/sensor-input resistors are on the control board as 1206 anti-surge parts (§10.5, Panasonic ERJ-P08J102V); no discrete carbon comp | — | §7.3 |
| 2 | Honeycomb vent panel | **Hex-cell aluminum, 1/8″ cell, 1/2″ thick** (>90 dB to 1 GHz) | Class | §8 |
| 1 | Blower | **Delta AFB1212VHE-F00** — 120 × 38 mm, 12 V 0.6 A, ball bearing, tach; alt. AFB1212SH-F00 (25 mm) | Part | §8 |
| 1 | Fan guard | **Orion G109-15A**, 120 mm wire | Part | §8 |
| 1 | Coax bulkhead adapter | **Amphenol RF 172124** — N jack-jack, PTFE, jam nut; partition X, Ø0.634″ double-D | Part | §7.3a |
| 1 | Intake filter | Washable electrostatic cartridge, over honeycomb | Class | §8 |
| 3 | Membrane vent | **Gore PMF100320** (M12 × 1.5, black) + nut M10510-009, Ø0.480″ hole — **not PMF100318** (M12 × 1); stocked at RS / Distrelec, not Digi-Key | Part | §8E.4 |
| — | Shielded twisted pair | 4-conductor, 18–20 AWG, foil — Control→Motor | Class | §7.3 |
| — | Coax, internal | **RG-393 PTFE** — K1 → X → shelf bulkhead (W15, W17); the choke's RG-400 continues to C1 (§10.2) | Class | §7.3, §6 |

---

### 10.12 Output termination

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 2 | HV feedthrough insulator | **≥10 kV**, ceramic, panel mount, ¼–⅜″ stud | Class | §8D.1 |
| 2 | Output terminal | Brass or copper stud, **6.03″ spacing for #12 open-wire** — measure the actual line | Class | §8D.2 |
| 1 | Strain insulator | Anchored to wall or frame — **takes all mechanical load** | Class | §8D.4 |
| — | Jumper conductor | Same gauge and spacing as the feeder, 1–2 ft maximum | Class | §8D.4 |
| 2 | Lightning arrestor | At the entry baseplate, **antenna side of the tuner** | Class | §8D.5 |
| 1 | C2 static bleed | **100 MΩ, ≥ 10 kV** thick-film HV resistor (or 2 × 50 MΩ / 5 kV in series), across C2's terminals on the deck — drains leg 2, ≈ 0.03 W | Class | §8D.5 |

> §8D.5: leg 1 (deck) is DC-grounded through the input choke's braid; leg 2 floats behind C2 and is
> drained by the 100 MΩ bleed across C2 (≈ 0.03 W). The arrestors remain load-bearing for surges. No
> bleeder from an output terminal to ground (1 MΩ there dissipates 8.8 W).

---

### 10.13 Derived quantities — method, not guesswork

Quantities defined by rules elsewhere in this document, tallied here. *Fastener and gasket
quantities come from TUNER-E-210 (§10.11); the 16 × 16 × 12″ fastener and BeCu tallies are in §11.2.*

**Feedthroughs and filtered contacts (§7.3, §7.3a)**

| Crossing | Part at the wall | Lines |
|:--|:--|--:|
| Control → Motor (logic): STEP1–3, DIR1–3, DRV_EN, encoder SPI incl. MOSI + 3V3, LIM1–6 | J-A, filtered DB-25, 1000 pF | 20 |
| Sampler group, bulkhead: detector/sampler 7, K1/K2 coils 4, cal-load thermal 2, cal-load detector 1 | J-B, filtered DB-25, 5600 pF | 14 |
| Sampler group, partition | J-S, filtered DB-25, 5600 pF | same 14 |
| Control → RF tank: tank thermal, imbalance CT, RF service-panel switch | J-E, filtered DE-9, 5600 pF (FCE17-E09SM-290) | 3 |
| Control → blower: +12 V, GND, tach | J-F, filtered DE-9, 5600 pF, left lower panel | 3 |
| Frequency: ÷1024 prescaler | FT-P, 2 × discrete 1000 pF (partition + bulkhead) | 1 |
| Shelf: tank thermal, imbalance CT, common return, RF service-panel switch | FT1–FT4, discrete 0.01 µF (all four used) | 4 |

Discrete 0.01 µF: 4 shelf + 2 spare = **6**. Discrete 1000 pF: **3** (2 + 1 spare). Filtered D-subs:
DB-25 1000 pF × 1 (J-A), DB-25 5600 pF × 2 (J-B, J-S), DE-9 5600 pF × 2 (J-E, J-F). Plugs and
hoods: DB-25 × 3, DE-9 × 2. The 1 kΩ series resistors on ADC/sensor inputs are on the control board
(§10.5): 1206 anti-surge thick film, Panasonic ERJ-P08J102V, in place of discrete carbon comp. *The earlier 36-line tally is in §11.7.*

---

### 10.14 Open selections — DECISION REQUIRED

These are not omissions. Each is a real trade-off that changes cost or architecture, and inventing
a part number would hide the choice rather than document it.

**C-1 · Second vacuum variable — RESOLVED Rev 3.7 (15 kV-class C1 to buy; UCSX-740-10 → C2)**

The Rev 3.7 working-voltage correction (§5.1) makes a second -10 Jennings inadequate for C1 at
1500 W (0.92×). **Resolution:** the UCSX-740-10 in hand goes to C2; buy a 15 kV-class C1
(UCSX-700-15 / "CB-154" or CVDD-500-15S); the KP1-4 is a spare. The vertical stack (§3.0) fits
either C1 candidate with straight shafts. *Options A/B and their Rev 3.6 notes are in §11.3.*

**R-1 · Roller inductor — RESOLVED Rev 3.7b: C (homebuilt, §5.3a)**

A single 34 µH roller: 5.2″ to wire center, 22 turns #4 solid at 3 TPI, no series link. The Harris /
229-class roller in hand is a spare. *Options A/B/C and their history are in §11.5.*

**M-1 · Absolute multi-turn encoder (×3) — the cost driver**

Requirement: absolute position across the element's **full travel (~30 turns)**, surviving power
loss with no homing cycle (§7.1, §8B.4b). Low-cost magnetic encoders are **single-turn**; genuine
multi-turn absolute is an industrial part.

| Option | Approach | Indicative cost (×3) | Trade |
|:--|:--|:--|:--|
| **A** | Industrial multi-turn SSI/SPI (Posital IXARC class) | **$600–1200** | Drops straight in. Expensive |
| **B** | Single-turn absolute (AS5048A class) on a zero-backlash **timing-belt reduction** so full travel < 1 rev | **$60–120** | Cheap and absolute, but the reduction must be belt or friction — **any geared backlash lands directly in the position reading**. *Rev 3.7b:* the 22-turn roller needs **≥ 24:1** shaft-to-encoder (two belt stages, 2 turns' margin); 14 bits then give 16384 / 24 ≈ 683 counts per roller turn, ≈ 1.1 counts per step at 600 steps/turn (0.6° at the element) — enough to verify every step |
| **C** | Single-turn absolute + firmware turn counter, battery-backed | **$60–100** | Cheapest. **Forfeits the power-loss guarantee** when the battery dies — contradicts §8B.4b |

**Adopted (Rev 3.7b): B** — AS5048A in the encoder / limit-cam module (§7.1, §10.6). It preserves the absolute-across-power-loss property that §8B.4b depends on,
at roughly a tenth of A. It does add a mechanism per axis, which belongs in Section 7 before it
belongs in a BOM.

**M-2 · Motor frame and reduction ratio — RESOLVED Rev 3.7b: StepperOnline 23HS22-2804S, direct on all three axes**

*Datasheet (2020-10-30): 1.20 N·m holding (page says 1.24), 2.8 A, 0.90 Ω, 2.60 mH, 300 g·cm², 56 mm body, Ø6.35 mm × 21 mm shaft with flat, Ø38.1 mm pilot, 47.14 mm □ Ø5.2 holes, side lead exit, 0.7 kg, ≈ $13.40, in stock (2026-11-16). Pull-out on DM542T at 24 V: ~0.82 / 0.72 / 0.60 / 0.36 N·m at 300 / 450 / 600 / 900 rpm (1 / 1.5 / 2 / 3 kHz full step); at 36 V ~0.82 N·m to 600 rpm and ~0.52 at 900. Run 1.5–2 kHz on the 24 V rail (≥ 1.5× over the 0.4 N·m cap figure); 3 kHz needs a 36 V motor supply. Depth: pulley 0.6 + coupler 1.0 + plate 0.125 + body 2.20 ≈ 3.93″ of the 5.00″ layer — 1.05″ under the motors (model). Band changes ~3–4 s worst (§8B.3a). The option table below is kept for the reasoning.*

The 0.4 N·m of §3.1 is stated for **the vacuum capacitor mechanism**. The homebuilt roller is not
built yet, so its torque is unmeasured (rotor inertia ≈ 30 lb·in², estimate), and it may need more.

| Option | Buys | Torque at element | Depth | Trade |
|:--|:--|--:|--:|:--|
| **A** | 2 × 23HS30-2804S | 1.90 N·m (4.75×) | 5.22″ — **0.22″ over** | Simplest drive. Needs a deeper bay. 53 W idle heat |
| **B** | nothing | 1.26 N·m (3.15×) | 3.54″ — 1.46″ spare | 3 × NEMA 17 + 3:1 belt. 18 s full travel, 0.60°/step, ~31 W |
| **C** | nothing | roller 1.90×, caps 1.26× | mixed | NEMA 23 direct on the roller, NEMA 17 + belt on both caps |

**Settle this by measurement, not estimate.** C2 is in hand; C1 is to be bought and the roller to be
built. Measure breakaway and running torque on each with a spring scale on a known radius. If the
roller stays under 1.26 N·m, **B buys
nothing and fits best**; if it exceeds that, **C** puts the large motor where the load is.

Reduction also costs slew time (modeled in §8B.3a: band changes ~6 s with A, ~16–18 s with B) — 3:1 takes full travel from 6 s to 18 s at 1 kHz — while *improving*
resolution from 1.80° to 0.60° per step at the element. Belts are zero-backlash, so the reduction
does not degrade position the way a geared head would.

**I-1 · SB-220 keying interface** — §7.4.4 specifies the switch defensively for the stock +120 V
case. §9 item 14 requires **measuring** which regime the modified amplifier actually presents
before the opto-MOSFET and its cable are finalized.

**G-1 · Gasket strategy — RESOLVED Rev 3.7a: conductive elastomer** on the frame flanges
(TUNER-E-202 to E-208; §8E.6). *Options history in §11.7.*

**L-1 · Choke turn count** — *resolved Rev 3.7c:* 15 turns of RG-400 on 5 × FT-240-61 (§6). The installed VNA sweep (§9 item 49) may take off a turn; 12 ft of RG-400 covers any outcome.

---

### 10.15 Discrepancies found while compiling this section

Five inconsistencies surfaced when the scattered specifications were put in one table. Items 1–4 are
resolved or superseded and are kept in §11.10; item 5 remains:

5. **Parts named in the body but missing from §10** *(Rev 3.7a sweep)*. §10.0 claims the BOM is
   complete; it is not until these are added: two Fair-Rite #61 toroids (§6), the 0–30 pF
   trimming vane (§2.2), the bifilar imbalance CT (§2.2), an RF-bay thermal sensor (§9 item 16),
   the RF service-panel interlock switch (§7.4), the mains surge suppressor (§8A.3), the Ethernet surge
   arrestor at the entry panel (§8A.3, §8C.3.1), the fan-lead bifilar chokes (§8) and the shaft
   lip seals (§8E.4).


---

## Section 11 — Superseded Designs and Decisions

*Rev 3.7b; 11.11–11.12 added Rev 3.7c.* Design content that no longer describes the tuner, kept verbatim for its derivations and
as the record of why the current design is what it is. Nothing here is current: **do not build or
order from this section.** Each subsection says what superseded it and where the current design is.
Section and item cross-references inside the moved text refer to the document as it was when the
text was written.

### 11.1 Side-column enclosure (Rev 3.3–3.6)

*Superseded by the Rev 3.7 vertical stack (§3.0; TUNER-E-200 to E-216).*

#### Rev 3.3–3.6 side-column layout *(SUPERSEDED by §3.0)*

**FIX APPLIED — the utility column has been re-proportioned and re-ordered.** Rev 3.2's layout
placed three NEMA 23 motors in a 5.50″ bay (they need 6.66″ in a row) and put the Control chamber at
the *rear* while assigning it the *front* display.

Outer envelope **16.00″ W × 16.00″ D × 12.00″ H** *(Rev 3.6: raised from 10.00″ for roller and
capacitor headroom; deck-to-lid is now 9.42″)*. One longitudinal spine wall divides the box into
an RF bay and a utility column; two transverse walls subdivide the column.

```
 <------------------------------ 16.00" WIDTH ----------------------------->
 +-----------------------------------------------+----------------------+   ^
 |                                               |   CONTROL CHAMBER    |   |
 |                                               |  5.37"W x 3.71"D     |   |  FRONT
 |                                               |  - MCU / ADC board   |   |
 |                                               |  - Display + encoders|   |
 |                                               +----------------------+   |
 |              RF TANK CHAMBER                  |    MOTOR CHAMBER     |   |
 |            10.42" W x 15.87" D                |  5.37"W x 7.00"D     | 16.00"
 |                                               |  - 3x NEMA 23 inline |  DEPTH
 |   [UCSX Cap 1]  [Harris Roller]  [UCSX Cap 2] |  - Encoders (rear)   |   |
 |   [Floating Deck 8.50" W x 13.00" D]          |  - Limit switches    |   |
 |   [4-Bit HV Doorknob Array]                   +----------------------+   |
 |                                               |   SAMPLER CHAMBER    |   |
 |                                               |  5.37"W x 5.00"D     |   |  REAR
 |                                               |  - Bruene bridge     |   |
 |                                               |  - 1:1 input choke   |   |
 +-----------------------------------------------+----------------------+   v
 <--------------- 10.42" ----------------------> <------- 5.37" ------->
```

**Dimensional closure — verified**

```
WIDTH :  10.42 (RF) + 5.37 (util) + 0.081 (spine) + 2 x 0.064 (sides) = 15.999"   OK
DEPTH :  16.000 - 0.128 (front+rear panels) - 0.162 (2 transverse walls) = 15.710"
         Control 3.71 + Motor 7.00 + Sampler 5.00 = 15.710"                        OK
```

**Why this ordering**
- **Control at the front** — it hosts the display and manual encoders, which must front the front
  panel. 3.71″ is ample for an MCU board behind a panel-mounted display.
- **Motor in the middle, 7.00″ deep** — three NEMA 23 (2.22″ square) in a row along the depth axis
  need 6.66″. They now fit inline, every shaft exiting toward the RF bay at its own depth station,
  all at one height. This is what makes the short-shaft geometry work.
- **Sampler at the rear, 5.00″ deep** — adjacent to the rear-panel input connector where the Bruene
  bridge belongs, and deep enough for the 4.25″ OD input choke (Section 6).

#### From §3.1 — staggered shafts in the side-column box

The three
driven components cannot sit in a single line across 6.66″ of depth — two 3.0″ capacitors
plus a 4.5″ roller inductor need 10.5″ in a row. They are therefore **staggered in width as well as
depth**, which gives unequal shaft lengths.

#### From §2.2 — floating-deck parasitics, side-column box (Rev 3.6)

**Parasitic budget, derived:**

| Contribution | Value |
|:--|--:|
| Deck plate to floor, 8.50″ × 13.00″ at d = 2.50″ (`C = ε₀A/d`) | 9.94 pF |
| Fringing (perimeter 43.0″, Palmer) | ≈ 6.5 pF |
| Top coupling to lid at 7.0″ *(Rev 3.6, was 5.0″ / 5.0 pF)* | ≈ 3.6 pF |
| Component bodies on deck | ≈ 7.0 pF |
| **Total C_deck-chassis** | **≈ 27.0 pF** |


#### From §7.5 — local panel fit, side-column control chamber

Control chamber fronts **5.37″ W × 12.00″ H** of the front panel. *Rev 3.7a: side-column figures — in
the vertical stack the Control chamber front is ~15.87″ W × 5.00″ H; re-lay out per §9 item 29.*

```
Display : 3.5" TFT (ILI9488 / Nextion NX4832T035), bezel 3.96" W x 2.56" H
          -> 0.70" margin each side within 5.37"                    FITS

Vertical stack (12.00" available):
  top margin 1.00 + display 2.56 + gap 1.00 + encoder 1.25
  + gap 1.00 + encoder 1.25 + bottom margin 3.94  = 12.00"          FITS
```

#### From §6 — input-choke former and the side-column sampler chamber

**FIX APPLIED — former diameter reduced from 6.0″ to 4.0″.** The 6.0″ former did not fit the 5.37″
Sampler chamber in any orientation.

### 11.2 Materials, cut list, nesting and tallies for the 16 × 16 × 12″ box

*Superseded by the vertical-stack drawings TUNER-E-201 (frame), E-210 (parts list, fastener holes) and E-211 (nesting), and by the G-1 conductive-elastomer gasket (§8E.6); current text in §4, §10.11 and §10.13.*

#### From §4 — cut list, nesting and frame (Rev 3.6 / 3.7 notes)

> **Rev 3.7: the table and nesting below are for the superseded 16 × 16 × 12″ side-column box.**
> The vertical stack (§3.0) is 16.00″ × 16.00″ × 21.00″ H. Its parts: four 16 × 21″ outer panels
> (front, rear, sides), floor, shelf, lid, two 15.87 × 5.00″ utility partitions, and a 10.75″ ×
> 10.75″ deck. There is no spine. Cut list, nesting, frame angle and tallies are to be re-derived
> (§9 item 29).
>
> *Rev 3.7a: re-derived for the wall-mounted vertical stack in **TUNER-E-201** (frame cut list) and
> **TUNER-E-211** (nesting); see Appendix B. The tables below are kept for their reasoning only.*

**Sheet:** 5052-H32 aluminum — chosen over 6061-T6 for formability; it bends 90° without the
cracking 6061-T6 exhibits at tight radii.

| Panel | Dimensions | Qty | Gauge |
|:--|:--|--:|:--|
| Chassis floor | 16.00″ × 16.00″ | 1 | 12 ga (0.081″) |
| Longitudinal spine wall | 16.00″ × 12.00″ | 1 | 12 ga (0.081″) |
| Transverse sub-wall (Control/Motor) | 5.37″ × 12.00″ | 1 | 12 ga (0.081″) |
| Transverse sub-wall (Motor/Sampler) | 5.37″ × 12.00″ | 1 | 12 ga (0.081″) |
| Floating sub-deck plate | 8.50″ × 13.00″ | 1 | 12 ga (0.081″) |
| Front UI panel | 16.00″ × 12.00″ | 1 | 14 ga (0.064″) |
| Rear connection panel | 16.00″ × 12.00″ | 1 | 14 ga (0.064″) |
| Side wall panels | 16.00″ × 12.00″ | 2 | 14 ga (0.064″) |
| Removable lid | 16.00″ × 16.00″ | 1 | 14 ga (0.064″) |

**Raw stock — nesting verified, not just area-checked**

- **12 ga:** one **36″ × 36″** sheet. Parts total 687 in² of 1,296 in² *(Rev 3.6, 12″ walls)*. Floor
  in one corner; spine (16 × 12) beside it; both sub-walls (12 × 5.37, rotated) stacked under the
  spine; deck plate below the floor.
  *(A 24″ × 36″ sheet passes on area and fails on layout — after the 16×16 floor the remnants are an
  8×36 strip and a 16×20 region, which cannot yield a third 16″ part.)*
- **14 ga:** one **36″ × 48″** sheet *(Rev 3.6)*. Parts total 1,024 in²: lid plus four 16 × 12 panels.
  A 36″ × 36″ sheet passes on area but fails on layout — three 12″ panels across 36″ leave no
  saw kerf. On 36 × 48: lid and two panels in one 16″ column (to 40.25″), two panels in the next.
- **Frame:** **22 linear feet** of 1″ × 1″ × 1/8″ **6061-T6** angle *(Rev 3.6: four vertical corners
  2″ longer; was 20 ft)*.

*Former assembly notes:*

- 8-32 stainless button-head fasteners on **1.75″ centers** (λ/20 at 30 MHz is 19.7″, so this is
  more than sufficient for HF RF tightness)
- Beryllium-copper finger gasket along every partition seam and under the lid
- Yields >85 dB shielding at HF while keeping the RF bay serviceable

#### From §10.13 — fastener and BeCu tallies (Rev 3.6 geometry)

Three quantities are defined by rules in Sections 4 and 7.3 but were never tallied. Computed from
the 16″ × 16″ × 12″ geometry *(Rev 3.6)* with a 5.00″-deep utility strip and three 5.37″ bays:

**Fasteners — 8-32 on 1.75″ centers (§4)**

| Seam | Length |
|:--|--:|
| Floor to 4 perimeter walls | 64.00″ |
| Vertical corners (4) | 48.00″ |
| Lid to wall tops | 64.00″ |
| Spine wall to floor | 16.00″ |
| Spine wall to front + rear panels | 24.00″ |
| Transverse sub-walls (2 × floor + spine + outer) | 58.00″ |
| **Total seam length** | **274.00″ (22.8 ft)** |

274.00 ÷ 1.75 = 157, plus ~14 seam-end fasteners ≈ **171. Order 200.**

**BeCu finger gasket (§4)**

Under lid (wall tops 64.00″ + spine top 16.00″ + sub-wall tops 10.74″) = 90.74″; partition seams
98.00″. **Total 188.74″ = 15.7 ft. Order 20 ft.**

#### From §10.11 — earlier sheet stock

- 12 ga: Side-column basis was 36″ × 36″, 5052-H32 (0.081″) — floor, spine, sub-walls, sub-deck
- 14 ga: Rev 3.6 basis was one 36″ × 48″, 5052-H32 (0.064″) — panels, sides, lid

### 11.3 Capacitor complement history

*Settled in Rev 3.7 (DECISION C-1, §10.14): UCSX-740-10 → C2, a purchased 15 kV-class C1, KP1-4 a spare. Current figures are in §5.1.*

#### From §5.1 — Rev 3.4 capacitance and voltage figures

*Rev 3.4 figures, superseded:*

```
Coverage, bare capacitors        : 26/27   (only gap: 160 m @ 1.800 MHz)   -- not reproduced
Worst voltage utilization        : 59% of rated withstand  ->  1.69x margin
Largest capacitance demanded     : 666 pF  (part reaches 675)               -- policy artifact
```

Rev 3.4 put the worst case at 160 m 1.900 MHz: 5,267 V peak across C1 at 123 pF. The re-run puts it
at 1.800 MHz (5.99 kV padded, 6.54 kV bare); §1.3 now carries these figures (Rev 3.7a).

| Requirement (Rev 3.4, superseded by the re-run above) | C1 (input) | C2 (output) |
|:--|--:|--:|
| Capacitance range demanded | 33 – 347 pF | 25 – 830 pF |
| Peak voltage | 6,102 V | 4,170 V |
| Available (part) | 20 – 675 pF | 20 – 675 pF + pad |

#### From §5.1 — why the old figures disagreed

**Why the old figures disagreed.** The lowest-loss T solution always runs C2 to the top of
whatever range it is given. With the pad that is ~830–875 pF (Rev 3.4's "25–830 pF"); bare it
pins at ~666–675 pF (Rev 3.4's "666 pF"; the Rev 3.5 re-run's "671 pF"). **Neither number is a
requirement.** They are where the optimizer parks, not what the match needs. The real requirement
is the smallest C2 that matches, and that never exceeds 270 pF. The "26/27, gap at 160 m @ 1.800"
claim is not reproduced.

#### From §5.1 — coverage with the KP1-4 as C2 (Rev 3.6 run)

```
Coverage, KP1-4 as C2 (20–1000 pF)         : 27/27
```

#### Former §5.1a — Second variable in hand — Soviet KP1-4, 20–1000 pF / 10 kV

Datasheet: [eandc.ru/pdf/kondensator/kp1-4.pdf](https://eandc.ru/pdf/kondensator/kp1-4.pdf)
(20–1000 pF variant; glass envelope, confirmed on the part).

| Parameter | KP1-4 rating | Requirement / impact |
|:--|--:|:--|
| Capacitance | 20–1000 pF, ±5 / ±10% | C2: ≤ 270 pF needed to match (§5.1 re-run; 830 pF was a solver artifact) — covered bare |
| Nominal voltage | 10 kV | C1 6.54 kV / C2 2.40 kV pk (§5.1) — adequate in C2; in C1 only if 10 kV is a working rating, not test (unconfirmed) |
| Working current | ≤ 50 A | 18.4 A RMS worst case (§1.7) — 2.7× |
| Frequency | ≤ 30 MHz | 10 m top edge 29.7 MHz — at the limit, no headroom |
| Drive torque | ≤ 0.49 N·m | §3.1 assumed 0.4 N·m — re-size per DECISION M-2 |
| Axial tuning force | 344 N | Leadscrew thrust must be taken by the cap's own mount, not the coupling |
| Tuning cycle life | up to 5,000 cycles | Low for an auto-tuner — see below |
| Tuning speed | ≤ 5 cycles/min | M-2 option A (6 s full travel) sits at the limit; B (18 s) is well under |
| Size, D × L | 145 × 278 mm (5.7″ × 10.9″) | vs 3.0″ class assumed in §3 — **does not fit** (§3.2) |
| Mass | ≤ 3.2 kg | Needs a cradle/clamp mount; cannot hang on the shaft or end ring |
| Minimum service life | 1,000 h | — |
| Environment | −60 to +125 °C, to 533 hPa | Fine |

**Placement, if it fits:** C2 (output). *Rev 3.6:* the §5.1 re-run shows the 830 pF "demand" was
an optimizer artifact. The bare Jennings already covers 27/27, so the KP1-4 removes nothing that is
required; at C2 it saves the same ~20–28 W on 160 m that the pad does, and no more.

**Cycle life.** 5,000 cycles is the binding mechanical life. Firmware must prefer stored-position
recall over full sweeps (§7.6, §8B.3), and the axis driving the KP1-4 must be speed-limited to
≤ 5 cycles/min. Log cumulative travel per axis in EEPROM (§8B.5) so wear is visible.

#### From §3.1 — KP1-4 drive torque

> **Rev 3.5:** the KP1-4 (§5.1a) is rated **≤ 0.49 N·m** drive torque, 23% above the 0.4 N·m used
> here. Windup scales linearly (10″ span → 2.2°, still negligible), but motor sizing in DECISION
> M-2 must use 0.49 N·m for any axis that drives the KP1-4.

#### From §3.2 — KP1-4 envelope

| Requirement | Value |
|:--|--:|
| *Rev 3.5:* KP1-4 envelope (5.7″ dia × 10.9″) plus 2.25″ each side | **10.2″ × 15.4″** — does not fit a 10.42″ × 15.87″ × 12.00″ H bay with drive coupling — its 10.9″ length exceeds the width, and upright it exceeds the 9.42″ above the deck (DECISION C-1) |

#### From §10.14 — DECISION C-1 options and notes

The KP1-4 in hand (§5.1a) is electrically adequate in either position but needs ~10.2″ × 15.4″ of
envelope with clearance, against a 10.42″ W × 15.87″ D × 12.00″ H RF bay that must also hold the
other cap, the roller and the floating deck (§3).

*Rev 3.6:* the bay is now 12″ H, but that alone does not admit the KP1-4: its 10.9″ length exceeds
the 10.42″ width, and upright it exceeds the 9.42″ above the deck. B still needs the depth
orientation and a right-angle drive — the same mechanism §9 item 28 may need for the roller.

| Option | Approach | Cost | Trade |
|:--|:--|:--|:--|
| **A** | Buy a second 20–675 pF / 10 kV Jennings-class variable; KP1-4 becomes a spare | one cap | Keeps §3 layout, §5.1 analysis and M-2 torque as written. Pad + relay stay |
| **B** | Enlarge the RF bay (≥ ~12″ H, or lay the KP1-4 along the depth axis with a right-angle drive) and fit KP1-4 as C2 | sheet + rework of §3/§4 | Could delete the 200 pF pad and one vacuum relay (pending §10.15 item 4 re-run). Adds 0.49 N·m axis, 5,000-cycle life limit, 3.2 kg mount, 30 MHz ceiling |

*Rev 3.7 — superseded.* **C-1 is resolved by a different route:** the Rev 3.7 working-voltage
correction (§5.1) makes a second -10 Jennings inadequate for C1 at 1500 W (0.92–1.00×). So
neither A nor B as written stands. **Resolution:** the UCSX-740-10 in hand goes to C2; buy a
15 kV-class C1 (UCSX-700-15 / "CB-154" or CVDD-500-15S); the KP1-4 is a spare. The vertical
stack (§3.0) fits either C1 candidate with straight shafts.

*Rev 3.6 — re-run done (§5.1).* The pad is not required for coverage with a bare Jennings (27/27);
it only trims ~20–28 W of roller loss on 160 m. So B removes nothing that A needs, and it does not
fit the bay in any usable orientation (§3.2). **Recommendation: A.** Whether to keep the pad on A
is a separate, minor choice (§5.2).

#### From §10.14 — DECISION M-2, KP1-4 note

*Rev 3.5:* if DECISION C-1 selects B, the KP1-4 axis needs **0.49 N·m** (datasheet), which
B and C still clear at 1.26 N·m (2.6×).

### 11.4 Output padding: 4-bit array (Rev 3.3), 200 pF pad (Rev 3.4–3.7a), deleted (Rev 3.7b)

*Deleted in Rev 3.7b (§5.2): the bare C2 covers all 27 band edges; current loss and voltage figures are in §5.1 and §1.7.*

#### Former §5.2 — Output pad — one capacitor, one relay

The 4-bit binary array of Rev 3.3 is **deleted**. It existed only to keep the variables unmeshed
for voltage reasons; with real stress figures that rationale disappears. One fixed capacitor
closes the single remaining gap at the bottom of 160 m:

| Pad | C_var then | V_pad pk | I_pad | Variable utilization |
|--:|--:|--:|--:|--:|
| **200 pF** | 493 pF | 2,341 V | 3.75 A | 47% |

**Specification:** one 200 pF transmitting doorknob (Centralab 858 or K15U-2 class),
**≥10 kV peak, ≥40 kVAr**, switched by one vacuum relay. A 40 kVAr part handles ~9.6 A at
1.8 MHz and sees 3.75 A — 2.6× margin.

*Deleted from Rev 3.3: seven doorknob capacitors, three vacuum relays, the binary decoder, the
16-state coverage table, and the per-unit LCR calibration procedure.*

> **Rev 3.6 — the pad is optional.** The §5.1 re-run finds **no gap** to close: a bare Jennings
> covers all 27 band edges (the smallest C2 that matches is ≤ 270 pF). The pad's only effect is
> lower loss on 160 m: ~28 / 23 / 19 W less roller dissipation at 1.800 / 1.900 / 2.000 MHz
> (1500 W, Q = 250; ~1.7× that at Q = 150), and ~0.5 kV less on C1 at 1.800 MHz.
>
> | | Keep the pad | Delete it |
> |:--|:--|:--|
> | Parts | 200 pF doorknob + 1 vacuum relay | none |
> | 160 m 1.800–1.850 derate (§1.7.1) | 570 W | ~530 W |
> | C1 peak at 1.800 MHz | 6.0 kV (1.50× to 9 kV working) | 6.5 kV (1.38× to 9 kV working) |
> | Firmware | Pad state in every stored profile | One fewer element |
>
> Not yet chosen. The relay count in §5.5 assumes the pad is kept.

#### From §5.1 — coverage with the pad (Rev 3.6 run)

```
Coverage, with 200 pF pad (220–875 pF)     : 27/27
```

#### From §5.1 — what the pad bought

**What the pad actually buys: loss, not coverage.** Lowest-loss solution, roller Q = 250, 1500 W:

| Point | Bare: C1 / C2 | Bare: V_C1 pk | Padded: V_C1 pk | Roller loss bare / padded | Saved |
|:--|:--|--:|--:|--:|--:|
| 160 m 1.800 | 105 / 675 pF | 6.54 kV | 5.99 kV | 341 / 313 W | 28 W |
| 160 m 1.900 | 135 / 674 pF | 4.82 kV | 4.34 kV | 236 / 213 W | 23 W |
| 160 m 2.000 | 185 / 674 pF | 3.34 kV | 2.93 kV | 154 / 135 W | 19 W |
| 60 m 5.332 | 235 / 674 pF | 0.99 kV | 0.91 kV | 30 / 28 W | 2 W |
| all others | — | — | — | — | ≤ 1 W |

Roller current is the same to 0.1 A either way (18.4 A at 1.800 MHz). Dropping the pad costs ~8%
more roller loss on 160 m only (~47 W at Q = 150), moving the 1.800–1.850 MHz derate (§1.7.1) from
**570 W to ~530 W**, and raises the C1 peak at 1.800 MHz from 6.0 to 6.5 kV: against a 15 kV-class
C1 (9 kV working), 1.38× margin, from 1.50× *(Rev 3.7 basis; Rev 3.6 stated 1.36× / 1.49× against
the test rating)*. **The pad is optional** (§5.2).

#### From §5.1 — padded demand table

**Demand under the lowest-loss policy, padded** (cf. §1.3, which used the geometry envelope):

| Quantity | Value |
|:--|--:|
| C1 range used | 25 – 316 pF |
| C2 range used (total) | 448 – 874 pF — policy-driven, see above |
| L range used | 0.46 – 34.40 µH (pins at the top of range at 40 m @ 7.000) |
| Max V_C1 / V_C2 / V_L, peak | 5.99 / 1.86 / 6.00 kV |
| Max roller current | 18.4 A RMS (160 m @ 1.800) |

#### From §9.1 — parts summary row

| Item | Source | Status |
|:--|:--|:--|
| 1 × 200 pF doorknob, ≥10 kV / ≥40 kVAr | to buy | output pad |

#### From §10.1 — BOM row

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 1 | Transmitting doorknob capacitor | **200 pF, ≥10 kV pk, ≥40 kVAr** — Centralab 858 or K15U-2 class | Class | §5.2 |

### 11.5 Roller history: Harris / 229-class (R-1 A), purchased (R-1 B), homebuilt 3.5″ and 4.7″

*Superseded by DECISION R-1 = C (Rev 3.7b): the single 34 µH / 5.2″ / 22-turn homebuilt roller of §5.3a, with no series link. The Harris roller in hand is a spare.*

#### Former §5.3 — Roller inductor — Harris 492-0309-000, measured

> **Rev 3.6 — this part is under-rated and damaged.** Re-identified as a **Cardwell/Johnson
> 229-203-class** roller (0.1–28 µH, **#12 tinned wire**, caliper 0.081″). Surplus listings rate
> that class at **5–10 A**, against **18.4 A** demanded on 160 m. Its front ceramic end plate has
> also been broken (replacement: Surplus Sales 229EP-LOG). Kept as-is it limits 160 m to roughly
> **110–145 W at 5 A or 445–580 W at 10 A**; 80 m top edge, 12 m and 10 m to ~600 W at 5 A; all other
> bands are unaffected. The replacement path is DECISION R-1 (§10.14); the homebuilt option is §5.3a.
> The table below remains valid as a measurement of this coil.

Pulled from a Harris SX-5A coupler. Variable-pitch winding (turns closer at one end), which
linearizes µH per shaft revolution — exactly the characteristic wanted for stepper control.

| Parameter | Value |
|:--|--:|
| **Measured range (end-to-wiper)** | **0.20 – 24.40 µH** (122:1) |
| Measured at | 200 kHz (Peak Atlas LCR) |
| Range demanded by the design | 0.46 – 31.70 µH |
| Current demanded | **18.4 A RMS** (160 m) |

**Low end: covered with margin** — 0.20 µH available against 0.46 µH demanded.
**High end: 7.3 µH short** — hence the series link below.

**Self-resonance is not a limiting factor.** For this coil, inductance and distributed capacitance
both scale with the winding in use, so Cd is not fixed: ~5 pF at full mesh falling to ~0.1 pF near
minimum. Worst case across all bands is **f/SRF ≈ 0.48**, comfortably clear. The 200 kHz
measurement is therefore valid for the inductance value.

#### From §10.14 — DECISION R-1 options and notes

**R-1 · Roller inductor — keep, buy, or build**

The roller in hand is 229-203 class (#12 wire, 5–10 A) against 18.4 A demanded on 160 m, and its
end plate is broken (§5.3).

| Option | Approach | Cost | Trade |
|:--|:--|:--|:--|
| **A** | Keep the 229; replace the end plate (Surplus Sales 229EP-LOG); firmware power limit on 160 m | end plate | 160 m ~110–580 W depending on the true rating; heat test at commissioning sets the limit. Link stays 10 µH |
| **B** | Buy a heavy ~22 µH roller (e.g. eBay 236849096846, #6–#8 solid, 9⅜″ × 4½″ × 6½″; RF Parts L402 class) | ~$140 surplus / ~$330 new | Unrated surplus; verify by the same heat test. Link to 12.5 µH |
| **C** | Build per §5.3a: Ultem rib cage, #4 solid, **18 turns at 4.7″** (Rev 3.7; was 26 turns at 3.5″) | Ultem stock + wire + wheel hardware | Full control of conductor and pitch; the wheel contact is the real build risk. Link to 12.5 µH |

*Rev 3.6:* B and C (9⅜″ and ~12.6″ overall) **do not fit across the bay width** that the drive
train imposes (§5.3a, "Fit in the RF bay"). Either needs a right-angle drive or motor pod, or C
is re-sized: at 12″ H, a ~16 µH roller at 5.2″ with a ~16 µH link fits with the existing relay
count. Settle alongside C-1 in the mock-up.

*Rev 3.7:* the vertical stack (§3.0) removes the width limit. **B (9⅜″) and C at 4.7″ (9.9″) both
fit upright.** C is now specified at 4.7″ / 18 turns (§5.3a, Rev 3.7 note). The choice between A,
B and C is still open.
No recommendation between B and C — B is cheaper and faster, C is the only one with a known conductor.

#### From §5.3a — end brackets for a horizontal shaft (Rev 3.6)

**End brackets**

Two upright **½″ Ultem** plates, bolted and doweled to the floating deck, one at each end.

| Function | Bracket A (drive / cold end) | Bracket B (far end) |
|:--|:--|:--|
| Shaft bearing | Yes — **axially fixed** (thrust collars both sides, PTFE washers) | Yes — **axially free** (sliding fit) for thermal growth |
| Bus rod (hot, 6.1 kV pk) | One end | Other end |
| Finger contact block + deck strap | Yes | — |
| Wheel-carriage end stop | Stop collar on bus rod | Stop collar on bus rod |

```
  End view (looking along the shaft):

        ┌─────────────────────────┐
        │                         │
        │      ◎ shaft            │   ◎ bearing — cold (deck potential)
        │      bearing   ○ bus    │   ○ bus rod — HOT, edges radiused ≥ 1/16″,
        │                  rod    │     ~3.2″ from axis, level with it
        │                         │
     ┌──┘                         └──┐
     │ ▪  foot, bolted + doweled ▪  │  ← deck (cold)
     └───────────────────────────────┘
```

| Dimension | Value | Basis |
|:--|--:|:--|
| Bracket | ~5″ W × 6½″ H × ½″ | Fits the 3.5″ coil with bus rod alongside |
| Shaft axis above deck | **~3½″** | Hot turns (r ≈ 1.95″) ≥ 1.5″ above the deck (§3.2) |
| Bus rod position | **Level with the axis**, beside the coil, facing bay center | Keeps the bracket short. At 12″ H, above the coil is also legal (~6¾″ up, ~2.7″ to the lid) |
| Bus rod offset | ~1¼″ outside the wire surface | Wheel carriage slides on the rod; spring arm presses wheel to wire |
| Creepage, bus rod hole to any cold part on the bracket | **≥ 2″** (layout gives ~3″) | Ultem's tracking index is modest; slot the plate if a cold part comes closer |

#### From §5.3a — fit in the side-column RF bay (Rev 3.6)

**Fit in the RF bay — orientation conflict (§9 item 28)** *(Rev 3.6 analysis, side-column box —
resolved by the Rev 3.7 note below)*

The drive train does not allow the roller to lie along the bay depth. All three motors sit in
a row along the depth axis (§3) and **every element shaft crosses the spine across the width**.
Across the width the roller must fit on the 8.50″ deck: overall length ≈ winding + ~3.9″
(brackets, discs, contact collar), so **winding ≤ ~4.5″**. Height is also capped: the deck sits
2.58″ up a 12.00″ bay *(Rev 3.6; was 10.00″)*, leaving 9.42″, and the hot turns need 1.5″ to the lid
as well as to the deck.

Effect of coil diameter (#4 at 3 TPI; diameter to wire center; height fit for the 12″ bay):

| Roller max | Dia | Turns | Winding | Overall | Wire | Rotor inertia | One turn | Fits width | Fits height |
|--:|--:|--:|--:|--:|--:|--:|--:|:--:|:--:|
| 22 µH | 3.7″ | 26 | 8.7″ | 12.6″ | 25 ft | 11 lb·in² | 0.18 µH | no | yes |
| 22 µH | 4.7″ | 18 | 6.0″ | 9.9″ | 22 ft | 15 lb·in² | 0.24 µH | no | yes |
| 22 µH | 6.2″ | 13 | 4.3″ | 8.2″ | 21 ft | 26 lb·in² | 0.35 µH | yes (0.3″) | yes (0.02″) |
| **16 µH** | **5.2″** | **13** | **4.3″** | **8.2″** | 18 ft | 15 lb·in² | 0.28 µH | **yes (0.3″)** | **yes (1.0″)** |
| ~11 µH | 4.2″ | 12 | 4.0″ | 7.9″ | 13 ft | 7 lb·in² | 0.21 µH | yes (0.6″) | yes (2.0″) |

**Width, not height, is now the binding limit.** At 12″ H every diameter clears the lid, but only
coils with ≤ ~13 turns fit across the deck. A 22 µH roller does that only at 6.2″, with no height
margin, 2.3× the inertia, ~0.35 µH per turn against a 0.46 µH demand, and 10+ ribs to hold the
polygon bump down. Wire length falls only ~16% from 3.7″ to 6.2″, so Q rises only about as much.

Resolutions, none yet chosen:

1. **Right-angle drive, roller along the depth** — zero-backlash only (90°-twist timing belt or
   anti-backlash mitres), because any backlash is invisible to the motor-side encoder. Same
   mechanism DECISION C-1 option B needs for the KP1-4.
2. **Separate motor pod** on the RF bay's front or rear wall, driving along the depth directly.
3. **Smaller roller, bigger link — now the leading option at 12″ H.** A **~16–17 µH roller at
   5.2″ (13–14 turns)** fits across the deck with the existing drive and 1″ of height margin. One
   **~16 µH link** on the existing relay covers the rest (0.46–16 µH roller alone; ~16–32 µH with
   the link), so the relay count is unchanged. Width margin is only ~0.3″ and 14 turns would
   exceed it — confirm in the mock-up. Fallback: an ~11 µH roller (4.2″, 12 turns, 0.6″ width
   margin) with **two** switched links (about 10.5 and 21 µH), costing one more vacuum relay.
   *Back-of-envelope: re-run the network solver (as §10.15 item 4) before adopting either.*

**Settle in the cardboard mock-up (§9 item 5) together with DECISION C-1.**

#### From §5.3a — height basis, 12″ box

*Height basis:* the 9.42″ above the deck takes §3's 12.00″ as the **interior** height, which is
true if the 12.00″ walls sit between floor and lid (outside ≈ 12.15″). If the floor or lid is
inset within the walls, the interior falls by up to ~0.15″: the 6.2″ / 22 µH row then fails, and
the others keep their margin.

#### From §5.3a — 4.7″ / 18-turn build target (Rev 3.7–3.7a)

> **Rev 3.7 — resolved by the vertical stack (§3.0).** The roller now stands upright on a vertical
> shaft, so its overall length sets box height, not deck width. **Build target for R-1 C: 22 µH at
> 4.7″ to wire center, #4 at 3 TPI, 18 turns, 6.0″ winding, ~9.9″ overall** (row 2 of the table
> above). It keeps the 12.5 µH link (§5.4) and the relay count, has ~12% less wire than the 3.7″
> version, and so a little more Q. The footprint is the ~5″ × 6.5″ end plate. The form-parts table,
> rib count and stock list above were derived for the 3.5″ form and must be **re-scaled for
> 4.7″** before ordering: the polygon effect needs more ribs at the larger diameter (about 10).
> Running vertical, the **fixed R8 bearing (A) goes at the bottom**, taking rotor weight as well as
> thrust. Options 1–3 above are no longer needed.
>
> *Rev 3.7a — also re-scale for 4.7″ / 18 turns:* the electrical-target table (one turn ≈ 0.24 µH,
> turn-to-turn ≈ 240 V RMS = 4.3 kV / 18), the end-bracket table (written for a horizontal shaft:
> "axis above deck", bus rod "level with the axis"; upright, the brackets become bottom and top
> plates) and the stock list. **Rib notches are not identical:** on a helix each successive rib's
> notch pattern shifts by pitch ÷ rib count (0.0333″ with 10 ribs). A parametric model with
> dimensioned rib and assembly drawings is in `cad/roller.py` (draft, Rev 3.7a).

#### From §5.3a — clearance estimate for the 4.7″ / 18-turn coil (Rev 3.7a)

> *Rev 3.7a — clearance to the enclosure, vertical stack.* 12.19″ from deck top to lid underside
> (§3.0). Metal across a coil end carries an opposing image current, lowering L and Q. Image-coil
> estimate for this 18-turn, 4.7″ coil (21.3 µH free air), one plane:
>
> | Gap, plate to nearest turn | 0.5″ | 1″ | 2″ | 3″ | 4.7″ (1 D) |
> |:--|--:|--:|--:|--:|--:|
> | ΔL, full coil | −11% | −7% | −3% | −1.7% | −0.7% |
> | ΔL, 2 turns in (10 m) | −30% | −15% | −5% | −2.2% | −0.7% |
>
> | Coil surface to… | Distance | HV (§3.2) | Magnetic (1 D ends, ½ D sides) |
> |:--|--:|:--|:--|
> | Deck below (cold-end potential) | 1.94″ | n/a | short: ≈ −3 to −5%, every setting (active turns start at the bottom) |
> | Lid above (grounded) | 4.05″ | ✓ | ≈ −1%, only with most turns in |
> | Side walls | ~2.4–2.8″ (deck layout not yet drawn) | ✓ | ≈ ½ D ✓ |
> | Bus rod ends (hot) | 1.56″ air / 2.74″ creepage to deck, 3.04″ to lid | ✓ (on Ultem pillars) | — |
>
> Net: max L ≈ 20.4 µH installed. With the 12.5 µH link that is ≈ 32.9 µH against 31.70 µH
> demanded, which still covers; the two spare notches add ~2.4 µH. The shift is measured out in
> the installed calibration. The bus rod spans only the wheel travel, on Ultem pillars; a
> through-rod would have put its hot ends 0.375″ from the deck and 1.125″ from the lid.

#### From §5.3a — stock list for the 3.5″ form

**Stock to buy (3.5″ / 22 µH design):** 12″ × 12″ × 3/8″ Ultem (8 ribs + hub), **12″ × 12″ × ½″
Ultem** (2 end brackets ~5″ × 6½″ side by side, plus 2 end discs ~4¼″ from the remaining 12″ × 5½″
strip), ~4 ft of 3/8″ Ultem rod (4 tie rods at ~11½″), ~30 ft #4 solid bare copper, wheel/bar
hardware, plating supplies, high-temperature cement, ~14″ of ½″ C360 brass rod (shaft and collars),
BeCu finger stock, 2 × R8 sealed bearings (or Rulon J flanged sleeves), PTFE thrust washers.
**Hold the order until the parts are re-scaled for 4.7″** (Rev 3.7 note above); this list is for the 3.5″ form.

### 11.6 Series link inductor and the RF-tank vacuum relays

*Deleted in Rev 3.7b: the single 34 µH roller (§5.3a) needs no series link, and with the pad and link gone there are no vacuum relays in the RF tank (§5.5 now covers K1/K2 only).*

#### Former §5.4 — Series link inductor — one coil, one relay

Extends the roller's top end to cover 40 m CW and the bottom of 160 m.

| Parameter | Value |
|:--|--:|
| Value | **10 µH** air-wound |
| Minimum that works | 8 µH (7 µH fails on 40 m @ 7.000) |
| Tolerance | 8–12 µH all give full coverage |
| Current | 18.4 A RMS — size conductor accordingly |
| Switching | one vacuum relay, shorted out when not in use |

Specified at 10 µH rather than 8 for margin against winding tolerance. **Short the link when
bypassed** — a dangling coil resonates.

*Rev 3.6:* if the roller is replaced by a ~22 µH part (DECISION R-1 options B or C), the link rises
to **12.5 µH** so roller + link still reaches 31.70 µH. Winding method: W3JIP, QST August 1997.

#### From §5.5 — vacuum-relay note

> Vacuum relays (Kilovac HC-1, Jennings RJ-series) are **single RF contacts in a vacuum envelope —
> no auxiliary dry contacts**, and operate in 6–20 ms, not <2 ms. The interlock is a separate
> signal relay or solid-state opto device on the same control line.

#### From §9.1 — parts summary rows

| Item | Source | Status |
|:--|:--|:--|
| 1 × 12.5 µH air-wound link inductor, 18.4 A (10 µH if R-1 A) | to wind | series link |
| 2 × HV vacuum relay (Kilovac HC-1 / Jennings RJ) | to buy | pad + link |

#### From §10.1 — BOM rows and note

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 1 | Link inductor | **12.5 µH air-wound** with a 22 µH roller (R-1 B or C); 10 µH only if R-1 A keeps the 229-class roller. 18.4 A RMS — fabricate, see 10.14 | Fabricate | §5.4 |
| 2 | HV vacuum relay | SPST, 24–26 V coil, HF-rated — **Kilovac HC-1** or **Jennings RJ-1A** | Class | §5.5 |

> The two relays are **single RF contacts in a vacuum envelope with no auxiliary dry contacts**
> (§5.5). Anything needing a confirmation contact uses a separate signal relay or opto device.

#### From §9 — item 42 as open in Rev 3.7a

| # | Item | Status |
|:--|:--|:--|
| 42 | **Link coil has no RF-bay position.** Since the Rev 3.7 vertical stack, the deck plan holds only C1, C2 and the roller (§3.0) and is full at 1.5″ hot-to-hot. Still to place: the **§5.4 series link** (12.5 µH air-wound, 18.4 A — Wheeler estimate ≈ 3″ dia × 4″, ~17 turns #8 / 3/16″ tubing) and **its shorting vacuum relay** — required, since the installed roller is ≈ 20.4 µH against 31.70 µH demanded (§5.3a). The §5.2 **pad doorknob + relay** only if the pad is kept (optional since Rev 3.6, undecided). The imbalance CT rides the output conductors at the top feedthroughs and the tank thermal is a small probe — neither needs deck area. Options: a second tier on insulated posts above C2, the coil on a side wall at ≥ 2.25″ clearance, or a larger bay. Found while populating the cabinet (TUNER-E-212) | **OPEN — layout (blocks the mock-up)** |

### 11.7 Bulkhead filtering and gasketing history

*Superseded by the graded bulkhead filtering of §7.3 / §7.3a (Rev 3.7a, revised Rev 3.7b) and the G-1 conductive-elastomer gasket (§8E.6).*

#### From §7.3 — opening note (Rev 3.7a), with the single 0.01 µF rule

*Rev 3.7a (parts selected — §9 items 16, 23, 38, 40):* every line crossing a chamber boundary still
passes a **feedthrough capacitor at the wall**, but the capacitance is now set by **what the line
carries**, not one value for everything. The single 0.01 µF rule of earlier revisions could not be
met by any stocked filtered D-sub (the highest signal-rated values are 4000 pF pi / 5600 pF C), and
it was wrong for the motor lines anyway: 0.01 µF with 1 kΩ is a 15.9 kHz corner, which erases a
2.5 µs STEP pulse and a ~1 MHz encoder SPI clock.

#### From §10.13 — feedthrough tally (36 lines)

**Feedthrough capacitors (§7.3)** — from the actual connector nets in `control.net`:

| Crossing | Lines |
|:--|--:|
| Sampler → Control (J7 ↔ J11, 16-way IDC) | 8 |
| Control → Motor: STEP1-3, DIR1-3, DRV_EN | 7 |
| Control → Motor: encoder SPI + 3V3 | 6 |
| Control → Motor: LIM1–LIM6 | 6 |
| Control → RF tank: relay coils (J8) | 4 |
| RF tank → Control: thermal + imbalance CT (J12) | 3 |
| Control → blower (J9) | 2 |
| **Total** | **36 — order 50** |

*Rev 3.7a:* the tally stands, but the parts changed — 26 of the 36 lines now cross on filtered D-sub
contacts (§7.3a); discrete feedthroughs remain only in the shelf (7) and on the prescaler (2).

The relay-coil and thermal/CT rows are **crossings 6 and 7 of §9 item 16**, absent from the §7.3 table. Counting
them here does not close that item; the table still needs correcting.

#### From §8E.6 — BeCu finger stock and the two gasket options

> **BeCu finger stock (Section 4) seals RF, not dust or moisture.** It is a spring contact, not a
> gasket. Specifying it does not get you IP5X.

*Rev 3.7a — decided (G-1): **conductive elastomer**. The bolted angle frame gives every panel a flat
1″ machined flange to seal against, which removes the flatness objection.*

Two options:

1. **Conductive elastomer gasket** — does both jobs in one part. More expensive, and needs decent
   flange flatness to compress evenly.
2. **Two gaskets in parallel channels** — finger stock for RF, separate closed-cell elastomer for
   environment. More machining, more forgiving of flatness.

The binding constraint either way is **flange flatness**. On scratch-built 14 ga aluminum a plain
sheared edge will not seal. **Form a flange on the panel edges, or add a stiffener strip**, and
check with a straightedge before committing to a gasket type — that decision is expensive to revisit
after fabrication.

#### From §10.14 — DECISION G-1 note

**G-1 · Gasket strategy — RESOLVED Rev 3.7a: conductive elastomer** on the frame flanges (TUNER-E-202 to E-208). Original note:  — §8E.6: conductive elastomer (one part, both jobs, needs flange
flatness) **or** two gaskets in parallel channels (more machining, forgiving of flatness). §9 item
19 makes this dependent on forming flanges first. **Expensive to revisit after fabrication.**

### 11.8 Frequency counter: direct gate counting

*Superseded by the ÷1024 prescaler and 200 ms gate of §8B.0.1 (Rev 3.7a); see §6A.10.*

#### From §6A.10

**Method: direct gate counting, 5 ms gate.** Resolution is `1/gate` and independent of input
frequency — a flat **200 Hz** across the whole range, against the 200 kHz width of 160 m. That is
three orders of magnitude finer than band-edge selection requires, and avoids the complexity of
reciprocal counting.

| Input | Counts in 5 ms gate |
|--:|--:|
| 1.8 MHz | 9,000 |
| 7.0 MHz | 35,000 |
| 29.7 MHz | 148,500 |

Needs a counter wider than 17 bits — any 32-bit MCU timer is ample. Most modern MCU timers count
30 MHz directly on an external input; add a ÷2 or ÷4 prescaler only if the chosen part cannot.

### 11.9 Bench panel (a): hardware TUNE / ACK / LEDs

*Superseded by the passive bench box of §8C.4(b) (Rev 3.7a): E-STOP and permissive LED only; TUNE, ACK and status moved to the web UI.*

#### From §8C.4

**(a) Physical bench panel — no software in the path**

| Control | Function |
|:--|:--|
| **E-STOP** | Breaks amp keying locally (8C.2). Large, red, latching |
| **TUNE** | Requests a tuning cycle |
| **ACK** | Clears a class B fault |
| LED: MATCHED | Solid — tuner reports a good match |
| LED: TUNING | Flashing — cycle in progress, PTT inhibited |
| LED: FAULT | Solid class B, flashing class C (go to the box) |
| LED: LINK | Off means the panel is blind — see 8C.6 |

E-STOP is hardwired. TUNE, ACK and the LEDs ride the link, so they fail soft.

*Rev 3.7a:* superseded by (b) — TUNE, ACK and the MATCHED / TUNING / FAULT / LINK indications
move to the web UI. The bench box keeps the E-STOP and a permissive-state LED.

### 11.10 Resolved discrepancies (Rev 3.5–3.7a)

*Items 1–4 of the §10.15 discrepancy log, all resolved or superseded by Rev 3.7a; item 5 remains in §10.15.*

#### From §10.15 — items 1–4

1. **§4 transverse sub-wall dimension.** The cut list gives **5.37″ × 12.00″** (10.00″ before Rev 3.6), but §6's choke fit
   check establishes the bays as **5.37″ W × 5.00″ D** — which makes the sub-wall 5.00″ long, not
   5.37″. Neither reading fills the 16″ width exactly (3 × 5.37 + 2 × 0.081 = 16.27″; 3 × 5.00 +
   2 × 0.081 = 15.16″). **The chamber layout needs dimensioning properly before cutting metal.**
   Carried to §9 as item 22.
2. **§7.3 internal contradiction.** The opening sentence requires a feedthrough capacitor on
   *every* line crossing a boundary; the table beneath routes Control→Motor through **cable glands
   with shielded twisted pair** instead. 10.13 counts them as feedthroughs (19 of the 36) on the
   conservative reading. Carried to §9 as item 23. **RESOLVED Rev 3.7a** — graded feedthroughs, no glands (§7.3, §7.3a).
3. **Stepper shaft configuration.** §7.1 required a rear shaft for the encoder but never said
   **dual-shaft** in so many words. **RESOLVED Rev 3.7a — the other way:** a dual-shaft motor
   plus rear encoder does not fit the utility layer (§10.6 depth table). The motor is single
   shaft and the encoder comes off the G10 shaft by belt (M-1 B); §7.1 and the §3.0 diagram
   updated.
4. **§5.1 capacitance figures disagree with each other, and with a re-run** *(Rev 3.5)*. §5.1's
   summary block says the largest capacitance demanded is **666 pF**; its table says C2 needs
   **25–830 pF**. The script that produced the §5.1 voltages and coverage is **not archived** in
   `nec/` (only `tnet.py` / `optc.py` are). A lossless re-run of `tnet.py`'s solver at 40 ft
   with measured ranges finds **27/27 bare** (C2 ≤ 671 pF, C1 ≤ 6.6 kV), not 26/27 — so the
   pad's necessity, and whether the KP1-4 removes it, are unsettled. Re-run the original analysis,
   archive the script, and correct §5.1 before deciding C-1.
   **RESOLVED Rev 3.6:** re-derived and archived as `nec/cap_demand.py` (§5.1). Both old
   figures are where a lowest-loss solver parks C2 (at the top of whatever range it is given), not
   requirements; the smallest C2 that matches is ≤ 270 pF. Bare coverage is 27/27; the pad is a
   ~20–28 W loss saving on 160 m only.

### 11.11 Input choke: air-core design C in the sampler chamber (Rev 3.7b)

*Superseded Rev 3.7c by the #61 ferrite choke in the RF bay (§6). Two findings ended it:
- **Coax loss.** Its ~36 ft of RG-142B lost 40–232 W of the input power inside the sealed sampler
  chamber.
- **Bypassed by the routing.** Its deck-side coax crossed two grounded bulkheads (adapter X and the
  shelf), which bypassed it (Changes in Rev 3.7c, item 1).

The NEC model (`nec/choke_vna.py`) and its outputs stay in `nec/` for reference. Text as it stood in
Rev 3.7b:*

**Former 3.3″** (3.69″ OD assembled), lying flat in the Sampler chamber with **0.49″ to the grounded baseplate and to the shelf** (§3.0; Rev 3.7b — the 4.0″ former sat 0.05″ off the baseplate with its deck end at kV RF).

**No ferrite in the high-stress path.** With a floating deck, the input choke must withstand the full
deck-to-chassis common-mode potential — kilovolts. Fair-Rite #31 is deliberately lossy (μ″ ≫ 0); at
kV common-mode its resistive core dissipation would exceed 250 W and drive the ferrite past its
130 °C Curie point within seconds.

**Adopted: air-core Guanella transmission-line choke.**

| Parameter | Value |
|:--|--:|
| Former | **3.3″ dia G10 fiberglass** (3.69″ OD assembled) — Rev 3.7b, design C |
| Winding | **39 turns** RG-142B/U, close-wound single layer |
| Coax length | ≈ **35.7 ft** (+ leads; order 40 ft) |
| Winding length | **7.61″** (≈ 8.1″ with end caps) |
| Inductance | **45.4 µH** at 1 MHz, installed (NEC, below) |
| Mounting | Axis **horizontal** — lies flat in the Sampler chamber (§3.0) |

```
Fit check (vertical stack): axis across the width, lying flat
            Sampler chamber is ~15.87" W x 5.00" D x 5.00" H
            -> 4.25" OD: 0.375" clearance in D and in H; 5.85" winding + end caps in 15.87" W
            FITS — tight in H; confirm with the end-cap mounts in the mock-up (§9 item 5)
```

**Choking reactance:** 547 Ω @ 1.85 MHz · 1,079 Ω @ 3.65 MHz · 4,199 Ω @ 14.2 MHz · 8,427 Ω @ 28.5 MHz

Zero magnetic core means zero core dissipation, zero flux saturation, and no Curie-point runaway.

**Self-resonance — modeled Rev 3.7b** (`nec/choke_vna.py`: nec2++ wire model of the shield's
outer surface as the common-mode helix, end A bonded to the baseplate, port at the deck end, grounded
baseplate below and shelf above at the real gaps). The old "quarter-wave near 5.5 MHz" estimate does
not hold: the first resonance is a **parallel** one (impedance peaks — harmless) and the dangerous one
is the **series** resonance, which tracks coax length (~0.57 MHz per turn) and moves strongly with the
gap to grounded metal.

| Design | Former / turns | Gaps below / above | Parallel | **Series** | Verdict |
|:--|:--|:--|--:|--:|:--|
| Rev 3.7a | 4.0″ / 30 t | 0.05″ / 0.37″ | 8.97 MHz | 22.62 | 0.05″ clearance at kV — rejected |
| A | 3.3″ / 36 t | 0.49″ / 0.49″ | 7.75 | 24.85 | **on 12 m** (53 Ω) |
| B | 3.3″ / 42 t, 0.25″ pitch | 0.49″ / 0.49″ | 7.65 | 21.85 | **on 15 m** (160 Ω) |
| **C — adopted** | **3.3″ / 39 t close-wound** | 0.49″ / 0.49″ | 7.35 | **23.15** | 7.9 % above 15 m, 7.0 % below 12 m |
| D | 3.3″ / 38 t, 0.21″ pitch | 0.49″ / 0.49″ | 7.65 | 23.85 | 4 % from 12 m |

Design C, choke impedance (minimum in band) against the deck's ~23 pF to chassis (§2.2) — the vane
can only balance the deck capacitance, so the choke must be the *higher* impedance:
160 m 536 Ω (deck 3.85 kΩ — **choke-limited**), 80 m 1.26 kΩ (1.98 kΩ), 60 m 3.2 kΩ, 40 m 19.6 kΩ,
30 m 3.1 kΩ, 20 m 1.34 kΩ, 17 m 851 Ω, 15 m 507 Ω (deck 330 Ω), 12 m 1.39 kΩ, 10 m 566 Ω (deck 247 Ω).
From 60 m up the choke always exceeds the deck reactance; **160 / 80 m remain choke-limited**, which is
what the #61 supplement below is for.

**Sweep it installed, not on the bench:** raising the 4.0″ choke from 0.05″ to 0.50″ moved its
parallel resonance from 9.0 to 7.2 MHz. Measure the series resonance in the chamber; if it lands within
~0.5 MHz of 21.45 or 24.89 MHz, take off or add one turn (~0.57 MHz per turn).

**Low-band supplement.** Two Fair-Rite **#61** toroids in series on the cold side add >1,500 Ω of
reactive choking on 160/80 m. #61 is low-loss NiZn (tan δ < 0.005 below 10 MHz), so it adds
impedance without the thermal failure mode of #31 — roughly 1/50th the dissipation. Being reactive
rather than resistive, it can itself resonate with stray capacitance; include it in the VNA sweep.

### 11.12 Enclosure at 22.00″ with 3.50″ standoffs (Rev 3.7b)

*Superseded Rev 3.7c: the standoffs grew 2.00″ (to 5.50″) and the box with them (to 24.00″) so the
input choke can stand under the deck (§3.0, §6). Text as it stood in Rev 3.7b:*

**Height closure (bottom to top):**

```
Floor 0.081 + utility 5.000 + shelf 0.081 + standoffs 3.500 + deck 0.081
  + roller over plates 11.547 + plate B to top 1.630 + top 0.081         = 22.00"
Specified 22.00" (Rev 3.7b; was 21.00" / 12U)
```

**Why 3.50″ standoffs.** The hot capacitor shaft tip now hangs ~0.75″ below the deck. At 2.50″
that left 1.75″ of air and creepage to the grounded shelf, under the ≥ 2″ creepage used in
§5.3a. At 3.50″ it is 2.75″. The roller shaft is at deck potential (§5.3a), so it needs only the
deck's own clearance.

### 11.13 Control board as generated through Rev 3.7b (Rev 3.4 generator)

*Superseded Rev 3.7c: `kicad/board_control.py` had not followed the log since Rev 3.4. It was
rebuilt to the current text (§10.5). What the old board got wrong:*

- **Panel bus.** The panel was an I2C expander on 3V3 only. The selected Nextion is a 5 V UART
  display, so it now runs on Serial8 (§7.5, §8B.0.4).
- **Blower.** The blower was switched +24 V on two pins with no tach. §8 calls for 12 V from an
  on-board TSR 2-24120 and a tach input. The PWM line was also on pin 32, which has no PWM.
- **Encoder MOSI.** It ended at the Teensy, so the AS5048As could receive no command (diagnostics,
  error clear).
- **No hardware permissive.**
  - The MCU drove the fiber tone directly, so software was in the interlock path. §7.4 forbids that.
  - The bypass could not have worked with a dead controller (§8B.4d).
  - None of §6B's inputs existed: the cal-load window, the cal-load thermal switch, coil-current
    sense, and the §5.5 blanking timer.
- **Missing parts.**
  - No DC-DCs, no fiber transmitter, no §7.3 series resistors.
  - Separate pin headers instead of one ribbon per bulkhead D-sub.
  - The two "RF tank" relay drivers outlived the RF-tank relays (deleted Rev 3.7b).
- **Size.** The outline was 240 × 190 mm. The cassette's envelope is 5.5 × 3.6″ (140 × 91 mm).

Bill of materials as it stood (40 components, all through-hole except U1):

| Qty | Value | Package | Refs |
|--:|:--|:--|:--|
| 10 | 10 kΩ, 1 % | Axial DIN0207 | R1–R6, R9, R10, R12, R13 |
| 3 | 100 Ω | Axial DIN0207 | R7, R8, R11 |
| 3 | 0.1 µF, 50 V ceramic | Disc, 5.00 mm pitch | C1, C3, C5 |
| 1 | 100 µF electrolytic | Radial D5.0 P2.50 | C2 |
| 1 | 220 µF electrolytic | Radial D5.0 P2.50 | C4 |
| 3 | **IRLZ44N** logic-level N-MOSFET | TO-220-3 | Q1–Q3 |
| 3 | **1N4007** flyback diode | DO-41 | D1–D3 |
| 1 | **AMS1117-3.3** regulator | SOT-223 | U1 |
| 1 | **Teensy 4.1** | PJRC, 48-pin, 60.96 × 17.78 mm | A1 |
| 1 | Terminal block, 2-pos | Phoenix MKDS-1,5-2-5.08 | J1 (24 V in) |
| 6 | Pin header 1×04 | 2.54 mm vertical | J2–J5, J8, J10 |
| 3 | Pin header 1×08 | 2.54 mm vertical | J6, J7, J13 |
| 1 | Pin header 1×06 | 2.54 mm vertical | J12 |
| 2 | Pin header 1×02 | 2.54 mm vertical | J9, J15 |
| 1 | IDC header 2×08, latching | 2.54 mm, shrouded | J11 |

### 11.14 Measurement board as generated through Rev 3.7b (Rev 3.4 generator)

*Superseded Rev 3.7c: `kicad/board_measurement.py` had not followed the log since Rev 3.4. It was
rebuilt to the current text (§10.4). What the old board got wrong:*

- **Item 35 not done.** There was no cal-load detector (§6B.3a). The ÷1024 count left on the ribbon
  through an RC filter instead of on coax (W10).
- **AD8302 not in measurement mode.**
  - MSET and PSET were tied to VREF instead of VMAG and VPHS, so the outputs would not have carried
    30 mV/dB and 10 mV/°.
  - The inputs ran straight to the SMA jacks, with no coupling capacitors or 52.3 Ω terminations.
  - The 1 nF offset capacitors put the offset loop's high-pass at 2 MHz, inside 160 m.
- **Vector-path level.** It was built for the ~60 dB pad of §6A.5 (corrected there). The pads were
  external SMA attenuators that were never in a BOM.
- **Coupled ports mis-terminated.** A 6 dB resistive splitter fed the detector arm with no load, so
  each port saw ~83 Ω, not 50 Ω (§6A.2's most common build error). Its 16.5 Ω input resistor ran at
  0.31 W in a 0.25 W part at 1500 W.
- **Detector diodes.**
  - The HSMS-2850 breaks down at 3.8 V, against ~19 V reverse at 1500 W.
  - It sat on a SOD-323 footprint, a package the part does not come in.
  - The outputs were unscaled: ~4.7 V at 1500 W, for a 3.3 V ADC.
- **Counter.**
  - The comparator's input idled at 0 V with its threshold at 1.65 V, so it counted only above
    ~50 W.
  - Its SHDN pin was tied high, which disables a TLV3501.
  - The 74AC4040 is now obsolete.
- **Trip threshold.** It was fixed by a 10 k / 10 k divider instead of a trimmer or DAC (§6A.4).
- **Size.** The board was 215 × 145 mm, 2 layers, through-hole; the sampler envelope is 4.0 × 3.0″.

Bill of materials as it stood (54 components; all passives through-hole except the four SOD-323
diodes, the AD8302 (TSSOP-14), the TLV3501 (SOIC-8) and the AMS1117 (SOT-223)):

| Qty | Value | Package | Refs |
|--:|:--|:--|:--|
| 6 | 16.5 Ω, 1 %, metal film 0.25 W | Axial DIN0207 | R1–R6 |
| 6 | 1 kΩ, 1 %, metal film | Axial DIN0207 | R16–R21 |
| 6 | 10 kΩ, 1 %, metal film | Axial DIN0207 | R7, R8, R11–R14 |
| 1 | 470 Ω | Axial DIN0207 | R9 |
| 1 | 4.7 kΩ | Axial DIN0207 | R15 |
| 1 | 1 MΩ | Axial DIN0207 | R10 |
| 5 | 0.01 µF, 50 V ceramic | Disc, 5.00 mm pitch | C12–C16 |
| 5 | 0.1 µF, 50 V ceramic | Disc, 5.00 mm pitch | C1, C2, C7, C10, C11 |
| 5 | 1 nF, 50 V ceramic | Disc, 5.00 mm pitch | C3–C6, C17 |
| 1 | 1 µF ceramic | Disc, 5.00 mm pitch | C8 |
| 1 | 10 µF electrolytic | Radial D5.0 P2.50 | C9 |
| 1 | **AD8302** gain/phase detector | TSSOP-14 | U1 |
| 1 | **TLV3501** comparator | SOIC-8 | U2 |
| 1 | **LM393** dual comparator | DIP-8 | U3 |
| 1 | **74AC4040** ÷1024 prescaler | DIP-16 | U4 |
| 1 | **AMS1117-3.3** regulator | SOT-223 | U5 |
| 2 | **HSMS-2850** Schottky detector diode | SOD-323 | D1, D2 |
| 2 | **BAT54** Schottky | SOD-323 | D3, D4 |
| 6 | SMA vertical jack | Amphenol 132134-11 | J1–J6 |
| 1 | IDC header 2×08, latching | 2.54 mm, shrouded | J7 |

---

## Appendix A — Homebuilt Roller Drawings (TUNER-L-100 to L-109)

Draft fabrication drawings for DECISION R-1 = C (§5.3a). Sheets L-100 to L-109 show the **34 µH /
5.2″ / 22-turn roller** (regenerated 2026-11-16), generated from the parametric model
(`cad/roller.py`, build123d) by FreeCAD TechDraw (`cad/drawings.py`). `build.sh`
pulls the latest sheets in on every build. All dimensions in inches; every sheet is marked
DRAFT — NOT FOR FABRICATION until the open items in §5.3a and §9 (27, 32, 44) are closed and the
wiper geometry, which §5.3a specifies by function only, has been reviewed.

<div class="drawing-sheet"><img src="sheets/L-100-assembly.svg" alt="TUNER-L-100 — Roller assembly: elevation, Section B-B through the wiper, Detail D"/><p>TUNER-L-100 — Roller assembly: elevation, Section B-B through the wiper, Detail D</p></div>

<div class="drawing-sheet"><img src="sheets/L-101-rib.svg" alt="TUNER-L-101 — Rib (Ultem 1000), notch detail and helix stagger"/><p>TUNER-L-101 — Rib (Ultem 1000), notch detail and helix stagger</p></div>

<div class="drawing-sheet"><img src="sheets/L-102-end-plate.svg" alt="TUNER-L-102 — End plates A and B (mounting flange), hole table A–L"/><p>TUNER-L-102 — End plates A and B (mounting flange), hole table A–L</p></div>

<div class="drawing-sheet"><img src="sheets/L-103-end-disc-hub.svg" alt="TUNER-L-103 — Cage end disc with Section E-E, and center hub"/><p>TUNER-L-103 — Cage end disc with Section E-E, and center hub</p></div>

<div class="drawing-sheet"><img src="sheets/L-104-rods.svg" alt="TUNER-L-104 — Shaft, bus rod, guide rod, tie rods, frame posts, bus-rod pillars"/><p>TUNER-L-104 — Shaft, bus rod, guide rod, tie rods, frame posts, bus-rod pillars</p></div>

<div class="drawing-sheet"><img src="sheets/L-105-wiper.svg" alt="TUNER-L-105 — Wiper: wheel, fork, carriage"/><p>TUNER-L-105 — Wiper: wheel, fork, carriage</p></div>

<div class="drawing-sheet"><img src="sheets/L-106-exploded.svg" alt="TUNER-L-106 — Exploded isometric and parts list"/><p>TUNER-L-106 — Exploded isometric and parts list</p></div>

<div class="drawing-sheet"><img src="sheets/L-107-retention.svg" alt="TUNER-L-107 — End retention: Section A-A, end details, retention schedule, cement"/><p>TUNER-L-107 — End retention: Section A-A, end details, retention schedule, cement</p></div>

<div class="drawing-sheet"><img src="sheets/L-108-coupler.svg" alt="TUNER-L-108 — Coupler B, Delrin Oldham (reference)"/><p>TUNER-L-108 — Coupler B, Delrin Oldham (reference)</p></div>

<div class="drawing-sheet"><img src="sheets/L-109-install.svg" alt="TUNER-L-109 — Roller installation in the RF bay: stack section, plan, holes, clearances"/><p>TUNER-L-109 — Roller installation in the RF bay: stack section, plan, holes, clearances</p></div>


## Appendix B — Enclosure Drawings (TUNER-E-200 to E-216)

Draft fabrication drawings for the wall-mounted, modular vertical-stack enclosure (§3.0 Rev 3.7a),
generated from `cad/enclosure.py` by `cad/drawings_enclosure.py`. Every panel's
cutouts and fastener pattern come from one specification in the model, which is interference-checked
against the roller, caps, deck and drive trains. DRAFT — NOT FOR FABRICATION until §9 items 5
(mock-up), 38–41 are closed.

<div class="drawing-sheet"><img src="sheets/E-200-overview.svg" alt="TUNER-E-200 — Enclosure overview: front, left side, top, cutaway"/><p>TUNER-E-200 — Enclosure overview: front, left side, top, cutaway</p></div>

<div class="drawing-sheet"><img src="sheets/E-201-frame.svg" alt="TUNER-E-201 — Frame: 6061-T6 angle cut list"/><p>TUNER-E-201 — Frame: 6061-T6 angle cut list</p></div>

<div class="drawing-sheet"><img src="sheets/E-202-front.svg" alt="TUNER-E-202 — Front panels: RF service panel and cassette face (UI)"/><p>TUNER-E-202 — Front panels: RF service panel and cassette face (UI)</p></div>

<div class="drawing-sheet"><img src="sheets/E-203-left.svg" alt="TUNER-E-203 — Left side panels (exhaust)"/><p>TUNER-E-203 — Left side panels (exhaust)</p></div>

<div class="drawing-sheet"><img src="sheets/E-204-right.svg" alt="TUNER-E-204 — Right side panels (intake)"/><p>TUNER-E-204 — Right side panels (intake)</p></div>

<div class="drawing-sheet"><img src="sheets/E-205-top-rear.svg" alt="TUNER-E-205 — Top panel (output feedthroughs) and rear panel"/><p>TUNER-E-205 — Top panel (output feedthroughs) and rear panel</p></div>

<div class="drawing-sheet"><img src="sheets/E-206-floor.svg" alt="TUNER-E-206 — Floor: low-voltage I/O"/><p>TUNER-E-206 — Floor: low-voltage I/O</p></div>

<div class="drawing-sheet"><img src="sheets/E-207-shelf.svg" alt="TUNER-E-207 — Grounded shelf"/><p>TUNER-E-207 — Grounded shelf</p></div>

<div class="drawing-sheet"><img src="sheets/E-208-bulkhead.svg" alt="TUNER-E-208 — Bulkhead (filtered connectors) and partition"/><p>TUNER-E-208 — Bulkhead (filtered connectors) and partition</p></div>

<div class="drawing-sheet"><img src="sheets/E-209-small-parts.svg" alt="TUNER-E-209 — Cassette tray and rails, axis bracket, sampler baseplate, wall flange"/><p>TUNER-E-209 — Cassette tray and rails, axis bracket, sampler baseplate, wall flange</p></div>

<div class="drawing-sheet"><img src="sheets/E-210-exploded.svg" alt="TUNER-E-210 — Exploded view and parts list"/><p>TUNER-E-210 — Exploded view and parts list</p></div>

<div class="drawing-sheet"><img src="sheets/E-211-nesting.svg" alt="TUNER-E-211 — Sheet-metal nesting and stock"/><p>TUNER-E-211 — Sheet-metal nesting and stock</p></div>

<div class="drawing-sheet"><img src="sheets/E-212-populated.svg" alt="TUNER-E-212 — Populated cabinet: front and left views, item list"/><p>TUNER-E-212 — Populated cabinet: front and left views, item list</p></div>

<div class="drawing-sheet"><img src="sheets/E-213-utility-plan.svg" alt="TUNER-E-213 — Utility layer plan, populated and with harness runs"/><p>TUNER-E-213 — Utility layer plan, populated and with harness runs</p></div>

<div class="drawing-sheet"><img src="sheets/E-214-harness.svg" alt="TUNER-E-214 — Harness routing, color-coded (floor to shelf)"/><p>TUNER-E-214 — Harness routing, color-coded (floor to shelf)</p></div>

<div class="drawing-sheet"><img src="sheets/E-215-wire-list.svg" alt="TUNER-E-215 — Wire list with cut lengths"/><p>TUNER-E-215 — Wire list with cut lengths</p></div>

<div class="drawing-sheet"><img src="sheets/E-216-choke.svg" alt="TUNER-E-216 — Input choke assembly: half section, section at mid-winding, exploded view and parts list"/><p>TUNER-E-216 — Input choke assembly: half section, section at mid-winding, exploded view and parts list</p></div>

## Appendix C — Control and Measurement Boards (KiCad)

Rendered by `doc/build.sh` from the routed boards in `kicad/` on every build. The 3D views are the bare
board as the fab delivers it: solder mask, silkscreen reference designators, pads and vias. No
component models are installed, so parts appear only as their silkscreen and pads. The silkscreen
view is the same layer as vector line art, with the pad openings, as the fab prints it; values are
in the BOM by reference. Placement, routing and
DRC are described in §10.5 (control) and §10.4 (measurement).

<div class="drawing-sheet"><img src="sheets/pcb-control-top.png" alt="Control board — top, 3D render (139 × 91 mm, 4 layers; Teensy A1 flat on sockets with its SD end at the top edge)"/><p>Control board — top, 3D render (139 × 91 mm, 4 layers; Teensy A1 flat on sockets with its SD end at the top edge)</p></div>

<div class="drawing-sheet"><img src="sheets/pcb-control-silk.svg" alt="Control board — top silkscreen and pad openings, as the fab prints them (values are in the §10.5 BOM by reference)"/><p>Control board — top silkscreen and pad openings, as the fab prints them (values are in the §10.5 BOM by reference)</p></div>

<div class="drawing-sheet"><img src="sheets/pcb-control-bottom.png" alt="Control board — bottom, 3D render"/><p>Control board — bottom, 3D render</p></div>

<div class="drawing-sheet"><img src="sheets/pcb-control-F.svg" alt="F.Cu" style="width:49%;max-height:84mm;object-fit:contain;margin:0 0.5%"/><img src="sheets/pcb-control-In1.svg" alt="In1.Cu" style="width:49%;max-height:84mm;object-fit:contain;margin:0 0.5%"/><img src="sheets/pcb-control-In2.svg" alt="In2.Cu" style="width:49%;max-height:84mm;object-fit:contain;margin:0 0.5%"/><img src="sheets/pcb-control-B.svg" alt="B.Cu" style="width:49%;max-height:84mm;object-fit:contain;margin:0 0.5%"/><p>Control board — copper: F.Cu (top left), In1.Cu GND plane (top right), In2.Cu (bottom left), B.Cu (bottom right), each viewed from the top</p></div>

<div class="drawing-sheet"><img src="sheets/pcb-measurement-top.png" alt="Measurement board — top, 3D render (100 × 74 mm, 4 layers; FWD/REF in on the right edge, ÷1024 out top left, cal-load tap bottom left)"/><p>Measurement board — top, 3D render (100 × 74 mm, 4 layers; FWD/REF in on the right edge, ÷1024 out top left, cal-load tap bottom left)</p></div>

<div class="drawing-sheet"><img src="sheets/pcb-measurement-silk.svg" alt="Measurement board — top silkscreen and pad openings, as the fab prints them (values are in the §10.4 BOM by reference)"/><p>Measurement board — top silkscreen and pad openings, as the fab prints them (values are in the §10.4 BOM by reference)</p></div>

<div class="drawing-sheet"><img src="sheets/pcb-measurement-bottom.png" alt="Measurement board — bottom, 3D render"/><p>Measurement board — bottom, 3D render</p></div>

<div class="drawing-sheet"><img src="sheets/pcb-measurement-F.svg" alt="F.Cu" style="width:49%;max-height:84mm;object-fit:contain;margin:0 0.5%"/><img src="sheets/pcb-measurement-In1.svg" alt="In1.Cu" style="width:49%;max-height:84mm;object-fit:contain;margin:0 0.5%"/><img src="sheets/pcb-measurement-In2.svg" alt="In2.Cu" style="width:49%;max-height:84mm;object-fit:contain;margin:0 0.5%"/><img src="sheets/pcb-measurement-B.svg" alt="B.Cu" style="width:49%;max-height:84mm;object-fit:contain;margin:0 0.5%"/><p>Measurement board — copper: F.Cu (top left), In1.Cu GND plane (top right), In2.Cu (bottom left), B.Cu (bottom right), each viewed from the top</p></div>

---

*Stress basis: real NEC-2 simulation, `nec2++` (708/708 self-tests pass), 1200 segments,
Sommerfeld-Norton ground, 27 band-edge points across 160 m–10 m inclusive of 60 m. Network
reachability verified by closed-form T-network solution at every point against measured component
ranges. Model, solver and raw output archived in `nec/`; capacitance demand regenerates with
`python3 cap_demand.py` (bare Rev 3.7b run: `nec/cap_demand_rev37b.out`); the input-choke screen with
`python3 choke_screen.py` (`nec/out/choke_screen_rev37c.txt`).
Review history and per-item resolutions: `doc/design-review-rev3.2.md`.
Previous revisions preserved at `archive/design-log-rev3.3.md` and `archive/design-log-rev3.4.md`.*
