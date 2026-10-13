# Model 3D Robot Line Tracer Micro v12 = v11 dengan leher PCB sensor dipendekkan 20 mm (usulan 13/10/2026,
# PCB sensor belum diubah) + PCB utama v2 (13/10/2026: ESP32 & TB6612 & OLED di socket, ESP32 keluar dari bawah
# dudukan baterai, buck di bawah dudukan baterai). Basis v11 (livery navy-merah-kuning, roda kecil), gaya jangkar (referensi R3D Maker + LF edukasi 14 sensor
# + model Inventor kelompok). Sumbu: X kanan, Y maju, Z atas; nol = lantai di bawah tengah poros.
# 11/10/2026 sore: posisi komponen, lubang, dan outline PCB disamakan dengan layout PCB v1-draft
# (hardware/tools/gen_pcb.py memakai koordinat yang sama: MAIN_PLACE, HOLES_MAIN, SB_HALF, SENSOR_PLACE).
import json, math, sys
import cadquery as cq
from cadquery.occ_impl.exporters.assembly import exportAssembly

OUT = sys.argv[1] if len(sys.argv) > 1 else "."

# ------------------------------ ukuran (mm) ------------------------------
D_RODA = 26.0                 # diameter roda (11/10/2026: Ø34 -> Ø26 atas permintaan kelompok)
R_W, W_W = D_RODA / 2, 14.0   # jari-jari & lebar roda (roda lebar "lonjong" seperti referensi)
RIM_R = R_W - 4.5             # jari-jari velg (ban silikon tebal 4,5, tepi membulat)
WX0 = 40.0                    # sisi dalam roda
PCB_Z, T = 8.0, 1.6           # PCB utama
TOP = PCB_Z + T
SB_Z = 4.0                    # PCB sensor (jangkar)
PLATE_Z0 = R_W + 6.5          # dudukan baterai tepat di atas motor
PLATE_Z1 = PLATE_Z0 + 2.5
HOLD = (76.0, 42.0, 20.0)
BAT_Y = 8.0
ANC_C, R_OUT, R_IN, TH = 74.0, 50.0, 38.0, 62.0   # jangkar: pusat busur, jari-jari, sudut lengan

parts = []   # (nama, shape, material, grup)


def add(name, wp, mat, group="base"):
    vals = wp.vals() if isinstance(wp, cq.Workplane) else [wp]
    solids = [v for v in vals if isinstance(v, cq.Shape)]
    shape = solids[0] if len(solids) == 1 else cq.Compound.makeCompound(solids)
    parts.append((name, shape, mat, group))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_x(x0, x1, yc, zc, r):
    return cq.Workplane("YZ").circle(r).extrude(x1 - x0).translate((x0, yc, zc))


def cyl_z(xc, yc, z0, h, r):
    return cq.Workplane("XY").circle(r).extrude(h).translate((xc, yc, z0))


def cyl_y(y0, y1, xc, zc, r):
    return cq.Workplane("XZ").circle(r).extrude(-(y1 - y0)).translate((xc, y0, zc))


def U(a, b):
    """gabung dua solid (None diabaikan)"""
    if b is None:
        return a
    return b if a is None else a.union(b)


def pol(r, deg):  # titik pada busur jangkar
    a = math.radians(deg)
    return (r * math.sin(a), ANC_C + r * math.cos(a))


def try_fillet(wp, sel, r):
    try:
        return wp.edges(sel).fillet(r)
    except Exception:
        return wp


def pads_rect(cx, cy, w, h, ang=0.0, z=None):
    """kotak tipis (pad/silkscreen) diputar terhadap sumbu Z"""
    z = TOP if z is None else z
    return (cq.Workplane("XY").box(w, h, 0.06).rotate((0, 0, 0), (0, 0, 1), ang)
            .translate((cx, cy, z + 0.03)))


