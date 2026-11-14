"""Konsep v18: baterai satu bidang dengan PCB utama (tidak lagi bertingkat di atas motor). PCB tidak diubah.

Membandingkan susunan sekarang (v17) dengan 3 cara menaruh baterai di skid plate:
  pelana  2 holder tunggal melintang, mengapit motor (depan dan belakang poros)      -> usulan
  ekor    holder 2x18650 rebah di belakang poros
  tengah  holder 2x18650 rebah di antara poros dan PCB utama
Menulis konsep-v18.html (tampak atas + tampak samping, to-scale) dan mencetak hasil cek: tabrakan kotak 3D, komponen
di dalam skid plate, zona kosong USB/saklar, batas ukuran lomba, serta perkiraan titik berat dan inersia putar.

PCB utama rev B dan board interface rev A dibaca sekali dari KiCad (courtyard tiap footprint, 14/11/2026) lalu ditulis
di tabel MB_PART / IB_PART; kalau layout PCB berubah, tabel itu ikut diperbarui.
Koordinat robot (mm): x ke kanan, y maju, z naik dari lantai, (0, 0) = tengah poros roda (sama dengan v16/v17).

Jalankan: py mechanical/konsep-v18/gen_konsep.py
"""
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")

G, MU = 9.81, 0.6                           # mu ban = asumsi docs/perhitungan-motor.md bagian 3
R_W, W_T = 17.0, 18.0                       # ban O34 x 18 (velg 3D print, keputusan 03/11)
CH_Z0, CH_Z1 = 10.0, 12.0                   # skid plate 3D print
WELL = 20.5                                 # coakan roda: setengah panjang (celah ±4 mm ke ban)
NOSE_HW, NOSE_Y = 31.0, 93.0                # hidung skid plate v17
K_SIDE = (57.5 - NOSE_HW) / 125.0           # kemiringan sisi skid plate v17 = sisi PCB utama trapesium
CASTER_Y = 72.0
LIMIT = (250.0, 200.0, 100.0, 350.0)        # guidebook IARC XII SD: p, l, t (mm), massa (g, butir C)

# ------------------------------ PCB (tetap): dari KiCad, posisi pada v17 (dy = 0) ------------------------------
MB_Y0, MB_Y1, MB_XR, MB_XF = 24.0, 82.0, 43.3, 31.0      # trapesium rev B
MB_Z0 = 15.0                                # di atas spacer 3 mm
MBT = MB_Z0 + 1.6
SOCK = 8.5
DK_Z0 = MBT + SOCK                          # sisi bawah PCB DevKit
EY = 46.15                                  # tengah ESP32 (melintang, USB kiri, antena kanan)
# (label, x0, x1, y0, y1, tinggi di atas PCB, kelas)
MB_PART = [
    ("J2", -34.90, -16.41, 24.66, 31.50, 9.8, "conn"), ("J1", -4.25, 4.25, 24.66, 31.50, 9.8, "conn"),
    ("J3", 16.41, 34.90, 24.66, 31.50, 9.8, "conn"), ("", -16.29, -6.49, 24.66, 31.15, 2.5, "small"),
    ("", 4.80, 11.10, 24.95, 31.25, 11.0, "round"), ("SW1", -43.75, -34.25, 32.76, 44.25, 4.4, "small"),
    ("MP1584", -30.19, -7.60, 61.71, 79.30, 8.1, "module"), ("", -7.40, 5.56, 70.36, 73.65, 2.8, "small"),
    ("BZ", 18.50, 30.50, 61.50, 73.50, 9.5, "round"), ("J5", -7.50, 16.00, 74.91, 81.75, 9.8, "conn"),
]
MB_HOLE = [(-38.5, 29.0), (38.5, 29.0), (-32.5, 56.0), (32.5, 56.0)]
ESP = (-25.75, 25.75, EY - 14.15, EY + 14.15)
J6 = (-7.41, 8.91, 65.69, 69.32)            # socket ke board interface
IB = (-27.05, 19.05, 42.95, 79.05)          # board interface rev A, z 33
IB_Z0 = 33.0
IBT = IB_Z0 + 1.6
OLED = (-17.65, 9.65, 47.4, 75.2)
OLED_SOCK = (-9.62, 1.62, 71.84, 75.47)
BTN = [(-22.5, 70.0), (-22.5, 52.0), (14.5, 70.0), (14.5, 61.0), (14.5, 52.0)]
TOP_Z = IBT + SOCK + 2.6                    # puncak OLED = titik tertinggi robot
ESP_TOP = DK_Z0 + 4.7


# ------------------------------ susunan yang dibandingkan ------------------------------
# holder: (x0, x1, y0, y1, z0, z1, jumlah sel). Holder tunggal dimodelkan 77 x 21 x 19 (ukur barangnya).
# dy = geser semua bagian depan (PCB utama, interface, PCB sensor, ball caster, hidung skid plate) terhadap poros.
LAYOUT = {
    "v17": dict(nama="Sekarang (v17)", singkat="bertingkat di atas motor", dy=0.0, wx=39.5,
                holders=[(-38.0, 38.0, -21.0, 21.0, 24.0, 44.0, 2)], tray=True,
                charger=(-12.5, 12.5, -28.0, -12.0), bms=None, sk_y0=-32.0, tail_hw=None),
    "pelana": dict(nama="A · Pelana", singkat="2 holder tunggal mengapit motor", dy=7.0, wx=42.0,
                   holders=[(-38.5, 38.5, -29.5, -8.5, 12.0, 31.0, 1), (-38.5, 38.5, 8.5, 29.5, 12.0, 31.0, 1)],
                   tray=False, charger=(-27.0, -2.0, -48.0, -32.0), bms=(4.0, 34.0, -45.5, -34.5),
                   sk_y0=-50.0, tail_hw=40.0),
    "ekor": dict(nama="B · Ekor", singkat="holder ganda rebah di belakang poros", dy=0.0, wx=39.5,
                 holders=[(-38.0, 38.0, -50.5, -8.5, 12.0, 32.0, 2)], tray=False,
                 charger=(-27.0, -2.0, -69.0, -53.0), bms=(4.0, 34.0, -66.5, -55.5), sk_y0=-71.0, tail_hw=40.0),
    "tengah": dict(nama="C · Tengah", singkat="holder ganda rebah di antara poros dan PCB", dy=28.0, wx=39.5,
                   holders=[(-38.0, 38.0, 8.5, 50.5, 12.0, 32.0, 2)], tray=False,
                   charger=(-27.0, -2.0, -25.0, -9.0), bms=(4.0, 34.0, -22.0, -11.0), sk_y0=-32.0, tail_hw=None),
}
ORDER = ["v17", "pelana", "ekor", "tengah"]


# ------------------------------ geometri ------------------------------
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


