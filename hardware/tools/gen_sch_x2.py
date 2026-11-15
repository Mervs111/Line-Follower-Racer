"""Membuat skematik LFM X2 rev B: 4 papan gaya Ichibot Ultimate 5 Max, tiap papan proyek KiCad 10 sendiri.

LFM X2 = side project di luar RAB PjBL. Rev B (keputusan user 15/11/2026) memecah PCB all-in-one rev A menjadi:
  utama      hardware/lfm-x2/utama/      segitiga: ESP32-WROOM-32E, CH340C + USB-C, buck MP1584EN + LDO, saklar daya,
                                         konektor ke tiga papan lain. Sebagian besar komponen di sisi bawah.
  antarmuka  hardware/lfm-x2/antarmuka/  ditumpuk di atas papan utama: OLED 0,96" di socket, 6 tombol menu, RST, buzzer
  driver     hardware/lfm-x2/driver/     di bawah papan utama: 4x BTN7971B, konektor motor + encoder
  sensor     hardware/lfm-x2/sensor/     bulan sabit + leher garpu: 12 pasang LED IR + fototransistor PT67-21B, mux
Urutan pin konektor antar-papan ditulis sekali (KONEKTOR) dan dipakai kedua sisi.

Gaya gambar sama dengan rev A (mesin gambar dari gen_sch_utama.py): tiap pin diberi kabel pendek lalu label global
(nama sama = tersambung) atau simbol daya; rangkaian kecil (pembagi tegangan, buzzer) digambar dengan kabel.

Jalankan dari folder repo: py hardware/tools/gen_sch_x2.py [papan ...] [--paksa]
Tanpa nama papan = keempatnya. Tanpa --paksa skrip menolak menimpa skematik yang sudah berisi simbol (supaya suntingan
user tidak hilang); UUID simbol dipertahankan antar-jalan. Sesudahnya: py hardware/tools/cek_net_x2.py
"""
import json
import math
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kisym  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
X2 = os.path.join(ROOT, "hardware", "lfm-x2")      # pustaka bersama lfm-x2.kicad_sym + lfm-x2.pretty ada di sini
POWER = {"+5V": "power:+5V", "+3V3": "power:+3V3", "GND": "power:GND"}
STUB = 2.54

FP_R = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
FP_C = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_C1206 = "Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder"
FP_SOT23 = "Package_TO_SOT_SMD:SOT-23"
FP_SMA = "Diode_SMD:D_SMA"
FP_BTN = "Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92"
FP_TO263 = "Package_TO_SOT_SMD:TO-263-7_TabPin8"
FP_PLCC2 = "lfm-x2:PLCC-2_3528_HandSolder"

# ============================== KONEKTOR ANTAR-PAPAN ==============================
# nomor pin -> net. Papan utama memakai socket (betina), papan lain header (jantan), urutan sama.
KONEKTOR = {
    # FFC 1,0 mm 8 pin, urutan = J1 PCB sensor rev B jalur utama
    "sensor": {"1": "+5V", "2": "+3V3", "3": "GND", "4": "MUX_S3", "5": "MUX_S2", "6": "MUX_S1", "7": "MUX_S0",
               "8": "MUX_SIG", "MP": "GND"},
    # 2x5 2,54 mm: socket di sisi atas papan utama, header di sisi bawah papan antarmuka
    "antarmuka": {"1": "+5V", "2": "+3V3", "3": "GND", "4": "GND", "5": "SDA", "6": "SCL", "7": "BTN", "8": "BTN2",
                  "9": "BUZ", "10": "EN"},
    # 2x7 2,54 mm: socket di sisi bawah papan utama, header di sisi atas papan driver. VBAT 2 pin + GND 2 pin (3 A/pin)
    "driver": {"1": "VBAT", "2": "VBAT", "3": "GND", "4": "GND", "5": "ML_IN1", "6": "ML_IN2", "7": "MR_IN1",
               "8": "MR_IN2", "9": "DRV_EN", "10": "+3V3", "11": "ENC_L_A", "12": "ENC_L_B", "13": "ENC_R_A",
               "14": "ENC_R_B"},
}
FP_FFC = "Connector_FFC-FPC:JUSHUO_AFA07-S08FCA-00_1x8-1MP_P1.0mm_Horizontal"


def uid():
    return str(uuid.uuid4())


def f(v):
    """angka koordinat: dibulatkan ke 0,01 mm, tanpa nol berlebih"""
    s = f"{round(v, 4):.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


LIB = {}


def lib(lib_id):
    if lib_id not in LIB:
        LIB[lib_id] = kisym.load(lib_id, [X2])
    return LIB[lib_id]


def rot(x, y, r):
    """putar vektor koordinat library (Y ke atas) berlawanan jarum jam"""
    a = math.radians(r)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def to_sch(X, Y, lx, ly, r=0):
    """titik library -> skematik (Y ke bawah)"""
    rx, ry = rot(lx, ly, r)
    return round(X + rx, 4), round(Y - ry, 4)


def outward(q):
    """arah keluar pin (derajat, Y ke atas): kebalikan arah pin menuju badan simbol"""
    return (q["ang"] + 180) % 360


def eff(size=1.27, justify=None, hide=False, bold=False):
    j = f" (justify {justify})" if justify else ""
    b = " (bold yes)" if bold else ""
    h = " (hide yes)" if hide else ""
    return f"(effects (font (size {size} {size}){b}){j}{h})"


def lib_prop(blk, name):
    m = re.search(r'\(property "%s" "([^"]*)"\s*\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)' % name, blk)
    return (m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4) or 0)) if m else ("", 0, 0, 0)


