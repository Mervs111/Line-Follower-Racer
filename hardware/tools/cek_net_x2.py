"""Cek skematik LFM X2 rev B (4 papan) terhadap daftar net dari gen_sch_x2.py (<papan>/net-harapan.json).

Per papan: ERC kicad-cli, lalu netlist dibandingkan per pin, jadi kabel/label yang tidak sengaja tersambung atau
terlepas (saat digambar generator maupun sesudah diedit di Eeschema) ketahuan. Terakhir: konektor antar-papan harus
membawa net yang sama di kedua sisi (utama J3-sensor J1, utama J4-antarmuka J1, utama J5-driver J1).

Jalankan dari folder repo: py hardware/tools/cek_net_x2.py [papan ...]
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
X2 = os.path.join(ROOT, "hardware", "lfm-x2")
PAPAN = ["utama", "antarmuka", "driver", "sensor"]
# (papan, ref) pasangan konektor: pin yang sama harus membawa net yang sama
PASANGAN = [(("utama", "J3"), ("sensor", "J1")), (("utama", "J4"), ("antarmuka", "J1")),
            (("utama", "J5"), ("driver", "J1"))]


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


def erc(sch):
    rpt = os.path.join(tempfile.mkdtemp(), "erc.rpt")
    subprocess.run([kisym.KICAD_CLI, "sch", "erc", "--severity-all", "-o", rpt, sch], capture_output=True)
    teks = open(rpt, encoding="utf8").read()
    m = re.search(r"\*\* ERC messages: (\d+)", teks)
    n = int(m.group(1)) if m else -1
    if n:
        print(teks[teks.find("***"):][:3000])
    return n


def cek(papan):
    d = os.path.join(X2, papan)
    sch = os.path.join(d, f"lfm-x2-{papan}.kicad_sch")
    net = os.path.join(tempfile.mkdtemp(), f"{papan}.net")
    subprocess.run([kisym.KICAD_CLI, "sch", "export", "netlist", "-o", net, sch], check=True, capture_output=True)
    got, n_comp = baca(net)
    harap = json.load(open(os.path.join(d, "net-harapan.json"), encoding="utf8"))
    salah = 0
    alias = {}                                     # net tanpa label (*nama): semua pinnya harus di satu net yang sama
    for k, v in harap.items():
        g = got.get(k)
        if v.startswith("*"):
            if g is None or alias.setdefault(v, g) != g:
                print(f"  SALAH {k}: harus satu net dengan {v}, dapat {g}"); salah += 1
        elif g != v:
            print(f"  SALAH {k}: harus {v}, dapat {g}"); salah += 1
    # tiap net hanya boleh berisi pin yang memang diharapkan di net itu (tidak ada net yang menyatu)
    balik = {}
    for k, v in harap.items():
        balik.setdefault(alias.get(v, v), set()).add(k)
    for k, g in got.items():
        if k not in harap and not g.startswith("unconnected-"):
            print(f"  TAK TERDUGA {k} di net {g}"); salah += 1
    for nama, pins in balik.items():
        lain = {k for k, g in got.items() if g == nama} - pins
        if lain:
            print(f"  MENYATU net {nama}: pin asing {sorted(lain)}"); salah += 1
    n_erc = erc(sch)
    print(f"{papan}: {n_comp} komponen, {len(harap)} pin, {len(set(got.values()))} net, ERC {n_erc}: "
          + ("SEMUA COCOK" if salah == 0 else f"{salah} SALAH"))
    return salah + (n_erc != 0), got


def main():
    pilih = [a for a in sys.argv[1:]] or PAPAN
    gagal, nets = 0, {}
    for p in pilih:
        g, nets[p] = cek(p)
        gagal += g
    for (pa, ra), (pb, rb) in PASANGAN:
        if pa not in nets or pb not in nets:
            continue
        sa = {k.split(".")[1]: v for k, v in nets[pa].items() if k.split(".")[0] == ra}
        sb = {k.split(".")[1]: v for k, v in nets[pb].items() if k.split(".")[0] == rb}
        beda = {p: (sa.get(p), sb.get(p)) for p in set(sa) | set(sb) if sa.get(p) != sb.get(p)}
        print(f"konektor {pa} {ra} <-> {pb} {rb}: {len(sa)} pin, " + ("cocok" if not beda else f"BEDA {beda}"))
        gagal += bool(beda)
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