def poly_cy(p):
    """y titik berat poligon"""
    a = sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p))) / 2
    return sum((p[i - 1][1] + p[i][1]) * (p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1]) for i in range(len(p))) / (6 * a)


def in_poly(p, poly):
    x, y, c = p[0], p[1], False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i - 1], poly[i]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def seg_dist(p, a, b):
    ax, ay, bx, by = *a, *b
    L2 = (bx - ax) ** 2 + (by - ay) ** 2
    u = max(0.0, min(1.0, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / L2)) if L2 else 0.0
    return math.dist(p, (ax + u * (bx - ax), ay + u * (by - ay)))


def edge_dist(p, poly):
    return min(seg_dist(p, poly[i - 1], poly[i]) for i in range(len(poly)))


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
SENS_Y0, SENS_Y1 = min(y for _, y in SENSOR), max(y for _, y in SENSOR)
SENS_J1 = (-11.0, 12.5, 96.6, 103.4)        # J1 JST XH 8 pin di tangkai PCB sensor (sisi atas)
TRAP = fillet_dense([(MB_XR, MB_Y0, 4), (MB_XF, MB_Y1, 4)])


def skid_poly(L):
    """trapesium: sisi lurus sejajar sisi PCB utama, dari hidung melebar sampai sisi luar ban; coakan roda; ekor"""
    dy, wo, wi = L["dy"], L["wx"] + W_T, L["wx"] - 1.5

    def sx(y):
        return min(NOSE_HW + (NOSE_Y + dy - y) * K_SIDE, wo)
    y_hit = NOSE_Y + dy - (wo - NOSE_HW) / K_SIDE          # di sini sisi miring mencapai sisi luar ban
    pts = [(L["tail_hw"], L["sk_y0"], 4), (wo, min(y_hit, -WELL - 6), 3)] if L["tail_hw"] else [(wo, L["sk_y0"], 4)]
    pts += [(sx(-WELL), -WELL, 1.5), (wi, -WELL, 1.5), (wi, WELL, 1.5), (sx(WELL), WELL, 1.5)]
    if y_hit > WELL + 3:
        pts.append((wo, y_hit, 3))
    pts.append((NOSE_HW, NOSE_Y + dy, 5))
    return fillet_dense(pts)


for _L in LAYOUT.values():
    _L["skid"] = skid_poly(_L)


# ------------------------------ kotak 3D + cek ------------------------------
def boxes(L):
    """(nama, x0, x1, y0, y1, z0, z1, jenis)"""
    dy, wx = L["dy"], L["wx"]
    b = []
    for s, sisi in ((-1, "kiri"), (1, "kanan")):
        x0, x1 = sorted((s * (wx - 34.1), s * (wx - 2.0)))
        b.append((f"Motor N20 + encoder {sisi}", x0, x1, -6.2, 6.2, CH_Z1, CH_Z1 + 10, "motor"))
        x0, x1 = sorted((s * wx, s * (wx + W_T)))
        b.append((f"Ban {sisi}", x0, x1, -R_W, R_W, 0, 2 * R_W, "wheel"))
    for i, h in enumerate(L["holders"]):
        b.append((f"Holder baterai {i + 1}", *h[:6], "battery"))
    if L["tray"]:
        b.append(("Dudukan baterai (3D print)", -38, 38, -24, 24, 22, 24, "print"))
    c = L["charger"]
    b.append(("Charger 2S USB-C", c[0], c[1], c[2], c[3], CH_Z1, CH_Z1 + 5.5, "charger"))
    cx = (c[0] + c[1]) / 2
    b.append(("Jalur steker USB-C charger", cx - 4.5, cx + 4.5, c[2] - 20, c[2], CH_Z1 + 0.5, CH_Z1 + 8, "keep"))
    if L["bms"]:
        m = L["bms"]
        b.append(("BMS 2S", m[0], m[1], m[2], m[3], CH_Z1, CH_Z1 + 3.5, "bms"))
    # PCB utama + komponennya sebagai satu selubung (kaki THT 2 mm di bawah sampai puncak modul ESP32)
    b.append(("PCB utama + komponen", -MB_XR, MB_XR, MB_Y0 + dy, MB_Y1 + dy, MB_Z0 - 2, ESP_TOP, "pcb"))
    b.append(("Board interface + OLED", IB[0], IB[1], IB[2] + dy, IB[3] + dy, IB_Z0 - 2, TOP_Z, "pcb"))
    b.append(("Jalur steker USB ESP32", -48.0, -26.5, EY - 4.5 + dy, EY + 4.5 + dy, DK_Z0 - 0.5, DK_Z0 + 6.5, "keep"))
    b.append(("Jari ke tuas saklar SW1", -52.0, -43.75, 33.0 + dy, 44.0 + dy, MBT, MBT + 8, "keep"))
    b.append(("PCB sensor rev B", -47.5, 47.5, SENS_Y0 + dy, SENS_Y1 + dy, 3.0, 6.4, "sensor"))
    b.append(("Ball caster", -5, 5, CASTER_Y + dy - 5, CASTER_Y + dy + 5, 0, CH_Z0, "caster"))
    return b


def overlap(a, b, eps=0.05):
    return all(min(a[i + 1], b[i + 1]) - max(a[i], b[i]) > eps for i in (1, 3, 5))


def gap_xy(a, b):
    """jarak mendatar dua kotak yang rentang z-nya bertumpuk (None kalau tidak setinggi)"""
    if min(a[6], b[6]) - max(a[5], b[5]) <= 0.05:
        return None
    dx = max(a[1] - b[2], b[1] - a[2], 0.0)
    dy = max(a[3] - b[4], b[3] - a[4], 0.0)
    return math.hypot(dx, dy)


def check(key):
    L = LAYOUT[key]
    bx = boxes(L)
    prob = []
    for i, a in enumerate(bx):
        for b in bx[i + 1:]:
            if overlap(a, b) and not ({a[7], b[7]} == {"pcb"} or {a[7], b[7]} == {"keep", "pcb"}):
                prob.append(f"tabrakan: {a[0]} × {b[0]}")
    skid = L["skid"]
    for a in bx:                                     # yang duduk di skid plate harus di dalam garis luarnya
        if a[7] in ("battery", "charger", "bms") and abs(a[5] - CH_Z1) < 0.01:
            for p in ((a[1], a[3]), (a[1], a[4]), (a[2], a[3]), (a[2], a[4])):
                q = (p[0] * 0.999, p[1])
                if not in_poly(q, skid) and edge_dist(q, skid) > 0.1:
                    prob.append(f"keluar skid plate: {a[0]}")
                    break
    for x, y in TRAP:                                # PCB utama di dalam skid plate, jarak tepi >= 1,5 mm
        p = (x, y + L["dy"])
        if not in_poly(p, skid) or edge_dist(p, skid) < 1.5:
            prob.append(f"PCB utama terlalu dekat tepi skid plate ({edge_dist(p, skid):.1f} mm)")
            break
    hw = [gap_xy(a, b) for a in bx for b in bx if a[7] == "battery" and b[7] == "wheel"]
    hw = min(g for g in hw if g is not None)
    if hw < 1.0:
        prob.append(f"celah holder ke ban {hw:.1f} mm")
    hp = [gap_xy(a, b) for a in bx for b in bx if a[7] == "battery" and b[0].startswith("PCB utama")]
    hp = min((g for g in hp if g is not None), default=None)
    p, l, t = SENS_Y1 + L["dy"] - L["sk_y0"], 2 * (L["wx"] + W_T), TOP_Z
    for v, lim, n in ((p, LIMIT[0], "panjang"), (l, LIMIT[1], "lebar"), (t, LIMIT[2], "tinggi")):
        if v > lim:
            prob.append(f"{n} {v:.0f} mm melewati batas lomba {lim:.0f} mm")
    return dict(prob=prob, gap_ban=hw, gap_pcb=hp, p=p, l=l, t=t, batt_top=max(h[5] for h in L["holders"]))


