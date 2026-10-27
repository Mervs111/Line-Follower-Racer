# Naskah bicara pitching RAB (27/10/2026)

Pegangan pembicara untuk deck `LFM_Pitching_RAB_P01-5.pptx` (16 slide + 3 lampiran). Target **±13 menit**, lalu
tanya jawab. Angka sesuai deck dan charter per 27/10 pagi: RAB **Rp937.390**, simulasi CoppeliaSim 26/10 malam.
Isi slide ada di `naskah-slide.md`; file ini berisi kalimat yang diucapkan.

**[...]** = aksi pembicara. Kalimat boleh diucapkan dengan gaya sendiri, asal angkanya tetap.

## Sebelum tampil

- [ ] Isi peran tiap anggota di slide 2 (masih "[isi peran]"), lalu sesuaikan kalimat slide 2 di bawah.
- [ ] Slide 11: ganti gambar uji 2D dengan `simulasi/hasil/coppeliasim_jendela.png` dan label hasil dengan angka
      CoppeliaSim (8,3 s / 12,6 mm; rute terpendek 5,7 s / 11,2 mm). Kalau tidak sempat, naskah di bawah tetap cocok.
- [ ] Siapkan video `simulasi/hasil/coppeliasim_slide.mp4` (9 detik) untuk diputar di slide 11, tersimpan di laptop
      (jangan bergantung internet). Cadangan: `coppeliasim_bfs.mp4` (6 detik) kalau ditanya rute terpendek.
- [ ] Bawa PDF deck (`LFM_Pitching_RAB_P01-5-pratinjau.pdf`) dan charter (`docs/Project_Charter_PJBL.docx`).
- [ ] Latihan sekali penuh dengan stopwatch.

**Angka yang wajib hafal:** total **Rp937.390** (sembilan ratus tiga puluh tujuh ribu tiga ratus sembilan puluh
rupiah), sisa **Rp62.610 (6,3%)** dari batas Rp1.000.000, **±47%** harga kit pembanding, 12 sensor jarak 8 mm,
kecepatan maksimum teoritis 0,89 m/s, simulasi **8,3 detik, berhenti 12,6 mm** dari tujuan.

## Pembagian pembicara (usulan)

Dibagi per blok berurutan supaya pergantian pembicara cuma 4 kali. Pilih pembicara blok 2–4 dari yang paling
menguasai isinya.

| Blok | Slide | Pembicara | Waktu |
|---|---|---|---|
| 1. Pembuka | 1–4 | Mararevi (Project Manager) | 2:40 |
| 2. Produk dan sasaran | 5–7 | Pembicara 2 (mis. Mekanik & Pengujian) | 2:40 |
| 3. Rancangan teknis dan simulasi | 8–11 | Pembicara 3 (mis. Firmware, Kendali & Path Planning) | 3:50 |
| 4. RAB | 12–14 | Pembicara 4 (mis. Platform Web, RAB & Dokumentasi) | 2:40 |
| 5. Penutup | 15–16 | Mararevi | 1:20 |
| | | **Total** | **±13:10** |

---

## Blok 1: Pembuka (Mararevi)

### Slide 1. Judul (0:30)

Selamat pagi, Bapak dan Ibu dosen. Kami kelompok P01-5 dengan proyek **Line Follower Micro**: robot edukasi pengikut
garis yang bisa menjalankan rute yang sudah direncanakan. Robot ini hasil reverse engineering kit Ichiduino Pro yang
kami rancang ulang dari nol. Hari ini kami mengajukan rencana anggaran biaya untuk pembelian komponen dan fabrikasi
PCB.

### Slide 2. Tim (0:30)

Tim kami empat orang, dibimbing Ibu Fira Aulia. Saya Mararevi Subagyo, project manager, sekaligus memegang
[peran]. Fernandy memegang [peran], Iqbal memegang [peran], dan Adhityanoval memegang [peran].

### Slide 3. Latar belakang (0:50)

