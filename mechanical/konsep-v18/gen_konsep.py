"""Konsep v18 (susunan A "ransel", dipilih user 14/11/2026): pack Li-ion 2S 14500 (50 x 30 x 15 mm, 46 g) rebah di
belakang motor dan diikat strap, sebidang dengan PCB utama. Semua PCB punya pengikat sendiri:
  PCB sensor rev B      2 baut M3 di H1/H2 + spacer nilon ke hidung skid plate
  PCB utama rev B       4 baut M3 x 30 kepala benam dari bawah skid plate, boss 3 mm menyatu dengan skid plate
  rangka interface      3D print, 4 kaki di atas PCB utama, ikut 4 baut M3 yang sama (mur di atas kaki)
  board interface rev B 4 baut M2 ke boss rangka, tepi belakang (baris tombol) bertumpu di balok rangka
  OLED 0,96"            socket 4 pin + 4 spacer M2
PCB utama dan PCB sensor tidak diubah. Board interface rev B (39 x 45 mm, OLED di tengah, 5 tombol sebaris) dibuat
hardware/tools/gen_pcb_interface.py; angka posisinya disalin ke sini (IB, BTN, IB_HOLE, OLED_HOLE).

Riwayat: versi pertama konsep v18 (2x 18650 rebah) ditolak user; versi kedua membandingkan tiga susunan pack (ransel,
bak, tengah) dengan v17, ada di git (commit 620f487). v17 (holder 2x18650 di atas motor) masih dihitung di sini sebagai
pembanding angka.

Menulis konsep-v18.html (viewer 3D + angka), konsep-v18-model.json (mesh), dan interface-rev-b.png (render KiCad yang
dikecilkan), lalu mencetak hasil cek: tabrakan kotak 3D, batas ukuran lomba, perkiraan titik berat. Model 3D dirakit
tanpa CadQuery: komponen yang tidak berubah diambil dari mesh v16 (mechanical/viewer/model.json) lalu digeser ke posisi
PCB utama rev B / board interface rev B, sisanya dibuat di sini dari kotak, prisma, dan tabung.
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
SENS_H = [(-4.75, 85.55), (4.75, 85.55)]    # lubang M3 H1/H2 PCB sensor rev B
LIMIT = (250.0, 200.0, 100.0, 350.0)        # guidebook IARC XII SD: p, l, t (mm), massa (g, butir C)

# PCB utama rev B (tetap), posisi dari KiCad
MB_Y0, MB_Y1, MB_XR, MB_XF = 24.0, 82.0, 43.3, 31.0
MB_Z0 = 15.0
MBT = MB_Z0 + 1.6
SOCK, HDR = 8.5, 2.54                       # socket female 8,5 mm; plastik header pin 2,54 mm duduk di atasnya
DK_Z0 = MBT + SOCK + HDR                    # sisi bawah PCB ESP32 DevKit (model v16/v17 lupa plastik header: 2,54 lebih rendah)
EY = 46.15
ESP_TOP = DK_Z0 + 4.7                       # puncak kaleng modul ESP32
MB_HOLE = [(-38.5, 29.0), (38.5, 29.0), (-32.5, 56.0), (32.5, 56.0)]
JST = {"J2": (-34.90, -16.41, 24.66, 31.50), "J1": (-4.25, 4.25, 24.66, 31.50), "J3": (16.41, 34.90, 24.66, 31.50),
       "J5": (-7.50, 16.00, 74.91, 81.75)}
J6 = (-7.41, 8.91, 65.69, 69.32)

# board interface rev B (hardware/tools/gen_pcb_interface.py): OLED di tengah, 5 tombol sebaris di belakangnya
IB = (-19.5, 19.5, 34.0, 79.0)
IB_Z0 = MBT + 2 * SOCK + HDR                # J6 socket + header susun 8,5 + plastik header J1 -> 36,14
IBT = IB_Z0 + 1.6
BTN_Y, BTN_P = 41.6, 7.62
BTN = [(-2 * BTN_P, "KEMBALI"), (-BTN_P, "ATAS"), (0.0, "OK"), (BTN_P, "BAWAH"), (2 * BTN_P, "LANJUT")]
IB_HOLE = [(-17.0, 62.0), (17.0, 62.0), (-17.0, 76.5), (17.0, 76.5)]            # M2 ke rangka
OLED_HOLE = [(-11.75, 49.0), (11.75, 49.0), (-11.75, 72.8), (11.75, 72.8)]      # M2 spacer OLED
OLED_Y, OLED_Z0 = 61.0, IBT + SOCK + HDR    # tengah modul, sisi bawah PCB OLED
TOP_Z = OLED_Z0 + 2.6                       # puncak kaca OLED = titik tertinggi robot
RES_ROW = {-1: (53.3, 56.9, 60.5), 1: (53.3, 56.9)}                             # baris resistor kiri / kanan
IB_V17 = (-27.05, 19.05, 42.95, 79.05)      # rev A, hanya untuk angka pembanding v17

# rangka interface (3D print): pelat 2,5 mm di bawah tepi board + 4 kaki di lubang M3 PCB utama
FR_Z1 = IB_Z0
FR_Z0 = FR_Z1 - 2.5
RAIL_X0, RAIL_X1 = IB[1] + 0.4, IB[1] + 3.8
LEG_R, BOSS_R = 3.25, 2.7

PACK_L, PACK_W, PACK_H, PACK_M = 50.0, 30.0, 15.0, 46.0     # listing: Li-ion 14500 7,4 V 2S, 46 g
STRAP_W, STRAP_T = 16.0, 1.0

# pack: (y0, z0) = sisi belakang dan dasar pack
LAYOUT = {
    "v17": dict(nama="v17", pack=None),
    "ransel": dict(nama="v18", pack=(-41.5, CH_Z1)),
}
ORDER = ["v17", "ransel"]


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
    """trapesium v17 (sisi sejajar PCB utama, coakan roda); v18: ekor meruncing untuk pack 50 mm + bibir"""
    def sx(y):
        return min(NOSE_HW + (NOSE_Y - y) * K_SIDE, WO)
    front = [(WI, WELL, 1.5), (sx(WELL), WELL, 1.5), (NOSE_HW, NOSE_Y, 5)]
    wing = [(WO, -32.0, 3), (sx(-WELL), -WELL, 1.5), (WI, -WELL, 1.5)]
    rear = [(WO, -32.0, 4)] + wing[1:] if key == "v17" else [(30.0, -43.0, 4)] + wing
    return fillet_dense(rear + front)


SKID = {k: skid_poly(k) for k in ORDER}


# ------------------------------ kotak 3D + cek susunan ------------------------------
def pack_box(L):
    y0, z0 = L["pack"]
    return (-PACK_L / 2, PACK_L / 2, y0, y0 + PACK_W, z0, z0 + PACK_H)


def boxes(key):
    """(nama, x0, x1, y0, y1, z0, z1, jenis)"""
    L = LAYOUT[key]
    ib = IB_V17 if key == "v17" else IB
    b = []
    for s, sisi in ((-1, "kiri"), (1, "kanan")):
        x0, x1 = sorted((s * (WX - 34.1), s * (WX - 2.0)))
        b.append((f"Motor N20 + encoder {sisi}", x0, x1, -6.2, 6.2, CH_Z1, CH_Z1 + 10, "motor"))
        x0, x1 = sorted((s * WX, s * WO))
        b.append((f"Ban {sisi}", x0, x1, -R_W, R_W, 0, 2 * R_W, "wheel"))
    if L["pack"]:
        p = pack_box(L)
        b.append(("Pack Li-ion 2S", *p, "battery"))
        zlow = CH_Z0 - 0.45 - STRAP_T                # strap melingkari pack, lewat di bawah plat
        b.append(("Strap", -STRAP_W / 2, STRAP_W / 2, p[2] - 1.4, p[3] + 1.4, zlow, p[5] + 1.4, "strap"))
    else:
        b.append(("Holder 2x18650", -38, 38, -21, 21, 24, 44, "battery"))
        b.append(("Dudukan baterai (3D print)", -38, 38, -24, 24, 22, 24, "print"))
        b.append(("Charger 2S USB-C", -12.5, 12.5, -28, -12, CH_Z1, CH_Z1 + 5.5, "charger"))
    b.append(("PCB utama + komponen", -MB_XR, MB_XR, MB_Y0, MB_Y1, MB_Z0 - 2, ESP_TOP, "pcb"))
    b.append(("Board interface + OLED", ib[0], ib[1], ib[2], ib[3], IB_Z0 - 2, TOP_Z, "pcb"))
    b.append(("PCB sensor rev B", -47.5, 47.5, 80.0, SENS_Y1, 3.0, 6.4, "sensor"))
    b.append(("Ball caster", -5, 5, CASTER_Y - 5, CASTER_Y + 5, 0, CH_Z0, "caster"))
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
            if overlap(a, b) and {a[7], b[7]} not in ({"pcb"}, {"battery", "strap"}):
                prob.append(f"tabrakan: {a[0]} × {b[0]}")
    skid = SKID[key]
    if L["pack"]:                                    # pack duduk di plat: harus di dalam garis luarnya
        p = pack_box(L)
        if not all(in_poly(q, skid) for q in ((p[0], p[2]), (p[0], p[3]), (p[1], p[2]), (p[1], p[3]))):
            prob.append("pack keluar dari skid plate")
    for q in TRAP:                                   # PCB utama di dalam skid plate, jarak tepi >= 1,5 mm
        if not in_poly(q, skid) or edge_dist(q, skid) < 1.5:
            prob.append(f"PCB utama terlalu dekat tepi skid plate ({edge_dist(q, skid):.1f} mm)")
            break
    batt = next(b for b in bx if b[7] == "battery")
    rear = min(min(y for _, y in skid), -R_W)
    p, l, t = SENS_Y1 - rear, 2 * WO, TOP_Z
    for v, lim, n in ((p, LIMIT[0], "panjang"), (l, LIMIT[1], "lebar"), (t, LIMIT[2], "tinggi")):
        if v > lim:
            prob.append(f"{n} {v:.0f} mm melewati batas lomba {lim:.0f} mm")
    low = min(b[5] for b in bx if b[7] in ("strap", "battery"))
    return dict(prob=prob, p=p, l=l, t=t, batt_top=batt[6], low=min(low, CH_Z0))


def mass_model(key):
    """massa per bagian dari docs/perhitungan-motor.md bagian 4 (asumsi, belum ditimbang)"""
    L = LAYOUT[key]
    it = []                                          # (m gram, y, z)

    def add(m, y, z):
        it.append((m, y, z))
    if L["pack"]:
        p = pack_box(L)
        add(PACK_M + 4, (p[2] + p[3]) / 2, (p[4] + p[5]) / 2)       # pack + strap dan bibir penahan
        add(6, 52, 30)                                              # rangka interface (PLA ±4,5 cm3)
    else:
        add(92 + 12, 0, 34)                                         # 2 sel 18650 + holder
        add(13, 0, 20)                                              # dudukan baterai + tiang
        add(3, -20, CH_Z1 + 2.5)                                    # charger
        add(3, 0, 23)                                               # BMS di holder
    add(24, 0, R_W)                                                 # 2 motor + encoder
    add(12, 0, R_W)                                                 # 2 roda
    add(14, EY, DK_Z0)                                              # ESP32 DevKit + socket
    add(5, 46.0, MBT + 3)                                           # TB6612
    add(4, 70.5, MBT + 4)                                           # MP1584
    add(abs(area2(TRAP)) / 200 * 0.36, poly_cy(TRAP), MB_Z0 + 0.8)  # PCB utama FR4 1,6 mm
    add(10, 50, MBT + 4)                                            # konektor, saklar, buzzer, elko, dioda
    add(14, 58, IBT + 3)                                            # board interface + OLED + tombol
    add(10, 110, 5.6)                                               # PCB sensor + komponen
    add(8, CASTER_Y, 5)                                             # ball caster
    add(10, 55, 14)                                                 # baut, mur, spacer
    add(8, 45, 20)                                                  # kabel
    sk = SKID[key]
    add(abs(area2(sk)) / 200 * 0.2 * 1.24 + 12, poly_cy(sk), 11.5)  # skid plate PLA + dudukan motor
    M = sum(i[0] for i in it)
    ycm = sum(i[0] * i[1] for i in it) / M
    zcm = sum(i[0] * i[2] for i in it) / M
    share = ycm / CASTER_Y                                          # bagian berat di ball caster (diam)
    return dict(M=M, ycm=ycm, zcm=zcm, caster=share, a_slip=MU * G * (1 - share), a_lift=G * ycm / zcm)


RES = {k: {**check(k), **mass_model(k)} for k in ORDER}
for k in ORDER:
    if RES[k]["M"] > LIMIT[3]:
        RES[k]["prob"].append(f"perkiraan massa {RES[k]['M']:.0f} g melewati batas lomba {LIMIT[3]:.0f} g")


# ------------------------------ mesh ------------------------------
V16 = json.load(open(os.path.join(HERE, "..", "viewer", "model.json"), encoding="utf-8"))
MATS = dict(V16["mats"])
MATS.update({"skid": ["#aab3bd", 0.78, 0.0], "pack": ["#15161a", 0.38, 0.1], "strap": ["#f08a1c", 0.92, 0.0],
             "buckle": ["#2a2c31", 0.5, 0.2], "pack_end": ["#2c5fb8", 0.5, 0.0], "frame": ["#76828f", 0.8, 0.0]})
MESH = []


def emit(name, mat, group, pi, dbl=True):
    p, i = pi
    o = {"n": name, "m": mat, "g": group, "p": [round(v, 2) for v in p], "i": i}
    if dbl:
        o["d"] = 1
    MESH.append(o)


def reuse(names, group, dx=0.0, dy=0.0, dz=0.0, fx=None, pred=None, fz=None):
    """salin mesh v16 (nama persis atau awalan berakhiran *), digeser; fx/fz = pemetaan x/z sebelum digeser"""
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
            p[k + 2] = (fz(p[k + 2]) if fz else p[k + 2]) + dz
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


# grup = lapisan gambar urai: base (skid plate, motor, roda, baut M3), pack, sensor, main (PCB utama), frame (rangka
# interface), mur, iface (board interface), oled, kabel (disembunyikan saat diurai)

# ---------- base: motor, roda (ban dilebarkan 12 -> 18 mm ke luar), skid plate, ball caster ----------
reuse(["Gearbox N20", "Motor N20", "Tutup motor", "Encoder PCB", "Magnet encoder", "Konektor encoder", "As roda"], "base")
reuse(["Ban merah", "Velg"], "base", fx=lambda x: math.copysign(WX + (abs(x) - WX) * W_T / 12.0, x))
emit("Skid plate 3D print", "skid", "base", prism(SKID["ransel"], CH_Z0, CH_Z1))
for s in (-1, 1):                                    # klem motor: 2 pelana per motor, menyatu dengan skid plate
    for xa, xb in ((15.0, 26.0), (29.5, 36.5)):
        x0, x1 = sorted((s * xa, s * xb))
        emit("Klem motor", "skid", "base", merge(box(x0, x1, -8.2, -6.3, CH_Z1, 23.6), box(x0, x1, 6.3, 8.2, CH_Z1, 23.6),
                                                 box(x0, x1, -8.2, 8.2, 22.15, 23.6)))
for hx, hy in MB_HOLE:                               # boss 3 mm + baut kepala benam dari bawah, berdiri menembus semua lapisan
    emit("Boss M3 skid plate", "skid", "base", prism(circle(hx, hy, 3.5, 32), CH_Z1, MB_Z0))
    emit("Baut M3 x 30 kepala benam", "chrome", "base", merge(prism(circle(hx, hy, 1.5, 16), CH_Z0 + 0.2, CH_Z0 + 30.0),
                                                              prism(circle(hx, hy, 2.8, 24), CH_Z0 - 0.05, CH_Z0 + 0.2)))
    emit("Mur M3 rangka", "chrome", "mur", prism(circle(hx, hy, 3.1, 6), FR_Z1, FR_Z1 + 2.4))
emit("Ball caster rumah", "black_plastic", "base", prism(circle(0, CASTER_Y, 6.5, 32), 4.0, CH_Z0))
emit("Ball caster bola", "chrome", "base", sphere((0, CASTER_Y, 5.0), 5.0), dbl=False)

# ---------- pack: pack 2S, strap lewat celah skid plate, bibir penahan (bibir menyatu dengan skid plate) ----------
PX0, PX1, PY0, PY1, PZ0, PZ1 = pack_box(LAYOUT["ransel"])
PYC, PZC = (PY0 + PY1) / 2, (PZ0 + PZ1) / 2
emit("Pack Li-ion 14500 2S", "pack", "pack", prism(stadium(PY0, PY1, PZ0, PZ1), PX0 + 1.0, PX1 - 1.0, "x"))
for xa, xb in ((PX0, PX0 + 1.0), (PX1 - 1.0, PX1)):  # tutup ujung (barley paper)
    emit("Pack ujung", "pack_end", "pack", prism(stadium(PY0 + 0.6, PY1 - 0.6, PZ0 + 0.6, PZ1 - 0.6), xa, xb, "x"))
_zb, _r, _o = CH_Z0 - 0.45, PACK_H / 2, 0.35         # strap: belakang pack, atas, depan, kembali lewat bawah plat
_path = [(PY0 - _o, _zb)]
_path += [(PY0 + _r + (_r + _o) * math.cos(math.pi - math.pi / 2 * k / 10), PZC + (_r + _o) * math.sin(math.pi - math.pi / 2 * k / 10))
          for k in range(11)]
_path += [(PY1 - _r + (_r + _o) * math.cos(math.pi / 2 - math.pi / 2 * k / 10), PZC + (_r + _o) * math.sin(math.pi / 2 - math.pi / 2 * k / 10))
          for k in range(11)]
_path += [(PY1 + _o, _zb)]
emit("Strap velcro 16 mm", "strap", "pack", band(_path, -STRAP_W / 2, STRAP_W / 2, STRAP_T))
emit("Gesper strap", "buckle", "pack", box(-STRAP_W / 2 - 1.5, STRAP_W / 2 + 1.5, PYC + 4.0, PYC + 8.5,
                                           PZ1 + _o + STRAP_T - 0.2, PZ1 + _o + STRAP_T + 1.6))
_lips = [box(sx0, sx1, ya, yb, CH_Z1, CH_Z1 + 4.0) for sx0, sx1 in ((-23.0, -10.5), (10.5, 23.0))
         for ya, yb in ((PY0 - 1.6, PY0 - 0.2), (PY1 + 0.2, PY1 + 1.6))]
emit("Bibir penahan pack", "skid", "base", merge(*_lips, box(PX1 + 0.3, PX1 + 1.8, PY0 + 6.0, PY1 - 6.0, CH_Z1, CH_Z1 + 4.0)))
_py = PYC - 6.0                                      # kabel balancer -> steker XH 3 pin (untuk cas di luar robot)
emit("Steker balancer XH 3 pin", "jst_plug", "pack", box(-37.0, -30.0, _py - 3.0, _py + 3.0, CH_Z1, CH_Z1 + 5.7))
for k, mat in enumerate(("wire_blk", "wire_blu", "wire_red")):
    emit("Kabel balancer", mat, "pack", tube([(PX0, PYC - 3 + k * 1.2, PZC - 1), (-28.5, PYC - 3, PZC + 1),
                                              (-29.5, _py - 1.2 + k * 1.2, CH_Z1 + 6.5), (-31.0, _py - 1.2 + k * 1.2, CH_Z1 + 3.0)], 0.5, 6))

# ---------- sensor: PCB sensor rev B, 2 baut M3 dari bawah di H1/H2, spacer nilon, mur di atas hidung skid plate ----------
reuse(["PCB sensor", "Sensor QRE1113GR x12", "QRE1113GR *", "Resistor SMD sensor", "Silkscreen sensor*",
       "Pad lubang sensor", "IC mux *", "C 100 nF mux", "Header JST XH J1", "Steker JST XH J1", "Mur M3"], "sensor")
reuse(["Spacer nilon 4 mm"], "sensor", fz=lambda z: 6.4 + (z - 6.4) * (CH_Z0 - 6.4) / 4.0)       # 4 -> 3,6 mm
for hx, hy in SENS_H:
    emit("Baut M3 x 10 sensor", "chrome", "sensor", merge(prism(circle(hx, hy, 2.8, 24), 3.0, 4.8),
                                                          prism(circle(hx, hy, 1.5, 16), 4.8, 14.8)))

# ---------- main: PCB utama rev B + komponen (posisi KiCad), ESP32 di socket + plastik header ----------
emit("PCB utama rev B", "pcb", "main", prism(TRAP, MB_Z0, MBT))
for ref, (x0, x1, y0, y1) in JST.items():
    emit(f"Header JST XH {ref} utama", "jst", "main", box(x0 + 0.45, x1 - 0.45, y0 + 0.5, y1 - 0.5, MBT, MBT + 7.0))
    emit(f"Steker JST XH {ref} utama", "jst_plug", "main", box(x0 + 1.4, x1 - 1.4, y0 + 1.4, y1 - 1.4, MBT + 2.0, MBT + 9.8))
for y in (26.2, 29.6):
    emit("Resistor R1/R2", "resistor", "main", prism(circle(y, MBT + 1.3, 1.2, 12), -14.6, -8.2, "x"))
reuse(["ESP32 socket"], "main", dy=7.5, dz=MBT - 12.0)
reuse(["ESP32 *"], "main", dy=7.5, dz=MBT - 12.0 + HDR, pred=lambda o: o["n"] != "ESP32 socket")
for y0, y1 in ((32.2, 34.74), (57.56, 60.1)):
    emit("ESP32 plastik header", "black_plastic", "main", box(-19.1, 19.1, y0, y1, MBT + SOCK, DK_Z0))
reuse(["TB6612 PCB", "TB6612 chip"], "main", dx=-48.9, dy=10.9, dz=-1.4)
reuse(["Buzzer"], "main", dx=-13.5, dy=16.0, dz=MBT - 12.0)
reuse(["Saklar", "Saklar tuas"], "main", dx=10.3, dy=8.2, dz=MBT - 12.0)
reuse(["Elko C1 *"], "main", dx=44.95, dy=-11.9, dz=MBT - 12.0)
reuse(["MP1584 *"], "main", dx=-33.9, dy=91.5, dz=MBT - 12.0)
reuse(["Dioda 1N5819*"], "main", dx=-0.9, dy=92.0, dz=MBT - 12.0)
emit("Socket J6", "black_plastic", "main", box(J6[0] + 0.3, J6[1] - 0.3, J6[2] + 0.5, J6[3] - 0.5, MBT, MBT + SOCK))

# ---------- frame: rangka interface (3D print). Pelat di bawah tepi board, 4 kaki di lubang M3 PCB utama ----------
FRAME = [box(-RAIL_X1, RAIL_X1, IB[2] - 2.0, IB[2] + 2.5, FR_Z0, FR_Z1)]         # balok belakang: tumpuan baris tombol
for s in (-1, 1):
    def sbox(xa, xb, *r):
        x0, x1 = sorted((s * xa, s * xb))
        return box(x0, x1, *r)
    FRAME.append(sbox(RAIL_X0, RAIL_X1, IB[2] - 2.0, IB[3], FR_Z0, FR_Z1))        # rel samping, di luar tepi board
    for hx, hy in IB_HOLE[1::2]:                                                  # tab + boss baut M2
        FRAME.append(sbox(hx - BOSS_R, RAIL_X0, hy - BOSS_R, min(hy + BOSS_R, IB[3]), FR_Z0, FR_Z1))
        FRAME.append(prism(circle(s * hx, hy, BOSS_R, 24), FR_Z0 - (2.4 if hy < 70 else 5.6), FR_Z0))
    FRAME.append(sbox(RAIL_X1, 32.5, 53.0, 59.0, FR_Z0, FR_Z1))                   # lengan ke kaki depan
    FRAME.append(prism([(s * RAIL_X1, 32.0), (s * 37.0, 25.9), (s * 41.6, 30.6), (s * RAIL_X1, 37.0)], FR_Z0, FR_Z1))
for hx, hy in MB_HOLE:
    FRAME.append(prism(circle(hx, hy, LEG_R, 28), MBT, FR_Z1))
for _f in FRAME:
    emit("Rangka interface (3D print)", "frame", "frame", _f)

# ---------- iface: board interface rev B, tombol sebaris, tangga resistor, socket OLED, spacer, header ke J6 ----------
emit("Board interface rev B", "pcb", "iface", prism(rrect(IB[0], IB[1], IB[2], IB[3], 2.0), IB_Z0, IBT))
for bx_, _ in BTN:
    reuse(["Tombol", "Tombol tutup"], "iface", dx=bx_ + 22.0, dy=BTN_Y - 66.0, dz=IBT - 12.0,
          pred=lambda o: min(o["p"][0::3]) < 0)
for s, rows in RES_ROW.items():
    for y in rows:
        x0, x1 = sorted((s * 4.9, s * 10.3))
        emit("Resistor tangga tombol", "resistor", "iface", prism(circle(y, IBT + 1.3, 1.2, 12), x0, x1, "x"))
emit("C1 100 nF", "cap_smd", "iface", box(5.0, 9.0, 59.5, 61.5, IBT, IBT + 4.0))
reuse(["OLED socket"], "iface", dy=OLED_Y - 67.4, dz=IBT - 12.0)
for hx, hy in OLED_HOLE:
    emit("Spacer M2 OLED", "nylon", "iface", prism(circle(hx, hy, 1.9, 6), IBT, OLED_Z0))
for hx, hy in IB_HOLE:
    emit("Baut M2 x 6 ke rangka", "chrome", "iface", prism(circle(hx, hy, 1.9, 20), IBT, IBT + 1.3))
emit("Header susun 1x6", "black_plastic", "iface", box(J6[0] + 0.3, J6[1] - 0.3, J6[2] + 0.5, J6[3] - 0.5, MBT + SOCK, MBT + 2 * SOCK))
emit("Header J1 interface", "jst_plug", "iface", box(J6[0] + 0.5, J6[1] - 0.5, J6[2] + 0.6, J6[3] - 0.6, MBT + 2 * SOCK, IB_Z0))

# ---------- oled: modul OLED + plastik header, baut M2 di 2 lubang atas (lubang bawah terlalu dekat kaca) ----------
reuse(["OLED PCB", "OLED kaca", "OLED flex", "OLED tampilan", "OLED lubang"], "oled", dy=OLED_Y - 67.4, dz=OLED_Z0 - 20.5)
emit("OLED plastik header", "black_plastic", "oled", box(-5.08, 5.08, OLED_Y + 11.4, OLED_Y + 13.94, IBT + SOCK, OLED_Z0))
for hx, hy in OLED_HOLE[2:]:
    emit("Baut M2 OLED", "chrome", "oled", prism(circle(hx, hy, 1.8, 20), OLED_Z0 + 1.2, OLED_Z0 + 2.3))

# ---------- kabel ----------
WIRE = ["wire_red", "wire_yel", "wire_blk"] + ["wire_blu"] * 5
for k in range(8):                                   # kabel J5 -> J1 PCB sensor (urutan pin sama)
    xa, xb = 13.0 - 2.5 * k, 8.75 - 2.5 * k
    emit(f"Kabel sensor pin {k + 1}", WIRE[k], "kabel",
         tube([(xa, 77.8, MBT + 9.6), (xa, 78.6, MBT + 14.5), ((xa + xb) / 2, 89.0, MBT + 13.5), (xb, 99.6, 23.5),
               (xb, 100.0, 17.2)], 0.55, 6))
for o_, mat, xj in ((0.9, "wire_red", -1.25), (-0.9, "wire_blk", 1.25)):          # kabel pack -> steker XH di J1
    mid = [(-30.0, PYC + 2, PZC + 2), (-31.0, -9.0, 25.6), (-27.0, 6.0, 26.6), (-12.0, 20.0, 29.6)]
    pts = [(PX0, PYC + 2 + o_, PZC)] + [(a + o_, b, c + o_) for a, b, c in mid] + [(xj, 27.6, 31.0), (xj, 28.1, MBT + 9.6)]
    emit("Kabel pack", mat, "kabel", tube(pts, 0.8))
for s in (-1, 1):                                    # kabel motor + encoder (6 kawat, digambar satu selubung) ke J2/J3
    xj = s * 25.65
    emit("Kabel motor + encoder", "ribbon", "kabel",
         tube([(s * 7.2, 0, 19.0), (s * 8.0, 4.0, 24.5), (s * 16.0, 14.0, 25.5), (xj, 25.1, 30.5), (xj, 28.1, MBT + 9.6)], 1.4))

json.dump({"mats": MATS, "meshes": MESH}, open(os.path.join(HERE, "konsep-v18-model.json"), "w", encoding="utf-8"),
          separators=(",", ":"))


# ------------------------------ cek tumpukan PCB (kotak pembatas tiap mesh) ------------------------------
def bbox(o):
    p = o["p"]
    return (min(p[0::3]), max(p[0::3]), min(p[1::3]), max(p[1::3]), min(p[2::3]), max(p[2::3]))


def hit(a, b, eps=0.05):
    return all(min(a[2 * k + 1], b[2 * k + 1]) - max(a[2 * k], b[2 * k]) > eps for k in range(3))


BB = [(o["n"], o["g"], bbox(o)) for o in MESH]
# kaki solder di sisi bawah board interface (2 mm) dan kepala baut spacer OLED: tidak digambar, tetapi ikut dicek
_pads = [(bx_ + sx, BTN_Y + sy) for bx_, _ in BTN for sx in (-2.25, 2.25) for sy in (-3.25, 3.25)]
_pads += [(s * x, y) for s, rows in RES_ROW.items() for y in rows for x in (3.81, 11.43)]
_pads += [(4.5, 60.5), (9.5, 60.5)] + [(-3.81 + 2.54 * k, 73.65) for k in range(4)] + OLED_HOLE
JOINT = [("kaki solder / baut bawah board interface", "joint", (x - 1.2, x + 1.2, y - 1.2, y + 1.2, IB_Z0 - 2.0, IB_Z0))
         for x, y in _pads]
KEEP = [("jalur steker USB ESP32", "keep", (-48.0, -26.5, EY - 4.5, EY + 4.5, DK_Z0 - 0.5, DK_Z0 + 6.5)),
        ("jari ke tuas saklar SW1", "keep", (-52.0, -43.75, 33.0, 44.0, MBT, MBT + 8.0))]


def stack_check():
    prob = set()

    def pairs(ga, gb):
        A = [b for b in BB + JOINT + KEEP if b[1] in ga]
        Bs = [b for b in BB + JOINT + KEEP if b[1] in gb]
        for a in A:
            for b in Bs:
                if hit(a[2], b[2]):
                    prob.add(f"tabrakan: {a[0]} × {b[0]}")
    pairs({"frame"}, {"main", "kabel", "keep", "joint", "oled", "pack", "sensor"})
    pairs({"iface", "joint"}, {"main", "kabel", "keep"})
    pairs({"oled"}, {"iface"})
    pairs({"mur"}, {"main", "iface", "kabel"})
    for hx, hy in IB_HOLE + OLED_HOLE:               # lubang M2 di dalam papan, tepi >= 1,2 mm
        if min(hx - IB[0], IB[1] - hx, hy - IB[2], IB[3] - hy) - 1.1 < 1.2:
            prob.add(f"lubang M2 ({hx}; {hy}) terlalu dekat tepi board interface")
    if IB[1] - 0.5 > 19.25:                          # tembaga (pour berhenti 0,5 mm dari tepi) tidak di atas antena ESP32
        prob.add("tembaga board interface masuk zona antena ESP32")
    return sorted(prob)


RES["ransel"]["prob"] += stack_check()

# render KiCad board interface (tampak atas) dikecilkan untuk halaman
try:
    from PIL import Image
    _im = Image.open(os.path.join(HERE, "..", "..", "hardware", "board-interface", "render-atas.png")).convert("RGBA")
    _im = Image.alpha_composite(Image.new("RGBA", _im.size, "white"), _im).convert("RGB")      # latar render transparan
    _im = _im.crop((60, 60, _im.width - 60, _im.height - 60))
    _im = _im.resize((560, round(560 * _im.height / _im.width)), Image.LANCZOS)
    _im.save(os.path.join(HERE, "interface-rev-b.png"), optimize=True)
    IMG_WH = _im.size
except ImportError:                                  # tanpa Pillow: pakai file yang sudah ada
    IMG_WH = (560, 648)


# ------------------------------ halaman ------------------------------
def fmt(v, n=1):
    return f"{v:.{n}f}".replace(".", ",")


B, A = RES["v17"], RES["ransel"]
KV = [["Ukuran p × l × t", f"{A['p']:.0f} × {A['l']:.0f} × {A['t']:.0f} mm"],
      ["Perkiraan massa", f"±{A['M']:.0f} g"],
      ["Puncak baterai", f"{A['batt_top']:.0f} mm"],
      ["Berat di roda penggerak", f"{(1 - A['caster']) * 100:.0f}%"],
      ["Board interface", f"{IB[1] - IB[0]:.0f} × {IB[3] - IB[2]:.0f} mm"],
      ["Celah lantai terendah", f"{fmt(A['low'])} mm"]]
EXPL = {"pack": [0, -34, 0], "sensor": [0, 36, 0], "main": [0, 0, 16], "frame": [0, 0, 42], "mur": [0, 0, 52],
        "iface": [0, 0, 66], "oled": [0, 0, 86]}
LABELS = [
    dict(g="oled", p=[13.65, OLED_Y, OLED_Z0 + 1.2], t="OLED: socket 4 pin + 4 spacer M2"),
    dict(g="iface", p=[19.5, 52.0, IBT], t="Board interface rev B: 4 baut M2 ke rangka"),
    dict(g="mur", p=[-38.5, 29.0, FR_Z1 + 1.2], t="4 mur M3"),
    dict(g="frame", p=[32.5, 56.0, FR_Z1 - 1.2], t="Rangka interface (3D print)"),
    dict(g="main", p=[-42.0, 27.0, MBT], t="PCB utama rev B"),
    dict(g="base", p=[32.5, 56.0, 21.0], t="4 baut M3 × 30 dari bawah skid plate"),
    dict(g="sensor", p=[40.0, 112.0, 6.4], t="PCB sensor: 2 baut M3 + spacer"),
    dict(g="pack", p=[-25.0, -26.0, 24.0], t="Pack 2S + strap velcro"),
]
META = dict(kv=KV, expl=EXPL, labels=LABELS, pack=[PX0, PX1, PY0, PY1, PZ0, PZ1], ibt=IBT, ib=list(IB),
            btn=[[x, t] for x, t in BTN])

FIX = [
    ["PCB sensor rev B", "hidung skid plate",
     "2 baut M3 × 10 dari bawah di lubang H1/H2, spacer nilon ±3,5 mm, mur di atas skid plate"],
    ["PCB utama rev B", "skid plate",
     "4 baut M3 × 30 kepala benam dari bawah skid plate, lewat boss 3 mm yang menyatu dengan skid plate"],
    ["Rangka interface (3D print, baru)", "di atas PCB utama",
     "4 kakinya masuk ke 4 baut M3 yang sama, dikunci 4 mur di atas kaki. Sekaligus menjepit PCB utama"],
    ["Board interface rev B", "rangka interface",
     "4 baut M2 × 6 ke boss rangka; tepi belakang (di bawah baris tombol) bertumpu di balok rangka; header 1×6 ke J6"],
    ["Modul OLED 0,96 inci", "board interface",
     "socket 4 pin + 4 spacer M2 ±11 mm; baut M2 di 2 lubang atas (2 lubang bawah cukup jadi ganjal, kepala baut "
     "di situ mepet kaca)"],
    ["ESP32 DevKit", "PCB utama", "socket 2 × 15 pin (tidak berubah)"],
    ["Pack Li-ion 2S", "ekor skid plate", "strap velcro 16 mm lewat celah skid plate + bibir 4 mm di empat sudut"],
]
fix_rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in FIX)
checks = "".join(f"<li>{p}</li>" for p in A["prob"]) or "<li>0 masalah</li>"

PAGE = r"""<title>Konsep LFM v18</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* lembar konsep (sama dengan konsep v17): kertas hijau-abu, tinta gelap; panggung 3D di atas, angka di bawahnya */
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
main { max-width: 1080px; margin: 0 auto; display: grid; grid-template-columns: minmax(0, 1fr); gap: 28px; }
h1 { font-size: 1.7rem; font-weight: 600; margin: 0; text-wrap: balance; letter-spacing: -0.01em; }
h2 { font-size: 0.78rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.09em; color: var(--muted); margin: 0 0 10px; }
p { margin: 0; max-width: 68ch; }
.lead { color: var(--muted); }
.viewer { display: grid; gap: 10px; min-width: 0; }
#stage { position: relative; background: var(--stage); border: 1px solid var(--line); border-radius: 6px; overflow: hidden;
  aspect-ratio: 16 / 9; max-height: 640px; width: 100%; }
