"""Logika kendali Line Follower Micro untuk simulasi.

Dipakai bersama oleh uji 2D (`test_2d.py`) dan CoppeliaSim (`coppeliasim/run_sim.py`), jadi logika yang dites di
sini sama dengan yang menggerakkan robot di CoppeliaSim. Isinya:
- geometri robot (model v16 + PCB sensor rev B),
- posisi garis dari 12 sensor (rata-rata berbobot, nilai 0-1000 seperti firmware),
- PID ikut garis,
- deteksi persimpangan dari sensor lengan kiri/kanan,
- path planning per indeks gaya Ichiduino (pemicu -> aksi -> ikuti garis), aksi diukur encoder, bukan waktu,
- rute terpendek di grid (Dijkstra/BFS, sama panjang -> belok paling sedikit) yang menghasilkan daftar indeks.

Satuan SI (m, s, rad), kecuali posisi garis dalam mm.
Koordinat robot: x kanan, y maju, z atas; nol = lantai di bawah tengah poros roda (sama dengan mechanical/ dan KiCad).
"""
import heapq
import math

# ------------------------------------------------------------------ geometri robot
WHEEL_R = 0.017                     # roda O34
TRACK = 0.091                       # jarak tengah ban kiri-kanan
MOTOR_RPM = 500                     # N20 6 V 500 RPM
W_MAX = MOTOR_RPM * 2 * math.pi / 60    # 52,4 rad/s -> 0,89 m/s di roda O34
# 12 QRE1113GR, urut kiri ke kanan (S1..S12), dari hardware/sensor-garis/sensor-garis.kicad_pcb (rev B)
SENSOR_X_MM = [-41.39, -35.26, -28.01, -20.19, -12.22, -4.25, 4.25, 12.22, 20.19, 28.01, 35.26, 41.39]
SENSOR_Y_MM = [114.72, 119.86, 123.24, 124.91, 125.60, 126.30, 126.30, 125.60, 124.91, 123.24, 119.86, 114.72]
SENSOR_H = 0.0033                   # muka sensor dari lantai
SKID_POS = [(-0.00475, 0.08555), (0.00475, 0.08555)]   # skid nilon di baut H1/H2 PCB sensor
N_SENS = 12

# ------------------------------------------------------------------ arena
LINE_W = 0.02                       # garis hitam 2 cm (IARC XII)
GRID_STEP = 0.30                    # jarak antar simpul grid (perkiraan; samakan dengan arena lomba bila sudah ada)

ACTION_TEXT = {"forward": "maju", "left": "belok kiri", "right": "belok kanan", "uturn": "putar balik",
               "stop": "berhenti"}
TRIGGER_TEXT = {"junction": "persimpangan", "left": "cabang kiri", "right": "cabang kanan", "direct": "langsung"}


def line_position(vals, last_side):
    """Posisi garis (mm, + = garis di kanan robot) dari 12 nilai 0-1000 (1000 = di atas garis).

    Rata-rata berbobot koordinat x sensor. Garis hilang -> nilai ujung sesuai sisi terakhir (aturan firmware).
    """
    num = den = 0.0
    for v, x in zip(vals, SENSOR_X_MM):
        if v > 150:                  # buang derau lantai
            num += v * x
            den += v
    if den < 300:
        return (45.0 if last_side >= 0 else -45.0), False
    return num / den, True


