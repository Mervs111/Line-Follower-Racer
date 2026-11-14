"""Konsep v18: pack Li-ion 2S 14500 (50 x 30 x 15 mm, 46 g) diikat strap, sebidang dengan PCB utama. PCB tidak diubah.

Versi pertama konsep v18 (2x 18650 rebah: pelana/ekor/tengah) ditolak user 14/11; penggantinya memakai pack siap colok
tanpa holder. Susunan yang dibandingkan dengan v17 (holder 2x18650 di atas motor):
  ransel  pack rebah melintang tepat di belakang motor, strap velcro lewat celah skid plate     -> usulan
  bak     sama, tetapi pack duduk di bak yang turun dari skid plate (puncak rata dengan motor)
  tengah  pack di antara motor dan PCB utama, semua bagian depan maju

Menulis konsep-v18.html (viewer 3D + angka) dan konsep-v18-model.json (mesh), lalu mencetak hasil cek: tabrakan
kotak 3D, batas ukuran lomba, perkiraan titik berat. Model 3D dirakit tanpa CadQuery: komponen yang tidak berubah
diambil dari mesh v16 (mechanical/viewer/model.json) lalu digeser ke posisi PCB utama rev B / board interface rev A,
sisanya (skid plate, pack, strap, kabel, PCB) dibuat di sini dari kotak, prisma, dan tabung.
Koordinat robot (mm): x ke kanan, y maju, z naik dari lantai, (0, 0) = tengah poros roda (sama dengan v16/v17).

Jalankan: py mechanical/konsep-v18/gen_konsep.py
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

G, MU = 9.81, 0.6                           # mu ban = asumsi docs/perhitungan-motor.md bagian 3
R_W, W_T, WX = 17.0, 18.0, 39.5             # ban O34 x 18, sisi dalam ban
WO, WI = WX + W_T, WX - 1.5                 # sisi luar ban, tepi dalam coakan roda
CH_Z0, CH_Z1 = 10.0, 12.0                   # skid plate 3D print
WELL = 20.5                                 # coakan roda: setengah panjang
NOSE_HW, NOSE_Y = 31.0, 93.0                # hidung skid plate
K_SIDE = (57.5 - NOSE_HW) / 125.0           # kemiringan sisi skid plate = sisi PCB utama trapesium
CASTER_Y, SENS_Y1 = 72.0, 131.0
LIMIT = (250.0, 200.0, 100.0, 350.0)        # guidebook IARC XII SD: p, l, t (mm), massa (g, butir C)

# PCB (tetap), posisi dari KiCad rev B / interface rev A pada dy = 0
MB_Y0, MB_Y1, MB_XR, MB_XF = 24.0, 82.0, 43.3, 31.0
MB_Z0 = 15.0
MBT = MB_Z0 + 1.6
SOCK = 8.5
DK_Z0 = MBT + SOCK
EY = 46.15
MB_HOLE = [(-38.5, 29.0), (38.5, 29.0), (-32.5, 56.0), (32.5, 56.0)]
JST = {"J2": (-34.90, -16.41, 24.66, 31.50), "J1": (-4.25, 4.25, 24.66, 31.50), "J3": (16.41, 34.90, 24.66, 31.50),
       "J5": (-7.50, 16.00, 74.91, 81.75)}
J6 = (-7.41, 8.91, 65.69, 69.32)
IB = (-27.05, 19.05, 42.95, 79.05)
IB_Z0 = 33.0
IBT = IB_Z0 + 1.6
BTN = [(-22.5, 70.0), (-22.5, 52.0), (14.5, 70.0), (14.5, 61.0), (14.5, 52.0)]
TOP_Z = IBT + SOCK + 2.6                    # puncak OLED = titik tertinggi robot
ESP_TOP = DK_Z0 + 4.7

PACK_L, PACK_W, PACK_H, PACK_M = 50.0, 30.0, 15.0, 46.0     # listing: Li-ion 14500 7,4 V 2S, 46 g
STRAP_W, STRAP_T = 16.0, 1.0

# pack: (y0, z0) = sisi belakang dan dasar pack; dy = geser bagian depan (PCB, sensor, caster, hidung) terhadap poros
LAYOUT = {
    "v17": dict(nama="Sekarang", sub="2× 18650 di atas motor", dy=0.0, pack=None,
                teks="Susunan yang sekarang: holder 2× 18650 di dudukan di atas motor, charger USB-C dan BMS di "
                     "bawahnya. Ini yang kamu sebut bertingkat."),
    "ransel": dict(nama="A · Ransel", sub="pack di belakang motor", dy=0.0, pack=(-41.5, CH_Z1),
                   teks="Pack rebah melintang tepat di belakang motor, diikat satu strap velcro 16 mm yang lewat celah "
                        "di skid plate. Kabel pack langsung ke J1. PCB, lebar robot, dan jarak sensor tidak berubah."),
    "bak": dict(nama="B · Bak", sub="pack turun ke dalam bak", dy=0.0, pack=(-41.5, 7.5),
                teks="Sama seperti A, tetapi pack duduk di bak yang turun 4,5 mm dari skid plate, jadi puncaknya rata "
                     "dengan motor. Celah ke lantai di bawah bak tinggal ±4,5 mm dan skid plate lebih rumit dicetak."),
    "tengah": dict(nama="C · Tengah", sub="pack di antara motor dan PCB", dy=22.0, pack=(11.5, CH_Z1),
                   teks="Pack di antara motor dan PCB utama, terlindung di tengah. Supaya muat, PCB utama, board "
                        "interface, PCB sensor, dan ball caster maju 22 mm, dan berat di roda penggerak turun."),
}
ORDER = ["v17", "ransel", "bak", "tengah"]


# ------------------------------ geometri 2D ------------------------------
def fillet_dense(right, mirror=True):
    pts = list(right) + ([(-x, y, r) for x, y, r in reversed(right)] if mirror else [])
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


def area2(p):
    return sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p)))


def poly_cy(p):
    a = area2(p) / 2
    return sum((p[i - 1][1] + p[i][1]) * (p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1]) for i in range(len(p))) / (6 * a)


def in_poly(p, poly):
    x, y, c = p[0], p[1], False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i - 1], poly[i]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def edge_dist(p, poly):
    best = 1e9
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i - 1], poly[i]
        L2 = (bx - ax) ** 2 + (by - ay) ** 2
        u = max(0.0, min(1.0, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / L2)) if L2 else 0.0
        best = min(best, math.dist(p, (ax + u * (bx - ax), ay + u * (by - ay))))
    return best


TRAP = fillet_dense([(MB_XR, MB_Y0, 4), (MB_XF, MB_Y1, 4)])


def skid_poly(key):
    """trapesium v17 (sisi sejajar PCB utama, coakan roda); bagian belakang berbeda tiap susunan"""
    dy = LAYOUT[key]["dy"]

    def sx(y):
        return min(NOSE_HW + (NOSE_Y + dy - y) * K_SIDE, WO)
    front = [(WI, WELL, 1.5), (sx(WELL), WELL, 1.5), (NOSE_HW, NOSE_Y + dy, 5)]
    wing = [(WO, -32.0, 3), (sx(-WELL), -WELL, 1.5), (WI, -WELL, 1.5)]
    if key == "v17":
        rear = [(WO, -32.0, 4)] + wing[1:]
    elif key == "ransel":                   # ekor meruncing, pack 50 mm + bibir di atasnya
        rear = [(30.0, -43.0, 4)] + wing
    elif key == "bak":                      # ekor bercabang: coakan 54 mm untuk bak, terbuka ke bawah
        rear = [(27.0, -9.5, 0.8), (27.0, -43.5, 0.8), (34.0, -43.5, 3)] + wing
    else:                                   # tengah: tidak ada apa-apa di belakang motor, plat dipotong di y -12
        rear = [(WI, -12.0, 1.5)]
    return fillet_dense(rear + front)


SKID = {k: skid_poly(k) for k in ORDER}


# ------------------------------ kotak 3D + cek ------------------------------
def pack_box(L):
    y0, z0 = L["pack"]
    return (-PACK_L / 2, PACK_L / 2, y0, y0 + PACK_W, z0, z0 + PACK_H)


def boxes(key):
    """(nama, x0, x1, y0, y1, z0, z1, jenis)"""
    L = LAYOUT[key]
    dy = L["dy"]
    b = []
    for s, sisi in ((-1, "kiri"), (1, "kanan")):
        x0, x1 = sorted((s * (WX - 34.1), s * (WX - 2.0)))
        b.append((f"Motor N20 + encoder {sisi}", x0, x1, -6.2, 6.2, CH_Z1, CH_Z1 + 10, "motor"))
        x0, x1 = sorted((s * WX, s * WO))
        b.append((f"Ban {sisi}", x0, x1, -R_W, R_W, 0, 2 * R_W, "wheel"))
    if L["pack"]:
        p = pack_box(L)
        b.append(("Pack Li-ion 2S", *p, "battery"))
        # strap melingkari pack, lewat di bawah plat/bak
        zlow = (p[4] - 1.5 if key == "bak" else CH_Z0) - 0.45 - STRAP_T
        b.append(("Strap", -STRAP_W / 2, STRAP_W / 2, p[2] - 1.4, p[3] + 1.4, zlow, p[5] + 1.4, "strap"))
    else:
        b.append(("Holder 2x18650", -38, 38, -21, 21, 24, 44, "battery"))
        b.append(("Dudukan baterai (3D print)", -38, 38, -24, 24, 22, 24, "print"))
        b.append(("Charger 2S USB-C", -12.5, 12.5, -28, -12, CH_Z1, CH_Z1 + 5.5, "charger"))
    b.append(("PCB utama + komponen", -MB_XR, MB_XR, MB_Y0 + dy, MB_Y1 + dy, MB_Z0 - 2, ESP_TOP, "pcb"))
    b.append(("Board interface + OLED", IB[0], IB[1], IB[2] + dy, IB[3] + dy, IB_Z0 - 2, TOP_Z, "pcb"))
    b.append(("Jalur steker USB ESP32", -48.0, -26.5, EY - 4.5 + dy, EY + 4.5 + dy, DK_Z0 - 0.5, DK_Z0 + 6.5, "keep"))
    b.append(("Jari ke tuas saklar SW1", -52.0, -43.75, 33.0 + dy, 44.0 + dy, MBT, MBT + 8, "keep"))
    b.append(("PCB sensor rev B", -47.5, 47.5, 80.0 + dy, SENS_Y1 + dy, 3.0, 6.4, "sensor"))
    b.append(("Ball caster", -5, 5, CASTER_Y + dy - 5, CASTER_Y + dy + 5, 0, CH_Z0, "caster"))
    return b


def overlap(a, b, eps=0.05):
    return all(min(a[i + 1], b[i + 1]) - max(a[i], b[i]) > eps for i in (1, 3, 5))


def gap_xy(a, b):
    if min(a[6], b[6]) - max(a[5], b[5]) <= 0.05:
        return None
    return math.hypot(max(a[1] - b[2], b[1] - a[2], 0.0), max(a[3] - b[4], b[3] - a[4], 0.0))


def check(key):
    L = LAYOUT[key]
    bx = boxes(key)
    prob = []
    for i, a in enumerate(bx):
        for b in bx[i + 1:]:
            if overlap(a, b) and {a[7], b[7]} not in ({"pcb"}, {"keep", "pcb"}, {"battery", "strap"}):
                prob.append(f"tabrakan: {a[0]} × {b[0]}")
    skid = SKID[key]
    if L["pack"] and key != "bak":                   # pack duduk di plat: harus di dalam garis luarnya
        p = pack_box(L)
        for q in ((p[0], p[2]), (p[0], p[3]), (p[1], p[2]), (p[1], p[3])):
            if not in_poly(q, skid):
                prob.append("pack keluar dari skid plate")
                break
    for x, y in TRAP:                                # PCB utama di dalam skid plate, jarak tepi >= 1,5 mm
        q = (x, y + L["dy"])
        if not in_poly(q, skid) or edge_dist(q, skid) < 1.5:
            prob.append(f"PCB utama terlalu dekat tepi skid plate ({edge_dist(q, skid):.1f} mm)")
            break
    batt = next(b for b in bx if b[7] == "battery")
    gaps = {n: min((g for g in (gap_xy(batt, b) for b in bx if b[7] == t) if g is not None), default=None)
            for n, t in (("ban", "wheel"), ("motor", "motor"))}
    rear = min(min(y for _, y in skid), -R_W)
    p, l, t = SENS_Y1 + L["dy"] - rear, 2 * WO, TOP_Z
    for v, lim, n in ((p, LIMIT[0], "panjang"), (l, LIMIT[1], "lebar"), (t, LIMIT[2], "tinggi")):
        if v > lim:
            prob.append(f"{n} {v:.0f} mm melewati batas lomba {lim:.0f} mm")
    low = min(b[5] for b in bx if b[7] in ("strap", "battery"))
    return dict(prob=prob, gap=gaps, p=p, l=l, t=t, batt_top=batt[6], low=min(low, CH_Z0))


def mass_model(key):
    """massa per bagian dari docs/perhitungan-motor.md bagian 4 (asumsi, belum ditimbang)"""
    L = LAYOUT[key]
    dy = L["dy"]
    it = []                                          # (m gram, y, z)

    def add(m, y, z, depan=False):
        it.append((m, y + (dy if depan else 0.0), z))
    if L["pack"]:
        p = pack_box(L)
        add(PACK_M + 4, (p[2] + p[3]) / 2, (p[4] + p[5]) / 2)       # pack + strap dan bibir penahan
    else:
        add(92 + 12, 0, 34)                                         # 2 sel 18650 + holder
        add(13, 0, 20)                                              # dudukan baterai + tiang
        add(3, -20, CH_Z1 + 2.5)                                    # charger
        add(3, 0, 23)                                               # BMS di holder
    add(24, 0, R_W)                                                 # 2 motor + encoder
    add(12, 0, R_W)                                                 # 2 roda
    add(14, EY, DK_Z0, True)                                        # ESP32 DevKit + socket
    add(5, 46.0, MBT + 3, True)                                     # TB6612
    add(4, 70.5, MBT + 4, True)                                     # MP1584
    add(abs(area2(TRAP)) / 200 * 0.36, poly_cy(TRAP), MB_Z0 + 0.8, True)     # PCB utama FR4 1,6 mm
    add(10, 50, MBT + 4, True)                                      # konektor, saklar, buzzer, elko, dioda
    add(14, 61, IBT + 3, True)                                      # board interface + OLED + tombol
    add(10, 110, 5.6, True)                                         # PCB sensor + komponen
    add(8, CASTER_Y, 5, True)                                       # ball caster
    add(10, 55, 14, True)                                           # baut, mur, spacer
    add(8, 45, 20, True)                                            # kabel
    sk = SKID[key]
    add(abs(area2(sk)) / 200 * 0.2 * 1.24 + 12 + (6 if key == "bak" else 0), poly_cy(sk), 11.5)   # PLA + dudukan motor
    M = sum(i[0] for i in it)
    ycm = sum(i[0] * i[1] for i in it) / M
    zcm = sum(i[0] * i[2] for i in it) / M
    share = ycm / (CASTER_Y + dy)                                   # bagian berat di ball caster (diam)
    return dict(M=M, ycm=ycm, zcm=zcm, caster=share, a_slip=MU * G * (1 - share), a_lift=G * ycm / zcm)


RES = {k: {**check(k), **mass_model(k)} for k in ORDER}
for k in ORDER:
    if RES[k]["M"] > LIMIT[3]:
        RES[k]["prob"].append(f"perkiraan massa {RES[k]['M']:.0f} g melewati batas lomba {LIMIT[3]:.0f} g")


# ------------------------------ mesh ------------------------------
V16 = json.load(open(os.path.join(HERE, "..", "viewer", "model.json"), encoding="utf-8"))
MATS = dict(V16["mats"])
MATS.update({"skid": ["#aab3bd", 0.78, 0.0], "pack": ["#15161a", 0.38, 0.1], "strap": ["#f08a1c", 0.92, 0.0],
             "buckle": ["#2a2c31", 0.5, 0.2], "pack_end": ["#2c5fb8", 0.5, 0.0]})
MESH = []


def emit(name, mat, group, pi, dbl=True):
    p, i = pi
    o = {"n": name, "m": mat, "g": group, "p": [round(v, 2) for v in p], "i": i}
    if dbl:
        o["d"] = 1
    MESH.append(o)


def reuse(names, group, dx=0.0, dy=0.0, dz=0.0, fx=None, pred=None):
    """salin mesh v16 (nama persis atau awalan berakhiran *), digeser"""
    n = 0
    for o in V16["meshes"]:
        if not any(o["n"] == s or (s.endswith("*") and o["n"].startswith(s[:-1])) for s in names):
            continue
        if pred and not pred(o):
            continue
        p = o["p"][:]
        for k in range(0, len(p), 3):
            p[k] = (fx(p[k]) if fx else p[k]) + dx
            p[k + 1] += dy
            p[k + 2] += dz
        emit(o["n"], o["m"], group, (p, o["i"]), dbl=False)
        n += 1
    assert n, names


def quad(P, I, a, b, c, d):
    n = len(P) // 3
    P += [*a, *b, *c, *d]
    I += [n, n + 1, n + 2, n, n + 2, n + 3]


def box(x0, x1, y0, y1, z0, z1):
    P, I = [], []
    quad(P, I, (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))
    quad(P, I, (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0))
    quad(P, I, (x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1))
    quad(P, I, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))
    quad(P, I, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))
    quad(P, I, (x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1))
    return P, I


def merge(*parts):
    P, I = [], []
    for p, i in parts:
        n = len(P) // 3
        P += p
        I += [k + n for k in i]
    return P, I


def earclip(poly):
    """triangulasi poligon sederhana (boleh cekung), titik CCW"""
    idx = list(range(len(poly)))
    tris = []

    def cr(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    guard = 0
    while len(idx) > 3 and guard < 20000:
        guard += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if cr(a, b, c) <= 1e-9:
                continue
            if any(cr(a, b, poly[j]) >= -1e-9 and cr(b, c, poly[j]) >= -1e-9 and cr(c, a, poly[j]) >= -1e-9
                   for j in idx if j not in (i0, i1, i2)):
                continue
            tris += [i0, i1, i2]
            idx.pop(k)
            break
        else:                                        # tidak ada telinga: buang titik segaris
            k = min(range(len(idx)), key=lambda q: abs(cr(poly[idx[q - 1]], poly[idx[q]], poly[idx[(q + 1) % len(idx)]])))
            idx.pop(k)
    return tris + idx


def prism(poly, a0, a1, axis="z"):
    """poligon (u, v) ditarik dari a0 ke a1. axis z: (x, y) = (u, v); axis x: (y, z) = (u, v)"""
    pts = [poly[0]]
    for q in poly[1:]:
        if math.dist(q, pts[-1]) > 1e-4:
            pts.append(q)
    if math.dist(pts[0], pts[-1]) < 1e-4:
        pts.pop()
    if area2(pts) < 0:
        pts.reverse()

    def V(u, v, w):
        return (u, v, w) if axis == "z" else (w, u, v)
    P, I = [], []
    tri = earclip(pts)
    n = len(pts)
    for u, v in pts:
        P += V(u, v, a1)
    I += tri
    for u, v in pts:
        P += V(u, v, a0)
    I += [n + t for t in reversed(tri)]
    for k in range(n):
        (u0, v0), (u1, v1) = pts[k], pts[(k + 1) % n]
        quad(P, I, V(u0, v0, a0), V(u1, v1, a0), V(u1, v1, a1), V(u0, v0, a1))
    return P, I


def circle(cu, cv, r, n=40):
    return [(cu + r * math.cos(2 * math.pi * k / n), cv + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def rrect(x0, x1, y0, y1, r):
    return fillet_dense([(x1, y0, r), (x1, y1, r), (x0, y1, r), (x0, y0, r)], mirror=False)


def stadium(y0, y1, z0, z1, n=20):
    """penampang pack 2 sel berdampingan di bidang (y, z)"""
    r = (z1 - z0) / 2
    zc = (z0 + z1) / 2
    out = [(y1 - r + r * math.cos(-math.pi / 2 + math.pi * k / n), zc + r * math.sin(-math.pi / 2 + math.pi * k / n))
           for k in range(n + 1)]
    out += [(y0 + r + r * math.cos(math.pi / 2 + math.pi * k / n), zc + r * math.sin(math.pi / 2 + math.pi * k / n))
            for k in range(n + 1)]
    return out


def smooth(pts, k=3):
    for _ in range(k):
        q = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            q += [tuple(a[i] * 0.75 + b[i] * 0.25 for i in range(3)), tuple(a[i] * 0.25 + b[i] * 0.75 for i in range(3))]
        q.append(pts[-1])
        pts = q
    return pts


def tube(path, r, n=8):
    path = smooth(path)
    P, I, m = [], [], len(path)
    for k, p in enumerate(path):
        a, b = path[max(k - 1, 0)], path[min(k + 1, m - 1)]
        t = [b[i] - a[i] for i in range(3)]
        lt = math.sqrt(sum(c * c for c in t)) or 1.0
        t = [c / lt for c in t]
        ref = (0.0, 0.0, 1.0) if abs(t[2]) < 0.9 else (1.0, 0.0, 0.0)
        u = [ref[1] * t[2] - ref[2] * t[1], ref[2] * t[0] - ref[0] * t[2], ref[0] * t[1] - ref[1] * t[0]]
        lu = math.sqrt(sum(c * c for c in u))
        u = [c / lu for c in u]
        v = [t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0]]
        for j in range(n):
            ca, sa = math.cos(2 * math.pi * j / n), math.sin(2 * math.pi * j / n)
            P += [p[i] + r * (ca * u[i] + sa * v[i]) for i in range(3)]
    for k in range(m - 1):
        for j in range(n):
            a, b, c, d = k * n + j, k * n + (j + 1) % n, (k + 1) * n + (j + 1) % n, (k + 1) * n + j
            I += [a, b, c, a, c, d]
    return P, I


def band(path, x0, x1, t):
    """pita tertutup: path (y, z) = sisi dalam, tebal t ke luar, lebar x0..x1"""
    n = len(path)
    cy, cz = sum(p[0] for p in path) / n, sum(p[1] for p in path) / n
    outer = []
    for k in range(n):
        (ay, az), (by, bz), (qy, qz) = path[k - 1], path[k], path[(k + 1) % n]
        ny, nz = (bz - az) + (qz - bz), -(by - ay) - (qy - by)
        ln = math.hypot(ny, nz) or 1.0
        ny, nz = ny / ln, nz / ln
        if ny * (by - cy) + nz * (bz - cz) < 0:
            ny, nz = -ny, -nz
        outer.append((by + ny * t, bz + nz * t))
    P, I = [], []
    for k in range(n):
        j = (k + 1) % n
        i0, i1, o0, o1 = path[k], path[j], outer[k], outer[j]
        quad(P, I, (x0, *o0), (x1, *o0), (x1, *o1), (x0, *o1))
        quad(P, I, (x0, *i0), (x0, *i1), (x1, *i1), (x1, *i0))
        quad(P, I, (x0, *i0), (x0, *o0), (x0, *o1), (x0, *i1))
        quad(P, I, (x1, *i0), (x1, *i1), (x1, *o1), (x1, *o0))
    return P, I


def sphere(c, r, n=20):
    P, I = [], []
    for a in range(n + 1):
        th = math.pi * a / n
        for b in range(2 * n):
            ph = math.pi * b / n
            P += [c[0] + r * math.sin(th) * math.cos(ph), c[1] + r * math.sin(th) * math.sin(ph), c[2] + r * math.cos(th)]
    for a in range(n):
        for b in range(2 * n):
            p0, p1 = a * 2 * n + b, a * 2 * n + (b + 1) % (2 * n)
            I += [p0, p0 + 2 * n, p1 + 2 * n, p0, p1 + 2 * n, p1]
    return P, I


# ---------- selalu ada: motor, roda (ban dilebarkan 12 -> 18 mm ke luar) ----------
reuse(["Gearbox N20", "Motor N20", "Tutup motor", "Encoder PCB", "Magnet encoder", "Konektor encoder", "As roda"], "base")
reuse(["Ban merah", "Velg"], "base", fx=lambda x: math.copysign(WX + (abs(x) - WX) * W_T / 12.0, x))

# ---------- bagian depan (ikut geser dy): PCB sensor, PCB utama rev B + komponen, ball caster ----------
reuse(["PCB sensor", "Sensor QRE1113GR x12", "QRE1113GR *", "Resistor SMD sensor", "Silkscreen sensor*",
       "Pad lubang sensor", "IC mux *", "C 100 nF mux", "Header JST XH J1", "Steker JST XH J1", "Spacer nilon 4 mm",
       "Mur M3"], "front")
emit("PCB utama rev B", "pcb", "front", prism(TRAP, MB_Z0, MBT))
for hx, hy in MB_HOLE:
    emit("Spacer M3", "nylon", "front", prism(circle(hx, hy, 2.75, 6), CH_Z1, MB_Z0))
    emit("Baut M3", "chrome", "front", prism(circle(hx, hy, 2.6, 24), MBT, MBT + 1.8))
for ref, (x0, x1, y0, y1) in JST.items():
    emit(f"Header JST XH {ref}", "jst", "front", box(x0 + 0.45, x1 - 0.45, y0 + 0.5, y1 - 0.5, MBT, MBT + 7.0))
    emit(f"Steker JST XH {ref}", "jst_plug", "front", box(x0 + 1.4, x1 - 1.4, y0 + 1.4, y1 - 1.4, MBT + 2.0, MBT + 9.8))
for y in (26.2, 29.6):
    emit("Resistor R1/R2", "resistor", "front", prism(circle(y, MBT + 1.3, 1.2, 12), -14.6, -8.2, "x"))
reuse(["ESP32 *"], "front", dy=7.5, dz=MBT - 12.0)
reuse(["TB6612 PCB", "TB6612 chip"], "front", dx=-48.9, dy=10.9, dz=-1.4)
reuse(["Buzzer"], "front", dx=-13.5, dy=16.0, dz=MBT - 12.0)
reuse(["Saklar", "Saklar tuas"], "front", dx=10.3, dy=8.2, dz=MBT - 12.0)
reuse(["Elko C1 *"], "front", dx=44.95, dy=-11.9, dz=MBT - 12.0)
reuse(["MP1584 *"], "front", dx=-33.9, dy=91.5, dz=MBT - 12.0)
reuse(["Dioda 1N5819*"], "front", dx=-0.9, dy=92.0, dz=MBT - 12.0)
emit("Socket J6", "black_plastic", "front", box(J6[0] + 0.3, J6[1] - 0.3, J6[2] + 0.5, J6[3] - 0.5, MBT, MBT + SOCK))
emit("Ball caster rumah", "black_plastic", "front", prism(circle(0, CASTER_Y, 6.5, 32), 4.0, CH_Z0))
emit("Ball caster bola", "chrome", "front", sphere((0, CASTER_Y, 5.0), 5.0), dbl=False)
WIRE = ["wire_red", "wire_yel", "wire_blk"] + ["wire_blu"] * 5
for k in range(8):                                   # kabel J5 -> J1 PCB sensor (urutan pin sama)
    xa, xb = 13.0 - 2.5 * k, 8.75 - 2.5 * k
    emit(f"Kabel sensor pin {k + 1}", WIRE[k], "front",
         tube([(xa, 77.8, MBT + 9.6), (xa, 78.6, MBT + 14.5), ((xa + xb) / 2, 89.0, MBT + 13.5), (xb, 99.6, 23.5),
               (xb, 100.0, 17.2)], 0.55, 6))

# ---------- board interface rev A (ikut geser): PCB, OLED di socket, 5 tombol 6x6, header ke J6 ----------
emit("Board interface rev A", "pcb", "front", prism(rrect(IB[0], IB[1], IB[2], IB[3], 3.0), IB_Z0, IBT))
emit("Header J1 interface", "black_plastic", "front", box(J6[0] + 0.3, J6[1] - 0.3, J6[2] + 0.5, J6[3] - 0.5, MBT + SOCK, IB_Z0))
reuse(["OLED *"], "front", dx=-4.0, dy=-6.1, dz=IBT - 12.0)
for bx_, by_ in BTN:
    reuse(["Tombol", "Tombol tutup"], "front", dx=bx_ + 22.0, dy=by_ - 66.0, dz=IBT - 12.0,
          pred=lambda o: min(o["p"][0::3]) < 0)


# ---------- per susunan: skid plate, baterai, strap, dudukan, kabel ----------
def build(key):
    L = LAYOUT[key]
    g, dy = "opt-" + key, L["dy"]
    emit("Skid plate 3D print", "skid", g, prism(SKID[key], CH_Z0, CH_Z1))
    if not L["pack"]:
        reuse(["Dudukan motor + baterai (3D print)", "Holder 2x18650", "Baterai 18650*"], g)
        reuse(["Modul charger 2S", "USB-C charger"], g, dz=-2.5)
        return
    for s in (-1, 1):                                # klem motor: 2 pelana per motor, menyatu dengan skid plate
        for xa, xb in ((15.0, 26.0), (29.5, 36.5)):
            x0, x1 = sorted((s * xa, s * xb))
            emit("Klem motor", "skid", g, merge(box(x0, x1, -8.2, -6.3, CH_Z1, 23.6), box(x0, x1, 6.3, 8.2, CH_Z1, 23.6),
                                                box(x0, x1, -8.2, 8.2, 22.15, 23.6)))
    x0, x1, y0, y1, z0, z1 = pack_box(L)
    yc, zc = (y0 + y1) / 2, (z0 + z1) / 2
    emit("Pack Li-ion 14500 2S", "pack", g, prism(stadium(y0, y1, z0, z1), x0 + 1.0, x1 - 1.0, "x"))
    for xa, xb in ((x0, x0 + 1.0), (x1 - 1.0, x1)):  # tutup ujung (barley paper)
        emit("Pack ujung", "pack_end", g, prism(stadium(y0 + 0.6, y1 - 0.6, z0 + 0.6, z1 - 0.6), xa, xb, "x"))
    # strap: naik di belakang pack, melewati atas, turun di depan, kembali lewat bawah plat (atau bawah bak)
    zb = (z0 - 1.5 if key == "bak" else CH_Z0) - 0.45
    r, o = PACK_H / 2, 0.35
    path = [(y0 - o, zb)]
    path += [(y0 + r + (r + o) * math.cos(math.pi - math.pi / 2 * k / 10), zc + (r + o) * math.sin(math.pi - math.pi / 2 * k / 10))
             for k in range(11)]
    path += [(y1 - r + (r + o) * math.cos(math.pi / 2 - math.pi / 2 * k / 10), zc + (r + o) * math.sin(math.pi / 2 - math.pi / 2 * k / 10))
             for k in range(11)]
    path += [(y1 + o, zb)]
    emit("Strap velcro 16 mm", "strap", g, band(path, -STRAP_W / 2, STRAP_W / 2, STRAP_T))
    emit("Gesper strap", "buckle", g, box(-STRAP_W / 2 - 1.5, STRAP_W / 2 + 1.5, yc + 4.0, yc + 8.5, z1 + o + STRAP_T - 0.2, z1 + o + STRAP_T + 1.6))
    if key == "bak":                                 # bak: lantai + 4 dinding, menggantung dari skid plate
        f0, f1 = z0 - 1.5, z0
        emit("Bak baterai", "skid", g, merge(
            box(-27.0, 27.0, -43.5, -9.5, f0, f1), box(-27.0, -25.5, -43.5, -9.5, f1, CH_Z1),
            box(25.5, 27.0, -43.5, -9.5, f1, CH_Z1), box(-25.5, -9.5, -43.5, -42.0, f1, CH_Z1),
            box(9.5, 25.5, -43.5, -42.0, f1, CH_Z1), box(-25.5, -9.5, -11.0, -9.5, f1, CH_Z1),
            box(9.5, 25.5, -11.0, -9.5, f1, CH_Z1)))
    else:                                            # bibir penahan di 4 sudut + penahan ujung kanan
        lips = [box(sx0, sx1, ya, yb, CH_Z1, CH_Z1 + 4.0) for sx0, sx1 in ((-23.0, -10.5), (10.5, 23.0))
                for ya, yb in ((y0 - 1.6, y0 - 0.2), (y1 + 0.2, y1 + 1.6))]
        emit("Bibir penahan pack", "skid", g, merge(*lips, box(x1 + 0.3, x1 + 1.8, y0 + 6.0, y1 - 6.0, CH_Z1, CH_Z1 + 4.0)))
    # kabel pack (merah/hitam) keluar dari ujung kiri -> steker XH di J1; kabel balancer ke steker XH 3 pin
    yj = 28.1 + dy
    for o_, mat, xj in ((0.9, "wire_red", -1.25), (-0.9, "wire_blk", 1.25)):
        if key == "tengah":
            mid = [(-30.0, yc + 3, zc + 3), (-30.0, yj - 7.5, 26.0), (-13.0, yj - 5.0, 30.0)]
        else:
            mid = [(-30.0, yc + 2, zc + 2), (-31.0, -9.0, 25.6), (-27.0, 6.0, 26.6), (-12.0, 20.0, 29.6)]
        pts = [(x0, yc + 2 + o_, zc)] + [(a + o_, b, c + o_) for a, b, c in mid] + [(xj, yj - 0.5, 31.0), (xj, yj, MBT + 9.6)]
        emit("Kabel pack", mat, g, tube(pts, 0.8))
    py = yc - 6.0
    emit("Steker balancer XH 3 pin", "jst_plug", g, box(-37.0, -30.0, py - 3.0, py + 3.0, CH_Z1, CH_Z1 + 5.7))
    for k, mat in enumerate(("wire_blk", "wire_blu", "wire_red")):
        emit("Kabel balancer", mat, g, tube([(x0, yc - 3 + k * 1.2, zc - 1), (-28.5, yc - 3, zc + 1),
                                             (-29.5, py - 1.2 + k * 1.2, CH_Z1 + 6.5), (-31.0, py - 1.2 + k * 1.2, CH_Z1 + 3.0)], 0.5, 6))
    for s in (-1, 1):                                # kabel motor + encoder (6 kawat, digambar satu selubung) ke J2/J3
        xj = s * 25.65
        if key == "tengah":                          # memutari ujung pack
            pts = [(s * 7.2, 0, 19.0), (s * 10.0, 3.0, 25.0), (s * 31.0, 8.0, 25.0), (s * 33.0, yc, 21.0),
                   (s * 31.0, yj - 8.0, 26.0), (xj, yj - 1.0, 30.5), (xj, yj, MBT + 9.6)]
        else:
            pts = [(s * 7.2, 0, 19.0), (s * 8.0, 4.0, 24.5), (s * 16.0, 14.0, 25.5), (xj, yj - 3.0, 30.5), (xj, yj, MBT + 9.6)]
        emit("Kabel motor + encoder", "ribbon", g, tube(pts, 1.4))


for _k in ORDER:
    build(_k)

json.dump({"mats": MATS, "meshes": MESH}, open(os.path.join(HERE, "konsep-v18-model.json"), "w", encoding="utf-8"),
          separators=(",", ":"))


# ------------------------------ halaman ------------------------------
def fmt(v, n=1):
    return f"{v:.{n}f}".replace(".", ",")


B, A = RES["v17"], RES["ransel"]


def metrics(k):
    r, L = RES[k], LAYOUT[k]
    return [["Puncak baterai", f"{fmt(r['batt_top'], 0 if r['batt_top'] % 1 == 0 else 1)} mm"],
            ["Ukuran p × l × t", f"{r['p']:.0f} × {r['l']:.0f} × {r['t']:.0f} mm"],
            ["Perkiraan massa", f"±{r['M']:.0f} g"],
            ["Berat di roda penggerak", f"{(1 - r['caster']) * 100:.0f}%"],
            ["Poros → sensor depan", f"{SENS_Y1 + L['dy']:.0f} mm"],
            ["Celah lantai terendah", f"{fmt(r['low'])} mm"]]


META = {k: dict(nama=LAYOUT[k]["nama"], sub=LAYOUT[k]["sub"], teks=LAYOUT[k]["teks"], dy=LAYOUT[k]["dy"],
                kv=metrics(k), pack=list(pack_box(LAYOUT[k])) if LAYOUT[k]["pack"] else None) for k in ORDER}


def row(nama, f):
    return "<tr><td>" + nama + "</td>" + "".join(f"<td>{f(RES[k], LAYOUT[k])}</td>" for k in ORDER) + "</tr>"


rows = "".join([
    row("Puncak baterai dari lantai", lambda r, L: f"{fmt(r['batt_top'], 0 if r['batt_top'] % 1 == 0 else 1)} mm"),
    row("Ukuran p × l × t", lambda r, L: f"{r['p']:.0f} × {r['l']:.0f} × {r['t']:.0f} mm"),
    row("Jarak poros roda → sensor depan", lambda r, L: f"{SENS_Y1 + L['dy']:.0f} mm"),
    row("Perkiraan massa", lambda r, L: f"±{r['M']:.0f} g"),
    row("Tinggi titik berat", lambda r, L: f"{fmt(r['zcm'])} mm"),
    row("Berat di roda penggerak / ball caster", lambda r, L: f"{(1 - r['caster']) * 100:.0f}% / {r['caster'] * 100:.0f}%"),
    row("Percepatan maksimum tanpa selip (μ 0,6)", lambda r, L: f"{fmt(r['a_slip'])} m/s²"),
    row("Celah lantai terendah (di luar sensor)", lambda r, L: f"{fmt(r['low'])} mm"),
    row("Yang berubah dari v17", lambda r, L: {
        "v17": "acuan", "ransel": "ekor skid plate +11 mm, celah strap", "bak": "ekor +11,5 mm, bak di bawah plat",
        "tengah": "bagian depan maju 22 mm, plat belakang dipotong"}[next(k for k in ORDER if LAYOUT[k] is L)]),
])
head = "".join(f"<th>{LAYOUT[k]['nama']}</th>" for k in ORDER)
checks = "".join(f"<li><b>{LAYOUT[k]['nama']}:</b> " + ("; ".join(RES[k]["prob"]) or "0 masalah") + "</li>" for k in ORDER)
tabs = "".join(f'<button type="button" data-opt="{k}" aria-pressed="{"true" if k == "ransel" else "false"}">'
               f'<b>{LAYOUT[k]["nama"]}</b><span>{LAYOUT[k]["sub"]}</span></button>' for k in ORDER)
OK = not any(RES[k]["prob"] for k in ORDER)

PAGE = r"""<title>Konsep LFM v18</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* lembar konsep (sama dengan konsep v17): kertas hijau-abu, tinta gelap; panggung 3D di tengah, angka di bawahnya */
:root {
  --bg: #f3f5f2; --paper: #fbfcfa; --ink: #1c2420; --muted: #5d6b63; --line: #c9d2cc;
  --accent: #b4521f; --good: #2f7a4f; --pick: #d3202e; --on-pick: #ffffff; --stage: #e6eaee; --floor: #f4f4f1;
  --display: "IBM Plex Sans", system-ui, sans-serif; --mono: "IBM Plex Mono", ui-monospace, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #121614; --paper: #181d1a; --ink: #e4ebe6; --muted: #98a69e; --line: #2e3833;
  --accent: #e08a5a; --good: #59a87a; --pick: #e2414d; --on-pick: #ffffff; --stage: #232a2f; --floor: #3a4046;
  color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #121614; --paper: #181d1a; --ink: #e4ebe6; --muted: #98a69e; --line: #2e3833;
  --accent: #e08a5a; --good: #59a87a; --pick: #e2414d; --on-pick: #ffffff; --stage: #232a2f; --floor: #3a4046;
  color-scheme: dark; }
