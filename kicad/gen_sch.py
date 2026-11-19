#!/usr/bin/env python3
"""Generate a KiCad 10 .kicad_sch programmatically.

Connections are made with pin stubs + net labels rather than routed wires.
That is valid KiCad and produces a correct netlist; it is not a pretty
hand-drawn schematic. Rearrange in eeschema if you want it prettier.
"""
import math, os, sys, hashlib
import sexpr

LIBDIR = '/usr/share/kicad/symbols'
GRID = 1.27

def uid(*parts):
    h = hashlib.sha1(('|'.join(map(str, parts))).encode()).hexdigest()
    return f'{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}'

class Sch:
    def __init__(self, title, project, paper='A3', rev='Rev 3.4'):
        self.title, self.project = title, project
        self.paper, self.rev = paper, rev
        self.libs, self.used = {}, {}
        self.items, self.comps = [], []
        self._conn = []

    def _lib(self, name):
        if name not in self.libs:
            local = os.path.join(os.path.dirname(os.path.abspath(__file__)), name + '.kicad_sym')
            path = local if os.path.exists(local) else os.path.join(LIBDIR, name + '.kicad_sym')
            self.libs[name] = sexpr.load_lib(path)
        return self.libs[name]

    @staticmethod
    def snap(v):
        """KiCad connection grid is 1.27 mm; off-grid pins do not connect"""
        return round(round(v / GRID) * GRID, 4)

    def sym(self, lib_id, ref, value, at, footprint='', unit=1):
        at = (self.snap(at[0]), self.snap(at[1]))
        libname, symname = lib_id.split(':')
        d = self._lib(libname)
        if symname not in d:
            raise KeyError(f'{lib_id} not found')
        self.used[lib_id] = d[symname]
        up = sexpr.pins_unit(d[symname], unit, d)
        c = dict(lib_id=lib_id, ref=ref, value=value, at=at, unit=unit,
                 footprint=footprint,
                 pins=[(n, nm, et) for n, nm, et, _, _, _ in up],
                 geo={n: (x, y, a) for n, _, _, x, y, a in up})
        self.comps.append(c)
        return c

    @staticmethod
    def _pin_geo(symdef):
        """{pin_number: (x, y, angle)} in symbol coords"""
        g = {}
        def walk(n):
            for p in sexpr.find(n, 'pin'):
                at = sexpr.find1(p, 'at'); num = sexpr.find1(p, 'number')
                if at and num:
                    g[sexpr.sval(num[1])] = (float(at[1]), float(at[2]), float(at[3]))
            for s in sexpr.find(n, 'symbol'):
                walk(s)
        walk(symdef)
        return g

    def pin_xy(self, comp, pin):
        """absolute schematic coords of a pin's connection point"""
        num = self._resolve(comp, pin)
        px, py, ang = comp['geo'][num]
        X, Y = comp['at']
        return (X + px, Y - py, ang)

    @staticmethod
    def _resolve(comp, pin):
        pin = str(pin)
        if pin in comp['geo']:
            return pin
        for num, nam, _ in comp['pins']:
            if nam == pin or pin in nam.split('/'):
                return num
        raise KeyError(f"{comp['ref']}: no pin {pin!r}")

    def net(self, comp, pin, name, stub=5.08):
        self._conn.append((comp, pin))
        x, y, ang = self.pin_xy(comp, pin)
        dx, dy = -math.cos(math.radians(ang)), math.sin(math.radians(ang))
        ex, ey = round(x + dx*stub, 4), round(y + dy*stub, 4)
        self.items.append(['wire',
            ['pts', ['xy', f'{x}', f'{y}'], ['xy', f'{ex}', f'{ey}']],
            ['stroke', ['width', '0'], ['type', 'default']],
            ['uuid', sexpr.q(uid('w', comp['ref'], pin, name))]])
        lang = '0' if abs(dx) >= abs(dy) else '90'
        self.items.append(['label', sexpr.q(name),
            ['at', f'{ex}', f'{ey}', lang],
            ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left', 'bottom']],
            ['uuid', sexpr.q(uid('l', comp['ref'], pin, name))]])

    def nc(self, comp, pin):
        """place a no-connect flag on a pin"""
        x, y, _ = self.pin_xy(comp, pin)
        self.items.append(['no_connect', ['at', f'{x}', f'{y}'],
                           ['uuid', sexpr.q(uid('nc', comp['ref'], pin))]])

    def nc_rest(self, comp, skip_types=('power_in','power_out')):
        """no-connect every pin of comp that has no net, except power pins"""
        wired = {self._resolve(comp, p) for (r, p) in self._conn if r is comp}
        n = 0
        for num, nam, et in comp['pins']:
            if num in wired or et in skip_types:
                continue
            self.nc(comp, num); n += 1
        return n

    def build(self):
        root = ['kicad_sch',
            ['version', '20251024'],
            ['generator', sexpr.q('tuner-gen')],
            ['generator_version', sexpr.q('10.0')],
            ['uuid', sexpr.q(uid('sheet', self.title))],
            ['paper', sexpr.q(self.paper)],
            ['title_block',
                ['title', sexpr.q(self.title)],
                ['company', sexpr.q(f'1500W Doublet Tuner  {self.rev}')]]]
        lib = ['lib_symbols']
        for lib_id, sd in sorted(self.used.items()):
            libname = lib_id.split(':')[0]
            d = self._lib(libname)
            ext = sexpr.find1(sd, 'extends')
            if ext and sexpr.sval(ext[1]) in d:
                # lib_symbols entries must be SELF-CONTAINED: KiCad cannot resolve
                # (extends ...) inside a .kicad_sch. Splice the base symbol's graphic
                # and pin content under the derived name, keeping derived properties.
                base = sexpr.resolve(d, sexpr.sval(ext[1]))
                derived_props = {sexpr.sval(pr[1]): pr for pr in sexpr.find(sd, 'property')}
                out = [sd[0], sexpr.q(lib_id)]
                for child in base[2:]:
                    if isinstance(child, list) and child[0] == 'property':
                        nm = sexpr.sval(child[1])
                        out.append(derived_props.get(nm, child))
                    elif isinstance(child, list) and child[0] == 'symbol':
                        # rename unit children to match the new parent name
                        c = [x for x in child]
                        old = sexpr.sval(child[1])
                        suffix = '_'.join(old.rsplit('_', 2)[-2:])
                        c[1] = sexpr.q(f"{lib_id.split(':')[1]}_{suffix}")
                        out.append(c)
                    else:
                        out.append(child)
                lib.append(out)
            else:
                e = [x for x in sd]
                e[1] = sexpr.q(lib_id)
                lib.append(e)
        root.append(lib)
        for c in self.comps:
            X, Y = c['at']
            u = uid('sym', c['ref'])
            node = ['symbol',
                ['lib_id', sexpr.q(c['lib_id'])],
                ['at', f'{X}', f'{Y}', '0'],
                ['unit', str(c['unit'])],
                ['exclude_from_sim', 'no'], ['in_bom', 'yes'],
                ['on_board', 'yes'], ['dnp', 'no'],
                ['uuid', sexpr.q(u)],
                ['property', sexpr.q('Reference'), sexpr.q(c['ref']),
                    ['at', f'{X-1.27}', f'{Y-8.89}', '0'],
                    ['effects', ['font', ['size','1.27','1.27']], ['justify','right']]],
                ['property', sexpr.q('Value'), sexpr.q(c['value']),
                    ['at', f'{X-1.27}', f'{Y-6.35}', '0'],
                    ['effects', ['font', ['size','1.02','1.02']], ['justify','right']]],
                ['property', sexpr.q('Footprint'), sexpr.q(c['footprint']),
                    ['at', f'{X}', f'{Y}', '0'],
                    ['effects', ['font', ['size','1.27','1.27']], ['hide','yes']]],
                ['instances',
                    ['project', sexpr.q(self.project),
                        ['path', sexpr.q('/' + uid('sheet', self.title)),
                            ['reference', sexpr.q(c['ref'])], ['unit', str(c['unit'])]]]]]
            root.append(node)
        root.extend(self.items)
        root.append(['sheet_instances', ['path', sexpr.q('/'), ['page', sexpr.q('1')]]])
        root.append(['embedded_fonts', 'no'])
        return root

    def check(self):
        """Catch stub collisions: two pin stubs that are collinear and overlapping
        merge into one net silently. This has bitten twice -- limit switches shorted
        to +3V3, and filter outputs merged -- so it is checked, not eyeballed."""
        segs = []
        for it in self.items:
            if it[0] != 'wire':
                continue
            pts = it[1]
            (x1, y1) = (float(pts[1][1]), float(pts[1][2]))
            (x2, y2) = (float(pts[2][1]), float(pts[2][2]))
            segs.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
        labels = {}
        for it in self.items:
            if it[0] == 'label':
                labels[(round(float(it[2][1]), 3), round(float(it[2][2]), 3))] = sexpr.sval(it[1])
        bad = []
        for i in range(len(segs)):
            ax1, ay1, ax2, ay2 = segs[i]
            for j in range(i + 1, len(segs)):
                bx1, by1, bx2, by2 = segs[j]
                # overlapping (not merely touching) and collinear
                ox = min(ax2, bx2) - max(ax1, bx1)
                oy = min(ay2, by2) - max(ay1, by1)
                if ox > 1e-6 and oy > 1e-6:
                    bad.append((segs[i], segs[j]))
                elif (abs(ax1 - ax2) < 1e-6 and abs(bx1 - bx2) < 1e-6
                      and abs(ax1 - bx1) < 1e-6 and oy > 1e-6):
                    bad.append((segs[i], segs[j]))
                elif (abs(ay1 - ay2) < 1e-6 and abs(by1 - by2) < 1e-6
                      and abs(ay1 - by1) < 1e-6 and ox > 1e-6):
                    bad.append((segs[i], segs[j]))
        if bad:
            msg = [f'{len(bad)} overlapping stub pair(s) -- these MERGE NETS silently:']
            for a, b in bad[:8]:
                la = labels.get((round(a[0],3), round(a[1],3))) or labels.get((round(a[2],3), round(a[3],3)))
                lb = labels.get((round(b[0],3), round(b[1],3))) or labels.get((round(b[2],3), round(b[3],3)))
                msg.append(f'   {la} <-> {lb}   at ({a[0]:.2f},{a[1]:.2f}) / ({b[0]:.2f},{b[1]:.2f})')
            raise RuntimeError('\n'.join(msg))
        return len(segs)

    def write(self, path):
        n = self.check()
        open(path, 'w').write(sexpr.dump(self.build()) + '\n')
        print(f'  stub-collision check passed over {n} wires')
