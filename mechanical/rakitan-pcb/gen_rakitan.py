# Rakitan PCB LFM (24/10/2026): PCB sensor rev B + PCB utama hasil layout digabung di posisi pasangnya, untuk melihat
# bentuk dan ukuran robot dengan PCB yang sebenarnya.
# 1. pcb-utama.kicad_pcb disalin ke folder sementara dan diberi model 3D dari pustaka KiCad (footprint di board belum
#    punya baris (model ...)). File di hardware/ tidak diubah.
# 2. kicad-cli pcb export glb untuk kedua PCB (tembaga, pour, silkscreen, mask, komponen) dengan titik asal
#    (200; 180,55) = tengah poros roda, jadi X/Y hasilnya langsung koordinat robot.
# 3. Bagian mekanik model v16 (roda, motor, baterai, modul, kabel, sayap) disaring: yang sudah ada di file KiCad
#    dibuang, ESP32 digeser ke posisi U1 di layout.
# 4. Semua digabung per material jadi satu GLB (LFM_rakitan.glb, mm, Z ke atas di dalam node akar yang memutar ke
#    konvensi glTF) + ukuran utama di "extras" node akar. Viewer: index.html.
# Pakai: py gen_rakitan.py [model.json v16]   (bawaan: mechanical/viewer/model.json, data viewer v16)
# Butuh KiCad 10 (kicad-cli), numpy, Node.js (npx gltfpack untuk kompresi; tanpa Node hasilnya tidak dikompres).
import base64, json, math, os, re, shutil, struct, subprocess, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
KICAD = r"C:\Program Files\KiCad\10.0"
CLI = os.path.join(KICAD, "bin", "kicad-cli.exe")
FPLIB = os.path.join(KICAD, "share", "kicad", "footprints")
KX0, KY0 = 200.0, 180.55                    # X KiCad = 200 + x robot, Y KiCad = 180,55 - y robot
# tinggi sisi bawah papan dari lantai (sama dengan model v16): sensor 4,8 (muka QRE +-3 mm dari lantai), utama 10,4
# (spacer nilon 4 mm di atas PCB sensor)
BOARDS = {"pcb_sensor": (os.path.join(REPO, "hardware", "sensor-garis", "sensor-garis.kicad_pcb"), 4.8),
          "pcb_utama": (os.path.join(REPO, "hardware", "pcb-utama", "pcb-utama.kicad_pcb"), 10.4)}


# ------------------------------ 1-2. ekspor KiCad ------------------------------
def add_models(src, dst):
    """salin board, tambahkan blok (model ...) dari footprint pustaka KiCad untuk footprint yang belum punya"""
    k = open(src, encoding="utf8").read()
    n_add, miss = 0, []

    def fix(m):
        nonlocal n_add
        name, body = m.group(1), m.group(2)
        if "(model " in body or ":" not in name:
            return m.group(0)
        lib, fp = name.split(":", 1)
        path = os.path.join(FPLIB, lib + ".pretty", fp + ".kicad_mod")
        mod = re.search(r"\n\t\(model .*?\n\t\)", open(path, encoding="utf8").read(), re.S) if os.path.exists(path) else None
        if not mod:
            miss.append(name)
            return m.group(0)
        n_add += 1
        return f'\n\t(footprint "{name}"{body}' + mod.group(0).replace("\n\t", "\n\t\t") + "\n\t)"

    k = re.sub(r'\n\t\(footprint "([^"]+)"(.*?)\n\t\)', fix, k, flags=re.S)
    open(dst, "w", encoding="utf8").write(k)
    print(f"  model 3D ditambahkan: {n_add}, tanpa model: {sorted(set(miss))}")


def export_glb(board, out):
    cmd = [CLI, "pcb", "export", "glb", "--force", "--user-origin", f"{KX0}x{KY0}mm", "--subst-models",
           "--include-tracks", "--include-pads", "--include-zones", "--include-silkscreen", "--include-soldermask",
           "-o", out, board]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)


