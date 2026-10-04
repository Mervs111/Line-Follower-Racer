# Project Charter — Robot Line Tracer Micro (revisi untuk G1)

Draf isi charter, disesuaikan dengan Lembar Telaah (ditandatangani 02/10/2026) dan
Pedoman PjBL Semester 5 (Butir 1). Bagian bertanda [ISI] diisi kelompok.

## 1. Project Identity

- Nama: Robot Line Tracer Micro
- Short description: Robot line follower edukasi berbasis ESP32 untuk pembelajaran coding siswa SD,
  dapat diprogram dengan block coding berbasis web, biaya komponen ≤ Rp 450.000 per unit.
  Dikembangkan dari nol dengan kit Ichiduino Pro sebagai acuan pembanding.
- Supervisor: Fira Aulia, S.Tr.T, M.Tr.T

| No | Nama | NRP | Peran |
|---|---|---|---|
| 1 | Mararevi Subagyo | 2040241036 | Project Manager + [ISI] |
| 2 | Fernandy Raditya Wardhana | 2040241007 | [ISI] |
| 3 | Achmad Iqbal Adiputra | 2040241121 | [ISI] |
| 4 | Adhityanoval Dewa Mahendra | 2040241085 | [ISI] |

Usulan pembagian peran: (a) Firmware & kendali, (b) Elektronik & PCB,
(c) Mekanik & pengujian, (d) Platform web, RAB & dokumentasi.

## 2. Business Reasons

Robot line follower edukasi di pasaran lokal umumnya ditujukan untuk kompetisi. Kit acuan proyek ini,
Ichiduino Pro, dijual ± Rp 2.000.000 per kit lengkap dengan unit kontrol (Ultimate 5 Max) seharga
Rp 825.000. Harga dan fiturnya (kecepatan tinggi, baterai LiPo 2S) kurang sesuai untuk siswa SD.
Kelompok merancang dari nol robot line follower edukasi ≤ Rp 450.000 per unit yang dapat diprogram
dengan block coding berbasis web tanpa instalasi. Kit Ichiduino Pro digunakan sebagai pembanding
spesifikasi dan kinerja. Proyek mengintegrasikan sensor, mikrokontroler, aktuator, kendali PID,
kinematika robot, dan pemrograman.

## 3. Project Objectives

1. Membuat prototipe robot Line Tracer Micro berbasis ESP32 sebagai media pembelajaran coding siswa SD
   yang mampu mengikuti lintasan garis hitam di atas putih secara otomatis.
2. Mengintegrasikan sensor garis, encoder motor, ESP32, driver motor, dan motor DC dalam satu sistem
   dengan biaya komponen ≤ Rp 450.000 per unit.
3. Membuat firmware pembacaan sensor, kalibrasi, dan kendali PID dengan akurasi pembacaan posisi garis
   ≤ 2 mm dan kecepatan rata-rata ≥ 0,5 m/s.
4. Menerapkan fitur keamanan: berhenti ≤ 500 ms setelah garis tidak terdeteksi dan pemutusan saat
   tegangan baterai < 3,2 V per sel.
5. Mengembangkan platform block coding berbasis web (Blockly) agar robot dapat diprogram tanpa menulis kode.
6. Menguji performa dan keterulangan gerak robot serta melakukan uji coba kepada siswa SD.

## 4. Project Scope

Dikerjakan (seluruhnya dikembangkan sendiri, bukan modifikasi kit):
1. Perancangan robot berbasis ESP32 dari prototipe sampai desain PCB siap produksi.
2. Sistem elektronik: ESP32, sensor garis, motor DC + encoder, driver motor, OLED, catu daya baterai.
3. Firmware: pembacaan sensor, kalibrasi, kendali PID, kinematika (odometri), fitur keamanan.
4. Platform block coding berbasis web (Blockly).
5. Pengujian akurasi sensor, kecepatan, keterulangan, batas kerja aman; uji coba ke siswa SD.
6. Dokumentasi dan analisis hasil pengujian.

Tidak dikerjakan: produksi massal dan penjualan; lintasan selain hitam di atas putih; upload via
Bluetooth dan dukungan iPad/Safari; fitur lomba (mapping lintasan, kecepatan tinggi); modifikasi
kit Ichiduino Pro (hanya diukur sebagai pembanding).

## 5. Key Project Deliverables

Prototipe robot · desain PCB (skematik + layout) · firmware · platform block coding web ·
data pengujian · dokumentasi kegiatan · laporan mingguan · laporan akhir · manual pengguna.

## 6. Criteria for Success — sasaran terukur