def frame_rect(cx, cy, w, h, ang, z, lw=0.35):
    o = cq.Workplane("XY").box(w, h, 0.05)
    i = cq.Workplane("XY").box(w - 2 * lw, h - 2 * lw, 0.2)
    return o.cut(i).rotate((0, 0, 0), (0, 0, 1), ang).translate((cx, cy, z + 0.025))


def text(s, size, cx, cy, z, ang=0.0):
    try:
        t = cq.Workplane("XY").text(s, size, 0.06, font="DejaVu Sans", kind="bold", halign="center", valign="center")
        return t.rotate((0, 0, 0), (0, 0, 1), ang).translate((cx, cy, z))
    except Exception:
        return None


# ============================== PCB UTAMA (perisai) ==============================
MAIN_PTS = [(-36, 8), (36, 8), (36, 18), (47, 22), (47, 62), (28, 86), (13, 92),
            (-13, 92), (-28, 86), (-47, 62), (-47, 22), (-36, 18)]
main = cq.Workplane("XY").polyline(MAIN_PTS).close().extrude(T).translate((0, 0, PCB_Z))
main = try_fillet(main, "|Z", 2.5)
HOLES_MAIN = [(-32, 16), (32, 16), (-37.5, 69), (37.5, 69), (-10.5, 83), (10.5, 83)]   # = gen_pcb.py
for hx, hy in HOLES_MAIN:
    main = main.cut(cyl_z(hx, hy, PCB_Z - 1, T + 2, 1.6))
add("PCB utama", main, "pcb")
gold = None
for hx, hy in HOLES_MAIN:
    ring = cyl_z(hx, hy, TOP, 0.05, 2.9).cut(cyl_z(hx, hy, TOP - 1, 2, 1.6))
    gold = ring if gold is None else gold.union(ring)
add("Pad lubang", gold, "gold")
silk = None
for x in (-20, 20):                                   # tombol
    silk = U(silk, frame_rect(x, 83, 9, 9, 0, TOP))
silk = U(silk, frame_rect(-0.5, 69.15, 20.4, 20.3, 0, TOP, 0.15))      # garis modul TB6612
silk = U(silk, frame_rect(-22.3, 68.8, 21.8, 18.8, 0, TOP, 0.15))      # kotak blok SUARA
silk = U(silk, frame_rect(26.1, 46.25, 31.0, 29.3, 0, TOP, 0.15))      # kotak blok LAYAR (di bawah OLED)
for t in (text("A", 2.2, -26.5, 83, TOP), text("B", 2.2, 26.5, 83, TOP),
          text("LINE TRACER MICRO v2", 1.4, 0, 89.3, TOP), text("KE SENSOR", 1.1, 0, 86.6, TOP),
          text("SUARA", 1.3, -26.0, 61.4, TOP), text("ALUR DAYA", 1.2, 25.6, 77.6, TOP),
          text("BATERAI", 1.0, 22.4, 75.5, TOP), text("SAKLAR", 1.0, 22.4, 72.4, TOP),
          text("BUCK 5V", 1.0, 22.4, 69.3, TOP), text("MOTOR", 1.0, 30.6, 69.3, TOP),
          text("ESP32 + SENSOR", 1.0, 22.4, 66.2, TOP), text("DAYA", 2.0, -20, 27.4, TOP),
          text("KIRI", 1.1, -31.6, 9.9, TOP), text("KANAN", 1.1, 31.6, 9.9, TOP)):
    silk = U(silk, t)
add("Silkscreen utama", silk, "silk")
# ujung pin header PCB sensor yang menembus J5 (disolder di atas PCB utama)
j5 = None
for k in range(5):
    for y in (81.23, 83.77):
        x = -5.08 + 2.54 * k
        j5 = U(j5, cyl_z(x, y, TOP, 0.25, 0.85).union(box(x - 0.32, x + 0.32, y - 0.32, y + 0.32, TOP, TOP + 1.6)))
add("Pin J5 (tembus)", j5, "gold")

