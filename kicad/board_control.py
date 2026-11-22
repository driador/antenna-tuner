#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Control board, Control chamber -- 1500W Doublet Tuner Rev 3.7c.

Scope (Sections 5.5, 6B, 7.1-7.5, 8, 8A, 8B, 8C):
  - 24 V in through a fuse; TSR 3-2450N (5 V) and TSR 2-24120N (12 V, blower),
    each behind TRACO's LC input filter (8A.1); AMS1117-3.3 for board logic
  - J-A, one 2x13 ribbon: STEP/DIR x3, DRV_EN, encoder SPI incl. MOSI, 3V3 and
    six limit senses, 47 ohm on every logic line (7.3, 7.3a)
  - J-B, one 2x13 ribbon (sampler group): five ADC lines (1 k), the SWR
    permissive, 5 V out, K1/K2 coils, cal-load thermal switch and RF detector
  - J-E, one 2x5 ribbon (RF tank): tank thermal, imbalance CT, RF service-panel
    interlock switch (shelf FT4)
  - /1024 frequency on RG-316 to an SMA jack, 1 k (7.3 frequency grade)
  - K1/K2 low-side drivers with coil-current sense, fed from a latch that only
    follows the MCU after the permissive has been down >= 30 ms (5.5)
  - the hardware permissive (7.4): (SWR AND MCU) OR the bypass key, AND the
    cal-load window, cal-load thermal, RF panel and limit conditions, gating a
    10 kHz hardware tone into the HFBR-1521Z. The bypass therefore works with a
    dead controller (6B.2, 8B.4d) and defeats only the SWR trip and the MCU.
  - blower: 12 V, on unless the MCU pulls the gate down (PWM), tach in (8)
  - local panel: Nextion on Serial8; both encoders, the bypass key and every
    permissive input readable through an MCP23017 (7.5, 8B.4d, 8B.4f)
  - recovery button (8B.4f.2)

OFF-BOARD, connectors only: stepper drivers, encoders, limit switches, K1/K2,
measurement board, blower, panel parts. Ethernet is PJRC's kit on the Teensy.