# ------------------------------ baca GLB KiCad ------------------------------
CTYPE = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read_glb(path):
    b = open(path, "rb").read()
    jl = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + jl])
    bin_ = b[20 + jl + 8:]

    def acc(i):
        a = j["accessors"][i]
        bv = j["bufferViews"][a["bufferView"]]
        dt, n = np.dtype(CTYPE[a["componentType"]]), NCOMP[a["type"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride", dt.itemsize * n)
        raw = np.frombuffer(bin_, np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * n, offset=off)
        if stride == dt.itemsize * n:
            return raw.view(dt).reshape(a["count"], n)
        return np.lib.stride_tricks.as_strided(raw, (a["count"], dt.itemsize * n), (stride, 1)).copy().view(dt).reshape(a["count"], n)

    def trs(nd):
        if "matrix" in nd:
            return np.array(nd["matrix"], float).reshape(4, 4).T
        m = np.eye(4)
        x, y, z, w = nd.get("rotation", [0, 0, 0, 1])
        m[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
        m[:3, :3] *= np.array(nd.get("scale", [1, 1, 1]))[None, :]
        m[:3, 3] = nd.get("translation", [0, 0, 0])
        return m

    out = []                                    # (referensi komponen / "", material, posisi, normal, indeks)

    def walk(n, parent, ref=""):
        nd = j["nodes"][n]
        m = parent @ trs(nd)
        if nd.get("name") and not nd["name"].startswith("=>"):
            ref = nd["name"]
        if "mesh" in nd:
            for p in j["meshes"][nd["mesh"]]["primitives"]:
                if p.get("mode", 4) != 4:
                    continue
                pos = acc(p["attributes"]["POSITION"]).astype(float)
                nor = acc(p["attributes"]["NORMAL"]).astype(float) if "NORMAL" in p["attributes"] else None
                idx = acc(p["indices"]).reshape(-1).astype(np.uint32) if "indices" in p else np.arange(len(pos), dtype=np.uint32)
                pos = pos @ m[:3, :3].T + m[:3, 3]
                if nor is not None:
                    nor = nor @ m[:3, :3].T
                out.append((ref, j["materials"][p["material"]], pos, nor, idx))
        for c in nd.get("children", []):
            walk(c, m, ref)

    for n in j["scenes"][j.get("scene", 0)]["nodes"]:
        walk(n, np.eye(4))
    return out


# glTF KiCad (meter, Y ke atas, -Z = maju) -> robot (mm, Z ke atas, Y maju)
G2R = np.array([[1000.0, 0, 0], [0, 0, -1000.0], [0, 1000.0, 0]])


# ------------------------------ ukuran dari Edge.Cuts ------------------------------
def arc_pts(a, mid, e, n=32):
    """titik-titik busur KiCad (start, mid, end) lewat lingkaran 3 titik"""
    (ax, ay), (bx, by), (cx, cy) = a, mid, e
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return [a, e]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.dist(a, (ux, uy))
    t0, tm, t1 = (math.atan2(p[1] - uy, p[0] - ux) for p in (a, mid, e))
    sweep = (t1 - t0) % (2 * math.pi)
    if (tm - t0) % (2 * math.pi) > sweep:                # busur lewat arah sebaliknya
        sweep -= 2 * math.pi
    return [(ux + r * math.cos(t0 + sweep * i / n), uy + r * math.sin(t0 + sweep * i / n)) for i in range(n + 1)]


def outline(path):
    """tepi luar papan (poligon koordinat robot) dari Edge.Cuts: segmen dirangkai jadi lintasan tertutup, yang
    luasnya terbesar = tepi luar (sisanya celah/potongan di dalam papan)"""
    k = open(path, encoding="utf8").read()
    segs = []
    for m in re.finditer(r'\((gr_line|gr_arc)\s+\(start ([\d.\-]+) ([\d.\-]+)\)\s*(?:\(mid ([\d.\-]+) ([\d.\-]+)\)\s*)?'
                         r'\(end ([\d.\-]+) ([\d.\-]+)\)[^()]*\(stroke[^()]*\([^()]*\)[^()]*\([^()]*\)\s*\)\s*\(layer "Edge\.Cuts"\)', k):
        g = m.groups()
        a, e = (float(g[1]), float(g[2])), (float(g[5]), float(g[6]))
        segs.append(arc_pts(a, (float(g[3]), float(g[4])), e) if g[0] == "gr_arc" else [a, e])
    loops = []
    while segs:
        loop = segs.pop(0)
        while math.dist(loop[0], loop[-1]) > 1e-3:
            for i, s in enumerate(segs):
                if math.dist(s[0], loop[-1]) < 1e-3:
                    loop += segs.pop(i)[1:]
                    break
                if math.dist(s[-1], loop[-1]) < 1e-3:
                    loop += segs.pop(i)[::-1][1:]
                    break
            else:
                break
        loops.append(np.array([(x - KX0, KY0 - y) for x, y in loop]))
    area = [abs(np.sum(p[:-1, 0] * p[1:, 1] - p[1:, 0] * p[:-1, 1])) for p in loops]
    return loops[int(np.argmax(area))]


def inside(poly, pts):
    """titik (N x 2) di dalam poligon? (ray casting)"""
    x, y = pts[:, 0][:, None], pts[:, 1][:, None]
    x0, y0, x1, y1 = poly[:-1, 0], poly[:-1, 1], poly[1:, 0], poly[1:, 1]
    cross = ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / np.where(y1 != y0, y1 - y0, 1) + x0)
    return cross.sum(1) % 2 == 1


def sensor_xy(path):
    k = open(path, encoding="utf8").read()
    out = []
    for m in re.finditer(r'\n\t\(footprint "OptoDevice:[^"]+"(.*?)\n\t\)', k, re.S):
        at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)', m.group(1)).groups()
        out.append((round(float(at[0]) - KX0, 2), round(KY0 - float(at[1]), 2)))
    return sorted(out)


# ------------------------------ 3. bagian mekanik v16 ------------------------------
# bagian v16 yang sekarang datang dari file KiCad (papan, komponen ber-footprint)
FROM_KICAD = ["PCB sensor", "Sensor QRE1113GR", "QRE1113GR", "Resistor SMD sensor", "Silkscreen", "Pad lubang",
              "IC mux", "C 100 nF mux", "Header JST XH", "PCB utama", "OLED socket", "Tombol", "Buzzer", "Saklar",
              "Elko C1", "Transistor S8050", "Resistor THT", "Dioda 1N5819", "JST PH motor", "JST XH baterai"]
ESP32_DX = -3.5                             # U1 di layout digeser 3,5 mm ke kiri dari tengah (README PCB utama)


def vertex_normals(pos, idx):
    t = idx.reshape(-1, 3)
    fn = np.cross(pos[t[:, 1]] - pos[t[:, 0]], pos[t[:, 2]] - pos[t[:, 0]])
    vn = np.zeros_like(pos)
    for c in range(3):
        np.add.at(vn, t[:, c], fn)
    ln = np.linalg.norm(vn, axis=1, keepdims=True)
    return vn / np.where(ln > 0, ln, 1)


def mech_parts(src):
    d = json.load(open(src, encoding="utf8"))
    out = []
    for o in d["meshes"]:
        if any(o["n"].startswith(p) for p in FROM_KICAD) and not o["n"].startswith("Tombol tutup"):
            continue
        pos = np.array(o["p"], float).reshape(-1, 3)
        if o["n"].startswith("ESP32"):
            pos[:, 0] += ESP32_DX
        idx = np.array(o["i"], np.uint32)
        c, r, met = d["mats"][o["m"]]
        mat = {"name": o["m"], "pbrMetallicRoughness": {"baseColorFactor": srgb_to_lin(c) + [1.0],
                                                        "metallicFactor": met, "roughnessFactor": r}}
        if o["m"] == "screen":
            mat["emissiveFactor"] = srgb_to_lin("#7fc4ff")
        out.append(("sayap" if o["g"] == "wing" else "mekanik", o["n"], mat, pos, vertex_normals(pos, idx), idx))
    return out


def srgb_to_lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [round(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4, 5) for v in c]


# ------------------------------ 4. tulis GLB gabungan ------------------------------
def write_glb(groups, extras, path):
    """groups: {nama node: {kunci material: (material, [pos], [normal], [indeks])}}"""
    j = {"asset": {"version": "2.0", "generator": "gen_rakitan.py (KiCad 10 + model v16)"},
         "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [], "meshes": [], "materials": [], "accessors": [],
         "bufferViews": [], "buffers": []}
    blob = bytearray()

    def view(arr, target):
        while len(blob) % 4:
            blob.append(0)
        j["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": arr.nbytes, "target": target})
        blob.extend(arr.tobytes())
        return len(j["bufferViews"]) - 1

    def accessor(arr, ctype, typ, target, minmax=False):
        a = {"bufferView": view(arr, target), "componentType": ctype, "count": len(arr), "type": typ}
        if minmax:
            a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()
        j["accessors"].append(a)
        return len(j["accessors"]) - 1

    # akar: isi dalam mm dan Z ke atas; diputar -90 derajat di X dan diskala 0,001 supaya penampil glTF biasa
    # (Y ke atas, meter) menampilkannya tegak
    j["nodes"].append({"name": "LFM_rakitan", "rotation": [-math.sqrt(0.5), 0, 0, math.sqrt(0.5)],
                       "scale": [0.001] * 3, "children": [], "extras": extras})
    for gname, mats in groups.items():
        prims = []
        for key, (mat, P, N, I) in mats.items():
            off, ii = 0, []
            for p, i in zip(P, I):
                ii.append(i + off)
                off += len(p)
            pos = np.concatenate(P).astype(np.float32)
            nor = np.concatenate(N).astype(np.float32)
            idx = np.concatenate(ii).astype(np.uint32)
            j["materials"].append(mat)
            prims.append({"attributes": {"POSITION": accessor(pos, 5126, "VEC3", 34962, True),
                                         "NORMAL": accessor(nor, 5126, "VEC3", 34962)},
                          "indices": accessor(idx, 5125, "SCALAR", 34963), "material": len(j["materials"]) - 1})
        j["meshes"].append({"name": gname, "primitives": prims})
        j["nodes"].append({"name": gname, "mesh": len(j["meshes"]) - 1})
        j["nodes"][0]["children"].append(len(j["nodes"]) - 1)
    j["buffers"].append({"byteLength": len(blob)})
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    while len(blob) % 4:
        blob.append(0)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))


