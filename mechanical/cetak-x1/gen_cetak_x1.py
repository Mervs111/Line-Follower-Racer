"""Bagian cetak 3D LFM X1 (badan robot konsep v18), siap slice untuk Bambu Lab A1 (22/11/2026).

Konsep v18 (mechanical/konsep-v18/) baru berupa kotak-kotak. Skrip ini membuat versi cetaknya dengan ukuran yang sama;
posisi lubang dan kaki THT dibaca langsung dari KiCad (PCB utama rev B, PCB sensor rev C, board interface rev B):
  sasis             skid plate 2 mm + bibir tepi, dudukan kedua motor N20 (rel + ganjal gearbox), 4 boss M3 PCB utama
                    (baut kepala benam dari bawah), 4 boss baut tutup klem (mur di kantong bawah), lubang PCB sensor,
                    bibir + 2 celah strap pack 2S, jendela untuk kaki THT PCB utama dan piringan encoder
  tutup klem        menekan motor dari atas, 2 baut M3 x 16 per motor (kiri = cermin kanan)
  rangka interface  pelat 2,5 mm + 4 kaki di baut M3 PCB utama, memikul board interface (dari konsep v18; boss depan
                    dipapas supaya tidak di atas tepi ESP32 DevKit)
  velg + ban TPU    O34 x 18, lubang D untuk as N20 (tekan + lem), ban TPU dipasang meregang di antara 2 flens
  skid sensor       tumpuan depan di bawah lubang H1/H2 PCB sensor, mur M3 tertanam (dipakai selama ball caster belum
                    ada; ball caster di RAB belum punya ukuran)
  spacer sensor     cincin 3,6 mm di antara PCB sensor dan sasis
  uji               potongan dudukan motor kanan + blok 3 ukuran lubang D, dicetak dulu sebelum sasis penuh
Semua benda = tumpukan ekstrusi 2D (shapely; cara yang sama dengan gen_rakitan_x2.py), jadi STL tertutup rapat dan
semua bagian bisa dicetak tanpa support pada posisi cetaknya.

Keluaran (folder ini):
  stl/*.stl              posisi cetak (alas di z = 0), mm
  cetak-x1-model.json    mesh untuk index.html: rakitan (mesh konsep v18 + bagian cetak) dan susunan di alas cetak A1
Hasil cek (STL tertutup, tabrakan terhadap komponen konsep v18 dan KiCad, panjang baut, massa) dicetak di akhir.

Koordinat robot (mm): x kanan, y maju, z naik dari lantai, (0, 0) = tengah poros roda; KiCad X = 200 + x,
Y = 180,55 - y (sama di semua proyek PCB X1).
Jalankan: py mechanical/cetak-x1/gen_cetak_x1.py   (butuh KiCad 10 untuk membaca PCB, numpy, shapely >= 2.1, trimesh)
"""
import base64, json, math, os, struct, subprocess, sys
import numpy as np
import shapely
import shapely.affinity as aff
from shapely.geometry import Polygon, box as sbox
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
KICAD_PY = r"C:\Program Files\KiCad\10.0\bin\python.exe"

# ------------------------------ ukuran (konsep v18 + KiCad) ------------------------------
R_W, W_T, WX = 17.0, 18.0, 39.5             # ban O34 x 18, sisi dalam ban
WO, WI = WX + W_T, WX - 1.5                 # sisi luar ban, tepi coakan roda
AX_Z = R_W                                  # tinggi poros
CH_Z0, CH_Z1 = 10.0, 12.0                   # pelat sasis
RIM_W, RIM_Z = 1.6, 14.5                    # bibir tepi (pengaku), puncaknya 0,5 mm di bawah PCB utama
WELL = 20.5                                 # coakan roda: setengah panjang
NOSE_HW, NOSE_Y = 31.0, 93.0                # hidung sasis
K_SIDE = (57.5 - NOSE_HW) / 125.0           # kemiringan sisi = sisi PCB utama trapesium
TAIL_Y = -47.5                              # v18 -43: ekor diperpanjang supaya celah strap belakang muat

MB_Z0 = 15.0                                # PCB utama rev B
MBT = MB_Z0 + 1.6
MB_HOLE = [(-38.5, 29.0), (38.5, 29.0), (-32.5, 56.0), (32.5, 56.0)]
SENS_H = [(-4.75, 85.55), (4.75, 85.55)]    # H1/H2 PCB sensor
SB_Z = 4.8                                  # sisi bawah PCB sensor (muka QRE1113GR +-3,1 mm dari lantai)
SZ_TOP = SB_Z + 1.6

SOCK, HDR = 8.5, 2.54                       # board interface rev B di atas socket J6 + header susun
IB = (-19.5, 19.5, 34.0, 79.0)
IB_Z0 = MBT + 2 * SOCK + HDR                # 36,14
IB_HOLE = [(-17.0, 62.0), (17.0, 62.0), (-17.0, 76.5), (17.0, 76.5)]
FR_Z1 = IB_Z0                               # rangka interface: pelat di bawah tepi board
FR_Z0 = FR_Z1 - 2.5
RAIL_X0, RAIL_X1 = IB[1] + 0.4, IB[1] + 3.8
LEG_R, BOSS_R = 3.25, 2.7
ESP_EDGE_Y = 46.15 + 14.15                  # tepi depan PCB ESP32 DevKit (lebar 28,3)

