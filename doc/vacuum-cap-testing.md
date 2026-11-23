# Vacuum Variable Capacitor Testing

As of 2026-11-13 · Reuben A. Popp

A used vacuum variable is fit for the tuner once it passes five checks in order: mechanism,
capacitance range, glow (glass only), DC hi-pot, and an on-air test under load. Loss of vacuum is
the most common hidden failure: with gas inside, the plate gaps arc at a few hundred volts to a
couple kV instead of at the rated voltage, and a meter won't show it.

## Caps under test

| Cap | Range | Envelope | Peak voltage rating | Current rating |
|:--|:--|:--|:--|:--|
| Jennings UCSX-740-10 (**C2**) | 20–675 pF | Ceramic (opaque) | 10 kV test / **6 kV working** | UCSX family 65 A (catalog); this OEM variant unconfirmed |
| 15 kV-class C1, to buy: UCSX-700-15 ("CB-154") or CVDD-500-15S | 25–700 / 20–500 pF | Glass / ceramic | 15 kV test / **9 kV working** | 70 A / 95 A |
| Soviet KP1-4 (spare) | 20–1000 pF (±5 / ±10%) | Glass (confirmed) | 10 kV | 50 A, to 30 MHz |

**Jennings ratings:** the model suffix is the **peak test** voltage. The RF **peak working**
voltage is 60% of it: 6 kV for a -10 part, 9 kV for a -15. Margins below use working voltage.

### KP1-4 datasheet ([eandc.ru](https://eandc.ru/pdf/kondensator/kp1-4.pdf), 20–1000 pF variant)

| Parameter | Value | Tuner impact |
|:--|:--|:--|
| Nominal voltage | 10 kV | Same as Jennings |
| Working current | ≤ 50 A | Well above ~14 A design-basis peak (§1.3) |
| Frequency | ≤ 30 MHz | 10 m (28–29.7 MHz) is at the limit |
| Drive torque | ≤ 0.49 N·m | Above the 0.4 N·m assumed in §3.1; re-check stepper and G10 shaft sizing |
| Axial thrust | 344 N | Bearing/mount must take this |
| Tuning cycle life | up to 5,000 cycles | Low for an auto-tuner; limit full sweeps, prefer memory recall |
| Tuning speed | ≤ 5 cycles/min | Cap the stepper speed for this axis |
| Size (D × L) | 145 × 278 mm (5.7″ × 10.9″) | Far larger than the 3.0″ caps in §4 layout; re-check clearances |
| Mass | ≤ 3,200 g | Needs a solid mount, not shaft-hung |
| Minimum service life | 1,000 h | — |
| Ambient / pressure | −60 to +125 °C; to 533 hPa | Fine |

### Stress these caps will see (design log Rev 3.7c, §5.1: bare network, band edges)

| Position | C demanded | Peak V @ 1500 W | Peak V @ 1100 W (×0.856) |
|:--|--:|--:|--:|
| C1 (input) | 33–347 pF | 6,540 V (1.800 MHz) | ~5,600 V |
| C2 (output) | ≤ 270 pF needed to match; solver runs to 675–875 pF (design log §5.1, Rev 3.6) | 2,400 V | ~2,050 V |

*Rev 3.3 gave 6,102 V and 4,170 V here, with the output pad and series link the design has since
deleted (design log §11).*

- **UCSX-740-10 (6 kV working) belongs in C2.** C2 worst case is 2.40 kV peak without the pad
  (1.86 kV with it): 2.50× margin. In C1 it would see 6.54 kV bare / 5.99 kV padded at 1.800 MHz,
  0.92× / 1.00× of its working rating, which is not acceptable at 1500 W (design log §5.1, Rev 3.7).
- **C1 needs a 15 kV-class part (9 kV working):** 1.38× bare / 1.50× padded at 1500 W.
- **KP1-4 (10 kV, 50 A):** now a spare. The Rev 3.6 re-run shows a bare Jennings already covers
  every band edge, so its extra range removes nothing that is required (design log DECISION C-1,
  resolved Rev 3.7). The catches are mechanical: size, mass, 0.49 N·m torque, and a 5,000-cycle tuning life.

## 1. Mechanical inspection

Do this first. A cap that fails here never needs high voltage.

- [ ] Envelope: no cracks or chips, especially at the seals to the metal end rings.
- [ ] End stops: turn slowly to find both ends. **Never force past a stop.** Over-travel can tear
      the bellows. Some Soviet caps lack positive stops, so feel for rising resistance.
