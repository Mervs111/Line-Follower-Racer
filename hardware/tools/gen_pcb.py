#!/usr/bin/env python3
"""Generator layout PCB Robot Line Tracer Micro: PCB utama + PCB sensor jangkar (KiCad 7 pcbnew + FreeRouting).

Alur: skematik -> netlist (kicad-cli) -> outline dari model mekanik v11 -> footprint di posisi mekanik
      -> DSN -> FreeRouting (autorouter) -> SES -> jalur & via -> pour GND -> DRC -> .kicad_pcb

Koordinat penempatan di script ini = koordinat model mekanik (mm; X kanan, Y maju, nol = tengah poros
roda), sama dengan mechanical/cadquery/ltm_v11.py. Di KiCad: x = X + OX, y = OY - Y.

Jalankan dengan Python yang punya modul pcbnew (Python bawaan KiCad), butuh kicad-cli, java 21+ dan
FreeRouting (FREEROUTING_JAR):
    python3 hardware/tools/gen_pcb.py            # dua papan
    python3 hardware/tools/gen_pcb.py main       # PCB utama saja
PERINGATAN: menjalankan ulang MENIMPA .kicad_pcb (jalur yang diedit manual hilang).
"""
import math, os, re, shutil, subprocess, sys
import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_kicad import parse  # noqa: E402

HW = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FPDIR = os.environ.get("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
LTM_PRETTY = os.path.join(HW, "ltm-lib", "ltm.pretty")
FREEROUTING = os.environ.get("FREEROUTING_JAR", "/opt/freerouting/freerouting.jar")
JAVA = os.environ.get("JAVA", shutil.which("java") or "java")
WORK = os.environ.get("LTM_WORK", os.path.join(HW, "build"))
OX, OY = 100.0, 150.0
mm = pcbnew.FromMM


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
    def __init__(self, name, title):
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
        tb.SetDate("2026-10-11")
        tb.SetRevision("v1-draft")
        tb.SetCompany("P01 Kel.5 PjBL DTEO FV ITS")
        tb.SetComment(0, "Layout mengikuti mekanik v11; footprint modul SEMENTARA (ukur ulang)")
        tb.SetComment(1, "Jalur dirouting otomatis FreeRouting: routing ulang setelah footprint final")

    # -------------------------------------------------- aturan desain
    def rules(self):
        ds = self.b.GetDesignSettings()
        ds.m_MinClearance = mm(0.2)
        ds.m_TrackMinWidth = mm(0.2)
        ds.m_ViasMinSize = mm(0.5)
        ds.m_MinThroughDrill = mm(0.3)
        ds.m_ViasMinAnnularWidth = mm(0.13)
        ds.m_CopperEdgeClearance = mm(0.3)
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

    def check_pair(self, other, ref_a, ref_b):
        """pastikan pad header antar papan berada di posisi yang sama"""
        for p in self.fps[ref_a].Pads():
            q = next(q for q in other.fps[ref_b].Pads() if q.GetNumber() == p.GetNumber())
            if p.GetPosition() != q.GetPosition():
                raise SystemExit(f"posisi pin {ref_a}.{p.GetNumber()} != {ref_b}.{q.GetNumber()}")

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
        z.SetLocalClearance(mm(0.3))
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(mm(0.4))
        z.SetThermalReliefSpokeWidth(mm(0.5))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        self.b.Add(z)
        return z

    # -------------------------------------------------- routing
    def autoroute(self, passes=40, thin_nets=()):
        """thin_nets: net Power yang dirouting dengan lebar default (mis. GND: nanti dibantu pour)"""
        dsn = os.path.join(WORK, self.name + ".dsn")
        ses = os.path.join(WORK, self.name + ".ses")
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
        cmd = [JAVA, "-jar", FREEROUTING, "-de", dsn, "-do", ses, "-mp", str(passes), "-mt", "1",
               "--gui.enabled=false", "--router.automatic_neckdown=false"]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=WORK)
        open(os.path.join(WORK, self.name + ".freerouting.log"), "w").write(r.stdout + r.stderr)
        if not os.path.exists(ses):
            raise SystemExit("FreeRouting tidak menghasilkan SES, lihat log di " + WORK)
        return import_ses(self, ses)

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
                width = max(mm(float(path[2]) * scale), mm(0.2))
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
# outline = MAIN_PTS di mechanical/cadquery/ltm_v11.py (fillet 2,5)
MAIN_PTS = [(-36, 8), (36, 8), (36, 18), (47, 22), (47, 62), (28, 86), (13, 92), (-13, 92), (-28, 86),
            (-47, 62), (-47, 22), (-36, 18)]
