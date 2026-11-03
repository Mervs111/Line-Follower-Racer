"""Konsep v17: PCB utama ringkas + board interface bertumpuk di depan baterai, sasis skid plate 3D print.

Menulis konsep-v17.html (gambar tampak atas v16 vs usulan + tampak samping, to-scale) dan mencetak hasil cek:
tabrakan kotak 3D antar komponen, komponen keluar outline board, jalur kabel USB, dan zona antena ESP32.
Koordinat robot (mm): x ke kanan, y maju, z naik dari lantai, (0, 0) = tengah poros roda (sama dengan v16).

Jalankan: py mechanical/konsep-v17/gen_konsep.py
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")

# ------------------------------ dari v16 (mechanical/cadquery/ltm_v16.py) ------------------------------
R_W, W_W, WX0 = 17.0, 12.0, 39.5            # roda O34, lebar 12, sisi dalam roda
MAIN_R_V16 = [(37, -34, 10), (37, 20, 3), (50, 23.5, 3), (50, 54, 6), (27, 65, 8), (27, 84, 8), (12, 93, 5)]
H12 = [(-4.75, 85.55), (4.75, 85.55)]       # baut PCB sensor

# ------------------------------ usulan v17 ------------------------------
CH_Z0, CH_Z1 = 10.0, 12.0                    # skid plate 3D print (ganti PCB utama sebagai sasis)
MB = dict(x0=-31.0, x1=31.0, y0=24.0, y1=82.0, r=4.0, z0=15.0)   # PCB utama di atas spacer 3 mm
MB["z1"] = MB["z0"] + 1.6
IB = dict(x0=-24.0, x1=18.0, y0=35.0, y1=77.0, r=3.0, z0=33.0)   # board interface
IB["z1"] = IB["z0"] + 1.6
EY0, EY1 = 32.0, 60.3                        # ESP32 DevKit melintang (USB ke kiri, antena ke kanan)
EY = (EY0 + EY1) / 2
SOCK = 8.5
MBT = MB["z1"]
DK_Z0 = MBT + SOCK                           # sisi bawah PCB DevKit

# (nama, x0, x1, y0, y1, z0, z1, kelas gambar, label pendek)
BOX = []


def box(name, x0, x1, y0, y1, z0, z1, cls, label=None):
    BOX.append((name, x0, x1, y0, y1, z0, z1, cls, label))


# sasis, motor, roda, baterai (tetap seperti v16)
for s in (-1, 1):
    box(f"Motor N20 {'kiri' if s < 0 else 'kanan'}", min(s * 13, s * 38), max(s * 13, s * 38), -6, 6, CH_Z1, CH_Z1 + 10,
        "motor")
    box(f"Roda {'kiri' if s < 0 else 'kanan'}", min(s * WX0, s * (WX0 + W_W)), max(s * WX0, s * (WX0 + W_W)),
        -R_W, R_W, 0, 2 * R_W, "wheel")
box("Dudukan baterai (3D print)", -38, 38, -24, 24, 22, 24, "print")
box("Holder 2x18650", -38, 38, -21, 21, 24, 44, "battery")
# charger 2S di skid plate di antara/di belakang motor, di bawah dudukan baterai, USB-C menghadap ke belakang
box("Charger 2S USB-C (di skid plate)", -12.5, 12.5, -28.0, -12.0, CH_Z1, CH_Z1 + 5.5, "hidden", "charger")
box("Steker USB-C charger", -4.5, 4.5, -48.0, -28.0, CH_Z1 + 0.5, CH_Z1 + 8.0, "keepzone")
# rangka: skid plate, PCB sensor (digantung di bawah hidung skid plate), ball caster di skid plate di belakang PCB sensor
box("Skid plate 3D print", -33, 33, -30, 93, CH_Z0, CH_Z1, "frame")
box("PCB sensor rev B", -47.5, 47.5, 80.0, 131.0, 4.8, 6.4, "frame")
CASTER_Y = 72.0
box("Ball caster", -5, 5, CASTER_Y - 5, CASTER_Y + 5, 0, CH_Z0, "frame")

# PCB utama: baris belakang (konektor), ESP32 di tengah (TB6612 di bawahnya), baris depan (daya, buzzer, J5)
box("J2 motor kiri (JST XH 6)", -30, -15.1, 25, 30.75, MBT, MBT + 9.8, "conn", "J2")
box("J1 baterai (JST XH 2)", -4.2, 4.2, 24.5, 31.3, MBT, MBT + 9.8, "conn", "J1")
box("J3 motor kanan (JST XH 6)", 15.1, 30, 25, 30.75, MBT, MBT + 9.8, "conn", "J3")
box("R1/R2 pembagi baterai", -14.6, -4.9, 25.0, 31.3, MBT, MBT + 2.5, "small", "R1 R2")
box("D1 1N5819", 4.6, 14.6, 26.0, 29.2, MBT, MBT + 2.8, "small", "D1")
for yr in (EY - 12.7, EY + 12.7):
    box("Socket ESP32", -19.05, 19.05, yr - 1.27, yr + 1.27, MBT, DK_Z0, "socket")
box("ESP32 DevKit (PCB + sisi bawah)", -25.75, 25.75, EY0, EY1, DK_Z0 - 1.6, DK_Z0 + 1.6, "esp", "ESP32 DevKit")
box("ESP32 modul", 1.25, 19.25, EY - 9, EY + 9, DK_Z0 + 1.6, DK_Z0 + 4.7, "espmod")
box("ESP32 USB", -26.5, -21.0, EY - 3.8, EY + 3.8, DK_Z0 + 1.6, DK_Z0 + 4.3, "espusb")
box("TB6612 (disolder rendah, di bawah ESP32)", -21.0, -0.5, 35.8, 56.3, MBT, MBT + 5.6, "under", "TB6612")
box("Q1 + R3/R4 buzzer (di bawah ESP32)", 3.0, 14.0, 37.0, 47.0, MBT, MBT + 4.6, "under", "Q1 R3 R4")
box("MP1584", -30.0, -7.5, 62.0, 79.5, MBT, MBT + 8.1, "module", "MP1584")
box("C1 100uF", -6.15, 0.15, 62.85, 69.15, MBT, MBT + 11.0, "small", "C1")
box("Buzzer", 8.0, 20.0, 61.0, 73.0, MBT, MBT + 9.5, "small", "BZ")
box("SW1 saklar (tuas keluar ke kanan)", 21.6, 31.0, 62.0, 73.4, MBT, MBT + 4.4, "small", "SW1")
box("Header ke board interface", -7.2, 8.0, 73.5, 76.0, MBT, IB["z0"], "header", "J6")
box("J5 ke PCB sensor (JST XH 8)", -6.0, 16.4, 76.0, 81.75, MBT, MBT + 9.8, "conn", "J5")

# board interface: OLED di socket + 5 tombol 6x6 + resistor ladder di bawah OLED
IBT = IB["z1"]
box("Socket OLED", -8.1, 2.1, 62.3, 64.8, IBT, IBT + SOCK, "socket")
box("OLED 0,96 inci", -16.65, 10.65, 37.0, 64.8, IBT + SOCK, IBT + SOCK + 2.6, "oled", "OLED")
box("Resistor ladder (di bawah OLED)", -14.0, 8.0, 40.0, 52.0, IBT, IBT + 2.5, "under", "ladder")
BTN_X = [-21 + 3 + i * 8.0 for i in range(5)]
for i, x in enumerate(BTN_X):
    box(f"Tombol {i + 1} (6x6)", x - 3, x + 3, 66.5, 72.5, IBT, IBT + 5.0, "button")

# zona yang harus kosong
KEEP = [
    ("Jalur steker USB ESP32", -48.0, -26.5, EY - 4.5, EY + 4.5, DK_Z0 - 0.5, DK_Z0 + 6.5),
    ("Zona antena ESP32", 19.25, 25.75, EY - 9, EY + 9, MB["z0"], 60.0),
]
BOARDS = [("PCB utama", MB), ("Board interface", IB)]


def overlap(a, b, eps=0.05):
    return all(min(a[i + 1], b[i + 1]) - max(a[i], b[i]) > eps for i in (1, 3, 5))


def inside(b, brd):
    return b[1] >= brd["x0"] - 0.01 and b[2] <= brd["x1"] + 0.01 and b[3] >= brd["y0"] - 0.01 and b[4] <= brd["y1"] + 0.01


problems = []
for i, a in enumerate(BOX):
    for b in BOX[i + 1:]:
        if overlap(a, b) and not ({a[7], b[7]} == {"socket", "esp"} or {a[7], b[7]} == {"socket", "oled"}):
            problems.append(f"tabrakan: {a[0]} x {b[0]}")
    for k in KEEP:
        if overlap(a, k) and not (k[0].startswith("Jalur") and a[0] == "ESP32 USB") and \
                not (k[0].startswith("Zona") and a[0].startswith("ESP32")):
            problems.append(f"masuk {k[0]}: {a[0]}")
for name, brd in BOARDS:
    bb = (name, brd["x0"], brd["x1"], brd["y0"], brd["y1"], brd["z0"], brd["z1"])
    for a in BOX:
        if overlap(a, bb) and a[7] not in ("header",):
            problems.append(f"tabrakan dengan {name}: {a[0]}")
    for k in KEEP:
        if k[0].startswith("Zona") and overlap(bb, k) and name != "PCB utama":
            problems.append(f"{name} menutupi {k[0]}")
for a in BOX:
    if MBT - 0.01 <= a[5] <= MBT + 0.01 and a[7] not in ("motor", "wheel") and not inside(a, MB):
        problems.append(f"keluar outline PCB utama: {a[0]}")
    if IBT - 0.01 <= a[5] <= IBT + 0.01 and not inside(a, IB):
        problems.append(f"keluar outline board interface: {a[0]}")
# komponen di bawah DevKit harus di bawah sisi bawah DevKit (sambungan kaki + chip CH340 kalau ada: 1,6 mm)
for a in BOX:
    if a[7] == "under" and a[0] != "Resistor ladder (di bawah OLED)" and a[6] > DK_Z0 - 1.6:
        problems.append(f"terlalu tinggi di bawah ESP32: {a[0]}")


def rr_area(b):
    w, h, r = b["x1"] - b["x0"], b["y1"] - b["y0"], b["r"]
    return (w * h - (4 - math.pi) * r * r) / 100


# ------------------------------ outline v16 dan PCB sensor ------------------------------
def fillet_dense(right):
    pts = list(right) + [(-x, y, r) for x, y, r in reversed(right)]
    n, out = len(pts), []
    for i in range(n):
        (ax, ay, _), (bx, by, r), (cx, cy, _) = pts[i - 1], pts[i], pts[(i + 1) % n]
        u = ((ax - bx) / math.dist((ax, ay), (bx, by)), (ay - by) / math.dist((ax, ay), (bx, by)))
        v = ((cx - bx) / math.dist((cx, cy), (bx, by)), (cy - by) / math.dist((cx, cy), (bx, by)))
        th = math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1])))
        t = r / math.tan(th / 2)
        bis = (u[0] + v[0], u[1] + v[1])
        lb = math.hypot(*bis)
        c = (bx + bis[0] / lb * r / math.sin(th / 2), by + bis[1] / lb * r / math.sin(th / 2))
        p1, p2 = (bx + u[0] * t, by + u[1] * t), (bx + v[0] * t, by + v[1] * t)
        a1, a2 = math.atan2(p1[1] - c[1], p1[0] - c[0]), math.atan2(p2[1] - c[1], p2[0] - c[0])
        da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        out += [(c[0] + r * math.cos(a1 + da * k / 8), c[1] + r * math.sin(a1 + da * k / 8)) for k in range(9)]
    return out


def poly_area(p):
    return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2


def sensor_outline():
    """Edge.Cuts PCB sensor rev B -> poliline koordinat robot (X = 200 + x, Y = 180,55 - y)"""
    t = open(os.path.join(ROOT, "hardware", "sensor-garis", "sensor-garis.kicad_pcb"), encoding="utf-8").read()
    segs = []
    for m in re.finditer(r'\((gr_line|gr_arc)\s+\(start ([\d.\-]+) ([\d.\-]+)\)\s*(?:\(mid ([\d.\-]+) ([\d.\-]+)\)\s*)?'
                         r'\(end ([\d.\-]+) ([\d.\-]+)\)(?:(?!\(gr_).)*?\(layer "Edge\.Cuts"\)', t, re.S):
        s = (float(m.group(2)), float(m.group(3)))
        e = (float(m.group(6)), float(m.group(7)))
        if m.group(1) == "gr_line":
            pts = [s, e]
        else:
            mid = (float(m.group(4)), float(m.group(5)))
            ax, ay, bx, by, cx, cy = *s, *mid, *e
            d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
            if abs(d) < 1e-9:
                pts = [s, e]
            else:
                ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
                uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
                r = math.dist((ux, uy), s)
                a0, am, a1 = (math.atan2(p[1] - uy, p[0] - ux) for p in (s, mid, e))
                da1 = (am - a0) % (2 * math.pi)
                da = (a1 - a0) % (2 * math.pi)
                if da1 > da:
                    da -= 2 * math.pi
                pts = [(ux + r * math.cos(a0 + da * k / 12), uy + r * math.sin(a0 + da * k / 12)) for k in range(13)]
        segs.append(pts)
    chain = segs.pop(0)
    while segs:
        end = chain[-1]
        j, rev = min(((j, rv) for j in range(len(segs)) for rv in (0, 1)),
                     key=lambda q: math.dist(end, segs[q[0]][-1 if q[1] else 0]))
        sg = segs.pop(j)
        chain += (sg[::-1] if rev else sg)[1:]
    return [(x - 200.0, 180.55 - y) for x, y in chain]


SENSOR = sensor_outline()
V16 = fillet_dense(MAIN_R_V16)
A_V16 = poly_area(V16) / 100
A_MB, A_IB = rr_area(MB), rr_area(IB)
A_SENS = poly_area(SENSOR) / 100

# ------------------------------ gambar SVG ------------------------------
CLS = {  # kelas CSS per jenis
    "motor": "motor", "wheel": "wheel", "print": "print", "battery": "battery", "conn": "conn", "small": "small",
    "socket": "socket", "esp": "esp", "espmod": "espmod", "espusb": "espusb", "under": "under", "module": "module",
    "header": "conn", "oled": "oled", "button": "button", "hidden": "hidden", "keepzone": "keep",
}


def P(x, y):
    return f"{x:.2f},{-y:.2f}"


def poly(pts, cls, extra=""):
    return f'<polygon class="{cls}" points="{" ".join(P(x, y) for x, y in pts)}" {extra}/>'


def rect(x0, x1, y0, y1, cls, r=0.6, extra=""):
    return (f'<rect class="{cls}" x="{x0:.2f}" y="{-y1:.2f}" width="{x1 - x0:.2f}" height="{y1 - y0:.2f}" '
            f'rx="{r}" {extra}/>')


def label(x, y, s, cls="lbl", size=3.0, anchor="middle"):
    return f'<text class="{cls}" x="{x:.2f}" y="{-y:.2f}" font-size="{size}" text-anchor="{anchor}">{s}</text>'


def common_frame():
    out = [poly(SENSOR, "sensor")]
    out.append(label(0, 133.5, "PCB sensor rev B (tetap)", "lbl dim", 3.0))
    for s in (-1, 1):
        x0, x1 = sorted((s * WX0, s * (WX0 + W_W)))
        out.append(rect(x0, x1, -R_W, R_W, "wheel", 2))
        x0, x1 = sorted((s * 13, s * 38))
        out.append(rect(x0, x1, -6, 6, "motor", 1))
    return out


def axle_and_dims(len_lbl):
    return [f'<line class="axis" x1="-54" y1="0" x2="54" y2="0"/>', label(-54, 1.2, "poros", "lbl dim", 2.6, "start")]


def view_v16():
    g = common_frame()
    g.append(poly(V16, "board"))
    g += [rect(-38, 38, -21, 21, "battery-above", 2), label(0, -16.5, "holder 2×18650 (di atas)", "lbl dim", 2.8)]
    g += [rect(-25.75, 25.75, 24.5, 52.8, "esp", 1), label(0, 37, "ESP32 DevKit", "lbl inv", 3.2)]
    g += [rect(28, 48.3, 25, 45.3, "module", 1), label(38.15, 34.5, "TB6612", "lbl inv", 2.8)]
    g += [rect(-13.65, 13.65, 53.5, 81.3, "oled", 1), label(0, 66, "OLED", "lbl light", 3.2)]
    g += [rect(4, 26, -29.5, -12.5, "module", 1), label(15, -22, "MP1584", "lbl inv", 2.8)]
    g += [rect(-29, -4, -29.5, -13.5, "module", 1), label(-16.5, -22, "charger", "lbl inv", 2.8)]
    for x in (-22, 22):
        g.append(rect(x - 6, x + 6, 60, 72, "button", 1))
    g += [f'<circle class="small" cx="38" cy="-51.5" r="6"/>', label(38, 50.4, "BZ", "lbl", 2.6)]
    g += [rect(-50, -45.6, 26, 34.6, "small", 0.5)]
    for hx, hy in H12:
        g.append(f'<circle class="hole" cx="{hx}" cy="{-hy}" r="1.6"/>')
    g += axle_and_dims("127")
    g.append(dim_v(56, -34, 93, "127 mm"))
    g.append(dim_h(-50, 50, -41, "100 mm"))
    return g


def skid_and_battery():
    g = []
    sk = fillet_dense([(38, -30, 6), (38, 24, 3), (33, 30, 4), (33, 80, 8), (14, 93, 5)])
    g.append(poly(sk, "skid"))
    g.append(label(-35.5, -27, "skid plate 3D print", "lbl dim", 2.6, "start"))
    g += [rect(-38, 38, -21, 21, "battery-above", 2), label(0, -16.5, "holder 2×18650 (di atas)", "lbl dim", 2.8)]
    g.append(f'<circle class="caster-top" cx="0" cy="{-CASTER_Y}" r="5"/>')
    return g


def main_board_layer(dim=False):
    """PCB utama + komponennya (+ charger di skid plate); dim=True untuk latar panel tumpukan"""
    g = [f'<g{" class=\"faded\"" if dim else ""}>']
    g.append(rect(MB["x0"], MB["x1"], MB["y0"], MB["y1"], "board", MB["r"]))
    for cls in ["hidden", "conn", "small", "module", "socket", "esp", "espmod", "espusb", "under", "header"]:
        for b in BOX:
            if b[7] != cls or b[5] >= IB["z0"] - 0.01 and cls != "header":
                continue
            if b[0] == "Buzzer":
                g.append(f'<circle class="small" cx="{(b[1] + b[2]) / 2:.2f}" cy="{-(b[3] + b[4]) / 2:.2f}" r="6"/>')
            elif b[0] == "C1 100uF":
                g.append(f'<circle class="small" cx="{(b[1] + b[2]) / 2:.2f}" cy="{-(b[3] + b[4]) / 2:.2f}" r="3.15"/>')
            else:
                g.append(rect(b[1], b[2], b[3], b[4], CLS[b[7]], 0.6))
    for k in KEEP:
        if k[0].startswith("Zona"):
            g.append(rect(k[1], k[2], k[3], k[4], "keep", 0.3))
    if not dim:
        for b in BOX:
            if b[8] and b[7] in ("conn", "small", "header"):
                g.append(label((b[1] + b[2]) / 2, (b[3] + b[4]) / 2 - 1.0, b[8], "lbl", 2.4))
        g += [label(-18.75, 72.5, "MP1584", "lbl inv", 2.8), label(-10.75, 52.5, "TB6612", "lbl", 2.5),
              label(-10.75, 49, "(di bawah)", "lbl", 2.1), label(8.5, 49, "Q1 R3 R4", "lbl", 2.1),
              label(0, 34.6, "ESP32 DevKit", "lbl inv", 2.6), label(22.5, 30.2, "antena", "lbl dim", 2.2),
              label(0, -21.5, "charger", "lbl", 2.5), label(2, -38.5, "USB-C cas", "lbl dim", 2.4, "start"),
              label(-38.5, EY + 6.5, "USB", "lbl dim", 2.4)]
        g.append(f'<line class="usb" x1="-47" y1="{-EY:.2f}" x2="-27.5" y2="{-EY:.2f}" marker-end="url(#arr)"/>')
        g.append(f'<line class="usb" x1="0" y1="41" x2="0" y2="29" marker-end="url(#arr)"/>')
    g.append("</g>")
    return g


def view_v17_main():
    g = common_frame() + skid_and_battery() + main_board_layer()
    for hx, hy in H12:
        g.append(f'<circle class="hole" cx="{hx}" cy="{-hy}" r="1.6"/>')
    g += axle_and_dims("")
    g.append(dim_v(37, MB["y0"], MB["y1"], "58 mm"))
    g.append(dim_h(MB["x0"], MB["x1"], 87.5, "62 mm"))
    return g


def view_v17_stack():
    g = common_frame() + skid_and_battery() + main_board_layer(dim=True)
    g.append(rect(IB["x0"], IB["x1"], IB["y0"], IB["y1"], "iboard", IB["r"]))
    g.append(rect(-14.0, 8.0, 40.0, 52.0, "under", 0.4))
    for b in BOX:
        if b[5] >= IB["z1"] - 0.01 and b[7] in ("oled", "button", "socket"):
            g.append(rect(b[1], b[2], b[3], b[4], CLS[b[7]], 0.8 if b[7] == "button" else 1))
            if b[7] == "button":
                g.append(f'<circle class="cap" cx="{(b[1] + b[2]) / 2:.2f}" cy="{-(b[3] + b[4]) / 2:.2f}" r="1.75"/>')
    g += [label(-3, 52, "OLED", "lbl light", 3.2), label(-3, 47.5, "di socket", "lbl light", 2.3),
          label(-3, 74.3, "5 tombol 6×6", "lbl inv", 2.3)]
    for hx, hy in H12:
        g.append(f'<circle class="hole" cx="{hx}" cy="{-hy}" r="1.6"/>')
    g += axle_and_dims("")
    g.append(dim_h(IB["x0"], IB["x1"], 87.5, "42 mm", "dim2"))
    g.append(dim_v(-28.5, IB["y0"], IB["y1"], "42 mm", "dim2"))
    return g


def dim_v(x, y0, y1, s, cls="dim"):
    return (f'<g class="{cls}"><line x1="{x}" y1="{-y0}" x2="{x}" y2="{-y1}"/>'
            f'<line x1="{x - 1.5}" y1="{-y0}" x2="{x + 1.5}" y2="{-y0}"/><line x1="{x - 1.5}" y1="{-y1}" x2="{x + 1.5}" y2="{-y1}"/>'
            f'<text x="{x + 1.8}" y="{-(y0 + y1) / 2:.2f}" font-size="3" transform="rotate(-90 {x + 1.8} {-(y0 + y1) / 2:.2f})" '
            f'text-anchor="middle" dy="2.4">{s}</text></g>')


def dim_h(x0, x1, y, s, cls="dim"):
    return (f'<g class="{cls}"><line x1="{x0}" y1="{-y}" x2="{x1}" y2="{-y}"/>'
            f'<line x1="{x0}" y1="{-y - 1.5}" x2="{x0}" y2="{-y + 1.5}"/><line x1="{x1}" y1="{-y - 1.5}" x2="{x1}" y2="{-y + 1.5}"/>'
            f'<text x="{(x0 + x1) / 2:.2f}" y="{-y - 1.2:.2f}" font-size="3" text-anchor="middle">{s}</text></g>')


def side_v17():
    """tampak samping dari kiri: y robot ke kanan, z ke atas"""
    g = ['<line class="floor" x1="-42" y1="0" x2="138" y2="0"/>']

    def r(y0, y1, z0, z1, cls, rx=0.4):
        return f'<rect class="{cls}" x="{y0:.2f}" y="{-z1:.2f}" width="{y1 - y0:.2f}" height="{z1 - z0:.2f}" rx="{rx}"/>'
    sens_y = [y for _, y in SENSOR]
    g.append(r(min(sens_y), max(sens_y), 4.8, 6.4, "sensor"))
    g.append(r(-30, 93, CH_Z0, CH_Z1, "skid-side"))
    g.append(f'<circle class="wheel" cx="0" cy="{-R_W}" r="{R_W}"/>')
    g.append(f'<circle class="axis-dot" cx="0" cy="{-R_W}" r="1.2"/>')
    g.append(r(-6, 6, CH_Z1, CH_Z1 + 10, "motor"))
    g.append(r(-24, 24, 22, 24, "print"))
    g.append(r(-21, 21, 24, 44, "battery", 1.5))
    g.append(f'<circle class="caster" cx="{CASTER_Y}" cy="-5" r="5"/>')
    g.append(r(MB["y0"], MB["y1"], MB["z0"], MB["z1"], "board", 0.3))
    for b in BOX:
        if b[7] in ("motor", "wheel", "battery", "print", "frame", "keepzone") or \
                (b[7] == "button" and b[0] != "Tombol 1 (6x6)"):
            continue
        g.append(r(b[3], b[4], b[5], b[6], CLS[b[7]], 0.3))
    g.append(r(IB["y0"], IB["y1"], IB["z0"], IB["z1"], "iboard", 0.3))
    g.append(f'<path class="cable" d="M 79 {-(MBT + 9)} C 88 {-(MBT + 9)}, 92 -14, 94 -7"/>')
    lbls = [(-21, 46.5, "holder 2×18650", "start"), (IB["y1"] + 2, IB["z0"] - 0.2, "board interface", "start"),
            (62, 12.5, "PCB utama", "middle"), (51, 48.5, "OLED", "middle"),
            (104, 8.2, "PCB sensor", "start"), (40, 6.0, "skid plate 3D print", "middle"),
            (CASTER_Y + 6.5, 1.2, "ball caster", "start"), (-30, 6.0, "charger", "start")]
    for y, z, s, anc in lbls:
        g.append(f'<text class="lbl dim" x="{y}" y="{-z}" font-size="2.8" text-anchor="{anc}">{s}</text>')
    g.append(f'<g class="dim"><line x1="135" y1="0" x2="135" y2="{-46.3:.1f}"/>'
             f'<line x1="133.5" y1="-46.3" x2="136.5" y2="-46.3"/>'
             f'<text x="137" y="-23" font-size="3" transform="rotate(-90 137 -23)" text-anchor="middle" dy="2.4">±46 mm</text></g>')
    return g


def svg(body, vb, aria):
    return (f'<svg viewBox="{vb}" role="img" aria-label="{aria}" xmlns="http://www.w3.org/2000/svg">'
            '<defs><marker id="arr" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="4" markerHeight="4" orient="auto">'
            '<path d="M0,0 L6,3 L0,6 z" class="arrowhead"/></marker></defs>'
            + "".join(body) + "</svg>")


top16 = svg(view_v16(), "-58 -136 116 182", "Tampak atas v16: PCB utama bentuk mobil F1 127 kali 100 mm")
top17 = svg(view_v17_main(), "-58 -136 116 182", "Tampak atas usulan v17: PCB utama 62 kali 58 mm")
top17b = svg(view_v17_stack(), "-58 -136 116 182", "Tampak atas usulan v17 dengan board interface 42 kali 42 mm di atasnya")
side17 = svg(side_v17(), "-44 -56 186 62", "Tampak samping usulan v17")

rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in [
    ("PCB utama", "127 × 100 mm, {:.1f} cm²".format(A_V16).replace(".", ","),
     "62 × 58 mm, {:.1f} cm²".format(A_MB).replace(".", ",")),
    ("Board interface", "tidak ada", "42 × 42 mm, {:.1f} cm²".format(A_IB).replace(".", ",")),
    ("Total PCB utama + interface", "{:.1f} cm²".format(A_V16).replace(".", ","),
     "{:.1f} cm² ({:+.0f}%)".format(A_MB + A_IB, (A_MB + A_IB) / A_V16 * 100 - 100).replace(".", ",")),
    ("PCB sensor", "{:.1f} cm²".format(A_SENS).replace(".", ","), "tetap"),
    ("Sasis", "PCB utama", "skid plate 3D print"),
    ("Tombol", "2 × 12×12 mm (GPIO34, GPIO35)", "5 × 6×6 mm, resistor ladder di GPIO34 (GPIO35 bebas)"),
    ("Charger 2S + BMS", "di PCB utama bagian belakang", "charger di skid plate (di bawah dudukan baterai), BMS ditempel di holder"),
])

checks = "".join(f"<li>{p}</li>" for p in problems) or "<li>0 tabrakan antar komponen, semua komponen di dalam outline, jalur USB dan zona antena kosong.</li>"
OK = not problems

html = f"""<title>Konsep LFM v17</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* lembar gambar teknik: kertas hijau-abu, tinta gelap, PCB hijau solder mask, board interface biru */
:root {{
  --bg: #f3f5f2; --paper: #fbfcfa; --ink: #1c2420; --muted: #5d6b63; --line: #c9d2cc;
  --mask: #2f6b47; --mask-edge: #1f4a31; --iface: #2b5d8a; --accent: #b4521f;
  --sensor: #3b3f3d; --wheel: #2a2d2c; --motor: #a8b0ac; --print: #e2c98f; --batt: #6f7f99;
  --module: #4a6fa5; --esp: #24262a; --oled: #101418; --oled-hi: #7fd3ff; --small: #d9b84a; --conn: #f1efe8;
  --under: #c46a3d; --keep: #b4521f; --on-dark: #eef3f0;
  --display: "IBM Plex Sans", system-ui, sans-serif; --mono: "IBM Plex Mono", ui-monospace, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #121614; --paper: #181d1a; --ink: #e4ebe6; --muted: #98a69e; --line: #2e3833;
  --mask: #2f7a4f; --mask-edge: #59a87a; --iface: #4f8cc4; --accent: #e08a5a;
  --sensor: #8a908d; --wheel: #6b706d; --motor: #6d7672; --print: #8a7442; --batt: #7d8db0;
  --module: #6b8fc8; --esp: #3a3d43; --oled: #05080a; --small: #c9a73c; --conn: #d8d4c8; --under: #d9845a; --keep: #e08a5a;
  color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --bg: #121614; --paper: #181d1a; --ink: #e4ebe6; --muted: #98a69e; --line: #2e3833;
  --mask: #2f7a4f; --mask-edge: #59a87a; --iface: #4f8cc4; --accent: #e08a5a;
  --sensor: #8a908d; --wheel: #6b706d; --motor: #6d7672; --print: #8a7442; --batt: #7d8db0;
  --module: #6b8fc8; --esp: #3a3d43; --oled: #05080a; --small: #c9a73c; --conn: #d8d4c8; --under: #d9845a; --keep: #e08a5a;
  color-scheme: dark; }}
