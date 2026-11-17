# 1500W Automated Antenna Tuner — Design Log
### Revision 3.4 — Entry-Box Architecture · Measured Parts · All-Band Band-Edge Basis

**Revision history**
- **Rev 1** — initial spec. Correct on materials/welding, chamber-crossing discipline, relay sequencing.
- **Rev 3.2** — *replacement, not revision*. Fixed several items; dropped four correct sections from
  Rev 1, which is how the encoder regression got in.
- **Rev 3.3** — cumulative consolidation; fixed three mechanical conflicts; real NEC-2 basis.
- **Rev 3.4 (this document)** — **tuner relocated to the antenna entry box**, stress rebased on
  *all band edges* including 60 m, and the whole capacitor/inductor specification rebuilt around
  the **parts actually in hand** (measured, not catalogue).

**Changes in this revision**
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

**Modelled configuration**
- 170 ft total #12 AWG copper (85 ft per leg), center-fed
- Inverted-V, apex 37.5 ft, ends 10 ft AGL (horizontal run ≈ 80.4 ft per leg)
- Real ground: σ = 0.005 S/m, ε_r = 13 (Sommerfeld-Norton, `GN 2`)
- Copper wire loss included (`LD 5`)
- Feeder: **~40 ft** of 600 Ω open-wire ladder line, VF ≈ 0.95, **outdoor run only**
  (tuner sited at the entry box — see Section 1.6)

**Simulation provenance.** `nec2++` built from source (github.com/tmolteno/necpp, CMake, Release);
708/708 self-test assertions pass. Model run at **1200 segments**. Binary, deck generator and raw
output are archived in `~/tuner-nec/`.

> **Segmentation note.** R converges by ~400 segments on every band. X does **not** at the top end:
> at 28.5 MHz (≈4.9 λ, near a voltage antinode) X was still drifting ≈ −55 Ω per refinement at 1200
> segments. |Z| is stable to <0.5% but phase moves several degrees, which propagates into the line
> transform. **Treat 10 m reactance as ±10%; all other bands are converged.**

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

Twenty-seven band-edge points modelled. 60 m is the standout: 170 ft is 1.85 half-waves there,
close to a voltage antinode, giving Z_ant ≈ 7,100 Ω.

| Band | Edge freqs modelled | Worst Z_ant |
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
-frequency modelling understated them.

### 1.3 Design envelope

Apex and end height are both approximate, so the design figures are the **worst case across
apex 35–40 ft and ends 6–15 ft**, not the nominal:

| Quantity | Spot-frequency basis (superseded) | **Design envelope (band edges, 40 ft)** |
|:--|--:|--:|
| Peak RF voltage at tuner | 3,088 V | **4,191 V** |
| Peak RF current at tuner | 12.51 A | **~14 A** |
| Max voltage across C1 | — | **6,102 V pk** (160 m @ 1.800) |
| Max voltage across C2 | — | **4,170 V pk** (40 m @ 7.150) |
| Max roller current | — | **18.4 A RMS** (160 m) |

Geometry sensitivity remains small (apex 35–40 ft, ends 6–15 ft moved the result only a few
percent). **Both limits occur on 160 m at the band edges.**

#### 1.3.1 Actual operating power — the design basis is conservative

The station amplifier is a **Heathkit SB-220** (pair of 3-500Z), which delivers roughly
**1000–1200 W output**, not 1500 W. Retaining 1500 W as the design basis is deliberate headroom
against a future amplifier, but the real stress is lower. Voltage and current scale as √P:

| Actual power | Peak V at tuner | Peak I | 160 m loss @ 1.800 |
|--:|--:|--:|--:|
| 1500 W *(design basis)* | 4,191 V | 14.0 A | 526 W |
| 1200 W | 3,749 V | 12.5 A | 421 W |
| **1100 W** *(realistic SB-220 max)* | **3,589 V** | **12.0 A** | **386 W** |
| 1000 W | 3,422 V | 11.4 A | 351 W |
| 100 W *(typical use)* | 1,082 V | 3.6 A | 35 W |

At ~1100 W the margins improve meaningfully: the worst-case Jennings utilisation goes from
**1.46× to 1.70×**, and the ≥10 kV output feedthroughs sit at **2.79×**.

**The 160 m derate table in 1.7.1 does not change** — those limits are set by the 200 W dissipation
budget, not by amplifier capability. But at ~1100 W the amp **cannot reach** the limit on the upper
two 160 m segments, so in practice only **1.800–1.850 MHz** is genuinely constrained.

### 1.4 Feeder length — ~40 ft, and make the last foot adjustable

With the tuner at the entry box the feeder is the outdoor run only. Coverage of all 27 band-edge
points, using the **measured** parts (roller 0.20–24.40 µH, Jennings 20–675 pF, 200 pF pad,
10 µH link):

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

- **Peak RF voltage up to ~3.1 kV** at high-impedance nodes. Contact causes deep RF burns which are
  far more extensive than they appear at the surface. Note the mechanism: above ~100 kHz the hazard
  is **thermal, not electrocution** — HF RF does not induce ventricular fibrillation. The practical
  rule is unchanged: never open the cabinet with the amplifier keyed.
- **Circulating current up to ~18.5 A RMS** through the roller inductor on 160 m. Any oxidation or
  weak contact at the roller wheel becomes localised ohmic heating, pitting, or arcing.
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
or network link** (see Section 7.5) and an enclosure rated for an unheated but **sheltered**
garage interior — see Section 8E.

### 1.7 Network loss, efficiency, and bandwidth — derived

The 200 W thermal figure inherited from Rev 3.2 was asserted, never derived. Computed here from
the actual network solutions, with roller Q at 250 (clean contact) and 150 (realistic with
contact resistance):

| Band | f (MHz) | L | I_roller | Loss @ Q=250 | Loss @ Q=150 | Efficiency | Q_loaded | 2:1 BW |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| **160 m** | **1.800** | 20.5 µH | **18.4 A** | **316 W** | **526 W** | **79%** | 15.6 | 115 kHz |
| 160 m | 1.900 | 15.1 µH | 17.3 A | 215 W | 358 W | 86% | 11.3 | 168 kHz |
| 160 m | 2.000 | 10.4 µH | 16.1 A | 136 W | 226 W | 91% | 7.6 | 263 kHz |
| 80 m | 3.500 | 21.6 µH | 6.0 A | 67 W | 112 W | 96% | 10.3 | 340 kHz |
| 80 m | 4.000 | 12.7 µH | 8.0 A | 82 W | 137 W | 95% | 9.3 | 430 kHz |
| 60 m | 5.332 | 2.1 µH | 10.0 A | 28 W | 47 W | 98% | 2.4 | 2.3 MHz |
| 40 m | 7.000 | 31.4 µH | 1.6 A | 14 W | 23 W | 99% | 7.9 | 887 kHz |
| 30 m | 10.100 | 7.7 µH | 2.9 A | 16 W | 27 W | 99% | 5.0 | 2.0 MHz |
| 20 m | 14.000 | 3.4 µH | 2.1 A | 6 W | 9 W | >99% | 2.1 | 6.6 MHz |
| 15 m | 21.000 | 1.0 µH | 3.9 A | 8 W | 14 W | >99% | 1.6 | 13 MHz |
| 12 m | 24.890 | 0.7 µH | 8.0 A | 26 W | 44 W | 98% | 2.8 | 8.8 MHz |
| 10 m | 28.000 | 0.7 µH | 7.8 A | 30 W | 51 W | 98% | 3.4 | 8.2 MHz |

**The loss is confined to 160 m, and specifically its bottom end.** Every other band edge stays
under 140 W even at Q = 150. The 200 W figure was broadly right — but wrong where it matters.

**Why 160 m is expensive.** At 1.800 MHz the antenna is 0.64 half-waves — electrically short, so
radiation resistance is low and the feeder presents R_in ≈ 8.9 Ω with −j226 of reactance. Matching
that to 50 Ω demands Q_loaded ≈ 15.6, which puts **4.3 kV RMS across the roller and 18.4 A through
it.** The loss is `I²·ωL/Q`, and at 232 Ω of reactance with Q = 150 that is 1.55 Ω of equivalent
series resistance carrying 18.4 A.

**This is an antenna limitation, not a tuner defect.** No feeder length fixes it — R_in on 160 m
stays between 7.6 and 11.6 Ω across every length from 60 to 120 ft. A 170 ft wire on 160 m is short,
and a tuner cannot recover what a short antenna does not present.

#### 1.7.1 Continuous power limit by band

Loss scales linearly with power, so for a **200 W internal dissipation budget**:

| Band segment | Continuous power limit |
|:--|--:|
| **160 m, 1.800–1.850 MHz** | **570 W** |
| **160 m, 1.850–1.950 MHz** | **840 W** |
| **160 m, 1.950–2.000 MHz** | **1325 W** |
| **All other bands** | **1500 W — no derate** |

Three things keep this from being a real constraint in practice:

1. **At 100 W — the stated typical operating power — worst-case loss is 35 W.** Trivial anywhere.
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
[50Ω Amp] -> [Bruene Bridge] -> [1:1 Input Choke] -> [Floating T-Network Deck] -> [600Ω Output]
```

**This is a compromise, adopted knowingly.** A 1:1 input choke provides common-mode isolation of the
coax from the shack; it does **not** by itself balance the antenna, because a T-network output is
single-ended. The floating deck is what creates the second output terminal, and it carries parasitic
capacitance to the surrounding chassis.

### 2.1 Alternatives evaluated and rejected on the record

| Topology | Verdict |
|:--|:--|
| **Link-coupled / Z-match** (Johnson Matchbox) | Truly balanced, no ferrite in the RF path. **Rejected:** automating variable link coupling plus multi-tap HV band switching needs rotary tap servos or multiple vacuum contactors. |
| **Differential balanced L/T** (Palstar BT1500A style) | Fully symmetric about ground, no floating-deck strays. **Documented as the gold-standard alternative; rejected** on cost — doubles the motorised elements and requires paired vacuum variables. |
| **Floating sub-deck** | **Adopted**, with the hard limits below. |

### 2.2 Balance specification

Balance is specified by **measured feeder current imbalance**, not by total deck capacitance —
total capacitance does not capture the structural asymmetry (leg 1 lands on the large deck plate,
leg 2 on a compact capacitor terminal):

```
    | I_leg1 - I_leg2 | / ( (I_leg1 + I_leg2)/2 )  <=  0.05