# motor N20 (model v16): gearbox x 28,5..37,5, kaleng 13,5..28,5, lebar 12, tinggi 10 (z 12..22), encoder di x 5..13
GB_X0, MOT_Z1 = 28.5, AX_Z + 5.0
SLOT_HW = 6.2                               # setengah lebar alur motor (motor 12 mm + 0,2 tiap sisi)
RAIL_X = (14.5, 37.5)
RAIL_FY, RAIL_RY, RAIL_Z = 8.4, 11.3, 18.0  # rel depan y 6,2..8,4; rel belakang y -11,3..-6,2 = penahan depan pack
LEDGE = (24.5, GB_X0 - 0.1, 4.8, 13.2)      # ganjal di sudut bawah alur: menahan gearbox masuk ke tengah
ENC_WIN = (3.5, 14.0, 7.2)                  # jendela pelat di bawah piringan encoder (r 6,2 > setengah tinggi motor)
CAP_BOLT = [(26.0, 12.6), (33.0, -12.0)]    # baut tutup klem (sisi kanan), mur di kantong bawah sasis
CAP_BOSS_R, CAP_BOSS_Z = 3.75, MOT_Z1 - 0.4  # boss 0,4 mm di bawah tutup: tutup melentur menekan motor
CAP_Z1 = MOT_Z1 + 3.0

PACK = (-27.0, 27.0, -42.3, -11.3)          # kantong pack 14500 2S (listing 50 x 30 x 15) + kelonggaran
LIP_Z = CH_Z1 + 4.0
STRAP_HW = 8.75                             # strap velcro 16 mm
SLOTS = [(-44.3, -42.1), (-11.1, -8.9)]     # celah strap di belakang dan di depan pack

M3, M3_TAP, M2_TAP, NUT_AF, NUT_H = 3.4, 2.5, 1.7, 5.7, 2.6
CSK = [(10.0, 3.2), (10.4, 2.8), (10.8, 2.4), (11.2, 2.0), (11.5, M3 / 2)]   # kepala benam M3 90 derajat (z, r)

PETG, PLA, TPU = 1.27, 1.24, 1.21           # g/cm3
BED = 256.0                                 # Bambu Lab A1


# ------------------------------ geometri 2D ------------------------------
def rrect(x0, x1, y0, y1, r=0.0):
    b = sbox(x0, y0, x1, y1)
    return b.buffer(-r, join_style="mitre").buffer(r, quad_segs=8) if r > 0 else b


def circ(x, y, r, n=48):
    return Polygon([(x + r * math.cos(2 * math.pi * k / n), y + r * math.sin(2 * math.pi * k / n)) for k in range(n)])


def hexa(x, y, af):
    rc = af / math.sqrt(3)
    return Polygon([(x + rc * math.cos(math.pi / 3 * k), y + rc * math.sin(math.pi / 3 * k)) for k in range(6)])


def mirror_x(g):
    return aff.scale(g, -1, 1, origin=(0, 0))


def both(g):
    return unary_union([g, mirror_x(g)])


def ring(x, y, ro, ri, n=96):
    return circ(x, y, ro, n).difference(circ(x, y, ri, n))


def d_hole(x, y, d, flat):
    """lubang D as N20: lingkaran O d, sisi rata sejauh flat dari pusat (as asli O3, tebal di sisi rata 2,5)"""
    r = d / 2
    return circ(x, y, r, 40).intersection(sbox(x - r, y - r, x + r, y + flat))


def fillet_dense(right, mirror=True):
    """poligon bersudut tumpul: right = [(x, y, jari-jari)] sisi kanan, dicerminkan ke kiri (dari konsep v18)"""
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


def polys(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [q for h in getattr(g, "geoms", []) for q in polys(h)]


def clean(g):
    """buang serpih dan titik kembar (perpotongan yang jatuh hampir tepat di sudut lingkaran -> ruas nol, STL bocor)"""
    if g.is_empty:
        return Polygon()
    g = shapely.remove_repeated_points(g.buffer(0), 1e-5)
    return unary_union([p for p in polys(g) if p.area > 1e-3])


# ------------------------------ benda tumpukan ekstrusi (sama dengan gen_rakitan_x2.py) ------------------------------
class Layered:
    """benda = daftar fitur (z0, z1, poligon, +1 tambah / -1 potong). Tiap selang antar-ketinggian dihitung satu poligon
    (tambah - potong, lalu dipotong clip kalau ada); dinding dari cincin poligon, tutup dari selisih selang bawah-atas."""

    def __init__(self, name, clip=None):
        self.name, self.feats, self.clip = name, [], clip

    def add(self, z0, z1, g):
        self.feats.append((z0, z1, g, 1))
        return self

    def cut(self, z0, z1, g):
        self.feats.append((z0, z1, g, -1))
        return self

    def slabs(self):
        lv = sorted({round(z, 4) for f in self.feats for z in f[:2]})
        out = []
        for a, b in zip(lv, lv[1:]):
            m = (a + b) / 2
            add = [g for z0, z1, g, s in self.feats if s > 0 and z0 <= m <= z1]
            cut = [g for z0, z1, g, s in self.feats if s < 0 and z0 <= m <= z1]
            p = unary_union(add) if add else Polygon()
            if cut:
                p = p.difference(unary_union(cut))
            if self.clip is not None:
                p = p.intersection(self.clip)
            out.append((a, b, clean(p)))
        return lv, out

    def triangles(self):
        lv, sl = self.slabs()
        walls, tri = [], []
        for a, b, p in sl:
            for poly in polys(p):
                poly = orient(poly, 1.0)
                for rg in (poly.exterior, *poly.interiors):
                    c = list(rg.coords)[:-1]
                    walls += [(c[i], c[(i + 1) % len(c)], a, b) for i in range(len(c))]
        empty = Polygon()
        for i, z in enumerate(lv):
            below = sl[i - 1][2] if i > 0 else empty
            above = sl[i][2] if i < len(sl) else empty
            tri += cap(below.difference(above), z, 1) + cap(above.difference(below), z, -1)
        # titik tiap ketinggian (sudut tutup + ujung dinding): dinding dipecah di titik yang jatuh di tepinya supaya
        # tidak ada sambungan-T (STL tertutup rapat)
        pts = {z: set() for z in lv}
        for t in tri:
            for x, y, z in t:
                pts[z].add((x, y))
        for (p, q, a, b) in walls:
            pts[a].update((p, q)), pts[b].update((p, q))
        arr = {z: np.array(sorted(s)) for z, s in pts.items()}
        for p, q, a, b in walls:
            tri += zipper(p, q, a, b, on_edge(arr[a], p, q), on_edge(arr[b], p, q))
        # titik potong yang dihitung dua kali (tutup dan dinding) beda di digit terakhir: satukan di grid 1 nm, lalu
        # buang segitiga yang jadi nol (ruas nol) supaya tiap rusuk tepat dipakai dua segitiga
        tri = np.round(np.array(tri, float), 6)
        ok = ~((tri[:, 0] == tri[:, 1]).all(1) | (tri[:, 1] == tri[:, 2]).all(1) | (tri[:, 0] == tri[:, 2]).all(1))
        return tri[ok]


def on_edge(P, p, q, tol=1e-6):
    """titik P yang jatuh di ruas p-q, urut dari p ke q, termasuk kedua ujung: [(t, (x, y))]. Koordinat titik asli
    dipakai apa adanya (bukan hasil interpolasi t) supaya sama persis dengan sudut tutup di ketinggian itu."""
    pa, qa = np.array(p), np.array(q)
    d = qa - pa
    L2 = d @ d
    t = (P - pa) @ d / L2
    off = np.abs((P[:, 0] - pa[0]) * d[1] - (P[:, 1] - pa[1]) * d[0]) / math.sqrt(L2)
    m = (off < tol) & (t > 1e-7) & (t < 1 - 1e-7)
    mid = sorted({(round(float(tt), 9), (float(x), float(y))) for tt, (x, y) in zip(t[m], P[m])})
    return [(0.0, tuple(p))] + mid + [(1.0, tuple(q))]


def zipper(p, q, a, b, tb, tt):
    """dinding p->q dari z a ke b, tepi bawah dipecah di titik tb, tepi atas di tt; normal keluar = kanan arah p->q"""
    out, i, j = [], 0, 0
    while i < len(tb) - 1 or j < len(tt) - 1:
        if j == len(tt) - 1 or (i < len(tb) - 1 and tb[i + 1][0] <= tt[j + 1][0]):
            out.append(((*tb[i][1], a), (*tb[i + 1][1], a), (*tt[j][1], b)))
            i += 1
        else:
            out.append(((*tb[i][1], a), (*tt[j + 1][1], b), (*tt[j][1], b)))
            j += 1
    return out


def cap(g, z, up):
    out = []
    for poly in polys(g):
        if poly.area < 1e-4:
            continue
        for t in shapely.constrained_delaunay_triangles(poly).geoms:
            c = list(t.exterior.coords)[:3]
            ar = (c[1][0] - c[0][0]) * (c[2][1] - c[0][1]) - (c[1][1] - c[0][1]) * (c[2][0] - c[0][0])
            if abs(ar) < 1e-7:
                continue
            if (ar > 0) != (up > 0):
                c = [c[0], c[2], c[1]]
            out.append(tuple((x, y, z) for x, y in c))
    return out


def volume(tri):
    return float(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6)


def write_stl(tri, path, name):
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as f:
        f.write(name.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(tri)))
        f.write(rec.tobytes())