SOCK = 8.5                         # tinggi socket header female (ESP32, TB6612, OLED bisa dicabut)
# ---------- ESP32 DevKit (PCB v2: melintang di depan dudukan baterai, USB ke kiri, di socket) ----------
EY0, EY1 = 30.2, 58.6
for yr in (31.7, 57.1):            # 2 socket 1x15
    add("ESP32 socket", box(-43.65, -5.55, yr - 1.27, yr + 1.27, TOP, TOP + SOCK), "black_plastic")
dz = TOP + SOCK


def esp(x0, x1, y0, y1):
    """kotak di atas modul ESP32; koordinat lama (antena di -X, Y tengah 28) diputar 180 derajat"""
    return (-21.1 - x1, -21.1 - x0, 72.4 - y1, 72.4 - y0)


add("ESP32 PCB", box(-46.6, 4.4, EY0, EY1, dz, dz + T), "pcb")
add("ESP32 antena", box(*esp(-25.5, -19.5, 19, 37), dz + T, dz + T + 0.8), "pcb_dark")
add("ESP32 modul", box(*esp(-19.5, -1.5, 19, 37), dz + T, dz + T + 3.0), "shield")
add("ESP32 USB-C", box(*esp(18.5, 26.2, 23.5, 32.5), dz + T, dz + T + 3.2), "shield")
add("ESP32 chip", box(*esp(4, 14, 17, 21), dz + T, dz + T + 1.4).union(box(*esp(6, 12, 34, 38), dz + T, dz + T + 1.6)),
    "black_plastic")
add("ESP32 tombol", box(*esp(15, 18, 15.2, 17.8), dz + T, dz + T + 1.6).union(box(*esp(15, 18, 38.2, 40.8), dz + T, dz + T + 1.6)),
    "shield")

# ---------- OLED 1.3" (header di sisi depan, tampilan tegak dilihat dari belakang robot) ----------
oz = TOP + SOCK
add("OLED socket", box(23.02, 33.18, 61.28, 63.82, TOP, oz), "black_plastic")
add("OLED PCB", box(10.4, 45.8, 30.5, 64.0, oz, oz + 1.2), "pcb_blue")
add("OLED kaca", box(10.9, 45.3, 34.5, 59.0, oz + 1.2, oz + 2.7), "glass")
gz = oz + 2.71
bars = None
for i, x1 in enumerate((19, 23, 16, 21)):
    y = 55.0 - i * 5.0
    b_ = box(15.1, 15.1 + x1, y - 0.9, y + 0.9, gz, gz + 0.02)
    bars = b_ if bars is None else bars.union(b_)
bars = bars.union(box(12.6, 13.9, 49.1, 50.9, gz, gz + 0.02))     # kursor menu
add("OLED tampilan", bars, "screen")

# ---------- driver (tengah depan, di socket) & buck (di bawah dudukan baterai, disolder) ----------
for xc in (-8.12, 7.12):           # 2 socket 1x8
    add("TB6612 socket", box(xc - 1.27, xc + 1.27, 58.99, 79.31, TOP, TOP + SOCK), "black_plastic")
add("TB6612 PCB", box(-10.65, 9.65, 59.0, 79.3, TOP + SOCK, TOP + SOCK + 1.6), "pcb_purple")
add("TB6612 chip", box(-3.75, 2.75, 66.4, 71.9, TOP + SOCK + 1.6, TOP + SOCK + 2.7), "black_plastic")
add("MP1584 PCB", box(-11, 11, 12.6, 29.6, TOP + 2.5, TOP + 4.1), "pcb_blue")
add("MP1584 pin", box(-11, -8.5, 13.6, 28.6, TOP, TOP + 2.5).union(box(8.5, 11, 13.6, 28.6, TOP, TOP + 2.5)), "black_plastic")
add("MP1584 induktor", box(-3, 3, 18.1, 24.1, TOP + 4.1, TOP + 8.1), "black_plastic")
add("MP1584 trimpot", box(4, 7, 14.6, 17.6, TOP + 4.1, TOP + 6.6), "pot")

