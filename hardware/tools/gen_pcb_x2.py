"""Tata letak awal 4 PCB LFM X2 rev B (gaya Ichibot Ultimate 5 Max, 15/11/2026): outline, lubang, semua footprint +
net. TANPA jalur dan tanpa pour: jalur digambar user sendiri di KiCad.

Dijalankan dengan python KiCad (modul pcbnew), bukan py biasa, dari folder repo:
  KPY="C:/Program Files/KiCad/10.0/bin/python.exe"
  "$KPY" hardware/tools/gen_pcb_x2.py tata [papan ...] [--paksa]   <papan>/lfm-x2-<papan>.kicad_pcb dari skematiknya
  "$KPY" hardware/tools/gen_pcb_x2.py pour papan                    sesudah routing: GND pour F.Cu + B.Cu (jarak 0,5 mm)
  "$KPY" hardware/tools/gen_pcb_x2.py peta [papan ...]               peta rakit PDF (lapisan Fab) tiap sisi

`tata` MENIMPA papan, jadi menolak jalan kalau papan sudah berisi jalur (kecuali --paksa). Netlist diekspor sendiri dari
skematik. Path footprint = UUID simbol, jadi F8 (Update PCB from Schematic) tidak membuat ulang footprint.

Koordinat robot (mm): x ke kanan, y maju, (0, 0) = tengah poros roda; KiCad X = 200 + x, Y = 180,55 - y (sama dengan
proyek PCB lain di repo ini), jadi keempat papan bisa ditumpuk langsung dari koordinatnya. Tinggi (z, dari lantai) yang
dipakai untuk susunan: sensor 4,5-6,1; driver 6,0-7,6; utama 18,6-20,2; antarmuka 31,2-32,8 (header 2,54 mm + socket
8,5 mm = jarak antar-papan 11 mm). Motor N20 di y -6..6, baterai LiPo 2S di dudukan 3D print di atas motor (y -22..8).

Konektor pasangan dicari orientasinya otomatis supaya pin bertemu pin: utama J4 (atas) - antarmuka J1 (bawah),
utama J5 (bawah) - driver J1 (atas), utama J3 (FFC, bawah) - sensor J1 (FFC, atas; pin sejajar sumbu x, kabel lurus).
Papan utama dibuat dulu; kalau tidak ikut dibuat, posisi pad-nya dibaca dari file.
"""
import math
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_pcb_utama_v17 as gu  # noqa: E402  (K, R, netlist, bentuk, teks)
import kisym  # noqa: E402
import pcbnew  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
X2 = os.path.join(ROOT, "hardware", "lfm-x2")
PRETTY = os.path.join(X2, "lfm-x2.pretty")
PAPAN = ["utama", "antarmuka", "driver", "sensor"]
M3, M2 = "MountingHole:MountingHole_3.2mm_M3", "MountingHole:MountingHole_2.2mm_M2"


def sch(p):
    return os.path.join(X2, p, f"lfm-x2-{p}.kicad_sch")


def brd(p):
    return os.path.join(X2, p, f"lfm-x2-{p}.kicad_pcb")


# ================================================================ bentuk
def bulat(pts):
    """poligon tertutup [(x, y, r)] -> ('seg', a, b) / ('arc', a, tengah, b); sudut dibulatkan radius r (0 = tajam)"""
    n, sudut = len(pts), []
    for i in range(n):
        c, r = pts[i][:2], pts[i][2]
        if r <= 0:
            sudut.append((c, None, c))
            continue
        a, b = pts[i - 1][:2], pts[(i + 1) % n][:2]
        u1 = (a[0] - c[0], a[1] - c[1]); l1 = math.hypot(*u1); u1 = (u1[0] / l1, u1[1] / l1)
        u2 = (b[0] - c[0], b[1] - c[1]); l2 = math.hypot(*u2); u2 = (u2[0] / l2, u2[1] / l2)
        half = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))) / 2
        if half > math.pi / 2 - 0.005:                # (hampir) segaris: tidak dibulatkan (busur nm = outline rusak)
            sudut.append((c, None, c))
            continue
        t = r / math.tan(half)
        if t > min(l1, l2) / 2 + 1e-6:
            raise SystemExit(f"radius {r} terlalu besar di {c}")
        bis = (u1[0] + u2[0], u1[1] + u2[1]); lb = math.hypot(*bis); bis = (bis[0] / lb, bis[1] / lb)
        ctr = (c[0] + bis[0] * r / math.sin(half), c[1] + bis[1] * r / math.sin(half))
        sudut.append(((c[0] + u1[0] * t, c[1] + u1[1] * t), (ctr[0] - bis[0] * r, ctr[1] - bis[1] * r),
                      (c[0] + u2[0] * t, c[1] + u2[1] * t)))
    out = []
    for i in range(n):
        t1, mid, t2 = sudut[i]
        if mid is not None:
            out.append(("arc", t1, mid, t2))
        nxt = sudut[(i + 1) % n][0]
        if math.hypot(nxt[0] - t2[0], nxt[1] - t2[1]) > 1e-6:
            out.append(("seg", t2, nxt))
    return out


def cermin(kanan):
    """setengah kanan (dari titik di sumbu x = 0 sampai titik di sumbu lagi) -> poligon tertutup simetris"""
    return list(kanan) + [(-x, y, r) for x, y, r in reversed(kanan[1:-1])]


