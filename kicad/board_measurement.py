#!/usr/bin/env python3
"""Measurement board, Sampler chamber -- 1500W Doublet Tuner Rev 3.4.

NO MICROCONTROLLER (Section 8B.0). Everything leaves as filtered DC plus one
29 kHz logic line, so a single Teensy 4.1 on the Control board does the lot.

  - 6 dB resistive splitter on each coupled port
  - Schottky envelope detectors        -> V_FWD, V_REF_DET  (DC out)
  - AD8302 gain/phase detector         -> V_MAG, V_PHS, AD_VREF (DC out)
  - Frequency front end + 74AC4040 /1024 -> 29 kHz max, crosses the bulkhead
  - Protection comparator, open drain, wire-ANDed into PERMISSIVE
  - local 3V3 from the bulkhead 5V

OFF-BOARD: Stockton coupler (chassis toroids), 60 dB SMA attenuator chains.
"""
from gen_sch import Sch

FP_R  = 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'
FP_C  = 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
FP_CE = 'Capacitor_THT:CP_Radial_D5.0mm_P2.50mm'
FP_D  = 'Diode_SMD:D_SOD-323'
FP_SMA= 'Connector_Coaxial:SMA_Amphenol_132134-11_Vertical'
FP_REG= 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'
FP_IDC= 'Connector_IDC:IDC-Header_2x08-1MP_P2.54mm_Latch6.5mm_Vertical'

s = Sch('Measurement Board -- Sampler Chamber', 'tuner')
A = s.sym

# ---------- forward RF channel ----------
J1 = A('Connector:Conn_Coaxial','J1','FWD from coupler',(20,30),footprint=FP_SMA)
R1 = A('Device:R','R1','16R5',(45,30),footprint=FP_R)
R2 = A('Device:R','R2','16R5',(68,18),footprint=FP_R)
R3 = A('Device:R','R3','16R5',(68,45),footprint=FP_R)
J2 = A('Connector:Conn_Coaxial','J2','FWD to 60dB pad',(92,45),footprint=FP_SMA)
s.net(J1,'In','FWD_CPL'); s.net(J1,'Ext','GND')
s.net(R1,'1','FWD_CPL'); s.net(R1,'2','FWD_SPLIT')
s.net(R2,'1','FWD_SPLIT'); s.net(R2,'2','FWD_DET_IN')
s.net(R3,'1','FWD_SPLIT'); s.net(R3,'2','FWD_TO_PAD')
s.net(J2,'In','FWD_TO_PAD'); s.net(J2,'Ext','GND')

# ---------- reflected RF channel ----------
J4 = A('Connector:Conn_Coaxial','J4','REF from coupler',(20,110),footprint=FP_SMA)
R4 = A('Device:R','R4','16R5',(45,110),footprint=FP_R)
R5 = A('Device:R','R5','16R5',(68,98),footprint=FP_R)
R6 = A('Device:R','R6','16R5',(68,125),footprint=FP_R)
J5 = A('Connector:Conn_Coaxial','J5','REF to 60dB pad',(92,125),footprint=FP_SMA)
s.net(J4,'In','REF_CPL'); s.net(J4,'Ext','GND')
s.net(R4,'1','REF_CPL'); s.net(R4,'2','REF_SPLIT')
s.net(R5,'1','REF_SPLIT'); s.net(R5,'2','REF_DET_IN')
s.net(R6,'1','REF_SPLIT'); s.net(R6,'2','REF_TO_PAD')
s.net(J5,'In','REF_TO_PAD'); s.net(J5,'Ext','GND')

# ---------- Schottky envelope detectors ----------
for ref,din,out,rr,cc,y in (('D1','FWD_DET_IN','V_FWD','R7','C1',18),
                            ('D2','REF_DET_IN','V_REF_DET','R8','C2',98)):
    D = A('Device:D_Schottky',ref,'HSMS-2850',(95,y),footprint=FP_D)
    R = A('Device:R',rr,'10k',(115,y+8),footprint=FP_R)
    C = A('Device:C',cc,'100n',(132,y+8),footprint=FP_C)
    s.net(D,'A',din); s.net(D,'K',out)
    s.net(R,'1',out); s.net(R,'2','GND')
    s.net(C,'1',out); s.net(C,'2','GND')

