# PROJECT CHARTER — Robot Line Tracer Micro

Semester Gasal 2026/2027 · Revisi 3.4 (arahan dosen 05/10/2026: reverse engineering, path planning,
budget maksimal Rp 900.000; arahan 09/10/2026: tanpa IMU; arahan 26/10/2026: path planning dengan peta yang ditentukan di awal) · diperbarui 22/10/2026: 12 QRE1113GR (toko lokal), PCB sensor bentuk jangkar

## 1. Project Identity

| | |
|---|---|
| Nama | Robot Line Tracer Micro |
| Short Description | Robot line tracer edukasi untuk anak sekolah, hasil reverse engineering kit Ichiduino Pro, yang mampu mengikuti garis secara otomatis dan menjalankan path planning pada lintasan grid yang petanya ditentukan di awal (pre-defined map by index). Berbasis ESP32, dapat diprogram dengan block coding berbasis web, dan dibangun dengan anggaran maksimal Rp 900.000. |
| Supervisor | Fira Aulia, S.Tr.T, M.Tr.T |

| No | Nama | NRP | Peran |
|---|---|---|---|
| 1 | Mararevi Subagyo | 2040241036 | Project Manager, [isi peran] |
| 2 | Fernandy Raditya Wardhana | 2040241007 | [isi peran] |
| 3 | Achmad Iqbal Adiputra | 2040241121 | [isi peran] |
| 4 | Adhityanoval Dewa Mahendra | 2040241085 | [isi peran] |

Pilihan peran: Firmware, Kendali & Path Planning · Elektronik & PCB · Mekanik & Pengujian ·
Platform Web, RAB & Dokumentasi.

## 2. Business Reasons for Project

Robot line tracer edukasi di pasaran lokal, seperti Ichiduino Pro, dijual sekitar Rp 2.000.000 per kit
lengkap dengan unit kontrol (Ultimate 5 Max) seharga Rp 825.000, dan ditujukan untuk kompetisi.
Harga dan fiturnya (kecepatan tinggi, baterai LiPo 2S) kurang sesuai sebagai media belajar anak sekolah.

Proyek ini melakukan reverse engineering terhadap Ichiduino Pro: fungsi dan arsitekturnya dianalisis,
lalu dirancang ulang dari nol dengan anggaran maksimal Rp 900.000. Fitur yang dipertahankan, diganti,
atau ditiadakan dipilih berdasarkan kebutuhan edukasi dan batas anggaran. Selain mengikuti garis,
robot memiliki kemampuan path planning dengan peta lintasan yang ditentukan di awal (pre-defined map
by index): setiap persimpangan grid diberi nomor indeks, lalu rute disusun sebagai aksi per indeks atau
dihitung otomatis sebagai rute terpendek menuju titik tujuan, sehingga siswa dapat belajar konsep
algoritma dan navigasi melalui block coding berbasis web tanpa instalasi aplikasi.

## 3. Project Objectives / Purposes

1. Melakukan reverse engineering kit Ichiduino Pro dan merancang ulang robot line tracer edukasi
   berbasis ESP32 dengan anggaran maksimal Rp 900.000.
2. Membuat robot yang mampu mengikuti garis hitam di atas putih secara otomatis dengan kendali PID,
   dengan akurasi pembacaan posisi garis ≤ 2 mm dan kecepatan rata-rata ≥ 0,5 m/s.
3. Menerapkan path planning dengan peta lintasan yang ditentukan di awal (pre-defined map by index):
   setiap persimpangan grid diberi nomor indeks, robot menghitung persimpangan yang dilewati dan menjalankan
   aksi tiap indeks (belok kiri, belok kanan, lurus, berhenti), baik dari rute yang disusun pengguna maupun
   rute terpendek yang dihitung otomatis dari peta.
4. Menerapkan fitur keamanan berupa berhenti ≤ 500 ms setelah garis tidak terdeteksi dan pemutusan
   saat tegangan baterai < 3,2 V per sel.
5. Mengembangkan platform block coding berbasis web (Blockly), termasuk blok aksi per indeks dan blok rute
   terpendek menuju titik tujuan.
6. Menguji performa, keterulangan gerak, dan path planning robot, serta melakukan uji coba kepada
   siswa sekolah.

## 4. Project Scope

**Yang dikerjakan:**

