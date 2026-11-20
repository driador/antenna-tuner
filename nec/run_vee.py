# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

import subprocess, re, os, math
NEC = os.path.expanduser('~/src/necpp/build/src/nec2++')   # static build (README)
FT=0.3048; RAD=0.0808*0.0254/2.0; EPSR,SIGMA=13.0,0.005; CU=5.8001e7
LEG=85*FT   # 85 ft of wire per leg (170 ft total)

def deck(nseg, fmhz, h_peak_ft, h_end_ft):
    hp, he = h_peak_ft*FT, h_end_ft*FT
    drop = hp-he
    if drop >= LEG: raise ValueError('drop exceeds leg length')
    horiz = math.sqrt(LEG**2 - drop**2)
    return f"""CM 170ft doublet as inverted-V / sloper, apex {h_peak_ft}ft, ends {h_end_ft}ft
CM leg={LEG/FT:.1f}ft wire, horizontal run={horiz/FT:.1f}ft per leg
CE
GW 1 {nseg} 0 0 {hp:.6f} 0 {-horiz:.6f} {he:.6f} {RAD:.8f}
GW 2 {nseg} 0 0 {hp:.6f} 0 {horiz:.6f} {he:.6f} {RAD:.8f}
GE 1
LD 5 1 0 0 {CU:.6E}
LD 5 2 0 0 {CU:.6E}
GN 2 0 0 0 {EPSR} {SIGMA}
EX 0 1 1 0 1.0 0.0
FR 0 1 0 0 {fmhz} 0
XQ
EN
"""

def run(nseg, fmhz, hp, he, tag):
    i,o=f'/tmp/v_{tag}.nec',f'/tmp/v_{tag}.out'
    open(i,'w').write(deck(nseg,fmhz,hp,he))
    r=subprocess.run([NEC,f'-i{i}',f'-o{o}'],capture_output=True,text=True,timeout=900)
    txt=open(o).read()
    m=re.search(r'ANTENNA INPUT PARAMETERS(.*?)(?:\n\s*\n\s*\n|$)',txt,re.S)
    nums=re.findall(r'-?\d+\.\d+E[+-]\d+', m.group(1) if m else txt)
    if len(nums)<8: return None
    return float(nums[4]), float(nums[5])
