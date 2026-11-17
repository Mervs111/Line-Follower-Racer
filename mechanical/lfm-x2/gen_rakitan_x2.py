"""Rakitan LFM X2 rev B + usulan bagian cetak 3D (16/11/2026).

Keempat papan X2 (hardware/lfm-x2/: sensor, driver, utama, antarmuka) diekspor kicad-cli ke GLB dan ditumpuk di tinggi
rancangan README X2, lalu ditambah motor + roda (mesh v16, ban 18 mm), modul OLED, LiPo 2S, baut, spacer, kabel, dan
tiga bagian cetak 3D yang belum pernah digambar sebelumnya (USULAN Claude, belum disetujui user):
  rangka motor     klem gearbox kedua N20 + alas motor + lengan ke telinga (+-44; 23,5) dengan tiang 11 mm yang
                   menggantikan spacer driver <-> papan utama; alas datar di z 7,6 (= muka atas papan driver)
  dudukan baterai  alas LiPo 2S (ruang 56 x 31 mm, diikat strap velcro 16 mm) yang sekaligus menjadi tutup klem gearbox,
                   4 baut M3 x 18 ke rangka motor (mur di kantong heksagon bawah rangka)
  skid depan       kubah O9 x 4,5 mm di lubang depan papan sensor (0; 134,3), mur M3 tertanam, baut M3 x 5 dari atas
Bagian cetak dibangun dari tumpukan ekstrusi 2D (shapely, tanpa CadQuery): tiap selang z punya satu poligon berlubang,
dinding dan tutup dihitung dari selisih poligon antar-selang, jadi STL-nya tertutup dan bisa langsung di-slice.

Keluaran (folder ini):
  LFM_X2_web.json     GLB rakitan (meshopt, base64) untuk index.html; artifact claude.ai tidak menyajikan .glb
  stl/*.stl           bagian cetak dalam posisi cetak (alas di z = 0), mm
Hasil cek tabrakan bagian cetak terhadap komponen KiCad, motor, roda, steker dicetak di akhir.

Koordinat robot (mm): x kanan, y maju, z naik dari lantai, (0, 0) = tengah poros roda; KiCad X = 200 + x,
Y = 180,55 - y (sama di keempat proyek X2).
Jalankan: py mechanical/lfm-x2/gen_rakitan_x2.py   (butuh KiCad 10, numpy, shapely >= 2.1, Node.js untuk gltfpack)
"""
import base64, json, math, os, re, struct, sys, tempfile
import numpy as np
import shapely
from shapely.geometry import Point, Polygon, box as sbox
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "mechanical", "rakitan-pcb"))
import gen_rakitan as gr                    # ekspor/baca GLB KiCad, tulis GLB, gltfpack

T = 1.6                                     # tebal PCB
# sisi bawah tiap papan dari lantai (README X2, tabel susunan)
BOARDS = {"sensor": 4.5, "driver": 6.0, "utama": 18.6, "antarmuka": 31.2}
X2 = os.path.join(REPO, "hardware", "lfm-x2")
RZ0 = BOARDS["driver"] + T                  # alas rangka motor = muka atas papan driver (7,6)
EAR = (44.0, 23.5)                          # lubang telinga papan utama + driver
TZ0 = 22.0                                  # alas dudukan baterai = puncak gearbox / kaleng N20
SKID = (0.0, 134.3)                         # lubang depan papan sensor
PETG = 1.27                                 # g/cm3

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
    return shapely.affinity.scale(g, -1, 1, origin=(0, 0))


def both(g):
    return unary_union([g, mirror_x(g)])


# ------------------------------ benda tumpukan ekstrusi ------------------------------
class Layered:
    """benda = daftar fitur (z0, z1, poligon, +1 tambah / -1 potong). Tiap selang antar-ketinggian dihitung satu poligon
    (tambah - potong); dinding dari cincin poligon, tutup atas/bawah dari selisih poligon selang bawah dan atas."""

    def __init__(self, name):
        self.name, self.feats = name, []

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
            out.append((a, b, p.buffer(0)))
        return lv, out

    def triangles(self):
        lv, sl = self.slabs()
        walls, tri = [], []
        for a, b, p in sl:
            for poly in polys(p):
                poly = orient(poly, 1.0)
                for ring in (poly.exterior, *poly.interiors):
                    c = list(ring.coords)[:-1]
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
        return np.array(tri, float)


def on_edge(P, p, q, tol=1e-6):
    """parameter t (0..1, urut) titik P yang jatuh di ruas p-q, termasuk kedua ujung"""
    p, q = np.array(p), np.array(q)
    d = q - p
    L2 = d @ d
    t = (P - p) @ d / L2
    off = np.abs((P[:, 0] - p[0]) * d[1] - (P[:, 1] - p[1]) * d[0]) / math.sqrt(L2)
    t = t[(off < tol) & (t > 1e-7) & (t < 1 - 1e-7)]
    return [0.0] + sorted(set(np.round(t, 9).tolist())) + [1.0]