body {{ background: var(--bg); color: var(--ink); font-family: var(--display); font-size: 15px; line-height: 1.55;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 28px 48px; }}
main {{ max-width: 1080px; margin: 0 auto; display: grid; gap: 28px; }}
h1 {{ font-size: 1.7rem; font-weight: 600; margin: 0; text-wrap: balance; letter-spacing: -0.01em; }}
h2 {{ font-size: 0.78rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.09em; color: var(--muted); margin: 0 0 10px; }}
p {{ margin: 0; max-width: 68ch; }}
.lead {{ color: var(--muted); }}
.sheets {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
@media (max-width: 980px) {{ .sheets {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 720px) {{ .sheets {{ grid-template-columns: 1fr; }} }}
figure {{ margin: 0; background: var(--paper); border: 1px solid var(--line); border-radius: 6px; padding: 14px; min-width: 0; }}
figcaption {{ font-family: var(--mono); font-size: 0.78rem; color: var(--muted); margin-top: 8px; }}
figure.wide {{ overflow-x: auto; }}
figure.wide svg {{ min-width: 560px; }}
svg {{ width: 100%; height: auto; display: block; }}
svg text {{ font-family: var(--mono); fill: var(--ink); }}
svg .lbl.dim {{ fill: var(--muted); }}
svg .lbl.light {{ fill: var(--oled-hi); }}
svg .lbl.inv {{ fill: var(--on-dark); }}
.faded {{ opacity: 0.35; }}
.caster-top {{ fill: none; stroke: var(--muted); stroke-width: 0.5; stroke-dasharray: 1.2 0.8; }}
.board {{ fill: var(--mask); stroke: var(--mask-edge); stroke-width: 0.5; }}
.iboard {{ fill: var(--iface); stroke: var(--iface); stroke-width: 0.6; }}
.sensor {{ fill: var(--sensor); fill-opacity: 0.85; }}
.skid {{ fill: var(--print); fill-opacity: 0.28; stroke: var(--print); stroke-width: 0.5; stroke-dasharray: 2 1.2; }}
.skid-side {{ fill: var(--print); }}
.wheel {{ fill: var(--wheel); }}
.motor {{ fill: var(--motor); }}
.print {{ fill: var(--print); }}
.battery {{ fill: var(--batt); }}
.battery-above {{ fill: none; stroke: var(--batt); stroke-width: 0.7; stroke-dasharray: 2.5 1.5; }}
.module {{ fill: var(--module); }}
.esp {{ fill: var(--esp); }}
.espmod {{ fill: #9aa3a8; }}
.espusb {{ fill: #c3c8cc; }}
.socket {{ fill: #111; }}
.oled {{ fill: var(--oled); stroke: #2a3138; stroke-width: 0.4; }}
.small {{ fill: var(--small); }}
.conn {{ fill: var(--conn); stroke: #8c8778; stroke-width: 0.35; }}
.under {{ fill: none; stroke: var(--under); stroke-width: 0.6; stroke-dasharray: 1.6 1; }}
.hidden {{ fill: var(--module); fill-opacity: 0.25; stroke: var(--module); stroke-width: 0.5; stroke-dasharray: 1.6 1; }}
.keep {{ fill: var(--keep); fill-opacity: 0.12; stroke: var(--keep); stroke-width: 0.4; stroke-dasharray: 1 0.8; }}
.button {{ fill: #d7dbd9; stroke: #6c736f; stroke-width: 0.3; }}
.cap {{ fill: #23272a; }}
.hole {{ fill: var(--paper); stroke: var(--ink); stroke-width: 0.3; }}
.axis {{ stroke: var(--muted); stroke-width: 0.3; stroke-dasharray: 3 1.5 0.6 1.5; }}
.axis-dot {{ fill: var(--paper); }}
.floor {{ stroke: var(--ink); stroke-width: 0.5; }}
.caster {{ fill: #c3c8cc; stroke: #6c736f; stroke-width: 0.3; }}
.cable {{ fill: none; stroke: var(--accent); stroke-width: 0.8; }}
.usb {{ stroke: var(--muted); stroke-width: 0.5; }}
.arrowhead {{ fill: var(--muted); }}
.dim line {{ stroke: var(--accent); stroke-width: 0.35; }}
.dim text {{ fill: var(--accent); font-family: var(--mono); }}
.dim2 line {{ stroke: var(--iface); stroke-width: 0.35; }}
.dim2 text {{ fill: var(--iface); font-family: var(--mono); }}
.legend {{ display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: 0.85rem; color: var(--muted); }}
.legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
.sw {{ width: 14px; height: 10px; border-radius: 2px; display: inline-block; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.92rem; }}
.tablewrap {{ overflow-x: auto; }}
th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
th {{ font-weight: 500; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; }}
td {{ font-variant-numeric: tabular-nums; }}
td:first-child {{ color: var(--muted); }}
.status {{ display: inline-flex; align-items: center; gap: 8px; font-family: var(--mono); font-size: 0.82rem;
  padding: 4px 10px; border-radius: 999px; border: 1px solid var(--line); background: var(--paper); }}
.dot {{ width: 8px; height: 8px; border-radius: 50%; background: {'#3f9b62' if OK else '#c0432f'}; }}
ol, ul {{ margin: 0; padding-left: 1.2em; display: grid; gap: 6px; max-width: 72ch; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }}
@media (max-width: 720px) {{ .cols {{ grid-template-columns: 1fr; }} }}
.cols > section {{ min-width: 0; }}
</style>
<main>
  <header style="display:grid;gap:10px">
    <h1>Konsep LFM v17: PCB ringkas + board interface</h1>
    <p class="lead">Sasis diganti skid plate 3D print, jadi PCB utama cukup seukuran modulnya. Board interface (OLED + 5 tombol 6×6)
    ditumpuk di atasnya, di depan baterai. Motor, roda, baterai di atas poros, dan PCB sensor rev B tidak berubah. Semua gambar to-scale (mm).</p>
    <span class="status"><span class="dot"></span>Cek otomatis: {len(problems)} masalah</span>
  </header>

  <div class="sheets">
    <figure>{top16}<figcaption>Sekarang (v16): PCB utama = sasis, 127 × 100 mm</figcaption></figure>
    <figure>{top17}<figcaption>Usulan (v17): PCB utama 62 × 58 mm di skid plate 3D print</figcaption></figure>
    <figure>{top17b}<figcaption>Usulan (v17): board interface 42 × 42 mm ditumpuk di atas PCB utama</figcaption></figure>
  </div>
  <div class="legend">
    <span><i class="sw" style="background:var(--mask)"></i>PCB utama</span>
    <span><i class="sw" style="background:var(--iface);opacity:.7"></i>board interface</span>
    <span><i class="sw" style="border:1px dashed var(--under)"></i>komponen pendek di bawah ESP32</span>
    <span><i class="sw" style="background:var(--keep);opacity:.35"></i>zona antena (tanpa tembaga)</span>
    <span><i class="sw" style="border:1px dashed var(--batt)"></i>holder baterai di atas</span>
    <span><i class="sw" style="border:1px dashed var(--module);background:color-mix(in srgb, var(--module) 25%, transparent)"></i>charger di skid plate (di bawah dudukan)</span>
    <span><i class="sw" style="background:var(--print);opacity:.6"></i>skid plate 3D print</span>
  </div>

  <figure class="wide">{side17}<figcaption>Tampak samping v17 (dari kiri, depan ke kanan). Tinggi OLED ±46 mm, sejajar atas holder baterai.</figcaption></figure>

  <section>
    <h2>Angka</h2>
    <div class="tablewrap"><table><thead><tr><th></th><th>v16</th><th>Usulan v17</th></tr></thead><tbody>{rows}</tbody></table></div>
  </section>

  <div class="cols">
    <section>
      <h2>Susunan</h2>
      <ul>
        <li><b>PCB utama</b>: belakang J2, J1 baterai, J3, R1/R2, D1; tengah ESP32 DevKit melintang di socket (USB ke kiri, antena ke kanan);
        depan MP1584, C1, buzzer, SW1 (tuas ke kanan), header J6 ke board interface, J5 ke PCB sensor (kabel lurus ke depan).</li>
        <li><b>Ball caster</b> pindah ke skid plate tepat di belakang PCB sensor (y ±72 mm dari poros). Di v16 caster masih di baut PCB sensor dan
        bertabrakan dengan PCB sensor (celah ke lantai cuma 4,8 mm).</li>
        <li><b>Di bawah ESP32</b> (celah socket 8,5 mm): TB6612 disolder rendah tanpa socket, Q1 + R3/R4 buzzer.</li>
        <li><b>Board interface</b>: socket OLED, 5 tombol 6×6 sebaris, resistor ladder di bawah OLED. Ke PCB utama lewat J6 6 pin:
        3V3, GND, SDA, SCL, tombol (GPIO34), cadangan.</li>
        <li><b>Charger 2S</b> pindah ke skid plate di belakang motor, di bawah dudukan baterai, USB-C menghadap ke belakang.
        <b>BMS</b> (tanpa konektor) ditempel di holder baterai. Keduanya tidak lagi di PCB.</li>
      </ul>
    </section>
    <section>
      <h2>Perlu dicek / diputuskan</h2>
      <ol>
        <li>Fungsi 5 tombol (usul: kiri, kanan, OK, atas, bawah, atau START/STOP).</li>
        <li>TB6612 di bawah ESP32: ringkas, tapi ESP32 harus dicabut dulu untuk melihat TB6612.</li>
        <li>Sisi bawah ESP32 DevKit yang dibeli: kalau ada chip (CH340 di bawah), celah untuk TB6612 tinggal ±1 mm.</li>
        <li>Ukuran modul charger 2S yang dibeli: konsep memakai 25 × 16 mm dengan USB-C di sisi panjang (seperti model v16).</li>
        <li>Harga cetak: 3 desain PCB (sensor, utama, interface); tanya apakah bisa digabung satu panel.</li>
      </ol>
    </section>
  </div>

  <section>
    <h2>Hasil cek otomatis (kotak 3D tiap komponen)</h2>
    <ul>{checks}</ul>
  </section>
</main>
"""

out = os.path.join(HERE, "konsep-v17.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"luas: v16 {A_V16:.1f} cm2, PCB utama {A_MB:.1f}, interface {A_IB:.1f}, total {A_MB + A_IB:.1f} "
      f"({(A_MB + A_IB) / A_V16 * 100 - 100:+.0f}%), sensor {A_SENS:.1f}")
print(f"titik outline sensor: {len(SENSOR)}, y {min(y for _, y in SENSOR):.1f}..{max(y for _, y in SENSOR):.1f}")
print("masalah:" if problems else "masalah: tidak ada")
for p in problems:
    print(" -", p)
print("tulis", out)
