"""DSN papan utama LFM X2 rev B sebelum FreeRouting: kelas net (lebar + jarak longgar), keepout lubang, larangan
jalur/via sisi bawah di bawah badan modul ESP32, pad termal U1-39 dilepas dari net GND (tersambung lewat pour).

  py dsnfix_x2.py <in.dsn> <out.dsn> [jarak_um]

Jarak antar net default 400 um (aturan tempat cetak 254, proyek 300): makin longgar makin aman dicetak/disolder.
Net USB (pad konektor jarak 0,5 mm) tetap 300 um supaya jalur bisa keluar dari pad.
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
JARAK = int(sys.argv[3]) if len(sys.argv) > 3 else 400
s = open(src, encoding="utf8").read()

KELAS = [   # (nama, lebar um, jarak um, net)
    ("BESAR", 1000, JARAK, ["VBAT", "BAT+"]),                 # arus motor sampai +-3 A
    ("BUCKSW", 800, JARAK, ["BUCK_SW"]),
    ("DAYA", 500, JARAK, ["+5V", "+5V_BUCK", "VBUS", "+3V3", "GND"]),
    ("USB", 300, 300, ["USB_DP", "USB_DM", "CC1", "CC2"]),
]
khusus = {n for _, _, _, ns in KELAS for n in ns}
nets = re.findall(r'\(net ("[^"]+"|\S+)\s*\n\s*\(pins', s)
sisa = [n.strip('"') for n in nets if n.strip('"') not in khusus and not n.strip('"').startswith("unconnected")]


def kelas(nama, w, c, ns):
    q = " ".join(n if re.fullmatch(r"[A-Za-z0-9_+]+", n) else f'"{n}"' for n in ns)
    return (f"    (class {nama} {q}\n      (circuit\n        (use_via \"Via[0-1]_1300:600_um\")\n      )\n"
            f"      (rule\n        (width {w})\n        (clearance {c})\n      )\n    )\n")


baru = kelas("SINYAL", 300, JARAK, sisa) + "".join(kelas(*k) for k in KELAS)
s = re.sub(r"    \(class .*?\n    \)\n(?=    \(class|  \)\n  \(wiring)", "", s, flags=re.S)
s = s.replace("  )\n  (wiring", baru + "  )\n  (wiring", 1)
# jarak default papan (dipakai untuk pad/keepout tanpa kelas) ikut dilonggarkan
s = re.sub(r"(\(structure.*?\(rule\s*\(width \d+\)\s*\(clearance )\d+", rf"\g<1>{JARAK}", s, count=1, flags=re.S)

# lubang M3 (keepout lingkaran 3,7 mm dari footprint) -> 4,4 mm: tembaga >= 0,5 mm dari tepi lubang 3,2 mm
s = re.sub(r'\(keepout "" \(circle (F\.Cu|B\.Cu) 3700\)\)', r'(keepout "" (circle \1 4400))', s)

# sisi bawah di bawah badan ESP32 (antara baris pad 1-14, 25-38 dan kolom 15-24, sampai ujung antena): tanpa jalur
# dan via, supaya tidak ada tembaga terbuka yang tertindih modul. Koordinat KiCad X 158-183,05, Y 132,5-147,6.
kotak = "158000 -147600  183050 -147600  183050 -132500  158000 -132500  158000 -147600"
s = s.replace("    (via \"Via[0-1]_1300:600_um\")",
              f"    (keepout \"esp32_bawah\" (polygon B.Cu 0  {kotak}))\n    (via \"Via[0-1]_1300:600_um\")", 1)

# pad termal ESP32 (pin 39, 9 bagian) tidak dirouting: tersambung ke GND pour sisi bawah
s, n39 = re.subn(r"\s+U1-39(@\d+)?(?=[\s)])", "", s)

open(dst, "w", encoding="utf8").write(s)
print(f"{len(sisa)} net sinyal, jarak {JARAK} um, {s.count('(keepout')} keepout, {n39} pad U1-39 dilepas")
