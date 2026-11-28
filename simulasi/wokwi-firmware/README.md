# Simulasi firmware ASLI LFM X1 di Wokwi (28/11/2026)

Folder ini menjalankan **firmware yang sama dengan yang diunggah ke robot** (`firmware/src` + `firmware/lib/LineFollower`)
di **wokwi.com** (browser, akun gratis). Menu OLED, kalibrasi, PID, dan rute per indeks bisa dicoba sebelum barang ada.
Simulasi lama `../wokwi-oled/` hanya purwarupa menu dengan data palsu.

Wokwi tidak punya mux CD74HC4067, QRE1113, motor N20 + encoder, dan tidak bisa menghitung tangga resistor. Semuanya
diganti satu **custom chip `robot-lfm`** yang memakai pin ESP32 yang sama seperti robot asli:

| Bagian robot | Ditiru chip | Pin ESP32 |
|---|---|---|
| 5 tombol tangga resistor | 5 pushbutton masuk chip, chip mengeluarkan tegangan tangga (0,30 / 0,93 / 1,49 / 2,12 / 2,63 V) | 34 |
| Baterai (pembagi 100k/33k) | slider **Baterai** | 39 (VN) |
| Mux + 12 sensor | 12 sensor di koordinat busur PCB sensor rev B, garis hitam 2 cm | S0–S3 = 26/25/33/32, SIG = 36 (VP) |
| TB6612 + motor N20 | chip membaca STBY, arah, dan duty PWM, lalu menggerakkan robot di arena grid | 2, 5/17/18, 4/15/16 |
| Encoder (PCNT) | pulsa kuadratur sesuai putaran roda | 13/14 (kiri), 23/19 (kanan) |
| Buzzer | LED merah "BUZZER" | 12 |
| OLED SSD1306 | OLED Wokwi | SDA 21, SCL 22 |

Layar di chip menampilkan arena (garis hitam), simpul start (hijau), robot (biru), dan sensor (merah = melihat garis).

## Menyiapkan file

```
python simulasi/wokwi-firmware/siapkan.py
```

Hasilnya di `simulasi/wokwi-firmware/unggah/` (tidak masuk git), 6 file:
`sketch.ino` (sengaja kosong), `firmware.cpp` (seluruh firmware digabung jadi satu file, karena wokwi.com tidak bisa
memakai folder library sendiri), `diagram.json`, `libraries.txt`, `robot-lfm.chip.json`, `robot-lfm.chip.c`.
**Jalankan ulang tiap firmware berubah.** Jangan edit `firmware.cpp` langsung.

## Langkah di wokwi.com

1. **New Project → ESP32** (Arduino).
2. Ganti isi `sketch.ino`, `diagram.json`, dan `libraries.txt` dengan file dari `unggah/` (buka file, Ctrl+A, Ctrl+V).
   Kalau `libraries.txt` belum ada, buat file baru dengan nama itu.
3. Buat 3 file baru lewat tombol **▼ di sebelah tab file → New file…**, beri nama persis `firmware.cpp`,
   `robot-lfm.chip.json`, `robot-lfm.chip.c`, lalu tempel isinya. (Kalau menunya punya *Upload file…*, keenam file
   bisa langsung diunggah.)
4. Tekan ▶. Kompilasi pertama agak lama (firmware ±3000 baris + chip).
5. Klik area kosong di gambar rangkaian supaya keyboard ikut bekerja: **← KEMBALI, ↑ ATAS, Enter OK, ↓ BAWAH, → LANJUT**.
6. **Klik chip robot** saat simulasi jalan untuk memunculkan slider-nya.

## Slider chip robot

| Slider | Isi |
|---|---|
| Baterai (V) | 7,6 V awal. Di bawah 6,8 V ikon baterai berkedip; 0 = hanya USB (motor mati, layar tulis "USB") |
| Geser robot ke kanan | menggeser robot tegak lurus garis: untuk **kalibrasi geser dengan tangan** dan melihat bar sensor bergerak |
| Arena grid N × N, jarak simpul | awal 4 × 4, 300 mm (sama dengan arena CoppeliaSim) |
| Start x, y, arah | robot ditaruh 2 cm sesudah simpul start, menghadap arah (0 timur, 1 utara, 2 barat, 3 selatan) |
| Geser untuk menaruh robot di start lagi | ubah nilainya (0 ↔ 1) untuk mengembalikan robot ke start |
| Skala ADC | lihat bagian "Kalau ada masalah" |