def offset(poly, d):
    """polyline [(x, y)] digeser d tegak lurus (d > 0 = ke kiri arah jalan, di sini = ke depan), sudut miter"""
    out = []
    for i in range(len(poly)):
        ns = []
        for a, b in ((poly[i - 1], poly[i]) if i > 0 else (None, None), (poly[i], poly[i + 1]) if i < len(poly) - 1
                     else (None, None)):
            if a is None:
                continue
            tx, ty = b[0] - a[0], b[1] - a[1]; ln = math.hypot(tx, ty)
            ns.append((-ty / ln, tx / ln))
        mx, my = sum(n[0] for n in ns), sum(n[1] for n in ns); lm = math.hypot(mx, my); mx, my = mx / lm, my / lm
        k = d / (mx * ns[0][0] + my * ns[0][1])
        out.append((poly[i][0] + mx * k, poly[i][1] + my * k))
    return out


# ---------------------------------------------------------------- papan utama: segitiga gaya Ichibot
UTAMA = cermin([(0, 20, 0), (46, 20, 3), (48.5, 23.5, 3), (46, 28, 2), (38, 31, 3), (38, 50, 4), (16, 72, 3),
                (16, 78, 3), (0, 78, 0)])
# ---------------------------------------------------------------- antarmuka: sayap tombol 3 + 3, OLED di tengah
ANTARMUKA = cermin([(0, 21, 0), (16, 21, 3), (16.5, 34, 2), (29, 35, 3), (39, 45, 3), (39, 55, 3), (29, 65, 3),
                    (15, 65, 2), (15, 70, 3), (8, 79, 3), (0, 79, 0)])
# ---------------------------------------------------------------- driver: badan + 2 telinga lubang M3
DRIVER = cermin([(0, 7, 0), (25, 7, 3), (27, 19, 1.5), (45, 19, 3), (48.5, 23.5, 3), (45, 28, 3), (27, 28, 1.5),
                 (27, 44.5, 3), (0, 44.5, 0)])
# ---------------------------------------------------------------- sensor: busur rev B + bulan sabit + leher garpu
# titik sensor = posisi PCB sensor rev B (hardware/sensor-garis), sensor 1 = paling kiri dilihat dari atas
SENSOR_C = [(-41.393, 114.719), (-35.265, 119.861), (-28.014, 123.242), (-20.189, 124.906), (-12.22, 125.603),
            (-4.25, 126.3), (4.25, 126.3), (12.22, 125.603), (20.189, 124.906), (28.014, 123.242), (35.265, 119.861),
            (41.393, 114.719)]
BAND, UJUNG, LANCIP = 7.0, 9.0, 4.0                 # setengah lebar pita, perpanjangan ujung sayap, ujung lancip
LEHER_X, LENGAN_X, CELAH_Y, LENGAN_Y = 14.5, 7.5, 92.5, 55.0   # leher: tepi luar, tepi dalam lengan, atas celah, ujung
# y lubang M3 di lengan (x = +-11). 67 = nominal (segaris lubang papan utama); lubang lain menggeser sensor +7 / -7 /
# -14 mm. Jarak 7 mm: courtyard lubang M3 berdiameter 6,9 mm.
LUBANG_LEHER = [60.0, 67.0, 74.0, 81.0]


def sensor_geo():
    """titik busur diperpanjang, arah singgung dan normal (ke depan) tiap sensor"""
    c = SENSOR_C
    t0 = ((c[0][0] - c[1][0]) / 8, (c[0][1] - c[1][1]) / 8)
    t1 = ((c[-1][0] - c[-2][0]) / 8, (c[-1][1] - c[-2][1]) / 8)

    def unit(v):
        ln = math.hypot(*v)
        return v[0] / ln, v[1] / ln
    t0, t1 = unit(t0), unit(t1)
    jalur = [(c[0][0] + t0[0] * UJUNG, c[0][1] + t0[1] * UJUNG)] + c + [(c[-1][0] + t1[0] * UJUNG,
                                                                         c[-1][1] + t1[1] * UJUNG)]
    arah = []
    for i in range(1, len(jalur) - 1):
        t = unit((jalur[i + 1][0] - jalur[i - 1][0], jalur[i + 1][1] - jalur[i - 1][1]))
        arah.append((t, (-t[1], t[0])))            # singgung (ke kanan), normal (ke depan)
    return jalur, arah, t0, t1


def potong_x(poly, x):
    """titik pertama polyline yang memotong garis tegak x -> (indeks segmen, y)"""
    for i in range(len(poly) - 1):
        (x1, y1), (x2, y2) = poly[i], poly[i + 1]
        if (x1 - x) * (x2 - x) <= 0 and x1 != x2:
            return i, y1 + (y2 - y1) * (x - x1) / (x2 - x1)
    raise SystemExit(f"tidak memotong x = {x}")