class Controller:
    """Path planning per indeks + PID ikut garis. Satu panggilan step() = satu siklus kendali.

    plan: daftar langkah (indeks 1, 2, ...), tiap langkah dict:
        trigger: "junction" (cabang kiri atau kanan), "left", "right", atau "direct" (langsung, tanpa sensor)
        action:  "forward", "left", "right", "uturn", atau "stop"
        speed:   kecepatan ikuti garis sesudah aksi (m/s)
        follow:  jarak ikuti garis sesudah aksi sebelum pemicu berikutnya dicek (m); pengganti "while ms" di blok
                 Ichiduino, diukur encoder
    step() mengembalikan kecepatan sudut target roda kiri dan kanan (rad/s).
    """

    CROSS_DIST = 0.05       # dari cabang pertama terlihat sampai sensor lewat garis melintang (m)
    CHECK_DIST = 0.03       # jendela pengumpulan cabang kiri/kanan (m)

    def __init__(self, plan, speed=0.40, kp=0.0060, kd=0.00030, line_black=True, turn_speed=0.16,
                 approach_speed=0.25):
        self.plan = plan
        self.follow_speed = speed
        self.kp, self.kd = kp, kd
        self.line_black = line_black
        self.turn_speed = turn_speed
        self.approach_speed = approach_speed
        self.idx = 0                    # langkah aktif = indeks idx + 1
        self.state = "follow"
        self.last_side = 0.0
        self.prev_err = 0.0
        self.enc_start = None
        self.enc0 = None                # encoder (kiri, kanan) saat cabang pertama terlihat / belok dimulai
        self.dist = 0.0                 # jarak tempuh total dari encoder (m)
        self.ignore_until = 0.03        # pemicu baru dicek sesudah jarak tempuh ini
        self.branch = {"left": False, "right": False}
        self.to_center = 0.0            # jarak poros -> tengah persimpangan saat cabang pertama terlihat
        self.t = 0.0
        self.log = []                   # (waktu, teks status) tiap kali status berganti
        self._set_status()

    # ---------------------------------------------------------- bantu
    def current(self):
        return self.plan[self.idx] if self.idx < len(self.plan) else None

    def _set_status(self, text=None):
        st = self.current()
        if text is None:
            text = "Selesai" if st is None else "Indeks %d: jika %s lakukan %s" % (
                self.idx + 1, TRIGGER_TEXT[st["trigger"]], ACTION_TEXT[st["action"]])
        self.status = text
        self.log.append((self.t, text))

    def _since(self, el, er):
        """(jarak rata-rata, sudut putar) sejak enc0, dari encoder."""
        dl = (el - self.enc0[0]) * WHEEL_R
        dr = (er - self.enc0[1]) * WHEEL_R
        return (dl + dr) / 2, (dr - dl) / TRACK

    @staticmethod
    def _wheels(v_left, v_right):
        lim = W_MAX * WHEEL_R
        return max(-lim, min(lim, v_left)) / WHEEL_R, max(-lim, min(lim, v_right)) / WHEEL_R

    @staticmethod
    def _branches(vals):
        """Cabang kiri/kanan = sensor lengan (|x| >= 28 mm) melihat garis. Di garis lurus garis 2 cm tidak sampai ke
        sensor ini kecuali robot melenceng > +-16 mm."""
        return max(vals[0:3]) > 500, max(vals[9:12]) > 500

    def _straight(self):
        return self._wheels(self.approach_speed, self.approach_speed)

    def _next_index(self):
        st = self.current()
        self.follow_speed = st.get("speed", self.follow_speed)
        self.ignore_until = self.dist + st.get("follow", 0.08)
        self.idx += 1
        self.prev_err = 0.0
        self.state = "follow" if self.current() is not None else "done"
        self._set_status()

    # ---------------------------------------------------------- satu siklus
    def step(self, t, dt, raw_vals, enc_left, enc_right):
        self.t = t
        vals = raw_vals if self.line_black else [1000 - v for v in raw_vals]
        if self.enc_start is None:
            self.enc_start = (enc_left, enc_right)
        self.dist = ((enc_left - self.enc_start[0]) + (enc_right - self.enc_start[1])) / 2 * WHEEL_R
        st = self.current()

        if self.state == "done":
            return 0.0, 0.0

        if self.state == "follow":
            if self.dist < self.ignore_until:
                return self._pid(dt, vals)
            if st["trigger"] == "direct":
                self.enc0 = (enc_left, enc_right)
                self.to_center = 0.0
                return self._begin_action()
            left, right = self._branches(vals)
            if left or right:
                # tengah persimpangan ada di depan poros sejauh y sensor lengan yang melihat + setengah lebar garis
                ys = [SENSOR_Y_MM[i] for i in ((0, 1, 2) if left else (9, 10, 11))]
                self.to_center = max(ys) / 1000 + LINE_W / 2
                self.branch = {"left": left, "right": right}
                self.enc0 = (enc_left, enc_right)
                self.state = "check"
                return self._straight()
            return self._pid(dt, vals)

        d, ang = self._since(enc_left, enc_right)

        if self.state == "check":
            # maju lurus (tanpa PID: garis melintang mengacaukan posisi) sambil mengumpulkan cabang
            left, right = self._branches(vals)
            self.branch["left"] |= left
            self.branch["right"] |= right
            if d < self.CHECK_DIST:
                return self._straight()
            trig = st["trigger"]
            if (trig == "junction" or (trig == "left" and self.branch["left"]) or
                    (trig == "right" and self.branch["right"])):
                return self._begin_action()
            self.state = "skip"             # persimpangan ini bukan pemicu indeks aktif: lewati
            return self._straight()

        if self.state in ("skip", "cross"):
            # lewati garis melintang lurus, lalu ikuti garis lagi
            if d < self.CROSS_DIST:
                return self._straight()
            if self.state == "cross":
                self._next_index()
            else:
                self.state = "follow"
                self.ignore_until = self.dist + 0.03
            return self._pid(dt, vals)

        if self.state == "approach":
            # maju sampai poros roda tepat di tengah persimpangan (encoder)
            if d < self.to_center:
                return self._straight()
            if st["action"] == "stop":
                self.idx = len(self.plan)
                self.state = "done"
                self._set_status("Selesai: berhenti di tujuan")
                return 0.0, 0.0
            self.enc0 = (enc_left, enc_right)
            self.state = "turn"
            return 0.0, 0.0

        if self.state == "turn":
            # putar di tempat sampai encoder +-60 deg (putar balik 150 deg), lalu kunci ke garis oleh sensor tengah
            need = math.radians(150 if st["action"] == "uturn" else 60)
            if abs(ang) >= need and max(vals[5], vals[6]) > 500:
                self._next_index()
                return 0.0, 0.0
            if abs(ang) > math.radians(200):
                self.state = "done"
                self._set_status("Gagal: garis tidak ketemu saat belok")
                return 0.0, 0.0
            sgn = -1 if st["action"] == "right" else 1     # kiri dan putar balik: berlawanan jarum jam
            return self._wheels(-sgn * self.turn_speed, sgn * self.turn_speed)

        return 0.0, 0.0

    def _begin_action(self):
        act = self.current()["action"]
        if act == "forward":
            self.state = "cross"
        else:
            self.state = "approach"
        return self._straight() if self.to_center > 0 else (0.0, 0.0)

    def _pid(self, dt, vals):
        pos, seen = line_position(vals, self.last_side)
        if seen:
            self.last_side = pos
        derr = (pos - self.prev_err) / dt
        self.prev_err = pos
        u = self.kp * pos + self.kd * derr
        v = self.follow_speed
        return self._wheels(v + u, v - u)


