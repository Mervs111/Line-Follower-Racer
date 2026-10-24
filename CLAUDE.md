# Line Follower ESP32 + Block Programming

## Tujuan
Robot line follower yang murah tapi performanya bagus, bisa diprogram pakai blok (Mind+ user extension, MicroBlocks opsional).
Arsitektur 3 lapis:
1. **Library C++ `LineFollower`**: logika aslinya, ditulis & dites duluan
2. **Desain blok**: 1 blok = 1 fungsi library
3. **Extension Mind+**: blok menghasilkan kode C++ yang memanggil library (compile native → PID tetap cepat)

Target lomba: **IARC XII Smart Robotics** (9–10/01/2027): arena grid, **garis hitam 2 cm**, misi dorong kubus 4 cm;
spesifikasi kit panitia (Nano, TCRT5000 5 ch) tidak wajib. Robot dibuat **serbaguna** (grid + lintasan banyak tikungan).

## Rancangan terkini (22/10/2026)

### Elektronik
- **MCU: ESP32 biasa (DevKit 30 pin, CH340/CP2102)**, bukan S3 (harga). Hanya ADC1; ADC2 tidak dipakai (bentrok WiFi).
- **Sensor: 12× QRE1113GR** (LED IR + fototransistor SMD; pin 1 A, 2 K, 3 C, 4 E) di sisi bawah PCB sensor.
  A ← R 220 Ω ← +5V (±17 mA), K → GND, C ← R 10k ← +3V3, C → label `S1`…`S12`, E → GND. LED IR **selalu nyala**
  (tanpa MOSFET/IR_EN): andalkan kalibrasi + pelindung cahaya.
- **Mux: IC CD74HC4067M SOIC-24W** (`Package_SO:SOIC-24W_7.5x15.4mm_P1.27mm`) disolder di PCB sensor: VCC +3V3 +
  C 100 nF, E̅ → GND, **S1–S12 = I2–I13**, I0/I1/I14/I15 tidak tersambung, COM → `MUX_SIG`, select → `MUX_S0`…`MUX_S3`.
  Cadangan IC: 74HC4067D (SO-24) Rp35.000 di marconijawa.
- **J1 PCB sensor = JST XH 8 pin** (B8B-XH-A): 1 +5V, 2 +3V3, 3 GND, 4 MUX_S3, 5 MUX_S2, 6 MUX_S1, 7 MUX_S0,
  8 MUX_SIG. Konektor pasangannya di PCB utama **wajib urutan sama**.
- Motor N20 6V 500 RPM + encoder, **roda Ø34**; driver TB6612FNG (modul).
- Daya: 2S (2× 18650, holder 76×42×20 mm), BMS 2S, charger 2S USB-C (di dinding belakang rangka, OUT ke P+/P− BMS),
  buck MP1584 5 V, pembagi baterai 100k/33k.
- UI: OLED 0,96" I2C (bacaan sensor tampil sebagai bar), 2 tombol, buzzer aktif + S8050. **Tanpa IMU** (arahan dosen
  09/10: belok 90° di persimpangan pakai selisih encoder lalu dikunci ke garis oleh sensor). **Tanpa MCP23017/LED
  indikator**. I2C hanya untuk OLED.

### Pin ESP32 (dari `docs/skematik-v1.md`, 13/10; `firmware/Pins.h` masih peta S3 lama → wajib diperbarui)
| Fungsi | GPIO | | Fungsi | GPIO |
|---|---|---|---|---|
| MUX_SIG (ADC1) | 36 | | TB6612 PWMA / AIN1 / AIN2 | 18 / 5 / 17 |
| VBAT_SENSE (ADC1) | 39 | | TB6612 PWMB / BIN1 / BIN2 | 16 / 4 / 15 |
| MUX_S0 / S1 / S2 / S3 | 26 / 25 / 33 / 32 | | TB6612 STBY (LOW saat boot) | 2 |
| BTN_A / BTN_B (+R 10k pull-up) | 34 / 35 | | ENC_L A / B | 13 / 14 |
| Buzzer (R4 pull-down, LOW saat boot) | 12 | | ENC_R A / B | 23 / 19 |
| I2C SDA / SCL | 21 / 22 | | IR_EN (tidak dipakai lagi) | 27 |