PACKAGES: the board must fit the cassette's 5.5 x 3.6 in envelope, so it is
mixed technology in hot-air-friendly sizes: 1206 passives, SOIC logic, SOT-223
MOSFETs, SMA/SOD-123 diodes, 1812/2920 PTCs. Teensy, connectors, DC-DCs,
electrolytics, inductors, trimpot and the fiber transmitter stay through-hole.
"""
from gen_sch import Sch

FP_R   = 'Resistor_SMD:R_1206_3216Metric'
FP_RP  = 'Resistor_SMD:R_2512_6332Metric'          # 1 W: coil sense, LED
FP_C   = 'Capacitor_SMD:C_1206_3216Metric'
FP_CE5 = 'Capacitor_THT:CP_Radial_D5.0mm_P2.50mm'
FP_CE6 = 'Capacitor_THT:CP_Radial_D6.3mm_P2.50mm'
FP_CE8 = 'Capacitor_THT:CP_Radial_D8.0mm_P3.50mm'
FP_DSMA= 'Diode_SMD:D_SMA'
FP_D123= 'Diode_SMD:D_SOD-123'
FP_FET = 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'
FP_REG = 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'
FP_TB  = 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal'
FP_PTC_IN = 'Fuse:Fuse_2920_7451Metric'
FP_PTC = 'Fuse:Fuse_1812_4532Metric'
FP_L   = 'Inductor_THT:L_Radial_D7.8mm_P5.00mm_Fastron_07HCP'
FP_POT = 'Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical'
FP_SMA = 'Connector_Coaxial:SMA_Amphenol_132134-11_Vertical'
def hdr(n): return f'Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical'
def idc(n): return f'Connector_IDC:IDC-Header_2x{n:02d}_P2.54mm_Vertical'   # shrouded, keyed
SOIC = {8: 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 14: 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',
        20: 'Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm', 28: 'Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm'}
NFET = 'Transistor_FET:Q_NMOS_GDS'                # IRLL2705TRPBF: 55 V, Vgs(th) 1-2 V, 65 mohm at 4 V, SOT-223 (tab = D)

s = Sch('Control Board -- Control Chamber', 'tuner', paper='A2', rev='Rev 3.7c')
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
cell = Grid(20, 285, 27)

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
def CE(val, pos, neg='GND', fp=FP_CE5):
    return two('Device:C_Polarized', 'C', val, pos, neg, fp)
def D(part, anode, cathode, fp=FP_D123, sym='Device:D_Schottky'):
    return two(sym, 'D', part, anode, cathode, fp, pins=('A', 'K'))

def chip(lib_id, ref, val, x, y, units, fp, dx=27.94):
    """one symbol per unit, side by side; returns them in unit order"""
    return [A(lib_id, ref, val, (x + i * dx, y), footprint=fp, unit=u) for i, u in enumerate(units)]
def unused_gate(g, ins, out):
    for p in ins:
        s.net(g, p, 'GND')                     # CMOS inputs never float
    s.nc(g, out)

# ================= power (8A.1) =================
block('power')
J1 = A('Connector_Generic:Conn_01x02', 'J1', '24V in', (20, 40), footprint=FP_TB)
s.net(J1, 'Pin_1', '+24V_IN'); s.net(J1, 'Pin_2', 'GND')
F1 = A('Device:Polyfuse', 'F1', '2920L185DR', (45, 40), footprint=FP_PTC_IN)    # 1.85 A hold, 33 V
s.net(F1, '1', '+24V_IN'); s.net(F1, '2', '+24V')
# TRACO's reflected-ripple filter (TSR 3 sheet, fig. 1: 220 uF / 1 uH / 150 uF), one
# leg per converter. It is also the first defense against their ~300 kHz harmonics
# landing on 160 m (8A.1).
L1 = A('Device:L', 'L1', '1u 07HCP', (70, 35), footprint=FP_L)
L2 = A('Device:L', 'L2', '1u 07HCP', (70, 60), footprint=FP_L)
s.net(L1, '1', '+24V'); s.net(L1, '2', '+24V_5')
s.net(L2, '1', '+24V'); s.net(L2, '2', '+24V_12')
U1 = A('Converter_DCDC:TSR3-2450N', 'U1', 'TSR 3-2450N', (100, 35),
       footprint='Converter_DCDC:Converter_DCDC_TRACO_TSR2-24xxN_TSR2-24xxxN_THT')
s.net(U1, 'Vin', '+24V_5'); s.net(U1, 'GND', 'GND'); s.net(U1, 'Vout', '+5V')
U2 = A('Converter_DCDC:TSR2-24120N', 'U2', 'TSR 2-24120N', (100, 65),
       footprint='Converter_DCDC:Converter_DCDC_TRACO_TSR2-24xxN_TSR2-24xxxN_THT')
s.net(U2, 'Vin', '+24V_12'); s.net(U2, 'GND', 'GND'); s.net(U2, 'Vout', '+12V')
U3 = A('Regulator_Linear:AMS1117-3.3', 'U3', 'AMS1117-3.3', (135, 35), footprint=FP_REG)
s.net(U3, 'VI', '+5V'); s.net(U3, 'VO', '+3V3'); s.net(U3, 'GND', 'GND')
CE('220u 35V low-ESR', '+24V', fp=FP_CE8)
CE('150u 35V', '+24V_5', fp=FP_CE8)
CE('100u 35V', '+24V_12', fp=FP_CE6)
CE('47u 10V', '+5V')
CE('22u 25V', '+12V')
CE('100u 10V', '+3V3', fp=FP_CE6)              # AMS1117 output stability
C('100n', '+5V', 'GND'); C('100n', '+3V3', 'GND')

# ================= Teensy 4.1, mounted directly =================
block('teensy')
A1 = A('tuner:Teensy4.1', 'A1', 'Teensy 4.1', (300, 115), footprint='tuner:Teensy4.1')
PINMAP = [
    # motion (J-A)
    ('D0', 'STEP1'), ('D1', 'DIR1'), ('D2', 'STEP2'), ('D3', 'DIR2'), ('D4', 'STEP3'),
    ('D7', 'DIR3'),  ('D8', 'DRV_EN'),
    # frequency: FreqCount requires pin 9
    ('D9', 'FREQ_DIV'),
    # encoder SPI (J-A). MOSI carries the AS5048A command frames: diagnostics/AGC and error clear
    ('D13', 'ENC_SCK'), ('D12', 'ENC_MISO'), ('D11', 'ENC_MOSI'),
    ('D10', 'ENC_CS1'), ('D5', 'ENC_CS2'), ('D6', 'ENC_CS3'),
    # ADC: measurement board (J-B), RF tank (J-E), cal-load detector, K1/K2 coil current
    ('D14', 'V_MAG'), ('D15', 'V_PHS'), ('D16', 'V_FWD'), ('D17', 'V_REF_DET'),
    ('D20', 'AD_VREF'), ('D21', 'THERM'), ('D22', 'CT_DC'), ('D23', 'CAL_ADC'),
    ('D38', 'K1_I'), ('D39', 'K2_I'),
    # I2C to the MCP23017: panel encoders, bypass key, every permissive input
    ('D18', 'I2C_SDA'), ('D19', 'I2C_SCL'), ('D41', 'IOX_INT'),
    # limits (J-A): sense only, the cut is hardwired at the driver board (7.2)
    ('D24', 'LIM1'), ('D25', 'LIM2'), ('D26', 'LIM3'), ('D27', 'LIM4'), ('D28', 'LIM5'), ('D29', 'LIM6'),
    # K1/K2 commands (latched, 5.5); the MCU's vote in the permissive and the result
    ('D30', 'RLY1_CMD'), ('D31', 'RLY2_CMD'), ('D32', 'MCU_PERMIT'), ('D36', 'PERMIT'),
    # blower: 33 has PWM, 32 does not; tach in on 40
    ('D33', 'BLOWER_PWM'), ('D40', 'TACH'),
    # Nextion on Serial8: RX8 = 34, TX8 = 35 (Teensy 4.1 only)
    ('D34', 'NEX_RX'), ('D35', 'NEX_TX'),
    ('D37', 'BTN_RECOVERY'),
]
for pin, net in PINMAP:
    s.net(A1, pin, net)
s.net(A1, '25', '+5V')               # pad 25 = Vin
for pad in ('1', '26', '39'):        # all three GND pads
    s.net(A1, pad, 'GND')
# The Teensy's own 3V3 stays off the board rail: two regulators in parallel share
# load unpredictably, and the board rail also feeds the encoder cables.
s.nc(A1, '15'); s.nc(A1, '27')
n_nc = s.nc_rest(A1)
print(f'  no-connect flags on {n_nc} unused Teensy pins')

# ================= J-A: logic to the motor chamber (7.3a) =================
# 26-way ribbon to an FCE17-B25SM-250 DB-25 plug; wire 26 is unused. The edge lines
# (STEP, SCK) sit between grounds.
block('conn')
J2 = A('Connector_Generic:Conn_02x13_Odd_Even', 'J2', 'J-A logic', (40, 125), footprint=idc(13))
JA = {1: 'STEP1_X', 2: 'GND', 3: 'STEP2_X', 4: 'GND', 5: 'STEP3_X', 6: 'GND', 7: 'ENC_SCK_X', 8: 'GND',
      9: 'DIR1_X', 10: 'DIR2_X', 11: 'DIR3_X', 12: 'DRV_EN_X', 13: 'ENC_MOSI_X', 14: 'ENC_MISO_X',
      15: 'ENC_CS1_X', 16: 'ENC_CS2_X', 17: 'ENC_CS3_X', 18: '+3V3', 19: 'GND',
      20: 'LIM1_X', 21: 'LIM2_X', 22: 'LIM3_X', 23: 'LIM4_X', 24: 'LIM5_X', 25: 'LIM6_X'}
for p_, net in JA.items():
    s.net(J2, f'Pin_{p_}', net)
s.nc(J2, 'Pin_26')
block('ja')
LOGIC = ('STEP1', 'STEP2', 'STEP3', 'DIR1', 'DIR2', 'DIR3', 'DRV_EN',
         'ENC_SCK', 'ENC_MOSI', 'ENC_MISO', 'ENC_CS1', 'ENC_CS2', 'ENC_CS3')
LIMS = tuple(f'LIM{i}' for i in range(1, 7))
for net in LOGIC + LIMS:
    R('47', net, net + '_X')                   # 7.3 logic grade: 47 ohm, board side
# Limit senses: NC contacts to ground, so a trip OR a broken wire reads high.
# A Schottky OR of all six feeds the permissive's limit term (7.4).
for net in LIMS:
    R('10k', '+3V3', net)
    D('BAT42W', net, 'LIM_ANY')
R('1M', 'LIM_ANY', 'GND')

# ================= J-B: sampler group (7.3a, 6B.5) =================
# 26-way ribbon to an FCE17-B25SM-290 DB-25 plug (5600 pF); every analog line has
# its own ground, each relay coil its own return.
block('conn')
J3 = A('Connector_Generic:Conn_02x13_Odd_Even', 'J3', 'J-B sampler', (105, 125), footprint=idc(13))
JB = {1: 'V_MAG_X', 2: 'GND', 3: 'V_PHS_X', 4: 'GND', 5: 'V_FWD_X', 6: 'GND', 7: 'V_REF_DET_X', 8: 'GND',
      9: 'AD_VREF_X', 10: 'GND', 11: 'CAL_DET_X', 12: 'GND', 13: 'SWR_OK', 14: 'GND', 15: '+5V', 16: 'GND',
      17: 'CALTH_X', 18: 'GND', 19: 'GND', 20: 'K1_PLUS', 21: 'K1_LO', 22: 'K2_PLUS', 23: 'K2_LO',
      24: 'GND', 25: 'GND'}
for p_, net in JB.items():
    s.net(J3, f'Pin_{p_}', net)
s.nc(J3, 'Pin_26')
block('jb')
for net in ('V_MAG', 'V_PHS', 'V_FWD', 'V_REF_DET', 'AD_VREF'):
    R('1k', net + '_X', net)                   # 7.3 analog grade: 1 k carbon comp
    C('10n', net, 'GND')
# SWR permissive: open drain on the measurement board, 4.7 k pull-up there. The
# pull-down here makes an unplugged ribbon read as a trip.
R('100k', 'SWR_OK', 'GND')
R('1k', 'SWR_OK', 'SWR_OK_L')
# Cal-load thermal switch (6B.3): NC, opens at 85 C; open or broken reads high.
R('10k', '+3V3', 'CALTH_X')
R('1k', 'CALTH_X', 'CALTH_L')

# ---- cal-load RF detector window (6B.3a) ----
block('cal')
# The detector's idle level is +1.0 V through 1 Mohm, so nothing here may load
# it: 100 k into a CMOS follower. The 10 M pull-down is what makes an open line
# read ~0 V and trip the low side, as 6B.3a requires (idle shifts 1.00 -> 0.91 V).
R('10M', 'CAL_DET_X', 'GND')
R('100k', 'CAL_DET_X', 'CAL_DET_IN')
C('1n', 'CAL_DET_IN', 'GND')
u12 = chip('Amplifier_Operational:MCP6002-xSN', 'U12', 'MCP6002', 420, 200, (1, 2, 3), SOIC[8])
s.net(u12[0], '+', 'CAL_DET_IN'); s.net(u12[0], '-', 'CAL_BUF'); s.net(u12[0], '1', 'CAL_BUF')
s.net(u12[1], '+', 'GND');        s.net(u12[1], '-', 'OPB_OUT');  s.net(u12[1], '7', 'OPB_OUT')
s.net(u12[2], 'V+', '+5V');       s.net(u12[2], 'V-', 'GND')
R('10k', 'CAL_BUF', 'CAL_ADC'); R('10k', 'CAL_ADC', 'GND'); C('10n', 'CAL_ADC', 'GND')
# LM393 on 5 V so the 60 W threshold (~2.1 V) is inside its 0-3.5 V common-mode range;
# open-collector outputs wire-AND into CALDET_OK.
u11 = chip('Comparator:LM393', 'U11', 'LM393', 330, 240, (1, 2, 3), SOIC[8])
s.net(u11[0], '+', 'CAL_HI');  s.net(u11[0], '-', 'CAL_BUF'); s.net(u11[0], '1', 'CALDET_OK')
s.net(u11[1], '+', 'CAL_BUF'); s.net(u11[1], '-', 'CAL_LO');  s.net(u11[1], '7', 'CALDET_OK')
s.net(u11[2], 'V+', '+5V');    s.net(u11[2], 'V-', 'GND')
R('10k', '+3V3', 'CALDET_OK')
# high trip: set once with a wattmeter in CAL (6B.3a); RV1 spans 0.86-3.08 V
R('1k', '+3V3', 'CAL_HI_T')
RV1 = A('Device:R_Potentiometer_Trim', 'RV1', '10k 3296W', (560, 240), footprint=FP_POT)
s.net(RV1, '1', 'CAL_HI_T'); s.net(RV1, '3', 'CAL_HI_B'); s.net(RV1, '2', 'CAL_HI')
R('3k9', 'CAL_HI_B', 'GND'); C('100n', 'CAL_HI', 'GND')
# low trip: 0.50 V, below the 0.91 V idle level and above an open or shorted line
R('56k', '+3V3', 'CAL_LO'); R('10k', 'CAL_LO', 'GND'); C('100n', 'CAL_LO', 'GND')

# ---- K1/K2 coil drivers (5.5, 6B.2) ----
block('relay')
# Coils are 24 V Tohtsu CX600N-24 with suppression diodes at the relay (7.3a); the
# diode here clamps the ribbon end too. A PTC per coil survives a shorted cable;
# the 1 ohm source resistor is the coil-current confirmation 6B.2 requires.
for i, (q, f) in enumerate((('Q1', 'F2'), ('Q2', 'F3')), start=1):
    F = A('Device:Polyfuse', f, 'MF-MSMF030/60X-2', (440 + i * 28, 240), footprint=FP_PTC)
    s.net(F, '1', '+24V'); s.net(F, '2', f'K{i}_PLUS')
    Q = A(NFET, q, 'IRLL2705TRPBF', (470 + i * 28, 205), footprint=FP_FET)
    s.net(Q, 'G', f'Q{i}_G'); s.net(Q, 'D', f'K{i}_LO'); s.net(Q, 'S', f'K{i}_SNS')
    R('100', f'K{i}_DRV', f'Q{i}_G'); R('10k', f'Q{i}_G', 'GND')
    R('1R 1W', f'K{i}_SNS', 'GND', fp=FP_RP)
    R('1k', f'K{i}_SNS', f'K{i}_I'); C('100n', f'K{i}_I', 'GND')
    D('S1M', f'K{i}_LO', f'K{i}_PLUS', fp=FP_DSMA, sym='Device:D')

# ================= J-E: RF tank sensors and the RF panel interlock =================
block('je')
# 10-way ribbon to an FCE17-E09SM-290 DE-9 plug: shelf FT1 thermal, FT2 CT,
# FT3 common return, FT4 the RF service-panel switch (NC to chassis when closed).
J4 = A('Connector_Generic:Conn_02x05_Odd_Even', 'J4', 'J-E RF tank', (170, 115), footprint=idc(5))
JE = {1: 'THERM_X', 2: 'GND', 3: 'CT_DC_X', 4: 'GND', 5: 'PANEL_X', 6: 'GND', 7: 'GND', 8: 'GND', 9: 'GND'}
for p_, net in JE.items():
    s.net(J4, f'Pin_{p_}', net)
s.nc(J4, 'Pin_10')
R('10k', '+3V3', 'THERM_X')                    # bias for a 10 k NTC to chassis at the tank
R('1k', 'THERM_X', 'THERM'); C('10n', 'THERM', 'GND')
R('1k', 'CT_DC_X', 'CT_DC'); C('10n', 'CT_DC', 'GND')
R('10k', '+3V3', 'PANEL_X'); R('1k', 'PANEL_X', 'PANEL_L')

# ================= /1024 frequency (7.3 frequency grade) =================
block('freq')
J11 = A('Connector:Conn_Coaxial', 'J11', 'SMA /1024 in', (420, 125), footprint=FP_SMA)   # Cinch 142-0701-201 (Amphenol 132134-11 is 2.6x the price)
s.net(J11, 'In', 'FREQ_X'); s.net(J11, 'Ext', 'GND')
R('1k', 'FREQ_X', 'FREQ_DIV')

# ================= blower (8): 12 V, on by default, PWM down from the MCU =================
block('blower')
# Low-side switch with the gate pulled UP: a dead or resetting MCU leaves the
# blower running, which the bypass (8B.4d) relies on. Tach is open collector,
# 2 pulses/rev; the clamp covers the PWM off-phase, when the fan's ground floats.
J5 = A('Connector_Generic:Conn_01x03', 'J5', 'J-F blower', (200, 150), footprint=hdr(3))
s.net(J5, 'Pin_1', '+12V'); s.net(J5, 'Pin_2', 'BLOWER_LO'); s.net(J5, 'Pin_3', 'TACH_X')
Q3 = A(NFET, 'Q3', 'IRLL2705TRPBF', (556, 205), footprint=FP_FET)
s.net(Q3, 'G', 'Q3_G'); s.net(Q3, 'D', 'BLOWER_LO'); s.net(Q3, 'S', 'GND')
R('100', 'BLOWER_PWM', 'Q3_G'); R('10k', '+3V3', 'Q3_G')
D('SS14', 'BLOWER_LO', '+12V', fp=FP_DSMA)
CE('4.7u 25V', '+12V', 'BLOWER_LO')            # across the fan, per Delta
R('10k', '+3V3', 'TACH_X'); R('10k', 'TACH_X', 'TACH')
D('BAT42W', 'TACH', '+3V3'); D('BAT42W', 'GND', 'TACH')

# ================= local panel (7.5) =================
block('panel')
# Nextion NX4832K035: UART at 3.3 V levels, 5 V supply. Its own 4-pin cable plugs in here.
J6 = A('Connector_Generic:Conn_01x04', 'J6', 'Nextion', (380, 50), footprint=hdr(4))
s.net(J6, 'Pin_1', '+5V'); s.net(J6, 'Pin_2', 'NEX_RX_X'); s.net(J6, 'Pin_3', 'NEX_TX_X'); s.net(J6, 'Pin_4', 'GND')
R('100', 'NEX_RX_X', 'NEX_RX'); R('100', 'NEX_TX', 'NEX_TX_X')
# Grayhill 62V15-02-xxxCH (3.3 V, push-pull A/B, N.O. push): 0.100" connector pinout
for i, j in ((1, 'J7'), (2, 'J8')):
    E = A('Connector_Generic:Conn_01x06', j, f'encoder {i}', (380, 70 + i * 30), footprint=hdr(6))
    for p_, net in ((1, 'GND'), (2, 'GND'), (3, f'ENC{i}_SW'), (4, f'ENC{i}_B'), (5, f'ENC{i}_A'), (6, '+3V3')):
        s.net(E, f'Pin_{p_}', net)
    R('10k', '+3V3', f'ENC{i}_SW')
# Bypass key (8B.4d): forces the bypassable half of the permissive. 1 k limits a
# shorted panel lead; the MCU only reads it (logging, remote indication).
J9 = A('Connector_Generic:Conn_01x02', 'J9', 'bypass key', (420, 50), footprint=hdr(2))
s.net(J9, 'Pin_1', 'BYP_SRC'); s.net(J9, 'Pin_2', 'BYPASS')
R('1k', '+3V3', 'BYP_SRC'); R('10k', 'BYPASS', 'GND'); C('100n', 'BYPASS', 'GND')
# Recovery button (8B.4f.2): recessed, sealed; held through power-up -> recovery mode.
# Deliberately NOT on the Teensy reset line: a hung firmware is the watchdog's job.
J10 = A('Connector_Generic:Conn_01x02', 'J10', 'recovery button', (420, 80), footprint=hdr(2))
s.net(J10, 'Pin_1', 'BTN_RECOVERY'); s.net(J10, 'Pin_2', 'GND')
R('10k', '+3V3', 'BTN_RECOVERY'); C('100n', 'BTN_RECOVERY', 'GND')

# ---- MCP23017: panel inputs and permissive status, one interrupt ----
block('logic')
# GPA7/GPB7 are output-only on current silicon: GPA7 switches the alarm sounder
# (8B.4i), and GPB7 stays unused.
U10 = A('Interface_Expansion:MCP23017x-x-SO', 'U10', 'MCP23017', (500, 115), footprint=SOIC[28])
for pin, net in (('V_{DD}', '+3V3'), ('V_{SS}', 'GND'), ('SCK', 'I2C_SCL'), ('SDA', 'I2C_SDA'),
                 ('A0', 'GND'), ('A1', 'GND'), ('A2', 'GND'), ('~{RESET}', 'IOX_RST'), ('INTA', 'IOX_INT'),
                 ('GPA0', 'ENC1_A'), ('GPA1', 'ENC1_B'), ('GPA2', 'ENC1_SW'),
                 ('GPA3', 'ENC2_A'), ('GPA4', 'ENC2_B'), ('GPA5', 'ENC2_SW'), ('GPA6', 'BYPASS'),
                 ('GPB0', 'SWR_OK_L'), ('GPB1', 'CALDET_OK'), ('GPB2', 'CALTH_OK'), ('GPB3', 'PANEL_OK'),
                 ('GPB4', 'LIMIT_OK'), ('GPB5', 'HARD_OK'), ('GPB6', 'BYP_OK'), ('GPA7', 'SOUNDER')):
    s.net(U10, pin, net)
s.nc_rest(U10)
R('10k', '+3V3', 'IOX_RST'); R('10k', '+3V3', 'IOX_INT')
R('4k7', '+3V3', 'I2C_SDA'); R('4k7', '+3V3', 'I2C_SCL')

# ================= the hardware permissive (7.4) =================
#   BYP_OK  = SWR_OK AND MCU_PERMIT          (what the bypass key may override)
#   HARD_OK = CALDET_OK AND CALTH_OK AND PANEL_OK AND LIMIT_OK   (never bypassed)
#   PERMIT  = (BYP_OK OR BYPASS) AND HARD_OK
#   LED     = PERMIT AND 10 kHz tone         (7.4.2: no tone, no permissive)
# MCU_PERMIT is pulled down, so a hung MCU drops out when its watchdog resets it.
R('100k', 'MCU_PERMIT', 'GND')
u4 = chip('74xx:74LS08', 'U4', '74HC08', 30, 200, (1, 2, 3, 4, 5), SOIC[14])
s.net(u4[0], '1', 'SWR_OK_L'); s.net(u4[0], '2', 'MCU_PERMIT'); s.net(u4[0], '3', 'BYP_OK')
s.net(u4[1], '4', 'BYP_OR');   s.net(u4[1], '5', 'HARD_OK');    s.net(u4[1], '6', 'PERMIT')
s.net(u4[2], '9', 'PERMIT');   s.net(u4[2], '10', 'TONE');      s.net(u4[2], '8', 'LED_DRV')
unused_gate(u4[3], ('12', '13'), '11')
s.net(u4[4], 'VCC', '+3V3');   s.net(u4[4], 'GND', 'GND')
u5 = chip('74xx:74LS32', 'U5', '74HC32', 175, 200, (1, 2, 3, 4, 5), SOIC[14])
s.net(u5[0], '1', 'BYP_OK');   s.net(u5[0], '2', 'BYPASS');     s.net(u5[0], '3', 'BYP_OR')
unused_gate(u5[1], ('4', '5'), '6'); unused_gate(u5[2], ('9', '10'), '8'); unused_gate(u5[3], ('12', '13'), '11')
s.net(u5[4], 'VCC', '+3V3');   s.net(u5[4], 'GND', 'GND')
u6 = chip('74xx:74LS21', 'U6', '74HC21', 320, 200, (1, 2, 3), SOIC[14])
for p_, net in (('1', 'CALDET_OK'), ('2', 'CALTH_OK'), ('4', 'PANEL_OK'), ('5', 'LIMIT_OK'), ('6', 'HARD_OK')):
    s.net(u6[0], p_, net)
unused_gate(u6[1], ('9', '10', '12', '13'), '8')
s.net(u6[2], 'VCC', '+3V3');   s.net(u6[2], 'GND', 'GND')
# Schmitt inverters: switch inputs to OK levels, the limit OR, and the relay blanking timer
u7 = chip('74xx:74HC14', 'U7', '74HC14', 30, 240, (1, 2, 3, 4, 5, 6, 7), SOIC[14])
s.net(u7[0], '1', 'CALTH_L'); s.net(u7[0], '2', 'CALTH_OK')
s.net(u7[1], '3', 'PANEL_L'); s.net(u7[1], '4', 'PANEL_OK')
s.net(u7[2], '5', 'LIM_ANY'); s.net(u7[2], '6', 'LIMIT_OK')
s.net(u7[3], '9', 'BLANK');   s.net(u7[3], '8', 'SWITCH_OK')
unused_gate(u7[4], ('11',), '10'); unused_gate(u7[5], ('13',), '12')
s.net(u7[6], 'VCC', '+3V3');  s.net(u7[6], 'GND', 'GND')

# ---- 10 kHz tone: hardware, so the bypass works with a dead controller ----
# f = 1.44 / ((1k + 2 x 6.8k) x 10n) = 9.9 kHz, 53 % duty; C0G timing cap
U8 = A('Timer:LMC555xM', 'U8', 'LMC555', (250, 240), footprint=SOIC[8])
s.net(U8, 'VCC', '+3V3'); s.net(U8, 'GND', 'GND'); s.net(U8, '~{RST}', '+3V3')
s.net(U8, 'TRIG', 'TIM_C'); s.net(U8, 'THRES', 'TIM_C'); s.net(U8, 'DISCH', 'TIM_D')
s.net(U8, 'CONT', 'TIM_CV'); s.net(U8, 'OUT', 'TONE')
R('1k', '+3V3', 'TIM_D'); R('6k8', 'TIM_D', 'TIM_C')
C('10n C0G', 'TIM_C', 'GND'); C('10n', 'TIM_CV', 'GND')

# ---- LED driver: ~56 mA into the HFBR-1521Z (its 60 mA test point; 80 mA max DC) ----
block('fiber')
R('100', 'LED_DRV', 'Q4_G'); R('10k', 'Q4_G', 'GND')
Q4 = A(NFET, 'Q4', 'IRLL2705TRPBF', (470, 50), footprint=FP_FET)
s.net(Q4, 'G', 'Q4_G'); s.net(Q4, 'S', 'GND'); s.net(Q4, 'D', 'HFBR_K')
U13 = A('tuner:HFBR-1521Z', 'U13', 'HFBR-1521Z', (520, 50), footprint='OptoDevice:AGILENT_HFBR-152x')
s.net(U13, 'A', 'HFBR_A'); s.net(U13, 'K', 'HFBR_K')
for p_ in ('3', '4', '5', '6'):
    s.nc(U13, p_)
R('56 1W', '+5V', 'HFBR_A', fp=FP_RP)

# ---- K1/K2 hold latch and the 30 ms blanking timer (5.5) ----
block('relay')
# PERMIT high charges BLANK at once and closes the latch; after PERMIT falls the
# latch stays shut until BLANK decays past the 74HC14's lower threshold:
# 560k x 100n from 3.0 V to 0.9-1.5 V = 39-67 ms, never under 30 ms.
D('BAT42W', 'PERMIT', 'BL_CHG')
R('1k', 'BL_CHG', 'BLANK'); R('560k', 'BLANK', 'GND'); C('100n C0G', 'BLANK', 'GND')
U9 = A('74xx:74HC373', 'U9', '74HC373', (390, 240), footprint=SOIC[20])
s.net(U9, 'OE', 'GND'); s.net(U9, 'LE', 'SWITCH_OK')
s.net(U9, 'D0', 'RLY1_CMD'); s.net(U9, 'D1', 'RLY2_CMD')
for k in range(2, 8):
    s.net(U9, f'D{k}', 'GND')
s.net(U9, 'O0', 'K1_DRV'); s.net(U9, 'O1', 'K2_DRV')
s.net(U9, 'VCC', '+3V3'); s.net(U9, 'GND', 'GND')
s.nc_rest(U9)
R('100k', 'RLY1_CMD', 'GND'); R('100k', 'RLY2_CMD', 'GND')

# ---- decoupling, one per logic/analog IC ----
block('logic')
for _ in ('U4', 'U5', 'U6', 'U7', 'U8', 'U9', 'U10'):
    C('100n', '+3V3', 'GND')
block('cal')
for _ in ('U11', 'U12'):
    C('100n', '+5V', 'GND')

# ---- alarm sounder (8B.4i), last so that no earlier reference designator moves ----
block('panel')
# Alarm sounder (8B.4i): an active piezo indicator on the cassette face, switched
# low-side from +12 V. The gate is pulled down, so the sounder stays off while the
# expander's outputs float at power-up. The Schottky covers a part whose driver
# has a coil.
J12 = A('Connector_Generic:Conn_01x02', 'J12', 'sounder', (420, 100), footprint=hdr(2))
s.net(J12, 'Pin_1', '+12V'); s.net(J12, 'Pin_2', 'SND_LO')
Q5 = A(NFET, 'Q5', 'IRLL2705TRPBF', (445, 100), footprint=FP_FET)
s.net(Q5, 'G', 'Q5_G'); s.net(Q5, 'D', 'SND_LO'); s.net(Q5, 'S', 'GND')
R('100', 'SOUNDER', 'Q5_G'); R('10k', 'Q5_G', 'GND')
D('BAT42W', 'SND_LO', '+12V')

# ================= power flags =================
block('none')
# +5V, +12V and +3V3 come from power outputs (U1, U2, U3). Flag only the rails
# that reach a power input through passive parts.
for i, (netname, xy) in enumerate((('+24V_5', (20, 80)), ('+24V_12', (45, 80)), ('GND', (70, 80)))):
    f = A('power:PWR_FLAG', f'#FLG{i+1}', 'PWR_FLAG', xy)
    s.net(f, '1', netname)

s.write('control.kicad_sch')
import json
json.dump(BLOCKS, open('control.blocks.json', 'w'), indent=0, sort_keys=True)
print(f'wrote control.kicad_sch: {len(s.comps)} symbols, {len(s.items)//2} connections')
