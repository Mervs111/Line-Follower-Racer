"""Routing papan utama LFM X2 tanpa FreeRouting (FreeRouting 2.1 macet di papan ini: >50 sambungan tidak selesai dan
batas pass di freerouting.json diabaikan). Bagian KiCad (python KiCad, modul pcbnew); pencarian jalurnya di
x2_cari.py (python sistem: numpy + scikit-image).

  "$KPY" x2_router.py fanout <board>                    jalur tetap USB-C J2 (lihat fanout_usb)
  "$KPY" x2_router.py ekspor <board> <drc.json> <out.json> [net dilewati] [--ganti <sambungan.json>]
                                                        rintangan + pasangan "unconnected" dari laporan DRC
  py     x2_cari.py <out.json> <jalur.json>             cari jalur (python sistem)
  "$KPY" x2_router.py pasang <board> <jalur.json>       tulis jalur + via ke board
  "$KPY" x2_router.py pour <board>                      GND pour F.Cu + B.Cu (jarak 0,5 mm), isi, simpan
  "$KPY" x2_router.py jahit <board>                     via jahit GND penyambung pulau pour atas-bawah
  "$KPY" x2_router.py gnd <board> <out.json> [tepi]     kelompok GND yang masih terpisah -> sambungan x2_cari
Urutan lengkap ada di README.md folder ini.
"""
import json
import math
import os
import sys

import pcbnew

VIA_D, VIA_DRILL = 1.3, 0.7     # bor 0,7: lubang minimal SPECTRA pcb (17/11)
W_MIN = float(os.environ.get("W_MIN", "0.3"))         # lebar jalur minimum (X1 aturan 20/11: 0,5)
POUR_CLR = float(os.environ.get("POUR_CLR", "0.5"))   # jarak pour GND ke net lain (X1: 0,7)
_SIMPAN = []                              # referensi objek SWIG yang dibuang (lihat gen_pcb_utama_v17.py)


def mm(v):
    return round(pcbnew.ToMM(v), 4)


def lapis(it):
    return ("F" if it.IsOnLayer(pcbnew.F_Cu) else "") + ("B" if it.IsOnLayer(pcbnew.B_Cu) else "")


def kotak(it):
    bx = it.GetBoundingBox()
    return [mm(bx.GetLeft()), mm(bx.GetTop()), mm(bx.GetRight()), mm(bx.GetBottom())]


def data_pad(p):
    c = p.GetPosition()
    if p.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
        return "circ", [mm(c.x), mm(c.y), mm(p.GetSize(pcbnew.F_Cu).x) / 2]
    return "rect", kotak(p)


def data_jalur(t):
    if t.GetClass() == "PCB_VIA":
        c = t.GetPosition()
        return [t.GetNetname(), "FB", "circ", [mm(c.x), mm(c.y), mm(t.GetWidth(pcbnew.F_Cu)) / 2]]
    s, e = t.GetStart(), t.GetEnd()
    return [t.GetNetname(), "F" if t.GetLayer() == pcbnew.F_Cu else "B", "seg",
            [[mm(s.x), mm(s.y)], [mm(e.x), mm(e.y)], mm(t.GetWidth()) / 2]]


def pulau(b, it):
    """semua jalur + via satu net yang tersambung ke `it` lewat titik ujung (mis. seluruh jalur fanout J2)"""
    net = it.GetNetname()
    semua = [t for t in b.GetTracks() if t.GetNetname() == net]
    def titik(t):
        if t.GetClass() == "PCB_VIA":
            return [t.GetPosition()]
        return [t.GetStart(), t.GetEnd()]
    hasil, baru = {it.m_Uuid.AsString(): it}, [it]
    while baru:
        tp = [p for t in baru for p in titik(t)]
        baru = [t for t in semua if t.m_Uuid.AsString() not in hasil and
                any((q - p).EuclideanNorm() < 1000 for q in titik(t) for p in tp)]
        hasil.update((t.m_Uuid.AsString(), t) for t in baru)
    return list(hasil.values())


