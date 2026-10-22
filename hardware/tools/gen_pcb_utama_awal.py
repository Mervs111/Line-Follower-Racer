"""Membuat proyek KiCad 10 awal untuk PCB utama baru (hardware/pcb-utama/), sekali jalan.

Isi yang dibuat:
- pcb-utama.kicad_pro: salinan setting proyek PCB sensor user (aturan cetak, net class), nama diganti.
- pcb-utama.kicad_sch: skematik kosong (A3), HANYA kalau belum ada / belum berisi simbol (skematik lengkap dibuat
  gen_sch_utama.py, tidak pernah ditimpa skrip ini).
- pcb-utama.kicad_pcb: setup papan dari PCB sensor + outline Edge.Cuts (bentuk "mobil F1" dari MAIN_R model 3D v16,
  jari-jari sudut per titik, 2 celah piringan encoder, 6 lubang M3) + gambar bantu penempatan di User.Drawings dan
  outline PCB sensor rev B di User.Comments.
- sym-lib-table / fp-lib-table: library ltm (ESP32 DevKit, modul TB6612, MP1584).

Koordinat SAMA dengan proyek PCB sensor: X KiCad = 200 + x robot, Y KiCad = Y0 - y robot (Y0 = tepi depan PCB sensor
+ 131), jadi lubang H1/H2 di kedua papan bernomor sama. Robot: x kanan, y maju, 0 = tengah poros roda.

Jalankan dari folder repo: py hardware/tools/gen_pcb_utama_awal.py   (tidak menimpa .kicad_pcb yang sudah ada kecuali
diberi --paksa; jangan pakai --paksa kalau PCB sudah berisi footprint/jalur buatan user).
"""
import math
import os
import re
import sys
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SENSOR = os.path.join(ROOT, "hardware", "sensor-garis", "sensor-garis")
OUTDIR = os.path.join(ROOT, "hardware", "pcb-utama")
NAME = "pcb-utama"
MODEL = os.path.join(ROOT, "mechanical", "cadquery", "ltm_v16.py")
FORCE = "--paksa" in sys.argv

KX0 = 200.0
F_SENSOR = 131.0                     # tepi depan PCB sensor di koordinat robot (F di ltm_v16.py)

pcb_src = open(SENSOR + ".kicad_pcb", encoding="utf8").read()
edges_src = re.findall(r'\n\t\((gr_line|gr_arc)\s+\(start ([\d.\-]+) ([\d.\-]+)\)\s*(?:\(mid ([\d.\-]+) ([\d.\-]+)\)\s*)?'
                       r'\(end ([\d.\-]+) ([\d.\-]+)\)[^()]*\(stroke[^()]*\([^()]*\)[^()]*\([^()]*\)\s*\)\s*'
                       r'\(layer "Edge\.Cuts"\)', pcb_src)
KY0 = min(min(float(e[2]), float(e[6])) for e in edges_src)
Y0 = KY0 + F_SENSOR


def k(x, y):
    """koordinat robot -> KiCad"""
    return (round(KX0 + x, 4), round(Y0 - y, 4))


# outline PCB utama dari model 3D (satu sumber: MAIN_R di ltm_v16.py)
model_src = open(MODEL, encoding="utf8").read()
MAIN_R = eval(re.search(r"^MAIN_R = (\[.*?\])", model_src, re.M).group(1))
MAIN_PTS = list(MAIN_R) + [(-x, y, r) for x, y, r in reversed(MAIN_R)]     # (x, y, jari-jari sudut)
HOLES = [(sx * 33.0, sy * 20.0) for sx in (-1, 1) for sy in (-1, 1)]       # tiang dudukan motor + baterai
SB_HOLES = [(float(a), float(b)) for a, b in re.findall(
    r'\(footprint "MountingHole[^"]*".*?\(at ([\d.\-]+) ([\d.\-]+)', pcb_src, re.S)]   # sudah koordinat KiCad
SLOTS = [(min(s * 10.2, s * 13.9), max(s * 10.2, s * 13.9), -6.6, 6.6) for s in (-1, 1)]   # celah piringan encoder


def uid():
    return str(uuid.uuid4())


def stroke(w=0.05):
    return f"\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type default)\n\t\t)\n"


def line(a, b, layer="Edge.Cuts", w=0.05):
    return (f"\t(gr_line\n\t\t(start {a[0]} {a[1]})\n\t\t(end {b[0]} {b[1]})\n{stroke(w)}"
            f"\t\t(layer \"{layer}\")\n\t\t(uuid \"{uid()}\")\n\t)\n")


def arc(a, m, b, layer="Edge.Cuts", w=0.05):
    return (f"\t(gr_arc\n\t\t(start {a[0]} {a[1]})\n\t\t(mid {m[0]} {m[1]})\n\t\t(end {b[0]} {b[1]})\n{stroke(w)}"
            f"\t\t(layer \"{layer}\")\n\t\t(uuid \"{uid()}\")\n\t)\n")