# ------------------------------ perkiraan massa, titik berat, inersia putar ------------------------------
def mass_model(key):
    """massa per bagian dari docs/perhitungan-motor.md bagian 4 (asumsi, belum ditimbang)"""
    L = LAYOUT[key]
    dy, wx = L["dy"], L["wx"]
    it = []                                          # (m gram, x, y, z, panjang x, panjang y)

    def add(m, x, y, z, sx=0.0, sy=0.0, depan=False):
        it.append((m, x, y + (dy if depan else 0.0), z, sx, sy))
    for h in L["holders"]:
        yc, zc, n = (h[2] + h[3]) / 2, (h[4] + h[5]) / 2, h[6]
        for k in range(n):
            add(46 + 6, 0, yc + (k - (n - 1) / 2) * 21.0, zc, 65, 18)       # sel 46 g + bagian holder 6 g
    for s in (-1, 1):
        add(12, s * (wx - 18), 0, R_W, 32, 12)                              # motor + encoder
        add(6, s * (wx + W_T / 2), 0, R_W, W_T, 34)                         # roda
    c = L["charger"]
    add(3, (c[0] + c[1]) / 2, (c[2] + c[3]) / 2, CH_Z1 + 2.5, 25, 16)
    m = L["bms"]
    if m:
        add(3, (m[0] + m[1]) / 2, (m[2] + m[3]) / 2, CH_Z1 + 1.5, 30, 11)
    else:
        add(3, 0, 0, 23, 30, 11)                                            # v17: BMS ditempel di holder
    if L["tray"]:
        add(13, 0, 0, 20, 76, 48)                                           # dudukan baterai + 4 tiang
    add(14, 0, EY, DK_Z0, 51.5, 28.3, True)                                 # ESP32 DevKit + socket
    add(5, -10.75, 46.0, MBT + 3, 20.5, 20.5, True)                         # TB6612
    add(4, -18.9, 70.5, MBT + 4, 22, 17, True)                              # MP1584
    add(poly_area(TRAP) / 100 * 0.36, 0, poly_cy(TRAP), MB_Z0 + 0.8, 74, 58, True)   # PCB utama FR4 1,6 mm
    add(10, 0, 50, MBT + 4, 60, 50, True)                                   # konektor, saklar, buzzer, elko, dioda
    add(14, -4, 61, IBT + 3, 46, 36, True)                                  # board interface + OLED + tombol
    add(10, 0, poly_cy(SENSOR), 5.6, 95, 30, True)                          # PCB sensor + komponen
    add(8, 0, CASTER_Y, 5, 10, 10, True)                                    # ball caster
    add(10, 0, 55, 14, 60, 60, True)                                        # baut, mur, spacer
    add(8, 0, 45, 20, 40, 60, True)                                         # kabel
    sk = L["skid"]
    ys = [y for _, y in sk]
    add(poly_area(sk) / 100 * 0.2 * 1.24 + 12, 0, poly_cy(sk), 11.5, 90, max(ys) - min(ys))   # PLA + dinding/boss
    M = sum(i[0] for i in it)
    ycm = sum(i[0] * i[2] for i in it) / M
    zcm = sum(i[0] * i[3] for i in it) / M
    izz = sum(i[0] * (i[1] ** 2 + i[2] ** 2 + (i[4] ** 2 + i[5] ** 2) / 12) for i in it) / 1e6     # g·m² terhadap tengah poros
    share = ycm / (CASTER_Y + dy)                                           # bagian berat di ball caster (diam)
    return dict(M=M, ycm=ycm, zcm=zcm, izz=izz, caster=share, a_slip=MU * G * (1 - share), a_lift=G * ycm / zcm)


RES = {k: {**check(k), **mass_model(k)} for k in ORDER}
for k in ORDER:
    if RES[k]["M"] > LIMIT[3]:
        RES[k]["prob"].append(f"perkiraan massa {RES[k]['M']:.0f} g melewati batas lomba {LIMIT[3]:.0f} g")


# ------------------------------ gambar SVG ------------------------------
def P(x, y):
    return f"{x:.2f},{-y:.2f}"


def poly(pts, cls, extra=""):
    return f'<polygon class="{cls}" points="{" ".join(P(x, y) for x, y in pts)}" {extra}/>'


def rect(x0, x1, y0, y1, cls, r=0.6, extra=""):
    return (f'<rect class="{cls}" x="{x0:.2f}" y="{-y1:.2f}" width="{x1 - x0:.2f}" height="{y1 - y0:.2f}" '
            f'rx="{r}" {extra}/>')


def label(x, y, s, cls="lbl", size=3.0, anchor="middle"):
    return f'<text class="{cls}" x="{x:.2f}" y="{-y:.2f}" font-size="{size}" text-anchor="{anchor}">{s}</text>'


def dim_v(x, y0, y1, s, cls="dim"):
    return (f'<g class="{cls}"><line x1="{x}" y1="{-y0}" x2="{x}" y2="{-y1}"/>'
            f'<line x1="{x - 1.5}" y1="{-y0}" x2="{x + 1.5}" y2="{-y0}"/><line x1="{x - 1.5}" y1="{-y1}" x2="{x + 1.5}" y2="{-y1}"/>'
            f'<text x="{x + 1.8}" y="{-(y0 + y1) / 2:.2f}" font-size="3" transform="rotate(-90 {x + 1.8} {-(y0 + y1) / 2:.2f})" '
            f'text-anchor="middle" dy="2.4">{s}</text></g>')


