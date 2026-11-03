"""Membuat skematik board interface (hardware/board-interface/board-interface.kicad_sch), KiCad 10.

Board kecil yang ditumpuk di atas PCB utama (konsep v17, 03/11/2026): OLED 0,96 inci di socket + 5 tombol 6x6 untuk
menu (kiri atas/bawah, kanan kembali/OK/lanjut). Kelima tombol membentuk tangga resistor ke satu pin ADC (GPIO34):
tombol k menghubungkan BTN ke GND lewat Rk, pull-up 10k (R5) ada di PCB utama supaya GPIO34 tidak mengambang saat
board ini dilepas. Sambungan ke PCB utama lewat J1 1x6 (= J6 PCB utama, urutan pin sama).

Mesin gambar disalin dari gen_sch_utama.py. Jalankan dari folder repo: py hardware/tools/gen_sch_interface.py [--paksa]
Sesudahnya cek: kicad-cli sch erc hardware/board-interface/board-interface.kicad_sch
"""
import math
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kisym  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCH = os.path.join(ROOT, "hardware", "board-interface", "board-interface.kicad_sch")
LTM = os.path.join(ROOT, "hardware", "ltm-lib")
PROJECT = "board-interface"
POWER = {"+5V": "power:+5V", "+3V3": "power:+3V3", "GND": "power:GND"}
STUB = 2.54

FP_R = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"


def uid():
    return str(uuid.uuid4())


def f(v):
    """angka koordinat: dibulatkan ke 0,01 mm, tanpa nol berlebih"""
    s = f"{round(v, 4):.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ============================== DAFTAR KOMPONEN ==============================
# nets: nomor pin -> nama net | "NC" (tanda X) | None (disambung manual di bawah)
#       atau dict(net=..., lang=sudut label, pdir=arah badan simbol daya (derajat), len=panjang kabel)
PARTS = []


def part(ref, lib_id, value, fp, x, y, nets, fields="lib"):
    PARTS.append(dict(ref=ref, lib_id=lib_id, value=value, fp=fp, x=x, y=y, nets=nets, fields=fields))


# ---- KONEKTOR ----
part("J1", "Connector_Generic:Conn_01x06", "Ke PCB utama (J6)",
     "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", 45.72, 63.5,
     {"1": "+3V3", "2": "GND", "3": "SDA", "4": "SCL", "5": "BTN", "6": "NC"})
part("J2", "Connector_Generic:Conn_01x04", "OLED 0,96 I2C", "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
     45.72, 121.92, {"1": "GND", "2": "+3V3", "3": "SCL", "4": "SDA"})
part("C1", "Device:C", "100nF", "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm", 88.9, 63.5,
     {"1": "BTN", "2": "GND"}, fields="right")

# ---- TANGGA RESISTOR 5 TOMBOL ----
# tegangan BTN saat tombol k ditekan = 3,3 * Rk / (10k + Rk); lepas = 3,3 V
LADDER = [("Atas", "1k"), ("Bawah", "3.9k"), ("Kembali", "8.2k"), ("OK", "18k"), ("Lanjut", "39k")]
for i, (fn, rv) in enumerate(LADDER, 1):
    x = 129.54 + (i - 1) * 30.48
    part(f"SW{i}", "Switch:SW_Push", fn, "Button_Switch_THT:SW_PUSH_6mm", x, 63.5,
         {"1": "BTN", "2": f"B{i}"})
    part(f"R{i}", "Device:R", rv, FP_R, x + 7.62, 88.9, {"1": f"B{i}", "2": "GND"}, fields="right")

BLOCKS = [
    (12.7, 12.7, 284.48, 165.1, "BOARD INTERFACE: OLED + 5 TOMBOL MENU", [
        (106.68, 106.68, "Tegangan BTN (pull-up 10k = R5 di PCB utama):\nAtas 0,30 V, Bawah 0,93 V, Kembali 1,49 V,\n"
                         "OK 2,12 V, Lanjut 2,63 V, lepas 3,3 V"),
    ]),
]

# ============================== GEOMETRI ==============================
LIB = {}


def lib(lib_id):
    if lib_id not in LIB:
        LIB[lib_id] = kisym.load(lib_id, [LTM])
    return LIB[lib_id]