def flip_x(tri):
    """putar 180 derajat terhadap sumbu x (muka atas jadi alas), tetap rotasi murni jadi arah normal benar"""
    return tri * np.array([1.0, -1.0, -1.0])


def to_bed(tri):
    """geser ke alas: tengah kotak pembatas di (0, 0), dasar di z 0"""
    lo, hi = tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)
    return tri - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])


# ------------------------------ data KiCad ------------------------------
KICAD_DUMP = r'''
import json, sys, pcbnew
out = {}
for key, path in json.loads(sys.argv[1]).items():
    b = pcbnew.LoadBoard(path)
    R = lambda p: (round(pcbnew.ToMM(p.x) - 200.0, 4), round(180.55 - pcbnew.ToMM(p.y), 4))
    fps = []
    for fp in b.GetFootprints():
        bb = fp.GetBoundingBox(False)
        (x0, y1), (x1, y0) = R(bb.GetOrigin()), R(bb.GetEnd())
        pads = [dict(p=R(pd.GetPosition()), s=[pcbnew.ToMM(pd.GetBoundingBox().GetWidth()),
                                                 pcbnew.ToMM(pd.GetBoundingBox().GetHeight())],
                     d=pcbnew.ToMM(pd.GetDrillSize().x), pth=pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)
                for pd in fp.Pads()]
        fps.append(dict(ref=fp.GetReference(), side="B" if fp.IsFlipped() else "F", p=R(fp.GetPosition()),
                        bb=[x0, x1, y0, y1], pads=pads))
    out[key] = fps
print(json.dumps(out))
'''


def kicad_data():
    boards = {"utama": "hardware/pcb-utama/pcb-utama.kicad_pcb", "sensor": "hardware/sensor-garis/sensor-garis.kicad_pcb",
              "interface": "hardware/board-interface/board-interface.kicad_pcb"}
    arg = json.dumps({k: os.path.join(REPO, v) for k, v in boards.items()})
    r = subprocess.run([KICAD_PY, "-c", KICAD_DUMP, arg], capture_output=True, text=True, check=True)
    return json.loads(r.stdout.strip().splitlines()[-1])


def holes(fps, prefix="H"):
    return sorted((round(f["p"][0], 2), round(f["p"][1], 2)) for f in fps if f["ref"].startswith(prefix)
                  and f["ref"][1:].isdigit())


# ------------------------------ bagian cetak ------------------------------
def plate_outline():
    def sx(y):
        return min(NOSE_HW + (NOSE_Y - y) * K_SIDE, WO)
    front = [(WI, WELL, 1.5), (sx(WELL), WELL, 1.5), (NOSE_HW, NOSE_Y, 5)]
    wing = [(WO, -32.0, 3), (sx(-WELL), -WELL, 1.5), (WI, -WELL, 1.5)]
    return Polygon(fillet_dense([(30.0, TAIL_Y, 4)] + wing + front))


