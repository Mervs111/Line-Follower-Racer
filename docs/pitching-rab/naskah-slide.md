# Naskah slide Pitching RAB (27/10/2026)

Pitching RAB untuk minta dana ke dosen/departemen, 10–15 menit, 15 slide utama + 2 lampiran (±50 detik per
slide). Semua angka diambil dari `docs/charter.md` (rev 3.4, 22/10/2026) dan file desain di repo per 26/10/2026; RAB diperbarui 27/10/2026 dengan harga
hasil validasi di marketplace online.
Isi ini dipindah ke template kelompok setelah templatenya ada.

Gambar: `docs/pitching-rab/gambar/` (render PCB terbaru dari KiCad 10, 26/10), `mechanical/render/ltm-v16-*.png`,
`docs/diagram-blok.png`, `docs/diagram-blok-kendali.png`. **Jangan pakai `hardware/render/`**: itu PCB versi lama
(16 sensor + MCP23017).

---

## 1. Judul

**Robot Line Tracer Micro**
Robot edukasi pengikut garis dengan path planning, dibuat ulang dari nol dengan anggaran ≤ Rp1.000.000

Pitching RAB · PjBL Semester 5 Proyek 3 · P01 Kel.5 · DTEO FV ITS · Pembimbing: Fira Aulia, S.Tr.T, M.Tr.T · 27/10/2026

Gambar: `mechanical/render/ltm-v16-iso.png`

## 2. Tim

| Nama | NRP | Peran |
|---|---|---|
| Mararevi Subagyo | 2040241036 | Project Manager, [isi] |
| Fernandy Raditya Wardhana | 2040241007 | [isi] |
| Achmad Iqbal Adiputra | 2040241121 | [isi] |
| Adhityanoval Dewa Mahendra | 2040241085 | [isi] |

Pilihan peran di charter: Firmware, Kendali & Path Planning · Elektronik & PCB · Mekanik & Pengujian · Platform Web,
RAB & Dokumentasi.

## 3. Masalah

- Kit line tracer edukasi di pasaran mahal: **Ichiduino Pro ± Rp2.000.000 per kit**, unit kontrolnya saja Rp825.000.
- Kit dirancang untuk kompetisi (motor 1200 RPM, LiPo 2S kecil), kurang pas sebagai media belajar anak sekolah.
- Arahan dosen (05/10/2026): reverse engineering produk contoh, buat ulang dengan **budget maks Rp1.000.000** (naik dari Rp900.000 pada 26/10), minimal
  **mengikuti garis otomatis + path planning**.

Catatan bicara: buka dengan harga kit, lalu arahan dosen sebagai batas proyek.

## 4. Solusi dan tujuan

**Robot Line Tracer Micro**: hasil reverse engineering Ichiduino Pro, dirancang ulang dari nol.

- Mengikuti garis hitam otomatis dengan kendali **PID**, 12 sensor garis.
- **Path planning** dengan peta yang ditentukan di awal (pre-defined map by index, usulan Bu Fira 26/10): rute ditulis
  sebagai urutan indeks (pola sensor → aksi → ikuti garis), dan di grid urutannya bisa dibuat otomatis dari rute terpendek.
- **Block coding berbasis web (Blockly)**: siswa memprogram tanpa instalasi aplikasi.
- **Aman**: BMS baterai, motor mati di bawah 3,2 V per sel, berhenti ≤ 500 ms kalau garis hilang.
- **Rp937.390**, sekitar 47% harga kit pembanding.

Target uji lapangan: lomba **IARC XII Smart Robotics** (9–10/01/2027, arena grid, garis hitam 2 cm).

## 5. Reverse engineering: Ichiduino Pro vs Line Tracer Micro

