# Model 3D Robot Line Tracer Micro v14 (20/10/2026): rombak sensor (keputusan user 20/10):
# - 12 pasang LED superbright MERAH + fototransistor bening, keduanya SMD 1206, di sisi bawah PCB sensor bentuk
#   capit (posisi keputusan 15/10: X +-5, +-15 di 8 mm; +-25..55 di 18..48 mm dari tepi depan). PCB sensor tipis,
#   4,8 mm dari lantai, dengan masker 3D print (jendela per LED/fototransistor + pelindung cahaya).
# - MCP23017 + 12 LED indikator DIHAPUS: bacaan 12 sensor ditampilkan sebagai bar di OLED.
# - Roda O34 (sesuai RAB): PCB utama 12 mm dari lantai, celah ke PCB sensor 4 mm, jadi modul mux (socket) berada di
#   palm PCB sensor di depan hidung PCB utama dan kelihatan.
# - PCB utama sama dengan v13 (ESP32 di socket di atas, OLED 0,96" di depannya, tombol A/B, TB6612 di bahu kanan).
# - Penahan depan: skid nilon (ball caster tidak muat di bawah PCB sensor yang rendah).
# Sumbu: X kanan, Y maju, Z atas; nol = lantai di bawah tengah poros roda.
import json, math, os, sys
import cadquery as cq
from cadquery.occ_impl.exporters.assembly import exportAssembly

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
for d in ("step", "stl", "dxf"):
    os.makedirs(f"{OUT}/{d}", exist_ok=True)

# ------------------------------ ukuran (mm) ------------------------------
D_RODA = 34.0                 # roda N20 O34 (RAB); lebar 12 dimodelkan, ukur roda yang dibeli
R_W, W_W = D_RODA / 2, 12.0
WX0 = 39.5                    # sisi dalam roda (holder baterai 76 mm muat di antara roda)
AX_Z = R_W                    # tinggi poros
T = 1.6                       # tebal PCB
TOP = AX_Z - 5.0              # 12: motor N20 (tinggi 10) duduk langsung di atas PCB utama
PCB_Z = TOP - T               # 10,4: sisi bawah PCB utama
SB_Z = 4.8                    # sisi bawah PCB sensor: muka LED/fototransistor SMD (tinggi 1,1) +-3,7 mm dari lantai
SZ_TOP = SB_Z + T             # 6,4; celah ke PCB utama 4,0 = spacer nilon M3 x 4
F = 139.5                     # tepi depan PCB sensor (hidung PCB utama di Y 91 = 48,5 mm di belakang tepi depan)
TRAY_Z0 = TOP + 10.0          # 22: alas dudukan baterai menekan motor dari atas
TRAY_Z1 = TRAY_Z0 + 2.0
HOLD = (76.0, 42.0, 20.0)     # holder 2x18650
SOCK = 8.5                    # socket header female (OLED, TB6612, ESP32, mux bisa dicabut)
WING_Z, WING_TILT, WING_PIV = 46.9, 4.0, -10.0   # sayap: tinggi sisi bawah di Y pivot, sudut (ekor naik)
WING_TE = -34.0               # tepi belakang sayap

parts = []    # (nama, shape, material, grup)
export = {}   # nama file -> (shape, jenis)


def add(name, wp, mat, group="base"):
    if wp is None:
        return None
    vals = wp.vals() if isinstance(wp, cq.Workplane) else [wp]
    solids = [v for v in vals if isinstance(v, cq.Shape)]
    shape = solids[0] if len(solids) == 1 else cq.Compound.makeCompound(solids)
    parts.append((name, shape, mat, group))
    return shape


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cbox(cx, cy, w, h, z0, z1, ang=0.0):
    """kotak di tengah (cx, cy), diputar ang derajat terhadap sumbu Z"""
    return (cq.Workplane("XY").box(w, h, z1 - z0).rotate((0, 0, 0), (0, 0, 1), ang)
            .translate((cx, cy, (z0 + z1) / 2)))


def cyl_x(x0, x1, yc, zc, r):
    return cq.Workplane("YZ").circle(r).extrude(x1 - x0).translate((x0, yc, zc))


def cyl_y(y0, y1, xc, zc, r):
    return cq.Workplane("XZ").circle(r).extrude(-(y1 - y0)).translate((xc, y0, zc))


def cyl_z(xc, yc, z0, h, r):
    return cq.Workplane("XY").circle(r).extrude(h).translate((xc, yc, z0))


def hexnut(xc, yc, z0, h, s=5.5):
    return cq.Workplane("XY").polygon(6, s / math.cos(math.pi / 6)).extrude(h).translate((xc, yc, z0))


def U(a, b):
    if b is None:
        return a
    return b if a is None else a.union(b)


def try_fillet(wp, sel, r):
    try:
        return wp.edges(sel).fillet(r)
    except Exception:
        return wp


def text(s, size, cx, cy, z, ang=0.0):
    try:
        t = cq.Workplane("XY").text(s, size, 0.06, font="DejaVu Sans", kind="bold", halign="center", valign="center")
        return t.rotate((0, 0, 0), (0, 0, 1), ang).translate((cx, cy, z))
    except Exception:
        return None


def silk_border(pts, z, inset=1.0, lw=0.35):
    """garis silkscreen mengikuti tepi papan (seperti tepi putih PCB Ichiduino)"""
    try:
        a = cq.Workplane("XY").polyline(pts).close().offset2D(-inset, "arc").extrude(0.05)
        b = cq.Workplane("XY").polyline(pts).close().offset2D(-(inset + lw), "arc").extrude(0.2).translate((0, 0, -0.1))
        return a.cut(b).translate((0, 0, z))
    except Exception:
        return None


