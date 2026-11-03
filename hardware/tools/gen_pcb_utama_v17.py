"""Layout PCB utama rev B (konsep v17, 03-04/11/2026): outline trapesium, 4 lubang M3, penempatan, silkscreen, pour.

Dijalankan dengan python KiCad (modul pcbnew), bukan py biasa:
  KPY="C:/Program Files/KiCad/10.0/bin/python.exe"
  "$KPY" hardware/tools/gen_pcb_utama_v17.py tata <netlist.net> <board.kicad_pcb>   kosongkan board, isi footprint + net
  "$KPY" hardware/tools/gen_pcb_utama_v17.py ses <board.kicad_pcb> <hasil.ses>     pasang hasil FreeRouting, buang jalur
                                                                                    menggantung, GND pour
  "$KPY" hardware/tools/gen_pcb_utama_v17.py pour|tanpa-pour <board.kicad_pcb>      buat ulang / buang GND pour

Netlist dari `kicad-cli sch export netlist` (format kicadsexpr) skematik rev B. Board yang dipakai sebagai dasar hanya
diambil setup-nya (layer, stackup); semua isi lama dihapus. Path footprint = UUID simbol, jadi F8 (Update PCB from
Schematic) sesudahnya tidak membuat ulang footprint. Routing di antara `tata` dan `ses`: lihat autoroute/README.md
(hasil rev B: hardware/pcb-utama/routing/).

Koordinat robot (mm): x ke kanan, y maju, (0, 0) = tengah poros roda; KiCad X = 200 + x, Y = 180,55 - y.
"""
import math
import re
import sys

import pcbnew

FP_SHARE = "C:/Program Files/KiCad/10.0/share/kicad/footprints"
FP_LTM = __file__.replace("\\", "/").rsplit("/tools/", 1)[0] + "/ltm-lib/ltm.pretty"
_BUANG = []

# ---------------------------------------------------------------- outline (sama dengan konsep v17)
SK_F, SK_R, SK_Y0, SK_Y1 = 31.0, 57.5, -32.0, 93.0           # skid plate: setengah lebar depan/belakang


def sk_x(y):
    return SK_F + (SK_Y1 - y) * (SK_R - SK_F) / (SK_Y1 - SK_Y0)


Y0, Y1, XF = 24.0, 82.0, 31.0                                 # PCB: belakang, depan, setengah lebar depan
TR_D = sk_x(Y1) - XF                                          # jarak tepi miring PCB ke tepi skid plate
XR = sk_x(Y0) - TR_D                                          # setengah lebar belakang (43,3)
R_FIL = 4.0
OUTLINE = [(-XR, Y0), (XR, Y0), (XF, Y1), (-XF, Y1)]
HOLES = [(-38.5, 29.0), (38.5, 29.0), (-32.5, 56.0), (32.5, 56.0)]
ANTENA = (19.0, 26.5, 36.6, 55.7)                             # di bawah antena ESP32: tanpa tembaga (x0, x1, y0, y1)
INTERFACE = (-27.0, 19.0, 43.0, 79.0)                         # board interface 46 x 36 di atas (z 33), gambar bantu