# ---------- UI: tombol, buzzer, saklar ----------
for x in (-20, 20):
    add("Tombol", box(x - 3, x + 3, 80, 86, TOP, TOP + 3.5), "black_plastic")
    add("Tombol tutup", cyl_z(x, 83, TOP + 3.5, 1.5, 1.8), "rb_red" if x < 0 else "rb_yellow")
bz = cyl_z(-26.0, 70.0, TOP, 9.5, 6).cut(cyl_z(-26.0, 70.0, TOP + 8.5, 2, 1.2))
add("Buzzer", try_fillet(bz, ">Z", 0.6), "black_plastic")
# saklar geser SW1 di tepi kanan (di bawah OLED), tuas keluar ke +X; konektor baterai J1 (JST XH 2 pin) di belakangnya
add("Saklar", box(42.6, 47.0, 32.7, 41.3, TOP, TOP + 4.4), "shield")
add("Saklar tuas", box(47.0, 51.0, 35.0, 37.0, TOP + 1.4, TOP + 3.0), "black_plastic")
add("JST XH baterai", box(40.5, 46.45, 23.1, 30.6, TOP, TOP + 7.0), "jst")
for x0, x1 in ((-28.95, -15.05), (15.05, 28.95)):     # konektor motor JST PH 6 pin (J2, J3)
    add("JST PH motor", box(x0, x1, 8.5, 13.0, TOP, TOP + 6), "jst")
# komponen kecil (posisi = MAIN_PLACE di gen_pcb.py), semua kaki tembus
res = None
for xc, yc, along_y in ((20.81, 26.0, 0), (20.81, 21.0, 0), (-16.5, 64.81, 1), (-13.5, 64.81, 1)):    # R1 R2 R3 R4
    r_ = cyl_y(yc - 3.15, yc + 3.15, xc, TOP + 1.25, 1.25) if along_y else cyl_x(xc - 3.15, xc + 3.15, yc, TOP + 1.25, 1.25)
    res = U(res, r_)
add("Resistor THT", res, "resistor")
add("Elko C1 100uF", cyl_z(13.65, 75.5, TOP + 0.3, 10.7, 3.15), "elko")
add("Elko C1 100uF tutup", cyl_z(13.65, 75.5, TOP + 11.0, 0.15, 2.85), "shield")
to92 = cyl_z(-15.23, 74.9, TOP + 3.0, 4.5, 2.3).intersect(box(-17.63, -12.83, 73.8, 77.3, TOP + 2.9, TOP + 7.6))
add("Transistor S8050", to92, "black_plastic")
add("Dioda 1N5819", cyl_x(-22.5, -17.3, 17.5, TOP + 1.35, 1.35), "black_plastic")
add("Dioda 1N5819 cincin", cyl_x(-22.2, -21.5, 17.5, TOP + 1.35, 1.38), "silk")

# ---------- bawah PCB utama: ball caster, header antar papan, spacer ----------
add("Ball caster rumah", cyl_z(0, 62, 4.6, PCB_Z - 4.6, 5.5), "black_plastic")
add("Ball caster bola", cq.Workplane("XY").sphere(3.0).translate((0, 62, 3.0)), "chrome")
add("Header antar papan", box(-6.35, 6.35, 79.96, 85.04, SB_Z + T, PCB_Z), "black_plastic")
for x in (-10.5, 10.5):
    add("Spacer nilon", cyl_z(x, 83, SB_Z + T, PCB_Z - SB_Z - T, 2.6), "nylon")
    add("Baut M3", cyl_z(x, 83, TOP, 1.8, 2.7), "chrome")

# ============================== PCB SENSOR (jangkar + leher) ==============================
F = 112.0                                     # ujung depan jangkar (v11: 132; v12: leher dipendekkan 20 mm)
D = (0.581, -0.814)                           # arah lengan (±54° ke belakang)
ARM_ANG = math.degrees(math.atan2(D[1], D[0]))
R_HALF = [(0, F), (26, F - 2), (46, F - 30), (32.5, F - 30), (20, F - 12.6), (7, F - 11.6), (7, 90), (14, 90), (14, 79)]
pts = R_HALF + [(-x, y) for x, y in reversed(R_HALF)]
pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
if pts[-1] == pts[0]:
    pts = pts[:-1]
