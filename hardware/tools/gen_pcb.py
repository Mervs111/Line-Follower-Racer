#!/usr/bin/env python3
"""Generator layout PCB Robot Line Tracer Micro: PCB utama + PCB sensor jangkar (KiCad 7 pcbnew + FreeRouting).

Alur: skematik -> netlist (kicad-cli) -> outline dari model mekanik v11 -> footprint di posisi mekanik
      -> DSN -> FreeRouting (autorouter) -> SES -> jalur & via -> pour GND -> DRC -> .kicad_pcb

Koordinat penempatan di script ini = koordinat model mekanik (mm; X kanan, Y maju, nol = tengah poros
roda): PCB utama v2 = arsip/mechanical/cadquery/ltm_v12.py, PCB sensor = ltm_v11.py (folder yang sama). Di KiCad: x = X + OX, y = OY - Y.

Jalankan dengan Python yang punya modul pcbnew (Python bawaan KiCad), butuh kicad-cli, java 21+ dan
FreeRouting (FREEROUTING_JAR):
    python3 hardware/tools/gen_pcb.py            # dua papan
    python3 hardware/tools/gen_pcb.py main       # PCB utama saja
PERINGATAN: menjalankan ulang MENIMPA .kicad_pcb (jalur yang diedit manual hilang).
"""
import json, math, os, re, shutil, subprocess, sys
import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_kicad import parse  # noqa: E402

HW = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FPDIR = os.environ.get("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
LTM_PRETTY = os.path.join(HW, "ltm-lib", "ltm.pretty")
FREEROUTING = os.environ.get("FREEROUTING_JAR", "/opt/freerouting/freerouting.jar")
JAVA = os.environ.get("JAVA", shutil.which("java") or "java")
WORK = os.environ.get("LTM_WORK", os.path.join(HW, "build"))
FR_ARGS = os.environ.get("LTM_FR_ARGS", "").split()        # argumen tambahan FreeRouting (eksperimen)
ROUNDS = int(os.environ.get("LTM_ROUNDS", "3"))              # ronde FreeRouting (hasil diumpankan lagi)
OX, OY = 100.0, 150.0
mm = pcbnew.FromMM
# aturan cetak PCB di tempat user (13/10/2026): jalur minimal 0,8 mm. Jarak 0,5 mm dan via 1,6/0,8 mm =
# asumsi aman untuk cetak lokal (cek ke tempat cetak).
FAB = dict(track=0.8, power=1.2, clearance=0.5, via=1.6, via_drill=0.8, edge=0.5)
DRU = """(version 1)

# Pad GND yang dikepung jalur boleh tersambung ke pour dengan 1 spoke (jalur GND tetap ada)
(rule "spoke_min_1"
  (constraint min_resolved_spokes 1))

# Tab logam saklar geser (tanpa net) bawaan footprint berjarak 0,25 mm dari kaki 1/3. Kalau tersambung
# saat dicetak tidak apa-apa: tab hanya pegangan mekanik.
(rule "tab_saklar_SW1"
  (condition "A.Type == 'Pad' && B.Type == 'Pad' && A.intersectsCourtyard('SW1') && B.intersectsCourtyard('SW1')")
  (constraint clearance (min 0.2mm)))
"""


def fab_project(pro_path):
    """tulis aturan FAB ke net class & aturan desain di .kicad_pro (dibaca pcbnew.NewBoard)"""
    pro = json.load(open(pro_path))
    for c in pro["net_settings"]["classes"]:
        c.update(clearance=FAB["clearance"], via_diameter=FAB["via"], via_drill=FAB["via_drill"],
                 track_width=FAB["power"] if c["name"] == "Power" else FAB["track"])
    pro.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {}).update(
        min_clearance=FAB["clearance"], min_track_width=FAB["track"], min_via_diameter=FAB["via"],
        min_copper_edge_clearance=FAB["edge"])
    json.dump(pro, open(pro_path, "w"), indent=2)


def P(x, y):
    return pcbnew.VECTOR2I(mm(x + OX), mm(OY - y))


def mech(v):
    return pcbnew.ToMM(v.x) - OX, OY - pcbnew.ToMM(v.y)


# ------------------------------------------------------------------ geometri
def _sub(a, b): return (a[0] - b[0], a[1] - b[1])
def _add(a, b): return (a[0] + b[0], a[1] + b[1])
def _mul(a, k): return (a[0] * k, a[1] * k)


def _unit(a):
    d = math.hypot(*a)
    return (a[0] / d, a[1] / d)


