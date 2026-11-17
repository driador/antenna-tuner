#!/usr/bin/env python3
"""Control board, Control chamber -- 1500W Doublet Tuner Rev 3.4.

Scope (Sections 7.1-7.4, 8A, 8B, 8C):
  - 3x stepper STEP/DIR to external driver modules
  - 3x absolute encoder on a shared SPI bus
  - 6x limit switch sense (the HARD cut goes direct to driver EN, Section 7.2)
  - 2x vacuum relay coil drive, low-side, with flyback
  - blower drive
  - POF link to bench: data strand + independent interlock strand (Section 8C.3)
  - UART and permissive to the measurement board
  - local panel: display + 2 manual encoders
  - 24 V in, 5 V via buck module, 3V3 for logic

OFF-BOARD, connectors only: NUCLEO (ribbon), stepper driver modules, POF
transceivers, 24->5 V buck module, encoders, limit switches, relay coils.
"""
from gen_sch import Sch

FP_R   = 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'
FP_C   = 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
FP_CE  = 'Capacitor_THT:CP_Radial_D5.0mm_P2.50mm'
FP_D   = 'Diode_THT:D_DO-41_SOD81_P7.62mm_Horizontal'
FP_FET = 'Package_TO_SOT_THT:TO-220-3_Vertical'
FP_REG = 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'
FP_TB  = 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal'
def hdr(n): return f'Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical'
FP_IDC = 'Connector_IDC:IDC-Header_2x20-1MP_P2.54mm_Latch6.5mm_Vertical'

s = Sch('Control Board -- Control Chamber', 'tuner')
A = s.sym

# ================= power =================
J1 = A('Connector_Generic:Conn_01x02', 'J1', '24V in',      (30, 25),  footprint=FP_TB)
J2 = A('Connector_Generic:Conn_01x04', 'J2', 'buck 24->5V', (30, 55),  footprint=hdr(4))
U1 = A('Regulator_Linear:AMS1117-3.3', 'U1', 'AMS1117-3.3', (70, 55),  footprint=FP_REG)
C1 = A('Device:C',  'C1', '100n', (90, 62), footprint=FP_C)
C2 = A('Device:C_Polarized', 'C2', '100u', (105, 62), footprint=FP_CE)
C3 = A('Device:C',  'C3', '100n', (120, 62), footprint=FP_C)
C4 = A('Device:C_Polarized', 'C4', '220u', (55, 35),  footprint=FP_CE)
s.net(J1,'Pin_1','+24V');  s.net(J1,'Pin_2','GND')
s.net(J2,'Pin_1','+24V');  s.net(J2,'Pin_2','GND')
s.net(J2,'Pin_3','+5V');   s.net(J2,'Pin_4','GND')
s.net(U1,'VI','+5V');      s.net(U1,'VO','+3V3');  s.net(U1,'GND','GND')
s.net(C1,'1','+5V');  s.net(C1,'2','GND')
s.net(C2,'1','+3V3'); s.net(C2,'2','GND')
s.net(C3,'1','+3V3'); s.net(C3,'2','GND')
s.net(C4,'1','+24V'); s.net(C4,'2','GND')

# ================= steppers (external driver modules) =================
for i, (ref, xy) in enumerate((('J3',(30,95)), ('J4',(30,125)), ('J5',(30,155))), start=1):
    j = A('Connector_Generic:Conn_01x04', ref, f'stepper drv {i}', xy, footprint=hdr(4))
    s.net(j,'Pin_1',f'STEP{i}'); s.net(j,'Pin_2',f'DIR{i}')
    s.net(j,'Pin_3','DRV_EN');   s.net(j,'Pin_4','GND')

# ================= encoders: shared SPI =================
J6 = A('Connector_Generic:Conn_01x08', 'J6', 'encoders SPI', (80, 95), footprint=hdr(8))
for pin, net in (('Pin_1','+3V3'),('Pin_2','GND'),('Pin_3','ENC_SCK'),('Pin_4','ENC_MISO'),
                 ('Pin_5','ENC_CS1'),('Pin_6','ENC_CS2'),('Pin_7','ENC_CS3'),('Pin_8','GND')):
    s.net(J6, pin, net)

# ================= limit switches =================
# Section 7.2: the limit switch cut is wired DIRECTLY to the driver enable pin.
# These lines are sense only, so firmware can report which axis tripped.
J7 = A('Connector_Generic:Conn_01x08', 'J7', 'limit switches', (72, 150), footprint=hdr(8))
for n in range(1, 7):
    r = A('Device:R', f'R{n}', '10k', (118, 70 + n*24), footprint=FP_R)
    s.net(r,'1','+3V3'); s.net(r,'2',f'LIM{n}')
    s.net(J7, f'Pin_{n}', f'LIM{n}')