class Skematik:
    """satu papan: daftar komponen + gambar + file proyek"""

    def __init__(self, nama, judul, kertas, kelas):
        self.nama, self.judul, self.kertas = nama, judul, kertas
        self.kelas = kelas                         # net class: {"Daya": [...], "Daya besar": [...]}
        self.dir = os.path.join(X2, nama)
        self.project = f"lfm-x2-{nama}"
        self.path = os.path.join(self.dir, self.project + ".kicad_sch")
        self.parts, self.nomor, self.blocks, self.manual = [], {}, [], {}
        self.wires, self.juncs, self.labels, self.ncs, self.powers = [], [], [], [], []
        self._peta = None

    # ---------------------------------------------------------------- daftar komponen
    # nets: nomor pin -> nama net | "NC" (tanda X) | None (disambung manual)
    #       atau dict(net=..., lang=sudut label, pdir=arah badan simbol daya (derajat), len=panjang kabel)
    def part(self, ref, lib_id, value, fp, x, y, nets, fields="lib"):
        self.parts.append(dict(ref=ref, lib_id=lib_id, value=value, fp=fp, x=x, y=y, nets=nets, fields=fields))
        self._peta = None
        return ref

    def auto(self, awalan):
        self.nomor[awalan] = self.nomor.get(awalan, 0) + 1
        return f"{awalan}{self.nomor[awalan]}"

    def R(self, value, atas, bawah, x, y):
        """resistor tegak: pin 1 di atas, pin 2 di bawah"""
        return self.part(self.auto("R"), "Device:R", value, FP_R, x, y, {"1": atas, "2": bawah}, fields="right")

    def C(self, value, atas, bawah, x, y, fp=FP_C, lib_id="Device:C"):
        return self.part(self.auto("C"), lib_id, value, fp, x, y, {"1": atas, "2": bawah}, fields="right")

    # ---------------------------------------------------------------- gambar
    def pin(self, ref, num):
        if self._peta is None:
            self._peta = {p["ref"]: p for p in self.parts}
            if len(self._peta) != len(self.parts):
                raise SystemExit(f"{self.nama}: referensi kembar")
        p = self._peta[ref]
        for q in lib(p["lib_id"])[1]:
            if q["num"] == num:
                return to_sch(p["x"], p["y"], q["x"], q["y"])
        raise KeyError((ref, num))

    def wire(self, a, b):
        self.wires.append((a, b))

    def label(self, net, at, ang):
        self.labels.append((net, at, ang % 360))

    def power(self, net, at, body_dir, lib_id=None):
        """simbol daya di titik at; badan simbol menunjuk ke body_dir (derajat, Y ke atas)"""
        lid = lib_id or POWER[net]
        base = 270 if net == "GND" else 90         # arah badan simbol di library
        self.powers.append((lid, at, (body_dir - base) % 360))

    def attach(self, at, d, spec):
        if isinstance(spec, str):
            spec = {"net": spec}
        net = spec["net"]
        ln = spec.get("len", STUB)
        end = (round(at[0] + ln * math.cos(math.radians(d)), 4), round(at[1] - ln * math.sin(math.radians(d)), 4))
        self.wire(at, end)
        if net in POWER:
            self.power(net, end, spec.get("pdir", d))
        else:
            self.label(net, end, spec.get("lang", d if d in (0, 180) else 0))

    def sambung(self):
        """kabel pendek + label/simbol daya untuk semua pin yang diberi net"""
        for p in self.parts:
            sudah = set()                          # pin bertumpuk (VBUS/GND USB-C, OUT BTN7971B): satu kabel saja
            for q in lib(p["lib_id"])[1]:
                spec = p["nets"].get(q["num"], "MISSING")
                if spec == "MISSING":
                    raise SystemExit(f"{self.nama}: pin {p['ref']}.{q['num']} ({q['name']}) belum diberi net")
                at = to_sch(p["x"], p["y"], q["x"], q["y"])
                if spec is None:
                    continue
                kunci = (at, spec if isinstance(spec, str) else spec["net"])
                if kunci in sudah:
                    continue
                sudah.add(kunci)
                if spec == "NC":
                    self.ncs.append(at)
                    continue
                self.attach(at, outward(q), spec)
            lebih = set(p["nets"]) - {q["num"] for q in lib(p["lib_id"])[1]}
            if lebih:
                raise SystemExit(f"{p['ref']}: pin tidak ada di simbol: {sorted(lebih)}")

    def pembagi(self, r_atas, r_bawah, net, dx=5.08):
        """dua resistor tegak bersusun: titik tengah diberi label net"""
        a, b = self.pin(r_atas, "2"), self.pin(r_bawah, "1")
        mid = (a[0], round((a[1] + b[1]) / 2 / 1.27) * 1.27)
        self.wire(a, mid), self.wire(mid, b), self.juncs.append(mid)
        self.wire(mid, (mid[0] + dx, mid[1])), self.label(net, (mid[0] + dx, mid[1]), 0)
        self.manual.update({f"{r_atas}.2": net, f"{r_bawah}.1": net})

    def buzzer(self, rb, rp, q, bz):
        """BUZ - rb - basis q, rp basis ke GND, kolektor ke kaki - buzzer"""
        r3b, qb, r4t = self.pin(rb, "2"), self.pin(q, "1"), self.pin(rp, "1")
        k1 = (r3b[0], qb[1])
        self.wire(r3b, k1), self.wire(k1, (r4t[0], qb[1])), self.wire((r4t[0], qb[1]), qb)
        self.wire((r4t[0], qb[1]), r4t)
        self.juncs.append((r4t[0], qb[1]))
        qc, bzn = self.pin(q, "3"), self.pin(bz, "2")
        self.wire(bzn, (qc[0], bzn[1])), self.wire((qc[0], bzn[1]), qc)
        self.manual.update({f"{rb}.2": "*basis", f"{rp}.1": "*basis", f"{q}.1": "*basis", f"{q}.3": "*buzzer",
                            f"{bz}.2": "*buzzer"})           # *nama = net tanpa label (harus satu net)

    def flag(self, nets, x, y, dy=7.62):
        """PWR_FLAG berderet untuk net yang dayanya datang dari konektor/MOSFET/dioda, bukan pin keluaran daya"""
        for i, net in enumerate(nets):
            fl = (x, y + i * dy)
            self.powers.append(("power:PWR_FLAG", fl, 0))
            self.wire(fl, (fl[0] + 10.16, fl[1]))
            if net in POWER:
                self.power(net, (fl[0] + 10.16, fl[1]), 270 if net == "GND" else 90)
            else:
                self.label(net, (fl[0] + 10.16, fl[1]), 0)

    # ---------------------------------------------------------------- file
    def symbol(self, root_uuid, old_uuid, lib_id, ref, value, fp, X, Y, r=0, fields="lib", hide_ref=False,
               hide_val=False):
        blk, pins = lib(lib_id)
        _, rx, ry, ra = lib_prop(blk, "Reference")
        _, vx, vy, va = lib_prop(blk, "Value")
        ds = lib_prop(blk, "Datasheet")[0]
        if isinstance(fields, dict):               # posisi sendiri: {"ref": (dx, dy), "val": (dx, dy)}, rata kiri
            rp, vp = (X + fields["ref"][0], Y + fields["ref"][1]), (X + fields["val"][0], Y + fields["val"][1])
            ang, just = 0, "left"
        elif fields in ("right", "right_far"):
            dx = 2.54 if fields == "right" else 5.08
            rp, vp, ang, just = (X + dx, Y - 1.27), (X + dx, Y + 1.27), 0, "left"
        elif r in (90, 270):
            # simbol daya menyamping: teks nilai mendatar di ujung badan simbol (sudut field ikut putaran simbol)
            bd = math.radians(r + (270 if value == "GND" else 90))
            d = 3.0 + 0.55 * len(value)
            rp = vp = (round(X + d * math.cos(bd), 4), round(Y - d * math.sin(bd), 4))
            ang, just = r, None
        else:
            rp, vp = to_sch(X, Y, rx, ry, r), to_sch(X, Y, vx, vy, r)
            ang, just = 0, None
        s = [f'\t(symbol (lib_id "{lib_id}") (at {f(X)} {f(Y)} {f(r)}) (unit 1)',
             '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)',
             f'\t\t(uuid "{old_uuid.get(ref) or uid()}")',
             f'\t\t(property "Reference" "{ref}" (at {f(rp[0])} {f(rp[1])} {ang}) {eff(justify=just, hide=hide_ref)})',
             f'\t\t(property "Value" "{value}" (at {f(vp[0])} {f(vp[1])} {ang}) {eff(justify=just, hide=hide_val)})',
             f'\t\t(property "Footprint" "{fp}" (at {f(X)} {f(Y)} 0) {eff(hide=True)})',
             f'\t\t(property "Datasheet" "{ds}" (at {f(X)} {f(Y)} 0) {eff(hide=True)})']
        for q in pins:
            s.append(f'\t\t(pin "{q["num"]}" (uuid "{uid()}"))')
        s.append(f'\t\t(instances (project "{self.project}" (path "/{root_uuid}" (reference "{ref}") (unit 1))))')
        s.append("\t)")
        return "\n".join(s)

    def tulis(self, paksa):
        old = open(self.path, encoding="utf8").read() if os.path.exists(self.path) else ""
        m_uuid = re.search(r'\(uuid "([^"]+)"\)', old)
        root_uuid = m_uuid.group(1) if m_uuid else uid()
        if "(lib_id" in old and not paksa:
            raise SystemExit(f"{self.path} sudah berisi simbol; pakai --paksa kalau memang mau ditimpa")
        # UUID simbol dipertahankan (kunci = referensi): footprint di PCB terikat ke UUID ini (F8 tidak membuat ulang)
        old_uuid = {}
        for m in re.finditer(r'\(symbol\s+\(lib_id "[^"]*"\).*?\(uuid "([^"]+)"\)\s*\(property "Reference" "([^"]+)"',
                             old, re.S):
            old_uuid[m.group(2)] = m.group(1)

        out = []
        used = sorted({p["lib_id"] for p in self.parts} | {lid for lid, _, _ in self.powers})
        out.append("(kicad_sch\n\t(version 20260306)\n\t(generator \"eeschema\")\n\t(generator_version \"10.0\")")
        out.append(f'\t(uuid "{root_uuid}")\n\t(paper "{self.kertas}")')
        out.append(f'\t(title_block\n\t\t(title "LFM X2 rev B - {self.judul}")\n\t\t(date "2026-11-15")\n\t\t(rev "B")\n'
                   '\t\t(company "Side project LFM (di luar RAB PjBL)")\n'
                   '\t\t(comment 1 "Penjelasan, BOM, dan catatan routing: hardware/lfm-x2/README.md")\n'
                   '\t\t(comment 2 "Dibuat oleh hardware/tools/gen_sch_x2.py")\n\t)')
        out.append("\t(lib_symbols\n" + "\n".join(lib(u)[0] for u in used) + "\n\t)")
        for x0, y0, x1, y1, title, notes in self.blocks:
            out.append(f'\t(rectangle (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width 0.254) (type dash)) '
                       f'(fill (type none)) (uuid "{uid()}"))')
            out.append(f'\t(text "{title}" (exclude_from_sim no) (at {f(x0 + 2.54)} {f(y0 + 5.08)} 0) '
                       f'{eff(2.0, "left", bold=True)} (uuid "{uid()}"))')
            for tx, ty, t in notes:
                t = t.replace("\n", "\\n")
                out.append(f'\t(text "{t}" (exclude_from_sim no) (at {f(tx)} {f(ty)} 0) {eff(1.27, "left")} '
                           f'(uuid "{uid()}"))')
        for p in self.parts:
            out.append(self.symbol(root_uuid, old_uuid, p["lib_id"], p["ref"], p["value"], p["fp"], p["x"], p["y"],
                                   fields=p["fields"]))
        npwr = nflg = 0
        for lid, at, r in self.powers:
            if lid == "power:PWR_FLAG":
                nflg += 1
                ref = f"#FLG{nflg:02d}"
            else:
                npwr += 1
                ref = f"#PWR{npwr:03d}"
            out.append(self.symbol(root_uuid, old_uuid, lid, ref, lid.split(":")[1], "", at[0], at[1], r,
                                   hide_ref=True))
        for a, b in self.wires:
            out.append(f'\t(wire (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})) (stroke (width 0) '
                       f'(type default)) (uuid "{uid()}"))')
        for j in self.juncs:
            out.append(f'\t(junction (at {f(j[0])} {f(j[1])}) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))')
        for at in self.ncs:
            out.append(f'\t(no_connect (at {f(at[0])} {f(at[1])}) (uuid "{uid()}"))')
        for net, at, ang in self.labels:
            just = "left" if ang in (0, 90) else "right"
            out.append(f'\t(global_label "{net}" (shape passive) (at {f(at[0])} {f(at[1])} {ang}) '
                       f'(fields_autoplaced yes) {eff(justify=just)} (uuid "{uid()}"))')
        out.append('\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n')
        os.makedirs(self.dir, exist_ok=True)
        open(self.path, "w", encoding="utf8", newline="\n").write("\n".join(out))
        print(f"ditulis {self.path}: {len(self.parts)} komponen, {len(self.labels)} label, {len(self.wires)} kabel, "
              f"{len(self.ncs)} NC")

        # daftar net yang diharapkan (dibandingkan dengan netlist KiCad oleh cek_net_x2.py): "REF.PIN" -> net
        harap = dict(self.manual)
        for p in self.parts:
            for num, spec in p["nets"].items():
                if isinstance(spec, dict):
                    spec = spec["net"]
                if spec and spec != "NC":
                    for n in (num.strip("[]").split(",") if num.startswith("[") else [num]):
                        harap[f"{p['ref']}.{n}"] = spec
        with open(os.path.join(self.dir, "net-harapan.json"), "w", encoding="utf8", newline="\n") as fh:
            json.dump(dict(sorted(harap.items())), fh, indent=1)
        self.file_proyek(root_uuid)

    def file_proyek(self, root_uuid):
        """dibuat sekali (tidak ditimpa): tabel pustaka, .kicad_pro (aturan cetak dari PCB utama), .kicad_dru"""
        tabel = os.path.join(self.dir, "sym-lib-table")
        if not os.path.exists(tabel):
            open(tabel, "w", encoding="utf8", newline="\n").write(
                '(sym_lib_table\n  (version 7)\n  (lib (name "lfm-x2")(type "KiCad")'
                '(uri "${KIPRJMOD}/../lfm-x2.kicad_sym")(options "")(descr "LFM X2: BTN7971B, CH340C 3,3 V, MP1584EN"))\n)\n')
        tabel = os.path.join(self.dir, "fp-lib-table")
        if not os.path.exists(tabel):
            open(tabel, "w", encoding="utf8", newline="\n").write(
                '(fp_lib_table\n  (version 7)\n  (lib (name "lfm-x2")(type "KiCad")'
                '(uri "${KIPRJMOD}/../lfm-x2.pretty")(options "")(descr "LFM X2: PLCC-2 3528 solder tangan"))\n)\n')
        dru = os.path.join(self.dir, self.project + ".kicad_dru")
        if not os.path.exists(dru):
            open(dru, "w", encoding="utf8", newline="\n").write(DRU.get(self.nama, DRU["dasar"]))
        pro_path = os.path.join(self.dir, self.project + ".kicad_pro")
        if os.path.exists(pro_path):
            return
        pro = json.load(open(os.path.join(ROOT, "hardware", "pcb-utama", "pcb-utama.kicad_pro"), encoding="utf8"))
        pro["meta"]["filename"] = self.project + ".kicad_pro"
        ns = pro["net_settings"]
        dasar = {k: v for k, v in ns["classes"][1].items() if k not in ("name", "track_width")}
        lebar = {"Daya": 0.5, "Daya besar": 1.2}
        ns["classes"] = [ns["classes"][0]] + [dict(dasar, name=k, track_width=lebar[k]) for k in self.kelas]
        ns["netclass_patterns"] = [{"netclass": k, "pattern": n} for k, nets in self.kelas.items() for n in nets]
        ds = pro["board"]["design_settings"]
        ds["track_widths"] = [0.0, 0.3, 0.5, 1.2, 2.0]
        ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 1.3, "drill": 0.6}]
        pro["sheets"] = [[root_uuid, "Root"]]
        pro["schematic"]["top_level_sheets"] = [{"filename": self.project + ".kicad_sch", "name": "Root",
                                                 "uuid": root_uuid}]
        pro["schematic"].pop("used_designators", None)
        json.dump(pro, open(pro_path, "w", encoding="utf8", newline="\n"), indent=2)
        print(f"ditulis {pro_path}")


