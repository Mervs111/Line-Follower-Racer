# Line Follower ESP32 + Block Programming

Proyek PjBL Semester 5: robot line follower edukasi yang murah tapi performanya bagus, dan bisa diprogram pakai
blok (user extension Mind+). Target lomba: IARC XII Smart Robotics (9–10/01/2027). Anggaran maks Rp1.000.000 (naik dari Rp900.000 pada 26/10/2026).

> **Untuk anggota kelompok:** baca bagian [Status terkini](#status-terkini-23102026) dan
> [Yang harus dilakukan](#yang-harus-dilakukan-berikutnya) dulu. Catatan kerja harian ada di
> [`docs/log-kerja.md`](docs/log-kerja.md); detail rancangan lengkap (pin map, keputusan, aturan) di
> [`CLAUDE.md`](CLAUDE.md).

## Status terkini (23/10/2026)

| Bagian | Status | Di mana |
|---|---|---|
| Charter & RAB | Charter sudah disesuaikan dengan rancangan terbaru. **RAB Rp937.390 (harga hasil validasi marketplace 27/10), sisa Rp62.610** dari batas Rp1.000.000 | `docs/charter.md`, `docs/Project_Charter_PJBL.docx` |
| Diagram (blok, wiring, arsitektur, flowchart) | Selesai, sudah sesuai rancangan 22/10 | tautan di bawah, `docs/wiring-diagram.html` |
| PCB sensor | **Rev B disetujui**: bentuk jangkar, lebar 95 mm, 12 QRE1113GR + mux CD74HC4067, DRC 0 | `hardware/sensor-garis/` (+ `REVISI.md`) |
| Skematik PCB utama | **Selesai**: 21 komponen, ERC 0, netlist dicek terhadap pin map | `hardware/pcb-utama/pcb-utama.kicad_sch`, PDF `pcb-utama-skematik.pdf` |
| Layout PCB utama | **Routing pertama selesai** (22/10): bentuk "mobil F1" 100 × 127 mm, semua net tersambung, GND pour 2 sisi. Masih ada 11 error DRC dari footprint Q1 dan SW1 (lihat di bawah) | `hardware/pcb-utama/` (+ `README.md`) |
| Mekanik | Model 3D **v16**: PCB sensor rev B + PCB utama F1, 0 tabrakan. Body 3D print belum masuk RAB | `mechanical/` |
| Firmware | **Belum mulai** (M0). `Pins.h` dan `platformio.ini` masih untuk ESP32-S3 lama | `firmware/` |
| Extension Mind+ | Belum mulai (M6) | `mindplus-ext/` |

### Lihat hasilnya (artifact claude.ai)

- Model 3D v16 (bisa diputar): https://claude.ai/artifact/C6BMXLgUPLJN5Aubm8uyx3
- Perbandingan opsi bentuk PCB utama: https://claude.ai/artifact/PYASQTHgLPKjVaxw33yyMZ
- Wiring diagram per blok: https://claude.ai/artifact/Enb11oGXVb5YkwQmU6DhJY
- Diagram blok sistem: https://claude.ai/artifact/VgPaH3FbRFSDaHB658YTcT
- Arsitektur sistem: https://claude.ai/artifact/9dNV7sB3TdaNBcSojbtzAa · Flowchart: https://claude.ai/artifact/EMfY1GGrPrx9etNHpKmhEi

Artifact bersifat privat. Kalau link tidak bisa dibuka, minta pemiliknya membagikan lewat menu Share. Render
gambar model juga ada di `mechanical/render/`.

## Yang harus dilakukan berikutnya

Urut dari yang paling mendesak. Batas waktu dari pedoman PjBL dan charter: desain mekanik selesai **minggu 8**,
PCB dipesan **paling lambat minggu 10**, prototipe jalan 3× berturut-turut untuk **G3 (minggu 10)**.

### 1. Keputusan kelompok (perlu dibahas dulu)

- [x] ~~Pangkas RAB Rp2.000~~: tidak perlu lagi, batas anggaran naik jadi Rp1.000.000 (26/10).
- [ ] **Ukuran PCB utama**: tetap 100 × 127 mm, atau dipadatkan (OLED ditumpuk di atas ESP32, hidung dipendekkan,
      resistor SMD; perkiraan 15–25 % lebih kecil). Mengganti 18650 dengan LiPo bisa membuat papan jauh lebih kecil,
      tapi bertentangan dengan alasan keselamatan di charter, jadi tanyakan dosen dulu.
- [ ] **Saklar SW1**: pad pemasangnya berjarak 0,25 mm dari pad lain (batas tempat cetak 0,254 mm). Pilihannya:
      pelanggaran ini dikecualikan di DRC, atau ganti saklar.
- [x] ~~Skid nilon~~: diganti **ball caster** (RAB 27/10). Model 3D v16 masih memakai skid, perlu diperbarui.

### 2. PCB utama (sampai siap pesan)

- [ ] Ganti footprint Q1 ke `Package_TO_SOT_THT:TO-92_Inline_Wide` di Eeschema, lalu F8 di PCB Editor. Jangan
      jalankan ulang `gen_sch_utama.py` karena UUID-nya acak dan akan mengacak penempatan.
- [ ] Rapikan jalur Q1 ↔ R3/R4/buzzer, jalur daya (BAT+ masih melintang miring di B.Cu), dan silkscreen yang bertumpuk.
- [ ] **Cocokkan footprint modul dengan modul yang dibeli** (ESP32 DevKit, TB6612, MP1584 di `hardware/ltm-lib/`).
      Ukur jarak pin modul asli pakai jangka sorong; footprint sekarang masih perkiraan.
- [ ] **Footprint ikut barang di RAB 27/10**: tombol SW2/SW3 → tactile 12×12 mm (sekarang `SW_PUSH_6mm`), konektor
      motor J2/J3 → JST XH 6 pin `B6B-XH-A` (sekarang JST PH 2,0). Kabel encoder N20 bawaan biasanya berkonektor
      PH 2,0, jadi ujung kabelnya perlu diganti housing XH.
- [ ] DRC 0 error → buat Gerber → pesan PCB utama **bersama PCB sensor** (ikuti `docs/aturan-cetak-pcb.md`).

### 3. Pembelian & mekanik

- [x] ~~Tautan toko~~: ada di `docs/charter.md` bagian 8 (27/10), kecuali mux WKH Electronic (menyusul).
- [ ] Koreksi spreadsheet RAB kelompok: baris mux masih modul CD74HC4067 kakarobot Rp35.000; yang dipakai IC
      CD74HC4067M SOP-24 dari WKH Electronic Rp20.000 (keputusan 27/10).
- [ ] Info printer 3D lab → body 3D print (cover, bumper, dudukan motor & baterai, sayap) masuk RAB atau tidak.
- [ ] Sinkronkan `docs/perhitungan-motor.md` dengan charter (≥ 0,5 m/s) dan roda Ø34.

### 4. Firmware (mulai sesudah komponen ada)

- [ ] Perbarui `firmware/lib/LineFollower/src/Pins.h` ke pin map ESP32 DevKit (tabel di `CLAUDE.md`) dan
      `platformio.ini` ke board ESP32 DevKit.
- [ ] Kerjakan milestone M0 → M7 berurutan (lihat [Progres firmware](#progres-firmware)). Tiap milestone dites di
      hardware dulu sebelum lanjut. Sementara PCB belum datang, tes di breadboard (pinjam lab).

### 5. Dokumen PjBL

- [ ] **Analisis bahaya (FMEA) ≥ 8 mode kegagalan** untuk G3 (minggu 7–8), belum ada di repo. Daftar risiko di
      charter bisa jadi titik awal.
- [ ] Logbook: konfirmasi ke pembimbing format mana yang dipakai (logbook perseorangan Lampiran C atau template
      departemen, mungkin keduanya). Isi `docs/logbook/logbook-utama.md` dengan kegiatan tim yang benar-benar
      terjadi; entri terakhir masih 02/10.
- [ ] Dokumen lama yang belum ikut rancangan terbaru: `docs/skematik-v1.md`, `docs/minsys-v1.md`,
      `docs/00-mulai-dari-sini.md` (masih ESP32-S3), `docs/gen_rab_pemeliharaan.py`.

## Rancangan singkat

| Bagian | Pilihan |
|---|---|
| MCU | ESP32 DevKit 30 pin (ESP32 biasa, CH340/CP2102), di socket di atas PCB utama |
| Sensor | 12× QRE1113GR + mux CD74HC4067 (SOIC-24) di PCB sensor bentuk jangkar, kabel JST XH 8 pin ke PCB utama |
| Driver motor | Modul TB6612FNG + motor N20 6V 500 RPM dengan encoder, roda Ø34 |
| Daya | 2× 18650 (2S) + BMS 2S + charger USB-C → buck MP1584 5 V |
| UI | OLED 0,96" I2C (bacaan sensor tampil sebagai bar), 2 tombol, buzzer aktif |
| Mekanik | Bentuk rendah gaya Ichiduino: PCB jadi sasis, body 3D print (cover, bumper, dudukan, sayap belakang) |

Arsitektur perangkat lunak 3 lapis:

1. **Library C++ `LineFollower`** (`firmware/lib/LineFollower/`): logika utama, ditulis dan dites duluan.
2. **Desain blok**: 1 blok = 1 fungsi library.
3. **Extension Mind+** (`mindplus-ext/`): blok menghasilkan kode C++ yang memanggil library, di-compile native
   sehingga loop PID tetap cepat.

## Struktur repo

```
├── CLAUDE.md        rancangan lengkap, pin map, riwayat keputusan, aturan kerja
├── firmware/        proyek PlatformIO (library LineFollower + program uji)
├── mindplus-ext/    extension Mind+
├── hardware/        KiCad: sensor-garis/ (PCB sensor rev B), pcb-utama/ (PCB utama baru), ltm-lib/ (footprint modul),
│                    tools/ (generator skematik/PCB, autoroute FreeRouting, MCP KiCad), ltm-main/ (v2 lama)
├── mechanical/      model 3D v16 (CadQuery, STEP, DXF, STL, render); v15 untuk perbandingan
├── docs/            charter, RAB, wiring diagram, diagram blok, aturan cetak PCB, logbook, log kerja
└── arsip/           file yang sudah digantikan rancangan terbaru
```

## Cara ikut mengerjakan

1. `git pull` dulu sebelum mulai, supaya dapat versi terbaru.
2. Buka file KiCad pakai **KiCad 10** (KiCad 8 tidak bisa membuka file versi ini).
3. Model 3D: buka file `.step` di `mechanical/v16/step/` (Fusion, Inventor, FreeCAD), atau lihat lewat link artifact.
4. Sesudah mengerjakan sesuatu, tulis ringkasannya di `docs/log-kerja.md` (per hari), lalu commit dengan pesan
   Bahasa Indonesia.

## Build firmware

```bash
cd firmware
pio run            # compile
pio run -t upload  # flash
pio device monitor # serial 115200
```

## Progres firmware

- [ ] M0: setup PlatformIO, serial jalan, tanda hidup lewat OLED/buzzer
- [ ] M1: driver motor + perintah serial `m <kiri> <kanan>`
- [ ] M2: baca 12 sensor mentah lewat mux, stream ke serial
- [ ] M3: kalibrasi + posisi + simpan/muat NVS
- [ ] M4: PID `follow()` + tuning lewat serial
- [ ] M5: persimpangan, tombol, buzzer, baterai + peringatan baterai lemah
- [ ] M6: extension Mind+
- [ ] M7: contoh program + panduan blok