def ujung(b, it):
    """item ujung sambungan: pad, atau pulau jalur/via (sel awal mencakup seluruh pulau). Pad yang sudah punya jalur
    tetap dari net yang sama (fanout) diganti pulau jalur itu: DRC sering melaporkan pad-nya, padahal pad deret kaki
    ESP32 terkurung (kiri modul, kanan-kiri pad lain) dan hanya bisa dicapai lewat via fanout-nya."""
    if isinstance(it, pcbnew.PAD):
        nempel = [t for t in b.GetTracks() if t.GetNetname() == it.GetNetname() and t.GetClass() != "PCB_VIA"
                  and (it.HitTest(t.GetStart()) or it.HitTest(t.GetEnd()))]
        if not nempel:
            c = it.GetPosition()
            return {"jenis": "pad", "lay": lapis(it), "box": kotak(it), "anchor": [mm(c.x), mm(c.y)]}
        it = nempel[0]
    segs, vias = [], []
    for t in pulau(b, it):
        n, lay, kind, data = data_jalur(t)
        (vias if kind == "circ" else segs).append([lay] + data)
    return {"jenis": "pulau", "segs": segs, "vias": vias, "anchor": None}


def dasar(b, byid):
    """pad, lubang, jalur, rule area, outline papan untuk x2_cari"""
    items = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            byid[p.m_Uuid.AsString()] = p
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                c = p.GetPosition()
                items.append(["#lubang", "FB", "circ", [mm(c.x), mm(c.y), mm(p.GetDrillSize().x) / 2], False])
                continue
            kind, data = data_pad(p)
            items.append([p.GetNetname(), lapis(p), kind, data, p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD])
    jalur = []
    for t in b.GetTracks():
        byid[t.m_Uuid.AsString()] = t
        jalur.append(data_jalur(t))
    area = []
    for z in b.Zones():
        if z.GetIsRuleArea():
            area.append([lapis(z), kotak(z), z.GetDoNotAllowTracks(), z.GetDoNotAllowVias()])
    ps = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(ps, False)
    ol = ps.Outline(0)
    outline = [[mm(ol.CPoint(i).x), mm(ol.CPoint(i).y)] for i in range(ol.PointCount())]
    return {"outline": outline, "items": items, "jalur": jalur, "area": area}


def item_di(b, net, xy):
    """pad, jalur, atau via net `net` di titik `xy` (mm KiCad)"""
    p = pcbnew.VECTOR2I(pcbnew.FromMM(xy[0]), pcbnew.FromMM(xy[1]))
    for fp in b.GetFootprints():
        for q in fp.Pads():
            if q.GetNetname() == net and q.HitTest(p):
                return q
    for t in b.GetTracks():
        if t.GetNetname() == net and t.HitTest(p):
            return t
    raise SystemExit(f"tidak ada item {net} di {xy}")


def kena(u, xy, tol=0.3):
    """titik `xy` ada di ujung sambungan `u` (pad: di dalam kotaknya; pulau: dekat titik jalur/via)"""
    x, y = xy
    if u["jenis"] == "pad":
        x0, y0, x1, y1 = u["box"]
        return x0 - tol <= x <= x1 + tol and y0 - tol <= y <= y1 + tol
    pts = [q for s in u["segs"] for q in s[1:3]] + [v[1:3] for v in u["vias"]]
    return any(math.hypot(q[0] - x, q[1] - y) <= tol for q in pts)


def ganti_sambungan(b, pasang, file):
    """ganti sambungan ratsnest yang pasti bersilang (mis. ujungnya terkurung jalur tetap) dengan pasangan lain yang
    menyambung kelompok yang sama. Isi file: {"ganti": [{"net", "dari": [p, q], "ke": [p, q]}]}, mm KiCad."""
    for g in json.load(open(file, encoding="utf8"))["ganti"]:
        cocok = [k for k, s in enumerate(pasang) if s["net"] == g["net"] and
                 ((kena(s["A"], g["dari"][0]) and kena(s["B"], g["dari"][1])) or
                  (kena(s["A"], g["dari"][1]) and kena(s["B"], g["dari"][0])))]
        if len(cocok) != 1:
            raise SystemExit(f"ganti {g['net']} {g['dari']}: {len(cocok)} sambungan cocok")
        A, B = (item_di(b, g["net"], xy) for xy in g["ke"])
        (xa, ya), (xb, yb) = g["ke"]
        pasang[cocok[0]] = {"net": g["net"], "A": ujung(b, A), "B": ujung(b, B), "jarak": math.hypot(xa - xb, ya - yb)}
        print(f"  sambungan {g['net']} {g['dari']} -> {g['ke']}")