def tht_windows(utama, outline):
    """jendela tembus di bawah kaki THT PCB utama: ekor pin socket female +-3 mm, celah PCB-sasis hanya 3 mm"""
    pads = [circ(*pd["p"], max(pd["s"]) / 2 + 0.7, 24) for f in utama for pd in f["pads"] if pd["pth"]]
    win = unary_union(pads).buffer(1.2, quad_segs=4).buffer(-1.2, quad_segs=4)
    keep = unary_union([circ(x, y, 4.0) for x, y in MB_HOLE])
    win = clean(win.difference(keep).intersection(outline.buffer(-1.2)))
    rest = polys(outline.difference(win))                 # pulau pelat yang terkurung jendela ikut dibuang
    main = max(rest, key=lambda q: q.area)
    return clean(unary_union([win] + [q for q in rest if q is not main]))


def make_sasis(utama, clip=None):
    p = Layered("Sasis", clip)
    out = plate_outline()
    win = tht_windows(utama, out)
    motor_zone = both(sbox(3.0, -6.5, 39.0, 6.5))
    p.add(CH_Z0, CH_Z1, out)
    p.add(CH_Z1, RIM_Z, out.difference(out.buffer(-RIM_W)).difference(motor_zone))
    # dudukan motor: rel kiri-kanan alur, ganjal gearbox, boss baut tutup klem
    x0, x1 = RAIL_X
    p.add(CH_Z1, RAIL_Z, both(unary_union([sbox(x0, SLOT_HW, x1, RAIL_FY), sbox(x0, -RAIL_RY, x1, -SLOT_HW)])))
    lx0, lx1, ly, lz = LEDGE
    p.add(CH_Z1, lz, both(unary_union([sbox(lx0, ly, lx1, SLOT_HW), sbox(lx0, -SLOT_HW, lx1, -ly)])))
    p.add(CH_Z1, CAP_BOSS_Z, both(unary_union([circ(x, y, CAP_BOSS_R) for x, y in CAP_BOLT])))
    # boss PCB utama
    p.add(CH_Z1, MB_Z0, unary_union([circ(x, y, 3.5) for x, y in MB_HOLE]))
    # bibir pack: belakang (di kiri-kanan strap) + 4 sudut; depan = rel belakang motor
    px0, px1, py0, py1 = PACK
    lips = both(unary_union([sbox(10.0, py0 - 1.6, px1 + 1.6, py0), sbox(px1, py0, px1 + 1.6, py0 + 6.0),
                             sbox(px1, py1 - 6.0, px1 + 1.6, py1)]))
    p.add(CH_Z1, LIP_Z, lips)
    # potongan
    p.cut(CH_Z0, RIM_Z, win)
    p.cut(CH_Z0, CH_Z1, both(sbox(ENC_WIN[0], -ENC_WIN[2], ENC_WIN[1], ENC_WIN[2])))
    for y0, y1 in SLOTS:
        p.cut(CH_Z0, CH_Z1, sbox(-STRAP_HW, y0, STRAP_HW, y1))
    for x, y in CAP_BOLT:
        for s in (1, -1):
            p.cut(CH_Z0, CAP_BOSS_Z, circ(s * x, y, M3 / 2, 32))
            p.cut(CH_Z0, CH_Z0 + NUT_H, hexa(s * x, y, NUT_AF))
    for x, y in MB_HOLE:
        p.cut(CH_Z0, MB_Z0, circ(x, y, M3 / 2, 32))
        for (za, r), (zb, _) in zip(CSK, CSK[1:]):
            p.cut(za, zb, circ(x, y, r, 32))
    for x, y in SENS_H:
        p.cut(CH_Z0, CH_Z1, circ(x, y, M3 / 2, 32))
    return p


def cap_plan(s):
    body = sbox(15.5, -SLOT_HW, 36.5, SLOT_HW)
    g = unary_union([body.union(circ(x, y, CAP_BOSS_R)).convex_hull for x, y in CAP_BOLT])
    g = g.buffer(-1.0).buffer(1.0).difference(unary_union([circ(x, y, M3 / 2, 32) for x, y in CAP_BOLT]))
    return g if s > 0 else mirror_x(g)


def make_cap(s):
    return Layered("Tutup klem motor " + ("kanan" if s > 0 else "kiri")).add(MOT_Z1, CAP_Z1, cap_plan(s))


def make_frame():
    """rangka interface konsep v18: pelat di bawah tepi board interface + 4 kaki di lubang M3 PCB utama"""
    p = Layered("Rangka interface")
    plate = [sbox(-RAIL_X1, IB[2] - 2.0, RAIL_X1, IB[2] + 2.5)]                       # balok belakang (baris tombol)
    for s in (-1, 1):
        def sb(xa, xb, ya, yb):
            return sbox(min(s * xa, s * xb), ya, max(s * xa, s * xb), yb)
        plate.append(sb(RAIL_X0, RAIL_X1, IB[2] - 2.0, IB[3]))                       # rel samping di luar tepi board
        for hx, hy in IB_HOLE[1::2]:
            plate.append(sb(hx - BOSS_R, RAIL_X0, hy - BOSS_R, min(hy + BOSS_R, IB[3])))   # tab di bawah lubang M2
            boss = circ(s * hx, hy, BOSS_R, 24)
            if hy < 70:                                                              # papas di atas tepi ESP32 DevKit
                boss = boss.intersection(sbox(-50, ESP_EDGE_Y + 0.1, 50, 100))
            p.add(FR_Z0 - (2.4 if hy < 70 else 5.6), FR_Z0, boss)
        plate.append(sb(RAIL_X1, 32.5, 53.0, 59.0))                                  # lengan ke kaki depan
        plate.append(Polygon([(s * RAIL_X1, 32.0), (s * 37.0, 25.9), (s * 41.6, 30.6), (s * RAIL_X1, 37.0)]))
    p.add(FR_Z0, FR_Z1, unary_union(plate))
    p.add(MBT, FR_Z1, unary_union([circ(x, y, LEG_R, 32) for x, y in MB_HOLE]))
    p.cut(MBT, FR_Z1, unary_union([circ(x, y, M3 / 2, 32) for x, y in MB_HOLE]))
    p.cut(FR_Z0 - 6, FR_Z1, unary_union([circ(x, y, M2_TAP / 2, 16) for x, y in IB_HOLE]))
    return p