DRU = {
    "dasar": """(version 1)

# Aturan tempat cetak (21/10/2026): jarak tembaga ke ground pour minimal 0,5 mm
(rule "jarak_ke_pour"
  (condition "A.Type == 'Zone'")
  (constraint clearance (min 0.5mm)))
""",
}
DRU["utama"] = DRU["dasar"] + """
# U4 MP1584EN (SOIC-8 dengan pad bawah): pad bawah ke kaki 0,295 mm. Di atas batas tempat cetak (0,254), hanya di
# bawah angka proyek (0,3).
(rule "u4_pad_bawah"
  (condition "A.Type == 'Pad' && B.Type == 'Pad' && A.intersectsCourtyard('U4') && B.intersectsCourtyard('U4')")
  (constraint clearance (min 0.254mm)))

# J2 USB-C 16 pin: pad 0,3 mm jarak 0,5 mm, jadi celah antar pad 0,2 mm, DI BAWAH batas tempat cetak (0,254).
# Sengaja dibiarkan muncul sebagai peringatan sampai tempat cetak memastikan sanggup, atau konektor diganti.
(rule "usb_c_celah_pad_0,2"
  (severity warning)
  (condition "A.Type == 'Pad' && B.Type == 'Pad' && A.intersectsCourtyard('J2') && B.intersectsCourtyard('J2')")
  (constraint clearance (min 0.3mm)))

# Jalur fanout J2 (x2_router.py fanout): jalur 0,3 mm keluar lurus dari ujung pad, jadi celah ke pad/jalur tetangga
# 0,2-0,25 mm sepanjang +-0,6 mm pertama, sama dengan celah antar pad konektor. Peringatan, alasan sama.
(rule "usb_c_fanout_0,2"
  (severity warning)
  (condition "A.Type == 'Track' && A.intersectsCourtyard('J2') && B.intersectsCourtyard('J2')")
  (constraint clearance (min 0.3mm)))

# SW1 dan kaki pelindung J2 (pad THT GND di tepi kanan yang padat): satu jari thermal ke pour sudah cukup, GND juga
# sampai lewat jalur
(rule "thermal_satu_jari"
  (condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole' && (A.intersectsCourtyard('SW1') || A.intersectsCourtyard('J2'))")
  (constraint min_resolved_spokes 1))
"""