def ekspor(brd, drcfile, out, skip=()):
    skip = list(skip)
    ganti = skip.pop(skip.index("--ganti") + 1) if "--ganti" in skip else None
    skip = [n for n in skip if n != "--ganti"]
    b = pcbnew.LoadBoard(brd)
    rep = json.load(open(drcfile, encoding="utf-8"))
    byid = {}
    d = dasar(b, byid)
    pasang = []
    for u in rep.get("unconnected_items", []):
        A, B = (byid.get(i["uuid"]) for i in u["items"])
        if A is None or B is None:
            print("  item tidak ketemu:", [i["description"] for i in u["items"]])
            continue
        if A.GetNetname() in skip:
            continue
        pa, pb = A.GetPosition(), B.GetPosition()
        pasang.append({"net": A.GetNetname(), "A": ujung(b, A), "B": ujung(b, B),
                       "jarak": math.hypot(mm(pa.x) - mm(pb.x), mm(pa.y) - mm(pb.y))})
    if ganti:
        ganti_sambungan(b, pasang, ganti)
    d["pasang"] = pasang
    json.dump(d, open(out, "w", encoding="utf8"))
    print(f"{len(d['items'])} pad/lubang, {len(d['jalur'])} jalur, {len(d['area'])} rule area, {len(pasang)} sambungan")


def tambah_jalur(b, net, L, a, c, w):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(c[0]), pcbnew.FromMM(c[1])))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(pcbnew.F_Cu if L == "F" else pcbnew.B_Cu)
    t.SetNet(b.FindNet(net))
    b.Add(t)


def tambah_via(b, net, x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.F_Cu, pcbnew.FromMM(VIA_D))
    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
    v.SetNet(b.FindNet(net))
    b.Add(v)


