# Line Follower ESP32-S3 + Block Programming

## Tujuan
Robot line follower yang murah tapi performanya bagus, bisa diprogram pakai blok (Mind+ user extension, MicroBlocks opsional).
Arsitektur 3 lapis:
1. **Library C++ `LineFollower`**: logika aslinya, ditulis & dites duluan
2. **Desain blok**: 1 blok = 1 fungsi library
3. **Extension Mind+**: blok menghasilkan kode C++ yang memanggil library (compile native → PID tetap cepat)

## Keputusan terbaru (menggantikan bagian Hardware/Pin map di bawah bila bertentangan)
- 08/10/2026: MCU diganti dari ESP32-S3 ke **ESP32 biasa (DevKit CH340/CP2102)** karena harga
  S3 di marketplace > Rp 130.000. ADC1 ESP32 biasa di devkit hanya 6 pin (32, 33, 34, 35, 36, 39):
  **5 sensor garis + 1 sensor tegangan baterai**, tanpa multiplexer. Jangan pakai ADC2 (bentrok
  WiFi, banyak pin strapping). Posisi garis jadi −2000..2000. Acuan: Pololu 3pi (5 sensor, bisa
  maze solving). Pin map & platformio.ini perlu disusun ulang sebelum milestone firmware berikutnya.
- Sensor: 5 buah, susunan panah, di PCB sensor terpisah. **Diganti 13/10/2026: 16 sensor + multiplexer
  CD74HC4067 + LED indikator tiap sensor (MCP23017), lihat catatan 13/10 di bawah. 15/10/2026: jadi 12 TCRT5000. 20/10/2026: jadi 12 QRE1113GR, PCB gaya XLINE.**
- Baterai: 2S (2× 18650, holder 76×42×20 mm melintang di atas PCB utama), BMS 2S, charger 2S USB-C, buck 5 V.
- RAB revisi 3.3: Rp858.000 (digantikan revisi 3.4 Rp833.000, lihat di bawah) (lintasan uji di luar RAB). Body 3D print = opsi B (dipilih 08/10/2026): PCB tetap jadi sasis, 3D print berupa cover/body
  penutup di atas + bumper + dudukan motor & baterai. Belum di RAB (tunggu info printer lab).
- Motor: N20 6V 500 RPM + encoder, roda Ø34 mm (v_maks ± 0,89 m/s); driver TB6612FNG.
- 09/10/2026 (arahan dosen): **IMU MPU6050 dihapus** karena pengambilan datanya sulit. Belok 90° di
  persimpangan pakai encoder (selisih putaran roda) lalu dikunci ke garis oleh sensor. RAB revisi 3.4:
  Rp833.000 (sisa Rp67.000). I2C hanya untuk OLED.
- 11/10/2026: **bentuk robot = v10 "jangkar"** (menggantikan v9 rata dan konsep ringkas tanpa leher):
  PCB sensor jangkar + leher (gaya R3D Maker / LF edukasi 14 sensor), PCB utama siluet roket 94×84,
  motor N20 melintang di belakang, baterai 2×18650 di atas motor dengan cover oranye, sayap belakang
  opsional. ±174×98×59 mm. Model 3D: https://claude.ai/artifact/3rW7AaXeb6bug9ahwW6mWv, STEP + sumber
  CadQuery di `mechanical/`. CAD lanjutan: Fusion 360. Target dosen: desain mekanik selesai minggu ke-8.
  v11 (11/10/2026): livery navy-merah-kuning (inspirasi Red Bull Racing, TANPA logo/merek) + roda lebar
  "lonjong" Ø26 × 14 (lebar robot ±110; v_maks ±0,68 m/s; ketersediaan roda belum dicek → RAB & perhitungan
  motor menyusul).
  Pelajaran: user berkali-kali kecewa karena visual tidak mengikuti referensi; selalu buka
  `docs/referensi/` dan cocokkan siluet sebelum menggambar, dan render/cek sendiri sebelum dikirim.
