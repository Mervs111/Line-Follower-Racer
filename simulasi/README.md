# Simulasi robot Line Follower Micro (26/10/2026)

Simulasi 3D untuk pitching (permintaan dosen: simulasi seperti CoppeliaSim). Robot ukuran asli berjalan di arena grid
dengan **PID ikut garis + path planning per indeks** (gaya Ichiduino, aksi diukur encoder). Logikanya satu modul
Python (`lfm_control.py`) yang dipakai oleh uji 2D dan CoppeliaSim, jadi yang dites di 2D sama dengan yang jalan di
CoppeliaSim. Nanti logika yang sama dipindah ke firmware (`LineFollower.follow()`, path planning).

| File | Isi |
|---|---|
| `lfm_control.py` | geometri robot, posisi garis, PID, deteksi persimpangan, path planning per indeks, rute terpendek grid |
| `test_2d.py` | uji 2D tanpa CoppeliaSim (kinematika + model sensor): gambar lintasan, opsional video tampak atas |
| `coppeliasim/build_scene.py` | membangun scene CoppeliaSim lewat ZMQ remote API, simpan `lfm_grid.ttt` |
| `coppeliasim/run_sim.py` | menjalankan skenario di CoppeliaSim (mode stepping), video MP4 + log JSON |
| `coppeliasim/make_mesh.py` + `mesh/` | tampilan robot dari rakitan PCB (`mechanical/rakitan-pcb/LFM_rakitan.glb`), OBJ per warna |
| `hasil/` | gambar/video hasil uji |

## Model

| Bagian | Nilai | Sumber |
|---|---|---|
| Roda | Ø34 mm, jarak tengah ban 91 mm | model v16, RAB |
| Motor | N20 500 RPM (maks 52 rad/s = 0,89 m/s), velocity control, torsi maks 0,04 N·m (perkiraan) | RAB, charter |
| Massa | ±0,22 kg (badan 0,19 + roda 2 × 0,01 + skid) | perkiraan dari komponen |
| Sensor | 12 titik baca di posisi QRE1113GR PCB rev B (busur, 8 mm), 3,3 mm dari lantai, daerah baca 4 mm | `hardware/sensor-garis/` |
| Penahan depan | 1 bola bebas di posisi skid nilon (y 85,6 mm) | model v16 |
| Arena | grid 4 × 4 simpul, jarak 30 cm (perkiraan, samakan dengan arena lomba), garis hitam 2 cm | IARC XII |
| Kendali | 200 Hz (dt 5 ms), kecepatan 0,4 m/s, Kp 0,006 (m/s)/mm, Kd 0,0003 | disetel di uji 2D |

Di CoppeliaSim tiap sensor = vision sensor ortografik 4 × 4 piksel yang hanya merender arena; nilainya
dinormalisasi 0–1000 dari kalibrasi saat start (sensor tengah di garis, lengan di putih), sama dengan aturan firmware.

## Logika path planning (sama dengan blok yang direncanakan)

Rute = daftar indeks. Tiap indeks: **pemicu** (persimpangan / cabang kiri / cabang kanan / langsung) → **aksi**
(maju, belok kiri, belok kanan, putar balik, berhenti) → **ikuti garis** dengan kecepatan tertentu sejauh sekian cm
(pengganti "while ms" di blok Ichiduino, diukur encoder) → indeks berikutnya.

- Cabang terdeteksi oleh sensor lengan (|x| ≥ 28 mm, tiga di tiap sisi); robot lalu maju lurus 3 cm tanpa PID
  sambil mencatat cabang kiri/kanan.
- Belok: maju sampai poros roda di tengah persimpangan (jarak dari encoder), putar di tempat sampai encoder 60°,
  lalu dikunci ke garis oleh sensor tengah (arahan dosen 09/10: tanpa IMU).
- Rute terpendek di grid: Dijkstra/BFS; dari rute yang sama panjang dipilih yang beloknya paling sedikit, lalu
  diubah otomatis jadi daftar indeks. Simpul terhalang (mis. kubus misi) bisa diberikan.

## Uji 2D (sudah jalan, 26/10)

Semua perintah dijalankan dari folder `simulasi/`.

```
py -m pip install -r requirements.txt
py test_2d.py                                   # rute slide 8: S -> T, indeks 1 kiri ... 6 berhenti
py test_2d.py --scenario bfs --blocked 1,0 2,2 1,2
py test_2d.py --video hasil/uji2d_slide.mp4
```

Hasil 26/10: rute slide 8 selesai 8,2 s, berhenti 9 mm dari T. Rute terpendek (dengan dan tanpa simpul terhalang)
lulus. Kecepatan 0,3 / 0,4 / 0,5 / 0,6 / 0,7 m/s × 5 seed derau: 25/25 lulus. Gambar: `hasil/uji2d_*.png`, video
tampak atas: `hasil/uji2d_slide.mp4`.