def rounded_outline(pts, r, min_turn=8.0):
    """poligon -> [('seg', a, b) | ('arc', a, mid, b)] dengan sudut di-fillet jari-jari r"""
    n = len(pts)
    corners = []
    for i in range(n):
        p, a, b = pts[i], pts[i - 1], pts[(i + 1) % n]
        u1, u2 = _unit(_sub(a, p)), _unit(_sub(b, p))
        ang = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])))
        if 180 - math.degrees(ang) < min_turn:
            corners.append((p, None, None, None))
            continue
        d = r / math.tan(ang / 2)
        t1, t2 = _add(p, _mul(u1, d)), _add(p, _mul(u2, d))
        c = _add(p, _mul(_unit(_add(u1, u2)), r / math.sin(ang / 2)))
        corners.append((p, t1, _add(c, _mul(_unit(_sub(p, c)), r)), t2))
    out = []
    for i in range(n):
        p, t1, m, t2 = corners[i]
        q = corners[(i + 1) % n]
        if t1:
            out.append(("arc", t1, m, t2))
        out.append(("seg", t2 or p, q[1] or q[0]))
    return out


# ------------------------------------------------------------------ netlist
def _field(e, key):
    for k in e:
        if isinstance(k, list) and k[0] == key:
            return k[1].strip('"')
    return None


def read_netlist(path):
    tree = parse(open(path).read())
    comps, pins = {}, {}
    for e in tree:
        if isinstance(e, list) and e[0] == "components":
            for c in e[1:]:
                props = {_field(p, "name"): _field(p, "value") for p in c if isinstance(p, list) and p[0] == "property"}
                comps[_field(c, "ref")] = dict(value=_field(c, "value"), fp=_field(c, "footprint"),
                                               uuid=_field(c, "tstamps"), props=props)
        if isinstance(e, list) and e[0] == "nets":
            for n in e[1:]:
                name = _field(n, "name")
                for nd in n:
                    if isinstance(nd, list) and nd[0] == "node":
                        pins[(_field(nd, "ref"), _field(nd, "pin"))] = name
    return comps, pins