body { background: var(--bg); color: var(--ink); font-family: var(--display); font-size: 15px; line-height: 1.55;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 28px 48px; }
main { max-width: 1080px; margin: 0 auto; display: grid; gap: 28px; }
h1 { font-size: 1.7rem; font-weight: 600; margin: 0; text-wrap: balance; letter-spacing: -0.01em; }
h2 { font-size: 0.78rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.09em; color: var(--muted); margin: 0 0 10px; }
p { margin: 0; max-width: 68ch; }
.lead { color: var(--muted); }
.viewer { display: grid; gap: 10px; min-width: 0; }
.tabs { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
@media (max-width: 720px) { .tabs { grid-template-columns: 1fr 1fr; } }
.tabs button { display: grid; gap: 1px; text-align: left; font: inherit; color: var(--ink); background: var(--paper);
  border: 1px solid var(--line); border-radius: 6px; padding: 9px 12px; cursor: pointer; min-width: 0; }
.tabs button b { font-weight: 600; }
.tabs button span { font-size: 0.8rem; color: var(--muted); }
.tabs button[aria-pressed="true"] { background: var(--pick); border-color: var(--pick); color: var(--on-pick); }
.tabs button[aria-pressed="true"] span { color: var(--on-pick); opacity: 0.85; }
.tabs button:focus-visible, .views button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
#stage { position: relative; background: var(--stage); border: 1px solid var(--line); border-radius: 6px; overflow: hidden;
  aspect-ratio: 16 / 9; max-height: 640px; width: 100%; }
