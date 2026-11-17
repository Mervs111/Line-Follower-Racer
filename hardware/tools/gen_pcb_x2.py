"""Tata letak awal 4 PCB LFM X2 rev B (gaya Ichibot Ultimate 5 Max, 15/11/2026): outline, lubang, semua footprint +
net. TANPA jalur dan tanpa pour (16/11: keempat papan dirouting dengan hardware/tools/autoroute/x2_router.py).

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
utama J5 (bawah) - driver J1 (atas), utama J3 (JST XH siku, bawah) - sensor J1 (JST XH tegak, atas; pin sejajar sumbu
x, kabel lurus).
Rombak 16/11 (permintaan user): ESP32 membujur di tengah papan utama, antena ke depan (gaya Ichibot); socket J4 pindah
ke kiri (membujur), J5 ke kiri; papan driver dilebarkan ke x +-30 supaya J1-nya ikut; sensor = 12x QRE1113GR.
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
DRIVER = cermin([(0, 7, 0), (25, 7, 3), (27, 19, 1.5), (45, 19, 3), (48.5, 23.5, 3), (45, 28, 3), (30, 28, 1.5),
                 (30, 44.5, 3), (0, 44.5, 0)])
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
        # Rombak 16/11: ESP32 membujur di tengah (antena ke depan), J4 membujur di kiri, J5 melintang di kiri belakang
        # (keduanya ditempatkan kode, lihat tempatkan()).
        # sisi atas: XT30 kanan belakang (mulut ke belakang, 0,55 mm melewati tepi papan supaya steker LiPo tidak
        # menabrak papan), saklar + USB-C di bahu kanan
        "J1": (20.75, 32.6, 180, "F"), "LED1": (32.25, 23.5, 0, "F"), "R9": (36.15, 23.5, 0, "F"),
        "SW1": (35.5, 31.5, 90, "F"), "J2": (34.8, 45.0, 90, "F"),
        # Fanout deret kanan ESP32 tetap (autoroute/x2_fanout_utama.json, 16/11): via kaki 2-7 dan 12 berselang dua
        # kolom (x 10,45 / 11,45), EN/BTN/BTN2/BUZ/+3V3 ke kiri lewat sisi atas di atas modul, MUX_SIG di sisi atas ke
        # depan, 4 MUX_S di sisi bawah (x 12,6-14,4) ke J3. Karena itu pasif kaki 2/3 tidak lagi di kanan deret pin:
        # C14 (100 nF 3V3) di sisi bawah tepat di depan kaki 1 (diputar: pad GND ke belakang, langsung ke kaki 1 GND,
        # karena kantong di depan kaki 1-2 tertutup daerah antena dan jalur MUX), C13 (10 uF) di dekat LDO, R14/C12
        # (RC EN) di kiri J4.
        # Sisi atas kanan tinggal pembagi VBAT + C (kaki 5); R3 diputar supaya ketiga pad VBAT_SENSE sebaris di
        # belakang dan VBAT masuk R3 dari depan.
        "C14": (10.85, 55.0, -90, "B"), "C13": (-24.0, 54.2, 90, "B"), "R14": (-19.0, 57.6, -90, "F"),
        "C12": (-19.0, 53.6, 90, "F"), "C2": (14.0, 44.1, 90, "F"), "R3": (16.7, 44.1, -90, "F"),
        "R4": (19.4, 44.1, 90, "F"),
        # sisi bawah, kanan belakang: saklar beban (di antara kaki XT30 dan pasak)
        "Q1": (25.5, 28.0, 0, "B"), "R1": (29.5, 26.5, 90, "B"), "C1": (31.8, 26.5, 90, "B"),
        "R2": (34.1, 26.5, 90, "B"),
        # bahu kanan: CH340C + dioda VBUS; resistor CC di sisi atas tepat di ujung jalur fanout USB-C (CC1/CC2 tidak
        # perlu menyeberangi D+/D-, lihat autoroute/x2_router.py fanout); dioda +5V dari buck di belakangnya. C11
        # (100 nF CH340C) di belakang U2: lajur sisi bawah x 14,9-17,2 di antara jalur MUX_S0 dan U2 dibiarkan kosong
        # untuk +5V_BUCK ke D2, yang harus menyeberangi jalur VBAT_SENSE (sisi atas) ke pembagi. R10/R11 tegak (17/11):
        # pad CC menghadap D+/D-, pad GND menghadap kaki pelindung J2 di belakang/depannya dan disambung jalur tetap
        # (autoroute/x2_fanout_utama.json); mendatar, pad GND R10 terkurung jalur D+/D-/CC1/VBUS dan lepas dari pour.
        "U2": (22.5, 42.5, 90, "B"), "C11": (18.5, 36.8, 0, "B"), "R10": (26.6, 42.2, -90, "F"),
        "R11": (26.6, 47.75, 90, "F"), "D3": (25.0, 35.8, 0, "B"), "D2": (14.6, 35.9, 90, "B"),
        # kanan depan: buck MP1584, U4 diputar 90 (16/11): kaki SW (1) dan BST (8) di sisi kanan, C5 tepat di antaranya,
        # D1 + L1 (di depan via VBUS dan kaki pelindung J2) di kanan belakang, C3 (VIN) + R5 (FREQ, lewat sela pad C3) di
        # depan, C4 (VIN), C6 (keluaran) dan R6 (FB atas) di sisi atas, R7 (FB) + R8/C7 (COMP) di belakang U4. Lajur
        # sisi bawah x 9,6-14 di kanan deret pin ESP32 bebas komponen untuk 4 jalur MUX_S ke J3 (D2 ikut mundur supaya
        # jalur MUX_S0 dari kaki 11 lewat).
        "U4": (19.0, 57.8, 90, "B"), "C5": (23.0, 59.4, -90, "B"), "D1": (20.75, 50.6, -90, "B"),
        "L1": (26.85, 53.63, 0, "B"), "C6": (25.6, 58.6, 90, "F"), "C3": (18.2, 62.7, 180, "B"),
        "C4": (20.2, 63.0, 0, "F"), "R5": (18.37, 65.8, 90, "B"), "R6": (16.6, 57.6, 180, "F"),
        "R7": (15.95, 52.1, -90, "B"), "R8": (17.95, 52.1, -90, "B"), "C7": (17.95, 48.3, -90, "B"),
        # kiri depan: LDO 3,3 V (tab ke arah ESP32) + kapasitor +5V / +3V3
        "U3": (-27.0, 47.8, 0, "B"), "C8": (-33.5, 47.8, 90, "B"), "C9": (-20.2, 47.8, 90, "B"),
        "C10": (-20.2, 53.0, 90, "B"),
        # tengah belakang: auto-reset; kiri belakang: pull-up IO0, tombol BOOT, pull-down DRV_EN
        "Q2": (-3.5, 27.0, 0, "B"), "R12": (-0.5, 27.0, 90, "B"), "Q3": (-3.5, 31.0, 0, "B"),
        "R13": (-0.5, 31.0, 90, "B"), "R15": (-18.0, 28.0, 90, "B"), "SW2": (-26.5, 25.0, 0, "B"),
        "R16": (-13.5, 33.0, 90, "B"),
    },
    "antarmuka": {
        # tombol: kiri ATAS / OK / BAWAH, kanan KEMBALI / START / LANJUT, RST di tab depan (gaya Ichibot)
        "SW1": (-24.5, 58.5, 0, "F"), "SW4": (-32.5, 50.0, 0, "F"), "SW2": (-24.5, 41.5, 0, "F"),
        "SW3": (24.5, 58.5, 0, "F"), "SW6": (32.5, 50.0, 0, "F"), "SW5": (24.5, 41.5, 0, "F"),
        "SW7": (0.0, 73.5, 0, "F"),
        "R1": (-17.5, 61.6, 90, "F"), "R2": (-17.5, 41.5, 90, "F"), "R4": (-24.0, 50.0, 0, "F"),
        "R3": (17.5, 58.5, 90, "F"), "R5": (17.5, 41.5, 90, "F"),
        "R7": (24.0, 50.0, 0, "F"), "C2": (24.0, 52.5, 0, "F"), "R6": (-6.0, 44.0, 90, "F"), "C1": (-3.5, 44.0, 90, "F"),
        # buzzer di tab belakang (tidak di bawah OLED: tinggi 9,5 mm), transistornya di bawah OLED
        "BZ1": (-3.8, 28.0, 0, "F"), "Q1": (7.0, 40.0, 0, "F"), "R8": (4.0, 43.0, 90, "F"), "R9": (10.0, 43.0, 90, "F"),
    },
    "driver": {
        # konektor motor di tepi belakang (dekat motor), tab BTN7971B ke belakang, kaki ke depan
        "J2": (-20.5, 10.8, 0, "F"), "J3": (8.0, 10.8, 0, "F"),   # JST XH siku: badan 0,6 mm dari BTN7971B
        "U1": (-18.0, 21.25, -90, "F"), "U2": (-6.0, 21.25, -90, "F"), "U3": (6.0, 21.25, -90, "F"),
        "U4": (18.0, 21.25, -90, "F"),
        "C5": (0.0, 40.7, 0, "F"),                   # elko VBAT di tengah (J1 pindah ke kiri, 16/11)
    },
    "sensor": {
        "U13": (0.0, 111.0, 0, "F"), "C1": (9.5, 117.0, 90, "F"),
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
# utama: ESP32 membujur di tengah, antena ke depan (16/11). Badan modul y 34,7-60,2, pin 1 di y 52,71 (deret 1-14 di
# kanan, x +8,75), deret 15-24 di belakang (y 34,95). Tanpa jalur/via/pour di bawah antena sampai 0,8 mm di depan
# modul. Dulu modul 3 mm lebih maju dan larangan sampai badan J3: bersama lubang H5/H6 (+-11; 67) menutup jalan
# jalur MUX dari J3, router macet (+-50 tabrakan); sekarang ada lorong +-5 mm antara modul dan lubang.
U1_POS = (0.0, 47.45)
ANTENA = (-9.6, 9.6, 53.4, 61.0)                   # utama: daerah antena ESP32 (x0, x1, y0, y1)
# utama: sisi bawah di bawah badan ESP32 (antara baris pad 1-14 / 25-38 dan kolom 15-24, 0,45 mm dari pad): tanpa
# jalur dan via (tembaga terbuka tertindih modul), GND pour boleh (menyambung pad termal pin 39)
BAWAH_ESP32 = (-7.55, 7.55, 36.15, 53.4)
OLED = (0.0, 48.0, 27.3, 27.8)                     # antarmuka: modul OLED 0,96" (tengah x, y, lebar, panjang)
# pad pemasang SW1 bawaan KiCad (oval 2,2 x 3,5) hanya 0,25 mm dari kaki 1/3: dikecilkan (lubang 1,5 tetap).
PAD_FIX = {("utama", "SW1"): {"": (2.0, 3.3)}}
REF_SILK = {"utama": {"U1", "U2", "U3", "U4", "J2", "J3", "J4", "J5", "L1", "SW1", "SW2"},
            "antarmuka": {"J1", "J2"}, "driver": {"J1"}, "sensor": {"U13"}}
SILK = {    # (teks, x, y, ukuran, rotasi, sisi)
    "utama": [("LFM X2", 0.0, 47.0, 3.0, 0, "F"), ("rev B - papan utama", 0.0, 43.8, 1.0, 0, "F"),
              ("LIPO 2S", 23.25, 36.2, 0.9, 0, "F"), ("SAKLAR", 34.0, 26.9, 0.9, 0, "F"), ("USB", 31.5, 50.8, 0.9, 0, "F"),
              ("KE ANTARMUKA", -14.5, 61.2, 0.9, 0, "F"), ("PWR", 32.25, 21.5, 0.8, 0, "F"),
              ("KE DRIVER", -19.2, 35.4, 0.9, 0, "B"), ("KE SENSOR", 0.0, 66.5, 0.9, 0, "B"),
              ("BOOT", -26.5, 29.5, 0.9, 0, "B"), ("LFM X2 rev B", 0.0, 24.0, 1.2, 0, "B"),
              ("ANTENA", 0.0, 57.0, 0.9, 0, "F")],
    "antarmuka": [("ATAS", -24.5, 63.3, 0.9, 0, "F"), ("BAWAH", -24.5, 36.7, 0.9, 0, "F"),
                  ("OK", -32.5, 55.0, 0.9, 0, "F"), ("KEMBALI", 24.5, 63.3, 0.9, 0, "F"),
                  ("LANJUT", 24.5, 36.7, 0.9, 0, "F"), ("START", 32.5, 55.0, 0.9, 0, "F"),
                  ("RST", 0.0, 68.3, 0.9, 0, "F"), ("LFM X2 antarmuka rev B", 0.0, 50.0, 1.2, 0, "B")],
    "driver": [("MOTOR KIRI", -14.25, 16.0, 0.9, 0, "B"), ("MOTOR KANAN", 14.25, 16.0, 0.9, 0, "B"),
               ("LFM X2 driver rev B", 17.0, 40.5, 0.9, 0, "F")],
    "sensor": [("LFM X2 sensor rev B", 0.0, 104.5, 1.0, 0, "B")],          # sisi bawah: di atas ada badan J1 (16/11)
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


def badan_y(fp):
    """y robot tengah kotak badan footprint (untuk arah mulut konektor siku)"""
    bx = fp.GetBoundingBox(False)
    return gu.R(bx.GetCenter())[1]


SISI_QRE = {}                                      # sensor: kanal -> [sisi anoda, sisi kolektor] sepanjang busur


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
              "sensor": {"J1"} | {f"U{i}" for i in range(1, 13)} | {f"R{i}" for i in range(1, 25)}}[p]
    kurang = sorted(set(comps) - set(place) - khusus)
    if kurang:
        raise SystemExit(f"{p}: belum punya posisi: {kurang}")

    # sensor: QRE (U1-U12) dulu, resistornya mengikuti sisi pad QRE (SISI_QRE)
    for ref, c in sorted(comps.items(), key=lambda kv: (p == "sensor" and kv[0][0] != "U", kv[0])):
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
        if p == "sensor" and ref[0] == "U" and ref != "U13":            # QRE1113GR di sisi bawah
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
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetZoneName("Bawah ESP32")
        z.SetLayer(pcbnew.B_Cu)
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        (z.SetDoNotAllowZoneFills if hasattr(z, "SetDoNotAllowZoneFills") else z.SetDoNotAllowCopperPour)(False)
        x0, x1, y0, y1 = BAWAH_ESP32
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
        # ESP32 di sisi bawah, membujur di tengah, antena ke depan: deret 1-14 dari depan ke belakang, deret 15-24 di
        # belakang (16/11; dulu melintang di bahu kiri)
        arahkan(fp, lambda f: dekat(selisih(f, "1", "14"), (0.0, -16.51)) and pads(f)["15"][0][1] < pads(f)["1"][0][1],
                ref)
        fp.SetPosition(gu.K(*U1_POS))
    elif p == "utama" and ref == "J4":
        # socket 2x5 membujur di kiri ESP32 (16/11): pin 1 di belakang kiri, pin genap di kolom kanan
        arahkan(fp, lambda f: dekat(selisih(f, "1", "9"), (0.0, 10.16)) and dekat(selisih(f, "1", "2"), (2.54, 0.0)), ref)
        taruh_pad(fp, "1", -15.77, 46.5)    # 5,2 mm di depan baris atas J5 (lorong jalur), pin 10 3,6 mm dari lubang OLED
    elif p == "utama" and ref == "J5":
        # socket 2x7 melintang di kiri belakang ESP32, pin 1 di kiri depan, pin genap di baris belakang
        arahkan(fp, lambda f: dekat(selisih(f, "1", "13"), (15.24, 0.0)) and abs(selisih(f, "1", "2")[0]) < 0.02, ref)
        taruh_pad(fp, "1", -26.82, 41.27 if selisih(fp, "1", "2")[1] < 0 else 38.73)
    elif p == "utama" and ref == "J3":
        # JST XH 8 siku di sisi bawah, mulut ke depan (+y) menonjol 3,3 mm dari ujung segitiga (posisi user 16/11)
        arahkan(fp, lambda f: dekat(selisih(f, "1", "8"), (17.5, 0.0)) and badan_y(f) > pads(f)["1"][0][1], ref)
        taruh_pad(fp, "1", -8.75, 73.2)
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
        # JST XH 8 tegak di sisi atas, tepat di depan celah leher, pin sejajar pin J3 papan utama (kabel lurus)
        mate = target["J3"]
        arahkan(fp, lambda f: dekat(selisih(f, "1", "8"), (17.5, 0.0)), ref)
        taruh_pad(fp, "1", mate["1"][0], 97.5)
        for i in range(1, 9):
            if abs(pads(fp)[str(i)][0][0] - mate[str(i)][0]) > 0.02:
                raise SystemExit("sensor J1: pin tidak sejajar dengan J3 papan utama")
    elif p == "sensor" and ref[0] in "UR" and ref != "U13":
        n = int(ref[1:])
        if ref[0] == "R":
            i, k = (n - 1) // 2, (n - 1) % 2       # R ganjil = 220 (anoda LED), genap = 10k (kolektor)
        else:
            i, k = n - 1, None
        cx, cy = SENSOR_C[i]
        (tx, ty), (nx, ny) = arah[i]
        if ref[0] == "U":
            # QRE1113GR di sisi bawah, tengah kemasan di titik sensor: LED (pad 1/2) di depan, fototransistor (3/4) di
            # belakang, sumbu panjang (pad 1-2) sepanjang busur
            fp.SetPosition(gu.K(cx, cy))
            sudut = math.degrees(math.atan2(ty, tx))
            terbaik = None
            for r in [sgn * sudut + d for sgn in (1, -1) for d in (0, 90, 180, 270)]:
                fp.SetOrientationDegrees(r)
                pd = pads(fp)
                led = [(pd["1"][0][j] + pd["2"][0][j]) / 2 for j in (0, 1)]
                pt = [(pd["3"][0][j] + pd["4"][0][j]) / 2 for j in (0, 1)]
                d12 = (pd["2"][0][0] - pd["1"][0][0], pd["2"][0][1] - pd["1"][0][1])
                skor = (led[0] - pt[0]) * nx + (led[1] - pt[1]) * ny + abs(d12[0] * tx + d12[1] * ty) / 4
                if terbaik is None or skor > terbaik[0]:
                    terbaik = (skor, r)
            fp.SetOrientationDegrees(terbaik[1])
            pd = pads(fp)                          # sisi busur (+1 = arah singgung) tempat anoda dan kolektor
            SISI_QRE[i] = [1 if (pd[q][0][0] - cx) * tx + (pd[q][0][1] - cy) * ty > 0 else -1 for q in ("1", "3")]
            return
        # resistor di sisi atas, di sisi busur tempat pad QRE pasangannya (220 -> anoda pad 1, 10k -> kolektor pad 3),
        # tegak lurus busur, pad 2 menghadap pad QRE itu (QRE U1..U12 ditempatkan lebih dulu: urutan nama)
        sisi_pad = SISI_QRE[i][0 if k == 0 else 1]
        x, y = cx + sisi_pad * 2.1 * tx, cy + sisi_pad * 2.1 * ty
        sumbu = (nx, ny) if k == 0 else (-nx, -ny)
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
    Papan sensor tanpa nilai (terlalu rapat): U1-U12 = QRE1113GR (LED di depan), R ganjil 220, genap 10k, U13 mux.
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
        if p == "utama":    # sama dengan autoroute/x2_router.py pour: pad SMD menempel penuh, THT thermal
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
        gu.zone_poly(z, [(-60, 0), (60, 0), (60, 145), (-60, 145)])
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(brd(p), b)
    print(f"{p}: GND pour F.Cu + B.Cu")


if __name__ == "__main__":
    main()
