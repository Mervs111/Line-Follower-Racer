"""Bangun scene CoppeliaSim robot Line Follower Micro di arena grid, lewat ZMQ remote API.

Isi scene:
- arena grid 4 x 4 simpul, jarak 30 cm, garis hitam 2 cm di atas alas putih (LFM_arena),
- robot dinamis ukuran asli: badan, 2 roda O34 (jarak 91 mm) dengan motor velocity control (maks 500 RPM),
  skid depan (bola bebas), 12 vision sensor 4 x 4 piksel di posisi QRE1113GR rev B (hanya merender LFM_arena),
- tampilan robot dari rakitan PCB (mesh/*.obj, lihat make_mesh.py), menempel ke badan,
- 2 kamera untuk rekaman video: LFM_cam (seluruh arena) dan LFM_chase (mengikuti robot).

Cara pakai (CoppeliaSim 4.6 atau lebih baru disarankan, ZMQ remote API aktif bawaan):
    1. Buka CoppeliaSim, File > New scene.
    2. pip install coppeliasim-zmqremoteapi-client
    3. python build_scene.py            -> scene tersimpan di lfm_grid.ttt (folder ini)
Skrip boleh dijalankan ulang: objek LFM_* lama dihapus dulu.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import lfm_control as lc  # noqa: E402

W = -1                      # sim.handle_world
COLS = ROWS = 4
BODY_SIZE = (0.074, 0.11, 0.02)     # kotak dinamis pembawa massa (tidak terlihat bila mesh ada)
BODY_POS = (0.0, 0.02, 0.022)       # pusat kotak di koordinat robot
MASS_BODY = 0.19                    # total robot +-0,22 kg (2x18650, PCB, motor, modul)
MASS_WHEEL = 0.010
MASS_SKID = 0.003
WHEEL_W = 0.012
SKID_D = 0.010
MOTOR_TORQUE = 0.04                 # N.m, perkiraan torsi stall N20 500 RPM
SENSOR_RES = 4                      # piksel per sisi vision sensor
SENSOR_SPOT = 0.004                 # lebar daerah baca (ortho), +-QRE1113GR pada 3 mm
ARENA_MARGIN = 0.2
Q_DOWN = [1.0, 0.0, 0.0, 0.0]               # (x, y, z, w): putar 180 deg terhadap X, sumbu Z menghadap lantai
Q_AXLE = [0.0, -math.sqrt(0.5), 0.0, math.sqrt(0.5)]   # Z sendi ke -X robot: kecepatan + = maju


def connect():
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient
    client = RemoteAPIClient()
    try:
        sim = client.require("sim")
    except Exception:
        sim = client.getObject("sim")         # CoppeliaSim < 4.6
    return client, sim


def find(sim, alias):
    try:
        return sim.getObject("/" + alias, {"noError": True})
    except Exception:
        return -1


def remove_old(sim):
    for alias in ("LFM_robot", "LFM_arena", "LFM_floor", "LFM_cam", "LFM_S_mark", "LFM_T_mark", "LFM_cubes"):
        h = find(sim, alias)
        if h != -1:
            objs = sim.getObjectsInTree(h, sim.handle_all, 0)
            sim.removeObjects(objs)


def primitive(sim, kind, size, pos, rgb, alias, parent=-1, dynamic=False, respondable=False, mass=None,
              quat=None, visible=True):
    kinds = {"box": ("primitiveshape_cuboid", 0), "sphere": ("primitiveshape_spheroid", 1),
             "cyl": ("primitiveshape_cylinder", 2)}
    try:
        h = sim.createPrimitiveShape(getattr(sim, kinds[kind][0]), list(size), 0)
    except Exception:
        h = sim.createPureShape(kinds[kind][1], 16, list(size), mass or 0.0)     # API lama
    sim.setObjectPosition(h, W, list(pos))
    if quat is not None:
        sim.setObjectQuaternion(h, W, list(quat))
    sim.setShapeColor(h, None, sim.colorcomponent_ambient_diffuse, list(rgb))
    sim.setObjectAlias(h, alias)
    sim.setObjectInt32Param(h, sim.shapeintparam_static, 0 if dynamic else 1)
    sim.setObjectInt32Param(h, sim.shapeintparam_respondable, 1 if respondable else 0)
    if dynamic and mass:
        vol = {"box": size[0] * size[1] * size[2], "sphere": math.pi / 6 * size[0] ** 3,
               "cyl": math.pi / 4 * size[0] ** 2 * size[2]}[kind]
        sim.computeMassAndInertia(h, mass / vol)
    if not visible:
        sim.setObjectInt32Param(h, sim.objintparam_visibility_layer, 0)
    if parent != -1:
        sim.setObjectParent(h, parent, True)
    return h


def joint(sim, spherical, pos, alias, parent, quat=None):
    sub = sim.joint_spherical_subtype if spherical else sim.joint_revolute_subtype
    h = sim.createJoint(sub, sim.jointmode_dynamic, 0, [0.02, 0.006])
    sim.setObjectPosition(h, W, list(pos))
    if quat is not None:
        sim.setObjectQuaternion(h, W, list(quat))
    sim.setObjectAlias(h, alias)
    sim.setObjectParent(h, parent, True)
    if not spherical:
        try:
            sim.setObjectInt32Param(h, sim.jointintparam_dynctrlmode, sim.jointdynctrl_velocity)
        except Exception:
            sim.setObjectInt32Param(h, sim.jointintparam_motor_enabled, 1)        # API lama
        try:
            sim.setJointTargetForce(h, MOTOR_TORQUE)
        except Exception:
            sim.setJointForce(h, MOTOR_TORQUE)
        sim.setJointTargetVelocity(h, 0)
    return h


def vision_sensor(sim, res, ortho_size_or_angle, near, far, perspective, explicit, alias, pos, quat, parent=-1,
                  body_size=0.003, bg=None):
    opts = (1 if explicit else 0) | (2 if perspective else 0) | (64 if bg else 0)
    fl = [near, far, ortho_size_or_angle, body_size, body_size, body_size, 0, 0, 0, 0, 0]
    if bg:
        fl[6:9] = list(bg)
    h = sim.createVisionSensor(opts, [res[0], res[1], 0, 0], fl)
    sim.setObjectPosition(h, W, list(pos))
    sim.setObjectQuaternion(h, W, list(quat))
    sim.setObjectAlias(h, alias)
    if parent != -1:
        sim.setObjectParent(h, parent, True)
    return h


def look_at_quat(pos, target):
    """Kuaternion (x, y, z, w) vision sensor di pos yang memandang target, atas gambar = atas dunia."""
    z = [t - p for t, p in zip(target, pos)]
    n = math.sqrt(sum(c * c for c in z))
    z = [c / n for c in z]
    up = [0.0, 0.0, 1.0]
    d = sum(a * b for a, b in zip(up, z))
    y = [u - d * c for u, c in zip(up, z)]
    n = math.sqrt(sum(c * c for c in y))
    y = [c / n for c in y]
    x = [y[1] * z[2] - y[2] * z[1], y[2] * z[0] - y[0] * z[2], y[0] * z[1] - y[1] * z[0]]
    m = [[x[0], y[0], z[0]], [x[1], y[1], z[1]], [x[2], y[2], z[2]]]
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        return [(m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s, 0.25 * s]
    if m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        return [0.25 * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s, (m[2][1] - m[1][2]) / s]
    if m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        return [(m[0][1] + m[1][0]) / s, 0.25 * s, (m[1][2] + m[2][1]) / s, (m[0][2] - m[2][0]) / s]
    s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
    return [(m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, 0.25 * s, (m[1][0] - m[0][1]) / s]


def build_arena(sim):
    span = (COLS - 1) * lc.GRID_STEP
    c = span / 2
    # lantai respondable tak terlihat (permukaan di z = 0), alas putih dan garis hanya tampilan
    primitive(sim, "box", (span + 2 * ARENA_MARGIN + 1, span + 2 * ARENA_MARGIN + 1, 0.02), (c, c, -0.01),
              (0.8, 0.8, 0.8), "LFM_floor", respondable=True, visible=False)
    parts = [primitive(sim, "box", (span + 2 * ARENA_MARGIN, span + 2 * ARENA_MARGIN, 0.0004), (c, c, 0.0002),
                       (1, 1, 1), "LFM_alas")]
    for k, (cx, cy, lx, ly) in enumerate(lc.grid_segments(COLS, ROWS)):
        parts.append(primitive(sim, "box", (lx, ly, 0.0002), (cx, cy, 0.0005), (0.02, 0.02, 0.02), "LFM_garis%d" % k))
    arena = sim.groupShapes(parts, False)
    sim.setObjectAlias(arena, "LFM_arena")
    sim.setObjectInt32Param(arena, sim.shapeintparam_static, 1)
    sim.setObjectInt32Param(arena, sim.shapeintparam_respondable, 0)
    for alias, (i, j), off, rgb in (("LFM_S_mark", (0, 0), -0.07, (0.18, 0.49, 0.2)),
                                    ("LFM_T_mark", (COLS - 1, ROWS - 1), 0.07, (0.78, 0.16, 0.16))):
        primitive(sim, "box", (0.05, 0.05, 0.001), (i * lc.GRID_STEP + off, j * lc.GRID_STEP + off, 0.0008), rgb,
                  alias)
    return arena


def load_obj(path):
    verts, idx = [], []
    for line in open(path):
        if line.startswith("v "):
            verts.extend(float(v) for v in line.split()[1:4])
        elif line.startswith("f "):
            idx.extend(int(v.split("/")[0]) - 1 for v in line.split()[1:4])
    return verts, idx


def build_visual(sim, body):
    """Tampilan robot dari mesh/*.obj (koordinat robot = dunia, karena robot dibangun di titik nol)."""
    man = json.load(open(os.path.join(HERE, "mesh", "mesh.json")))
    shapes = []
    for g in man["groups"]:
        v, f = load_obj(os.path.join(HERE, "mesh", g["file"]))
        try:
            h = sim.createMeshShape(0, math.radians(30), v, f)
        except Exception:
            h = sim.createShape(0, math.radians(30), v, f, None, None, None, None)
        sim.setShapeColor(h, None, sim.colorcomponent_ambient_diffuse, g["rgb"])
        shapes.append(h)
    vis = sim.groupShapes(shapes, False) if len(shapes) > 1 else shapes[0]
    sim.setObjectAlias(vis, "LFM_tampilan")
    sim.setObjectInt32Param(vis, sim.shapeintparam_static, 1)
    sim.setObjectInt32Param(vis, sim.shapeintparam_respondable, 0)
    sim.setObjectParent(vis, body, True)
    return vis


def build_robot(sim, arena, with_mesh=True):
    """Robot dibangun di titik nol dunia dengan sumbu = sumbu robot (x kanan, y maju), lalu dipindah ke start."""
    body = primitive(sim, "box", BODY_SIZE, BODY_POS, (0.1, 0.35, 0.75), "LFM_robot", dynamic=True,
                     respondable=False, mass=MASS_BODY)
    origin = sim.createDummy(0.01)
    sim.setObjectPosition(origin, W, [0, 0, 0])
    sim.setObjectAlias(origin, "LFM_origin")       # titik tengah poros di lantai (pose robot)
    sim.setObjectParent(origin, body, True)
    for side, sx in (("L", -1), ("R", 1)):
        x = sx * (lc.TRACK / 2)
        j = joint(sim, False, (x, 0, lc.WHEEL_R), "LFM_joint" + side, body, Q_AXLE)
        wheel = primitive(sim, "cyl", (2 * lc.WHEEL_R, 2 * lc.WHEEL_R, WHEEL_W), (x, 0, lc.WHEEL_R),
                          (0.65, 0.02, 0.04), "LFM_wheel" + side, dynamic=True, respondable=True, mass=MASS_WHEEL,
                          quat=Q_AXLE)
        sim.setObjectParent(wheel, j, True)
        # velg abu-abu + jari-jari putih supaya putaran roda terlihat
        primitive(sim, "cyl", (0.022, 0.022, WHEEL_W + 0.001), (x, 0, lc.WHEEL_R), (0.37, 0.39, 0.42),
                  "LFM_hub" + side, parent=wheel, quat=Q_AXLE)
        primitive(sim, "box", (WHEEL_W + 0.0015, 0.003, 0.026), (x, 0, lc.WHEEL_R), (0.95, 0.95, 0.95),
                  "LFM_spoke" + side, parent=wheel)
    sk_y = lc.SKID_POS[0][1]
    sj = joint(sim, True, (0, sk_y, SKID_D / 2), "LFM_skidjoint", body)
    skid = primitive(sim, "sphere", (SKID_D, SKID_D, SKID_D), (0, sk_y, SKID_D / 2), (0.85, 0.82, 0.75), "LFM_skid",
                     dynamic=True, respondable=True, mass=MASS_SKID)
    sim.setObjectParent(skid, sj, True)
    for k, (sx, sy) in enumerate(zip(lc.SENSOR_X_MM, lc.SENSOR_Y_MM)):
        h = vision_sensor(sim, (SENSOR_RES, SENSOR_RES), SENSOR_SPOT, 0.0005, 0.02, False, False, "LFM_S%d" % (k + 1),
                          (sx / 1000, sy / 1000, lc.SENSOR_H), Q_DOWN, body)
        sim.setObjectInt32Param(h, sim.visionintparam_entity_to_render, arena)
    chase = vision_sensor(sim, (640, 360), math.radians(60), 0.01, 3.0, True, True, "LFM_chase",
                          (0, -0.30, 0.22), look_at_quat((0, -0.30, 0.22), (0, 0.15, 0)), body, 0.01,
                          bg=(0.86, 0.89, 0.93))
    vis = -1
    if with_mesh:
        try:
            vis = build_visual(sim, body)
            sim.setObjectInt32Param(body, sim.objintparam_visibility_layer, 0)
        except Exception as e:       # tanpa mesh: kotak biru tetap terlihat
            print("PERINGATAN: mesh tampilan gagal dibuat (%s); robot tampil sebagai kotak." % e)
    try:
        sim.setModelProperty(body, 0)              # robot = satu model (bisa dipilih/dipindah utuh)
    except Exception:
        pass
    return body, chase, vis


def place_robot(sim, body, x, y, heading):
    """Letakkan robot: titik tengah poros di (x, y), arah maju = heading (rad, dari sumbu X dunia)."""
    g = heading - math.pi / 2
    c, s = math.cos(g), math.sin(g)
    bx, by, bz = BODY_POS
    sim.setObjectPosition(body, W, [x + bx * c - by * s, y + bx * s + by * c, bz])
    sim.setObjectOrientation(body, W, [0, 0, g])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "lfm_grid.ttt"))
    ap.add_argument("--no-mesh", action="store_true", help="robot tampil sebagai kotak (lebih ringan)")
    args = ap.parse_args()
    client, sim = connect()
    if sim.getSimulationState() != sim.simulation_stopped:
        sim.stopSimulation()
        while sim.getSimulationState() != sim.simulation_stopped:
            pass
    remove_old(sim)
    try:
        sim.setFloatParam(sim.floatparam_simulation_time_step, 0.005)
    except Exception as e:
        print("PERINGATAN: dt simulasi tidak bisa diatur (%s); atur manual 5 ms." % e)
    arena = build_arena(sim)
    body, chase, vis = build_robot(sim, arena, not args.no_mesh)
    span = (COLS - 1) * lc.GRID_STEP
    cam_pos = (span / 2, -0.50, 0.95)
    vision_sensor(sim, (1280, 720), math.radians(60), 0.01, 5.0, True, True, "LFM_cam", cam_pos,
                  look_at_quat(cam_pos, (span / 2, span / 2 - 0.05, 0)), -1, 0.02, bg=(0.86, 0.89, 0.93))
    place_robot(sim, body, 0.02, 0.0, 0.0)
    sim.saveScene(os.path.abspath(args.out))
    print("scene tersimpan:", os.path.abspath(args.out))


if __name__ == "__main__":
    main()
