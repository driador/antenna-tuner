<!-- SPDX-FileCopyrightText: 2026 Reuben A. Popp -->
<!-- SPDX-License-Identifier: CERN-OHL-W-2.0 -->

# Bench Tests Before Cutting the Enclosure

As of 2026-11-22 · Reuben A. Popp

Nothing in the tuner has run on hardware yet. Four things carry most of the build risk: the
homebuilt roller, the K1 coax relay at full power, the AD8302's lost phase sign, and the two used
vacuum variables. Each can be proved on the bench before any metal is cut, and a failure in any of
them changes what gets cut. This is the procedure, with a decision rule for the result that matters
most, the roller's Q.

Figures are from the design log, Rev 3.7c. "§" means a section of the log, and "item N" an entry in
its §9 open-items table. Anything marked *(inferred)* is this document's own reasoning or arithmetic,
not the log's; check it before relying on it. *(proposed)* marks a pass/fail figure the log does not
set, offered for the owner to accept or change. Not covered here, though both can also run on the
bench: the input choke (item 49) and the amplifier's T/R relay release time (item 17).

## Safety

- **1.5 kW into a dummy load (test 2).** RF burns go deep (§1.5). Tighten every connector before
  keying. Hands off the relays, jumpers and load while keyed.
- **26 A DC (test 1.4).** Leads and lugs get hot. Make and break connections with the supply off. A
  clamp that lifts at this current arcs and pits the very contact under test.
- **Hi-pot (test 4).** Follow the safety rules in [vacuum-cap-testing.md](vacuum-cap-testing.md).
- **The low-power bench T (test 3b).** At 10 W on 160 m, C1 still sees about 0.5 kV peak
  *(inferred: 6.54 kV × √(10/1500), §1.3)*. Hands off while keyed.

## 1. Homebuilt roller inductor

**Purpose.** The roller (§5.3a, DECISION R-1 = C) is the one tank part with no catalog behind it. At
160 m, 1.800 MHz, it carries **18.4 A RMS** with **4.63 kV RMS** across the turns in use (§1.3,
§5.3a, item 45). Its Q sets the 160 m power limits (§1.7.1, item 12). Its wheel contact is "the one
failure mode that matters on any roller" (§5.3a). Its idle turns resonate near the top of 10 m
(item 44). These tests run the §5.3a commissioning checks on the bench, while the coil can still be
changed. The build is TUNER-L-100 to L-109 (Appendix A): 34 µH free air, 5.20″ to wire center,
22 turns of #4 at 3 TPI, notched for 24.

**Equipment**
- LCR meter (100 kHz–1 MHz). VNA covering 1–35 MHz, S11 and S21 (NanoVNA class).
- C2 (UCSX-740-10) as a low-loss resonator for 1.5, with short, wide copper straps, and two small
  coupling capacitors of a few pF.
- A stand-in deck: a 12 ga (0.081″) 5052 aluminum plate at least the deck's 10.75″ × 10.75″ (§3.0,
  §10.11), with the deck's 1.50″ hole for the shaft and thrust collar (TUNER-L-109). Also a wooden or
  plastic platform with the same hole, for the free-air tests.
- A torque gauge, or a spring scale on a lever or pulley of known radius (§10.14, M-2).
- A supply that holds 26 A at a volt or two: a constant-current DC supply, or a variac driving a
  low-voltage, high-current transformer. A DC clamp meter or a shunt.
- A DMM that resolves 0.01 mV, for Kelvin readings. Fine-gauge thermocouples, Kapton tape and a
  logger. An IR thermometer.
- For the motor steps of 1.3: a 23HS22-2804S, a DM542T-class driver on 24 V and a step source
  (§10.6).

**Setup, all of section 1.** Stand the roller upright on plate A as installed (TUNER-L-109), so the
rotor weight rides bearing A as it will in service (item 30(c)). Keep metal at least one coil
diameter (5.2″) off the ends and half a diameter off the sides (§5.3a, "What sets Q", rule 1), except
where a test adds the stand-in deck. The bus rod is the hot terminal. The deck strap from the finger
block is the cold one (§5.3a, "The shaft is cold").

### 1.1 Inspect, then measure L