```

**Parasitic budget, derived:**

| Contribution | Value |
|:--|--:|
| Deck plate to floor, 8.50″ × 13.00″ at d = 2.50″ (`C = ε₀A/d`) | 9.94 pF |
| Fringing (perimeter 43.0″, Palmer) | ≈ 6.5 pF |
| Top coupling to lid at 5.0″ | ≈ 5.0 pF |
| Component bodies on deck | ≈ 7.0 pF |
| **Total C_deck-chassis** | **≈ 28.4 pF** |

Leg 2 presents ≈ 3.0 pF. A **0 to 30 pF adjustable aluminium trimming vane** between leg 2 and
chassis provides mechanical calibration to equalise both legs.

**Verification instrument:** a bifilar current transformer on the balanced output feeds
real-time imbalance telemetry to the microcontroller. Balance is measured, not assumed.

---

## Section 3 — Enclosure Architecture

**FIX APPLIED — the utility column has been re-proportioned and re-ordered.** Rev 3.2's layout
placed three NEMA 23 motors in a 5.50″ bay (they need 6.66″ in a row) and put the Control chamber at
the *rear* while assigning it the *front* display.

Outer envelope **16.00″ W × 16.00″ D × 10.00″ H**. One longitudinal spine wall divides the box into
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

### 3.1 Shaft geometry

The three driven components cannot sit in a single line across 6.66″ of depth — two 3.0″ capacitors
plus a 4.5″ roller inductor need 10.5″ in a row. They are therefore **staggered in width as well as
depth**, which gives unequal shaft lengths.

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
| Floating sub-deck standoff height (steatite or G10 pillars) | **2.50″** |
| Lateral clearance, deck edge to side and rear walls | **≥ 2.50″** |
| Clearance, 3.0″ vacuum caps and 4.5″ roller to any wall | **≥ 2.25″** |
| Edge radius on all HV conductors, busbars, lugs (corona suppression) | **≥ 1/16″** |

Standoff height is **2.50″ uniformly** across all sections, cut lists, and drawings.

> **Before cutting metal:** mock the RF bay up in cardboard with the actual components. The
> clearances above are necessary, not sufficient — final placement has not been proven in three
> dimensions.

---

## Section 4 — Materials and Cut List

**Sheet:** 5052-H32 aluminium — chosen over 6061-T6 for formability; it bends 90° without the
cracking 6061-T6 exhibits at tight radii.

| Panel | Dimensions | Qty | Gauge |
|:--|:--|--:|:--|
| Chassis floor | 16.00″ × 16.00″ | 1 | 12 ga (0.081″) |
| Longitudinal spine wall | 16.00″ × 10.00″ | 1 | 12 ga (0.081″) |
| Transverse sub-wall (Control/Motor) | 5.37″ × 10.00″ | 1 | 12 ga (0.081″) |
| Transverse sub-wall (Motor/Sampler) | 5.37″ × 10.00″ | 1 | 12 ga (0.081″) |
| Floating sub-deck plate | 8.50″ × 13.00″ | 1 | 12 ga (0.081″) |
| Front UI panel | 16.00″ × 10.00″ | 1 | 14 ga (0.064″) |
| Rear connection panel | 16.00″ × 10.00″ | 1 | 14 ga (0.064″) |
| Side wall panels | 16.00″ × 10.00″ | 2 | 14 ga (0.064″) |
| Removable lid | 16.00″ × 16.00″ | 1 | 14 ga (0.064″) |

**Raw stock — nesting verified, not just area-checked**

- **12 ga:** one **36″ × 36″** sheet. Parts total 580 in² of 1,296 in². Nests with the floor in one
  corner and the spine plus both sub-walls stacked beside it.
  *(A 24″ × 36″ sheet passes on area and fails on layout — after the 16×16 floor the remnants are an
  8×36 strip and a 16×20 region, which cannot yield a third 16″ part.)*
- **14 ga:** one **36″ × 36″** sheet. Parts total 896 in²; lid plus four 16×10 panels nest in three rows.
- **Frame:** **20 linear feet** of 1″ × 1″ × 1/8″ **6061-T6** angle.

**Assembly — bolted, not welded.** Continuous TIG seams across 16″ of 0.081″ aluminium cause severe
thermal warping and oil-canning, and seal the RF bay behind a permanent wall.

- 8-32 stainless button-head fasteners on **1.75″ centres** (λ/20 at 30 MHz is 19.7″, so this is
  more than sufficient for HF RF tightness)
- Beryllium-copper finger gasket along every partition seam and under the lid
- Yields >85 dB shielding at HF while keeping the RF bay serviceable
- Bolting also avoids the **40–50% HAZ strength loss** welded 6061-T6 suffers, preserving full T6 temper

*If any welding is done on 5052 sheet: 5356 filler, pure argon, 4–5 s post-flow.*

---

## Section 5 — Capacitors and Inductor (As Measured)

Every value here is from the parts in hand, measured, not from a catalogue.

### 5.1 Vacuum variables — existing Jennings UCSX, 20–675 pF / 10 kV

**The 85 pF travel clamp introduced in Rev 3.2 is removed.** It existed to dodge a 9.5 kV stress
figure that the real NEC model shows does not occur. Both capacitors mesh freely across their
full range.

Verified against all 27 band-edge points with the clamp removed and **no padding array**:

```
Coverage, bare capacitors        : 26/27   (only gap: 160 m @ 1.800 MHz)
Worst voltage utilisation        : 59% of rated withstand  ->  1.69x margin
Largest capacitance demanded     : 666 pF  (part reaches 675)
```

Worst case is 160 m at 1.900 MHz: 5,267 V peak across C1 meshed to 123 pF, against ~8.9 kV
withstand at that mesh. Every other band edge sits between 1% and 48% utilisation.

| Requirement | C1 (input) | C2 (output) |
|:--|--:|--:|
| Capacitance range demanded | 33 – 347 pF | 25 – 830 pF |
| Peak voltage | 6,102 V | 4,170 V |
| Available (part) | 20 – 675 pF | 20 – 675 pF + pad |

### 5.2 Output pad — one capacitor, one relay

The 4-bit binary array of Rev 3.3 is **deleted**. It existed only to keep the variables unmeshed
for voltage reasons; with real stress figures that rationale disappears. One fixed capacitor
closes the single remaining gap at the bottom of 160 m:

| Pad | C_var then | V_pad pk | I_pad | Variable utilisation |
|--:|--:|--:|--:|--:|
| **200 pF** | 493 pF | 2,341 V | 3.75 A | 47% |

**Specification:** one 200 pF transmitting doorknob (Centralab 858 or K15U-2 class),
**≥10 kV peak, ≥40 kVAr**, switched by one vacuum relay. A 40 kVAr part handles ~9.6 A at
1.8 MHz and sees 3.75 A — 2.6× margin.

*Deleted from Rev 3.3: seven doorknob capacitors, three vacuum relays, the binary decoder, the
16-state coverage table, and the per-unit LCR calibration procedure.*

### 5.3 Roller inductor — Harris 492-0309-000, measured

Pulled from a Harris SX-5A coupler. Variable-pitch winding (turns closer at one end), which
linearises µH per shaft revolution — exactly the characteristic wanted for stepper control.

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

> **Inspect the roller wheel contact surface before assembly.** At 18.4 A RMS on 160 m, oxidation
> or pitting on the wheel or its bus rod localises into heat. This is the one failure mode that
> matters on a surplus part, and it is far more consequential than anything in the inductance spec.

### 5.4 Series link inductor — one coil, one relay

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

### 5.5 Relay switching — break-before-make

Two relays total (output pad, series link). Neither may hot-switch:

1. PTT permissive is withdrawn (Section 7.4), dropping the bench-side keying switch
2. Hardware blanking timer enforces **30 ms RF decay** before any coil energises
3. Relays transition under zero-RF conditions
4. **25 ms** post-switch settling for contact bounce
5. Amplifier keying re-enabled

> Vacuum relays (Kilovac HC-1, Jennings RJ-series) are **single RF contacts in a vacuum envelope —
> no auxiliary dry contacts**, and operate in 6–20 ms, not <2 ms. The interlock is a separate
> signal relay or solid-state opto device on the same control line.

## Section 6 — Input Common-Mode Choke

**FIX APPLIED — former diameter reduced from 6.0″ to 4.0″.** The 6.0″ former did not fit the 5.37″
Sampler chamber in any orientation.

**No ferrite in the high-stress path.** With a floating deck, the input choke must withstand the full
deck-to-chassis common-mode potential — kilovolts. Fair-Rite #31 is deliberately lossy (μ″ ≫ 0); at
kV common-mode its resistive core dissipation would exceed 250 W and drive the ferrite past its
130 °C Curie point within seconds.

**Adopted: air-core Guanella transmission-line choke.**

| Parameter | Value |
|:--|--:|
| Former | **4.0″ dia G10 fiberglass** (4.25″ OD assembled) |
| Winding | **30 turns** RG-142B/U, close-wound single layer |
| Coax length | ≈ **31.4 ft** |
| Winding length | **5.85″** |
| Inductance (Wheeler) | ≈ **47 µH** |
| Mounting | Axis **vertical** in the Sampler chamber |

```
Fit check:  4.25" OD needs 4.25" in two dimensions
            Sampler bay is 5.37" W x 5.00" D x 10.00" H
            -> 0.56" clearance in W, 0.375" in D, 5.85" of 10" in H     FITS