# ---------------------------------------------------------------- penempatan: ref -> (x, y robot titik asal, rotasi)
# titik asal footprint pustaka KiCad = pad 1; footprint ltm = tengah modul
PLACE = {
    # baris belakang (konektor motor, baterai, pembagi tegangan, elko VM)
    "J2": (-31.9, 28.6, 0), "R1": (-15.2, 26.2, 0), "R2": (-15.2, 29.6, 0), "J1": (-1.25, 28.6, 0),
    "C1": (6.7, 28.1, 0), "J3": (19.4, 28.6, 0),
    # saklar di tepi kiri (tuas keluar ke kiri), dekat J1: jalur VBAT semua di sisi kiri
    "SW1": (-37.0, 40.5, -90),
    # tengah: ESP32 melintang di socket (USB kiri, antena kanan). TB6612 di bawahnya: baris kontrol menghadap baris pin
    # belakang ESP32, keluaran motor di depan (AO lewat ujung kiri ke J2, BO lewat lorong kanan x 15-19 ke J3)
    "U1": (-3.5, 46.15, -90), "U2": (-10.75, 46.05, 90),
    "R3": (0.9, 37.9, 0), "R4": (0.9, 41.2, 0), "Q1": (0.9, 45.5, 0), "R5": (0.9, 51.5, 0), "C2": (12.0, 44.0, 90),
    # depan: MP1584, D1, header board interface, buzzer, kabel ke PCB sensor
    "U3": (-18.9, 70.5, 0), "D1": (4.16, 72.0, 180), "J6": (-5.6, 67.5, 90), "BZ1": (20.7, 67.5, 0),
    "J5": (13.0, 77.8, 180),                                  # arah sama dengan J1 PCB sensor (kabel lurus)
}
# pad pemasang SW1 bawaan KiCad (oval 2,2 x 3,5) hanya 0,25 mm dari kaki 1/3 dan < 0,5 mm dari tepi miring:
# dikecilkan di board ini (lubang 1,5 tetap, cincin 0,25). Jangan "Update Footprints from Library" untuk SW1.
PAD_FIX = {"SW1": {"": (2.0, 3.3)}}
# boleh menumpuk dengan U1 (ESP32 di socket 8,5 mm): komponen rendah di bawahnya
UNDER_U1 = {"U2", "R3", "R4", "Q1", "R5", "C2"}

# label konektor ditulis di dalam badan JST XH (antara garis dalam dan pad): terbaca saat merakit, tertutup sesudahnya.
# Celah antara konektor belakang dan baris pin ESP32 cuma ±1,2 mm, jadi tidak ada tempat untuk teks di luar badan.
SILK = [  # (teks, x, y, ukuran, rotasi)
    ("J2 MOTOR KIRI", -25.65, 26.75, 0.8, 0), ("J1 BAT", 0.0, 26.75, 0.8, 0), ("J3 MOTOR KANAN", 25.65, 26.75, 0.8, 0),
    ("J5 KE SENSOR", 4.25, 79.7, 0.8, 0), ("J6 KE INTERFACE", 0.75, 64.3, 0.9, 0), ("POWER", -33.0, 46.0, 1.0, 0),
]
SILK_B = [("LTM PCB utama rev B", 4.0, 63.4, 1.2), ("P01 Kel.5 PjBL 2026", 4.0, 61.5, 0.9)]   # sisi bawah (dicermin)
REF_FAB = {"J1", "J2", "J3", "J5", "J6"}                       # referensi sudah ada di label SILK
REF_TENGAH = {"R1", "R2", "R3", "R4", "R5", "C2"}             # referensi di tengah badan (antara dua pad)
REF_AT = {"C1": (13.3, 28.1)}


def K(x, y):
    """koordinat robot -> VECTOR2I KiCad"""
    return pcbnew.VECTOR2I(pcbnew.FromMM(200.0 + x), pcbnew.FromMM(180.55 - y))


def R(v):
    return pcbnew.ToMM(v.x) - 200.0, 180.55 - pcbnew.ToMM(v.y)


def fillet(poly, r):
    """poligon cembung -> daftar ('seg', a, b) / ('arc', a, mid, b), sudut dibulatkan radius r"""
    n, corners = len(poly), []
    for i in range(n):
        c, a, b = poly[i], poly[i - 1], poly[(i + 1) % n]
        u1 = [a[0] - c[0], a[1] - c[1]]; l1 = math.hypot(*u1); u1 = [u1[0] / l1, u1[1] / l1]
        u2 = [b[0] - c[0], b[1] - c[1]]; l2 = math.hypot(*u2); u2 = [u2[0] / l2, u2[1] / l2]
        half = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))) / 2
        t = r / math.tan(half)
        bis = [u1[0] + u2[0], u1[1] + u2[1]]; lb = math.hypot(*bis); bis = [bis[0] / lb, bis[1] / lb]
        ctr = (c[0] + bis[0] * r / math.sin(half), c[1] + bis[1] * r / math.sin(half))
        mid = (ctr[0] - bis[0] * r, ctr[1] - bis[1] * r)
        corners.append(((c[0] + u1[0] * t, c[1] + u1[1] * t), mid, (c[0] + u2[0] * t, c[1] + u2[1] * t)))
    out = []
    for i in range(n):
        t1, mid, t2 = corners[i]
        out.append(("arc", t1, mid, t2))
        out.append(("seg", t2, corners[(i + 1) % n][0]))
    return out