Mengubah ukuran arena atau start juga langsung menaruh ulang robot.

## Urutan mencoba

1. Layar utama tampil: rute, "Kal: BELUM", bar 12 sensor (S6–S7 menyala karena robot di atas garis).
2. **▶ → Kalibrasi → OK** (robot berayun sendiri): robot di layar chip bergoyang kiri-kanan, lalu "Selesai! Data
   disimpan". Bisa juga ▶ (geser dengan tangan) sambil menggeser slider **Geser robot** dari −60 ke +60.
3. **Lihat sensor**: geser slider, bar dan "Pos" berubah (+ = garis di kanan robot).
4. **Tes motor**: LED motor menyala, robot di layar bergerak; **Info robot** menampilkan hitungan encoder.
5. Layar utama, **▲▼ pilih rute**, **OK** → hitung mundur → robot menjalankan rute di arena:

| Rute di menu | Start (slider) | Yang terjadi |
|---|---|---|
| Uji simpang | (0,0) timur | berhenti di simpang pertama |
| Slide 8 | (0,0) timur | rute slide 8 deck pitching (= CoppeliaSim) |
| Kotak kiri | (0,0) timur | 4× belok kiri, kembali ke awal |
| Ujung balik | (0,0) timur | ke ujung garis, putar balik, berhenti di simpang |
| Terpendek 4x4 | (0,0) **utara** (arah = 1) | rute terpendek ke (3,3) menghindari (1,0), (2,2), (1,2) |

Tombol apa pun saat robot berjalan = STOP. Sesudah rute, taruh robot di start lagi (slider) sebelum mencoba rute lain.
Kalibrasi tersimpan di NVS tiruan dan hilang saat simulasi dihentikan.

Perintah serial (Serial Monitor Wokwi, ketik `help`) juga bisa dipakai: `raw`, `pos`, `btn`, `bat`, `enc`, `jalan`, dst.

## Kalau ada masalah

- **Tombol kacau** (OK terbaca LANJUT, dsb.): dokumentasi Wokwi menulis acuan ADC virtual = 5 V untuk semua MCU,
  jadi chip mengalikan tegangan 5/3,3. Kalau ternyata tidak begitu, klik chip dan ubah **Skala ADC** ke 3,3. Cek dengan
  perintah serial `btn`: angka mV saat tombol ditahan harus dekat 300 (ATAS), 930 (BAWAH), 1490 (KEMBALI),
  2120 (OK), 2630 (LANJUT).
- **Baterai terbaca beda ±0,5 V dari slider**: wajar, kalibrasi ADC (eFuse) ESP32 tiruan Wokwi tidak sama dengan chip
  asli.
- **Error kompilasi**: salin pesan errornya. Firmware gabungan sudah dicek lolos kompilasi di core 2.0.17 dan 4.0.0
  (PlatformIO); versi core wokwi.com tidak tertulis di dokumentasinya.
- **Robot tidak bergerak** saat tes motor tapi LED motor menyala: chip tidak bisa membaca PWM. Laporkan, nanti chip
  diganti memakai kecepatan tetap.

## Batas tiruan

- Belum dicoba di wokwi.com oleh Claude (tidak bisa membuka Wokwi dari laptop). Yang sudah dicek: firmware gabungan
  lolos kompilasi (core 2.0.17 dan 4.0.0, tanpa warning), sintaks C chip dengan header tiruan, JSON valid.
- Arena = grid penuh, bukan arena tangga IARC. Motor linear tanpa zona mati, roda tidak selip, sensor tanpa cahaya
  luar. Jadi nilai PID yang bagus di sini **belum tentu** bagus di robot asli; tuning tetap di robot
  (`docs/firmware-uji.md`).
- Angka robot (koordinat sensor, roda, encoder, tegangan tombol) disalin dari `RobotConfig.h`. Kalau konstanta di sana
  diubah, ubah juga di `robot-lfm.chip.c`.