```

**Choking reactance:** 547 Ω @ 1.85 MHz · 1,079 Ω @ 3.65 MHz · 4,199 Ω @ 14.2 MHz · 8,427 Ω @ 28.5 MHz

Zero magnetic core means zero core dissipation, zero flux saturation, and no Curie-point runaway.

> **OPEN ITEM — self-resonance.** A 31.4 ft winding has its first quarter-wave self-resonance near
> **5.5 MHz** (VF ≈ 0.70), i.e. between 80 m and 40 m. This is inherent: you cannot get both high
> low-band reactance and resonance-free HF behaviour from a single coax choke. **The finished choke
> assembly must be swept with a VNA before installation** and the resonance located. Do not assume
> the calculated reactance holds across the whole range.

**Low-band supplement.** Two Fair-Rite **#61** toroids in series on the cold side add >1,500 Ω of
reactive choking on 160/80 m. #61 is low-loss NiZn (tan δ < 0.005 below 10 MHz), so it adds
impedance without the thermal failure mode of #31 — roughly 1/50th the dissipation. Being reactive
rather than resistive, it can itself resonate with stray capacitance; include it in the VNA sweep.

---

## Section 6A — Directional Sampler and Impedance Measurement

Occupies the Sampler chamber alongside the input choke. This subsystem was named in every prior
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

Also known as the **Sontheimer coupler**; popularised for amateur use by Grebenkemper, KI6WX,
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
Magnetising inductance   L = A_L x N^2 = 73 nH x 1600 = 117 uH
Reactance at 1.8 MHz     X_L = 1,321 ohm   -> 26x the 50 ohm termination   OK
Flux density at 1.8 MHz  B = V/(4.44 f N A_e) ~= 8.7 gauss                 negligible
```

The magnetising reactance must stay well above the termination impedance at the **lowest**
frequency or low-band accuracy degrades; 26:1 is comfortable. Verify A_L against the actual core
datasheet — it varies between vendors and mixes.

**Terminations: 50 Ω non-inductive, 2 W minimum.** Metal film or carbon composition — **never
wirewound**, whose inductance destroys directivity. Both ports get identical parts; under high SWR
the reflected termination sees power comparable to the forward one.

### 6A.3b Physical placement — all detection happens in the Sampler chamber

**Conflict resolved.** Section 7.3 routes Sampler → Control crossings through 0.01 µF feedthroughs
with a 1 kΩ series resistor — a lowpass with a **15.9 kHz corner**. An RF sample at 1.8–30 MHz
cannot survive that; it would be attenuated to nothing.

Therefore **both detectors live in the Sampler chamber, next to the coupler.** Only their DC
outputs cross into Control, where the existing feedthrough filtering works exactly as intended.

```
SAMPLER CHAMBER                              | CONTROL CHAMBER
  coupler -> pads -> Schottky detectors ----> | 0.01uF + 1k -> ADC   (magnitude)
          -> pads -> AD8302 ----------------> | 0.01uF + 1k -> ADC   (V_MAG, V_PHS)
                                              |
  (no RF crosses the bulkhead)                |
```

The AD8302 and the Schottky detectors are the only active devices in the Sampler chamber; give
them a local regulator fed through a filtered feedthrough, not a shared rail.

### 6A.4 Magnitude path — protection and display

Coupled ports → Schottky envelope detectors (HSMS-282x class) → ADC.

Yields forward power, reflected power and SWR. This path drives the **fast protection trip**
(reflected-power threshold → PTT drop, Section 5.5) and must remain functional and independent of
the vector path — protection cannot depend on a computation.

**The trip is a comparator, not an ADC read.** Section 7.4 requires PTT to drop in <2 ms; a
firmware polling loop cannot guarantee that. Put an analogue comparator directly on the reflected
detector output, with its threshold set by a DAC or trimmer, and wire its output into the hardware
PTT loop. Firmware reads the same detector through the ADC for display and logging, but never
stands between a fault and the trip.

**Coupler primary.** The single-turn primary *is* the main RF path — the line conductor passes
through both cores. Size it as main-line conductor (≥ the input coax centre conductor), keep it
straight through the cores, and do not rely on the core for mechanical support.

### 6A.5 Vector path — the R/X measurement

Coupled ports → 60 dB resistive attenuation → **AD8302 gain-and-phase detector**.

```
Coupled port at 1500 W   : 6.85 V RMS into 50 ohm = +29.7 dBm
AD8302 useful input       : roughly -60 to 0 dBm, target about -30 dBm
Attenuation required      : ~60 dB, resistive pad on each port
```

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
   stored in EEPROM. Use the modelled sign as the initial hypothesis and confirm by method 1.
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

### 6A.9 Integration with the solver

With R and X in hand, the firmware solves the T-network in closed form rather than searching. The
validated solver is archived in `~/tuner-nec/tnet.py`:

```
XL >= sqrt(50 R)                              feasibility test
X1  = -XL +/- sqrt( R (XL^2/50 - R) )          node reactance
C2  = 1 / (w (X - X1))                         output capacitor
Im(Z2) = XL (X1(X1+XL) + R^2) / (R^2 + (X1+XL)^2)
C1  = 1 / (w Im(Z2))                           input capacitor, requires Im(Z2) > 0
```

Sweep L across the roller's measured 0.20–24.40 µH range (plus 10 µH when the series link is
engaged), take the first feasible solution, and drive all three elements to the computed
positions in one move. This is why the absolute encoders of Section 7.1 matter: a computed
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

A 37 dB range, so the front end must limit, not amplify linearly:

```
fwd port --> 1:1 isolating tap --> clamp diodes (+/- 5V) --> high-speed comparator
             (10:1 resistive)       back-to-back Schottky    (LT1016 / MAX9201 class,
                                                              ~10 mV hysteresis)
                                                                     |
                                                                     v
                                                            MCU timer input (counts to 30 MHz+)
```

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

