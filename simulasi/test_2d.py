"""Uji 2D logika kendali (tanpa CoppeliaSim): kinematika roda diferensial + model sensor sederhana.

Dipakai untuk mengecek dan menyetel lfm_control.py sebelum dijalankan di CoppeliaSim, dan sebagai cadangan visual
(gambar lintasan PNG, opsional video tampak atas MP4).

    python test_2d.py                         # rute slide 8 (S -> T, indeks 1 kiri ... 6 berhenti)
    python test_2d.py --scenario bfs          # rute terpendek otomatis S (0,0) -> T (3,3)
    python test_2d.py --scenario bfs --blocked 1,0 2,2    # dengan simpul terhalang (mis. kubus)
    python test_2d.py --video hasil/uji2d.mp4  # + video tampak atas

Butuh: numpy, matplotlib (+ imageio, imageio-ffmpeg untuk --video).
"""
import argparse
import math
import os
import random

import lfm_control as lc

MOTOR_TAU = 0.04        # konstanta waktu motor + inersia (s), perkiraan
SPOT_R = 0.002          # jari-jari bintik baca QRE1113GR di lantai (m), perkiraan
NOISE = 20              # derau bacaan (skala 0-1000)


def coverage(px, py, segs):
    """Fraksi bintik sensor (lingkaran SPOT_R) yang berada di atas garis hitam."""
    n = hit = 0
    for i in range(-3, 4):
        for j in range(-3, 4):
            dx, dy = i / 3 * SPOT_R, j / 3 * SPOT_R
            if dx * dx + dy * dy > SPOT_R * SPOT_R:
                continue
            n += 1
            x, y = px + dx, py + dy
            for cx, cy, w, h in segs:
                if abs(x - cx) <= w / 2 and abs(y - cy) <= h / 2:
                    hit += 1
                    break
    return hit / n


def read_sensors(x, y, yaw, segs, rng):
    vals = []
    for sx, sy in lc.sensor_world(x, y, yaw):
        v = coverage(sx, sy, segs) * 1000 + rng.gauss(0, NOISE)
        vals.append(max(0, min(1000, v)))
    return vals


def simulate(plan, start_pose, segs, dt=0.005, t_max=40.0, seed=1, ctrl_kw=None):
    rng = random.Random(seed)
    ctrl = lc.Controller(plan, **(ctrl_kw or {}))
    x, y, yaw = start_pose
    wl = wr = 0.0                       # kecepatan sudut roda sebenarnya (rad/s)
    el = er = 0.0                       # encoder (rad)
    t = 0.0
    traj = []
    while t < t_max and ctrl.state != "done":
        vals = read_sensors(x, y, yaw, segs, rng)
        tl, tr = ctrl.step(t, dt, vals, el, er)
        a = dt / (MOTOR_TAU + dt)       # motor orde satu
        wl += a * (tl - wl)
        wr += a * (tr - wr)
        vl, vr = wl * lc.WHEEL_R, wr * lc.WHEEL_R
        v, w = (vl + vr) / 2, (vr - vl) / lc.TRACK
        x += v * math.cos(yaw) * dt
        y += v * math.sin(yaw) * dt
        yaw += w * dt
        el += wl * dt
        er += wr * dt
        traj.append((t, x, y, yaw, ctrl.status, v))
        t += dt
    return ctrl, traj


def robot_outline():
    """Garis luar PCB utama (bentuk mobil F1, MAIN_R dari mechanical/cadquery/ltm_v16.py) + busur sensor, mm."""
    main_r = [(37, -34), (37, 20), (50, 23.5), (50, 54), (27, 65), (27, 84), (12, 93)]
    right = main_r
    left = [(-px, py) for px, py in reversed(main_r)]
    body = [(0, -34)] + right + [(0, 95)] + left
    arc = list(zip(lc.SENSOR_X_MM, lc.SENSOR_Y_MM))
    sensor_band = [(px, py + 4) for px, py in arc] + [(px, py - 6) for px, py in reversed(arc)]
    return body, sensor_band


