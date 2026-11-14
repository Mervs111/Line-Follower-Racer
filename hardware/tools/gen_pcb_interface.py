"""Layout board interface rev B (konsep v18, 14/11/2026): 39 x 45 mm, simetris terhadap garis tengah robot. OLED di
tengah, 5 tombol 6x6 sebaris di belakangnya (KEMBALI, ATAS, OK, BAWAH, LANJUT), tangga resistor di bawah OLED,
4 lubang M2 ke rangka interface (3D print) + 4 lubang M2 spacer OLED, J1 tepat di atas J6 PCB utama (posisi pin sama
persis). Tepi belakang papan (y 34..36,5) bertumpu di balok rangka: jangan taruh kaki komponen di situ.
Rev A (46 x 36 mm, tombol 2 kiri + 3 kanan) ada di riwayat git.

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

# tepi kanan 19,5: tembaga pour berhenti di 19,0, di kiri zona antena ESP32 (x 19,25..25,75)
X0, X1, Y0, Y1, R_FIL = -19.5, 19.5, 34.0, 79.0, 2.0
# M2 ke rangka interface (3D print): di depan ESP32 (y > 60,3), di bawahnya ada ruang untuk boss 5 mm
HOLES = [(-17.0, 62.0), (17.0, 62.0), (-17.0, 76.5), (17.0, 76.5)]
# spacer M2 di 4 lubang modul OLED (jarak lubang 23,5 x 23,8 dari gambar umum modul 0,96": UKUR modul sebelum cetak)
HOLES_OLED = [(-11.75, 49.0), (11.75, 49.0), (-11.75, 72.8), (11.75, 72.8)]
J6_PIN1 = (-5.6, 67.5)                           # = gen_pcb_utama_v17.PLACE["J6"], pin ke arah +x
BTN_Y, BTN_P = 41.6, 7.62                        # baris tombol di belakang OLED, jarak antar tombol 7,62 mm
BTN = {"SW3": (-2 * BTN_P, BTN_Y), "SW1": (-BTN_P, BTN_Y), "SW4": (0.0, BTN_Y), "SW2": (BTN_P, BTN_Y),
       "SW5": (2 * BTN_P, BTN_Y)}
LBL = {"SW1": "ATAS", "SW2": "BAWAH", "SW3": "KEMBALI", "SW4": "OK", "SW5": "LANJUT"}
OLED = (0.0, 61.0, 27.3, 27.8)                   # tengah x, y, lebar, tinggi modul (di socket 8,5 mm)

# tangga resistor di bawah OLED, 2 kolom x 3 baris; pad 1 (Bk) di sisi luar, pad 2 (GND) di tengah. C1 di bawah pin
# BTN J1 (x 4,56).
PLACE = {"J1": (J6_PIN1[0], J6_PIN1[1], 90), "J2": (-3.81, 73.65, 90), "C1": (4.5, 60.5, 0),
         "R3": (-11.43, 53.3, 0), "R1": (-11.43, 56.9, 0), "R4": (-11.43, 60.5, 0),
         "R5": (11.43, 53.3, 180), "R2": (11.43, 56.9, 180)}
# SW_PUSH_6mm diputar: pad 4,5 mm searah x, 6,5 mm searah y; kaki 1 (BTN) di kiri, kaki 2 (Bk) di kanan
for ref, (cx, cy) in BTN.items():
    PLACE[ref] = (cx - 2.25, cy - 3.25, 90)


def main(netfile, base, out):
    comps, nets = gu.read_netlist(netfile)
    loaded = {ref: gu.load_fp(c["fp"]) for ref, c in comps.items()}
    holes = [gu.load_fp("MountingHole:MountingHole_2.2mm_M2") for _ in HOLES + HOLES_OLED]
    b = pcbnew.LoadBoard(base)
    gu._BUANG.extend(list(b.GetFootprints()) + list(b.GetTracks()) + list(b.Zones()) + list(b.GetDrawings()))
    for it in gu._BUANG:
        b.Remove(it)
    tb = b.GetTitleBlock()
    tb.SetTitle("LTM - board interface"); tb.SetRevision("B"); tb.SetDate("2026-11-14")

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
        if ref.startswith("R"):                           # baris resistor rapat: referensi di lorong tengah
            t = fp.Reference()
            t.SetPosition(gu.K(-1.7 if x < 0 else 1.7, y))
            t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
            t.SetTextThickness(pcbnew.FromMM(0.15))
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
    for i, (x, y) in enumerate(HOLES + HOLES_OLED, 1):
        fp = holes[i - 1]
        fp.SetReference(f"H{i}"); fp.SetValue("M2"); fp.SetPosition(gu.K(x, y)); fp.SetBoardOnly(True)
        fp.Reference().SetLayer(pcbnew.F_Fab); fp.Value().SetLayer(pcbnew.F_Fab)
        b.Add(fp)

    for ref, t in LBL.items():                    # nama tombol di tepi belakang, di bawah tombolnya
        cx, cy = BTN[ref]
        gu.add_text(b, pcbnew.F_SilkS, t, cx, Y0 + 1.3, 0.8, 0, 0.15)
    gu.add_text(b, pcbnew.F_SilkS, "J1 (bawah) ke J6 PCB utama", 0.75, 64.3, 0.8)
    gu.add_text(b, pcbnew.B_SilkS, "LTM interface rev B", 0.0, 48.5, 1.2, mirror=True)
    ox, oy, ow, oh = OLED                         # garis bantu modul OLED (dipasang di atas socket J2)
    a, c = (ox - ow / 2, oy - oh / 2), (ox + ow / 2, oy + oh / 2)
    for p, q in (((a[0], a[1]), (c[0], a[1])), ((c[0], a[1]), (c[0], c[1])), ((c[0], c[1]), (a[0], c[1])),
                 ((a[0], c[1]), (a[0], a[1]))):
        gu.add_shape(b, pcbnew.F_Fab, "seg", (p, q), 0.1)
    gu.add_text(b, pcbnew.F_Fab, "OLED 0,96 (di socket J2)", ox, oy, 1.0)
    pcbnew.SaveBoard(out, b)
    print(f"{len(comps)} komponen + {len(HOLES + HOLES_OLED)} lubang M2, {len(netobj)} net, {X1 - X0:.0f} x {Y1 - Y0:.0f} mm")


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
