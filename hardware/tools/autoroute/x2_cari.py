"""Pencari jalur papan LFM X2 (python sistem: numpy + scikit-image), masukan dari `x2_router.py ekspor`.

  py -I -X utf8 x2_cari.py <ekspor.json> <jalur.json> [iterasi maksimum, default 40] [NAMA=nilai ...]
  py -I -X utf8 x2_cari.py perbaiki <ekspor.json> <jalur.json> <jalur-baru.json> [iterasi per putaran]
  py -I -X utf8 x2_cari.py bongkar <ekspor.json> <jalur.json> <jalur-baru.json> <radius> [iterasi] [x,y ...]
                                   [--gnd <gnd.json>]

Grid 0,1 mm dua layer, A* arah 0/45/90 derajat dengan biaya belokan dan biaya via (jalur lurus, sedikit via),
heuristik jarak dari skimage MCP (lapis tengah = via). Supaya jalur yang dirouting duluan tidak menjadi tembok bagi
yang lain, dipakai cara PathFinder (negotiated congestion): semua sambungan dirouting ulang tiap iterasi, tabrakan
dengan jalur net lain boleh tapi mahal, dan biayanya naik tiap iterasi (biaya sekarang x faktor yang tumbuh + riwayat
tabrakan di sel itu) sampai tidak ada tabrakan.

Jarak: 0,3 mm ke tembaga net lain adalah batas keras (tabrakan = lebih dekat dari itu); sel yang lebih dekat dari
0,4 mm diberi biaya tambahan, jadi jalur mengambil 0,4 mm kalau ada ruang. Pad, lubang, tepi papan dan rule area
selalu batas keras. Jalur daya menyempit (0,5 lalu 0,3 mm) hanya kalau dengan lebar penuh tidak mungkin sampai.
Kalau macet di beberapa tabrakan, `perbaiki` membongkar hanya rute di sekitar titik tabrakan (rute lain dikunci) dan
mencarinya ulang, radius diperbesar tiap putaran. `bongkar` membongkar per net (seluruh net yang lewat dekat titik
yang diberikan, atau dekat pad kelompok GND yang masih terpisah dari `x2_router.py gnd`), jalur GND yang sudah ada
dikunci. Hasil: daftar segmen + via untuk `x2_router.py pasang`.
"""
import heapq
import json
import math
import sys
import time

import numpy as np
from skimage.graph import MCP_Geometric

G = 0.1                                   # langkah grid (mm)
EDGE, HOLE, MARGIN = 0.5, 0.5, 0.05       # ke tepi papan, ke lubang tanpa tembaga, cadangan galat grid
CLR, CLR_AMAN = 0.3, 0.4                  # jarak minimum (proyek; tempat cetak 0,254) dan jarak yang diutamakan
BIAYA_DEKAT = 0.6                         # tambahan biaya (x panjang) untuk sel di antara 0,3 dan 0,4 mm
VIA_D = 1.3
VIA_COST, BEND45, BEND90 = 2.5, 0.25, 1.0  # biaya dalam mm panjang jalur
BIAYA_B = 1.5                             # sisi bawah penuh komponen: jalan di B 1,5x lebih mahal, jalur panjang
                                          # cenderung lewat sisi atas yang kosong, B dipakai untuk keluar dari pad
JENDELA = 12.0                            # heuristik dihitung di kotak sambungan + 12 mm dulu, lalu seluruh papan
PRES0, PRES_NAIK, RIWAYAT = 0.5, 1.7, 0.5  # PathFinder: faktor tabrakan awal, kenaikan per iterasi, tambahan riwayat
LEBAR = {"VBAT": 1.0, "BAT+": 1.0, "BUCK_SW": 0.8, "+5V": 0.6, "+5V_BUCK": 0.6, "VBUS": 0.6, "+3V3": 0.5, "GND": 0.5,
         "ML_P": 1.0, "ML_N": 1.0, "MR_P": 1.0, "MR_N": 1.0}            # driver: keluaran motor (16/11)