@media (max-width: 720px) { #stage { aspect-ratio: 4 / 5; } }
#stage canvas { display: block; width: 100%; height: 100%; outline: none; touch-action: none; }
.bar { position: absolute; top: 10px; left: 10px; right: 10px; display: flex; flex-wrap: wrap; gap: 8px;
  justify-content: space-between; pointer-events: none; }
.views, .urai { display: flex; gap: 2px; background: var(--paper); border: 1px solid var(--line); border-radius: 6px;
  padding: 3px; pointer-events: auto; }
.bar button { font: 500 0.8rem var(--display); color: var(--ink); background: transparent; border: 0; border-radius: 4px;
  padding: 6px 9px; cursor: pointer; }
.bar button[aria-pressed="true"] { background: var(--ink); color: var(--paper); }
.urai button[aria-pressed="true"] { background: var(--pick); color: var(--on-pick); }
.bar button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.hint { position: absolute; left: 10px; bottom: 10px; font-size: 0.75rem; color: var(--muted); background: var(--paper);
  border-radius: 4px; padding: 3px 8px; pointer-events: none; }
#labels { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.lbl { position: absolute; transform: translate(14px, -50%); font-size: 0.74rem; line-height: 1.3; white-space: nowrap;
  color: var(--ink); background: var(--paper); border: 1px solid var(--line); border-radius: 4px; padding: 2px 7px;
  opacity: 0; transition: opacity 0.2s; }
