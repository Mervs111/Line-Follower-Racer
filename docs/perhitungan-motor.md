# Perhitungan rancangan Line Follower Micro (diperbarui 27/10/2026)

Perhitungan untuk rancangan dan RAB terkini (27/10): motor N20 6 V 500 RPM + encoder, roda Ø34, jarak roda 91 mm,
baterai 2× 18650 (2S), buck MP1584, 12 QRE1113GR + mux CD74HC4067, nilai komponen dari skematik PCB utama
(`hardware/tools/gen_sch_utama.py`). Draf awal kelompok (08/10) ada di lampiran paling bawah.

**Asumsi** ditandai *(asumsi)*; angka yang perlu dicocokkan dengan listing toko ditandai **cek listing**.
Semua angka dihitung ulang dengan skrip, bukan dengan tangan.

## Ringkasan

| Besaran | Hasil | Sasaran / batas | Status |
|---|---|---|---|
| Kecepatan maksimum teoritis | 0,89 m/s | ≥ 0,5 m/s (sasaran 2) | memenuhi |
| Torsi desain per roda (SF 2) | 10,2 N·mm ≈ 0,10 kg·cm | torsi rated N20 0,20 kg·cm (listing) | memenuhi (1,9×) |
| Kecepatan pada beban rated (300 RPM) | 0,53 m/s | ≥ 0,5 m/s | memenuhi |
| Massa robot | ±0,25 kg tanpa 3D print, ±0,29 kg lengkap | desain 0,30 kg | memenuhi |
| Jarak dan waktu rem dari 0,5 m/s | 2,8 cm, 0,11 s | berhenti ≤ 500 ms (sasaran 7) | memenuhi |
| Daya total saat berjalan | 3,1–4,1 W | | |
| Lama pakai (berjalan terus) | 3,3–6,5 jam | klaim "±3 jam" di charter | memenuhi (batas bawah) |
| Waktu cas | ±3–3,5 jam (adaptor 5 V 2 A) | | |
| Arus LED sensor | 15,7 mA (17,3 mA kalau buck 5,35 V) | maks 50 mA | memenuhi |
| Tegangan ADC baterai | 1,59–2,08 V | rentang ADC 11 dB | memenuhi |
| Waktu baca 12 sensor | ±0,36 ms | loop kendali 1 ms | memenuhi |

## Spesifikasi motor (listing CNC Store Bandung, varian MTR-0239, dicek 27/10)

| Data | Nilai | Artinya untuk robot |
|---|---|---|
| Kecepatan tanpa beban | 500 RPM | 0,89 m/s di roda Ø34 |
| Kecepatan pada beban rated | 300 RPM | 0,53 m/s: sasaran 0,5 m/s tetap tercapai walau motor dibebani penuh |
| Torsi rated | 0,2 kg·cm | 1,9× torsi desain 0,10 kg·cm (yang sudah memakai SF 2) |
| Torsi stall | 0,45 kg·cm | 4,3× torsi desain |
| Arus rated | 170 mA | 2 motor pada beban rated: 6 V × 0,34 A = 2,0 W |
| Arus stall | tertulis 60 mA | lebih kecil dari arus rated, jadi hampir pasti salah ketik (kemungkinan 600 mA); tanya penjual |
| Rasio gearbox | 30 : 1 | dipakai di bagian 5 |
| Tegangan kerja | 3–6 V | PWM dibatasi 6,0 / V_bat (bagian 1) |
| PPR encoder, jenis konektor | tidak tertulis | tanya penjual (konektor: PH 2.0 atau XH 2.54) |

Saat robot melaju datar, beban tiap roda hanya ±0,005 kg·cm (hambatan gulir), jauh di bawah torsi rated, jadi
motor bekerja dekat putaran tanpa bebannya.

## 1. Kecepatan

Roda Ø34 mm (r = 0,017 m), motor 500 RPM tanpa beban pada 6 V:

v_maks = π · D · n / 60 = π · 0,034 · 500 / 60 = **0,89 m/s**

Untuk sasaran 0,5 m/s, roda cukup berputar n = 0,5 · 60 / (π · 0,034) = **281 RPM** (56% putaran maksimum),
jadi masih ada cadangan untuk beban dan baterai yang melemah.

**Tegangan motor.** Motor 6 V dipasok baterai 2S 6,4–8,4 V (3,2–4,2 V per sel). Supaya tegangan rata-rata motor
tidak lebih dari 6 V, duty PWM dibatasi sesuai tegangan baterai yang dibaca VBAT_SENSE:

