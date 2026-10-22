# Model 3D Robot Line Tracer Micro v16 (22/10/2026): v15 dengan PCB sensor rev B buatan user (KiCad):
# - PCB sensor bentuk jangkar (lebar 95 mm, 12 QRE1113GR jarak 8 mm di busur, IC mux SOIC-24 + J1 JST XH 8 pin di
#   tangkai, 2 lubang M3 di ujung tangkai). Bentuk, lubang, dan posisi komponen dibaca langsung dari
#   hardware/sensor-garis/sensor-garis.kicad_pcb, jadi model selalu ikut file PCB terbaru.
# - Tepi depan PCB sensor tetap di Y 131 (jarak sensor ke poros roda sama dengan v15).
# - Penahan depan (usulan): skid nilon di kedua baut H1/H2 (rev B tidak punya lubang skid terpisah).
# - PCB utama bentuk "mobil F1" (pilihan user 22/10): sidepod lebar, pinggang lengkung di antara roda, hidung panjang.
# - Kabel pita IDC diganti kabel JST XH 8 pin: J5 di tepi miring sidepod kiri, pin 1 di ujung dekat hidung; kabel
#   dibundel menyusuri tepi kiri hidung (kiri tombol A) ke J1 PCB sensor. Elko C1 pindah ke sidepod kiri.
# Sumbu: X kanan, Y maju, Z atas; nol = lantai di bawah tengah poros roda.
import json, math, os, re, sys
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
SB_Z = 4.8                    # sisi bawah PCB sensor: muka QRE1113GR (tinggi 1,7) +-3,1 mm dari lantai
SZ_TOP = SB_Z + T             # 6,4; celah ke PCB utama 4,0 = spacer nilon M3 x 4
F = 131.0                     # tepi depan PCB sensor (hidung PCB utama di Y 91; J1 tepat di depannya)
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


# ============================== PCB SENSOR (rev B dari KiCad, 12 QRE1113GR) ==============================
# Bentuk, lubang, dan posisi komponen dibaca langsung dari hardware/sensor-garis/sensor-garis.kicad_pcb (rev B,
# bentuk jangkar, lebar 95 mm). KiCad: X kanan, Y ke belakang, titik tengah X 200. Robot: X = kx - 200,
# Y = F - (ky - tepi depan).
KPCB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hardware", "sensor-garis",
                    "sensor-garis.kicad_pcb")
_k = open(KPCB, encoding="utf8").read()
KX0 = 200.0


def _xy(a, b):
    return float(a), float(b)


_edges = []
for m in re.finditer(r'\((gr_line|gr_arc)\s+\(start ([\d.\-]+) ([\d.\-]+)\)\s*(?:\(mid ([\d.\-]+) ([\d.\-]+)\)\s*)?'
                     r'\(end ([\d.\-]+) ([\d.\-]+)\)[^()]*\(stroke[^()]*\([^()]*\)[^()]*\([^()]*\)\s*\)\s*\(layer "Edge\.Cuts"\)',
                     _k):
    g = m.groups()
    _edges.append((g[0], _xy(*g[1:3]), _xy(*g[3:5]) if g[3] else None, _xy(*g[5:7])))
KY0 = min(min(e[1][1], e[3][1]) for e in _edges)        # tepi depan PCB sensor (Y KiCad)


def k2r(kx, ky):
    return (kx - KX0, F - (ky - KY0))


def _chain(edges, tol=1e-3):
    """urutkan segmen Edge.Cuts jadi satu lintasan tertutup (arah segmen dibalik bila perlu)"""
    rest, out = list(edges[1:]), [edges[0]]
    while rest:
        end = out[-1][3]
        for i, (t, a, mid, b) in enumerate(rest):
            if math.dist(a, end) < tol:
                out.append(rest.pop(i))
                break
            if math.dist(b, end) < tol:
                rest.pop(i)
                out.append((t, b, mid, a))
                break
        else:
            raise RuntimeError("outline PCB sensor tidak tersambung")
    return out