def dim_h(x0, x1, y, s, cls="dim"):
    return (f'<g class="{cls}"><line x1="{x0}" y1="{-y}" x2="{x1}" y2="{-y}"/>'
            f'<line x1="{x0}" y1="{-y - 1.5}" x2="{x0}" y2="{-y + 1.5}"/><line x1="{x1}" y1="{-y - 1.5}" x2="{x1}" y2="{-y + 1.5}"/>'
            f'<text x="{(x0 + x1) / 2:.2f}" y="{-y + 4.2:.2f}" font-size="3" text-anchor="middle">{s}</text></g>')


def top_view(key):
    L, R = LAYOUT[key], RES[key]
    dy, wx = L["dy"], L["wx"]
    wo = wx + W_T
    g = [poly([(x, y + dy) for x, y in SENSOR], "sensor"), label(0, SENS_Y1 + dy + 2.5, "PCB sensor rev B", "lbl dim", 3.0)]
    g.append(poly(L["skid"], "skid"))
    for s in (-1, 1):
        x0, x1 = sorted((s * wx, s * wo))
        g.append(rect(x0, x1, -R_W, R_W, "wheel", 2))
        x0, x1 = sorted((s * (wx - 34.1), s * (wx - 2.0)))
        g.append(rect(x0, x1, -6, 6, "motor", 1))
    g.append(f'<line class="axis" x1="-66" y1="0" x2="66" y2="0"/>')
    g.append(f'<circle class="caster-top" cx="0" cy="{-(CASTER_Y + dy)}" r="5"/>')
    # PCB utama + komponen
    g.append(poly([(x, y + dy) for x, y in TRAP], "board"))
    for hx, hy in MB_HOLE:
        g.append(f'<circle class="hole" cx="{hx}" cy="{-(hy + dy)}" r="1.6"/>')
    for lb, x0, x1, y0, y1, _, cls in MB_PART:
        if cls == "round":
            g.append(f'<circle class="small" cx="{(x0 + x1) / 2:.2f}" cy="{-((y0 + y1) / 2 + dy):.2f}" r="{(x1 - x0) / 2:.2f}"/>')
        else:
            g.append(rect(x0, x1, y0 + dy, y1 + dy, cls, 0.6))
        if lb and lb != "MP1584":
            g.append(label((x0 + x1) / 2, (y0 + y1) / 2 + dy - 0.9, lb, "lbl", 2.3))
    g.append(rect(ESP[0], ESP[1], ESP[2] + dy, ESP[3] + dy, "esp", 1))
    g.append(rect(1.25, 19.25, EY - 9 + dy, EY + 9 + dy, "espmod", 0.5))
    g.append(rect(-26.5, -21.0, EY - 3.8 + dy, EY + 3.8 + dy, "espusb", 0.4))
    g.append(label(-11, EY + dy - 12.2, "ESP32", "lbl inv", 2.4))
    g.append(f'<line class="usb" x1="-49" y1="{-(EY + dy):.2f}" x2="-28" y2="{-(EY + dy):.2f}" marker-end="url(#arr)"/>')
    g.append(label(-50, EY + dy - 0.9, "USB", "lbl dim", 2.4, "end"))
    # board interface di atasnya
    g.append(rect(IB[0], IB[1], IB[2] + dy, IB[3] + dy, "iboard", 3))
    g.append(rect(OLED[0], OLED[1], OLED[2] + dy, OLED[3] + dy, "oled", 1))
    g.append(label((OLED[0] + OLED[1]) / 2, (OLED[2] + OLED[3]) / 2 + dy - 1, "OLED", "lbl light", 3.0))
    for x, y in BTN:
        g.append(rect(x - 3, x + 3, y - 3 + dy, y + 3 + dy, "button", 0.8))
        g.append(f'<circle class="cap" cx="{x}" cy="{-(y + dy)}" r="1.75"/>')
    # baterai
    for h in L["holders"]:
        x0, x1, y0, y1, z0, _, n = h
        g.append(rect(x0, x1, y0, y1, "battery", 2))
        yc = (y0 + y1) / 2
        for k in range(n):
            ycell = yc + (k - (n - 1) / 2) * 21.0
            g.append(rect(-32.5, 32.5, ycell - 9.2, ycell + 9.2, "cell", 2.5))
            g.append(rect(32.5, 34.0, ycell - 3, ycell + 3, "cellcap", 0.4))
            g.append(label(0, ycell - 1.0, "sel 18650", "lbl inv", 2.8))
    # kabel motor: lewat kanal di bawah holder kalau holder ada di antara motor dan PCB utama
    if any(h[2] > 0 and h[4] < 20 for h in L["holders"]):
        yb = max(h[3] for h in L["holders"]) - 2.5
        for s in (-1, 1):
            g.append(f'<polyline class="cable" points="{P(s * (wx - 31), 5)} {P(s * (wx - 31), yb)} '
                     f'{P(s * 25.65, MB_Y0 + dy + 0.6)}"/>')
    c, m = L["charger"], L["bms"]
    hidden = L["tray"]
    g.append(rect(c[0], c[1], c[2], c[3], "hidden" if hidden else "module", 0.8))
    if not hidden:
        g.append(label((c[0] + c[1]) / 2, (c[2] + c[3]) / 2 - 0.9, "charger", "lbl inv", 2.4))
    cx = (c[0] + c[1]) / 2
    g.append(f'<line class="usb" x1="{cx}" y1="{-(c[2] - 11)}" x2="{cx}" y2="{-(c[2] - 1)}" marker-end="url(#arr)"/>')
    g.append(label(cx + 2, c[2] - 8.5, "USB-C cas", "lbl dim", 2.4, "start"))
    if m:
        g.append(rect(m[0], m[1], m[2], m[3], "bms", 0.8))
        g.append(label((m[0] + m[1]) / 2, (m[2] + m[3]) / 2 - 0.9, "BMS", "lbl", 2.4))
    g.append(dim_h(-wo, wo, min(L["sk_y0"], c[2] - 11) - 4, f"{R['l']:.0f} mm"))
    g.append(dim_v(64, L["sk_y0"], SENS_Y1 + dy, f"{R['p']:.0f} mm"))
    return g