def dense(shape, step=0.5):
    """outline -> titik rapat (untuk cek komponen di dalam papan)"""
    pts = []
    for s in shape:
        if s[0] == "seg":
            pts.append(s[1])
        else:
            a, m, b = s[1], s[2], s[3]
            # pusat lingkaran dari 3 titik
            ax, ay, bx, by, cx, cy = a[0], a[1], m[0], m[1], b[0], b[1]
            d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
            ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
            uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
            r = math.hypot(ax - ux, ay - uy)
            t0, t1 = math.atan2(ay - uy, ax - ux), math.atan2(cy - uy, cx - ux)
            tm = math.atan2(by - uy, bx - ux)
            # arah putar yang melewati titik tengah
            def between(t, s, e):
                return (t - s) % (2 * math.pi) < (e - s) % (2 * math.pi)
            if not between(tm, t0, t1):
                t0, t1 = t1, t0
            span = (t1 - t0) % (2 * math.pi)
            k = max(2, int(span * r / step))
            seq = [(ux + r * math.cos(t0 + span * i / k), uy + r * math.sin(t0 + span * i / k)) for i in range(k + 1)]
            if math.hypot(seq[0][0] - a[0], seq[0][1] - a[1]) > 1e-6:
                seq.reverse()
            pts += seq
    return pts


def inside_margin(pt, poly):
    """jarak bertanda titik ke tepi poligon (+ = di dalam)"""
    x, y = pt
    ins, dmin = False, 1e9
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i - 1], poly[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ins = not ins
        dx, dy = x2 - x1, y2 - y1
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy or 1)))
        dmin = min(dmin, math.hypot(x - x1 - t * dx, y - y1 - t * dy))
    return dmin if ins else -dmin


# ---------------------------------------------------------------- netlist kicadsexpr
def sexpr(text):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack = [[]]
    for t in toks:
        if t == "(":
            stack.append([])
        elif t == ")":
            last = stack.pop()
            stack[-1].append(last)
        else:
            stack[-1].append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return stack[0][0]


def find(node, key):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == key]


def val(node, key):
    f = find(node, key)
    return f[0][1] if f and len(f[0]) > 1 else None


def read_netlist(path):
    root = sexpr(open(path, encoding="utf-8").read())
    comps = {}
    for c in find(find(root, "components")[0], "comp"):
        comps[val(c, "ref")] = dict(value=val(c, "value"), fp=val(c, "footprint"), uuid=val(c, "tstamps"),
                                    datasheet=val(c, "datasheet"))
    nets = {}
    for n in find(find(root, "nets")[0], "net"):
        name = val(n, "name")
        for nd in find(n, "node"):
            nets[(val(nd, "ref"), val(nd, "pin"))] = name
    return comps, nets


# ---------------------------------------------------------------- langkah 1: tata letak
def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(FP_LTM if lib == "ltm" else f"{FP_SHARE}/{lib}.pretty", name)
    if fp is None:
        raise SystemExit(f"footprint tidak ketemu: {fpid}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def crtyd_box(fp):
    """kotak courtyard footprint dalam koordinat robot (x0, x1, y0, y1)"""
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            b = g.GetBoundingBox()
            for v in (b.GetOrigin(), b.GetEnd()):
                x, y = R(v); xs.append(x); ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)


def add_shape(b, layer, kind, pts, width=0.1):
    s = pcbnew.PCB_SHAPE(b)
    if kind == "arc":
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(K(*pts[0]), K(*pts[1]), K(*pts[2]))
    else:
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(K(*pts[0])); s.SetEnd(K(*pts[1]))
    s.SetLayer(layer)
    s.SetWidth(pcbnew.FromMM(width))
    b.Add(s)


