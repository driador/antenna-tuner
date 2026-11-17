import json, math, cmath, tnet
Z0 = 600.0
d = json.load(open('zant_edges.json'))
pts = sorted([(v[0], float(f), complex(v[1], v[2])) for f, v in d.items()], key=lambda x: x[1])

def zin(f, ZL, Lft, vf=0.95):
    bl = 2*math.pi*f*1e6*Lft*0.3048/(2.998e8*vf)
    t = cmath.tan(bl)
    return Z0*(ZL + 1j*Z0*t)/(Z0 + 1j*ZL*t)

C3S = [0, 50e-12, 100e-12, 150e-12, 200e-12, 300e-12, 400e-12, 600e-12, 835e-12]

def coverage(Lft, c3s, vf=0.95):
    bad = []
    for b, f, ZL in pts:
        Z = zin(f, ZL, Lft, vf)
        if not any(tnet.t_matchable(f, tnet.with_shunt(Z, f, c)) for c in c3s):
            bad.append(f'{b}/{f:.2f}')
    return bad

if __name__ == '__main__':
    print('OPTION C -- plain T plus switchable output shunt capacitance')
    print('Coverage of 27 band-edge points vs TOTAL feeder length (VF 0.95)')
    print()
    print(f"{'ft':>4} | {'plain T':>7} | {'Option C':>8} | unmatched under Option C")
    print('-' * 66)
    full = []
    for Lft in range(40, 95, 2):
        pb = len(coverage(Lft, [0]))
        bad = coverage(Lft, C3S)
        if not bad:
            full.append(Lft)
        print(f'{Lft:4d} | {27-pb:3d}/27 | {27-len(bad):3d}/27  | ' +
              (', '.join(bad) if bad else 'none'), flush=True)
    print()
    print('FULL 27/27 under Option C at:', full)
    runs = []; cur = []
    for L in range(40, 95, 2):
        if L in full: cur.append(L)
        else:
            if cur: runs.append((cur[0], cur[-1])); cur = []
    if cur: runs.append((cur[0], cur[-1]))
    print('Contiguous robust bands:', ', '.join(f'{a}-{b} ft' for a, b in runs))
