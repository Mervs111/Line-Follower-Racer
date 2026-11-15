"""Cek netlist skematik LFM X2 terhadap daftar net di gen_sch_x2.py (hardware/lfm-x2/net-harapan.json).

Mengekspor netlist lewat kicad-cli lalu membandingkan tiap pin: menangkap kabel/label yang tidak sengaja tersambung
atau terlepas saat skematik digambar generator maupun sesudah diedit di Eeschema.

Jalankan dari folder repo: py hardware/tools/cek_net_x2.py [netlist.net]
"""
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kisym  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DIR = os.path.join(ROOT, "hardware", "lfm-x2")


def baca(path):
    """netlist kicadsexpr -> {"REF.PIN": net}, jumlah komponen"""
    teks = open(path, encoding="utf8").read()
    got = {}
    bagian = teks[teks.index("(nets"):]
    for blok in re.split(r'\(net\s+\(code', bagian)[1:]:
        nama = re.search(r'\(name "([^"]*)"\)', blok).group(1).lstrip("/")
        for nd in re.finditer(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', blok):
            got[f"{nd.group(1)}.{nd.group(2)}"] = nama
    return got, len(re.findall(r'\(comp\s+\(ref ', teks))


def main():
    if len(sys.argv) > 1:
        net = sys.argv[1]
    else:
        net = os.path.join(tempfile.mkdtemp(), "lfm-x2.net")
        subprocess.run([kisym.KICAD_CLI, "sch", "export", "netlist", "-o", net, os.path.join(DIR, "lfm-x2.kicad_sch")],
                       check=True, capture_output=True)
    got, n_comp = baca(net)
    harap = json.load(open(os.path.join(DIR, "net-harapan.json"), encoding="utf8"))
    salah = 0
    alias = {}                                     # net tanpa label (*nama): semua pinnya harus di satu net yang sama
    for k, v in harap.items():
        g = got.get(k)
        if v.startswith("*"):
            if g is None or alias.setdefault(v, g) != g:
                print(f"SALAH {k}: harus satu net dengan {v}, dapat {g}"); salah += 1
        elif g != v:
            print(f"SALAH {k}: harus {v}, dapat {g}"); salah += 1
    # tiap net hanya boleh berisi pin yang memang diharapkan di net itu (tidak ada net yang menyatu)
    balik = {}
    for k, v in harap.items():
        balik.setdefault(alias.get(v, v), set()).add(k)
    for k, g in got.items():
        if k not in harap and not g.startswith("unconnected-"):
            print(f"TAK TERDUGA {k} di net {g}"); salah += 1
    for nama, pins in balik.items():
        lain = {k for k, g in got.items() if g == nama} - pins
        if lain:
            print(f"MENYATU net {nama}: pin asing {sorted(lain)}"); salah += 1
    print(f"{n_comp} komponen, {len(harap)} pin dicek, {len(set(got.values()))} net: "
          + ("SEMUA COCOK" if salah == 0 else f"{salah} SALAH"))
    return 1 if salah else 0


if __name__ == "__main__":
    sys.exit(main())