def zipper(p, q, a, b, tb, tt):
    """dinding p->q dari z a ke b, tepi bawah dipecah di tb, tepi atas di tt; normal keluar = kanan arah p->q"""
    P = lambda t, z: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, z)
    out, i, j = [], 0, 0
    while i < len(tb) - 1 or j < len(tt) - 1:
        if j == len(tt) - 1 or (i < len(tb) - 1 and tb[i + 1] <= tt[j + 1]):
            out.append((P(tb[i], a), P(tb[i + 1], a), P(tt[j], b)))
            i += 1
        else:
            out.append((P(tb[i], a), P(tt[j + 1], b), P(tt[j], b)))
            j += 1
    return out


def polys(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [q for h in getattr(g, "geoms", []) for q in polys(h)]


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


def revolve(cx, cy, outer, inner, n=48):
    """benda putar: outer = [(z, r)] dari atas ke bawah (r = 0 boleh di titik terbawah), inner = [(z, bentuk, ukuran)]
    dari atas ke bawah ('hex' lebar kunci / 'circ' jari-jari), diakhiri dasar lubang buntu"""
    ang = [2 * math.pi * k / n for k in range(n)]

    def ring(z, kind, s):
        if kind == "hex":
            r = [(s / 2) / math.cos(((a + math.pi / 6) % (math.pi / 3)) - math.pi / 6) for a in ang]
        else:
            r = [s] * n
        return [(cx + ri * math.cos(a), cy + ri * math.sin(a), z) for ri, a in zip(r, ang)]

    tri = []

    def strip(A, B):                         # A di atas B, normal keluar = kanan arah putar dilihat dari luar
        for k in range(n):
            j = (k + 1) % n
            tri.extend([(A[k], B[k], B[j]), (A[k], B[j], A[j])])

    O = [ring(z, "circ", r) for z, r in outer]
    for A, B in zip(O, O[1:]):
        strip(A, B)
    I = [ring(z, k, s) for z, k, s in inner]
    for A, B in zip(I, I[1:]):
        strip(B, A)                          # dinding lubang menghadap ke dalam lubang
    top_o, top_i = O[0], I[0]
    for k in range(n):                       # tutup atas: cincin antara luar dan lubang
        j = (k + 1) % n
        tri.extend([(top_i[k], top_o[k], top_o[j]), (top_i[k], top_o[j], top_i[j])])
    c = (cx, cy, inner[-1][0])
    for k in range(n):                       # dasar lubang buntu, menghadap ke atas (ke rongga lubang)
        tri.append((c, I[-1][k], I[-1][(k + 1) % n]))
    tri = np.array(tri, float)
    ar = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    return tri[ar > 1e-9]                    # buang segitiga nol di kutub kubah


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


# ------------------------------ bagian cetak ------------------------------
SAD_X0, SAD_X1, SAD_Y = 29.3, 37.5, 14.5     # klem gearbox (gearbox N20: x 28,5..37,5, y +-6, z 12..22)
POCKET_Y, POCKET_Z = 6.15, 11.9
TRAY_BOLT = [(sx * 33.4, sy * 9.8) for sx in (-1, 1) for sy in (-1, 1)]
NUT_AF, NUT_H, M3 = 5.7, 2.6, 3.4


def make_rangka():
    p = Layered("Rangka motor")
    z0 = RZ0
    # alas motor: tengah (x +-24, y > -4) dikosongkan untuk konektor motor J2/J3 driver + steker + kabel encoder
    p.add(z0, z0 + 2.0, unary_union([rrect(-SAD_X1, SAD_X1, -10.0, -4.0, 2.0), both(rrect(24.0, SAD_X1, -10.0, 6.5, 2.0))]))
    p.add(z0, 13.0, rrect(-SAD_X0, SAD_X0, -10.0, -7.0, 1.0))                          # rusuk belakang
    p.add(z0, POCKET_Z, both(rrect(24.0, SAD_X0 + 1, -4.0, 4.0, 1.0)))                # tumpuan kaleng motor
    sad = both(rrect(SAD_X0, SAD_X1, -SAD_Y, SAD_Y, 1.5))
    p.add(z0, TZ0, sad)                                                                # klem gearbox
    p.cut(POCKET_Z, TZ0 + 1, both(sbox(SAD_X0 - 1, -POCKET_Y, SAD_X1 + 1, POCKET_Y)))  # alur gearbox (terbuka ke atas)
    ear = unary_union([rrect(SAD_X0, EAR[0], 19.5, 27.5, 1.5), circ(*EAR, 4.0)])
    p.add(z0, 12.0, both(unary_union([rrect(SAD_X0, SAD_X1, 10.0, 21.0, 1.5), ear])))   # lengan + telinga
    p.add(12.0, BOARDS["utama"], both(circ(*EAR, 3.6)))                                # tiang 11 mm
    p.cut(z0, BOARDS["utama"], both(circ(*EAR, M3 / 2, 32)))
    for x, y in TRAY_BOLT:
        p.cut(z0, TZ0, circ(x, y, M3 / 2, 32))
        p.cut(z0, z0 + NUT_H, hexa(x, y, NUT_AF))
    return p


def box2(xa, xb, ya, yb):
    return sbox(min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb))


TRAY = (29.6, -31.1, 3.1)                   # setengah lebar, tepi belakang, tepi depan alas baterai