- 11/10/2026: **layout PCB v1-draft** di `hardware/` (KiCad 7; user pakai KiCad 8/9): penempatan ikut
  koordinat mekanik v11, jalur FreeRouting + pour GND dua sisi, DRC 0 error/0 unconnected. Generator
  `hardware/tools/gen_pcb.py` (menimpa .kicad_pcb). J5 = lubang tembus: pin header J1 PCB sensor disolder di
  atas PCB utama (celah antar papan ±2,4 mm). OLED wajib socket 8,5 mm (R3–R8, Q1 di bawahnya); header
  OLED di belakang → layar diputar 180° di firmware. Model 3D v11 sudah disamakan dengan PCB (saklar &
  konektor baterai di tepi kiri Y 22–42, lubang bahu H3/H4 (±37,5; 69), spacer (±10,5; 83), pangkal leher
  PCB sensor ±14, JST motor X ±(17–27), area ball caster (0; 62) bebas kaki solder). Charger 2S USB-C TETAP
  di dinding belakang rangka (keputusan user 11/10), kabel OUT ke P+/P− BMS. Pelajaran: net dari label lokal
  KiCad berawalan "/" (pola net class harus "/VBAT", bukan "VBAT").
- 13/10/2026: **PCB utama v2** (permintaan user: kurangi clutter, gampang diakses untuk edukasi): C2–C6 &
  R5–R8 lama dibuang (modul sudah punya kapasitor; encoder INPUT_PULLUP), buzzer + Q1/R3/R4 tetap, D1 SS14 →
  1N5819 (semua kaki tembus). ESP32 keluar dari bawah dudukan baterai (Y 30,2–58,6, USB ke kiri) di socket female
  8,5 mm, TB6612 tengah depan & OLED kanan di socket (header OLED di depan → layar TIDAK diputar, U8G2_R0),
  MP1584 + D1 + R1/R2 di bawah dudukan baterai (set 5 V sebelum rangka dipasang), J1 + SW1 di tepi kanan, BMS
  di bawah PCB sisi kiri. Silkscreen kotak blok (DAYA, OTAK, DRIVER MOTOR, LAYAR, SUARA) + peta "ALUR DAYA".
  Tepi depan dudukan baterai (rangka) jadi Y 29,5.
- 13/10/2026: **16 sensor + mux + LED** (keputusan user; sebelumnya kukira mux cuma pertanyaan, jangan ulangi:
  konfirmasi keputusan besar). PCB sensor batang lurus 110 × 51 mm, 16 ITR20001 jarak 6,5 mm (diputar 270°:
  A/K di depan), LED IR seri berdua (R 120 Ω), modul breakout CD74HC4067 (C0–C15 satu baris, di socket; DIP
  tidak bisa dirouting dengan jalur 0,8), MCP23017 DIP-28 (I2C 0x20) untuk 16 LED 0805 (LED1–8 = GPA7..0,
  LED9–16 = GPB7..0). Pin ESP32 baru (tabel di docs/skematik-v1.md): SIG GPIO36, VBAT GPIO39, BTN_A/B
  GPIO34/35 (+R5/R6 10k pull-up), MUX_S0–S3 GPIO26/25/33/32, IR_EN 27, ENC_R 23/19, ENC_L 13/14, TB6612 di
  baris belakang (PWMA 18, AIN1 5, AIN2 17, PWMB 16, BIN1 4, BIN2 15, STBY 2 = LOW saat boot). firmware/Pins.h masih peta lama (S3). **Kabel pita IDC 12 pin** (box header J5 ↔ J1; pin ganjil = sinyal, genap = daya/I2C)
  + dudukan 3D print 2 lengan (H3/H4 PCB utama ↔ H1/H2 PCB sensor), konsep dari referensi Hackster user
  (QTR-8RC + kabel pita). Robot ±179 × 111 mm (user terima). RAB naik ke Rp896.000 (sisa Rp4.000; modul
  TCRT5000 prototipe dihapus).