- Reverse engineering kit Ichiduino Pro (analisis fungsi, arsitektur, dan spesifikasi)
- Robot line tracer edukasi berbasis ESP32, dirancang dari nol
- Elektronik: 12 sensor garis QRE1113GR (PCB sensor bentuk jangkar) + multiplexer, motor DC + encoder, driver motor, OLED, catu daya baterai 2S (2× 18650)
- Firmware: baca sensor, kalibrasi, kendali PID, deteksi persimpangan, fitur keamanan
- Path planning: peta grid yang ditentukan di awal (indeks persimpangan), rute berupa aksi per indeks atau
  rute terpendek otomatis ke titik tujuan
- Platform block coding berbasis web (Blockly)
- Prototipe sampai desain PCB yang siap diproduksi
- Uji performa robot, uji path planning, dan uji coba ke pengguna (anak sekolah)

**Yang TIDAK dikerjakan:**

- Produksi massal dan penjualan (baru rencana bisnis)
- Lintasan selain garis hitam di atas putih
- Path planning pada persimpangan dengan sudut cabang selain 90° (peta lintasan berbentuk grid; garis yang berbelok dan melengkung tetap dapat diikuti)
- Pemetaan lintasan secara otonom (robot menjelajah sendiri); peta ditentukan di awal sesuai arahan dosen
  26/10/2026
- Penghindaran halangan / obstacle avoidance (bukan kebutuhan line tracer)
- Upload program lewat Bluetooth dan dukungan iPad/Safari (jadi pengembangan lanjutan)
- Fitur lomba, seperti kecepatan tinggi dan kipas penyedot
- Modifikasi kit Ichiduino Pro (kit hanya dianalisis dan diukur sebagai pembanding)

## 5. Key Project Deliverables

| Nama | Deskripsi |
|---|---|
| Analisis Reverse Engineering | Tabel analisis fungsi, arsitektur, dan spesifikasi Ichiduino Pro beserta keputusan fitur yang dipertahankan, diganti, atau ditiadakan |
| Prototipe | Robot Line Tracer Micro yang dapat mengikuti garis dan menjalankan path planning |
| Desain PCB | File skematik dan layout PCB (papan utama dan papan sensor) yang siap diproduksi |
| Firmware | Program pembacaan sensor, kendali PID, deteksi persimpangan, path planning, dan fitur keamanan |
| Platform Block Coding | Aplikasi web berbasis Blockly untuk memprogram robot tanpa menulis kode |
| Lintasan Uji | Lintasan garis lurus dan lintasan grid 4 × 4 persimpangan |
| Data Pengujian | Hasil uji seluruh sasaran dan uji coba kepada siswa |
| Dokumentasi | Dokumentasi kegiatan kelompok minggu 4–16 selama proses pengerjaan proyek PJBL |
| Laporan Mingguan | Laporan mingguan berisi aktivitas, perkembangan, dan kendala selama proses PJBL |
| Laporan Akhir & Manual | Laporan menyeluruh mengenai proses, solusi, dan hasil PJBL, beserta manual pengguna |

## 6. Project's Criteria for Success

Lintasan uji path planning berupa grid garis 4 × 4 titik persimpangan (indeks 1–16) dengan jarak antar titik 30 cm.