def circle(c, r, layer="Edge.Cuts", w=0.05):
    return (f"\t(gr_circle\n\t\t(center {c[0]} {c[1]})\n\t\t(end {round(c[0] + r, 4)} {c[1]})\n{stroke(w)}"
            f"\t\t(fill no)\n\t\t(layer \"{layer}\")\n\t\t(uuid \"{uid()}\")\n\t)\n")


def text(s, at, layer="Dwgs.User", size=1.2, ang=0.0):
    return (f"\t(gr_text \"{s}\"\n\t\t(at {at[0]} {at[1]} {round(ang, 1)})\n\t\t(layer \"{layer}\")\n"
            f"\t\t(uuid \"{uid()}\")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n"
            f"\t\t\t\t(thickness {round(size * 0.15, 3)})\n\t\t\t)\n\t\t)\n\t)\n")


def poly(pts, layer="Dwgs.User", w=0.12):
    out = ""
    for i in range(len(pts)):
        out += line(pts[i], pts[(i + 1) % len(pts)], layer, w)
    return out


def rect_r(x0, x1, y0, y1, layer="Dwgs.User", w=0.12):
    """kotak dari koordinat robot"""
    return poly([k(x0, y0), k(x1, y0), k(x1, y1), k(x0, y1)], layer, w)


def rot_rect_r(cx, cy, L, W, ang, layer="Dwgs.User", w=0.12):
    a = math.radians(ang)
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        lx, ly = sx * L / 2, sy * W / 2
        pts.append(k(cx + lx * math.cos(a) - ly * math.sin(a), cy + lx * math.sin(a) + ly * math.cos(a)))
    return poly(pts, layer, w)


def unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n)