# ============================== PAPAN UTAMA ==============================
def utama():
    b = Skematik("utama", "papan utama (ESP32, USB, daya)", "A2",
                 {"Daya": ["+5V", "+3V3", "GND", "+5V_BUCK", "VBUS"], "Daya besar": ["VBAT", "BAT+", "BUCK_SW"]})
    # ---- 1. DAYA ----
    # XT30PW-M (jantan, pack XT30 betina): pin 1 = sisi bersudut miring = negatif, pin 2 = sisi rata = positif
    # (gambar AMASS + tanda +/- footprint KiCad)
    b.part("J1", "Connector_Generic:Conn_01x02", "LiPo 2S XT30",
           "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal", 38.1, 43.18, {"1": "GND", "2": "BAT+"})
    # saklar daya: SW1 hanya mengalirkan arus gate Q1 (AO3401A, P-MOSFET sisi atas). R1 menahan gate di BAT+ (mati),
    # R2 menariknya ke GND saat SW1 hidup: Vgs = -VBAT x 100/110 = -7,6 V pada 8,4 V (batas Vgs AO3401A 12 V, jadi
    # hanya untuk 2S). C1 x R2 = 1 ms memperlambat nyala.
    b.part("Q1", "Transistor_FET:AO3401A", "AO3401A", FP_SOT23, 71.12, 43.18, {"1": "PWR_G", "2": "BAT+", "3": "VBAT"},
           fields="right_far")
    b.R("100k", "BAT+", "PWR_G", 96.52, 43.18)                                              # R1
    b.C("100nF", "BAT+", "PWR_G", 119.38, 43.18)                                            # C1
    b.R("10k", "PWR_G", "PWR_SW", 142.24, 43.18)                                            # R2
    b.part("SW1", "Switch:SW_SPDT", "Saklar daya", "Button_Switch_THT:SW_Slide_SPDT_Angled_CK_OS102011MA1Q",
           170.18, 43.18, {"2": "PWR_SW", "1": "GND", "3": "NC"})
    r_vb = b.R("100k", "VBAT", None, 226.06, 35.56)
    r_vg = b.R("33k", None, "GND", 226.06, 50.8)
    b.C("100nF", "VBAT_SENSE", "GND", 254.0, 43.18)
    b.pembagi(r_vb, r_vg, "VBAT_SENSE")

    b.part("U4", "lfm-x2:MP1584EN", "MP1584EN", "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm", 50.8, 91.44,
           {"7": "VBAT", "2": "NC", "6": "BUCK_FREQ", "8": "BUCK_BST", "1": "BUCK_SW", "4": "BUCK_FB", "3": "BUCK_COMP",
            "5": None, "9": None})
    b.C("10uF 25V", "VBAT", "GND", 91.44, 91.44, FP_C1206)
    b.C("100nF", "VBAT", "GND", 109.22, 91.44)
    b.R("100k", "BUCK_FREQ", "GND", 127.0, 91.44)
    b.C("100nF", "BUCK_BST", "BUCK_SW", 149.86, 91.44)
    b.part("D1", "Device:D_Schottky", "SS34", FP_SMA, 180.34, 91.44, {"1": "BUCK_SW", "2": "GND"})
    b.part("L1", "Device:L", "15uH 2A", "Inductor_SMD:L_Sumida_CR75", 203.2, 91.44,
           {"1": "BUCK_SW", "2": "+5V_BUCK"}, fields="right")
    b.C("22uF 16V", "+5V_BUCK", "GND", 228.6, 91.44, FP_C1206)
    r_fa = b.R("220k", "+5V_BUCK", None, 254.0, 83.82)
    r_fb = b.R("39k", None, "GND", 254.0, 99.06)
    b.pembagi(r_fa, r_fb, "BUCK_FB")
    r_cp = b.R("100k", "BUCK_COMP", None, 276.86, 83.82)
    c_cp = b.C("150pF", None, "GND", 276.86, 99.06)
    b.wire(b.pin(r_cp, "2"), b.pin(c_cp, "1"))                 # kompensasi buck: R seri C
    b.manual.update({f"{r_cp}.2": "*kompensasi", f"{c_cp}.1": "*kompensasi"})
    g5, g9 = b.pin("U4", "5"), b.pin("U4", "9")                # GND dan pad bawah MP1584: satu simbol GND
    b.wire(g5, (g5[0], g5[1] + STUB)), b.wire(g9, (g9[0], g9[1] + STUB))
    b.wire((g5[0], g5[1] + STUB), (g9[0], g9[1] + STUB))
    b.power("GND", (g5[0], g5[1] + STUB), 270)
    b.manual.update({"U4.5": "GND", "U4.9": "GND"})

    b.part("D2", "Device:D_Schottky", "SS14", FP_SMA, 38.1, 134.62, {"1": "+5V", "2": "+5V_BUCK"})
    b.part("D3", "Device:D_Schottky", "SS14", FP_SMA, 78.74, 134.62, {"1": "+5V", "2": "VBUS"})
    b.part("U3", "Regulator_Linear:AMS1117-3.3", "AMS1117-3.3", "Package_TO_SOT_SMD:SOT-223-3_TabPin2", 127.0, 132.08,
           {"3": "+5V", "2": "+3V3", "1": "GND"}, fields={"ref": (-5.08, -7.62), "val": (-5.08, -5.08)})
    b.C("10uF 25V", "+5V", "GND", 154.94, 134.62, FP_C1206)
    b.C("22uF 16V", "+3V3", "GND", 175.26, 134.62, FP_C1206)
    b.C("100nF", "+3V3", "GND", 195.58, 134.62)
    b.R("1k", "+3V3", "LED_A", 215.9, 129.54)
    b.part("LED1", "Device:LED", "LED hijau", "LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder",
           241.3, 139.7, {"2": "LED_A", "1": "GND"})
    b.flag(["VBAT", "+5V", "GND"], 266.7, 127.0)

    # ---- 2. ESP32 + USB ----
    b.part("J2", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C 16 pin",
           "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", 35.56, 218.44,
           {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND",
            "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2",
            "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM", "A8": "NC", "B8": "NC"})
    b.R("5.1k", "CC1", "GND", 68.58, 264.16)
    b.R("5.1k", "CC2", "GND", 88.9, 264.16)
    b.part("U2", "lfm-x2:CH340C_3V3", "CH340C", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", 101.6, 215.9,
           {"16": None, "4": None, "1": "GND", "5": "USB_DP", "6": "USB_DM", "2": "ESP_RX", "3": "ESP_TX",
            "13": "DTR", "14": "RTS", "9": "NC", "10": "NC", "11": "NC", "12": "NC", "15": "NC", "7": "NC", "8": "NC"},
           fields={"ref": (-10.16, -13.97), "val": (2.54, -13.97)})
    b.C("100nF", "+3V3", "GND", 111.76, 264.16)
    vcc, v3 = b.pin("U2", "16"), b.pin("U2", "4")              # CH340C dicatu 3,3 V: V3 disambung ke VCC
    b.wire(vcc, (vcc[0], vcc[1] - STUB)), b.wire(v3, (v3[0], v3[1] - STUB))
    b.wire((vcc[0], vcc[1] - STUB), (v3[0], v3[1] - STUB))
    b.power("+3V3", (vcc[0], vcc[1] - STUB), 90)
    b.manual.update({"U2.16": "+3V3", "U2.4": "+3V3"})
    # auto-reset (rangkaian DevKit): DTR/RTS dari CH340C menarik EN dan IO0 lewat dua NPN
    b.R("10k", "DTR", "Q2_B", 139.7, 180.34)
    b.part("Q2", "Transistor_BJT:SS8050", "SS8050", FP_SOT23, 160.02, 187.96, {"1": "Q2_B", "2": "RTS", "3": "EN"},
           fields="right_far")
    b.R("10k", "RTS", "Q3_B", 139.7, 226.06)
    b.part("Q3", "Transistor_BJT:SS8050", "SS8050", FP_SOT23, 160.02, 233.68, {"1": "Q3_B", "2": "DTR", "3": "IO0"},
           fields="right_far")
    b.part("U1", "RF_Module:ESP32-WROOM-32E", "ESP32-WROOM-32E", "RF_Module:ESP32-WROOM-32E", 210.82, 228.6,
           {"2": "+3V3", "[1,15,38,39]": "GND", "3": "EN", "4": "MUX_SIG", "5": "VBAT_SENSE", "6": "BTN", "7": "BTN2",
            "8": "MUX_S3", "9": "MUX_S2", "10": "MUX_S1", "11": "MUX_S0", "12": "NC", "13": "ENC_L_B", "14": "BUZ",
            "16": "ENC_L_A", "17": "NC", "18": "NC", "19": "NC", "20": "NC", "21": "NC", "22": "NC", "23": "NC",
            "24": "DRV_EN", "25": "IO0", "26": "ML_IN1", "27": "ML_IN2", "28": "MR_IN1", "29": "NC", "30": "MR_IN2",
            "31": "ENC_R_B", "32": "NC", "33": "SDA", "34": "ESP_RX", "35": "ESP_TX", "36": "SCL", "37": "ENC_R_A"},
           fields={"ref": (-15.24, -34.29), "val": (2.54, -34.29)})
    b.R("10k", "+3V3", "EN", 254.0, 180.34)
    b.C("1uF", "EN", "GND", 274.32, 180.34)
    b.R("10k", "+3V3", "IO0", 254.0, 228.6)
    b.part("SW2", "Switch:SW_Push", "BOOT", FP_BTN, 264.16, 254.0, {"1": "IO0", "2": "GND"})
    b.C("10uF 25V", "+3V3", "GND", 254.0, 276.86, FP_C1206)
    b.C("100nF", "+3V3", "GND", 274.32, 276.86)

    # ---- 3. KONEKTOR KE PAPAN LAIN ----
    b.part("J3", "Connector_Generic_MountingPin:Conn_01x08_MountingPin", "FFC ke sensor", FP_FFC, 325.12, 50.8,
           KONEKTOR["sensor"], fields={"ref": (-2.54, -13.97), "val": (1.27, -13.97)})
    b.part("J4", "Connector_Generic:Conn_02x05_Odd_Even", "Ke antarmuka",
           "Connector_PinSocket_2.54mm:PinSocket_2x05_P2.54mm_Vertical", 431.8, 50.8, KONEKTOR["antarmuka"])
    b.part("J5", "Connector_Generic:Conn_02x07_Odd_Even", "Ke driver",
           "Connector_PinSocket_2.54mm:PinSocket_2x07_P2.54mm_Vertical", 330.2, 116.84, KONEKTOR["driver"])
    b.R("10k", "DRV_EN", "GND", 457.2, 116.84)                 # tahan driver tidur saat boot (IO2 = pin strapping)
    b.R("10k", "BUZ", "GND", 482.6, 116.84)                    # IO12 LOW saat boot (HIGH = flash 1,8 V, gagal boot)

    b.blocks = [
        (12.7, 12.7, 292.1, 152.4, "1. DAYA", [
            (15.24, 22.86, "J1: LiPo 2S (6,0-8,4 V) lewat XT30PW-M (pack XT30 betina). Pin 1 = GND (sudut miring),\n"
                           "pin 2 = BAT+ (sisi rata). Tanpa proteksi polaritas terbalik: cek tanda + pada pack."),
            (60.96, 60.96, "Q1 + SW1: saklar daya. SW1 ke GND = hidup (Vgs = -0,91 x VBAT).\n"
                           "SW1 hanya dialiri arus gate, arus motor lewat Q1 (maks kontinu +-2 A)."),
            (236.22, 64.77, "VBAT_SENSE ke GPIO39:\nVBAT x 33/133 (8,4 V -> 2,08 V)"),
            (15.24, 116.84, "U4 buck 5,3 V: umpan balik 0,8 V x (1 + 220k/39k). R 100k di FREQ -> +-900 kHz. "
                            "EN dibiarkan lepas = aktif.\nNilai lain dari datasheet MP1584 gambar 4 (5 V): L 15 uH, "
                            "C 150 pF + R 100k kompensasi."),
            (15.24, 147.32, "D2/D3: +5V dari buck atau USB (yang lebih tinggi). 5,3 V - 0,35 V = +-5,0 V."),
            (228.6, 121.92, "PWR_FLAG: VBAT, +5V, GND"),
        ]),
        (12.7, 157.48, 292.1, 297.18, "2. ESP32-WROOM-32E + USB (CH340C, auto-reset)", [
            (15.24, 284.48, "J2: R 5,1k di CC = perangkat USB (dapat 5 V dari laptop/charger).\n"
                            "U2 dicatu 3,3 V: V3 disambung ke VCC (datasheet CH340)."),
            (132.08, 255.27, "Q2/Q3: auto-reset saat upload\n(DTR, RTS -> EN, IO0)"),
            (132.08, 274.32, "Tombol RST ada di papan antarmuka (EN lewat J4).\nIO5, IO15, IO27 kosong."),
            (246.38, 289.56, "C 10 uF/100 nF dekat pin 3V3 U1"),
        ]),
        (297.18, 12.7, 581.66, 160.02, "3. KONEKTOR KE PAPAN LAIN", [
            (299.72, 78.74, "J3: FFC 1,0 mm 8 pin ke papan sensor, urutan sama dengan J1 PCB sensor rev B.\n"
                            "Pasang di sisi bawah, di ujung segitiga. MP (kaki pemasang) ke GND."),
            (406.4, 78.74, "J4: socket 2x5 di sisi atas, papan antarmuka ditumpuk di atasnya\n"
                           "(header 2x5 di sisi bawah papan antarmuka)."),
            (299.72, 142.24, "J5: socket 2x7 di sisi bawah, papan driver di bawahnya (header 2x7 di sisi atasnya).\n"
                             "VBAT 2 pin + GND 2 pin (arus motor). R pull-down: IO2 (DRV_EN) dan IO12 (BUZ) LOW saat "
                             "boot."),
        ]),
        (297.18, 165.1, 398.78, 208.28, "PIN ESP32 (beda dari jalur utama: motor)", [
            (299.72, 190.5, "ML_IN1 4, ML_IN2 16, MR_IN1 17, MR_IN2 18, DRV_EN 2\n"
                             "MUX_SIG 36, S0-S3 26/25/33/32, VBAT_SENSE 39\n"
                             "BTN 34, BTN2 35, BUZ 12, SDA 21, SCL 22\n"
                             "ENC_L A/B 13/14, ENC_R A/B 23/19"),
        ]),
    ]
    return b


