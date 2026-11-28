# Uji firmware LFM X1 di robot

Firmware M0–M5 + path planning + menu OLED ditulis 28/11/2026 **sebelum barang ada**, jadi semua di bawah ini
belum pernah jalan di robot. Sudah dicek: build tanpa warning di Arduino-ESP32 core 2.0.17 dan 4.0.0. Belum dicek:
semua perilaku di hardware. Tes **berurutan**: bagian berikutnya bergantung pada yang sebelumnya benar.

## 0. Upload dan serial

```
cd firmware
pio run -t upload          # pertama kali mengunduh toolchain (±5 menit)
pio device monitor         # 115200 baud, ketik perintah lalu Enter
```

Tanpa VS Code: `pip install platformio`, lalu perintah yang sama dipanggil sebagai `python -m platformio ...`.
Ketik `help` untuk daftar perintah. Untuk tes pertama **angkat robot** (roda tidak menyentuh lantai).

## 1. Dasar (M0)

| Perintah / cek | Harus terjadi | Kalau tidak |
|---|---|---|
| nyalakan | buzzer bunyi pendek, OLED menampilkan layar utama LFM X1 | OLED gelap: cek SDA 21 / SCL 22, alamat 0x3C |
| `info` | versi firmware, core, kalibrasi BELUM, tegangan baterai | |
| `beep 500` | buzzer bunyi 0,5 s | cek Q1 S8050, GPIO12 |

## 2. Motor (M1) — roda diangkat

| Perintah | Harus terjadi | Kalau tidak |
|---|---|---|
| `m 100 100` | kedua roda berputar **maju** 1,5 s | roda mundur: balik `MOTOR_L_INVERT` / `MOTOR_R_INVERT` di `RobotConfig.h` |
| `m 100 -100` | robot akan **putar kanan** (kiri maju, kanan mundur) | kiri-kanan tertukar: cek kabel J2/J3 |
| `m 255 255` | lebih cepat; dengan baterai penuh tetap setara 6 V (kompensasi) | |
| `stop` | rem | |

## 3. Sensor (M2–M3)

| Perintah | Harus terjadi | Kalau tidak |
|---|---|---|
| `raw` | 12 angka; di atas putih kecil, di atas hitam besar | semua sama / acak: cek kabel JST XH 8, mux, `MUX_S0..S3` |
| geser garis dari kiri ke kanan | angka naik berurutan S1 → S12 | terbalik: `SENSOR_REVERSED = true` |
| satu sensor ditutup, tetangganya ikut naik | — | bocor antar kanal: naikkan `MUX_SETTLE_US` (4 → 10) |
| `cal` lalu geser robot melintasi garis 3 s | "Kalibrasi berhasil" + tabel min/max | GAGAL S…: sensor itu tidak pernah melihat garis + lantai, ulangi |
| `cal 3000 putar` | robot berayun kiri-kanan sendiri, lalu berhasil | ayunan terlalu kecil/besar: ubah `CAL_SWING_MS` |
| `pos` | nilai 0–1000 per sensor, `pos` ≈ 0 saat garis di tengah, + saat garis di kanan robot | tanda terbalik = urutan sensor terbalik (lihat di atas) |
| letakkan di persimpangan | `<KIRI` / `KANAN>` muncul | |

## 4. Ikut garis (M4)

`jalan` = ikuti garis sampai `stop` (atau berhenti sendiri kalau garis hilang 1 s). Nilai awal dari simulasi:
`kp 0.07`, `kd 3.5`, `spd 120`. Tuning:

1. `spd 80`, `kd 0`, naikkan `kp` sampai robot mengikuti garis tapi berayun.
2. Naikkan `kd` sampai ayunan hilang (biasanya 20–60 × kp).
3. Naikkan `spd` sedikit demi sedikit, ulangi 1–2 kalau mulai lepas di tikungan.
4. `simpan` (tersimpan ke NVS, sama dengan menu Atur PID).

