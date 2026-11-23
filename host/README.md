<!-- SPDX-FileCopyrightText: 2026 Reuben A. Popp -->
<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# The bench PC's tools

Two programs for the bench PC, on the tuner's own subnet: `catbridge.py`, the CAT bridge (below), and
`fwupdate.py`, the firmware update over the network (at the end). Both need Python 3.8 or later, with
the standard library only.

## The CAT bridge

`catbridge.py` runs on the bench PC, between the rig's CAT control and the tuner's line port (TCP 4600,
§8C.5). It does two things:

- **Band-follow** (§8B.3a). It polls the rig's frequency every 0.5 s and sends `PRESET <MHz>` on a band
  change, or on a move of more than 0.5 % from the last PRESET. The elements then move while the rig still
  receives. It sends nothing while the rig transmits, at most one PRESET every 2 s, and only once the
  tuner's telemetry shows IDLE, no carrier, the TUNE path, the bypass off and no self-test running.
- **One-button tune.** When the tuner's telemetry shows `want=1` (a TUNE from the page, the panel or this
  bridge, waiting for a carrier) on the TUNE path, it saves the rig's mode, power and PTT, sets the carrier
  mode at the tune power, and keys the rig. When the tune ends it unkeys and puts the rig back.

It needs Python 3.8 or later, with the standard library only, and either Hamlib's `rigctld` or flrig.
The PC must be on the tuner's own subnet, which is all the tuner serves (§8C.7).

```sh
rigctld -m 3073 -r /dev/ttyUSB0 -s 115200 &        # for example an IC-7300; no --vfo
python3 catbridge.py run                           # the daemon
python3 catbridge.py run --rig flrig               # through flrig instead
python3 catbridge.py tune                          # one tune: TUNE, the carrier, exit 0 on a match
python3 catbridge.py run --dry-run -v              # log what it would send; change and key nothing
```

| Option | Default | |
|:--|:--|:--|
| `--tuner HOST[:PORT]` | `tuner.local:4600` | or the tuner's address |
| `--rig hamlib\|flrig` | `hamlib` | |
| `--rig-addr` | `localhost:4532`, `http://localhost:12345` | rigctld HOST[:PORT], or the flrig URL |
| `--tune-watts W` | 20 | the tune carrier; above 50 W is refused |
| `--rig-max-watts W` | 100 | the rig's power at Hamlib RFPOWER 1.0; the level sent is W / this |
| `--tune-mode MODE` | `RTTY` | below |
| `--tune-timeout S` | 15 | the longest key-down for one tune; above 30 s is refused |
| `--threshold PCT` | 0.5 | PRESET again after a move of this percent of the frequency |
| `--dry-run`, `-v` | | the dry run sends only SUBSCRIBE and QUERY; `-v` logs at debug |

`run` reconnects to either end with backoff (1 s doubling to 30 s) and keeps running. Don't run `tune`
while `run` is up: the daemon already answers TUNE from the page, and two programs would both key the
rig.

### The carrier mode

`RTTY` is the default because on most rigs it is FSK. Keyed by PTT with the FSK line idle, the rig sends
a steady, unmodulated mark carrier at the RF POWER setting, with the microphone out of circuit. Hamlib
maps RTTY to each rig's own FSK mode. With flrig the names are the rig's own (`rig.get_modes`), so the
bridge takes the first name that matches: RTTY on an Icom, RTTY-L on a Yaesu, FSK on a Kenwood.

- **FM** is a full, steady carrier too, but PTT keys the microphone. Speech would modulate it, so keep
  the mic quiet.
- **AM** is a carrier with no audio, but most rigs hold the AM carrier to about a quarter of their rated
  power. The tuner then sees well under `--tune-watts`, about 5 W from a 20 W setting on a 100 W rig.
- **CW** sends nothing on PTT alone on most rigs; it needs the key down.
- **Data modes** (`PKTUSB`, USB-D) send whatever the sound card plays, and silence is no carrier.

A mode that gives no carrier the tuner can see costs 3 s: with no carrier after that, the bridge
unkeys.

### Safety rules

- **When it keys.** Only when the tuner asks (`want=1`) on the TUNE path, and never while the rig
  already transmits. It keys once per request and never retries on its own.
- **Before the key-down.** The tune power is at most 50 W. The rig must read back the tune mode, and
  no more than the tune power plus 5 % of its maximum (at least 2 W), or nothing is keyed.
- **When it unkeys.** At the first of these:
  - the tuner reports MATCHED or FAULT;
  - the tune moves past IDLE and comes back to it (the carrier lost, or the tune abandoned);
  - the tuner withdraws `want` before the tune starts;
  - `hold=1`, a move waiting on forward power above the tuner's tune window (§8B.3b);
  - no carrier at the tuner 3 s after the key-down;
  - the timeout, 15 s by default and never over 30 s;
  - the tuner's link drops or goes quiet for 3 s;
  - any error, or SIGINT or SIGTERM. The unkey is done in a `finally`, and a signal waits until the
    rig is back.
- **If the rig's link fails.** The unkey reopens the link and tries again, four times. If all four fail,
  it logs a critical error, and the daemon tries again whenever the rig reconnects.
- **What is beyond it.** A `kill -9`, or a rigctld that dies while keyed. Set the rig's own transmit
  time-out timer where it has one.

### As a service

`KillSignal` is SIGTERM by default, so `systemctl --user stop` unkeys the rig like Ctrl-C does.

```ini
# ~/.config/systemd/user/catbridge.service
[Unit]
Description=Tuner CAT bridge
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 %h/antenna-tuner/host/catbridge.py run --tuner tuner.local
Restart=on-failure

[Install]
WantedBy=default.target
```

### Tests

```sh
cd host && python3 -m unittest -v test_catbridge
```

The tests run against fake servers: rigctld, flrig, and the tuner's line port with a toy state machine.
Two of them start the program itself, hold the rig keyed, and stop it with SIGTERM or SIGINT.

### ALE mode

`catbridge.py run --ale` is for a rig under an ALE controller (design log §8C.10). The bridge polls
every 0.25 s and sends PRESET only once a frequency has held for `--dwell` seconds (default 1.5), so
the scan's two to five channels a second send nothing. It never keys the rig: one-button tune is off
and `tune --ale` is refused, because the controller owns the rig and the tuner tunes on its
transmission. It warns above 60 channel changes an hour. Tune each channel once beforehand so the
tuner's recall memory holds it, and give the controller a tune time of about 5 s.

## The firmware update

`fwupdate.py` sends a Teensy 4.1 `.hex` to the tuner's line port (design log §8C.8). The tuner stages
it in its own flash and checks it, then shows FIRMWARE UPDATE READY with the image's CRC-32 on its
panel. Nothing is installed until someone at the box compares that CRC with the one printed here and
pushes the left knob. From the start of the transfer until then, the tuner holds its vote down.

```sh
cd fw && pio run
python3 ../host/fwupdate.py .pio/build/teensy41/firmware.hex --tuner tuner.local --wait
python3 ../host/fwupdate.py --check .pio/build/teensy41/firmware.hex   # check the file only
python3 ../host/fwupdate.py --status                                   # where an update stands
python3 ../host/fwupdate.py --abort                                    # discard one
```

With `--wait` it stays until the install starts and the tuner answers again after its restart.

```sh
cd host && python3 -m unittest -v test_fwupdate
```

Its tests run against a fake tuner, and one reads the real build if it exists.