# ============================== PAPAN ANTARMUKA ==============================
def antarmuka():
    b = Skematik("antarmuka", "papan antarmuka (OLED, tombol, buzzer)", "A3", {"Daya": ["+5V", "+3V3", "GND"]})
    b.part("J1", "Connector_Generic:Conn_02x05_Odd_Even", "Ke papan utama",
           "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", 45.72, 142.24, KONEKTOR["antarmuka"])
    b.part("J2", "Connector_Generic:Conn_01x04", "OLED 0,96 I2C",
           "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical", 45.72, 38.1,
           {"1": "GND", "2": "+3V3", "3": "SCL", "4": "SDA"})
    # tangga resistor 5 tombol di GPIO34: nilai sama dengan board interface jalur utama (firmware sama)
    for i, (fn, rv) in enumerate([("ATAS", "1k"), ("BAWAH", "3.9k"), ("KEMBALI", "8.2k"), ("OK", "18k"),
                                  ("LANJUT", "39k")], 1):
        x = 83.82 + (i - 1) * 30.48
        b.part(f"SW{i}", "Switch:SW_Push", fn, FP_BTN, x, 35.56, {"1": "BTN", "2": f"B{i}"})
        b.R(rv, f"B{i}", "GND", x + 7.62, 55.88)
    b.R("10k", "+3V3", "BTN", 238.76, 35.56)
    b.C("100nF", "BTN", "GND", 259.08, 35.56)
    b.part("SW6", "Switch:SW_Push", "START", FP_BTN, 83.82, 88.9, {"1": "BTN2", "2": "GND"})   # tombol ke-6, GPIO35
    b.R("10k", "+3V3", "BTN2", 114.3, 88.9)
    b.C("100nF", "BTN2", "GND", 134.62, 88.9)
    b.part("SW7", "Switch:SW_Push", "RST", FP_BTN, 45.72, 88.9, {"1": "EN", "2": "GND"})
    rb = b.R("1k", "BUZ", None, 198.12, 78.74)
    rp = b.R("10k", None, "GND", 205.74, 93.98)
    b.part("Q1", "Transistor_BJT:SS8050", "SS8050", FP_SOT23, 223.52, 86.36, {"1": None, "3": None, "2": "GND"},
           fields="right_far")
    b.part("BZ1", "Device:Buzzer", "Buzzer aktif 5V", "Buzzer_Beeper:Buzzer_12x9.5RM7.6", 233.68, 69.85,
           {"1": {"net": "+5V", "pdir": 90}, "2": None}, fields="right_far")
    b.buzzer(rb, rp, "Q1", "BZ1")
    b.flag(["+5V", "+3V3", "GND"], 238.76, 129.54)
    b.blocks = [
        (12.7, 12.7, 292.1, 167.64, "PAPAN ANTARMUKA: OLED, 6 TOMBOL MENU, RST, BUZZER", [
            (15.24, 55.88, "J2: cek urutan pin modul\nOLED (GND VCC SCL SDA)."),
            (60.96, 21.59, "Tangga resistor di GPIO34 (pull-up 10k): ATAS 0,30 V, BAWAH 0,93 V, KEMBALI 1,49 V, OK 2,12 V, "
                           "LANJUT 2,63 V, lepas 3,3 V"),
            (60.96, 76.2, "START: tombol ke-6, sendiri di GPIO35"),
            (17.78, 104.14, "RST: menarik EN ke GND\n(R/C EN di papan utama)"),
            (198.12, 109.22, "Q1 + buzzer aktif 5 V. R pull-down IO12\njuga ada di papan utama (syarat boot)."),
            (76.2, 137.16, "J1: header 2x5 di sisi bawah, masuk ke socket J4 papan utama (ditumpuk, jarak antar-papan "
                           "+-11 mm).\nTombol tinggi 7-8 mm atau diberi tutup supaya tidak tenggelam di bawah OLED."),
        ]),
    ]
    return b