SB_CHAIN = _chain(_edges)
_wedges = []
for t, a, mid, b in SB_CHAIN:
    pa, pb = cq.Vector(*k2r(*a), 0), cq.Vector(*k2r(*b), 0)
    if t == "gr_arc" and math.dist(a, b) > 0.02:
        _wedges.append(cq.Edge.makeThreePointArc(pa, cq.Vector(*k2r(*mid), 0), pb))
    else:
        _wedges.append(cq.Edge.makeLine(pa, pb))
SB_FACE = cq.Face.makeFromWires(cq.Wire.assembleEdges(_wedges))

FP = []                                                 # (ref, lib, sisi, x, y, sudut) koordinat robot
for m in re.finditer(r'\n\t\(footprint "([^"]+)"(.*?)\n\t\)', _k, re.S):
    body = m.group(2)
    at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', body).groups()
    ref = re.search(r'\(property "Reference" "([^"]+)"', body).group(1)
    side = "B" if body.lstrip().startswith('(layer "B.Cu")') else "F"
    FP.append((ref, m.group(1), side, *k2r(float(at[0]), float(at[1])), float(at[2] or 0)))
FPD = {f[0]: f for f in FP}
SENS = sorted([(f[3], f[4], f[5]) for f in FP if f[1].startswith("OptoDevice:OnSemi_CASE100CY")])   # kiri ke kanan
SB_HOLES = sorted([(f[3], f[4]) for f in FP if f[1].startswith("MountingHole")])
SB_HOLE_R = 1.6

sb = cq.Workplane("XY").add(cq.Solid.extrudeLinear(SB_FACE, cq.Vector(0, 0, T))).translate((0, 0, SB_Z))
for hx, hy in SB_HOLES:
    sb = sb.cut(cyl_z(hx, hy, SB_Z - 1, T + 2, SB_HOLE_R))
sb_board = add("PCB sensor", sb, "pcb", "sensor")
export["pcb_sensor"] = (sb_board, "pcb")


def local(x, y, ang, lx, ly):
    a = math.radians(ang)
    return (x + lx * math.cos(a) - ly * math.sin(a), y + lx * math.sin(a) + ly * math.cos(a))


def text_bottom(s_, size, cx, cy, z, ang=0.0):
    """teks silkscreen sisi bawah (dicerminkan supaya terbaca dari bawah)"""
    t = text(s_, size, 0, 0, 0)
    if t is None:
        return None
    return t.mirror("YZ").rotate((0, 0, 0), (0, 0, 1), ang).translate((cx, cy, z))


# QRE1113GR (badan 2,9 x 3,6 x 1,7) di sisi bawah; kaki di ujung sisi 3,6 (footprint OnSemi CASE100CY);
# sudut KiCad dipakai langsung (badan simetris, jadi cermin sisi bawah tidak mengubah arah sumbunya)
qre = lens = leads = smd = None
for x, y, ang in SENS:
    qre = U(qre, cbox(x, y, 2.9, 3.6, SB_Z - 1.7, SB_Z, ang))
    for ly in (0.85, -0.85):
        lens = U(lens, cyl_z(*local(x, y, ang, 0, ly), SB_Z - 1.75, 0.06, 0.6))
    for lx in (-0.9, 0.9):
        for ly in (-2.0, 2.0):
            leads = U(leads, cbox(*local(x, y, ang, lx, ly), 0.5, 0.9, SB_Z - 0.35, SB_Z, ang))
for ref, lib, side, x, y, ang in FP:
    if lib.startswith("Resistor_SMD:R_0805") and side == "B":
        smd = U(smd, cbox(x, y, 2.0, 1.25, SB_Z - 0.5, SB_Z, ang))
add("Sensor QRE1113GR x12", qre, "black_plastic", "sensor")
add("QRE1113GR lensa", lens, "glass", "sensor")
add("QRE1113GR kaki", leads, "steel", "sensor")
add("Resistor SMD sensor", smd, "resistor_smd", "sensor")

