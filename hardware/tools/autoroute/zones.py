"""Tambah GND pour di F.Cu + B.Cu (menutupi seluruh papan, dipotong outline) ke board live, lalu isi ulang.
Satu commit = satu langkah undo. Jarak pour 0,5 mm (aturan tempat cetak), lebar minimum 0,3 mm."""
from kipy import KiCad
from kipy.board_types import Zone
from kipy.geometry import PolygonWithHoles, PolyLine, PolyLineNode, Vector2
from kipy.proto.board.board_types_pb2 import BoardLayer
from kipy.util.units import from_mm

b = KiCad(client_name="claude-route", timeout_ms=60000).get_board()
gnd = {n.name: n for n in b.get_nets()}["GND"]

zones = []
for lay in (BoardLayer.BL_F_Cu, BoardLayer.BL_B_Cu):
    z = Zone()
    z.layers = [lay]
    z.net = gnd
    z.name = "GND"
    z.clearance = from_mm(0.5)
    z.min_thickness = from_mm(0.3)
    line = PolyLine()
    for x, y in ((148, 85), (252, 85), (252, 217), (148, 217)):     # sedikit lebih besar dari papan
        line.append(PolyLineNode.from_point(Vector2.from_xy(from_mm(x), from_mm(y))))
    line.closed = True
    poly = PolygonWithHoles()
    poly.outline = line
    z.outline = poly
    zones.append(z)

c = b.begin_commit()
try:
    b.create_items(zones)
except Exception:
    b.drop_commit(c)
    raise
b.push_commit(c, "Claude: GND pour")
b.refill_zones(block=True)      # KiCad bisa sibuk beberapa detik sesudah ini
print("2 zona GND dibuat")