def sensor_outline():
    jalur, _, t0, t1 = sensor_geo()
    luar, dalam = offset(jalur, BAND), offset(jalur, -BAND)
    tip_l = (jalur[0][0] + t0[0] * LANCIP, jalur[0][1] + t0[1] * LANCIP)
    tip_r = (jalur[-1][0] + t1[0] * LANCIP, jalur[-1][1] + t1[1] * LANCIP)
    pts = [(tip_r[0], tip_r[1], 0.6)]
    # tepi depan dari kanan ke kiri, dengan tonjolan baut skid di tengah
    for i in range(len(luar) - 1, -1, -1):
        x, y = luar[i]
        if i in (6, 7):                             # sensor 6 dan 7: tepi depan diganti tonjolan baut skid
            if i == 7:
                pts += [(x, y, 1.0), (3.5, y + 4.6, 1.5), (-3.5, y + 4.6, 1.5)]
            else:
                pts.append((x, y, 1.0))
            continue
        pts.append((x, y, 1.0 if i in (0, len(luar) - 1) else 2.0))
    pts.append((tip_l[0], tip_l[1], 0.6))
    # tepi dalam kiri sampai leher, leher + lengan garpu, tepi dalam kanan
    il, yl = potong_x(dalam, -LEHER_X)
    ir, yr = potong_x(dalam, LEHER_X)
    pts += [(x, y, 1.0 if i == 0 else 2.0) for i, (x, y) in enumerate(dalam[:il + 1])]
    pts += [(-LEHER_X, yl, 2.0), (-LEHER_X, LENGAN_Y, 3.4), (-LENGAN_X, LENGAN_Y, 3.4), (-LENGAN_X, CELAH_Y, 2.0),
            (LENGAN_X, CELAH_Y, 2.0), (LENGAN_X, LENGAN_Y, 3.4), (LEHER_X, LENGAN_Y, 3.4), (LEHER_X, yr, 2.0)]
    pts += [(x, y, 1.0 if i == len(dalam) - 1 else 2.0) for i, (x, y) in enumerate(dalam) if i > ir]
    return pts


OUTLINE = {"utama": UTAMA, "antarmuka": ANTARMUKA, "driver": DRIVER, "sensor": None}


def outline(p):
    return sensor_outline() if p == "sensor" else OUTLINE[p]


# ================================================================ isi tiap papan
# PLACE: ref -> (x, y, rotasi, sisi "F"/"B"). Titik asal footprint pustaka KiCad: SMD = tengah badan, THT = pin 1.
# Konektor pasangan dan sensor ditempatkan oleh kode (lihat tata()).
PLACE = {
    "utama": {
        # sisi atas: XT30 kanan belakang (mulut ke belakang, 0,55 mm melewati tepi papan supaya steker LiPo tidak
        # menabrak papan), saklar + USB-C di bahu kanan, socket antarmuka
        "J1": (20.75, 32.6, 180, "F"), "LED1": (32.25, 23.5, 0, "F"), "R9": (36.15, 23.5, 0, "F"),
        "SW1": (35.5, 31.5, 90, "F"), "J2": (34.8, 45.0, 90, "F"),
        # sisi bawah, kanan belakang: saklar beban (di antara kaki XT30 dan pasak)
        "Q1": (25.5, 28.0, 0, "B"), "R1": (29.5, 26.5, 90, "B"), "C1": (31.8, 26.5, 90, "B"),
        "R2": (34.1, 26.5, 90, "B"),
        # bahu kanan: CH340C + CC USB + dioda VBUS
        "U2": (22.5, 42.5, 90, "B"), "C11": (15.5, 44.5, 90, "B"), "R10": (29.6, 37.0, 90, "B"),
        "R11": (31.9, 37.0, 90, "B"), "D3": (25.0, 37.0, 0, "B"),
        # kanan depan: buck MP1584 (kalang C3 - U4 - D1 pendek)
        "U4": (15.5, 57.0, 0, "B"), "C3": (10.4, 56.5, 90, "B"), "C4": (7.9, 56.5, 90, "B"),
        "R5": (13.0, 61.8, 90, "B"), "C5": (21.3, 58.8, 90, "B"), "D1": (19.5, 50.5, 90, "B"),
        "L1": (26.0, 52.5, 0, "B"), "C6": (24.0, 59.5, 90, "B"), "R6": (18.3, 65.5, 90, "B"),
        "R7": (16.0, 65.5, 90, "B"), "R8": (16.5, 61.8, 0, "B"), "C7": (20.6, 63.0, 90, "B"),
        # tengah: dioda +5V dari buck, LDO 3,3 V
        "U3": (-5.0, 50.0, 0, "B"), "D2": (6.5, 46.5, 0, "B"), "C8": (6.5, 51.0, 0, "B"),
        "C9": (-10.7, 49.5, 90, "B"), "C10": (-13.2, 49.5, 90, "B"),
        # tengah belakang: auto-reset, pull-up IO0, tombol BOOT, pull-down DRV_EN
        "Q2": (-3.5, 29.0, 0, "B"), "R12": (-0.5, 29.0, 90, "B"), "Q3": (-3.5, 33.5, 0, "B"),
        "R13": (-0.5, 33.5, 90, "B"), "R15": (-18.0, 28.5, 90, "B"), "SW2": (-26.5, 25.0, 0, "B"),
        "R16": (-11.5, 36.5, 90, "B"),
        # depan ESP32: kapasitor 3V3, R/C EN, pembagi VBAT, pull-down BUZ
        "C13": (-29.0, 54.0, 90, "B"), "C14": (-26.5, 54.0, 90, "B"), "R14": (-24.0, 54.0, 90, "B"),
        "C12": (-21.5, 54.0, 90, "B"), "C2": (-19.0, 54.0, 90, "B"), "R3": (-16.5, 54.0, 90, "B"),
        "R4": (-14.0, 54.0, 90, "B"), "R17": (-11.5, 54.0, 90, "B"),
    },
    "antarmuka": {
        # tombol: kiri ATAS / OK / BAWAH, kanan KEMBALI / START / LANJUT, RST di tab depan (gaya Ichibot)
        "SW1": (-24.5, 58.5, 0, "F"), "SW4": (-32.5, 50.0, 0, "F"), "SW2": (-24.5, 41.5, 0, "F"),
        "SW3": (24.5, 58.5, 0, "F"), "SW6": (32.5, 50.0, 0, "F"), "SW5": (24.5, 41.5, 0, "F"),
        "SW7": (0.0, 73.5, 0, "F"),
        "R1": (-17.5, 58.5, 90, "F"), "R2": (-17.5, 41.5, 90, "F"), "R4": (-24.0, 50.0, 0, "F"),
        "R3": (17.5, 58.5, 90, "F"), "R5": (17.5, 41.5, 90, "F"),
        "R7": (24.0, 50.0, 0, "F"), "C2": (24.0, 52.5, 0, "F"), "R6": (-6.0, 44.0, 90, "F"), "C1": (-3.5, 44.0, 90, "F"),
        # buzzer di tab belakang (tidak di bawah OLED: tinggi 9,5 mm), transistornya di bawah OLED
        "BZ1": (-3.8, 28.0, 0, "F"), "Q1": (7.0, 40.0, 0, "F"), "R8": (4.0, 43.0, 90, "F"), "R9": (10.0, 43.0, 90, "F"),
    },
    "driver": {
        # konektor motor di tepi belakang (dekat motor), tab BTN7971B ke belakang, kaki ke depan
        "J2": (-20.5, 11.5, 0, "F"), "J3": (8.0, 11.5, 0, "F"),
        "U1": (-18.0, 21.25, -90, "F"), "U2": (-6.0, 21.25, -90, "F"), "U3": (6.0, 21.25, -90, "F"),
        "U4": (18.0, 21.25, -90, "F"),
        "C5": (-17.0, 40.3, 0, "F"),
    },
    "sensor": {
        "U1": (0.0, 111.0, 0, "F"), "C1": (9.5, 117.0, 90, "F"),
    },
}
RC_Y = 34.48                                       # driver: baris R/C di depan kaki BTN7971B (tegak)
RC_BTN = [(-4.6, None), (-2.3, "IS"), (0.0, "SR"), (2.3, "INH"), (4.6, "IN")]
HOLES = {   # (x, y, footprint, nama); dicerminkan ke x negatif
    "utama": [(44.0, 23.5, M3, "telinga: rangka + driver"), (12.5, 27.0, M3, "antarmuka belakang"),
              (11.0, 67.0, M3, "antarmuka depan + leher sensor")],
    "antarmuka": [(12.5, 27.0, M3, "ke papan utama"), (11.0, 67.0, M3, "ke papan utama"),
                  (11.75, 60.0, M2, "spacer OLED")],
    "driver": [(44.0, 23.5, M3, "telinga: rangka + papan utama")],
    "sensor": [(11.0, y, M3, "leher") for y in LUBANG_LEHER],
}
SKID = (0.0, 134.3)                                # sensor: baut skid nilon di tonjolan depan
ANTENA = (-42.0, -33.8, 30.5, 50.5)                # utama: daerah antena ESP32 (x0, x1, y0, y1), menonjol 3 mm
OLED = (0.0, 48.0, 27.3, 27.8)                     # antarmuka: modul OLED 0,96" (tengah x, y, lebar, panjang)
# pad pemasang SW1 bawaan KiCad (oval 2,2 x 3,5) hanya 0,25 mm dari kaki 1/3: dikecilkan (lubang 1,5 tetap).
PAD_FIX = {("utama", "SW1"): {"": (2.0, 3.3)}}
REF_SILK = {"utama": {"U1", "U2", "U3", "U4", "J2", "J3", "J4", "J5", "L1", "SW1", "SW2"},
            "antarmuka": {"J1", "J2"}, "driver": {"J1"}, "sensor": {"U1"}}
