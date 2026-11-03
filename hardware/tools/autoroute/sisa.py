"""Routing sisa: sambungkan pasangan item yang masih "unconnected" di laporan DRC (JSON kicad-cli) dengan router grid
A* dua layer. Dipakai karena FreeRouting 2.1 kadang membuang beberapa net dari file SES walau lognya bilang lengkap.

Dijalankan dengan python KiCad (pcbnew + numpy), board di file (bukan board live):
  "$KPY" hardware/tools/autoroute/sisa.py <board.kicad_pcb> <drc.json> [net yang dilewati, mis. GND]
Hapus GND pour dulu (pour ikut dianggap rintangan); buat ulang pour sesudahnya. Lebar jalur per net sama dengan
dsnfix.py. Jarak: 0,3 mm ke tembaga net lain, 0,5 mm ke tepi papan dan lubang tanpa tembaga; tidak masuk rule area.
"""
import heapq
import json
import math
import sys

import numpy as np
import pcbnew

G = 0.1                                   # langkah grid (mm)
CLR, EDGE, HOLE = 0.3, 0.5, 0.5           # clearance tembaga, ke tepi, ke lubang NPTH
MARGIN = 0.06                             # cadangan galat grid (sel 0,1 mm)
VIA_D, VIA_DRILL, VIA_COST = 1.0, 0.6, 2.5
WIDTH = {"VBAT": 1.0, "BAT+": 1.0, "ML_P": 0.8, "ML_N": 0.8, "MR_P": 0.8, "MR_N": 0.8, "+5V": 0.8, "+5V_BUCK": 0.8,
         "+3V3": 0.5, "GND": 0.5}
_SIMPAN = []                              # referensi objek SWIG yang dibuang (lihat gen_pcb_utama_v17.py)


def mm(v):
    return pcbnew.ToMM(v)


class Grid:
    def __init__(self, b):
        bb = b.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = mm(bb.GetLeft()) - 1, mm(bb.GetTop()) - 1
        self.nx, self.ny = int((mm(bb.GetWidth()) + 2) / G) + 1, int((mm(bb.GetHeight()) + 2) / G) + 1
        xs = self.x0 + np.arange(self.nx) * G
        ys = self.y0 + np.arange(self.ny) * G
        self.X, self.Y = np.meshgrid(xs, ys, indexing="ij")

    def sl(self, x0, y0, x1, y1):
        i0 = max(0, int((x0 - self.x0) / G) - 1); i1 = min(self.nx, int((x1 - self.x0) / G) + 2)
        j0 = max(0, int((y0 - self.y0) / G) - 1); j1 = min(self.ny, int((y1 - self.y0) / G) + 2)
        return np.s_[i0:i1, j0:j1]

    def cell(self, x, y):
        return int(round((x - self.x0) / G)), int(round((y - self.y0) / G))

    def xy(self, i, j):
        return self.x0 + i * G, self.y0 + j * G


def dist_seg(X, Y, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L, 0, 1) if L > 0 else 0
    return np.hypot(X - ax - t * dx, Y - ay - t * dy)


def shapes(b):
    """tembaga & rintangan: (net, layers, jenis, data, jarak minimum)"""
    out = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bx = p.GetBoundingBox()
            box = (mm(bx.GetLeft()), mm(bx.GetTop()), mm(bx.GetRight()), mm(bx.GetBottom()))
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                c = p.GetPosition()
                out.append((None, "FB", "circ", (mm(c.x), mm(c.y), mm(p.GetDrillSize().x) / 2), HOLE))
                continue
            lay = ("F" if p.IsOnLayer(pcbnew.F_Cu) else "") + ("B" if p.IsOnLayer(pcbnew.B_Cu) else "")
            if p.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
                c = p.GetPosition()
                out.append((p.GetNetname(), lay, "circ", (mm(c.x), mm(c.y), mm(p.GetSize(pcbnew.F_Cu).x) / 2), CLR))
            else:
                out.append((p.GetNetname(), lay, "rect", box, CLR))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition()
            out.append((t.GetNetname(), "FB", "circ", (mm(c.x), mm(c.y), mm(t.GetWidth(pcbnew.F_Cu)) / 2), CLR))
        else:
            s, e = t.GetStart(), t.GetEnd()
            out.append((t.GetNetname(), "F" if t.GetLayer() == pcbnew.F_Cu else "B", "seg",
                        ((mm(s.x), mm(s.y)), (mm(e.x), mm(e.y)), mm(t.GetWidth()) / 2), CLR))
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowTracks():
            bx = z.GetBoundingBox()
            out.append((None, "FB", "rect", (mm(bx.GetLeft()), mm(bx.GetTop()), mm(bx.GetRight()), mm(bx.GetBottom())), 0.0))
    return out


