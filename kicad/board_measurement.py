#!/usr/bin/env python3
"""Measurement board, Sampler chamber -- 1500W Doublet Tuner Rev 3.7c.

NO MICROCONTROLLER (Section 8B.0). Everything leaves as filtered DC on the J-S
ribbon, plus the /1024 count on its own coax, so the Teensy on the Control
board does the lot.

Scope (Sections 6A, 6B.3a, 7.3, 7.3a, 7.4):
  - FWD and REF coupled ports in on edge SMAs, from the separate coupler box
    (two equal-length RG-316 jumpers). Each port is terminated here: 2 x 105
    ohm 1 W in parallel, so the coupler sees 50 ohm with the taps (6A.3)
  - Schottky envelope detectors (1N5711W, 70 V) -> V_FWD, V_REF_DET, scaled so
    1500 W reads ~2.9 V at the Teensy ADC (6A.4)
  - AD8302 in measurement mode on ~30 dB resistive taps -> V_MAG, V_PHS,
    AD_VREF (6A.5). INPA = REF, INPB = FWD
  - frequency: AC-coupled, mid-biased TLV3501 with clamps, a 74LVC74 /4 and a
    74HC4040 /256, so /1024 overall; out through 1 k on an SMA for the RG-316
    run W10 (6A.10, 7.3 frequency grade)
  - over-SWR trip: LM393 on the reflected detector, threshold on a trimmer,
    open collector with its 4.7 k pull-up here (6A.4, 7.4)
  - cal-load RF detector (6B.3a): 3.3 pF 1 kV / 100 pF divider, BAT54S doubler,
    2.2 nF, 100 k, +1.0 V bias through 1 M, 33 V TVS
  - local 3V3 from the J-S 5 V; ferrite-split into an analog rail (AD8302) and a
    digital rail (counter) so the counter's 30 MHz edges stay off the detector

OFF-BOARD: the Stockton coupler (its own diecast box), K1/K2 (wired from J-S
directly, W9b), the cal-load thermostat (W9c).

PACKAGES: 1206 passives, 2512 terminations, SOIC logic, SOT-223 regulator, as on
the Control board; the AD8302 is TSSOP-14 only. Through-hole: the header, the
electrolytic, the trimmer, the 1 kV disc and the wire pads.
"""
from gen_sch import Sch