| Tegangan baterai | Duty maksimum = 6,0 / V_bat | Nilai PWM 8-bit |
|---|---|---|
| 8,4 V (penuh) | 71,4% | 182 / 255 |
| 7,4 V (nominal) | 81,1% | 207 / 255 |
| 6,4 V (batas 3,2 V/sel) | 93,8% | 239 / 255 |

Dengan batas tetap 70% (tanpa kompensasi), pada 6,4 V motor hanya mendapat 4,48 V → 373 RPM → 0,66 m/s: masih di
atas 0,5 m/s, tapi kecepatan berubah mengikuti baterai. Kompensasi ini sekaligus penanganan risiko R4 di charter.

## 2. Gaya dan torsi

Asumsi: massa desain m = 0,30 kg (lihat bagian 4), percepatan 0 → 0,9 m/s dalam 0,5 s (a = 1,8 m/s²), koefisien
hambatan gulir roda karet di kertas/banner C_rr = 0,02 *(asumsi)*.

| | Rumus | Hasil |
|---|---|---|
| Gaya percepatan | F_a = m · a = 0,30 · 1,8 | 0,540 N |
| Hambatan gulir | F_rr = C_rr · m · g = 0,02 · 0,30 · 9,81 | 0,059 N |
| Gaya total | F = F_a + F_rr | 0,599 N |
| Torsi total di roda | τ = F · r = 0,599 · 0,017 | 10,2 N·mm |
| Torsi per roda | τ / 2 | 5,1 N·mm |
| **Torsi desain per roda (SF 2)** | 5,1 × 2 | **10,2 N·mm ≈ 0,10 kg·cm** |

(1 kg·cm = 98,1 N·mm.) Torsi rated N20 500 RPM di listing **0,2 kg·cm**, jadi 1,9× torsi desain.
Charter menulis ±9 N·mm karena belum memasukkan hambatan gulir; bedanya kecil.

Daya mekanik puncak saat berakselerasi F · v_maks = 0,53 W. Saat melaju 0,5 m/s cukup melawan hambatan gulir
(0,03 W), jadi motor jarang mendekati beban penuh.

**Traksi.** Titik berat diperkirakan 20 mm di depan poros dan ball caster 85,6 mm di depan poros *(asumsi)*, jadi
±77% berat ada di roda penggerak. Dengan koefisien gesek ban μ = 0,6 *(asumsi)*, percepatan maksimum tanpa selip
a = μ · g · 0,77 = **4,5 m/s²**, lebih besar dari 1,8 m/s² yang dibutuhkan.

**Tikungan.** Kecepatan maksimum tanpa selip di tikungan berjari-jari R: v = √(μ · g · R).

| R | 5 cm | 10 cm | 20 cm |
|---|---|---|---|
| v maksimum | 0,54 m/s | 0,77 m/s | 1,08 m/s |

**Terguling.** Titik berat ±25 mm dari lantai *(asumsi)* dan setengah jarak roda 45,5 mm: robot baru terguling pada
percepatan samping g · 45,5 / 25 = 17,9 m/s², jauh di atas batas selip 5,9 m/s². Robot akan selip dulu, tidak
terguling.

## 3. Berhenti saat garis hilang (sasaran 7)

Pengereman dibatasi traksi (4,5 m/s², motor di-*short brake* oleh TB6612). Dari 0,5 m/s:
t = v / a = **0,11 s**, jarak = v² / 2a = **2,8 cm**. Ditambah waktu memastikan garis hilang (±20 ms), total
±0,13 s, jauh di bawah batas 500 ms.

## 4. Anggaran massa

| Bagian | Massa (g) | Keterangan |
|---|---|---|
| Baterai 18650 × 2 | 92 | ±46 g per sel |
| Holder 2× 18650 | 12 | |
| ESP32 DevKit + socket | 14 | |
| TB6612 modul + socket | 5 | |
| MP1584 + BMS 2S + charger USB-C | 10 | |
| OLED 0,96" | 5 | |
| Motor N20 + encoder × 2 | 24 | ±12 g per motor |
| Roda Ø34 × 2 | 12 | |
| PCB utama (±96 cm², FR4 1,6 mm) | 34 | 0,36 g/cm² |
| PCB sensor (20,7 cm²) + komponen | 10 | |
| Ball caster | 8 | |
| Baut, mur, spacer | 10 | |
| Kabel dan konektor | 8 | |
| Tombol, buzzer, saklar, kapasitor, dioda | 6 | |
| **Subtotal** | **250** | |
| Cetak 3D (dudukan motor dan baterai, cover, bumper, sayap) | ±40 | *(asumsi, belum didesain)* |
| **Total** | **±290** | dipakai m_desain = **0,30 kg** |

