"""Membuat skematik LFM X2 (hardware/lfm-x2/lfm-x2.kicad_sch), KiCad 10.

LFM X2 = side project: satu PCB all-in-one full SMD (keputusan user 15/11/2026). Isi: modul ESP32-WROOM-32E + CH340C +
USB-C, buck MP1584EN dan LDO AMS1117-3.3 di papan, 4x BTN7971B (2 setengah H-bridge per motor), 12x QRE1113GR + mux
CD74HC4067M, OLED + 6 tombol menu + RST/BOOT, buzzer. Pin ESP32 mengikuti jalur utama (CLAUDE.md) kecuali driver motor.

Gaya gambar sama dengan gen_sch_utama.py (mesin gambarnya disalin dari sana): tiap pin diberi kabel pendek lalu label
global (nama sama = tersambung) atau simbol daya; rangkaian kecil (pembagi tegangan, buzzer) digambar dengan kabel.

Jalankan dari folder repo: py hardware/tools/gen_sch_x2.py [--paksa]
Tanpa --paksa, skrip menolak menimpa skematik yang sudah berisi simbol (supaya suntingan user tidak hilang).
Sesudahnya cek: kicad-cli sch erc hardware/lfm-x2/lfm-x2.kicad_sch, lalu py hardware/tools/cek_net_x2.py
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
DIR = os.path.join(ROOT, "hardware", "lfm-x2")
SCH = os.path.join(DIR, "lfm-x2.kicad_sch")
PROJECT = "lfm-x2"
POWER = {"+5V": "power:+5V", "+3V3": "power:+3V3", "GND": "power:GND"}
STUB = 2.54

FP_R = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
FP_C = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_C1206 = "Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder"
FP_SOT23 = "Package_TO_SOT_SMD:SOT-23"
FP_SMA = "Diode_SMD:D_SMA"
FP_BTN = "Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92"
FP_TO263 = "Package_TO_SOT_SMD:TO-263-7_TabPin8"


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
NOMOR = {}


def part(ref, lib_id, value, fp, x, y, nets, fields="lib"):
    PARTS.append(dict(ref=ref, lib_id=lib_id, value=value, fp=fp, x=x, y=y, nets=nets, fields=fields))
    return ref


def auto(awalan):
    NOMOR[awalan] = NOMOR.get(awalan, 0) + 1
    return f"{awalan}{NOMOR[awalan]}"


def R(value, atas, bawah, x, y):
    """resistor tegak: pin 1 di atas, pin 2 di bawah"""
    return part(auto("R"), "Device:R", value, FP_R, x, y, {"1": atas, "2": bawah}, fields="right")


def C(value, atas, bawah, x, y, fp=FP_C, lib_id="Device:C"):
    return part(auto("C"), lib_id, value, fp, x, y, {"1": atas, "2": bawah}, fields="right")


# ---- 1. DAYA ----
part("J1", "Connector_Generic:Conn_01x02", "Baterai 2S", "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
     38.1, 43.18, {"1": "BAT+", "2": "GND"})
# saklar daya: SW1 hanya mengalirkan arus gate Q1 (AO3401A, P-MOSFET sisi atas). R1 menahan gate di BAT+ (mati),
# R2 menariknya ke GND saat SW1 hidup: Vgs = -VBAT x 100/110 = -7,6 V pada 8,4 V (batas Vgs AO3401A 12 V, jadi hanya
# untuk 2S). C1 x R2 = 1 ms memperlambat nyala (arus masuk ke C2 470 uF).
part("Q1", "Transistor_FET:AO3401A", "AO3401A", FP_SOT23, 71.12, 43.18, {"1": "PWR_G", "2": "BAT+", "3": "VBAT"},
     fields="right_far")
R("100k", "BAT+", "PWR_G", 96.52, 43.18)                                                  # R1
C("100nF", "BAT+", "PWR_G", 119.38, 43.18)                                                # C1
R("10k", "PWR_G", "PWR_SW", 142.24, 43.18)                                                # R2
part("SW1", "Switch:SW_SPDT", "Saklar daya", "Button_Switch_THT:SW_Slide_SPDT_Angled_CK_OS102011MA1Q",
     170.18, 43.18, {"2": "PWR_SW", "1": "GND", "3": "NC"})
C("470uF 16V", "VBAT", "GND", 200.66, 43.18, "Capacitor_SMD:CP_Elec_8x10.5", "Device:C_Polarized")   # C2
R("100k", "VBAT", None, 226.06, 35.56)                                                    # R3
R("33k", None, "GND", 226.06, 50.8)                                                       # R4
C("100nF", "VBAT_SENSE", "GND", 254.0, 43.18)                                             # C3

part("U4", "lfm-x2:MP1584EN", "MP1584EN", "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm", 50.8, 91.44,
     {"7": "VBAT", "2": "NC", "6": "BUCK_FREQ", "8": "BUCK_BST", "1": "BUCK_SW", "4": "BUCK_FB", "3": "BUCK_COMP",
      "5": None, "9": None})
C("10uF 25V", "VBAT", "GND", 91.44, 91.44, FP_C1206)                                      # C4
C("100nF", "VBAT", "GND", 109.22, 91.44)                                                  # C5
R("100k", "BUCK_FREQ", "GND", 127.0, 91.44)                                               # R5
C("100nF", "BUCK_BST", "BUCK_SW", 149.86, 91.44)                                          # C6
part("D1", "Device:D_Schottky", "SS34", FP_SMA, 180.34, 91.44, {"1": "BUCK_SW", "2": "GND"})
part("L1", "Device:L", "15uH 2A", "Inductor_SMD:L_Sumida_CR75", 203.2, 91.44, {"1": "BUCK_SW", "2": "+5V_BUCK"},
     fields="right")
C("22uF 16V", "+5V_BUCK", "GND", 228.6, 91.44, FP_C1206)                                  # C7
R("220k", "+5V_BUCK", None, 254.0, 83.82)                                                 # R6
R("39k", None, "GND", 254.0, 99.06)                                                       # R7
R("100k", "BUCK_COMP", None, 276.86, 83.82)                                               # R8
C("150pF", None, "GND", 276.86, 99.06)                                                    # C8

part("D2", "Device:D_Schottky", "SS14", FP_SMA, 38.1, 134.62, {"1": "+5V", "2": "+5V_BUCK"})
part("D3", "Device:D_Schottky", "SS14", FP_SMA, 78.74, 134.62, {"1": "+5V", "2": "VBUS"})
part("U3", "Regulator_Linear:AMS1117-3.3", "AMS1117-3.3", "Package_TO_SOT_SMD:SOT-223-3_TabPin2", 127.0, 132.08,
     {"3": "+5V", "2": "+3V3", "1": "GND"}, fields={"ref": (-5.08, -7.62), "val": (-5.08, -5.08)})
C("10uF 25V", "+5V", "GND", 154.94, 134.62, FP_C1206)                                     # C9
C("22uF 16V", "+3V3", "GND", 175.26, 134.62, FP_C1206)                                    # C10
C("100nF", "+3V3", "GND", 195.58, 134.62)                                                 # C11
R("1k", "+3V3", "LED_A", 215.9, 129.54)                                                   # R9
part("LED1", "Device:LED", "LED hijau", "LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder",
     241.3, 139.7, {"2": "LED_A", "1": "GND"})

# ---- 2. ESP32 + USB ----
part("J4", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C 16 pin",
     "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", 35.56, 218.44,
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND",
      "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2",
      "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM", "A8": "NC", "B8": "NC"})
R("5.1k", "CC1", "GND", 68.58, 264.16)                                                    # R10
R("5.1k", "CC2", "GND", 88.9, 264.16)                                                     # R11
part("U2", "lfm-x2:CH340C_3V3", "CH340C", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", 101.6, 215.9,
     {"16": None, "4": None, "1": "GND", "5": "USB_DP", "6": "USB_DM", "2": "ESP_RX", "3": "ESP_TX",
      "13": "DTR", "14": "RTS", "9": "NC", "10": "NC", "11": "NC", "12": "NC", "15": "NC", "7": "NC", "8": "NC"},
     fields={"ref": (-10.16, -13.97), "val": (2.54, -13.97)})
C("100nF", "+3V3", "GND", 111.76, 264.16)                                                 # C12
# auto-reset (rangkaian DevKit): DTR/RTS dari CH340C menarik EN dan IO0 lewat dua NPN
R("10k", "DTR", "Q2_B", 139.7, 180.34)                                                    # R12
part("Q2", "Transistor_BJT:SS8050", "SS8050", FP_SOT23, 160.02, 187.96, {"1": "Q2_B", "2": "RTS", "3": "EN"},
     fields="right_far")
R("10k", "RTS", "Q3_B", 139.7, 226.06)                                                    # R13
part("Q3", "Transistor_BJT:SS8050", "SS8050", FP_SOT23, 160.02, 233.68, {"1": "Q3_B", "2": "DTR", "3": "IO0"},
     fields="right_far")
part("U1", "RF_Module:ESP32-WROOM-32E", "ESP32-WROOM-32E", "RF_Module:ESP32-WROOM-32E", 210.82, 228.6,
     {"2": "+3V3", "[1,15,38,39]": "GND", "3": "EN", "4": "MUX_SIG", "5": "VBAT_SENSE", "6": "BTN", "7": "BTN2",
      "8": "MUX_S3", "9": "MUX_S2", "10": "MUX_S1", "11": "MUX_S0", "12": "NC", "13": "ENC_L_B", "14": "BUZ",
      "16": "ENC_L_A", "17": "NC", "18": "NC", "19": "NC", "20": "NC", "21": "NC", "22": "NC", "23": "NC",
      "24": "DRV_EN", "25": "IO0", "26": "MR_IN2", "27": "MR_IN1", "28": "ML_IN2", "29": "NC", "30": "ML_IN1",
      "31": "ENC_R_B", "32": "NC", "33": "SDA", "34": "ESP_RX", "35": "ESP_TX", "36": "SCL", "37": "ENC_R_A"},
     fields={"ref": (-15.24, -34.29), "val": (2.54, -34.29)})
R("10k", "+3V3", "EN", 254.0, 180.34)                                                     # R14
C("1uF", "EN", "GND", 274.32, 180.34)                                                     # C13
part("SW8", "Switch:SW_Push", "RST", FP_BTN, 264.16, 205.74, {"1": "EN", "2": "GND"})
R("10k", "+3V3", "IO0", 254.0, 228.6)                                                     # R15
part("SW9", "Switch:SW_Push", "BOOT", FP_BTN, 264.16, 254.0, {"1": "IO0", "2": "GND"})
C("10uF 25V", "+3V3", "GND", 254.0, 276.86, FP_C1206)                                     # C14
C("100nF", "+3V3", "GND", 274.32, 276.86)                                                 # C15

# ---- 3. DRIVER MOTOR: 4x BTN7971B, tiap chip setengah H-bridge ----
# resistor seri IN/INH 4,7k (datasheet 10k untuk logika 5 V; diperkecil karena logika ESP32 3,3 V), R_SR 1k (0-51k),
# R_IS 1k ke GND (IS tidak dibaca), 470 nF di VS tiap chip
BTN = [("U6", "ML_IN1", "ML_P", 368.3, 45.72), ("U7", "ML_IN2", "ML_N", 502.92, 45.72),
       ("U8", "MR_IN1", "MR_P", 368.3, 96.52), ("U9", "MR_IN2", "MR_N", 502.92, 96.52)]
for ref, sin, sout, cx, cy in BTN:
    part(ref, "lfm-x2:BTN7971B", "BTN7971B", FP_TO263, cx, cy,
         {"1": "GND", "2": f"{ref}_IN", "3": f"{ref}_INH", "4": sout, "8": sout, "5": f"{ref}_SR", "6": f"{ref}_IS",
          "7": "VBAT"}, fields={"ref": (7.62, -8.89), "val": (7.62, -6.35)})
    R("4.7k", sin, f"{ref}_IN", cx - 60.96, cy)
    R("4.7k", "DRV_EN", f"{ref}_INH", cx - 38.1, cy)
    R("1k", f"{ref}_SR", "GND", cx + 22.86, cy)
    R("1k", f"{ref}_IS", "GND", cx + 40.64, cy)
    C("470nF", "VBAT", "GND", cx + 55.88, cy)
R("10k", "DRV_EN", "GND", 314.96, 142.24)                                                 # tahan driver tidur saat boot
MOTOR_FP = "Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical"
part("J2", "Connector_Generic:Conn_01x06", "Motor kiri + encoder", MOTOR_FP, 381.0, 139.7,
     {"1": "ML_P", "2": "+3V3", "3": "ENC_L_A", "4": "ENC_L_B", "5": "GND", "6": "ML_N"})
part("J3", "Connector_Generic:Conn_01x06", "Motor kanan + encoder", MOTOR_FP, 469.9, 139.7,
     {"1": "MR_P", "2": "+3V3", "3": "ENC_R_A", "4": "ENC_R_B", "5": "GND", "6": "MR_N"})

# ---- 4. SENSOR GARIS: 12x QRE1113GR + mux (sama dengan PCB sensor rev B: S1-S12 = I2-I13) ----
for i in range(12):
    sx, sy = 302.26 + (i % 6) * 45.72, 190.5 + (i // 6) * 48.26
    n = i + 1
    part(f"IR{n}", "Sensor_Proximity:QRE1113GR", "QRE1113GR", "OptoDevice:OnSemi_CASE100CY", sx + 22.86, sy,
         {"1": f"A{n}", "2": "GND", "3": f"S{n}", "4": "GND"})
    R("220", "+5V", f"A{n}", sx + 10.16, sy + 20.32)
    R("10k", "+3V3", f"S{n}", sx + 30.48, sy + 20.32)
MUX = {"1": "MUX_SIG", "10": "MUX_S0", "11": "MUX_S1", "14": "MUX_S2", "13": "MUX_S3", "15": "GND", "24": "+3V3",
       "12": "GND", "9": "NC", "8": "NC", "17": "NC", "16": "NC"}
for n, p in enumerate(["7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18"], 1):   # I2..I13
    MUX[p] = f"S{n}"
part("U5", "74xx:CD74HC4067M", "CD74HC4067M", "Package_SO:SOIC-24W_7.5x15.4mm_P1.27mm", 342.9, 322.58, MUX)
C("100nF", "+3V3", "GND", 391.16, 322.58)

# ---- 5. ANTARMUKA: OLED, 6 tombol menu, buzzer ----
part("J5", "Connector_Generic:Conn_01x04", "OLED 0,96 I2C", "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
     45.72, 327.66, {"1": "GND", "2": "+3V3", "3": "SCL", "4": "SDA"})
# tangga resistor 5 tombol di GPIO34: nilai sama dengan board interface jalur utama (firmware sama)
LADDER = [("ATAS", "1k"), ("BAWAH", "3.9k"), ("KEMBALI", "8.2k"), ("OK", "18k"), ("LANJUT", "39k")]
for i, (fn, rv) in enumerate(LADDER, 1):
    x = 83.82 + (i - 1) * 30.48
    part(f"SW{i + 1}", "Switch:SW_Push", fn, FP_BTN, x, 325.12, {"1": "BTN", "2": f"B{i}"})
    R(rv, f"B{i}", "GND", x + 7.62, 345.44)
R("10k", "+3V3", "BTN", 238.76, 325.12)
C("100nF", "BTN", "GND", 259.08, 325.12)
part("SW7", "Switch:SW_Push", "START", FP_BTN, 83.82, 378.46, {"1": "BTN2", "2": "GND"})   # tombol ke-6 di GPIO35
R("10k", "+3V3", "BTN2", 114.3, 378.46)
C("100nF", "BTN2", "GND", 134.62, 378.46)
RB = R("1k", "BUZ", None, 198.12, 368.3)
RP = R("10k", None, "GND", 205.74, 383.54)
part("Q4", "Transistor_BJT:SS8050", "SS8050", FP_SOT23, 223.52, 375.92, {"1": None, "3": None, "2": "GND"},
     fields="right_far")
part("BZ1", "Device:Buzzer", "Buzzer aktif 5V", "Buzzer_Beeper:Buzzer_12x9.5RM7.6", 233.68, 359.41,
     {"1": {"net": "+5V", "pdir": 90}, "2": None}, fields="right_far")

# kotak blok + judul + catatan: (x0, y0, x1, y1, judul, [(x, y, teks), ...])
BLOCKS = [
    (12.7, 12.7, 292.1, 152.4, "1. DAYA", [
        (15.24, 22.86, "J1: pack Li-ion 2S (6,0-8,4 V). Pin 1 = BAT+, tanpa proteksi polaritas terbalik."),
        (60.96, 60.96, "Q1 + SW1: saklar daya. SW1 ke GND = hidup (Vgs = -0,91 x VBAT).\n"
                       "SW1 hanya dialiri arus gate, arus motor lewat Q1 (maks kontinu +-2 A)."),
        (236.22, 64.77, "VBAT_SENSE ke GPIO39:\nVBAT x 33/133 (8,4 V -> 2,08 V)"),
        (15.24, 116.84, "U4 buck 5,3 V: R6/R7 = 0,8 V x (1 + 220k/39k). R5 100k -> +-900 kHz. EN dibiarkan lepas = aktif.\n"
                        "Nilai lain dari datasheet MP1584 gambar 4 (5 V): L 15 uH, C3 150 pF, R3 100k."),
        (15.24, 147.32, "D2/D3: +5V dari buck atau USB (yang lebih tinggi). 5,3 V - 0,35 V = +-5,0 V."),
        (228.6, 121.92, "PWR_FLAG: VBAT, +5V, GND"),
    ]),
    (12.7, 157.48, 292.1, 297.18, "2. ESP32-WROOM-32E + USB (CH340C, auto-reset)", [
        (15.24, 284.48, "J4: R10/R11 5,1k di CC = perangkat USB (dapat 5 V dari laptop/charger).\n"
                        "U2 dicatu 3,3 V: V3 disambung ke VCC (datasheet CH340)."),
        (132.08, 255.27, "Q2/Q3: auto-reset saat upload\n(DTR, RTS -> EN, IO0)"),
        (132.08, 274.32, "IO2 (DRV_EN) dan IO12 (BUZ) ditarik ke GND:\nsyarat boot ESP32. IO5, IO15, IO27 kosong."),
        (246.38, 289.56, "C14/C15 dekat pin 3V3 U1"),
    ]),
    (297.18, 12.7, 581.66, 160.02, "3. DRIVER MOTOR: 4x BTN7971B (setengah H-bridge, 2 per motor)", [
        (406.4, 127.0, "Maju: IN1 = PWM, IN2 = 0. Mundur: IN1 = 0, IN2 = PWM. Rem: IN1 = IN2.\n"
                       "DRV_EN (GPIO2) = INH keempat chip: LOW = tidur, keluaran lepas."),
        (502.92, 142.24, "J2/J3 = urutan pin jalur utama:\n1 M+, 2 3V3, 3 ENC A, 4 ENC B, 5 GND, 6 M-"),
    ]),
    (297.18, 165.1, 581.66, 358.14, "4. SENSOR GARIS: 12x QRE1113GR + CD74HC4067M", [
        (411.48, 304.8, "Sama dengan PCB sensor rev B: LED IR selalu nyala (220 ohm dari +5V, +-17 mA),\n"
                        "kolektor ditarik 10k ke +3V3, S1..S12 = I2..I13. I0, I1, I14, I15 kosong.\n"
                        "IR1 = paling kiri, IR12 = paling kanan (dilihat dari atas, robot menghadap depan)."),
    ]),
    (12.7, 302.26, 292.1, 406.4, "5. ANTARMUKA: OLED, 6 TOMBOL, BUZZER", [
        (15.24, 396.24, "J5: cek urutan pin modul OLED (GND VCC SCL SDA)."),
        (60.96, 311.15, "Tangga resistor di GPIO34 (pull-up 10k): ATAS 0,30 V, BAWAH 0,93 V, KEMBALI 1,49 V, OK 2,12 V, "
                        "LANJUT 2,63 V, lepas 3,3 V"),
        (60.96, 365.76, "START: tombol ke-6, sendiri di GPIO35"),
        (238.76, 388.62, "R pull-down menjaga GPIO12\nLOW saat boot"),
    ]),
    (297.18, 363.22, 398.78, 406.4, "PIN ESP32 (beda dari jalur utama: motor)", [
        (299.72, 388.62, "ML_IN1 18, ML_IN2 17, MR_IN1 16, MR_IN2 4, DRV_EN 2\n"
                         "MUX_SIG 36, S0-S3 26/25/33/32, VBAT_SENSE 39\n"
                         "BTN 34, BTN2 35, BUZ 12, SDA 21, SCL 22\n"
                         "ENC_L A/B 13/14, ENC_R A/B 23/19"),
    ]),
]

# ============================== GEOMETRI ==============================
LIB = {}


def lib(lib_id):
    if lib_id not in LIB:
        LIB[lib_id] = kisym.load(lib_id, [DIR])
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
if len(PARTMAP) != len(PARTS):
    raise SystemExit("referensi kembar")


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
    sudah = set()                                  # pin bertumpuk (VBUS/GND USB-C, OUT BTN7971B): satu kabel saja
    for q in lib(p["lib_id"])[1]:
        spec = p["nets"].get(q["num"], "MISSING")
        if spec == "MISSING":
            raise SystemExit(f"pin {p['ref']}.{q['num']} ({q['name']}) belum diberi net")
        at = to_sch(p["x"], p["y"], q["x"], q["y"])
        if spec is None:
            continue
        kunci = (at, spec if isinstance(spec, str) else spec["net"])
        if kunci in sudah:
            continue
        sudah.add(kunci)
        if spec == "NC":
            NCS.append(at)
            continue
        attach(at, outward(q), spec)
    lebih = set(p["nets"]) - {q["num"] for q in lib(p["lib_id"])[1]}
    if lebih:
        raise SystemExit(f"{p['ref']}: pin tidak ada di simbol: {sorted(lebih)}")


# ---- sambungan manual ----
def pembagi(r_atas, r_bawah, net, dx=5.08):
    """dua resistor tegak bersusun: titik tengah diberi label net"""
    a, b = pin(r_atas, "2"), pin(r_bawah, "1")
    mid = (a[0], round((a[1] + b[1]) / 2 / 1.27) * 1.27)
    wire(a, mid), wire(mid, b), JUNCS.append(mid)
    wire(mid, (mid[0] + dx, mid[1])), label(net, (mid[0] + dx, mid[1]), 0)


pembagi("R3", "R4", "VBAT_SENSE")                  # pembagi tegangan baterai
pembagi("R6", "R7", "BUCK_FB")                     # umpan balik buck
wire(pin("R8", "2"), pin("C8", "1"))               # kompensasi buck: R8 seri C8
g5, g9 = pin("U4", "5"), pin("U4", "9")            # GND dan pad bawah MP1584: satu simbol GND
wire(g5, (g5[0], g5[1] + STUB)), wire(g9, (g9[0], g9[1] + STUB)), wire((g5[0], g5[1] + STUB), (g9[0], g9[1] + STUB))
power("GND", (g5[0], g5[1] + STUB), 270)

# CH340C: V3 disambung ke VCC, keduanya ke +3V3
vcc, v3 = pin("U2", "16"), pin("U2", "4")
wire(vcc, (vcc[0], vcc[1] - STUB)), wire(v3, (v3[0], v3[1] - STUB)), wire((vcc[0], vcc[1] - STUB), (v3[0], v3[1] - STUB))
power("+3V3", (vcc[0], vcc[1] - STUB), 90)

# buzzer: BUZ - RB - basis Q4, RP basis ke GND, kolektor ke kaki - buzzer
r3b, qb, r4t = pin(RB, "2"), pin("Q4", "1"), pin(RP, "1")
k1 = (r3b[0], qb[1])
wire(r3b, k1), wire(k1, (r4t[0], qb[1])), wire((r4t[0], qb[1]), qb), wire((r4t[0], qb[1]), r4t)
JUNCS.append((r4t[0], qb[1]))
qc, bzn = pin("Q4", "3"), pin("BZ1", "2")
wire(bzn, (qc[0], bzn[1])), wire((qc[0], bzn[1]), qc)

# PWR_FLAG untuk VBAT, +5V, GND (daya datang dari konektor, MOSFET, dan dioda, bukan pin keluaran daya)
for net, y in (("VBAT", 127.0), ("+5V", 134.62), ("GND", 142.24)):
    fl = (266.7, y)
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


old = open(SCH, encoding="utf8").read() if os.path.exists(SCH) else ""
m_uuid = re.search(r'\(uuid "([^"]+)"\)', old)
root_uuid = m_uuid.group(1) if m_uuid else uid()
if "(lib_id" in old and "--paksa" not in sys.argv:
    raise SystemExit("skematik sudah berisi simbol; pakai --paksa kalau memang mau ditimpa")
# UUID simbol dipertahankan antar-jalan (kunci = referensi): footprint di PCB terikat ke UUID ini (F8 tidak membuat ulang)
OLD_UUID = {}
for m in re.finditer(r'\(symbol\s+\(lib_id "[^"]*"\).*?\(uuid "([^"]+)"\)\s*\(property "Reference" "([^"]+)"', old, re.S):
    OLD_UUID[m.group(2)] = m.group(1)


def lib_prop(blk, name):
    m = re.search(r'\(property "%s" "([^"]*)"\s*\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)' % name, blk)
    return (m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4) or 0)) if m else ("", 0, 0, 0)


def symbol(lib_id, ref, value, fp, X, Y, r=0, fields="lib", hide_ref=False, hide_val=False):
    blk, pins = lib(lib_id)
    _, rx, ry, ra = lib_prop(blk, "Reference")
    _, vx, vy, va = lib_prop(blk, "Value")
    ds = lib_prop(blk, "Datasheet")[0]
    if isinstance(fields, dict):                   # posisi sendiri: {"ref": (dx, dy), "val": (dx, dy)}, rata kiri
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
         f'\t\t(uuid "{OLD_UUID.get(ref) or uid()}")',
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
out.append(f'\t(uuid "{root_uuid}")\n\t(paper "A2")')
out.append('\t(title_block\n\t\t(title "LFM X2 - PCB all-in-one full SMD")\n\t\t(date "2026-11-15")\n\t\t(rev "A")\n'
           '\t\t(company "Side project LFM (di luar RAB PjBL)")\n'
           '\t\t(comment 1 "Penjelasan, BOM, dan catatan routing: hardware/lfm-x2/README.md")\n'
           '\t\t(comment 2 "Dibuat oleh hardware/tools/gen_sch_x2.py")\n\t)')
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
os.makedirs(DIR, exist_ok=True)
open(SCH, "w", encoding="utf8", newline="\n").write("\n".join(out))
print(f"ditulis {SCH}: {len(PARTS)} komponen, {len(LABELS)} label, {len(WIRES)} kabel, {len(NCS)} NC")

# daftar net yang diharapkan (dibandingkan dengan netlist KiCad oleh cek_net_x2.py): "REF.PIN" -> net.
# Pin yang disambung manual (None) ditulis di MANUAL; pin NC tidak ditulis.
MANUAL = {"R3.2": "VBAT_SENSE", "R4.1": "VBAT_SENSE", "R6.2": "BUCK_FB", "R7.1": "BUCK_FB", "U2.16": "+3V3",
          "U2.4": "+3V3", "U4.5": "GND", "U4.9": "GND", "R8.2": "*kompensasi", "C8.1": "*kompensasi", f"{RB}.2": "*basis", f"{RP}.1": "*basis",
          "Q4.1": "*basis", "Q4.3": "*buzzer", "BZ1.2": "*buzzer"}       # *nama = net tanpa label (harus satu net)
harap = dict(MANUAL)
for p in PARTS:
    for num, spec in p["nets"].items():
        if isinstance(spec, dict):
            spec = spec["net"]
        if spec and spec != "NC":
            for n in (num.strip("[]").split(",") if num.startswith("[") else [num]):
                harap[f"{p['ref']}.{n}"] = spec
with open(os.path.join(DIR, "net-harapan.json"), "w", encoding="utf8", newline="\n") as fh:
    json.dump(dict(sorted(harap.items())), fh, indent=1)

# ============================== FILE PROYEK ==============================
# dibuat sekali (tidak ditimpa): aturan cetak disalin dari proyek PCB utama, kelas net disesuaikan untuk X2
TABEL = os.path.join(DIR, "sym-lib-table")
if not os.path.exists(TABEL):
    open(TABEL, "w", encoding="utf8", newline="\n").write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "lfm-x2")(type "KiCad")(uri "${KIPRJMOD}/lfm-x2.kicad_sym")'
        '(options "")(descr "LFM X2: BTN7971B, CH340C catu 3,3 V, MP1584EN"))\n)\n')
PRO = os.path.join(DIR, "lfm-x2.kicad_pro")
if not os.path.exists(PRO):
    pro = json.load(open(os.path.join(ROOT, "hardware", "pcb-utama", "pcb-utama.kicad_pro"), encoding="utf8"))
    pro["meta"]["filename"] = "lfm-x2.kicad_pro"
    ns = pro["net_settings"]
    dasar = {k: v for k, v in ns["classes"][1].items() if k not in ("name", "track_width")}
    ns["classes"] = [ns["classes"][0], dict(dasar, name="Daya", track_width=0.5),
                     dict(dasar, name="Daya besar", track_width=1.2)]
    ns["netclass_patterns"] = (
        [{"netclass": "Daya", "pattern": n} for n in ("+5V", "+3V3", "GND", "+5V_BUCK", "VBUS")]
        + [{"netclass": "Daya besar", "pattern": n} for n in ("VBAT", "BAT+", "BUCK_SW", "ML_P", "ML_N", "MR_P", "MR_N")])
    ds = pro["board"]["design_settings"]
    ds["track_widths"] = [0.0, 0.3, 0.5, 1.2, 2.0]
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 1.3, "drill": 0.6}]
    # emitor fototransistor QRE1113 (tipe open emitter) memang ke GND, dan GND diberi PWR_FLAG: bukan kesalahan
    pro["erc"]["pin_map"][8][10] = pro["erc"]["pin_map"][10][8] = 0
    pro["sheets"] = [[root_uuid, "Root"]]
    pro["schematic"]["top_level_sheets"] = [{"filename": "lfm-x2.kicad_sch", "name": "Root", "uuid": root_uuid}]
    pro["schematic"].pop("used_designators", None)
    json.dump(pro, open(PRO, "w", encoding="utf8", newline="\n"), indent=2)
    print(f"ditulis {PRO}")