# ------------------------------------------------------------------ rute terpendek di grid -> daftar indeks
DIRS = {(1, 0): "timur", (0, 1): "utara", (-1, 0): "barat", (0, -1): "selatan"}


def shortest_route(cols, rows, start, goal, blocked=()):
    """Rute terpendek dari simpul start ke goal di grid cols x rows (simpul (i, j), i ke timur, j ke utara).

    Biaya = jumlah ruas + 0,001 per belok, jadi dari semua rute terpendek dipilih yang beloknya paling sedikit.
    blocked: simpul yang tidak boleh dilewati (mis. kubus misi). Hasil: daftar simpul dari start sampai goal.
    Robot diletakkan di start menghadap ruas pertama rute (lihat start_heading()).
    """
    blocked = set(map(tuple, blocked))
    pq = [(0.0, start, None, [start])]
    best = {}
    while pq:
        cost, node, hd, path = heapq.heappop(pq)
        if node == goal:
            return path
        if best.get((node, hd), 1e9) <= cost:
            continue
        best[(node, hd)] = cost
        for d in DIRS:
            if hd is not None and d == (-hd[0], -hd[1]):
                continue
            nxt = (node[0] + d[0], node[1] + d[1])
            if not (0 <= nxt[0] < cols and 0 <= nxt[1] < rows) or nxt in blocked:
                continue
            heapq.heappush(pq, (cost + 1 + (0.001 if hd is not None and d != hd else 0), nxt, d, path + [nxt]))
    raise ValueError("tidak ada rute dari %s ke %s" % (start, goal))