sb = cq.Workplane("XY").polyline(pts).close().extrude(T)
sb = try_fillet(sb, "|Z", 1.2)
for x in (-10.5, 10.5):
    sb = sb.cut(cyl_z(x, 83, -1, 4, 1.6))
sb = sb.translate((0, 0, SB_Z))
add("PCB sensor jangkar", sb, "pcb")
SZ_TOP = SB_Z + T
SENS = [(-20, F - 8.0, 6), (-10, F - 6.0, 4), (0, F - 4.5, 0), (10, F - 6.0, -4), (20, F - 8.0, -6)]
gold = None; silk = None; sens = None
for i, (cx, cy, a) in enumerate(SENS):
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    for dx in (-1.27, 1.27):                       # pad THT sensor (footprint sementara 2x2, 2,54 mm)
        for dy in (-1.27, 1.27):
            gold = U(gold, cyl_z(cx + dx * ca - dy * sa, cy + dx * sa + dy * ca, SZ_TOP, 0.06, 0.7))
    s_ = cq.Workplane("XY").box(4.0, 3.2, 2.5).rotate((0, 0, 0), (0, 0, 1), a).translate((cx, cy, SB_Z - 1.25))
    sens = U(sens, s_)
    silk = U(silk, text(str(i + 1), 1.7, cx - 4.3, cy, SZ_TOP))
for t in (text("LINE TRACER MICRO", 1.8, -30.7, F - 18.1, SZ_TOP, 54.4),      # leher pendek: tulisan pindah ke lengan
          text("P01 KEL.5", 1.8, 30.7, F - 18.1, SZ_TOP, -54.4)):
    silk = U(silk, t)
add("Sensor ITR20001 x5", sens, "black_plastic")
add("Pad sensor", gold, "gold")
add("Silkscreen sensor", silk, "silk")
# komponen SMD di sisi BAWAH PCB sensor (posisi = SENSOR_PLACE di gen_pcb.py)
smd = None
for k in range(10):                                # R1-R10 sebaris di bawah pangkal leher (posisi usulan, PCB belum diubah)
    x = -12.6 + 2.8 * k
    smd = U(smd, box(x - 0.62, x + 0.62, 86.5, 88.5, SB_Z - 0.5, SB_Z))
for x in (-4.3, 4.3):                              # R11, R12
    smd = U(smd, box(x - 0.62, x + 0.62, 94.0, 96.0, SB_Z - 0.5, SB_Z))
add("Resistor SMD sensor", smd, "black_plastic")
add("MOSFET AO3400", box(-0.65, 0.65, 93.55, 96.45, SB_Z - 1.0, SB_Z), "black_plastic")
add("Kapasitor C1 sensor", box(-1.0, 1.0, 97.88, 99.12, SB_Z - 0.6, SB_Z), "cap_ceramic")

