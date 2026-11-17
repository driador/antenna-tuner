"""Minimal S-expression reader/writer for KiCad 10 files.
Format learned by inspection of /usr/share/kicad/symbols/*.kicad_sym (version 20251024),
not from memory. Atoms are str; lists are python lists.
"""
import io

def parse(text):
    toks, i, n = [], 0, len(text)
    out, stack = [], []
    cur = out
    while i < n:
        c = text[i]
        if c == '(':
            new = []
            cur.append(new); stack.append(cur); cur = new; i += 1
        elif c == ')':
            cur = stack.pop(); i += 1
        elif c == '"':
            j = i + 1; buf = []
            while j < n:
                if text[j] == '\\':
                    buf.append(text[j+1]); j += 2; continue
                if text[j] == '"':
                    break
                buf.append(text[j]); j += 1
            cur.append('"' + ''.join(buf)); i = j + 1
        elif c in ' \t\r\n':
            i += 1
        else:
            j = i
            while j < n and text[j] not in '() \t\r\n"':
                j += 1
            cur.append(text[i:j]); i = j
    return out

def is_str(a):   return isinstance(a, str) and a.startswith('"')
def sval(a):     return a[1:] if is_str(a) else a
def q(s):        return '"' + str(s)   # internal marker form; quoting happens in _atom

def _atom(a):
    '''render an atom. internal strings carry a leading quote as a type marker;
    real quoting and escaping happen here, once, at write time.'''
    if not is_str(a):
        return a
    body = a[1:].replace('\\', '\\\\').replace('"', '\\"')
    return '"' + body + '"'

def dump(node, indent=0, out=None):
    top = out is None
    if top: out = io.StringIO()
    pad = '\t' * indent
    if not isinstance(node, list):
        out.write(_atom(node)); return out.getvalue() if top else None
    simple = all(not isinstance(x, list) for x in node)
    if simple:
        out.write(pad + '(' + ' '.join(_atom(x) for x in node) + ')')
    else:
        out.write(pad + '(' + _atom(node[0]))
        for x in node[1:]:
            if isinstance(x, list):
                out.write('\n'); dump(x, indent + 1, out)
            else:
                out.write(' ' + _atom(x))
        out.write('\n' + pad + ')')
    return out.getvalue() if top else None

def find(node, tag):
    """all direct children that are lists headed by tag"""
    return [c for c in node if isinstance(c, list) and c and c[0] == tag]

def find1(node, tag):
    r = find(node, tag)
    return r[0] if r else None

def load_lib(path):
    root = parse(io.open(path, encoding='utf-8').read())[0]
    return {sval(s[1]): s for s in find(root, 'symbol')}

def resolve(lib, name, seen=None):
    """follow (extends "BASE") inheritance to the symbol that owns the pins"""
    seen = seen or set()
    if name in seen: return lib[name]
    seen.add(name)
    s = lib[name]
    e = find1(s, 'extends')
    if e and sval(e[1]) in lib:
        return resolve(lib, sval(e[1]), seen)
    return s

def pins(sym, lib=None):
    """(number, name, etype) for a symbol, following child unit symbols.
    If the symbol only (extends ...) a base, pass lib to resolve it."""
    if lib is not None and not find(sym, 'symbol'):
        e = find1(sym, 'extends')
        if e and sval(e[1]) in lib:
            sym = resolve(lib, sval(e[1]))
    out = []
    def walk(node):
        for p in find(node, 'pin'):
            num = find1(p, 'number'); nam = find1(p, 'name')
            out.append((sval(num[1]) if num else '?',
                        sval(nam[1]) if nam else '?',
                        p[1] if len(p) > 1 else '?'))
        for sub in find(node, 'symbol'):
            walk(sub)
    walk(sym)
    return out


def pins_unit(sym, unit, lib=None):
    """pins belonging to a given unit, plus unit 0 (common/power).
    KiCad names child symbols NAME_<unit>_<bodystyle>."""
    if lib is not None and not find(sym, 'symbol'):
        e = find1(sym, 'extends')
        if e and sval(e[1]) in lib:
            sym = resolve(lib, sval(e[1]))
    out = []
    for sub in find(sym, 'symbol'):
        nm = sval(sub[1])
        parts = nm.rsplit('_', 2)
        if len(parts) < 3:
            continue
        try: u = int(parts[1])
        except ValueError: continue
        if u not in (0, unit):
            continue
        for pn in find(sub, 'pin'):
            at = find1(pn, 'at'); num = find1(pn, 'number'); nam = find1(pn, 'name')
            if at and num:
                out.append((sval(num[1]), sval(nam[1]) if nam else '',
                            pn[1] if len(pn) > 1 else '?',
                            float(at[1]), float(at[2]), float(at[3])))
    return out
