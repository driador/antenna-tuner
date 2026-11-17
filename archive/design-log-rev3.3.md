# 1500W Automated Antenna Tuner — Design Log
### Revision 3.3 — Consolidated Master · Mechanical Fixes Applied · Real NEC-2 Basis

**Revision history**
- **Rev 1** — initial spec. Correct on materials/welding, chamber-crossing discipline, relay sequencing.
- **Rev 3.2** — *replacement, not revision*. Fixed several items; dropped four correct sections from
  Rev 1, which is how the encoder regression got in.
- **Rev 3.3 (this document)** — **cumulative consolidation.** Restores everything Rev 3.2 dropped,
  applies all agreed review resolutions, fixes the three outstanding mechanical conflicts, and
  rebases every stress figure on a real NEC-2 simulation of the *actual installed antenna*.

**Changes in this revision**
1. **Antenna basis corrected** — modelled as an inverted-V/sloper at its real height, not a 55 ft flattop.
2. **Padding array bit 3 → 4 × 100 pF** (was 2 × 200 pF, under-rated on current).
3. **Input choke former → 4.0″** (was 6.0″, did not fit its 5.37″ chamber).
4. **Utility column re-proportioned and re-ordered** (motors did not fit; display faced the wrong panel).

---

## Section 1 — Antenna and System Basis

> **Correction carried into this revision.** Rev 3.2 and all prior stress figures assumed a
> *"170 ft horizontal dipole at 55 ft AGL."* The installed antenna is an **inverted-V / sloper
> with an apex near 35–40 ft, cut for NVIS work.** Every voltage and current figure below has
> been recomputed for that geometry.

**Modelled configuration**
- 170 ft total #12 AWG copper (85 ft per leg), center-fed
- Inverted-V, apex 37.5 ft, ends 10 ft AGL (horizontal run ≈ 80.4 ft per leg)
- Real ground: σ = 0.005 S/m, ε_r = 13 (Sommerfeld-Norton, `GN 2`)
- Copper wire loss included (`LD 5`)
- Feeder: 88 ft of 600 Ω open-wire ladder line, VF 0.95

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

### 1.2 Tuner input impedance and 1500 W PEP stress — 88 ft line

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

### 1.3 Design envelope

Apex and end height are both approximate, so the design figures are the **worst case across
apex 35–40 ft and ends 6–15 ft**, not the nominal:

| Quantity | Nominal | **Design envelope** |
|:--|--:|--:|
| Peak RF voltage at tuner | 3,088 V | **3,140 V** |
| Peak RF current at tuner | 12.51 A | **13.12 A** |

Across that whole geometry range the worst case moved only 3,056–3,140 V and 11.79–13.12 A — the
design is insensitive to the remaining height uncertainty. **Both limits occur on 160 m.**

### 1.4 Feeder length

Swept 60–120 ft against the real model, worst case across all nine bands:

```
  68 ft   3722 V   13.02 A      92 ft   3612 V   12.32 A
  72 ft   3363 V   12.99 A      96 ft   4127 V   12.09 A
  80 ft   2913 V   12.81 A     104 ft   5125 V   11.55 A
  84 ft   3099 V   12.68 A     112 ft   6073 V   10.89 A
  88 ft   3088 V   12.51 A     120 ft   6960 V   10.13 A
```

- **78–88 ft is a broad acceptable plateau.** 88 ft is confirmed sound.
- **Do not exceed ~92 ft** — peak voltage climbs monotonically and steeply beyond it.
- Shorter line lowers voltage but slightly *raises* current. Since voltage margin is >4× and
  current margin is the binding constraint, the upper end of the plateau is preferred.
- **Do not chase the 80 ft minimum.** Real open-wire VF varies 0.90–0.98 with construction, which
  slides the whole curve; sitting mid-plateau beats hitting an unreproducible minimum.

### 1.5 Safety

- **Peak RF voltage up to ~3.1 kV** at high-impedance nodes. Contact causes deep RF burns which are
  far more extensive than they appear at the surface. Note the mechanism: above ~100 kHz the hazard
  is **thermal, not electrocution** — HF RF does not induce ventricular fibrillation. The practical
  rule is unchanged: never open the cabinet with the amplifier keyed.
- **Circulating current up to ~18.5 A RMS** through the roller inductor on 160 m. Any oxidation or
  weak contact at the roller wheel becomes localised ohmic heating, pitting, or arcing.
- **160 m is the limiting band for both** voltage and current in this installation.

---

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

## Section 5 — Capacitors and Padding Array

### 5.1 Vacuum variables

**Jennings UCSX-700-15S, 25–700 pF, 15 kV peak test.** The UCSX family derates with mesh —
approximately 15 kV at minimum capacitance falling toward maximum — so travel is clamped:

| Parameter | Value |
|:--|--:|
| Travel limit, lower bands | **85 pF** |
| Withstand at 85 pF | ≈ **14.21 kV** |
| Design peak voltage (envelope) | 3,140 V |
| **Margin** | **4.53×** |

*(The earlier 20–675 pF / 10 kV part was rejected: at 200 pF it derates to ~8 kV, and even clamped
to 75 pF it reached only ~9.4 kV.)*

### 5.2 Padding array — FIX APPLIED

4-bit binary array, **50 / 100 / 200 / 400 pF**, switched by vacuum relays.