Kit line tracer edukasi di pasaran mahal. Satu kit Ichiduino Pro sekitar **dua juta rupiah**, unit kontrolnya saja
Rp825.000. Kit itu juga dirancang untuk kompetisi, dengan motor 1200 RPM dan baterai LiPo kecil, sehingga kurang pas
sebagai media belajar anak sekolah.

Arahan dosen kepada kami: lakukan reverse engineering produk contoh, lalu buat ulang dengan anggaran maksimal **satu
juta rupiah**. Syarat minimumnya dua: robot mengikuti garis secara otomatis dan punya kemampuan path planning.

### Slide 4. Solusi (0:50)

Solusi kami Line Follower Micro, dirancang ulang dari elektronik, PCB, firmware, sampai block coding. Ada empat fitur
utama. **Pertama**, ikut garis dengan kendali PID dari 12 sensor QRE1113GR. **Kedua**, path planning: rute ditulis
sebagai urutan indeks, dan di lintasan grid urutan itu bisa dibuat otomatis dari rute terpendek. **Ketiga**, robot
diprogram dengan blok di browser lewat Blockly, tanpa instalasi. **Keempat**, keamanan: BMS baterai, motor mati di
bawah 3,2 volt per sel, dan robot berhenti dalam 500 milidetik kalau garis hilang.

Biayanya **Rp937.390**, sekitar 47 persen harga kit pembanding. Target uji lapangannya lomba IARC XII Smart Robotics,
Januari 2027.

Selanjutnya [Pembicara 2] akan menjelaskan hasil reverse engineering dan sasaran kami.

---

## Blok 2: Produk dan sasaran (Pembicara 2)

### Slide 5. Reverse engineering (1:00)

Ini hasil reverse engineering kami terhadap Ichiduino Pro. Fungsi utamanya kami **pertahankan**: 12 sensor garis dan
layar OLED. Yang kami **ganti** adalah bagian yang mahal atau kurang cocok untuk edukasi. Otaknya dari ATmega2560
menjadi ESP32, yang punya WiFi untuk pemrograman lewat browser. Baterai LiPo 400 mAh menjadi dua baterai 18650 dengan
BMS dan charger USB-C. Motor 1200 RPM menjadi N20 500 RPM dengan encoder.

Yang kami **kembangkan** adalah path planning. Di kit, aksi tiap indeks berbasis waktu dalam milidetik, sehingga
hasilnya berubah kalau baterai melemah. Di robot kami, maju dan belok diukur encoder, dan di lintasan grid rutenya
bisa dibuat otomatis. Port servo dan kipas untuk lomba kami tiadakan. Hasilnya, robot kami 53 persen lebih murah.

### Slide 6. Sasaran terukur (0:50)

Di charter kami menetapkan sasaran terukur, masing-masing dengan cara uji dan alat ukurnya. Yang utama: akurasi posisi
garis **paling besar 2 mm**, kecepatan rata-rata **minimal 0,5 meter per detik**, deteksi persimpangan **minimal 95
persen** dari 40 persimpangan, rute pada peta indeks **benar 10 dari 10** percobaan, dan robot berhenti **paling jauh
30 mm** dari titik tujuan. Sasaran kesembilan adalah total biaya paling besar satu juta rupiah, yang akan dibahas di
bagian RAB.

### Slide 7. Arsitektur sistem (0:50)

Arsitektur sistemnya seperti ini. Dua belas sensor dibaca bergantian lewat multiplexer CD74HC4067, sehingga ESP32
cukup memakai **lima pin**: satu ADC dan empat pemilih kanal. ESP32 menggerakkan dua motor N20 lewat driver TB6612FNG,
dan encoder motor memberi umpan balik ke ESP32. Dayanya dari dua baterai 18650 lewat BMS, saklar, dan buck converter
5 volt; motor langsung dari baterai. Untuk antarmuka ada OLED, dua tombol, buzzer, dan sensor tegangan baterai.
Programnya dikirim dari Blockly lewat WiFi atau kabel USB-C.

Rancangan teknisnya akan dilanjutkan oleh [Pembicara 3].

---