# ============================== PCB SENSOR (capit/jangkar, 12 pasang LED merah + fototransistor SMD) ==============================
# koordinat lokal (u, v): u = X, v = jarak ke belakang dari tepi depan (sama dengan sumbu Y KiCad)
PLATE_R = [(19, 0), (60, 41), (60, 54), (57.5, 56.5), (57.5, 62), (46, 62), (22, 38), (22, 64), (17, 80)]
PLATE_UV = PLATE_R + [(-u, v) for u, v in reversed(PLATE_R)]
PLATE_PTS = [(u, F - v) for u, v in PLATE_UV]
SENS_UV = sorted([(s * a, b) for a, b in ((5, 8), (15, 8), (25, 18), (35, 28), (45, 38), (55, 48)) for s in (-1, 1)])
SB_HOLES_UV = [(-17, 56), (17, 56), (-12, 76), (12, 76)]          # spacer ke PCB utama (di batang, di bawah hidung)
SKID_UV = [(-49, 58), (49, 58)]                                    # baut nilon anti-jungkit di ujung tanduk
CASTER_UV = (0, 30)                                                # skid nilon penahan depan (pengganti ball caster)
MASK_UV = [(0, 8), (-30, 23), (30, 23)]                            # baut M2 masker
PAIR = 1.9                                                         # LED di depan, fototransistor di belakang (+-1,9 mm)


def uv(u, v):
    return (u, F - v)


sb = cq.Workplane("XY").polyline(PLATE_PTS).close().extrude(T).translate((0, 0, SB_Z))
sb = try_fillet(sb, "|Z", 1.5)
for hu, hv in SB_HOLES_UV + SKID_UV + [CASTER_UV]:
    x, y = uv(hu, hv)
    sb = sb.cut(cyl_z(x, y, SB_Z - 1, T + 2, 1.6))
for hu, hv in MASK_UV:
    x, y = uv(hu, hv)
    sb = sb.cut(cyl_z(x, y, SB_Z - 1, T + 2, 1.1))
sb_board = add("PCB sensor", sb, "pcb")
export["pcb_sensor"] = (sb_board, "pcb")

led = led_dot = pt = pt_dot = smd = None
for k, (u, v) in enumerate(SENS_UV):
    x, y = uv(u, v)
    # SMD 1206 (3,2 x 1,6 x 1,1) di sisi bawah, sisi panjang melintang; LED merah di depan, fototransistor di belakang
    led = U(led, box(x - 1.6, x + 1.6, y + PAIR - 0.8, y + PAIR + 0.8, SB_Z - 1.1, SB_Z))
    led_dot = U(led_dot, cyl_z(x, y + PAIR, SB_Z - 1.15, 0.06, 0.55))
    pt = U(pt, box(x - 1.6, x + 1.6, y - PAIR - 0.8, y - PAIR + 0.8, SB_Z - 1.1, SB_Z))
    pt_dot = U(pt_dot, cyl_z(x, y - PAIR, SB_Z - 1.15, 0.06, 0.55))
    for dx in (-2, 2):                                                  # R330 (LED) + R pull-up, 7,5 mm di belakang
        smd = U(smd, box(x + dx - 0.63, x + dx + 0.63, y - 8.5, y - 6.5, SZ_TOP, SZ_TOP + 0.5))
add("LED sensor merah SMD 1206 x12", led, "led_smd")
add("LED sensor chip", led_dot, "led_red")
add("Fototransistor SMD 1206 x12", pt, "pt_clear")
add("Fototransistor chip", pt_dot, "black_plastic")
add("Resistor SMD sensor", smd, "resistor_smd")

silk = silk_border(PLATE_PTS, SZ_TOP)
for k, (u, v) in enumerate(SENS_UV):                                    # tanda posisi sensor di sisi atas
    x, y = uv(u, v)
    try:
        silk = U(silk, cq.Workplane("XY").circle(2.4).circle(2.05).extrude(0.05).translate((x, y, SZ_TOP)))
    except Exception:
        pass
    silk = U(silk, text(str(k + 1), 1.4, x + (3.6 if u > 0 else -3.6), y + 2.6, SZ_TOP))
silk = U(silk, text("LINE TRACER MICRO", 2.2, *uv(31, 40), SZ_TOP, -45))
silk = U(silk, text("SENSOR 12 TITIK", 2.2, *uv(-31, 40), SZ_TOP, 45))
add("Silkscreen sensor", silk, "silk")
gold = None
for hu, hv in SB_HOLES_UV + SKID_UV + [CASTER_UV]:
    x, y = uv(hu, hv)
    gold = U(gold, cyl_z(x, y, SZ_TOP, 0.05, 2.8).cut(cyl_z(x, y, SZ_TOP - 1, 2, 1.6)))
add("Pad lubang sensor", gold, "gold")

# modul mux CD74HC4067 (socket) di palm, sisi atas, di depan hidung PCB utama (celah antar papan cuma 4 mm)
mx0, mx1 = -20.3, 20.3
my0, my1 = F - 36.8, F - 19.0
add("Mux socket", box(-20.32, 20.32, my1 - 2.54, my1, SZ_TOP, SZ_TOP + SOCK)
    .union(box(-10.16, 10.16, my0, my0 + 2.54, SZ_TOP, SZ_TOP + SOCK)), "black_plastic")
add("Modul mux PCB", box(mx0, mx1, my0, my1, SZ_TOP + SOCK, SZ_TOP + SOCK + T), "pcb_blue")
add("Modul mux chip", box(-7.5, 7.5, my0 + 6.0, my0 + 11.5, SZ_TOP + SOCK + T, SZ_TOP + SOCK + T + 1.4), "black_plastic")
j1y0, j1y1 = F - 46.9, F - 38.0                    # J1 di pangkal batang, tepat di depan hidung PCB utama


