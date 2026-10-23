"""Dijalankan dengan python KiCad (modul pcbnew).
  dsn <board> <out.dsn>             ekspor Specctra DSN
  ses <board> <in.ses> <out.json>   impor SES ke board salinan, tulis track/via hasilnya ke JSON (format route.py)"""
import json
import sys
import pcbnew

cmd, brd = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(brd)
if cmd == "dsn":
    print("ekspor", pcbnew.ExportSpecctraDSN(b, sys.argv[3]))
elif cmd == "ses":
    for t in list(b.GetTracks()):
        b.Remove(t)
    print("impor", pcbnew.ImportSpecctraSES(b, sys.argv[3]))
    tracks, vias = [], []
    for t in b.GetTracks():
        net = t.GetNetname()
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            vias.append(dict(net=net, at=[pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)], d=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)),
                             drill=pcbnew.ToMM(t.GetDrillValue())))
        else:
            s, e = t.GetStart(), t.GetEnd()
            tracks.append(dict(net=net, layer="F" if t.GetLayer() == pcbnew.F_Cu else "B", w=pcbnew.ToMM(t.GetWidth()),
                               pts=[[pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)], [pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)]]))
    json.dump(dict(name="FreeRouting", tracks=tracks, vias=vias), open(sys.argv[4], "w"))
    print(len(tracks), "segmen,", len(vias), "via")