def side_view(key):
    """tampak samping dari kiri: y robot ke kanan, z ke atas"""
    L, R = LAYOUT[key], RES[key]
    dy = L["dy"]
    g = ['<line class="floor" x1="-78" y1="0" x2="170" y2="0"/>']

    def r(y0, y1, z0, z1, cls, rx=0.4):
        return f'<rect class="{cls}" x="{y0:.2f}" y="{-z1:.2f}" width="{y1 - y0:.2f}" height="{z1 - z0:.2f}" rx="{rx}"/>'

    def t(y, z, s, anc="middle", cls="lbl dim", size=2.8):
        return f'<text class="{cls}" x="{y:.2f}" y="{-z:.2f}" font-size="{size}" text-anchor="{anc}">{s}</text>'
    top = R["batt_top"]
    x0 = max(-78.0, L["sk_y0"] - 22)
    g.append(f'<line class="deck" x1="{x0}" y1="{-top}" x2="{SENS_Y1 + dy}" y2="{-top}"/>')
    g.append(t(x0, top + 1.4, f"puncak baterai {top:.0f} mm", "start", "lbl acc"))
    g.append(r(SENS_Y0 + dy, SENS_Y1 + dy, 4.8, 6.4, "sensor"))
    g.append(r(SENS_J1[2] + dy, SENS_J1[3] + dy, 6.4, 16.2, "conn"))
    g.append(r(L["sk_y0"], NOSE_Y + dy, CH_Z0, CH_Z1, "skid-side"))
    g.append(f'<circle class="wheel" cx="0" cy="{-R_W}" r="{R_W}"/>')
    g.append(f'<circle class="axis-dot" cx="0" cy="{-R_W}" r="1.2"/>')
    g.append(r(-6, 6, CH_Z1, CH_Z1 + 10, "motor"))
    g.append(f'<circle class="caster" cx="{CASTER_Y + dy}" cy="-5" r="5"/>')
    if L["tray"]:
        g.append(r(-24, 24, 22, 24, "print"))
        for y in (-23, 21):
            g.append(r(y, y + 2, CH_Z1, 22, "print", 0.2))
    for h in L["holders"]:
        _, _, y0, y1, z0, z1, n = h
        g.append(r(y0, y1, z0, z1, "battery", 1.5))
        yc = (y0 + y1) / 2
        for k in range(n):
            g.append(f'<circle class="cell" cx="{yc + (k - (n - 1) / 2) * 21.0:.2f}" cy="{-(z0 + 9.9):.2f}" r="9.2"/>')
    c, m = L["charger"], L["bms"]
    g.append(r(c[2], c[3], CH_Z1, CH_Z1 + 1.6, "module", 0.2))
    g.append(r(c[2] - 1.0, c[2] + 7.0, CH_Z1 + 1.6, CH_Z1 + 4.8, "espusb", 0.4))
    if c[2] - 26.5 < -78:                            # tidak muat di kiri charger: tulis di atasnya
        g.append(t(c[3], CH_Z1 + 7.5, "charger + BMS" if m else "charger", "end"))
    else:
        g.append(t(c[2] - 2.5, CH_Z1 + 1.2, "charger + BMS" if m else "charger", "end"))
    # PCB utama
    g.append(r(MB_Y0 + dy, MB_Y1 + dy, MB_Z0, MBT, "board", 0.3))
    for _, _, _, y0, y1, hgt, cls in MB_PART:
        g.append(r(y0 + dy, y1 + dy, MBT, MBT + hgt, "small" if cls == "round" else cls, 0.3))
    for yr in (EY - 12.7, EY + 12.7):
        g.append(r(yr - 1.27 + dy, yr + 1.27 + dy, MBT, DK_Z0, "socket", 0.2))
    g.append(r(ESP[2] + dy, ESP[3] + dy, DK_Z0, DK_Z0 + 1.6, "esp", 0.3))
    g.append(r(EY - 9 + dy, EY + 9 + dy, DK_Z0 + 1.6, ESP_TOP, "espmod", 0.3))
    # board interface
    g.append(r(J6[2] + dy, J6[3] + dy, MBT, IB_Z0, "conn", 0.2))
    g.append(r(IB[2] + dy, IB[3] + dy, IB_Z0, IBT, "iboard", 0.3))
    g.append(r(OLED_SOCK[2] + dy, OLED_SOCK[3] + dy, IBT, IBT + SOCK, "socket", 0.2))
    g.append(r(OLED[2] + dy, OLED[3] + dy, IBT + SOCK, TOP_Z, "oled", 0.3))
    g.append(r(49 + dy, 55 + dy, IBT, IBT + 5.0, "button", 0.3))
    # kabel J5 -> J1 PCB sensor
    g.append(f'<path class="cable-solid" d="M {78.3 + dy} {-(MBT + 9.8)} C {86 + dy} {-(MBT + 17)}, '
             f'{97 + dy} -26, {100 + dy} -16.4"/>')
    for h in L["holders"]:
        g.append(t((h[2] + h[3]) / 2, h[5] + 3.6 if h[5] > 40 else h[5] + 4.6,
                   "holder 2×18650" if h[6] == 2 else "sel 18650"))
    g += [t(61 + dy, TOP_Z + 2.0, "board interface + OLED"), t(SENS_J1[3] + dy + 3, 8.4, "PCB sensor", "start"),
          t(CASTER_Y + dy + 6.5, 1.3, "ball caster", "start"), t(40 + dy / 2, 6.3, "skid plate 3D print")]
    xd = SENS_Y1 + dy + 5
    g.append(f'<g class="dim"><line x1="{xd}" y1="0" x2="{xd}" y2="{-TOP_Z:.1f}"/>'
             f'<line x1="{xd - 1.5}" y1="{-TOP_Z:.1f}" x2="{xd + 1.5}" y2="{-TOP_Z:.1f}"/>'
             f'<text x="{xd + 2}" y="{-TOP_Z / 2:.1f}" font-size="3" transform="rotate(-90 {xd + 2} {-TOP_Z / 2:.1f})" '
             f'text-anchor="middle" dy="2.4">{TOP_Z:.0f} mm</text></g>')
    return g


def svg(body, vb, aria):
    return (f'<svg viewBox="{vb}" role="img" aria-label="{aria}" xmlns="http://www.w3.org/2000/svg">'
            '<defs><marker id="arr" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="4" markerHeight="4" orient="auto">'
            '<path d="M0,0 L6,3 L0,6 z" class="arrowhead"/></marker></defs>'
            + "".join(body) + "</svg>")


def fmt(v, n=1):
    return f"{v:.{n}f}".replace(".", ",")


VB_TOP1, VB_TOP2, VB_SIDE = "-70 -150 140 220", "-70 -172 140 262", "-80 -56 254 62"
TOP = {k: svg(top_view(k), VB_TOP1 if k in ("v17", "pelana") else VB_TOP2, f"Tampak atas {LAYOUT[k]['nama']}") for k in ORDER}
SIDE = {k: svg(side_view(k), VB_SIDE, f"Tampak samping {LAYOUT[k]['nama']}") for k in ORDER}

# ------------------------------ tabel ------------------------------
B = RES["v17"]


def row(nama, f):
    return "<tr><td>" + nama + "</td>" + "".join(f"<td>{f(RES[k], LAYOUT[k])}</td>" for k in ORDER) + "</tr>"


def d_izz(r, _):
    return "acuan" if r is B else f"{(r['izz'] / B['izz'] - 1) * 100:+.0f}%"