silk = silk_border([k2r(*e[1]) for e in SB_CHAIN], SZ_TOP, 0.8, 0.3)
silk_b = None
for k, (x, y, ang) in enumerate(SENS):                 # nomor sensor 1-12 (kiri ke kanan) di kedua sisi
    tang = ang + 180 if abs(ang) > 90 else ang         # teks tetap tegak dilihat dari belakang robot
    silk = U(silk, text(str(k + 1), 1.4, *local(x, y, tang, 0, -5.6), SZ_TOP, tang))
    silk_b = U(silk_b, text_bottom(str(k + 1), 1.4, *local(x, y, tang, 0, -5.6), SB_Z - 0.06, tang))
add("Silkscreen sensor", silk, "silk", "sensor")
add("Silkscreen sensor bawah", silk_b, "silk", "sensor")
gold = None
for hx, hy in SB_HOLES:
    gold = U(gold, cyl_z(hx, hy, SZ_TOP, 0.05, 2.8).cut(cyl_z(hx, hy, SZ_TOP - 1, 2, SB_HOLE_R)))
add("Pad lubang sensor", gold, "gold", "sensor")

# IC mux CD74HC4067 SOIC-24 lebar (badan 7,5 x 15,4, sumbu panjang searah Y) + C1 100 nF 0805, sisi atas
icx, icy = FPD["U13"][3:5]
add("IC mux CD74HC4067 SOIC-24", try_fillet(box(icx - 3.75, icx + 3.75, icy - 7.7, icy + 7.7, SZ_TOP + 0.15, SZ_TOP + 2.45),
                                            "|Z", 0.2), "black_plastic", "sensor")
legs = None
for k in range(12):
    y = icy + 6.985 - k * 1.27
    for sx in (-1, 1):
        x0, x1 = sorted((icx + sx * 3.75, icx + sx * 5.15))
        legs = U(legs, box(x0, x1, y - 0.22, y + 0.22, SZ_TOP, SZ_TOP + 0.25))
        x0, x1 = sorted((icx + sx * 3.75, icx + sx * 4.15))
        legs = U(legs, box(x0, x1, y - 0.22, y + 0.22, SZ_TOP, SZ_TOP + 1.1))
add("IC mux kaki", legs, "steel", "sensor")
mark = cyl_z(icx - 2.3, icy + 6.2, SZ_TOP + 2.45, 0.03, 0.5)
mark = U(mark, text("HC4067", 1.4, icx, icy, SZ_TOP + 2.45, 90))
add("IC mux tanda", mark, "silk", "sensor")
cx_, cy_, cang = FPD["C1"][3:6]
add("C 100 nF mux", cbox(cx_, cy_, 2.0, 1.25, SZ_TOP, SZ_TOP + 0.6, cang), "cap_smd", "sensor")

# J1 JST XH 8 pin vertikal (B8B-XH-A): rumah 22,4 x 5,75 x 7, pin berjarak 2,5 mm
XH_L, XH_W, XH_H = 22.4, 5.75, 7.0


def jst_xh(x, y, ang, z0):
    """header JST XH 8 pin tegak + steker kabelnya; (x, y) = tengah rumah"""
    body = cbox(x, y, XH_L, XH_W, z0, z0 + XH_H, ang).cut(cbox(x, y, XH_L - 1.6, XH_W - 1.6, z0 + 1.5, z0 + XH_H + 1, ang))
    plug = cbox(x, y, XH_L - 1.8, XH_W - 1.8, z0 + 2.0, z0 + XH_H + 4.0, ang)
    return body, plug


j1x, j1y, j1ang = FPD["J1"][3:6]
J1C = local(j1x, j1y, j1ang, 8.75, 0.0)                 # tengah rumah (pin 1 di titik asal footprint)
j1_body, j1_plug = jst_xh(*J1C, j1ang, SZ_TOP)
print("J1 sensor", [round(v, 2) for v in (j1x, j1y, j1ang)], "tengah", [round(v, 2) for v in J1C])
add("Header JST XH J1", j1_body, "jst", "sensor")
add("Steker JST XH J1", j1_plug, "jst_plug", "sensor")