# velg + ban, dibangun langsung di posisi cetak: sumbu = z, muka luar di alas (z 0), muka dalam (sisi motor) di z 18
V_RF, V_RS, V_RI, V_RH = 14.8, 14.0, 12.4, 4.6   # flens (ban meregang 7 % saat dipasang), dudukan ban, rim, hub
V_BORE = (3.1, 1.05, 8.0)                         # lubang D: diameter, jarak sisi rata, dalam (as 10 mm ditekan
                                                  # sampai mentok -> celah velg-gearbox 2 mm)
T_RI, T_W = 13.8, 15.4                            # ban: jari-jari dalam (meregang 1,4 % di dudukan), lebar


def make_velg():
    p = Layered("Velg")
    holes = unary_union([circ(8.5 * math.cos(math.pi / 3 * k), 8.5 * math.sin(math.pi / 3 * k), 2.5, 32) for k in range(6)])
    p.add(0.0, 1.2, circ(0, 0, V_RF, 128)).add(1.2, 2.0, circ(0, 0, V_RS, 128)).cut(0.0, 2.0, holes)
    p.add(2.0, W_T, ring(0, 0, V_RS, V_RI, 128))
    p.add(W_T - 1.2, W_T - 0.6, ring(0, 0, V_RF, V_RI, 128))                         # flens dalam
    p.add(W_T - 0.6, W_T, ring(0, 0, V_RF - 0.5, V_RI, 128))                         # serong: ban lebih mudah masuk
    p.add(0.0, W_T, circ(0, 0, V_RH, 48))
    rib = sbox(V_RH - 0.3, -0.8, V_RI + 0.3, 0.8)
    p.add(2.0, 6.0, unary_union([aff.rotate(rib, 30 + 60 * k, origin=(0, 0)) for k in range(6)]))
    d, flat, depth = V_BORE
    p.cut(W_T - depth, W_T, d_hole(0, 0, d, flat))
    return p


def make_ban():
    p = Layered("Ban TPU")
    steps = [(0.0, 0.5, R_W - 0.6), (0.5, 1.0, R_W - 0.2), (1.0, T_W - 1.0, R_W), (T_W - 1.0, T_W - 0.5, R_W - 0.2),
             (T_W - 0.5, T_W, R_W - 0.6)]
    for z0, z1, r in steps:
        p.add(z0, z1, ring(0, 0, r, T_RI, 160))
    return p


SKID_C, SKID_HX, SKID_HY, SKID_R = (0.0, 85.55), 8.5, 4.5, 20.0


def make_skid():
    """batang 17 x 9 di bawah H1/H2 PCB sensor (koordinat robot, z 0..4,8), dasar = tudung bola R 20 (titik sentuh di
    tengah), mur M3 di kantong dari atas, lubang buntu sampai z 1,2"""
    cx, cy = SKID_C
    plan = rrect(cx - SKID_HX, cx + SKID_HX, cy - SKID_HY, cy + SKID_HY, SKID_HY - 0.01)
    rmax = max(math.dist(SKID_C, q) for q in plan.exterior.coords)
    zmax = SKID_R - math.sqrt(SKID_R ** 2 - rmax ** 2)
    p = Layered("Skid sensor")
    zs = np.round(np.arange(0.0, zmax, 0.1), 4).tolist() + [round(zmax, 4)]
    for za, zb in zip(zs, zs[1:]):
        zm = (za + zb) / 2
        p.add(za, zb, plan.intersection(circ(cx, cy, math.sqrt(SKID_R ** 2 - (SKID_R - zm) ** 2), 96)))
    p.add(zmax, SB_Z, plan)
    for x, y in SENS_H:
        p.cut(SB_Z - NUT_H, SB_Z, hexa(x, y, NUT_AF))
        p.cut(1.2, SB_Z, circ(x, y, M3 / 2, 32))
    return p


def make_spacer(x, y):
    return Layered("Spacer sensor").add(SZ_TOP, CH_Z0, ring(x, y, 3.2, M3 / 2, 32))


def make_bore_test():
    """blok uji lubang D: kiri ke kanan O3,0 / 3,1 / 3,2, ditandai 1 / 2 / 3 takik di sisi depan"""
    p = Layered("Uji lubang as").add(0.0, 10.0, rrect(-15.0, 15.0, -5.0, 5.0, 1.0))
    for k, (d, flat) in enumerate([(3.0, 1.0), (3.1, 1.05), (3.2, 1.1)]):
        x = -9.0 + 9.0 * k
        p.cut(10.0 - V_BORE[2], 10.0, d_hole(x, 0.0, d, flat))
        for j in range(k + 1):
            xt = x - 1.2 * k + 2.4 * j
            p.cut(9.0, 10.0, sbox(xt - 0.4, -5.1, xt + 0.4, -4.3))
    return p


# ------------------------------ cek ------------------------------
def clash(part, slabs, obst, ignore=()):
    hits = []
    for name, x0, x1, y0, y1, z0, z1 in obst:
        if any(name.startswith(s) for s in ignore):
            continue
        r = sbox(x0, y0, x1, y1)
        for a, b, p in slabs:
            if min(b, z1) - max(a, z0) > 0.05 and p.intersection(r).area > 0.05:
                hits.append(f"{part} <-> {name} (z {max(a, z0):.1f}..{min(b, z1):.1f})")
                break
    return hits


def gap(slabs, x0, x1, y0, y1, z0, z1):
    """jarak mendatar terkecil antara benda cetak dan kotak, pada selang z yang tumpang"""
    r, best = sbox(x0, y0, x1, y1), 1e9
    for a, b, p in slabs:
        if min(b, z1) - max(a, z0) > 0.05 and not p.is_empty:
            best = min(best, p.distance(r))
    return best


