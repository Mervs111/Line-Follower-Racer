"""Pembaca simbol KiCad (.kicad_sym) sederhana untuk generator skematik.

Mengambil satu simbol dari library (termasuk yang memakai `extends`, diratakan), mengganti namanya jadi
"Lib:Nama" untuk bagian lib_symbols skematik, dan membaca posisi pin unit 1 (titik sambung + arah).
"""
import os
import re
import subprocess
import tempfile

KICAD_SYM = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"


def _block(s, start):
    """potongan S-expression seimbang mulai dari indeks '(' di start"""
    depth, i, instr = 0, start, False
    while True:
        ch = s[i]
        if instr:
            if ch == "\\":
                i += 1
            elif ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
        i += 1


def _find_symbol(text, name):
    m = re.search(r'\(symbol "%s"' % re.escape(name), text)
    if not m:
        raise KeyError(name)
    return _block(text, m.start())


def _children(block):
    """anak langsung dari sebuah blok (daftar string)"""
    out, depth, i, instr, start = [], 0, 0, False, None
    while i < len(block):
        ch = block[i]
        if instr:
            if ch == "\\":
                i += 1
            elif ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch == "(":
            depth += 1
            if depth == 2:
                start = i
        elif ch == ")":
            if depth == 2:
                out.append(block[start:i + 1])
            depth -= 1
        i += 1
    return out


_cache = {}


def _lib_text(lib, extra_dirs):
    if lib not in _cache:
        for d in list(extra_dirs) + [KICAD_SYM]:
            p = os.path.join(d, lib + ".kicad_sym")
            if os.path.exists(p):
                text = open(p, encoding="utf8").read()
                ver = int(re.search(r"\(version (\d+)\)", text).group(1))
                if ver < 20250000:                      # format lama (mis. ltm, KiCad 7): naikkan dulu lewat kicad-cli
                    tmp = os.path.join(tempfile.mkdtemp(), lib + ".kicad_sym")
                    subprocess.run([KICAD_CLI, "sym", "upgrade", "-o", tmp, p], check=True, capture_output=True)
                    text = open(tmp, encoding="utf8").read()
                _cache[lib] = text
                break
        else:
            raise FileNotFoundError(lib)
    return _cache[lib]


def load(lib_id, extra_dirs=()):
    """kembalikan (teks simbol untuk lib_symbols, daftar pin)"""
    lib, name = lib_id.split(":")
    text = _lib_text(lib, extra_dirs)
    blk = _find_symbol(text, name)
    ext = re.search(r'\(extends "([^"]+)"\)', blk)
    if ext:                                             # ratakan: badan dari induk, properti induk ditimpa anak
        parent = _find_symbol(text, ext.group(1))

        def pname(c):
            return re.match(r'\(property "([^"]*)"', c).group(1)
        child = {pname(c): c for c in _children(blk) if c.startswith("(property")}
        props = [child.pop(pname(c), c) for c in _children(parent) if c.startswith("(property")]
        props += list(child.values())
        keep = [c for c in _children(parent) if not c.startswith("(property")]
        body = []
        for c in keep:
            c = re.sub(r'^\(symbol "%s_' % re.escape(ext.group(1)), '(symbol "%s_' % name, c)
            body.append(c)
        blk = '(symbol "%s"\n' % name + "\n".join(props + body) + "\n)"
    blk = blk.replace('(symbol "%s"' % name, '(symbol "%s"' % lib_id, 1)
    pins = []
    for c in _children(blk):
        m = re.match(r'\(symbol "[^"]*_(\d+)_(\d+)"', c)
        if not m or m.group(1) not in ("0", "1") or m.group(2) not in ("0", "1"):
            continue
        for p in re.finditer(r'\(pin (\w+) \w+\s*\(at ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)\)', c):
            pb = _block(c, p.start())
            nm = re.search(r'\(name "([^"]*)"', pb).group(1)
            num = re.search(r'\(number "([^"]*)"', pb).group(1)
            pins.append(dict(type=p.group(1), x=float(p.group(2)), y=float(p.group(3)),
                             ang=float(p.group(4)), name=nm, num=num))
    return blk, pins