| No | Sasaran | Nilai | Cara uji | Alat ukur | Alasan nilai |
|---|---|---|---|---|---|
| S1 | Akurasi pembacaan posisi garis | error ≤ 2 mm | Robot diam (motor mati) diletakkan pada offset −30 s.d. +30 mm (langkah 5 mm) dari tengah garis; bandingkan posisi terbaca (serial) dengan offset sebenarnya; 3 ulangan tiap titik | Kertas milimeter + jangka sorong | ≈ 10% lebar garis 19 mm; di bawah jarak antar sensor (~9,5 mm) |
| S2 | Kecepatan rata-rata | ≥ 0,5 m/s | v = panjang lintasan / waktu tempuh, 3 ulangan | Meteran, stopwatch / video | Sengaja dibatasi demi keamanan siswa SD; lebih lambat dari kit lomba Ichiduino |
| S3 | Keterulangan waktu tempuh | simpangan baku ≤ 5% dari rata-rata | 10 putaran pada lintasan dan kondisi baterai sama | Stopwatch / timer firmware | 5% dari ± 20 s ≈ 1 s, jauh di atas ketelitian alat (0,01 s) |
| S4 | Waktu berhenti saat garis hilang | ≤ 500 ms | Garis diputus; hitung selang garis hilang → roda berhenti dari video slow-motion; 3 ulangan | Video HP 240 fps (± 4 ms) | Pada 0,5 m/s robot berhenti dalam ≤ 25 cm |
| S5 | Pemutusan baterai lemah | motor mati pada < 3,2 V/sel | Baterai diganti power supply variabel, tegangan diturunkan perlahan; catat tegangan saat motor mati; 3 ulangan | Power supply + multimeter | Memberi margin di atas batas discharge Li-ion |
| S6 | Biaya komponen per unit | ≤ Rp 450.000 | Jumlah BOM per unit, tiap harga tertelusur ke tautan toko | Daftar harga | ± 22% harga kit Ichiduino Pro |

## 7. Milestone Dates (per gerbang, pekan sesuai pedoman — tanggal dikonfirmasi ke koordinator)

| No | Tonggak | Pekan | Gerbang |
|---|---|---|---|
| 1 | Lembar telaah & uji defisit, Project Charter, sasaran terukur | M-1–M-2 | G1 Penetapan |
| 2 | WBS, jadwal, RAB ≤ Rp 900.000, rumusan optimasi | M-3–M-5 | |
| 3 | Rancangan teknis: arsitektur, wiring, flowchart, skematik, pembandingan alternatif, pustaka IEEE | M-3–M-6 | G2 Rancangan |
| 4 | Analisis bahaya (≥ 8 mode kegagalan) | M-7–M-8 | |
| 5 | Prototipe berjalan, data awal 3 ulangan, demo progres | M-7–M-10 | G3 Realisasi awal |
| 6 | PCB, platform block coding, pengujian menyeluruh S1–S6, uji coba siswa SD | M-11–M-14 | G4 Pembuktian |
| 7 | Laporan akhir, manual (diuji orang luar kelompok), serah terima | M-15–M-16 | G5 Serah terima |

Risiko terbesar: pembacaan sensor IR terganggu cahaya ruangan dan kondisi permukaan sehingga posisi
garis tidak akurat (S1).

### Daftar risiko dan penanganan

| No | Risiko | Dampak | Penanganan |
|---|---|---|---|
| R1 | Sensor IR terganggu cahaya ruangan / permukaan lintasan | S1 gagal | Emitter IR ON–OFF (selisih), kalibrasi tiap dinyalakan |
| R2 | PID tidak stabil saat kecepatan/tegangan baterai berubah | S2, S3 gagal | Tuning lewat serial, kompensasi tegangan baterai |
| R3 | PCB salah desain atau terlambat datang | Jadwal G3–G4 mundur | Prototipe modul di breadboard dulu, pesan PCB paling lambat M-10 |
| R4 | Biaya melebihi pagu / target per unit | S6 gagal | RAB dipantau tiap pembelian, pilih komponen alternatif |
| R5 | Baterai Li-ion overcharge / overdischarge / korsleting | Bahaya keselamatan | BMS 2S, cutoff firmware (S5), ruang baterai tertutup |
| R6 | Platform web tidak jalan di perangkat sekolah | Uji coba SD terhambat | Uji di Chrome/Edge sejak awal; jalur Arduino IDE sebagai cadangan |

## 8. Budget Summary

Lihat RAB (dirinci penuh pada Butir 2 / G2). Ringkasan perkiraan: elektronik Rp 640.000,
mekanik Rp 60.000, lain-lain Rp 105.000, total Rp 805.000 (pagu Rp 900.000).
Kit Ichiduino Pro tidak dianggarkan ulang.

## Persetujuan

Ditandatangani Pengawas PjBL, Manajer Proyek, dan SELURUH anggota (syarat Butir 1).