# skid nilon di kedua baut H1/H2 (usulan: rev B tidak punya lubang skid terpisah): baut nilon dari bawah dengan
# kepala kubah menyentuh lantai, spacer nilon 4 mm di antara papan, mur di atas PCB utama
def skid(x, y, z0, r):
    dome = cq.Workplane("XY").sphere(r + 1.0).translate((x, y, z0 + r + 1.0)).intersect(
        box(x - r - 2, x + r + 2, y - r - 2, y + r + 2, z0, z0 + 2.0))
    add("Skid nilon", dome.union(cyl_z(x, y, z0 + 1.5, SB_Z - z0 - 1.5, r)), "nylon", "sensor")


for x, y in SB_HOLES:
    skid(x, y, 0.0, 2.4)
    add("Spacer nilon 4 mm", cyl_z(x, y, SZ_TOP, PCB_Z - SZ_TOP, 2.4).cut(cyl_z(x, y, SZ_TOP - 1, 6, 1.6)), "nylon")
    add("Mur M3", hexnut(x, y, TOP, 2.4), "chrome")

# ============================== PCB UTAMA ==============================
# bentuk "mobil F1" (pilihan user 22/10): pinggang selebar celah antar roda (74), sidepod 100 di depan roda, lengkung
# menyempit ke hidung 54 yang menutupi tengah PCB sensor (sisi atas PCB sensor di situ cuma komponen < 1 mm; celah
# antar papan 4 mm). MAIN_R = setengah kanan (x, y, jari-jari sudut) dari belakang ke depan; dibaca juga oleh
# hardware/tools/gen_pcb_utama_awal.py untuk Edge.Cuts KiCad.
MAIN_R = [(37, -34, 10), (37, 20, 3), (50, 23.5, 3), (50, 54, 6), (27, 65, 8), (27, 84, 8), (12, 93, 5)]


def fillet_outline(right):
    """poligon simetris dengan jari-jari sudut per titik -> (wire CadQuery, polyline rapat untuk offset/silk)"""
    pts = [(0.0, right[0][1], 0)] + list(right) + [(0.0, right[-1][1], 0)]
    pts = pts[1:-1] + [(-x, y, r) for x, y, r in reversed(right)]
    n, segs, dense = len(pts), [], []
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
        mid = (c[0] - bis[0] / lb * r, c[1] - bis[1] / lb * r)
        segs.append((p1, mid, p2))
        a1, a2 = math.atan2(p1[1] - c[1], p1[0] - c[0]), math.atan2(p2[1] - c[1], p2[0] - c[0])
        da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        dense += [(c[0] + r * math.cos(a1 + da * k / 8), c[1] + r * math.sin(a1 + da * k / 8)) for k in range(9)]
    edges = []
    for i, (p1, mid, p2) in enumerate(segs):
        edges.append(cq.Edge.makeThreePointArc(cq.Vector(*p1, 0), cq.Vector(*mid, 0), cq.Vector(*p2, 0)))
        q = segs[(i + 1) % n][0]
        edges.append(cq.Edge.makeLine(cq.Vector(*p2, 0), cq.Vector(*q, 0)))
    return cq.Wire.assembleEdges(edges), dense


MAIN_WIRE, MAIN_PTS = fillet_outline(MAIN_R)
HOLES_MAIN = list(SB_HOLES) + [(sx * 33, sy * 20) for sx in (-1, 1) for sy in (-1, 1)]
main = cq.Workplane("XY").add(cq.Solid.extrudeLinear(cq.Face.makeFromWires(MAIN_WIRE), cq.Vector(0, 0, T))) \
    .translate((0, 0, PCB_Z))
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
          text("LTM", 2.0, 0, -25.5, TOP), text("v16", 1.4, 0, -28.2, TOP)):
    silk = U(silk, t)
for x in (-22, 22):
    try:
        silk = U(silk, cq.Workplane("XY").circle(4.6).circle(4.25).extrude(0.05).translate((x, BTN_Y, TOP)))
    except Exception:
        pass
add("Silkscreen utama", silk, "silk")