- 13/10/2026: aturan cetak lama (jalur min 0,8 mm, asumsi) **digantikan 21/10/2026**: dari tempat cetak user, jalur
  min **0,3 mm**, jarak beda net min 0,254 mm, jarak ke ground pour min **0,5 mm**, via lubang 0,6 / pad 1,0 (2 layer
  1,27), slot 1 / 1,5, silkscreen 0,2 mm, mask expansion 0,1 mm. Isian KiCad di `docs/aturan-cetak-pcb.md`. SOIC aman,
  SSOP 0,65 mm tidak. Konstanta `FAB` di `gen_pcb.py` masih aturan lama.
  Tab logam saklar SW1 dikecualikan lewat `.kicad_dru` (`intersectsCourtyard`; `memberOfFootprint` tidak jalan
  di KiCad 7). FreeRouting bisa mentok: cari leher botol (celah antar baris kaki) daripada menambah passes.
- 15/10/2026: **user menggambar skematik sendiri di KiCad** (wiring diagram panduan per blok:
  https://claude.ai/artifact/Enb11oGXVb5YkwQmU6DhJY). Keputusan user: **12 sensor TCRT5000** (tiap LED IR
  R 330 Ω sendiri, selalu nyala; fototransistor COLL ← 4k7 ← +3V3, E → GND; PCB sensor bentuk jangkar 120 × 60 mm: sisi depan 40 mm, sayap 45°, batang tengah; sensor tegak
  (90° di footprint ltm:OPTO_TCRT5000) dengan jarak ke samping 10 mm: X ±5, ±15 (Y 8), ±25/35/45/55 (Y 18/28/38/48)
  dari tengah tepi depan = KiCad (212,5; 75); R330/R4k7 di sisi atas 7,5 mm di belakang tiap sensor, X ∓2),
  mux tetap (C0–C11, C12–C15 kosong), MCP23017 tetap (LED1–8 GPA7..0, LED9–12 GPB7..4). PCB utama target
  **12 × 12 cm** (kompromi; user awalnya minta 18 × 18). LED IR selalu nyala (tanpa MOSFET/IR_EN, keputusan user;
  pin 1 kabel pita kosong). Charter/RAB: Rp879.500, sisa Rp20.500; risiko R1 = kalibrasi + pelindung cahaya. File di hardware/ (generator, 16 ITR20001) dan model v12 BELUM ikut keputusan ini.
- 13/10/2026: mekanik v12 = PCB utama v2 + batang sensor + dudukan + kabel pita. Model 3D:
  https://claude.ai/artifact/MjwounZ25sDKUH1FWent3d (link v11 tetap). Usulan "leher pendek" sebelumnya
  digantikan konsep kabel pita.
- 16/10/2026: **usulan mekanik v13 gaya Ichiduino Pro** (permintaan user: semirip mungkin dengan foto produk,
  komponen RAB sekarang, OLED 0,96"). PCB sensor capit 120 × 80 (12 TCRT5000 posisi 15/10, batang masuk ke bawah
  PCB utama + 4 spacer 4 mm), roda Ø43 × 19 merah, mux + MCP23017 di sisi bawah PCB sensor, pelindung cahaya
  3D print, sayap 3 panel. ±120 × 160 × 70. 18/10: **ESP32 jangan di bawah** (keputusan user) → ESP32 di socket di
  atas, melintang di depan dudukan baterai; PCB utama jadi 100 × 121 (bahu di depan roda, hidung menutupi tengah PCB
  sensor). Model: https://claude.ai/artifact/MPiswHWgW5SBjHc9BhH8u4, file per bagian di `mechanical/v13/`. Belum
  dikonfirmasi user: roda Ø43, mux/MCP di bawah. User merancang PCB sendiri sesudah ini.