## Blok 3: Rancangan teknis dan simulasi (Pembicara 3)

### Slide 8. Kendali dan path planning (1:10)

Kendali robot terdiri dari dua loop. **Loop luar**: posisi garis dari 12 sensor masuk ke PID, keluarannya kecepatan
motor kiri dan kanan. **Loop dalam**: encoder mengukur jarak tempuh dan sudut belok. Sesuai arahan dosen, kami tidak
memakai IMU; belok 90 derajat dihitung dari selisih putaran roda, lalu robot dikunci kembali ke garis oleh sensor.

Path planning-nya memakai peta yang ditentukan di awal, sesuai usulan Bu Fira. Rute ditulis sebagai urutan indeks.
Tiap indeks berisi pola sensor pemicu, aksi, lalu ikuti garis sampai indeks berikutnya.
**[Tunjuk grid di kanan]** Contohnya di sini: dari S, indeks 1 belok kiri, 2 kanan, 3 kiri, 4 kanan, 5 kiri, dan
6 berhenti di T. Robot tidak perlu menjelajah lintasan dulu.

### Slide 9. Rancangan PCB (0:50)

Kami merancang dua PCB sendiri di KiCad. **PCB sensor** berbentuk jangkar, 95 kali 51 mm, berisi 12 sensor dengan
jarak 8 mm. Jarak ini dipilih untuk garis lomba selebar 2 cm. PCB sensor sudah lolos pemeriksaan DRC tanpa error dan
siap cetak.

**PCB utama** berbentuk seperti mobil F1, 100 kali 127 mm, memuat ESP32, driver motor, buck 5 volt, OLED, tombol, dan
buzzer. Semua jalurnya sudah tersambung. Sebelum dicetak, kami bereskan 11 error DRC dari dua footprint dan
menyesuaikan footprint tombol dan konektor motor dengan barang yang akan dibeli.

### Slide 10. Rancangan mekanik (0:40)

Ini model 3D robotnya: sekitar 11,6 kali 16,5 kali 6,2 cm, bentuk rendah seperti kit pembanding. PCB sekaligus
menjadi sasis, semua komponen dan baterai ada di atas, dan muka sensor sekitar 3 mm dari lantai. Body 3D print untuk
cover, bumper, dan dudukan belum masuk RAB karena kami masih menunggu info printer lab.

### Slide 11. Simulasi (1:10)

**[Putar video `coppeliasim_slide.mp4`, 9 detik, sambil bicara]**

Sesuai arahan dosen, rancangan ini kami uji dulu di simulasi **CoppeliaSim**. Model robot ukuran asli dibangun
otomatis dari skrip Python: roda 34 mm berjarak 91 mm, motor N20 500 RPM, dan 12 sensor di posisi PCB sensor yang
sebenarnya, dengan fisika roda dari mesin Bullet. Arenanya grid 30 cm dengan garis hitam 2 cm, sama dengan lintasan
uji di charter. Logika kendalinya sama dengan yang akan masuk firmware.

Hasilnya: rute contoh dari S ke T selesai dalam **8,3 detik**, dan robot berhenti **12,6 mm** dari titik tujuan, di
bawah batas sasaran 30 mm. Rute terpendek yang dibuat otomatis, dengan tiga kubus menghalangi jalur, juga berhasil:
5,7 detik dan 11,2 mm. Sebelumnya, logika yang sama lolos **25 dari 25** variasi kecepatan dan derau sensor di
simulasi 2D.

Berikutnya, [Pembicara 4] akan memaparkan rencana anggaran biaya.

---

## Blok 4: RAB (Pembicara 4)

### Slide 12. Rencana anggaran biaya (0:50)

Total RAB kami **Rp937.390**: elektrikal Rp862.390, mekanik Rp50.000, dan timah solder Rp25.000. Harga-harga ini
sudah kami validasi di marketplace online, dan tautan tokonya tercantum di charter. **[Tunjuk grafik]** Porsi
terbesar ada di fabrikasi dua PCB, Rp200.000, dan 12 sensor QRE1113GR, Rp180.000.