def mat_key(m):
    pbr = m.get("pbrMetallicRoughness", {})
    return json.dumps([pbr.get("baseColorFactor"), pbr.get("metallicFactor"), pbr.get("roughnessFactor"),
                       m.get("alphaMode"), m.get("emissiveFactor")])


def gltfpack(src, dst, *flags):
    """kompres GLB dengan gltfpack (npm, versi dikunci); False kalau Node.js tidak ada"""
    npx = shutil.which("npx") or r"C:\Program Files\nodejs\npx.cmd"
    if not os.path.exists(npx):
        return False
    r = subprocess.run([npx, "-y", "gltfpack@1.2.0", "-i", src, "-o", dst, "-kn", "-km", "-ke", *flags],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    return True


if __name__ == "__main__":
    groups, wheels, extras = {}, [], {"pcb": {}}
    tmp = tempfile.mkdtemp(prefix="rakitan-")
    for name, (board, z0) in BOARDS.items():
        proj = os.path.join(tmp, name)
        os.makedirs(proj)
        dst = os.path.join(proj, os.path.basename(board))
        print(name)
        add_models(board, dst)
        pro = board.replace(".kicad_pcb", ".kicad_pro")
        if os.path.exists(pro):
            shutil.copy(pro, os.path.join(proj, os.path.basename(pro)))
        glb = os.path.join(tmp, name + ".glb")
        export_glb(dst, glb)
        mats = groups.setdefault(name, {})
        low, qre_z = (1e9, ""), 1e9
        for ref, mat, pos, nor, idx in read_glb(glb):
            pos = pos @ G2R.T + [0, 0, z0]
            nor = nor @ (G2R / 1000).T if nor is not None else vertex_normals(pos, idx)
            m = dict(mat)
            m.pop("name", None)
            e = mats.setdefault(mat_key(m), (m, [], [], []))
            e[1].append(pos), e[2].append(nor), e[3].append(idx)
            low = min(low, (float(pos[:, 2].min()), ref))
            if name == "pcb_sensor" and re.fullmatch(r"U([1-9]|1[0-2])", ref):      # U1-U12 = QRE1113GR
                qre_z = min(qre_z, float(pos[:, 2].min()))
        poly = outline(board)
        allp = np.concatenate([p for e in mats.values() for p in e[1]])
        extras["pcb"][name] = {"x": [round(float(poly[:, 0].min()), 2), round(float(poly[:, 0].max()), 2)],
                               "y": [round(float(poly[:, 1].min()), 2), round(float(poly[:, 1].max()), 2)],
                               "z": [z0, z0 + 1.6], "zmin": round(low[0], 2), "zmin_ref": low[1],
                               "zmax": round(float(allp[:, 2].max()), 2)}
        if name == "pcb_sensor":
            extras["pcb"][name]["y_di_xmax"] = round(float(poly[np.argmax(poly[:, 0]), 1]), 2)
            extras["muka_qre"] = round(qre_z, 2)
            sens_poly, sens_pts = poly, allp
    shutil.rmtree(tmp, ignore_errors=True)

    # celah tegak terkecil antara bagian bawah PCB utama (kaki THT dll.) dan PCB sensor di area tumpang (hidung)
    under = np.concatenate([p for e in groups["pcb_utama"].values() for p in e[1]])
    under = under[(under[:, 2] < BOARDS["pcb_utama"][1]) & inside(sens_poly, under[:, :2])]
    top_z = BOARDS["pcb_sensor"][1] + 1.6
    if len(under):
        x0, x1, y0, y1 = under[:, 0].min() - 2, under[:, 0].max() + 2, under[:, 1].min() - 2, under[:, 1].max() + 2
        near = sens_pts[(sens_pts[:, 0] > x0) & (sens_pts[:, 0] < x1) & (sens_pts[:, 1] > y0) & (sens_pts[:, 1] < y1)]
        top_z = max([top_z] + ([float(near[:, 2].max())] if len(near) else []))
        extras["celah_tumpang"] = round(float(under[:, 2].min()) - top_z, 2)
    else:
        extras["celah_tumpang"] = round(BOARDS["pcb_utama"][1] - top_z, 2)

    v16 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "viewer", "model.json")
    for gname, pname, mat, pos, nor, idx in mech_parts(v16):
        e = groups.setdefault(gname, {}).setdefault(mat_key(mat), (mat, [], [], []))
        e[1].append(pos), e[2].append(nor), e[3].append(idx)
        if pname.startswith("Ban merah"):
            wheels.append([round(float(v), 2) for v in (*pos.min(0), *pos.max(0))])

    extras["sensor"] = sensor_xy(BOARDS["pcb_sensor"][0])
    extras["roda"] = wheels                     # [xmin, ymin, zmin, xmax, ymax, zmax] tiap ban
    extras["grup"] = {}
    for gname, mats in groups.items():
        allp = np.concatenate([p for e in mats.values() for p in e[1]])
        extras["grup"][gname] = [round(float(v), 2) for v in (*allp.min(0), *allp.max(0))]

    raw = os.path.join(tempfile.gettempdir(), "LFM_rakitan_mentah.glb")
    write_glb(groups, extras, raw)
    n_tri = sum(len(i) for m in groups.values() for e in m.values() for i in e[3]) // 3
    print(f"gabungan: {n_tri} segitiga, {sum(len(m) for m in groups.values())} primitif, "
          f"{os.path.getsize(raw) / 1e6:.1f} MB")
    # LFM_rakitan.glb: kuantisasi saja (KHR_mesh_quantization, terbaca Blender/penampil glTF umum).
    # LFM_rakitan_web.json: + kompresi meshopt, GLB-nya di-base64 di dalam JSON karena artifact claude.ai tidak
    # menyajikan file .glb; dibaca index.html.
    out, web = os.path.join(HERE, "LFM_rakitan.glb"), os.path.join(HERE, "LFM_rakitan_web.json")
    packed = os.path.join(tempfile.gettempdir(), "LFM_rakitan_web.glb")
    if gltfpack(raw, out) and gltfpack(raw, packed, "-cc"):
        json.dump({"isi": "GLB (meshopt) base64, dari gen_rakitan.py",
                   "glb": base64.b64encode(open(packed, "rb").read()).decode()}, open(web, "w"))
        os.remove(packed)
        for f in (out, web):
            print(f"{os.path.basename(f)}: {os.path.getsize(f) / 1e6:.1f} MB")
    else:
        shutil.copy(raw, out)
        print("Node.js tidak ditemukan: LFM_rakitan.glb tanpa kompresi, LFM_rakitan_web.json (viewer) tidak dibuat")
    os.remove(raw)
    print(json.dumps(extras))
