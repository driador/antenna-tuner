# Tuner firmware

Firmware for the Teensy 4.1 on the control board (design log §8B), in two layers:

- **The portable core** (`core/`) is the tuning logic plus every piece of the hardware handling that
  does no I/O. It is plain C++17 with no Arduino, heap, exceptions or RTTI, and it is tested on the
  build host, the state machine in closed loop against a model of the tuner.
- **The Teensy layer** (`teensy/`) reads the hardware into `Inputs` every 10 ms, steps the state
  machine, and carries out its `Outputs`. It builds with PlatformIO but has not run on hardware yet;
  the boards are not built.

```
fw/
  core/include/tuner/   the portable core: headers
  core/src/             ...and sources; seed_priors.inc and roller_model.inc are generated
  teensy/               the Teensy layer; config.hpp holds every hardware constant
  test/                 host tests (own harness, no framework); tnet_vectors.inc is generated
  tools/gen_tables.py   regenerates the .inc files from nec/cap_demand.py and the NEC roller sweep
  CMakeLists.txt        host build;  platformio.ini  Teensy build
```

## Build and test

```sh
cmake -S fw -B fw/build                     # host: the core and its tests
cmake --build fw/build -j
ctest --test-dir fw/build --output-on-failure

cd fw && pio run                            # Teensy 4.1 (PlatformIO fetches PJRC's toolchain once)
pio run -t upload                           # cut the Teensy's VUSB-VIN pad first (§8B.0.3)
pio device monitor                          # the USB console
```

The Teensy build is about 92 KB of code and 46 KB of RAM1 (of 7.75 MB and 512 KB).

`fw/build/compile_commands.json` is picked up by clangd. `TRACE_MHZ=1.8 fw/build/test_fsm` prints
every state change for the 1.8 MHz sweep cases, and `TRACE_CASE=n` does the same for one Monte Carlo
draw.

After a change to the NEC model or `cap_demand.py`, regenerate the tables and rerun the tests:

```sh
python3 fw/tools/gen_tables.py
```

## What maps to what

| Module | Does | Log |
|:--|:--|:--|
| `tnet` | Closed-form T solution (lowest roller current, or the nearest within 3 %), the network's input impedance, and de-embedding: the load from what the bridge reads at the input | §5.1, §6A.9, §8B.3a |
| `bridge` | AD8302 voltages ↔ \|Γ\| and \|θ\|, Γ ↔ Z | §6A.5–§6A.7 |
| `freq` | The ÷1024 count → MHz, bands, the ±0.5 % validity window, 1 % profile segments | §6A.10, §8B.0.1, §8B.2 |
| `faults` | Classes A/B/C, the COMMISSIONING/STRICT/PERMISSIVE policy, what survives a power cycle | §8B.4–§8B.4b |
| `fsm` | The state machine, the sign of θ, PTT and move sequencing | §8B.1–§8B.3 |
| `seed` | Factory priors per segment from the NEC model | §6A.7 option 2, §7.6 |
| `pins` | The Teensy pin map, from `kicad/board_control.py` `PINMAP` | §8B.0.4 |
| `as5048` | AS5048A frames: commands with parity, replies, diagnostics | §7.1 |
| `curve` | Element calibration (turns → F or H); the roller's default is the NEC model | §7.1, §9 item 54 |
| `motion` | The coordinated move: every axis on one straight line in step space, speed and acceleration per axis, the roller's slow zone, a ramp-down when stopped | §7.2, §8B.3, §8B.3a |
| `sense` | The steady-carrier test, the tank NTC, over-temperature hysteresis | §6A.10, §8B.4a |
| `cal` | The bridge's calibration per band from open, short and load, with an optional slope standard | §6A.8 |
| `path` | TUNE / AUX / CAL: the vote held while K1 and K2 change, coil currents and the first key-down checked | §5.5, §6B.2 |
| `panel` | Every panel screen, drawn as text, with the scroll-to-confirm rule for class C | §7.5, §8B.4f |
| `panel_io` | The encoders' quadrature and the Nextion's serial protocol | §7.5 |

`test_tnet` matches `nec/cap_demand.py` at all 29 band-edge points to 1e-9. `test_bridge` reproduces
the §6A.6 round trips and the §6A.7 example (91 ± j65 Ω → 0.717 V, 1.470 V).

## The Teensy layer