**Steps**
1. Inspect and clean before anything else (item 2, REQUIRED: "18.4 A RMS localizes at any
   oxidation"). Look at the wheel groove and face, the wire's outer surface along the wheel track,
   the shoe, the carriage bore and the bus rod, the cold-end collar and the BeCu fingers. Photograph
   each.
2. Check that every rib edge sits about 1/16″ below the top of the wire (§5.3a, TUNER-L-101). A
   flush rib makes the wheel chatter.
3. On the wound helix, before final assembly (§5.3a), measure L end to end and at each turn, at 1 MHz
   or below. The NEC model reports L at 1 MHz. Do this before the RTV dabs lock the turns, so turns
   can still come off *(inferred)*.
4. Mark the wheel position for each setting in the 1.5 table.

**Pass/fail**
- §5.3a: "confirm ≥ 34 µH free air (≥ 23 µH needed installed) and ≤ 0.46 µH reachable. Use the spare
  notches if short."
- The hard requirement is **≥ 23.1 µH installed** (item 47: the worst case over feeder 39–42 ft,
  VF 0.93–0.97). With the deck's 3–5 % (item 32) that is about 24 µH free air *(inferred)*.
- *(inferred)* Don't wind the spare turns just to reach 34 µH. The NEC model already puts the 22-turn
  coil at 30.6 µH (item 44), so the 34 µH check fails on the model's own numbers while the 23.1 µH
  need is met. Every added turn also lengthens the idle section, which pulls the 10 m resonance down,
  and item 44's remedy is fewer idle turns. Run 1.2 first, then decide.

**Record.** L end to end; L at every turn; the turn for each 1.5 setting; photos of every contact
surface.

### 1.2 Idle-turn self-resonance (item 44)

**Purpose.** The turns beyond the wheel resonate. `nec/roller_vna.py` puts the resonances at the
roller's terminals at **13.2–15.6 MHz** and **28.4–30.2 MHz** for every wheel position. Every band
edge lands off them except the top of 10 m: "wheel ≈ 1 turn, idle resonance ≈ 30.1 MHz, only 1.3%
above 29.7 MHz → Q ≈ 185, ~11 W at 29.7 MHz" (item 44, status "modeled risk at 29.5–29.7 MHz"). The
model leaves out the Ultem ribs, whose dielectric pulls the resonance down.

**Setup.** The wound roller with wheel, carriage and bus rod in place, before final assembly. VNA S11
across the terminals, cold end to bus rod: the port `roller_vna.py` models. Calibrate open, short and
load at the ends of short leads.

**Steps**
1. Wheel at turn 1. Sweep 1–35 MHz, the model's range, then 27–32 MHz in 10 kHz steps.
2. A resonance shows as a sharp peak in R with X passing through zero. Note each one.
3. Repeat at turns 2 and 3, then at each band's setting from 1.1. Watch the 20 m setting, about 5–6
   turns *(inferred from the model's L per turn)*.
4. Put the stand-in deck under plate A, which sets the 1.94″ from deck to first turn (TUNER-L-109),
   and repeat steps 1–3.
5. Compare each sweep with the model: `nec/out/roller_vna_k<turn>.csv` free, `_deck.csv` on the deck.
6. *(Optional, inferred.)* Sweep all 22 positions on the model's 1–35 MHz / 0.1 MHz grid and save
   them in the same CSV form in a copy of `nec/`. `nec/roller_bands.py` then maps every band edge onto
   the real coil.

**Pass/fail**
- Item 44: with the wheel at turns 1–3, "the 28–31 MHz resonance must sit above ~30.5 MHz." If it
  lands in-band: "slimmer rib contact at the notches, or fewer idle turns".
- The log doesn't say what to do between 29.7 and 30.5 MHz. *(inferred)* Expect that case: the model
  puts the resonance at 30.1–30.2 MHz for turns 1–3, under the 30.5 MHz line before the ribs pull it
  lower. Then measure Q at 29.7 MHz at those settings (1.5) and decide on the loss. The model's figure
  is Q ≈ 185, ~11 W.
- *(inferred)* Flag any R peak within ~3 % of a band edge at the wheel position that band uses, the
  same margin as 30.5 MHz against 29.7. The first resonance at the 20 m setting sits 7–9 % above
  14.35 MHz in the model; the ribs eat into that.

**Record.** Resonance frequencies at each position, free and on the deck; shift from the model (%);
R and X at 29.7 MHz for turns 1–3.

### 1.3 Torque, end stops and stopping distance (items 24, 48)

**Purpose.** Every axis is a 23HS22-2804S, direct (§10.14, M-2). Item 24: "measure breakaway and
running torque … on the roller when built, against the motor's 0.60 N·m pull-out at 2 kHz / 24 V. If
the roller exceeds ~0.4 N·m running, slow its axis or add a 36 V motor supply." Item 48 covers the
overtravel settings: the capacitors' end-stop torque sets the driver current ceiling (§7.2 layer 4),
and the roller's stopping distance at the slow-zone speed places its inner cam (48(c)). The log gives
no end-stop torque for the roller.

**Setup.** Roller upright, plate B on, bearings as built (§5.3a), the wheel spring at its working
3–5 lb (TUNER-L-105 note 4). Torque gauge on the shaft stub, or a spring scale on a known radius
(M-2). Clamp any lever or pulley; don't drill or set-screw the shaft (§7.1a).

**Steps**
1. **Breakaway** is the peak torque to start from rest. **Running** is the steady torque while
   turning slowly. Take both, in both directions, at turns 1, 6, 11, 16 and 21, and once across a rib
   crossing *(positions inferred)*.
2. **End stop.** Turn the carriage gently onto a stop collar by hand (§7.2 layer 5). Raise the torque
   slowly, never past the motor's 1.20 N·m holding torque (M-2), and stop at the first event: the
   wheel riding out of the groove and skipping a turn, a collar slipping on the bus rod, or a rib or
   the carriage deflecting. Record the torque and what happened. *(inferred)* The helix is a screw: at
   the stop, a torque T pushes the carriage with about 2πT ÷ pitch, ~450 N (100 lbf) at 0.60 N·m on
   the 0.333″ pitch, before friction. With a groove only 0.045″ deep (§5.3a wiper note) and 0.10″ of
   radial fork travel (`cad/roller.py`), expect the wheel to ride over the wire long before that. If
   it does, that is the roller's end stop, and its driver current has to stall the motor below it.
3. **Stopping distance** (48(c)), once the motor drives the roller. Run at the slow-zone speed,
   2 rev/s (§7.2), gate STEP as the inner switch does, and measure the overrun at the shaft (encoder,
   or a pointer and a mark). Five runs each way. Repeat with EN dropped, the outer switch's case
   (§7.2 layer 3) *(inferred addition)*.
4. *(Optional, inferred.)* Measure the rotor's inertia; the log's 30 lb·in² is an estimate (§5.3a).
   Wrap a string on a known radius r, hang a mass m and time a drop of height h:
   a = 2h/t², J = r (m (g − a) r − τ_run) / a.

**Pass/fail**
- **Running ≤ ~0.4 N·m** (item 24). That keeps 1.5× under the 0.60 N·m pull-out at 2 kHz / 24 V
  (M-2). Above it, slow the roller axis or add the 36 V supply (item 24; ~0.82 N·m to 600 rpm at
  36 V, M-2).
- Breakaway: the log sets no limit. *(proposed)* Compare it with the low-speed pull-out, ~0.82 N·m at
  300 rpm (M-2), and flag anything above two-thirds of that, ~0.55 N·m: the same 1.5× margin.
- End stop: no figure in the log. Decide from step 2.
- Stopping distance shorter than the gap from the inner switch's trip to the stop collar. §7.2
  expects ~0.1 turn at 2 rev/s.

**Record.** Breakaway and running torque at each position and direction; the end-stop torque and what
gave; overrun with STEP gated and with EN dropped; inertia, if measured.

### 1.4 Contact resistance and heat at 18.4 A

**Purpose.** §5.3a: "the rotating contact decides the current rating", and "oxidation or pitting on
the wheel or its bus rod localizes into heat." For scale, 10 mΩ is ~3.4 W at 18.4 A (§5.3a). Four
moving joints carry the full current: the wheel rolling on the wire, the silver shoe on the wheel
face, the carriage's bore on the bus rod (TUNER-L-105, note 3 and the carriage table), and the BeCu
fingers on the cold-end collar (§5.3a).

The log's own heat test comes at commissioning: key-down at 100 / 300 / 600 W on 160 m (§5.3a).
*(inferred)* That test cannot reach 18.4 A. The roller current goes as √P, so 600 W gives ~11.6 A and
the SB-220's ~1,100 W (§1.3.1) ~15.8 A. Only a 1,500 W carrier makes 18.4 A. This bench test puts the
full current, and more, through the contacts now.

**Why DC or 60 Hz can stand in for RF, and where it can't** *(inferred)*
- A contact heats in a few small spots where the current converges. Their resistance, constriction
  plus surface film, is what heats it, and 18.4 A of DC drives the same current through the same
  spots. 60 Hz behaves as DC here: copper's skin depth at 60 Hz is ~0.33″, more than the #4 wire's
  radius.
- At 1.8 MHz the current runs in the outer ~0.002″ (§5.3a) and crowds toward the inside of the coil,
  while the wheel touches the outside. The current must spread around the wire through that thin
  skin to reach the wheel, so the contact likely has more resistance at RF than at DC, perhaps a few
  times more.
- DC leaves out the RF heat around the contact: the turns' own skin- and proximity-effect loss (copper
  alone is ≈ 53 W at 18.4 A in the NEC model, §5.3a, against ~2 W at DC for the same ~17 turns), the
  ribs' dielectric heating, and eddy loss in nearby metal.
- So the DC test is necessary, not sufficient. A contact that fails at DC fails at RF. A pass shows
  the contact is not the weak point at 18.4 A, and the commissioning test confirms the rest. The 26 A
  step doubles the contact heat, to cover an RF resistance up to twice the DC value.

**Setup**
- Roller upright on the free-air platform, wheel at the 160 m (1.800 MHz) setting from 1.1. Still air:
  the bay will have forced air, so this is the harder case *(inferred)*.
- Heavy leads, #4 welding cable or larger, lugged to the bus rod's hot terminal and to the deck strap.
- Kelvin taps across each joint: bus rod to carriage; carriage to braid to shoe; shoe to wheel; wheel
  to wire (a sharp probe on the wire within ¼″ of the wheel); coil end to lug to collar; collar to
  fingers to strap.
- Thermocouples under Kapton tape: the shoe and the wheel face beside it, the carriage, the bus rod at
  the carriage, the wire next to the wheel, the nearest rib notch, the collar, one finger, plate A at
  bearing A, the shaft stub where the Oldham will sit, and ambient. Bare silver and copper read far
  low on an IR thermometer; use it only on a dot of Kapton tape or flat paint *(inferred)*.

**Steps**
1. **Cold resistance.** At 5 A, read every Kelvin tap. Reverse the current and average, to cancel
   thermal EMFs *(inferred)*.
2. **Contact sweep.** At 5 A, turn the coil slowly by hand through the full travel and back, logging
   the bus-rod-to-wire voltage (min/max hold or a scope). Note where each spike falls: a rib
   crossing, a notch, a particular turn. These are the dead spots §5.3a warns about.
3. **18.4 A.** Back at the 160 m setting, log every channel and every Kelvin tap each minute until all
   have leveled off (under ~1 °C change in 5 minutes *(inferred)*).
4. **26 A.** The same.
5. Off. When cold, repeat step 1. Inspect the wheel track for discoloration or pitting.
6. *(Optional, inferred.)* If the DC result is marginal, test the contacts at RF without high
   voltage. With the wheel ~2 turns in, X is only ~10 Ω at 1.8 MHz, so 18.4 A needs only ~180 V RMS
   across it, and the current still crosses the wheel and the fingers. Resonate that section at
   1.8 MHz with about 9 nF of capacitors rated for the current. The log has no such fixture; design it
   and record what was used.

**Pass/fail**
- From the log: "Ribs must stay cool to the touch; any warm rib means dielectric heating" (§5.3a).
  That line is for the RF test. At DC there is no dielectric heating, so a warm rib here means heat
  conducted from the wire *(inferred)*.
- The log sets no temperature or resistance limit for the contacts. Decide them before the run.
  *(proposed)*:
  - Every channel levels off at both currents.
  - Each rise at 26 A is no more than about 2× its rise at 18.4 A. 2× is plain I²R; more means the
    resistance climbs with temperature, which is how runaway starts.
  - Every joint reads within ~10 % of its cold value after the run, and none drifts up during it.
  - No spike in the sweep above about 2× the baseline.
  - The hottest contact rises no more than ~40 °C at 18.4 A, leaving room for the RF heat that DC
    can't show. Check that against the datasheet ratings of the RTV, the bearing grease and the BeCu
    finger stock; the log gives only Ultem's ~170 °C (§5.3a materials table).

**Record.** Each joint's resistance, cold and after; each sweep spike, its size and where; every
channel's temperature against time at 18.4 A and 26 A; the joints' resistance against time; photos of
the track.

### 1.5 Q at the frequencies that matter (item 12)

**Purpose.** The roller loses I²·ωL/Q. The match fixes I and L, so the loss goes as 1/Q, and the
continuous limit, the 200 W budget divided by the loss per watt, goes as Q. §1.7 brackets it: Q = 250
("clean contact") loses **342 W** at 1500 W on 160 m, 1.800 MHz; Q = 150 ("realistic with contact
resistance") loses **569 W**. The §1.7.1 limits use Q = 150. 250 ÷ 150 = 1.67, the "1.7×" of item 12.
*(inferred)* The input choke's ~10 W on 160 m (§6) doesn't scale with Q, so with it the swing is
~1.6×. §5.3a sets the spec: "Q ≥ 300 at 1.8 MHz, measured installed in the bay (not on the bench)".
The bench figure is the early read that the decision in section 5 needs.

**Settings** (from §1.7 and `nec/cap_demand_rev37b.out`; the C2 setting to resonate is *(inferred)*
from 1/(ω²L)):

| f (MHz) | L in use | Roller current at 1500 W | Why it matters | C2 to resonate |
|--:|--:|--:|:--|--:|
| 1.800 | 22.2 µH | 18.4 A | The derate's worst point (§1.7.1) | ~352 pF |
| 1.900 | 16.6 µH | 17.3 A | Middle 160 m segment | ~423 pF |
| 2.000 | 11.7 µH | 16.2 A | Top 160 m segment | ~541 pF |
| 3.500 | 21.4 µH | 5.9 A | 80 m, the next-largest loss | ~97 pF |
| 4.000 | 12.9 µH | 8.0 A | The worst RF-bay total off 160 m, 166 W (§1.7.1) | ~123 pF |
| 5.332 | 2.2 µH | 10.1 A | 60 m: high current on few turns | ~405 pF |
| 28.000 | 0.7 µH | 7.7 A | 10 m, next to the idle-turn resonance | ~46 pF |
| 29.700 | turns 1 and 2 | — | Item 44's modeled Q ≈ 185 | ~103 / ~34 pF |

All lie inside C2's 20–675 pF. Turn 3 at 29.7 MHz would need less than C2's 20 pF minimum.

**Setup**
- Wheel at the setting by the LCR reading. Within a turn is close enough for Q *(inferred)*.
- C2 from bus rod to cold terminal on the shortest, widest copper straps you can make. Their loss
  counts against the roller.
- Couple each VNA port to the bus rod through a small capacitor of a few pF, with the port grounds on
  the cold terminal. Keep it loose: S21 at resonance −30 dB or lower *(inferred: standard
  weak-coupling practice)*.
- Don't read Q from S11 across the roller. At 1.8 MHz, Q = 250 is ~1 Ω against 251 Ω of reactance, a
  return loss of ~0.01 dB, finer than a VNA resolves *(inferred)*.

**Steps**
1. Sweep S21 across the resonance: a span of about five bandwidths (at Q = 250 the bandwidth is
   7.2 kHz at 1.800 MHz), in fine steps.
2. Read f₀, the 3 dB bandwidth and |S21| at f₀ as a linear ratio. Loaded Q_L = f₀ ÷ bandwidth;
   unloaded Q_u = Q_L ÷ (1 − |S21|) *(inferred: standard)*. At −30 dB the correction is 3 %.
3. Every setting in free air. Then the 1.800 MHz setting again with the stand-in deck under plate A.
4. The 1.800 MHz setting again within a few minutes of the 18.4 A run (1.4), with the contact still
   warm *(inferred: shows whether heat moves Q)*.

**Pass/fail**
- The spec is installed: **Q ≥ 300 at 1.8 MHz**, in the bay with the RF service panel on (§5.3a,
  item 12). The deck costs ≈ 3–5 % of Q and the top panel ≈ 1 % (item 32), so on the bench look for
  **≥ ~320 in free air** *(inferred)*.
- **Q ≥ 250** meets the §1.7 clean-contact case. **Below 250**, take the result to section 5 (review
  item 9). **Below 150**, the §1.7.1 table itself is optimistic.
- The stand-in deck should cost 3–5 % (item 32). If it costs more, raise the roller on about 1″ of
  insulating spacer under plate A (item 32).
- The other bands have no Q spec. §1.7 uses the same Q on every band *(inferred from its table)*, so
  flag any setting under 150.
- *(inferred)* Compare with the model's copper-only Q at each setting (`nec/out/roller_vna_k*.csv`;
  ≈ 1,600 at 1.800 MHz, §5.3a). The gap is what the model leaves out: the contact, the ribs, the
  proximity effect and nearby metal.

**Record.** f₀, bandwidth, |S21| and Q_u at each setting, free and on the deck; Q after the heat run;
the straps and coupling capacitors used.

**Later, installed.** The §5.3a key-down heat test (100 / 300 / 600 W on 160 m; the wheel contact,
ribs, notches, finger contact and collar) and the installed Q (item 12) close section 1. Use the same
thermocouple points as 1.4, so the rise per A² at RF compares directly with the DC run *(inferred)*.

## 2. K1 coax relay at full power (item 34)

**Purpose.** K1 and K2 are Tohtsu CX600N-24 relays: SPDT, N, 24 V coil, no auxiliary contacts (§5.5,
§10.3). Item 34: "K1 is published at 1 kW CW at 50 MHz only, against 1.5 kW CW here". The Rev 3.7c
search found no HF CW figure anywhere, "So the commissioning temperature test stands as the way to
close this." At 1.5 kW in 50 Ω the relay carries ~5.5 A at ~274 V RMS (§6B.1). *(inferred)* It
belongs before the enclosure because item 34's fallbacks (a factory-order Dow-Key 402A-280132 or
Ducommun 2NH6C31, or an open-frame Gigavac GH1 vacuum SPDT) are different parts to fit in the
5.00″ × 5.00″ × 15.87″ sampler chamber (§6B.5).