# ---------- J5 JST XH 8 pin (kabel ke J1 PCB sensor), sejajar tepi miring sidepod kiri ----------
# hidung dipakai baut H1/H2 PCB sensor + OLED + tombol, sidepod kanan dipakai buzzer/S8050, jadi J5 di sidepod kiri
_e0, _e1 = (-27.0, 65.0), (-50.0, 54.0)               # tepi miring sidepod kiri (dari hidung ke bahu)
_d = ((_e1[0] - _e0[0]) / math.dist(_e0, _e1), (_e1[1] - _e0[1]) / math.dist(_e0, _e1))
J5ANG = math.degrees(math.atan2(_d[1], _d[0]))
J5C = (_e0[0] + 13.5 * _d[0] - 4.5 * _d[1], _e0[1] + 13.5 * _d[1] + 4.5 * _d[0])
j5_body, j5_plug = jst_xh(*J5C, J5ANG, TOP)
add("Header JST XH J5", j5_body, "jst")
add("Steker JST XH J5", j5_plug, "jst_plug")

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
add("Elko C1 100uF", cyl_z(-37, 40.0, TOP + 0.3, 10.7, 3.15), "elko")
add("Elko C1 tutup", cyl_z(-37, 40.0, TOP + 11.0, 0.15, 2.85), "shield")
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

# ---------- kabel JST XH 8 jalur: J5 (PCB utama) -> J1 (PCB sensor), pin n ke pin n ----------
# pin 1 J5 di ujung dekat hidung supaya 8 kabel tidak bersilangan menuju J1 (pin 1 di kanan). Kabel diikat jadi satu
# bundel yang menyusuri tepi kiri hidung (di sebelah kiri tombol A, tidak menutupi tombol/OLED), lalu masuk J1 dari depan.
WIRE_R = 0.65                                            # kabel AWG 26 berisolasi
WIRE_MAT = ["wire_red", "wire_yel", "wire_blk"] + ["wire_blu"] * 5     # +5V, +3V3, GND, MUX_S3..S0, MUX_SIG
CABLE_WAY = [(-34.0, 68.0, TOP + 3.0), (-21.0, 89.0, TOP + 6.0)]     # titik lintasan bundel kabel (kiri tombol A)


def wire(p0, p3, way, off, bend=3.0):
    """kabel bulat: tegak dari steker, lewat titik lintasan (digeser off ke kanan arah jalan), tegak masuk steker;
    segmen lurus dengan tikungan membulat (seperti kabel yang ditekuk tangan)"""
    pts = [p0, (p0[0], p0[1], p0[2] + 4.0)]
    for i, w in enumerate(way):
        a = way[i - 1] if i else p0
        b = way[i + 1] if i + 1 < len(way) else p3
        h = (b[0] - a[0], b[1] - a[1])
        n = math.hypot(*h)
        pts.append((w[0] + off * h[1] / n, w[1] - off * h[0] / n, w[2]))
    pts += [(p3[0], p3[1], p3[2] + 4.0), p3]
    V = [cq.Vector(*p) for p in pts]
    edges, start = [], V[0]
    for i in range(1, len(V) - 1):
        A, B, C = V[i - 1], V[i], V[i + 1]
        u, v = (A - B).normalized(), (C - B).normalized()
        th = math.acos(max(-1.0, min(1.0, u.dot(v))))
        if th > math.radians(175):                       # hampir lurus: tanpa tikungan
            continue
        t = min(bend / math.tan(th / 2), 0.45 * (A - B).Length, 0.45 * (C - B).Length)
        r = t * math.tan(th / 2)
        bis = (u + v).normalized()
        cen = B + bis * (r / math.sin(th / 2))
        p1, p2 = B + u * t, B + v * t
        edges += [cq.Edge.makeLine(start, p1), cq.Edge.makeThreePointArc(p1, cen - bis * r, p2)]
        start = p2
    edges.append(cq.Edge.makeLine(start, V[-1]))
    path = cq.Wire.assembleEdges(edges)
    return cq.Workplane(cq.Plane(origin=p0, xDir=(1, 0, 0), normal=(0, 0, 1))).circle(WIRE_R).sweep(cq.Workplane().add(path))


