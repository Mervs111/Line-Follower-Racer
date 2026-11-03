"""Layout board interface rev A (konsep v17, 03/11/2026): 46 x 36 mm, 4 lubang M2 di pojok, OLED di tengah diapit
5 tombol 6x6, tangga resistor di bawah OLED, J1 tepat di atas J6 PCB utama (posisi pin sama persis).

Dijalankan dengan python KiCad (modul pcbnew):
  "$KPY" hardware/tools/gen_pcb_interface.py <netlist.net> <dasar.kicad_pcb> <board-interface.kicad_pcb>
Board dasar hanya diambil setup-nya (mis. pcb-utama.kicad_pcb). Routing sesudahnya dengan autoroute/sisa.py
(papan kecil, GND lewat pour). Koordinat robot sama dengan PCB utama (KiCad X = 200 + x, Y = 180,55 - y).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_pcb_utama_v17 as gu  # noqa: E402  (fungsi outline, netlist, footprint)
import pcbnew  # noqa: E402

X0, X1, Y0, Y1, R_FIL = -27.0, 19.0, 43.0, 79.0, 2.0
HOLES = [(-24.5, 45.5), (16.5, 45.5), (-24.5, 76.5), (16.5, 76.5)]
J6_PIN1 = (-5.6, 67.5)                           # = gen_pcb_utama_v17.PLACE["J6"], pin ke arah +x
BTN = {"SW1": (-22.5, 70.0), "SW2": (-22.5, 52.0), "SW3": (14.5, 70.0), "SW4": (14.5, 61.0), "SW5": (14.5, 52.0)}
LBL = {"SW1": "ATAS", "SW2": "BAWAH", "SW3": "KEMBALI", "SW4": "OK", "SW5": "LANJUT"}
OLED = (-4.0, 61.0, 27.3, 27.8)                  # tengah x, y, lebar, tinggi modul (di socket 8,5 mm)

# tangga resistor di bawah OLED, dekat tombolnya: R1/R2 kiri, R3-R5 kanan (pad 1 = Bk menghadap tombol)
PLACE = {"J1": (J6_PIN1[0], J6_PIN1[1], 90), "J2": (-7.81, 73.65, 90), "C1": (-7.5, 55.5, 0),
         "R1": (-15.0, 61.0, 0), "R2": (-15.0, 50.0, 0),
         "R3": (8.0, 61.0, 180), "R4": (8.0, 56.5, 180), "R5": (8.0, 50.0, 180)}
# SW_PUSH_6mm diputar: pad 4,5 mm searah x, 6,5 mm searah y; kaki 2 (Bk) menghadap ke dalam (ke resistor)
for ref, (cx, cy) in BTN.items():
    PLACE[ref] = (cx - 2.25, cy - 3.25, 90) if cx < 0 else (cx + 2.25, cy + 3.25, -90)


def main(netfile, base, out):
    comps, nets = gu.read_netlist(netfile)
    loaded = {ref: gu.load_fp(c["fp"]) for ref, c in comps.items()}
    holes = [gu.load_fp("MountingHole:MountingHole_2.2mm_M2") for _ in HOLES]
    b = pcbnew.LoadBoard(base)
    gu._BUANG.extend(list(b.GetFootprints()) + list(b.GetTracks()) + list(b.Zones()) + list(b.GetDrawings()))
    for it in gu._BUANG:
        b.Remove(it)
    tb = b.GetTitleBlock()
    tb.SetTitle("LTM - board interface"); tb.SetRevision("A"); tb.SetDate("2026-11-03")

    shape = gu.fillet([(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)], R_FIL)
    for s in shape:
        gu.add_shape(b, pcbnew.Edge_Cuts, s[0], s[1:])
    netobj = {}
    for ref, c in sorted(comps.items()):
        fp = loaded[ref]
        fp.SetReference(ref); fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        x, y, rot = PLACE[ref]
        fp.SetOrientationDegrees(rot); fp.SetPosition(gu.K(x, y))
        if ref.startswith("SW"):                          # referensi tombol mepet tepi papan: pindah ke F.Fab
            fp.Reference().SetLayer(pcbnew.F_Fab)
        b.Add(fp)
        if ref == "J1":                                   # header dipasang dari bawah, menghadap J6 PCB utama
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)   # (sesudah Add: sebelum itu segfault)
            fp.SetOrientationDegrees(rot + 180)                # di sisi B arah pin terbalik: pin 1-6 tetap ke +x
        for p in fp.Pads():
            name = nets.get((ref, p.GetNumber()))
            if name:
                if name not in netobj:
                    netobj[name] = pcbnew.NETINFO_ITEM(b, name); b.Add(netobj[name])
                p.SetNet(netobj[name])
    for i, (x, y) in enumerate(HOLES, 1):
        fp = holes[i - 1]
        fp.SetReference(f"H{i}"); fp.SetValue("M2"); fp.SetPosition(gu.K(x, y)); fp.SetBoardOnly(True)
        fp.Reference().SetLayer(pcbnew.F_Fab); fp.Value().SetLayer(pcbnew.F_Fab)
        b.Add(fp)

    for ref, t in LBL.items():                    # nama tombol tegak di sisi dalam tombol
        cx, cy = BTN[ref]
        gu.add_text(b, pcbnew.F_SilkS, t, cx + (4.5 if cx < 0 else -4.2), cy, 0.9, 90, 0.15)
    gu.add_text(b, pcbnew.F_SilkS, "J1 (bawah) ke J6 PCB utama", 0.75, 64.4, 0.8)
    gu.add_text(b, pcbnew.B_SilkS, "LTM interface rev A", -4.0, 47.0, 1.2, mirror=True)
    ox, oy, ow, oh = OLED                         # garis bantu modul OLED (dipasang di atas socket J2)
    a, c = (ox - ow / 2, oy - oh / 2), (ox + ow / 2, oy + oh / 2)
    for p, q in (((a[0], a[1]), (c[0], a[1])), ((c[0], a[1]), (c[0], c[1])), ((c[0], c[1]), (a[0], c[1])),
                 ((a[0], c[1]), (a[0], a[1]))):
        gu.add_shape(b, pcbnew.F_Fab, "seg", (p, q), 0.1)
    gu.add_text(b, pcbnew.F_Fab, "OLED 0,96 (di socket J2)", ox, oy, 1.0)
    pcbnew.SaveBoard(out, b)
    print(f"{len(comps)} komponen + {len(HOLES)} lubang M2, {len(netobj)} net, {X1 - X0:.0f} x {Y1 - Y0:.0f} mm")


def pour(brd):
    b = pcbnew.LoadBoard(brd)
    old = [z for z in b.Zones() if not z.GetIsRuleArea()]
    gu._BUANG.extend(old)
    for z in old:
        b.Remove(z)
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b)
        z.SetLayer(lay); z.SetNet(b.FindNet("GND")); z.SetZoneName("GND")
        z.SetLocalClearance(pcbnew.FromMM(0.5)); z.SetMinThickness(pcbnew.FromMM(0.3))
        z.SetThermalReliefGap(pcbnew.FromMM(0.5)); z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.5))
        gu.zone_poly(z, [(X0 - 2, Y0 - 2), (X1 + 2, Y0 - 2), (X1 + 2, Y1 + 2), (X0 - 2, Y1 + 2)])
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(brd, b)
    print("GND pour F.Cu + B.Cu")


if __name__ == "__main__":
    if sys.argv[1] == "pour":
        pour(sys.argv[2])
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