def start_heading(route):
    """Arah ruas pertama rute, (di, dj)."""
    return (route[1][0] - route[0][0], route[1][1] - route[0][1])


def plan_from_route(route, speed=0.40, follow=0.08):
    """Ubah rute (daftar simpul) jadi daftar indeks: tiap simpul sesudah start = satu indeks dengan pemicu
    persimpangan; aksinya maju/kiri/kanan dari arah datang ke arah pergi; simpul terakhir = berhenti."""
    plan = []
    hd = start_heading(route)
    for k in range(1, len(route)):
        cur = route[k]
        if k == len(route) - 1:
            plan.append({"trigger": "junction", "action": "stop", "speed": speed, "follow": follow})
            break
        nxt = route[k + 1]
        out = (nxt[0] - cur[0], nxt[1] - cur[1])
        cross = hd[0] * out[1] - hd[1] * out[0]
        if out == hd:
            act = "forward"
        elif cross > 0:
            act = "left"
        elif cross < 0:
            act = "right"
        else:
            act = "uturn"
        plan.append({"trigger": "junction", "action": act, "speed": speed, "follow": follow})
        hd = out
    return plan


# rute contoh slide 8 deck pitching: S (0,0) -> T (3,3), indeks 1 kiri, 2 kanan, 3 kiri, 4 kanan, 5 kiri, 6 berhenti
SLIDE_PLAN = [
    {"trigger": "left", "action": "left", "speed": 0.40, "follow": 0.08},
    {"trigger": "junction", "action": "right", "speed": 0.40, "follow": 0.08},
    {"trigger": "junction", "action": "left", "speed": 0.40, "follow": 0.08},
    {"trigger": "junction", "action": "right", "speed": 0.40, "follow": 0.08},
    {"trigger": "junction", "action": "left", "speed": 0.40, "follow": 0.08},
    {"trigger": "junction", "action": "stop", "speed": 0.40, "follow": 0.08},
]


def make_scenario(name, start=(0, 0), goal=(3, 3), blocked=(), speed=0.40, cols=4, rows=4):
    """Skenario uji: (plan, simpul start, arah awal (di, dj), rute atau None).

    "slide": rencana indeks manual seperti slide 8 deck (robot di S menghadap timur).
    "bfs":   rute terpendek otomatis dari start ke goal, simpul blocked dihindari.
    """
    if name == "slide":
        return [dict(st, speed=speed) for st in SLIDE_PLAN], (0, 0), (1, 0), None
    route = shortest_route(cols, rows, tuple(start), tuple(goal), blocked)
    return plan_from_route(route, speed=speed), route[0], start_heading(route), route


def start_pose(node, heading, back=-0.02):
    """Pose awal (x, y, yaw): poros 2 cm di depan simpul start, menghadap ruas pertama."""
    return (node[0] * GRID_STEP - back * heading[0], node[1] * GRID_STEP - back * heading[1],
            math.atan2(heading[1], heading[0]))


def grid_segments(cols=4, rows=4, step=GRID_STEP, w=LINE_W):
    """Garis hitam arena grid sebagai persegi panjang (cx, cy, panjang_x, panjang_y), koordinat dunia (m)."""
    segs = []
    for j in range(rows):
        segs.append(((cols - 1) * step / 2, j * step, (cols - 1) * step + w, w))
    for i in range(cols):
        segs.append((i * step, (rows - 1) * step / 2, w, (rows - 1) * step + w))
    return segs


def sensor_world(x, y, yaw):
    """Posisi dunia 12 sensor untuk pose robot (x, y = titik tengah poros di lantai, yaw = arah maju, rad)."""
    c, s = math.cos(yaw), math.sin(yaw)
    out = []
    for sx, sy in zip(SENSOR_X_MM, SENSOR_Y_MM):
        # sumbu robot: y maju = (cos yaw, sin yaw), x kanan = (sin yaw, -cos yaw)
        fx, fy = sy / 1000, sx / 1000
        out.append((x + fx * c + fy * s, y + fx * s - fy * c))
    return out