_d5 = (math.cos(math.radians(J5ANG)), math.sin(math.radians(J5ANG)))
for k in range(8):
    q5 = (J5C[0] - (8.75 - 2.5 * k) * _d5[0], J5C[1] - (8.75 - 2.5 * k) * _d5[1], TOP + XH_H + 4.0)
    q1 = (*local(j1x, j1y, j1ang, 2.5 * k, 0.0), SZ_TOP + XH_H + 4.0)
    add(f"Kabel JST XH pin {k + 1}", wire(q5, q1, CABLE_WAY, (3.5 - k) * 1.4), WIRE_MAT[k])

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
    "pt_clear": ("#cfd8de", 0.15, 0.2), "cap_smd": ("#b98a5a", 0.6, 0.0), "jst_plug": ("#f7f3e8", 0.55, 0.0),
    "wire_red": ("#d3202e", 0.5, 0.0), "wire_yel": ("#e8b923", 0.5, 0.0), "wire_blk": ("#222326", 0.5, 0.0), "wire_blu": ("#2f5fb3", 0.5, 0.0),
}
meshes = []
for name, shape, mat, group in parts:
    verts, tris = shape.tessellate(0.03, 0.25)
    meshes.append({"n": name, "m": mat, "g": group,
                   "p": [round(c, 2) for v in verts for c in (v.x, v.y, v.z)],
                   "i": [i for t in tris for i in t]})
json.dump({"mats": MATS, "meshes": meshes}, open(f"{OUT}/model.json", "w"), separators=(",", ":"))

assy = cq.Assembly(name="LTM_v16")
for k, (name, shape, mat, group) in enumerate(parts):
    h = MATS[mat][0]
    col = cq.Color(int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255)
    assy.add(shape, name=f"{k:03d}_{name.replace(' ', '_').replace('(', '').replace(')', '')}", color=col)
exportAssembly(assy, f"{OUT}/step/LTM_v16_rakitan.step")

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
for x, y, ang in SENS:                             # kotak badan QRE1113GR 2,9 x 3,6, koordinat dari PCB rev B
    marks = U(marks, cq.Workplane("XY").rect(2.9, 3.6).extrude(1).rotate((0, 0, 0), (0, 0, 1), ang).translate((x, y - F, 0)))
cq.exporters.export(marks.faces("<Z"), f"{OUT}/dxf/pcb_sensor_posisi_qre1113.dxf", cq.exporters.ExportTypes.DXF)
with open(f"{OUT}/dxf/pcb_sensor_posisi_qre1113.csv", "w") as fcsv:
    fcsv.write("no,x_mm,y_mm_dari_tepi_depan,putar_deg_kicad\n")
    for k, (x, y, ang) in enumerate(SENS):
        fcsv.write(f"{k + 1},{x:.2f},{F - y:.2f},{ang:+.1f}\n")

bb = cq.Compound.makeCompound([p[1] for p in parts]).BoundingBox()
print(f"parts {len(parts)}  bbox X {bb.xmin:.1f}..{bb.xmax:.1f}  Y {bb.ymin:.1f}..{bb.ymax:.1f}  Z {bb.zmin:.1f}..{bb.zmax:.1f}")

# cek tabrakan antar bagian (CHECK=1): pasangan yang memang bersentuhan/masuk (as di velg, baut di lubang, dll.) dilewati
if os.environ.get("CHECK"):
    OK = [("As roda", "Velg"), ("As roda", "Gearbox"), ("Baut", "Pad"), ("Mur", "PCB"), ("Spacer", "Pad"),
          ("Baterai 18650", "Holder"), ("kutub", "Holder"), ("Silkscreen", "Pad"), ("OLED lubang", "OLED"),
          ("OLED tampilan", "OLED kaca"), ("Kabel JST", "Steker JST"), ("Kabel JST", "Kabel JST"), ("Tutup", "Tombol"), ("Elko C1 tutup", "Elko"),
          ("Ban merah", "Velg"), ("Dioda 1N5819 cincin", "Dioda"), ("Skid", "PCB sensor"), ("Silkscreen", ""),
          ("Pad lubang", "Dudukan"), ("OLED kaca", "OLED flex"),
          ("QRE1113GR lensa", "QRE1113GR x12"), ("QRE1113GR kaki", "QRE1113GR x12"), ("IC mux", "IC mux"),
          ("Mur M3", "Pad"), ("Mur M3", "PCB utama")]

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
