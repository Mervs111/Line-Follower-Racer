"""Tata letak awal PCB LFM X2 rev A (15/11/2026): outline, lubang, semua footprint + net. TANPA jalur dan tanpa pour:
jalur digambar user sendiri di KiCad.

Dijalankan dengan python KiCad (modul pcbnew), bukan py biasa, dari folder repo:
  KPY="C:/Program Files/KiCad/10.0/bin/python.exe"
  "$KPY" hardware/tools/gen_pcb_x2.py tata [--paksa]   buat hardware/lfm-x2/lfm-x2.kicad_pcb dari skematik
  "$KPY" hardware/tools/gen_pcb_x2.py pour             sesudah routing: GND pour F.Cu + B.Cu (jarak 0,5 mm)

`tata` MENIMPA papan, jadi menolak jalan kalau papan sudah berisi jalur (kecuali --paksa). Netlist diekspor sendiri
dari lfm-x2.kicad_sch. Path footprint = UUID simbol, jadi F8 (Update PCB from Schematic) tidak membuat ulang footprint.

Koordinat robot (mm): x ke kanan, y maju, (0, 0) = tengah poros roda; KiCad X = 200 + x, Y = 180,55 - y (sama dengan
proyek PCB lain di repo ini).

Susunan dari belakang ke depan (semua di sisi atas kecuali sensor):
  ekor      y -46..-13   alas pack Li-ion 2S 50 x 30 x 15 + 2 celah strap (tidak ada komponen)
  motor     y -12..12    2 motor N20 di atas PCB (bracket M2), tanpa komponen
  konektor  y 12..19     J1 baterai, J2/J3 motor + encoder
  driver    y 19..41     4 BTN7971B (tab ke belakang, kaki ke depan) + R/C-nya; kiri: saklar daya, kanan: elko + buzzer
  antarmuka y 42..70     OLED di socket (di bawahnya buck 5 V + LDO 3,3 V), 3 tombol di kiri dan 3 di kanan
  MCU       y 70..97     ESP32-WROOM-32E melintang (antena menonjol 5 mm keluar tepi kanan), CH340C + USB-C di kiri,
                         RST/BOOT
  leher     y 97..114    2 lubang skid M3, mux CD74HC4067M
  sensor    y 103..131   busur 12 QRE1113GR + resistornya di sisi BAWAH: salinan persis PCB sensor rev B
"""
import math
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_pcb_utama_v17 as gu  # noqa: E402  (K, netlist, footprint, bentuk, teks)
import kisym  # noqa: E402
import pcbnew  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DIR = os.path.join(ROOT, "hardware", "lfm-x2")
SCH = os.path.join(DIR, "lfm-x2.kicad_sch")
BRD = os.path.join(DIR, "lfm-x2.kicad_pcb")

# ---------------------------------------------------------------- outline
# setengah kanan, dari tengah ekor ke leher; sisi kiri = cermin. (x, y, radius sudut)
HALF = [(0.0, -46.0, 0), (25.5, -46.0, 2), (31.5, -40.0, 3), (31.5, -19.5, 3), (38.0, -13.0, 3), (38.0, 40.0, 5),
        (27.0, 70.0, 6), (27.0, 94.5, 3), (12.5, 104.0, 3), (12.5, 113.57, 0)]
# sayap sensor kanan = outline PCB sensor rev B (hardware/sensor-garis), dari leher (12,5; 113,57) ke hidung (0; 131)
REVB = [("arc", (12.5, 113.57), (13.37, 115.683), (15.476, 116.57)), ("seg", (15.476, 116.57), (18.734, 116.596)),
        ("arc", (18.734, 116.596), (18.948, 116.592), (19.161, 116.577)), ("seg", (19.161, 116.577), (25.125, 115.984)),
        ("arc", (25.125, 115.984), (25.566, 115.915), (25.997, 115.798)), ("seg", (25.997, 115.798), (31.125, 114.085)),
        ("arc", (31.125, 114.085), (31.496, 113.94), (31.851, 113.759)), ("seg", (31.851, 113.759), (33.7, 112.696)),
        ("arc", (33.7, 112.696), (34.416, 111.995), (34.702, 111.034)), ("seg", (34.702, 111.034), (34.948, 104.275)),
        ("arc", (34.948, 104.275), (35.499, 103.417), (36.516, 103.489)), ("seg", (36.516, 103.489), (42.79, 107.832)),
        ("arc", (42.79, 107.832), (43.085, 108.082), (43.326, 108.383)), ("seg", (43.326, 108.383), (46.954, 113.942)),
        ("arc", (46.954, 113.942), (47.182, 114.982), (46.662, 115.911)), ("seg", (46.662, 115.911), (37.972, 123.158)),
        ("arc", (37.972, 123.158), (37.557, 123.46), (37.108, 123.706)), ("seg", (37.108, 123.706), (29.79, 127.128)),
        ("arc", (29.79, 127.128), (29.371, 127.296), (28.936, 127.415)), ("seg", (28.936, 127.415), (20.946, 129.132)),
        ("arc", (20.946, 129.132), (20.824, 129.154), (20.702, 129.169)), ("seg", (20.702, 129.169), (4.438, 130.596)),
        ("seg", (4.438, 130.596), (0.0, 131.0))]
