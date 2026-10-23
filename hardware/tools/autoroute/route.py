"""Pasang jalur + via dari file rencana (JSON) ke board live dalam satu commit (satu langkah undo).
Rencana: {"tracks": [{"net", "layer", "w", "pts": [[x,y],...]}], "vias": [{"net", "at": [x,y]}]}
Koordinat page KiCad (mm). Argumen ke-2 "hapus" = hapus dulu semua track/via yang ada."""
import json
import sys
from kipy import KiCad
from kipy.board_types import Track, Via
from kipy.proto.board.board_types_pb2 import BoardLayer
from kipy.util.units import from_mm
from kipy.geometry import Vector2


def V(x, y):
    return Vector2.from_xy(from_mm(x), from_mm(y))

plan = json.load(open(sys.argv[1], encoding="utf8"))
b = KiCad(client_name="claude-route", timeout_ms=30000).get_board()
nets = {n.name: n for n in b.get_nets()}
LAY = {"F": BoardLayer.BL_F_Cu, "B": BoardLayer.BL_B_Cu}

items = []
for t in plan.get("tracks", []):
    n = nets[t["net"]]
    for p, q in zip(t["pts"], t["pts"][1:]):
        tr = Track()
        tr.start = V(*p)
        tr.end = V(*q)
        tr.width = from_mm(t["w"])
        tr.layer = LAY[t["layer"]]
        tr.net = n
        items.append(tr)
for v in plan.get("vias", []):
    via = Via()
    via.position = V(*v["at"])
    via.diameter = from_mm(v.get("d", 1.3))
    via.drill_diameter = from_mm(v.get("drill", 0.6))
    via.net = nets[v["net"]]
    items.append(via)

c = b.begin_commit()
try:
    if len(sys.argv) > 2 and sys.argv[2] == "hapus":
        old = list(b.get_tracks()) + list(b.get_vias())
        if old:
            b.remove_items(old)
    created = b.create_items(items)
except Exception:
    b.drop_commit(c)
    raise
b.push_commit(c, "Claude: routing " + plan.get("name", ""))
print(f"{len(created)} item dibuat")
