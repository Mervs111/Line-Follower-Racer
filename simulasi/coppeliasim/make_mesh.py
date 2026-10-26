"""Mesh tampilan robot untuk CoppeliaSim dari rakitan PCB LFM (mechanical/rakitan-pcb/LFM_rakitan.glb).

GLB (posisi terkuantisasi, 49 material) -> OBJ per kelompok warna di mesh/, satuan meter, koordinat robot
(x kanan, y maju, z atas, nol = lantai di bawah tengah poros roda). Roda dibuang (di CoppeliaSim roda = silinder
yang berputar). Mesh disederhanakan supaya CoppeliaSim tetap ringan. build_scene.py membaca OBJ ini sendiri
(sim.createMeshShape), jadi tidak bergantung pada pengimpor file CoppeliaSim.

Jalankan ulang tiap rakitan PCB berubah:  python make_mesh.py   (butuh numpy, fast-simplification)
"""
import json
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "..", "..", "mechanical", "rakitan-pcb", "LFM_rakitan.glb")
OUT = os.path.join(HERE, "mesh")
TARGET_TRIS = 60000
WHEEL_X, WHEEL_R, AXLE_Z = 39.3, 17.6, 17.0     # mm: sisi dalam roda, jari-jari + kelonggaran, tinggi poros

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read_glb(path):
    data = open(path, "rb").read()
    jlen = struct.unpack("<I", data[12:16])[0]
    gj = json.loads(data[20:20 + jlen])
    off = 20 + jlen
    blen = struct.unpack("<I", data[off:off + 4])[0]
    return gj, data[off + 8:off + 8 + blen]


def accessor(gj, binb, idx):
    a = gj["accessors"][idx]
    bv = gj["bufferViews"][a["bufferView"]]
    dt = np.dtype(CT[a["componentType"]])
    n = NC[a["type"]]
    stride = bv.get("byteStride", dt.itemsize * n)
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    raw = np.frombuffer(binb, dtype=np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * n, offset=start)
    out = np.lib.stride_tricks.as_strided(raw, shape=(a["count"], dt.itemsize * n), strides=(stride, 1))
    return np.frombuffer(out.copy().tobytes(), dtype=dt).reshape(a["count"], n).astype(np.float64)


def main():
    import fast_simplification
    gj, binb = read_glb(GLB)
    mats = [m.get("pbrMetallicRoughness", {}).get("baseColorFactor", [0.5, 0.5, 0.5, 1])[:3] for m in gj["materials"]]
    names = [m.get("name") or "m%d" % i for i, m in enumerate(gj["materials"])]
    parts = {}          # material -> list (verts mm, faces)
    for node in gj["nodes"]:
        if "mesh" not in node:
            continue
        s = np.array(node.get("scale", [1, 1, 1]))
        t = np.array(node.get("translation", [0, 0, 0]))
        for p in gj["meshes"][node["mesh"]]["primitives"]:
            v = accessor(gj, binb, p["attributes"]["POSITION"]) * s + t        # mm
            f = accessor(gj, binb, p["indices"]).astype(np.int64).reshape(-1, 3)
            parts.setdefault(p["material"], []).append((v, f))

    # kelompok warna: material dengan warna mirip digabung (jarak RGB < 0,12)
    groups = []         # [warna, [material]]
    for mi in sorted(parts):
        c = np.array(mats[mi])
        for g in groups:
            if np.linalg.norm(g[0] - c) < 0.12:
                g[1].append(mi)
                break
        else:
            groups.append([c, [mi]])

    total = sum(sum(len(f) for _, f in parts[mi]) for mi in parts)
    keep = TARGET_TRIS / total
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        os.remove(os.path.join(OUT, old))
    manifest = []
    removed = 0
    for gi, (col, mlist) in enumerate(groups):
        vs, fs, base = [], [], 0
        wsum, nsum = np.zeros(3), 0
        for mi in mlist:
            for v, f in parts[mi]:
                c = v[f].mean(axis=1)
                wheel = (np.abs(c[:, 0]) > WHEEL_X) & (c[:, 1] ** 2 + (c[:, 2] - AXLE_Z) ** 2 < WHEEL_R ** 2)
                removed += int(wheel.sum())
                f = f[~wheel]
                vs.append(v)
                fs.append(f + base)
                base += len(v)
                wsum += np.array(mats[mi]) * len(f)
                nsum += len(f)
        v = np.vstack(vs)
        f = np.vstack(fs)
        if len(f) == 0:
            continue
        # gabung titik kembar (GLB memisah titik per normal), buang segitiga gepeng
        q = np.round(v / 0.01).astype(np.int64)
        _, uniq, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
        v = v[uniq]
        f = inv.reshape(-1)[f]
        f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
        n0 = len(f)
        if n0 > 1500:
            v, f = fast_simplification.simplify(v.astype(np.float32), f.astype(np.int32), 1 - keep)
            v = v.astype(np.float64)
        rgb = (wsum / nsum).tolist()        # warna rata-rata berbobot jumlah segitiga
        label = "-".join(sorted({names[mi] for mi in mlist}))[:40].replace(" ", "_")
        fname = "g%02d.obj" % gi
        with open(os.path.join(OUT, fname), "w") as fo:
            fo.write("# LFM rakitan, kelompok warna %d (%s), meter, koordinat robot\n" % (gi, label))
            for x, y, z in v * 0.001:
                fo.write("v %.5f %.5f %.5f\n" % (x, y, z))
            for a, b, c in f + 1:
                fo.write("f %d %d %d\n" % (a, b, c))
        manifest.append({"file": fname, "rgb": [round(x, 3) for x in rgb], "tris": int(len(f)),
                         "materials": label})
        print("%s %-40s %6d -> %6d segitiga  rgb %s" % (fname, label, n0, len(f), [round(x, 2) for x in rgb]))
    json.dump({"units": "m", "frame": "robot: x kanan, y maju, z atas, nol = lantai di bawah tengah poros roda",
               "source": "mechanical/rakitan-pcb/LFM_rakitan.glb", "groups": manifest},
              open(os.path.join(OUT, "mesh.json"), "w"), indent=1)
    print("segitiga roda dibuang:", removed, "| total:", sum(m["tris"] for m in manifest))


if __name__ == "__main__":
    main()