def filleted_outline(pts):
    """polygon robot (x, y, r) dengan tiap sudut dibulatkan r-nya (sama dengan model 3D), hasil gr_line + gr_arc"""
    n = len(pts)
    corners = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1][:2], pts[i][:2], pts[(i + 1) % n][:2]
        r = pts[i][2]
        u1, u2 = unit((p0[0] - p1[0], p0[1] - p1[1])), unit((p2[0] - p1[0], p2[1] - p1[1]))
        th = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])))
        d = r / math.tan(th / 2)
        lim = 0.5 * min(math.dist(p0, p1), math.dist(p1, p2))
        rr = r if d <= lim else r * lim / d                  # sisi pendek: jari-jari diperkecil
        d = rr / math.tan(th / 2)
        t1 = (p1[0] + u1[0] * d, p1[1] + u1[1] * d)
        t2 = (p1[0] + u2[0] * d, p1[1] + u2[1] * d)
        b = unit((u1[0] + u2[0], u1[1] + u2[1]))
        hc = rr / math.sin(th / 2)
        c = (p1[0] + b[0] * hc, p1[1] + b[1] * hc)
        mid = (c[0] - b[0] * rr, c[1] - b[1] * rr)
        corners.append((t1, mid, t2))
    out = ""
    for i in range(n):
        t1, mid, t2 = corners[i]
        out += arc(k(*t1), k(*mid), k(*t2))
        out += line(k(*t2), k(*corners[(i + 1) % n][0]))
    return out


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    pcb_path = os.path.join(OUTDIR, NAME + ".kicad_pcb")
    sch_path = os.path.join(OUTDIR, NAME + ".kicad_sch")
    if os.path.exists(pcb_path) and not FORCE:
        sys.exit(f"{pcb_path} sudah ada (mungkin sudah diedit user); pakai --paksa untuk menimpa")

    # proyek: setting PCB sensor user, nama diganti
    pro = open(SENSOR + ".kicad_pro", encoding="utf8").read().replace("sensor-garis", NAME)
    open(os.path.join(OUTDIR, NAME + ".kicad_pro"), "w", encoding="utf8", newline="\n").write(pro)
    for fn, kind, ext in (("sym-lib-table", "sym_lib_table", "ltm.kicad_sym"), ("fp-lib-table", "fp_lib_table", "ltm.pretty")):
        open(os.path.join(OUTDIR, fn), "w", encoding="utf8", newline="\n").write(
            f'({kind}\n  (lib (name "ltm")(type "KiCad")(uri "${{KIPRJMOD}}/../ltm-lib/{ext}")(options "")'
            f'(descr "Modul LTM: ESP32 DevKit, TB6612, MP1584 (footprint sementara, cek ukuran modul asli)"))\n)\n')

    sch = (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n'
           f'\t(uuid "{uid()}")\n\t(paper "A3")\n\t(title_block\n\t\t(title "LTM - PCB utama")\n'
           f'\t\t(company "P01 Kel.5 PjBL DTEO FV ITS")\n\t\t(comment 1 "Panduan per blok: docs/wiring-diagram.html")\n'
           f'\t)\n\t(lib_symbols)\n\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n'
           f'\t(embedded_fonts no)\n)\n')
    if not os.path.exists(sch_path) or "(lib_id" not in open(sch_path, encoding="utf8").read():
        open(sch_path, "w", encoding="utf8", newline="\n").write(sch)

    head = pcb_src[:pcb_src.index("\n\t(footprint")].replace('(paper "A4")', '(paper "A3")')
    body = filleted_outline(MAIN_PTS)
    for x, y in HOLES:
        body += circle(k(x, y), 1.6)
    for c in SB_HOLES:
        body += circle(c, 1.6)
    for x0, x1, y0, y1 in SLOTS:
        body += rect_r(x0, x1, y0, y1, "Edge.Cuts", 0.05)

    # gambar bantu penempatan (posisi dari model 3D v16), lapisan User.Drawings
    D = [
        ((-25.75, 25.75, 24.5, 52.8), "ESP32 DevKit (socket 8,5 mm, USB ke kiri)"),
        ((-13.65, 13.65, 53.5, 81.3), "OLED 0,96 (socket, header di depan)"),
        ((28.0, 48.3, 25.0, 45.3), "TB6612 (socket)"),
        ((-38.0, 38.0, -24.0, 24.0), "dudukan baterai 3D print di atas: komponen maks 10 mm", (0.0, 21.5)),
        ((12.5, 37.5, -6.0, 6.0), "motor kanan N20"),
        ((-37.5, -12.5, -6.0, 6.0), "motor kiri N20"),
        ((-50.0, -45.6, 26.0, 34.6), "SW1"),
        ((4.0, 26.0, -29.5, -12.5), "MP1584 (set 5 V dulu)"),
        ((-29.0, -4.0, -29.5, -13.5), "charger 2S", (-16.5, -15.5)),
        ((27.5, 33.4, -29.8, -24.4), "baterai"),
        ((-19.9, -6.0, 13.0, 17.5), "J2 motor kiri"),
        ((6.0, 19.9, 13.0, 17.5), "J3 motor kanan"),
        ((-35.0, -5.0, -28.0, -17.0), "BMS (sisi bawah)", (-20.0, -26.5)),
        ((-25.0, -19.0, 63.0, 69.0), "A"),
        ((19.0, 25.0, 63.0, 69.0), "B"),
    ]
    for (x0, x1, y0, y1), label, *pos in D:
        body += rect_r(x0, x1, y0, y1)
        size = 1.0 if (x1 - x0) > 12 else 0.8
        body += text(label, k(*(pos[0] if pos else ((x0 + x1) / 2, (y0 + y1) / 2))), size=size)
    body += circle(k(38.0, 51.5), 6.0, "Dwgs.User", 0.12) + text("buzzer", k(38.0, 51.5), size=0.8)
    body += circle(k(-37.0, 40.0), 3.15, "Dwgs.User", 0.12) + text("C1", k(-37.0, 40.0), size=0.8)
    # J5 JST XH 8 pin sejajar tepi miring sidepod kiri (sama dengan model v16), pin 1 di ujung dekat hidung;
    # kabel dibundel menyusuri tepi kiri hidung (kiri tombol A) ke J1 PCB sensor
    e0, e1 = (-27.0, 65.0), (-50.0, 54.0)
    d = unit((e1[0] - e0[0], e1[1] - e0[1]))
    ang = math.degrees(math.atan2(d[1], d[0]))
    c = (e0[0] + 13.5 * d[0] - 4.5 * d[1], e0[1] + 13.5 * d[1] + 4.5 * d[0])
    body += rot_rect_r(*c, 22.4, 5.75, ang)
    kang = -ang                                          # sumbu Y KiCad terbalik: sudut ikut terbalik
    kang = kang + 180 if kang <= -90 else (kang - 180 if kang > 90 else kang)
    body += text("J5 JST XH 8 (urutan = J1 sensor)", k(*c), size=0.8, ang=kang)
    p1 = (c[0] - 8.75 * d[0], c[1] - 8.75 * d[1])          # pin 1 di ujung dekat hidung (kabel tidak bersilangan)
    body += circle(k(*p1), 0.8, "Dwgs.User", 0.12) + text("pin 1", k(p1[0] + 1.5, p1[1] + 2.5), size=0.8)
    # outline PCB sensor rev B (koordinat sama), lapisan User.Comments
    for t, x0, y0, xm, ym, x1, y1 in edges_src:
        if t == "gr_arc" and xm:
            body += arc((x0, y0), (xm, ym), (x1, y1), "Cmts.User", 0.1)
        else:
            body += line((x0, y0), (x1, y1), "Cmts.User", 0.1)
    body += text("PCB sensor rev B (di bawah, Z 4,8-6,4)", k(0.0, 120.0), "Cmts.User", 1.0)

    open(pcb_path, "w", encoding="utf8", newline="\n").write(head + "\n" + body + "\t(embedded_fonts no)\n)\n")
    print("dibuat:", OUTDIR, f"(Y0 = {Y0:.3f}, lubang sensor {SB_HOLES})")


if __name__ == "__main__":
    main()