# ------------------------------------------------------------------ papan
class Board:
    def __init__(self, name, title, rev="v1-draft", date="2026-10-11", mech="v11"):
        self.name, self.title = name, title
        self.dir = os.path.join(HW, name)
        self.path = os.path.join(self.dir, name + ".kicad_pcb")
        os.makedirs(WORK, exist_ok=True)
        net_path = os.path.join(WORK, name + ".net")
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net_path,
                        os.path.join(self.dir, name + ".kicad_sch")], check=True, capture_output=True)
        self.comps, self.pinnet = read_netlist(net_path)
        if os.path.exists(self.path):
            os.remove(self.path)
        fab_project(os.path.join(self.dir, name + ".kicad_pro"))
        open(os.path.join(self.dir, name + ".kicad_dru"), "w").write(DRU)
        self.b = pcbnew.NewBoard(self.path)          # memuat net class dari .kicad_pro
        self.b.SetFileName(self.path)                # dipakai DRC untuk membaca .kicad_dru
        self.nets = {}
        for name_ in sorted(set(self.pinnet.values())):
            ni = pcbnew.NETINFO_ITEM(self.b, name_)
            self.b.Add(ni)
            self.nets[name_] = ni
        self.fps = {}
        self.outline_pts = None
        tb = self.b.GetTitleBlock()
        tb.SetTitle(title)
        tb.SetDate(date)
        tb.SetRevision(rev)
        tb.SetCompany("P01 Kel.5 PjBL DTEO FV ITS")
        tb.SetComment(0, f"Layout mengikuti mekanik {mech}; footprint modul SEMENTARA (ukur ulang)")
        tb.SetComment(1, "Jalur dirouting otomatis FreeRouting: routing ulang setelah footprint final")

    # -------------------------------------------------- aturan desain
    def rules(self):
        ds = self.b.GetDesignSettings()
        ds.m_MinClearance = mm(FAB["clearance"])
        ds.m_TrackMinWidth = mm(FAB["track"])
        ds.m_ViasMinSize = mm(FAB["via"])
        ds.m_MinThroughDrill = mm(0.3)
        ds.m_ViasMinAnnularWidth = mm(0.13)
        ds.m_CopperEdgeClearance = mm(FAB["edge"])
        ds.m_HoleClearance = mm(0.25)
        ds.m_HoleToHoleMin = mm(0.5)
        ds.m_SilkClearance = mm(0.0)
        ds.SetBoardThickness(mm(1.6))

    # -------------------------------------------------- outline
    def outline(self, pts, r):
        self.outline_pts = pts
        for it in rounded_outline(pts, r):
            s = pcbnew.PCB_SHAPE(self.b)
            if it[0] == "seg":
                s.SetShape(pcbnew.SHAPE_T_SEGMENT)
                s.SetStart(P(*it[1]))
                s.SetEnd(P(*it[2]))
            else:
                s.SetShape(pcbnew.SHAPE_T_ARC)
                s.SetArcGeometry(P(*it[1]), P(*it[2]), P(*it[3]))
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetWidth(mm(0.1))
            self.b.Add(s)

    # -------------------------------------------------- footprint
    def place(self, ref, x, y, rot=0.0, side="F"):
        c = self.comps[ref]
        lib, name = c["fp"].split(":")
        fp = pcbnew.FootprintLoad(LTM_PRETTY if lib == "ltm" else os.path.join(FPDIR, lib + ".pretty"), name)
        if fp is None:
            raise SystemExit(f"footprint {c['fp']} tidak ditemukan")
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        fp.SetProperty("Sheetfile", c["props"].get("Sheetfile", self.name + ".kicad_sch"))
        fp.SetProperty("Sheetname", "")
        if "exclude_from_bom" in c["props"]:
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
        self.b.Add(fp)
        fp.SetPosition(P(x, y))
        if side == "B":
            fp.Flip(fp.GetPosition(), False)
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            net = self.pinnet.get((ref, pad.GetNumber()))
            if net:
                pad.SetNet(self.nets[net])
        for t in (fp.Reference(), fp.Value()):
            t.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
            t.SetTextThickness(mm(0.12))
        fp.Value().SetVisible(False)
        self.fps[ref] = fp
        return fp

    # -------------------------------------------------- teks referensi otomatis
    def _inside(self, x, y, margin):
        """titik KiCad (mm) berada di dalam outline dengan jarak >= margin dari tepi"""
        X, Y = x - OX, OY - y
        pts, inside, dmin = self.outline_pts, False, 1e9
        for i in range(len(pts)):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
            if (y1 > Y) != (y2 > Y) and X < x1 + (Y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
            dx, dy = x2 - x1, y2 - y1
            t = max(0.0, min(1.0, ((X - x1) * dx + (Y - y1) * dy) / (dx * dx + dy * dy)))
            dmin = min(dmin, math.hypot(X - x1 - t * dx, Y - y1 - t * dy))
        return inside and dmin >= margin

    def _silk_obstacles(self, side):
        silk = pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS
        cu = pcbnew.F_Cu if side == "F" else pcbnew.B_Cu
        obs = []

        def rect(bb, m):
            return (pcbnew.ToMM(bb.GetLeft()) - m, pcbnew.ToMM(bb.GetTop()) - m,
                    pcbnew.ToMM(bb.GetRight()) + m, pcbnew.ToMM(bb.GetBottom()) + m)
        for fp in self.b.GetFootprints():
            for p in fp.Pads():
                if p.IsOnLayer(cu) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    obs.append(rect(p.GetBoundingBox(), 0.2))
            for g in fp.GraphicalItems():
                if g.GetLayer() == silk:
                    obs.append(rect(g.GetBoundingBox(), 0.1))
        for d in self.b.GetDrawings():
            if d.GetLayer() == silk:
                obs.append(rect(d.GetBoundingBox(), 0.15))
        return obs

    def auto_refs(self, hide=(), inside=(), size=0.9):
        """letakkan teks referensi di sekitar footprint tanpa menimpa pad, silkscreen lain, atau tepi papan"""
        placed = {"F": [], "B": []}
        obst = {"F": self._silk_obstacles("F"), "B": self._silk_obstacles("B")}

        def hit(r, lst):
            return any(r[0] < o[2] and r[2] > o[0] and r[1] < o[3] and r[3] > o[1] for o in lst)

        for ref in sorted(self.fps, key=lambda r: -self.fps[r].GetBoundingBox(False, False).GetArea()):
            fp = self.fps[ref]
            t = fp.Reference()
            if ref in hide:
                t.SetVisible(False)
                continue
            side = "B" if fp.IsFlipped() else "F"
            t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
            t.SetTextThickness(mm(size * 0.15))
            xs, ys = [], []
            for p in fp.Pads():
                bb = p.GetBoundingBox()
                xs += [bb.GetLeft(), bb.GetRight()]
                ys += [bb.GetTop(), bb.GetBottom()]
            for g in fp.GraphicalItems():
                if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                    bb = g.GetBoundingBox()
                    xs += [bb.GetLeft(), bb.GetRight()]
                    ys += [bb.GetTop(), bb.GetBottom()]
            x0, x1, y0, y1 = (pcbnew.ToMM(v) for v in (min(xs), max(xs), min(ys), max(ys)))
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            best = None
            for ang in (0, 90):
                t.SetTextAngleDegrees(ang - fp.GetOrientationDegrees())
                t.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy)))
                bb = t.GetBoundingBox()
                w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
                g = 0.25
                cands = [(cx, cy)] if ref in inside else []
                cands += [(cx, y0 - g - h / 2), (cx, y1 + g + h / 2), (x0 - g - w / 2, cy), (x1 + g + w / 2, cy),
                          (x0 - g - w / 2, y0 - g - h / 2), (x1 + g + w / 2, y0 - g - h / 2),
                          (x0 - g - w / 2, y1 + g + h / 2), (x1 + g + w / 2, y1 + g + h / 2)]
                for px, py in cands:
                    r = (px - w / 2, py - h / 2, px + w / 2, py + h / 2)
                    corners = [(r[0], r[1]), (r[2], r[1]), (r[0], r[3]), (r[2], r[3]), (px, r[1]), (px, r[3])]
                    if not all(self._inside(a, b_, 0.5) for a, b_ in corners):
                        continue
                    if (px, py) != (cx, cy) and hit(r, obst[side]):
                        continue
                    if hit(r, placed[side]):
                        continue
                    best = (ang, px, py, r)
                    break
                if best:
                    break
            if best is None:
                t.SetVisible(False)
                print(f"  [silk] {self.name}: teks {ref} disembunyikan (tidak ada tempat)")
                continue
            ang, px, py, r = best
            t.SetTextAngleDegrees(ang - fp.GetOrientationDegrees())
            t.SetPosition(pcbnew.VECTOR2I(mm(px), mm(py)))
            t.SetVisible(True)
            placed[side].append(r)

    def no_track_between_pads(self, prefixes):
        """larang jalur/via lewat di antara dua pad komponen SMD kecil (lebih aman saat disolder tangan)"""
        for ref, fp in self.fps.items():
            pads = list(fp.Pads())
            if not ref.startswith(prefixes) or len(pads) != 2 or pads[0].GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            a, b_ = (p.GetBoundingBox() for p in pads)
            x0, x1 = max(a.GetLeft(), b_.GetLeft()), min(a.GetRight(), b_.GetRight())
            y0, y1 = max(a.GetTop(), b_.GetTop()), min(a.GetBottom(), b_.GetBottom())
            if x0 < x1:          # pad tersusun vertikal: celah di arah Y
                y0, y1 = min(a.GetBottom(), b_.GetBottom()), max(a.GetTop(), b_.GetTop())
            else:
                x0, x1 = min(a.GetRight(), b_.GetRight()), max(a.GetLeft(), b_.GetLeft())
            X0, Y1 = mech(pcbnew.VECTOR2I(x0, y0))
            X1, Y0 = mech(pcbnew.VECTOR2I(x1, y1))
            layer = pcbnew.B_Cu if fp.IsFlipped() else pcbnew.F_Cu
            self.keepout(X0, Y0, X1, Y1, f"celah pad {ref}", pour=False, layers=(layer,))

    def pad_xy(self, ref, num):
        for p in self.fps[ref].Pads():
            if p.GetNumber() == num:
                return mech(p.GetPosition())
        raise KeyError((ref, num))

    # -------------------------------------------------- grafis
    def text(self, s, x, y, size=1.0, ang=0.0, layer=pcbnew.F_SilkS, bold=False, thick=None):
        t = pcbnew.PCB_TEXT(self.b)
        t.SetText(s)
        t.SetPosition(P(x, y))
        t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(thick or size * (0.2 if bold else 0.15)))
        t.SetTextAngleDegrees(ang)
        if layer in (pcbnew.B_SilkS, pcbnew.B_Cu):
            t.SetMirrored(True)
        self.b.Add(t)
        return t

    def line(self, pts, layer=pcbnew.F_SilkS, w=0.15, close=False):
        pts = list(pts) + ([pts[0]] if close else [])
        for a, b in zip(pts, pts[1:]):
            s = pcbnew.PCB_SHAPE(self.b)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(P(*a))
            s.SetEnd(P(*b))
            s.SetLayer(layer)
            s.SetWidth(mm(w))
            self.b.Add(s)

    def arrow(self, a, b, layer=pcbnew.F_SilkS, w=0.2, head=0.9):
        """panah dari a ke b (ujung di b)"""
        self.line([a, b], layer, w)
        d = _unit(_sub(a, b))
        for s in (1, -1):
            c, n = math.cos(math.radians(28)), s * math.sin(math.radians(28))
            self.line([b, _add(b, _mul((d[0] * c - d[1] * n, d[0] * n + d[1] * c), head))], layer, w)

    # -------------------------------------------------- zone
    def _zone(self, pts, layers):
        z = pcbnew.ZONE(self.b)
        ls = pcbnew.LSET()
        for l in layers:
            ls.AddLayer(l)
        z.SetLayerSet(ls)
        o = z.Outline()
        o.NewOutline()
        for x, y in pts:
            v = P(x, y)
            o.Append(v.x, v.y)
        return z

    def keepout(self, x0, y0, x1, y1, name, tracks=True, pour=True, layers=(pcbnew.F_Cu, pcbnew.B_Cu)):
        z = self._zone([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layers)
        z.SetIsRuleArea(True)
        z.SetZoneName(name)
        z.SetDoNotAllowCopperPour(pour)
        z.SetDoNotAllowTracks(tracks)
        z.SetDoNotAllowVias(tracks)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        self.b.Add(z)
        return z

    def gnd_pour(self, layer, prio=0):
        xs = [p[0] for p in self.outline_pts]
        ys = [p[1] for p in self.outline_pts]
        x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
        z = self._zone([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], [layer])
        z.SetNet(self.nets["GND"])
        z.SetZoneName("GND " + ("atas" if layer == pcbnew.F_Cu else "bawah"))
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(mm(FAB["clearance"]))
        z.SetMinThickness(mm(FAB["track"]))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(mm(FAB["clearance"]))
        z.SetThermalReliefSpokeWidth(mm(FAB["track"]))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        self.b.Add(z)
        return z

    # -------------------------------------------------- routing
    def autoroute(self, passes=40, thin_nets=(), rounds=1):
        """thin_nets: net Power yang dirouting dengan lebar default (mis. GND: nanti dibantu pour).
        rounds > 1: hasil diumpankan lagi ke FreeRouting (jalur lama boleh dibongkar) sampai semua tersambung"""
        dsn = os.path.join(WORK, self.name + ".dsn")
        ses = os.path.join(WORK, self.name + ".ses")
        for k in range(rounds):
            if os.path.exists(ses):
                os.remove(ses)
            if not pcbnew.ExportSpecctraDSN(self.b, dsn):
                raise SystemExit("ekspor DSN gagal")
            if thin_nets:                                 # pindahkan net dari class Power ke class default
                txt = open(dsn).read()
                i = txt.index("(class Power ") + len("(class Power ")
                j = txt.index("(circuit", i)
                names = [n for n in txt[i:j].split() if n not in thin_nets]
                txt = txt[:i] + " ".join(names) + "\n      " + txt[j:]
                i = txt.index('(class kicad_default ""')
                j = txt.index("(circuit", i)
                txt = txt[:j] + " ".join(thin_nets) + "\n      " + txt[j:]
                open(dsn, "w").write(txt)
            if k == 0:
                shutil.copy(dsn, os.path.join(WORK, self.name + "-r1.dsn"))
            cmd = [JAVA, "-jar", FREEROUTING, "-de", dsn, "-do", ses, "-mp", str(passes), "-mt", "1",
                   "--gui.enabled=false", "--router.automatic_neckdown=false",
                   # via murah: dengan jalur 0,8 mm router perlu bebas pindah lapisan (default berhenti di 1-7 sisa)
                   "--router.scoring.via_costs=10"] + FR_ARGS
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=WORK)
            open(os.path.join(WORK, f"{self.name}.freerouting{k + 1}.log"), "w").write(r.stdout + r.stderr)
            if not os.path.exists(ses):
                raise SystemExit("FreeRouting tidak menghasilkan SES, lihat log di " + WORK)
            for t in list(self.b.GetTracks()):        # SES berisi seluruh jalur: ganti jalur lama
                self.b.Remove(t)
            n = import_ses(self, ses)
            self.b.BuildConnectivity()
            left = self.b.GetConnectivity().GetUnconnectedCount(False)
            print(f"    ronde {k + 1}: {n[0]} segmen, {n[1]} via, belum tersambung {left}")
            if left == 0:
                break
        return n

    def fill_and_check(self):
        rpt = os.path.join(WORK, self.name + "-drc.rpt")
        # DRC pertama menyiapkan mesin aturan (dipakai zone filler untuk jarak ke lubang NPTH)
        pcbnew.WriteDRCReport(self.b, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
        filler = pcbnew.ZONE_FILLER(self.b)
        filler.Fill(self.b.Zones())
        pcbnew.WriteDRCReport(self.b, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
        return rpt

    def save(self):
        self.b.SetModified()
        pcbnew.SaveBoard(self.path, self.b)


# ------------------------------------------------------------------ SES -> jalur & via
def import_ses(brd, ses_path):
    """baca session FreeRouting (Specctra SES) dan tambahkan jalur/via ke papan"""
    tree = parse(open(ses_path).read())

    def find(e, key):
        return [k for k in e if isinstance(k, list) and k[0] == key]

    routes = find(tree, "routes")[0]
    res = find(routes, "resolution")[0]
    unit, per = res[1], float(res[2])
    scale = {"um": 1e-3, "mm": 1.0, "mil": 0.0254, "inch": 25.4}[unit] / per

    def pt(x, y):          # koordinat SES (Y ke atas) -> KiCad (nm)
        return pcbnew.VECTOR2I(mm(float(x) * scale), mm(-float(y) * scale))

    vias = {}
    for lib in find(routes, "library_out"):
        for ps in find(lib, "padstack"):
            name = ps[1].strip('"')
            m = re.search(r"(\d+):(\d+)_um", name)
            if m:
                vias[name] = (int(m.group(1)) * 1000, int(m.group(2)) * 1000)
    layer_id = {brd.b.GetLayerName(l): l for l in (pcbnew.F_Cu, pcbnew.B_Cu)}
    n_tr = n_via = 0
    for no in find(routes, "network_out"):
        for net in find(no, "net"):
            ni = brd.nets[net[1].strip('"')]
            for w in find(net, "wire"):
                path = find(w, "path")[0]
                layer = layer_id[path[1].strip('"')]
                width = max(mm(float(path[2]) * scale), mm(FAB["track"]))
                xy = path[3:]
                pts = [pt(xy[i], xy[i + 1]) for i in range(0, len(xy) - 1, 2)]
                for a, b in zip(pts, pts[1:]):
                    t = pcbnew.PCB_TRACK(brd.b)
                    t.SetStart(a)
                    t.SetEnd(b)
                    t.SetWidth(width)
                    t.SetLayer(layer)
                    t.SetNet(ni)
                    brd.b.Add(t)
                    n_tr += 1
            for v in find(net, "via"):
                name = v[1].strip('"')
                dia, drill = vias.get(name, (mm(0.6), mm(0.3)))
                via = pcbnew.PCB_VIA(brd.b)
                via.SetPosition(pt(v[2], v[3]))
                via.SetWidth(dia)
                via.SetDrill(drill)
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetNet(ni)
                brd.b.Add(via)
                n_via += 1
    return n_tr, n_via


# ================================================================== PCB UTAMA
# outline = MAIN_PTS di arsip/mechanical/cadquery/ltm_v12.py (fillet 2,5)
MAIN_PTS = [(-36, 8), (36, 8), (36, 18), (47, 22), (47, 62), (28, 86), (13, 92), (-13, 92), (-28, 86),
            (-47, 62), (-47, 22), (-36, 18)]
HOLES_MAIN = {"H1": (-32, 16), "H2": (32, 16),          # standoff ke dudukan baterai (sama dengan model)
              "H3": (-37.5, 69), "H4": (37.5, 69)}      # bahu depan + dudukan 3D print PCB sensor
# v2 (13/10/2026): ESP32 keluar dari bawah dudukan baterai (dudukan berakhir di Y 30) dan dipasang di socket
# female; buck, dioda, dan pembaca baterai pindah ke bawah dudukan baterai; kapasitor kecil & pull-up dibuang.
MAIN_PLACE = {
    # ref: (X, Y, rotasi)  = posisi ORIGIN footprint (pin 1 untuk konektor), koordinat mekanik
    "U1": (-24.6, 44.4, 270),   # ESP32 melintang, USB ke kiri (-X), antena ke kanan;
                                # baris pin 1-15 di depan (Y 57,1), 16-30 di belakang (Y 31,7)
    "U2": (-0.5, 70.8, 0),      # TB6612 tengah depan: kolom kiri = input, kolom kanan = VM/VCC/GND/output
    "U3": (0.0, 21.1, 180),     # MP1584 di bawah dudukan baterai: IN di kanan, OUT di kiri
    "J4": (24.29, 62.55, 90),   # socket OLED, header OLED di sisi depan (tampilan tegak, tidak diputar)
    "J5": (-6.35, 85.8, 90),    # box header IDC 2x6 ke kabel pita PCB sensor (baris belakang = 6 sinyal)
    "R5": (-13.75, 80.6, 90), "R6": (13.75, 80.6, 90),     # pull-up tombol (GPIO34/35)
    "SW2": (-23.25, 85.25, 0), "SW3": (16.75, 85.25, 0),
    "BZ1": (-29.8, 70.0, 0), "Q1": (-18.4, 74.5, 0), "R3": (-16.5, 61.0, 90), "R4": (-13.5, 61.0, 90),
    "J2": (-27.0, 11.3, 0), "J3": (17.0, 11.3, 0),           # motor kiri / kanan
    "J1": (43.6, 28.1, 270),    # baterai (dari BMS), tepi kanan di luar dudukan baterai; pin 1 (BAT+) di depan
    "SW1": (44.6, 35.0, 90),    # saklar geser di tepi kanan (di bawah OLED), tuas keluar ke +X
    "D1": (-25.0, 17.5, 0),
    "R1": (17.0, 26.0, 0), "R2": (17.0, 21.0, 0),
    "C1": (12.4, 75.5, 0),      # dekat pin VM TB6612
    **{k: (x, y, 0) for k, (x, y) in HOLES_MAIN.items()},
}
ANTENNA = (-1.4, 30.2, 4.7, 58.6)          # ujung antena ESP32 (X0, Y0, X1, Y1)
CASTER = (0.0, 62.0, 5.5)                  # ball caster di bawah PCB utama (X, Y, jari-jari rumah)
BMS = (-46.5, 37.0, -2.5, 52.0)            # modul BMS 2S ditempel di bawah PCB utama, di antara baris pin ESP32
DAYA = [(-27.8, 14.4), (-12.2, 14.4), (-12.2, 12.0), (12.2, 12.0), (12.2, 14.4), (27.2, 14.4), (27.2, 29.9),
        (-27.8, 29.9)]                     # kotak blok DAYA (di bawah dudukan baterai)


def build_main(route=True):
    b = Board("ltm-main", "LTM - PCB Utama", rev="v2", date="2026-10-13", mech="v12")
    b.rules()
    b.outline(MAIN_PTS, 2.5)
    for ref, (x, y, r) in MAIN_PLACE.items():
        b.place(ref, x, y, r)
    left = sorted(set(b.comps) - set(MAIN_PLACE))
    if left:
        raise SystemExit(f"komponen belum ditempatkan: {left}")
    # antena ESP32: modul di socket 8,5 mm (antena +-10 mm di atas tembaga), jadi jalur boleh lewat di bawahnya;
    # pour GND tetap dikosongkan (keepout dipasang setelah routing)

    # ---- silkscreen: blok (kotak + nama). Modul bersocket: nama di dalam garis modul (terbaca saat dicabut)
    T, L = b.text, b.line
    L(DAYA, close=True)
    T("DAYA", -20.0, 27.4, 1.6, bold=True)
    b.arrow((26.4, 17.2), (12.6, 17.2))
    T("VBAT", 19.5, 18.2, 0.8)
    b.arrow((-22.0, 20.4), (-22.0, 23.8))
    T("5V", -19.8, 22.1, 0.9, bold=True)
    T("BUCK 5V", 0.0, 24.4, 1.1, bold=True)
    T("IN", 6.4, 21.1, 0.9)
    T("OUT", -6.0, 21.1, 0.9)
    T("BACA BATERAI", 20.8, 29.0, 0.8)
    T("BATERAI", 37.9, 26.9, 0.9, 90)
    T("+", 39.1, 28.1, 1.3, bold=True)
    T("-", 39.1, 25.6, 1.3, bold=True)
    T("SAKLAR", 40.4, 37.0, 0.9, 90)
    T("MOTOR", -31.6, 11.2, 0.8)
    T("KIRI", -31.6, 9.8, 0.8)
    T("MOTOR", 31.6, 11.2, 0.8)
    T("KANAN", 31.6, 9.8, 0.8)
    T("OTAK: ESP32", -21.1, 51.0, 1.8, bold=True)
    T("< USB", -41.0, 41.0, 1.0)
    T("ANTENA", 1.7, 44.6, 0.9, 90)
    T("DRIVER MOTOR", -0.5, 75.6, 1.1, bold=True)
    L([(10.6, 31.6), (41.6, 31.6), (41.6, 60.9), (10.6, 60.9)], close=True)
    T("LAYAR (OLED)", 26.1, 46.0, 1.6, bold=True)
    for i, s in enumerate(("GND", "VCC", "SCL", "SDA")):
        T(s, 24.29 + 2.54 * i, 58.8, 0.8, 90)
    L([(-33.2, 59.4), (-11.4, 59.4), (-11.4, 78.2), (-33.2, 78.2)], close=True)
    T("SUARA", -26.0, 61.4, 1.0, bold=True)
    T("A", -26.5, 83.0, 1.6, bold=True)
    T("B", 26.5, 83.0, 1.6, bold=True)
    # peta alur daya di depan kanan (tetap terlihat setelah robot dirakit)
    T("ALUR DAYA", 25.6, 77.6, 0.9, bold=True)
    T("BATERAI", 22.4, 75.5, 0.8)
    b.arrow((22.4, 74.7), (22.4, 73.3), w=0.15, head=0.6)
    T("SAKLAR", 22.4, 72.4, 0.8)
    b.arrow((22.4, 71.6), (22.4, 70.2), w=0.15, head=0.6)
    b.arrow((25.0, 71.9), (28.6, 70.2), w=0.15, head=0.6)
    T("BUCK 5V", 22.4, 69.3, 0.8)
    T("MOTOR", 30.6, 69.3, 0.8)
    b.arrow((22.4, 68.5), (22.4, 67.1), w=0.15, head=0.6)
    T("ESP32 + SENSOR", 22.4, 66.2, 0.8)
    # sisi bawah: nama papan, tanda tempat ball caster & BMS (tidak boleh ada kaki solder di area caster)
    B = pcbnew.B_SilkS
    T("LINE TRACER MICRO v2", 24.0, 52.0, 1.4, layer=B, bold=True)
    T("P01 KEL.5", 24.0, 49.0, 1.4, layer=B, bold=True)
    T("PjBL DTEO FV ITS 2026", 24.0, 46.4, 1.0, layer=B)
    cx, cy, cr = CASTER
    b.line([(cx + cr * math.cos(math.radians(a)), cy + cr * math.sin(math.radians(a))) for a in range(0, 361, 10)],
           B, 0.15)
    T("CASTER", cx, cy, 1.0, layer=B)
    x0, y0, x1, y1 = BMS
    b.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], B, 0.15, close=True)
    T("BMS 2S (ditempel di sini)", (x0 + x1) / 2, (y0 + y1) / 2, 1.2, layer=B)
    for fp in b.fps.values():
        for pad in fp.Pads():
            if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                px, py = mech(pad.GetPosition())
                if math.hypot(px - cx, py - cy) < cr + 1.0:
                    raise SystemExit(f"pad {fp.GetReference()}.{pad.GetNumber()} kena area ball caster")
                if x0 - 1 < px < x1 + 1 and y0 - 1 < py < y1 + 1:
                    raise SystemExit(f"pad {fp.GetReference()}.{pad.GetNumber()} kena area BMS")
    b.auto_refs(hide=tuple(HOLES_MAIN) + ("J5",), inside=("U1", "U2", "U3"))

    if route:
        print("  routing ltm-main ...", b.autoroute(100, thin_nets=("GND", "/BAT+"), rounds=ROUNDS))
    b.keepout(*ANTENNA, "antena ESP32 (tanpa pour)", tracks=False)
    b.gnd_pour(pcbnew.F_Cu)
    b.gnd_pour(pcbnew.B_Cu)
    rpt = b.fill_and_check()
    b.save()
    return b, rpt