Semua pin taruh di `Pins.h` sebagai satu-satunya sumber kebenaran. Kedua jalur PCB (lihat Riwayat 08/10) wajib
memakai pin map yang sama.

### PCB
- **PCB sensor**: `hardware/sensor-garis/` (KiCad 10, buatan user; asli di `C:\ITS\LineFollowerRacer\PCB_LFM_FIX\` →
  sekarang salinannya di `LineFollowerRacer/` dalam repo, di-gitignore). **Rev B (disetujui)**: bentuk jangkar, lebar
  95 mm, 12 QRE jarak 8 mm di busur (tengah ±4,25, segmen 5/5/12/25/40°), DRC 0. Koordinat sensor untuk firmware
  dan riwayat revisi di `hardware/sensor-garis/REVISI.md`.
- **PCB utama baru**: `hardware/pcb-utama/` (KiCad 10, dibuat 22/10 oleh `hardware/tools/gen_pcb_utama_awal.py`;
  nama folder boleh diganti user). Isi awal: outline **"mobil F1"** 100 × 127 (pilihan user 22/10, `MAIN_R` di
  `ltm_v16.py`; perbandingan opsi https://claude.ai/artifact/PYASQTHgLPKjVaxw33yyMZ), lubang, gambar bantu penempatan
  (User.Drawings), outline PCB sensor (User.Comments). **Skematik sudah dibuat Claude 22/10** (atas permintaan user,
  `hardware/tools/gen_sch_utama.py` + `kisym.py`; ERC 0, netlist dicek terhadap tabel pin). **Layout 22/10**:
  21 footprint ditempatkan sesuai model v16, routing pertama FreeRouting (`hardware/tools/autoroute/`) + GND pour 2 sisi,
  0 unconnected; tertunda: Q1 → `TO-92_Inline_Wide` (ganti di Eeschema + F8, jangan buat ulang skematik karena UUID
  acak), keputusan SW1 (pad pemasang 0,25 mm), merapikan jalur. Koordinat sama dengan proyek PCB sensor (X = 200 + x robot, Y = 180,55 − y robot). J5 JST XH 8 pin
  di tepi miring sidepod kiri (pin 1 dekat hidung), urutan = J1; C1 elko di sidepod kiri. ESP32 di socket di atas (jangan di bawah, keputusan user 18/10). Penjelasan di
  `hardware/pcb-utama/README.md`. `hardware/ltm-main/` = PCB utama v2 lama (13/10, kabel pita IDC), tidak dipakai.
- **Aturan cetak (tempat cetak user, 21/10)**: jalur min **0,3 mm**, jarak beda net 0,254, ke ground pour **0,5**,
  via 0,6/1,0 (2 layer 1,27), slot 1/1,5, silkscreen 0,2, mask expansion 0,1. SOIC aman, SSOP 0,65 tidak. Isian
  KiCad di `docs/aturan-cetak-pcb.md`, template impor di `hardware/aturan-cetak-template/`. Konstanta `FAB` di
  `gen_pcb.py` masih aturan lama (0,8 mm).

### Mekanik
- **v16** (`mechanical/`, 22/10): model https://claude.ai/artifact/C6BMXLgUPLJN5Aubm8uyx3, ±116 × 165 × 62 mm.
  Bentuk rendah gaya Ichiduino: PCB sensor + PCB utama sejajar dekat lantai, semua komponen + baterai di atas.
  PCB sensor rev B dibaca langsung dari `.kicad_pcb` (`cadquery/ltm_v16.py`), PCB utama bentuk mobil F1, kabel JST
  XH 8 pin menyusuri tepi kiri hidung, usulan skid nilon
  di baut H1/H2 (belum dikonfirmasi user). v15 (XLINE) https://claude.ai/artifact/AKgsuWNwB9LYzNtRYeSRqo.
- **Rakitan PCB LFM** (`mechanical/rakitan-pcb/`, 24/10): kedua PCB asli diekspor `kicad-cli` (GLB) + mekanik v16,
  viewer dengan garis ukuran + alat ukur https://claude.ai/artifact/7JpKSCkUepxGQdxK5ZhVpv. Jalankan ulang
  `gen_rakitan.py` tiap PCB berubah. Footprint `pcb-utama` belum punya model 3D (skrip menambahkannya di salinan).
- Body 3D print = opsi B: PCB jadi sasis, 3D print untuk cover, bumper, dudukan motor & baterai, sayap belakang.
  Belum di RAB (tunggu info printer lab). Target dosen: desain mekanik selesai minggu ke-8.
- Versi lama (v11–v14) di `arsip/` (lihat `arsip/README.md`).

### Anggaran & dokumen
- RAB terakhir **Rp902.000** (22/10/2026), **lewat Rp2.000 dari batas Rp900.000** → perlu dipangkas sebelum pitching.
  QRE1113GR ternyata ada di toko lokal **Rp15.000/pcs** → dibeli 12 tanpa cadangan (keputusan user); breadboard +
  timah dipinjam lab (keluar RAB); kabel pita → JST XH 8 pin (Rp5.000, perkiraan). Nama toko + link QRE menyusul
  dari user. Lintasan uji di luar RAB.
- Charter: `docs/charter.md`; docx dibuat ulang dengan `docs/charter-docx/gen_charter.js` (`npm i docx`, lalu
  `node gen_charter.js ../Project_Charter_PJBL.docx`; isinya harus sama dengan `charter.md`). Node.js 24 LTS sudah
  terpasang di laptop (22/10); di shell lama tambahkan `C:Program Files
odejs` ke PATH.
- Perhitungan motor kelompok (`docs/perhitungan-motor.md`): masih draf, belum sinkron dengan charter (≥ 0,5 m/s)
  dan roda Ø34.
- Belum ikut rancangan terkini: `docs/skematik-v1.md`, `docs/minsys-v1.md`, `docs/gen_rab_pemeliharaan.py`,
  generator `hardware/tools/`, `firmware/Pins.h`, `README.md` bagian firmware.

### Visual (artifact claude.ai)
- Wiring diagram per blok: https://claude.ai/artifact/Enb11oGXVb5YkwQmU6DhJY (sumber `docs/wiring-diagram.html`;
  22/10: kabel JST XH 8 pin, mux I2–I13)
- Diagram blok (21/10): https://claude.ai/artifact/VgPaH3FbRFSDaHB658YTcT (`docs/diagram-blok.png`,
  `docs/diagram-blok-kendali.png`, sumber `docs/diagram-blok-src/`)
- Arsitektur sistem: https://claude.ai/artifact/9dNV7sB3TdaNBcSojbtzAa; flowchart 3 slide:
  https://claude.ai/artifact/EMfY1GGrPrx9etNHpKmhEi
- Model lama: v11 3rW7AaXeb6bug9ahwW6mWv, v12 MjwounZ25sDKUH1FWent3d, v13 MPiswHWgW5SBjHc9BhH8u4,
  v14 5zf7kFLtjenLFpFJ7Ukids, bentuk rendah PHUWVJWJy2sDEXEf3AtSyx (semua `https://claude.ai/artifact/<id>`)

## Riwayat keputusan (ringkas)
- 05/10: arahan dosen: line tracer ikuti garis + **path planning**, budget maks Rp900.000, reverse engineering
  produk contoh (Ichibot).
- 08/10: ESP32-S3 → ESP32 biasa. Dua jalur PCB: (1) **jalur utama PjBL** versi modul (ESP32 DevKit, modul TB6612,
  modul buck disolder ke PCB carrier); (2) **side project pribadi** PCB semi-terintegrasi (chip di PCB, dana sendiri;
  kalau bagus bisa jadi versi utama dengan persetujuan tertulis koordinator).
- 09/10: IMU MPU6050 dihapus (arahan dosen).
- 11/10: bentuk jangkar (v10/v11), layout PCB v1 dari generator.
- 13/10: PCB utama v2 (lebih sedikit komponen, silkscreen blok untuk edukasi); sensor 16 ITR20001 + mux + MCP23017.
- 15/10: 12 TCRT5000, LED IR selalu nyala; user menggambar skematik sendiri.
- 16–18/10: mekanik v13 gaya Ichiduino Pro, ESP32 di atas.
- 20/10: sensor LED merah + PT 1206 (v14), lalu diganti **12 QRE1113GR**, PCB sensor gaya XLINE (v15); MCP23017 dihapus.
- 21/10: mux jadi IC SOIC-24W; aturan cetak baru (0,3 mm).
- 22/10: PCB sensor user masuk repo (rev A), lalu **rev B jangkar** disetujui; MCP KiCad; kerja pindah ke laptop.
  File usang dipindah ke `arsip/`.

## Aturan teknis firmware
- **Kompatibel dengan Arduino-ESP32 core 2.x DAN 3.x.** API LEDC berubah di 3.0 (`ledcSetup/ledcAttachPin` →
  `ledcAttach`). Bungkus pakai `#if ESP_ARDUINO_VERSION_MAJOR >= 3`, karena Mind+ bisa jadi pakai core yang lebih lama.
- PWM motor 20 kHz, resolusi 8-bit.
- ADC cuma boleh pakai ADC1, atenuasi 11 dB. Sensor dibaca lewat mux (satu pin SIG).
- LED IR selalu nyala: tidak ada pembacaan ON/OFF; andalkan kalibrasi min/max.
- Posisi pakai weighted average dari nilai ternormalisasi 0–1000. Kalau garis hilang, return nilai ujung sesuai sisi
  terakhir. Rentang posisi untuk 12 sensor (dan apakah memakai koordinat busur rev B) belum diputuskan.
- `follow()` jalan di rate tetap (mis. 1 kHz, cek pakai `micros()`). Kalau dipanggil lebih cepat, langsung return.
  Nggak boleh ada `delay()`.
- Nggak pakai `String` dan alokasi dinamis di loop.
- Semua dokumentasi dan komentar dalam Bahasa Indonesia, nama kode tetap bahasa Inggris.
- `platformio.ini` masih untuk ESP32-S3 (board `esp32-s3-devkitc-1`, USB CDC); susun ulang untuk ESP32 DevKit
  sebelum milestone firmware pertama.

### API library (target, dari rancangan 8 sensor; sesuaikan ke 12 sensor)
```cpp
void begin();
void calibrate(uint16_t durationMs = 3000); // simpan min/max ke NVS (Preferences)
bool loadCalibration();
void readRaw(uint16_t out[]);                // nilai mentah tiap sensor
int  position();                             // 0 = tengah
bool lineDetected();
bool junction();                             // sebagian besar sensor lihat garis
void setLineColor(bool blackOnWhite);
void motor(int left, int right);             // -255..255
void stop();
void follow(int speed, float kp, float kd);  // 1 langkah PID, non-blocking
float batteryVoltage();
void beep(uint16_t ms);
void led(uint8_t r, uint8_t g, uint8_t b);   // WS2812 belum ada di rancangan sekarang
bool buttonPressed(uint8_t id);
```

### Milestone (kerjakan berurutan, 1 milestone = 1 commit)
- [ ] M0: setup PlatformIO, serial jalan, blink (WS2812 belum ada di rancangan; pakai OLED/buzzer)
- [ ] M1: driver motor + perintah serial `m <kiri> <kanan>`
- [ ] M2: baca sensor mentah lewat mux, stream ke serial
- [ ] M3: kalibrasi + posisi + simpan/muat NVS
- [ ] M4: PID `follow()` + tuning lewat serial (`kp`, `kd`, `spd`)
- [ ] M5: junction, tombol, buzzer, baterai + low-battery warning
- [ ] M6: extension Mind+ (lihat catatan di bawah)
- [ ] M7: contoh program + `docs/` panduan pemakaian blok

### Catatan extension Mind+
- **Cek dulu format user extension Mind+ dari dokumentasi resmi DFRobot** sebelum nulis (struktur config, definisi
  blok, generator, folder library C++). Jangan nebak formatnya.
- Daftar blok: `inisialisasi robot`, `kalibrasi sensor`, `muat kalibrasi`, `posisi garis`, `garis terdeteksi?`,
  `ada persimpangan?`, `warna garis [hitam/putih]`, `ikuti garis kecepatan () Kp () Kd ()`, `motor kiri () kanan ()`,
  `stop`, `tegangan baterai`, `bunyi () ms`, `LED R G B`, `tombol [A/B] ditekan?`

## Struktur repo
```
Line-Follower-Racer/
├── CLAUDE.md
├── firmware/        proyek PlatformIO (lib/LineFollower/src/{LineFollower.h,.cpp, Pins.h}, src/main.cpp)
├── mindplus-ext/    extension Mind+ (belum dimulai)
├── hardware/        KiCad: sensor-garis/ (PCB sensor), pcb-utama/ (PCB utama baru), ltm-main/ (v2 lama), tools/
├── mechanical/      model 3D v16 (CadQuery, STEP, DXF, STL, render)
├── docs/            charter, skematik, wiring diagram, logbook, referensi
└── arsip/           file yang sudah digantikan (lihat arsip/README.md)
```

## KiCad & MCP
- MCP KiCad `hardware/tools/kicad-mcp/` (IPC API KiCad 9/10 lewat kicad-python, KiCad 8 tidak didukung). Panduan:
  `kicad-mcp/README.md` dan `docs/handover-claude-lokal.md` bagian 4. KiCad 9 belum punya FlipItems & GetItemsById.
- Jangan `save_board` tanpa diminta. Sesudah mengubah tata letak: render (tampak bawah untuk sensor) + DRC.
- Net dari label lokal KiCad berawalan `/` (pola net class `/VBAT`, bukan `VBAT`); net simbol daya tidak.
- `.kicad_dru`: pakai `intersectsCourtyard` (`memberOfFootprint` tidak jalan di KiCad 7).
- FreeRouting mentok: cari leher botol (celah antar baris kaki) daripada menambah passes.

## Workflow dengan Claude Code
- Kerja di laptop user sejak 22/10/2026: status, pekerjaan tertunda, dan cara setup di `docs/handover-claude-lokal.md`.
- Tiap selesai milestone: `pio run` harus sukses tanpa warning baru.
- Flash dan tes di hardware dilakukan Merv. Tunggu hasil tesnya sebelum lanjut ke milestone berikutnya.
- Kalau ada keputusan desain yang belum jelas, tanya dulu, jangan diasumsikan. **Konfirmasi keputusan besar**
  (pernah salah mengira pertanyaan user sebagai keputusan).
- Visual: buka `docs/referensi/`, cocokkan siluet, render dan bandingkan berdampingan dengan foto referensi sebelum
  dikirim. User berkali-kali kecewa karena gambar tidak mirip referensi.
- Commit per pekerjaan selesai, pesan commit Bahasa Indonesia, push ke `main`.
- **Tiap selesai mengerjakan sesuatu: tambahkan entri di `docs/log-kerja.md` (log per hari), commit, push** (permintaan
  user 22/10).

## Pedoman PjBL
- Ringkasan pedoman resmi (gerbang G1–G5, 7 butir tugas, kriteria penerimaan, penilaian):
  `docs/pedoman-ringkas.md`. Cek ini sebelum menyusun dokumen apa pun untuk gerbang.
- Kelompok ini jalur P, tapi kit yang dibeli hanya contoh/pembanding: seluruh robot dibuat
  dari nol. Di dokumen, kit acuan diposisikan sebagai pembanding.
- PjBL berjalan per **gate**: tiap gate wajib diasistensikan ke dosen pembimbing sebelum
  lanjut ke tahap berikutnya (G1 = lembar telaah & uji defisit, sudah ditandatangani 02/10/2026).

## Logbook mingguan (PjBL)
- PERHATIAN: pedoman (Lampiran C) mewajibkan logbook PERSEORANGAN dengan menit praktik
  (dari 1020 menit) dan 5 pertanyaan. Template departemen di `docs/logbook/README.md` berbeda;
  konfirmasi ke pembimbing mana yang dipakai (mungkin keduanya).
- Tiap minggu kelompok wajib mengumpulkan logbook/laporan mingguan.
- Format WAJIB mengikuti template resmi: lihat `docs/logbook/README.md`
  (1. Project Identity, 2. Weekly Report Description, 3. Obstacle(s), 4. Documentation).
- Kalau diminta bikin logbook: tanya minggu ke- dan tanggalnya, kegiatan yang benar-benar
  dilakukan, kendala yang belum selesai, dan foto/dokumentasi yang ada. Jangan mengarang kegiatan.
- Simpan drafnya di `docs/logbook/minggu-XX.md`.
- Ada juga logbook utama (tabel harian: Tanggal | Rincian Kegiatan | Dokumentasi) di
  `docs/logbook/logbook-utama.md`. Laporan mingguan dirangkum dari entri di sana;
  tambahkan entri baru ke tabel itu tiap ada kegiatan.