Yang tidak masuk RAB: lintasan uji, breadboard yang kami pinjam dari lab, dan software yang semuanya gratis. Kit
Ichiduino Pro hanya pembanding, jadi tidak dianggarkan ulang.

### Slide 13. Alasan komponen utama (1:00)

Ini alasan enam komponen dengan biaya terbesar.
- **ESP32**, Rp65.900: dual-core 240 MHz dengan WiFi untuk Blockly, jauh lebih murah dari ESP32-S3.
- **Sensor QRE1113GR**: LED inframerah dan fototransistor dalam satu kemasan kecil yang bersekat, jadi PCB sensor
  tipis dan dekat lantai.
- **Motor N20 dengan encoder**: kecepatan maksimum teoritis 0,89 meter per detik, di atas sasaran 0,5. Encodernya
  dipakai untuk belok 90 derajat dan mengukur jarak.
- **TB6612FNG**, Rp50.000: tegangan jatuhnya jauh lebih kecil dari L298N, jadi motor mendapat tenaga penuh dan
  driver tidak panas.
- **Baterai 18650 dengan BMS dan charger**: sekitar tiga jam pemakaian, terlindungi, dan diisi lewat USB-C.
- **Fabrikasi PCB**: menggantikan kabel breadboard, sehingga rapi dan awet dipakai siswa.

### Slide 14. Riwayat RAB dan efisiensi (0:50)

RAB ini sudah direvisi sebelas kali, dan **[tunjuk grafik]** totalnya selalu di bawah batas satu juta rupiah.
Kenaikan terbesar datang dari harga QRE1113GR di toko lokal, tambah Rp105.000, dan dari validasi harga marketplace,
tambah Rp50.390. Penghematan datang dari penghapusan MCP23017 dan LED indikator, breadboard yang dipinjam dari lab,
dan IC multiplexer yang Rp15.000 lebih murah.

Sisanya **Rp62.610, atau 6,3 persen**, untuk menutup kenaikan harga atau body 3D print yang belum masuk RAB.

Untuk jadwal dan penutup, kembali ke Mararevi.

---

## Blok 5: Penutup (Mararevi)

### Slide 15. Jadwal dan risiko (0:50)

Jadwal kami mengikuti gerbang PjBL. G1 sudah lulus 2 Oktober, dan hari ini bagian dari G2. Berikutnya analisis bahaya
di minggu 7 sampai 8, prototipe jalan tiga kali berturut-turut dan PCB dipesan paling lambat minggu 10 untuk G3, lalu
pembuktian dan uji coba siswa di G4, dan serah terima di G5.

Ada tiga risiko yang berkaitan dengan dana. PCB salah desain atau terlambat: kami buat prototipe breadboard dulu.
Biaya melebihi batas: RAB dipantau tiap pembelian dan semua harga ada tautannya. Sensor tanpa cadangan: tiap sensor
diuji di breadboard sebelum disolder.

### Slide 16. Penutup (0:30)

Dengan ini kami mohon persetujuan dana sebesar **Rp937.390** untuk pembelian komponen dan fabrikasi dua PCB. Setelah
dana cair, kami langsung membeli komponen, menguji rangkaian di breadboard, memesan PCB sensor dan PCB utama, lalu
mengerjakan firmware dan prototipe untuk G3.

Terima kasih. Kami siap menjawab pertanyaan.

---

## Antisipasi tanya jawab

Jawab singkat dulu (satu-dua kalimat), tambah detail kalau ditanya lagi. Lampiran A–C bisa dibuka kalau ditanya
rincian harga.