s.net(J7,'Pin_7','GND'); s.net(J7,'Pin_8','GND')

# ================= vacuum relay drive =================
# Low-side switch, flyback across the coil. Section 5.5 forbids hot switching;
# sequencing is firmware + the hardware blanking timer, not this stage.
J8 = A('Connector_Generic:Conn_01x04', 'J8', 'relay coils -> RF tank', (215, 40), footprint=hdr(4))
for i, (q, d, rg, rp, y) in enumerate(((('Q1'),'D1','R7','R9', 30), (('Q2'),'D2','R8','R10', 80)), start=1):
    Q = A('Transistor_FET:IRLZ44N', q, 'IRLZ44N', (165, y), footprint=FP_FET)
    D = A('Diode:1N4007', d, '1N4007', (190, y-16), footprint=FP_D)
    RG = A('Device:R', rg, '100R', (140, y), footprint=FP_R)
    RP = A('Device:R', rp, '10k',  (140, y+24), footprint=FP_R)
    s.net(RG,'1',f'RLY{i}_GATE'); s.net(RG,'2',f'Q{i}_G')
    s.net(RP,'1',f'Q{i}_G');      s.net(RP,'2','GND')
    s.net(Q,'G',f'Q{i}_G');       s.net(Q,'S','GND');  s.net(Q,'D',f'RLY{i}_LO')
    s.net(D,'A',f'RLY{i}_LO');    s.net(D,'K','+24V')
    s.net(J8, f'Pin_{i*2-1}', '+24V'); s.net(J8, f'Pin_{i*2}', f'RLY{i}_LO')

# ================= blower =================
Q3 = A('Transistor_FET:IRLZ44N', 'Q3', 'IRLZ44N', (165, 135), footprint=FP_FET)
D3 = A('Diode:1N4007', 'D3', '1N4007', (190, 120), footprint=FP_D)
R11 = A('Device:R', 'R11', '100R', (140, 135), footprint=FP_R)
R12 = A('Device:R', 'R12', '10k',  (140, 159), footprint=FP_R)
J9  = A('Connector_Generic:Conn_01x02', 'J9', 'blower', (210, 135), footprint=hdr(2))
s.net(R11,'1','BLOWER_PWM'); s.net(R11,'2','Q3_G')
s.net(R12,'1','Q3_G');       s.net(R12,'2','GND')
s.net(Q3,'G','Q3_G'); s.net(Q3,'S','GND'); s.net(Q3,'D','BLOWER_LO')
s.net(D3,'A','BLOWER_LO'); s.net(D3,'K','+24V')
s.net(J9,'Pin_1','+24V');  s.net(J9,'Pin_2','BLOWER_LO')

# ================= POF link to the bench =================
# Two independent strands: data, and the Section 7.4 interlock permissive.
# Section 8C.3: data goes over Ethernet (PJRC kit, chamber wall, no board parts).
# The POF strand carries ONLY the interlock permissive.
J10 = A('Connector_Generic:Conn_01x04', 'J10', 'POF interlock TX', (200, 130), footprint=hdr(4))
for pin, net in (('Pin_1','+3V3'),('Pin_2','GND'),('Pin_3','INTLK_MOD'),('Pin_4','GND')):
    s.net(J10, pin, net)

# ================= bulkhead to the measurement board =================
# Measurement board has no MCU (Section 8B.0): five analogue lines, the /1024
# frequency, and the permissive, all with interleaved grounds.
J11 = A('Connector_Generic:Conn_02x08_Odd_Even', 'J11', 'to measurement bd', (200, 165),
        footprint='Connector_IDC:IDC-Header_2x08-1MP_P2.54mm_Latch6.5mm_Vertical')
for pin, net in (('Pin_1','V_MAG'),('Pin_3','V_PHS'),('Pin_5','V_FWD'),
                 ('Pin_7','V_REF_DET'),('Pin_9','AD_VREF'),('Pin_11','FREQ_DIV'),
                 ('Pin_13','PERMISSIVE'),('Pin_15','+5V')):
    s.net(J11, pin, net)
for p_ in (2,4,6,8,10,12,14,16):
    s.net(J11, f'Pin_{p_}', 'GND')

# ================= sensors from the RF tank =================
# Interconnect-map crossing #7: rectified in the RF tank, DC only across the wall.
J12 = A('Connector_Generic:Conn_01x06', 'J12', 'thermal + imbalance CT', (255, 30), footprint=hdr(6))
for pin, net in (('Pin_1','+3V3'),('Pin_2','GND'),('Pin_3','THERM'),
                 ('Pin_4','CT_DC'),('Pin_5','GND'),('Pin_6','GND')):
    s.net(J12, pin, net)