def edge_dist(b, g):
    """jarak bertanda sel ke tepi papan (+ = di dalam)"""
    ps = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(ps, False)
    ol = ps.Outline(0)
    pts = [(mm(ol.CPoint(i).x), mm(ol.CPoint(i).y)) for i in range(ol.PointCount())]
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


def blocked(g, items, net, infl, ed, edge_min):
    """sel terlarang untuk pusat jalur/via dengan jari-jari infl, per layer"""
    blk = {"F": ed < edge_min, "B": ed < edge_min}
    blk = {k: v.copy() for k, v in blk.items()}
    for n, lay, kind, data, clr in items:
        if n == net and n:
            continue
        m = clr + infl + MARGIN
        if kind == "circ":
            x, y, r = data
            s = g.sl(x - r - m, y - r - m, x + r + m, y + r + m)
            hit = np.hypot(g.X[s] - x, g.Y[s] - y) < r + m
        elif kind == "rect":
            x0, y0, x1, y1 = data
            s = g.sl(x0 - m, y0 - m, x1 + m, y1 + m)
            dx = np.maximum(np.maximum(x0 - g.X[s], g.X[s] - x1), 0)
            dy = np.maximum(np.maximum(y0 - g.Y[s], g.Y[s] - y1), 0)
            hit = np.hypot(dx, dy) < m if clr > 0 else (dx == 0) & (dy == 0)
        else:
            a, c, hw = data
            s = g.sl(min(a[0], c[0]) - hw - m, min(a[1], c[1]) - hw - m, max(a[0], c[0]) + hw + m, max(a[1], c[1]) + hw + m)
            hit = dist_seg(g.X[s], g.Y[s], a, c) < hw + m
        for L in lay:
            blk[L][s] |= hit
    return blk


def item_cells(g, it):
    """sel di dalam tembaga item (pad / track / via) + titik jangkar + layer"""
    if isinstance(it, pcbnew.PCB_TRACK) and it.GetClass() != "PCB_VIA":
        a, c = it.GetStart(), it.GetEnd()
        a, c = (mm(a.x), mm(a.y)), (mm(c.x), mm(c.y))
        s = g.sl(min(a[0], c[0]) - 1, min(a[1], c[1]) - 1, max(a[0], c[0]) + 1, max(a[1], c[1]) + 1)
        m = dist_seg(g.X[s], g.Y[s], a, c) < max(mm(it.GetWidth()) / 2 - 0.05, 0.05)
        lays = "F" if it.GetLayer() == pcbnew.F_Cu else "B"
        anchor = ("seg", a, c)
    else:
        c = it.GetPosition()
        x, y = mm(c.x), mm(c.y)
        if isinstance(it, pcbnew.PAD):
            bx = it.GetBoundingBox()
            hx, hy = mm(bx.GetWidth()) / 2 - 0.15, mm(bx.GetHeight()) / 2 - 0.15
            lays = ("F" if it.IsOnLayer(pcbnew.F_Cu) else "") + ("B" if it.IsOnLayer(pcbnew.B_Cu) else "")
        else:
            hx = hy = mm(it.GetWidth(pcbnew.F_Cu)) / 2 - 0.1
            lays = "FB"
        s = g.sl(x - hx, y - hy, x + hx, y + hy)
        m = (abs(g.X[s] - x) <= hx) & (abs(g.Y[s] - y) <= hy)
        anchor = ("pt", (x, y))
    ii, jj = np.nonzero(m)
    i0, j0 = s[0].start, s[1].start
    cells = {(L, int(i + i0), int(j + j0)) for L in lays for i, j in zip(ii, jj)}
    return cells, anchor


def astar(g, blk, vblk, src, dst):
    goal = dst
    gi = np.array([c[1] for c in goal]); gj = np.array([c[2] for c in goal])
    bi0, bi1, bj0, bj1 = gi.min(), gi.max(), gj.min(), gj.max()

    def h(i, j):
        dx = max(bi0 - i, 0, i - bi1); dy = max(bj0 - j, 0, j - bj1)
        return (max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)) * G

    openq, best, prev = [], {}, {}
    for c in src:
        best[c] = 0.0
        heapq.heappush(openq, (h(c[1], c[2]), 0.0, c))
    steps = [(1, 0, G), (-1, 0, G), (0, 1, G), (0, -1, G)] + [(a, b_, G * math.sqrt(2)) for a in (1, -1) for b_ in (1, -1)]
    n = 0
    while openq:
        f, cost, c = heapq.heappop(openq)
        if cost > best.get(c, 1e18):
            continue
        if c in goal:
            path = [c]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return path[::-1]
        n += 1
        if n > 4_000_000:
            return None
        L, i, j = c
        nb = []
        for di, dj, w in steps:
            ii, jj = i + di, j + dj
            if 0 <= ii < g.nx and 0 <= jj < g.ny and (not blk[L][ii, jj] or (L, ii, jj) in goal):
                nb.append(((L, ii, jj), w))
        if not vblk[i, j]:
            nb.append((("B" if L == "F" else "F", i, j), VIA_COST))
        for d, w in nb:
            nc = cost + w
            if nc < best.get(d, 1e18):
                best[d] = nc
                prev[d] = c
                heapq.heappush(openq, (nc + h(d[1], d[2]), nc, d))
    return None