FP_R    = 'Resistor_SMD:R_1206_3216Metric'
FP_RP   = 'Resistor_SMD:R_2512_6332Metric'
FP_C    = 'Capacitor_SMD:C_1206_3216Metric'
FP_CE6  = 'Capacitor_THT:CP_Radial_D6.3mm_P2.50mm'
FP_DISC = 'Capacitor_THT:C_Disc_D7.5mm_W5.0mm_P5.00mm'      # 1 kV NP0 disc, leads formed 6.4 -> 5.0 mm
FP_D123 = 'Diode_SMD:D_SOD-123'
FP_D123F= 'Diode_SMD:D_SOD-123F'
FP_SOT23= 'Package_TO_SOT_SMD:SOT-23'
FP_REG  = 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'
FP_FB   = 'Inductor_SMD:L_1206_3216Metric'
FP_SMA  = 'Connector_Coaxial:SMA_Molex_73251-1153_EdgeMount_Horizontal'
FP_IDC  = 'Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical'   # On Shore 302-S161, shrouded, keyed
FP_POT  = 'Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical'
FP_TP   = 'TestPoint:TestPoint_THTPad_D1.5mm_Drill0.7mm'
FP_WIRE = 'TestPoint:TestPoint_THTPad_D2.5mm_Drill1.2mm'     # 22 AWG wire pad
FP_MH   = 'MountingHole:MountingHole_3.2mm_M3_Pad_Via'
SOIC = {8: 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 14: 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',
        16: 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm'}

s = Sch('Measurement Board -- Sampler Chamber', 'tuner', rev='Rev 3.7c')
# Each part is tagged with the board block it belongs to; make_pcb.py packs the
# blocks into fixed regions so the router starts from a sensible floor plan.
BLOCKS, _blk = {}, ['misc']
def block(name):
    _blk[0] = name
def A(*args, **kw):
    c = s.sym(*args, **kw)
    BLOCKS.setdefault(c['ref'], _blk[0])
    return c

# Connections are by label, so the sheet only has to keep pin stubs apart;
# two-terminal parts go on a grid below the multi-pin parts.
class Grid:
    def __init__(self, x0, y0, cols, dx=20.32, dy=22.86):
        self.x0, self.y0, self.cols, self.dx, self.dy, self.n = x0, y0, cols, dx, dy, 0
    def __call__(self):
        r, c = divmod(self.n, self.cols); self.n += 1
        return (self.x0 + c * self.dx, self.y0 + r * self.dy)
cell = Grid(20, 165, 19)

_count = {}
def nxt(prefix):
    _count[prefix] = _count.get(prefix, 0) + 1
    return f'{prefix}{_count[prefix]}'

def two(lib_id, prefix, val, a, b, fp, pins=('1', '2')):
    p = A(lib_id, nxt(prefix), val, cell(), footprint=fp)
    s.net(p, pins[0], a); s.net(p, pins[1], b)
    return p
def R(val, a, b, fp=FP_R):   return two('Device:R', 'R', val, a, b, fp)
def C(val, a, b, fp=FP_C):   return two('Device:C', 'C', val, a, b, fp)
def CE(val, pos, neg='GND', fp=FP_CE6):
    return two('Device:C_Polarized', 'C', val, pos, neg, fp)
def D(part, anode, cathode, fp=FP_D123, sym='Device:D_Schottky'):
    return two(sym, 'D', part, anode, cathode, fp, pins=('A', 'K'))
def FB(a, b):
    return two('Device:FerriteBead_Small', 'FB', 'BLM31PG601SN1L', a, b, FP_FB)
_tp = [0]
def TP(net, label):
    _tp[0] += 1
    t = A('Connector:TestPoint', f'TP{_tp[0]}', label, cell(), footprint=FP_TP)
    s.net(t, '1', net)

# ================= coupled ports: termination, detector, AD8302 tap (6A.3-6A.5) =================
# Each port sees 2 x 105 R in parallel (52.5 R, 2 W) against the taps' ~1.2 k
# (FWD) / ~1.5 k (REF): 50.2 / 50.7 ohm, return loss > 40 dB, so the Stockton
# separation holds (6A.2). 0.94 W at 1500 W, both ports under full reflection.
#
# Detector: 1N5711W, 70 V. At 1500 W the port peaks at 9.7 V and the diode sees
# ~19 V reverse, past the HSMS-282x's 15 V (and the old HSMS-2850's 3.8 V). The
# 22 k / 10 k load divides the ~9.4 V peak to 2.9 V for the ADC (3.3 V max).
#
# Vector tap: 1.62 k into the AD8302's 52.3 R shunt = -30.2 dB, from a ~50 ohm
# source as the datasheet assumes. FWD (INPB, the reference channel) then sits
# at -22 dBm at 10 W and -0.3 dBm at 1500 W (max input -3 dBV), and REF can
# fall the full 30 dB below it inside the -60 dBm floor from ~2 W up (6A.5).
def port(tag, sma, sma_val, inp):
    block('rf_' + tag.lower())
    J = A('Connector:Conn_Coaxial', sma, sma_val, (40, 35 if tag == 'FWD' else 95), footprint=FP_SMA)
    rf = f'{tag}_RF'
    s.net(J, 'In', rf); s.net(J, 'Ext', 'GND')
    R('105 1W', rf, 'GND', fp=FP_RP); R('105 1W', rf, 'GND', fp=FP_RP)
    D('1N5711W', rf, f'{tag}_PK')
    C('10n', f'{tag}_PK', 'GND')
    out = 'V_FWD' if tag == 'FWD' else 'V_REF_DET'
    R('22k', f'{tag}_PK', out); R('10k', out, 'GND')
    R('1k62', rf, f'{tag}_ATT'); R('52R3', f'{tag}_ATT', 'GND')
    C('10n C0G', f'{tag}_ATT', inp)            # all four AD8302 inputs are biased ~100 mV below VPOS
    return out

V_FWD = port('FWD', 'J1', 'SMA FWD in', 'INPB_AC')
V_REF = port('REF', 'J2', 'SMA REF in', 'INPA_AC')

# ================= AD8302, measurement mode (6A.5) =================
block('ad8302')
U1 = A('RF:AD8302xRU', 'U1', 'AD8302ARUZ', (90, 65), footprint='Package_SO:TSSOP-14_4.4x5mm_P0.65mm')
s.net(U1, 'INPA', 'INPA_AC'); s.net(U1, 'INPB', 'INPB_AC')
s.net(U1, 'VPOS', '+3V3A'); s.net(U1, 'COMM', 'GND')
# VMAG -> MSET and VPHS -> PSET give the default 30 mV/dB and 10 mV/deg about 900 mV
s.net(U1, 'VMAG', 'V_MAG'); s.net(U1, 'MSET', 'V_MAG')
s.net(U1, 'VPHS', 'V_PHS'); s.net(U1, 'PSET', 'V_PHS')
s.net(U1, 'VREF', 'AD_VREF')
# offset loop: f_HP (MHz) = 2 / C (nF), so 100 nF puts it at 20 kHz, far under
# 1.8 MHz (the old 1 nF put it at 2 MHz, inside 160 m)
s.net(U1, 'OFSA', 'OFSA'); s.net(U1, 'OFSB', 'OFSB')
C('100n', 'OFSA', 'GND'); C('100n', 'OFSB', 'GND')
# video filter: T (ns) = 3.3 x C (pF) -> 33 us; the 2f ripple at 1.8 MHz is ~57 dB down
s.net(U1, 'MFLT', 'MFLT'); s.net(U1, 'PFLT', 'PFLT')
C('10n', 'MFLT', 'GND'); C('10n', 'PFLT', 'GND')
C('100p C0G', '+3V3A', 'GND'); C('100n', '+3V3A', 'GND')
FB('+3V3', '+3V3A'); C('10u', '+3V3A', 'GND')

# ================= frequency (6A.10, 8B.0.1, 7.3 frequency grade) =================
block('counter')
# Tap the 50 ohm node through 1 nF and 4.7 k into a node held at mid-rail by
# 10 k: 0.68 of the port voltage, so 1 W (0.25 V peak) still swings the
# comparator +/-170 mV, and 1500 W is clamped by the BAT54S at ~1 mA.
C('1n C0G', 'FWD_RF', 'FREQ_TAP')
R('4k7', 'FREQ_TAP', 'FREQ_IN')
R('10k', 'FREQ_IN', 'FREQ_MID')
R('10k', '+3V3D', 'FREQ_MID'); R('10k', 'FREQ_MID', 'GND'); C('100n', 'FREQ_MID', 'GND')
Dc = A('Diode:BAT54S', nxt('D'), 'BAT54SLT1G', (150, 30), footprint=FP_SOT23)
s.net(Dc, 'A', 'GND'); s.net(Dc, 'COM', 'FREQ_IN'); s.net(Dc, 'K', '+3V3D')
U2 = A('Comparator:TLV3501AID', 'U2', 'TLV3501AIDR', (180, 30), footprint=SOIC[8])
s.net(U2, '+', 'FREQ_IN'); s.net(U2, '-', 'FREQ_MID'); s.net(U2, '6', 'FREQ_TTL')
s.net(U2, 'V+', '+3V3D'); s.net(U2, 'V-', 'GND')
s.net(U2, 'SHDN', 'GND')      # SHDN within 0.9 V of V+ disables it; the old board tied it high
s.nc(U2, '1'); s.nc(U2, '5')
R('1M', 'FREQ_TTL', 'FREQ_IN')                 # ~10 mV of hysteresis on top of its own 6 mV
# 74AC4040 is obsolete and plain HC is marginal at 29.7 MHz on 3.3 V (8B.0.1),
# so a 74LVC74 (150 MHz) divides by 4 first; the HC4040 then sees <= 7.4 MHz.
U3 = [A('74xx:74LS74', 'U3', '74LVC74AD', (215 + 30 * i, 30), unit=u, footprint=SOIC[14]) for i, u in enumerate((1, 2, 3))]
s.net(U3[0], 'C', 'FREQ_TTL'); s.net(U3[0], 'D', 'DIV2_N'); s.net(U3[0], '~{Q}', 'DIV2_N'); s.net(U3[0], 'Q', 'DIV2')
s.net(U3[1], 'C', 'DIV2');     s.net(U3[1], 'D', 'DIV4_N'); s.net(U3[1], '~{Q}', 'DIV4_N'); s.net(U3[1], 'Q', 'DIV4')
for u in U3[:2]:
    s.net(u, '~{S}', '+3V3D'); s.net(u, '~{R}', '+3V3D')
s.net(U3[2], 'VCC', '+3V3D'); s.net(U3[2], 'GND', 'GND')
U4 = A('4xxx:4040', 'U4', 'SN74HC4040DR', (310, 30), footprint=SOIC[16])
s.net(U4, 'CLK', 'DIV4'); s.net(U4, 'Reset', 'GND')
s.net(U4, 'Q7', 'FREQ_DIV')                    # Q7 = /256, so /1024 overall
s.net(U4, 'VDD', '+3V3D'); s.net(U4, 'VSS', 'GND')
for q in ('Q0', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q8', 'Q9', 'Q10', 'Q11'):
    s.nc(U4, q)
for _ in range(3):
    C('100n', '+3V3D', 'GND')
FB('+3V3', '+3V3D'); C('10u', '+3V3D', 'GND')
block('freqout')
J3 = A('Connector:Conn_Coaxial', 'J3', 'SMA /1024 out', (350, 30), footprint=FP_SMA)
s.net(J3, 'In', 'FREQ_X'); s.net(J3, 'Ext', 'GND')
R('1k', 'FREQ_DIV', 'FREQ_X')                  # 7.3 frequency grade: 1 k + the FT-P 1000 pF

# ================= over-SWR trip (6A.4, 7.4) =================
block('swr')
# Reflected-power threshold: 0.15-2.29 V, i.e. ~10 W to ~800 W reflected; set at
# commissioning with a wattmeter (167 W reflected = 2:1 at 1500 W reads ~0.92 V).
# LM393 on 5 V for a 0-3.5 V input range; trips (pulls SWR_OK low) when
# V_REF_DET rises above the threshold. 1 M gives ~10 mV of hysteresis.
U6 = [A('Comparator:LM393', 'U6', 'LM393DR', (150 + 30 * i, 100), unit=u, footprint=SOIC[8]) for i, u in enumerate((1, 2, 3))]
s.net(U6[0], '+', 'SWR_TH'); s.net(U6[0], '-', V_REF); s.net(U6[0], '1', 'SWR_OK')
s.net(U6[1], '+', 'GND'); s.net(U6[1], '-', '+3V3'); s.nc(U6[1], '7')
s.net(U6[2], 'V+', '+5V'); s.net(U6[2], 'V-', 'GND')
C('100n', '+5V', 'GND')
R('4k7', '+3V3A', 'SWR_TH_T')
RV1 = A('Device:R_Potentiometer_Trim', 'RV1', '10k 3296W', (245, 100), footprint=FP_POT)
s.net(RV1, '1', 'SWR_TH_T'); s.net(RV1, '3', 'SWR_TH_B'); s.net(RV1, '2', 'SWR_TH')
R('680', 'SWR_TH_B', 'GND'); C('100n', 'SWR_TH', 'GND')
R('1M', 'SWR_OK', 'SWR_TH')
# open collector, pulled up here; the Control board's 100 k pull-down makes an
# unplugged ribbon read as a trip (7.4)
R('4k7', '+3V3', 'SWR_OK')
TP('SWR_TH', 'SWR TH'); TP(V_REF, 'V REF')

# ================= cal-load RF detector (6B.3a) =================
block('hv')
# The load node peaks at 77 V at 60 W and 387 V if 1.5 kW reaches the load, so
# the top capacitor is a 1 kV NP0 disc and the tap pad keeps 2.5 mm to all
# other copper (IPC-2221 B2, 301-500 V). Divider 1:31; doubler; 0.2 ms.
J5 = A('Connector_Generic:Conn_01x01', 'J5', 'CAL LOAD TAP', (270, 100), footprint=FP_WIRE)
J6 = A('Connector_Generic:Conn_01x01', 'J6', 'CAL GND', (285, 100), footprint=FP_WIRE)
s.net(J5, 'Pin_1', 'CAL_TAP'); s.net(J6, 'Pin_1', 'GND')
C('3p3 1kV NP0', 'CAL_TAP', 'CAL_DIV', fp=FP_DISC)
block('cal')
C('100p C0G', 'CAL_DIV', 'GND')
Dk = A('Diode:BAT54S', nxt('D'), 'BAT54SLT1G', (305, 100), footprint=FP_SOT23)
s.net(Dk, 'A', 'GND'); s.net(Dk, 'COM', 'CAL_DIV'); s.net(Dk, 'K', 'CAL_PK')
C('2n2 C0G', 'CAL_PK', 'GND')
R('100k', 'CAL_PK', 'CAL_DET')
R('1M', 'CAL_BIAS', 'CAL_DET')
R('22k', '+3V3A', 'CAL_BIAS'); R('10k', 'CAL_BIAS', 'GND'); C('100n', 'CAL_BIAS', 'GND')   # +1.03 V
D('SMF33A', 'GND', 'CAL_DET', fp=FP_D123F, sym='Device:D_Zener')                       # 33 V TVS
TP('CAL_DET', 'CAL DET')

# ================= local 3V3 (6A.3b: own regulator behind a filtered feedthrough) =================
block('power')
U5 = A('Regulator_Linear:AMS1117-3.3', 'U5', 'AMS1117-3.3', (335, 100), footprint=FP_REG)
s.net(U5, 'VI', '+5V'); s.net(U5, 'VO', '+3V3'); s.net(U5, 'GND', 'GND')
C('10u', '+5V', 'GND')
CE('100u 10V', '+3V3')                         # AMS1117 output stability, as on the Control board
C('100n', '+3V3', 'GND')
TP('GND', 'GND')

# ================= J-S: sampler group, pins 1-16 of the J-B allocation (7.3a) =================
# W9: J-S solder cups 1-16 -> this header one to one, so the pinout is the
# Control board's J-B pins 1-16. Every line has its own ground; 1 k on each
# analog output isolates its driver from the 5600 pF contacts and makes the
# 28 kHz analog-grade corner (7.3).
block('conn')
J4 = A('Connector_Generic:Conn_02x08_Odd_Even', 'J4', 'J-S sampler', (380, 95), footprint=FP_IDC)
JS = {1: 'V_MAG_X', 3: 'V_PHS_X', 5: 'V_FWD_X', 7: 'V_REF_DET_X', 9: 'AD_VREF_X',
      11: 'CAL_DET', 13: 'SWR_OK', 15: '+5V'}
for p_ in range(1, 17):
    s.net(J4, f'Pin_{p_}', JS.get(p_, 'GND'))
for net in ('V_MAG', 'V_PHS', 'V_FWD', 'V_REF_DET', 'AD_VREF'):
    R('1k', net, net + '_X')

# ================= mounting: four M3, plated, bonded to GND (the chassis, through the standoffs) =================
block('mech')
for i in range(4):
    h = A('Mechanical:MountingHole_Pad', f'H{i + 1}', 'M3', (300 + 15 * i, 140), footprint=FP_MH)
    s.net(h, '1', 'GND')

# ================= power flags =================
block('none')
# +5V arrives on a connector pin and +3V3A / +3V3D through ferrite beads, so flag
# them; +3V3 comes from the regulator's output.
for i, (netname, xy) in enumerate((('+5V', (20, 140)), ('GND', (45, 140)), ('+3V3A', (70, 140)), ('+3V3D', (95, 140)))):
    f = A('power:PWR_FLAG', f'#FLG{i + 1}', 'PWR_FLAG', xy)
    s.net(f, '1', netname)

s.write('measurement.kicad_sch')
import json
json.dump(BLOCKS, open('measurement.blocks.json', 'w'), indent=0, sort_keys=True)
print(f'wrote measurement.kicad_sch: {len(s.comps)} symbols, {len(s.items)//2} connections')
