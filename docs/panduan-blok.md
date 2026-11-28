# Panduan blok Mind+ robot LFM X1

Extension "Robot LFM X1" untuk Mind+ V2 (cara memasang: [`mindplus-ext/README.md`](../mindplus-ext/README.md)).
Pilih papan **ESP32**. Robot belum dirakit saat panduan ini ditulis (28/11/2026), jadi nilai awal (kecepatan,
Kp, Kd) masih dari simulasi dan perlu disetel di robot asli (lihat [`firmware-uji.md`](firmware-uji.md)).

## Dasar

- Blok di bagian **setup** (atas) dijalankan sekali; blok di **ulangi selamanya** (loop) dijalankan terus.
- `inisialisasi robot` dipasang otomatis paling awal begitu ada blok LFM X1 yang dipakai. Kalibrasi yang
  tersimpan langsung dimuat saat robot menyala.
- Tombol robot dari kiri: **KEMBALI, ATAS, OK, BAWAH, LANJUT**.
- `posisi garis`: −1000 (garis di kiri robot) … 0 (tengah) … +1000 (kanan). Nilai sensor: 0 = lantai, 1000 = garis.
- Kecepatan memakai skala PWM 0–255 (120 ≈ 0,4 m/s). Tegangan baterai dikompensasi otomatis, jadi kecepatan tidak
  turun saat baterai melemah.

## Daftar blok

### Persiapan dan sensor

| Blok | Fungsinya |
|---|---|
| `inisialisasi robot LFM X1` | menyalakan sensor, motor, encoder, buzzer (tidak wajib dipasang, sudah otomatis) |
| `kalibrasi sensor [geser dengan tangan / robot berayun sendiri] selama () ms` | merekam nilai lantai dan garis tiap sensor, lalu disimpan (tetap ada sesudah robot dimatikan). Robot harus di atas garis |
| `muat kalibrasi tersimpan` | memuat ulang kalibrasi dari memori |
| `sensor sudah dikalibrasi?` | benar kalau ada kalibrasi yang berhasil |
| `warna garis [hitam / putih]` | hitam = garis hitam di lantai putih (arena IARC) |
| `posisi garis` | −1000 … +1000, lihat di atas |
| `garis terdeteksi?` | ada sensor yang melihat garis |
| `ada persimpangan?` | ada cabang kiri atau kanan |
| `ada cabang [kiri / kanan]?` | sensor ujung kiri (S1–S3) atau kanan (S10–S12) melihat garis |
| `nilai sensor S()` | 0–1000 untuk satu sensor (S1 paling kiri) |

### Gerak

| Blok | Fungsinya |
|---|---|
| `ikuti garis kecepatan () Kp () Kd ()` | satu langkah PID; pasang di dalam loop. Nilai awal 120 / 0,07 / 3,5 |
| `motor kiri () kanan ()` | −255 … 255, minus = mundur |
| `berhenti` | rem kedua motor |
| `maju () mm kecepatan ()` | maju lurus sejauh itu (encoder), lalu berhenti. Menunggu sampai selesai |
| `putar () derajat (+ kiri) kecepatan ()` | putar di tempat; −90 = putar kanan 90° |
| `belok [kiri / kanan] sampai ketemu garis kecepatan ()` | putar minimal 60° lalu berhenti saat sensor tengah menemukan garis |

Blok yang menunggu (`maju`, `putar`, `belok … sampai ketemu garis`, `indeks`, `jalankan rute terpendek`) bisa
dibatalkan dengan **tombol apa pun**.

### Path planning per indeks

| Blok | Fungsinya |
|---|---|
| `atur PID rute Kp () Kd ()` | Kp dan Kd yang dipakai blok indeks |
| `mulai rute baru` | wajib sebelum menjalankan rute lagi sesudah rute dibatalkan |
| `indeks () jika [pemicu] lakukan [aksi] lalu ikuti garis [warna] kecepatan () sejauh () mm` | satu langkah rute, lihat di bawah |
| `tandai simpul x () y () terhalang` | simpul yang tidak boleh dilewati rute terpendek (maks 16) |
| `hapus semua simpul terhalang` | |
| `jalankan rute terpendek grid () x () dari x () y () menghadap [] ke x () y () kecepatan ()` | robot menghitung sendiri urutan indeks (belok paling sedikit) lalu menjalankannya |

Cara kerja satu blok **indeks**:

