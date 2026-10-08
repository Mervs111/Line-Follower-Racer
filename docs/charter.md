# Project Charter — Robot Line Tracer Micro (revisi 2: arahan dosen 05/10/2026)

Disesuaikan dengan Lembar Telaah (02/10/2026), Pedoman PjBL Semester 5 (Butir 1), dan arahan dosen
05/10/2026: reverse engineering produk contoh, budget maksimal Rp 900.000, minimum requirement
**mengikuti garis otomatis + path planning**. Bagian bertanda [ISI] diisi kelompok.

## 1. Project Identity

- Nama: Robot Line Tracer Micro
- Short description: Robot line tracer edukasi untuk anak sekolah, hasil reverse engineering kit
  Ichiduino Pro, yang mampu mengikuti garis secara otomatis dan merencanakan rute terpendek (path
  planning) pada lintasan bercabang. Berbasis ESP32, dapat diprogram dengan block coding berbasis web,
  dibangun dengan anggaran maksimal Rp 900.000.
- Supervisor: Fira Aulia, S.Tr.T, M.Tr.T

| No | Nama | NRP | Peran |
|---|---|---|---|
| 1 | Mararevi Subagyo | 2040241036 | Project Manager + [ISI] |
| 2 | Fernandy Raditya Wardhana | 2040241007 | [ISI] |
| 3 | Achmad Iqbal Adiputra | 2040241121 | [ISI] |
| 4 | Adhityanoval Dewa Mahendra | 2040241085 | [ISI] |

Usulan peran: (a) Firmware, kendali & path planning, (b) Elektronik & PCB,
(c) Mekanik & pengujian, (d) Platform web, RAB & dokumentasi.

## 2. Business Reasons

Robot line tracer edukasi di pasaran lokal, seperti Ichiduino Pro, dijual ± Rp 2.000.000 per kit
lengkap dengan unit kontrol (Ultimate 5 Max) seharga Rp 825.000, dan ditujukan untuk kompetisi.
Harga dan fiturnya (kecepatan tinggi, baterai LiPo 2S) kurang sesuai sebagai media belajar anak sekolah.

Proyek ini melakukan reverse engineering terhadap Ichiduino Pro: fungsi dan arsitekturnya dianalisis,
lalu dirancang ulang dari nol dengan anggaran maksimal Rp 900.000. Fitur yang dipertahankan,
diganti, atau ditiadakan dipilih berdasarkan kebutuhan edukasi dan batas anggaran. Selain mengikuti
garis, robot memiliki kemampuan path planning: memetakan lintasan bercabang dan menentukan rute
terpendek menuju titik tujuan, sehingga siswa dapat belajar konsep algoritma dan navigasi melalui
block coding berbasis web tanpa instalasi.

## 3. Project Objectives

1. Melakukan reverse engineering kit Ichiduino Pro dan merancang ulang robot line tracer edukasi
   berbasis ESP32 dengan anggaran maksimal Rp 900.000.
2. Membuat robot yang mampu mengikuti garis hitam di atas putih secara otomatis dengan kendali PID,
   akurasi pembacaan posisi garis ≤ 2 mm dan kecepatan rata-rata ≥ 0,5 m/s.
3. Menerapkan path planning: robot mendeteksi persimpangan, menyimpan peta lintasan sebagai graf,
   dan menghitung serta menjalankan rute terpendek menuju titik tujuan.
4. Menerapkan fitur keamanan: berhenti ≤ 500 ms setelah garis tidak terdeteksi dan pemutusan saat
   tegangan baterai < 3,2 V per sel.
5. Mengembangkan platform block coding berbasis web (Blockly), termasuk blok navigasi menuju titik tujuan.
6. Menguji performa, keterulangan gerak, dan path planning, serta melakukan uji coba kepada siswa sekolah.

## 4. Project Scope