- [ ] Full travel: torque is smooth and even. Grinding, binding or a tight spot means a bent
      shaft, galled lead screw or damaged bellows.
- [ ] Turn count end to end recorded (needed for encoder/step calibration).
- [ ] Copper end rings and mounting faces cleaned of tarnish. They carry RF current, and poor
      contact becomes a hot spot.
- [ ] Shaft not bent. Mount with a flexible/insulated coupling so the drive puts no side load on
      it (see design log §7.1a; never drill the Jennings shaft).

## 1a. Lead-screw cleaning and re-grease

Do this after the mechanical checks above and **before** the glow test and hi-pot, so those tests
also prove the cleaning did no harm.

The drive screw and nut are on the **air side** of the bellows. The vacuum is not exposed, but the
bellows wall is thin, and the bellows is the part you are working next to. Two things kill it:
puncturing or denting it, and **twisting** it. Rough cleaning is the danger, not the solvent.

**Before**

- [ ] Glow test (KP1-4) and record the result as the before-cleaning baseline.
- [ ] Measure drive torque at several points through the full travel with a torque screwdriver or
      small torque gauge on the shaft. Record the peak value.

**Cleaning the screw and the cavity**

1. **Orient the cap so the cavity opening faces down,** so loosened grease and solvent drain out,
   not further in. Clamp it gently by the end ring in a padded holder, never by the glass.
2. **Set the travel to open the bellows convolutions.** Turn to whichever end of travel extends the
   bellows. The pleats open up and the grease in them becomes reachable.
3. **Warm it gently.** A hair dryer or heat gun on low, to about 50–60 °C (hand-warm, not hot), for
   a few minutes. Old grease softens a great deal and wipes out instead of needing to be scraped.
   Both caps are rated well above this (KP1-4 to +125 °C). Warm evenly and keep the heat off any one
   spot on the glass.
4. **Remove the bulk mechanically.** Use soft tools only: wooden or bamboo skewers, plastic picks,
   foam swabs (not cotton, which leaves lint). Work along the convolutions, not into them. **No
   metal picks or dental tools inside the cavity.**
5. **Then clean with a damp swab.** Use a foam swab wetted with naphtha and squeezed out, not
   dripping. Wipe, discard, repeat. Use IPA for the final wipe; it leaves less residue.
6. **Use the screw to help.** Running the screw slowly through its travel pushes old grease out of
   the thread onto the swabs. Do this by hand and stop well short of both ends.
7. **Stop at "clean enough."** A thin stained film left in a convolution that never touches the
   screw or nut is harmless. Chasing it with tools is how the bellows gets dented.

**Do not**

- Do not use compressed air into the cavity. The bellows is built for one atmosphere across it,
  and an air nozzle in a blind cavity can push well past that.
- Do not immerse the cap or put it in an ultrasonic cleaner.
- Do not spray brake cleaner or other aerosol solvents into the cavity. The spray force drives
  grease deeper, chlorinated types leave residue, and they attack some insulating parts.
- Do not use acetone or other aggressive solvents if there are any plastic, textolite or phenolic
  parts in the drive. Naphtha and IPA are safe on these.
- Do not take the drive apart unless it clearly comes apart. If the screw and nut must come out,
  hold the moving end so the bellows **cannot rotate** while threads are loosened. Twisting the
  bellows is a common way to lose a vacuum cap.

**Re-grease**

- [ ] Let the solvent flash off completely (15–30 min, cavity facing down).
- [ ] Use a light, non-tacky, non-conductive synthetic grease, e.g. Super Lube (PTFE). Don't use
      graphite or MoS₂ (they conduct, and the screw sits at or near terminal potential). Don't use
      silicone (it creeps onto the envelope and leaves a tracking path). Don't use tackified
      greases such as red and tacky (they add drag, collect dust and stiffen with age).
- [ ] Apply a **thin film** to the screw thread only, then run the full travel by hand several
      times. Wipe off whatever squeezes out of the nut. Leave the cavity and bellows unpacked.
- [ ] Keep grease off the glass, the ceramic and the end-ring contact faces.

**After**

- [ ] Re-measure drive torque through the full travel and record it. Use the measured peak, not the
      0.49 N·m datasheet figure, for the stepper and G10 shaft check (design log §3.1).
- [ ] Glow test again (KP1-4). It must still be dark. Any glow now means cleaning damaged the bellows.

## 2. Low-voltage electrical checks

These catch plate damage but say nothing about vacuum. A cap full of air passes them perfectly.