**Coverage.** Variable span is 85 − 25 = **60 pF** against a 50 pF smallest step, giving **10 pF
overlap at every state boundary** — monotonic and gap-free from 25 pF to 835 pF across all 16 states.

```
  0000 ->    0 pF :   25 -  85 pF        1000 ->  400 pF :  425 - 485 pF
  0001 ->   50 pF :   75 - 135 pF        1001 ->  450 pF :  475 - 535 pF
  0010 ->  100 pF :  125 - 185 pF        ...
  0011 ->  150 pF :  175 - 235 pF        1111 ->  750 pF :  775 - 835 pF
```

**Construction — bit 3 changed from 2 × 200 pF to 4 × 100 pF.** The previous configuration was
under-rated: paralleling two capacitors doubles the kVAr rating but the bit's reactance halves, so
current capability does **not** double as claimed.

| Bit | Value | Build | Unit Xc | Bit capability | Worst current | Margin |
|:--|--:|:--|--:|--:|--:|--:|
| 0 | 50 pF | 1 × 50 pF | 445 Ω @ 7.15 MHz | 9.48 A | 5.74 A | 1.65× |
| 1 | 100 pF | 1 × 100 pF | 223 Ω @ 7.15 MHz | 13.41 A | 5.74 A | 2.34× |
| 2 | 200 pF | 2 × 100 pF | 223 Ω @ 7.15 MHz | 26.81 A | 5.74 A | 4.67× |
| 3 | **400 pF** | **4 × 100 pF** | 860 Ω @ 1.85 MHz | **27.28 A** | **13.12 A** | **2.08×** |

*Worst case assumes the bit carries the entire branch current with all other bits open. Bit 3 is
rated on 160 m, where the design-envelope current is 13.12 A; the smaller bits are rated on 40 m,
the highest-current band at which a small total capacitance is actually commanded.*

```
  2 x 200 pF (rejected) :  19.29 A  ->  1.47x   too thin
  4 x 100 pF (adopted)  :  27.28 A  ->  2.08x   adequate
```

**Specification:** Centralab 858 or K15U-2 transmitting doorknobs, **15 kV peak minimum, 40 kVAr
minimum each.** Eight capacitors, two part numbers (50 pF × 1, 100 pF × 7). Verify kVAr at the
operating frequency — ceramic loss tangent derates reactive power with frequency.

**Tolerance.** A 400 pF doorknob at ±5% is ±20 pF, which would swamp 10 pF of designed overlap.
Every capacitor is **individually metered on a precision 100 kHz LCR bridge on arrival and its
measured value stored in EEPROM**; the auto-tune solver computes state boundaries from measured,
not nominal, capacitance. Paralleling four units on bit 3 also averages the tolerance stack.

### 5.3 Relay switching — break-before-make

Firmware must never hot-switch a vacuum relay. Sequence, enforced in hardware:

1. PTT interrupt drops the amplifier keying line via high-speed optocoupler
2. Hardware blanking timer enforces a **30 ms RF decay period** before any relay coil energises
3. Relays transition under zero-RF conditions
4. **25 ms** post-switch settling for contact bounce
5. Amplifier keying re-enabled

> Vacuum relays (Kilovac HC-1, Jennings RJ-series) are **single RF contacts in a vacuum envelope —
> they have no auxiliary dry contacts**, and operate in 6–20 ms, not <2 ms. The interlock is a
> separate signal relay or solid-state opto device on the same control line. An auxiliary contact,
> where one exists, is a *permissive* confirming position — it is not a sequencer.

---

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
                                --> [flexible bellows coupler]
                                   --> [UCSX / Harris roller]   (RF Tank)
```

Open-loop step counting is rejected. Encoders are absolute and multi-turn, so position survives
power loss without a homing cycle; a lost step cannot silently invalidate a stored profile.

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

### 7.4 Amplifier interlock

A hardware loop in series with the amplifier keying line drops PTT in **<2 ms** (solid-state, not a
relay contact) on any of: limit switch fault, high-SWR spike, cabinet latch break, or pad-array
switching command. Independent of firmware state.

### 7.5 User interface

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

Up to **200 W** of inductive loss during high-Q low-band operation (160 m: roller branch carries
≈18.5 A RMS, ≈15.9 kVAr, ≈64 W at Q_coil = 250; the remainder is contact and dielectric loss).

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

## Section 9 — Open Items

| # | Item | Status |
|:--|:--|:--|
| 1 | **Choke self-resonance near 5.5 MHz** — VNA sweep of the finished assembly required before install | **OPEN** |
| 2 | **Antenna end height** assumed 10 ft — measure it; the design envelope covers 6–15 ft so this is confirmation, not a blocker | **OPEN (low risk)** |
| 3 | **10 m reactance ±10%** — NEC X had not fully converged at 1200 segments near the 4.9 λ voltage antinode | **OPEN (low risk)** |
| 4 | **RF bay 3-D mock-up** in cardboard with actual components before cutting metal | **REQUIRED** |
| 5 | **Roller inductor µH range** still unspecified — needed to confirm the network reaches every computed Z_in | **OPEN** |
| 6 | **Grounding scheme** — single-point vs multi-point bonding across four chambers not yet defined | **OPEN** |

---

*Stress basis: real NEC-2 simulation, `nec2++` (708/708 self-tests pass), 1200 segments,
Sommerfeld-Norton ground. Model and raw output archived in `~/tuner-nec/`.
Review history and per-item resolutions: `~/tuner-design-review-rev3.2.md`.*