Massa tiap komponen adalah perkiraan *(asumsi)*; timbang komponen setelah dibeli. Simulasi CoppeliaSim (26/10)
memakai 0,22 kg; samakan menjadi 0,30 kg saat simulasi dijalankan lagi.

## 5. Encoder dan belok 90° tanpa IMU

Rasio gearbox **30 : 1** (listing). PPR encoder belum tertulis di listing; contoh perhitungan memakai 7 PPR
*(asumsi, tanya penjual)*, dibaca kuadratur (×4):

| | Rumus | Hasil |
|---|---|---|
| Hitungan per putaran roda | 7 · 30 · 4 | 840 |
| Jarak per hitungan | π · 34 mm / 840 | 0,127 mm |
| Busur tiap roda saat putar di tempat 90° | (π/2) · (91 mm / 2) | 71,5 mm = 562 hitungan |
| Resolusi sudut belok | 90° / 562 | 0,16° per hitungan |
| Laju pulsa pada 500 RPM | 500/60 · 840 | 7.000 hitungan/s per roda |

Resolusi sudut jauh lebih halus dari yang dibutuhkan, jadi belok 90° cukup diukur encoder lalu dikunci ke garis oleh
sensor (arahan dosen 09/10). Laju 7.000 pulsa/s per roda sebaiknya dibaca **PCNT** (penghitung pulsa hardware
ESP32), bukan interrupt.

## 6. Daya dan baterai

**Rel +5 V.** MP1584 diatur 5,0 V, lalu melewati dioda D1 1N5819 (mencegah arus USB balik ke buck), turun ±0,35 V
→ +5 V ≈ **4,65 V**. ESP32, OLED, dan encoder mengambil 3,3 V dari regulator ESP32 yang dipasok +5 V, jadi arusnya
dihitung di rel 5 V.

| Beban | Arus | Keterangan |
|---|---|---|
| 12 LED IR QRE1113GR | 188 mA | (4,65 − 1,2) / 220 Ω = 15,7 mA per sensor |
| ESP32 dengan WiFi aktif | 150 mA | rata-rata *(asumsi)*, puncak ±300 mA saat kirim data |
| OLED | 15 mA | *(asumsi)* |
| 2 encoder motor | 10 mA | *(asumsi)* |
| 12 pull-up fototransistor | 4 mA | 3,3 V / 10 kΩ, paling besar |
| **Total** | **±370 mA** | buzzer (±30 mA) hanya sesekali |

Daya keluaran buck 5,0 V × 0,37 A = 1,84 W; efisiensi buck 88% *(asumsi)* → **2,1 W dari baterai**.
Motor saat berjalan dengan belokan rata-rata 1–2 W *(asumsi; batas atasnya = 2 motor pada arus rated 170 mA, 2,0 W)*,
jadi **total 3,1–4,1 W**.

**Energi baterai.** 2 sel 3000 mAh seri: 3,0 Ah × 7,4 V = 22,2 Wh; dipakai sampai 3,2 V/sel ±90% → 20,0 Wh.
Kapasitas sel marketplace sering di bawah label, jadi kemungkinan buruk 2000 mAh → 13,3 Wh.

| Kondisi | Kemungkinan buruk (13,3 Wh, 4,1 W) | Nominal (20,0 Wh, 3,1 W) |
|---|---|---|
| Berjalan terus | **3,3 jam** | 6,5 jam |
| Menyala tanpa motor (2,1 W) | 6,4 jam | 9,6 jam |

Klaim "±3 jam pemakaian" di charter adalah batas bawahnya.

**Pengisian.** Adaptor USB-C 5 V 2 A = 10 W, efisiensi charger 85% *(asumsi)* → ±1,0 A ke baterai 8,4 V →
±3 jam fase arus tetap + ±0,5 jam fase tegangan tetap = **±3–3,5 jam**.

**Arus puncak.** Arus stall di listing tertulis 60 mA (salah ketik, lihat tabel spesifikasi); dengan asumsi
±0,8 A per motor + rel 5 V ±0,3 A dari sisi baterai → ±1,9 A. Syarat: arus stall motor ≤ 1,2 A (batas kontinu TB6612 per kanal, puncak 3,2 A), dan arus
BMS ≥ 3 A (**cek listing**).

## 7. Rangkaian