# ================================================================== PCB SENSOR
# v2 (13/10/2026): batang lurus 16 sensor (jarak 6 mm) di dudukan 3D print di depan PCB utama, disambung kabel
# pita 12 pin. ITR20001 di sisi bawah; LED indikator + resistornya di atas; pull-up & resistor LED IR di bawah;
# modul mux, MCP23017 (socket), dan J1 di bagian belakang batang.
F_TIP = 137.0
SB_PTS = [(-55, 86), (55, 86), (55, F_TIP), (-55, F_TIP)]
SX = [-48.75 + 6.5 * i for i in range(16)]    # X sensor S1 (kiri) .. S16 (kanan); jarak 6,5: 1 jalur muat di sela
SY = F_TIP - 4.0                               # Y baris sensor
MUX_X = -8.5                                   # X kaki C0 modul mux
SENSOR_PLACE = {
    # ref: (X, Y, rotasi, sisi)
    # sensor menghadap lantai, diputar: kaki A/K (LED IR) di depan, C/E (fototransistor) di belakang
    **{f"U{k + 1}": (SX[k], SY, 270, "B") for k in range(16)},
    **{f"D{k + 1}": (SX[k], SY - 4.8, 0, "F") for k in range(16)},        # LED indikator di belakang sensor
    **{f"R{25 + k}": (SX[k], SY - 8.0, 0, "F") for k in range(16)},       # resistor LED 330R
    **{f"R{9 + k}": (MUX_X + 2.54 * k, 108.5, 90, "B") for k in range(16)},  # pull-up 10k, di bawah kaki C0-C15
    **{f"R{j + 1}": (SX[2 * j] - 3.25, SY, 90, "F") for j in range(8)},   # LED IR 120R, di sela antar pasangan
    "U18": (-46.5, 95.5, 90, "F"),     # MCP23017 DIP-28: GPA di baris depan, GPB di baris belakang
    "U17": (MUX_X, 112.5, 0, "F"),     # modul mux: C0-C15 di baris depan, SIG..GND di belakang
    "J1": (44.5, 114.3, 0, "F"),       # box header IDC 2x6 (berdiri): kolom dalam = sinyal, kolom luar = daya
    "C1": (MUX_X + 25.4, 93.0, 0, "F"), "C2": (-26.18, 91.5, 0, "F"),
    "Q1": (37.5, 104.0, 0, "B"), "R41": (34.0, 104.0, 90, "B"), "R42": (37.5, 108.5, 0, "B"),
    "H1": (-52.0, 92.5, 0, "F"), "H2": (52.0, 92.5, 0, "F"),            # baut ke lengan dudukan 3D print
}