def idc(y0, y1, z0, key_front):
    b = box(-11.4, 11.4, y0, y1, z0, z0 + 9.0).cut(box(-8.9, 8.9, y0 + 1.4, y1 - 1.4, z0 + 2.0, z0 + 9.5))
    ky = (y1 - 0.5, y1 + 0.5) if key_front else (y0 - 0.5, y0 + 0.5)
    return b.cut(box(-2.25, 2.25, ky[0], ky[1], z0 + 2.0, z0 + 9.5))


add("Box header IDC J1", idc(j1y0, j1y1, SZ_TOP, False), "black_plastic")

# skid nilon penahan depan (menyentuh lantai) + 2 skid anti-jungkit di ujung tanduk (1 mm di atas lantai)
for (hu, hv), z0 in [(CASTER_UV, 0.0)] + [(p, 1.0) for p in SKID_UV]:
    x, y = uv(hu, hv)
    add("Baut nilon kepala", cq.Workplane("XY").sphere(2.9).translate((x, y, SZ_TOP)).intersect(
        box(x - 3, x + 3, y - 3, y + 3, SZ_TOP, SZ_TOP + 2.2)), "nylon")
    dome = cq.Workplane("XY").sphere(3.5).translate((x, y, z0 + 3.5)).intersect(box(x - 4, x + 4, y - 4, y + 4, z0, z0 + 2.0))
    add("Skid nilon", dome.union(cyl_z(x, y, z0 + 1.5, SB_Z - z0 - 1.5, 2.5)), "nylon")
for hu, hv in MASK_UV:
    x, y = uv(hu, hv)
    add("Baut M2 masker", cyl_z(x, y, SZ_TOP, 1.3, 1.9), "chrome")

# masker sensor (3D print, risiko R1 di charter): pelat hitam 2,8 mm di bawah baris sensor dengan jendela terpisah
# untuk tiap LED dan fototransistor (sekat 1,8 mm mencegah cahaya LED langsung masuk ke fototransistor, sekaligus
# menahan cahaya ruangan); 2 mm di atas lantai; dibaut M2 dari atas di 3 titik
SK_Z0 = 2.0


def band_pts(d, cap):
    """poligon pita selebar 2d di sekitar baris sensor (tengah lurus + sayap 45 derajat), ujung diperpanjang cap"""
    r2 = math.sqrt(2)
    eo = (55 + (d + cap) / r2, 48 + (cap - d) / r2)
    p1 = (15 + (r2 - 1) * d, 8 - d)
    ei = (55 + (cap - d) / r2, 48 + (cap + d) / r2)
    p2 = (15 - (r2 - 1) * d, 8 + d)
    pts = [eo, p1, (-p1[0], p1[1]), (-eo[0], eo[1]), (-ei[0], ei[1]), (-p2[0], p2[1]), p2, ei]
    return [(u, F - v) for u, v in pts]


def prism(pts, z0, z1, inset=0.0):
    w = cq.Workplane("XY").polyline(pts).close()
    if inset:
        w = w.offset2D(-inset, "intersection")
    return w.extrude(z1 - z0).translate((0, 0, z0))


skirt = prism(band_pts(5.5, 5.0), SK_Z0, SB_Z).intersect(prism(PLATE_PTS, SK_Z0 - 1, SB_Z + 1, 0.3))
skirt = try_fillet(skirt, "|Z", 0.5)
for u, v in SENS_UV:
    x, y = uv(u, v)
    for dy in (PAIR, -PAIR):
        skirt = skirt.cut(box(x - 1.8, x + 1.8, y + dy - 1.0, y + dy + 1.0, SK_Z0 - 1, SB_Z + 1))
for hu, hv in MASK_UV:
    x, y = uv(hu, hv)
    skirt = skirt.cut(cyl_z(x, y, SK_Z0 - 1, SB_Z, 0.8))                # lubang pilot baut M2
sk = add("Masker sensor (3D print)", skirt, "print", "shield")
export["cetak_masker_sensor"] = (sk, "print")

for hu, hv in SB_HOLES_UV:
    x, y = uv(hu, hv)
    add("Spacer nilon 4 mm", cyl_z(x, y, SZ_TOP, PCB_Z - SZ_TOP, 2.5).cut(cyl_z(x, y, SZ_TOP - 1, 6, 1.6)), "nylon")
    add("Baut M3", cyl_z(x, y, TOP, 1.8, 2.75), "chrome")
    add("Mur M3", hexnut(x, y, SB_Z - 2.4, 2.4), "chrome")

# ============================== PCB UTAMA ==============================
# bagian belakang selebar celah antar roda (74), "bahu" 100 di depan roda, hidung menutupi tengah PCB sensor
# (sisi atas PCB sensor di situ cuma resistor/LED setinggi < 1 mm; celah antar papan 4 mm)
MAIN_R = [(32, -30), (37, -25), (37, 22), (48, 24), (50, 26), (50, 44), (42, 56), (30, 72), (16, 91)]
MAIN_PTS = [(x, y) for x, y in MAIN_R] + [(-x, y) for x, y in reversed(MAIN_R)]
HOLES_MAIN = [uv(u, v) for u, v in SB_HOLES_UV] + [(sx * 33, sy * 20) for sx in (-1, 1) for sy in (-1, 1)]
main = cq.Workplane("XY").polyline(MAIN_PTS).close().extrude(T).translate((0, 0, PCB_Z))
main = try_fillet(main, "|Z", 2.5)
for hx, hy in HOLES_MAIN:
    main = main.cut(cyl_z(hx, hy, PCB_Z - 1, T + 2, 1.6))
for s in (-1, 1):                                    # celah untuk piringan encoder N20 (lebih besar dari badan motor)
    main = main.cut(box(min(s * 10.2, s * 13.9), max(s * 10.2, s * 13.9), -6.6, 6.6, PCB_Z - 1, TOP + 1))
