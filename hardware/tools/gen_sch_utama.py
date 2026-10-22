"""Membuat skematik PCB utama (hardware/pcb-utama/pcb-utama.kicad_sch), KiCad 10.

Isi sesuai wiring diagram blok 1-4 dan tabel di hardware/pcb-utama/README.md: daya, driver motor + motor,
layar/tombol/buzzer, ESP32, dan J5 kabel ke PCB sensor. Gaya label: tiap pin diberi kabel pendek lalu label global
(nama sama = tersambung) atau simbol daya, kecuali rangkaian kecil (pembagi tegangan, tombol, buzzer) yang digambar
dengan kabel.

Jalankan dari folder repo: py hardware/tools/gen_sch_utama.py [--paksa]
Tanpa --paksa, skrip menolak menimpa skematik yang sudah berisi simbol (supaya gambar user tidak hilang).
Sesudahnya cek: kicad-cli sch erc hardware/pcb-utama/pcb-utama.kicad_sch
"""
import math
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kisym  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCH = os.path.join(ROOT, "hardware", "pcb-utama", "pcb-utama.kicad_sch")
LTM = os.path.join(ROOT, "hardware", "ltm-lib")
PROJECT = "pcb-utama"
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


# ---- 1. DAYA ----
part("J1", "Connector_Generic:Conn_01x02", "Baterai (P+/P- BMS)",
     "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical", 45.72, 34.29, {"1": "BAT+", "2": "GND"})
part("SW1", "Switch:SW_SPDT", "Saklar geser", "Button_Switch_THT:SW_Slide_SPDT_Angled_CK_OS102011MA1Q",
     83.82, 36.83, {"2": "VBAT", "1": "BAT+", "3": "NC"})
part("U3", "ltm:MP1584_Module", "MP1584 (set 5,0 V)", "ltm:MP1584_Module", 55.88, 62.23,
     {"1": "VBAT", "2": "GND", "3": "+5V_BUCK", "4": "GND"})
part("D1", "Device:D_Schottky", "1N5819", "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal", 106.68, 60.96,
     {"1": "+5V", "2": "+5V_BUCK"})
part("C1", "Device:C_Polarized", "100uF 16V", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm", 25.4, 88.9,
     {"1": "VBAT", "2": "GND"}, fields="right")
part("R1", "Device:R", "100k", FP_R, 50.8, 86.36, {"1": "VBAT", "2": None}, fields="right")
part("R2", "Device:R", "33k", FP_R, 50.8, 101.6, {"1": None, "2": "GND"}, fields="right")

# ---- 2. DRIVER MOTOR + MOTOR ----
part("U2", "ltm:TB6612_Module", "TB6612 modul", "ltm:TB6612_Module_2x8_W15.24", 190.5, 55.88,
     {"1": "PWMA", "2": "AIN2", "3": "AIN1", "4": "STBY", "5": "BIN1", "6": "BIN2", "7": "PWMB", "8": "GND",
      "9": "VBAT", "10": "+3V3", "11": "GND", "12": "ML_P", "13": "ML_N", "14": "MR_N", "15": "MR_P", "16": "GND"})
MOTOR_FP = "Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical"
part("J2", "Connector_Generic:Conn_01x06", "Motor kiri + encoder", MOTOR_FP, 271.78, 50.8,
     {"1": "ML_P", "2": "+3V3", "3": "ENC_L_A", "4": "ENC_L_B", "5": "GND", "6": "ML_N"})
part("J3", "Connector_Generic:Conn_01x06", "Motor kanan + encoder", MOTOR_FP, 347.98, 50.8,
     {"1": "MR_P", "2": "+3V3", "3": "ENC_R_A", "4": "ENC_R_B", "5": "GND", "6": "MR_N"})

# ---- 3. LAYAR, TOMBOL, BUZZER ----
part("J4", "Connector_Generic:Conn_01x04", "OLED 0,96 I2C", "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
     50.8, 140.97, {"1": "GND", "2": "+3V3", "3": "SCL", "4": "SDA"})
part("R5", "Device:R", "10k", FP_R, 30.48, 167.64, {"1": "+3V3", "2": None}, fields="right")
part("SW2", "Switch:SW_Push", "Tombol A", "Button_Switch_THT:SW_PUSH_6mm", 38.1, 175.26,
     {"1": None, "2": {"net": "GND", "pdir": 270}})