def build_sensor(route=True):
    b = Board("ltm-sensor", "LTM - PCB Sensor 16 titik", rev="v2", date="2026-10-13", mech="v12")
    b.rules()
    b.outline(SB_PTS, 2.0)
    for ref, (x, y, r, side) in SENSOR_PLACE.items():
        b.place(ref, x, y, r, side)
    left = sorted(set(b.comps) - set(SENSOR_PLACE))
    if left:
        raise SystemExit(f"komponen belum ditempatkan: {left}")

    T = b.text
    for k, x in enumerate(SX):
        T(str(k + 1), x, F_TIP - 1.3, 0.9, bold=True)
    T("LINE TRACER MICRO  SENSOR 16", 0.0, 118.6, 1.3, bold=True)
    T("MCP23017 (LED)", -30.5, 106.6, 1.0)
    T("MUX 16 KANAL", 11.0, 104.0, 1.0)
    T("KABEL KE PCB UTAMA", 38.4, 107.5, 0.8, 90)
    b.auto_refs(hide=("H1", "H2"))

    if route:
        print("  routing ltm-sensor ...", b.autoroute(100, thin_nets=("GND", "+5V", "/LED_K"), rounds=ROUNDS))
    b.gnd_pour(pcbnew.F_Cu)
    b.gnd_pour(pcbnew.B_Cu)
    rpt = b.fill_and_check()
    b.save()
    return b, rpt


def summary(rpt):
    txt = open(rpt).read()
    kinds = {}
    for k in re.findall(r"^\[(\w+)\]", txt, re.M):
        kinds[k] = kinds.get(k, 0) + 1
    unc = re.search(r"Found (\d+) unconnected", txt)
    return kinds, int(unc.group(1)) if unc else -1


if __name__ == "__main__":
    which = [a for a in sys.argv[1:] if not a.startswith("-")] or ["main", "sensor"]
    route = "--no-route" not in sys.argv
    boards = {}
    for w in which:
        print(f"== {w}")
        brd, rpt = (build_main if w == "main" else build_sensor)(route)
        boards[w] = brd
        kinds, unc = summary(rpt)
        print(f"  DRC: {kinds or 'bersih'}; unconnected: {unc}; laporan: {rpt}")
    if len(boards) == 2:          # kabel pita lurus: pin n J5 = pin n J1
        a, c = boards["main"].pinnet, boards["sensor"].pinnet
        bad = [n for n in map(str, range(1, 13)) if a[("J5", n)].lstrip("/") != c[("J1", n)].lstrip("/")]
        if bad:
            raise SystemExit(f"pin kabel pita tidak cocok: {bad}")
        print("  net pin J5 (utama) = J1 (sensor): cocok")