HOLES_MAIN = {"H1": (-32, 16), "H2": (32, 16),          # standoff ke dudukan baterai (sama dengan model)
              "H3": (-37.5, 69), "H4": (37.5, 69),      # bahu depan
              "H5": (-10.5, 83), "H6": (10.5, 83)}      # spacer ke PCB sensor
MAIN_PLACE = {
    # ref: (X, Y, rotasi)  = posisi ORIGIN footprint (pin 1 untuk konektor), koordinat mekanik
    "U1": (3.5, 28.0, 90),      # ESP32 melintang, USB ke kanan (+X); baris pin 1-15 di belakang
    "U2": (-33.85, 54.15, 270),  # TB6612: baris belakang = VM/VCC/GND/output, baris depan = input
    "U3": (34.0, 52.5, 180),    # MP1584: OUT di kiri, IN di kanan
    "J4": (3.81, 45.45, 270),   # socket OLED (header OLED di sisi belakang)
    "J5": (-5.08, 81.23, 90),   # lubang tembus pin header PCB sensor
    "SW2": (-23.25, 85.25, 0), "SW3": (16.75, 85.25, 0),
    "BZ1": (23.7, 71.5, 0),
    "J2": (-27.0, 11.3, 0), "J3": (17.0, 11.3, 0),           # motor kiri / kanan
    "SW1": (-44.8, 30.2, 270),  # saklar geser di tepi kiri, tuas keluar ke -X
    "J1": (-44.1, 37.0, 90),    # baterai (dari BMS), tepi kiri di luar dudukan baterai
    "D1": (20.5, 48.5, 270),
    "C1": (-30.25, 69.0, 0), "C2": (-20.2, 45.5, 90), "C6": (-20.2, 53.5, 90),
    "R1": (28.0, 42.67, 270), "R2": (31.3, 35.05, 90), "C5": (34.6, 36.0, 90), "C4": (37.9, 36.0, 90),
    "C3": (42.0, 39.0, 0),
    "Q1": (11.0, 66.0, 0), "R3": (4.0, 61.0, 0), "R4": (4.0, 57.0, 0),       # di bawah OLED (socket 8,5 mm)
    "R5": (-14.0, 62.0, 90), "R6": (-11.0, 62.0, 90), "R7": (-8.0, 62.0, 90), "R8": (-5.0, 62.0, 90),
    **{k: (x, y, 0) for k, (x, y) in HOLES_MAIN.items()},
}
ANTENNA = (-26.0, 14.0, -18.5, 42.0)       # ujung antena ESP32 (X0, Y0, X1, Y1)


def build_main(route=True):
    b = Board("ltm-main", "LTM - PCB Utama")
    b.rules()
    b.outline(MAIN_PTS, 2.5)
    for ref, (x, y, r) in MAIN_PLACE.items():
        b.place(ref, x, y, r)
    left = sorted(set(b.comps) - set(MAIN_PLACE))
    if left:
        raise SystemExit(f"komponen belum ditempatkan: {left}")
    x0, y0, x1, y1 = ANTENNA
    b.keepout(x0, y0 + 4, x1, y1 - 4, "antena ESP32")                 # tanpa jalur, via, pour

    # ---- silkscreen
    T = b.text
    T("P01 KEL.5", -36.0, 27.0, 1.6, 90, bold=True)
    T("LINE TRACER MICRO  v1", -33.0, 29.0, 1.0, 90)
    T("A", -26.5, 83.0, 1.6, bold=True)
    T("B", 26.5, 83.0, 1.6, bold=True)
    T("PWR", -39.6, 28.2, 0.9)
    T("+", -39.0, 37.0, 1.3, bold=True)
    T("-", -39.0, 39.5, 1.3, bold=True)
    T("BAT", -39.0, 41.9, 0.9)
    T("ML", -31.5, 9.9, 0.9)
    T("MR", 31.5, 9.9, 0.9)
    for i, s in enumerate(("GND", "VCC", "SCL", "SDA")):
        T(s, 3.81 - 2.54 * i, 48.1, 0.8)
    T("OLED", 0.0, 50.0, 1.0)
    T("ESP32 DEVKIT 30P", 0.0, 32.0, 1.2)
    T("USB >", 22.6, 28.0, 1.0, 90)
    T("TB6612", -33.85, 51.0, 1.2)
    T("MP1584 5V", 34.0, 55.5, 1.0)
    T("OUT", 26.6, 52.5, 0.9)
    T("IN", 41.6, 52.5, 0.9)
    T("SENSOR", 0.0, 87.6, 0.8)
    b.auto_refs(hide=tuple(HOLES_MAIN) + ("J5",), inside=("U1", "U2", "U3"))

    if route:
        print("  routing ltm-main ...", b.autoroute(40, thin_nets=("GND",)))
    b.keepout(*ANTENNA, "antena ESP32 (tanpa pour)", tracks=False)
    b.gnd_pour(pcbnew.F_Cu)
    b.gnd_pour(pcbnew.B_Cu)
    rpt = b.fill_and_check()
    b.save()
    return b, rpt