- [ ] Capacitance range: LCR meter or NanoVNA at min, max and several points between. Expect
      ~20–675 pF (Jennings) and ~20–1000 pF (KP1-4). Far-off readings, jumps or dropouts mean
      bent or touching plates.
- [ ] Shorts: ohmmeter, or better a 500–1000 V insulation tester, swept across the full range.
      Must read open everywhere.

## 3. Glow test (glass envelopes only)

A handheld high-frequency spark tester ("vacuum leak detector", e.g. Electro-Technic BD-10A) held
near the glass shows the vacuum state directly. It doesn't work through the Jennings' ceramic body.

- No glow: hard vacuum, which is good.
- Pink, purple or blue glow inside: soft vacuum. The cap is compromised.

## 4. DC hi-pot test

This is the definitive vacuum check. Apply a slowly rising DC high voltage through a current limit
and watch for breakdown or leakage.

**Equipment, best to worst**

- Hi-pot tester or 5 kV / 10 kV insulation tester (e.g. Megger MIT-series). It's current-limited,
  reads leakage directly, and is the safest option. Worth renting or borrowing.
- Variable HV DC supply with a few MΩ of series HV-rated resistors, short-circuit current
  ≤ ~1 mA, microammeter in the ground return.
- **Never a microwave oven transformer.** It delivers lethal current with nothing to limit it.

**Procedure**

1. Test once at minimum capacitance and again at maximum, because breakdown can occur at different
   points in the travel.
2. Start low and raise in ~500 V steps, holding each step 30–60 s.
3. **Good:** leakage in the µA range or below. A few small arcs that clear and don't return are
   normal conditioning for a shelf-stored cap, so let it settle before going higher.
4. **Bad:** repeated arcing under ~2–3 kV that doesn't clear, steadily climbing leakage, or
   visible glow in a glass envelope. That means gas inside, and the cap is scrap for HV use.
5. **Ceiling:** never exceed the rated test voltage. Target ~1.5× worst-case peak RF voltage for
   the position:
   - C1, 15 kV-class: 1.5 × 6.54 kV ≈ **10 kV** (under its 15 kV test rating).
   - C2, UCSX-740-10: **6 kV**, its working rating. That is 2.5× its 2.40 kV duty and well under
     its 10 kV test rating.
   - KP1-4 (spare): 6 kV is enough to show it holds vacuum.

**Safety**

- One hand in your pocket. Clip leads only, never hand-held probes.
- Discharge the cap with a grounding stick through a resistor before every touch. Stored energy is
  small (1000 pF at 5 kV ≈ 12 mJ); the supply is the real hazard.
- Supply off and zero volts verified before moving any lead.

## 5. On-air test and current rating

After the bench tests pass, install the cap and work up in power across bands, including the
worst-case high-Z loads (160 m, per §1.3) where voltage across the cap peaks.

- [ ] Low power first, then step up. Watch for SWR jumps, crackling and amplifier faults.
- [ ] After a sustained key-down, feel the end rings and mounts for heating.

Current is the other rating. The bellows is in the current path, and current rises with frequency
and capacitance (I = 2πfCV), so high bands at large C settings are the worst case. A cooked bellows
is the other main way these caps die. Confirm each cap's RF current rating against the ~14 A peak
design-basis figure (§1.3) and stay under it.

## Verdict guide

| Result | Meaning |
|:--|:--|
| Smooth mechanism, correct C range, no glow, holds rated test voltage | Good: use it |
| Arcs at low kV, doesn't clear | Lost vacuum: QRP or low-voltage positions only |
| C range wrong, intermittent, or shorts | Mechanical damage: scrap |
| Rough or binding mechanism but passes hi-pot | Usable, but suspect the bellows: be gentle and monitor |

## Test log

| Test | Jennings UCSX-740-10 (C2) | KP1-4 (spare) |
|:--|:--|:--|
| Turns end to end | | |
| Drive torque peak, before / after re-grease (N·m) | | |
| Glow test before cleaning | N/A (ceramic) | |
| Measured C min / max (pF) | | |
| Insulation test, full sweep | | |
| Glow test | N/A (ceramic) | (glass, applies) |
| Hi-pot at min C: max kV held, leakage (µA) | | |
| Hi-pot at max C: max kV held, leakage (µA) | | |
| On-air: max power, bands, heating | | |
| Verdict | | |

## Open questions

- UCSX-740-10 current rating (OEM variant; the catalog UCSX family is 65 A).
- Add a test-log column for the C1 part once bought. The UCSX-700-15 is glass, so the glow test
  applies; the CVDD-500-15S is ceramic, so it doesn't.
