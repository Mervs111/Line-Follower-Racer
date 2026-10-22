"""Rev B PCB sensor: 12 QRE jarak 8 mm di busur jangkar, routing ulang (lewat IPC API KiCad 10).
Dijalankan sekali saat membuat rev B; JANGAN dijalankan ulang ke board yang sudah diedit (menimpa).
Pakai: py -I sensor_revb_layout.py [groups|outline|place|verify|rip|route|silk]
"""
import json
import math
import sys

from kipy import KiCad
from kipy.board_types import Track, Via, BoardLayer
from kipy.geometry import Vector2, Angle
from kipy.util.units import from_mm, to_mm

F, B = BoardLayer.BL_F_Cu, BoardLayer.BL_B_Cu
SIG, PWR = 0.3, 0.5
RO = 2.85
X0, Y0 = 200.0, 54.25
PITCH = 8.0
SEG = [5, 5, 12, 25, 40]          # sudut segmen U7->U8 ... U11->U12
LANE = 0.7                        # jarak antar jalur S di pita
BASE, BASE_C = 5.3, 6.6           # offset jalur S di belakang sensor (biasa / U6-U7)

# --- posisi grup sensor: (cx, cy, phi) phi = sudut matematis (Y ke bawah) ---
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
G = {}
for k, (x, y, phi) in enumerate(right):
    G[7 + k] = (x, y, phi)
    G[6 - k] = (2 * X0 - x, y, -phi)


def L(i, lx, ly):
    cx, cy, phi = G[i]
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    return (cx + lx * c - ly * s, cy + lx * s + ly * c)


def base(i):
    return BASE_C if i in (6, 7) else BASE


# --- U13 / J1 ---
ROW2 = Y0 + BASE_C
ROW1 = ROW2 - 1.27
YU = ROW1 + 6.985
JY = YU + 14.0
LP, RP = X0 - 4.65, X0 + 4.65          # x pad kiri/kanan U13


def row(k):
    return ROW1 + (k - 1) * 1.27


J = {"+5V": X0 + 8.75, "+3V3": X0 + 6.25, "GND": X0 + 3.75, "MUX_S3": X0 + 1.25,
     "MUX_S2": X0 - 1.25, "MUX_S1": X0 - 3.75, "MUX_S0": X0 - 6.25, "MUX_SIG": X0 - 8.75}
VC = {"L_OUT": X0 - 2.6, "L_IN": X0 - 0.9, "R_IN": X0 + 0.9, "R_OUT": X0 + 2.6}
HOP_TOP, HOP_BOT = (X0, Y0 - 3.4), (X0, Y0 + 4.0)
C1_X = RP + 2.55


def placements():
    """ref -> (x, y, sudut KiCad)"""
    p = {}
    for i in range(1, 13):
        _, _, phi = G[i]
        p[f"U{i}"] = (*L(i, 0, 0), 180 - phi)
        p[f"R{2 * i - 1}"] = (*L(i, RO, -1), 90 - phi)   # 220 ohm
        p[f"R{2 * i}"] = (*L(i, -RO, 1), 90 - phi)       # 10k
    p["U13"] = (X0, YU, 0)
    p["J1"] = (J["+5V"], JY, 180)
    p["C1"] = (C1_X, ROW1, 90)
    p["H1"] = (X0 - 4.75, 95.0, 0)
    p["H2"] = (X0 + 4.75, 95.0, 0)
    return p


def expected_pads():
    e = {}
    for i in range(1, 13):
        e[(f"U{i}", "1")] = L(i, 0.9, -2)
        e[(f"U{i}", "2")] = L(i, 0.9, 2)
        e[(f"U{i}", "3")] = L(i, -0.9, 2)
        e[(f"U{i}", "4")] = L(i, -0.9, -2)
        e[(f"R{2 * i - 1}", "1")] = L(i, RO, 0)
        e[(f"R{2 * i - 1}", "2")] = L(i, RO, -2)
        e[(f"R{2 * i}", "1")] = L(i, -RO, 2)
        e[(f"R{2 * i}", "2")] = L(i, -RO, 0)
    e[("U13", "1")] = (LP, row(1))
    e[("U13", "24")] = (RP, row(1))
    e[("U13", "12")] = (LP, row(12))
    e[("U13", "13")] = (RP, row(12))
    e[("C1", "1")] = (C1_X, ROW1 + 1.0375)
    e[("C1", "2")] = (C1_X, ROW1 - 1.0375)
    e[("J1", "1")] = (J["+5V"], JY)
    e[("J1", "8")] = (J["MUX_SIG"], JY)
    return e


# ------------------------------------------------------------------ routing
tracks, vias = [], []


def T(net, layer, w, *pts):
    tracks.append((net, layer, w, list(pts)))


def V(net, p):
    vias.append((net, p))


# start diagonal jalur S kiri (j = 1..5) dan kanan (cermin)
START_L = {1: 194.3, 2: 194.65, 3: 195.0, 4: 195.35, 5: 195.7}