main_board = add("PCB utama", main, "pcb")
export["pcb_utama"] = (main_board, "pcb")
gold = None
for hx, hy in HOLES_MAIN:
    gold = U(gold, cyl_z(hx, hy, TOP, 0.05, 2.8).cut(cyl_z(hx, hy, TOP - 1, 2, 1.6)))
add("Pad lubang utama", gold, "gold")
silk = silk_border(MAIN_PTS, TOP)
BTN_Y = 66.0
for t in (text("A", 2.0, -29.5, BTN_Y, TOP), text("B", 2.0, 29.5, BTN_Y, TOP),
          text("LTM", 2.0, 0, -25.5, TOP), text("v14", 1.4, 0, -28.2, TOP)):
    silk = U(silk, t)
for x in (-22, 22):
    try:
        silk = U(silk, cq.Workplane("XY").circle(4.6).circle(4.25).extrude(0.05).translate((x, BTN_Y, TOP)))
    except Exception:
        pass
add("Silkscreen utama", silk, "silk")

# ---------- J5 (kabel pita ke PCB sensor) di hidung ----------
J5Y0, J5Y1 = 81.8, 90.7
add("Box header IDC J5", idc(J5Y0, J5Y1, TOP, True), "black_plastic")

# ---------- OLED 0,96" (header di depan, layar terbaca dari belakang robot), di depan ESP32 ----------
oz = TOP + SOCK
OX, OY0 = 13.65, 53.5
OY1 = OY0 + 27.8
add("OLED socket", box(-5.08, 5.08, OY1 - 2.5, OY1 + 0.04, TOP, oz), "black_plastic")
for x in (-11.65, 11.65):
    add("OLED standoff", cyl_z(x, OY0 + 1.9, TOP, SOCK, 1.6), "nylon")
add("OLED PCB", box(-OX, OX, OY0, OY1, oz, oz + 1.2), "pcb")
add("OLED kaca", box(-13.35, 13.35, OY0 + 1.8, OY0 + 21.1, oz + 1.2, oz + 2.6), "glass")
add("OLED flex", box(-6.0, 6.0, OY0 + 0.3, OY0 + 1.9, oz + 1.2, oz + 1.5), "flex")
gz = oz + 2.61
bars = None
for i, w_ in enumerate((14, 18, 11, 16)):
    y = OY0 + 17.0 - i * 3.3
    bars = U(bars, box(-9.6, -9.6 + w_, y - 0.8, y + 0.8, gz, gz + 0.02))
bars = bars.union(box(-10.9, -10.2, OY0 + 12.9, OY0 + 14.3, gz, gz + 0.02))
add("OLED tampilan", bars, "screen")
for x in (-11.65, 11.65):
    for y in (OY0 + 1.9, OY0 + 25.9):
        add("OLED lubang", cyl_z(x, y, oz + 1.2, 0.05, 1.1), "gold")

# ---------- ESP32 DevKit melintang di socket, di depan dudukan baterai (USB ke kiri, mudah dicabut) ----------
EY0, EY1 = 24.5, 52.8
ey = (EY0 + EY1) / 2
for yr in (ey - 12.7, ey + 12.7):
    add("ESP32 socket", box(-19.05, 19.05, yr - 1.27, yr + 1.27, TOP, TOP + SOCK), "black_plastic")
ez = TOP + SOCK + T                # sisi atas PCB DevKit
add("ESP32 PCB", box(-25.75, 25.75, EY0, EY1, TOP + SOCK, ez), "pcb_dark")
add("ESP32 modul", box(1.25, 19.25, ey - 9, ey + 9, ez, ez + 3.1), "shield")
add("ESP32 antena", box(19.25, 25.75, ey - 9, ey + 9, ez, ez + 0.8), "pcb_dark")
add("ESP32 USB", box(-26.5, -21.0, ey - 3.8, ey + 3.8, ez, ez + 2.7), "shield")
add("ESP32 chip", box(-15, -10, ey - 2.5, ey + 2.5, ez, ez + 1.2).union(box(-6, -2, ey + 4, ey + 7, ez, ez + 1.6)),
    "black_plastic")
add("ESP32 tombol", box(-19, -16, EY0 + 2, EY0 + 5, ez, ez + 1.6).union(box(-19, -16, EY1 - 5, EY1 - 2, ez, ez + 1.6)),
    "shield")

# ---------- TB6612 (diputar 90 derajat, di socket, di bahu kanan) ----------
TBX0, TBX1, TBY0, TBY1 = 28.0, 48.3, 25.0, 45.3
tby = (TBY0 + TBY1) / 2
for yr in (tby - 7.62, tby + 7.62):
    add("TB6612 socket", box(TBX0, TBX1, yr - 1.27, yr + 1.27, TOP, TOP + SOCK), "black_plastic")
add("TB6612 PCB", box(TBX0, TBX1, TBY0, TBY1, TOP + SOCK, TOP + SOCK + T), "pcb_purple")
add("TB6612 chip", cbox((TBX0 + TBX1) / 2, tby, 5.5, 6.5, TOP + SOCK + T, TOP + SOCK + T + 1.1), "black_plastic")

# ---------- UI: tombol (tutup bulat hitam seperti Ichiduino), buzzer, saklar ----------
for x in (-22, 22):
    add("Tombol", box(x - 3, x + 3, BTN_Y - 3, BTN_Y + 3, TOP, TOP + 3.5), "black_plastic")
    add("Tombol tutup", try_fillet(cyl_z(x, BTN_Y, TOP + 3.5, 3.2, 2.6), ">Z", 0.6), "cap_black")