def watertight(tri):
    import trimesh
    m = trimesh.Trimesh(vertices=tri.reshape(-1, 3), faces=np.arange(len(tri) * 3).reshape(-1, 3), process=True)
    return bool(m.is_watertight and m.is_winding_consistent and m.volume > 0)


# ------------------------------ viewer ------------------------------
V18_DROP = ("Skid plate 3D print", "Klem motor", "Boss M3 skid plate", "Bibir penahan pack", "Rangka interface",
            "Ban merah", "Velg", "Ball caster", "Mur M3", "Spacer nilon", "Baut M3 x 10 sensor", "Strap velcro",
            "Gesper strap")
REV_C_SHIFT = ("Header JST XH J1", "Steker JST XH J1", "IC mux", "C 100 nF mux")   # rev C: U13/C1/J1 mundur 2,5 mm


def b64(a, dt):
    return base64.b64encode(np.ascontiguousarray(a, dtype=dt).tobytes()).decode()


def mesh_obj(name, mat, group, tri=None, dbl=False, p=None, i=None):
    """mesh viewer: titik float32 + indeks uint32 (base64); segitiga benda cetak disatukan titiknya dulu"""
    if tri is not None:
        p, i = np.unique(np.round(tri.reshape(-1, 3), 3), axis=0, return_inverse=True)
    o = {"n": name, "m": mat, "g": group, "p": b64(p, "<f4"), "i": b64(np.asarray(i).ravel(), "<u4")}
    if dbl:
        o["d"] = 1
    return o


def strap_tri():
    """strap velcro 16 mm: naik dari celah belakang, melingkari pack, turun ke celah depan, kembali di bawah sasis"""
    pz0, pz1, t = CH_Z1, CH_Z1 + 15.0, 1.0
    ya, yb = SLOTS[0][1] - 0.6, SLOTS[1][0] + 0.6
    r = 7.5
    path = [(ya, CH_Z0 - 0.5), (ya, pz1 - r)]
    path += [(ya + r - r * math.cos(math.pi / 2 * k / 8), pz1 - r + r * math.sin(math.pi / 2 * k / 8) + 0.6) for k in range(9)]
    path += [(yb - r + r * math.sin(math.pi / 2 * k / 8), pz1 - r + r * math.cos(math.pi / 2 * k / 8) + 0.6) for k in range(9)]
    path += [(yb, CH_Z0 - 0.5)]
    tri = []
    for (y0, z0), (y1, z1) in zip(path + [path[0]], path[1:] + [path[0]]):
        q = lambda x, y, z: (x, y, z)
        d = np.array([y1 - y0, z1 - z0])
        nrm = np.array([d[1], -d[0]]) / (np.linalg.norm(d) or 1) * t
        a, b = (y0, z0), (y1, z1)
        c, e = (y1 + nrm[0], z1 + nrm[1]), (y0 + nrm[0], z0 + nrm[1])
        for x0, x1 in ((-8.0, 8.0),):
            tri += [(q(x0, *a), q(x1, *a), q(x1, *b)), (q(x0, *a), q(x1, *b), q(x0, *b)),
                    (q(x0, *e), q(x0, *c), q(x1, *c)), (q(x0, *e), q(x1, *c), q(x1, *e))]
    return np.array(tri, float)


def bolt_tri(x, y, z_head, up, L, head="socket"):
    """baut M3: muka bawah kepala di z_head, batang ke arah up (+1 atas / -1 bawah) sepanjang L"""
    hh, hr = {"socket": (3.0, 2.75), "csk": (1.7, 3.0)}[head]
    shank = Layered("").add(*sorted((z_head, z_head + up * L)), circ(x, y, 1.5, 16)).triangles()
    hd = Layered("").add(*sorted((z_head, z_head - up * hh)), circ(x, y, hr, 24)).triangles()
    return np.concatenate([shank, hd])


def nut_tri(x, y, z0, z1):
    return Layered("").add(z0, z1, hexa(x, y, 5.5).difference(circ(x, y, 1.5, 16))).triangles()


def shelf(items, gap=6.0, width=BED):
    """susun kotak pembatas (w, h) di alas: baris dari bawah, kiri ke kanan; hasil = posisi tengah tiap kotak"""
    pos, x, y, row = [], gap, gap, 0.0
    for w, h in items:
        if x + w + gap > width:
            x, y, row = gap, y + row + gap, 0.0
        pos.append((x + w / 2 - width / 2, y + h / 2 - width / 2))
        x, row = x + w + gap, max(row, h)
    assert y + row + gap <= width, "tidak muat di alas"
    return pos