STRAP = (27.5, -38.0, -20.0, 2.5)                 # celah strap baterai: x tengah (cermin kiri/kanan), y0, y1, lebar
# lubang: (x, y, footprint, nama). Semua dicerminkan ke x negatif.
HOLES = [(32.0, 9.0, "MountingHole:MountingHole_2.2mm_M2", "bracket motor"),
         (32.0, -9.0, "MountingHole:MountingHole_2.2mm_M2", "bracket motor"),
         (11.75, 44.0, "MountingHole:MountingHole_2.2mm_M2", "spacer OLED"),
         (4.75, 99.5, "MountingHole:MountingHole_3.2mm_M3", "skid depan")]
OLED = (0.0, 56.0, 27.3, 27.8)                    # modul OLED 0,96" di socket J5: tengah x, y, lebar, panjang
# gambar bantu (Dwgs.User): kotak (x0, x1, y0, y1, teks), dicerminkan kalau cermin = True
BANTU = [(4.0, 37.0, -6.0, 6.0, "motor N20", True), (39.5, 57.5, -17.0, 17.0, "roda 34 x 18", True),
         (-25.0, 25.0, -44.0, -14.0, "pack Li-ion 2S 50 x 30 x 15", False)]

# ---------------------------------------------------------------- penempatan: ref -> (x, y, rotasi)
# titik asal footprint SMD = tengah badan; konektor/saklar/buzzer THT = pin 1
BTN_X, BTN_Y = (-18.0, -6.0, 6.0, 18.0), 25.97     # U6..U9: tab di belakang (dekat J2/J3), kaki ke depan
RC_Y = 39.2                                        # baris R/C di depan kaki BTN7971B, 0805 tegak
PLACE = {
    # daya masuk (kiri): J1 -> Q1 (saklar beban) -> VBAT; SW1 di tepi kiri, tuas keluar ke kiri (depan = hidup)
    "J1": (-29.5, 16.22, 0), "Q1": (-26.5, 22.0, 0), "R1": (-30.6, 20.7, 0), "C1": (-30.6, 22.8, 0),
    "R2": (-30.6, 24.9, 0), "SW1": (-35.5, 33.0, -90),
    "R3": (-28.3, 27.6, 0), "R4": (-28.3, 29.8, 0), "C3": (-28.3, 32.0, 0), "R9": (-28.3, 34.4, 0),
    "LED1": (-28.3, 36.7, 0),
    # konektor motor tepat di belakang tab BTN7971B (pin 1 = M+ di kiri, pin 6 = M- di kanan)
    "J2": (-16.3, 16.22, 0), "J3": (3.8, 16.22, 0),
    "U6": (BTN_X[0], BTN_Y, -90), "U7": (BTN_X[1], BTN_Y, -90), "U8": (BTN_X[2], BTN_Y, -90),
    "U9": (BTN_X[3], BTN_Y, -90),
    # kanan: elko VBAT, buzzer + transistornya
    "C2": (30.6, 25.0, 0), "BZ1": (26.8, 36.2, 0), "Q4": (29.6, 46.6, 0), "R64": (29.6, 49.9, 0),
    "R65": (29.6, 52.0, 0),
    # tombol menu: kiri ATAS / OK / BAWAH, kanan KEMBALI / START / LANJUT (depan ke belakang)
    "SW2": (-20.5, 64.0, 0), "SW5": (-20.5, 56.0, 0), "SW3": (-20.5, 48.0, 0),
    "SW4": (20.5, 64.0, 0), "SW7": (20.5, 56.0, 0), "SW6": (20.5, 48.0, 0),
    # tangga resistor di sisi dalam tiap tombol, pull-up + filter BTN (kiri) dan BTN2 (kanan)
    "R57": (-14.4, 63.5, 90), "R60": (-14.4, 56.0, 90), "R58": (-14.4, 48.6, 90),
    "R59": (14.4, 63.5, 90), "R61": (14.4, 48.6, 90), "R63": (14.4, 54.0, 90), "C22": (14.4, 58.2, 90),
    "R62": (-11.9, 52.0, 90), "C21": (-11.9, 56.2, 90),
    # di bawah OLED, belakang: buck MP1584 (VBAT masuk dari belakang, L1/D1 di kanan)
    "C5": (-7.2, 43.6, 0), "R32": (4.5, 43.6, 0), "C6": (-3.3, 45.6, 0), "U4": (-3.3, 49.6, 180),
    "C4": (-8.4, 49.6, 90), "R5": (-7.0, 53.6, 0), "D1": (3.0, 49.0, 90), "L1": (9.0, 51.0, 90),
    "C7": (9.0, 56.8, 180), "R7": (-2.6, 53.7, 180), "R6": (-2.6, 55.9, 180), "R8": (2.2, 53.7, 0),
    "C8": (2.2, 55.9, 180),
    # di bawah OLED, depan: dioda-OR 5 V dan LDO 3,3 V
    "D2": (8.0, 60.0, 0), "D3": (8.0, 63.8, 0), "C9": (3.0, 61.8, -90), "U3": (-3.0, 61.8, 180),
    "C10": (-9.0, 61.8, 90), "C11": (-11.9, 61.2, 90),
    "J5": (-3.81, 68.65, 90),                      # socket OLED, pin 1 (GND) di kiri
    # MCU: ESP32 melintang, bagian antena (6,2 mm) menonjol 5 mm keluar tepi kanan supaya daerah larangan tembaga di
    # footprint (15 mm kiri-kanan antena, x > 25,8) tidak mengenai tombol kanan dan sayap sensor. USB-C di tepi kiri,
    # CH340C + auto-reset di antaranya.
    "U1": (19.25, 82.5, -90), "J4": (-23.8, 78.0, -90), "R11": (-17.3, 73.6, 90), "R10": (-17.3, 82.4, 90),
    "U2": (-9.0, 78.0, 0), "C12": (-9.0, 84.4, 0), "R15": (0.8, 73.2, 0), "R13": (0.8, 75.5, 0),
    "Q3": (0.8, 78.4, 0), "Q2": (0.8, 82.4, 0), "R12": (0.8, 85.3, 0),
    "SW9": (-21.0, 89.5, 0), "SW8": (-10.2, 89.9, 0),
    "C15": (21.5, 94.4, 0), "C14": (16.5, 94.6, 0), "R14": (16.9, 96.9, 0), "C13": (12.6, 96.9, 0),
    # leher: mux dan kapasitornya di posisi yang sama dengan PCB sensor rev B (U13, C1)
    "U5": (0.0, 113.985, 0), "C20": (7.2, 120.97, 90),
}
# 5 komponen per BTN7971B di baris RC_Y: (jarak x dari tengah chip, pola nama net chip atau None = kapasitor VBAT)
RC_BTN = [(-4.6, None), (-2.3, "IS"), (0.0, "SR"), (2.3, "INH"), (4.6, "IN")]
# busur sensor: posisi PCB sensor rev B (x, y, rotasi; semua di sisi bawah). IR1 = paling kiri dilihat dari atas.
REVB_IR = [(-41.393, 114.719, -140.0), (-35.265, 119.861, -147.5), (-28.014, 123.242, -161.5),
           (-20.189, 124.906, -171.5), (-12.22, 125.603, -175.0), (-4.25, 126.3, -177.5), (4.25, 126.3, 177.5),
           (12.22, 125.603, 175.0), (20.189, 124.906, 171.5), (28.014, 123.242, 161.5), (35.265, 119.861, 147.5),
           (41.393, 114.719, 140.0)]