rows = "".join([
    row("Puncak baterai dari lantai", lambda r, L: f"{r['batt_top']:.0f} mm"),
    row("Ukuran p × l × t", lambda r, L: f"{r['p']:.0f} × {r['l']:.0f} × {r['t']:.0f} mm"),
    row("Jarak poros roda → sensor depan", lambda r, L: f"{SENS_Y1 + L['dy']:.0f} mm"),
    row("Tinggi titik berat", lambda r, L: f"{fmt(r['zcm'])} mm"),
    row("Titik berat di depan poros", lambda r, L: f"{fmt(r['ycm'])} mm"),
    row("Berat di roda penggerak / ball caster", lambda r, L: f"{(1 - r['caster']) * 100:.0f}% / {r['caster'] * 100:.0f}%"),
    row("Percepatan maksimum tanpa selip (μ 0,6)", lambda r, L: f"{fmt(r['a_slip'])} m/s²"),
    row("Hidung mulai terangkat pada percepatan", lambda r, L: f"{fmt(r['a_lift'])} m/s²"),
    row("Inersia putar terhadap tengah poros", d_izz),
    row("Celah holder ke ban", lambda r, L: f"{fmt(r['gap_ban'])} mm"),
    row("Holder", lambda r, L: "2 × holder 1 sel" if len(L["holders"]) == 2 else "1 × holder 2 sel (RAB sekarang)"),
    row("Perkiraan massa", lambda r, L: f"±{r['M']:.0f} g"),
])
head = "".join(f"<th>{LAYOUT[k]['nama']}</th>" for k in ORDER)
nprob = sum(len(RES[k]["prob"]) for k in ORDER)
checks = "".join(f"<li><b>{LAYOUT[k]['nama']}:</b> " + ("; ".join(RES[k]["prob"]) or "0 masalah") + "</li>" for k in ORDER)
A = RES["pelana"]
OK = not A["prob"]

