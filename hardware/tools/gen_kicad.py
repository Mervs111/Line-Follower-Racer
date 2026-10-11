#!/usr/bin/env python3
"""Generator starter proyek KiCad Robot Line Tracer Micro (format KiCad 7, bisa dibuka KiCad 7/8/9).

Membuat:
  hardware/ltm-lib/ltm.kicad_sym           symbol buatan sendiri
  hardware/ltm-lib/ltm.pretty/*.kicad_mod  footprint sementara (WAJIB dicek dengan modul asli)
  hardware/ltm-main/                       proyek + skematik PCB utama
  hardware/ltm-sensor/                     proyek + skematik PCB sensor jangkar

PERINGATAN: menjalankan ulang script ini MENIMPA skematik. Jalankan hanya sekali untuk starter,
setelah itu edit langsung di KiCad. Acuan sambungan: docs/skematik-v1.md.
"""
import copy, json, math, os, sys, uuid

KICAD_SYM_DIR = os.environ.get("KICAD_SYMBOL_DIR", "/usr/share/kicad/symbols")
HW = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATE = "2026-10-11"


def U():
    return str(uuid.uuid4())


def num(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


# ------------------------------------------------------------------ s-expression
def tokenize(s):
    i, n, out = 0, len(s), []
    while i < n:
        c = s[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()":
            out.append(c); i += 1
        elif c == '"':
            j = i + 1
            while j < n:
                if s[j] == "\\":
                    j += 2; continue
                if s[j] == '"':
                    break
                j += 1
            out.append(s[i:j + 1]); i = j + 1
        else:
            j = i
            while j < n and s[j] not in " \t\r\n()":
                j += 1
            out.append(s[i:j]); i = j
    return out


def parse(text):
    stack = [[]]
    for t in tokenize(text):
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t)
    return stack[0][0]


def dump(x, ind=0):
    if not isinstance(x, list):
        return x
    if all(not isinstance(e, list) for e in x):
        return "(" + " ".join(x) + ")"
    pad = "  " * (ind + 1)
    head = []
    rest = []
    for e in x:
        if not rest and not isinstance(e, list):
            head.append(e)
        else:
            rest.append(e)
    s = "(" + " ".join(head)
    for e in rest:
        s += "\n" + pad + dump(e, ind + 1)
    return s + "\n" + "  " * ind + ")"


_LIB_CACHE = {}


def lib_symbol(lib, name):
    if lib not in _LIB_CACHE:
        _LIB_CACHE[lib] = parse(open(os.path.join(KICAD_SYM_DIR, lib + ".kicad_sym")).read())
    for e in _LIB_CACHE[lib]:
        if isinstance(e, list) and e[0] == "symbol" and e[1] == q(name):
            if any(isinstance(k, list) and k[0] == "extends" for k in e):
                raise SystemExit(f"{lib}:{name} memakai extends, pilih symbol lain")
            return copy.deepcopy(e)
    raise SystemExit(f"symbol {lib}:{name} tidak ditemukan")


def sym_pins(sym):
    """pin -> (x, y, angle, type) dalam koordinat library (Y ke atas)"""
    pins = {}

    def walk(e):
        for k in e:
            if isinstance(k, list):
                if k[0] == "pin":
                    at = next(a for a in k if isinstance(a, list) and a[0] == "at")
                    number = next(a for a in k if isinstance(a, list) and a[0] == "number")[1].strip('"')
                    name = next(a for a in k if isinstance(a, list) and a[0] == "name")[1].strip('"')
                    pins[number] = (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0, k[1], name)
                elif k[0] == "symbol":
                    walk(k)
    walk(sym)
    return pins


def sym_props(sym):
    out = {}
    for k in sym:
        if isinstance(k, list) and k[0] == "property":
            at = next(a for a in k if isinstance(a, list) and a[0] == "at")
            eff = next(a for a in k if isinstance(a, list) and a[0] == "effects")
            out[k[1].strip('"')] = (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0, eff)
    return out


# ------------------------------------------------------------------ symbol buatan sendiri
def pin_line(ptype, x, y, ang, length, name, number):
    return (f'(pin {ptype} line (at {num(x)} {num(y)} {num(ang)}) (length {num(length)})\n'
            f'        (name {q(name)} (effects (font (size 1.27 1.27))))\n'
            f'        (number {q(number)} (effects (font (size 1.27 1.27))))\n'
            f'      )')


def make_symbol(name, ref, value, footprint, desc, keywords, body, pins, extra_graphics="", pin_names_offset=1.016):
    """body = (x0, y0, x1, y1) koordinat library; pins = [(type, x, y, angle, length, name, number)]"""
    x0, y0, x1, y1 = body
    props = [
        (f'(property "Reference" {q(ref)} (at {num(x0)} {num(y0 + 1.27)} 0)\n'
         f'      (effects (font (size 1.27 1.27)) (justify left bottom))\n    )'),
        (f'(property "Value" {q(value)} (at {num(x0)} {num(y1 - 1.27)} 0)\n'
         f'      (effects (font (size 1.27 1.27)) (justify left top))\n    )'),
        (f'(property "Footprint" {q(footprint)} (at 0 0 0)\n'
         f'      (effects (font (size 1.27 1.27)) hide)\n    )'),
        (f'(property "Datasheet" "~" (at 0 0 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )'),
        (f'(property "ki_keywords" {q(keywords)} (at 0 0 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )'),
        (f'(property "ki_description" {q(desc)} (at 0 0 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )'),
    ]
    g = (f'(symbol "{name}_0_1"\n      (rectangle (start {num(x0)} {num(y0)}) (end {num(x1)} {num(y1)})\n'
         f'        (stroke (width 0.254) (type default))\n        (fill (type background))\n      )\n'
         f'{extra_graphics}    )')
    p = "\n      ".join(pin_line(*pp) for pp in pins)
    return (f'  (symbol "{name}" (pin_names (offset {num(pin_names_offset)})) (in_bom yes) (on_board yes)\n    '
            + "\n    ".join(props) + f"\n    {g}\n    (symbol \"{name}_1_1\"\n      {p}\n    )\n  )")


ESP32_LEFT = [("1", "EN", "input"), ("2", "GPIO36/VP", "input"), ("3", "GPIO39/VN", "input"),
              ("4", "GPIO34", "input"), ("5", "GPIO35", "input"), ("6", "GPIO32", "bidirectional"),
              ("7", "GPIO33", "bidirectional"), ("8", "GPIO25", "bidirectional"), ("9", "GPIO26", "bidirectional"),
              ("10", "GPIO27", "bidirectional"), ("11", "GPIO14", "bidirectional"), ("12", "GPIO12", "bidirectional"),
              ("13", "GPIO13", "bidirectional"), ("14", "GND", "power_in"), ("15", "VIN", "power_in")]
ESP32_RIGHT = [("16", "GPIO23", "bidirectional"), ("17", "GPIO22", "bidirectional"), ("18", "TX0/GPIO1", "bidirectional"),
               ("19", "RX0/GPIO3", "bidirectional"), ("20", "GPIO21", "bidirectional"), ("21", "GPIO19", "bidirectional"),
               ("22", "GPIO18", "bidirectional"), ("23", "GPIO5", "bidirectional"), ("24", "GPIO17/TX2", "bidirectional"),
               ("25", "GPIO16/RX2", "bidirectional"), ("26", "GPIO4", "bidirectional"), ("27", "GPIO2", "bidirectional"),
               ("28", "GPIO15", "bidirectional"), ("29", "GND", "power_in"), ("30", "3V3", "power_out")]
TB_LEFT = [("1", "PWMA", "input"), ("2", "AIN2", "input"), ("3", "AIN1", "input"), ("4", "STBY", "input"),
           ("5", "BIN1", "input"), ("6", "BIN2", "input"), ("7", "PWMB", "input"), ("8", "GND", "power_in")]
TB_RIGHT = [("9", "VM", "power_in"), ("10", "VCC", "power_in"), ("11", "GND", "power_in"), ("12", "AO1", "output"),
            ("13", "AO2", "output"), ("14", "BO2", "output"), ("15", "BO1", "output"), ("16", "GND", "power_in")]


def build_library():
    syms = []
    pins = []
    for i, (n, nm, t) in enumerate(ESP32_LEFT):
        pins.append((t, -15.24, 17.78 - 2.54 * i, 0, 2.54, nm, n))
    for i, (n, nm, t) in enumerate(ESP32_RIGHT):
        pins.append((t, 15.24, 17.78 - 2.54 * i, 180, 2.54, nm, n))
    syms.append(make_symbol("ESP32_DevKit_30", "U", "ESP32_DevKit_30", "ltm:ESP32_DevKit_30P_W25.4",
                            "Modul ESP32 DevKit 30 pin (susunan DOIT V1). Pin 1-15 baris kiri, 16-30 baris kanan, "
                            "dari ujung antena ke ujung USB. CEK dengan modul yang dibeli.",
                            "ESP32 DevKit 30 pin CH340 modul", (-12.7, 20.32, 12.7, -20.32), pins))
    pins = []
    for i, (n, nm, t) in enumerate(TB_LEFT):
        pins.append((t, -12.7, 8.89 - 2.54 * i, 0, 2.54, nm, n))
    for i, (n, nm, t) in enumerate(TB_RIGHT):
        pins.append((t, 12.7, 8.89 - 2.54 * i, 180, 2.54, nm, n))
    syms.append(make_symbol("TB6612_Module", "U", "TB6612FNG_Modul", "ltm:TB6612_Module_2x8_W15.24",
                            "Modul breakout driver motor TB6612FNG 16 pin. Urutan pin = susunan umum, CEK modul asli.",
                            "TB6612 TB6612FNG motor driver modul", (-10.16, 11.43, 10.16, -11.43), pins))
    pins = [("power_in", -12.7, 1.27, 0, 2.54, "IN+", "1"), ("power_in", -12.7, -1.27, 0, 2.54, "IN-", "2"),
            ("power_out", 12.7, 1.27, 180, 2.54, "OUT+", "3"), ("power_in", 12.7, -1.27, 180, 2.54, "OUT-", "4")]
    syms.append(make_symbol("MP1584_Module", "U", "MP1584_5V", "ltm:MP1584_Module",
                            "Modul buck converter MP1584 (set 5,0 V sebelum dipasang). Posisi pad CEK modul asli.",
                            "MP1584 buck step down modul", (-10.16, 3.81, 10.16, -3.81), pins))
    led = ('      (polyline (pts (xy -3.81 1.27) (xy -1.27 1.27) (xy -2.54 -0.635) (xy -3.81 1.27))\n'
           '        (stroke (width 0.254) (type default)) (fill (type none)))\n'
           '      (polyline (pts (xy -3.81 -0.635) (xy -1.27 -0.635)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
           '      (polyline (pts (xy -0.635 0.635) (xy 0.635 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
           '      (polyline (pts (xy -0.635 -0.635) (xy 0.635 0)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
           '      (polyline (pts (xy 2.54 1.905) (xy 2.54 -1.905)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
           '      (polyline (pts (xy 2.54 0.635) (xy 3.81 1.905)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
           '      (polyline (pts (xy 2.54 -0.635) (xy 3.81 -1.905)) (stroke (width 0.254) (type default)) (fill (type none)))\n')
    pins = [("passive", -7.62, 2.54, 0, 2.54, "A", "1"), ("passive", -7.62, -2.54, 0, 2.54, "K", "2"),
            ("passive", 7.62, 2.54, 180, 2.54, "C", "3"), ("passive", 7.62, -2.54, 180, 2.54, "E", "4")]
    syms.append(make_symbol("ITR20001", "U", "ITR20001", "ltm:ITR20001",
                            "Sensor reflektif IR (LED + fototransistor). Nomor pin CEK datasheet ITR20001/T.",
                            "ITR20001 reflective sensor line", (-5.08, 3.81, 5.08, -3.81), pins, led, 0.508))
    text = "(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n" + "\n".join(syms) + "\n)\n"
    os.makedirs(os.path.join(HW, "ltm-lib"), exist_ok=True)
    open(os.path.join(HW, "ltm-lib", "ltm.kicad_sym"), "w").write(text)
    return parse(text)


# ------------------------------------------------------------------ footprint sementara
def fp_text(kind, text, x, y, layer, size=1.0, ang=0):
    a = f" {num(ang)}" if ang else ""
    return (f'  (fp_text {kind} {q(text)} (at {num(x)} {num(y)}{a}) (layer "{layer}")\n'
            f'    (effects (font (size {num(size)} {num(size)}) (thickness {num(size * 0.15)})))\n'
            f'    (tstamp {U()})\n  )')


def fp_rect(x0, y0, x1, y1, layer, w):
    return (f'  (fp_rect (start {num(x0)} {num(y0)}) (end {num(x1)} {num(y1)})\n'
            f'    (stroke (width {num(w)}) (type solid)) (fill none) (layer "{layer}") (tstamp {U()}))')


def pad(n, x, y, size=1.7, drill=1.0, shape=None):
    shape = shape or ("rect" if n == "1" else "circle")
    return (f'  (pad {q(n)} thru_hole {shape} (at {num(x)} {num(y)}) (size {num(size)} {num(size)}) '
            f'(drill {num(drill)}) (layers "*.Cu" "*.Mask") (tstamp {U()}))')


def write_fp(name, descr, body, pads, texts=()):
    x0, y0, x1, y1 = body
    items = [f'(footprint {q(name)} (version 20221018) (generator pcbnew)', '  (layer "F.Cu")',
             f'  (descr {q(descr)})', f'  (tags {q("LTM sementara cek ukur")})', '  (attr through_hole)',
             fp_text("reference", "REF**", 0, y0 - 1.5, "F.SilkS"), fp_text("value", name, 0, y1 + 1.5, "F.Fab"),
             fp_text("user", "${REFERENCE}", 0, 0, "F.Fab"),
             fp_rect(x0, y0, x1, y1, "F.SilkS", 0.12), fp_rect(x0, y0, x1, y1, "F.Fab", 0.1),
             fp_rect(x0 - 0.25, y0 - 0.25, x1 + 0.25, y1 + 0.25, "F.CrtYd", 0.05)]
    items += [fp_text("user", t, x, y, "F.Fab", 0.8) for t, x, y in texts]
    items += pads
    path = os.path.join(HW, "ltm-lib", "ltm.pretty")
    os.makedirs(path, exist_ok=True)
    open(os.path.join(path, name + ".kicad_mod"), "w").write("\n".join(items) + "\n)\n")


def build_footprints():
    for w in (25.4, 22.86):
        pads = [pad(str(i + 1), -w / 2, -17.78 + 2.54 * i) for i in range(15)]
        pads += [pad(str(16 + i), w / 2, -17.78 + 2.54 * i) for i in range(15)]
        write_fp(f"ESP32_DevKit_30P_W{num(w)}",
                 f"ESP32 DevKit 30 pin, jarak baris {num(w)} mm. SEMENTARA: ukur modul asli (panjang papan, posisi pin 1).",
                 (-14.2, -29.3, 14.2, 22.3), pads, [("ANTENA", 0, -25.5), ("USB", 0, 20.5), ("UKUR ULANG", 0, 2)])
    pads = [pad(str(i + 1), -7.62, -8.89 + 2.54 * i) for i in range(8)]
    pads += [pad(str(9 + i), 7.62, -8.89 + 2.54 * i) for i in range(8)]
    write_fp("TB6612_Module_2x8_W15.24", "Modul TB6612FNG 2x8 pin, jarak baris 15,24 mm. SEMENTARA: ukur modul asli.",
             (-10.2, -10.9, 10.2, 10.9), pads, [("UKUR ULANG", 0, 0)])
    pads = [pad("1", -9.5, -6.0, 2.0, 1.2), pad("2", -9.5, 6.0, 2.0, 1.2),
            pad("3", 9.5, -6.0, 2.0, 1.2), pad("4", 9.5, 6.0, 2.0, 1.2)]
    write_fp("MP1584_Module", "Modul MP1584 22x17 mm, 4 titik solder di sudut. SEMENTARA: ukur modul asli.",
             (-11.0, -8.5, 11.0, 8.5), pads, [("IN", -6.5, 0), ("OUT", 6.5, 0), ("UKUR ULANG", 0, 3.5)])
    pads = [pad("1", -1.27, -1.27, 1.4, 0.8), pad("2", -1.27, 1.27, 1.4, 0.8),
            pad("3", 1.27, -1.27, 1.4, 0.8), pad("4", 1.27, 1.27, 1.4, 0.8)]
    write_fp("ITR20001", "ITR20001/T 4 kaki. SEMENTARA: cocokkan jarak & urutan kaki dengan datasheet.",
             (-2.6, -2.6, 2.6, 2.6), pads, [("CEK DS", 0, 0)])


# ------------------------------------------------------------------ skematik
FP = {
    "R": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
    "R_SMD": "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder",
    "C": "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
    "C_SMD": "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder",
    "CP100": "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
    "CP10": "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
    "SS14": "Diode_SMD:D_SMA",
    "TO92": "Package_TO_SOT_THT:TO-92_Inline",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "BTN": "Button_Switch_THT:SW_PUSH_6mm",
    "SLIDE": "Button_Switch_THT:SW_Slide_SPDT_Angled_CK_OS102011MA1Q",
    "BUZ": "Buzzer_Beeper:Buzzer_12x9.5RM7.6",
    "XH2": "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
    "PH6": "Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical",
    "SOCK4": "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
    "SOCK2x5": "Connector_PinSocket_2.54mm:PinSocket_2x05_P2.54mm_Vertical",
    "HDR2x5": "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical",
    "HOLE": "MountingHole:MountingHole_3.2mm_M3",
}
POWER_SYMS = {"GND": "GND", "+5V": "+5V", "+3V3": "+3V3"}
STUB = 2.54


class Sheet:
    def __init__(self, project, title, comments, ltm_lib):
        self.project, self.title, self.comments = project, title, comments
        self.root = U()
        self.items = []
        self.libs = {}
        self.ltm = ltm_lib
        self.pwr_n = 0
        self.expect = {}      # (ref, pin) -> net, untuk verifikasi

    def get_sym(self, lib_id):
        if lib_id not in self.libs:
            lib, name = lib_id.split(":")
            if lib == "ltm":
                s = next(copy.deepcopy(e) for e in self.ltm if isinstance(e, list) and e[0] == "symbol" and e[1] == q(name))
            else:
                s = lib_symbol(lib, name)
            s[1] = q(lib_id)
            self.libs[lib_id] = s
        return self.libs[lib_id]

    # -------------------------------------------------- penempatan simbol
    def place(self, lib_id, ref, value, x, y, fp="", rot=0, fields="lib", hidden_ref=False, in_bom=True):
        sym = self.get_sym(lib_id)
        pins = sym_pins(sym)
        props = sym_props(sym)
        ca, sa = round(math.cos(math.radians(rot)), 6), round(math.sin(math.radians(rot)), 6)

        def tf(px, py):          # koordinat library -> skematik
            rx, ry = px * ca - py * sa, px * sa + py * ca
            return x + rx, y - ry

        out = {}
        for n, (px, py, pa, ptype, pname) in pins.items():
            ax, ay = tf(px, py)
            a = math.radians(pa + rot)
            dx, dy = -math.cos(a), -math.sin(a)          # arah keluar (library)
            out[n] = (round(ax, 4), round(ay, 4), (round(dx), round(-dy)), pname)
        fl = []
        for key in ("Reference", "Value", "Footprint", "Datasheet"):
            px, py, pang, eff = props.get(key, (0, 0, 0, ["effects"]))
            val = {"Reference": ref, "Value": value, "Footprint": fp, "Datasheet": "~"}[key]
            hide = key in ("Footprint", "Datasheet") or (key == "Reference" and hidden_ref) or "hide" in eff
            if fields == "right" and key in ("Reference", "Value"):
                fx, fy, fang = x + 3.81, y + (-1.27 if key == "Reference" else 1.27), 0
                e = "(effects (font (size 1.27 1.27)) (justify left))"
            else:
                fx, fy = tf(px, py)
                fang = 90 if rot in (90, 270) else 0
                justify = next((k for k in eff if isinstance(k, list) and k[0] == "justify"), None)
                e = "(effects (font (size 1.27 1.27))" + (" " + dump(justify) if justify else "") + (" hide" if hide else "") + ")"
            if hide and "hide" not in e:
                e = e[:-1] + " hide)"
            fl.append(f'    (property "{key}" {q(val)} (at {num(fx)} {num(fy)} {fang})\n      {e}\n    )')
        pin_uuids = "\n".join(f'    (pin {q(n)} (uuid {U()}))' for n in sorted(pins, key=lambda s: (len(s), s)))
        self.items.append(
            f'  (symbol (lib_id {q(lib_id)}) (at {num(x)} {num(y)} {rot}) (unit 1)\n'
            f'    (in_bom {"yes" if in_bom else "no"}) (on_board yes) (dnp no)\n    (uuid {U()})\n' + "\n".join(fl) + "\n"
            + pin_uuids + "\n"
            f'    (instances\n      (project {q(self.project)}\n        (path "/{self.root}"\n'
            f'          (reference {q(ref)}) (unit 1)\n        )\n      )\n    )\n  )')
        return out

    # -------------------------------------------------- sambungan
    def wire(self, x1, y1, x2, y2):
        self.items.append(f'  (wire (pts (xy {num(x1)} {num(y1)}) (xy {num(x2)} {num(y2)}))\n'
                          f'    (stroke (width 0) (type default))\n    (uuid {U()})\n  )')

    def label(self, net, x, y, d):
        ang = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[d]
        just = "left bottom" if ang in (0, 90) else "right bottom"
        self.items.append(f'  (label {q(net)} (at {num(x)} {num(y)} {ang}) (fields_autoplaced)\n'
                          f'    (effects (font (size 1.27 1.27)) (justify {just}))\n    (uuid {U()})\n  )')

    def power(self, net, x, y, d):
        self.pwr_n += 1
        if net == "GND":
            rot = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[d]
        else:
            rot = {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}[d]
        self.place("power:" + POWER_SYMS[net], f"#PWR0{self.pwr_n:02d}", net, x, y, rot=rot, hidden_ref=True)

    def flag(self, net, x, y):
        """PWR_FLAG pada sebuah net (untuk ERC)"""
        self.pwr_n += 1
        self.place("power:PWR_FLAG", f"#FLG0{self.pwr_n:02d}", "PWR_FLAG", x, y, hidden_ref=True)
        self.wire(x, y, x, y + STUB)
        if net in POWER_SYMS:
            self.power(net, x, y + STUB, (0, 1))
        else:
            self.label(net, x, y + STUB, (0, 1))

    def nc(self, x, y):
        self.items.append(f'  (no_connect (at {num(x)} {num(y)}) (uuid {U()}))')

    def connect(self, ref, pins, mapping):
        """mapping: nomor pin -> nama net, atau None untuk no-connect"""
        stub = {}
        groups = {}
        for n, net in mapping.items():
            if net in POWER_SYMS and pins[n][2][1] == 0:          # pin daya mendatar
                x, y, d, _ = pins[n]
                groups.setdefault((x, d), []).append((y, n))
        for lst in groups.values():                                 # pin daya bersebelahan: 2,54 / 7,62 selang-seling
            lst.sort()
            prev = None
            for y, n in lst:
                long_ = prev is not None and abs(y - prev[0] - 2.54) < 0.01 and stub[prev[1]] == STUB
                stub[n] = 3 * STUB if long_ else STUB
                prev = (y, n)
        for n, net in mapping.items():
            x, y, d, _ = pins[n]
            if net is None:
                self.nc(x, y)
                continue
            self.expect[(ref, n)] = net
            L = stub.get(n, STUB)
            ex, ey = x + d[0] * L, y + d[1] * L
            self.wire(x, y, ex, ey)
            if net in POWER_SYMS:
                self.power(net, ex, ey, d)
            else:
                self.label(net, ex, ey, d)

    def part(self, lib_id, ref, value, x, y, fp, mapping, fields="lib", in_bom=True):
        pins = self.place(lib_id, ref, value, x, y, fp, fields=fields, in_bom=in_bom)
        self.connect(ref, pins, mapping)
        return pins

    # -------------------------------------------------- grafis
    def text(self, s, x, y, size=1.27, bold=False):
        b = f" (thickness {num(size * 0.2)}) bold" if bold else ""
        self.items.append(f'  (text {q(s)} (at {num(x)} {num(y)} 0)\n'
                          f'    (effects (font (size {num(size)} {num(size)}){b}) (justify left bottom))\n'
                          f'    (uuid {U()})\n  )')

    def frame(self, x0, y0, x1, y1, title):
        pts = f"(xy {num(x0)} {num(y0)}) (xy {num(x1)} {num(y0)}) (xy {num(x1)} {num(y1)}) (xy {num(x0)} {num(y1)}) (xy {num(x0)} {num(y0)})"
        self.items.append(f'  (polyline (pts {pts})\n    (stroke (width 0) (type dash))\n    (uuid {U()})\n  )')
        self.text(title, x0 + 1.27, y0 + 4.445, 2.0, bold=True)

    # -------------------------------------------------- tulis file
    def save(self, path):
        comments = "\n".join(f'    (comment {i + 1} {q(c)})' for i, c in enumerate(self.comments))
        libs = "\n".join("    " + dump(self.libs[k], 2) for k in sorted(self.libs))
        text = (f'(kicad_sch (version 20230121) (generator eeschema)\n\n  (uuid {self.root})\n\n  (paper "A3")\n\n'
                f'  (title_block\n    (title {q(self.title)})\n    (date {q(DATE)})\n    (rev "v1-starter")\n'
                f'    (company "P01 Kel.5 PjBL DTEO FV ITS")\n{comments}\n  )\n\n'
                f'  (lib_symbols\n{libs}\n  )\n\n' + "\n\n".join(self.items) +
                '\n\n  (sheet_instances\n    (path "/" (page "1"))\n  )\n)\n')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").write(text)


def write_project(folder, name, root_uuid):
    os.makedirs(folder, exist_ok=True)
    cls = dict(bus_width=12, clearance=0.2, diff_pair_gap=0.25, diff_pair_via_gap=0.25, diff_pair_width=0.2,
               line_style=0, microvia_diameter=0.3, microvia_drill=0.1, pcb_color="rgba(0, 0, 0, 0.000)",
               schematic_color="rgba(0, 0, 0, 0.000)", track_width=0.25, via_diameter=0.6, via_drill=0.3, wire_width=6)
    power = dict(cls, name="Power", track_width=0.8)
    default = dict(cls, name="Default")
    pro = {
        "board": {"design_settings": {"rules": {
            "min_clearance": 0.2, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.25,
            "min_hole_to_hole": 0.5, "min_through_hole_diameter": 0.3, "min_track_width": 0.2,
            "min_via_annular_width": 0.13, "min_via_diameter": 0.5}}},
        "meta": {"filename": f"{name}.kicad_pro", "version": 1},
        "net_settings": {"classes": [default, power], "meta": {"version": 3},
                         "net_colors": None, "netclass_assignments": None,
                         # net dari label lokal diberi awalan "/" oleh KiCad (mis. "/VBAT")
                         "netclass_patterns": [{"netclass": "Power", "pattern": p} for p in
                                               ("GND", "+5V", "/VBAT", "/BAT+", "/+5V_BUCK", "/ML_*", "/MR_*", "/LED_K")]},
        "sheets": [[root_uuid, ""]],
        "text_variables": {},
    }
    json.dump(pro, open(os.path.join(folder, f"{name}.kicad_pro"), "w"), indent=2)
    open(os.path.join(folder, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (lib (name "ltm")(type "KiCad")(uri "${KIPRJMOD}/../ltm-lib/ltm.kicad_sym")(options "")(descr "Simbol LTM"))\n)\n')
    open(os.path.join(folder, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (lib (name "ltm")(type "KiCad")(uri "${KIPRJMOD}/../ltm-lib/ltm.pretty")(options "")(descr "Footprint LTM"))\n)\n')


# ================================================================== PCB UTAMA
def build_main(ltm):
    s = Sheet("ltm-main", "LTM - PCB Utama",
              ["Acuan: docs/skematik-v1.md", "Pin modul = susunan umum, CEK dengan modul yang dibeli",
               "Format KiCad 7, dibuka KiCad 8/9 otomatis di-upgrade"], ltm)
    G = 2.54

    # ---- 1. DAYA
    s.frame(12.7, 15.24, 152.4, 132.08, "1. DAYA: baterai, saklar, buck 5 V, pembaca baterai")
    s.part("Connector_Generic:Conn_01x02", "J1", "BATERAI (dari BMS)", 30.48, 38.1, FP["XH2"], {"1": "BAT+", "2": "GND"})
    s.part("Switch:SW_SPDT", "SW1", "ON/OFF", 63.5, 38.1, FP["SLIDE"], {"2": "VBAT", "1": "BAT+", "3": None})
    s.part("Device:C_Polarized", "C1", "100uF/16V", 86.36, 38.1, FP["CP100"], {"1": "VBAT", "2": "GND"}, "right")
    s.part("Device:C", "C2", "100nF", 99.06, 38.1, FP["C"], {"1": "VBAT", "2": "GND"}, "right")
    s.part("ltm:MP1584_Module", "U3", "MP1584 (5,0 V)", 63.5, 66.04, "ltm:MP1584_Module",
           {"1": "VBAT", "2": "GND", "3": "+5V_BUCK", "4": "GND"})
    s.part("Device:D_Schottky", "D1", "SS14", 106.68, 66.04, FP["SS14"], {"2": "+5V_BUCK", "1": "+5V"})
    s.part("Device:C_Polarized", "C3", "10uF/16V", 129.54, 66.04, FP["CP10"], {"1": "+5V", "2": "GND"}, "right")
    s.part("Device:C", "C4", "100nF", 142.24, 66.04, FP["C"], {"1": "+5V", "2": "GND"}, "right")
    s.part("Device:R", "R1", "100k", 30.48, 96.52, FP["R"], {"1": "VBAT", "2": "VBAT_SENSE"}, "right")
    s.part("Device:R", "R2", "33k", 48.26, 96.52, FP["R"], {"1": "VBAT_SENSE", "2": "GND"}, "right")
    s.part("Device:C", "C5", "100nF", 66.04, 96.52, FP["C"], {"1": "VBAT_SENSE", "2": "GND"}, "right")
    s.text("Pembaca baterai: 8,4 V -> 2,08 V ke GPIO33", 20.32, 127.0)
    s.text("PWR_FLAG (untuk ERC)", 99.06, 91.44)
    s.flag("GND", 101.6, 96.52)
    s.flag("VBAT", 116.84, 96.52)
    s.flag("+5V", 132.08, 96.52)
    s.text("D1 mencegah arus balik ke USB laptop", 96.52, 78.74)

    # ---- 2. ESP32
    s.frame(160.02, 15.24, 264.16, 132.08, "2. ESP32 DevKit 30 pin")
    esp_left = {"1": None, "2": "S1", "3": "S2", "4": "S3", "5": "S4", "6": "S5", "7": "VBAT_SENSE", "8": "PWMA",
                "9": "AIN1", "10": "AIN2", "11": "PWMB", "12": "BUZ", "13": "IR_EN", "14": "GND", "15": "+5V"}
    esp_right = {"16": "ENC_R_A", "17": "SCL", "18": None, "19": None, "20": "SDA", "21": "ENC_L_B", "22": "ENC_L_A",
                 "23": "ENC_R_B", "24": "BIN2", "25": "BIN1", "26": "STBY", "27": "BTN_B", "28": "BTN_A",
                 "29": "GND", "30": "+3V3"}
    s.part("ltm:ESP32_DevKit_30", "U1", "ESP32 DevKit 30P CH340", 212.09, 73.66, "ltm:ESP32_DevKit_30P_W25.4",
           {**esp_left, **esp_right})
    s.text("GPIO12 (BUZ) harus LOW saat boot: ada R4 10k di basis Q1", 165.1, 124.46)

    # ---- 3. DRIVER + MOTOR
    s.frame(271.78, 15.24, 408.94, 132.08, "3. DRIVER MOTOR + KONEKTOR MOTOR")
    s.part("ltm:TB6612_Module", "U2", "TB6612FNG", 304.8, 50.8, "ltm:TB6612_Module_2x8_W15.24",
           {"1": "PWMA", "2": "AIN2", "3": "AIN1", "4": "STBY", "5": "BIN1", "6": "BIN2", "7": "PWMB", "8": "GND",
            "9": "VBAT", "10": "+3V3", "11": "GND", "12": "ML_P", "13": "ML_N", "14": "MR_N", "15": "MR_P", "16": "GND"})
    s.part("Device:C", "C6", "100nF", 294.64, 81.28, FP["C"], {"1": "+3V3", "2": "GND"}, "right")
    s.part("Connector_Generic:Conn_01x06", "J2", "MOTOR KIRI", 365.76, 45.72, FP["PH6"],
           {"1": "ML_P", "2": "+3V3", "3": "ENC_L_A", "4": "ENC_L_B", "5": "GND", "6": "ML_N"})
    s.part("Connector_Generic:Conn_01x06", "J3", "MOTOR KANAN", 365.76, 76.2, FP["PH6"],
           {"1": "MR_P", "2": "+3V3", "3": "ENC_R_A", "4": "ENC_R_B", "5": "GND", "6": "MR_N"})
    for i, net in enumerate(("ENC_L_A", "ENC_L_B", "ENC_R_A", "ENC_R_B")):
        s.part("Device:R", f"R{5 + i}", "10k", 327.66 + i * 17.78, 106.68, FP["R"], {"1": "+3V3", "2": net}, "right")
    s.text("R5-R8 pull-up encoder: boleh tidak dipasang bila encoder sudah punya pull-up", 276.86, 124.46)
    s.text("Urutan kabel N20 beda tiap penjual: cocokkan", 340.36, 91.44)

    # ---- 4. OLED + TOMBOL
    s.frame(12.7, 142.24, 109.22, 233.68, "4. OLED + TOMBOL")
    s.part("Connector_Generic:Conn_01x04", "J4", "OLED 1.3in I2C", 40.64, 165.1, FP["SOCK4"],
           {"1": "GND", "2": "+3V3", "3": "SCL", "4": "SDA"})
    s.text("Sebagian OLED urutannya VCC-GND: cek", 20.32, 180.34)
    s.part("Switch:SW_Push", "SW2", "A (MENU)", 50.8, 198.12, FP["BTN"], {"1": "BTN_A", "2": "GND"})
    s.part("Switch:SW_Push", "SW3", "B (OK)", 50.8, 215.9, FP["BTN"], {"1": "BTN_B", "2": "GND"})
    s.text("Pull-up internal ESP32 (INPUT_PULLUP)", 20.32, 228.6)

    # ---- 5. BUZZER
    s.frame(116.84, 142.24, 215.9, 233.68, "5. BUZZER")
    s.part("Device:R", "R3", "1k", 134.62, 172.72, FP["R"], {"1": "BUZ", "2": "BZ_B"}, "right")
    s.part("Device:R", "R4", "10k", 134.62, 203.2, FP["R"], {"1": "BZ_B", "2": "GND"}, "right")
    s.part("Transistor_BJT:S8050", "Q1", "S8050", 170.18, 190.5, FP["TO92"], {"1": "GND", "2": "BZ_B", "3": "BZ_N"})
    s.part("Device:Buzzer", "BZ1", "Buzzer aktif 5V", 195.58, 167.64, FP["BUZ"], {"1": "+5V", "2": "BZ_N"})
    s.text("Buzzer magnetik: tambah 1N4148 paralel", 121.92, 228.6)

    # ---- 6. KONEKTOR PCB SENSOR
    s.frame(223.52, 142.24, 312.42, 233.68, "6. KE PCB SENSOR (J5 = lubang tembus)")
    s.part("Connector_Generic:Conn_02x05_Odd_Even", "J5", "KE PCB SENSOR", 264.16, 185.42, FP["HDR2x5"],
           {"1": "+5V", "2": "+3V3", "3": "GND", "4": "GND", "5": "IR_EN", "6": "S1", "7": "S2", "8": "S3",
            "9": "S4", "10": "S5"}, in_bom=False)
    s.text("Urutan pin sama persis dengan J1 PCB sensor", 228.6, 213.36)
    s.text("J5 tidak dipasang komponen: pin header J1 PCB sensor\nmasuk dari bawah lewat lubang J5, disolder di atas", 228.6, 222.25)

    # ---- 7. LUBANG BAUT
    s.frame(320.04, 142.24, 408.94, 190.5, "7. LUBANG BAUT M3")
    for i in range(6):
        s.place("Mechanical:MountingHole", f"H{i + 1}", "M3", 332.74 + i * 13.97, 167.64, FP["HOLE"])
    s.text("H1-H2 rangka, H3-H4 bahu, H5-H6 spacer PCB sensor", 325.12, 185.42)

    s.save(os.path.join(HW, "ltm-main", "ltm-main.kicad_sch"))
    write_project(os.path.join(HW, "ltm-main"), "ltm-main", s.root)
    return s


# ================================================================== PCB SENSOR
def build_sensor(ltm):
    s = Sheet("ltm-sensor", "LTM - PCB Sensor Jangkar",
              ["Acuan: docs/skematik-v1.md", "Nilai 180R / 10k = nilai awal, setel saat uji",
               "Slot sensor cadangan di lengan jangkar ditambah saat layout"], ltm)
    s.frame(12.7, 15.24, 83.82, 106.68, "1. KE PCB UTAMA")
    s.part("Connector_Generic:Conn_02x05_Odd_Even", "J1", "KE PCB UTAMA", 45.72, 55.88, FP["HDR2x5"],
           {"1": "+5V", "2": "+3V3", "3": "GND", "4": "GND", "5": "IR_EN", "6": "S1", "7": "S2", "8": "S3",
            "9": "S4", "10": "S5"})
    s.text("PWR_FLAG (untuk ERC)", 17.78, 81.28)
    s.flag("+5V", 25.4, 86.36)
    s.flag("+3V3", 43.18, 86.36)
    s.flag("GND", 60.96, 86.36)

    s.frame(91.44, 15.24, 408.94, 132.08, "2. SENSOR GARIS S1-S5 (ITR20001)")
    for i in range(5):
        x = 111.76 + i * 60.96
        s.part("Device:R", f"R{1 + i}", "180", x, 45.72, FP["R_SMD"], {"1": "+5V", "2": f"LED_A{i + 1}"}, "right")
        s.part("ltm:ITR20001", f"U{1 + i}", f"ITR20001 (S{i + 1})", x + 22.86, 81.28, "ltm:ITR20001",
               {"1": f"LED_A{i + 1}", "2": "LED_K", "3": f"S{i + 1}", "4": "GND"})
        s.part("Device:R", f"R{6 + i}", "10k", x + 40.64, 45.72, FP["R_SMD"], {"1": "+3V3", "2": f"S{i + 1}"}, "right")
    s.text("LED IR: (5 V - 1,2 V) / 180 = 21 mA per sensor, total +-105 mA lewat Q1", 96.52, 124.46)

    s.frame(12.7, 142.24, 160.02, 233.68, "3. SAKLAR LED IR (emitter ON/OFF)")
    s.part("Device:Q_NMOS_GSD", "Q1", "AO3400", 96.52, 190.5, FP["SOT23"], {"1": "IR_G", "2": "GND", "3": "LED_K"})
    s.part("Device:R", "R11", "100", 55.88, 182.88, FP["R_SMD"], {"1": "IR_EN", "2": "IR_G"}, "right")
    s.part("Device:R", "R12", "10k", 71.12, 208.28, FP["R_SMD"], {"1": "IR_G", "2": "GND"}, "right")
    s.part("Device:C", "C1", "100nF", 134.62, 190.5, FP["C_SMD"], {"1": "+3V3", "2": "GND"}, "right")
    s.text("IR_EN HIGH = LED menyala (baca ON - OFF)", 17.78, 228.6)

    s.frame(167.64, 142.24, 241.3, 190.5, "4. LUBANG BAUT M3")
    for i in range(2):
        s.place("Mechanical:MountingHole", f"H{i + 1}", "M3", 185.42 + i * 25.4, 167.64, FP["HOLE"])

    s.save(os.path.join(HW, "ltm-sensor", "ltm-sensor.kicad_sch"))
    write_project(os.path.join(HW, "ltm-sensor"), "ltm-sensor", s.root)
    return s


if __name__ == "__main__":
    ltm = build_library()
    build_footprints()
    sheets = {"ltm-main": build_main(ltm), "ltm-sensor": build_sensor(ltm)}
    expect = {k: {f"{r}.{p}": n for (r, p), n in v.expect.items()} for k, v in sheets.items()}
    json.dump(expect, open(os.path.join(HW, "tools", "expected_nets.json"), "w"), indent=1, sort_keys=True)
    print("ok")