**Operational notes:**
- Requires a **steady carrier**. SSB speech gives intermittent, modulated output and will not
  produce a stable reading. Tuning on a carrier (CW or the rig's TUNE mode) is standard practice
  for any tuner — make it an explicit requirement, not an assumption.
- **Carrier-present interlock:** below a count threshold, declare no carrier and inhibit tuning.
  This is free and prevents the tuner acting on noise.
- The comparator sees the fundamental plus any harmonics; at the coupler the fundamental dominates
  and comparator hysteresis handles the rest. No input filter needed.

## Section 7 — Control, Position Feedback, and Interlocks

### 7.1 Position feedback — no wires cross into the RF bay

**The Rev 1 rule is restored and binding: NO WIRES between the Motor Chamber and the RF Tank
Chamber.** Rev 3.2 placed SPI encoders on the component side of the shaft, inside the RF bay — an
active digital device in a multi-kilovolt near field, with its signal lines crossing back out.

```
[NEMA 23 dual-shaft stepper]
   |
   +-- rear shaft  --> [12-bit absolute multi-turn encoder]   (Motor Chamber)
   |
   +-- front shaft --> [zero-backlash helical coupler]
                          --> [0.375" OD heavy-wall G10 shaft]
                             --> [flanged bronze bushing in partition]
                                  ===== BULKHEAD - NO WIRES =====
                                --> [Delrin Oldham coupler - see 7.1a]
                                   --> [UCSX / Harris roller]   (RF Tank)
```

Open-loop step counting is rejected. Encoders are absolute and multi-turn, so position survives
power loss without a homing cycle; a lost step cannot silently invalidate a stored profile.

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
| **Specified** | **Commercial aluminium zero-backlash helical or bellows, 1/4″–3/8″** | **Shop-made Delrin (acetal homopolymer) Oldham** |

**Coupler A is a purchased part.** Both ends are in the same chamber at the same potential, and the
G10 shaft is the isolator. There is nothing a fabricated plastic coupler accomplishes here that a
$10–15 catalogue helical does not do better, with a known torque rating and no creep.

**Coupler B is specified as Delrin, superseding the "flexible bellows coupler" of Rev 3.3.** A metal
bellows at that position is a floating conductor mechanically captive to a rotor at up to 4,191 V
peak (Section 1.7) — an unnecessary electrode in the highest-field region of the cabinet. Delrin
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
> ~1.25 W** as a standoff insulator at 30 MHz and full voltage. Not a hazard — it is a fibreglass
> rod with a 130 °C service temperature and it is in open air — but it is the first identified
> dielectric loss inside the tank that is not the capacitors, and it scales as V². Worth confirming
> by touch after a long 10 m carrier run.

#### Why Oldham, not a solid hub

**This matters more than the material.** A rigid coupler forces the capacitor shaft to follow the
G10 shaft's axis exactly, dumping every bit of bushing-to-rotor misalignment into the vacuum
capacitor's bellows as radial side load. That is the same failure mode the limit switches of
Section 7.2 exist to prevent, reintroduced at the other end of the shaft.

An Oldham coupler — two slotted hubs and a centre disc with tongues 90° apart — accommodates
parallel offset by design, is zero-backlash when the tongue/slot fit is close, and is the easiest
coupler type to machine. Acetal is the standard centre-disc material in commercial Oldhams (Ruland,
Huco) precisely because of its low friction against the sliding tongue. Loading is trivial:

- Centre disc, 0.4 N·m, 8 mm tongue × 20 mm engagement × 3 mm height, 7 mm mean arm
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

### 7.2 Limits

Dual heavy-duty mechanical microswitches per axis, **wired directly to the hardware motor-driver
enable pins** — not through firmware. Power is cut before motor torque can crush a vacuum bellows
or strip the roller inductor wheel. Firmware cannot override them.

### 7.3 Bulkhead filtering

Every signal and sensor line crossing a chamber boundary passes through a **0.01 µF (10,000 pF)
filtered feedthrough capacitor**, paired with a **1 kΩ series carbon-composition resistor on the
ADC side**. That RC corner is 15.9 kHz — enormous rejection at 1.8 MHz and above, with settling
delay negligible for a DC-level reading.

| Boundary | Method |
|:--|:--|
| Sampler → Control | 22 AWG hookup through 0.01 µF feedthroughs + 1 kΩ series |
| Sampler → RF Tank | RG-213 or RG-393 PTFE coax, SO-239 bulkhead barrels |
| Control → Motor | Shielded twisted pair (4-cond, 18–20 AWG, foil), metal cable glands |
| **Motor → RF Tank** | **Insulated shaft only. No wires.** |

### 7.4 Amplifier interlock — optical permissive, fail-safe on loss of signal

> **Corrected for entry-box siting.** Earlier revisions specified *"a hardware loop in series with
> the amplifier keying line"* at the tuner. That assumed tuner and amplifier were co-located. With
> the tuner at the entry box (Section 1.6) and the amplifier at the bench, the keying line is
> twenty-odd feet away and the loop cannot live at the tuner.

Two tempting fixes are both wrong: running the keying pair out to the box reintroduces the copper
ground path that Section 8A.3 exists to eliminate, and carrying the permissive over the data link
contradicts Section 8C.6 — protection must never depend on the link.

**The interlock is its own dedicated optical channel, independent of the data link.**

```
   AT THE TUNER (entry box)                      AT THE BENCH
   -----------------------                       ------------
   MCU permissive      ----+
   over-SWR comparator ----+--> AND --> LED --> [ fibre ] --> receiver
   limit-fault clear   ----+                                     |
   lid interlock       ----+                                      v
                                                        opto-isolated switch
                                                                  |
                                           [ rig PTT ] -- E-STOP -+- [ amp key in ]
```

- The permissive is the **logical AND** of every protective condition, formed in hardware, not
  computed by firmware.
- It drives an LED into a dedicated fibre strand — **not** the data link, no protocol, no software.
- At the bench a receiver drives an **opto-isolated switch in series with the keying line**, in
  series with the hardwired E-STOP of Section 8C.2.

#### 7.4.1 Fail-safe analysis

| Failure | Optical state | Result |
|:--|:--|:--|
| Fibre broken or disconnected | dark | **inhibit** ✓ |
| LED or its driver fails open | dark | **inhibit** ✓ |
| Tuner loses power | dark | **inhibit** ✓ |
| Bench receiver loses power | switch unpowered, NO contacts | **inhibit** ✓ |
| MCU hangs | permissive is hardware AND, not firmware | **inhibit** ✓ |
| **LED driver fails shorted — stuck on** | **light present** | **permissive stuck closed — FAILS DANGEROUS** |

Every failure mode is safe except the last one, and the last one matters: a stuck-closed permissive
means the tuner can traverse the roller or switch a vacuum relay while the amplifier is keyed at
1500 W.

#### 7.4.2 Dynamic permissive — closing the stuck-on hole

Do not send steady light. Send a **modulated permissive**: the tuner pulses the LED at a fixed
tone (10 kHz is convenient from an MCU PWM output), and the bench receiver requires *that tone*,
not merely the presence of light, before closing the switch.

- Stuck-on LED → DC light, no tone → **inhibit** ✓
- Stuck-off, broken, dark → **inhibit** ✓
- A tone detector is a handful of parts; the MCU side is one timer channel.

This converts the only dangerous failure mode into a safe one. It is standard practice in safety
interlocks and is proportionate here: the consequence of a stuck-closed permissive is hot-switching
a vacuum relay or driving a roller under full power.

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

**Stock behaviour (for reference, and for the defensive rating below):** the SB-220 ANT RELAY jack
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
hot-switching a vacuum relay.

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

Control chamber fronts **5.37″ W × 10.00″ H** of the front panel.

```
Display : 3.5" TFT (ILI9488 / Nextion NX4832T035), bezel 3.96" W x 2.56" H
          -> 0.70" margin each side within 5.37"                    FITS

Vertical stack (10.00" available):
  top margin 1.00 + display 2.56 + gap 1.00 + encoder 1.25
  + gap 1.00 + encoder 1.25 + bottom margin 1.94  = 10.00"          FITS
```

- **Display shielding:** 100-mesh copper wire fabric laminated behind the panel cutout, **bonded
  continuously around the full perimeter** — an ungrounded mesh is decoration.
- **Manual controls:** two rotary optical encoders on non-conductive Delrin shaft extensions.
- **Menu architecture:**
  - *Tuning Monitor* — SWR, forward/reflected PEP, band and frequency, step counts for Cap 1,
    Cap 2 and the roller, plus feeder current imbalance from the bifilar CT
  - *Manual Override* — maps front encoders directly to stepper pulses
  - *Utilities* — Find Home, Save Profile to EEPROM, pad capacitor calibration entry

### 7.6 Tuning algorithm

**PID control of SWR is rejected.** SWR as a function of element position is not a smooth
single-minimum surface — it has multiple local minima, and a PID loop will hunt or settle
confidently into a high-SWR local minimum.

**Adopted:** measure R and X directly at the bridge and *compute* target positions from the network
equations, then refine with a bounded local search. Per-band solutions are stored as starting
points in EEPROM.

---

## Section 8 — Thermal

**Derived, not assumed — see Section 1.7.** Worst case is **316 W at roller Q = 250, or 526 W at
Q = 150**, both on 160 m at 1.800 MHz where the roller carries 18.4 A. Every other band edge stays
under 140 W.

The cooling system below is sized for **200 W continuous**, which covers every band except the
bottom of 160 m. That segment is handled by the **power derate table in Section 1.7.1** rather than
by more airflow — cooling 526 W out of a sealed 16″ enclosure is disproportionate for one band
segment used at full key-down power.

Natural convection through honeycomb cannot move 200 W. **Forced air required.**

| Element | Specification |
|:--|:--|
| Blower | 120 mm 12 V brushless, ball-bearing, external rear panel of RF bay |
| Intake | **Upper front-left sidewall** of RF chamber — *not* the chassis floor |
| Intake filter | Washable electrostatic cartridge over hex-cell honeycomb |
| Exhaust | Rear hex-cell aluminium honeycomb, 1/8″ cell, 1/2″ thick (>90 dB to 1 GHz) |
| Fan wiring | Enters utility bay via 0.01 µF feedthroughs + series bifilar chokes |

A floor intake was rejected: it blocks on a bench, and ingested dust settling on HV standoffs is a
tracking and flashover path at kilovolt potentials.

---

## Section 8A — Power, Grounding, and Entry-Box Infrastructure

Entry-box siting (Section 1.6) puts mains power and a control link at the point where the antenna
enters the building. That has consequences beyond a power supply.

### 8A.1 Rails and budget

| Rail | Load | Budget |
|:--|:--|--:|
| **24 V main** | 3 × NEMA 23 steppers via chopper drivers | 5 A peak while slewing |
| | 2 × vacuum relay coils (24–26 V types) | 2 A at pull-in, brief |
| **12 V** | cooling blower | 0.5 A |
| **5 V** | MCU, display, encoders, comparator | 2 A |
| **3.3 V** | AD8302, logic — local regulator in the Sampler chamber | 0.2 A |

Peak is non-simultaneous; **a 200 W 24 V supply is comfortable**, with DC-DC converters for the
lower rails. Size the stepper share from the actual driver datasheets — chopper drivers draw
considerably less from the supply than the per-phase current suggests.

**Cut stepper current when idle.** The roller leadscrew and the capacitor drives are self-locking,
so no holding torque is needed once positioned. This saves continuous dissipation inside a sealed
box and removes a standing heat source. It is only safe because position is held by **absolute**
encoders (Section 7.1) — with incremental encoders, de-energising would lose position.

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
   optical fibre: a light path carries no DC ground reference, so it can never become a second
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
| ~37 control signals | 55 IO available; the MCU mounts directly, no ribbon |

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

Implementation: **74AC4040** 12-stage ripple counter, Q9 output. Specify the **AC** variant — plain
HC is marginal at 29.7 MHz on a 3.3 V rail.

#### 8B.0.2 What this costs

Section 6A.3b argued that digitising locally is "strictly better" because the analogue measurement
signals then never cross a boundary. **That remains true** — it simply is not worth a second
microcontroller. The RC-filtered DC crossing was the design's own specification from Rev 1 onward
and is adequate: a 15.9 kHz corner against a 1.8 MHz lowest operating frequency.

The measurement board therefore carries **no microcontroller at all** — coupler, splitter,
detectors, AD8302, comparator, divider. Everything leaves as filtered DC plus one 29 kHz logic line.

#### 8B.0.3 Teensy 4.1 notes

- **Not 5 V tolerant.** Every input must be held at or below 3.3 V. The counter front end already
  clamps (Section 6A.10); check the limit-switch and encoder interfaces too.
- **No built-in SWD debugger**, unlike an ST-Link-equipped Nucleo. Programming is over USB; add SWD
  via the pads if hardware debugging proves necessary for the state machine.
- **FreqCount is documented for 1 kHz–8 MHz on Teensy 4.x** (the 65 MHz figure on PJRC's page is
  scoped to the Teensy 3.0–3.6 family). At ÷1024 the input is 29 kHz, comfortably inside the
  documented range — this is why the prescaler is specified rather than relying on forum reports of
  higher rates.
- **Ethernet deliberately unused.** The 4.1 has a MAC, but Section 8C.3 rejects copper to the bench
  on isolation grounds at an antenna entry point. The POF link stands; those pins stay free.

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

### 8B.4 Fault handling

| Fault | Immediate action | Recovery |
|:--|:--|:--|
| Limit switch | Hardware already cut driver enable | Back off that axis, re-home, flag |
| Over-SWR in transmit | Hardware comparator drops PTT (Section 6A.4) | Require manual acknowledgement |
| Encoder / position mismatch | Stop all axes | Re-home, re-verify, flag |
| Over-temperature | Drop PTT, blower to full | Auto-clear on hysteresis |
| No feasible solution | Stay put, inhibit full power | Flag — likely antenna fault |
| Carrier lost mid-tune | Abort to IDLE, hold position | Normal, not a fault |

**Power loss mid-tune is safe by construction.** Absolute multi-turn encoders mean position is
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
guessing, the behaviour is an explicit policy with a **conservative default**:

| Mode | Limit hit / encoder mismatch | Transmit | Intended for |
|:--|:--|:--|:--|
| **COMMISSIONING** | Logged, does **not** latch | **Hard-inhibited** | Bring-up and debugging |
| **STRICT** *(default)* | **Latches on first occurrence**, class C, local clear | Normal | Normal service |
| **PERMISSIVE** | First occurrence → remote ACK + re-home. Repeat in one session → escalates to C | Normal | Qualified hardware only |

**STRICT is the shipped and default state**, and the one to run until the roller has hours on it.
Rationale: this is a surplus Harris coil whose wheel and bus-rod contact condition is unproven
(Section 5.3). A slipping coupler, a binding leadscrew, or a roller riding off the winding all
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
- the roller wheel and bus rod inspected and found clean (Section 5.3)

Mode changes are **local-only** — a configuration action at the box (Section 8B.4f), never a remote command — and
every change is logged with a timestamp. A class C latch in PERMISSIVE mode automatically reverts
the policy to STRICT, so proven hardware that starts misbehaving tightens up by itself rather than
continuing on an assumption that has just been falsified.

### 8B.4b Behaviour across a power cycle

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

**Position survives power loss by construction.** Absolute multi-turn encoders mean an interrupted
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

For emergency operation, provide a **physically distinct, clearly labelled local bypass** that
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

| Action | Panel behaviour |
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
no extra hardware, and it is sampled before the display is even initialised.

#### 8B.4f.3 Recovery mode

For one situation: **the tuner is unreachable and cannot be fixed over the network** — a mistyped
static IP, wrong subnet, hostname clash.

**Two stages, so it degrades gracefully if the display is also dead:**

**Stage 1 — immediate, unconditional, no UI required:**

| | Behaviour |
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
another power cycle — so you cannot stumble out of recovery into a transmitting state. Signalled
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
curves and measured pad values (Sections 5.2, 6A.8) are too important to depend on a card that may
be out of the slot. The SD copy exists so calibration survives a board replacement and can be
transferred or inspected.

#### 8B.5.3 Behaviour with no card present

**Full function.** The tuner boots, tunes, protects, and reports with an empty slot:

| Item | No-card behaviour |
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

| Internal flash state | Card present and ID matches | Behaviour |
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
  "calibration":{ "detector_curves": [], "pad_measured_pF": [], "ad8302": {} },
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
  fall back to 8B.5.3 behaviour, logged. Never halt on a storage problem.
- **Card removal is not hot-swap safe.** Pull it with the tuner idle, or accept a possibly
  truncated log.

#### 8B.5.6 Physical access

The Control chamber is sealed (Section 8E). Reaching the card means removing the lid, which is a
deliberate occasional operation rather than routine — acceptable, because **the web UI is the
normal way to change configuration.** The card is for backup, transfer, and inspection.

> **Placement constraint:** the Teensy's SD socket needs insertion and ejection clearance. Orient
> the module so the socket faces the lid or a chamber edge, and keep that approach clear when
> laying out the Control board.

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

### 8C.3 Physical layer — Ethernet for data, optical fibre for the interlock

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
Ethernet at all.** Libraries: QNEthernet (lwIP-based) or NativeEthernet.

**Fibre.** One POF strand, HFBR-15xx/25xx class transceivers, carrying the modulated permissive.
Terminates with a razor blade and a crimp connector — no polishing, no fusion splicing.

**Rejected:** Wi-Fi, on its merits — an RF transmitter at the antenna entry point, inches from a
receive-path directional coupler.

### 8C.4 Two-part head

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
- Element positions — both capacitors and the roller, with the engaged pad and link state
- **Feeder current imbalance** from the bifilar CT (Section 2.2) — the only place balance is visible
- **Live dissipation estimate and derate status** (Section 1.7.1), with a warning when the 160 m
  limit is approached
- Fault log with timestamp, frequency and state
- Calibration data entry (Section 6A.8)
- Current fault-policy mode — **read-only; mode changes are local (8B.4a-1)**

### 8C.5 Protocol and telemetry

Line-oriented text over UART. Debuggable with a terminal emulator and a USB-serial adapter, which
matters when the thing is mounted on a garage wall.

| Aspect | Specification |
|:--|:--|
| Transport | **Ethernet (TCP for commands, WebSocket for telemetry)**; interlock is a separate POF strand carrying no protocol |
| Framing | Line-oriented text, one record per line, checksummed |
| Telemetry rate | 10–20 Hz SWR/power; 5 Hz frequency; positions on change |
| Fault events | **Pushed immediately**, never discovered by polling |
| Latency | < 100 ms end to end |
| Bandwidth | A few hundred bytes/second against ~11 kB/s available — ~3% utilised |

**Command set:** `TUNE`, `ACK`, `QUERY`, `SUBSCRIBE`, `GET_LOG`. Deliberately absent: fault-policy
mode changes, class C fault clears, and bypass — all local-only by design.

**Bandwidth is a non-issue on Ethernet** — a 20 Hz telemetry record of ~40 bytes is 800 bytes/s
against 100 Mbit/s. The point worth preserving from the serial design is that **fault events are
pushed, never polled**, so a congested or stalled link cannot delay a fault report. It can only
fail to deliver it, which the interlock strand makes safe.

**The interlock strand carries no protocol at all.** It is a 10 kHz tone, present or absent.

### 8C.6 Link loss behaviour

**Link loss degrades visibility, not safety.** Every protective function — the over-SWR comparator,
the limit switches, the relay sequencing, the PTT permissive — is hardware at the tuner and
entirely independent of the link.

On link loss:

| | Behaviour |
|:--|:--|
| Tuner | **Continues autonomously.** Holds its solution, retunes on frequency change as normal |
| Transmit | **Permitted.** Hardware protection is intact; the link was never in that path |
| Bench panel | LINK LED off; TUNE and ACK inoperative; E-STOP still works (hardwired, Section 8C.2) |
| Interlock | **Unaffected — separate fibre strand.** Permissive continues or withdraws on its own merits |
| Telemetry | Buffered at the tuner, replayed on reconnect so no fault events are lost |
| Medium | Data loss is Ethernet; the interlock strand is **optical and unaffected** by it |

Deliberately **not** implemented: inhibiting transmit on link loss. That would couple a convenience
path to a safety function and create a new failure mode — a flaky cable grounding the station —
while adding nothing, since protection never depended on the link.

### 8C.7 Network exposure

**The tuner now holds a LAN address.** The earlier design kept it off the network entirely by
speaking serial to a bench adapter; adopting Ethernet for data trades that structural protection
for a policy one. That trade is acceptable **only because the interlock is on its own fibre
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

Two feedthrough insulators on the rear panel, carrying the 600 Ω balanced output to the entry
panel. Named in every revision, specified in none.

### 8D.1 Voltage rating

From the band-edge envelope (Section 1.2b, 40 ft feeder):

```
differential, terminal to terminal  : 4,191 V peak  (2,964 V rms)
ideal balanced, each terminal to gnd:   2,096 V peak
design basis, assume full V on one  :   4,191 V peak
```

**Rate each feedthrough for the full differential voltage, not half.** In a perfectly balanced
system each terminal swings ±half, but this is a floating-deck approximation (Section 2.2) with
C_leg1-chassis ≈ 28.4 pF against C_leg2-chassis ≈ 3.0 pF before trimming. The split is asymmetric by
construction, and a mistrimmed or drifted vane puts more of the swing on one terminal. Designing
for half the differential bets the insulator on a trim adjustment holding.

**Specify ≥10 kV peak** transmitter-grade ceramic or steatite feedthroughs — 2.4× over envelope.

**Creepage, not just air gap, is the binding constraint.** The failure path on a feedthrough is
along the insulator *surface*, where contamination and humidity reduce withstand far below the air
figure. Clean dry ceramic manages roughly 1–2 kV per inch of surface path, so 4.2 kV wants 2–4″ of
creepage. That is what the skirts and ribs on transmitter-grade ceramic exist to provide.

> **Do not substitute a bolt through a plastic or phenolic block.** It will have the air gap and
> none of the creepage, and in an unheated garage it will track and carbonise.

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
is ≈ 6″, which fits across the 10.42″ rear face of the RF bay with room for the clearance below.

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

**There is no DC path from the output terminals to ground through this tuner.** Both output
conductors sit behind series capacitors (C2 and the pad), so the T-network presents an open circuit
at DC. Static accumulating on the antenna cannot drain through the tuner.

Drain therefore depends **entirely** on the arrestors and bonded baseplate at the entry panel. That
makes them load-bearing rather than belt-and-braces, and worth verifying rather than assuming:
confirm the arrestors are on the **antenna side** of the tuner, which they are in the specified
topology.

**Do not add a bleeder resistor at the tuner output.** It dissipates continuously at full power:

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
so they are not weather-exposed. But an unheated garage condenses, and condensation on ceramic
collapses creepage.

- Keep the enclosure sealed except for the filtered cooling path (Section 8).
- Fit a **drip loop** in the outdoor line before the entry panel so water does not track inward.
- Inspect and clean the feedthrough surfaces at the same interval as the roller contact
  (Section 5.3). Both are surface-condition failures and both are invisible until they arc.

---

## Section 8E — Environmental Protection

Site: **interior of a sealed, climate-controlled garage** (in-wall AC/heat combination unit),
Missouri. Scratch-built aluminium enclosure, mounted on the inside wall at the isolation box.

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
| Industrial-temp (−40/+85 °C) fibre converters | **Commercial 0–50 °C is adequate** for operating; confirm storage rating covers survival |
| Low-temperature synthetic leadscrew grease | **Standard grease is fine.** The cold-start torque problem does not arise at 10 °C |
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

**Membrane vents — keep them.** A PTFE pressure-equalising vent per sealed chamber still earns its
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
| 35 W *(100 W operating, typical)* | 119 BTU/hr | 1.5% |
| 200 W *(cooling design point)* | 682 BTU/hr | 8.5% |
| 400 W | 1,365 BTU/hr | 17.1% |

At typical operating power this is **negligible**. At the 200 W design point it is noticeable but
minor. The 400–526 W case occurs only on 160 m key-down at full power, which is already derated to
570 W output by Section 1.7.1 — so the worst sustained case is bounded well below it.

No action required; recorded so that a future "why is the garage warm during contests" question has
an answer.

### 8E.6 Gasketing a scratch-built box

Unchanged, and still the hardest part of this section to execute.

> **BeCu finger stock (Section 4) seals RF, not dust or moisture.** It is a spring contact, not a
> gasket. Specifying it does not get you IP5X.

Two options:

1. **Conductive elastomer gasket** — does both jobs in one part. More expensive, and needs decent
   flange flatness to compress evenly.
2. **Two gaskets in parallel channels** — finger stock for RF, separate closed-cell elastomer for
   environment. More machining, more forgiving of flatness.

The binding constraint either way is **flange flatness**. On scratch-built 14 ga aluminium a plain
sheared edge will not seal. **Form a flange on the panel edges, or add a stiffener strip**, and
check with a straightedge before committing to a gasket type — that decision is expensive to revisit
after fabrication.

---

## Section 9 — Open Items

| # | Item | Status |
|:--|:--|:--|
| 1 | **Feeder trim** — cut long, finish with a removable ~2 ft jumper, trim empirically against measured SWR (Section 1.4) | **BY DESIGN** |
| 2 | **Roller wheel / bus rod contact condition** — inspect and clean before assembly; 18.4 A RMS localises at any oxidation | **REQUIRED** |
| 2a | **Mechanical fault policy qualification** — run STRICT until 100 tune cycles / 50 h / zero mechanical faults, then consider PERMISSIVE (Section 8B.4a-1) | **COMMISSIONING TASK** |
| 3 | **Choke self-resonance near 5.5 MHz** — VNA sweep the finished assembly; note 60 m sits at 5.332–5.405 MHz, within 2.4% | **OPEN — highest priority** |
| 4 | ~~Remote head / network link~~ — **CLOSED**, specified in Section 8C (fibre link, two-part head, hardwired bench E-STOP) | **CLOSED** |
| 4a | ~~Frequency counter~~ — **CLOSED**, specified in Section 6A.10 (gate counter, 200 Hz resolution) | **CLOSED** |
| 4b | ~~Tuner power supply~~ — **CLOSED**, specified in Section 8A. *New sub-item: verify entry-panel bonding to service ground (8A.3).* | **CLOSED** |
| 4c | ~~Firmware state machine~~ — **CLOSED**, specified in Section 8B | **CLOSED** |
| 5 | **RF bay 3-D mock-up** in cardboard with actual components before cutting metal | **REQUIRED** |
| 6 | ~~Balanced output feedthroughs~~ — **CLOSED**, specified in Section 8D (≥10 kV ceramic, spacing matched to feeder, strain relief off the ceramic) | **CLOSED** |
| 7 | ~~Bruene bridge design~~ — **CLOSED**, specified in Section 6A as a Stockton coupler with dual magnitude/vector paths | **CLOSED** |
| 8 | ~~Grounding scheme~~ — **CLOSED**, single-point at the arrestor baseplate (Section 8A.2); isolated control link breaks the bench ground loop (8A.3) | **CLOSED** |
| 9 | **Antenna end height** assumed 10 ft; envelope covers 6–15 ft so this is confirmation, not a blocker | **OPEN (low risk)** |
| 10 | **10 m reactance ±10%** — NEC X not fully converged at 1200 segments near the 4.9 λ antinode | **OPEN (low risk)** |
| 11 | ~~Network loss / efficiency~~ — **CLOSED**, derived in Section 1.7; 160 m derate table in 1.7.1 | **CLOSED** |
| 12 | **Measure actual roller Q** once assembled — the 150 vs 250 assumption swings the 160 m derate by 1.7× | **COMMISSIONING TASK** |
| 13 | ~~Enclosure environmental spec~~ — **CLOSED**, Section 8E revised for a climate-controlled garage interior: IP5X sealed chambers, ventilated RF bay, membrane vents, 30–40 mesh, heater provision only | **CLOSED** |
| 14 | **Amplifier keying interface** — SB-220 identified; confirm by measurement which keying regime is present (Section 7.4.4). Switch is spec'd defensively for the stock +120 V case either way | **OPEN — measurement only** |
| 17 | **Amplifier T/R relay release time** — scope RF decay after permissive withdrawal; confirm the 30 ms blanking covers it (Section 7.4.5) | **OPEN — bench measurement** |
| 18 | ~~Cold-start motion check~~ — **DOWNGRADED TO OPTIONAL**; garage is climate controlled (Section 8E.2). Worth one check only if left unconditioned over a winter | **OPTIONAL** |
| 19 | **Flange flatness / gasket selection** — form flanges or stiffeners before choosing gasket type (Section 8E.7) | **OPEN — fabrication** |
| 15 | **Utility column re-order** to Sampler / Control / Motor, local UI to side panel (interconnect map finding) | **OPEN — layout change** |
| 16 | **Crossings 6 and 7** — relay coil drive into, and imbalance CT / thermal sensor out of, the RF tank. Absent from the Section 7.3 table | **OPEN** |
| 20 | **G10 shaft dielectric dissipation** — calculated ~1.25 W per shaft at 30 MHz / 4,191 V (Section 7.1a). First identified tank loss that is not the capacitors; scales as V². Confirm by touch after a long 10 m carrier run | **OPEN — commissioning check** |
| 21 | **Oldham tongue/slot fit** — backlash is set entirely by this clearance. Measure total drive-train lash at the element with a dial indicator before trusting a stored profile (Section 7.1a) | **OPEN — fabrication QA** |
| 22 | **Chamber layout dimensioning** — §4 sub-wall 5.37″ vs §6 bay depth 5.00″; neither fills 16″ exactly. Compounded: the 5.00″ Motor bay does not clear a NEMA 23 plus coupler plus encoder takeoff (5.22″, Section 10.6). Resolve before cutting metal | **OPEN — blocks fabrication** |
| 24 | **Element breakaway torque unmeasured** — §3.1's 0.4 N·m is stated for the capacitor mechanism only; the Harris roller is unquantified. Settles DECISION M-2 and the motor purchase | **OPEN — bench measurement** |
| 23 | **§7.3 contradiction** — opening rule requires a feedthrough on every crossing line; the table routes Control→Motor through glands instead. Pick one (Section 10.15) | **OPEN** |

**Closed in this revision:** static drain and lightning protection (existing entry-box bonded
baseplate and arrestors); roller inductor range (measured); capacitor adequacy (verified 1.69×);
network topology (plain T confirmed sufficient — switchable T/Pi not required at 40 ft).

### 9.1 Parts summary — critical path

> **This is a summary of the components that drove the design, not a build list.**
> For a complete from-scratch bill of materials — assuming nothing in hand — see **Section 10**.


| Item | Source | Status |
|:--|:--|:--|
| 2 × Jennings UCSX 20–675 pF / 10 kV | **in hand** | verified adequate, 1.69× |
| 1 × Harris 492-0309-000 roller, 0.20–24.40 µH | **in hand** | verified, inspect contact |
| 1 × 200 pF doorknob, ≥10 kV / ≥40 kVAr | to buy | output pad |
| 1 × 10 µH air-wound link inductor, 18.4 A | to wind | series link |
| 2 × HV vacuum relay (Kilovac HC-1 / Jennings RJ) | to buy | pad + link |
| 3 × NEMA 23 stepper + absolute encoder | to buy | unchanged |
| 3 × aluminium zero-backlash helical coupler | to buy | motor side only (Section 7.1a) |
| Delrin rod stock, ~1" dia | to buy | Oldham couplers, element side (7.1a) |
| Sheet, angle, BeCu gasket, feedthroughs, blower | to buy | unchanged |

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

No prices are given. They go stale, they vary by territory, and three of the DECISION items span
an order of magnitude in cost — those carry indicative bands because the cost *is* the decision.

Reference designators (R1, U3, J7 …) refer to the KiCad schematics in `~/tuner-kicad/`.
Quantities are per tuner, excluding the bench panel of 10.9, which is one per operating position.

---

### 10.1 RF power path

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 2 | Vacuum variable capacitor | 20–675 pF, 10 kV, e.g. **Jennings UCSX-675-10S** | Class | §5.1 |
| 1 | Roller inductor | 0.20–24.40 µH, HF-rated, e.g. **Harris 492-0309-000** (ex-SX-5A) | Class | §5.3 |
| 1 | Transmitting doorknob capacitor | **200 pF, ≥10 kV pk, ≥40 kVAr** — Centralab 858 or K15U-2 class | Class | §5.2 |
| 1 | Link inductor | **10 µH air-wound**, 18.4 A RMS — fabricate, see 10.14 | Fabricate | §5.4 |
| 2 | HV vacuum relay | SPST, 24–26 V coil, HF-rated — **Kilovac HC-1** or **Jennings RJ-1A** | Class | §5.5 |
| 1 | Floating sub-deck | 8.50″ × 13.00″, 12 ga — cut from sheet stock in 10.11 | Fabricate | §4 |
| 4 | Sub-deck standoff insulator | Ceramic or PTFE, ≥1.50″ height, HV-rated | Class | §3.2 |
| — | Tank interconnect strap | Copper strip, 0.032″ × 0.75″, ~4 ft — radius all edges ≥1/16″ | Class | §3.2 |

> The two relays are **single RF contacts in a vacuum envelope with no auxiliary dry contacts**
> (§5.5). Anything needing a confirmation contact uses a separate signal relay or opto device.

---

### 10.2 Input common-mode choke

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 1 | Coil former | **4.0″ dia G10 fibreglass tube**, ≥7″ long (4.25″ OD assembled) | Class | §6 |
| 1 | Winding coax | **RG-142B/U**, **31.4 ft** — 30 turns close-wound, 5.85″ winding length | Part | §6 |
| 2 | Former end cap / mount | G10 or PTFE, axis vertical in Sampler chamber | Fabricate | §6 |
| 2 | SO-239 bulkhead connector | PTFE dielectric, silver-plated | Class | §7.3 |

> **OPEN (§9 item 2):** first quarter-wave self-resonance of a 31.4 ft winding lands near 5.5 MHz,
> which collides with 60 m. VNA sweep required before committing. A different turn count may
> follow — order the coax with slack.

---

### 10.3 Directional sampler (Stockton / Tandem Match)

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 2 | Toroid core | **FT-82-61** NiZn, µ ≈ 125 — verify A_L against the actual vendor datasheet | Part | §6A.3 |
| — | Secondary winding wire | **40 turns each**, #26 AWG enamelled, ~6 ft total | Class | §6A.3 |
| — | Primary conductor | The through-line itself — PTFE-insulated, rated 14 A RMS | Class | §6A.3 |
| 2 | Termination resistor | **50 Ω, 2 W, non-inductive** — metal film or carbon comp, **never wirewound** | Class | §6A.3 |
| 2 | Sampler enclosure | Small diecast or PCB-shield can, inside the Sampler chamber | Class | §6A.3b |

---

### 10.4 Measurement board — 54 components

`~/tuner-kicad/measurement.kicad_sch`. Routed, 0 unconnected. All passives through-hole except
the four SOD-323 diodes, the AD8302 (TSSOP-14), the TLV3501 (SOIC-8) and the AMS1117 (SOT-223).

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

### 10.5 Control board — 40 components

`~/tuner-kicad/control.kicad_sch`. Routed, 0 unconnected. The Teensy mounts directly — verify the
**15.24 mm row spacing with calipers** before ordering boards (§9).

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

**Bare boards:** 2 × 2-layer PCB, 1.6 mm FR4, HASL or ENIG. Gerbers generate from `route.sh`.

---

### 10.6 Motion subsystem

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 3 | Stepper motor | **Single shaft is correct — see DECISION M-2.** NEMA 17 (0.42 N·m, 42×42×38) behind a 3:1 belt, or NEMA 23 **23HS30-2804S** (1.9 N·m, 2.8 A, Ø6.35 mm, 76.5 mm) direct | DECISION | §7.1 |
| 3 | Stepper driver | Chopper, 24 V, ≥3 A/phase, STEP/DIR/EN opto inputs — **StepperOnline DM542T** class | Class | §8A.1 |
| 3 | Absolute multi-turn encoder | 12-bit minimum, SPI — **see DECISION M-1, 10.14** | DECISION | §7.1 |
| 3 | Motor-side coupler | Aluminium zero-backlash helical, **8 mm → 9.525 mm (0.375″)** bore | Class | §7.1a |
| 3 | Element-side coupler | **Delrin Oldham** — fabricate from rod stock below | Fabricate | §7.1a |
| 3 | Insulating drive shaft | **0.375″ OD heavy-wall G10 rod**, length per axis + 2″ | Class | §7.1, §3.1 |
| 3 | Flanged bushing | Bronze, 0.375″ bore, partition-mount | Class | §7.1 |
| 3 | Intermediate bearing block | G10, required on any free span over 6″ | Fabricate | §3.1 |
| — | Delrin rod stock | Acetal **homopolymer**, 1.0″ dia × 12″ — Oldham hubs and discs | Class | §7.1a |
| 6 | Roll pin / dowel | 1/8″ × 0.75″, stainless — coupler retention, **not set screws** | Class | §7.1a |
| 6 | Limit microswitch | Heavy-duty mechanical SPDT, lever — wired to driver EN pins, not firmware | Class | §7.2 |

**Rail check with the real motor:** 2 phases × 2.8 A × 1.13 Ω = **17.7 W per motor**, drawing
**0.74 A from 24 V**, so three motors take **2.21 A** against the 5 A budget of §8A.1 — comfortable.
This also quantifies why §8A.1 de-energises at idle: **53 W of standing heat** in a sealed box
otherwise.

> **Why single shaft, corrected.** An earlier reading of §7.1 — encoder on the rear shaft —
> implied a dual-shaft motor. **It does not fit.** Depth stack against the 5.00″ Motor Chamber:
>
> | Arrangement | Depth | Result |
> |:--|--:|:--|
> | 23HS30-2804**S** single shaft + coupler | 4.59″ | fits, 0.41″ spare |
> | 23HS30-2804**S** + encoder belt takeoff | 5.22″ | **over by 0.22″** |
> | 23HS30-2804**D** dual shaft + rear encoder | 5.81″ | **over by 0.81″** |
> | NEMA 17 + 3:1 belt + encoder takeoff | 3.54″ | fits, 1.46″ spare |
>
> Buying the dual-shaft variant would have forced a chamber redesign. The rear shaft was never
> the constraint — **chamber depth is**. Since the encoder must come off a belt takeoff in any
> case (DECISION M-1 option B), it does not care which end of the motor it is driven from, and
> taking it off the G10 shaft puts the motor-side coupler *inside* the measurement loop, which is
> strictly better than reading the motor's rear shaft.

---

### 10.7 Local panel (Control chamber front face, 5.37″ W × 10.00″ H)

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 1 | Display | **3.5″ TFT**, ILI9488 SPI or **Nextion NX4832T035**, bezel 3.96″ × 2.56″ | Class | §7.5 |
| 2 | Rotary encoder | Optical or mechanical detented, with push, panel mount, 1.25″ dia knob | Class | §7.5 |
| 2 | Encoder shaft extension | **Delrin**, short, unloaded — RF isolation, not stiffness | Fabricate | §7.1a |
| 1 | Recovery button | Momentary, **recessed**, IP-rated, long-press for recovery boot | Class | §8B.4f.2 |
| 1 | microSD card | 8–32 GB, industrial or high-endurance grade | Class | §8B.5.5 |
| 1 | Panel gasket | Closed-cell elastomer behind display and control cutouts | Class | §8E.4 |

> §8B.5.6 constrains Control-board placement: the Teensy's SD socket needs insertion and ejection
> clearance, so orient the module with the socket facing the lid or a chamber edge.

---

### 10.8 Interlock and remote link

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 1 | POF transmitter | **Broadcom HFBR-1521Z** class, 660 nm | Class | §8C.3.3 |
| 1 | POF receiver | **Broadcom HFBR-2521Z** class | Class | §8C.3.3 |
| — | Plastic optical fibre | 1 mm duplex POF, length = tuner to bench + 20 % | Class | §8C.3.3 |
| 4 | POF crimp connector | Simplex latching — razor-blade termination, no polishing | Class | §8C.3.3 |
| 1 | Opto-MOSFET switch | **Panasonic AQV252 / AQY212** PhotoMOS — <2 ms, solid-state | Class | §7.4.3 |
| 1 | Ethernet kit | **PJRC Teensy 4.1 Ethernet kit** — magjack carrier + ribbon | Part | §8C.3.3 |
| 1 | Ethernet bulkhead | RJ45 panel feedthrough, **unshielded** — see §8C.3.1 | Class | §8C.3.1 |

> **Unshielded is deliberate.** §8C.3.1 corrects an earlier overstatement: STP makes the surge case
> *worse* by bonding the bench and entry-box grounds, and the coax shield already bridges them.
> The interlock stays optical regardless, because protection must not depend on the data link
> (§8C.6).

---

### 10.9 Bench panel — one per operating position

Physically separate build (§8C.4a). No software in the E-STOP path.

| Qty | Item | Specification | Type |
|--:|:--|:--|:--|
| 1 | Enclosure | Diecast or ABS, desktop, ~6″ × 4″ × 2″ | Class |
| 1 | E-STOP switch | **Large, red, latching, mushroom head** — breaks amp keying locally | Class |
| 2 | Pushbutton | Momentary — TUNE, ACK | Class |
| 4 | Indicator LED | MATCHED (grn), TUNING (amb), FAULT (red), LINK (blu) | Class |
| 1 | POF receiver | HFBR-2521Z class — the permissive arrives here | Class |
| 1 | Keying interface | Opto-MOSFET rated for the amplifier's keying regime | Class |
| 1 | Amp keying cable | To SB-220 relay jack — **see DECISION I-1, 10.14** | DECISION |

---

### 10.10 Power distribution

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 1 | Main supply | **24 V, 200 W**, low conducted emission, enclosed frame | Class | §8A.1 |
| 1 | DC-DC converter | 24 V → 12 V, 1 A — blower | Class | §8A.1 |
| 1 | DC-DC converter | 24 V → 5 V, 3 A — MCU, display, encoders | Class | §8A.1 |
| 2 | Common-mode choke | Mains-rated, on supply input **and** output leads | Class | §8A.1 |
| 1 | Ground strap | Tinned copper braid, 1″ wide × 18″ — chassis to arrestor baseplate | Class | §8A.2 |
| 1 | IEC inlet | Fused, filtered, panel mount | Class | §8A.1 |
| — | Hookup wire | 18 AWG (24 V), 22 AWG (signal), PTFE preferred | Class | §7.3 |

> The supply is a switcher sitting at the antenna entry point, directly on the receive path.
> §8A.1 requires it in the **Control chamber — never Sampler or RF**.

---

### 10.11 Enclosure, mechanical, EMI

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 1 | Aluminium sheet, 12 ga | **36″ × 36″**, 5052-H32 (0.081″) — floor, spine, sub-walls, sub-deck | Part | §4 |
| 1 | Aluminium sheet, 14 ga | **36″ × 36″**, 5052-H32 (0.064″) — panels, sides, lid | Part | §4 |
| 20 ft | Angle stock | **1″ × 1″ × 1/8″ 6061-T6** | Part | §4 |
| 200 | Machine screw | **8-32 stainless button head**, 1/2″ — see 10.13 for the count | Part | §4 |
| 200 | Nut / nutsert | 8-32, stainless | Part | §4 |
| 20 ft | BeCu finger gasket | Spring finger stock — **RF only, not an environmental seal** | Part | §4, §8E.6 |
| 8 ft | Elastomer gasket | Closed-cell, lid perimeter — **or** conductive elastomer in place of both | DECISION | §8E.6 |
| 50 | Feedthrough capacitor | **0.01 µF**, solder-in, 500 V — see 10.13 | Part | §7.3 |
| 36 | Series resistor | **1 kΩ carbon composition**, ADC side of each feedthrough | Part | §7.3 |
| 4 | Cable gland | Metal, EMC, 1/2″ NPT — Control→Motor shielded pairs | Class | §7.3 |
| 2 | Honeycomb vent panel | **Hex-cell aluminium, 1/8″ cell, 1/2″ thick** (>90 dB to 1 GHz) | Class | §8 |
| 1 | Blower | **120 mm, 12 V brushless, ball bearing** — external rear of RF bay | Class | §8 |
| 1 | Intake filter | Washable electrostatic cartridge, over honeycomb | Class | §8 |
| 2 | Membrane vent | Gore or equivalent, pressure equalisation | Class | §8E.4 |
| — | Shielded twisted pair | 4-conductor, 18–20 AWG, foil — Control→Motor | Class | §7.3 |
| — | Coax, internal | **RG-213** or **RG-393 PTFE** — Sampler→RF tank | Class | §7.3 |

---

### 10.12 Output termination

| Qty | Item | Specification | Type | Ref |
|--:|:--|:--|:--|:--|
| 2 | HV feedthrough insulator | **≥10 kV**, ceramic, panel mount, ¼–⅜″ stud | Class | §8D.1 |
| 2 | Output terminal | Brass or copper stud, **6.03″ spacing for #12 open-wire** — measure the actual line | Class | §8D.2 |
| 1 | Strain insulator | Anchored to wall or frame — **takes all mechanical load** | Class | §8D.4 |
| — | Jumper conductor | Same gauge and spacing as the feeder, 1–2 ft maximum | Class | §8D.4 |
| 2 | Lightning arrestor | At the entry baseplate, **antenna side of the tuner** | Class | §8D.5 |

> §8D.5: there is **no DC path to ground through this tuner** — both conductors sit behind series
> capacitors. Static drain depends entirely on these arrestors. They are load-bearing. Do not add
> a bleeder resistor at the output (1 MΩ dissipates 8.8 W continuously at 1500 W).

---

### 10.13 Derived quantities — method, not guesswork

Three quantities are defined by rules in Sections 4 and 7.3 but were never tallied. Computed from
the 16″ × 16″ × 10″ geometry with a 5.00″-deep utility strip and three 5.37″ bays:

**Fasteners — 8-32 on 1.75″ centres (§4)**

| Seam | Length |
|:--|--:|
| Floor to 4 perimeter walls | 64.00″ |
| Vertical corners (4) | 40.00″ |
| Lid to wall tops | 64.00″ |
| Spine wall to floor | 16.00″ |
| Spine wall to front + rear panels | 20.00″ |
| Transverse sub-walls (2 × floor + spine + outer) | 50.00″ |
| **Total seam length** | **254.00″ (21.2 ft)** |

254.00 ÷ 1.75 = 145, plus ~14 seam-end fasteners ≈ **159. Order 200.**

**BeCu finger gasket (§4)**

Under lid (wall tops 64.00″ + spine top 16.00″ + sub-wall tops 10.74″) = 90.74″; partition seams
86.00″. **Total 176.74″ = 14.7 ft. Order 20 ft.**

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

The last two rows are **crossings 6 and 7 of §9 item 16**, absent from the §7.3 table. Counting
them here does not close that item; the table still needs correcting.

---

### 10.14 Open selections — DECISION REQUIRED

These are not omissions. Each is a real trade-off that changes cost or architecture, and inventing
a part number would hide the choice rather than document it.

**M-1 · Absolute multi-turn encoder (×3) — the cost driver**

Requirement: absolute position across the element's **full travel (~30 turns)**, surviving power
loss with no homing cycle (§7.1, §8B.4b). Low-cost magnetic encoders are **single-turn**; genuine
multi-turn absolute is an industrial part.

| Option | Approach | Indicative cost (×3) | Trade |
|:--|:--|:--|:--|
| **A** | Industrial multi-turn SSI/SPI (Posital IXARC class) | **$600–1200** | Drops straight in. Expensive |
| **B** | Single-turn absolute (AS5048A class) on a zero-backlash **timing-belt reduction** so full travel < 1 rev | **$60–120** | Cheap and absolute, but the reduction must be belt or friction — **any geared backlash lands directly in the position reading** |
| **C** | Single-turn absolute + firmware turn counter, battery-backed | **$60–100** | Cheapest. **Forfeits the power-loss guarantee** when the battery dies — contradicts §8B.4b |

Recommendation: **B**. It preserves the absolute-across-power-loss property that §8B.4b depends on,
at roughly a tenth of A. It does add a mechanism per axis, which belongs in Section 7 before it
belongs in a BOM.

**M-2 · Motor frame and reduction ratio**

The 0.4 N·m of §3.1 is stated for **the vacuum capacitor mechanism**. The Harris roller — leadscrew
plus a spring-loaded wiper — has never been measured and may need more.

| Option | Buys | Torque at element | Depth | Trade |
|:--|:--|--:|--:|:--|
| **A** | 2 × 23HS30-2804S | 1.90 N·m (4.75×) | 5.22″ — **0.22″ over** | Simplest drive. Needs a deeper bay. 53 W idle heat |
| **B** | nothing | 1.26 N·m (3.15×) | 3.54″ — 1.46″ spare | 3 × NEMA 17 + 3:1 belt. 18 s full travel, 0.60°/step, ~31 W |
| **C** | nothing | roller 1.90×, caps 1.26× | mixed | NEMA 23 direct on the roller, NEMA 17 + belt on both caps |

**Settle this by measurement, not estimate.** Both elements are in hand: measure breakaway and
running torque with a spring scale on a known radius. If the roller stays under 1.26 N·m, **B buys
nothing and fits best**; if it exceeds that, **C** puts the large motor where the load is.

Reduction also costs slew time — 3:1 takes full travel from 6 s to 18 s at 1 kHz — while *improving*
resolution from 1.80° to 0.60° per step at the element. Belts are zero-backlash, so the reduction
does not degrade position the way a geared head would.

**I-1 · SB-220 keying interface** — §7.4.4 specifies the switch defensively for the stock +120 V
case. §9 item 14 requires **measuring** which regime the modified amplifier actually presents
before the opto-MOSFET and its cable are finalised.

**G-1 · Gasket strategy** — §8E.6: conductive elastomer (one part, both jobs, needs flange
flatness) **or** two gaskets in parallel channels (more machining, forgiving of flatness). §9 item
19 makes this dependent on forming flanges first. **Expensive to revisit after fabrication.**

**L-1 · Choke turn count** — §9 item 2. The 31.4 ft figure in 10.2 stands only if the VNA sweep
clears 60 m. Order coax with slack.

---

### 10.15 Discrepancies found while compiling this section

Three inconsistencies surfaced only when the scattered specifications were put in one table:

1. **§4 transverse sub-wall dimension.** The cut list gives **5.37″ × 10.00″**, but §6's choke fit
   check establishes the bays as **5.37″ W × 5.00″ D** — which makes the sub-wall 5.00″ long, not
   5.37″. Neither reading fills the 16″ width exactly (3 × 5.37 + 2 × 0.081 = 16.27″; 3 × 5.00 +
   2 × 0.081 = 15.16″). **The chamber layout needs dimensioning properly before cutting metal.**
   Carried to §9 as item 22.
2. **§7.3 internal contradiction.** The opening sentence requires a feedthrough capacitor on
   *every* line crossing a boundary; the table beneath routes Control→Motor through **cable glands
   with shielded twisted pair** instead. 10.13 counts them as feedthroughs (19 of the 36) on the
   conservative reading. Carried to §9 as item 23.
3. **Stepper shaft configuration.** §7.1 requires a rear shaft for the encoder but never says
   **dual-shaft** in so many words, which is how a single-shaft motor gets ordered. 10.6 now states
   it explicitly.

---

*Stress basis: real NEC-2 simulation, `nec2++` (708/708 self-tests pass), 1200 segments,
Sommerfeld-Norton ground, 27 band-edge points across 160 m–10 m inclusive of 60 m. Network
reachability verified by closed-form T-network solution at every point against measured component
ranges. Model, solver and raw output archived in `~/tuner-nec/`.
Review history and per-item resolutions: `~/tuner-design-review-rev3.2.md`.
Previous revision preserved at `~/.designlog_rev3.3.bak`.*