# ============================== PENGGERAK ==============================
for s in (-1, 1):
    def X(a, b):
        return tuple(sorted((s * a, s * b)))
    x0, x1 = X(26, 35)
    add("Gearbox N20", box(x0, x1, -6, 6, R_W - 5, R_W + 5), "gearbox")
    x0, x1 = X(11, 26)
    can = cyl_x(x0, x1, 0, R_W, 6).intersect(box(x0 - 1, x1 + 1, -7, 7, R_W - 5, R_W + 5))
    add("Motor N20", can, "steel")
    x0, x1 = X(10, 11)
    add("Tutup motor", cyl_x(x0, x1, 0, R_W, 5.5), "black_plastic")
    x0, x1 = X(8.4, 10)
    add("Encoder PCB", cyl_x(x0, x1, 0, R_W, 6.0), "pcb_green")
    x0, x1 = X(6.4, 8.4)
    add("Magnet encoder", cyl_x(x0, x1, 0, R_W, 3.0), "black_plastic")
    x0, x1 = X(5.0, 8.4)
    add("Konektor encoder", box(x0, x1, -3, 3, R_W - 6.5, R_W - 2.5), "jst")
    x0, x1 = X(35, 47)
    add("As roda", cyl_x(x0, x1, 0, R_W, 1.5), "steel")
    # roda: ban + velg
    x0, x1 = X(WX0, WX0 + W_W)
    tire = cyl_x(x0, x1, 0, R_W, R_W).cut(cyl_x(x0 - 1, x1 + 1, 0, R_W, RIM_R))
    try:
        tire = tire.edges(cq.selectors.RadiusNthSelector(1)).fillet(3.2)   # tepi luar ban membulat
    except Exception:
        tire = try_fillet(tire, "%CIRCLE", 1.0)
    add("Ban", tire, "rubber")
    x0, x1 = X(WX0 + 0.6, WX0 + W_W - 0.6)
    rim = cyl_x(x0, x1, 0, R_W, RIM_R + 0.05)
    for k in range(5):
        a = math.radians(90 + k * 72)
        rc = 0.58 * RIM_R
        rim = rim.cut(cyl_x(x0 - 1, x1 + 1, rc * math.cos(a), R_W + rc * math.sin(a), 0.2 * RIM_R))
    x0, x1 = X(WX0 + W_W - 1.5, WX0 + W_W + 0.8)
    xo0, xo1 = X(WX0 + W_W - 2.6, WX0 + W_W + 1)
    rim = rim.cut(cyl_x(xo0, xo1, 0, R_W, RIM_R - 1.0))                    # cekungan muka luar
    rim = rim.union(cyl_x(x0, x1, 0, R_W, 0.33 * RIM_R))                    # hub
    add("Velg", rim, "rb_yellow")

# ---------- rangka 3D print ----------
plate = (cq.Workplane("XY").moveTo(-39, 29.5).lineTo(39, 29.5).lineTo(39, -14)   # tepi depan 29,5: ESP32 mulai Y 30,2
         .threePointArc((46.5, -17.5), (49, -24)).threePointArc((32, -27.5), (0, -30))
         .threePointArc((-32, -27.5), (-49, -24)).threePointArc((-46.5, -17.5), (-39, -14)).close()
         .extrude(PLATE_Z1 - PLATE_Z0).translate((0, 0, PLATE_Z0)))
plate = try_fillet(plate, "|Z", 1.5)
plate = try_fillet(plate, ">Z", 0.8)
lower = box(-37.5, 37.5, -27, 7, R_W - 8, R_W - 5)
for sx in (-1, 1):   # kantong untuk PCB encoder
    lower = lower.cut(box(min(sx * 5, sx * 12), max(sx * 5, sx * 12), -7, 7, R_W - 6.2, R_W - 4.9))
lower = try_fillet(lower, "|Z", 2)
frame = plate.union(lower)
for s in (-1, 1):
    x0, x1 = sorted((s * 35, s * 37.5))
    wall = box(x0, x1, -10, 7.6, R_W - 8, PLATE_Z0 + 0.1)        # berhenti 0,4 mm sebelum tepi belakang PCB utama
    wall = wall.cut(cyl_x(x0 - 1, x1 + 1, 0, R_W, 2.2))
    frame = frame.union(wall)
    frame = frame.union(cyl_z(s * 26, -22, R_W - 5, PLATE_Z0 - (R_W - 5) + 0.1, 2.6))
rear = box(-30, 30, -27, -25, R_W - 5, PLATE_Z0 + 0.1)
rear = rear.cut(box(-5.4, 5.4, -28, -24, R_W - 4.0, R_W + 0.4))
for k in range(4):
    for sx in (-1, 1):
        x0 = sx * (12 + k * 4)
        rear = rear.cut(box(min(x0, x0 + sx * 2), max(x0, x0 + sx * 2), -28, -24, R_W - 2, R_W + 4))
