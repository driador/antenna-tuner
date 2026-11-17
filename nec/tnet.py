import math, cmath
# Closed-form T-network solver.
# Topology: 50ohm -- series C1 -- node -- shunt L to gnd -- series C2 -- Zload
# Derivation: with Z1 = R + jX1 (X1 = Xload - 1/wC2) and XL = wL,
#   Re(Z2) = XL^2 * R / (R^2 + (X1+XL)^2)  = 50
#   => (X1+XL)^2 = R*(XL^2/50 - R),  requires XL >= sqrt(50R)
#   => X1 = -XL +/- sqrt(R*(XL^2/50 - R))
#   Im(Z2) = XL*(X1*(X1+XL) + R^2) / (R^2 + (X1+XL)^2);  C1 = 1/(w*Im(Z2)), needs Im(Z2)>0
CMIN, CMAX = 25e-12, 835e-12
LMIN, LMAX = 0.15e-6, 60e-6

def t_solve(f_mhz, Zload, L_h):
    w = 2*math.pi*f_mhz*1e6
    R, Xl = Zload.real, Zload.imag
    if R <= 0: return None
    XL = w*L_h
    disc = R*(XL*XL/50.0 - R)
    if disc < 0: return None
    s = math.sqrt(disc)
    for X1 in (-XL + s, -XL - s):
        d = Xl - X1                      # = 1/(w C2)
        if d <= 0: continue
        C2 = 1.0/(w*d)
        if not (CMIN <= C2 <= CMAX): continue
        den = R*R + (X1+XL)**2
        imZ2 = XL*(X1*(X1+XL) + R*R)/den
        if imZ2 <= 0: continue
        C1 = 1.0/(w*imZ2)
        if not (CMIN <= C1 <= CMAX): continue
        return (C1, C2, L_h)
    return None

LGRID = [LMIN*(LMAX/LMIN)**(k/299) for k in range(300)]

def t_matchable(f_mhz, Zload):
    for L in LGRID:
        r = t_solve(f_mhz, Zload, L)
        if r: return r
    return None

def with_shunt(Zload, f_mhz, C3):
    """Add shunt C3 across the load."""
    if C3 <= 0: return Zload
    w = 2*math.pi*f_mhz*1e6
    return 1.0/(1.0/Zload + 1j*w*C3)