# ============================== PAPAN DRIVER ==============================
def driver():
    b = Skematik("driver", "papan driver motor (4x BTN7971B)", "A3",
                 {"Daya besar": ["VBAT", "GND", "ML_P", "ML_N", "MR_P", "MR_N"], "Daya": ["+3V3"]})
    # tiap chip setengah H-bridge: R seri IN/INH 4,7k (datasheet 10k untuk logika 5 V; diperkecil karena logika ESP32
    # 3,3 V), R_SR 1k (0-51k), R_IS 1k ke GND (IS tidak dibaca), 470 nF di VS
    for ref, sin, sout, cx, cy in [("U1", "ML_IN1", "ML_P", 83.82, 45.72), ("U2", "ML_IN2", "ML_N", 218.44, 45.72),
                                   ("U3", "MR_IN1", "MR_P", 83.82, 96.52), ("U4", "MR_IN2", "MR_N", 218.44, 96.52)]:
        b.part(ref, "lfm-x2:BTN7971B", "BTN7971B", FP_TO263, cx, cy,
               {"1": "GND", "2": f"{ref}_IN", "3": f"{ref}_INH", "4": sout, "8": sout, "5": f"{ref}_SR",
                "6": f"{ref}_IS", "7": "VBAT"}, fields={"ref": (7.62, -8.89), "val": (7.62, -6.35)})
        b.R("4.7k", sin, f"{ref}_IN", cx - 60.96, cy)
        b.R("4.7k", "DRV_EN", f"{ref}_INH", cx - 38.1, cy)
        b.R("1k", f"{ref}_SR", "GND", cx + 22.86, cy)
        b.R("1k", f"{ref}_IS", "GND", cx + 40.64, cy)
        b.C("470nF", "VBAT", "GND", cx + 55.88, cy)
    b.C("100uF 16V", "VBAT", "GND", 129.54, 182.88, "Capacitor_SMD:CP_Elec_6.3x5.4", "Device:C_Polarized")
    motor = "Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical"
    b.part("J2", "Connector_Generic:Conn_01x06", "Motor kiri + encoder", motor, 96.52, 139.7,
           {"1": "ML_P", "2": "+3V3", "3": "ENC_L_A", "4": "ENC_L_B", "5": "GND", "6": "ML_N"})
    b.part("J3", "Connector_Generic:Conn_01x06", "Motor kanan + encoder", motor, 185.42, 139.7,
           {"1": "MR_P", "2": "+3V3", "3": "ENC_R_A", "4": "ENC_R_B", "5": "GND", "6": "MR_N"})
    b.part("J1", "Connector_Generic:Conn_02x07_Odd_Even", "Ke papan utama",
           "Connector_PinHeader_2.54mm:PinHeader_2x07_P2.54mm_Vertical", 45.72, 182.88, KONEKTOR["driver"])
    b.flag(["VBAT", "+3V3", "GND"], 154.94, 175.26)
    b.blocks = [
        (12.7, 12.7, 292.1, 210.82, "PAPAN DRIVER MOTOR: 4x BTN7971B (setengah H-bridge, 2 per motor)", [
            (121.92, 127.0, "Maju: IN1 = PWM, IN2 = 0. Mundur: IN1 = 0, IN2 = PWM. Rem: IN1 = IN2.\n"
                            "DRV_EN (GPIO2) = INH keempat chip: LOW = tidur, keluaran lepas (pull-down di papan utama)."),
            (124.46, 152.4, "J2/J3 = urutan pin jalur utama: 1 M+, 2 3V3, 3 ENC A, 4 ENC B, 5 GND, 6 M-"),
            (76.2, 200.66, "J1: header 2x7 di sisi atas, masuk ke socket J5 di sisi bawah papan utama.\n"
                           "C 100 uF dekat J1 (VBAT dari papan utama lewat 2 pin)."),
        ]),
    ]
    return b