frame = frame.union(rear)
skid = cq.Workplane("XY").sphere(4.0).translate((0, -22, R_W - 6.5)).intersect(box(-5, 5, -27, -17, R_W - 11, R_W - 4.9))
frame = frame.union(skid)
add("Rangka 3D print", frame, "frame")
for s in (-1, 1):
    add("Standoff M3", cyl_z(s * 32, 16, TOP, PLATE_Z0 - TOP, 2.75), "brass")
add("Modul charger 2S", box(-12.5, 12.5, -24.5, -7.5, R_W - 5, R_W - 3.4), "pcb_blue")
add("USB-C charger", box(-4.5, 4.5, -26.6, -19.5, R_W - 3.4, R_W - 0.2), "shield")
add("BMS 2S", box(-46.5, -2.5, 37, 52, PCB_Z - 2.4, PCB_Z), "pcb_green")      # di bawah PCB utama, di antara baris pin ESP32

# ---------- baterai ----------
hz0 = PLATE_Z1
hx, hy, hz = HOLD
hold = box(-hx / 2, hx / 2, BAT_Y - hy / 2, BAT_Y + hy / 2, hz0, hz0 + hz)
for yc in (BAT_Y - 10, BAT_Y + 10):
    hold = hold.cut(cyl_x(-33, 33, yc, hz0 + 11, 9.6))
add("Holder 2x18650", try_fillet(hold, "|Z", 1.5), "black_plastic")
for yc in (BAT_Y - 10, BAT_Y + 10):
    cell = cyl_x(-32.5, 32.5, yc, hz0 + 11, 9.2)
    add("Baterai 18650", try_fillet(cell, "%CIRCLE", 1.0), "cell")

# ---------- cover (bodi) & sayap belakang ----------
cz0 = PLATE_Z1 + 11.0
PROF = [(-18, cz0), (-18, cz0 + 11.5), (-15, cz0 + 14.5), (28, cz0 + 13.0), (37, cz0 + 5.0), (38, cz0)]
outer = cq.Workplane("YZ").polyline(PROF).close().extrude(80).translate((-40, 0, 0))
outer = try_fillet(outer, "|Z", 7)
outer = try_fillet(outer, "|X", 2.5)
try:
    cov = outer.faces("<Z").shell(-1.6)
except Exception:
    cov = outer.cut(outer.translate((0, 0, -1.6)).intersect(box(-38.4, 38.4, -16.4, 31.4, 0, 60)))
add("Cover bodi", cov, "navy", "cover")
skin = outer.translate((0, 0, 0.35)).cut(outer)
add("Strip merah", skin.intersect(box(-6, 6, -30, 33, cz0 + 8, 80)), "rb_red", "cover")
add("Garis kuning", skin.intersect(box(-9.2, -7.6, -30, 33, cz0 + 8, 80)).union(skin.intersect(box(7.6, 9.2, -30, 33, cz0 + 8, 80))), "rb_yellow", "cover")
add("Hidung kuning", skin.intersect(box(-41, 41, 33.5, 45, cz0 - 1, 80)), "rb_yellow", "cover")
belt = box(-40.4, -39.9, -14, 33, cz0 + 0.8, cz0 + 3.6).union(box(39.9, 40.4, -14, 33, cz0 + 0.8, cz0 + 3.6))
add("Sabuk merah", belt, "rb_red", "cover")
vent = None
for k in range(3):
    y = 18 + k * 4.0
    v = skin.intersect(box(-30, -16, y, y + 1.6, cz0 + 8, 80)).union(skin.intersect(box(16, 30, y, y + 1.6, cz0 + 8, 80)))
    vent = v if vent is None else vent.union(v)
add("Ventilasi cover", vent, "black_plastic", "cover")

wz = PLATE_Z1 + 27.0
for s in (-1, 1):
    x0, x1 = sorted((s * 14.5, s * 17.5))
    add("Tiang sayap", box(x0, x1, -28.5, -25.5, PLATE_Z1 - 0.1, wz), "navy", "wing")