| File | Does |
|:--|:--|
| `main.cpp` | The §8B.4b boot sequence: safe outputs, the recovery button, the watchdog before the permit can rise, the self-test, the restored fault record and priors. Then the 10 ms tick and the console |
| `board.*` | The direct pins: MCU_PERMIT and its read-back, DRV_EN, the relay commands (held in TUNE), the blower PWM and tach, LIM1–6, RTWDOG |
| `motion.*` | Encoders over SPI, the 50 kHz step interrupt running a planned move, drivers on only while moving, the encoder check after every move |
| `sensors.*` | V_MAG and V_PHS averaged over each 200 ms counter gate and read against the AD8302's VREF, the carrier test, the MCP23017, the tank thermistor |
| `persist.*` | Two EEPROM records with their own CRCs, packed so that only changed bytes are rewritten. The authoritative one (faults, mode, calibration) is kept twice and written alternately, so a power loss mid-write leaves the older copy good. The other holds the priors and last positions |
| `calib.*` | The calibration procedure below |
| `panel_hw.*` | The Nextion on Serial8 (only changed rows are sent), the knobs and their pushes from the MCP23017 |

**USB console:** the box's local interface, with the panel (§8B.4f):

| Command | Does |
|:--|:--|
| `status` | One status line. One also prints every second |
| `ack` | Acknowledge class B faults |
| `clear` | Local clear of class B and C faults |
| `tune` | Start a tune |
| `mode commissioning\|strict` | Set the fault policy. PERMISSIVE is refused until the §8B.4a-1 qualification counters exist |
| `path tune\|aux\|cal` | Change the RF path |
| `cal load\|open\|short\|save` | The calibration steps (below) |
| `cal watts <W>` | Add a forward-power point at the wattmeter reading W |
| `jog c1\|c2\|l <turns>` | Move one element |

**Calibrating a band** (§6A.8), from the console or the panel's Calibrate screen. Key a steady
carrier of about 10 W on the band for each step; each averages five gates.

1. `path cal`, then `cal load`. This is the internal 50 Ω load, and it sets the floor.
2. `path aux`, an open on the rear N jack, then `cal open`.
3. A short there, then `cal short`.
4. `cal save` computes the band and stores it. It refuses standards that disagree and says why.
5. For the power readout: in AUX into a dummy load, or in CAL up to 50 W, run `cal watts <W>` at each
   drive level, giving what a wattmeter reads. Up to eight points a band.

The AD8302 reports only |θ| (§6A.7), so a complex one-port correction cannot be fitted. The
calibration is the part's scalar transfer: the 0 dB point and the 0°/180° phase ends from the open
and short, and the floor from the load. Keep the K1-to-network and K1-to-AUX runs the same electrical
length (§6B.3), or the phase is off by the difference.

**The panel's HMI.** The Nextion is a terminal, and every screen is drawn by `tuner::Panel`. Build the
HMI once in the Nextion Editor for the NX4832K035:

- **Page and rows:** page 0 (`page0`), landscape 480 × 320, with ten text components `t0` to `t9`.
  Each is 480 × 32 at y = 0, 32, … 288.
- **Font:** generate a monospace font (for example DejaVu Sans Mono) at 24 px height, ASCII.
- **Each row:** `txt_maxl` 40, left-aligned and vertically centered, white text (`pco` 65535) on
  black (`bco` 0), no word wrap.
- **Startup:** in `program.s`, put `baud=115200` before `page 0`.

The left knob moves and opens; its push confirms. The right knob jogs on the Jog screen; its push goes
back. A class C clear needs the fault list scrolled to the end before Confirm appears.

**Before first power-up, set `teensy/config.hpp`.** Each ASSUMED there is a fact about the build:

- **Drivers:** the DM542T microstep setting (8 assumed), and the DRV_EN polarity, which waits on the
  motor-chamber driver board.
- **Axes:** each axis's direction and encoder sense, and the encoder count at its low end
  (`enc_zero`). Find them by jogging at COMMISSIONING.
- **Travel and limits:** the capacitors' turns (§9 item 48), and which LIM input is which end.
- **Elements and thermal:** the element curves (§9 item 54); C1's part; the NTC's beta, the trip
  points and the blower PWM (§9 item 30).
- **Relays:** the K1/K2 coil-current threshold. Measure an energized coil across its 1 Ω sense.
- **Cal-load detector:** its RF threshold, from the detector with ~5 W in the load.
- **Panel knobs:** which knob is left and the 62V15's edges per detent. If a knob runs backward, swap
  its A and B.

**On the bench, check:**