def fanout_usb(brd):
    """Jalur tetap di depan pad USB-C J2 (pad 0,3 mm jarak 0,5 mm; ujung pad di x0, pad menghadap -x).
    Pasangan D+ (A6, B6) dan D- (A7, B7) bersilang, jadi tidak bisa disambung di satu sisi tanpa saling mengurung,
    dan via 1,3 mm tidak muat di antara pad: D+ disambung di belakang pad (di bawah badan konektor, tertutup solder
    mask), D- disambung bentuk C di depan ujung pad A6. VBUS (A4/B9 dan A9/B4) turun lewat 2 via dan disambung di
    sisi bawah. D+ dan CC1 dibelokkan ke arah pad SBU yang tidak tersambung. Celah 0,2 mm hanya di 0,2 mm pertama
    dari ujung pad (sama dengan celah antar pad konektor, aturan usb_c_* di .kicad_dru); sesudahnya >= 0,3 mm."""
    b = pcbnew.LoadBoard(brd)
    fp = b.FindFootprintByReference("J2")
    pad = {p.GetNumber(): p for p in fp.Pads() if p.GetNumber()[:1] in ("A", "B")}
    x0 = mm(pad["A6"].GetBoundingBox().GetLeft())             # ujung pad (sisi dalam papan)
    xb = mm(pad["A6"].GetBoundingBox().GetRight())            # pangkal pad (di bawah badan konektor)
    xc = mm(pad["A6"].GetPosition().x)
    y = {n: mm(p.GetPosition().y) for n, p in pad.items()}
    s = 1 if y["A9"] < y["A4"] else -1                         # urutan pad A9 ... A4 searah +y (s = 1)
    xe = x0 - 1.43                                             # ujung jalur tetap, diteruskan x2_cari.py
    j = []                                                     # (net, layer, a, b, lebar)
    # D+: A6 - B6 di belakang pad, keluar dari B6 lalu menjauhi D- (ke arah pad SBU A8 yang kosong)
    xr = xb + 0.47
    j += [("USB_DP", "F", (xc, y["A6"]), (xr, y["A6"]), 0.3), ("USB_DP", "F", (xr, y["A6"]), (xr, y["B6"]), 0.3),
          ("USB_DP", "F", (xr, y["B6"]), (xc, y["B6"]), 0.3),
          ("USB_DP", "F", (xc, y["B6"]), (x0 - 0.2, y["B6"]), 0.3),
          ("USB_DP", "F", (x0 - 0.2, y["B6"]), (x0 - 0.6, y["B6"] - 0.4 * s), 0.3),
          ("USB_DP", "F", (x0 - 0.6, y["B6"] - 0.4 * s), (xe, y["B6"] - 0.4 * s), 0.3)]
    # D-: A7 dan B7 bertemu di depan ujung pad A6
    xm = x0 - 0.63
    j += [("USB_DM", "F", (xc, y["A7"]), (xm, y["A7"]), 0.3), ("USB_DM", "F", (xc, y["B7"]), (xm, y["B7"]), 0.3),
          ("USB_DM", "F", (xm, y["A7"]), (xm, y["B7"]), 0.3), ("USB_DM", "F", (xm, y["A6"]), (xe, y["A6"]), 0.3)]
    # CC2 lurus, CC1 dibelokkan menjauhi D- (ke arah pad SBU B8 yang kosong)
    j += [("CC2", "F", (xc, y["B5"]), (xe, y["B5"]), 0.3)]
    j += [("CC1", "F", (xc, y["A5"]), (x0 - 0.2, y["A5"]), 0.3),
          ("CC1", "F", (x0 - 0.2, y["A5"]), (x0 - 0.5, y["A5"] + 0.3 * s), 0.3),
          ("CC1", "F", (x0 - 0.5, y["A5"] + 0.3 * s), (xe, y["A5"] + 0.3 * s), 0.3)]
    # VBUS: kedua pad lewat via menjauhi pad, disambung di sisi bawah
    xv = x0 - 1.28
    va, vb = (xv, y["A9"] - 0.8 * s), (xv, y["A4"] + 0.7 * s)
    j += [("VBUS", "F", (xc, y["A9"]), (xv + 0.8, y["A9"]), 0.5), ("VBUS", "F", (xv + 0.8, y["A9"]), va, 0.5),
          ("VBUS", "F", (xc, y["A4"]), (xv + 0.7, y["A4"]), 0.5), ("VBUS", "F", (xv + 0.7, y["A4"]), vb, 0.5),
          ("VBUS", "B", va, vb, 0.5)]
    for net, L, a, c, w in j:
        tambah_jalur(b, net, L, a, c, w)
    tambah_via(b, "VBUS", *va)
    tambah_via(b, "VBUS", *vb)
    pcbnew.SaveBoard(brd, b)
    print(f"fanout J2: {len(j)} segmen, 2 via (ujung pad x {x0}, via x {xv})")