| Aspek | Ichiduino Pro (pembanding) | Line Tracer Micro | Keputusan |
|---|---|---|---|
| Harga | ± Rp1.999.999 | **Rp937.390** | 53% lebih murah |
| Otak | ATmega2560 | ESP32 240 MHz dual-core, WiFi/Bluetooth | diganti |
| Sensor garis | 12 sensor optik | 12 QRE1113GR + multiplexer | dipertahankan (12) |
| Layar | OLED 0,96" | OLED 0,96" (bacaan sensor tampil sebagai bar) | dipertahankan |
| Baterai | LiPo 2S 400 mAh | 2× 18650 (2S) + BMS + charger USB-C, ± 3 jam | diganti (lebih aman, lebih awet) |
| Motor | DC 16 mm 12 V 1200 RPM | N20 6 V 500 RPM **+ encoder** | diganti (belok 90° presisi untuk path planning) |
| Pemrograman | mBlock, Arduino IDE | Blockly web, Arduino | diganti (tanpa instalasi) |
| Path planning | per indeks lewat mBlock, aksi berbasis waktu (ms) | per indeks + encoder + rute terpendek otomatis di grid | dikembangkan |
| Servo, kipas | 2 port servo, 1 port kipas | tidak ada | ditiadakan (fitur lomba) |
| Ukuran | 12,5 × 14,3 × 5,5 cm | 11,6 × 16,5 × 6,2 cm | setara |

Catatan bicara: kinerja nyata kit (kecepatan, akurasi, daya tahan) akan diukur di lintasan uji yang sama dengan robot kami.

## 6. Sasaran terukur (dari charter)

| Sasaran | Target | Cara uji |
|---|---|---|
| Akurasi posisi garis | ≤ 2 mm | robot diam, digeser −20…+20 mm, 3 ulangan |
| Kecepatan rata-rata | ≥ 0,5 m/s | panjang lintasan / waktu, 3 ulangan |
| Keterulangan waktu tempuh | simpangan baku ≤ 5% | 10 putaran |
| Deteksi persimpangan | ≥ 95% | ≥ 40 persimpangan |
| Path planning (peta indeks) | rute dijalankan benar 10/10 | 10 pasang titik awal–tujuan |
| Ketepatan berhenti | error ≤ 30 mm | 10 rute |
| Berhenti saat garis hilang | ≤ 500 ms | video 240 fps, 3 ulangan |
| Cutoff baterai | < 3,2 V/sel | power supply, 3 ulangan |
| Total biaya | ≤ Rp1.000.000 | RAB + tautan toko |

## 7. Arsitektur sistem

Gambar: `docs/diagram-blok.png`

- 12 QRE1113GR → multiplexer CD74HC4067 → ESP32: cukup **5 pin** (1 ADC + 4 pemilih kanal).
- ESP32 → driver TB6612FNG → 2 motor N20; encoder kembali ke ESP32.
- Daya: 2× 18650 → BMS 2S → saklar → buck 5 V (MP1584) → ESP32 dan sensor; motor langsung dari baterai.
- Antarmuka: OLED 0,96", 2 tombol, buzzer, pembaca tegangan baterai.
- Program dari platform Blockly lewat Wi-Fi atau USB-C; log pengujian disimpan.

## 8. Kendali dan path planning

Gambar: `docs/diagram-blok-kendali.png`

- Loop tertutup: posisi garis dari sensor → PID → kecepatan motor kiri/kanan; loop dalam dari encoder.
- Peta ditentukan di awal (pre-defined map by index, usulan Bu Fira 26/10), seperti blok path planning Ichiduino di
  mBlock: rute ditulis sebagai urutan **indeks = langkah**. Tiap indeks: pola sensor pemicu (mis. persimpangan kiri,
  OR/XOR, atau langsung) → aksi (maju, belok kiri, belok kanan, kecepatan motor kiri/kanan) → ikuti garis hitam/putih
  dengan kecepatan tertentu sampai indeks berikutnya. Robot tidak menjelajah.
- Contoh di grid 4 × 4 (jarak 30 cm), rute S → T: indeks 1 kiri, 2 kanan, 3 kiri, 4 kanan, 5 kiri, 6 berhenti.
- Bedanya dengan kit: aksi diukur encoder (jarak, sudut 90°), bukan waktu ms, jadi tidak tergantung tegangan baterai;
  di lintasan grid urutan indeks bisa dibuat otomatis dari rute terpendek (BFS).