bz = cyl_z(38, 51.5, TOP, 9.5, 6).cut(cyl_z(38, 51.5, TOP + 8.5, 2, 1.2))
add("Buzzer", try_fillet(bz, ">Z", 0.6), "black_plastic")
add("Saklar", box(-50.0, -45.6, 26.0, 34.6, TOP, TOP + 4.4), "shield")      # tepi kiri bahu, di depan roda
add("Saklar tuas", box(-54.0, -50.0, 29.3, 31.3, TOP + 1.4, TOP + 3.0), "black_plastic")
add("Elko C1 100uF", cyl_z(-38, 50.0, TOP + 0.3, 10.7, 3.15), "elko")
add("Elko C1 tutup", cyl_z(-38, 50.0, TOP + 11.0, 0.15, 2.85), "shield")
to92 = cyl_z(28.5, 54.0, TOP + 3.0, 4.5, 2.3).intersect(box(26.1, 30.9, 52.9, 56.4, TOP + 2.9, TOP + 7.6))
add("Transistor S8050", to92, "black_plastic")
res = None
for xc, yc, along_y in ((26.0, 48.5, 0), (26.0, 46.0, 0), (-22.0, 59.5, 0), (22.0, 59.5, 0),     # R3 R4 R5 R6
                        (0.0, -26.0, 0), (0.0, -28.4, 0)):                                       # R1 R2
    r_ = cyl_y(yc - 3.15, yc + 3.15, xc, TOP + 1.25, 1.25) if along_y else cyl_x(xc - 3.15, xc + 3.15, yc, TOP + 1.25, 1.25)
    res = U(res, r_)
add("Resistor THT", res, "resistor")
add("Dioda 1N5819", cyl_x(-2.6, 2.6, -20.0, TOP + 1.35, 1.35), "black_plastic")
add("Dioda 1N5819 cincin", cyl_x(-2.3, -1.6, -20.0, TOP + 1.35, 1.38), "silk")
for x0, x1 in ((-19.9, -6.0), (6.0, 19.9)):        # konektor motor JST PH 6 pin (J2, J3), di bawah dudukan baterai
    add("JST PH motor", box(x0, x1, 13.0, 17.5, TOP, TOP + 6), "jst")

# ---------- di bawah dudukan baterai: MP1584, charger (USB-C ke belakang), konektor baterai ----------
add("MP1584 pin", box(4, 6.5, -28.5, -13.5, TOP, TOP + 2.5).union(box(23.5, 26, -28.5, -13.5, TOP, TOP + 2.5)), "black_plastic")
add("MP1584 PCB", box(4, 26, -29.5, -12.5, TOP + 2.5, TOP + 4.1), "pcb_blue")
add("MP1584 induktor", box(12, 18, -24, -18, TOP + 4.1, TOP + 8.1), "black_plastic")
add("MP1584 trimpot", box(20, 23, -27.5, -24.5, TOP + 4.1, TOP + 6.6), "pot")
add("Charger pin", box(-29, -26.5, -28, -15, TOP, TOP + 2.5).union(box(-6.5, -4, -28, -15, TOP, TOP + 2.5)), "black_plastic")
add("Modul charger 2S", box(-29, -4, -29.5, -13.5, TOP + 2.5, TOP + 4.1), "pcb_blue")
add("USB-C charger", box(-21, -12, -31.0, -23.7, TOP + 4.1, TOP + 7.3), "shield")
add("JST XH baterai", box(27.5, 33.4, -29.8, -24.4, TOP, TOP + 7.0), "jst")

# ---------- sisi bawah PCB utama: BMS ----------
add("BMS 2S", box(-35, -5, -28, -17, PCB_Z - 2.4, PCB_Z), "pcb_green")

# ---------- kabel pita 12 pin: J5 (PCB utama) -> J1 (PCB sensor) ----------
RB_W = 15.2