part("R6", "Device:R", "10k", FP_R, 86.36, 167.64, {"1": "+3V3", "2": None}, fields="right")
part("SW3", "Switch:SW_Push", "Tombol B", "Button_Switch_THT:SW_PUSH_6mm", 93.98, 175.26,
     {"1": None, "2": {"net": "GND", "pdir": 270}})
part("R3", "Device:R", "1k", FP_R, 40.64, 207.01, {"1": "BUZ", "2": None}, fields="right")
part("R4", "Device:R", "10k", FP_R, 48.26, 222.25, {"1": None, "2": "GND"}, fields="right")
part("Q1", "Transistor_BJT:S8050", "S8050", "Package_TO_SOT_THT:TO-92_Inline", 66.04, 214.63,
     {"2": None, "3": None, "1": "GND"})
part("BZ1", "Device:Buzzer", "Buzzer aktif 5V", "Buzzer_Beeper:Buzzer_12x9.5RM7.6", 76.2, 198.12,
     {"1": {"net": "+5V", "pdir": 90}, "2": None}, fields="right_far")

# ---- 4. ESP32 ----
part("U1", "ltm:ESP32_DevKit_30", "ESP32 DevKit 30 pin", "ltm:ESP32_DevKit_30P_W25.4", 210.82, 180.34,
     {"1": "NC", "2": "MUX_SIG", "3": "VBAT_SENSE", "4": "BTN_A", "5": "BTN_B", "6": "MUX_S3", "7": "MUX_S2",
      "8": "MUX_S1", "9": "MUX_S0", "10": "NC", "11": "ENC_L_B", "12": "BUZ", "13": "ENC_L_A", "14": "GND",
      "15": "+5V", "16": "ENC_R_A", "17": "SCL", "18": "NC", "19": "NC", "20": "SDA", "21": "ENC_R_B",
      "22": "PWMA", "23": "AIN1", "24": "AIN2", "25": "PWMB", "26": "BIN1", "27": "STBY", "28": "BIN2",
      "29": "GND", "30": "+3V3"})

# ---- 5. KABEL KE PCB SENSOR ----
part("J5", "Connector_Generic:Conn_01x08", "Kabel PCB sensor (= J1 sensor)",
     "Connector_JST:JST_XH_B8B-XH-A_1x08_P2.50mm_Vertical", 320.04, 154.94,
     {"1": "+5V", "2": "+3V3", "3": "GND", "4": "MUX_S3", "5": "MUX_S2", "6": "MUX_S1", "7": "MUX_S0",
      "8": "MUX_SIG"})