def build():
    for i in range(1, 13):
        s, a = f"S{i}", f"Net-(U{i}-A)"
        T("GND", B, PWR, L(i, -0.9, -2), L(i, -0.9, -0.9), L(i, 0.9, 0.9), L(i, 0.9, 2), L(i, 0.9, 3.9))
        V("GND", L(i, 0.9, 3.9))
        T(a, B, SIG, L(i, 0.9, -2), L(i, RO, -2))
        T("+5V", B, PWR, L(i, RO, 0), L(i, RO, 1.6))
        V("+5V", L(i, RO, 1.6))
        T("+3V3", B, PWR, L(i, -RO, 0), L(i, -RO, -1.6))
        V("+3V3", L(i, -RO, -1.6))
        T(s, B, SIG, L(i, -0.9, 2), L(i, -RO, 2))

    # --- jalur S kiri
    for j in range(1, 7):
        pts = [L(j, -0.9, 2), L(j, -0.9, base(j))]
        if j == 6:
            vx = VC["L_IN"]
            pts += [(vx, ROW2)]
        else:
            for i in range(j + 1, 6):
                pts.append(L(i, -0.9, BASE + (i - j) * LANE))
            lane_y = Y0 + BASE_C + (6 - j) * LANE
            sx = START_L[j]
            wp = L(6, -0.9, BASE_C + (6 - j) * LANE)
            if sx > wp[0] + 0.05:
                pts.append(wp)
            d = (6 - j) * (1.27 - LANE)
            ry = ROW2 + (6 - j) * 1.27
            vx = VC["L_IN"] if j % 2 == 0 else VC["L_OUT"]
            pts += [(sx, lane_y), (sx + d, ry), (vx, ry)]
        T(f"S{j}", B, SIG, *pts)
        V(f"S{j}", pts[-1])
        T(f"S{j}", F, SIG, pts[-1], (LP, pts[-1][1]))

    # --- jalur S kanan (cermin dari kiri)
    for k in range(7, 13):
        pts = [L(k, -0.9, 2), L(k, -0.9, base(k))]
        if k == 7:
            pts += [(VC["R_IN"], ROW2)]
        else:
            for i in range(k - 1, 7, -1):
                pts.append(L(i, -0.9, BASE + (k - i) * LANE))
            m = 13 - k
            lane_y = Y0 + BASE_C + (k - 7) * LANE
            sx = 2 * X0 - START_L[m]
            d = (k - 7) * (1.27 - LANE)
            ry = ROW2 + (k - 7) * 1.27
            vx = VC["R_IN"] if k % 2 == 1 else VC["R_OUT"]
            pts += [(sx, lane_y), (sx - d, ry), (vx, ry)]
        T(f"S{k}", B, SIG, *pts)
        V(f"S{k}", pts[-1])
        T(f"S{k}", F, SIG, pts[-1], (RP, pts[-1][1]))

    # --- rel daya F
    v3 = [L(i, -RO, -1.6) for i in range(1, 13)]
    v5 = [L(i, RO, 1.6) for i in range(1, 13)]
    T("+3V3", F, PWR, *v3)
    T("+5V", F, PWR, *v5)
    a, b = v3[5], v3[6]
    ym = a[1] + (X0 - a[0]) / (b[0] - a[0]) * (b[1] - a[1])
    T("+3V3", F, PWR, (X0, ym), HOP_TOP)
    V("+3V3", HOP_TOP)
    T("+3V3", B, PWR, HOP_TOP, HOP_BOT)
    V("+3V3", HOP_BOT)
    T("+3V3", F, PWR, HOP_BOT, (X0 + (ROW1 - HOP_BOT[1]), ROW1), (RP, ROW1))
    T("+3V3", F, PWR, (RP, ROW1), (C1_X - 1.0375, ROW1), (C1_X, ROW1 + 1.0375))
    T("+3V3", F, PWR, (C1_X, ROW1 + 1.0375), (C1_X, JY - 1 - (C1_X - J["+3V3"])),
      (J["+3V3"], JY - 1), (J["+3V3"], JY))
    p = v5[6]
    cx5 = J["+5V"] + 0.85
    T("+5V", F, PWR, p, (cx5, p[1] + (cx5 - p[0])), (cx5, JY - 1.85), (J["+5V"], JY - 1), (J["+5V"], JY))

    # --- U13 -> J1 (F)
    def to_j(net, *pts, w=SIG):
        jx = J[net]
        c = pts[-1][0]
        T(net, F, w, *pts, (c, JY - 1 - abs(c - jx)), (jx, JY - 1), (jx, JY))
    to_j("MUX_SIG", (LP, row(1)), (LP - 2.85, row(1)))
    to_j("MUX_S0", (LP, row(10)), (LP - 1.85, row(10)))
    to_j("MUX_S1", (LP, row(11)), (LP + 1.75, row(11)))
    to_j("MUX_S2", (RP, row(11)), (RP - 2.55, row(11)))
    to_j("MUX_S3", (RP, row(12)), (RP, row(12) + 0.5))
    T("GND", F, PWR, (LP, row(12)), (LP, row(12) + 1.915))
    V("GND", (LP, row(12) + 1.915))
    T("GND", F, PWR, (RP, row(10)), (RP - 2.05, row(10)))
    V("GND", (RP - 2.05, row(10)))