# ---------- AD8302 vector detector ----------
J3 = A('Connector:Conn_Coaxial','J3','FWD from pad',(150,55),footprint=FP_SMA)
J6 = A('Connector:Conn_Coaxial','J6','REF from pad',(150,85),footprint=FP_SMA)
U1 = A('RF:AD8302xRU','U1','AD8302',(185,70),footprint='Package_SO:TSSOP-14_4.4x5mm_P0.65mm')
s.net(J3,'In','FWD_ATT'); s.net(J3,'Ext','GND')
s.net(J6,'In','REF_ATT'); s.net(J6,'Ext','GND')
s.net(U1,'INPB','FWD_ATT'); s.net(U1,'INPA','REF_ATT')
s.net(U1,'VPOS','+3V3A'); s.net(U1,'COMM','GND')
s.net(U1,'VMAG','V_MAG'); s.net(U1,'VPHS','V_PHS')
s.net(U1,'VREF','AD_VREF'); s.net(U1,'MSET','AD_VREF'); s.net(U1,'PSET','AD_VREF')
for ref,pin,x in (('C3','OFSA',150),('C4','OFSB',165),('C5','MFLT',205),('C6','PFLT',220)):
    c = A('Device:C',ref,'1n',(x,112),footprint=FP_C)
    s.net(c,'1','U1_'+pin); s.net(c,'2','GND'); s.net(U1,pin,'U1_'+pin)
C7 = A('Device:C','C7','100n',(212,48),footprint=FP_C); s.net(C7,'1','+3V3A'); s.net(C7,'2','GND')
C8 = A('Device:C','C8','1u',(228,48),footprint=FP_C);   s.net(C8,'1','+3V3A'); s.net(C8,'2','GND')