def pasang(brd, jfile):
    b = pcbnew.LoadBoard(brd)
    d = json.load(open(jfile, encoding="utf8"))
    for net, L, x1, y1, x2, y2, w in d["tracks"]:
        tambah_jalur(b, net, L, (x1, y1), (x2, y2), w)
    ada = [(t.GetNetname(), mm(t.GetPosition().x), mm(t.GetPosition().y))
           for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    tht = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                bb = p.GetBoundingBox()
                tht.append((p.GetNetname(), mm(p.GetPosition().x), mm(p.GetPosition().y),
                            mm(min(bb.GetWidth(), bb.GetHeight())) / 2 - 0.1))
    nvia = 0
    for net, x, y in d["vias"]:
        # via di dalam pad THT satu net tidak perlu (pad sudah menyambung kedua sisi) dan lubangnya bertumpuk
        if any(n == net and math.hypot(px - x, py - y) < r for n, px, py, r in tht):
            continue
        # dua sambungan satu net bisa memilih titik via yang sama atau berdempetan: via kedua tidak dipasang, ujung
        # jalurnya disambung dengan jalur pendek di kedua sisi. Batas 1,0 mm: lubang 0,6 mm yang lebih dekat dari ini
        # berjarak < 0,4 mm (peringatan hole_to_hole, 16/11 di papan sensor 0,7 mm)
        dekat = [(vx, vy) for n, vx, vy in ada if n == net and math.hypot(vx - x, vy - y) < 1.0]
        if dekat:
            vx, vy = dekat[0]
            if math.hypot(vx - x, vy - y) > 0.01:
                for L in ("F", "B"):
                    tambah_jalur(b, net, L, (x, y), (vx, vy), W_MIN)
            continue
        ada.append((net, x, y))
        tambah_via(b, net, x, y)
        nvia += 1
    pcbnew.SaveBoard(brd, b)
    print(f"dipasang {len(d['tracks'])} segmen, {nvia} via")


def pour(brd):
    """GND pour F.Cu + B.Cu menutupi papan (dipotong outline), isi, simpan. Pad SMD menempel penuh (jari-jari thermal
    sering terpotong jalur di papan padat), pad THT pakai thermal relief supaya mudah disolder."""
    b = pcbnew.LoadBoard(brd)
    lama = [z for z in b.Zones() if not z.GetIsRuleArea()]
    _SIMPAN.extend(lama)
    for z in lama:
        b.Remove(z)
    bb = b.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = bb.GetLeft() - 1000000, bb.GetTop() - 1000000, bb.GetRight() + 1000000, bb.GetBottom() + 1000000
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b)
        z.SetLayer(lay)
        z.SetNet(b.FindNet("GND"))
        z.SetZoneName("GND")
        z.SetLocalClearance(pcbnew.FromMM(POUR_CLR))
        z.SetMinThickness(pcbnew.FromMM(max(0.35, W_MIN)))
        z.SetThermalReliefGap(pcbnew.FromMM(0.5))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.5))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(x, y)
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(brd, b)
    print("GND pour F.Cu + B.Cu")