SILK = {    # (teks, x, y, ukuran, rotasi, sisi)
    "utama": [("LFM X2", 0.0, 47.0, 3.0, 0, "F"), ("rev B - papan utama", 0.0, 43.8, 1.0, 0, "F"),
              ("LIPO 2S", 23.25, 36.2, 0.9, 0, "F"), ("SAKLAR", 34.0, 26.9, 0.9, 0, "F"), ("USB", 31.5, 50.8, 0.9, 0, "F"),
              ("KE ANTARMUKA", 0.0, 64.2, 0.9, 0, "F"), ("PWR", 32.25, 21.5, 0.8, 0, "F"),
              ("KE DRIVER", 0.0, 36.3, 0.9, 0, "B"), ("KE SENSOR", 0.0, 66.5, 0.9, 0, "B"),
              ("BOOT", -26.5, 29.5, 0.9, 0, "B"), ("LFM X2 rev B", 0.0, 24.0, 1.2, 0, "B")],
    "antarmuka": [("ATAS", -24.5, 63.3, 0.9, 0, "F"), ("BAWAH", -24.5, 36.7, 0.9, 0, "F"),
                  ("OK", -32.5, 55.0, 0.9, 0, "F"), ("KEMBALI", 24.5, 63.3, 0.9, 0, "F"),
                  ("LANJUT", 24.5, 36.7, 0.9, 0, "F"), ("START", 32.5, 55.0, 0.9, 0, "F"),
                  ("RST", 0.0, 68.3, 0.9, 0, "F"), ("LFM X2 antarmuka rev B", 0.0, 50.0, 1.2, 0, "B")],
    "driver": [("MOTOR KIRI", -14.25, 16.0, 0.9, 0, "B"), ("MOTOR KANAN", 14.25, 16.0, 0.9, 0, "B"),
               ("LFM X2 driver rev B", 17.0, 40.5, 0.9, 0, "F")],
    "sensor": [("LFM X2 sensor rev B", -10.5, 105.0, 1.0, 90, "F")],
}
JUDUL = {"utama": "papan utama", "antarmuka": "papan antarmuka", "driver": "papan driver", "sensor": "papan sensor"}