## CoppeliaSim

1. Pasang **CoppeliaSim Edu** (gratis untuk pendidikan, coppeliarobotics.com, versi terbaru; minimal 4.6 disarankan).
2. `py -m pip install -r requirements.txt`
3. Buka CoppeliaSim, **File > New scene** (ZMQ remote API server menyala otomatis).
4. `py coppeliasim/build_scene.py` → scene `coppeliasim/lfm_grid.ttt` (boleh dijalankan ulang; objek `LFM_*` lama
   dihapus dulu). `--no-mesh` kalau robot cukup tampil sebagai kotak.
5. `py coppeliasim/run_sim.py` → robot jalan di jendela CoppeliaSim, video `hasil/coppeliasim_slide.mp4`
   (tampak arena + kamera pengikut di pojok, teks indeks aktif), log `hasil/coppeliasim_slide.json`.
   - `--scenario bfs --blocked 1,0 2,2 1,2`: rute terpendek + kubus 4 cm di simpul terhalang.
   - `--no-record`: tanpa video (lebih cepat). `--speed 0.5 --kp ... --kd ...`: setelan lain.
   - `--kinematic`: cadangan kalau fisika roda bermasalah (pose dihitung dari kecepatan roda, sensor tetap
     vision sensor).

### Hasil di CoppeliaSim asli (26/10 malam, laptop user)

CoppeliaSim Edu 4.10, mesin fisika Bullet 2.78 (bawaan), dt 5 ms, Python 3.14. Kedua skrip jalan tanpa perubahan
logika; fisika roda (bukan `--kinematic`) langsung benar arah dan torsinya. Kalibrasi sensor: putih 1,000,
hitam 0,110 (kontras cukup).

| Skenario | Waktu simulasi | Selisih ke T | Hasil | Video |
|---|---|---|---|---|
| rute slide 8 (6 indeks: kiri, kanan, kiri, kanan, kiri, berhenti) | 8,30 s | 12,6 mm | LULUS | `hasil/coppeliasim_slide.mp4` |
| `--scenario bfs --blocked 1,0 2,2 1,2` (rute (0,0)→(0,3)→(3,3), 1 belok kanan) | 5,69 s | 11,2 mm | LULUS | `hasil/coppeliasim_bfs.mp4` |

Poros roda paling jauh 12 mm (slide) dan 9,5 mm (BFS) dari garis terdekat; simpangan terbesar sesaat sesudah belok,
lalu dikoreksi PID. Satu run butuh ±1 menit di laptop (±75 s dengan video). Hasil sedikit berbeda antar run
(±2 mm) karena urutan langkah fisika.

Yang diubah dari versi cloud, hanya tampilan (`build_scene.py`): kamera video `LFM_cam` dipindah supaya arena dan
robot di S maupun T utuh di gambar (dulu robot di S terpotong tepi bawah dan di T tertutup teks), kamera perekam
disembunyikan dari jendela CoppeliaSim (garis frustum biru), dan pandangan jendela (`DefaultCamera`) diarahkan ke
arena. Screenshot jendela saat simulasi jalan: `hasil/coppeliasim_jendela.png` (rute slide, t = 4,7 s) dan
`hasil/coppeliasim_jendela_bfs.png` (rute terpendek + 3 kubus, t = 3,8 s). `hasil/cek_kamera.png` = frame pertama
video (tegak, tidak tercermin).

Kalau nanti ada masalah (versi CoppeliaSim lain, setelan diubah), yang perlu dicek:

| Gejala | Yang dicek |
|---|---|
| `run_sim.py` berhenti "robot tidak maju" | robot mundur: balik tanda `Q_AXLE` di `build_scene.py`; robot diam: torsi `MOTOR_TORQUE`, gesekan roda, atau `--kinematic` |
| "kontras sensor kecil" | lampu scene (pakai New scene bawaan), `entity_to_render` sensor = `LFM_arena` |
| robot bergetar/melompat | dt 5 ms, mesin fisika (Bullet/Newton/MuJoCo di menu), massa roda/skid |
| `cek_kamera.png` terbalik/tercermin | `Sim.image()` di `run_sim.py` (flipud / fliplr) |
| API tidak ada (`createPrimitiveShape`, `getVisionSensorImg`, ...) | versi CoppeliaSim lama; skrip punya cadangan untuk sebagian, sisanya sesuaikan |
| belok kurang/lebih, keluar garis | `--kp`, `--kd`, `turn_speed`, `approach_speed` di `Controller` |