def make_tray():
    p = Layered("Dudukan baterai")
    z1 = TZ0 + 3.0
    hx, yb, yf = TRAY
    floor = rrect(-hx, hx, yb, yf, 3.0)
    # tab tutup klem gearbox mulai x 30: steker XT30 (x <= 28,1) lewat di depan alas kanan
    tabs = both(unary_union([rrect(30.0, SAD_X1, -SAD_Y, SAD_Y, 1.5), sbox(hx - 1, -SAD_Y, 31.0, yf)]))
    p.add(TZ0, z1, unary_union([floor, tabs]))
    p.cut(TZ0, TZ0 + 1.6, both(sbox(10.4, -6.8, 13.9, 6.8)))                           # ruang PCB encoder (z 23,2)
    for x, y in TRAY_BOLT:
        p.cut(TZ0, z1, circ(x, y, M3 / 2, 32))
    rim = []                                                                           # siku penahan pack di 4 pojok
    for sx in (-1, 1):
        for ye, dy in ((yf, -1), (yb, 1)):
            xo, dx = sx * hx, -sx
            rim += [box2(xo, xo + dx * 6, ye, ye + dy * 1.6), box2(xo, xo + dx * 1.6, ye, ye + dy * 9)]
    p.add(z1, z1 + 4.0, unary_union(rim).intersection(floor))
    return p


def make_skid():
    """kubah: silinder r 4,5 di z 1,8..4,5, tudung bola di z 0..1,8; kantong mur M3 dari atas, lubang buntu sampai z 0,9"""
    a, h = 4.5, 1.8
    R = (a * a + h * h) / (2 * h)
    outer = [(4.5, a), (h, a)] + [(z, math.sqrt(max(R * R - (R - z) ** 2, 0))) for z in np.linspace(h, 0, 10)[1:]]
    inner = [(4.5, "hex", NUT_AF), (h, "hex", NUT_AF), (h, "circ", M3 / 2), (0.9, "circ", M3 / 2)]
    return revolve(*SKID, outer, inner)


# ------------------------------ geometri bantu (non-cetak) ------------------------------
def boxm(x0, x1, y0, y1, z0, z1):
    return Layered("").add(z0, z1, sbox(x0, y0, x1, y1)).triangles()


def prism(g, z0, z1):
    return Layered("").add(z0, z1, g).triangles()


def bolt(x, y, z_head, up, L, head="socket"):
    """baut M3: kepala di z_head (muka bawah kepala), batang ke arah up (+1 ke atas / -1 ke bawah) sepanjang L"""
    hh, hr = (3.0, 2.75) if head == "socket" else (1.7, 2.9)
    return np.concatenate([prism(circ(x, y, 1.5, 16), *sorted((z_head, z_head + up * L))),
                           prism(circ(x, y, hr, 24), *sorted((z_head, z_head - up * hh)))])


def nut(x, y, z0, z1):
    return prism(hexa(x, y, 5.5).difference(circ(x, y, 1.5, 16)), z0, z1)


def smooth(pts, k=3):
    for _ in range(k):
        q = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            q += [tuple(a[i] * 0.75 + b[i] * 0.25 for i in range(3)), tuple(a[i] * 0.25 + b[i] * 0.75 for i in range(3))]
        q.append(pts[-1])
        pts = q
    return pts


def frames(path):
    out = []
    for k, p in enumerate(path):
        a, b = np.array(path[max(k - 1, 0)]), np.array(path[min(k + 1, len(path) - 1)])
        t = (b - a) / (np.linalg.norm(b - a) or 1)
        ref = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(ref, t)
        u /= np.linalg.norm(u)
        out.append((np.array(p), t, u, np.cross(t, u)))
    return out


def tube(path, r, n=8):
    F = frames(smooth(path))
    tri = []
    rings = [[p + r * (math.cos(2 * math.pi * j / n) * u + math.sin(2 * math.pi * j / n) * v) for j in range(n)] for p, t, u, v in F]
    for A, B in zip(rings, rings[1:]):
        for j in range(n):
            k = (j + 1) % n
            tri += [(A[j], A[k], B[k]), (A[j], B[k], B[j])]
    return np.array(tri, float)


def ribbon(path_yz, x0, x1, t):
    """pita datar (FFC): lintasan (y, z) = garis tengah, lebar x0..x1, tebal t"""
    P = smooth([(0.0, y, z) for y, z in path_yz])
    tri = []
    for (_, ya, za), (_, yb, zb) in zip(P, P[1:]):
        d = np.array([yb - ya, zb - za])
        nrm = np.array([-d[1], d[0]]) / (np.linalg.norm(d) or 1) * t / 2
        c = [(ya + nrm[0], za + nrm[1]), (yb + nrm[0], zb + nrm[1]), (yb - nrm[0], zb - nrm[1]), (ya - nrm[0], za - nrm[1])]
        q = lambda x, p: (x, p[0], p[1])
        tri += [(q(x0, c[0]), q(x1, c[0]), q(x1, c[1])), (q(x0, c[0]), q(x1, c[1]), q(x0, c[1])),
                (q(x0, c[3]), q(x0, c[2]), q(x1, c[2])), (q(x0, c[3]), q(x1, c[2]), q(x1, c[3]))]
    return np.array(tri, float)