- 20/10/2026: **rombak sensor (keputusan user)**: 12 pasang **LED superbright merah + fototransistor bening, keduanya
  SMD 1206**, di sisi bawah PCB sensor capit (posisi 15/10; LED di depan, PT di belakang, jarak tengah 3,8 mm). LED:
  R 330 Ω dari +5V (±8 mA); PT: kolektor ← R 10k (uji 4k7–47k) ← +3V3, emitor → GND, kolektor ke mux. **MCP23017 +
  LED indikator dihapus** (bacaan sensor = bar di OLED). Kabel pita 12 pin tetap, pin 1, 10, 12 kosong. **Roda Ø34**
  (RAB). Model v14: https://claude.ai/artifact/5zf7kFLtjenLFpFJ7Ukids, file di `mechanical/v14/` (PCB utama = v13;
  PCB sensor Z 4,8, mux di socket di atas palm PCB sensor di depan hidung PCB utama, masker 3D print hitam dengan
  jendela per LED/PT, skid nilon pengganti ball caster; ±120 × 174 × 62). Wiring diagram artifact Enb11oGXVb5YkwQmU6DhJY
  sudah diperbarui (sumber: `docs/wiring-diagram.html`). RAB Rp859.500 (sisa Rp40.500): OLED 0,96" Rp33.000, LED 1206
  15×Rp500, PT 1206 impor 15×Rp4.000 (perkiraan, mis. Everlight PT15-21C / Vishay TEMT6000X01; tidak ada di toko
  lokal → risiko R8, pesan paling lambat minggu 8). Charter docx dibuat ulang dengan `docs/charter-docx/gen_charter.js`
  (`npm i docx`, lalu `node gen_charter.js ../Project_Charter_PJBL.docx`; isinya harus sama dengan `docs/charter.md`).
  Belum ikut 20/10: `docs/skematik-v1.md`, `docs/minsys-v1.md`, RAB pemeliharaan (`gen_rab_pemeliharaan.py`), `hardware/`.
- 20/10/2026 (kedua, menggantikan sensor LED merah + PT di atas): **12 QRE1113GR** (LED IR + fototransistor satu
  kemasan SMD; pin 1 A, 2 K, 3 C, 4 E; R LED 220 Ω dari +5V ±17 mA, pull-up 10k ke +3V3) dan **PCB sensor gaya JSumo
  XLINE** (foto `docs/referensi/ref-jsumo-xline.png`; pilihan user: tetap 12 sensor, warna hitam): pita 13 mm, tengah
  lurus + sayap 30°, jarak 9 mm, sensor 4 & 9 di tekukan, mux + J1 di badan tengah, tab 2 baut di bawah OLED, tanpa
  masker. Model v15: https://claude.ai/artifact/AKgsuWNwB9LYzNtRYeSRqo, file `mechanical/v15/` (posisi sensor di
  `dxf/pcb_sensor_posisi_qre1113.csv`). Robot ±118 × 165 × 62. RAB Rp867.000 (QRE 15 × Rp5.000 perkiraan impor;
  RS Indonesia ±Rp11.600/pcs → lewat batas). Pelajaran: bandingkan render dengan foto referensi berdampingan
  sebelum dikirim (versi pertama v15 masih berbentuk T, beda proporsi sayap).
- 21/10/2026: mux jadi **IC CD74HC4067 SOIC-24 lebar** disolder langsung (keputusan user: hemat tempat), simbol KiCad
  CD74HC4067M + SOIC-24W_7.5x15.4mm_P1.27mm (bukan SSOP), VCC +3V3, E̅ ke GND, I0–I11 = S1–S12, I12–I15 ke GND,
  C 100 nF. Listing kakarobot: foto IC tapi deskripsi "Breakout Module" → user diminta tanya penjual; cadangan IC
  74HC4067D (SO-24) Rp35.000 di marconijawa. Butuh jalur ±0,4 mm di sekitar IC; tempat cetak PCB sanggup 0,3 mm
  (aturan 21/10: jalur 0,3 mm, jadi aman). Model v15 (link sama) diperbarui: badan tengah 34 mm, skid tengah pindah ke tab.
  RAB Rp887.000 (sisa Rp13.000).
- Diagram blok (21/10/2026, sesuai rancangan terbaru): https://claude.ai/artifact/VgPaH3FbRFSDaHB658YTcT, gambar
  `docs/diagram-blok.png`. Arsitektur sistem 09/10 di bawah sudah usang (5 ITR20001, MOSFET, pin map lama).
- Visual terbaru: arsitektur sistem (Claude Design, 16:9) https://claude.ai/artifact/9dNV7sB3TdaNBcSojbtzAa,
  flowchart 3 slide https://claude.ai/artifact/EMfY1GGrPrx9etNHpKmhEi
