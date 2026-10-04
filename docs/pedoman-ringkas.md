# Ringkasan Pedoman Pelaksanaan PjBL Semester 5 (Edisi 1, Rev 0)

Sumber: "Pedoman Pelaksanaan PjBL Semester 5 — Proyek 3: Robot Industri", DTEO FV ITS,
Semester Gasal 2026/2027. Kelompok ini: P01 Kel.5, **jalur P (Project)**.

## Gerbang (gate) — tidak boleh lanjut sebelum gerbang LULUS

Menurut pedoman M-0 = 17 Agustus 2026, tenggat jatuh hari Senin.
**Tanggal nyata bisa bergeser — selalu konfirmasi ke koordinator/pembimbing.**

| Gerbang | Pekan | Nama | Yang harus sudah ada |
|---|---|---|---|
| G1 | M-2 | Penetapan | Topik, Project Charter, sasaran terukur, hasil uji defisit |
| G2 | M-6 | Rancangan | WBS + jadwal + RAB (≤ Rp 900.000), rancangan teknis berdiagram |
| G3 | M-10 | Realisasi awal | Analisis bahaya (FMEA), hasil awal 3 ulangan, demo progres |
| G4 | M-14 | Pembuktian | Pengujian menyeluruh, status tiap sasaran, tabel selisih |
| G5 | M-16 | Serah terima | Laporan akhir, manual (diuji orang luar), demo akhir, Pertanyaan perseorangan |

Ujian komprehensif: tengah M-7, akhir M-15 (perseorangan, 5% masing-masing).

## 7 butir tugas (Lampiran H)

| Butir | Isi | Pekan | Gerbang | Kunci penerimaan |
|---|---|---|---|---|
| 1 | Charter & sasaran terukur | M-1–M-2 | G1 | Lingkup 2 sisi; ≥ 4 sasaran bernilai, bersatuan, **bercara uji**; jadwal per gerbang + risiko terbesar; **peran tiap anggota**; ditandatangani semua anggota; daftar risiko + penanganan |
| 2 | Rancangan pekerjaan & RAB | M-3–M-5 | G2 | WBS sampai paket 1 pekan, tiap paket ada PJ & tenggat; RAB ≤ Rp 900.000, tertelusur ke daftar harga, alasan ≥ 3 komponen; **rumusan optimasi** (peubah, fungsi tujuan, kendala bersatuan) |
| 3 | Rancangan teknis | M-3–M-6 | G2 | Diagram (blok/alir/arsitektur); tabel ≥ 2 alternatif + apa yang dikorbankan; ≥ 5 pustaka 5 tahun terakhir, gaya IEEE |
| 4 | Analisis bahaya | M-7–M-8 | G3 | ≥ 8 mode kegagalan (gerak & listrik), sebab, akibat, kekerapan, keparahan, angka risiko; 3 risiko tertinggi dicegah nyata |
| 5 | Realisasi & hasil awal | M-7–M-10 | G3 | Jalan 3× berturut-turut tanpa perbaikan; data 3 ulangan bersatuan; data metode cerdas dipisah latih/uji; catatan penyimpangan |
| 6 | Pengujian menyeluruh | M-11–M-14 | G4 | Semua sasaran berstatus LULUS/GAGAL/BELUM TERBUKTI; uji gerak 3× dalam satu grafik; tabel selisih berangka |
| 7 | Dokumentasi & serah terima | M-15–M-16 | G5 | Laporan akhir; manual diuji orang luar; tabel keadaan terbaik; berita acara |

Butir 8 (simulasi sel robot) hanya untuk kelompok berdefisit ≥ 2.

## Jalur P

Jalur P = **mengembangkan produk di atas kit acuan yang dibeli** (kit ditetapkan koordinator).
Rubrik: lingkup harus memisahkan apa yang dikembangkan vs bawaan kit (A.1, C.1); barang bawaan
kit tidak dianggarkan ulang (A.3); sasaran tidak lebih longgar dari acuan minimum kit (A.2);
pembandingan dengan ≥ 2 produk sejenis memakai angka (C.2).

**Kasus kelompok ini:** kit yang dibeli hanya menjadi CONTOH/pembanding; robot dirancang dan
dibuat dari nol (elektronik, PCB, firmware, block coding). Di charter, tulis tegas bahwa kit
acuan = pembanding, dan seluruh sistem = pengembangan sendiri. Sasaran tetap tidak boleh lebih
longgar dari spesifikasi kit acuan (A.2).

**Kit acuan: Ichiduino Pro** (± Rp 1.999.999 per kit; unit kontrol Ultimate 5 Max Rp 825.000).
Spesifikasi dari brosur: ATmega2560, 12 sensor garis optik, OLED 0,96", LiPo 2S 400 mAh,
magnetic charger, USB-C, 2 port servo 5V, 1 port kipas DC, motor DC 16 mm 12V 1200 RPM,
dimensi 12,5 × 14,3 × 5,5 (cm), pemrograman mBlock dan Arduino IDE.
Kinerja nyata (kecepatan, akurasi, daya tahan baterai) belum diukur — ukur di lintasan uji yang sama.

## Logbook (Lampiran C) — PERSEORANGAN

Tiap anggota, tiap pekan M-1 s.d. M-16, unggah PDF paling lambat **Jumat 17.00**.
Isi: nama & NRP, kelompok & jalur, pekan ke, peran pekan ini; **menit dikerjakan dari 1020 menit**,
capaian praktik yang dituntaskan, paraf pencatat; lalu:
1. Apa yang saya kerjakan pekan ini
2. Hasil ukur atau hitung beserta angkanya
3. Kesulitan yang ditemui dan cara menanganinya
4. Rencana pekan berikutnya
5. Bukti dokumentasi gambar

Logbook yang diisi sekaligus menjelang tenggat hanya dihitung pekan yang terisi tepat waktu.

## Penilaian singkat

Rubrik kelompok (A1, 50%): A Charter 10 · B Rancangan 20 · C Pengembangan sendiri 15 ·
D Realisasi & pembuktian 25 · E Mutu praktik & K3 10 · F Dokumentasi 20.
Nilai akhir = nilai kelompok × 73% × faktor + nilai perseorangan 27%.
Faktor anggota: 1,00 / 0,85 / 0,70 / 0,50 (berdasar logbook, jam praktik, penilaian sejawat).
