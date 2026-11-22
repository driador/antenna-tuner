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

The Teensy build is about 262 KB of code and 120 KB of RAM1 variables (of 7.75 MB and 512 KB; code also runs from RAM1, leaving about 140 KB free). QNEthernet 0.37.0 is fetched by PlatformIO on the first build.

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
| `path` | TUNE / AUX / CAL: the vote held while K1 and K2 change, never under RF, coil currents and the first key-down checked | §5.5, §6B.2 |
| `panel` | Every panel screen, drawn as text, with the scroll-to-confirm rule for class C | §7.5, §8B.4f |
| `panel_io` | The encoders' quadrature and the Nextion's serial protocol | §7.5 |
| `qualify` | The PERMISSIVE qualification: tunes, bands, powered hours, no mechanical fault, the inspection | §8B.4a-1 |
| `events` | The numbered event log that the SD log and each link client read from, so nothing is lost | §8B.5.3, §8C.6 |
| `json`, `mirror` | The mirrored settings document, `/recovery.cfg` (network keys only), backup numbering and pruning | §8B.5.4 |
| `derate` | The continuous power limit: the RF bay's averaged loss against its 200 W of cooling, as a warning | §1.7.1 |
| `alarm` | The audible alarm: one pattern for the worst thing sounding, and what silences it | §8B.4i |
| `bit` | The built-in test: the detectors' windows at rest, the active run (each axis, each relay, the hold latch, the permit), how each check is graded, and the permit term that holds the permit down | §8B.4g, §8B.4h |
| `netcfg` | The network settings: the check a change must pass, and the key=value text the link, the console and `/recovery.cfg` share | §8B.5.3 |
| `proto` | The line protocol: commands, refusals of local-only actions, telemetry and event lines with checksums | §8C.5 |
| `web` | HTTP heads, the WebSocket handshake and frames, and the page | §8C.4 |
| `sntp` | One network-time request and its reply, to set the RTC | §8C |

`test_tnet` matches `nec/cap_demand.py` at all 29 band-edge points to 1e-9. `test_bridge` reproduces
the §6A.6 round trips and the §6A.7 example (91 ± j65 Ω → 0.717 V, 1.470 V).

## The Teensy layer

| File | Does |
|:--|:--|
| `main.cpp` | The §8B.4b boot sequence: safe outputs, the recovery button, the watchdog before the permit can rise, the boot checks, the restored fault record and priors. Then the 10 ms tick, the built-in test and the console |
| `board.*` | The direct pins: MCU_PERMIT and its read-back, DRV_EN, the relay commands (held in TUNE), the blower PWM and tach, LIM1–6, RTWDOG |
| `motion.*` | Encoders over SPI, the 50 kHz step interrupt running a planned move, drivers on only while moving, the encoder check after every move |
| `sensors.*` | V_MAG and V_PHS averaged over each 200 ms counter gate and read against the AD8302's VREF, the carrier test, the MCP23017, the tank thermistor, the detectors at rest for the built-in test, the alarm sounder on GPA7 |
| `persist.*` | Two EEPROM records with their own CRCs, packed so that only changed bytes are rewritten. The authoritative one (faults, mode, calibration) is kept twice and written alternately, so a power loss mid-write leaves the older copy good. The other holds the priors and last positions |
| `calib.*` | The calibration procedure below |
| `panel_hw.*` | The Nextion on Serial8 (only changed rows are sent), the knobs and their pushes from the MCP23017 |
| `storage.*` | The SD mirror: atomic writes, 20 versions, the event log, `/recovery.cfg`, tuner identity |
| `net.*` | Ethernet through QNEthernet: the line port, the page and WebSocket, the subnet rule, mDNS, SNTP |

**USB console:** the box's local interface, with the panel (§8B.4f):