def los(g, blk, L, a, b_, src_goal):
    """garis lurus a-b bebas rintangan di layer L"""
    n = int(math.hypot(b_[0] - a[0], b_[1] - a[1]) / (G / 2)) + 1
    for k in range(n + 1):
        x = a[0] + (b_[0] - a[0]) * k / n; y = a[1] + (b_[1] - a[1]) * k / n
        i, j = g.cell(x, y)
        if blk[L][i, j] and (L, i, j) not in src_goal:
            return False
    return True


def main(brd, drcfile, skip=()):
    b = pcbnew.LoadBoard(brd)
    rep = json.load(open(drcfile, encoding="utf-8"))
    byid = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            byid[p.m_Uuid.AsString()] = p
    for t in b.GetTracks():
        byid[t.m_Uuid.AsString()] = t
    g = Grid(b)
    ed = edge_dist(b, g)
    vr = VIA_D / 2
    ok = 0
    for u in rep.get("unconnected_items", []):
        A, B = (byid.get(i["uuid"]) for i in u["items"])
        if A is None or B is None:
            print("  item tidak ketemu:", [i["description"] for i in u["items"]]); continue
        net = A.GetNetname()
        if net in skip:
            continue
        w = WIDTH.get(net, 0.3)
        items = shapes(b)
        blk = blocked(g, items, net, w / 2, ed, EDGE + w / 2)
        vb = blocked(g, items, net, vr, ed, EDGE + vr)
        vblk = vb["F"] | vb["B"]
        src, sa = item_cells(g, A)
        dst, da = item_cells(g, B)
        path = astar(g, blk, vblk, src, dst)
        if not path:
            print(f"  GAGAL {net}: {[i['description'][:40] for i in u['items']]}"); continue
        # pecah per layer, rapikan dengan garis lurus terpanjang yang bebas
        segs, vias = [], []
        run = [path[0]]
        runs = []
        for c in path[1:]:
            if c[0] != run[-1][0]:
                runs.append(run); vias.append(g.xy(c[1], c[2])); run = [c]
            else:
                run.append(c)
        runs.append(run)
        sg = src | dst
        for r in runs:
            L = r[0][0]
            pts = [g.xy(c[1], c[2]) for c in r]
            k = 0
            while k < len(pts) - 1:
                m = len(pts) - 1
                while m > k + 1 and not los(g, blk, L, pts[k], pts[m], sg):
                    m -= 1
                segs.append((L, pts[k], pts[m]))
                k = m
        # ujung disambung ke jangkar item (pusat pad / garis tengah track)
        def snap(anchor, p):
            if anchor[0] == "pt":
                return anchor[1]
            (ax, ay), (cx, cy) = anchor[1], anchor[2]
            dx, dy = cx - ax, cy - ay
            t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / ((dx * dx + dy * dy) or 1)))
            return ax + t * dx, ay + t * dy
        L0, p0, p1 = segs[0]
        segs.insert(0, (L0, snap(sa, p0), p0))
        Ln, q0, q1 = segs[-1]
        segs.append((Ln, q1, snap(da, q1)))
        netinfo = b.FindNet(net)
        for L, a, c in segs:
            if math.hypot(c[0] - a[0], c[1] - a[1]) < 1e-3:
                continue
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(c[0]), pcbnew.FromMM(c[1])))
            t.SetWidth(pcbnew.FromMM(w))
            t.SetLayer(pcbnew.F_Cu if L == "F" else pcbnew.B_Cu)
            t.SetNet(netinfo)
            b.Add(t)
        for x, y in vias:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
            v.SetWidth(pcbnew.F_Cu, pcbnew.FromMM(VIA_D))
            v.SetDrill(pcbnew.FromMM(VIA_DRILL))
            v.SetNet(netinfo)
            b.Add(v)
        ok += 1
        print(f"  {net}: {len(segs)} segmen, {len(vias)} via, panjang "
              f"{sum(math.hypot(c[0] - a[0], c[1] - a[1]) for _, a, c in segs):.1f} mm")
    pcbnew.SaveBoard(brd, b)
    print(f"tersambung {ok} dari {len(rep.get('unconnected_items', []))}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