## 9. Rancangan PCB (2 papan)

Gambar: `gambar/pcb-sensor-bawah.png` dan `gambar/pcb-utama-atas.png` (atau `pcb-utama-iso.png`)

| | PCB sensor (rev B) | PCB utama |
|---|---|---|
| Ukuran | 95 × 51 mm, bentuk jangkar | 100 × 127 mm, bentuk "mobil F1" |
| Isi | 12 QRE1113GR jarak 8 mm di busur, mux SOIC-24, JST XH 8 pin | ESP32 DevKit, TB6612, buck 5 V, OLED, tombol, buzzer, konektor motor & baterai (21 komponen) |
| Status | **DRC 0 error, siap cetak** | skematik ERC 0, routing selesai (0 jalur putus); sisa 11 error DRC dari 2 footprint (Q1, SW1) sebelum cetak |

Catatan bicara: jarak sensor 8 mm dipilih untuk garis lomba 2 cm (kedua tepi garis bergantian melewati sensor). Aturan
cetak mengikuti tempat cetak (jalur min 0,3 mm). Keduanya dibuat di KiCad 10.

## 10. Rancangan mekanik

Gambar: `mechanical/render/ltm-v16-iso.png`, `ltm-v16-samping.png`, `ltm-v16-atas.png`

- Ukuran ± 116 × 165 × 62 mm, bentuk rendah seperti kit pembanding: PCB jadi sasis, semua komponen dan baterai di atas.
- PCB sensor dibaut di bawah hidung PCB utama, muka sensor ± 3 mm dari lantai.
- Body 3D print (cover, bumper, dudukan motor & baterai, sayap belakang): **belum masuk RAB**, menunggu info printer lab.

## 11. Simulasi (syarat pitching dari dosen)

Gambar kiri: `simulasi/hasil/uji2d_slide.png` (lintasan simulasi 2D, indeks 1–5, berhenti di T). **Ganti dengan
tangkapan layar CoppeliaSim** (dan perbarui angka) setelah `simulasi/coppeliasim/run_sim.py` dijalankan di laptop.

- Model robot ukuran asli dibangun otomatis di CoppeliaSim dari skrip Python: roda Ø34 jarak 91 mm, N20 500 RPM,
  12 sensor di posisi PCB rev B.
- Arena grid 30 cm, garis hitam 2 cm. Logika sama dengan firmware: PID + path planning per indeks, belok diukur encoder.
- Hasil uji logika kendali (simulasi 2D): rute contoh S → T 8,2 s, berhenti 9 mm dari T; kecepatan 0,3–0,7 m/s ×
  5 variasi derau 25/25 lulus; rute terpendek otomatis lulus, juga saat simpul terhalang kubus.

## 12. RAB ringkas: Rp937.390

Grafik batang/donat per kelompok:

| Kelompok | Isi | Biaya | Porsi |
|---|---|---|---|
| PCB & konektor | fabrikasi 2 PCB + ongkir Rp200.000, konektor JST XH, komponen pendukung | Rp240.000 | 25,6% |
| Sensor garis | 12 QRE1113GR Rp180.000, mux Rp20.000, resistor SMD | Rp203.000 | 21,7% |
| Penggerak | 2 motor N20 + encoder Rp110.000, TB6612 Rp50.000, roda | Rp185.000 | 19,7% |
| Daya | 2× 18650 Rp94.990, holder, BMS, charger USB-C, buck, saklar | Rp150.990 | 16,1% |
| Otak & antarmuka | ESP32 Rp65.900, OLED Rp36.500, tombol, buzzer | Rp108.400 | 11,6% |
| Mekanik & timah | ball caster, baut/mur/spacer, timah solder + flux | Rp50.000 | 5,3% |
| **Total** | Electrical Rp862.390 + Mechanical Rp50.000 + Lain-lain Rp25.000 | **Rp937.390** | |

Harga sudah divalidasi di marketplace online (27/10/2026); tautan toko di `docs/charter.md` bagian 8.
Di luar RAB: lintasan uji, breadboard (pinjam lab), software (Blockly, Arduino-ESP32, KiCad: gratis).
Kit Ichiduino Pro tidak dianggarkan ulang.