USB = ("USB_DP", "USB_DM", "CC1", "CC2")
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
R2 = math.sqrt(2)
LI = {"F": 0, "B": 1}


class Grid:
    def __init__(self, outline):
        xs, ys = [p[0] for p in outline], [p[1] for p in outline]
        self.x0, self.y0 = min(xs) - 1, min(ys) - 1
        self.nx, self.ny = int((max(xs) - min(xs) + 2) / G) + 1, int((max(ys) - min(ys) + 2) / G) + 1
        self.X, self.Y = np.meshgrid(self.x0 + np.arange(self.nx) * G, self.y0 + np.arange(self.ny) * G, indexing="ij")

    def sl(self, x0, y0, x1, y1):
        i0 = max(0, int((x0 - self.x0) / G) - 1); i1 = min(self.nx, int((x1 - self.x0) / G) + 2)
        j0 = max(0, int((y0 - self.y0) / G) - 1); j1 = min(self.ny, int((y1 - self.y0) / G) + 2)
        return np.s_[i0:i1, j0:j1]

    def xy(self, i, j):
        return round(self.x0 + i * G, 4), round(self.y0 + j * G, 4)

    def kosong(self, dtype=bool):
        return np.zeros((2, self.nx, self.ny), dtype)


def dist_seg(X, Y, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L, 0, 1) if L > 0 else 0
    return np.hypot(X - ax - t * dx, Y - ay - t * dy)