wing = (cq.Workplane("YZ").moveTo(-25, 0).threePointArc((-32, 1.6), (-40.5, 0.4)).lineTo(-40.5, -1.4)
        .threePointArc((-32, -0.4), (-25, -2.0)).close().extrude(92).translate((-46, 0, wz + 1.5)))
add("Sayap belakang", wing, "navy", "wing")
for s in (-1, 1):
    x0 = 46.0 if s > 0 else -47.8
    ep = (cq.Workplane("YZ").polyline([(-25, wz - 31), (-29, wz - 38), (-38, wz - 38), (-41.5, wz - 7), (-39, wz + 6), (-29, wz + 6), (-25.5, wz - 3)]).close()
          .extrude(1.8).translate((x0, 0, 0)))
    add("Endplate", ep, "rb_red", "wing")

# ------------------------------ ekspor ------------------------------
MATS = {
    "pcb": ("#16191d", 0.55, 0.15), "pcb_dark": ("#0e1013", 0.6, 0.1), "pcb_blue": ("#1d4d9a", 0.5, 0.1),
    "pcb_purple": ("#6b2a8e", 0.5, 0.1), "pcb_green": ("#1e6b3a", 0.5, 0.1),
    "gold": ("#d6aa45", 0.3, 0.9), "silk": ("#f1f1ee", 0.8, 0.0), "shield": ("#c3c8ce", 0.3, 0.9),
    "black_plastic": ("#1c1d20", 0.6, 0.0), "glass": ("#05080d", 0.12, 0.3), "screen": ("#9fd2ff", 0.4, 0.0),
    "pot": ("#2b6fd6", 0.5, 0.0), "cap_orange": ("#f07a1c", 0.5, 0.0), "cap_white": ("#e9e9e4", 0.5, 0.0),
    "jst": ("#efe9da", 0.6, 0.0), "chrome": ("#e3e6ea", 0.15, 1.0), "nylon": ("#eeeae0", 0.6, 0.0),
    "gearbox": ("#b89c5e", 0.35, 0.85), "steel": ("#c9ced4", 0.3, 0.9), "rubber": ("#18181a", 0.9, 0.0),
    "navy": ("#1f2c57", 0.62, 0.05), "rb_red": ("#d6203f", 0.5, 0.0), "rb_yellow": ("#ffc414", 0.45, 0.0),
    "frame": ("#1f2c57", 0.7, 0.05), "brass": ("#c9a24a", 0.35, 0.9),
    "cell": ("#2d62b0", 0.4, 0.1),
    "resistor": ("#cdb88e", 0.6, 0.0), "elko": ("#1f2340", 0.45, 0.1), "cap_ceramic": ("#b08d57", 0.6, 0.0),
}
meshes = []
for name, shape, mat, group in parts:
    verts, tris = shape.tessellate(0.03, 0.25)
    meshes.append({"n": name, "m": mat, "g": group,
                   "p": [round(c, 2) for v in verts for c in (v.x, v.y, v.z)],
                   "i": [i for t in tris for i in t]})
json.dump({"mats": MATS, "meshes": meshes}, open(f"{OUT}/model.json", "w"), separators=(",", ":"))

assy = cq.Assembly(name="LTM_v12")
for k, (name, shape, mat, group) in enumerate(parts):
    h = MATS[mat][0]
    col = cq.Color(int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255)
    assy.add(shape, name=f"{k:02d}_{name.replace(' ', '_')}", color=col)
exportAssembly(assy, f"{OUT}/LTM_v12.step")

bb = cq.Compound.makeCompound([p[1] for p in parts]).BoundingBox()
print(f"parts {len(parts)}  bbox X {bb.xmin:.1f}..{bb.xmax:.1f}  Y {bb.ymin:.1f}..{bb.ymax:.1f}  Z {bb.zmin:.1f}..{bb.zmax:.1f}")