**Which contacts carry full power** (§6B.1, §6B.2):

| Path | Energized | RF route |
|:--|:--|:--|
| TUNE (normal) | nothing | K1 COM → NC → choke |
| AUX | K1 | K1 COM → NO → K2 COM → K2 NC → rear N |

Item 34 used to say "K2 never carries more than 60 W". That holds for CAL, but in AUX the full power
passes K2's NC contact, and AUX is for "an external full-power dummy load" (§6B.2). The log now says
so (2026-11-22), and both paths get the test.

**Equipment.** K1 and K2; a 24 V supply for the coils; N jumpers of RG-393, the harness coax
(§10.11); the SB-220, or a 1.5 kW amplifier if one can be borrowed; a directional wattmeter; a dummy
load rated for the test power for at least 10 minutes (check its duty rating); a VNA with a 50 Ω load
standard; thermocouples and a logger; an IR thermometer with tape dots; a DMM for coil resistance.

**Setup**
- Mount the relays on a scrap aluminum plate, in still air. The sampler chamber is sealed (§8E) and
  has no airflow *(inferred)*. A loose cover approximates it.
- Thermocouples on each relay body near each port, on each N connector body, on each jumper's jacket
  1″ from its connector, and one for ambient.
- Coil resistance of K1 and K2, cold, at a known room temperature.
- VNA: return loss of each path into the 50 Ω standard, against a plain N barrel, at 1.8, 3.5, 7, 14,
  21, 28 and 29.7 MHz *(inferred list)*.