## 13. Alasan komponen utama

| Komponen | Harga | Alasan |
|---|---|---|
| ESP32 DevKit | Rp65.900 | 240 MHz dual-core + WiFi untuk Blockly; ESP32-S3 > Rp130.000 |
| 12× QRE1113GR | Rp180.000 | LED IR + fototransistor satu kemasan bersekat (2,9 × 3,6 mm): papan tipis, sensor rendah ± 3 mm, tidak perlu menata pasangan LED sendiri |
| Motor N20 + encoder | Rp110.000 | v maks teoritis 0,89 m/s (sasaran ≥ 0,5 m/s); encoder untuk belok 90° dan jarak tempuh |
| TB6612FNG | Rp50.000 | tegangan jatuh jauh lebih kecil dari L298N, tidak panas |
| 2× 18650 + BMS + charger | Rp129.990 | ± 3 jam pemakaian, dilindungi BMS, diisi lewat USB-C |
| Fabrikasi PCB | Rp200.000 | 2 papan custom, menggantikan kabel-kabel breadboard (rapi, awet untuk siswa) |

## 14. Riwayat RAB dan efisiensi

Grafik garis total RAB per revisi + garis batas Rp1.000.000:

| Revisi | Total | Perubahan utama |
|---|---|---|
| 3.2 (08/10) | Rp845.000 | rancangan awal (ESP32 biasa, bukan S3) |
| 3.3 (08/10) | Rp858.000 | — |
| 3.4 (09/10) | Rp833.000 | IMU dihapus (arahan dosen) |
| 13/10 | Rp896.000 | 16 sensor + mux + LED indikator (+Rp63.000) |
| 15/10 | Rp879.500 | 12 sensor, LED IR tanpa MOSFET (−Rp16.500) |
| 20/10 | Rp859.500 | MCP23017 + LED indikator dihapus, bacaan di OLED, skid nilon (−Rp20.000) |
| 20/10 | Rp867.000 | sensor QRE1113GR (+Rp7.500) |
| 21/10 | Rp887.000 | mux berupa IC SOIC-24 di PCB (+Rp20.000) |
| 22/10 | Rp902.000 | QRE harga lokal Rp15.000/pcs (+Rp105.000); breadboard + timah pinjam lab (−Rp85.000); JST XH (−Rp5.000) |
| 26/10 | Rp887.000 | mux CD74HC4067M SOP-24 harga toko WKH Electronic Rp20.000, 1 pcs tanpa cadangan (−Rp15.000) |
| 27/10 | **Rp937.390** | harga hasil validasi marketplace: TB6612FNG +Rp25.000, timah + flux masuk RAB +Rp25.000, baterai +Rp14.990, OLED +Rp3.500, ESP32 −Rp10.100, bracket motor dihapus (dudukan 3D print) −Rp10.000, ball caster ganti skid +Rp5.000, resistor THT masuk komponen pendukung −Rp2.000, push button 3 pcs −Rp1.000 (+Rp50.390) |

**Sisa Rp62.610 (6,3%)** dari batas Rp1.000.000 (batas naik dari Rp900.000 pada 26/10/2026). Kenaikan terbesar
dari harga QRE1113GR lokal yang ternyata 3× perkiraan awal, lalu harga marketplace 27/10 (+Rp50.390); sisa anggaran
bisa menutup kenaikan harga atau item yang belum di RAB (body 3D print).

## 15. Jadwal, risiko, dan penutup

| Tahap | Waktu | Status |
|---|---|---|
| G1 Penetapan (charter, sasaran) | minggu 1–2 | **lulus** (02/10/2026) |
| G2 Rancangan (RAB, diagram, PCB, mekanik) | minggu 3–6 | rancangan selesai, RAB dipitching hari ini |
| Analisis bahaya (FMEA ≥ 8 mode kegagalan) | minggu 7–8 | |
| G3 Realisasi awal: prototipe jalan 3× berturut-turut, PCB dipesan | ≤ minggu 10 | |
| G4 Pembuktian semua sasaran + uji coba siswa | minggu 11–14 | |
| G5 Serah terima (laporan, manual, demo) | minggu 15–16 | |