## 5. Encoder, tombol, baterai (M5)

| Perintah | Harus terjadi | Kalau tidak |
|---|---|---|
| `enc` lalu `m 100 100` | kedua angka **naik** | turun: balik `ENC_L_INVERT` / `ENC_R_INVERT`; diam: cek kabel encoder (A/B ke GPIO 13/14 dan 23/19) |
| `enc 0`, dorong robot lurus 500 mm dengan tangan | jarak ≈ 500 mm | ukur hitungan per putaran roda → `ENCODER_PPR` (PPR belum diketahui, perkiraan 7) atau `WHEEL_DIAMETER_MM` |
| `enc 0`, putar robot 90° dengan tangan di tempat | sudut ≈ +90 (ke kiri) | ubah `WHEEL_TRACK_MM` |
| `btn`, tekan tombol satu per satu | nama tombol benar | lihat mV yang tercetak, sesuaikan `BTN_EDGE_*_MV` |
| `bat` | sama dengan multimeter ± 0,1 V | `VBAT_TRIM` = V multimeter / V terbaca |

## 6. Gerak terukur dan path planning

Robot di lantai. Tombol apa pun membatalkan.

| Perintah | Harus terjadi |
|---|---|
| `maju 300` | maju lurus 30 cm lalu berhenti |
| `putar 90` | putar kiri 90° di tempat |
| robot di garis lurus, `belok kiri` | putar kiri sampai menemukan garis lain (minimal 60°) |
| `indeks simpang berhenti` | ikut garis sampai persimpangan, berhenti dengan poros roda di tengah persimpangan |
| `indeks simpang kiri` | belok kiri di persimpangan, ikuti garis 80 mm, berhenti |
| `rute` / `rute 1` | daftar rute / jalankan rute 1 (log tiap indeks di serial) |

Titik belok terlalu awal/terlambat: ubah `APPROACH_OFFSET_MM` (+ = lebih jauh). Belok kebablasan: turunkan `TURN_PWM`.

## 7. Menu OLED (pemakaian tanpa laptop)

Tombol kiri → kanan: **KEMBALI, ATAS, OK, BAWAH, LANJUT**.

- Layar utama: OK = mulai rute terpilih (hitung mundur 3 s), ATAS/BAWAH = ganti rute, LANJUT = menu.
- Menu: Mulai, Pilih rute, Kalibrasi (OK = robot berayun, LANJUT = geser dengan tangan), Lihat sensor, Atur PID
  (Kp, Kd, kecepatan; disimpan otomatis), Warna garis, Tes motor, Info robot.
- Saat robot berjalan layar tidak diperbarui (supaya PID tetap 1 kHz); tombol apa pun = STOP. Sesudah selesai
  tampil waktu tempuh dan indeks yang tercapai.

Rute ada di `firmware/src/Routes.cpp` (satu baris = satu indeks). Rute arena IARC dibuat setelah ukuran arena asli
diketahui.

## Konstanta yang harus diukur (`firmware/lib/LineFollower/src/RobotConfig.h`)

| Konstanta | Nilai sekarang | Cara ukur |
|---|---|---|
| `MOTOR_L/R_INVERT`, `ENC_L/R_INVERT`, `SENSOR_REVERSED` | perkiraan | bagian 2, 3, 5 |
| `ENCODER_PPR` | 7 (asumsi) | bagian 5 / tanya penjual |
| `WHEEL_DIAMETER_MM` | 34 | bagian 5 (ban TPU terpasang) |
| `WHEEL_TRACK_MM` | 97 | bagian 5 |
| `VBAT_TRIM` | 1,0 | bagian 5 |
| `CAL_SWING_MS` | 150 | bagian 3 |
| `APPROACH_OFFSET_MM`, `TURN_PWM`, `APPROACH_PWM` | 0 / 90 / 90 | bagian 6 |