def edge_dist(g, pts):
    """jarak bertanda sel ke tepi papan (+ = di dalam)"""
    d = np.full(g.X.shape, 1e9)
    inside = np.zeros(g.X.shape, bool)
    for i in range(len(pts)):
        a, c = pts[i - 1], pts[i]
        d = np.minimum(d, dist_seg(g.X, g.Y, a, c))
        cond = (a[1] > g.Y) != (c[1] > g.Y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xin = (c[0] - a[0]) * (g.Y - a[1]) / (c[1] - a[1]) + a[0]
        inside ^= cond & (g.X < xin)
    return np.where(inside, d, -d)


def kena(g, kind, data, m):
    """(slice, mask) sel yang berjarak < m dari bentuk"""
    if kind == "circ":
        x, y, r = data
        s = g.sl(x - r - m, y - r - m, x + r + m, y + r + m)
        return s, np.hypot(g.X[s] - x, g.Y[s] - y) < r + m
    if kind == "rect":
        x0, y0, x1, y1 = data
        s = g.sl(x0 - m, y0 - m, x1 + m, y1 + m)
        dx = np.maximum(np.maximum(x0 - g.X[s], g.X[s] - x1), 0)
        dy = np.maximum(np.maximum(y0 - g.Y[s], g.Y[s] - y1), 0)
        return s, (np.hypot(dx, dy) < m if m > 0 else (dx == 0) & (dy == 0))
    a, c, hw = data
    s = g.sl(min(a[0], c[0]) - hw - m, min(a[1], c[1]) - hw - m, max(a[0], c[0]) + hw + m, max(a[1], c[1]) + hw + m)
    return s, dist_seg(g.X[s], g.Y[s], a, c) < hw + m


def tandai(g, arr, lay, kind, data, m, tambah=False):
    s, hit = kena(g, kind, data, m)
    for L in lay:
        if tambah:
            arr[LI[L]][s] += hit
        else:
            arr[LI[L]][s] |= hit


def peta_tetap(g, ed, d, jalur_tetap, net, infl, via):
    """rintangan tetap (pad, lubang, tepi, rule area, jalur yang sudah ada sebelum routing) untuk pusat jalur
    (via=False) atau via (via=True) berjari-jari infl: (keras, dekat) — keras < 0,3 mm, dekat < 0,4 mm"""
    keras, dekat = g.kosong(), g.kosong()
    for k in range(2):
        keras[k] = ed < EDGE + infl
    for n, lay, kind, data, smd in d["items"]:
        if n == "#lubang":
            tandai(g, keras, lay, kind, data, HOLE + infl + MARGIN)
        elif n != net or not n:
            tandai(g, keras, lay, kind, data, CLR + infl + MARGIN)
            tandai(g, dekat, lay, kind, data, CLR_AMAN + infl + MARGIN)
        elif via and smd:                         # via tidak di atas pad SMD net sendiri (solder merembes)
            tandai(g, keras, lay, kind, data, 0.1 + infl)
    for n, lay, kind, data in jalur_tetap:
        if n != net:
            tandai(g, keras, lay, kind, data, CLR + infl + MARGIN)
            tandai(g, dekat, lay, kind, data, CLR_AMAN + infl + MARGIN)
    for lay, box, no_tr, no_via in d["area"]:
        if no_via if via else no_tr:
            tandai(g, keras, lay, "rect", box, infl)
    if via:                                       # via menembus kedua layer
        keras[:] = keras[0] | keras[1]
        dekat[:] = dekat[0] | dekat[1]
    return keras, dekat


def tembaga(g, path, w):
    """bentuk tembaga sebuah rute: segmen per layer + via"""
    polys, vias = jadi_segmen(g, path)
    out = []
    for L, verts in polys:
        if len(verts) == 1:
            out.append((L, "circ", (verts[0][0], verts[0][1], w / 2)))
        for a, c in zip(verts, verts[1:]):
            out.append((L, "seg", (a, c, w / 2)))
    out += [("FB", "circ", (x, y, VIA_D / 2)) for x, y in vias]
    return out


def sel_ujung(g, u, w=0.3):
    """sel awal/akhir: pad = sel yang membuat jalur selebar w tetap di dalam pad (keluar lewat tengah pad, tidak
    menyerempet pad tetangga); pulau jalur + via = sel di dalam tembaganya"""
    bagian = []                                # (layer, slice, mask)
    if u["jenis"] == "pulau":
        for lay, a, c, hw in u["segs"]:
            s = g.sl(min(a[0], c[0]) - 1, min(a[1], c[1]) - 1, max(a[0], c[0]) + 1, max(a[1], c[1]) + 1)
            bagian.append((lay, s, dist_seg(g.X[s], g.Y[s], a, c) < max(hw - 0.05, 0.05)))
        for lay, x, y, r in u["vias"]:
            s = g.sl(x - r, y - r, x + r, y + r)
            bagian.append((lay, s, np.hypot(g.X[s] - x, g.Y[s] - y) < r - 0.1))
    else:
        x0, y0, x1, y1 = u["box"]
        x, y = (x0 + x1) / 2, (y0 + y1) / 2
        m = max(w / 2, 0.12)
        hx, hy = max((x1 - x0) / 2 - m, 0.05), max((y1 - y0) / 2 - m, 0.05)
        s = g.sl(x - hx, y - hy, x + hx, y + hy)
        bagian.append((u["lay"], s, (abs(g.X[s] - x) <= hx) & (abs(g.Y[s] - y) <= hy)))
    sel = set()
    for lay, s, m in bagian:
        ii, jj = np.nonzero(m)
        i0, j0 = s[0].start, s[1].start
        sel |= {(L, int(i + i0), int(j + j0)) for L in lay for i, j in zip(ii, jj)}
    return sel


def heuristik(g, biaya, vbiaya, src, dst, penuh):
    """sisa biaya (mm) ke tujuan per sel, abaikan belokan: MCP 3 lapis (F, via, B). (cum, i0, j0) atau None"""
    cells = src | dst
    ii = [c[1] for c in cells]; jj = [c[2] for c in cells]
    if penuh:
        i0, i1, j0, j1 = 0, g.nx, 0, g.ny
    else:
        k = int(JENDELA / G)
        i0, i1 = max(0, min(ii) - k), min(g.nx, max(ii) + k + 1)
        j0, j1 = max(0, min(jj) - k), min(g.ny, max(jj) + k + 1)
    w = (slice(i0, i1), slice(j0, j1))
    c = np.empty((3, i1 - i0, j1 - j0))
    c[0], c[2] = biaya[0][w], biaya[1][w]
    c[1] = vbiaya[w] / G - 1.0
    for L, i, j in cells:
        c[0 if L == "F" else 2, i - i0, j - j0] = 1.0 if L == "F" else BIAYA_B
    off = [(0, a, b) for a, b in DIRS] + [(1, 0, 0), (-1, 0, 0)]
    cum, _ = MCP_Geometric(c, offsets=off).find_costs([(0 if L == "F" else 2, i - i0, j - j0) for L, i, j in dst])
    if not any(np.isfinite(cum[0 if L == "F" else 2, i - i0, j - j0]) for L, i, j in src):
        return None
    return cum * G, i0, j0


def astar(g, biaya, vbiaya, src, dst, anchor, hh):
    cum, ci0, cj0 = hh
    nI, nJ = cum.shape[1], cum.shape[2]
    hl = {"F": cum[0], "B": cum[2]}
    bl = {"F": biaya[0], "B": biaya[1]}

    def h(L, i, j):
        a, b = i - ci0, j - cj0
        if not (0 <= a < nI and 0 <= b < nJ):
            return math.inf
        return float(hl[L][a, b])

    openq, best, prev = [], {}, {}
    for c in src:
        hv = h(c[0], c[1], c[2])
        if not math.isfinite(hv):
            continue
        st = (c[0], c[1], c[2], 8)
        c0 = 0.0
        if anchor:
            x, y = g.xy(c[1], c[2])
            c0 = 0.5 * math.hypot(x - anchor[0], y - anchor[1])
        best[st] = c0
        heapq.heappush(openq, (c0 + hv, -c0, st))
    n = 0
    while openq:
        f, ncost, st = heapq.heappop(openq)
        cost = -ncost
        if cost > best.get(st, math.inf):
            continue
        L, i, j, d = st
        if (L, i, j) in dst:
            path = [st]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return [p[:3] for p in path[::-1]]
        n += 1
        if n > 3_000_000:
            return None
        b = bl[L]
        for nd, (di, dj) in enumerate(DIRS):
            if d != 8:
                turn = abs(nd - d); turn = min(turn, 8 - turn)
                if turn > 2:
                    continue
                tc = (0.0, BEND45, BEND90)[turn]
            else:
                tc = 0.0
            ii, jj = i + di, j + dj
            if not (0 <= ii < g.nx and 0 <= jj < g.ny):
                continue
            tujuan = (L, ii, jj) in dst
            cc = b[ii, jj]
            if tujuan:
                cc = min(cc, 1.0)
            elif cc == math.inf:
                continue
            if di and dj and not tujuan and (b[i + di, j] == math.inf or b[i, j + dj] == math.inf):
                continue                          # jangan menyelip diagonal di antara dua sel terlarang
            ns = (L, ii, jj, nd)
            nc = cost + (G * R2 if di and dj else G) * cc + tc
            if nc < best.get(ns, math.inf):
                hv = h(L, ii, jj)
                if math.isfinite(hv):
                    best[ns] = nc
                    prev[ns] = st
                    heapq.heappush(openq, (nc + hv, -nc, ns))
        vc = vbiaya[i, j]
        if vc != math.inf:
            L2 = "B" if L == "F" else "F"
            ns = (L2, i, j, 8)
            nc = cost + vc
            if nc < best.get(ns, math.inf):
                hv = h(L2, i, j)
                if math.isfinite(hv):
                    best[ns] = nc
                    prev[ns] = st
                    heapq.heappush(openq, (nc + hv, -nc, ns))
    return None


def jadi_segmen(g, path):
    """path sel -> polyline per layer (titik belok saja) + titik via"""
    runs, vias, cur = [], [], [path[0]]
    for a, c in zip(path, path[1:]):
        if c[0] != a[0]:
            runs.append(cur); vias.append(g.xy(c[1], c[2])); cur = [c]
        else:
            cur.append(c)
    runs.append(cur)
    out = []
    for r in runs:
        ps = [g.xy(p[1], p[2]) for p in r]
        verts = [ps[0]]
        for k in range(1, len(ps) - 1):
            d1 = (round((ps[k][0] - ps[k - 1][0]) / G), round((ps[k][1] - ps[k - 1][1]) / G))
            d2 = (round((ps[k + 1][0] - ps[k][0]) / G), round((ps[k + 1][1] - ps[k][1]) / G))
            if d1 != d2:
                verts.append(ps[k])
        if len(ps) > 1:
            verts.append(ps[-1])
        out.append((r[0][0], verts))
    return out, vias


def urutan(p):
    net = p["net"]
    w = p.get("w", LEBAR.get(net, 0.3))
    kelas = 0 if (net in LEBAR and net != "GND") or w >= 1.0 else 1 if net in USB else 3 if net == "GND" else 2
    return kelas, -w, p["jarak"]


class Router:
    def __init__(self, d):
        self.d = d
        self.g = Grid(d["outline"])
        self.ed = edge_dist(self.g, d["outline"])
        self.tetap = d["jalur"]
        self.cache = {}
        self.riwayat = self.g.kosong(float)
        self.vriwayat = np.zeros((self.g.nx, self.g.ny))

    def peta(self, net, w):
        k = (net, w)
        if k not in self.cache:
            self.cache[k] = (peta_tetap(self.g, self.ed, self.d, self.tetap, net, w / 2, False),
                             peta_tetap(self.g, self.ed, self.d, self.tetap, net, VIA_D / 2, True))
        return self.cache[k]

    def lunak(self, rute, net, infl, via):
        """jumlah net lain yang tembaganya < 0,3 mm (tabrak) dan < 0,4 mm (dekat) dari pusat jalur/via"""
        tabrak, dekat = self.g.kosong(np.float32), self.g.kosong(bool)
        for r in rute.values():
            if r is None or r["net"] == net:
                continue
            for lay, kind, data in r["cu"]:
                tandai(self.g, tabrak, lay, kind, data, CLR + infl + MARGIN, tambah=True)
                tandai(self.g, dekat, lay, kind, data, CLR_AMAN + infl + MARGIN)
        if via:
            tabrak[:] = tabrak[0] + tabrak[1]
            dekat[:] = dekat[0] | dekat[1]
        return tabrak, dekat

    def biaya(self, net, w, rute, pres):
        (keras, dekat_t), (vkeras, vdekat_t) = self.peta(net, w)
        tabrak, dekat = self.lunak(rute, net, w / 2, False)
        vtabrak, vdekat = self.lunak(rute, net, VIA_D / 2, True)
        dasar = np.array([1.0, BIAYA_B])[:, None, None]
        b = dasar * (1 + self.riwayat) * (1 + pres * tabrak) + dasar * BIAYA_DEKAT * (dekat | dekat_t)
        b[keras] = np.inf
        vb = VIA_COST * (1 + self.vriwayat) * (1 + pres * vtabrak[0]) + VIA_COST * BIAYA_DEKAT * (vdekat[0] | vdekat_t[0])
        vb[vkeras[0]] = np.inf
        return b, vb

    def satu(self, p, rute, pres):
        net = p["net"]
        w0 = p.get("w", LEBAR.get(net, 0.3))      # lebar khusus per sambungan (mis. jalur balik arus motor)
        for w in [w0] + [x for x in (0.5, 0.3) if x < w0]:
            src, dst = sel_ujung(self.g, p["A"], w), sel_ujung(self.g, p["B"], w)
            b, vb = self.biaya(net, w, rute, pres)
            for penuh in (False, True):
                hh = heuristik(self.g, b, vb, src, dst, penuh)
                if hh is None:
                    continue
                path = astar(self.g, b, vb, src, dst, p["A"]["anchor"], hh)
                if path:
                    return {"net": net, "w": w, "path": path, "cu": tembaga(self.g, path, w)}
        return None

    def tabrakan(self, rute):
        """rute yang lebih dekat dari 0,3 mm ke tembaga net lain + sel tempat tabrakannya"""
        hasil = {}
        for k, r in rute.items():
            if r is None:
                continue
            tabrak, _ = self.lunak({q: v for q, v in rute.items() if q != k}, r["net"], r["w"] / 2, False)
            vt, _ = self.lunak({q: v for q, v in rute.items() if q != k}, r["net"], VIA_D / 2, True)
            sel = [(L, i, j) for L, i, j in r["path"] if tabrak[LI[L], i, j] > 0]
            vias = jadi_segmen(self.g, r["path"])[1]
            vsel = []
            for x, y in vias:
                i, j = round((x - self.g.x0) / G), round((y - self.g.y0) / G)
                if vt[0, i, j] > 0:
                    vsel.append((i, j))
            if sel or vsel:
                hasil[k] = (sel, vsel)
        return hasil


def rute_data(R, d, k, r):
    """rute -> segmen + via (koordinat mm), `k` = nomor sambungan di ekspor asal"""
    p = d["pasang"][k]
    polys, vs = jadi_segmen(R.g, r["path"])
    if p["A"]["anchor"]:
        polys[0][1].insert(0, tuple(p["A"]["anchor"]))
    if p["B"]["anchor"]:
        polys[-1][1].append(tuple(p["B"]["anchor"]))
    tr = [[L, a[0], a[1], c[0], c[1], r["w"]] for L, verts in polys for a, c in zip(verts, verts[1:])
          if math.hypot(c[0] - a[0], c[1] - a[1]) > 1e-3]
    return {"k": p.get("k0", k), "net": p["net"], "w": r["w"], "tracks": tr, "vias": [list(v) for v in vs]}


def tulis(R, d, urut, rute, tb, out, tetap=()):
    """tracks/vias = rute yang bersih (siap dipasang); `rute` = semua rute termasuk yang bertabrakan (dengan titik
    tabrakannya), dipakai `perbaiki`"""
    semua, gagal, sempit = list(tetap), [], []
    for k in urut:
        p, r = d["pasang"][k], rute[k]
        if r is None:
            gagal.append(p["net"])
            continue
        x = rute_data(R, d, k, r)
        if k in tb:
            gagal.append(p["net"])
            sel, vsel = tb[k]
            x["tabrak"] = [list(R.g.xy(i, j)) for L, i, j in sel[::4]] + [list(R.g.xy(i, j)) for i, j in vsel]
        elif r["w"] < p.get("w", LEBAR.get(p["net"], 0.3)):
            sempit.append((p["net"], r["w"]))
        semua.append(x)
    bersih = [x for x in semua if "tabrak" not in x]
    tracks = [[x["net"]] + s for x in bersih for s in x["tracks"]]
    vias = [[x["net"]] + v for x in bersih for v in x["vias"]]
    json.dump({"tracks": tracks, "vias": vias, "gagal": gagal, "rute": semua}, open(out, "w", encoding="utf8"))
    return tracks, vias, gagal, sempit


def jalankan(d, out, iterasi, tetap=()):
    """PathFinder untuk semua d["pasang"]; hasil terbaik ditulis tiap kali membaik, jadi boleh dihentikan kapan saja.
    Mengembalikan jumlah sambungan yang belum bersih."""
    R = Router(d)
    urut = sorted(range(len(d["pasang"])), key=lambda k: urutan(d["pasang"][k]))
    rute = {k: None for k in urut}
    pres, t0, skor_terbaik = PRES0, time.time(), None
    for it in range(1, iterasi + 1):
        for k in urut:
            rute[k] = None                         # bongkar rute lama net ini, cari lagi dengan biaya sekarang
            rute[k] = R.satu(d["pasang"][k], rute, pres)
        tb = R.tabrakan(rute)
        gagal = [k for k in urut if rute[k] is None]
        nvia = sum(len(jadi_segmen(R.g, r["path"])[1]) for r in rute.values() if r)
        print(f"iterasi {it}: {len(tb)} rute bertabrakan {sorted(d['pasang'][k]['net'] for k in tb)}, "
              f"{len(gagal)} tidak sampai, {nvia} via, faktor {pres:.1f} ({time.time() - t0:.0f} s)", flush=True)
        skor = (len(gagal), len(tb), nvia)
        if skor_terbaik is None or skor < skor_terbaik:
            skor_terbaik = skor
            tracks, vias, gagal_net, sempit = tulis(R, d, urut, rute, tb, out, tetap)
            print(f"  ditulis: {len(gagal_net)} sambungan belum; {gagal_net}; menyempit: {sempit}", flush=True)
        if not tb:
            break
        for k, (sel, vsel) in tb.items():
            for L, i, j in sel:
                R.riwayat[LI[L], i, j] += RIWAYAT
            for i, j in vsel:
                R.vriwayat[i, j] += RIWAYAT
        pres *= PRES_NAIK
    print("selesai", flush=True)
    return skor_terbaik[0] + skor_terbaik[1]


def main(inp, out, iterasi=40):
    jalankan(json.load(open(inp, encoding="utf8")), out, iterasi)


def dekat_titik(x, titik, rad):
    for L, x1, y1, x2, y2, w in x["tracks"]:
        dx, dy = x2 - x1, y2 - y1
        ll = dx * dx + dy * dy or 1e-9
        for px, py in titik:
            u = min(1, max(0, ((px - x1) * dx + (py - y1) * dy) / ll))
            if math.hypot(x1 + u * dx - px, y1 + u * dy - py) < rad:
                return True
    return any(math.hypot(vx - px, vy - py) < rad for vx, vy in x["vias"] for px, py in titik)


def jalur_kunci(tetap):
    """rute yang dikunci -> jalur tetap (tembok bagi net lain)"""
    return [[x["net"], s[0], "seg", [[s[1], s[2]], [s[3], s[4]], s[5] / 2]] for x in tetap for s in x["tracks"]] \
        + [[x["net"], "FB", "circ", [v[0], v[1], VIA_D / 2]] for x in tetap for v in x["vias"]]


def bongkar_net(inp, hasil, out, rad, iterasi=30, titik=(), gnd=None):
    """bongkar per net: net (selain GND) yang gagal di `hasil` + net yang lewat < rad mm dari `titik` dibongkar seluruhnya
    dan dicari ulang dengan sambungannya dari `inp`; jalur lain, termasuk semua jalur GND, dikunci. Dengan `gnd`
    (keluaran `x2_router.py gnd`), sambungan kelompok GND terpisah ikut dicari dan pad kelompok itu menjadi titik
    bongkar."""
    d0 = json.load(open(inp, encoding="utf8"))
    c = json.load(open(hasil, encoding="utf8"))
    titik = list(titik)
    gp = []
    for p in (json.load(open(gnd, encoding="utf8"))["pasang"] if gnd else []):
        A = dict(p["A"], vias=[])                  # sisi kelompok terpisah: pad saja (pulaunya berubah sesudah routing)
        titik += [((s[1][0] + s[2][0]) / 2, (s[1][1] + s[2][1]) / 2) for s in A["segs"]]
        gp.append({"net": "GND", "A": A, "B": p["B"], "jarak": p["jarak"]})
    bongkar = set(c["gagal"])
    for t in c["tracks"]:
        if dekat_titik({"tracks": [t[1:]], "vias": []}, titik, rad):
            bongkar.add(t[0])
    for v in c["vias"]:
        if dekat_titik({"tracks": [], "vias": [v[1:]]}, titik, rad):
            bongkar.add(v[0])
    bongkar.discard("GND")
    tetap = {}
    for t in c["tracks"]:
        if t[0] not in bongkar:
            tetap.setdefault(t[0], {"net": t[0], "k": -1, "tracks": [], "vias": []})["tracks"].append(t[1:])
    for v in c["vias"]:
        if v[0] not in bongkar:
            tetap.setdefault(v[0], {"net": v[0], "k": -1, "tracks": [], "vias": []})["vias"].append(v[1:])
    tetap = list(tetap.values())
    d = dict(d0)
    d["jalur"] = d0["jalur"] + jalur_kunci(tetap)
    d["pasang"] = [p for p in d0["pasang"] if p["net"] in bongkar] + gp
    print(f"dibongkar {len(bongkar)} net: {sorted(bongkar)}; {len(d['pasang'])} sambungan dicari ({len(gp)} GND)",
          flush=True)
    return jalankan(d, out, iterasi, tetap)


def perbaiki(inp, hasil, out, iterasi=30, rad=3.0, putaran=6):
    """bongkar lokal: rute yang bertabrakan/belum sampai + semua rute yang lewat < rad mm dari titik tabrakan dicari
    ulang, rute lain dikunci (jadi tembok). Diulang dengan radius membesar sampai bersih."""
    d0 = json.load(open(inp, encoding="utf8"))
    h = json.load(open(hasil, encoding="utf8"))
    for pt in range(1, putaran + 1):
        rute = h["rute"]
        titik = [q for x in rute if "tabrak" in x for q in x["tabrak"]]
        ada = {x["k"] for x in rute}
        belum = [k for k in range(len(d0["pasang"])) if k not in ada]       # tidak sampai
        for k in belum:
            p = d0["pasang"][k]
            titik += [p[s]["anchor"] or [(p[s]["box"][0] + p[s]["box"][2]) / 2, (p[s]["box"][1] + p[s]["box"][3]) / 2]
                      for s in "AB" if p[s]["jenis"] == "pad"]
        if not titik and not belum:
            print("bersih")
            return
        bongkar = {x["k"] for x in rute if "tabrak" in x or dekat_titik(x, titik, rad)} | set(belum)
        tetap = [x for x in rute if x["k"] not in bongkar]
        d = dict(d0)
        d["jalur"] = d0["jalur"] + jalur_kunci(tetap)
        d["pasang"] = [dict(d0["pasang"][k], k0=k) for k in sorted(bongkar)]
        print(f"putaran {pt}: radius {rad} mm, {len(bongkar)} rute dicari ulang, {len(tetap)} dikunci", flush=True)
        sisa = jalankan(d, out, iterasi, tetap)
        if sisa == 0:
            print("bersih")
            return
        h = json.load(open(out, encoding="utf8"))
        rad += 1.5


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if "=" not in x]
    for kv in [x for x in sys.argv[1:] if "=" in x]:    # setelan coba-coba, mis. PRES_NAIK=1.3 RIWAYAT=1.0
        k, v = kv.split("=")
        if k.startswith("LEBAR_"):                     # lebar per net, mis. LEBAR_VBAT=0.6
            LEBAR[k[6:]] = float(v)
        else:
            globals()[k] = float(v)
    if a[0] == "perbaiki":
        perbaiki(a[1], a[2], a[3], *(int(x) for x in a[4:5]))
    elif a[0] == "bongkar":
        g = a[a.index("--gnd") + 1] if "--gnd" in a else None
        b = [x for x in a[1:] if x not in ("--gnd", g)]
        pts = [tuple(map(float, x.split(","))) for x in b if "," in x]
        b = [x for x in b if "," not in x]
        bongkar_net(b[0], b[1], b[2], float(b[3]), *(int(x) for x in b[4:5]), titik=pts, gnd=g)
    else:
        main(a[0], a[1], *(int(x) for x in a[2:3]))
