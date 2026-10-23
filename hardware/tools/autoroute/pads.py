"""Dump semua pad board live (KiCad IPC) -> pads.json: ref, pad, net, x, y (mm, page), plus koordinat robot."""
import json
import sys
from kipy import KiCad
from kipy.util.units import to_mm

b = KiCad(client_name="claude-route", timeout_ms=20000).get_board()
out = []
for fp in b.get_footprints():
    ref = fp.reference_field.text.value
    for p in fp.definition.pads:
        x, y = to_mm(p.position.x), to_mm(p.position.y)
        out.append(dict(ref=ref, pad=p.number, net=p.net.name, x=round(x, 3), y=round(y, 3),
                        rx=round(x - 200, 2), ry=round(180.55 - y, 2)))
json.dump(out, open(sys.argv[1], "w"), indent=0)
for o in sorted(out, key=lambda o: (o["ref"], o["pad"])):
    print(f'{o["ref"]}.{o["pad"]:>2} {o["net"]:<26} ({o["x"]:.3f}, {o["y"]:.3f})  robot ({o["rx"]}, {o["ry"]})')