- Bentuk robot: rendah satu bidang (gaya Ichiduino). PCB sensor panah + PCB utama sejajar ± 6 mm dari lantai,
  sensor di sisi bawah, semua komponen + baterai di atas, papan OLED/tombol ditumpuk di atas ESP32.
  Visual: https://claude.ai/artifact/PHUWVJWJy2sDEXEf3AtSyx
- Dua jalur PCB (08/10/2026):
  1. **Jalur utama PjBL (dana departemen, sesuai RAB revisi 3.2 Rp845.000):** versi modul ("tempel modul"):
     ESP32 DevKit, modul TB6612, modul buck, dll. disolder ke PCB carrier. Rancangan: `docs/minsys-v1.md`.
  2. **Side project pribadi (dana sendiri, di luar RAB):** PCB semi-terintegrasi seperti `docs/referensi/`:
     chip TB6612 + chip buck di PCB, sensor diskrit, dicetak & disolder sendiri. Kalau hasilnya bagus,
     bisa diangkat jadi versi utama (perlu persetujuan tertulis koordinator karena komponen RAB berubah).
  Kedua versi WAJIB memakai pin map yang sama supaya firmware bisa dipakai di keduanya.
- Perhitungan awal motor/roda dari kelompok (target 1,5 m/s, roda 60 mm, ±500 RPM, torsi desain ≥ 27 N·mm
  per roda): `docs/perhitungan-motor.md`. Masih draf, belum sinkron dengan charter (≥ 0,5 m/s) dan
  RAB (roda Ø34 mm).

## Hardware
- MCU: ESP32-S3-WROOM-1-N4 (flash 4MB, tanpa PSRAM), USB native (GPIO19/20)
- Sensor: 8× ITR20001/QRE1113, jarak 8–10 mm, emitter IR di-switch via MOSFET
- Driver motor: TB6612FNG, motor N20 6V (encoder opsional)
- Power: LiPo 2S → motor langsung; buck MP1584 5V → LDO ME6211 3,3V
- Pembagi tegangan baterai: 100k / 33k ke ADC
- UI: 2 tombol, buzzer, 1× WS2812, header I2C (OLED/IMU)

## Pin map
| Fungsi | GPIO |
|---|---|
| Sensor S1–S8 (ADC1) | 1, 2, 3, 4, 5, 6, 7, 8 |
| IR emitter enable | 9 |
| Sensor baterai | 10 |
| TB6612 PWMA / AIN1 / AIN2 | 11 / 12 / 13 |
| TB6612 PWMB / BIN1 / BIN2 | 14 / 15 / 16 |
| TB6612 STBY | 17 |
| Tombol A (BOOT) / Tombol B | 0 / 18 |
| Buzzer | 21 |
| WS2812 | 48 |
| I2C SDA / SCL | 40 / 41 |
| Encoder L-A, L-B, R-A, R-B | 38, 39, 42, 47 |

Semua pin taruh di `Pins.h` sebagai satu-satunya sumber kebenaran.

## Struktur repo
```
Line-Follower-Racer/
├── CLAUDE.md
├── firmware/                 # proyek PlatformIO
│   ├── platformio.ini
│   ├── lib/LineFollower/
│   │   ├── library.properties
│   │   ├── src/{LineFollower.h, LineFollower.cpp, Pins.h}
│   │   └── examples/
│   └── src/main.cpp          # test harness + perintah serial
├── mindplus-ext/             # extension Mind+
└── docs/
```

## API library (target)
```cpp
void begin();
void calibrate(uint16_t durationMs = 3000); // simpan min/max ke NVS (Preferences)
bool loadCalibration();
void readRaw(uint16_t out[8]);               // nilai (IR ON − IR OFF)
int  position();                             // -3500..3500, 0 = tengah
bool lineDetected();
bool junction();                             // ≥6 sensor lihat garis
void setLineColor(bool blackOnWhite);
void motor(int left, int right);             // -255..255
void stop();
void follow(int speed, float kp, float kd);  // 1 langkah PID, non-blocking
float batteryVoltage();
void beep(uint16_t ms);
void led(uint8_t r, uint8_t g, uint8_t b);
bool buttonPressed(uint8_t id);
```