def add_text(b, layer, txt, x, y, size, rot=0, thick=0.15, mirror=False):
    t = pcbnew.PCB_TEXT(b)
    t.SetMirrored(mirror)                                   # teks sisi bawah dicermin supaya terbaca dari bawah
    t.SetText(txt)
    t.SetPosition(K(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
    t.SetTextThickness(pcbnew.FromMM(thick))
    t.SetTextAngleDegrees(rot)
    b.Add(t)


def zone_poly(z, pts):
    ol = z.Outline()
    ol.NewOutline()
    for p in pts:
        ol.Append(K(*p))


def tata(netfile, brd):
    comps, nets = read_netlist(netfile)
    # footprint dimuat sebelum LoadBoard: di KiCad 10 FootprintLoad gagal (objek SWIG mentah) sesudah board dimuat
    loaded = {ref: load_fp(c["fp"]) for ref, c in comps.items()}
    holes = [load_fp("MountingHole:MountingHole_3.2mm_M3") for _ in HOLES]
    b = pcbnew.LoadBoard(brd)
    # referensi item yang dibuang disimpan: kalau ikut dibersihkan GC Python, wrapper SWIG KiCad 10 rusak
    _BUANG.extend(list(b.GetFootprints()) + list(b.GetTracks()) + list(b.Zones()) + list(b.GetDrawings()))
    for it in _BUANG:
        b.Remove(it)
    # KiCad 10 menyimpan nama net di tiap item (tanpa daftar net global): net lama ikut hilang bersama itemnya

    shape = fillet(OUTLINE, R_FIL)
    for s in shape:
        add_shape(b, pcbnew.Edge_Cuts, s[0], s[1:])
    edge = dense(shape)

    netobj = {}

    def net(name):
        if name not in netobj:
            n = pcbnew.NETINFO_ITEM(b, name)
            b.Add(n)
            netobj[name] = n
        return netobj[name]

    missing = sorted(set(comps) - set(PLACE))
    if missing:
        raise SystemExit(f"belum punya posisi: {missing}")
    boxes = {}
    for ref, c in sorted(comps.items()):
        fp = loaded[ref]
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        if c.get("datasheet") and c["datasheet"] != "~":
            fp.SetField("Datasheet", c["datasheet"])
        fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        x, y, rot = PLACE[ref]
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(K(x, y))
        ref_txt = fp.Reference()
        if ref in REF_FAB:
            ref_txt.SetLayer(pcbnew.F_Fab)
        elif ref in REF_TENGAH:
            ps = [p.GetPosition() for p in fp.Pads()]
            ref_txt.SetPosition(pcbnew.VECTOR2I((ps[0].x + ps[1].x) // 2, (ps[0].y + ps[1].y) // 2))
            ref_txt.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
            ref_txt.SetTextThickness(pcbnew.FromMM(0.12))
        elif ref in REF_AT:
            ref_txt.SetPosition(K(*REF_AT[ref]))
        if ref == "SW1":                                   # garis silk saklar keluar tepi papan (tuasnya menonjol)
            for g in fp.GraphicalItems():
                if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() != "PCB_FIELD":
                    g.SetLayer(pcbnew.F_Fab)
        b.Add(fp)
        for p in fp.Pads():
            if p.GetNumber() in PAD_FIX.get(ref, {}):
                w, h = PAD_FIX[ref][p.GetNumber()]
                p.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(pcbnew.FromMM(w), pcbnew.FromMM(h)))
            name = nets.get((ref, p.GetNumber()))
            if name:
                p.SetNet(net(name))
        boxes[ref] = crtyd_box(fp)
    for i, (x, y) in enumerate(HOLES, 1):
        fp = holes[i - 1]
        fp.SetReference(f"H{i}")
        fp.SetValue("M3")
        fp.SetPosition(K(x, y))
        fp.Reference().SetLayer(pcbnew.F_Fab)
        fp.SetBoardOnly(True)
        b.Add(fp)
        boxes[f"H{i}"] = crtyd_box(fp)

    # tanpa tembaga di bawah antena ESP32 (jalur, via, pour)
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetZoneName("Antena ESP32")
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    (z.SetDoNotAllowZoneFills if hasattr(z, "SetDoNotAllowZoneFills") else z.SetDoNotAllowCopperPour)(True)
    x0, x1, y0, y1 = ANTENA
    zone_poly(z, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    b.Add(z)

    for txt, x, y, size, rot in SILK:
        add_text(b, pcbnew.F_SilkS, txt, x, y, size, rot)
    for txt, x, y, size in SILK_B:
        add_text(b, pcbnew.B_SilkS, txt, x, y, size, mirror=True)
    x0, x1, y0, y1 = INTERFACE
    for a, c in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        add_shape(b, pcbnew.Dwgs_User, "seg", (a, c), 0.15)
    add_text(b, pcbnew.Dwgs_User, "board interface (z 33)", (x0 + x1) / 2, y1 - 2, 1.2)

    # cek: courtyard di dalam papan, tidak saling tumpuk (kecuali yang memang di bawah ESP32)
    bad = 0
    for ref, (bx0, bx1, by0, by1) in sorted(boxes.items()):
        if ref == "BZ1" or ref.startswith("H"):            # courtyard bulat: cek dari titik tengah
            r = (bx1 - bx0) / 2
            m = inside_margin(((bx0 + bx1) / 2, (by0 + by1) / 2), edge) - (2.9 if ref.startswith("H") else r)
        else:                                              # (lubang: kepala baut M3 r 2,75 + 0,15 harus di papan)
            m = min(inside_margin(p, edge) for p in ((bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)))
        if m < 0.2 and ref != "SW1":                       # tuas SW1 memang menonjol keluar tepi
            print(f"  KELUAR TEPI {ref}: {m:.2f} mm"); bad += 1
    refs = sorted(boxes)
    for i, a in enumerate(refs):
        for c in refs[i + 1:]:
            if {a, c} & {"U1"} and {a, c} - {"U1"} <= UNDER_U1:
                continue
            A, C = boxes[a], boxes[c]
            if min(A[1], C[1]) - max(A[0], C[0]) > 0.01 and min(A[3], C[3]) - max(A[2], C[2]) > 0.01:
                print(f"  TUMPUK {a} x {c}"); bad += 1
    pcbnew.SaveBoard(brd, b)
    print(f"{len(comps)} komponen + {len(HOLES)} lubang, {len(netobj)} net, outline {2 * XR:.1f}/{2 * XF:.1f} x "
          f"{Y1 - Y0:.0f} mm, masalah penempatan: {bad}")


# ---------------------------------------------------------------- langkah 2: hasil routing + GND pour
def ses(brd, sesfile):
    b = pcbnew.LoadBoard(brd)
    _BUANG.extend(list(b.GetTracks()) + [z for z in b.Zones() if not z.GetIsRuleArea()])
    for it in _BUANG:
        b.Remove(it)
    if not pcbnew.ImportSpecctraSES(b, sesfile):
        raise SystemExit("impor SES gagal")
    rapikan(b)
    pour(b, brd)


def jarak_ke_segmen(p, a, c):
    """jarak titik p ke segmen a-c (satuan internal KiCad, nm)"""
    dx, dy = c.x - a.x, c.y - a.y
    u = max(0.0, min(1.0, ((p.x - a.x) * dx + (p.y - a.y) * dy) / float(dx * dx + dy * dy or 1)))
    return math.hypot(p.x - a.x - u * dx, p.y - a.y - u * dy)


def rapikan(b):
    """buang jalur yang ujungnya menggantung dan via tanpa jalur (sisa FreeRouting), berulang sampai habis"""
    n = 0
    while True:
        pads, tracks = list(b.GetPads()), list(b.GetTracks())
        uid = lambda it: it.m_Uuid.AsString()                # noqa: E731

        def nyambung(pt, layer, me):
            for p in pads:
                if p.GetNetCode() == me.GetNetCode() and p.IsOnLayer(layer) and p.HitTest(pt):
                    return True
            for o in tracks:
                if uid(o) == uid(me) or o.GetNetCode() != me.GetNetCode():
                    continue
                if o.GetClass() == "PCB_VIA" or o.GetLayer() == layer:
                    if o.HitTest(pt):
                        return True
            return False

        buang, seen = [], set()
        for tr in tracks:                                    # segmen kembar (ujung sama, bolak-balik) dibuang satu
            if tr.GetClass() != "PCB_VIA":
                s, e = (tr.GetStart().x, tr.GetStart().y), (tr.GetEnd().x, tr.GetEnd().y)
                key = (tr.GetLayer(), tr.GetNetCode(), min(s, e), max(s, e))
                if key in seen:
                    buang.append(tr)
                seen.add(key)
        segs = [o for o in tracks if o.GetClass() != "PCB_VIA" and uid(o) not in {uid(x) for x in buang}]
        for tr in segs:                                      # segmen yang seluruhnya menumpuk di segmen lain
            for o in segs:
                if uid(o) != uid(tr) and o.GetLayer() == tr.GetLayer() and o.GetNetCode() == tr.GetNetCode()                         and o.GetLength() > tr.GetLength()                         and all(jarak_ke_segmen(p, o.GetStart(), o.GetEnd()) < 1000 for p in (tr.GetStart(), tr.GetEnd())):
                    buang.append(tr)
                    break
        if buang:
            tracks = [o for o in tracks if uid(o) not in {uid(x) for x in buang}]
        for tr in tracks:
            if tr.GetClass() == "PCB_VIA":
                if not any(o.GetClass() != "PCB_VIA" and o.GetNetCode() == tr.GetNetCode()
                           and (tr.HitTest(o.GetStart()) or tr.HitTest(o.GetEnd())) for o in tracks):
                    buang.append(tr)
            elif not (nyambung(tr.GetStart(), tr.GetLayer(), tr) and nyambung(tr.GetEnd(), tr.GetLayer(), tr)):
                buang.append(tr)
        if not buang:
            break
        _BUANG.extend(buang)
        for tr in buang:
            b.Remove(tr)
        n += len(buang)
    print(f"dibuang {n} jalur/via menggantung")


def pour(b, brd):
    """GND pour F.Cu + B.Cu menutupi papan (dipotong outline), isi, simpan"""
    old = [z for z in b.Zones() if not z.GetIsRuleArea()]
    _BUANG.extend(old)
    for z in old:
        b.Remove(z)
    gnd = b.FindNet("GND")
    pts = dense(fillet(OUTLINE, R_FIL))
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b)
        z.SetLayer(lay)
        z.SetNet(gnd)
        z.SetZoneName("GND")
        z.SetLocalClearance(pcbnew.FromMM(0.5))
        z.SetMinThickness(pcbnew.FromMM(0.35))            # 0,3 menyisakan leher pour 0,13 mm (warning DRC)
        z.SetThermalReliefGap(pcbnew.FromMM(0.5))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.5))
        zone_poly(z, [(-50, 20), (50, 20), (50, 86), (-50, 86)])
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(brd, b)
    n_tr = sum(1 for t in b.GetTracks() if t.GetClass() != "PCB_VIA")
    n_via = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
    print(f"{n_tr} segmen, {n_via} via, GND pour F.Cu + B.Cu, {len(pts)} titik outline")


if __name__ == "__main__":
    if sys.argv[1] == "pour":                      # pour <board>: buat ulang GND pour (mis. sesudah autoroute/sisa.py)
        pour(pcbnew.LoadBoard(sys.argv[2]), sys.argv[2])
    elif sys.argv[1] == "tanpa-pour":              # tanpa-pour <board>: buang GND pour sebelum autoroute/sisa.py
        bb = pcbnew.LoadBoard(sys.argv[2])
        old = [z for z in bb.Zones() if not z.GetIsRuleArea()]
        _BUANG.extend(old)
        for z in old:
            bb.Remove(z)
        pcbnew.SaveBoard(sys.argv[2], bb)
    elif sys.argv[1] == "tata":
        tata(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "ses":
        ses(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
