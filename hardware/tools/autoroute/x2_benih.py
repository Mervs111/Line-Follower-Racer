"""Pindahkan hasil x2_cari ke ekspor lain dari papan yang sama (python sistem), sebagai titik awal `perbaiki`.

  py -I x2_benih.py <ekspor-lama.json> <jalur-lama.json> <ekspor-baru.json> <jalur-benih.json>

Dipakai saat ekspor baru berisi sambungan tambahan (mis. GND ikut dirouting, aturan cetak X1 20/11) atau outline
berubah tapi pad sama: rute lama dipetakan ke indeks sambungan yang sama di ekspor baru (net + kedua ujung sama),
sambungan baru dibiarkan kosong. `x2_cari.py perbaiki <ekspor-baru> <jalur-benih> <hasil>` lalu hanya membongkar rute
di sekitar tabrakan dan pad sambungan baru; rute lain tetap.
"""
import json
import sys


def kunci(p, a, b):
    return p["net"], json.dumps(p[a], sort_keys=True), json.dumps(p[b], sort_keys=True)


def main(lama, jalur, baru, out):
    e = json.load(open(lama, encoding="utf8"))
    g = json.load(open(baru, encoding="utf8"))
    j = json.load(open(jalur, encoding="utf8"))
    idx = {kunci(p, "A", "B"): i for i, p in enumerate(g["pasang"])}
    peta = {i: idx.get(kunci(p, "A", "B"), idx.get(kunci(p, "B", "A"))) for i, p in enumerate(e["pasang"])}
    hilang = [x["k"] for x in j["rute"] if peta.get(x["k"]) is None]
    j["rute"] = [dict(x, k=peta[x["k"]]) for x in j["rute"] if peta.get(x["k"]) is not None]
    json.dump(j, open(out, "w", encoding="utf8"))
    print(f"{len(j['rute'])} rute dipindah, {len(hilang)} tidak ada pasangannya, "
          f"{len(g['pasang']) - len(j['rute'])} sambungan dicari baru")


if __name__ == "__main__":
    main(*sys.argv[1:5])