Dikerjakan (seluruhnya dikembangkan sendiri, bukan modifikasi kit):
1. Reverse engineering Ichiduino Pro: analisis fungsi, arsitektur, dan spesifikasi sebagai acuan.
2. Perancangan robot berbasis ESP32 dari prototipe sampai desain PCB siap produksi.
3. Sistem elektronik: ESP32, 8 sensor garis, motor DC + encoder, driver motor, OLED, catu daya baterai.
4. Firmware: pembacaan sensor, kalibrasi, kendali PID, deteksi persimpangan, odometri,
   path planning (pemetaan lintasan bercabang + pencarian rute terpendek), fitur keamanan.
5. Platform block coding berbasis web (Blockly).
6. Pengujian akurasi sensor, kecepatan, keterulangan, path planning, batas kerja aman; uji coba ke siswa.
7. Dokumentasi dan analisis hasil pengujian.

Tidak dikerjakan: produksi massal dan penjualan; lintasan selain garis hitam di atas putih; path
planning pada persimpangan bersudut selain 90° (peta lintasan berbentuk grid; garis berbelok dan
melengkung tetap dapat diikuti); penghindaran halangan (obstacle avoidance); upload via
Bluetooth dan dukungan iPad/Safari; fitur lomba (kecepatan tinggi, kipas penyedot); modifikasi kit
Ichiduino Pro (hanya dianalisis dan diukur sebagai pembanding).

## 5. Key Project Deliverables

Tabel reverse engineering Ichiduino Pro · prototipe robot · desain PCB (skematik + layout) · firmware
(termasuk path planning) · platform block coding web · lintasan uji grid · data pengujian ·
dokumentasi kegiatan · laporan mingguan · laporan akhir · manual pengguna.

## 6. Criteria for Success — sasaran terukur

Lintasan uji path planning: grid garis 4 × 4 titik persimpangan, jarak antar titik 30 cm.

| No | Sasaran | Nilai | Cara uji | Alat ukur | Alasan nilai |
|---|---|---|---|---|---|
| S1 | Akurasi pembacaan posisi garis | error ≤ 2 mm | Robot diam (motor mati) pada offset −30 s.d. +30 mm (langkah 5 mm); bandingkan posisi terbaca (serial) dengan offset sebenarnya; 3 ulangan tiap titik | Kertas milimeter + jangka sorong | ≈ 10% lebar garis 19 mm |
| S2 | Kecepatan rata-rata | ≥ 0,5 m/s | v = panjang lintasan / waktu tempuh, 3 ulangan | Meteran, stopwatch / video | Dibatasi demi keamanan anak sekolah |
| S3 | Keterulangan waktu tempuh | simpangan baku ≤ 5% dari rata-rata | 10 putaran pada lintasan dan kondisi baterai sama | Stopwatch / timer firmware | 5% dari ± 20 s ≈ 1 s, di atas ketelitian alat |
| S4 | Deteksi persimpangan | ≥ 95% benar | Robot melewati ≥ 40 persimpangan pada grid; bandingkan log deteksi dengan persimpangan sebenarnya | Log serial + video | Satu persimpangan terlewat membuat rute salah |
| S5 | Path planning: rute terpendek | 10 dari 10 rute sama dengan rute terpendek | 10 pasangan titik awal–tujuan berbeda; rute dari robot dibandingkan dengan rute terpendek hasil hitung manual | Log serial (urutan titik) | Graf kecil, rute optimal dapat dihitung pasti |
| S6 | Ketepatan berhenti di titik tujuan | error ≤ 30 mm | Ukur jarak pusat robot ke titik tujuan setelah berhenti, pada 10 rute S5 | Penggaris / meteran | ≈ 10% jarak antar titik (30 cm) |
| S7 | Waktu berhenti saat garis hilang | ≤ 500 ms | Garis diputus; hitung dari video slow-motion; 3 ulangan | Video HP 240 fps (± 4 ms) | Pada 0,5 m/s robot berhenti dalam ≤ 25 cm |
| S8 | Pemutusan baterai lemah | motor mati pada < 3,2 V/sel | Baterai diganti power supply variabel, tegangan diturunkan perlahan; 3 ulangan | Power supply + multimeter | Margin di atas batas discharge Li-ion |
| S9 | Total biaya proyek | ≤ Rp 900.000 | Jumlah RAB, tiap harga tertelusur ke tautan toko | Daftar harga | Batas anggaran dari dosen |