def band(path, x0, x1, t):
    """pita tertutup (strap): path (y, z) = sisi dalam, tebal t ke luar, lebar x0..x1"""
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
    tri = []
    for k in range(n):
        j = (k + 1) % n
        i0, i1, o0, o1 = path[k], path[j], outer[k], outer[j]
        for a, b, c, d in (((x0, *o0), (x1, *o0), (x1, *o1), (x0, *o1)), ((x0, *i0), (x0, *i1), (x1, *i1), (x1, *i0)),
                           ((x0, *i0), (x0, *o0), (x0, *o1), (x0, *i1)), ((x1, *i0), (x1, *i1), (x1, *o1), (x1, *o0))):
            tri += [(a, b, c), (a, c, d)]
    return np.array(tri, float)


# ------------------------------ susun GLB ------------------------------
GROUPS = {}
OBST = []                                   # kotak penghalang untuk cek tabrakan: (nama, x0, x1, y0, y1, z0, z1)


def mat(color, rough=0.6, metal=0.0, emissive=None, alpha=None):
    m = {"pbrMetallicRoughness": {"baseColorFactor": gr.srgb_to_lin(color) + [1.0 if alpha is None else alpha],
                                  "metallicFactor": metal, "roughnessFactor": rough}}
    if emissive:
        m["emissiveFactor"] = gr.srgb_to_lin(emissive)
    if alpha is not None:
        m["alphaMode"] = "BLEND"
    return m


M = {"print": mat("#E8742A", 0.62), "chrome": mat("#d9dde2", 0.25, 1.0), "brass": mat("#c9a24a", 0.35, 0.9),
     "nylon": mat("#eeeae0", 0.6), "pack": mat("#1b1d22", 0.42, 0.1), "pack_lbl": mat("#2a62c9", 0.5),
     "xt30": mat("#f2c21b", 0.5), "wire_red": mat("#d3202e", 0.5), "wire_blk": mat("#222326", 0.5),
     "wire_yel": mat("#e8b923", 0.5), "wire_blu": mat("#2f5fb3", 0.5), "wire_grn": mat("#2e9e4f", 0.5),
     "wire_wht": mat("#e9e9e4", 0.5), "strap": mat("#f08a1c", 0.92), "ffc": mat("#c99a52", 0.45, 0.2),
     "ffc_blue": mat("#2b5fb8", 0.5), "oled_pcb": mat("#1d4d9a", 0.5, 0.1), "glass": mat("#05080d", 0.12, 0.3),
     "screen": mat("#9fd2ff", 0.4, 0.0, emissive="#7fc4ff"), "black": mat("#1c1d20", 0.6),
     "led": mat("#e8e2d0", 0.4), "lens_clear": mat("#cfd8de", 0.15, 0.2), "lens_black": mat("#141518", 0.25),
     "gold": mat("#d6aa45", 0.3, 0.9), "jst": mat("#efe9da", 0.6)}


def emit(group, m, tri=None, pos=None, nor=None, idx=None):
    if tri is not None:
        tri = np.asarray(tri, float)
        pos = tri.reshape(-1, 3)
        fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        nor = np.repeat(fn, 3, axis=0)
        idx = np.arange(len(pos), dtype=np.uint32)
    e = GROUPS.setdefault(group, {}).setdefault(gr.mat_key(m), (m, [], [], []))
    e[1].append(np.asarray(pos, float)), e[2].append(np.asarray(nor, float)), e[3].append(np.asarray(idx, np.uint32))


def kicad_boards(tmp):
    info = {}
    for b, z0 in BOARDS.items():
        pcb = os.path.join(X2, b, f"lfm-x2-{b}.kicad_pcb")
        glb = os.path.join(tmp, b + ".glb")
        print(f"ekspor {b} ...")
        gr.export_glb(pcb, glb)
        refs = {}
        for ref, m, pos, nor, idx in gr.read_glb(glb):
            pos = pos @ gr.G2R.T + [0, 0, z0]
            nor = nor @ (gr.G2R / 1000).T if nor is not None else gr.vertex_normals(pos, idx)
            m = dict(m)
            m.pop("name", None)
            emit(b, m, pos=pos, nor=nor, idx=idx)
            lo, hi = pos.min(0), pos.max(0)
            if ref in refs:
                lo, hi = np.minimum(lo, refs[ref][0]), np.maximum(hi, refs[ref][1])
            refs[ref] = (lo, hi)
        poly = gr.outline(pcb)
        info[b] = {"x": [round(float(poly[:, 0].min()), 2), round(float(poly[:, 0].max()), 2)],
                   "y": [round(float(poly[:, 1].min()), 2), round(float(poly[:, 1].max()), 2)], "z": [z0, z0 + T],
                   "poly": Polygon(poly).buffer(0)}
        for ref, (lo, hi) in refs.items():
            if (hi - lo).max() < 60:                 # papan itu sendiri dicek dengan poligon tepinya
                OBST.append((f"{b}:{ref}", *[float(v) for v in (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])]))
    return info