## Aturan teknis
- **Kompatibel dengan Arduino-ESP32 core 2.x DAN 3.x.** API LEDC berubah di 3.0 (`ledcSetup/ledcAttachPin` → `ledcAttach`). Bungkus pakai `#if ESP_ARDUINO_VERSION_MAJOR >= 3`, karena Mind+ bisa jadi pakai core yang lebih lama.
- PWM motor 20 kHz, resolusi 8-bit.
- ADC cuma boleh pakai ADC1 (ADC2 bentrok dengan WiFi), atenuasi 11 dB.
- Pembacaan sensor: emitter ON → baca → emitter OFF → baca → selisih (anti cahaya ruangan). **15/10/2026: tidak
  dipakai, LED IR selalu nyala (keputusan user); andalkan kalibrasi + pelindung cahaya.**
- Posisi pakai weighted average dari nilai ternormalisasi 0–1000. Kalau garis hilang, return ±3500 sesuai sisi terakhir.
- `follow()` jalan di rate tetap (mis. 1 kHz, cek pakai `micros()`). Kalau dipanggil lebih cepat, langsung return. Nggak boleh ada `delay()`.
- Nggak pakai `String` dan alokasi dinamis di loop.
- Semua dokumentasi dan komentar dalam Bahasa Indonesia, nama kode tetap bahasa Inggris.

## platformio.ini (acuan)
```ini
[env:lf]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
board_upload.flash_size = 4MB
board_build.partitions = default.csv
monitor_speed = 115200
build_flags = -DARDUINO_USB_MODE=1 -DARDUINO_USB_CDC_ON_BOOT=1
```

## Milestone (kerjakan berurutan, 1 milestone = 1 commit)
- [ ] M0: setup PlatformIO, serial jalan, blink WS2812
- [ ] M1: driver motor + perintah serial `m <kiri> <kanan>`
- [ ] M2: baca sensor mentah ON/OFF, stream ke serial
- [ ] M3: kalibrasi + posisi + simpan/muat NVS
- [ ] M4: PID `follow()` + tuning lewat serial (`kp`, `kd`, `spd`)
- [ ] M5: junction, tombol, buzzer, baterai + low-battery warning
- [ ] M6: extension Mind+ (lihat catatan di bawah)
- [ ] M7: contoh program + `docs/` panduan pemakaian blok

## Catatan extension Mind+
- **Cek dulu format user extension Mind+ dari dokumentasi resmi DFRobot** sebelum nulis (struktur config, definisi blok, generator, folder library C++). Jangan nebak formatnya.
- Daftar blok: `inisialisasi robot`, `kalibrasi sensor`, `muat kalibrasi`, `posisi garis`, `garis terdeteksi?`, `ada persimpangan?`, `warna garis [hitam/putih]`, `ikuti garis kecepatan () Kp () Kd ()`, `motor kiri () kanan ()`, `stop`, `tegangan baterai`, `bunyi () ms`, `LED R G B`, `tombol [A/B] ditekan?`

## Workflow dengan Claude Code
- Tiap selesai milestone: `pio run` harus sukses tanpa warning baru.
- Flash dan tes di hardware dilakukan Merv. Tunggu hasil tesnya sebelum lanjut ke milestone berikutnya.
- Kalau ada keputusan desain yang belum jelas, tanya dulu, jangan diasumsikan.

## Pedoman PjBL
- Ringkasan pedoman resmi (gerbang G1–G5, 7 butir tugas, kriteria penerimaan, penilaian):
  `docs/pedoman-ringkas.md`. Cek ini sebelum menyusun dokumen apa pun untuk gerbang.
- Kelompok ini jalur P, tapi kit yang dibeli hanya contoh/pembanding: seluruh robot dibuat
  dari nol. Di dokumen, kit acuan diposisikan sebagai pembanding.

- Arahan dosen 05/10/2026: minimum requirement line tracer = ikuti garis otomatis + PATH PLANNING;
  budget maksimal Rp 900.000; proyek berupa reverse engineering produk contoh (Ichibot).

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
- PjBL berjalan per **gate**: tiap gate wajib diasistensikan ke dosen pembimbing sebelum
  lanjut ke tahap berikutnya (G1 = lembar telaah & uji defisit, sudah ditandatangani 02/10/2026).