S4 dan S5 diuji terpisah: S4 menguji sensor/deteksi, S5 menguji algoritma (rute dibandingkan per titik),
sehingga penyebab kegagalan dapat dibedakan.

## 7. Milestone Dates (per gerbang, pekan sesuai pedoman — tanggal dikonfirmasi ke koordinator)

| No | Tonggak | Pekan | Gerbang |
|---|---|---|---|
| 1 | Lembar telaah & uji defisit, Project Charter, sasaran terukur | M-1–M-2 | G1 Penetapan |
| 2 | Reverse engineering Ichiduino Pro, WBS, jadwal, RAB ≤ Rp 900.000, rumusan optimasi | M-3–M-5 | |
| 3 | Rancangan teknis: arsitektur, wiring, flowchart, skematik, algoritma path planning, pembandingan alternatif, pustaka IEEE | M-3–M-6 | G2 Rancangan |
| 4 | Analisis bahaya (≥ 8 mode kegagalan) | M-7–M-8 | |
| 5 | Prototipe mengikuti garis + deteksi persimpangan, data awal 3 ulangan, demo progres | M-7–M-10 | G3 Realisasi awal |
| 6 | Path planning, PCB, platform block coding, pengujian S1–S9, uji coba siswa | M-11–M-14 | G4 Pembuktian |
| 7 | Laporan akhir, manual (diuji orang luar kelompok), serah terima | M-15–M-16 | G5 Serah terima |

Risiko terbesar: pembacaan sensor IR terganggu cahaya ruangan dan kondisi permukaan sehingga posisi
garis dan persimpangan tidak terbaca akurat (S1, S4).

### Daftar risiko dan penanganan

| No | Risiko | Dampak | Penanganan |
|---|---|---|---|
| R1 | Sensor IR terganggu cahaya ruangan / permukaan lintasan | S1, S4 gagal | Emitter IR ON–OFF (selisih), kalibrasi tiap dinyalakan |
| R2 | Persimpangan terlewat atau terdeteksi ganda | S5, S6 gagal | Konfirmasi deteksi dengan jarak tempuh encoder sejak persimpangan terakhir |
| R3 | Belokan 90° di persimpangan tidak presisi | S5, S6 gagal | Belok berbasis encoder lalu dikunci kembali ke garis oleh sensor |
| R4 | PID tidak stabil saat kecepatan/tegangan baterai berubah | S2, S3 gagal | Tuning lewat serial, kompensasi tegangan baterai |
| R5 | PCB salah desain atau terlambat datang | Jadwal G3–G4 mundur | Prototipe modul di breadboard dulu, pesan PCB paling lambat M-10 |
| R6 | Biaya melebihi Rp 900.000 | S9 gagal | RAB dipantau tiap pembelian, siapkan komponen alternatif |
| R7 | Baterai Li-ion overcharge / overdischarge / korsleting | Bahaya keselamatan | BMS 2S, cutoff firmware (S8), ruang baterai tertutup |

## 8. Budget Summary

Ringkasan perkiraan (RAB rinci pada Butir 2 / G2): elektronik Rp 640.000, mekanik Rp 60.000,
lain-lain Rp 130.000 (termasuk lintasan uji grid), total Rp 830.000 (maksimal Rp 900.000).
Kit Ichiduino Pro tidak dianggarkan ulang.

## Persetujuan

Ditandatangani Pengawas PjBL, Manajer Proyek, dan SELURUH anggota (syarat Butir 1).