def footprints(board, pat):
    k = open(os.path.join(X2, board, f"lfm-x2-{board}.kicad_pcb"), encoding="utf8").read()
    out = []
    for m in re.finditer(r'\n\t\(footprint "([^"]+)"\s*\(layer "([^"]+)"\)\s*\(uuid "[^"]+"\)\s*\(at ([\d.\-]+) ([\d.\-]+)'
                         r'(?: ([\d.\-]+))?\)(.*?)\n\t\)', k, re.S):
        ref = re.search(r'\(property "Reference" "([^"]+)"', m.group(6)).group(1)
        if re.fullmatch(pat, ref):
            out.append((ref, m.group(1), m.group(2), float(m.group(3)) - gr.KX0, gr.KY0 - float(m.group(4)),
                        float(m.group(5) or 0)))
    return out


def sensor_parts():
    """sensor di sisi bawah papan sensor sebagai rintangan cek jarak. QRE1113GR (OnSemi CASE100CY, 16/11): model 3D
    ikut ekspor GLB, di sini hanya kotak badan 2,9 x 3,6 x 1,7. PLCC-2 3528 buatan sendiri (versi PT67 + LED IR, sebelum
    16/11) tidak punya model 3D: badan 3,5 x 2,8 x 1,9 digambar di sini."""
    zb = BOARDS["sensor"]
    for ref, fp, layer, x, y, rot in footprints("sensor", r"U\d+"):
        if "CASE100CY" in fp:
            g = shapely.affinity.rotate(sbox(x - 1.45, y - 1.8, x + 1.45, y + 1.8), rot, origin=(x, y))
            OBST.append((f"sensor:{ref}", *g.bounds[::2], *g.bounds[1::2], zb - 1.7, zb))
    for ref, fp, layer, x, y, rot in footprints("sensor", r"[DQ]\d+"):
        if "3528" not in fp:
            continue
        g = shapely.affinity.rotate(sbox(x - 1.75, y - 1.4, x + 1.75, y + 1.4), rot, origin=(x, y))
        lens = shapely.affinity.rotate(circ(x, y, 1.05, 24), rot, origin=(x, y))
        emit("sensor", M["led"], prism(g.difference(lens), zb - 1.9, zb))
        emit("sensor", M["lens_clear" if ref.startswith("D") else "lens_black"], prism(lens, zb - 1.8, zb))
        OBST.append((f"sensor:{ref}", *g.bounds[::2], *g.bounds[1::2], zb - 1.9, zb))


def sensor_points():
    """titik baca tiap sensor = tengah QRE1113GR U1..U12 (16/11, kiri ke kanan)"""
    fp = {ref: (x, y) for ref, _, _, x, y, _ in footprints("sensor", r"U\d+")}
    return [[round(fp[f"U{i}"][0], 2), round(fp[f"U{i}"][1], 2)] for i in range(1, 13)]


def mech_v16():
    """motor N20 + encoder dan roda dari model v16; ban dilebarkan 12 -> 18 mm ke luar (sama dengan konsep v18 dan
    gambar susunan X2)"""
    d = json.load(open(os.path.join(REPO, "mechanical", "viewer", "model.json"), encoding="utf8"))
    keep = ("Gearbox N20", "Motor N20", "Tutup motor", "Encoder PCB", "Magnet encoder", "Konektor encoder", "As roda",
            "Ban merah", "Velg")
    wheels = []
    for o in d["meshes"]:
        if not o["n"].startswith(keep):
            continue
        pos = np.array(o["p"], float).reshape(-1, 3)
        if o["n"].startswith(("Ban merah", "Velg")):
            pos[:, 0] = np.sign(pos[:, 0]) * (39.5 + (np.abs(pos[:, 0]) - 39.5) * 18.0 / 12.0)
        idx = np.array(o["i"], np.uint32)
        c, r, met = d["mats"][o["m"]]
        m = mat(c, r, met)
        if len(idx) < 900:                           # benda bersudut: normal datar
            emit("penggerak", m, tri=pos[idx.reshape(-1, 3)])
        else:
            emit("penggerak", m, pos=pos, nor=gr.vertex_normals(pos, idx), idx=idx)
        lo, hi = pos.min(0), pos.max(0)
        if o["n"].startswith("Ban merah"):
            wheels.append([round(float(v), 2) for v in (*lo, *hi)])
        if not o["n"].startswith(("Velg", "As roda")):
            OBST.append((o["n"], *[float(v) for v in (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])]))
    return wheels


# ------------------------------ cek tabrakan ------------------------------
def clash(part, slabs, ignore=()):
    hits = []
    for name, x0, x1, y0, y1, z0, z1 in OBST:
        if any(name.startswith(s) for s in ignore):
            continue
        r = sbox(x0, y0, x1, y1)
        for a, b, p in slabs:
            dz = min(b, z1) - max(a, z0)
            if dz > 0.05 and p.intersection(r).area > 0.05:
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