def vec(p):
    return Vector2.from_xy(from_mm(p[0]), from_mm(p[1]))


def get_board():
    return KiCad(client_name="claude-revb", timeout_ms=30000).get_board()


def place(b):
    pl = placements()
    fps = [fp for fp in b.get_footprints() if fp.reference_field.text.value in pl]
    for fp in fps:
        x, y, a = pl[fp.reference_field.text.value]
        fp.position = vec((x, y))
        fp.orientation = Angle.from_degrees(a)
    c = b.begin_commit()
    b.update_items(fps)
    b.push_commit(c, "Claude: rev B penempatan")
    print("dipindah", len(fps))


def verify(b):
    e = expected_pads()
    worst = 0
    for fp in b.get_footprints():
        ref = fp.reference_field.text.value
        for pd in fp.definition.pads:
            key = (ref, pd.number)
            if key in e:
                ex, ey = e[key]
                d = math.hypot(to_mm(pd.position.x) - ex, to_mm(pd.position.y) - ey)
                worst = max(worst, d)
                if d > 0.01:
                    print("SALAH", key, (round(to_mm(pd.position.x), 3), round(to_mm(pd.position.y), 3)), "harap", (round(ex, 3), round(ey, 3)))
    print("deviasi maks", round(worst, 4))


def rip(b):
    items = list(b.get_tracks()) + list(b.get_vias())
    c = b.begin_commit()
    b.remove_items(items)
    b.push_commit(c, "Claude: bongkar jalur rev A")
    print("dihapus", len(items))


def route(b):
    build()
    nets = {n.name: n for n in b.get_nets()}
    items = []
    for net, layer, w, pts in tracks:
        for p, q in zip(pts, pts[1:]):
            if math.hypot(p[0] - q[0], p[1] - q[1]) < 1e-4:
                continue
            t = Track()
            t.start, t.end = vec(p), vec(q)
            t.layer = layer
            t.width = from_mm(w)
            t.net = nets[net]
            items.append(t)
    for net, p in vias:
        v = Via()
        v.position = vec(p)
        v.net = nets[net]
        v.padstack.drill.diameter = Vector2.from_xy(from_mm(0.6), from_mm(0.6))
        for cl in v.padstack.copper_layers:
            cl.size = Vector2.from_xy(from_mm(1.3), from_mm(1.3))
        items.append(v)
    c = b.begin_commit()
    b.create_items(items)
    b.push_commit(c, "Claude: routing rev B")
    b.refill_zones()
    print("dibuat", len(items), "item")


def outline():
    """Separuh kanan outline (untuk draw_rounded_polygon mirror_x=X0)."""
    FR = -4.3
    rear = {i: base(i) + (12 - i) * LANE + 1.0 for i in range(7, 13)}
    pts = [((X0, Y0 - 4.7), 0)]
    rad = {7: 0, 8: 0, 9: 2, 10: 4, 11: 4, 12: 2}
    for i in range(7, 13):
        pts.append((L(i, 0, FR), rad[i]))
    pts += [(L(12, 4.6, FR), 1.5), (L(12, 5.6, 4.0), 2), (L(12, 3.0, 13.5), 1), (L(12, -3.5, 6.3), 2)]
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
    print(json.dumps([[round(p[0], 3), round(p[1], 3)] for p, _ in pts]))
    print(json.dumps([r for _, r in pts]))


def silk(b):
    pl = {}
    for i in range(1, 13):
        _, _, phi = G[i]
        pl[f"U{i}"] = (L(i, 0, -3.55), -phi)
        pl[f"R{2 * i - 1}"] = (L(i, RO, 4.4), 90 - phi)
        pl[f"R{2 * i}"] = (L(i, -RO, 4.4), 90 - phi)
    fps = [fp for fp in b.get_footprints() if fp.reference_field.text.value in pl]
    for fp in fps:
        p, a = pl[fp.reference_field.text.value]
        t = fp.reference_field.text
        t.position = vec(p)
        t.attributes.size = Vector2.from_xy(from_mm(0.8), from_mm(0.8))
        t.attributes.stroke_width = from_mm(0.2)
        t.attributes.angle = float(a)
    c = b.begin_commit()
    b.update_items(fps)
    b.push_commit(c, "Claude: teks referensi rev B")
    print("teks", len(fps))


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "outline":
        outline()
    elif what == "groups":
        for i in range(1, 13):
            print(i, [round(v, 3) for v in G[i]])
    else:
        b = get_board()
        {"place": place, "verify": verify, "rip": rip, "route": route, "silk": silk}[what](b)