@media (max-width: 720px) { #stage { aspect-ratio: 4 / 5; } }
#stage canvas { display: block; width: 100%; height: 100%; outline: none; touch-action: none; }
.views { position: absolute; top: 10px; right: 10px; display: flex; gap: 2px; background: var(--paper);
  border: 1px solid var(--line); border-radius: 6px; padding: 3px; }
.views button { font: 500 0.8rem var(--display); color: var(--ink); background: transparent; border: 0; border-radius: 4px;
  padding: 6px 9px; cursor: pointer; }
.views button[aria-pressed="true"] { background: var(--ink); color: var(--paper); }
.hint { position: absolute; left: 10px; bottom: 10px; font-size: 0.75rem; color: var(--muted); background: var(--paper);
  border-radius: 4px; padding: 3px 8px; pointer-events: none; }
#loading { position: absolute; inset: 0; display: grid; place-items: center; font-family: var(--mono); font-size: 0.82rem;
  color: var(--muted); pointer-events: none; text-align: center; padding: 16px; }
.info { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: 20px; align-items: start;
  background: var(--paper); border: 1px solid var(--line); border-radius: 6px; padding: 16px; }
@media (max-width: 720px) { .info { grid-template-columns: 1fr; } }
.info h3 { margin: 0 0 4px; font-size: 1.05rem; font-weight: 600; }
.info p { font-size: 0.92rem; }
.kv { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px 16px; margin: 0; }
@media (max-width: 480px) { .kv { grid-template-columns: 1fr 1fr; } }
.kv div { min-width: 0; }
.kv dt { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
.kv dd { margin: 0; font-family: var(--mono); font-size: 0.95rem; font-variant-numeric: tabular-nums; }
table { border-collapse: collapse; width: 100%; font-size: 0.92rem; min-width: 760px; }
.tablewrap { overflow-x: auto; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-weight: 500; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; }
td { font-variant-numeric: tabular-nums; }
td:first-child { color: var(--muted); }
th:nth-child(3), td:nth-child(3) { background: color-mix(in srgb, var(--good) 9%, transparent); }
th:nth-child(3) { color: var(--good); }
ol, ul { margin: 0; padding-left: 1.2em; display: grid; gap: 6px; max-width: 72ch; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }
@media (max-width: 720px) { .cols { grid-template-columns: 1fr; } }
.cols > section { min-width: 0; }
.note { font-size: 0.85rem; color: var(--muted); }
</style>
<script type="importmap">{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/" } }</script>
<main>
  <header style="display:grid;gap:10px">
    <h1>Konsep LFM v18: pack Li-ion 2S diikat strap</h1>
    <p class="lead">Holder 2× 18650 di atas motor diganti pack 7,4 V siap colok (50 × 30 × 15 mm, 46 g) yang rebah di skid
    plate dan diikat strap velcro. Baterai jadi sebidang dengan PCB, tidak bertingkat. PCB utama rev B, board interface,
    dan PCB sensor tidak diubah. Pilih susunan di bawah, lalu putar modelnya.</p>
  </header>

  <section class="viewer">
    <div class="tabs" role="group" aria-label="Susunan baterai">__TABS__</div>
    <div id="stage" aria-label="Model 3D robot, bisa diputar dengan mouse atau jari">
      <div id="loading">memuat model 3D…</div>
      <div class="views" role="group" aria-label="Sudut pandang">
        <button type="button" data-view="rear" aria-pressed="true">Belakang</button>
        <button type="button" data-view="front" aria-pressed="false">Depan</button>
        <button type="button" data-view="side" aria-pressed="false">Samping</button>
        <button type="button" data-view="top" aria-pressed="false">Atas</button>
      </div>
      <div class="hint">seret untuk memutar · scroll atau cubit untuk zoom · garis hitam = lintasan 20 mm</div>
    </div>
    <div class="info">
      <div><h3 id="o-nama"></h3><p id="o-teks"></p></div>
      <dl class="kv" id="o-kv"></dl>
    </div>
  </section>

  <section>
    <h2>Angka</h2>
    <div class="tablewrap"><table><thead><tr><th></th>__HEAD__</tr></thead><tbody>__ROWS__</tbody></table></div>
    <p class="note" style="margin-top:10px">Massa dan pembagian berat dihitung dari massa perkiraan tiap bagian
    (<code>docs/perhitungan-motor.md</code> bagian 4, belum ditimbang). Pakai untuk membandingkan susunan, bukan angka pasti.</p>
  </section>

  <div class="cols">
    <section>
      <h2>Kenapa A · Ransel</h2>
      <ul>__WHY__</ul>
    </section>
    <section>
      <h2>Soal pack-nya</h2>
      <ul>__PACK__</ul>
    </section>
  </div>

  <div class="cols">
    <section>
      <h2>Perlu diputuskan</h2>
      <ol>__TODO__</ol>
    </section>
    <section>
      <h2>Hasil cek otomatis (kotak 3D tiap bagian)</h2>
      <ul>__CHECKS__</ul>
      <p class="note" style="margin-top:10px">Yang dicek: tabrakan antar bagian (pack, strap, motor, ban, PCB, ball caster), pack di
      dalam skid plate, PCB utama ≥ 1,5 mm dari tepi skid plate, jalur steker USB ESP32, akses tuas SW1, batas ukuran dan massa lomba.</p>
    </section>
  </div>
</main>

<script type="module">
const META = __META__;
const ORDER = __ORDER__;
const $ = (s) => document.querySelector(s);
let setOpt3d = () => {};

function showOpt(k) {
  const m = META[k];
  $('#o-nama').textContent = m.nama + ' · ' + m.sub;
  $('#o-teks').textContent = m.teks;
  $('#o-kv').replaceChildren(...m.kv.map(([a, b]) => {
    const d = document.createElement('div'), dt = document.createElement('dt'), dd = document.createElement('dd');
    dt.textContent = a; dd.textContent = b; d.append(dt, dd); return d;
  }));
  document.querySelectorAll('[data-opt]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.opt === k)));
  setOpt3d(k);
}
const q = new URLSearchParams(location.search);
let current = ORDER.includes(location.hash.slice(1)) ? location.hash.slice(1) : (q.get('opt') || 'ransel');
document.querySelectorAll('[data-opt]').forEach(b => b.addEventListener('click', () => { current = b.dataset.opt; showOpt(current); }));
showOpt(current);

try {
  const THREE = await import('three');
  const { OrbitControls } = await import('three/addons/controls/OrbitControls.js');
  const { RoomEnvironment } = await import('three/addons/environments/RoomEnvironment.js');
  const stage = $('#stage');
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  stage.prepend(renderer.domElement);

  const scene = new THREE.Scene();
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  const camera = new THREE.PerspectiveCamera(30, 1, 1, 5000);
  camera.up.set(0, 0, 1);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.minDistance = 120; controls.maxDistance = 900;

  const floorMat = new THREE.MeshStandardMaterial({ roughness: 0.95 });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(3000, 3000), floorMat);
  floor.receiveShadow = true; scene.add(floor);
  const tape = new THREE.Mesh(new THREE.PlaneGeometry(20, 1400), new THREE.MeshStandardMaterial({ color: '#141414', roughness: 0.8 }));
  tape.position.set(0, 100, 0.05); tape.receiveShadow = true; scene.add(tape);
  function theme() {
    const cs = getComputedStyle(document.documentElement);
    scene.background = new THREE.Color(cs.getPropertyValue('--stage').trim());
    floorMat.color.set(cs.getPropertyValue('--floor').trim());
  }
  theme();
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', theme);
  new MutationObserver(theme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  const key = new THREE.DirectionalLight('#ffffff', 2.2);
  key.position.set(160, -200, 420);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  Object.assign(key.shadow.camera, { left: -170, right: 170, top: 190, bottom: -150, near: 50, far: 1200 });
  key.shadow.bias = -0.0004; key.shadow.radius = 4;
  key.target.position.set(0, 40, 0); scene.add(key.target, key);
  scene.add(new THREE.HemisphereLight('#ffffff', '#c9ced6', 0.6));

  const data = await (await fetch('konsep-v18-model.json')).json();
  const mats = {}, matsD = {};
  for (const [k, [c, r, m]] of Object.entries(data.mats)) {
    mats[k] = new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
    matsD[k] = mats[k].clone(); matsD[k].side = THREE.DoubleSide;
  }
  mats.screen.emissive = new THREE.Color('#7fc4ff'); mats.screen.emissiveIntensity = 1.4;
  mats.glass.envMapIntensity = 1.6;
  const groups = {};
  const group = (n) => groups[n] || (groups[n] = scene.add(new THREE.Group()).children.at(-1));
  for (const o of data.meshes) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(o.p, 3));
    g.setIndex(o.i);
    g.computeVertexNormals();
    const mesh = new THREE.Mesh(g, (o.d ? matsD : mats)[o.m]);
    mesh.name = o.n; mesh.castShadow = !['screen', 'silk', 'gold'].includes(o.m); mesh.receiveShadow = true;
    group(o.g).add(mesh);
  }
  // label pack: teks di sisi atas, di kanan strap
  const cv = document.createElement('canvas'); cv.width = 384; cv.height = 256;
  const cx = cv.getContext('2d');
  cx.fillStyle = '#f2f2ee'; cx.font = '600 76px "IBM Plex Sans", sans-serif'; cx.textAlign = 'center';
  cx.fillText('Li-ion 2S', 192, 104); cx.font = '500 64px "IBM Plex Sans", sans-serif'; cx.fillText('7,4 V', 192, 196);
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const labelMat = new THREE.MeshBasicMaterial({ map: tex, transparent: true });
  for (const k of ORDER) {
    const p = META[k].pack; if (!p) continue;
    const lb = new THREE.Mesh(new THREE.PlaneGeometry(13.5, 9), labelMat);
    lb.position.set(16.2, (p[2] + p[3]) / 2, p[5] + 0.06);
    group('opt-' + k).add(lb);
  }

  const VIEWS = {
    rear:  { pos: [125, -205, 125], tgt: [0, 32, 14] },
    front: { pos: [-150, 255, 140], tgt: [0, 48, 14] },
    side:  { pos: [-400, 45, 24],   tgt: [0, 45, 20] },
    top:   { pos: [0, 44.9, 430],   tgt: [0, 45, 0] },
  };
  function setView(v) {
    const s = VIEWS[v]; if (!s) return;
    camera.position.set(...s.pos); controls.target.set(...s.tgt); controls.update();
    document.querySelectorAll('[data-view]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === v)));
  }
  document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => setView(b.dataset.view)));
  setOpt3d = (k) => {
    for (const o of ORDER) group('opt-' + o).visible = o === k;
    group('front').position.y = META[k].dy;
  };
  setOpt3d(current);
  setView(q.get('view') || 'rear');

  function resize() {
    const w = stage.clientWidth, h = stage.clientHeight;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(stage); resize();
  $('#loading').remove();
  renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
  window.modelReady = true;
} catch (e) {
  $('#loading').textContent = 'Model 3D tidak bisa dimuat di perangkat ini (' + e.message + '). Angka di bawah tetap berlaku.';
}
</script>
"""

WHY = [
    f"<b>Tidak bertingkat.</b> Puncak baterai turun dari {B['batt_top']:.0f} mm ke {A['batt_top']:.0f} mm, di bawah puncak ESP32 "
    f"({fmt(ESP_TOP)} mm). Dudukan baterai, holder, charger, dan BMS hilang dari robot.",
    f"<b>Strap saja, seperti idemu.</b> Satu strap velcro 16 mm melingkari pack lewat celah di skid plate; bibir 4 mm di empat "
    "sudut menahan pack supaya tidak bergeser. Lepas-pasang tanpa alat.",
    f"<b>Pack di belakang poros menyeimbangkan elektronik di depan.</b> Berat di roda penggerak {(1 - A['caster']) * 100:.0f}% "
    f"(C · Tengah hanya {(1 - RES['tengah']['caster']) * 100:.0f}%), jadi traksi paling baik di antara susunan pack.",
    f"<b>Robot jauh lebih ringan:</b> ±{B['M']:.0f} g → ±{A['M']:.0f} g, sehingga motor N20 yang sama berakselerasi lebih cepat. "
    f"Panjang hanya bertambah {A['p'] - B['p']:.0f} mm ({B['p']:.0f} → {A['p']:.0f} mm), lebar tetap {A['l']:.0f} mm.",
]
PACKNOTE = [
    "<b>Kapasitas 5.000 mAh di listing tidak mungkin benar.</b> Dua sel 14500 seberat 46 g realistisnya 600–1.000 mAh. Dengan "
    "konsumsi robot dari perhitungan kita, itu kira-kira 1–1,5 jam jalan. Masih jauh di atas kebutuhan match 5 menit, tetapi "
    "jangan menulis 5.000 mAh di laporan.",
    "<b>Pilih varian konektor XH 2 pin</b> supaya langsung masuk J1 di PCB utama. Sebelum colok pertama, ukur polaritasnya dengan "
    "multimeter: di PCB kita pin 1 J1 = BAT+ dan pin 2 = GND, dan tidak ada proteksi polaritas terbalik.",
    "<b>Cas di luar robot</b> lewat kabel balancer (XH 3 pin) dengan charger balance 2S. Di model ini modul charger USB-C dan BMS "
    "sudah saya keluarkan.",
    "<b>Proteksi:</b> tanyakan ke penjual apakah pack punya papan proteksi. Kalau tidak, batas bawah tegangan dijaga firmware lewat "
    "VBAT_SENSE (GPIO39), yang memang sudah ada di rancangan.",
    "<b>Aturan lomba (guidebook hal. 8):</b> jenis Li-ion dan maksimum 8,2 V ± 1 V terpenuhi. Tetapi butir A.e menulis "
    "maksimal 4.000 mAh, sedangkan label pack ini 5.000 mAh. Kapasitas aslinya jauh di bawah itu, tetapi yang dibaca saat "
    "pemeriksaan adalah labelnya: tanyakan ke panitia, atau cari varian berlabel ≤ 4.000 mAh.",
    "<b>RAB:</b> yang keluar Rp137.990 (18650 Rp94.990, holder Rp8.000, BMS Rp10.000, charger Rp25.000). Harga pack dan charger "
    "balance belum saya tahu.",
]
TODO = [
    "Susunan mana yang dipakai: A · Ransel, B · Bak, atau C · Tengah.",
    "Cas di luar robot dengan charger balance (seperti di model), atau tetap mau cas USB-C di robot? Kalau tetap, charger dan BMS "
    "perlu tempat lagi.",
    "Harga pack dan charger balance, supaya RAB bisa dihitung ulang.",
    "Label 5.000 mAh terhadap batas 4.000 mAh di guidebook: perlu jawaban panitia sebelum pack dibeli.",
    "Panjang kabel pack: dari posisi A butuh ±8 cm sampai J1. Kalau kabel pack lebih pendek, pack diputar atau J1 diberi kabel sambung.",
]
html = (PAGE.replace("__TABS__", tabs).replace("__HEAD__", head).replace("__ROWS__", rows).replace("__CHECKS__", checks)
        .replace("__WHY__", "".join(f"<li>{s}</li>" for s in WHY)).replace("__PACK__", "".join(f"<li>{s}</li>" for s in PACKNOTE))
        .replace("__TODO__", "".join(f"<li>{s}</li>" for s in TODO))
        .replace("__META__", json.dumps(META, ensure_ascii=False)).replace("__ORDER__", json.dumps(ORDER)))
out = os.path.join(HERE, "konsep-v18.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
for k in ORDER:
    r = RES[k]
    print(f"{k:7s} {r['p']:.1f} x {r['l']:.0f} x {r['t']:.0f} mm  baterai z<={r['batt_top']:.1f}  M {r['M']:.0f} g  "
          f"ycm {r['ycm']:.1f}  zcm {r['zcm']:.1f}  caster {r['caster'] * 100:.0f}%  a_selip {r['a_slip']:.1f}  "
          f"a_angkat {r['a_lift']:.1f}  celah lantai {r['low']:.1f}  celah {r['gap']}")
    for p in r["prob"]:
        print("   -", p)
print(f"mesh {len(MESH)}, json {os.path.getsize(os.path.join(HERE, 'konsep-v18-model.json')) / 1e6:.2f} MB, tulis {out}")
