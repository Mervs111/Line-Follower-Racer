"""Outline PCB sensor rev C (20/11/2026): rev B dengan pita busur lebih tebal untuk aturan cetak jalur 0,5 / jarak 0,7.

Posisi QRE, komponen, tangkai, dan tab lubang sama dengan rev B; hanya tepi belakang pita (dan sisi dalam kait)
yang mundur, karena lajur jalur S di belakang sensor sekarang 1,2 mm (0,5 + 0,7), dulu 0,7 mm, ditambah 2 lajur
(2,4 mm) untuk jalur GND ke tiap QRE (GND dirouting sebagai jalur, pour saja terpecah). Bagian lain rev C (bukan dari
skrip ini): U13, C1, J1 mundur 2,5 mm ke tangkai, 24 resistor di F.Cu, pad U13 0,5 mm. Lihat REVISI.md.

  "C:/Program Files/KiCad/10.0/bin/python.exe" sensor_revc_outline.py <masuk.kicad_pcb> <keluar.kicad_pcb>

Geometri grup sensor disalin dari `sensor_revb_layout.py` (skrip itu memakai kipy + KiCad yang terbuka).
"""
import math
import sys

import pcbnew

X0, Y0 = 200.0, 54.25
PITCH = 8.0
SEG = [5, 5, 12, 25, 40]
BASE, BASE_C = 5.3, 6.6
LANE = 1.2                        # jarak antar jalur S di pita (rev B 0,7)
TAMBAH = 0.5 + 1.2 + 2.4          # jalur S pertama mundur 0,5 + sisa ke tepi (rev B 1,0) + 2 lajur GND

right = []
x, y = X0 + 4.25, Y0
angs = [0] + SEG
for k in range(6):
    if k > 0:
        a = math.radians(SEG[k - 1])
        x, y = x + PITCH * math.cos(a), y + PITCH * math.sin(a)
    nxt = SEG[k] if k < 5 else SEG[4]
    phi = (angs[k] + nxt) / 2 if k < 5 else SEG[4]
    right.append((x, y, phi))
G = {7 + k: g for k, g in enumerate(right)}


def L(i, lx, ly):
    cx, cy, phi = G[i]
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    return (cx + lx * c - ly * s, cy + lx * s + ly * c)


def base(i):
    return BASE_C if i == 7 else BASE


def separuh():
    """separuh kanan outline: [(titik, jari-jari sudut)], dari tengah depan searah jarum jam sampai tengah belakang"""
    FR = -4.3
    rear = {i: base(i) + (12 - i) * LANE + TAMBAH for i in range(7, 13)}
    pts = [((X0, Y0 - 4.7), 0)]
    rad = {7: 0, 8: 0, 9: 2, 10: 4, 11: 4, 12: 2}
    for i in range(7, 13):
        pts.append((L(i, 0, FR), rad[i]))
    dalam = 6.3 + rear[12] - (BASE + 1.0)          # sisi dalam kait ikut mundur
    pts += [(L(12, 4.6, FR), 1.5), (L(12, 5.6, 4.0), 2), (L(12, 3.0, 13.5), 1), (L(12, -3.5, dalam), 2)]
    rp = [L(i, 0, rear[i]) for i in (11, 10, 9, 8)]
    SX = X0 + 12.5
    keep = []
    for a, b in zip(rp, rp[1:]):
        keep.append(a)
        if (a[0] - SX) * (b[0] - SX) <= 0:
            yj = a[1] + (SX - a[0]) / (b[0] - a[0]) * (b[1] - a[1])
            break
    pts += [(p, 4) for p in keep]
    pts += [((SX, yj), 3), ((SX, 88.0), 3), ((X0 + 9, 88.0), 1.5), ((X0 + 9, 100.5), 0.5), ((X0, 100.5), 0)]
    return pts


def penuh():
    h = separuh()
    cermin = [((2 * X0 - p[0], p[1]), r) for p, r in reversed(h[1:-1])]
    return h + cermin


def gambar(b, pts):
    """poligon tertutup dengan sudut membulat (garis + busur) di Edge.Cuts"""
    n = len(pts)
    sudut = []
    for k in range(n):
        P, r = pts[k]
        A, B = pts[k - 1][0], pts[(k + 1) % n][0]
        u1 = ((A[0] - P[0]) / math.dist(A, P), (A[1] - P[1]) / math.dist(A, P))
        u2 = ((B[0] - P[0]) / math.dist(B, P), (B[1] - P[1]) / math.dist(B, P))
        th = math.acos(max(-1, min(1, u1[0] * u2[0] + u1[1] * u2[1])))
        if r <= 0 or th > math.radians(179):
            sudut.append((P, P, None))
            continue
        t = min(r / math.tan(th / 2), 0.49 * min(math.dist(A, P), math.dist(B, P)))
        r = t * math.tan(th / 2)
        bis = (u1[0] + u2[0], u1[1] + u2[1])
        bl = math.hypot(*bis)
        d = r / math.sin(th / 2)
        c = (P[0] + bis[0] / bl * d, P[1] + bis[1] / bl * d)
        mid = (c[0] - bis[0] / bl * r, c[1] - bis[1] / bl * r)
        sudut.append(((P[0] + u1[0] * t, P[1] + u1[1] * t), (P[0] + u2[0] * t, P[1] + u2[1] * t), mid))

    def v(p):
        return pcbnew.VECTOR2I(pcbnew.FromMM(p[0]), pcbnew.FromMM(p[1]))

    def tambah(bentuk, *p):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(bentuk)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.1))
        if bentuk == pcbnew.SHAPE_T_ARC:
            s.SetArcGeometry(v(p[0]), v(p[1]), v(p[2]))
        else:
            s.SetStart(v(p[0]))
            s.SetEnd(v(p[1]))
        b.Add(s)

    for k in range(n):
        t1, t2, mid = sudut[k]
        if mid:
            tambah(pcbnew.SHAPE_T_ARC, t1, mid, t2)
        nt1 = sudut[(k + 1) % n][0]
        if math.dist(t2, nt1) > 1e-4:
            tambah(pcbnew.SHAPE_T_SEGMENT, t2, nt1)


if __name__ == "__main__":
    b = pcbnew.LoadBoard(sys.argv[1])
    simpan = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    for d in simpan:
        b.Remove(d)
    gambar(b, penuh())
    pcbnew.SaveBoard(sys.argv[2], b)
    bb = b.GetBoardEdgesBoundingBox()
    print("outline rev C", [round(pcbnew.ToMM(q), 2) for q in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())])