def ribbon(p0, p3, rise, n=24):
    p1 = (p0[0], p0[1], p0[2] + rise)
    p2 = (p3[0], p3[1], p3[2] + rise)

    def bez(t):
        return tuple((1 - t) ** 3 * p0[i] + 3 * (1 - t) ** 2 * t * p1[i] + 3 * (1 - t) * t ** 2 * p2[i] + t ** 3 * p3[i]
                     for i in range(3))
    wires = []
    for k in range(n + 1):
        t = k / n
        c = bez(t)
        a, b = bez(min(1, t + 1e-3)), bez(max(0, t - 1e-3))
        tan = [a[i] - b[i] for i in range(3)]
        L = math.sqrt(sum(q * q for q in tan))
        tan = [q / L for q in tan]
        nrm = (0.0, -tan[2], tan[1])          # lebar kabel tetap searah X; tebal tegak lurus lintasan
        pts = [(c[0] + sw * RB_W / 2, c[1] + sn * 0.5 * nrm[1], c[2] + sn * 0.5 * nrm[2]) for sw, sn in
               ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        wires.append(cq.Wire.makePolygon([cq.Vector(*q) for q in pts], close=True))
    return cq.Solid.makeLoft(wires)


add("Kabel pita 12 pin", ribbon((0.0, (J5Y0 + J5Y1) / 2, TOP + 9.0), (0.0, (j1y0 + j1y1) / 2, SZ_TOP + 9.0), 11.0),
    "ribbon")

# ============================== PENGGERAK ==============================
for s in (-1, 1):
    def X(a, b):
        return tuple(sorted((s * a, s * b)))
    x0, x1 = X(28.5, 37.5)
    add("Gearbox N20", box(x0, x1, -6, 6, AX_Z - 5, AX_Z + 5), "gearbox")
    x0, x1 = X(13.5, 28.5)
    can = cyl_x(x0, x1, 0, AX_Z, 6).intersect(box(x0 - 1, x1 + 1, -7, 7, AX_Z - 5, AX_Z + 5))
    add("Motor N20", can, "steel")
    x0, x1 = X(12.5, 13.5)
    add("Tutup motor", cyl_x(x0, x1, 0, AX_Z, 5.5), "black_plastic")
    x0, x1 = X(10.9, 12.5)
    add("Encoder PCB", cyl_x(x0, x1, 0, AX_Z, 6.2), "pcb_green")
    x0, x1 = X(8.9, 10.9)
    add("Magnet encoder", cyl_x(x0, x1, 0, AX_Z, 3.0), "black_plastic")
    x0, x1 = X(5.4, 8.9)
    add("Konektor encoder", box(x0, x1, -3, 3, AX_Z - 2, AX_Z + 2), "jst")
    x0, x1 = X(37.5, 48)
    add("As roda", cyl_x(x0, x1, 0, AX_Z, 1.5), "steel")

# ---------- roda O34 x 12: ban merah 2 alur + velg abu-abu (pola lubang seperti Ichiduino) ----------
RIM_R = R_W - 4.5


def wheel(s):
    x0, x1 = sorted((s * WX0, s * (WX0 + W_W)))
    tire = cyl_x(x0, x1, 0, AX_Z, R_W).cut(cyl_x(x0 - 1, x1 + 1, 0, AX_Z, RIM_R))
    tire = try_fillet(tire, "%CIRCLE", 2.2) if False else tire
    try:
        tire = tire.edges(cq.selectors.RadiusNthSelector(1)).fillet(2.0)
    except Exception:
        pass
    xm = (x0 + x1) / 2
    tire = tire.cut(cyl_x(xm - 0.6, xm + 0.6, 0, AX_Z, R_W + 1).cut(cyl_x(xm - 1, xm + 1, 0, AX_Z, R_W - 1.0)))
    xi, xo = (x0, x1) if s > 0 else (x1, x0)          # muka dalam, muka luar
    rim = cyl_x(min(xi, xo + s * 0.0), max(xi, xo), 0, AX_Z, RIM_R + 0.05)
    xr0, xr1 = sorted((xo - s * 2.0, xo + s * 1.0))
    rim = rim.cut(cyl_x(xr0, xr1, 0, AX_Z, RIM_R - 1.2))       # cekungan muka luar
    bos = None
    for k in range(6):
        a = math.radians(30 + 60 * k)
        yc, zc = 6.9 * math.cos(a), AX_Z + 6.9 * math.sin(a)
        xb0, xb1 = sorted((xo - s * 2.0, xo + s * 0.4))
        bos = U(bos, cyl_x(xb0, xb1, yc, zc, 2.0))
    xb0, xb1 = sorted((xo - s * 2.0, xo + s * 0.9))
    bos = bos.union(cyl_x(xb0, xb1, 0, AX_Z, 2.6))
    rim = rim.union(bos)
    return tire, rim


for s in (-1, 1):
    tire, rim = wheel(s)
    add("Ban merah", tire, "tire_red")
    add("Velg", rim, "hub_grey")
    if s > 0:
        export["roda_34x12"] = (tire.union(rim).val(), "beli")

# ============================== DUDUKAN MOTOR + BATERAI (3D print) ==============================
tray = box(-38, 38, -24, 24, TRAY_Z0, TRAY_Z1)
tray = try_fillet(tray, "|Z", 3.0)
ext = box(-14, 14, -34, -22, TRAY_Z0, TRAY_Z1)
ext = try_fillet(ext, "|Z", 2.0)
cradle = tray.union(ext)
for s in (-1, 1):
    x0, x1 = sorted((s * 13.0, s * 38.0))
    sad = box(x0, x1, -11.5, 11.5, TOP, TRAY_Z0 + 0.01)
    sad = sad.cut(box(x0 - 0.5, x1 + 0.5, -6.15, 6.15, TOP - 0.1, TRAY_Z0 + 0.05))   # alur motor (badan 12 x 10)
    cradle = cradle.union(sad)
for sx in (-1, 1):
    for sy in (-1, 1):
        post = cyl_z(sx * 33, sy * 20, TOP, TRAY_Z0 - TOP + 0.01, 3.5).cut(cyl_z(sx * 33, sy * 20, TOP - 1, 8, 1.25))
        cradle = cradle.union(post)
cradle = cradle.union(box(-28, 28, 21.3, 23.8, TRAY_Z1 - 0.01, TRAY_Z1 + 4.5))   # bibir penahan holder depan
for s in (-1, 1):                                   # bibir belakang dibelah, tengahnya untuk tiang sayap
    x0, x1 = sorted((s * 12.0, s * 28.0))
    cradle = cradle.union(box(x0, x1, -23.8, -21.3, TRAY_Z1 - 0.01, TRAY_Z1 + 4.5))
cradle = cradle.cut(box(16, 26, -23.0, -20.0, TRAY_Z0 - 1, TRAY_Z1 + 6))   # lubang kabel baterai ke BMS
for s in (-1, 1):                                   # jendela di atas encoder & tutup motor (piringan encoder > tinggi motor)
    cradle = cradle.cut(box(min(s * 9.6, s * 13.9), max(s * 9.6, s * 13.9), -7.0, 7.0, TRAY_Z0 - 1, TRAY_Z1 + 1))


# ---------- tiang sayap (2x, 3D print) ----------
def wing_z(y):
    """tinggi sisi bawah sayap di posisi Y (sayap dimiringkan, ekor naik)"""
    return WING_Z - (y - WING_PIV) * math.sin(math.radians(WING_TILT))


PYL_Y, PYL_X, PYL_ANG = -26.5, 7.0, 12.0


def pylon(s, clearance=0.0):
    """pelat tegak miring ke belakang; tab bawah masuk alas, tab atas tembus sayap"""
    ca = math.cos(math.radians(PYL_ANG))
    zt = [wing_z(PYL_Y + t * ca) for t in (-5.0, 2.0)]
    c = clearance
    body = [(-4.0, TRAY_Z1), (4.0, TRAY_Z1), (2.0, zt[1]), (-5.0, zt[0])]
    tabs = [(-4.0 - c, zt[0] - 0.2), (0.0 + c, zt[1] - 0.2), (0.0 + c, zt[1] + 3.8), (-4.0 - c, zt[0] + 3.8)]
    bot = [(-2.5 - c, TRAY_Z0 - 0.2), (2.5 + c, TRAY_Z0 - 0.2), (2.5 + c, TRAY_Z1 + 0.5), (-2.5 - c, TRAY_Z1 + 0.5)]
    th = 1.2 + c

    def plate(pts):
        return cq.Workplane("YZ").polyline(pts).close().extrude(th, both=True)
    shape = plate(tabs).union(plate(bot)) if clearance else plate(body).union(plate(tabs)).union(plate(bot))
    if not clearance:
        shape = try_fillet(shape, "|X", 0.3)
    return shape.rotate((0, 0, 0), (0, 0, 1), s * PYL_ANG).translate((s * PYL_X, PYL_Y, 0))


slots = None
for s in (-1, 1):
    slots = U(slots, pylon(s, 0.15))
cradle = cradle.cut(slots)
cradle = try_fillet(cradle, ">Z", 0.0) if False else cradle
cradle_shape = add("Dudukan motor + baterai (3D print)", cradle, "print")
export["cetak_dudukan_motor_baterai"] = (cradle_shape, "print")

# ---------- baterai ----------
hx, hy, hz = HOLD
hold = box(-hx / 2, hx / 2, -hy / 2, hy / 2, TRAY_Z1, TRAY_Z1 + hz)
for yc in (-10, 10):
    hold = hold.cut(cyl_x(-33, 33, yc, TRAY_Z1 + 11, 9.6))
add("Holder 2x18650", try_fillet(hold, "|Z", 1.5), "black_plastic")
for yc in (-10, 10):
    cell = cyl_x(-32.5, 32.5, yc, TRAY_Z1 + 11, 9.2)
    add("Baterai 18650", try_fillet(cell, "%CIRCLE", 1.0), "cell")
    add("Baterai 18650 kutub", cyl_x(32.5, 33.3, yc, TRAY_Z1 + 11, 3.0), "steel")

# ============================== SAYAP BELAKANG (3D print, sekaligus penutup baterai) ==============================
# 3 panel: tengah datar (ujung depan runcing ke depan seperti Ichiduino), panel luar naik 12 derajat (gull wing),
# endplate tegak di ujung. Dicetak berdiri di tepi belakang supaya tanpa support.
WT, WC, WTIP, WDIH = 2.4, 14.0, 56.0, 10.0
WL = (WTIP - WC) / math.cos(math.radians(WDIH))      # panjang panel luar sebelum dilipat
center = cq.Workplane("XY").polyline([(0, 16), (6, 13), (WC, 6), (WC, WING_TE), (-WC, WING_TE), (-WC, 6), (-6, 13)]).close().extrude(WT)
wing = center
for s in (-1, 1):
    pts = [(WC, 6), (WC + 0.5 * WL, -4.5), (WC + WL, -12), (WC + WL, WING_TE), (WC, WING_TE)]
    panel = cq.Workplane("XY").polyline([(s * x, y) for x, y in pts]).close().extrude(WT)
    panel = panel.cut(cbox(s * (WC + 0.4 * WL), -9.5, 7.0, 2.2, -1, WT + 1, s * -24))   # celah hias dekat tepi depan
    panel = panel.rotate((s * WC, 0, 0), (s * WC, 1, 0), -s * WDIH)
    wing = wing.union(panel)
tip_z = (WTIP - WC) * math.tan(math.radians(WDIH))
for s in (-1, 1):                                    # endplate tegak di ujung sayap
    x0 = WTIP - 0.6 if s > 0 else -WTIP - 1.8
    ep = (cq.Workplane("YZ").polyline([(WING_TE, tip_z - 5), (-12, tip_z - 5), (-15, tip_z + 5.0),
                                       (WING_TE + 5, tip_z + 6.5), (WING_TE, tip_z + 3.5)]).close()
          .extrude(2.4).translate((x0, 0, 0)))
    wing = wing.union(try_fillet(ep, "|X", 0.8))
wing = wing.rotate((0, WING_PIV, 0), (1, WING_PIV, 0), -WING_TILT).translate((0, 0, WING_Z))
wing = wing.cut(slots)
wing_shape = add("Sayap belakang (3D print)", wing, "print", "wing")
export["cetak_sayap_belakang"] = (wing_shape, "print")
for s in (-1, 1):
    p = add("Tiang sayap (3D print)", pylon(s), "print", "wing")
    if s > 0:
        export["cetak_tiang_sayap"] = (p, "print")

# ------------------------------ ekspor ------------------------------
MATS = {
    "pcb": ("#141619", 0.55, 0.15), "pcb_dark": ("#0e1013", 0.6, 0.1), "pcb_blue": ("#1d4d9a", 0.5, 0.1),
    "pcb_purple": ("#6b2a8e", 0.5, 0.1), "pcb_green": ("#1e6b3a", 0.5, 0.1),
    "gold": ("#d6aa45", 0.3, 0.9), "silk": ("#f1f1ee", 0.8, 0.0), "shield": ("#c3c8ce", 0.3, 0.9),
    "black_plastic": ("#1c1d20", 0.6, 0.0), "glass": ("#05080d", 0.12, 0.3), "screen": ("#9fd2ff", 0.4, 0.0),
    "flex": ("#c99a52", 0.5, 0.3), "pot": ("#2b6fd6", 0.5, 0.0), "jst": ("#efe9da", 0.6, 0.0),
    "chrome": ("#e3e6ea", 0.15, 1.0), "nylon": ("#eeeae0", 0.6, 0.0), "gearbox": ("#b89c5e", 0.35, 0.85),
    "steel": ("#c9ced4", 0.3, 0.9), "tire_red": ("#d3202e", 0.55, 0.0), "hub_grey": ("#a3a8ae", 0.45, 0.3),
    "print": ("#202227", 0.72, 0.05), "cap_black": ("#202124", 0.5, 0.0), "cell": ("#3a3d45", 0.4, 0.2),
    "resistor": ("#cdb88e", 0.6, 0.0), "resistor_smd": ("#26262a", 0.6, 0.0), "elko": ("#1f2340", 0.45, 0.1),
    "led_red": ("#ff3b3b", 0.35, 0.0), "ribbon": ("#9aa0a8", 0.7, 0.0), "led_smd": ("#e8e2d0", 0.4, 0.0),
    "pt_clear": ("#cfd8de", 0.15, 0.2),
}
meshes = []
for name, shape, mat, group in parts:
    verts, tris = shape.tessellate(0.03, 0.25)
    meshes.append({"n": name, "m": mat, "g": group,
                   "p": [round(c, 2) for v in verts for c in (v.x, v.y, v.z)],
                   "i": [i for t in tris for i in t]})
json.dump({"mats": MATS, "meshes": meshes}, open(f"{OUT}/model.json", "w"), separators=(",", ":"))

assy = cq.Assembly(name="LTM_v14")
for k, (name, shape, mat, group) in enumerate(parts):
    h = MATS[mat][0]
    col = cq.Color(int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255)
    assy.add(shape, name=f"{k:03d}_{name.replace(' ', '_').replace('(', '').replace(')', '')}", color=col)
exportAssembly(assy, f"{OUT}/step/LTM_v14_rakitan.step")

for fname, (shape, kind) in export.items():
    cq.exporters.export(cq.Workplane().add(shape), f"{OUT}/step/{fname}.step")
    if kind == "print":
        cq.exporters.export(cq.Workplane().add(shape), f"{OUT}/stl/{fname}.stl", tolerance=0.02, angularTolerance=0.1)

# outline PCB untuk KiCad (Edge.Cuts): PCB utama di koordinat robot (0,0 = tengah poros roda);
# PCB sensor dengan 0,0 = tengah tepi depan dan arah belakang = -Y (setelah impor KiCad jadi +Y, sama dengan
# koordinat sensor keputusan 15/10)
def outline_dxf(shape, path, dy=0.0):
    face = cq.Workplane().add(shape).faces("<Z").val().translate(cq.Vector(0, dy, -shape.BoundingBox().zmin))
    cq.exporters.export(cq.Workplane("XY").add(face), path, cq.exporters.ExportTypes.DXF)


outline_dxf(main_board, f"{OUT}/dxf/pcb_utama_outline.dxf")
outline_dxf(sb_board, f"{OUT}/dxf/pcb_sensor_outline.dxf", -F)
marks = None
for u, v in SENS_UV:                               # kotak 3,2 x 1,6: LED (depan) dan fototransistor (belakang)
    for dv in (-PAIR, PAIR):
        marks = U(marks, cq.Workplane("XY").rect(3.2, 1.6).extrude(1).translate((u, -(v + dv), 0)))
cq.exporters.export(marks.faces("<Z"), f"{OUT}/dxf/pcb_sensor_posisi_led_fototransistor.dxf", cq.exporters.ExportTypes.DXF)

bb = cq.Compound.makeCompound([p[1] for p in parts]).BoundingBox()
print(f"parts {len(parts)}  bbox X {bb.xmin:.1f}..{bb.xmax:.1f}  Y {bb.ymin:.1f}..{bb.ymax:.1f}  Z {bb.zmin:.1f}..{bb.zmax:.1f}")

# cek tabrakan antar bagian (CHECK=1): pasangan yang memang bersentuhan/masuk (as di velg, baut di lubang, dll.) dilewati
if os.environ.get("CHECK"):
    OK = [("As roda", "Velg"), ("As roda", "Gearbox"), ("Baut", "Pad"), ("Mur", "PCB"), ("Spacer", "Pad"),
          ("Baterai 18650", "Holder"), ("kutub", "Holder"), ("Silkscreen", "Pad"), ("OLED lubang", "OLED"),
          ("OLED tampilan", "OLED kaca"), ("Kabel pita", "Box header"), ("Tutup", "Tombol"), ("Elko C1 tutup", "Elko"),
          ("Ban merah", "Velg"), ("Dioda 1N5819 cincin", "Dioda"), ("Skid", "PCB sensor"), ("Silkscreen", ""),
          ("Pad lubang", "Dudukan"), ("OLED kaca", "OLED flex"), ("LED sensor chip", "LED sensor"),
          ("Fototransistor chip", "Fototransistor"), ("Baut M2", "Pad")]

    def allowed(a, b):
        return any((p in a and q in b) or (p in b and q in a) for p, q in OK)
    hits = []
    for i in range(len(parts)):
        bi = parts[i][1].BoundingBox()
        for j in range(i + 1, len(parts)):
            bj = parts[j][1].BoundingBox()
            if (bi.xmax <= bj.xmin or bj.xmax <= bi.xmin or bi.ymax <= bj.ymin or bj.ymax <= bi.ymin
                    or bi.zmax <= bj.zmin or bj.zmax <= bi.zmin):
                continue
            a, b = parts[i][0], parts[j][0]
            if allowed(a, b):
                continue
            try:
                v = parts[i][1].intersect(parts[j][1]).Volume()
            except Exception:
                v = -1
            if v > 0.05 or v < 0:
                hits.append((round(v, 2), a, b))
    for h in sorted(hits, reverse=True):
        print("TABRAKAN", h)
    print("cek tabrakan selesai:", len(hits), "pasangan")
