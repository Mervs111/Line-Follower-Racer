"""Membuat pustaka simbol proyek LFM X2 (hardware/lfm-x2/lfm-x2.kicad_sym), KiCad 10.

Isi:
- BTN7971B   : salinan simbol KiCad Power_Management:BTN8982TA (keluarga NovalithIC, kemasan dan urutan pin sama:
               1 GND, 2 IN, 3 INH, 4 + tab OUT, 5 SR, 6 IS, 7 VS), nama dan datasheet diganti.
- CH340C_3V3 : salinan Interface_USB:CH340C dengan pin V3 dijadikan pasif. Pada catu 3,3 V pin V3 wajib disambung ke
               VCC (datasheet CH340 bagian 5); di simbol asli V3 bertipe keluaran daya sehingga ERC menganggapnya
               bentrok dengan keluaran regulator 3,3 V.
- MP1584EN   : simbol baru (KiCad tidak punya). Urutan pin SOIC-8 dari datasheet MPS: 1 SW, 2 EN, 3 COMP, 4 FB,
               5 GND, 6 FREQ, 7 VIN, 8 BST, 9 = pad bawah (GND).

Jalankan dari folder repo: py hardware/tools/gen_lib_x2.py
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kisym  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "hardware", "lfm-x2", "lfm-x2.kicad_sym")
EFF = "(effects (font (size 1.27 1.27)))"
HID = "(effects (font (size 1.27 1.27)) (hide yes))"


def turunan(lib_id, nama, ganti=()):
    """salin simbol pustaka KiCad dengan nama baru; ganti = [(pola regex, pengganti), ...]"""
    lib, lama = lib_id.split(":")
    blk, _ = kisym.load(lib_id)
    blk = re.sub(r'\(symbol "%s_(\d+_\d+)"' % re.escape(lama), r'(symbol "%s_\1"' % nama, blk)
    blk = blk.replace(f'"{lib_id}"', f'"{nama}"', 1)
    for pola, baru in ganti:
        blk, n = re.subn(pola, baru, blk, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"{nama}: pola tidak ketemu: {pola}")
    return blk


def prop(nama, isi, x=0.0, y=0.0, tampil=False, rata=None):
    eff = HID if not tampil else (f"(effects (font (size 1.27 1.27)) (justify {rata}))" if rata else EFF)
    return f'\t\t(property "{nama}" "{isi}" (at {x} {y} 0) {eff})'


def pin(tipe, x, y, sudut, nama, nomor):
    return (f'\t\t\t(pin {tipe} line (at {x} {y} {sudut}) (length 2.54) '
            f'(name "{nama}" {EFF}) (number "{nomor}" {EFF}))')


def mp1584en():
    s = ['\t(symbol "MP1584EN" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
         prop("Reference", "U", -10.16, 11.43, True, "left bottom"),
         prop("Value", "MP1584EN", 1.27, 11.43, True, "left bottom"),
         prop("Footprint", "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm"),
         prop("Datasheet", "https://www.monolithicpower.com/en/mp1584.html"),
         prop("Description", "Buck 3 A, 4,5-28 V, frekuensi 100 kHz-1,5 MHz, SOIC-8 dengan pad bawah"),
         prop("ki_keywords", "buck step-down MPS"),
         prop("ki_fp_filters", "SOIC*1EP*3.9x4.9mm*P1.27mm*"),
         '\t\t(symbol "MP1584EN_0_1"',
         '\t\t\t(rectangle (start -10.16 10.16) (end 10.16 -10.16) (stroke (width 0.254) (type default)) '
         '(fill (type background)))',
         '\t\t)',
         '\t\t(symbol "MP1584EN_1_1"',
         pin("power_in", -12.7, 7.62, 0, "VIN", 7),
         pin("input", -12.7, 2.54, 0, "EN", 2),
         pin("passive", -12.7, -2.54, 0, "FREQ", 6),
         pin("passive", 12.7, 7.62, 180, "BST", 8),
         pin("passive", 12.7, 2.54, 180, "SW", 1),
         pin("input", 12.7, -2.54, 180, "FB", 4),
         pin("passive", 12.7, -7.62, 180, "COMP", 3),
         pin("power_in", -2.54, -12.7, 90, "GND", 5),
         pin("passive", 2.54, -12.7, 90, "EP", 9),
         '\t\t)',
         '\t)']
    return "\n".join(s)


def main():
    btn = turunan("Power_Management:BTN8982TA", "BTN7971B", [
        (r'\(property "Value" "BTN8982TA"', '(property "Value" "BTN7971B"'),
        (r'\(property "Datasheet" "[^"]*"',
         '(property "Datasheet" "https://www.infineon.com/cms/en/product/power/motor-control-ics/'
         'brushed-dc-motor-driver-ics/single-half-bridge-ics/btn7971b/"'),
        (r'\(property "Description" "[^"]*"',
         '(property "Description" "Setengah H-bridge arus besar NovalithIC, TO-263-7 (2 chip per motor)"'),
    ])
    ch340 = turunan("Interface_USB:CH340C", "CH340C_3V3", [
        (r'\(property "Value" "CH340C"', '(property "Value" "CH340C"'),
        (r'\(pin power_out (\w+)(\s*\(at [^)]*\)\s*\(length [^)]*\)\s*\(name "V3")', r'(pin passive \1\2'),
    ])
    teks = ('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "kicad_symbol_editor")\n'
            '\t(generator_version "10.0")\n' + "\n".join(["\t" + btn, "\t" + ch340, mp1584en()]) + "\n)\n")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf8", newline="\n").write(teks)
    # dirapikan ke format simpan KiCad 10 (sekaligus memastikan pustakanya bisa dimuat)
    subprocess.run([kisym.KICAD_CLI, "sym", "upgrade", "--force", OUT], check=True, capture_output=True)
    print(f"ditulis {OUT}")


if __name__ == "__main__":
    main()