html = f"""<title>Konsep LFM v18</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* lembar gambar teknik (sama dengan konsep v17): kertas hijau-abu, tinta gelap, PCB hijau, baterai biru-abu */
:root {{
  --bg: #f3f5f2; --paper: #fbfcfa; --ink: #1c2420; --muted: #5d6b63; --line: #c9d2cc;
  --mask: #2f6b47; --mask-edge: #1f4a31; --iface: #2b5d8a; --accent: #b4521f;
  --sensor: #3b3f3d; --wheel: #2a2d2c; --motor: #a8b0ac; --print: #e2c98f; --batt: #6f7f99; --cell: #3d4a63;
  --module: #4a6fa5; --esp: #24262a; --oled: #101418; --oled-hi: #7fd3ff; --small: #d9b84a; --conn: #f1efe8;
  --bms: #8fbf9b; --on-dark: #eef3f0; --good: #2f7a4f;
  --display: "IBM Plex Sans", system-ui, sans-serif; --mono: "IBM Plex Mono", ui-monospace, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #121614; --paper: #181d1a; --ink: #e4ebe6; --muted: #98a69e; --line: #2e3833;
  --mask: #2f7a4f; --mask-edge: #59a87a; --iface: #4f8cc4; --accent: #e08a5a;
  --sensor: #8a908d; --wheel: #6b706d; --motor: #6d7672; --print: #8a7442; --batt: #7d8db0; --cell: #2c3650;
  --module: #6b8fc8; --esp: #3a3d43; --oled: #05080a; --small: #c9a73c; --conn: #d8d4c8; --bms: #5f9470; --good: #59a87a;
  color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --bg: #121614; --paper: #181d1a; --ink: #e4ebe6; --muted: #98a69e; --line: #2e3833;
  --mask: #2f7a4f; --mask-edge: #59a87a; --iface: #4f8cc4; --accent: #e08a5a;
  --sensor: #8a908d; --wheel: #6b706d; --motor: #6d7672; --print: #8a7442; --batt: #7d8db0; --cell: #2c3650;
  --module: #6b8fc8; --esp: #3a3d43; --oled: #05080a; --small: #c9a73c; --conn: #d8d4c8; --bms: #5f9470; --good: #59a87a;
  color-scheme: dark; }}
body {{ background: var(--bg); color: var(--ink); font-family: var(--display); font-size: 15px; line-height: 1.55;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 28px 48px; }}
main {{ max-width: 1080px; margin: 0 auto; display: grid; gap: 28px; }}
h1 {{ font-size: 1.7rem; font-weight: 600; margin: 0; text-wrap: balance; letter-spacing: -0.01em; }}
h2 {{ font-size: 0.78rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.09em; color: var(--muted); margin: 0 0 10px; }}
p {{ margin: 0; max-width: 68ch; }}
.lead {{ color: var(--muted); }}
.stack {{ display: grid; gap: 14px; }}
.sheets {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
@media (max-width: 720px) {{ .sheets {{ grid-template-columns: 1fr; }} }}
figure {{ margin: 0; background: var(--paper); border: 1px solid var(--line); border-radius: 6px; padding: 14px; min-width: 0; }}
figure.pick {{ border-color: var(--good); }}
figcaption {{ font-family: var(--mono); font-size: 0.78rem; color: var(--muted); margin-top: 8px; }}
figcaption b {{ color: var(--ink); font-weight: 500; }}
.wide {{ overflow-x: auto; }}
.wide svg {{ min-width: 720px; }}
svg {{ width: 100%; height: auto; display: block; }}
svg text {{ font-family: var(--mono); fill: var(--ink); }}
svg .lbl.dim {{ fill: var(--muted); }}
svg .lbl.light {{ fill: var(--oled-hi); }}
svg .lbl.inv {{ fill: var(--on-dark); }}
svg .lbl.acc {{ fill: var(--accent); }}
.board {{ fill: var(--mask); stroke: var(--mask-edge); stroke-width: 0.5; }}
.iboard {{ fill: var(--iface); fill-opacity: 0.9; stroke: var(--iface); stroke-width: 0.6; }}
.sensor {{ fill: var(--sensor); fill-opacity: 0.85; }}
.skid {{ fill: var(--print); fill-opacity: 0.28; stroke: var(--print); stroke-width: 0.5; stroke-dasharray: 2 1.2; }}
.skid-side {{ fill: var(--print); }}
.wheel {{ fill: var(--wheel); }}
.motor {{ fill: var(--motor); }}
.print {{ fill: var(--print); }}
.battery {{ fill: var(--batt); }}
.cell {{ fill: var(--cell); }}
.cellcap {{ fill: #c3c8cc; }}
.module {{ fill: var(--module); }}
.bms {{ fill: var(--bms); }}
.esp {{ fill: var(--esp); }}
.espmod {{ fill: #9aa3a8; }}
.espusb {{ fill: #c3c8cc; }}
.socket {{ fill: #111; }}
.oled {{ fill: var(--oled); stroke: #2a3138; stroke-width: 0.4; }}
.small {{ fill: var(--small); }}
.conn {{ fill: var(--conn); stroke: #8c8778; stroke-width: 0.35; }}
.hidden {{ fill: var(--module); fill-opacity: 0.25; stroke: var(--on-dark); stroke-width: 0.5; stroke-dasharray: 1.6 1; }}
.button {{ fill: #d7dbd9; stroke: #6c736f; stroke-width: 0.3; }}
.cap {{ fill: #23272a; }}
.hole {{ fill: var(--paper); stroke: var(--ink); stroke-width: 0.3; }}
.axis {{ stroke: var(--muted); stroke-width: 0.3; stroke-dasharray: 3 1.5 0.6 1.5; }}
.axis-dot {{ fill: var(--paper); }}
.floor {{ stroke: var(--ink); stroke-width: 0.5; }}
.deck {{ stroke: var(--accent); stroke-width: 0.4; stroke-dasharray: 2.2 1.4; }}
.caster {{ fill: #c3c8cc; stroke: #6c736f; stroke-width: 0.3; }}
.caster-top {{ fill: none; stroke: var(--muted); stroke-width: 0.5; stroke-dasharray: 1.2 0.8; }}
.cable {{ fill: none; stroke: var(--accent); stroke-width: 0.7; stroke-dasharray: 1.6 1; }}
.cable-solid {{ fill: none; stroke: var(--accent); stroke-width: 0.8; }}
.usb {{ stroke: var(--muted); stroke-width: 0.5; }}
.arrowhead {{ fill: var(--muted); }}
.dim line {{ stroke: var(--accent); stroke-width: 0.35; }}
.dim text {{ fill: var(--accent); font-family: var(--mono); }}
.legend {{ display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: 0.85rem; color: var(--muted); }}
.legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
.sw {{ width: 14px; height: 10px; border-radius: 2px; display: inline-block; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.92rem; min-width: 760px; }}
.tablewrap {{ overflow-x: auto; }}
th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
th {{ font-weight: 500; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; }}
td {{ font-variant-numeric: tabular-nums; }}
td:first-child {{ color: var(--muted); }}
th:nth-child(3), td:nth-child(3) {{ background: color-mix(in srgb, var(--good) 9%, transparent); }}
th:nth-child(3) {{ color: var(--good); }}
.status {{ display: inline-flex; align-items: center; gap: 8px; font-family: var(--mono); font-size: 0.82rem;
  padding: 4px 10px; border-radius: 999px; border: 1px solid var(--line); background: var(--paper); justify-self: start; }}
.dot {{ width: 8px; height: 8px; border-radius: 50%; background: {'#3f9b62' if OK else '#c0432f'}; }}
ol, ul {{ margin: 0; padding-left: 1.2em; display: grid; gap: 6px; max-width: 72ch; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }}
@media (max-width: 720px) {{ .cols {{ grid-template-columns: 1fr; }} }}
.cols > section {{ min-width: 0; }}
.note {{ font-size: 0.85rem; color: var(--muted); }}
</style>
<main>
  <header style="display:grid;gap:10px">
    <h1>Konsep LFM v18: baterai satu bidang dengan PCB</h1>
    <p class="lead">Baterai turun dari atas motor ke skid plate, sejajar dengan PCB utama. Caranya: holder 2 sel diganti
    2 holder 1 sel yang rebah melintang, satu di depan dan satu di belakang motor, seperti pelana di atas poros roda.
    PCB utama rev B, board interface, dan PCB sensor tidak diubah. Semua gambar to-scale (mm).</p>
    <span class="status"><span class="dot"></span>Cek otomatis susunan pelana: {len(A["prob"])} masalah</span>
  </header>

  <section class="stack">
    <h2>Tampak samping, skala sama</h2>
    <figure class="wide">{SIDE["v17"]}<figcaption><b>Sekarang (v17).</b> Holder duduk di dudukan di atas motor:
    puncak baterai {B["batt_top"]:.0f} mm, ada lantai kedua di belakang.</figcaption></figure>
    <figure class="wide pick">{SIDE["pelana"]}<figcaption><b>Usulan A · Pelana.</b> Kedua sel duduk di skid plate:
    puncak baterai {A["batt_top"]:.0f} mm, hampir sama dengan puncak ESP32 ({fmt(ESP_TOP)} mm). Yang lebih tinggi tinggal OLED.</figcaption></figure>
  </section>

  <section class="stack">
    <h2>Tampak atas, skala sama</h2>
    <div class="sheets">
      <figure>{TOP["v17"]}<figcaption><b>Sekarang (v17).</b> Holder 76 × 42 mm menutupi motor dan charger.</figcaption></figure>
      <figure class="pick">{TOP["pelana"]}<figcaption><b>Usulan A · Pelana.</b> Sel depan dan belakang mengapit motor;
      charger dan BMS di ekor; ban digeser ke luar 2,5 mm per sisi.</figcaption></figure>
    </div>
    <div class="legend">
      <span><i class="sw" style="background:var(--batt)"></i>holder baterai</span>
      <span><i class="sw" style="background:var(--cell)"></i>sel 18650</span>
      <span><i class="sw" style="background:var(--mask)"></i>PCB utama (tetap)</span>
      <span><i class="sw" style="background:var(--iface)"></i>board interface (tetap)</span>
      <span><i class="sw" style="background:var(--module)"></i>charger 2S, MP1584</span>
      <span><i class="sw" style="background:var(--bms)"></i>BMS 2S</span>
      <span><i class="sw" style="background:var(--print);opacity:.6"></i>skid plate 3D print</span>
      <span><i class="sw" style="border:1px dashed var(--accent)"></i>kabel motor lewat kanal di bawah sel</span>
    </div>
  </section>

  <section>
    <h2>Angka</h2>
    <div class="tablewrap"><table><thead><tr><th></th>{head}</tr></thead><tbody>{rows}</tbody></table></div>
    <p class="note" style="margin-top:10px">Titik berat, pembagian berat, dan inersia dihitung dari massa perkiraan tiap bagian
    (<code>docs/perhitungan-motor.md</code> bagian 4, belum ditimbang). Pakai untuk membandingkan susunan, bukan sebagai angka pasti.</p>
  </section>

  <div class="cols">
    <section>
      <h2>Kenapa pelana</h2>
      <ul>
        <li><b>Tidak bertingkat.</b> Dudukan baterai di atas motor hilang. Puncak baterai turun {B["batt_top"] - A["batt_top"]:.0f} mm
        dan titik berat robot turun {fmt(B["zcm"] - A["zcm"])} mm, jadi robot lebih tenang saat mengerem dan belok cepat.</li>
        <li><b>Berat tetap di roda penggerak.</b> Kedua sel simetris terhadap poros, jadi {(1 - A["caster"]) * 100:.0f}% berat
        tetap di roda penggerak (v17: {(1 - B["caster"]) * 100:.0f}%). Traksi tidak berkurang.</li>
        <li><b>Hidung lebih menempel.</b> Hidung baru terangkat pada percepatan {fmt(A["a_lift"])} m/s² (v17: {fmt(B["a_lift"])}),
        jauh di atas batas selip ban {fmt(A["a_slip"])} m/s². Sensor tetap rata dengan lantai saat tancap gas.</li>
        <li><b>Rakit lebih mudah.</b> Sel masuk dari atas, BMS dapat titik tengah langsung dari kabel antar holder,
        dan satu klem cetak 3D bisa menahan motor sekaligus kedua holder.</li>
      </ul>
    </section>
    <section>
      <h2>Yang dibayar</h2>
      <ul>
        <li><b>Lebar 115 → {A["l"]:.0f} mm.</b> Holder 1 sel panjangnya 77 mm, jadi ban digeser ke luar 2,5 mm per sisi supaya
        celah ke ban {fmt(A["gap_ban"])} mm. Jarak tengah ban 97 → 102 mm.</li>
        <li><b>Jarak poros ke sensor +{LAYOUT["pelana"]["dy"]:.0f} mm.</b> Sel depan butuh tempat di antara motor dan PCB utama, jadi PCB utama,
        board interface, PCB sensor, dan ball caster maju bersama {LAYOUT["pelana"]["dy"]:.0f} mm. Posisi antar PCB tidak berubah.</li>
        <li><b>Ekor +18 mm</b> untuk charger dan BMS yang tadinya tersembunyi di bawah dudukan. Panjang robot {B["p"]:.0f} → {A["p"]:.0f} mm
        (batas lomba 250 mm).</li>
        <li><b>Inersia putar {(A["izz"] / B["izz"] - 1) * 100:+.0f}%</b> karena bagian depan maju dan ada ekor (ekor
        {(RES["ekor"]["izz"] / B["izz"] - 1) * 100:+.0f}%, tengah {(RES["tengah"]["izz"] / B["izz"] - 1) * 100:+.0f}%). Belok sedikit lebih
        berat, PID perlu dituning dengan angka ini.</li>
        <li><b>Holder diganti.</b> 2 holder 1 sel menggantikan holder 2 sel di RAB. Harga di Tokopedia belum dicek.</li>
        <li><b>Kabel motor</b> ke J2/J3 lewat kanal di bawah sel depan (garis putus-putus di tampak atas).</li>
      </ul>
    </section>
  </div>

  <section class="stack">
    <h2>Dua cara lain yang juga sebidang</h2>
    <div class="sheets">
      <figure>{TOP["ekor"]}<figcaption><b>B · Ekor.</b> Holder 2 sel yang sama rebah di belakang motor. PCB dan lebar tidak
      berubah, tetapi berat pindah ke belakang: di ball caster tinggal {RES["ekor"]["caster"] * 100:.0f}%, dan hidung mulai
      terangkat pada percepatan {fmt(RES["ekor"]["a_lift"])} m/s² (batas selip {fmt(RES["ekor"]["a_slip"])} m/s²). Sensor bisa
      terangkat saat robot tancap gas.</figcaption></figure>
      <figure>{TOP["tengah"]}<figcaption><b>C · Tengah.</b> Holder 2 sel yang sama rebah di antara motor dan PCB. Lebar tetap dan
      charger tetap di belakang motor, tetapi semua bagian depan maju {LAYOUT["tengah"]["dy"]:.0f} mm: sensor jadi {SENS_Y1 + LAYOUT["tengah"]["dy"]:.0f} mm
      dari poros, ball caster memikul {RES["tengah"]["caster"] * 100:.0f}% berat, dan inersia putar
      {(RES["tengah"]["izz"] / B["izz"] - 1) * 100:+.0f}%.</figcaption></figure>
    </div>
    <figure class="wide">{SIDE["ekor"]}<figcaption>B · Ekor, tampak samping.</figcaption></figure>
    <figure class="wide">{SIDE["tengah"]}<figcaption>C · Tengah, tampak samping.</figcaption></figure>
    <p class="note"><b>Dicoret: sel membujur di kiri-kanan PCB (sidepod).</b> Sel kiri menutup colokan USB ESP32 dan tuas saklar SW1
    di tepi kiri PCB utama, jadi tidak bisa tanpa mengubah PCB. Berat ±100 g juga pindah ke depan dan ke luar.</p>
  </section>

  <div class="cols">
    <section>
      <h2>Tidak berubah</h2>
      <ul>
        <li>PCB utama rev B, board interface rev A, PCB sensor rev B: file KiCad tidak disentuh.</li>
        <li>Motor N20 500 RPM + encoder, ban Ø34 × 18 mm, ball caster, 4 baut M3 PCB utama.</li>
        <li>Tinggi robot {TOP_Z:.0f} mm, karena titik tertinggi tetap OLED di board interface.</li>
      </ul>
    </section>
    <section>
      <h2>Perlu diputuskan</h2>
      <ol>
        <li>Susunan mana yang dipakai: A pelana, B ekor, atau C tengah.</li>
        <li>Holder 1 sel dimodelkan 77 × 21 × 19 mm. Ukuran barang di toko bisa beda 1–2 mm; lebar robot ikut ukuran itu.</li>
        <li>Charger di ekor memakai ukuran model 25 × 16 mm dengan USB-C di sisi panjang. Ukuran modul yang dibeli belum diketahui.</li>
        <li>Kalau A dipilih: model 3D skid plate v18 (kanal kabel, klem motor + holder, dudukan charger) dibuat sesudah ini.</li>
      </ol>
    </section>
  </div>

  <section>
    <h2>Hasil cek otomatis (kotak 3D tiap bagian)</h2>
    <ul>{checks}</ul>
    <p class="note" style="margin-top:10px">Yang dicek: tabrakan antar bagian, holder/charger/BMS di dalam skid plate, PCB utama ≥ 1,5 mm
    dari tepi skid plate, jalur steker USB ESP32 dan charger, akses tuas SW1, celah holder ke ban ≥ 1 mm, batas ukuran dan massa lomba.</p>
  </section>
</main>
"""

out = os.path.join(HERE, "konsep-v18.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
for k in ORDER:
    r = RES[k]
    print(f"{k:7s} {r['p']:.0f} x {r['l']:.0f} x {r['t']:.0f} mm  baterai z<={r['batt_top']:.0f}  M {r['M']:.0f} g  "
          f"ycm {r['ycm']:.1f}  zcm {r['zcm']:.1f}  caster {r['caster'] * 100:.0f}%  a_selip {r['a_slip']:.1f}  "
          f"a_angkat {r['a_lift']:.1f}  Izz {r['izz']:.3f}  celah ban {r['gap_ban']:.1f}  "
          f"celah PCB {r['gap_pcb'] if r['gap_pcb'] is None else round(r['gap_pcb'], 1)}")
    for p in r["prob"]:
        print("   -", p)
print("tulis", out)