if __name__ == "__main__":
    tmp = tempfile.mkdtemp(prefix="lfm-x2-")
    info = kicad_boards(tmp)
    sensor_parts()
    wheels = mech_v16()

    # ---- modul OLED 0,96": deret pin di belakang (J2 antarmuka, y 36,5), diputar 180 derajat ----
    zs = BOARDS["antarmuka"] + T
    j2_top = BOARDS["antarmuka"] + 10.1                       # puncak socket J2 dari KiCad
    oz0 = j2_top + 2.54                                       # plastik header di atas socket
    oy0, oy1 = 34.3, 62.1
    oled_holes = [(sx * 11.75, y) for sx in (-1, 1) for y in (36.3, 60.1)]
    emit("oled", M["oled_pcb"], prism(rrect(-13.65, 13.65, oy0, oy1, 1.0).difference(
        unary_union([circ(x, y, 1.0, 16) for x, y in oled_holes])), oz0, oz0 + 1.2))
    emit("oled", M["glass"], prism(sbox(-13.35, 39.6, 13.35, 58.9), oz0 + 1.2, oz0 + 2.6))
    emit("oled", M["screen"], prism(sbox(-10.9, 43.6, 10.9, 54.6), oz0 + 2.6, oz0 + 2.65))
    emit("oled", M["black"], prism(sbox(-5.08, 35.3, 5.08, 37.7), j2_top, oz0))
    for k in range(4):
        x = -3.81 + 2.54 * k
        emit("oled", M["gold"], prism(sbox(x - 0.32, 36.18, x + 0.32, 36.82), j2_top - 6, oz0 + 2.0))
    for x, y in oled_holes[1::2]:                             # spacer M2 nilon di 2 lubang depan (y 60)
        emit("baut", M["nylon"], prism(hexa(x, y, 4.0).difference(circ(x, y, 1.0, 12)), zs, oz0))
    top_z = oz0 + 2.65

    # ---- bagian cetak ----
    parts = {"rangka": make_rangka(), "tray": make_tray()}
    meta = {}
    os.makedirs(os.path.join(HERE, "stl"), exist_ok=True)
    report = []
    pose = {"rangka": dict(dz=-RZ0, flip=False), "tray": dict(dz=-TZ0, flip=False), "skid": dict(dz=-4.5, flip=True)}
    slabs_of = {}
    for key, p in parts.items():
        tri = p.triangles()
        slabs_of[key] = p.slabs()[1]
        emit("cetak_" + key, M["print"], tri=tri)
        meta[key] = tri
    meta["skid"] = make_skid()
    emit("cetak_skid", M["print"], tri=meta["skid"])
    a, h = 4.5, 1.8
    slabs_of["skid"] = [(0.0, h, circ(*SKID, a)), (h, 4.5, circ(*SKID, a))]
    names = {"rangka": "Rangka motor", "tray": "Dudukan baterai", "skid": "Skid depan"}
    files = {"rangka": "x2_rangka_motor.stl", "tray": "x2_dudukan_baterai.stl", "skid": "x2_skid_depan.stl"}
    printed = []
    for key, tri in meta.items():
        q = tri.copy()
        if pose[key]["flip"]:                 # diputar 180 derajat di sumbu x: muka atas (z 4,5) jadi alas cetak
            q[:, :, 1] = 2 * SKID[1] - q[:, :, 1]
            q[:, :, 2] = 4.5 - q[:, :, 2]
        else:
            q[:, :, 2] += pose[key]["dz"]
        lo, hi = q.reshape(-1, 3).min(0), q.reshape(-1, 3).max(0)
        q[:, :, :2] -= (lo[:2] + hi[:2]) / 2                  # STL: tengah alas di (0, 0)
        write_stl(q, os.path.join(HERE, "stl", files[key]), "LFM X2 " + names[key])
        vol = volume(tri) / 1000
        printed.append({"key": key, "nama": names[key], "file": "stl/" + files[key],
                        "ukuran": [round(float(v), 1) for v in hi - lo], "volume_cm3": round(vol, 2),
                        "massa_padat_g": round(vol * PETG, 1), "segitiga": len(tri),
                        "pose": {"dz": pose[key]["dz"], "flip": pose[key]["flip"], "cy": SKID[1] if key == "skid" else 0}})
        print(f"{names[key]}: {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm, {vol:.2f} cm3, "
              f"padat {vol * PETG:.1f} g, alas z {lo[2]:.2f}")

    # ---- baut, mur, spacer ----
    ub, ut = BOARDS["utama"], BOARDS["utama"] + T
    for s in (-1, 1):
        x, y = s * EAR[0], EAR[1]
        emit("baut", M["chrome"], bolt(x, y, BOARDS["driver"], 1, 16))           # dari bawah telinga driver
        emit("baut", M["chrome"], nut(x, y, ut, ut + 2.4))
    for x, y in TRAY_BOLT:
        emit("baut", M["chrome"], bolt(x, y, TZ0 + 3.0, -1, 18))
        emit("baut", M["chrome"], nut(x, y, RZ0 + 0.1, RZ0 + 2.5))
    for x, y in ((-11.0, 67.0), (11.0, 67.0)):                                    # leher sensor: spacer 12,5 kuningan
        emit("baut", M["brass"], prism(hexa(x, y, 5.5).difference(circ(x, y, 1.5, 16)), BOARDS["sensor"] + T, ub))
        emit("baut", M["chrome"], bolt(x, y, BOARDS["sensor"], 1, 6, "button"))
    for x, y in ((-12.5, 27.0), (12.5, 27.0), (-11.0, 67.0), (11.0, 67.0)):       # antarmuka: spacer 11 mm
        emit("baut", M["nylon"], prism(hexa(x, y, 5.5).difference(circ(x, y, 1.5, 16)), ut, BOARDS["antarmuka"]))
        emit("baut", M["chrome"], bolt(x, y, zs, -1, 6, "button"))
    emit("baut", M["chrome"], bolt(*SKID, BOARDS["sensor"] + T, -1, 5, "button"))
    emit("baut", M["chrome"], nut(*SKID, 1.9, 4.3))

    # ---- LiPo 2S (contoh: Tattu 300 mAh 47 x 17 x 13, ber-XT30) + strap + steker XT30 ----
    PX, PY, PZ = 47.0, 17.0, 13.0
    pc = -14.0
    pz0 = TZ0 + 3.0
    emit("pack", M["pack"], prism(rrect(-PX / 2, PX / 2, pc - PY / 2, pc + PY / 2, 2.0), pz0, pz0 + PZ))
    emit("pack", M["pack_lbl"], prism(sbox(-PX / 2 + 4, pc - PY / 2 + 2, PX / 2 - 4, pc + PY / 2 - 2), pz0 + PZ, pz0 + PZ + 0.05))
    hx, yb, yf = TRAY
    strap_path = [(pc + PY / 2 + 0.3, pz0 + PZ + 0.3), (yf + 0.3, TZ0 + 3.0), (yf + 0.3, TZ0 - 0.2), (yb - 0.3, TZ0 - 0.2),
                  (yb - 0.3, TZ0 + 3.0), (pc - PY / 2 - 0.3, pz0 + PZ + 0.3)]
    emit("pack", M["strap"], band(strap_path, -8.0, 8.0, 1.0))
    # steker XT30 betina di mulut J1 (XT30PW-M, tepi belakang papan utama y 19,5)
    plug = (18.4, 28.1, 8.8, 20.5, ut + 0.4, ut + 5.0)
    emit("pack", M["xt30"], boxm(*plug))
    OBST.append(("steker XT30", *plug))
    pxc = (plug[0] + plug[1]) / 2
    for m, d in (("wire_red", 1.2), ("wire_blk", -1.2)):       # kabel pack keluar dari ujung kanan pack
        emit("pack", M[m], tube([(PX / 2 - 1.0, pc + d, pz0 + 6.5), (PX / 2 + 3.0, pc + 3.0 + d, pz0 + 6.0),
                                 (21.0 + d, -3.0, TZ0 + 7.0), (21.0 + d, 4.5, TZ0 + 4.5),
                                 (pxc + d, plug[2] - 2.0, ut + 2.7), (pxc + d, plug[2] + 0.5, ut + 2.7)], 1.0, 10))

    # ---- kabel: JST XH 8 sensor <-> utama (16/11, ganti FFC), kabel encoder motor <-> driver J2/J3 ----
    # utama J3 siku di sisi bawah, mulut ke depan (badan sampai y 81,3); sensor J1 tegak, steker dari atas
    st_u = (-10.6, 10.6, 78.6, 85.0, ub - 5.6, ub - 0.6)
    st_s = (-10.6, 10.6, 94.7, 99.3, BOARDS["sensor"] + T + 6.5, BOARDS["sensor"] + T + 11.6)
    for box in (st_u, st_s):
        emit("kabel", M["jst"], boxm(*box))
    emit("kabel", M["ffc_blue"], ribbon([(85.0, ub - 3.1), (89.5, ub - 2.0), (93.5, ub + 0.4), (97.0, ub - 0.4),
                                         (97.0, st_s[5])], -9.5, 9.5, 1.2))
    dz = BOARDS["driver"] + T
    cols = ["wire_red", "wire_blk", "wire_yel", "wire_grn", "wire_blu", "wire_wht"]
    for ref in ("J2", "J3"):                    # JST XH 6 pin motor + encoder: tegak (steker dari atas) atau siku
        _, x0, x1, y0, y1, z0, z1 = next(o for o in OBST if o[0] == "driver:" + ref)
        s = 1 if x0 > 0 else -1
        if y1 - y0 > 8:                         # S6B-XH-A siku: mulut menghadap motor, steker masuk dari belakang
            jp = (x0 + 0.6, x1 - 0.6, y0 - 6.0, y0 + 0.5, dz + 0.4, z1 - 1.2)
            start = [((jp[2] + 0.2), (jp[4] + jp[5]) / 2), (jp[2] - 1.5, (jp[4] + jp[5]) / 2 + 1.0)]
        else:                                   # B6B-XH-A tegak: steker dari atas
            jp = (x0 + 0.6, x1 - 0.6, y0 + 0.5, y1 - 0.5, dz + 4.0, dz + 11.0)
            start = [((y0 + y1) / 2, jp[5] - 0.2), ((y0 + y1) / 2 - 0.5, jp[5] + 2.5)]
        emit("kabel", M["jst"], boxm(*jp))
        OBST.append((f"steker motor {ref}", *jp))
        for k, c in enumerate(cols):
            x = s * (min(abs(x0), abs(x1)) + 2.45 + 2.5 * k)
            emit("kabel", M[c], tube([(x, *start[0]), (x, *start[1]), (s * (9.0 + 0.6 * k), -4.0, 19.5),
                                      (s * 7.6, -2.5 + k, 17.0 + (k % 2) * 0.3), (s * 5.6, -2.5 + k, 17.0)], 0.45, 6))

    # ---- cek tabrakan (papan: poligon tepi; komponen, motor, ban, steker: kotak pembatas) ----
    hits = []
    board_obst = [(b, d["poly"], d["z"][0], d["z"][1]) for b, d in info.items()]
    for key in ("rangka", "tray"):
        hits += clash(names[key], slabs_of[key])
        for b, poly, z0, z1 in board_obst:
            for a, bb, p in slabs_of[key]:
                if min(bb, z1) - max(a, z0) > 0.05 and p.intersection(poly).area > 0.05:
                    hits.append(f"{names[key]} <-> papan {b}")
                    break
    hits += clash("Skid depan", slabs_of["skid"])
    # komponen papan dan steker terhadap motor/roda (bukan bagian cetak, tapi menentukan bentuk rangka)
    MOTOR = ("Gearbox N20", "Motor N20", "Tutup motor", "Encoder PCB", "Magnet encoder", "Konektor encoder", "Ban merah")
    other = []
    for o in OBST:
        if o[0].startswith(MOTOR):
            continue
        for m in OBST:
            if not m[0].startswith(MOTOR):
                continue
            d = [min(o[2 * i + 2], m[2 * i + 2]) - max(o[2 * i + 1], m[2 * i + 1]) for i in range(3)]
            if min(d) > 0.05:
                other.append(f"{o[0]} <-> {m[0]} ({d[0]:.1f} x {d[1]:.1f} x {d[2]:.1f} mm)")
    print("\ncek komponen/steker <-> motor dan ban:", "tidak ada" if not other else "")
    for h in other:
        print("  TABRAK", h)
    near = {
        "rangka - ban (mendatar)": min(gap(slabs_of["rangka"], *(-57.6, -39.4, -17.0, 17.0, 0.0, 34.0)),
                                       gap(slabs_of["rangka"], *(39.4, 57.6, -17.0, 17.0, 0.0, 34.0))),
        "dudukan baterai - steker XT30": gap(slabs_of["tray"], *plug),
        "rangka - konektor driver J2/J3": min(gap(slabs_of["rangka"], n[1], n[2], n[3], n[4], n[5], n[6])
                                              for n in OBST if n[0] in ("driver:J2", "driver:J3")),
        "skid - sensor tengah U6/U7": min(gap(slabs_of["skid"], n[1], n[2], n[3], n[4], 0.0, 4.5) for n in OBST
                                          if n[0] in ("sensor:U6", "sensor:U7")),
    }
    print("\ncek tabrakan bagian cetak:", "tidak ada" if not hits else "")
    for h in hits:
        print("  TABRAK", h)
    for k, v in near.items():
        print(f"  jarak {k}: {v:.2f} mm")

    # ---- ukuran ----
    allp = np.concatenate([p for g in GROUPS.values() for e in g.values() for p in e[1]])
    lo, hi = allp.min(0), allp.max(0)
    low = {"QRE1113GR sensor": BOARDS["sensor"] - 1.7, "kepala baut leher sensor": BOARDS["sensor"] - 1.7,
           "kepala baut telinga": BOARDS["driver"] - 3.0, "alas rangka motor": RZ0}
    extras = {
        "papan": {b: {k: v for k, v in d.items() if k != "poly"} for b, d in info.items()},
        "grup": {g: [round(float(v), 2) for v in (*np.concatenate([p for e in m.values() for p in e[1]]).min(0),
                                                    *np.concatenate([p for e in m.values() for p in e[1]]).max(0))]
                 for g, m in GROUPS.items()},
        "robot": [round(float(v), 2) for v in (*lo, *hi)], "roda": wheels, "oled_top": round(top_z, 2),
        "terendah": {k: round(v, 2) for k, v in low.items()}, "cetak": printed, "jarak": {k: round(v, 2) for k, v in near.items()},
        "tabrakan": hits, "tabrakan_lain": other, "skid": list(SKID), "telinga": list(EAR), "tray_z": TZ0, "rangka_z": RZ0,
        "sensor": sensor_points(),
        "pack": {"nama": "Tattu 2S 300 mAh (contoh)", "ukuran": [PX, PY, PZ], "ruang": [56.0, 31.0]},
    }
    raw = os.path.join(tmp, "LFM_X2_mentah.glb")
    gr.write_glb(GROUPS, extras, raw)
    n_tri = sum(len(i) for m in GROUPS.values() for e in m.values() for i in e[3]) // 3
    print(f"\nrakitan: {n_tri} segitiga, {os.path.getsize(raw) / 1e6:.1f} MB mentah")
    packed = os.path.join(tmp, "LFM_X2_web.glb")
    web = os.path.join(HERE, "LFM_X2_web.json")
    if gr.gltfpack(raw, packed, "-cc"):
        json.dump({"isi": "GLB (meshopt) base64, dari gen_rakitan_x2.py", "glb": base64.b64encode(open(packed, "rb").read()).decode()},
                  open(web, "w"))
        print(f"{os.path.basename(web)}: {os.path.getsize(web) / 1e6:.1f} MB")
    else:
        print("Node.js tidak ditemukan: LFM_X2_web.json tidak dibuat")
    print(json.dumps({k: v for k, v in extras.items() if k not in ("grup", "papan")}, indent=1)[:3000])