REVB_R = [(-39.853, 117.317, 130.0), (-42.934, 112.121, 130.0), (-33.398, 122.236, 122.5), (-37.131, 117.487, 122.5),
          (-25.629, 125.095, 108.5), (-30.4, 121.39, 108.5), (-17.518, 126.316, 98.5), (-22.86, 123.495, 98.5),
          (-9.468, 126.847, 95.0), (-14.972, 124.358, 95.0), (-1.446, 127.423, 92.5), (-7.054, 125.177, 92.5),
          (7.141, 127.175, 87.5), (1.359, 125.425, 87.5), (15.146, 126.351, 85.0), (9.293, 124.855, 85.0),
          (23.156, 125.473, 81.5), (17.223, 124.338, 81.5), (31.034, 123.286, 71.5), (24.994, 123.198, 71.5),
          (38.206, 119.173, 57.5), (32.324, 120.549, 57.5), (44.219, 113.653, 50.0), (38.567, 115.785, 50.0)]
# pad pemasang SW1 bawaan KiCad (oval 2,2 x 3,5) hanya 0,25 mm dari kaki 1/3: dikecilkan (lubang 1,5 tetap).
# Jangan "Update Footprints from Library" untuk SW1.
PAD_FIX = {"SW1": {"": (2.0, 3.3)}}
LBL_BTN = {"SW2": "ATAS", "SW5": "OK", "SW3": "BAWAH", "SW4": "KEMBALI", "SW7": "START", "SW6": "LANJUT"}
SILK = [  # (teks, x, y, ukuran, rotasi)
    ("BAT", -34.6, 16.2, 1.0, 90), ("+  -", -28.25, 10.6, 1.0, 0), ("MOTOR KIRI", -10.0, 10.6, 1.0, 0),
    ("MOTOR KANAN", 10.0, 10.6, 1.0, 0), ("ON", -34.6, 38.0, 1.0, 0), ("BOOT", -21.0, 94.2, 1.0, 0),
    ("RST", -10.2, 94.6, 1.0, 0), ("LFM X2 rev A", 0.0, -29.0, 2.0, 0),
]
SILK_B = [("LFM X2 rev A", 0.0, 0.0, 2.0), ("PCB all-in-one, side project LFM 2026", 0.0, -3.5, 1.2)]
# referensi di silkscreen hanya untuk komponen yang punya tempat kosong di sebelahnya; sisanya di lapisan Fab
REF_SILK = {"U1", "U3", "U5", "J1", "J4", "J5", "BZ1"}


