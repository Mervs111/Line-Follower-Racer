# Line Follower ESP32-S3 + Block Programming

## Tujuan
Robot line follower yang murah tapi performanya bagus, bisa diprogram pakai blok (Mind+ user extension, MicroBlocks opsional).
Arsitektur 3 lapis:
1. **Library C++ `LineFollower`**: logika aslinya, ditulis & dites duluan
2. **Desain blok**: 1 blok = 1 fungsi library
3. **Extension Mind+**: blok menghasilkan kode C++ yang memanggil library (compile native → PID tetap cepat)

## Keputusan terbaru (menggantikan bagian Hardware/Pin map di bawah bila bertentangan)
- 08/10/2026: MCU diganti dari ESP32-S3 ke **ESP32 biasa (DevKit CH340/CP2102)** karena harga
  S3 di marketplace > Rp 130.000. ADC1 ESP32 biasa yang keluar di devkit hanya 6 pin, jadi
  8 sensor garis dibaca lewat **analog multiplexer 74HC4051** (1 pin ADC + 3 pin select).
  Jangan pakai ADC2 (bentrok WiFi, banyak pin strapping). Pin map & platformio.ini perlu
  disusun ulang untuk ESP32 biasa sebelum milestone firmware berikutnya.
- Sensor: 8 buah, susunan panah, di PCB sensor terpisah.
- Baterai: 2S (2× 18650), BMS 2S, charger 2S USB-C, buck 5 V.
- Motor: N20 + encoder; driver TB6612FNG.

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
- Pembacaan sensor: emitter ON → baca → emitter OFF → baca → selisih (anti cahaya ruangan).
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
