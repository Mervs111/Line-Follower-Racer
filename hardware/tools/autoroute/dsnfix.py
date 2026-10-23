"""Atur kelas net (lebar jalur) dan perbesar keepout lubang/celah di file DSN sebelum FreeRouting."""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf8").read()

CLASSES = [
    ("BIG", 1000, ["VBAT", "BAT+"]),
    ("MOTOR5V", 800, ["ML_P", "ML_N", "MR_P", "MR_N", "+5V", "+5V_BUCK"]),
    ("PWR", 500, ["+3V3", "GND"]),
]
special = {n for _, _, ns in CLASSES for n in ns}
nets = re.findall(r'\(net ("[^"]+"|\S+)\s*\n\s*\(pins', s)
rest = [n for n in nets if n.strip('"') not in special and not n.strip('"').startswith("unconnected")]


def cls(name, w, ns):
    q = " ".join(f'"{n}"' if not re.fullmatch(r"[A-Za-z0-9_+]+", n) else n for n in ns)
    return (f"    (class {name} {q}\n      (circuit\n        (use_via \"Via[0-1]_1300:600_um\")\n      )\n"
            f"      (rule\n        (width {w})\n        (clearance 300)\n      )\n    )\n")


new = cls("SIG", 300, [n.strip('"') for n in rest]) + "".join(cls(*c) for c in CLASSES)
s = re.sub(r"    \(class .*?\n    \)\n(?=    \(class|  \)\n  \(wiring)", "", s, flags=re.S)
s = s.replace("  )\n  (wiring", new + "  )\n  (wiring", 1)

# lubang M3 (keepout lingkaran) -> lingkaran Ø4,4 mm (r 1,6 lubang + 0,5 jarak tepi + cadangan)
def hole(m):
    xs = [float(v) for v in m.group(1).split()]
    px, py = xs[0::2], xs[1::2]
    cx, cy = (max(px) + min(px)) / 2, (max(py) + min(py)) / 2
    if max(px) - min(px) < 4000 and max(py) - min(py) < 4000:     # lingkaran lubang (bukan celah encoder)
        return f'(keepout "" (circle signal 4400 {cx:.0f} {cy:.0f}))'
    x0, x1, y0, y1 = min(px) - 300, max(px) + 300, min(py) - 300, max(py) + 300
    return f'(keepout "" (polygon signal 0  {x0:.0f} {y0:.0f}  {x1:.0f} {y0:.0f}  {x1:.0f} {y1:.0f}  {x0:.0f} {y1:.0f}))'


s = re.sub(r'\(keepout "" \(polygon signal 0\s+([-\d.\s]+)\)\)', hole, s)
open(dst, "w", encoding="utf8").write(s)
print(len(rest), "net sinyal;", s.count("(keepout"), "keepout")