def rantai(pts):
    """polyline terbuka [(x, y, r)] -> ('seg', a, b) / ('arc', a, tengah, b); sudut dibulatkan radius r"""
    out, awal = [], pts[0][:2]
    for i in range(1, len(pts) - 1):
        c, a, b, r = pts[i][:2], pts[i - 1][:2], pts[i + 1][:2], pts[i][2]
        u1 = (a[0] - c[0], a[1] - c[1]); l1 = math.hypot(*u1); u1 = (u1[0] / l1, u1[1] / l1)
        u2 = (b[0] - c[0], b[1] - c[1]); l2 = math.hypot(*u2); u2 = (u2[0] / l2, u2[1] / l2)
        half = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))) / 2
        t = r / math.tan(half)
        bis = (u1[0] + u2[0], u1[1] + u2[1]); lb = math.hypot(*bis); bis = (bis[0] / lb, bis[1] / lb)
        ctr = (c[0] + bis[0] * r / math.sin(half), c[1] + bis[1] * r / math.sin(half))
        t1, t2 = (c[0] + u1[0] * t, c[1] + u1[1] * t), (c[0] + u2[0] * t, c[1] + u2[1] * t)
        out.append(("seg", awal, t1))
        out.append(("arc", t1, (ctr[0] - bis[0] * r, ctr[1] - bis[1] * r), t2))
        awal = t2
    out.append(("seg", awal, pts[-1][:2]))
    return out


def outline():
    kanan = rantai(HALF) + REVB
    return kanan + [(s[0],) + tuple((-p[0], p[1]) for p in s[1:]) for s in kanan]


def kotak(b, layer, x0, x1, y0, y1, width=0.1):
    for a, c in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        gu.add_shape(b, layer, "seg", (a, c), width)


def netlist():
    net = os.path.join(tempfile.mkdtemp(), "lfm-x2.net")
    subprocess.run([kisym.KICAD_CLI, "sch", "export", "netlist", "-o", net, SCH], check=True, capture_output=True)
    return gu.read_netlist(net)