# ---------- frequency front end ----------
R9  = A('Device:R','R9','470R',(115,32),footprint=FP_R)
D3  = A('Device:D_Schottky','D3','BAT54',(132,24),footprint=FP_D)
D4  = A('Device:D_Schottky','D4','BAT54',(132,42),footprint=FP_D)
U2  = A('Comparator:TLV3501AID','U2','TLV3501',(158,32),
        footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
R10 = A('Device:R','R10','1M',(180,24),footprint=FP_R)
R11 = A('Device:R','R11','10k',(40,150),footprint=FP_R)
R12 = A('Device:R','R12','10k',(40,176),footprint=FP_R)
s.net(R9,'1','FWD_DET_IN'); s.net(R9,'2','FREQ_RAW')
s.net(D3,'A','FREQ_RAW'); s.net(D3,'K','+3V3A')
s.net(D4,'K','FREQ_RAW'); s.net(D4,'A','GND')
s.net(U2,'+','FREQ_RAW'); s.net(U2,'-','FREQ_BIAS'); s.net(U2,'6','FREQ_TTL')
s.net(U2,'V+','+3V3A'); s.net(U2,'V-','GND'); s.net(U2,'SHDN','+3V3A')
s.net(R10,'1','FREQ_TTL'); s.net(R10,'2','FREQ_RAW')
s.net(R11,'1','+3V3A'); s.net(R11,'2','FREQ_BIAS')
s.net(R12,'1','FREQ_BIAS'); s.net(R12,'2','GND')

# ---------- /1024 prescaler (Section 8B.0.1) ----------
# 29.7 MHz -> 29 kHz, so the count crosses a 1000 pF feedthrough with RF
# rejection intact. AC variant: plain HC is marginal at 29.7 MHz on 3.3 V.
U4 = A('4xxx:4040','U4','74AC4040',(205,32),footprint='Package_DIP:DIP-16_W7.62mm')
C11 = A('Device:C','C11','100n',(232,24),footprint=FP_C)
s.net(U4,'CLK','FREQ_TTL')
s.net(U4,'Q9','FREQ_DIV')        # Q9 = /1024
s.net(U4,'Reset','GND')
s.net(U4,'VDD','+3V3A'); s.net(U4,'VSS','GND')
s.net(C11,'1','+3V3A'); s.net(C11,'2','GND')
for q in ('Q0','Q1','Q2','Q3','Q4','Q5','Q6','Q7','Q8','Q10','Q11'):
    s.nc(U4,q)        # only Q9 (/1024) is used

# ---------- protection comparator -> PERMISSIVE wire-AND ----------
U3A = A('Comparator:LM393','U3','LM393',(185,150),unit=1,footprint='Package_DIP:DIP-8_W7.62mm')
U3B = A('Comparator:LM393','U3','LM393',(225,150),unit=2,footprint='Package_DIP:DIP-8_W7.62mm')
U3P = A('Comparator:LM393','U3','LM393',(225,178),unit=3,footprint='Package_DIP:DIP-8_W7.62mm')
R13 = A('Device:R','R13','10k',(150,140),footprint=FP_R)
R14 = A('Device:R','R14','10k',(150,158),footprint=FP_R)
R15 = A('Device:R','R15','4k7',(212,132),footprint=FP_R)
s.net(R13,'1','+3V3A'); s.net(R13,'2','SWR_TRIP_REF')
s.net(R14,'1','SWR_TRIP_REF'); s.net(R14,'2','GND')
s.net(U3A,'+','SWR_TRIP_REF'); s.net(U3A,'-','V_REF_DET'); s.net(U3A,'1','PERMISSIVE')
s.net(U3B,'+','GND'); s.net(U3B,'-','+3V3A'); s.nc(U3B,'7')
s.net(U3P,'V+','+3V3A'); s.net(U3P,'V-','GND')
s.net(R15,'1','+3V3A'); s.net(R15,'2','PERMISSIVE')

# ---------- local 3V3 ----------
U5 = A('Regulator_Linear:AMS1117-3.3','U5','AMS1117-3.3',(55,175),footprint=FP_REG)
C9  = A('Device:C_Polarized','C9','10u',(78,182),footprint=FP_CE)
C10 = A('Device:C','C10','100n',(95,182),footprint=FP_C)
s.net(U5,'VI','+5V'); s.net(U5,'VO','+3V3A'); s.net(U5,'GND','GND')
s.net(C9,'1','+3V3A'); s.net(C9,'2','GND')
s.net(C10,'1','+3V3A'); s.net(C10,'2','GND')

# ---------- bulkhead to Control, with the Section 7.3 RC filters ----------
# Analogue: 1k + 0.01uF -> 15.9 kHz. Frequency: 1k + 1000pF -> 159 kHz, which
# passes 29 kHz while still rejecting HF.
J7 = A('Connector_Generic:Conn_02x08_Odd_Even','J7','bulkhead to Control',(265,120),
       footprint=FP_IDC)
FILT = [('V_MAG','R16','C12','0.01u',1),  ('V_PHS','R17','C13','0.01u',3),
        ('V_FWD','R18','C14','0.01u',5),  ('V_REF_DET','R19','C15','0.01u',7),
        ('AD_VREF','R20','C16','0.01u',9),('FREQ_DIV','R21','C17','1n',11)]
for i,(net,rr,cc,cval,pin) in enumerate(FILT):
    R = A('Device:R',rr,'1k',(240,40+i*24),footprint=FP_R)
    C = A('Device:C',cc,cval,(258,52+i*24),footprint=FP_C)
    s.net(R,'1',net); s.net(R,'2',net+'_F')
    s.net(C,'1',net+'_F'); s.net(C,'2','GND')
    s.net(J7,f'Pin_{pin}',net+'_F')
s.net(J7,'Pin_13','PERMISSIVE')
s.net(J7,'Pin_15','+5V')
for p in (2,4,6,8,10,12,14,16):
    s.net(J7,f'Pin_{p}','GND')

for i,(nm,xy) in enumerate((('+5V',(30,205)),('GND',(70,220)))):
    f = A('power:PWR_FLAG',f'#FLG{i+1}','PWR_FLAG',xy)
    s.net(f,'1',nm)

s.write('measurement.kicad_sch')
print(f'wrote measurement.kicad_sch: {len(s.comps)} components, {len(s.items)//2} connections')