| Command | Does |
|:--|:--|
| `status` | One status line. One also prints every second |
| `ack` | Acknowledge class B faults |
| `clear` | Local clear of class B and C faults |
| `tune` | Start a tune |
| `mode commissioning\|strict` | Set the fault policy. PERMISSIVE is refused until the §8B.4a-1 qualification counters exist |
| `path tune\|aux\|cal` | Change the RF path, only while receiving (§5.5) |
| `cal load\|open\|short\|save` | The calibration steps (below) |
| `cal watts <W>` | Add a forward-power point at the wattmeter reading W |
| `jog c1\|c2\|l <turns>` | Move one element |
| `preset <MHz>` | Pre-position for a band while receiving (below) |
| `selftest` | Run the built-in test (below) |
| `inspected` | Record the roller inspection (§8B.4a-1) |
| `qual` | Show the PERMISSIVE qualification |
| `backups`, `restore <n>`, `adopt` | List the card's versions, restore one, claim another tuner's card (§8B.5.4b) |
| `net [key=value ...]` | Show the network settings, or change them as `NET` does (below) |

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

**PERMISSIVE** (§8B.4a-1) is offered only once the tuner has done 100 tunes on four bands and run 50
powered hours with no mechanical fault, and the roller inspection is recorded. A limit hit or an
encoder mismatch starts the count over. The panel's policy screen shows where it stands.

**The SD card** (§8B.5) mirrors the flash and never configures it.

- **When it writes:**
  - every administrative change (mode, calibration, inspection, restore) writes a new version under
    `/backup`, keeping 20;
  - `current.json` follows the profiles every 10 minutes;
  - `/log/events.log` collects the event log.
- **Every write is atomic:** a temporary file, then a rename.
- **No card is a condition, not a fault.** The events wait in RAM until one appears.
- **Presence through the extender:** the panel-mount extender keeps the Teensy's socket permanently
  "occupied", so presence is learned by using the card. A failed write marks it gone, and it is
  re-mounted every 5 s.
- **Identity:** a card from another tuner is never written to.
- **Restore:** a restore from this tuner's own card is a rollback and can be done any time. A board
  that came up blank or corrupt may restore from any card. Otherwise another tuner's card needs `adopt`
  first. A restore never promotes the policy to PERMISSIVE.
- **`/recovery.cfg`** is applied once at boot, network keys only, then renamed. Settings the tuner
  could not run on are refused whole, and the console says why.

**The recovery button** held at power-up (§8B.4f.3) forces DHCP as `tuner` and the STRICT policy, and
holds transmit off until the next reboot. Latched faults stay latched.

**The link protocol** (§8C.5), the same on a TCP port and inside the web page's WebSocket:

- **Commands:** `TUNE`, `ACK`, `QUERY`, `SUBSCRIBE [hz]` (0.1–20 Hz; 0 stops it), `GET_LOG [from]`,
  `PATH TUNE|AUX|CAL`, `CAL LOAD|OPEN|SHORT|SAVE|WATTS <w>` (up to 2000 W), `PRESET <MHz>`, `SELFTEST`,
  and `NET [mode=dhcp|static] [hostname=] [ip=] [netmask=] [gateway=] [dns=]`. A malformed number
  (`NAN`, `5X`) is refused with the usage, never read as 0.
- **Refused by name:** mode changes, class C clears, the bypass and jogging, which are local only.
- **Checksums:** every line ends in an NMEA-style `*HH`. A command typed by hand may leave it off.
- **What the tuner sends:**
  - `TLM` carries the state at the subscribed rate.
  - `EVT` lines are numbered, and `TLM` says how far the log has got. A client that missed events asks
    `GET_LOG` for them, so a dropped link loses nothing that is still in the 128-event ring (§8C.6).
  - `NET` answers `NET` with the saved settings, the address in use and `pending=1` while saved
    settings wait for a restart.

**Pre-positioning** (§8B.3a). After a band change on the rig, the page's Preset buttons (the band's
center) or `PRESET <MHz>` drive the elements to the stored setting for that frequency while the rig
still receives. It is taken only in IDLE with no carrier, on the TUNE path, with the bypass off and no
blocking fault, and the move drops the permit like any other. The key-down that follows measures the
real frequency as always, so a wrong preset costs a longer move and nothing else. In the simulation,
over all 90 changes between band edges, it cuts the key-down travel from 54 % of range to 10 % on
average (2.2 moves to 1.5), which leaves the refine.