def jahit(brd):
    """via jahit GND: menyambung pulau-pulau GND pour sisi atas dan bawah yang terpisah oleh jalur. Via hanya di titik
    yang seluruh tembaganya (+0,1 mm) berada di dalam pour kedua sisi (otomatis berjarak >= 0,5 mm dari net lain),
    tidak di rule area tanpa via, tidak di pad, >= 0,6 mm dari lubang lain. Hanya via yang menggabungkan dua kelompok
    pulau yang belum tersambung yang dipasang (jumlah minimum), lalu pour diisi ulang."""
    b = pcbnew.LoadBoard(brd)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    gnd = {z.GetLayer(): z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "GND"}
    poly = {L: gnd[L].GetFilledPolysList(L) for L in (pcbnew.F_Cu, pcbnew.B_Cu)}
    larang = [z.Outline() for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    induk = {}

    def akar(k):
        while induk.setdefault(k, k) != k:
            k = induk[k]
        return k

    def satukan(a, c):
        induk[akar(a)] = akar(c)

    def pulau_di(L, p, r=0):
        ps = poly[L]
        for i in range(ps.OutlineCount()):
            if all(ps.Contains(pcbnew.VECTOR2I(int(p.x + r * math.cos(a)), int(p.y + r * math.sin(a))), i)
                   for a in ([0] if r == 0 else [k * math.pi / 6 for k in range(12)])):
                return i
        return None

    lubang, kotak_pad = [], []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            kotak_pad.append((bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
            if p.GetDrillSize().x > 0:
                lubang.append((p.GetPosition(), p.GetDrillSize().x / 2))
            if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                f, k = pulau_di(pcbnew.F_Cu, p.GetPosition()), pulau_di(pcbnew.B_Cu, p.GetPosition())
                if f is not None and k is not None:
                    satukan(("F", f), ("B", k))
    for v in b.GetTracks():
        if v.GetClass() == "PCB_VIA":
            lubang.append((v.GetPosition(), v.GetDrillValue() / 2))
            if v.GetNetname() == "GND":
                f, k = pulau_di(pcbnew.F_Cu, v.GetPosition()), pulau_di(pcbnew.B_Cu, v.GetPosition())
                if f is not None and k is not None:
                    satukan(("F", f), ("B", k))
    for L, n in (("F", poly[pcbnew.F_Cu].OutlineCount()), ("B", poly[pcbnew.B_Cu].OutlineCount())):
        for i in range(n):
            akar((L, i))
    r_cu, r_lb = pcbnew.FromMM(0.75), pcbnew.FromMM(0.3)
    bb = b.GetBoardEdgesBoundingBox()
    langkah = pcbnew.FromMM(0.5)
    dipasang = []
    for x in range(bb.GetLeft(), bb.GetRight(), langkah):
        for y in range(bb.GetTop(), bb.GetBottom(), langkah):
            p = pcbnew.VECTOR2I(x, y)
            if any(x0 - r_cu < x < x1 + r_cu and y0 - r_cu < y < y1 + r_cu for x0, y0, x1, y1 in kotak_pad):
                continue
            if any((p - q).EuclideanNorm() < r_lb + rr + pcbnew.FromMM(0.6) for q, rr in lubang):
                continue
            if any(ol.Collide(p, r_cu) for ol in larang):
                continue
            f = pulau_di(pcbnew.F_Cu, p, r_cu)
            k = pulau_di(pcbnew.B_Cu, p, r_cu) if f is not None else None
            if k is None or akar(("F", f)) == akar(("B", k)):
                continue
            satukan(("F", f), ("B", k))
            tambah_via(b, "GND", mm(x), mm(y))
            lubang.append((p, r_lb))
            dipasang.append((round(mm(x), 2), round(mm(y), 2)))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(brd, b)
    grup = {akar(k) for k in induk}
    print(f"via jahit GND: {len(dipasang)} {dipasang}; kelompok pulau tersisa {len(grup)}")


def gnd_sisa(brd, out, tepi=0.35):
    """sesudah pour + jahit: kelompok tembaga GND (pulau pour, pad, via, jalur) yang belum tersambung ke kelompok
    terbesar diekspor sebagai sambungan untuk x2_cari. Ujung sambungan = semua pad kelompok itu + titik-titik di dalam
    pulau pour-nya (>= `tepi` mm dari tepi pulau), jadi pencari jalur memilih pasangan titik yang paling dekat."""
    b = pcbnew.LoadBoard(brd)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    gnd = {z.GetLayer(): z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "GND"}
    LAY = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
    poly = {L: gnd[LAY[L]].GetFilledPolysList(LAY[L]) for L in LAY}
    induk = {}

    def akar(k):
        while induk.setdefault(k, k) != k:
            k = induk[k]
        return k

    def satukan(a, c):
        induk[akar(a)] = akar(c)

    def pulau_kena(L, pts):
        ps = poly[L]
        return {i for i in range(ps.OutlineCount()) for p in pts if ps.Contains(p, i)}

    def keliling(x0, y0, x1, y1, m=pcbnew.FromMM(0.1), d=pcbnew.FromMM(0.1)):
        x0, y0, x1, y1 = x0 - m, y0 - m, x1 + m, y1 + m
        pts = [pcbnew.VECTOR2I(x, y) for x in range(x0, x1 + 1, d) for y in (y0, y1)]
        return pts + [pcbnew.VECTOR2I(x, y) for y in range(y0, y1 + 1, d) for x in (x0, x1)]

    bentuk = {}                                   # node -> ujung: segmen [lay, a, c, hw] / lingkaran [lay, x, y, r]
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != "GND":
                continue
            k = ("pad", fp.GetReference(), p.GetNumber(), p.m_Uuid.AsString())
            akar(k)
            bb = p.GetBoundingBox()
            x0, y0, x1, y1 = mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())
            hw = min(x1 - x0, y1 - y0) / 2
            if x1 - x0 > y1 - y0:
                seg = [[x0 + hw, (y0 + y1) / 2], [x1 - hw, (y0 + y1) / 2], hw]
            else:
                seg = [[(x0 + x1) / 2, y0 + hw], [(x0 + x1) / 2, y1 - hw], hw]
            lays = lapis(p)
            bentuk[k] = [[L] + seg for L in lays]
            pts = keliling(bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())
            for L in lays:
                for i in pulau_kena(L, pts):
                    satukan(k, (L, i))
    for v in b.GetTracks():
        if v.GetNetname() != "GND":
            continue
        k = ("jalur", v.m_Uuid.AsString())
        akar(k)
        if v.GetClass() == "PCB_VIA":
            c, r = v.GetPosition(), pcbnew.FromMM(0.7)
            pts = [pcbnew.VECTOR2I(int(c.x + r * math.cos(a)), int(c.y + r * math.sin(a))) for a in range(0, 7)]
            for L in LAY:
                for i in pulau_kena(L, pts):
                    satukan(k, (L, i))
            bentuk[k] = [["FB", mm(c.x), mm(c.y), 0.65]]
            continue
        L = "F" if v.GetLayer() == pcbnew.F_Cu else "B"
        s, e = v.GetStart(), v.GetEnd()
        for i in pulau_kena(L, [s, e, pcbnew.VECTOR2I((s.x + e.x) // 2, (s.y + e.y) // 2)]):
            satukan(k, (L, i))
        bentuk[k] = [[L, [mm(s.x), mm(s.y)], [mm(e.x), mm(e.y)], mm(v.GetWidth()) / 2]]
        for k2, bs in list(bentuk.items()):       # jalur yang ujungnya di pad GND
            if k2[0] != "pad":
                continue
            for q in (s, e):
                for lay, a, c, hw in bs:
                    if L in lay and min(a[0], c[0]) - hw <= mm(q.x) <= max(a[0], c[0]) + hw and \
                            min(a[1], c[1]) - hw <= mm(q.y) <= max(a[1], c[1]) + hw:
                        satukan(k, k2)
    luas = {}
    r_in, langkah = pcbnew.FromMM(tepi), pcbnew.FromMM(0.8)
    bb = b.GetBoardEdgesBoundingBox()
    for L in LAY:
        ps = poly[L]
        for i in range(ps.OutlineCount()):
            k = (L, i)
            akar(k)
            luas[k] = ps.Outline(i).Area() / 1e12
            titik = []
            for x in range(bb.GetLeft(), bb.GetRight(), langkah):
                for y in range(bb.GetTop(), bb.GetBottom(), langkah):
                    if ps.Contains(pcbnew.VECTOR2I(x, y), i) and all(
                            ps.Contains(pcbnew.VECTOR2I(int(x + r_in * math.cos(a)), int(y + r_in * math.sin(a))), i)
                            for a in [k * math.pi / 4 for k in range(8)]):
                        titik.append([L, mm(x), mm(y), W_MIN])
            bentuk[k] = titik
    grup = {}
    for k in induk:
        grup.setdefault(akar(k), []).append(k)
    utama = max(grup.values(), key=lambda ks: sum(luas.get(k, 0) for k in ks))

    def ujung_grup(ks):
        segs = [x for k in ks for x in bentuk.get(k, []) if isinstance(x[1], list)]
        circ = [x for k in ks for x in bentuk.get(k, []) if not isinstance(x[1], list)]
        return {"jenis": "pulau", "segs": segs, "vias": circ, "anchor": None}

    d = dasar(b, {})
    d["jalur"] = [j for j in d["jalur"] if j[0] != "GND"]
    pasang = []
    tujuan = ujung_grup(utama)
    for ks in grup.values():
        if ks is utama:
            continue
        A = ujung_grup(ks)
        if not A["segs"] and not A["vias"]:
            continue
        print("  kelompok terpisah:", [k[1:3] if k[0] == "pad" else k[:1] for k in ks][:8])
        pasang.append({"net": "GND", "A": A, "B": tujuan, "jarak": 5.0})
    d["pasang"] = pasang
    json.dump(d, open(out, "w", encoding="utf8"))
    print(f"GND: {len(grup)} kelompok, {len(pasang)} sambungan ke kelompok utama")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fanout":
        fanout_usb(sys.argv[2])
    elif cmd == "ekspor":
        ekspor(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
    elif cmd == "pasang":
        pasang(sys.argv[2], sys.argv[3])
    elif cmd == "pour":
        pour(sys.argv[2])
    elif cmd == "jahit":
        jahit(sys.argv[2])
    elif cmd == "gnd":
        gnd_sisa(sys.argv[2], sys.argv[3], *(float(a) for a in sys.argv[4:5]))
    else:
        raise SystemExit(__doc__)