**Steps**
1. **Run A, TUNE path.** K1 off; RF into COM; the load on NC. 28.0 MHz *(inferred: a relay's losses
   rise with frequency, so the top band is the worst; item 49's choke test uses the same frequency)*.
   The highest power available up to 1,500 W, key-down for 10 minutes (item 34).
2. Log the temperatures each minute, and forward and reflected power at 0, 5 and 10 minutes.
3. Unkey. Within 30 s read K1's coil resistance and spot-check with the IR thermometer. Copper's
   resistance rises 0.39 % per °C, so the change gives the temperature inside the relay, beside the
   contacts, where no probe reaches *(inferred: the resistance method)*.
4. Let everything cool to ambient. **Run B, AUX path:** K1 energized, K2 off; RF through K1 NO and
   K2 NC to the load. Repeat steps 2–3, reading both coils. K1's own coil heat adds here.
5. If the amplifier can't make 1,500 W, repeat one run at about half the power. *(inferred)* Contact
   and conductor loss go as I², and dielectric loss as V²; both are proportional to power. If the rise
   per watt matches at both powers, scale it linearly to 1,500 W.
6. VNA again once cool. Inspect the connectors and the jumpers' dielectric.

**Pass/fail.** The log names the test but no number. Decide before the run. *(proposed)*:
- Every temperature levels off within the 10 minutes.
- Reflected power at 10 minutes matches the start, and the cold return loss afterward matches before.
  If reflected power moves, check whether a wattmeter between the relay and the load moves too; then
  it is the load warming, not the relay.
- The hottest rise, scaled to 1,500 W, plus the warmest the utility layer may run (below ~60 °C with
  200 W in the RF bay, §8, item 30(a)) stays inside Tohtsu's rated operating temperature. The log
  doesn't carry that rating; look it up and record its source.
- No discoloration or softened PTFE. Both relays still switch, and the coil current reads normal (the
  control board senses it, §5.5).

If K1 fails, item 34's options stand: a rating confirmed by Tohtsu, a factory-order high-power relay
(Dow-Key 402A-280132, Ducommun 2NH6C31), or an open-frame vacuum SPDT (Gigavac GH1) as K1. If K2
fails in run B, AUX needs a power limit or the same upgrade *(inferred)*.

**Record.** Power, frequency and minutes for each run; temperatures each minute; coil resistance cold
and hot, and the temperature each implies; reflected power at 0, 5 and 10 minutes; return loss before
and after; the extrapolation, if used; Tohtsu's rated temperature range and where it came from.

## 3. AD8302 phase-sign probe (§6A.7)

**Purpose.** "The AD8302 reports phase magnitude only, 0–180°. It cannot distinguish +θ from −θ"
(§6A.7, verified: 91 + j65 Ω and 91 − j65 Ω give identical outputs). The log's options, in order:
(1) probe-and-observe, nudging C2 by a small known step and re-reading; (2) a stored band prior,
confirmed by (1); (3) an I/Q demodulator in place of the AD8302, "only if 1 and 2 prove inadequate".
The firmware settled the method (§8B.6): a stored prior decides only when one hypothesis is clearly
nearer it, once per tune; otherwise a 10 % C2 probe decides (`probe_step = 0.10`), and every VERIFY
repeats the test. The host tests prove that logic against a model. The bench proves it on the real
sensor, before option 3 would mean a different measurement board. Option 2 needs the real antenna, so
it is checked in service.

**Equipment**
- The coupler box (§10.3, item 53) and the measurement board (§10.4), joined by the two RG-316
  jumpers cut to one length. +5 V into J4 pin 15, grounds on the even pins. DMMs on J4 pin 1 (V_MAG),
  pin 3 (V_PHS) and pin 9 (AD_VREF, which the firmware reads against, §8B.6); the pinout is in
  `kicad/board_measurement.py`.
- A transceiver at 2–10 W. The vector path has its full ratio range from ~2 W (§6A.5).
- A VNA; open, short and 50 Ω standards; a resistive standard of known |Γ| (100 Ω or 25 Ω,
  |Γ| = 1/3).
- The test loads below.
- For 3b, a low-power bench T from parts in hand: C2; the KP1-4 spare as C1; the Harris spare roller
  (§5.3) if it still turns, or any coil of known value. At 10 W none of them is stressed.

**Reference plane.** The AD8302 measures Γ at the coupler. A jumper between the coupler and the load
rotates the phase, the same problem item 36 raises for CAL. Measure every load, and every bench-T
input, with the VNA at the coupler's output connector, through the jumper the test uses.

**Test loads** *(inferred: the log's own §6A.7 pair, and the model's tuner-end loads at 160 m
1.800 MHz and 10 m 28.000 MHz from `nec/cap_demand_rev37b.out`, each with its mirror)*. Build each
from a non-inductive resistor (carbon composition or metal film, never wirewound, as §6A.3 says of
the terminations) in series with a C0G or mica capacitor or an air-wound coil, on a short connector.
The VNA's reading at the test frequency, not the nominal value, is the known impedance.

| f (MHz) | Pair | Build as | Expected V_MAG / V_PHS, either of the pair (§6A.6, before calibration) |
|--:|:--|:--|:--|
| 7.15 | 91 ± j65 Ω | 91 Ω + 1.45 µH / 343 pF | 0.717 / 1.470 V (§6A.7) |
| 1.800 | 8.9 ± j226 Ω | 8.9 Ω + 20.0 µH / 391 pF | 0.896 / 1.551 V |
| 28.000 | 175 ± j276 Ω | 175 Ω + 1.57 µH / 20.6 pF | 0.858 / 1.652 V |
| any | 100 Ω, 25 Ω | resistor | 0.614 V; 1.800 / 0 V. The sign doesn't matter |

### 3a Sensor check: loads on the coupler

**Steps**
1. Calibrate each band as §6A.8 and §8B.6 describe. The open and short give the 0 dB point and the 0°
   and 180° ends, the 50 Ω load the directivity floor, and the resistive standard the dB slope.
   Record every reading.
2. On each load take five readings of V_MAG and V_PHS, re-seating the load between them
   *(inferred)*.
3. Convert with the calibration and compare |Γ| and |θ| with the VNA's.

**Pass/fail**
- The residual is within **±0.25 dB and ±2°** (item 54(b); §8B.6's tested envelope).
- Each mirror pair reads the same within the scatter (§6A.7). If a pair differs, something besides
  the load sets the phase, such as the reference plane or the directivity; find it before 3b
  *(inferred)*.
- The scatter of the five readings is the smallest change the probe can trust. Record it.

### 3b The probe in a bench T, by hand

**Setup.** The bench T between the coupler and a load, at 2–10 W. Loads *(inferred, from
`nec/cap_demand_rev37b.out`)*: 8.9 − j226 Ω at 1.800 MHz, 112 + j185 Ω at 14.000 MHz and
175 − j276 Ω at 28.000 MHz: two capacitive and one inductive, across 160, 20 and 10 m. Solve the T
for each with `nec/tnet.py` inside the stand-ins' ranges and set it. Measure each element at its
setting; the firmware is tested to ±3 % (item 54(a)).

**Steps**
1. Mistune C1, up and then down, until the SWR is about 2–4:1; the firmware refines only from
   readings under 5:1 (`trust_swr`). *(inferred)* C1 is the series element
   at the input, so Z_in stays near 50 Ω resistive and only its reactance changes sign: C1 up makes it
   inductive, C1 down capacitive. The VNA confirms which.
2. With the coupler back in line, read V_MAG and V_PHS. Step C2 by 10 % as the firmware does (up, or
   down if up would pass the end of its range; `start_probe()` in `fw/core/src/fsm.cpp`), read again,
   and step back. Measure C2 at both settings.
3. Decide the sign as `resolve_sign()` does: for each sign of the first reading, de-embed the load
   through the measured network, predict the second reading, and keep the hypothesis whose prediction
   lands nearer. The same arithmetic in Python on the `nec/tnet.py` equations will do *(inferred)*.
4. Three times for each load and each mistune *(inferred)*.

**Pass/fail**
- The probe's sign matches the VNA's in every case where the sign matters: 2|Γ| sin θ ≥ 0.05 (the
  firmware's `kSignMatters`). Below that the sign makes no difference, and the firmware takes +.
- *(proposed)* The two hypotheses' predictions differ by at least 3× the 3a scatter. A band where
  they don't is where option 3, the I/Q demodulator, would earn its place (§6A.7).

### 3c The firmware's probe, at bring-up

When the control board, motors and firmware run, repeat 3b's loads with the firmware's own PROBE
(§8B.6) and the stored priors cleared, so the probe decides. Pass: every tune converges to 1.2:1
within its three attempts (§8B.6), and no attempt moves the wrong way. Then load the priors and
confirm that a wrong one costs a single attempt (§8B.6).

**Record.** Each band's calibration readings; each load's VNA impedance and five readings; the
residuals; each mirror pair's difference; for 3b, the VNA sign, both readings, both C2 values, the
chosen sign and the gap between the predictions; for 3c, attempts per tune.

## 4. Vacuum capacitors (item 26)

The procedure, pass/fail criteria and test log are in
[vacuum-cap-testing.md](vacuum-cap-testing.md): mechanical inspection, lead-screw cleaning and
re-grease, capacitance and insulation sweep, glow test (glass envelopes only), DC hi-pot at minimum
and maximum mesh, then the on-air test. The UCSX-740-10 (C2) is used and untested, and C1 may be
bought used (§5.1b). Run its sections 1–4 on the bench now. Its section 5, on the air, waits for the
built tuner.

Hi-pot targets (§5.1b): **C1 (15 kV-class) ~10 kV**, 1.5× the 6.54 kV worst case and under its 15 kV
test rating; **C2 (UCSX-740-10) 6 kV**, its working rating, 2.5× the 2.40 kV duty. For the stress,
use that document's bullets (6.54 / 2.40 kV peak, §5.1), not its Rev 3.3 table (6,102 / 4,170 V).

Measure on C2 now, and on C1 when bought, for the drive:
- **Turns stop to stop** (item 48(b)). It sets the module reduction, ≥ (turns + 2):1 (§7.1), and the
  move times; 30 is assumed (§8B.3a). The cap document logs it as "Turns end to end".
- **Breakaway and running torque, separately** (item 24), after the re-grease, at several points
  through the travel. The cap document records only the peak. Pass: under the 0.4 N·m that §3.1 and
  M-2 size the drive for, which is 1.5× under the 0.60 N·m pull-out at 2 kHz / 24 V. Use the
  existing flat or a clamp; never drill the Jennings shaft (§7.1a).
- **End-stop torque** (item 48(a)): from Jennings data, or "a careful spring-scale test on C2". It
  sets the driver current ceiling (§7.2 layer 4). *(inferred)* Careful means choosing first the stall
  torque the driver will be allowed, then confirming the stop holds that much: approach slowly, raise
  the torque in small steps up to that figure and no further, then repeat the cap document's
  mechanical and capacitance checks, and the glow test on glass. Never test to failure: over-travel
  can tear the bellows (cap document, section 1).

**Record.** The cap document's test log for each cap, plus turns, breakaway and running torque, and
the end-stop torque held.

## 5. Decision: more 160 m headroom if Q < 250

**Where the log stands.** With the input choke's heat in the RF bay's 200 W budget, the 160 m
continuous limits are **≈ 502 / 600 / 882 W** for 1.800–1.850 / 1.850–1.950 / 1.950–2.000 MHz
(§1.7.1, Rev 3.7c). They assume Q = 150, and Q swings them by about 1.7× (item 12). The firmware warns
above them and never cuts PTT (§1.7.1, §8B.6).

**The case.** Review item 9 asks for more 160 m headroom if Q comes in under 250. It puts FT8 at full
SB-220 power on 1.84 MHz at about **550 W** average: ~1,100 W (§1.3.1) half the time. That is ~10 %
over the 502 W limit of its segment, and the firmware warns, since `fw/core/src/derate.cpp` rates the
whole segment at its 1.800 MHz worst point. *(inferred)* Two things make 550 W the conservative
figure. FT8 sends 12.6 s in each 15 s slot, so one slot in two averages nearer 460 W. And 1.84 MHz
itself loses less than 1.800 MHz: interpolating §1.7's losses puts its own limit near 570 W.

**What Q buys** *(inferred: computed from the §1.7 losses and `nec/out/choke_screen_rev37c.txt`,
taking the measured Q to hold at each segment's worst point)*:

| Roller Q | 1.800–1.850 MHz | 1.850–1.950 MHz | 1.950–2.000 MHz | Note |
|--:|--:|--:|--:|:--|
| 100 | ~340 W | ~405 W | ~600 W | |
| 150 | 502 W | 600 W | 882 W | §1.7.1 as written |
| ~165 | ~550 W | ~655 W | ~965 W | FT8 at full SB-220 fits |
| 200 | ~660 W | ~790 W | ~1,155 W | |
| 250 | ~810 W | ~970 W | ~1,415 W | §1.7 clean-contact case |
| 300 | ~960 W | ~1,145 W | no derate | §5.3a spec |
| ~350 | ~1,100 W | ~1,315 W | no derate | SB-220 key-down fits |

**The options, in order**, and the test 1 result that points to each:

| Option | Points here when test 1 shows | Cost and catch |
|:--|:--|:--|
| 1. More airflow, or an RF-bay budget above 200 W | Q between ~150 and 250 with the heat spread out: contacts stable and cool (1.4), ribs cool, Q no different warm or after cleaning (1.5). *(inferred)* FT8 at 550 W needs only ~219 W of budget at Q = 150, 10 % more | Blower and intake work (§8), then the item 30(a) run again: shelf and utility layer below ~60 °C. §8 chose the derate over more air for this one segment, so this reverses a logged choice |
| 2. Better wheel contact and plating | A joint that reads high, drifts up when hot, rises more than 2× at 26 A, or has dead spots (1.4); or Q that rises when the track is cleaned, or falls when warm (1.5) | Re-plate, a stronger spring, a wider shoe (§5.3a contact system; item 2). *(inferred)* A contact can't explain Q = 150 alone: the extra ~0.67 Ω between Q 250 and 150 would put ~227 W in one spot at 18.4 A. So contact work cures hot spots more than it raises Q. Record the plating method and thickness; the log gives neither |
| 3. A fixed high-Q 160 m inductor | Q well under 250 at 1.8 MHz with clean, cool contacts, cool ribs and a deck loss inside item 32's 3–5 %: the loss is in the coil itself (proximity effect, the form, the idle turns) | It brings back what Rev 3.7b deleted: a vacuum relay in the tank and a deck position for a coil (§5.4, §11.6, item 42). The last resort |

Two results point elsewhere, to the log's own fixes. A deck loss well over 3–5 % calls for the ~1″
insulating spacer (item 32). Warm ribs mean dielectric heating (§5.3a); item 44's "slimmer rib contact
at the notches" is the nearest remedy *(inferred)*.

**After deciding.** Decide on the bench Q and confirm with the installed Q (item 12). *(inferred)*
The firmware holds 502 / 600 / 882 W as constants (`fw/core/src/derate.cpp`), and the log doesn't say
how a measured Q reaches them. Rescale them, and §1.7.1, from the installed Q.

**Record.** The Q used, the option chosen and why, and the new limits.

## 6. Order and results

### Order

Cheapest and most informative first. Times are rough bench time, not waiting for parts. The roller
build is the long pole, so start it first and run the C2, K1 and sensor tests while it is made
*(inferred)*.

| # | Test | Needs | Time | Why here |
|--:|:--|:--|:--|:--|
| 1 | 4: C2 per the cap document's sections 1–4, turns, torque | C2 (in hand), insulation tester, hi-pot (borrow) | 1 day | In hand now. A soft C2 changes the parts plan, and 1.5 and 3b use C2 |
| 2 | 2: K1 and K2, both paths | The relays, the SB-220, a dummy load | ½ day | Settles the relay before the sampler chamber is cut |
| 3 | 3a: sensor check | Coupler box, measurement board, loads | ½ day | Option 3 would change the measurement board |
| 4 | 1.1–1.2: L and idle-turn sweep | Wound helix, LCR, VNA | 3 h | Before the turns are locked (item 44); may change the winding |
| 5 | 1.3 steps 1–2: torque by hand, end stop | Assembled roller, gauge | 2 h | Feeds item 24 |
| 6 | 1.4 steps 1–2: cold resistance, contact sweep | 5 A supply, DMM | 2 h | Finds dead spots before Q is measured |
| 7 | 1.5: Q, free and on the deck | C2, VNA, deck plate | ½ day | The number that sets the 160 m limits |
| 8 | 1.4 steps 3–5: 18.4 A and 26 A | 26 A supply, thermocouples | 1 day | |
| 9 | 1.5 step 4: Q warm | | 1 h | Right after 8 |
| 10 | 5: decision | Results of 6–9 | 1 h | |
| 11 | 3b: probe in a bench T | Spares in hand, loads | 1 day | |
| 12 | 1.3 steps 3–4 with the motor; 3c | Motor, driver, control board, firmware | ½ day each | At bring-up |
| 13 | 4: C1 | C1 (to buy) | 1 day | When bought |

### What the log leaves to decide

- The roller contacts' temperature-rise and resistance limits (1.4). The log has only "ribs cool to
  the touch".
- The roller's end-stop torque (1.3). Item 48 covers the capacitors' end-stop torque and the roller's
  stopping distance only.
- K1's temperature limit, and Tohtsu's rated operating temperature (2). And a 1.5 kW source: the
  SB-220 makes ~1,000–1,200 W (§1.3.1).
- *Settled 2026-11-22:* a 10 m idle-turn resonance between 29.7 and 30.5 MHz is acceptable, with a
  feel of the idle turns after a 29.7 MHz key-down; below 29.7 MHz it is fixed (item 44).
- *Settled 2026-11-22:* the acceptance is ≥ 26 µH installed, and the spare turns are wound only below
  it (§5.3a), since they pull the idle-turn resonance down.
- *Recorded 2026-11-22 as item 58:* a measured Q goes back into §1.7.1 and `fw/core/src/derate.cpp`.

### Results log

| Test | Quantity | Criterion (source) | Value | Pass? | Date |
|:--|:--|:--|:--|:--|:--|
| 1.1 | Contact surfaces inspected and cleaned; photos | Clean, unpitted (item 2) | | | |
| 1.1 | L end to end, free air (µH) | ≈ 24 free air for 23.1 installed (item 47) *(inferred)*; built 34 (§5.3a) | | | |
| 1.1 | L at turns 1 / 2 / 3 (µH) | ≤ 0.46 reachable (§5.3a) | | | |
| 1.1 | Turn at each 1.5 setting | — | | | |
| 1.2 | 28–31 MHz resonance, turns 1 / 2 / 3, free / deck (MHz) | > ~30.5 (item 44) | | | |
| 1.2 | First resonance at the 20 m setting (MHz), margin over 14.35 MHz | ≥ ~3 % *(proposed)* | | | |
| 1.2 | Shift from the model (%) | — | | | |
| 1.3 | Breakaway, worst position and direction (N·m) | ≤ ~0.55 *(proposed)* | | | |
| 1.3 | Running, worst (N·m) | ≤ ~0.4 (item 24) | | | |
| 1.3 | End stop: torque at the first event (N·m), and the event | Decide | | | |
| 1.3 | Overrun at 2 rev/s, STEP gated / EN dropped (turns) | Under the switch-to-collar gap; ~0.1 expected (§7.2) | | | |
| 1.3 | Rotor inertia, if measured (lb·in²) | 30 estimated (§5.3a) | | | |
| 1.4 | Cold resistance per joint (mΩ) | Decide | | | |
| 1.4 | Worst sweep spike (× baseline) and where | ≤ ~2× *(proposed)* | | | |
| 1.4 | Hottest rise at 18.4 A (°C), where; leveled off? | ≤ ~40 °C, levels off *(proposed)* | | | |
| 1.4 | Rise at 26 A ÷ rise at 18.4 A | ≤ ~2 *(proposed)* | | | |
| 1.4 | Joints after the run against before (%) | Within ~10 % *(proposed)* | | | |
| 1.4 | Ribs | Cool (§5.3a) | | | |
| 1.5 | Q_u at 1.800 MHz, free air | ≥ ~320 *(inferred)*; 250 and 150 decide section 5 | | | |
| 1.5 | Q_u at 1.800 MHz on the deck; change (%) | 3–5 % (item 32) | | | |
| 1.5 | Q_u at 1.900 / 2.000 / 3.500 / 4.000 / 5.332 / 28.000 MHz | ≥ 150 *(inferred)* | | | |
| 1.5 | Q_u at 29.700 MHz, turns 1 / 2 | Model ≈ 185 (item 44) | | | |
| 1.5 | Q_u at 1.800 MHz, warm after 1.4 | — | | | |
| 2 | Return loss, TUNE / AUX paths, cold, before / after (dB, worst band) | Unchanged *(proposed)* | | | |
| 2 | Run A (TUNE): W, MHz, min; hottest rise (°C), where; leveled off? | 1.5 kW for 10 min (item 34); levels off *(proposed)* | | | |
| 2 | Run B (AUX): the same | The same | | | |
| 2 | Coil resistance cold / hot (Ω) and implied °C, K1 / K2 | — | | | |
| 2 | Reflected power at 0 / 5 / 10 min (W) | Steady *(proposed)* | | | |
| 2 | Rise scaled to 1,500 W, plus 60 °C, against Tohtsu's rating (and its source) | Inside the rating *(proposed)* | | | |
| 3a | Calibration readings per band | — | | | |
| 3a | Worst residual (dB, °) | ±0.25 dB, ±2° (item 54(b)) | | | |
| 3a | Mirror pairs read alike? | Yes (§6A.7) | | | |
| 3a | Scatter of five readings (mV) | — | | | |
| 3b | Right sign, of the cases where the sign matters | All | | | |
| 3b | Smallest prediction gap ÷ 3a scatter | ≥ 3 *(proposed)* | | | |
| 3c | Tunes converged, attempts each; wrong-way moves | 1.2:1 within 3 attempts; none (§8B.6) | | | |
| 4 | C2: the cap document's verdict | Its guide; hi-pot 6 kV (§5.1b) | | | |
| 4 | C2: turns; breakaway / running (N·m); end-stop torque held (N·m) | 30 assumed (§8B.3a); ≤ 0.4 (§3.1, item 24); decide (item 48) | | | |
| 4 | C1: the same | Hi-pot ~10 kV (§5.1b) | | | |
| 5 | Q used; option chosen; new 160 m limits; §1.7.1 and firmware updated? | — | | | |