1. **Akurasi pembacaan posisi garis ≤ 2 mm.** Diuji dengan meletakkan robot dalam keadaan diam (motor mati) pada posisi geser −20 s.d. +20 mm (tiap 5 mm) dari tengah garis, lalu posisi yang terbaca sensor dibandingkan dengan posisi sebenarnya, 3 kali ulangan. Alat ukur: kertas milimeter dan jangka sorong.
2. **Kecepatan rata-rata robot ≥ 0,5 m/s.** Dihitung dari panjang lintasan dibagi waktu tempuh, 3 kali ulangan. Alat ukur: meteran dan stopwatch/video.
3. **Keterulangan waktu tempuh dengan simpangan baku ≤ 5%.** Robot dijalankan 10 putaran pada lintasan dan kondisi baterai yang sama. Alat ukur: stopwatch/timer firmware.
4. **Deteksi persimpangan benar ≥ 95%.** Robot melewati minimal 40 persimpangan, lalu catatan deteksi robot dibandingkan dengan jumlah persimpangan sebenarnya. Alat ukur: log serial dan video.
5. **Path planning dengan peta indeks benar pada 10 dari 10 percobaan.** Diuji pada 10 pasang titik awal dan tujuan yang berbeda; robot harus menjalankan seluruh aksi indeks tanpa salah belok, dan rute yang dihitung otomatis dibandingkan dengan rute terpendek hasil hitung manual. Alat ukur: log serial dan video.
6. **Ketepatan berhenti di titik tujuan dengan error ≤ 30 mm.** Jarak pusat robot ke titik tujuan diukur setelah robot berhenti, pada 10 rute di poin 5. Alat ukur: penggaris/meteran.
7. **Robot berhenti ≤ 500 ms setelah garis tidak terdeteksi.** Garis diputus, lalu waktu dihitung dari rekaman video slow-motion, 3 kali ulangan. Alat ukur: video HP 240 fps.
8. **Motor mati saat tegangan baterai < 3,2 V per sel.** Baterai diganti power supply, lalu tegangan diturunkan perlahan dan dicatat saat motor mati, 3 kali ulangan. Alat ukur: power supply dan multimeter.
9. **Total biaya proyek ≤ Rp 900.000.** Dihitung dari jumlah RAB, dan setiap harga disertai tautan toko. Alat ukur: daftar harga.
10. **Seluruh proses dan hasil pengujian terdokumentasi** dalam laporan mingguan dan laporan akhir PJBL.

## 7. Milestone Dates

| No | Milestones / Major Events | Due Dates |
|---|---|---|
| 1 | Lembar telaah, Project Charter, dan sasaran terukur (G1 Penetapan) | Minggu 1–2 |
| 2 | Reverse engineering Ichiduino Pro, WBS, jadwal, RAB, rumusan optimasi | Minggu 3–5 |
| 3 | Rancangan teknis: arsitektur, wiring, flowchart, skematik, algoritma path planning, pustaka (G2 Rancangan) | Minggu 3–6 |
| 4 | Analisis bahaya (≥ 8 mode kegagalan) | Minggu 7–8 |
| 5 | Prototipe mengikuti garis + deteksi persimpangan, data awal 3 ulangan, demo progres (G3 Realisasi Awal) | Minggu 7–10 |
| 6 | Path planning, PCB, platform block coding, pengujian seluruh sasaran, uji coba siswa (G4 Pembuktian) | Minggu 11–14 |
| 7 | Laporan akhir, manual, serah terima, demo akhir (G5 Serah Terima) | Minggu 15–16 |

**Risiko terbesar:** pembacaan sensor garis terganggu cahaya ruangan dan kondisi permukaan lintasan,
sehingga posisi garis dan persimpangan tidak terbaca akurat.

| No | Risiko | Dampak | Penanganan |
|---|---|---|---|
| R1 | Sensor garis terganggu cahaya ruangan / permukaan lintasan | Akurasi posisi dan deteksi persimpangan gagal | Kalibrasi hitam-putih tiap dinyalakan; sensor QRE1113GR (LED IR + fototransistor dalam satu kemasan bersekat) dipasang rendah, muka sensor ±3 mm dari lantai; pelindung cahaya 3D print ditambah kalau uji di ruangan terang gagal |
| R2 | Persimpangan terlewat atau terdeteksi ganda | Rute dan titik berhenti salah | Konfirmasi deteksi dengan jarak tempuh encoder |
| R3 | Belokan 90° di persimpangan tidak presisi | Rute dan titik berhenti salah | Belok berbasis encoder, lalu dikunci kembali ke garis oleh sensor |
| R4 | PID tidak stabil saat kecepatan/tegangan baterai berubah | Kecepatan dan keterulangan gagal | Tuning lewat serial, kompensasi tegangan baterai |
| R5 | PCB salah desain atau terlambat datang | Jadwal G3–G4 mundur | Prototipe breadboard dulu, pesan PCB paling lambat minggu 10 |
| R6 | Biaya melebihi Rp 900.000 | Sasaran biaya gagal | RAB dipantau tiap pembelian |
| R7 | Baterai Li-ion overcharge / overdischarge / korsleting | Bahaya keselamatan | BMS 2S, cutoff firmware, ruang baterai tertutup |
| R8 | QRE1113GR mahal (Rp15.000/pcs di toko lokal) sehingga dibeli 12 tanpa cadangan; sensor rusak saat disolder atau barang palsu | Satu titik sensor mati, posisi garis kurang presisi | Cek tanda pin 1 dan uji tiap sensor di breadboard (LED IR dilihat lewat kamera HP) sebelum disolder; kalau ada yang rusak, beli satuan di toko yang sama |

