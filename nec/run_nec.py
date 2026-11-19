import subprocess, re, os, sys
NEC = os.path.expanduser('~/src/necpp/build/src/nec2++')   # static build (README)
FT = 0.3048
HALF = 170*FT/2.0          # 25.908 m half-length
HEIGHT = 55*FT             # 16.764 m AGL
RAD = 0.0808*0.0254/2.0    # #12 AWG radius, m
EPSR, SIGMA = 13.0, 0.005
CU = 5.8001e7

def deck(nseg, fmhz):
    mid = (nseg+1)//2
    return f"""CM 170 ft doublet, 55 ft AGL, #12 AWG Cu, real ground
CE
GW 1 {nseg} 0 {-HALF:.6f} {HEIGHT:.6f} 0 {HALF:.6f} {HEIGHT:.6f} {RAD:.8f}
GE 1
LD 5 1 0 0 {CU:.6E}
GN 2 0 0 0 {EPSR} {SIGMA}
EX 0 1 {mid} 0 1.0 0.0
FR 0 1 0 0 {fmhz} 0
XQ
EN
"""

def run(nseg, fmhz, tag):
    i, o = f'/tmp/d_{tag}.nec', f'/tmp/d_{tag}.out'
    open(i,'w').write(deck(nseg,fmhz))
    r = subprocess.run([NEC, f'-i{i}', f'-o{o}'], capture_output=True, text=True, timeout=600)
    txt = open(o).read()
    m = re.search(r'ANTENNA INPUT PARAMETERS(.*?)(?:\n\s*\n\s*\n|$)', txt, re.S)
    blk = m.group(1) if m else txt
    nums = re.findall(r'-?\d+\.\d+E[+-]\d+', blk)
    if len(nums) < 8:
        print("PARSE FAIL", tag, r.returncode, txt[-400:]); return None
    # TAG SEG  VOLT(re,im) CURR(re,im) IMPEDANCE(re,im) ADMIT(re,im) POWER
    return float(nums[4]), float(nums[5])

if __name__ == '__main__':
    print("Segmentation convergence at 28.5 MHz (highest band, 4.93 lambda):")
    print(f"  {'segs':>5} {'seg len':>9} {'R (ohm)':>10} {'X (ohm)':>11}")
    prev=None
    for n in (101, 201, 301, 401):
        z = run(n, 28.5, f'c{n}')
        if z:
            d = (170*FT)/n
            delta = '' if prev is None else f'   dR={z[0]-prev[0]:+.1f}  dX={z[1]-prev[1]:+.1f}'
            print(f"  {n:5d} {d:8.3f}m {z[0]:10.1f} {z[1]:+11.1f}{delta}")
            prev=z