**The 160 m derate** (§1.7.1). The cooling carries 200 W of loss in the RF bay, and only the bottom of
160 m loses more than that at full power: the continuous limits are about 502 / 600 / 882 W for
1.800–1.850 / –1.950 / –2.000 MHz, and 1500 W everywhere else. The tuner averages the bay's loss
(forward power times each segment's loss at its worst point, on the TUNE path) the way its temperature
follows it, over about two minutes (ASSUMED, `kDerateTauS`). Over 200 W it warns: an event in the log,
a note on the panel and console, and a banner on the page. It never touches PTT, as §1.7.1 requires;
the tank's over-temperature fault stays the hard stop. Key-down at 1500 W at 1.82 MHz warns after about
49 s; SSB at 1500 W PEP never does, nor does any other band at full power. A band with no power
calibration counts as no power. `TLM` carries `loss=`, `lim=` and `derate=`.

**The built-in test** (§8B.4h) moves to power-up the faults that would otherwise show at first use,
and names what failed.

- **When it runs:**
  - **At every boot:** the original checks (the expander, the encoders, the AD8302's VREF, the limits,
    the permit down, the fault record). A failure there is SELF-TEST FAILURE, as before.
  - **At power-up:** the active run, 3 s after boot (`kBitAtPowerUp`, on by default; `kBitSettleMs`).
  - **On demand:** the panel's Self-test, the page's button, `SELFTEST` on the link and `selftest` on
    the console.
- **What a run does:**
  1. **The detectors at rest:** V_MAG and V_PHS inside their windows, the forward detector below its
     RF threshold, the cal-load detector near its bias, the thermistor between −20 and +60 °C. The
     windows are ASSUMED (`bit::Windows`) until bring-up reads the real idle levels.
  2. **Each axis:** one turn away from its nearer end and back. These are ordinary jogs, so the state
     machine's own move check judges them.
  3. **The relays:** AUX, CAL and TUNE again, through the path switch, each confirmed by coil current.
  4. **The hold latch:** with the permit up, K1 is driven directly for 50 ms, and its coil must draw
     nothing.
  5. **The permit:** it must follow the vote. If it doesn't, the console names the first term that
     reads low on the MCP23017.
- **Conditions:** no carrier and no RF for 0.5 s, the bypass off, nothing latched or awaiting ACK, the
  TUNE path, and the RF service panel closed. If any changes during a run, it stops and puts the path
  back to TUNE once the relays may move.
- **Results and grades:**
  - **SELF-TEST FAILURE (C):** the hold latch.
  - **The mechanical policy:** an axis, which raises an encoder mismatch.
  - **RELAY MISMATCH (B):** a relay.
  - **BUILT-IN TEST (B):** a detector off at rest.
  - **Warnings:** the thermistor and the permit.
- **Reporting:**
  - Each failed check is logged as its own event (`selftest check=`), and a run ends with
    `result=passed` or `result=stopped`.
  - The panel's fault screen names the checks under their fault, and the console says what could not
    be judged (COMMISSIONING withholds the vote, so the latch and permit go untested).
  - `TLM` carries `bit=`, the failed checks as a word of bits (`bit.hpp` order), and `bitrun=`.

**The alarm** (§8B.4i) sounds at the box and on the page, under the same rules:
- **Patterns:** a class C latch beeps fast (150 ms on, 150 off), an unacknowledged class B slowly (150 ms
  every 2 s), and an over-temperature or the derate warning chirps (60 ms every 15 s). Each starts with a
  beep at once.
- **Silencing:**
  - An ACK clears the B faults, and so their sound.
  - At the box, a knob press silences everything sounding at that moment; the C latches stay latched.
  - On the page, the Silence button quiets that page alone.
  - Anything new sounds again, and so does anything that clears and comes back.
- **At the box:** an active piezo sounder on the cassette face, switched from the MCP23017's GPA7.
  `kSounder = false` in `config.hpp` turns it off and leaves the page's tone.
- **On the page:** tick "alarm sound here" once; browsers allow sound only after a click on the page,
  so after a reload one click anywhere re-enables it. The tab title flashes while a fault is sounding.
  `TLM` carries `hot=` for the over-temperature.

**On the network** (§8C):

- **Addresses:** DHCP with the hostname `tuner` unless a static address is set (§8B.5.3). mDNS also
  answers `tuner.local`.
- **Page:** `http://tuner.local/` serves it, and it talks over a WebSocket at `/ws`.
- **Settings:** the page's Network card, `NET` over `nc`, or `net` on the console sets DHCP or a static
  address, mask, gateway, DNS and the hostname. A change is checked (a host address on a /8 to /30
  subnet, a gateway on it, a hostname a resolver takes), saved to flash and the card, logged, and used
  from the next restart, so the connection that made it never drops. If the tuner can't be reached
  after one, hold the recovery button at power-up (§8B.4f.3).
- **Scripts:** `nc tuner.local 4600` speaks the line protocol directly. Type `SUBSCRIBE 5`, `QUERY` or
  `GET_LOG 1`.
- **Access:** only hosts on the tuner's own subnet are served (§8C.7). Never port-forward it.
- **Clock:** SNTP from `pool.ntp.org` sets the RTC, so log entries and backups carry real times once
  it has answered. It asks every minute until then and every six hours after, believes only the server
  it asked, and handles the NTP rollover in 2036.
- **Never blocking:** writes go out only when they fit and connections close without waiting, so the
  link can't hold up the tick. A cable unplugged at power-up just means no link.

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
  points, the blower PWM and the derate's averaging time (§9 item 30).
- **Relays:** the K1/K2 coil-current threshold. Measure an energized coil across its 1 Ω sense.
- **Cal-load detector:** its RF threshold, from the detector with ~5 W in the load.
- **Forward detector:** `kFwdRfVolts`, the level that counts as RF for the §5.5 relay guard: just
  above its idle reading, below what a few watts give.
- **Panel knobs:** which knob is left and the 62V15's edges per detent. If a knob runs backward, swap
  its A and B.

**On the bench, check:**

- A deliberate hang in `loop()` resets the Teensy within 0.5 s and drops MCU_PERMIT. The RTWDOG
  registers come from the reference manual, not from the Teensy core.
- The microSD card works through the panel-mount extender (§8B.5.6): it mounts, writes a backup, and
  is noticed when pulled (within 10 s) and when put back (within 5 s). If it is unreliable over the
  ribbon, the SDIO clock comes down.
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
  range, half with priors and half cold: every seeded draw matches, and cold draws match 99.8 %
  (508 of 509). In band the tuner always has its seeds, so cold starts happen only out of band.
- **The cold-start search.** Cold, a bad enough start can leave nothing to solve from, and the coarse
  moves used to end there in NO SOLUTION. Now the tune first steps through up to six reference
  settings, each the match for a likely load at the measured frequency (`reference_settings`), and
  goes on from the first that reads within SWR 5, or from the best. Those moves count as neither
  attempts nor coarse moves, and a tune that a coarse move rescues never searches, so nothing that
  worked before is slower. Over 1491 cold draws it cuts the faults from 8 to 4 and the no-solution
  faults from 4 to 0.
- **Wider runs** (`RANDOM_DRAWS=5000 RANDOM_SEED=12345`, and seed 67890) show the limits. Cold faults
  fall from 0.59 % to 0.42 % with the search; what is left is 160 m running out of its three attempts
  (bounded by §8B.3 on purpose), and every fault is a clean stop. Separately, 3 of about 2,500 seeded
  draws at 29.700 MHz run out of attempts at SWR 14–15, with or without the search.

These bounds are what commissioning has to meet. The element calibration curves need to be within
about 3 %.

## Next

- **Bring-up** on the built boards, per the list above, then a calibration of every band.
- **Continuous checks** from the §8B.4g table: cross-check the counter against the forward detector,
  watch the blower tach, name the permit term that dropped in use (the built-in test names it only
  when the permit fails to rise), and read the imbalance CT.
- **Recovery mode stage 2** (§8B.4f.3): the panel's backup browser and network editor.
- **The top of 10 m:** wider random runs show 3 of about 2,500 seeded draws at 29.700 MHz ending in
  "tune failed after 3 attempts" at SWR 14–15; find what sends those attempts astray.

## License

GPL-3.0-or-later ([`LICENSE`](LICENSE)). The firmware is a separate work from the hardware, which is
CERN-OHL-W v2; see [`../NOTICE`](../NOTICE). The Teensy build links QNEthernet (AGPL-3.0-or-later),
so the AGPL's network clause applies to a built image, and the page the tuner serves links to this
source.