def rot(x, y, r):
    """putar vektor koordinat library (Y ke atas) berlawanan jarum jam"""
    a = math.radians(r)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def to_sch(X, Y, lx, ly, r=0):
    """titik library -> skematik (Y ke bawah)"""
    rx, ry = rot(lx, ly, r)
    return round(X + rx, 4), round(Y - ry, 4)


PARTMAP = {p["ref"]: p for p in PARTS}


def pin(ref, num):
    p = PARTMAP[ref]
    for q in lib(p["lib_id"])[1]:
        if q["num"] == num:
            return to_sch(p["x"], p["y"], q["x"], q["y"])
    raise KeyError((ref, num))


def outward(q):
    """arah keluar pin (derajat, Y ke atas): kebalikan arah pin menuju badan simbol"""
    return (q["ang"] + 180) % 360


# ============================== KELUARAN ==============================
out = []
WIRES, JUNCS, LABELS, NCS, POWERS = [], [], [], [], []
pwr_n = [0]


def wire(a, b):
    WIRES.append((a, b))


def label(net, at, ang):
    LABELS.append((net, at, ang % 360))


def power(net, at, body_dir, lib_id=None):
    """simbol daya di titik at; badan simbol menunjuk ke body_dir (derajat, Y ke atas)"""
    lid = lib_id or POWER[net]
    base = 270 if net == "GND" else 90             # arah badan simbol di library
    POWERS.append((lid, at, (body_dir - base) % 360))


def attach(at, d, spec):
    if isinstance(spec, str):
        spec = {"net": spec}
    net = spec["net"]
    ln = spec.get("len", STUB)
    end = (round(at[0] + ln * math.cos(math.radians(d)), 4), round(at[1] - ln * math.sin(math.radians(d)), 4))
    wire(at, end)
    if net in POWER:
        power(net, end, spec.get("pdir", d))
    else:
        lang = spec.get("lang", d if d in (0, 180) else 0)
        label(net, end, lang)


for p in PARTS:
    for q in lib(p["lib_id"])[1]:
        spec = p["nets"].get(q["num"], "MISSING")
        if spec == "MISSING":
            raise SystemExit(f"pin {p['ref']}.{q['num']} ({q['name']}) belum diberi net")
        at = to_sch(p["x"], p["y"], q["x"], q["y"])
        if spec is None:
            continue
        if spec == "NC":
            NCS.append(at)
            continue
        attach(at, outward(q), spec)

# ---- sambungan manual ----
# PWR_FLAG untuk +3V3 dan GND (daya datang dari J1)
for net, y in (("+3V3", 144.78), ("GND", 154.94)):
    fl = (157.48, y)
    POWERS.append(("power:PWR_FLAG", fl, 0))
    wire(fl, (fl[0] + 10.16, y))
    power(net, (fl[0] + 10.16, y), 270 if net == "GND" else 90)


# ============================== TULIS FILE ==============================
def eff(size=1.27, justify=None, hide=False, bold=False):
    j = f" (justify {justify})" if justify else ""
    b = " (bold yes)" if bold else ""
    h = " (hide yes)" if hide else ""
    return f"(effects (font (size {size} {size}){b}){j}{h})"


old = open(SCH, encoding="utf8").read() if os.path.exists(SCH) else ""
m = re.search(r'\(uuid "([^"]+)"\)', old)
root_uuid = m.group(1) if m else uid()
if "(lib_id" in old and "--paksa" not in sys.argv:
    raise SystemExit("skematik sudah berisi simbol; pakai --paksa kalau memang mau ditimpa")


def lib_prop(blk, name):
    m = re.search(r'\(property "%s" "([^"]*)"\s*\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)' % name, blk)
    return (m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4) or 0)) if m else ("", 0, 0, 0)