# ================================================================ alat bantu footprint
def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(PRETTY if lib == "lfm-x2" else f"{gu.FP_SHARE}/{lib}.pretty", name)
    if fp is None:
        raise SystemExit(f"footprint tidak ketemu: {fpid}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def pads(fp):
    """{nomor: [(x, y) robot, ...]}"""
    d = {}
    for p in fp.Pads():
        d.setdefault(p.GetNumber(), []).append(gu.R(p.GetPosition()))
    return d


def taruh_pad(fp, num, x, y):
    """geser footprint supaya pad num tepat di (x, y)"""
    px, py = pads(fp)[num][0]
    fx, fy = gu.R(fp.GetPosition())
    fp.SetPosition(gu.K(fx + x - px, fy + y - py))


def arahkan(fp, cocok, ref):
    """coba rotasi 0/90/180/270, pakai yang pertama memenuhi cocok(fp)"""
    for r in (0, 90, 180, -90):
        fp.SetOrientationDegrees(r)
        if cocok(fp):
            return r
    raise SystemExit(f"{ref}: tidak ada rotasi yang cocok")


def selisih(fp, a, b):
    pa, pb = pads(fp)[a][0], pads(fp)[b][0]
    return pb[0] - pa[0], pb[1] - pa[1]


def dekat(v, w, tol=0.02):
    return abs(v[0] - w[0]) < tol and abs(v[1] - w[1]) < tol


def ffc_buka(fp):
    """arah mulut konektor FFC (+1 = ke +y robot, -1 = ke -y): kaki pemasang MP ada di sisi mulut"""
    mp = pads(fp)["MP"]
    sig = [pads(fp)[str(i)][0] for i in range(1, 9)]
    return 1 if sum(p[1] for p in mp) / len(mp) > sum(p[1] for p in sig) / len(sig) else -1


def netlist(p):
    net = os.path.join(tempfile.mkdtemp(), f"{p}.net")
    subprocess.run([kisym.KICAD_CLI, "sch", "export", "netlist", "-o", net, sch(p)], check=True, capture_output=True)
    return gu.read_netlist(net)


def kotak(b, layer, x0, x1, y0, y1, width=0.1):
    for a, c in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        gu.add_shape(b, layer, "seg", (a, c), width)


# ================================================================ tata letak
def pasangan_utama(b_utama):
    """posisi pad konektor papan utama (robot) untuk papan pasangannya"""
    out = {}
    for f in b_utama.GetFootprints():
        if f.GetReference() in ("J3", "J4", "J5"):
            out[f.GetReference()] = {k: v[0] for k, v in pads(f).items()}
    return out


def tata(p, comps, nets, loaded, lubang, paksa, target):
    if os.path.exists(brd(p)):
        lama = pcbnew.LoadBoard(brd(p))
        if len(lama.GetTracks()) and not paksa:
            raise SystemExit(f"{brd(p)} sudah berisi {len(lama.GetTracks())} jalur/via: tidak ditimpa (pakai --paksa)")
    b = pcbnew.NewBoard(brd(p))
    tb = b.GetTitleBlock()
    tb.SetTitle(f"LFM X2 rev B - {JUDUL[p]}"); tb.SetRevision("B"); tb.SetDate("2026-11-15")
    tb.SetComment(0, "Side project LFM (di luar RAB PjBL)")
    tb.SetComment(1, "Tata letak awal dari hardware/tools/gen_pcb_x2.py, jalur digambar sendiri")
    for s in bulat(outline(p)):
        gu.add_shape(b, pcbnew.Edge_Cuts, s[0], s[1:])
    netobj = {}

    def net(name):
        if name not in netobj:
            n = pcbnew.NETINFO_ITEM(b, name)
            b.Add(n)
            netobj[name] = n
        return netobj[name]

    place = dict(PLACE[p])
    di_net = {}
    for (ref, pin), n in nets.items():
        di_net.setdefault(n.lstrip("/"), []).append((ref, pin))
    if p == "driver":                              # R/C tiap BTN7971B: kaki yang ke chip menghadap ke kaki chip
        for i in range(4):
            u = f"U{i + 1}"
            cx = PLACE["driver"][u][0]
            for dx, apa in RC_BTN:
                if apa is None:
                    ref, pin = f"C{i + 1}", "1"
                else:
                    ref, pin = next((r, q) for r, q in di_net[f"{u}_{apa}"] if r.startswith("R"))
                place[ref] = (cx + dx, RC_Y, 90 if pin == "1" else -90, "F")
    jalur, arah, _, _ = sensor_geo() if p == "sensor" else (None, None, None, None)
    khusus = {"utama": {"U1", "J3", "J4", "J5"}, "antarmuka": {"J1", "J2"}, "driver": {"J1"},
              "sensor": {"J1"} | {f"D{i}" for i in range(1, 13)} | {f"Q{i}" for i in range(1, 13)}
              | {f"R{i}" for i in range(1, 25)}}[p]
    kurang = sorted(set(comps) - set(place) - khusus)
    if kurang:
        raise SystemExit(f"{p}: belum punya posisi: {kurang}")

    for ref, c in sorted(comps.items()):
        fp = loaded[ref]
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        if c.get("datasheet") and c["datasheet"] != "~":
            fp.SetField("Datasheet", c["datasheet"])
        fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        x, y, rot, sisi = place.get(ref, (0.0, 0.0, 0, "F"))
        if p == "utama" and ref in ("U1", "J3", "J5"):
            sisi = "B"
        if p == "antarmuka" and ref == "J1":
            sisi = "B"
        if p == "sensor" and ref[0] in "DQ":
            sisi = "B"
        fp.SetPosition(gu.K(x, y))
        fp.SetOrientationDegrees(rot)
        b.Add(fp)
        if ref == "U1" and p == "utama":           # via termal bor 0,2 mm di pad bawah modul: di bawah bor minimum
            kecil = [q for q in fp.Pads() if q.GetNumber() == "39" and q.GetDrillSize().x > 0]
            # keepout bawaan footprint (48 x 21 mm di depan antena, termasuk "footprint tidak boleh") menutup telinga
            # kiri + lubangnya; diganti area aturan ANTENA di papan (tanpa jalur/via/pour di bawah antena)
            kecil += list(fp.Zones())
            # courtyard bawaan ikut melebar 48 mm di depan antena: diganti kotak badan modul saja
            kecil += [g for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.F_CrtYd]
            gu._BUANG.extend(kecil)
            for q in kecil:
                fp.Remove(q)
            cy = pcbnew.PCB_SHAPE(fp)
            cy.SetShape(pcbnew.SHAPE_T_RECT)
            o = fp.GetPosition()                   # (rotasi 0, belum dibalik: koordinat lokal + posisi)
            cy.SetStart(pcbnew.VECTOR2I(o.x + pcbnew.FromMM(-9.77), o.y + pcbnew.FromMM(-13.0)))
            cy.SetEnd(pcbnew.VECTOR2I(o.x + pcbnew.FromMM(9.77), o.y + pcbnew.FromMM(13.56)))
            cy.SetLayer(pcbnew.F_CrtYd)
            cy.SetWidth(pcbnew.FromMM(0.05))
            fp.Add(cy)
        if sisi == "B":                             # (Flip sesudah Add: sebelum itu segfault)
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            fp.SetOrientationDegrees(rot)
        tempatkan(p, ref, fp, target, jalur, arah, nets)
        fab = pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab
        if ref not in REF_SILK[p]:
            fp.Reference().SetLayer(fab)
        if (p, ref) == ("utama", "J1"):            # STEP XT30 tidak terpasang: model kotak dari gen_lib_x2.py xt30
            fp.Models().clear()
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = "${KIPRJMOD}/../lfm-x2.3dshapes/AMASS_XT30PW-M_sederhana.wrl"
            fp.Models().push_back(m)
        if (p, ref) in (("utama", "SW1"), ("utama", "J2"), ("utama", "J1")):   # badan menonjol keluar tepi: garis silk
            for g in fp.GraphicalItems():                                       # pindah ke Fab (tanda +/- XT30 tetap)
                if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() != "PCB_FIELD" and \
                        not (ref == "J1" and g.GetClass() == "PCB_TEXT"):
                    g.SetLayer(pcbnew.F_Fab)
        for q in fp.Pads():
            if q.GetNumber() in PAD_FIX.get((p, ref), {}):
                w, h = PAD_FIX[(p, ref)][q.GetNumber()]
                q.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(pcbnew.FromMM(w), pcbnew.FromMM(h)))
            name = nets.get((ref, q.GetNumber()))
            if name:
                q.SetNet(net(name))
    for i, (x, y, fp, nama) in enumerate(lubang, 1):
        fp.SetReference(f"H{i}")
        fp.SetValue(nama)
        fp.SetPosition(gu.K(x, y))
        fp.Reference().SetLayer(pcbnew.F_Fab)
        fp.SetBoardOnly(True)
        b.Add(fp)
    if p == "utama":                               # tanpa jalur/via/pour di bawah antena ESP32 (kedua sisi)
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetZoneName("Antena ESP32")
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu)
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        (z.SetDoNotAllowZoneFills if hasattr(z, "SetDoNotAllowZoneFills") else z.SetDoNotAllowCopperPour)(True)
        x0, x1, y0, y1 = ANTENA
        gu.zone_poly(z, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        b.Add(z)
    hiasan(b, p, jalur, arah)
    pcbnew.SaveBoard(brd(p), b)
    n_bawah = sum(1 for f in b.GetFootprints() if f.IsFlipped())
    print(f"ditulis {brd(p)}: {len(comps)} komponen ({n_bawah} di sisi bawah) + {len(lubang)} lubang, "
          f"{len(netobj)} net, 0 jalur")
    return b


def tempatkan(p, ref, fp, target, jalur, arah, nets):
    """penempatan yang dihitung: konektor pasangan, ESP32, sensor"""
    if p == "utama" and ref == "U1":
        # ESP32 di sisi bawah, antena ke kiri menonjol 3 mm keluar bahu kiri (x -38), deret pin 1-14 menghadap depan
        arahkan(fp, lambda f: dekat(selisih(f, "1", "14"), (16.51, 0.0)) and pads(f)["15"][0][0] > pads(f)["1"][0][0],
                ref)
        fp.SetPosition(gu.K(-28.25, 40.5))
    elif p == "utama" and ref in ("J4", "J5"):
        # socket 2 baris memanjang sumbu x, pin 1 di kiri depan, pin genap di baris belakang
        akhir = "9" if ref == "J4" else "13"
        panjang = 10.16 if ref == "J4" else 15.24
        arahkan(fp, lambda f: dekat(selisih(f, "1", akhir), (panjang, 0.0)) and abs(selisih(f, "1", "2")[0]) < 0.02,
                ref)
        if ref == "J4":
            taruh_pad(fp, "1", -5.08, 60.77 if selisih(fp, "1", "2")[1] < 0 else 58.23)
        else:
            taruh_pad(fp, "1", -7.62, 41.54 if selisih(fp, "1", "2")[1] < 0 else 39.0)
    elif p == "utama" and ref == "J3":
        # FFC di sisi bawah, mulut ke depan (+y) tepat di tepi ujung segitiga (y 78)
        arahkan(fp, lambda f: ffc_buka(f) == 1 and abs(selisih(f, "1", "8")[1]) < 0.02, ref)
        sig = [pads(fp)[str(i)][0] for i in range(1, 9)]
        cx = sum(q[0] for q in sig) / 8
        fx, fy = gu.R(fp.GetPosition())
        fp.SetPosition(gu.K(fx - cx, fy - sig[0][1] + 69.85))
    elif p in ("antarmuka", "driver") and ref == "J1":
        mate = target["J4" if p == "antarmuka" else "J5"]
        n = len(mate)

        def cocok(f):
            taruh_pad(f, "1", *mate["1"])
            return all(dekat(pads(f)[k][0], mate[k]) for k in mate)
        arahkan(fp, cocok, ref)
    elif p == "antarmuka" and ref == "J2":
        # socket OLED: pin 1 (GND) di kanan karena modul diputar 180 (deret pin di belakang)
        arahkan(fp, lambda f: dekat(selisih(f, "1", "4"), (-7.62, 0.0)), ref)
        taruh_pad(fp, "1", 3.81, OLED[1] - OLED[3] / 2 + 2.4)
    elif p == "sensor" and ref == "J1":
        # FFC di sisi atas, mulut ke belakang (-y) ke celah leher, pin sejajar pin J3 papan utama (kabel lurus)
        mate = target["J3"]
        arahkan(fp, lambda f: ffc_buka(f) == -1 and abs(selisih(f, "1", "8")[1]) < 0.02, ref)
        sig = [pads(fp)[str(i)][0] for i in range(1, 9)]
        fx, fy = gu.R(fp.GetPosition())
        fp.SetPosition(gu.K(fx + mate["1"][0] - sig[0][0], fy - sig[0][1] + CELAH_Y + 0.5 + 7.85))
        for i in range(1, 9):
            if abs(pads(fp)[str(i)][0][0] - mate[str(i)][0]) > 0.02:
                raise SystemExit("sensor J1: pin tidak sejajar dengan J3 papan utama")
    elif p == "sensor" and ref[0] in "DQR":
        n = int(ref[1:])
        if ref[0] == "R":
            i, k = (n - 1) // 2, (n - 1) % 2       # R ganjil = 220 (LED), genap = 10k (fototransistor)
        else:
            i, k = n - 1, None
        cx, cy = SENSOR_C[i]
        (tx, ty), (nx, ny) = arah[i]
        if ref[0] == "D":                          # LED di depan, fototransistor di belakang (sisi bawah)
            x, y, sumbu = cx + 2.0 * nx, cy + 2.0 * ny, (tx, ty)
        elif ref[0] == "Q":
            x, y, sumbu = cx - 2.0 * nx, cy - 2.0 * ny, (tx, ty)
        else:                                      # resistor di sisi atas, tegak lurus busur
            s = -1 if k == 0 else 1
            x, y = cx + s * 2.1 * tx, cy + s * 2.1 * ty
            sumbu = (nx, ny) if k == 0 else (-nx, -ny)   # pad 2 (A / S) menghadap LED / fototransistor
        fp.SetPosition(gu.K(x, y))
        sudut = math.degrees(math.atan2(sumbu[1], sumbu[0]))
        terbaik = None
        for r in (sudut, -sudut, sudut + 180, 180 - sudut):
            fp.SetOrientationDegrees(r)
            d = selisih(fp, "1", "2")
            ln = math.hypot(*d)
            skor = (d[0] * sumbu[0] + d[1] * sumbu[1]) / ln
            if terbaik is None or skor > terbaik[0]:
                terbaik = (skor, r)
        fp.SetOrientationDegrees(terbaik[1])


def hiasan(b, p, jalur, arah):
    """silkscreen, gambar bantu, papan lain di Dwgs.User"""
    for txt, x, y, size, rot, sisi in SILK[p]:
        lay = pcbnew.F_SilkS if sisi == "F" else pcbnew.B_SilkS
        gu.add_text(b, lay, txt, x, y, size, rot, 0.2 if size <= 1.2 else 0.3, mirror=(sisi == "B"))
    if p == "sensor":
        for i, (cx, cy) in enumerate(SENSOR_C):     # nomor sensor di sisi atas, di depan resistornya
            (tx, ty), (nx, ny) = arah[i]
            gu.add_text(b, pcbnew.F_SilkS, str(i + 1), cx + 4.6 * nx, cy + 4.6 * ny, 1.0, 0, 0.2)
            gu.add_text(b, pcbnew.B_SilkS, str(i + 1), cx + 4.6 * nx, cy + 4.6 * ny, 1.0, 0, 0.2, mirror=True)
        gu.add_text(b, pcbnew.F_Fab, "lubang leher: baut ke papan utama (x +-11, y 67) lewat spacer 12,5 mm", 0.0, 57.0,
                    0.8)
    if p == "antarmuka":
        ox, oy, ow, oh = OLED
        kotak(b, pcbnew.F_Fab, ox - ow / 2, ox + ow / 2, oy - oh / 2, oy + oh / 2)
        gu.add_text(b, pcbnew.F_Fab, "OLED 0,96 (deret pin di belakang)", ox, oy + oh / 2 - 1.5, 1.0)
    # papan lain dan mekanik di Dwgs.User (gambar bantu susunan)
    lain = {"utama": ["antarmuka", "driver", "sensor"], "antarmuka": ["utama"], "driver": ["utama"],
            "sensor": ["utama"]}[p]
    for q in lain:
        for s in bulat(outline(q)):
            gu.add_shape(b, pcbnew.Dwgs_User, s[0], s[1:], 0.1)
    if p in ("utama", "driver"):
        for sx in (1, -1):
            kotak(b, pcbnew.Dwgs_User, sx * 4, sx * 37, -6, 6, 0.15)
            kotak(b, pcbnew.Dwgs_User, sx * 39.5, sx * 57.5, -17, 17, 0.15)
        kotak(b, pcbnew.Dwgs_User, -27.5, 27.5, -22, 8, 0.15)
        gu.add_text(b, pcbnew.Dwgs_User, "LiPo 2S di atas motor (dudukan 3D print)", 0, -7, 1.2)
        gu.add_text(b, pcbnew.Dwgs_User, "motor N20", -20.5, 0, 1.2)
        gu.add_text(b, pcbnew.Dwgs_User, "motor N20", 20.5, 0, 1.2)


def peta(pilih):
    """peta rakit PDF tiap papan: lapisan Fab (referensi + nilai) + outline, diperbesar, sisi bawah dicermin.
    Papan sensor tanpa nilai (terlalu rapat): D = LED IR (depan), Q = PT67-21B (belakang), R ganjil 220, genap 10k.
    KiCad memusatkan gambar berskala memakai kotak SEMUA item, jadi dicetak dari salinan tanpa gambar bantu Dwgs.User."""
    for p in pilih:
        b = pcbnew.LoadBoard(brd(p))
        bantu = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Dwgs_User]
        gu._BUANG.extend(bantu)
        for d in bantu:
            b.Remove(d)
        tmp = os.path.join(tempfile.mkdtemp(), os.path.basename(brd(p)))
        pcbnew.SaveBoard(tmp, b)
        sisi = [("atas", "F.Fab,Edge.Cuts", [])]
        if any(f.IsFlipped() for f in b.GetFootprints()):
            sisi.append(("bawah", "B.Fab,Edge.Cuts", ["--mirror"]))
        for nama, lay, extra in sisi:
            out = os.path.join(X2, p, f"lfm-x2-{p}-peta-rakit-{nama}.pdf")
            subprocess.run([kisym.KICAD_CLI, "pcb", "export", "pdf", "--mode-single", "--layers", lay,
                            "--include-border-title", "--sketch-pads-on-fab-layers", "--black-and-white",
                            "--scale", "1.6" if p == "sensor" else "2", "-o", out, tmp]
                           + extra + (["--exclude-value"] if p == "sensor" else []), check=True, capture_output=True)
            print(f"ditulis {out}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or args[0] not in ("tata", "pour", "peta"):
        raise SystemExit(__doc__)
    if args[0] == "pour":
        return pour(args[1])
    if args[0] == "peta":
        return peta([q for q in PAPAN if q in args[1:]] or PAPAN)
    pilih = [q for q in PAPAN if q in args[1:]] or PAPAN
    # semua footprint dimuat sebelum papan apa pun dibuat/dibaca: di KiCad 10 FootprintLoad gagal sesudahnya
    data = {}
    for q in pilih:
        comps, nets = netlist(q)
        loaded = {ref: load_fp(c["fp"]) for ref, c in comps.items()}
        lubang = []
        for x, y, fpid, nama in HOLES[q]:
            for sx in ((1, -1) if x else (1,)):
                lubang.append((sx * x, y, load_fp(fpid), nama))
        if q == "sensor":
            lubang.append((SKID[0], SKID[1], load_fp(M3), "skid depan (baut nilon)"))
        data[q] = (comps, nets, loaded, lubang)
    target = None
    if "utama" not in pilih:
        target = pasangan_utama(pcbnew.LoadBoard(brd("utama")))
    for q in pilih:
        b = tata(q, *data[q], "--paksa" in sys.argv, target)
        if q == "utama":
            target = pasangan_utama(b)


def pour(p):
    """GND pour F.Cu + B.Cu sesudah routing (jarak ke pour 0,5 mm, aturan tempat cetak)"""
    b = pcbnew.LoadBoard(brd(p))
    lama = [z for z in b.Zones() if not z.GetIsRuleArea()]
    gu._BUANG.extend(lama)
    for z in lama:
        b.Remove(z)
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b)
        z.SetLayer(lay)
        z.SetNet(b.FindNet("GND"))
        z.SetZoneName("GND")
        z.SetLocalClearance(pcbnew.FromMM(0.5))
        z.SetMinThickness(pcbnew.FromMM(0.35))
        z.SetThermalReliefGap(pcbnew.FromMM(0.5))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.5))
        gu.zone_poly(z, [(-60, 0), (60, 0), (60, 145), (-60, 145)])
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(brd(p), b)
    print(f"{p}: GND pour F.Cu + B.Cu")


if __name__ == "__main__":
    main()