.lbl::before { content: ""; position: absolute; left: -15px; top: 50%; width: 15px; border-top: 1px solid var(--accent); }
.lbl::after { content: ""; position: absolute; left: -18px; top: calc(50% - 3px); width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent); }
.lbl.l { transform: translate(calc(-100% - 14px), -50%); }
.lbl.l::before { left: auto; right: -15px; }
.lbl.l::after { left: auto; right: -18px; }
@media (max-width: 720px) { .lbl { font-size: 0.66rem; white-space: normal; width: max-content; max-width: 118px; } }
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
table { border-collapse: collapse; width: 100%; font-size: 0.92rem; min-width: 640px; }
.tablewrap { overflow-x: auto; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-weight: 500; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; }
td:first-child { font-weight: 500; white-space: nowrap; }
td:nth-child(2) { color: var(--muted); white-space: nowrap; }
ol, ul { margin: 0; padding-left: 1.2em; display: grid; gap: 6px; max-width: 72ch; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }
@media (max-width: 720px) { .cols { grid-template-columns: 1fr; } }
.cols > section { min-width: 0; }
.board { display: grid; grid-template-columns: minmax(0, 300px) minmax(0, 1fr); gap: 24px; align-items: start; }
@media (max-width: 720px) { .board { grid-template-columns: 1fr; } }
.board figure { margin: 0; background: #ffffff; border: 1px solid var(--line); border-radius: 6px; padding: 8px; }
.board img { display: block; width: 100%; height: auto; }
.board figcaption { font-size: 0.78rem; color: #5d6b63; padding-top: 6px; }
.note { font-size: 0.85rem; color: var(--muted); }
</style>
<script type="importmap">{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/" } }</script>
<main>
  <header style="display:grid;gap:10px">
    <h1>Konsep LFM v18: susunan A, semua PCB terkunci, tombol sebaris</h1>
    <p class="lead">Susunan A · Ransel yang kamu pilih: pack Li-ion 2S rebah di belakang motor dan diikat strap. Sekarang
    tiap PCB punya pengikatnya sendiri, dan board interface digambar ulang (rev B) supaya simetris: OLED di tengah, lima
    tombol sebaris di belakangnya. PCB utama dan PCB sensor tidak diubah. Tekan <b>Urai</b> untuk melihat cara pasangnya.</p>
  </header>

  <section class="viewer">
    <div id="stage" aria-label="Model 3D robot, bisa diputar dengan mouse atau jari">
      <div id="loading">memuat model 3D…</div>
      <div id="labels" aria-hidden="true"></div>
      <div class="bar">
        <div class="urai"><button type="button" id="urai" aria-pressed="false">Urai</button></div>
        <div class="views" role="group" aria-label="Sudut pandang">
          <button type="button" data-view="rear" aria-pressed="true">Belakang</button>
          <button type="button" data-view="front" aria-pressed="false">Depan</button>
          <button type="button" data-view="side" aria-pressed="false">Samping</button>
          <button type="button" data-view="top" aria-pressed="false">Atas</button>
        </div>
      </div>
      <div class="hint">seret untuk memutar · scroll atau cubit untuk zoom · garis hitam = lintasan 20 mm</div>
    </div>
    <div class="info">
      <div><h3>v18 · pack di belakang motor</h3><p>__INFO__</p></div>
      <dl class="kv">__KV__</dl>
    </div>
  </section>

  <section>
    <h2>Board interface rev B: simetris</h2>
    <div class="board">
      <figure><img src="interface-rev-b.png" width="__IW__" height="__IH__" alt="Render KiCad board interface rev B tampak atas: lima tombol sebaris di tepi belakang, tangga resistor dan socket OLED di tengah, delapan lubang M2">
        <figcaption>Render KiCad tanpa modul OLED. Bawah gambar = belakang robot.</figcaption></figure>
      <ul>__BOARD__</ul>
    </div>
  </section>

  <section>
    <h2>Cara tiap PCB dipasang</h2>
    <div class="tablewrap"><table><thead><tr><th>Bagian</th><th>Dipasang ke</th><th>Pengikat</th></tr></thead>
      <tbody>__FIX__</tbody></table></div>
  </section>

  <div class="cols">
    <section>
      <h2>Perlu diukur atau diputuskan</h2>
      <ol>__TODO__</ol>
    </section>
    <section>
      <h2>Soal pack-nya (belum berubah)</h2>
      <ul>__PACK__</ul>
    </section>
  </div>

  <section>
    <h2>Hasil cek otomatis</h2>
    <ul>__CHECKS__</ul>
    <p class="note" style="margin-top:10px">Yang dicek dengan kotak pembatas tiap bagian: rangka interface terhadap semua komponen
    PCB utama, kabel, jalur steker USB ESP32, dan akses tuas SW1; kaki solder di bawah board interface terhadap kaleng modul ESP32
    dan rangka; OLED terhadap tombol; pack di dalam skid plate; batas ukuran dan massa lomba. Massa dihitung dari perkiraan
    tiap bagian (<code>docs/perhitungan-motor.md</code> bagian 4), belum ditimbang.</p>
  </section>
</main>

<script type="module">
const META = __META__;
const $ = (s) => document.querySelector(s);
const q = new URLSearchParams(location.search);

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
  controls.minDistance = 120; controls.maxDistance = 1300;

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
  Object.assign(key.shadow.camera, { left: -170, right: 170, top: 210, bottom: -150, near: 50, far: 1200 });
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
  // teks: label pack (di kanan strap) dan nama tombol di tepi belakang board interface (seperti silkscreen)
  function textPlane(w, h, px, draw) {
    const cv = document.createElement('canvas'); cv.width = Math.round(w * px); cv.height = Math.round(h * px);
    const cx = cv.getContext('2d'); cx.fillStyle = '#f2f2ee'; cx.textAlign = 'center'; cx.textBaseline = 'middle';
    draw(cx, px);
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
    return new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, transparent: true }));
  }
  const p = META.pack;
  const packLabel = textPlane(13.5, 9, 28, (cx, px) => {
    cx.font = `600 ${2.7 * px}px "IBM Plex Sans", sans-serif`; cx.fillText('Li-ion 2S', 6.75 * px, 3.1 * px);
    cx.font = `500 ${2.3 * px}px "IBM Plex Sans", sans-serif`; cx.fillText('7,4 V', 6.75 * px, 6.5 * px);
  });
  packLabel.position.set(16.2, (p[2] + p[3]) / 2, p[5] + 0.06); group('pack').add(packLabel);
  const ib = META.ib, silk = textPlane(ib[1] - ib[0], 2.2, 40, (cx, px) => {
    cx.font = `600 ${1.15 * px}px "IBM Plex Sans", sans-serif`;
    for (const [x, t] of META.btn) cx.fillText(t, (x - ib[0]) * px, 1.1 * px);
  });
  silk.position.set((ib[0] + ib[1]) / 2, ib[2] + 1.6, META.ibt + 0.05); group('iface').add(silk);

  const VIEWS = {
    rear:  { pos: [125, -205, 125], tgt: [0, 32, 16] },
    front: { pos: [-150, 255, 140], tgt: [0, 48, 16] },
    side:  { pos: [-330, 45, 30],   tgt: [0, 45, 22] },
    top:   { pos: [0, 44.9, 360],   tgt: [0, 45, 0] },
  };
  // gambar urai: tiap lapisan bergeser sepanjang vektornya, kabel disembunyikan, kamera mundur
  let urai = q.get('urai') === '1', t = urai ? 1 : 0;
  function zoomUrai(on) {
    const off = camera.position.clone().sub(controls.target).multiplyScalar(on ? 1.55 : 1 / 1.55);
    controls.target.z += on ? 36 : -36;
    camera.position.copy(controls.target).add(off);
    controls.update();
  }
  function setView(v) {
    const s = VIEWS[v]; if (!s) return;
    camera.position.set(...s.pos); controls.target.set(...s.tgt); controls.update();
    if (urai) zoomUrai(true);
    document.querySelectorAll('[data-view]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === v)));
  }
  document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => setView(b.dataset.view)));
  const btnUrai = $('#urai');
  btnUrai.setAttribute('aria-pressed', String(urai));
  btnUrai.addEventListener('click', () => {
    urai = !urai; btnUrai.setAttribute('aria-pressed', String(urai)); zoomUrai(urai);
  });
  setView(q.get('view') || 'rear');

  const labelBox = $('#labels');
  const labels = META.labels.map(l => {
    const el = document.createElement('div'); el.className = 'lbl'; el.textContent = l.t; labelBox.append(el);
    return { ...l, el };
  });
  const v3 = new THREE.Vector3(), c3 = new THREE.Vector3();
  function layout() {
    for (const [g, e] of Object.entries(META.expl)) group(g).position.set(e[0] * t, e[1] * t, e[2] * t);
    group('kabel').visible = t < 0.02;
    const w = stage.clientWidth, h = stage.clientHeight;
    c3.copy(controls.target).project(camera);
    for (const l of labels) {
      const e = META.expl[l.g] || [0, 0, 0];
      v3.set(l.p[0] + e[0] * t, l.p[1] + e[1] * t, l.p[2] + e[2] * t).project(camera);
      l.el.style.opacity = t > 0.7 && Math.abs(v3.x) < 1 && Math.abs(v3.y) < 1 ? 1 : 0;
      l.el.style.left = ((v3.x + 1) / 2 * w) + 'px'; l.el.style.top = ((1 - v3.y) / 2 * h) + 'px';
      l.el.classList.toggle('l', v3.x < c3.x);
    }
  }

  function resize() {
    const w = stage.clientWidth, h = stage.clientHeight;
    renderer.setSize(w, h, false); camera.aspect = w / h;
    // panggung potret (ponsel): sudut pandang mendatar dijaga sama dengan 16:9 supaya robot tidak terpotong
    camera.fov = w / h >= 16 / 9 ? 30 : 2 * THREE.MathUtils.radToDeg(Math.atan(Math.tan(Math.PI / 12) * (16 / 9) / (w / h)));
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(stage); resize();
  $('#loading').remove();
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  renderer.setAnimationLoop(() => {
    const goal = urai ? 1 : 0;
    t = still || Math.abs(goal - t) < 0.002 ? goal : t + (goal - t) * 0.14;
    controls.update(); layout(); renderer.render(scene, camera);
  });
  window.modelReady = true;
} catch (e) {
  $('#loading').textContent = 'Model 3D tidak bisa dimuat di perangkat ini (' + e.message + '). Angka di bawah tetap berlaku.';
}
</script>
"""

INFO = (f"Pack rebah melintang tepat di belakang motor, puncaknya {A['batt_top']:.0f} mm (dulu {B['batt_top']:.0f} mm di atas "
        f"motor). Perkiraan massa turun dari ±{B['M']:.0f} g ke ±{A['M']:.0f} g, panjang {B['p']:.0f} → {A['p']:.0f} mm, lebar tetap "
        f"{A['l']:.0f} mm. Titik tertinggi adalah kaca OLED, {A['t']:.0f} mm dari lantai.")
BOARD = [
    f"<b>{IB[1] - IB[0]:.0f} × {IB[3] - IB[2]:.0f} mm, simetris terhadap garis tengah robot.</b> Rev A 46 × 36 mm dengan dua tombol "
    "di kiri dan tiga di kanan OLED.",
    "<b>Lima tombol sebaris di belakang OLED</b>, jarak 7,62 mm: KEMBALI, ATAS, OK, BAWAH, LANJUT. OK tepat di tengah. Dilihat "
    "dari belakang robot, tombol ada di bawah layar.",
    "<b>Skematik tidak berubah</b> (tangga resistor ke GPIO34 yang sama), jadi firmware dan PCB utama tidak ikut berubah. "
    "Header J1 tetap tepat di atas J6 PCB utama.",
    "<b>8 lubang M2:</b> 4 ke rangka interface, 4 untuk spacer modul OLED.",
    "<b>Hasil KiCad:</b> DRC 0 error, 0 warning, 0 unconnected, cocok dengan skematik. Dua layer tanpa via, GND pour dua sisi. "
    "Tembaga tidak masuk zona antena ESP32.",
]
TODO = [
    "<b>Ukur modul OLED sebelum board interface dicetak.</b> Empat lubang spacer memakai ukuran umum modul 0,96 inci (jarak "
    "lubang 23,5 × 23,8 mm, deret pin 0,85 mm di atas lubang atas). Modul tiap penjual bisa beda sampai 1 mm.",
    f"<b>Tinggi ESP32 saya koreksi.</b> Model lama lupa plastik header pin (2,54 mm) di antara socket dan ESP32, jadi puncak "
    f"ESP32 sebenarnya {fmt(ESP_TOP)} mm, bukan 29,8 mm. Karena itu board interface naik dari 33 ke {fmt(IB_Z0)} mm supaya kaki "
    "solder tombol tidak menyentuh kaleng modul ESP32. Tolong ukur tinggi ESP32 di socket begitu barangnya ada.",
    f"<b>Header J6 → board interface:</b> jaraknya {fmt(IB_Z0 - MBT)} mm. Di model saya pakai socket 8,5 mm + header susun "
    "(stackable) 1×6 + header pin biasa. Pilihan lain: satu header pin panjang ±19 mm.",
    "<b>Cas:</b> di model, pack dicas di luar robot lewat kabel balancer. Kalau tetap mau cas USB-C di robot, modul charger dan "
    "BMS perlu tempat lagi.",
    "<b>Harga pack dan charger balance</b>, supaya RAB bisa dihitung ulang (yang keluar Rp137.990).",
    "<b>Label 5.000 mAh</b> terhadap batas 4.000 mAh di guidebook: perlu jawaban panitia sebelum pack dibeli.",
]
PACKNOTE = [
    "<b>Kapasitas 5.000 mAh di listing tidak mungkin benar.</b> Dua sel 14500 seberat 46 g realistisnya 600–1.000 mAh, "
    "kira-kira 1–1,5 jam jalan. Cukup untuk match 5 menit, tetapi jangan menulis 5.000 mAh di laporan.",
    "<b>Pilih varian konektor XH 2 pin</b> supaya langsung masuk J1. Sebelum colok pertama, ukur polaritasnya dengan multimeter: "
    "pin 1 J1 = BAT+, pin 2 = GND, dan tidak ada proteksi polaritas terbalik.",
    "<b>Proteksi:</b> tanyakan ke penjual apakah pack punya papan proteksi. Kalau tidak, batas bawah tegangan dijaga firmware "
    "lewat VBAT_SENSE (GPIO39).",
    "<b>Panjang kabel pack:</b> butuh ±8 cm sampai J1.",
]
html = (PAGE.replace("__INFO__", INFO)
        .replace("__KV__", "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in KV))
        .replace("__IW__", str(IMG_WH[0])).replace("__IH__", str(IMG_WH[1]))
        .replace("__BOARD__", "".join(f"<li>{s}</li>" for s in BOARD)).replace("__FIX__", fix_rows)
        .replace("__TODO__", "".join(f"<li>{s}</li>" for s in TODO))
        .replace("__PACK__", "".join(f"<li>{s}</li>" for s in PACKNOTE)).replace("__CHECKS__", checks)
        .replace("__META__", json.dumps(META, ensure_ascii=False)))
out = os.path.join(HERE, "konsep-v18.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
for k in ORDER:
    r = RES[k]
    print(f"{LAYOUT[k]['nama']:4s} {r['p']:.1f} x {r['l']:.0f} x {r['t']:.1f} mm  baterai z<={r['batt_top']:.1f}  M {r['M']:.0f} g  "
          f"ycm {r['ycm']:.1f}  zcm {r['zcm']:.1f}  caster {r['caster'] * 100:.0f}%  a_selip {r['a_slip']:.1f}  "
          f"a_angkat {r['a_lift']:.1f}  celah lantai {r['low']:.1f}")
    for p in r["prob"]:
        print("   -", p)
print(f"ESP32 puncak {ESP_TOP:.2f}, board interface z {IB_Z0:.2f}..{IBT:.2f}, rangka z {FR_Z0:.2f}..{FR_Z1:.2f}, puncak {TOP_Z:.2f}")
print(f"mesh {len(MESH)}, json {os.path.getsize(os.path.join(HERE, 'konsep-v18-model.json')) / 1e6:.2f} MB, tulis {out}")