# kotak blok + judul + catatan: (x0, y0, x1, y1, judul, [(x, y, teks), ...])
BLOCKS = [
    (12.7, 12.7, 139.7, 114.3, "1. DAYA  (wiring diagram blok 1)", [
        (99.06, 76.2, "PWR_FLAG: daya VBAT, +5V, GND\ndatang dari konektor/dioda"),
        (12.7 + 2.54, 22.86, "J1 = P+/P- BMS (baterai 2S di rangka)"),
        (66.04, 49.53, "SW1: kaki tengah (B) = VBAT"),
        (71.12, 71.12, "Set MP1584 ke 5,0 V dulu\nsebelum ESP32 dipasang"),
        (99.06, 52.07, "D1: cegah arus balik saat USB dicolok"),
        (17.78, 106.68, "C1 dekat pin VM TB6612"),
        (60.96, 106.68, "VBAT_SENSE ke GPIO39 (ADC1)"),
    ]),
    (144.78, 12.7, 406.4, 114.3, "2. DRIVER MOTOR + MOTOR  (wiring diagram blok 2)", [
        (152.4, 81.28, "Urutan pin modul TB6612 beda tiap penjual: cocokkan dengan modul yang dibeli."),
        (152.4, 86.36, "VM = VBAT (7,4 V) langsung, VCC = 3,3 V logika. AO ke motor kiri, BO ke motor kanan."),
        (241.3, 81.28 + 10.16, "J2/J3 = JST PH 6 pin. Encoder tanpa resistor (firmware INPUT_PULLUP)."),
        (241.3, 96.52, "Urutan 6 kabel motor N20 beda tiap penjual: cek sebelum crimp."),
    ]),
    (12.7, 119.38, 139.7, 248.92, "3. LAYAR, TOMBOL, BUZZER  (wiring diagram blok 3)", [
        (63.5, 139.7, "Cek urutan pin modul OLED\n(ada yang VCC dulu baru GND)"),
        (17.78, 187.96, "R5/R6 wajib: GPIO34/35 tanpa pull-up internal"),
        (86.36, 210.82, "R4 menjaga GPIO12 LOW\nsaat boot (syarat boot ESP32)"),
        (86.36, 222.25, "Q1 TO-92: cek urutan E-B-C"),
    ]),
    (144.78, 119.38, 276.86, 248.92, "4. ESP32 DEVKIT  (otak)", [
        (149.86, 208.28, "GPIO34/35/36/39: hanya input"),
        (149.86, 213.36, "GPIO2 (STBY) dan GPIO12 (BUZ) harus LOW saat boot"),
        (149.86, 218.44, "EN, GPIO27, TX0, RX0: tidak dipakai (X)"),
        (149.86, 223.52, "Footprint W25.4: ukur jarak baris pin modul (22,86 mm -> W22.86)"),
    ]),
    (281.94, 119.38, 406.4, 200.66, "5. KABEL KE PCB SENSOR  (wiring diagram blok 4)", [
        (335.28, 147.32, "J5 = JST XH 8 pin, urutan pin SAMA\ndengan J1 PCB sensor (kabel lurus,\npin n ke pin n)"),
        (335.28, 162.56, "Ikuti NOMOR pin: pin 4-7 terbalik\ndari urutan nama (S3 dulu)"),
        (287.02, 185.42, "Di PCB: J5 sejajar tepi miring sidepod kiri, pin 1 di ujung dekat hidung"),
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
# pembagi tegangan baterai: R1 - VBAT_SENSE - R2
a, b = pin("R1", "2"), pin("R2", "1")
mid = (a[0], round((a[1] + b[1]) / 2 / 1.27) * 1.27)
wire(a, mid), wire(mid, b), JUNCS.append(mid)
wire(mid, (mid[0] + 5.08, mid[1])), label("VBAT_SENSE", (mid[0] + 5.08, mid[1]), 0)

# tombol: +3V3 - R - node(BTN) - tombol - GND
for r_, sw, net in (("R5", "SW2", "BTN_A"), ("R6", "SW3", "BTN_B")):
    rb, s1 = pin(r_, "2"), pin(sw, "1")
    node = (rb[0], s1[1])
    wire(rb, node), wire(node, s1), JUNCS.append(node)
    wire(node, (node[0] - 2.54, node[1])), label(net, (node[0] - 2.54, node[1]), 180)

# buzzer: BUZ - R3 - basis Q1, R4 basis ke GND, kolektor ke kaki - buzzer
r3b, qb, r4t = pin("R3", "2"), pin("Q1", "2"), pin("R4", "1")
k1 = (r3b[0], qb[1])
wire(r3b, k1), wire(k1, (r4t[0], qb[1])), wire((r4t[0], qb[1]), qb), wire((r4t[0], qb[1]), r4t)
JUNCS.append((r4t[0], qb[1]))
qc, bzn = pin("Q1", "3"), pin("BZ1", "2")
wire(bzn, (qc[0], bzn[1])), wire((qc[0], bzn[1]), qc)

# PWR_FLAG untuk VBAT, +5V, GND (daya datang dari konektor dan dioda, bukan pin keluaran daya)
for net, y in (("VBAT", 86.36), ("+5V", 96.52), ("GND", 106.68)):
    fl = (104.14, y)
    POWERS.append(("power:PWR_FLAG", fl, 0))
    wire(fl, (fl[0] + 10.16, y))
    if net in POWER:
        power(net, (fl[0] + 10.16, y), 270 if net == "GND" else 90)
    else:
        label(net, (fl[0] + 10.16, y), 0)


# ============================== TULIS FILE ==============================
def eff(size=1.27, justify=None, hide=False, bold=False):
    j = f" (justify {justify})" if justify else ""
    b = " (bold yes)" if bold else ""
    h = " (hide yes)" if hide else ""
    return f"(effects (font (size {size} {size}){b}){j}{h})"


root_uuid = re.search(r'\(uuid "([^"]+)"\)', open(SCH, encoding="utf8").read()).group(1)
old = open(SCH, encoding="utf8").read()
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
out.append(f'\t(uuid "{root_uuid}")\n\t(paper "A3")')
out.append('\t(title_block\n\t\t(title "LTM - PCB utama")\n\t\t(date "2026-10-22")\n\t\t(rev "A")\n'
           '\t\t(company "P01 Kel.5 PjBL DTEO FV ITS")\n'
           '\t\t(comment 1 "Panduan per blok: docs/wiring-diagram.html")\n'
           '\t\t(comment 2 "Dibuat oleh hardware/tools/gen_sch_utama.py, pin ESP32 sesuai CLAUDE.md")\n\t)')
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