1. Robot mengikuti garis sampai **pemicu** terjadi:
   `ada persimpangan` (cabang mana saja), `ada cabang kiri`, `ada cabang kanan`, `ada cabang kiri dan kanan`,
   `garis habis` (ujung garis), atau `langsung` (tanpa menunggu).
   Persimpangan yang tidak cocok dengan pemicu dilewati lurus.
2. Robot maju sampai poros roda tepat di tengah persimpangan, lalu menjalankan **aksi**:
   `lurus`, `belok kiri`, `belok kanan`, `putar balik`, atau `berhenti`.
   Belokan diukur encoder lalu dikunci ke garis oleh sensor tengah.
3. Robot mengikuti garis sejauh **mm** yang diisi, lalu lanjut ke blok indeks berikutnya tanpa berhenti.

Nomor indeks hanya label untuk dibaca (urutan = urutan blok). Kalau sesudah blok indeks tidak ada blok lain dalam
0,3 s, motor direm otomatis. Indeks dengan aksi `berhenti` mengakhiri rute.

Grid rute terpendek: simpul (0,0) di pojok kiri bawah, x ke kanan (timur), y ke depan (utara), maks 8 × 8.
Letakkan robot di garis **tepat sesudah simpul start, menghadap arah yang dipilih**: ruas pertama selalu searah
hadapan robot. Jarak antar simpul tidak perlu diisi karena robot berpindah simpul dengan mengikuti garis sampai
persimpangan berikutnya. Kalau tidak ada rute, robot bunyi panjang dan tidak bergerak. Untuk arena IARC (bentuk
tangga, bukan grid penuh) pakai blok indeks satu per satu.

### Lain-lain

| Blok | Fungsinya |
|---|---|
| `tegangan baterai (V)` | tegangan pack 2S |
| `baterai lemah?` | di bawah 6,8 V, segera cas |
| `bunyi () ms` | buzzer, tidak menunggu |
| `tombol [] ditekan?` | benar selama tombol ditekan |
| `tunggu tombol [] ditekan` | program berhenti di sini sampai tombol ditekan |
| `jarak tempuh (mm)` / `reset jarak tempuh` | jarak dari encoder (rata-rata kedua roda) |

## Contoh program

Susunan blok contoh dan kode C++ hasilnya ada di `mindplus-ext/contoh/` (keempatnya sudah dicek bisa
dikompilasi).

**IkutiGaris**: setup = `warna garis hitam`, `jika tidak sensor sudah dikalibrasi? maka kalibrasi sensor robot
berayun sendiri selama 3000 ms`, `tunggu tombol OK ditekan`. Loop = `ikuti garis kecepatan 120 Kp 0.07 Kd 3.5`,
`jika ada persimpangan? maka berhenti, bunyi 300 ms, tunggu tombol OK ditekan, maju 40 mm kecepatan 90`.

**RuteIndeks** (rute slide 8, sama dengan simulasi CoppeliaSim dan rute "Slide 8" di menu OLED):

| Indeks | Jika | Lakukan | Ikuti garis |
|---|---|---|---|
| 1 | ada cabang kiri | belok kiri | hitam, 120, 80 mm |
| 2 | ada persimpangan | belok kanan | hitam, 120, 80 mm |
| 3 | ada persimpangan | belok kiri | hitam, 120, 80 mm |
| 4 | ada persimpangan | belok kanan | hitam, 120, 80 mm |
| 5 | ada persimpangan | belok kiri | hitam, 120, 80 mm |
| 6 | ada persimpangan | berhenti | — |

Sebelumnya: `atur PID rute Kp 0.07 Kd 3.5`, `tunggu tombol OK ditekan`, `mulai rute baru`; sesudahnya `bunyi 500 ms`.

**RuteTerpendek**: `hapus semua simpul terhalang`, tandai (1,0), (2,2), (1,2) terhalang, `tunggu tombol OK`,
`mulai rute baru`, `jalankan rute terpendek grid 4 x 4 dari x 0 y 0 menghadap utara ke x 3 y 3 kecepatan 120`.

**CekSensor**: setiap 0,1 s mengirim posisi garis, cabang kiri/kanan, nilai S6, dan tegangan baterai ke Serial
Monitor (115200), bunyi kalau baterai lemah.

## Tanpa Mind+

Firmware bawaan (`firmware/`, diunggah dengan PlatformIO) sudah punya menu OLED: pilih rute, kalibrasi, lihat
sensor, atur PID, tes motor. Rute untuk menu ditulis di `firmware/src/Routes.cpp` dengan isi yang sama seperti blok
indeks (satu baris = satu indeks).