# ------------------------------ utama ------------------------------
if __name__ == "__main__":
    kd = kicad_data()
    # sanity: lubang di KiCad harus sama dengan konstanta skrip
    assert holes(kd["utama"]) == sorted(MB_HOLE), holes(kd["utama"])
    assert holes(kd["sensor"]) == sorted(SENS_H), holes(kd["sensor"])
    assert sorted(h for h in holes(kd["interface"]) if abs(h[0]) == 17.0) == sorted(IB_HOLE), holes(kd["interface"])

    parts = {}                                   # nama file -> (Layered, jumlah cetak, bahan, transform ke alas)
    sasis = make_sasis(kd["utama"])
    parts["x1_sasis"] = (sasis, 1, "PETG/PLA", "up")
    parts["x1_tutup_klem_kanan"] = (make_cap(1), 1, "PETG/PLA", "up")
    parts["x1_tutup_klem_kiri"] = (make_cap(-1), 1, "PETG/PLA", "up")
    parts["x1_rangka_interface"] = (make_frame(), 1, "PETG/PLA", "flip")
    parts["x1_velg"] = (make_velg(), 2, "PETG/PLA", "up")
    parts["x1_ban_tpu"] = (make_ban(), 2, "TPU 95A", "up")
    parts["x1_skid_sensor"] = (make_skid(), 1, "PETG/PLA", "flip")
    parts["x1_spacer_sensor"] = (make_spacer(*SENS_H[1]), 2, "PETG/PLA", "up")
    parts["x1_uji_dudukan_motor"] = (make_sasis(kd["utama"], clip=sbox(11.0, -17.0, 40.0, 18.0)), 1, "PETG/PLA", "up")
    parts["x1_uji_lubang_as"] = (make_bore_test(), 1, "PETG/PLA", "up")

    os.makedirs(os.path.join(HERE, "stl"), exist_ok=True)
    tri_robot, tri_bed, slabs, info = {}, {}, {}, {}
    for name, (obj, n, bahan, how) in parts.items():
        t = obj.triangles()
        tri_robot[name] = t
        slabs[name] = obj.slabs()[1]
        tb = to_bed(flip_x(t) if how == "flip" else t)
        tri_bed[name] = tb
        write_stl(tb, os.path.join(HERE, "stl", name + ".stl"), obj.name)
        lo, hi = tb.reshape(-1, 3).min(0), tb.reshape(-1, 3).max(0)
        rho = TPU if "TPU" in bahan else PETG
        info[name] = dict(nama=obj.name, n=n, bahan=bahan, ukuran=[round(float(v), 1) for v in hi - lo],
                          vol=round(volume(t) / 1000, 2), massa=round(volume(t) / 1000 * rho, 1),
                          tertutup=watertight(tb), segitiga=len(tb))

    print("Bagian cetak (posisi cetak, massa = padat 100 %, PETG / TPU):")
    for name, d in info.items():
        u = d["ukuran"]
        print(f"  {name:24s} x{d['n']}  {u[0]:6.1f} x {u[1]:6.1f} x {u[2]:5.1f} mm  {d['vol']:6.2f} cm3  {d['massa']:5.1f} g"
              f"  {'tertutup' if d['tertutup'] else 'TIDAK TERTUTUP'}  {d['bahan']}")
        assert d["tertutup"], name
        assert max(d["ukuran"][:2]) <= BED - 10, name

    # ---- cek tabrakan terhadap mesh konsep v18 (kotak pembatas) + komponen KiCad ----
    V18 = json.load(open(os.path.join(REPO, "mechanical", "konsep-v18", "konsep-v18-model.json"), encoding="utf-8"))
    keep, obst = [], []
    for o in V18["meshes"]:
        if o["n"].startswith(V18_DROP):
            continue
        p = np.array(o["p"], float).reshape(-1, 3)
        if o["n"].startswith(REV_C_SHIFT):
            p[:, 1] -= 2.5
            o = dict(o, p=np.round(p, 2).ravel().tolist())
        keep.append(o)
        lo, hi = p.min(0), p.max(0)
        obst.append((o["n"], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    for f in kd["sensor"]:                                     # komponen sisi bawah PCB sensor (skid, sasis)
        if f["side"] == "B":
            x0, x1, y0, y1 = f["bb"]
            obst.append((f"sensor {f['ref']}", x0, x1, y0, y1, SB_Z - 1.8, SB_Z))
        if f["ref"] == "J1":                                   # header JST tegak di sisi atas, steker 10 mm
            x0, x1, y0, y1 = f["bb"]
            obst.append(("sensor J1 + steker", x0, x1, y0, y1, SZ_TOP, SZ_TOP + 11.0))
    # ekor kaki THT di bawah PCB utama: 3 mm (ekor socket female), harus jatuh di jendela sasis
    for f in kd["utama"]:
        for pd in f["pads"]:
            if pd["pth"]:
                x, y = pd["p"]
                obst.append((f"kaki THT {f['ref']}", x - 0.6, x + 0.6, y - 0.6, y + 0.6, MB_Z0 - 3.2, MB_Z0))
    # ban + velg baru (posisi rakitan) juga penghalang untuk sasis
    wheel_box = [("ban kanan", WX, WO, -R_W, R_W, 0.0, 2 * R_W), ("ban kiri", -WO, -WX, -R_W, R_W, 0.0, 2 * R_W)]
    probs = []
    motor_ok = ("Gearbox N20", "Motor N20", "Tutup motor", "Encoder PCB", "Magnet encoder", "Konektor encoder", "As roda")
    probs += clash("sasis", slabs["x1_sasis"], obst, ignore=("Baut M3 x 30", "Kabel", "Pack", "Steker balancer") + motor_ok)
    probs += clash("tutup klem", slabs["x1_tutup_klem_kanan"] + slabs["x1_tutup_klem_kiri"], obst,
                   ignore=("Kabel",) + motor_ok)
    probs += clash("rangka interface", slabs["x1_rangka_interface"], obst, ignore=("Baut M3 x 30", "Mur M3 rangka", "Kabel",
                                                                              "Baut M2 x 6"))
    probs += clash("skid", slabs["x1_skid_sensor"], obst, ignore=("Kabel",))
    # sasis terhadap ban (lantai sampai z 14,5 di coakan): jarak mendatar ke silinder ban
    for nm, x0, x1, y0, y1, z0, z1 in wheel_box:
        for a, b, p in slabs["x1_sasis"]:
            for poly in polys(p):
                for x, y in poly.exterior.coords:
                    if x0 - 1.0 < x < x1 + 1.0:
                        zc = AX_Z - math.sqrt(max(R_W ** 2 - y * y, 0.0)) if abs(y) < R_W else 99
                        if zc < b and abs(y) < R_W + 1.0:
                            probs.append(f"sasis <-> {nm} di ({x:.1f}; {y:.1f})")
                            break
    # motor di alur: alur 12,4, ganjal tidak menyentuh kaleng (r 6, rata di z 12/22), atap tutup = puncak motor
    lx0, lx1, ly, lz = LEDGE
    assert math.hypot(ly, AX_Z - lz) > 6.0 + 0.05, "ganjal menabrak kaleng motor"
    pack_box = [o for o in obst if o[0].startswith("Pack Li-ion")][0]
    gaps = {
        "kaki THT terdekat ke sasis (harus di jendela)": min(gap(slabs["x1_sasis"], *o[1:]) for o in obst if o[0].startswith("kaki THT")),
        "steker J1 sensor ke hidung sasis": gap(slabs["x1_sasis"], *[o for o in obst if o[0] == "sensor J1 + steker"][0][1:]),
        "pack ke rel/bibir": gap(slabs["x1_sasis"], *pack_box[1:]),
        "rangka ke ESP32 PCB": gap(slabs["x1_rangka_interface"], *[o for o in obst if o[0] == "ESP32 PCB"][0][1:]),
        "skid ke QRE terdekat": min(gap(slabs["x1_skid_sensor"], *o[1:]) for o in obst if o[0].startswith("sensor U")),
    }
    print("Cek tabrakan:", "0 masalah" if not probs else "")
    for s in probs:
        print("   -", s)
    print("Celah terkecil:")
    for k, v in gaps.items():
        print(f"   {k}: {v:.2f} mm")

    # ---- panjang baut ----
    bolts = [
        ("M3 x 30 kepala benam", 4, "PCB utama + rangka interface, dari bawah sasis", CH_Z0, FR_Z1 + 2.4),
        ("M3 x 16", 4, "tutup klem motor, mur di kantong bawah sasis", CAP_Z1, CH_Z0 + 0.2),
        ("M3 x 10", 2, "PCB sensor, kepala di atas hidung sasis, mur di skid", CH_Z1, SB_Z - NUT_H + 0.2),
    ]
    print("Baut (panjang minimum = sampai ujung mur):")
    for nm, n, guna, za, zb in bolts:
        print(f"   {n} x {nm:22s} butuh {abs(za - zb):4.1f} mm  {guna}")

    # ---- mesh viewer: rakitan + alas cetak ----
    meshes = [mesh_obj(o["n"], o["m"], o["g"], dbl=bool(o.get("d")), p=o["p"], i=o["i"]) for o in keep]
    col = {"x1_sasis": "print", "x1_tutup_klem_kanan": "print", "x1_tutup_klem_kiri": "print",
           "x1_rangka_interface": "print2", "x1_skid_sensor": "print", "x1_spacer_sensor": "print", "x1_velg": "print2",
           "x1_ban_tpu": "tpu"}
    for name in col:
        t = tri_robot[name]
        if name in ("x1_velg", "x1_ban_tpu"):         # posisi cetak -> poros roda kanan, lalu putar 180 untuk kiri
            off = 0.0 if name == "x1_velg" else 1.3
            R = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)
            right = t @ R.T + np.array([WO - off, 0.0, AX_Z])
            for s, tt in ((1, right), (-1, right * np.array([-1.0, -1.0, 1.0]))):
                meshes.append(mesh_obj(info[name]["nama"], col[name], "cetak", tt))
        elif name == "x1_spacer_sensor":
            for x, y in SENS_H:
                meshes.append(mesh_obj("Spacer sensor", col[name], "cetak", make_spacer(x, y).triangles()))
        else:
            meshes.append(mesh_obj(info[name]["nama"], col[name], "cetak", t))
    hw = []                                              # baut M3 x 30 + mur rangka ikut dari mesh konsep v18
    for x, y in CAP_BOLT:
        for s in (1, -1):
            hw += [bolt_tri(s * x, y, CAP_Z1, -1, 16), nut_tri(s * x, y, CH_Z0 + 0.2, CH_Z0 + 2.6)]
    for x, y in SENS_H:
        hw += [bolt_tri(x, y, CH_Z1, -1, 10), nut_tri(x, y, SB_Z - NUT_H, SB_Z - 0.2)]
    meshes.append(mesh_obj("Baut + mur", "chrome", "base", np.concatenate(hw)))
    meshes.append(mesh_obj("Strap velcro 16 mm", "strap", "pack", strap_tri(), dbl=True))

    # alas cetak A1: alas 1 PETG/PLA, alas 2 TPU, alas 3 potongan uji
    plates = [["x1_sasis", "x1_rangka_interface", "x1_tutup_klem_kanan", "x1_tutup_klem_kiri", "x1_velg", "x1_velg",
               "x1_skid_sensor", "x1_spacer_sensor", "x1_spacer_sensor"], ["x1_ban_tpu", "x1_ban_tpu"],
              ["x1_uji_dudukan_motor", "x1_uji_lubang_as"]]
    plate_meta = []
    for k, names in enumerate(plates):
        dims = [tuple(info[n]["ukuran"][:2]) for n in names]
        order = sorted(range(len(names)), key=lambda i: -dims[i][1] * 1000 - dims[i][0])
        pos = shelf([dims[i] for i in order])
        ox = k * (BED + 40.0)
        for i, (x, y) in zip(order, pos):
            n = names[i]
            m = {"x1_ban_tpu": "tpu", "x1_rangka_interface": "print2", "x1_velg": "print2"}.get(n, "print")
            meshes.append(mesh_obj(info[n]["nama"], m, "alas", tri_bed[n] + np.array([ox + x, y, 0.0])))
        plate_meta.append(dict(x=ox, judul=["Alas 1: PETG atau PLA", "Alas 2: TPU 95A", "Alas 3: cetak uji dulu"][k]))
    mats = dict(V18["mats"])
    mats.update({"print": ["#e4572e", 0.62, 0.0], "print2": ["#3a7bd5", 0.62, 0.0], "tpu": ["#2b2d31", 0.85, 0.0],
                 "strap": ["#f08a1c", 0.92, 0.0]})
    out = {"mats": mats, "meshes": meshes, "plates": plate_meta, "bed": BED,
           "parts": info, "bolts": [[nm, n, guna, round(abs(za - zb), 1)] for nm, n, guna, za, zb in bolts],
           "gaps": {k: round(v, 2) for k, v in gaps.items()}, "probs": probs}
    path = os.path.join(HERE, "cetak-x1-model.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    total = sum(d["massa"] * d["n"] for n, d in info.items() if not n.startswith("x1_uji"))
    print(f"Massa bagian cetak (padat, tanpa uji): {total:.0f} g;  mesh viewer {len(meshes)}, "
          f"{os.path.getsize(path) / 1e6:.1f} MB")