# ================================================================== PCB SENSOR
F_TIP = 132.0
# outline = R_HALF di ltm_v11.py; pangkal leher dilebarkan ke ±14 untuk lubang spacer (fillet 1,2)
SB_HALF = [(0, F_TIP), (26, F_TIP - 2), (46, F_TIP - 30), (32.5, F_TIP - 30), (20, F_TIP - 12.6),
           (7, F_TIP - 11.6), (7, 90), (14, 90), (14, 79)]
SB_PTS = SB_HALF[:-1] + [(14, 79)] + [(-x, y) for x, y in reversed(SB_HALF)][:-1]
SENS = [(-20, F_TIP - 8.0, 6), (-10, F_TIP - 6.0, 4), (0, F_TIP - 4.5, 0), (10, F_TIP - 6.0, -4),
        (20, F_TIP - 8.0, -6)]
SENSOR_PLACE = {
    # ref: (X, Y, rotasi, sisi)
    "J1": (-5.08, 81.23, 90, "F"),          # pin header male, pin panjang ke atas menembus J5 PCB utama
    "H1": (-10.5, 83, 0, "F"), "H2": (10.5, 83, 0, "F"),
    "C1": (0, 87.6, 0, "B"),
    "Q1": (0, 92.2, 0, "B"), "R11": (-4.3, 92.2, 90, "B"), "R12": (4.3, 92.2, 90, "B"),
    **{f"U{i + 1}": (x, y, a, "B") for i, (x, y, a) in enumerate(SENS)},   # sensor menghadap lantai
    **{f"R{1 + i}": (-3.4, 113.0 - 4.0 * i, 90, "B") for i in range(5)},  # 180R LED, R1 paling atas
    **{f"R{10 - i}": (3.4, 113.0 - 4.0 * i, 90, "B") for i in range(5)},  # 10k pull-up, R10 paling atas
}


def build_sensor(route=True):
    b = Board("ltm-sensor", "LTM - PCB Sensor Jangkar")
    b.rules()
    b.outline(SB_PTS, 1.2)
    for ref, (x, y, r, side) in SENSOR_PLACE.items():
        b.place(ref, x, y, r, side)
    left = sorted(set(b.comps) - set(SENSOR_PLACE))
    if left:
        raise SystemExit(f"komponen belum ditempatkan: {left}")

    T = b.text
    T("LINE TRACER MICRO", 0.0, 106.0, 1.5, 90, bold=True)
    for i, (x, y, a) in enumerate(SENS):
        T(str(i + 1), x - 4.3, y, 1.2, bold=True)
    T("P01 KEL.5", -33.5, 110.0, 1.3, 54.4, bold=True)
    T("PjBL DTEO ITS", 33.5, 110.0, 1.1, -54.4)
    b.auto_refs(hide=("H1", "H2"))
    b.no_track_between_pads(("R", "C"))

    if route:
        print("  routing ltm-sensor ...", b.autoroute(40, thin_nets=("GND",)))
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
    if len(boards) == 2:
        boards["main"].check_pair(boards["sensor"], "J5", "J1")
        print("  posisi pin J5 (utama) = J1 (sensor): cocok")