- A deliberate hang in `loop()` resets the Teensy within 0.5 s and drops MCU_PERMIT. The RTWDOG
  registers come from the reference manual, not from the Teensy core.
- Self-test failures latch as class C, as §8B.4b requires, so a missing encoder at power-up needs a
  `clear` once it is fixed.

## The tick contract

- **Moves.** A new `move_id` starts one coordinated move to `target`. The motion layer reports that
  id in `move_done` once the move has stopped, with `encoder_mismatch` set if the encoders disagree
  with the steps commanded. It compares counts, which only it knows. Steppers run only while
  `motion_enable` is set, and a move in progress stops when it falls.
- **PTT.** `mcu_permit` is down for the whole of PROBE and MOVE, and until the motion layer has
  reported the last move stopped. A move goes out only after the vote has been down 30 ms (§5.5,
  §7.4.5). The closed-loop tests check every tick that no move runs with the vote up, within 30 ms
  of its dropping, or under the bypass key.
- **Measurements.** `have_measurement` is set only for a measurement whose gate started after the
  last move stopped. `carrier` means a steady count, so SSB speech never starts a tune (§6A.10).

## Decisions beyond §8B

The closed-loop tests drove these; each is the smallest change that made a failing case pass.

1. **Priors per 1 % segment**, not per band. 80 m and 10 m swing too far across the band for one
   stored setting to help (50 segments in all). They are seeded from the NEC model at first boot,
   and each good tune replaces its segment's entry.
2. **The sign of θ.** A prior decides only when one hypothesis is clearly nearer it, and only once
   per tune. Otherwise PROBE steps C2 by 10 %. Every VERIFY repeats the test across the move just
   made, so a wrong prior costs one attempt.
3. **Far off (SWR > 5):** drive to the segment's stored setting first and measure there. At the top
   of the AD8302's range a fraction of a dB moves the R estimate several-fold. Solves from such
   readings are *coarse moves*, up to 3 per tune, and don't count against the 3 attempts. A move
   that leaves such a reading at over twice the best SWR so far is undone. "No feasible solution"
   is concluded only from a reading good enough to trust.
4. **Convergence at 1.2:1**, well under the 1.5:1 retune threshold, so a match holds. After the 3rd
   attempt a match under 1.5:1 is kept, since §8B.2 would not retune it. Above that it is TUNE FAILED.
5. **Over-SWR trips count only once MATCHED.** A tune starts from a mismatch, and the comparator keeps
   the amplifier off while it does. Counting those trips would make tuning a new band need an ACK.
6. **Carrier lost mid-move:** the move finishes, then IDLE. Stopping short leaves the elements nowhere
   useful.
7. **Every tune starts on a fresh key-down**, which is how "re-attempt on next carrier" (§8B.4a) works
   after a fault clears.
8. **Bypass key:** nothing moves, and a tune in progress is abandoned at once.
9. **A move still running after 15 s** is a position fault (encoder mismatch class).

## Tested envelope

The closed-loop model has the elements off their encoder calibration by up to ±3 % each and an
AD8302 residual of ±0.25 dB and ±2° after calibration. It covers the feeder spread `cap_demand.py`
sweeps (39–42 ft, VF 0.93–0.97) and the 10 m feedpoint uncertainty of §9 item 10.

- With the factory priors: every band edge from every start (mid-range, band change up, band change
  down) at every error corner. Most tunes take 1 attempt, the worst 3.
- 1000 random draws over the same bounds (992 within the network's reach), starting anywhere in
  range, half with priors and half cold: every seeded draw matches. Cold draws match 99.4 %. The
  rest start where the reading stays pinned at |Γ| = 1 through every coarse move, and they end in a
  fault, never anything unsafe. In band the tuner always has its seeds, so cold starts happen only
  out of band.

These bounds are what commissioning has to meet. The element calibration curves need to be within
about 3 %.

## Next

- **Bring-up** on the built boards, per the list above, then a calibration of every band.
- **Storage** per §8B.5: the SD mirror of profiles, calibration and the fault log, and versioned
  backups.
- **Remote:** Ethernet, the web UI and the remote head (§8C); recovery mode (§8B.4f.3).
- **Policy and operation:** the PERMISSIVE qualification counters (§8B.4a-1), pre-positioning on band
  select (§8B.3a), and the 160 m power derate (§1.7.1).
- **Cold-start search:** when there is no prior and the reading stays pinned at the top of the
  range, step through a few reference settings to find a readable neighborhood.
