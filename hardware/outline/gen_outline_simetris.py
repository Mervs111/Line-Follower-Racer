# Outline PCB sensor simetris (dari layout user 21/10/2026), koordinat mm, Y ke bawah (KiCad), 0,0 = puncak tepi depan
import math, sys
import ezdxf
from PIL import Image, ImageDraw, ImageFont

OUT_DXF, REF_PNG, OUT_PNG, OUT_CHECK = sys.argv[1:5]
R = [  # (x, y, radius)
    (0.0, 0.0, 0.0),
    (60.0, 5.5, 2.5), (60.0, 20.5, 2.5), (15.0, 20.5, 2.5), (15.0, 34.5, 2.5),
    (9.0, 34.5, 1.5), (9.0, 46.0, 0.0),
]
V = R + [(-x, y, r) for x, y, r in reversed(R[1:])]
HOLES = [(-5.0, 40.0), (5.0, 40.0)]


def fillet(prev, p, nxt, r):
    ux, uy = prev[0] - p[0], prev[1] - p[1]; l1 = math.hypot(ux, uy); ux, uy = ux / l1, uy / l1
    vx, vy = nxt[0] - p[0], nxt[1] - p[1]; l2 = math.hypot(vx, vy); vx, vy = vx / l2, vy / l2
    th = math.acos(max(-1, min(1, ux * vx + uy * vy)))
    t = r / math.tan(th / 2)
    t1 = (p[0] + ux * t, p[1] + uy * t); t2 = (p[0] + vx * t, p[1] + vy * t)
    bx, by = ux + vx, uy + vy; bl = math.hypot(bx, by); bx, by = bx / bl, by / bl
    d = r / math.sin(th / 2)
    c = (p[0] + bx * d, p[1] + by * d)
    return t1, t2, c


n = len(V)
segs = []  # ('line', a, b) / ('arc', c, r, a1, a2) dalam koordinat Y ke bawah
pts_in, pts_out = [], []
for i in range(n):
    x, y, r = V[i]
    if r > 0:
        t1, t2, c = fillet(V[i - 1], (x, y), V[(i + 1) % n], r)
        pts_in.append(t1); pts_out.append(t2); segs.append(("arc", c, r, t1, t2))
    else:
        pts_in.append((x, y)); pts_out.append((x, y)); segs.append(None)
lines = [(pts_out[i], pts_in[(i + 1) % n]) for i in range(n)]

doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM
msp = doc.modelspace()
F = lambda p: (p[0], -p[1])                        # DXF: Y ke atas
for a, b in lines:
    if math.dist(a, b) > 1e-6:
        msp.add_line(F(a), F(b))
for s in segs:
    if s is None:
        continue
    _, c, r, t1, t2 = s
    a1 = math.degrees(math.atan2(-(t1[1] - c[1]), t1[0] - c[0]))
    a2 = math.degrees(math.atan2(-(t2[1] - c[1]), t2[0] - c[0]))
    sweep = (a2 - a1) % 360
    if sweep > 180:
        a1, a2 = a2, a1
    msp.add_arc(F(c), r, a1, a2)
doc.saveas(OUT_DXF)


def poly(scale, ox, oy, steps=12):
    out = []
    for i in range(n):
        s = segs[i]
        if s is None:
            out.append(V[i][:2])
        else:
            _, c, r, t1, t2 = s
            a1 = math.atan2(t1[1] - c[1], t1[0] - c[0]); a2 = math.atan2(t2[1] - c[1], t2[0] - c[0])
            d = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
            out += [(c[0] + r * math.cos(a1 + d * k / steps), c[1] + r * math.sin(a1 + d * k / steps)) for k in range(steps + 1)]
    return [(ox + x * scale, oy + y * scale) for x, y in out]


try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
except Exception:
    font = fb = ImageFont.load_default()

# 1) cek: outline baru (merah) di atas screenshot user, skala 6,09 px/mm, puncak di (400, 45)
ref = Image.open(REF_PNG).convert("RGB")
d = ImageDraw.Draw(ref)
P = poly(6.09, 400, 45)
d.line(P + [P[0]], fill=(255, 70, 70), width=2)
for hx, hy in HOLES:
    cx, cy = 400 + hx * 6.09, 45 + hy * 6.09
    d.ellipse((cx - 9.7, cy - 9.7, cx + 9.7, cy + 9.7), outline=(255, 70, 70), width=2)
ref.save(OUT_CHECK)

# 2) gambar ukuran bersih
S, OX, OY = 9.0, 720, 130
img = Image.new("RGB", (1440, 640), (250, 250, 248))
d = ImageDraw.Draw(img)
P = poly(S, OX, OY)
d.polygon(P, fill=(32, 36, 44))
d.line(P + [P[0]], fill=(20, 20, 20), width=2)
d.line((OX, OY - 40, OX, OY + 52 * S), fill=(214, 60, 60), width=1)
d.text((OX + 6, OY - 44), "garis tengah X = 0", fill=(214, 60, 60), font=font)
for hx, hy in HOLES:
    cx, cy = OX + hx * S, OY + hy * S
    d.ellipse((cx - 1.6 * S, cy - 1.6 * S, cx + 1.6 * S, cy + 1.6 * S), fill=(250, 250, 248))
def label(x, y, s, anchor="mm"):
    d.text((x, y), s, fill=(30, 30, 30), font=font, anchor=anchor)
label(OX, OY - 14, "(0 ; 0)")
label(OX + 60 * S + 8, OY + 5.5 * S, "(60 ; 5,5)", "lm"); label(OX - 60 * S - 8, OY + 5.5 * S, "(-60 ; 5,5)", "rm")
label(OX + 60 * S + 8, OY + 20.5 * S, "(60 ; 20,5)", "lm"); label(OX - 60 * S - 8, OY + 20.5 * S, "(-60 ; 20,5)", "rm")
label(OX + 15 * S + 8, OY + 30 * S, "(15 ; 20,5)…(15 ; 34,5)", "lm")
label(OX + 9 * S + 8, OY + 42 * S, "(9 ; 34,5)…(9 ; 46)", "lm")
label(OX, OY + 46 * S + 18, "tab 18 mm, bawah Y = 46", "mm")
label(OX - 9 * S - 10, OY + 40 * S, "lubang H1 (-5 ; 40), H2 (5 ; 40)", "rm")
d.text((24, 18), "Outline PCB sensor simetris (mm, Y ke bawah seperti KiCad, 0,0 = puncak depan)", fill=(20, 20, 20), font=fb)
d.text((24, 40), "lebar 120 · sayap 15 · badan 30 · tab 18 · sudut luar R2,5 · leher R2,5 · tangga tab R1,5", fill=(60, 60, 60), font=font)
img.save(OUT_PNG)
print("ok", len(lines), "garis +", sum(1 for s in segs if s), "busur")