Risiko yang berkaitan dengan dana: PCB salah desain/terlambat (prototipe breadboard dulu, pesan PCB ≤ minggu 10);
biaya melebihi batas (RAB dipantau tiap pembelian); QRE tanpa cadangan (uji tiap sensor di breadboard sebelum disolder).

Penutup: **mohon persetujuan dana Rp937.390** untuk pembelian komponen dan fabrikasi PCB. Sesudah dana cair: beli
komponen → uji di breadboard → pesan PCB → firmware → G3.

---

## Lampiran A. RAB elektrikal (Rp862.390)

| Item | Harga | Qty | Total |
|---|---|---|---|
| ESP32 DevKit WiFi Bluetooth CH340 Type-C | Rp65.900 | 1 | Rp65.900 |
| OLED 0,96" 128×64 I2C | Rp36.500 | 1 | Rp36.500 |
| Sensor reflektif QRE1113GR SMD | Rp15.000 | 12 | Rp180.000 |
| IC multiplexer CD74HC4067M SOP-24 (WKH Electronic) | Rp20.000 | 1 | Rp20.000 |
| Modul driver motor TB6612FNG | Rp50.000 | 1 | Rp50.000 |
| Motor N20 6V 500 RPM + encoder | Rp55.000 | 2 | Rp110.000 |
| Push button tactile 12×12 mm | Rp1.000 | 3 | Rp3.000 |
| Resistor SMD 0805 (220 Ω, 10 kΩ) | Rp100 | 30 | Rp3.000 |
| Buzzer aktif 12 × 9,5 mm | Rp3.000 | 1 | Rp3.000 |
| Baterai Li-ion 18650 3000 mAh (isi 2) | Rp94.990 | 1 paket | Rp94.990 |
| Holder baterai 2× 18650 | Rp8.000 | 1 | Rp8.000 |
| Modul BMS 2S | Rp10.000 | 1 | Rp10.000 |
| Modul charger 2S USB-C | Rp25.000 | 1 | Rp25.000 |
| Buck converter 5 V (MP1584) | Rp10.000 | 1 | Rp10.000 |
| Saklar on/off | Rp3.000 | 1 | Rp3.000 |
| Konektor JST XH 6 pin + header (encoder motor) | Rp5.000 | 2 set | Rp10.000 |
| Konektor JST XH 8 pin + kabel | Rp5.000 | 1 set | Rp5.000 |
| Fabrikasi PCB (2 papan) + ongkir | Rp200.000 | 1 paket | Rp200.000 |
| Komponen pendukung (header, socket, kapasitor, dioda, resistor THT) | Rp25.000 | 1 paket | Rp25.000 |

## Lampiran B. RAB mekanik (Rp50.000) dan lain-lain (Rp25.000)

| Item | Harga | Qty | Total |
|---|---|---|---|
| Roda N20 Ø34 mm | Rp25.000 | 1 pasang | Rp25.000 |
| Ball caster | Rp10.000 | 1 pcs | Rp10.000 |
| Baut, mur, spacer | Rp15.000 | 1 paket | Rp15.000 |
| Timah solder + flux (lain-lain) | Rp25.000 | 1 paket | Rp25.000 |

## Belum lengkap (cek sebelum presentasi)

- Peran tiap anggota (slide 2).
- Slide 11 Simulasi: ganti gambar 2D dengan tangkapan CoppeliaSim + angka hasilnya (lihat `simulasi/README.md`).
- **Tautan toko tiap harga** (sasaran 9 di charter): sudah ada di `docs/charter.md` bagian 8 kecuali mux WKH Electronic
  (menyusul) dan item perkiraan (fabrikasi PCB, komponen pendukung, roda, ball caster, baut, timah).
- Harga masih perkiraan untuk fabrikasi PCB, komponen pendukung, roda, ball caster, baut, dan timah; cek ulang kalau sempat.