| Bagian | Perhitungan | Hasil |
|---|---|---|
| Resistor LED QRE (220 Ω, 0805) | P = I² · R = 0,0157² · 220 | 54 mW < 125 mW |
| Pembagi baterai R1 100k / R2 33k | k = 33 / 133 = 0,248 | 8,4 V → 2,08 V; 7,4 V → 1,84 V; 6,4 V → 1,59 V di GPIO39 (rentang ADC 11 dB) |
| Arus pembagi | 8,4 V / 133 kΩ | 63 µA, hanya saat saklar ON (pembagi di VBAT setelah SW1) |
| Resolusi baca baterai | 3,1 V / 4095 / 0,248 | ±3,1 mV per langkah ADC |
| Basis buzzer (R3 1k, R4 10k, S8050) | I_B = (3,3 − 0,7)/1k − 0,7/10k = 2,53 mA; dengan h_FE ≥ 85 → mampu 215 mA | buzzer ±30 mA: transistor jenuh. R4 menjaga GPIO12 LOW saat boot |
| Pull-up tombol (R5, R6 10k) | 3,3 V / 10 kΩ | 0,33 mA saat ditekan; GPIO34/35 tidak punya pull-up internal, jadi R5/R6 wajib |
| C1 100 µF 16 V di VBAT | 16 V / 8,4 V | 1,9× tegangan maksimum |
| MP1584 | masukan 6,4–8,4 V (batas 4,5–28 V), keluaran 0,37 A (batas 3 A) | longgar |

**Waktu baca sensor.** Tiap kanal mux butuh waktu tenang ±5 µs (sumber 10 kΩ × kapasitansi mux + ADC ±100 pF,
τ ≈ 1 µs *(asumsi)*) ditambah `analogRead` ±10–25 µs, jadi 12 sensor ≈ 0,36 ms. Itu muat dalam loop kendali 1 ms
(1 kHz). Pada 0,5 m/s robot hanya bergerak 0,5 mm tiap siklus kendali.

## 8. Rekomendasi dari perhitungan

1. Atur keluaran **MP1584 ke 5,35 V** supaya rel +5 V setelah dioda D1 ≈ 5,0 V. Arus LED jadi 17,3 mA dan regulator
   3,3 V ESP32 punya cadangan tegangan yang cukup.
2. Tambah **kapasitor 100 nF** dari GPIO39 (VBAT_SENSE) ke GND. Impedansi pembagi 24,8 kΩ terlalu tinggi untuk ADC
   ESP32 tanpa kapasitor (τ = 2,5 ms, cukup untuk memantau baterai).
3. Batasi PWM motor dengan **kompensasi tegangan** (duty = 6,0 / V_bat), bukan angka tetap 70%.
4. Baca encoder dengan **PCNT** ESP32.
5. Motor MTR-0239 sudah dicek: torsi rated 0,2 kg·cm (cukup), rasio 30 : 1. **Masih ditanyakan ke penjual:** arus
   stall (tertulis 60 mA, salah ketik), PPR encoder, dan jenis konektor (PH 2.0 atau XH 2.54). Cek juga arus maksimum
   BMS dan arus cas modul charger.
6. Samakan massa simulasi menjadi 0,30 kg, dan torsi di charter menjadi ±10 N·mm (0,10 kg·cm).

---

## Lampiran: draf awal kelompok (08/10/2026)

Disimpan sebagai riwayat. Dasar awalnya target 1,5 m/s, roda Ø60 mm, massa 0,3 kg, akselerasi 0 → 1,5 m/s dalam
0,5 s:

- ω = v / r = 1,5 / 0,03 = 50 rad/s → 477 RPM → dipilih motor ±500 RPM.
- a = 3 m/s², F = 0,9 N, τ = 27 N·mm (13,5 N·mm per roda), safety factor 2 → 27 N·mm per roda (≈ 0,28 kg·cm).
- Kecepatan teoritis motor 500 RPM: Ø40 1,05 · Ø50 1,31 · Ø60 1,57 · Ø65 1,70 · Ø70 1,83 m/s.

Keputusan sesudahnya (08/10):
- Sasaran kecepatan charter tetap ≥ 0,5 m/s; 1,5 m/s hanya dasar pemilihan motor.
- Di marketplace hanya ada N20 + encoder 6 V 500 RPM. Robot dibuat rendah satu bidang dengan roda Ø34
  → v_maks 0,89 m/s.
- Sempat dipakai baterai 2× 14500, lalu kembali ke 2× 18650 (rancangan sekarang).