def tata(paksa):
    comps, nets = netlist()
    place = dict(PLACE)
    bawah = set()
    di_net = {}
    for (ref, pin), n in nets.items():
        di_net.setdefault(n, []).append((ref, pin))

    def r_di(net):                                  # resistor yang salah satu kakinya di net ini -> (ref, pin)
        return next((r, p) for r, p in di_net[net] if r[0] == "R" and r[1:].isdigit())

    # R/C tiap BTN7971B: kaki yang ke chip (atau ke VBAT) menghadap belakang, ke arah kaki chip
    for i, cx in enumerate(BTN_X):
        u = f"U{6 + i}"
        for dx, apa in RC_BTN:
            ref, pin = (f"C{16 + i}", "1") if apa is None else r_di(f"{u}_{apa}")
            place[ref] = (cx + dx, RC_Y, 90 if pin == "1" else -90)
    # busur sensor = PCB sensor rev B. Urutan referensi X2: IRn, R(31+2n) = 220 ohm, R(32+2n) = 10k.
    for i in range(12):
        place[f"IR{i + 1}"] = REVB_IR[i]
        for k in (0, 1):
            ref = f"R{33 + 2 * i + k}"
            x, y, rot = REVB_R[2 * i + k]
            # rev B: pad 1 = +5V (220) / Sn (10k). Kalau di X2 pad 1 = +3V3, putar 180 supaya polanya sama.
            place[ref] = (x, y, rot + (180 if nets[(ref, "1")] == "+3V3" else 0))
        bawah |= {f"IR{i + 1}", f"R{33 + 2 * i}", f"R{34 + 2 * i}"}
    kurang = sorted(set(comps) - set(place))
    if kurang:
        raise SystemExit(f"belum punya posisi: {kurang}")

    # footprint dimuat sebelum papan dibuat: di KiCad 10 FootprintLoad gagal sesudah board ada
    loaded = {ref: gu.load_fp(c["fp"]) for ref, c in comps.items()}
    lubang = []
    for x, y, fpid, nama in HOLES:
        for sx in (1, -1):
            lubang.append((sx * x, y, gu.load_fp(fpid), nama))
    if os.path.exists(BRD):
        lama = pcbnew.LoadBoard(BRD)
        if len(lama.GetTracks()) and not paksa:
            raise SystemExit(f"{BRD} sudah berisi {len(lama.GetTracks())} jalur/via: tidak ditimpa (pakai --paksa)")
    b = pcbnew.NewBoard(BRD)
    tb = b.GetTitleBlock()
    tb.SetTitle("LFM X2 - PCB all-in-one full SMD"); tb.SetRevision("A"); tb.SetDate("2026-11-15")
    tb.SetComment(0, "Side project LFM (di luar RAB PjBL)")
    tb.SetComment(1, "Tata letak awal dari hardware/tools/gen_pcb_x2.py, jalur digambar sendiri")

    for s in outline():
        gu.add_shape(b, pcbnew.Edge_Cuts, s[0], s[1:])
    sx, y0, y1, w = STRAP
    for x in (sx, -sx):                              # celah strap: ujung setengah lingkaran
        r = w / 2
        gu.add_shape(b, pcbnew.Edge_Cuts, "seg", ((x - r, y0 + r), (x - r, y1 - r)))
        gu.add_shape(b, pcbnew.Edge_Cuts, "seg", ((x + r, y0 + r), (x + r, y1 - r)))
        gu.add_shape(b, pcbnew.Edge_Cuts, "arc", ((x - r, y1 - r), (x, y1), (x + r, y1 - r)))
        gu.add_shape(b, pcbnew.Edge_Cuts, "arc", ((x - r, y0 + r), (x, y0), (x + r, y0 + r)))

    netobj = {}

    def net(name):
        if name not in netobj:
            n = pcbnew.NETINFO_ITEM(b, name)
            b.Add(n)
            netobj[name] = n
        return netobj[name]

    for ref, c in sorted(comps.items()):
        fp = loaded[ref]
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        if c.get("datasheet") and c["datasheet"] != "~":
            fp.SetField("Datasheet", c["datasheet"])
        fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        x, y, rot = place[ref]
        fp.SetPosition(gu.K(x, y))
        fp.SetOrientationDegrees(rot)
        if ref not in REF_SILK:
            fp.Reference().SetLayer(pcbnew.F_Fab)
        if ref in ("SW1", "J4"):                    # badan menonjol keluar tepi papan: garis silk pindah ke Fab
            for g in fp.GraphicalItems():
                if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() != "PCB_FIELD":
                    g.SetLayer(pcbnew.F_Fab)
        b.Add(fp)
        if ref == "U1":                             # via termal bor 0,2 mm di pad bawah modul: di bawah bor minimum
            kecil = [p for p in fp.Pads() if p.GetNumber() == "39" and p.GetDrillSize().x > 0]   # tempat cetak (0,6)
            gu._BUANG.extend(kecil)
            for p in kecil:
                fp.Remove(p)
        if ref in bawah:                            # (Flip sesudah Add: sebelum itu segfault)
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            fp.SetOrientationDegrees(rot)
        for p in fp.Pads():
            if p.GetNumber() in PAD_FIX.get(ref, {}):
                w, h = PAD_FIX[ref][p.GetNumber()]
                p.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(pcbnew.FromMM(w), pcbnew.FromMM(h)))
            name = nets.get((ref, p.GetNumber()))
            if name:
                p.SetNet(net(name))
    for i, (x, y, fp, nama) in enumerate(lubang, 1):
        fp.SetReference(f"H{i}")
        fp.SetValue(nama)
        fp.SetPosition(gu.K(x, y))
        fp.Reference().SetLayer(pcbnew.F_Fab)
        fp.SetBoardOnly(True)
        b.Add(fp)

    for txt, x, y, size, rot in SILK:
        gu.add_text(b, pcbnew.F_SilkS, txt, x, y, size, rot, 0.2 if size <= 1.2 else 0.3)
    for ref, txt in LBL_BTN.items():                # nama tombol tegak di sisi luar tombol
        x, y, _ = PLACE[ref]
        gu.add_text(b, pcbnew.F_SilkS, txt, 27.0 if x > 0 else -27.0, y, 1.0, 90, 0.2)
    for txt, x, y, size in SILK_B:
        gu.add_text(b, pcbnew.B_SilkS, txt, x, y, size, 0, 0.2 if size <= 1.2 else 0.3, mirror=True)
    for i in range(12):                             # nomor sensor di sisi atas, tepat di atas tiap sensor
        x, y, rot = REVB_IR[i]
        gu.add_text(b, pcbnew.F_SilkS, str(i + 1), x, y, 1.0, 0, 0.2)
    ox, oy, ow, oh = OLED
    kotak(b, pcbnew.F_Fab, ox - ow / 2, ox + ow / 2, oy - oh / 2, oy + oh / 2)
    gu.add_text(b, pcbnew.F_Fab, "OLED 0,96 (di socket J5)", ox, oy + oh / 2 - 1.5, 1.0)
    for x0, x1, y0, y1, txt, cermin in BANTU:
        for s in ((1, -1) if cermin else (1,)):
            kotak(b, pcbnew.Dwgs_User, s * x0, s * x1, y0, y1, 0.15)
            gu.add_text(b, pcbnew.Dwgs_User, txt, s * (x0 + x1) / 2, (y0 + y1) / 2, 1.2)

    pcbnew.SaveBoard(BRD, b)
    # kertas A3 (papan 177 mm tidak muat di A4 pada koordinat ini); PAGE_INFO tidak bisa diatur dari python KiCad 10
    teks = open(BRD, encoding="utf8").read()
    open(BRD, "w", encoding="utf8", newline="\n").write(teks.replace('(paper "A4")', '(paper "A3")', 1))
    n_bawah = sum(1 for f in b.GetFootprints() if f.IsFlipped())
    print(f"ditulis {BRD}: {len(comps)} komponen ({n_bawah} di sisi bawah) + {len(lubang)} lubang, {len(netobj)} net, "
          f"0 jalur")


def pour():
    """GND pour F.Cu + B.Cu sesudah routing (jarak ke pour 0,5 mm, aturan tempat cetak)"""
    b = pcbnew.LoadBoard(BRD)
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
        gu.zone_poly(z, [(-50, -50), (50, -50), (50, 135), (-50, 135)])
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(BRD, b)
    print("GND pour F.Cu + B.Cu")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tata":
        tata("--paksa" in sys.argv)
    elif len(sys.argv) > 1 and sys.argv[1] == "pour":
        pour()
    else:
        raise SystemExit(__doc__)