# ============================== PAPAN SENSOR ==============================
def sensor():
    b = Skematik("sensor", "papan sensor (12 LED IR + fototransistor, mux)", "A3", {"Daya": ["+5V", "+3V3", "GND"]})
    # tiap kanal: D = LED IR 3528 (selalu nyala, 220 ohm dari +5V), Q = fototransistor PT67-21B (kolektor ditarik 10k
    # ke +3V3 = sinyal Sn, emitor ke GND). Referensi: Dn, Qn, R(2n-1) = 220, R(2n) = 10k.
    for i in range(12):
        sx, sy, n = 17.78 + (i % 6) * 45.72, 38.1 + (i // 6) * 48.26, i + 1
        b.part(f"D{n}", "Device:LED", "LED IR 940nm", FP_PLCC2, sx + 10.16, sy, {"1": "GND", "2": f"A{n}"})
        b.part(f"Q{n}", "Device:Q_Photo_NPN_EC", "PT67-21B", FP_PLCC2, sx + 30.48, sy, {"1": "GND", "2": f"S{n}"},
               fields="right_far")
        b.R("220", "+5V", f"A{n}", sx + 7.62, sy + 20.32)
        b.R("10k", "+3V3", f"S{n}", sx + 38.1, sy + 22.86)
    mux = {"1": "MUX_SIG", "10": "MUX_S0", "11": "MUX_S1", "14": "MUX_S2", "13": "MUX_S3", "15": "GND", "24": "+3V3",
           "12": "GND", "9": "NC", "8": "NC", "17": "NC", "16": "NC"}
    for n, p in enumerate(["7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18"], 1):   # I2..I13
        mux[p] = f"S{n}"
    b.part("U1", "74xx:CD74HC4067M", "CD74HC4067M", "Package_SO:SOIC-24W_7.5x15.4mm_P1.27mm", 58.42, 185.42, mux)
    b.C("100nF", "+3V3", "GND", 106.68, 185.42)
    b.part("J1", "Connector_Generic_MountingPin:Conn_01x08_MountingPin", "FFC ke papan utama", FP_FFC, 147.32, 185.42,
           KONEKTOR["sensor"], fields={"ref": (-2.54, -13.97), "val": (1.27, -13.97)})
    b.flag(["+3V3", "+5V", "GND"], 205.74, 175.26)
    b.blocks = [
        (12.7, 12.7, 292.1, 233.68, "PAPAN SENSOR: 12x LED IR + FOTOTRANSISTOR PT67-21B, CD74HC4067M", [
            (15.24, 124.46, "LED IR selalu nyala: 220 ohm dari +5V (+-17 mA; LED Everlight IR67-21C: VF 1,3 V, maks 65 mA).\n"
                            "PT67-21B lensa hitam (700-1100 nm, puncak 940 nm): kolektor ditarik 10k ke +3V3 = Sn, "
                            "makin terang makin rendah.\n10k titik awal: cek di breadboard di atas banner (4,7k-22k)."),
            (15.24, 139.7, "Pad 1 = katoda LED / emitor PT, pad 2 = anoda / kolektor. Sudut terpotong Everlight di sisi "
                            "pad 2;\nLED IR lain bisa terbalik: cek dengan multimeter mode dioda sebelum disolder."),
            (127.0, 210.82, "S1..S12 = I2..I13 (sama dengan rev B). I0, I1, I14, I15 kosong.\n"
                            "Kanal 1 = paling kiri dilihat dari atas, robot menghadap depan.\n"
                            "J1 FFC 1,0 mm 8 pin, urutan = J1 PCB sensor rev B. Kabel FFC tipe B (kontak berlawanan)."),
        ]),
    ]
    return b


PAPAN = {"utama": utama, "antarmuka": antarmuka, "driver": driver, "sensor": sensor}

if __name__ == "__main__":
    pilih = [a for a in sys.argv[1:] if not a.startswith("--")] or list(PAPAN)
    for nama in pilih:
        sk = PAPAN[nama]()
        sk.sambung()
        sk.tulis("--paksa" in sys.argv)