## 8. Budget Summary

Harga perkiraan; wajib dicek ulang dan disertai tautan toko. Kit Ichiduino Pro tidak dianggarkan ulang.

### Electrical

| Item | Price per unit | Qty | Unit | Total Price |
|---|---|---|---|---|
| ESP32 DevKit WiFi Bluetooth CH340 Type-C | Rp76.000 | 1 | pcs | Rp76.000 |
| OLED 0.96" 128×64 I2C | Rp33.000 | 1 | pcs | Rp33.000 |
| Sensor reflektif QRE1113GR SMD, toko lokal (tanpa cadangan) | Rp15.000 | 12 | pcs | Rp180.000 |
| IC multiplexer analog CD74HC4067 SOIC-24, 16 kanal (dipakai 12) | Rp35.000 | 1 | pcs | Rp35.000 |
| Modul driver motor TB6612FNG | Rp25.000 | 1 | pcs | Rp25.000 |
| Motor N20 6V 500 RPM + encoder | Rp55.000 | 2 | pcs | Rp110.000 |
| Push button | Rp1.000 | 4 | pcs | Rp4.000 |
| Resistor SMD 0805 (220 Ω dan 10 kΩ untuk PCB sensor) | Rp100 | 30 | pcs | Rp3.000 |
| Resistor 10 kΩ | Rp200 | 10 | pcs | Rp2.000 |
| Buzzer | Rp3.000 | 1 | pcs | Rp3.000 |
| Baterai Li-ion 18650 | Rp40.000 | 2 | pcs | Rp80.000 |
| Holder baterai 2× 18650 (seri) | Rp8.000 | 1 | pcs | Rp8.000 |
| Modul BMS 2S | Rp10.000 | 1 | pcs | Rp10.000 |
| Modul charger 2S USB-C | Rp25.000 | 1 | pcs | Rp25.000 |
| Modul buck converter 5 V (MP1584) | Rp10.000 | 1 | pcs | Rp10.000 |
| Saklar on/off | Rp3.000 | 1 | pcs | Rp3.000 |
| Konektor JST PH2.0 6 pin + header (motor encoder) | Rp5.000 | 2 | set | Rp10.000 |
| Komponen pendukung (header & socket female, kapasitor, dioda 1N5819) | Rp25.000 | 1 | paket | Rp25.000 |
| Konektor JST XH 2,5 mm 8 pin (2 header + 2 housing + terminal) + kabel, perkiraan | Rp5.000 | 1 | set | Rp5.000 |
| Fabrikasi PCB (papan utama + papan sensor) + ongkir | Rp200.000 | 1 | paket | Rp200.000 |
| **TOTAL** | | | | **Rp847.000** |

### Mechanical

| Item | Price per unit | Qty | Unit | Total Price |
|---|---|---|---|---|
| Roda N20 Ø34 mm | Rp25.000 | 1 | pasang | Rp25.000 |
| Bracket motor N20 | Rp10.000 | 1 | pasang | Rp10.000 |
| Skid nilon (pengganti ball caster; baut M2/M3, spacer, mur nilon) | Rp5.000 | 1 | paket | Rp5.000 |
| Baut, mur, spacer | Rp15.000 | 1 | paket | Rp15.000 |
| **TOTAL** | | | | **Rp55.000** |

**TOTAL BUDGET: Rp902.000** (Electrical Rp847.000 + Mechanical Rp55.000), **lewat Rp2.000 dari batas Rp900.000**
(perlu dipangkas sebelum pitching RAB). Lintasan uji disediakan di luar RAB; breadboard + kabel jumper dan timah
solder + flux dipinjam dari lab (tidak masuk RAB sejak 22/10/2026). Revisi 13/10/2026: 16 sensor +
multiplexer + LED indikator (+Rp63.000). Revisi 15/10/2026: sensor jadi 12 TCRT5000, LED IR selalu nyala tanpa MOSFET (−Rp16.500).
Revisi 20/10/2026: sensor jadi 12 pasang LED merah + fototransistor SMD 1206, MCP23017 + LED indikator dihapus
(bacaan sensor tampil di OLED), OLED 0,96", skid nilon pengganti ball caster (−Rp20.000). Revisi kedua 20/10/2026:
sensor jadi 12 QRE1113GR, PCB sensor bentuk sayap gaya JSumo XLINE (+Rp7.500). Revisi 21/10/2026: multiplexer
berupa IC CD74HC4067 SOIC-24 yang disolder langsung di PCB sensor, bukan modul (lebih hemat tempat, +Rp20.000);
tempat cetak sanggup jalur 0,3 mm. Revisi 22/10/2026: PCB sensor bentuk jangkar (rev B); QRE1113GR ternyata ada di
toko lokal dengan harga Rp15.000/pcs (sebelumnya perkiraan impor Rp5.000), jadi dibeli 12 tanpa cadangan
(+Rp105.000); kabel pita IDC diganti konektor JST XH 8 pin (−Rp5.000, perkiraan); breadboard dan timah dipinjam
dari lab (−Rp85.000).

