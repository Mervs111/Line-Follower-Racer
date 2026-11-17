"""tulis hardware/tools/autoroute/x2_fanout_utama.json: jalur tetap papan utama LFM X2 (fanout deret kanan ESP32,
C14, lajur MUX ke J3, GND USB-C, resistor CC). Jalankan dari akar repo: py hardware/tools/autoroute/x2_fanout_utama.py"""
import json, math

K = lambda x, y: (round(200 + x, 3), round(180.55 - y, 3))      # robot -> KiCad
C = 0.8                                                          # potongan sudut 45 derajat


def garis(pts, c=C):
    """polyline robot -> titik dengan sudut dipotong 45 derajat"""
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        a = math.hypot(x1 - x0, y1 - y0); b = math.hypot(x2 - x1, y2 - y1)
        ca, cb = min(c, a / 2), min(c, b / 2)
        out.append((x1 - (x1 - x0) / a * ca, y1 - (y1 - y0) / a * ca))
        out.append((x1 + (x2 - x1) / b * cb, y1 + (y2 - y1) / b * cb))
    out.append(pts[-1])
    return out


tracks, vias = [], []


def jalur(net, lay, pts, w=0.3, c=C):
    p = garis(pts, c)
    for (xa, ya), (xb, yb) in zip(p, p[1:]):
        if math.hypot(xb - xa, yb - ya) > 1e-6:
            tracks.append([net, lay, *K(xa, ya), *K(xb, yb), w])


PAD_X = 8.75
# kaki deret kanan yang naik ke sisi atas: (net, y kaki, x via). Via 1,3 mm berselang dua kolom; jalur kaki kolom B
# lewat di sela via kolom A (celah 0,47 mm).
for net, y, xv in [("+3V3", 51.44, 10.45), ("EN", 50.17, 11.45), ("MUX_SIG", 48.90, 10.45),
                   ("VBAT_SENSE", 47.63, 11.45), ("BTN", 46.36, 10.45), ("BTN2", 45.09, 11.45), ("BUZ", 38.74, 10.45)]:
    jalur(net, "B", [(PAD_X, y), (xv, y)], 0.5 if net == "+3V3" else 0.3)
    vias.append([net, *K(xv, y)])
# C14 (100 nF) di depan kaki 1, sisi bawah, pad GND di belakang langsung ke kaki 1 (GND); pad +3V3 di depan naik lewat
# via sendiri ke jalur +3V3 sisi atas (yang lewat depan daerah antena). Kantong ini tertutup daerah antena, jalur MUX,
# dan jalur +3V3/EN sisi atas, jadi GND C14 tidak bisa lewat via ke pour, dan pad C14 0805 terlalu lebar untuk jalur
# +3V3 dari via kaki 2 lewat di sampingnya.
jalur("+3V3", "B", [(10.85, 56.04), (10.45, 58.3)], 0.4, 0)
vias.append(["+3V3", *K(10.45, 58.3)])   # segaris via kaki 2: lajur x 11,1-12,45 bebas untuk EN
jalur("GND", "B", [(10.85, 53.96), (9.9, 52.71), (8.75, 52.71)], 0.5, 0)
# MUX_SIG: sisi atas, ke kanan lewat sela via kolom B, naik di x 12,6, belok di y 64,6 (di belakang lubang H6), masuk
# J3.8. Celah 3,6 mm antara daerah antena (y 61) dan belokan ini untuk +3V3 (kaki 2) dan EN (kaki 3) ke kiri.
jalur("MUX_SIG", "F", [(10.45, 48.9), (12.6, 48.9), (12.6, 64.6), (8.75, 64.6), (8.75, 73.2)], 0.3, 0.6)
# 4 MUX_S: sisi bawah, lajur x 12,6-14,4, belok ke kiri di y 61,6-63,4 (di antara daerah antena dan lubang H5), masuk J3
for net, y, x, yb, xj in [("MUX_S3", 43.82, 12.6, 61.6, -1.25), ("MUX_S2", 42.55, 13.2, 62.2, 1.25),
                          ("MUX_S1", 41.28, 13.8, 62.8, 3.75), ("MUX_S0", 40.01, 14.4, 63.4, 6.25)]:
    jalur(net, "B", [(PAD_X, y), (x, y), (x, yb), (xj, yb), (xj, 73.2)])

# GND USB-C: pad A1/B12 dan A12/B1 (deret dalam, diapit pad VBUS) langsung ke kaki pelindung SH di belakang/depannya.
# Lewat pour saja tidak pasti: jalur VBUS sisi atas di kiri pad memotong pour (17/11, router tidak melihat pour).
jalur("GND", "F", [(31.0, 41.75), (31.0, 40.68)], 0.4, 0)
jalur("GND", "F", [(31.0, 48.25), (31.0, 49.32)], 0.4, 0)
# Resistor CC (R10/R11 tegak di kiri ujung fanout USB-C): CC1/CC2 lurus masuk pad CC, pad GND ke kaki SH belakang/depan
# di sisi atas, lewat bawah/atas via VBUS. Via GND di jalur R10 turun ke kaki 1 (GND) CH340C di sisi bawah.
jalur("CC1", "F", [(28.6, 43.45), (26.9, 43.45)], 0.3, 0)
jalur("CC2", "F", [(28.6, 46.75), (26.9, 46.75)], 0.3, 0)
jalur("GND", "F", [(26.6, 41.2), (27.4, 40.4), (31.0, 40.4)], 0.4, 0)
jalur("GND", "B", [(27.95, 40.4), (26.94, 40.4)], 0.4, 0)
vias.append(["GND", *K(27.95, 40.4)])
jalur("GND", "F", [(26.6, 48.75), (27.45, 49.6), (31.0, 49.6)], 0.4, 0)

json.dump({"keterangan": "LFM X2 papan utama: fanout tetap deret kanan ESP32 (16/11). Via 1,3 mm kaki 2-7 dan 12 "
           "berselang dua kolom (x robot 10,45 / 11,45): +3V3, EN, BTN, BTN2, BUZ ke kiri lewat sisi atas di atas "
           "modul (+3V3 dan EN boleh lewat depan daerah antena), VBAT_SENSE ke pembagi di kanan atas, MUX_SIG di sisi "
           "atas ke J3.8 (belok di y 64,6). 4 MUX_S di sisi bawah (lajur x 12,6-14,4) belok ke kiri di depan "
           "daerah antena masuk J3.4-7. C14: GND langsung ke kaki 1, +3V3 lewat via sendiri. Pad GND USB-C, GND "
           "R10/R11, dan kaki 1 CH340C ke kaki SH J2; CC1/CC2 lurus ke R10/R11. Dipasang "
           "sesudah fanout USB-C, sebelum ekspor (x2_router.py pasang). Koordinat KiCad. Dibuat ulang dengan "
           "x2_fanout_utama.py; ubah bersama gen_pcb_x2.py kalau ESP32 atau J3 bergeser.",
           "tracks": tracks, "vias": vias},
          open("hardware/tools/autoroute/x2_fanout_utama.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
print(len(tracks), "segmen", len(vias), "via")
