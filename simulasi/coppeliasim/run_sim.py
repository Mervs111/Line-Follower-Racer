"""Jalankan skenario path planning robot Line Follower Micro di CoppeliaSim dan rekam videonya.

Kendali = lfm_control.Controller (sama dengan uji 2D). Skrip ini membaca 12 vision sensor dan encoder roda
(posisi sendi), menghitung kecepatan roda, lalu memajukan simulasi satu langkah (mode stepping, dt 5 ms).

    python run_sim.py                                   # rute slide 8 -> hasil/coppeliasim_slide.mp4
    python run_sim.py --scenario bfs                    # rute terpendek S (0,0) -> T (3,3)
    python run_sim.py --scenario bfs --blocked 1,0 2,2 1,2   # + kubus di simpul terhalang
    python run_sim.py --no-record                       # tanpa video (lebih cepat)
    python run_sim.py --kinematic                       # cadangan bila fisika roda bermasalah

Butuh: CoppeliaSim terbuka dengan scene lfm_grid.ttt (dari build_scene.py), pip install
coppeliasim-zmqremoteapi-client numpy pillow imageio imageio-ffmpeg.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import lfm_control as lc  # noqa: E402
import build_scene as bs  # noqa: E402

W = -1
DT = 0.005


class Sim:
    """Pembungkus API yang berbeda antar versi CoppeliaSim (stepping, gambar vision sensor)."""

    def __init__(self):
        self.client, self.sim = bs.connect()
        sim = self.sim
        try:
            sim.setStepping(True)
            self._step = sim.step
            self._stepping = sim.setStepping
        except Exception:
            self.client.setStepping(True)           # CoppeliaSim < 4.6
            self._step = self.client.step
            self._stepping = self.client.setStepping
        self._stepping(False)

    def step(self):
        self._step()

    def image(self, h):
        try:
            img, res = self.sim.getVisionSensorImg(h)
        except Exception:
            img, rx, ry = self.sim.getVisionSensorCharImage(h)
            res = [rx, ry]
        arr = np.frombuffer(img, dtype=np.uint8).reshape(res[1], res[0], 3)
        return np.flipud(arr)                       # baris pertama buffer = bawah gambar

    def intensity(self, h):
        try:
            img, _ = self.sim.getVisionSensorImg(h)
        except Exception:
            img = self.sim.getVisionSensorCharImage(h)[0]
        return np.frombuffer(img, dtype=np.uint8).mean() / 255.0

    def start(self):
        self._stepping(True)
        self.sim.startSimulation()

    def stop(self):
        sim = self.sim
        sim.stopSimulation()
        while sim.getSimulationState() != sim.simulation_stopped:
            time.sleep(0.05)
        self._stepping(False)


def robot_pose(sim, origin):
    m = sim.getObjectMatrix(origin, W)
    return m[3], m[7], math.atan2(m[5], m[1])       # posisi titik tengah poros, arah sumbu y robot


class Unwrap:
    """Sudut sendi roda (siklik -pi..pi) -> sudut kumulatif (encoder)."""

    def __init__(self):
        self.prev = None
        self.total = 0.0

    def __call__(self, a):
        if self.prev is not None:
            d = a - self.prev
            d = (d + math.pi) % (2 * math.pi) - math.pi
            self.total += d
        self.prev = a
        return self.total


def set_kinematic(sim, h, on):
    """Mode cadangan: semua bagian robot statis, pose dihitung dari kecepatan roda."""
    for k in ("LFM_robot", "LFM_wheelL", "LFM_wheelR", "LFM_skid"):
        sim.setObjectInt32Param(h[k], sim.shapeintparam_static, 1 if on else 0)
        if k != "LFM_robot":
            sim.setObjectInt32Param(h[k], sim.shapeintparam_respondable, 0 if on else 1)
    for k in ("LFM_jointL", "LFM_jointR", "LFM_skidjoint"):
        mode = sim.jointmode_dynamic
        if on:
            mode = getattr(sim, "jointmode_kinematic", None) or sim.jointmode_passive
        try:
            sim.setJointMode(h[k], mode, 0)
        except Exception:
            pass
        if not on and k != "LFM_skidjoint":
            try:
                sim.setObjectInt32Param(h[k], sim.jointintparam_dynctrlmode, sim.jointdynctrl_velocity)
            except Exception:
                pass


def hud(frame, inset, lines):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.fromarray(frame)
    if inset is not None:
        sm = Image.fromarray(inset).resize((448, 252))
        x0, y0 = img.width - sm.width - 16, img.height - sm.height - 16
        ImageDraw.Draw(img).rectangle([x0 - 3, y0 - 3, x0 + sm.width + 2, y0 + sm.height + 2], fill=(13, 29, 51))
        img.paste(sm, (x0, y0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        try:
            font = ImageFont.load_default(size=26)
        except Exception:
            font = ImageFont.load_default()
    d.rectangle([0, 0, img.width, 44 + 34 * (len(lines) - 1)], fill=(13, 29, 51))
    for k, ln in enumerate(lines):
        d.text((16, 8 + 34 * k), ln, fill=(255, 255, 255) if k == 0 else (156, 199, 238), font=font)
    return np.asarray(img)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=["slide", "bfs"], default="slide")
    ap.add_argument("--start", default="0,0")
    ap.add_argument("--goal", default="3,3")
    ap.add_argument("--blocked", nargs="*", default=[])
    ap.add_argument("--speed", type=float, default=0.40)
    ap.add_argument("--kp", type=float, default=0.0060)
    ap.add_argument("--kd", type=float, default=0.00030)
    ap.add_argument("--t-max", type=float, default=40.0)
    ap.add_argument("--no-record", action="store_true")
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--kinematic", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    start = tuple(int(v) for v in args.start.split(","))
    goal = tuple(int(v) for v in args.goal.split(","))
    blocked = [tuple(int(v) for v in b.split(",")) for b in args.blocked]
    plan, start, heading, route = lc.make_scenario(args.scenario, start, goal, blocked, args.speed)
    if args.scenario == "slide":
        goal = (3, 3)
    if route:
        print("rute:", route)
    for k, st in enumerate(plan):
        print("indeks %d: jika %s lakukan %s" % (k + 1, lc.TRIGGER_TEXT[st["trigger"]], lc.ACTION_TEXT[st["action"]]))

    S = Sim()
    sim = S.sim
    if sim.getSimulationState() != sim.simulation_stopped:
        S.stop()
    body = sim.getObject("/LFM_robot")
    h = {sim.getObjectAlias(o): o for o in sim.getObjectsInTree(body, sim.handle_all, 0)}
    sens = [h["LFM_S%d" % (k + 1)] for k in range(lc.N_SENS)]
    jl, jr, origin = h["LFM_jointL"], h["LFM_jointR"], h["LFM_origin"]
    cam, chase = sim.getObject("/LFM_cam"), h["LFM_chase"]
    try:
        sim.setFloatParam(sim.floatparam_simulation_time_step, DT)
    except Exception:
        pass

    x0, y0, yaw0 = lc.start_pose(start, heading)
    bs.place_robot(sim, body, x0, y0, yaw0)
    cubes = []
    for i, j in blocked:          # kubus misi 4 cm di simpul terhalang (tidak terlihat oleh sensor garis)
        cubes.append(bs.primitive(sim, "box", (0.04, 0.04, 0.04), (i * lc.GRID_STEP, j * lc.GRID_STEP, 0.0205),
                                  (0.98, 0.66, 0.15), "LFM_cube%d%d" % (i, j)))
    if args.kinematic:
        set_kinematic(sim, h, True)

    ctrl = lc.Controller(plan, speed=args.speed, kp=args.kp, kd=args.kd)
    unl, unr = Unwrap(), Unwrap()
    writer = None
    out = args.out or os.path.join(HERE, "..", "hasil", "coppeliasim_%s.mp4" % args.scenario)
    if not args.no_record:
        import imageio.v2 as imageio
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        rec_every = max(1, int(round(1.0 / args.fps / DT)))
        writer = imageio.get_writer(out, fps=1.0 / (rec_every * DT), codec="libx264", quality=8,
                                    macro_block_size=8)
    kin = {"x": x0, "y": y0, "yaw": yaw0, "wl": 0.0, "wr": 0.0, "el": 0.0, "er": 0.0}
    white = black = None
    t_done = None
    traj = []
    last_status = ""
    wall0 = time.time()
    S.start()
    try:
        S.step()
        n = 0
        while True:
            t = sim.getSimulationTime()
            raw = [S.intensity(s) for s in sens]
            if white is None:
                white, black = max(raw), min(raw)
                print("kalibrasi: putih %.3f, hitam %.3f" % (white, black))
                if white - black < 0.15:
                    print("PERINGATAN: kontras sensor kecil; cek lampu scene dan entity_to_render sensor.")
            vals = [max(0.0, min(1000.0, (white - r) / max(1e-6, white - black) * 1000)) for r in raw]
            if args.kinematic:
                el, er = kin["el"], kin["er"]
            else:
                el, er = unl(sim.getJointPosition(jl)), unr(sim.getJointPosition(jr))
            wl, wr = ctrl.step(t, DT, vals, el, er)
            if args.kinematic:
                a = DT / (0.04 + DT)
                kin["wl"] += a * (wl - kin["wl"])
                kin["wr"] += a * (wr - kin["wr"])
                v = (kin["wl"] + kin["wr"]) / 2 * lc.WHEEL_R
                w = (kin["wr"] - kin["wl"]) * lc.WHEEL_R / lc.TRACK
                kin["x"] += v * math.cos(kin["yaw"]) * DT
                kin["y"] += v * math.sin(kin["yaw"]) * DT
                kin["yaw"] += w * DT
                kin["el"] += kin["wl"] * DT
                kin["er"] += kin["wr"] * DT
                bs.place_robot(sim, body, kin["x"], kin["y"], kin["yaw"])
                sim.setJointPosition(jl, kin["el"] % (2 * math.pi))
                sim.setJointPosition(jr, kin["er"] % (2 * math.pi))
            else:
                sim.setJointTargetVelocity(jl, wl)
                sim.setJointTargetVelocity(jr, wr)
            px, py, pyaw = robot_pose(sim, origin)
            v_now = 0.0 if not traj else math.hypot(px - traj[-1][1], py - traj[-1][2]) / DT
            traj.append((t, px, py, pyaw, ctrl.status))
            if ctrl.status != last_status:
                print("%6.2f s  %s" % (t, ctrl.status))
                last_status = ctrl.status
            if not args.kinematic and abs(t - 0.3) < DT / 2:
                fwd = (px - x0) * math.cos(yaw0) + (py - y0) * math.sin(yaw0)
                if fwd < 0.01:
                    raise RuntimeError("robot tidak maju (%.1f mm dalam 0,3 s). Kalau mundur: balik tanda Q_AXLE "
                                       "di build_scene.py lalu bangun ulang scene; kalau diam: cek torsi motor "
                                       "dan gesekan roda, atau pakai --kinematic." % (fwd * 1000))
            if writer is not None and n % rec_every == 0:
                sim.handleVisionSensor(cam)
                sim.handleVisionSensor(chase)
                frame = hud(S.image(cam), S.image(chase),
                            [ctrl.status, "t = %.2f s   v = %.2f m/s   CoppeliaSim, robot Line Follower Micro" %
                             (t, v_now)])
                if n == 0:
                    from PIL import Image
                    Image.fromarray(frame).save(os.path.join(os.path.dirname(os.path.abspath(out)),
                                                             "cek_kamera.png"))
                writer.append_data(frame)
            if ctrl.state == "done" and t_done is None:
                t_done = t
            if (t_done is not None and t - t_done > 0.6) or t > args.t_max:
                break
            S.step()
            n += 1
    finally:
        S.stop()
        if writer is not None:
            writer.close()
        if args.kinematic:
            set_kinematic(sim, h, False)
        if cubes:
            sim.removeObjects(cubes)
        bs.place_robot(sim, body, 0.02, 0.0, 0.0)

    t_end, xe, ye = traj[-1][0], traj[-1][1], traj[-1][2]
    gx, gy = goal[0] * lc.GRID_STEP, goal[1] * lc.GRID_STEP
    err = math.hypot(xe - gx, ye - gy)
    ok = ctrl.status.startswith("Selesai") and err < 0.03
    print("status akhir:", ctrl.status)
    print("waktu simulasi %.2f s (komputer %.0f s), selisih ke T %.1f mm -> %s" %
          (t_done or t_end, time.time() - wall0, err * 1000, "LULUS" if ok else "GAGAL"))
    res = {"scenario": args.scenario, "route": route, "plan": plan, "speed": args.speed, "kp": args.kp,
           "kd": args.kd, "kinematic": args.kinematic, "time_s": t_done or t_end, "error_mm": err * 1000,
           "status": ctrl.status, "ok": ok, "log": ctrl.log,
           "traj": [r[:4] for r in traj[::10]]}
    jpath = os.path.splitext(out)[0] + ".json"
    os.makedirs(os.path.dirname(os.path.abspath(jpath)), exist_ok=True)
    json.dump(res, open(jpath, "w"), indent=1)
    if writer is not None:
        print("video:", os.path.abspath(out))
    print("log:", os.path.abspath(jpath))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