| Pertanyaan | Jawaban | Penjawab |
|---|---|---|
| Kenapa sensornya QRE1113GR Rp15.000, bukan sensor yang lebih murah? | LED IR dan fototransistor sudah dalam satu kemasan SMD kecil (2,9 × 3,6 mm) yang bersekat, jadi 12 sensor bisa dipasang rapat 8 mm di busur, dan muka sensor rendah ±3 mm dari lantai seperti kit. Dengan sensor terpisah kami harus menata dan menyekat pasangan LED + fototransistor sendiri. | Pembicara 3 |
| Tanpa IMU, apakah belok 90° cukup akurat? | Sudut belok dihitung dari selisih putaran roda (encoder), lalu robot dikunci ke garis oleh sensor tengah. Di simulasi robot berhenti 12,6 mm dari tujuan (batas 30 mm). Dengan robot asli dibuktikan lewat sasaran 5 dan 6. | Pembicara 3 |
| Seberapa bisa dipercaya simulasinya? | Ukuran robot, posisi sensor (diambil dari file PCB), roda, dan kecepatan motor sesuai rancangan, dan fisikanya dari mesin Bullet. Yang masih perkiraan: massa, torsi motor, gesekan. Karena itu hasil simulasi kami pakai untuk mengecek logika; pembuktian akhir tetap dengan robot asli di G3–G4. | Pembicara 3 |
| Simulasinya 0,4 m/s, padahal sasaran ≥ 0,5 m/s? | Rute contoh penuh belokan 90°, jadi dijalankan 0,4 m/s. Logika yang sama lolos sampai 0,7 m/s di simulasi 2D, dan motor bisa sampai 0,89 m/s teoritis. Sasaran kecepatan diuji di lintasan sesuai charter. | Pembicara 3 |
| Sisa Rp62.610 cukup untuk body 3D print? | Body 3D print sengaja belum dianggarkan karena menunggu info printer lab. Setelah harganya jelas, kami cocokkan dengan sisa dana; RAB tetap di bawah Rp1.000.000. | Pembicara 4 |
| Sensor dan multiplexer dibeli tanpa cadangan, kalau rusak? | Tiap sensor diuji di breadboard sebelum disolder dan pin 1 dicek. Kalau ada yang rusak, sensor bisa dibeli satuan di toko yang sama, dan multiplexer punya toko cadangan (74HC4067D SO-24, Rp35.000). Biayanya tertutup sisa dana. | Pembicara 4 |
| Kenapa PCB utama masih ada error DRC? | Error berasal dari dua footprint (transistor buzzer Q1 dan saklar SW1), bukan dari jalur. Bersama penyesuaian footprint tombol dan konektor motor, ini dibereskan sebelum PCB dipesan (paling lambat minggu 10). PCB sensor sudah DRC 0. | Pembicara 3 |
| Kenapa ESP32, bukan Arduino seperti kit? | ESP32 punya WiFi untuk pemrograman Blockly lewat browser tanpa instalasi, dual-core 240 MHz untuk PID, dan harganya Rp65.900, lebih murah dari unit kontrol kit. | Pembicara 2 |
| Kenapa TB6612FNG Rp50.000, bukan L298N yang lebih murah? | L298N kehilangan tegangan jauh lebih besar (sekitar 2 volt) dan cepat panas. Dengan baterai 2S, TB6612FNG membuat motor mendapat tenaga penuh. | Pembicara 4 |
| Kenapa 18650, bukan LiPo seperti kit? | Kapasitasnya besar (±3 jam pemakaian), dilindungi BMS, diisi lewat USB-C, dan lebih aman dipakai siswa. | Pembicara 2 |
| Apa nilai tambah dibanding kit? | Harga ±47% kit, aksi path planning diukur encoder (tidak terpengaruh baterai melemah), rute di grid dibuat otomatis, dan pemrograman Blockly lewat browser. | Mararevi |
| Ukuran grid 30 cm dari mana? | Dari lintasan uji path planning di charter (grid 4 × 4, jarak 30 cm). Di simulasi ukurannya cukup diganti satu angka kalau arena IARC ternyata berbeda. | Pembicara 3 |
| Bagaimana bentuk blok path planning-nya? | Satu blok per indeks: "indeks () jika [pola sensor] lakukan [aksi] lalu ikuti garis [hitam/putih] kecepatan ()", ditambah blok "buat rute terpendek dari () ke ()" untuk lintasan grid. | Pembicara 3 |
