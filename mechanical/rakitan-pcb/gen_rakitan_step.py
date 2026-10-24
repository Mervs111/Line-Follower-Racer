# STEP rakitan PCB LFM (24/10/2026): PCB sensor rev B + PCB utama dalam satu file STEP, untuk dibuka di Fusion 360 /
# FreeCAD / SolidWorks. Tanpa CadQuery: KiCad sendiri yang menggabungkan.
# 1. Tiap board diekspor ke STEP dengan titik asal = tengah poros roda (X/Y = koordinat robot). Salinan PCB utama diberi
#    model 3D pustaka KiCad dulu (sama dengan gen_rakitan.py). File di hardware/ tidak diubah.
# 2. Board kosong (tanpa outline) diberi dua footprint bantu di titik asal, model 3D-nya = kedua STEP tadi, dinaikkan
#    ke tinggi pasangnya. Board itu diekspor ke STEP -> dua sub-rakitan PCB_SENSOR + PCB_UTAMA dalam satu file.
# Sumbu sama dengan LTM_v16_rakitan.step: X kanan, Y maju, Z atas, nol = lantai di bawah tengah poros roda.
# Modul ESP32/TB6612/MP1584 tidak punya model 3D (ada di STEP v16).
# Pakai: py gen_rakitan_step.py [--tembaga] [--cek]
#   --tembaga: ikut jalur, pour, pad, silkscreen, mask (file jauh lebih besar); --cek: buka ulang hasil, cetak ukurannya
import os, shutil, subprocess, sys, tempfile, uuid
import numpy as np
import gen_rakitan as g

COPPER = ["--include-tracks", "--include-pads", "--include-zones", "--include-silkscreen", "--include-soldermask"]
TOP_Z = 1.685      # tinggi alas model footprint sisi atas dari sisi bawah papan (stackup 1,6 mm, ekspor KiCad 10)


def export(fmt, board, out, *flags):
    cmd = [g.CLI, "pcb", "export", fmt, "--force", "--user-origin", f"{g.KX0}x{g.KY0}mm", *flags, "-o", out, board]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or not os.path.exists(out):
        sys.exit(r.stdout + r.stderr)


def helper_footprint(ref, value, model, z):
    """footprint tanpa pad di titik asal robot, model 3D = STEP satu board, alasnya di tinggi z dari lantai"""
    u = lambda: str(uuid.uuid4())
    prop = lambda k, v: (f'\t\t(property "{k}" "{v}"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n'
                         f'\t\t\t(uuid "{u()}")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n'
                         f'\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n')
    return (f'\t(footprint "LFM:{ref}"\n\t\t(layer "F.Cu")\n\t\t(uuid "{u()}")\n\t\t(at {g.KX0} {g.KY0})\n' +
            prop("Reference", ref) + prop("Value", value) +
            '\t\t(attr board_only exclude_from_pos_files exclude_from_bom)\n'
            f'\t\t(model "{model.replace(os.sep, "/")}"\n\t\t\t(offset\n\t\t\t\t(xyz 0 0 {z - TOP_Z:.3f})\n\t\t\t)\n'
            '\t\t\t(scale\n\t\t\t\t(xyz 1 1 1)\n\t\t\t)\n\t\t\t(rotate\n\t\t\t\t(xyz 0 0 0)\n\t\t\t)\n\t\t)\n\t)\n')


def board_steps(tmp, flags):
    """STEP per board; PCB utama lewat salinan yang sudah diberi model 3D pustaka"""
    sensor, utama = g.BOARDS["pcb_sensor"][0], g.BOARDS["pcb_utama"][0]
    os.makedirs(os.path.join(tmp, "utama"))
    copy = os.path.join(tmp, "utama", os.path.basename(utama))
    g.add_models(utama, copy)
    shutil.copy(utama.replace(".kicad_pcb", ".kicad_pro"), os.path.join(tmp, "utama"))
    out = {}
    for name, board in (("pcb_sensor", sensor), ("pcb_utama", copy)):
        out[name] = os.path.join(tmp, name + ".step")
        print(f"{name} -> STEP")
        export("step", board, out[name], "--subst-models", *flags)
    return out


def host_board(tmp, steps):
    """board kosong (header PCB sensor: stackup sama, tanpa footprint/outline) + dua footprint bantu"""
    k = open(g.BOARDS["pcb_sensor"][0], encoding="utf8").read()
    k = k[:k.index("\n\t(footprint")] + "\n"
    k += helper_footprint("PCB_SENSOR", "PCB sensor rev B", steps["pcb_sensor"], g.BOARDS["pcb_sensor"][1])
    k += helper_footprint("PCB_UTAMA", "PCB utama", steps["pcb_utama"], g.BOARDS["pcb_utama"][1])
    dst = os.path.join(tmp, "rakitan.kicad_pcb")
    open(dst, "w", encoding="utf8").write(k + ")\n")
    return dst


def check(path, tmp):
    """buka ulang STEP hasil lewat KiCad (OCCT) dan ukur kotak pembatasnya dari lantai"""
    probe = os.path.join(tmp, "cek.kicad_pcb")
    k = open(g.BOARDS["pcb_sensor"][0], encoding="utf8").read()
    open(probe, "w", encoding="utf8").write(k[:k.index("\n\t(footprint")] + "\n" +
                                            helper_footprint("CEK", "cek", path, 0.0) + ")\n")
    glb = os.path.join(tmp, "cek.glb")
    export("glb", probe, glb, "--no-board-body")
    pts = np.vstack([pos @ g.G2R.T for ref, mat, pos, nor, idx in g.read_glb(glb)])
    lo, hi = pts.min(0), pts.max(0)
    print("cek: X %.1f .. %.1f, Y %.1f .. %.1f, Z %.2f .. %.2f (mm, Z dari lantai)" % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))


if __name__ == "__main__":
    copper = "--tembaga" in sys.argv
    tmp = tempfile.mkdtemp(prefix="rakitan-step-")
    host = host_board(tmp, board_steps(tmp, COPPER if copper else []))
    out = os.path.join(g.HERE, "LFM_rakitan_pcb_tembaga.step" if copper else "LFM_rakitan_pcb.step")
    print("gabungan -> STEP")
    export("step", host, out, "--no-board-body")
    print(f"{os.path.basename(out)}: {os.path.getsize(out) / 1e6:.1f} MB")
    if "--cek" in sys.argv:
        check(out, tmp)
    shutil.rmtree(tmp, ignore_errors=True)