### Alasan pemilihan komponen utama

- **ESP32 DevKit** (Rp76.000): prosesor 240 MHz dual-core dengan WiFi/Bluetooth, jauh lebih murah dari
  ESP32-S3 (> Rp130.000). 12 sensor garis dibaca bergantian lewat multiplexer CD74HC4067 ke satu kanal
  ADC1 (GPIO36), tegangan baterai ke kanal ADC1 lain (GPIO39).
- **12 sensor garis QRE1113GR pada PCB bentuk jangkar (jarak antar sensor 8 mm di busur, lebar baca
  ± 83 mm)**: 6 sensor tengah hampir lurus (posisi presisi dan deteksi persimpangan), lalu lengan melengkung
  ke belakang sampai sensor terluar mundur ± 11,6 mm, sehingga belokan tajam terlihat lebih awal. Jarak 8 mm
  dipilih untuk garis lomba 2 cm (IARC XII): kedua tepi garis bergantian melewati sensor, bacaan posisi halus.
  QRE1113GR berisi LED IR dan
  fototransistor dalam satu kemasan SMD kecil (2,9 × 3,6 mm) yang sudah bersekat, jadi PCB sensor tipis dan
  rendah (muka sensor ± 3 mm dari lantai) seperti kit pembanding, dan tidak perlu menata pasangan LED +
  fototransistor sendiri. Multiplexer membuat 12 sensor cukup memakai 5 pin ESP32 (1 ADC + 4 pemilih kanal). Bacaan 12 sensor
  ditampilkan sebagai bar di OLED, menggantikan LED indikator + MCP23017 (lebih murah dan PCB sensor lebih
  sederhana). Tangkai PCB sensor dibaut ke bawah PCB utama dengan 2 spacer nilon dan disambung kabel JST XH
  8 pin pendek.
- **Motor N20 6V 500 RPM + encoder, roda Ø34 mm**: kecepatan maksimum teoritis ± 0,89 m/s, cukup untuk
  sasaran ≥ 0,5 m/s dengan cadangan; roda kecil membuat robot rendah dan ringkas. Torsi desain
  (massa 0,3 kg, akselerasi 1,8 m/s², safety factor 2) ± 9 N·mm ≈ 0,09 kg·cm per roda. Encoder dibutuhkan
  untuk membaca kecepatan roda (CPMK-1) dan belokan 90° yang presisi untuk path planning: sudut belok
  dihitung dari selisih putaran roda kiri dan kanan, lalu robot dikunci kembali ke garis oleh sensor
  (tanpa IMU, sesuai arahan dosen 09/10/2026). PWM dibatasi ± 70% agar motor 6V tidak kelebihan
  tegangan dari baterai 2S.
- **TB6612FNG**: penurunan tegangan jauh lebih kecil daripada L298N, sehingga motor mendapat tenaga
  penuh dari baterai 2S dan driver tidak panas.
- **Baterai 2× 18650 (2S) + BMS + charger USB-C**: 7,4 V cukup untuk motor dan buck 5 V; kapasitas besar
  (± 3 jam pemakaian), arus maksimum tinggi, dan tidak mungkin tertukar dengan baterai AA; holder dipasang
  melintang di atas PCB utama; dilindungi BMS dan diisi lewat USB-C.

## Persetujuan

Ditandatangani Pengawas PJBL (Fira Aulia, S.Tr.T, M.Tr.T), Manajer Proyek (Mararevi Subagyo), dan
seluruh anggota (Fernandy Raditya Wardhana, Achmad Iqbal Adiputra, Adhityanoval Dewa Mahendra).