def symbol(lib_id, ref, value, fp, X, Y, r=0, fields="lib", hide_ref=False, hide_val=False):
    blk, pins = lib(lib_id)
    _, rx, ry, ra = lib_prop(blk, "Reference")
    _, vx, vy, va = lib_prop(blk, "Value")
    ds = lib_prop(blk, "Datasheet")[0]
    if fields in ("right", "right_far"):
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
         f'\t\t(uuid "{uid()}")',
         f'\t\t(property "Reference" "{ref}" (at {f(rp[0])} {f(rp[1])} {ang}) {eff(justify=just, hide=hide_ref)})',
         f'\t\t(property "Value" "{value}" (at {f(vp[0])} {f(vp[1])} {ang}) {eff(justify=just, hide=hide_val)})',
         f'\t\t(property "Footprint" "{fp}" (at {f(X)} {f(Y)} 0) {eff(hide=True)})',
         f'\t\t(property "Datasheet" "{ds}" (at {f(X)} {f(Y)} 0) {eff(hide=True)})']
    for q in pins:
        s.append(f'\t\t(pin "{q["num"]}" (uuid "{uid()}"))')
    s.append(f'\t\t(instances (project "{PROJECT}" (path "/{root_uuid}" (reference "{ref}") (unit 1))))')
    s.append("\t)")
    return "\n".join(s)


used = sorted({p["lib_id"] for p in PARTS} | {lid for lid, _, _ in POWERS})
out.append("(kicad_sch\n\t(version 20260306)\n\t(generator \"eeschema\")\n\t(generator_version \"10.0\")")
out.append(f'\t(uuid "{root_uuid}")\n\t(paper "A4")')
out.append('\t(title_block\n\t\t(title "LTM - board interface")\n\t\t(date "2026-11-03")\n\t\t(rev "A")\n'
           '\t\t(company "P01 Kel.5 PjBL DTEO FV ITS")\n'
           '\t\t(comment 1 "Ditumpuk di atas PCB utama lewat J1 = J6 PCB utama")\n'
           '\t\t(comment 2 "Dibuat oleh hardware/tools/gen_sch_interface.py")\n\t)')
out.append("\t(lib_symbols\n" + "\n".join(lib(u)[0] for u in used) + "\n\t)")

for x0, y0, x1, y1, title, notes in BLOCKS:
    out.append(f'\t(rectangle (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width 0.254) (type dash)) '
               f'(fill (type none)) (uuid "{uid()}"))')
    out.append(f'\t(text "{title}" (exclude_from_sim no) (at {f(x0 + 2.54)} {f(y0 + 5.08)} 0) '
               f'{eff(2.0, "left", bold=True)} (uuid "{uid()}"))')
    for tx, ty, t in notes:
        t = t.replace("\n", "\\n")
        out.append(f'\t(text "{t}" (exclude_from_sim no) (at {f(tx)} {f(ty)} 0) {eff(1.27, "left")} (uuid "{uid()}"))')

for p in PARTS:
    out.append(symbol(p["lib_id"], p["ref"], p["value"], p["fp"], p["x"], p["y"], fields=p["fields"]))

npwr = nflg = 0
for lid, at, r in POWERS:
    if lid == "power:PWR_FLAG":
        nflg += 1
        ref = f"#FLG{nflg:02d}"
    else:
        npwr += 1
        ref = f"#PWR{npwr:03d}"
    out.append(symbol(lid, ref, lid.split(":")[1], "", at[0], at[1], r, hide_ref=True))

for a, b in WIRES:
    out.append(f'\t(wire (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})) (stroke (width 0) (type default)) '
               f'(uuid "{uid()}"))')
for j in JUNCS:
    out.append(f'\t(junction (at {f(j[0])} {f(j[1])}) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))')
for at in NCS:
    out.append(f'\t(no_connect (at {f(at[0])} {f(at[1])}) (uuid "{uid()}"))')
for net, at, ang in LABELS:
    just = "left" if ang in (0, 90) else "right"
    out.append(f'\t(global_label "{net}" (shape passive) (at {f(at[0])} {f(at[1])} {ang}) (fields_autoplaced yes) '
               f'{eff(justify=just)} (uuid "{uid()}"))')

out.append('\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n')
open(SCH, "w", encoding="utf8", newline="\n").write("\n".join(out))
print(f"ditulis {SCH}: {len(PARTS)} komponen, {len(LABELS)} label, {len(WIRES)} kabel, {len(NCS)} NC")