def to_world(pts_mm, x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    out = []
    for px, py in pts_mm:
        fx, fy = py / 1000, px / 1000          # maju, kanan
        out.append((x + fx * c + fy * s, y + fx * s - fy * c))
    return out


def draw_arena(ax, segs, cols, rows, start, goal, blocked=()):
    import matplotlib.patches as mp
    ax.add_patch(mp.Rectangle((-0.2, -0.2), (cols - 1) * lc.GRID_STEP + 0.4, (rows - 1) * lc.GRID_STEP + 0.4,
                              color="white", zorder=0))
    for cx, cy, w, h in segs:
        ax.add_patch(mp.Rectangle((cx - w / 2, cy - h / 2), w, h, color="black", zorder=1))
    for lbl, (i, j), col in (("S", start, "#2e7d32"), ("T", goal, "#c62828")):
        ax.text(i * lc.GRID_STEP - 0.05, j * lc.GRID_STEP - 0.05, lbl, color=col, fontsize=16, weight="bold",
                ha="center", va="center", zorder=5)
    for i, j in blocked:
        ax.add_patch(mp.Rectangle((i * lc.GRID_STEP - 0.02, j * lc.GRID_STEP - 0.02), 0.04, 0.04, color="#f9a825",
                                  zorder=4))
    ax.set_xlim(-0.2, (cols - 1) * lc.GRID_STEP + 0.2)
    ax.set_ylim(-0.2, (rows - 1) * lc.GRID_STEP + 0.2)
    ax.set_aspect("equal")
    ax.set_facecolor("#dddddd")


def draw_robot(ax, x, y, yaw, alpha=1.0):
    import matplotlib.patches as mp
    body, band = robot_outline()
    ax.add_patch(mp.Polygon(to_world(body, x, y, yaw), closed=True, fc="#1565c0", ec="#0d47a1", alpha=0.55 * alpha,
                            zorder=3))
    ax.add_patch(mp.Polygon(to_world(band, x, y, yaw), closed=True, fc="#2e7d32", alpha=0.7 * alpha, zorder=3))
    for wx in (-45.5, 45.5):
        wheel = [(wx - 6, -17), (wx + 6, -17), (wx + 6, 17), (wx - 6, 17)]
        ax.add_patch(mp.Polygon(to_world(wheel, x, y, yaw), closed=True, fc="#212121", alpha=alpha, zorder=3))
    for sx, sy in lc.sensor_world(x, y, yaw):
        ax.plot(sx, sy, ".", color="#ff5252", ms=3, alpha=alpha, zorder=4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=["slide", "bfs"], default="slide")
    ap.add_argument("--start", default="0,0")
    ap.add_argument("--goal", default="3,3")
    ap.add_argument("--blocked", nargs="*", default=[])
    ap.add_argument("--speed", type=float, default=0.40)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil",
                                                  "uji2d_lintasan.png"))
    ap.add_argument("--video", default="")
    args = ap.parse_args()

    cols = rows = 4
    start = tuple(int(v) for v in args.start.split(","))
    goal = tuple(int(v) for v in args.goal.split(","))
    blocked = [tuple(int(v) for v in b.split(",")) for b in args.blocked]
    plan, start, heading, route = lc.make_scenario(args.scenario, start, goal, blocked, args.speed, cols, rows)
    if route:
        print("rute:", route)
    for k, st in enumerate(plan):
        print("indeks %d: jika %s lakukan %s" % (k + 1, lc.TRIGGER_TEXT[st["trigger"]], lc.ACTION_TEXT[st["action"]]))

    segs = lc.grid_segments(cols, rows)
    ctrl, traj = simulate(plan, lc.start_pose(start, heading), segs, ctrl_kw={"speed": args.speed})
    t_end, xe, ye, yawe = traj[-1][:4]
    gx, gy = goal[0] * lc.GRID_STEP, goal[1] * lc.GRID_STEP
    err = math.hypot(xe - gx, ye - gy)
    vmax = max(r[5] for r in traj)
    print("status akhir:", ctrl.status)
    print("waktu %.2f s, posisi akhir (%.3f, %.3f), selisih ke T %.1f mm, v maks %.2f m/s" %
          (t_end, xe, ye, err * 1000, vmax))
    for t, txt in ctrl.log:
        print("  %6.2f s  %s" % (t, txt))
    ok = ctrl.status.startswith("Selesai") and err < 0.03

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 7))
    draw_arena(ax, segs, cols, rows, start, goal, blocked)
    ax.plot([r[1] for r in traj], [r[2] for r in traj], "-", color="#ff9800", lw=2, zorder=2, label="lintasan poros")
    for k in range(0, len(traj), max(1, len(traj) // 12)):
        draw_robot(ax, *traj[k][1:4], alpha=0.35)
    draw_robot(ax, xe, ye, yawe)
    ax.set_title("Uji 2D: %s, %.1f s, %s" % ("rute slide 8" if args.scenario == "slide" else "rute terpendek",
                                              t_end, "LULUS" if ok else "GAGAL"))
    ax.legend(loc="upper left")
    fig.savefig(args.out, dpi=110, bbox_inches="tight")
    print("gambar:", args.out)

    if args.video:
        import imageio.v2 as imageio
        os.makedirs(os.path.dirname(os.path.abspath(args.video)), exist_ok=True)
        fps = 30
        stepk = max(1, int(round(1 / fps / 0.005)))
        w = imageio.get_writer(args.video, fps=fps, codec="libx264", quality=8, macro_block_size=8)
        for k in range(0, len(traj), stepk):
            fig, ax = plt.subplots(figsize=(7.2, 7.2), dpi=100)
            draw_arena(ax, segs, cols, rows, start, goal, blocked)
            ax.plot([r[1] for r in traj[:k + 1]], [r[2] for r in traj[:k + 1]], "-", color="#ff9800", lw=2, zorder=2)
            draw_robot(ax, *traj[k][1:4])
            ax.set_title("%s   t = %.2f s" % (traj[k][4], traj[k][0]), fontsize=11)
            ax.set_xticks([])
            ax.set_yticks([])
            fig.canvas.draw()
            w.append_data(__import__("numpy").asarray(fig.canvas.buffer_rgba())[..., :3])
            plt.close(fig)
        w.close()
        print("video:", args.video)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