# ================= local panel =================
J13 = A('Connector_Generic:Conn_01x08', 'J13', 'local panel', (255, 70), footprint=hdr(8))
# Display and BOTH manual encoders sit behind an I2C expander on the panel
# itself, so only a bus and an interrupt cross to this board. That also frees
# four ribbon pins that quadrature lines would otherwise have consumed.
for pin, net in (('Pin_1','+3V3'),('Pin_2','GND'),('Pin_3','PANEL_SDA'),('Pin_4','PANEL_SCL'),
                 ('Pin_5','PANEL_INT'),('Pin_6','GND'),('Pin_7','PANEL_RST'),('Pin_8','GND')):
    s.net(J13, pin, net)

# ================= local action button (Section 8B.4f.2) =================
# Recessed, sealed, panel mount. Held through power-up -> recovery mode.
# Deliberately NOT on the Teensy reset line: a hung firmware is the watchdog's job.
J15 = A('Connector_Generic:Conn_01x02', 'J15', 'recovery button', (255, 185), footprint=hdr(2))
R13 = A('Device:R', 'R13', '10k', (235, 180), footprint=FP_R)
C5  = A('Device:C', 'C5', '100n', (252, 204), footprint=FP_C)
s.net(R13,'1','+3V3');   s.net(R13,'2','BTN_RECOVERY')
s.net(C5,'1','BTN_RECOVERY'); s.net(C5,'2','GND')
s.net(J15,'Pin_1','BTN_RECOVERY'); s.net(J15,'Pin_2','GND')

# ================= Teensy 4.1, mounted directly =================
A1 = A('tuner:Teensy4.1', 'A1', 'Teensy 4.1', (300, 110), footprint='tuner:Teensy4.1')
PINMAP = [
    # steppers
    ('D0', 'STEP1'), ('D1', 'DIR1'), ('D2', 'STEP2'), ('D3', 'DIR2'), ('D4', 'STEP3'),
    ('D7', 'DIR3'),  ('D8', 'DRV_EN'),
    # frequency: FreqCount requires pin 9
    ('D9', 'FREQ_DIV'),
    # encoder SPI
    ('D13', 'ENC_SCK'), ('D12', 'ENC_MISO'), ('D11', 'ENC_MOSI'),
    ('D10', 'ENC_CS1'), ('D5', 'ENC_CS2'), ('D6', 'ENC_CS3'),
    # measurement ADCs
    ('D14', 'V_MAG'), ('D15', 'V_PHS'), ('D16', 'V_FWD'), ('D17', 'V_REF_DET'),
    ('D20', 'AD_VREF'), ('D21', 'THERM'), ('D22', 'CT_DC'),
    # panel I2C
    ('D18', 'PANEL_SDA'), ('D19', 'PANEL_SCL'), ('D34', 'PANEL_INT'), ('D35', 'PANEL_RST'),
    # limits
    ('D24', 'LIM1'), ('D25', 'LIM2'), ('D26', 'LIM3'), ('D27', 'LIM4'), ('D28', 'LIM5'), ('D29', 'LIM6'),
    # actuators and link
    ('D30', 'RLY1_GATE'), ('D31', 'RLY2_GATE'), ('D32', 'BLOWER_PWM'),
    ('D33', 'INTLK_MOD'), ('D36', 'PERMISSIVE'), ('D37', 'BTN_RECOVERY'),
]
for pin, net in PINMAP:
    s.net(A1, pin, net)
s.net(A1, '25', '+5V')               # pad 25 = Vin
for pad in ('1', '26', '39'):        # all three GND pads
    s.net(A1, pad, 'GND')
s.net(A1, '27', '+3V3')              # pad 27 = top-row 3V3 output
s.nc(A1, '15')                       # pad 15 = bottom-row 3V3, same rail, unused

n_nc = s.nc_rest(A1)
print(f'  no-connect flags on {n_nc} unused Teensy pins')

# ================= power flags =================
# +3V3 comes from U1's VO (a power output); flagging it too would be a second
# power output on one net. Flag only the rails arriving passively.
for i, (netname, xy) in enumerate((('+24V',(30,185)), ('+5V',(60,185)), ('GND',(90,185)))):
    f = A('power:PWR_FLAG', f'#FLG{i+1}', 'PWR_FLAG', xy)
    s.net(f, '1', netname)

s.write('control.kicad_sch')
print(f'wrote control.kicad_sch: {len(s.comps)} components, {len(s.items)//2} connections')
