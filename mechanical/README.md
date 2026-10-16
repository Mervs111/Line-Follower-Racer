# Mekanik — Robot Line Tracer Micro

## Usulan v13 (16/10/2026): gaya Ichiduino Pro, komponen RAB sekarang

Permintaan kelompok: bentuk dibuat semirip mungkin dengan Ichiduino Pro (foto produk), komponen tetap komponen
RAB sekarang, OLED diganti 0,96". PCB-nya dirancang kelompok sesudah ini; model ini memberi outline, lubang, dan
ruang untuk tiap komponen.

- Model 3D yang bisa diputar: https://claude.ai/artifact/MPiswHWgW5SBjHc9BhH8u4 (tombol "Pelindung cahaya" dan
  "Sayap belakang" untuk melihat bagian di bawahnya)
- Perbandingan siluet dengan foto Ichiduino: `render/ltm-v13-banding-ichiduino.png`
- Sumber: `cadquery/ltm_v13.py` (parametrik; `python ltm_v13.py <folder>`, tambah `CHECK=1` untuk cek tabrakan
  antar bagian: hasil terakhir 0 tabrakan)

### File per bagian (`v13/`)

| File | Isi | Cara buat |
|---|---|---|
| `step/cetak_dudukan_motor_baterai.step` + `.stl` | alas holder 2×18650 + penjepit 2 motor N20 + 4 tiang baut ke PCB utama + dudukan tiang sayap | 3D print, ±16 cm³ |
| `step/cetak_sayap_belakang.step` + `.stl` | sayap 3 panel (panel luar naik 12°) + endplate; sekaligus penutup baterai | 3D print berdiri di tepi belakang (tanpa support), ±12 cm³ |
| `step/cetak_tiang_sayap.step` + `.stl` | tiang sayap, cetak **2×** (kiri = kanan diputar) | 3D print, tab bawah masuk alas, tab atas tembus sayap |
| `step/cetak_pelindung_cahaya.step` + `.stl` | dinding pelindung cahaya di bawah baris sensor (risiko R1 charter), 1,8 mm di atas lantai | 3D print, ditempel/dibaut ke sisi bawah PCB sensor |
| `step/pcb_sensor.step`, `step/pcb_utama.step` | papan kosong (outline + lubang) | acuan layout PCB |
| `dxf/pcb_sensor_outline.dxf`, `dxf/pcb_utama_outline.dxf` | outline untuk KiCad (File › Import › Graphics → Edge.Cuts) | PCB sensor: 0,0 = tengah tepi depan (sama dengan koordinat sensor 15/10); PCB utama: 0,0 = tengah poros roda |
| `dxf/pcb_sensor_posisi_tcrt5000.dxf` | kotak 12 TCRT5000 (5,8 × 10,2) | impor ke layer F.Fab/User sebagai acuan |
| `step/roda_43x19.step` | roda Ø43 × 19 (beli) | acuan |
| `step/LTM_v13_rakitan.step` | rakitan lengkap 112 bagian berwarna | buka di Fusion 360 |

### Susunan dan alasannya

| Bagian | v13 | Alasan |
|---|---|---|
| PCB sensor | capit/jangkar 120 × 80 (sayap 45°, ujung tanduk ke belakang, batang tengah 44 → 34 mm masuk ke bawah hidung PCB utama), 12 TCRT5000 di posisi keputusan 15/10 | bentuk Ichiduino; susunan sensor tidak berubah |
| Sambungan PCB sensor ↔ utama | 4 spacer nilon M3 × 4 mm di batang + kabel pita 12 pin pendek (J5 di hidung PCB utama, J1 di batang) | kabel pita tetap (keputusan 13/10), dudukan 3D print 2 lengan tidak perlu lagi |
| Mux + MCP23017 | di **sisi bawah** batang PCB sensor (mux disolder menggantung, MCP23017 di socket DIP); jarak ke lantai ±3,7 dan ±2,8 mm | sisi atas PCB sensor bersih seperti Ichiduino; LED indikator tetap di atas |
| Tinggi | PCB sensor sisi bawah Z 9,3 (muka TCRT5000 ±2,3 mm dari lantai), PCB utama Z 14,9–16,5, motor duduk di atas PCB utama | TCRT5000 tingginya 7 mm, jadi PCB sensor tidak bisa serendah Ichiduino (sensor SMD) |
| Roda | **Ø43 × 19** merah, 2 alur, velg abu-abu | lebar seperti Ichiduino; poros di Z 21,5 menyisakan celah 4 mm antara PCB sensor dan PCB utama; v_maks ≈ 1,13 m/s |
| PCB utama | depan membulat 74 × 97, OLED 0,96" di tengah (socket 8,5), tombol A/B kiri-kanan, TB6612 di kanan OLED (socket, diputar 90°), buzzer + saklar di kiri | tata letak Ichiduino |
| ESP32 DevKit | **di sisi bawah PCB utama, disolder terbalik** (port USB ke kiri, Z 7,6–14,9) | supaya panjang robot ±160 mm; kalau ESP32 tetap di socket di atas, robot jadi ±180 mm |
| Belakang | motor N20 di atas PCB utama, dijepit dudukan 3D print; holder 2×18650 di atasnya; MP1584, charger (USB-C ke belakang), konektor baterai di bawah dudukan; BMS di sisi bawah PCB utama | baterai besar hanya muat di atas motor |
| Sayap | hitam, 3 panel, ujung depan runcing, endplate, 2 tiang miring | bentuk Ichiduino; sekaligus menutup baterai |
| Penahan depan | ball caster di bawah palm PCB sensor (tinggi total 9,3 mm) + 2 baut nilon anti-jungkit di ujung tanduk | |

### Ukuran (mm)

| | Ichiduino Pro | v12 | v13 |
|---|---|---|---|
| L × P × T | 125 × 143 × 55 | 111 × 179 × 55 | 120 × 160 × 70 |
| Sensor ke poros roda | – | ±133 | ±114 (sensor depan) |

Lebih tinggi dari Ichiduino karena holder 2×18650 (Ichiduino memakai LiPo 2S 400 mAh) dan sayap di atasnya.

### Yang perlu dicek / diputuskan

- **Roda Ø43 × 19 untuk as N20 (D 3 mm)**: cek ada di marketplace; RAB masih "Roda N20 Ø34 mm". Perhitungan
  motor perlu disesuaikan (jari-jari lebih besar → torsi di roda lebih besar).
- **OLED 0,96"** menggantikan 1,3" di RAB (lebih murah).
- **Ball caster** tinggi total 9,3 mm (RAB: "ball caster mini ±6 mm") → pakai spacer atau caster yang lebih tinggi.
- ESP32 tanpa socket dan mux/MCP23017 di sisi bawah PCB sensor: konfirmasi dulu, karena sebelumnya ESP32 di
  socket supaya mudah diakses.
- Ukuran modul masih nilai umum marketplace; ukur ulang dengan jangka sorong saat barang datang.

## Usulan v12 (13/10/2026): PCB utama v2 + PCB sensor 16 titik di dudukan + kabel pita

Model mengikuti `hardware/` (PCB utama v2 dan PCB sensor v2):

- **PCB utama v2:** ESP32 keluar dari bawah dudukan baterai (socket female 8,5 mm, USB ke kiri), TB6612 tengah
  depan dan OLED kanan (socket), MP1584 + dioda + pembagi tegangan baterai di bawah dudukan baterai, saklar +
  konektor baterai di tepi kanan, BMS ditempel di bawah PCB sisi kiri, box header IDC J5 di hidung.
- **PCB sensor batang lurus 110 × 51 mm:** 16 ITR20001 (jarak 6,5 mm, lebar baca ± 97 mm) di sisi bawah,
  16 LED indikator di atas, modul mux CD74HC4067 dan MCP23017 (socket) di belakang, box header IDC J1 di kanan.
- **Dudukan 3D print:** 2 lengan pendek setebal celah antar papan (Z 5,6–8 mm), dibaut dari atas lewat lubang
  bahu H3/H4 PCB utama dan dari bawah lewat lubang H1/H2 di sudut belakang PCB sensor.
- **Kabel pita 12 pin** dari J5 ke J1 (melengkung di atas TB6612).
- Tepi depan dudukan baterai dimundurkan ke Y 29,5 supaya tidak mepet dengan ESP32.

| | v11 | v12 (usulan) |
|---|---|---|
| P × L × T | ±174 × 110 × 55 | ±179 × 111 × 55 |
| Sensor ke poros roda | ±127 (tengah) | ±133 (16 sensor sebaris) |
| PCB sensor | 92 × 53 jangkar, 5 sensor | 110 × 51 batang, 16 sensor |

- Model 3D yang bisa diputar: https://claude.ai/artifact/MjwounZ25sDKUH1FWent3d
- File: `cadquery/ltm_v12.py`, `LTM_v12.step`, `render/ltm-v12-*.png`. Cek tabrakan antar bagian: tidak ada
  tabrakan baru (yang bersentuhan memang disengaja: lengan dudukan dengan pad lubang, kabel dengan konektor).
- Ukuran modul (ESP32, TB6612, OLED, modul mux) masih nilai umum marketplace: ukur ulang saat barang datang.

## Versi aktif: v11 (11/10/2026) — bentuk jangkar v10 + livery navy-merah-kuning + roda lebar Ø26 × 14

**Sudah disamakan dengan layout PCB v1-draft (`hardware/`, 11/10/2026 sore):** posisi komponen, lubang
baut, dan outline kedua PCB di model ini = koordinat di `hardware/tools/gen_pcb.py` saat itu. PCB utama di
`hardware/` sekarang v2 (13/10/2026), yang sudah diikuti model v12 di atas.

Mengikuti referensi di `docs/referensi/` (PCB sensor jangkar + leher panjang ala R3D Maker dan robot LF
edukasi 14 sensor) dan model Inventor kelompok (baterai di atas motor, sayap belakang). Warna terinspirasi
tim F1 Red Bull Racing (navy doff, merah, kuning) tanpa logo/merek.

- Model 3D yang bisa diputar: https://claude.ai/artifact/3rW7AaXeb6bug9ahwW6mWv
- File untuk Fusion 360: `LTM_v11.step` (File › Open › Open from my computer, atau Upload di Data Panel;
  tiap bagian jadi komponen terpisah lengkap dengan warna)
- Render untuk PPT: `render/ltm-v11-*.png` (iso, iso tanpa cover, atas, samping, belakang)
- Sumber model (parametrik, Python + CadQuery): `cadquery/ltm_v11.py` — semua tinggi diturunkan dari
  `D_RODA`; ganti angkanya lalu `python ltm_v11.py <folder>` → `model.json` + STEP

### Roda Ø26 × 14 "lonjong" (dari Ø34 × 8) — dampak

- v_maks teoritis = π × 0,026 × 500 / 60 ≈ **0,68 m/s** (sebelumnya 0,89); sasaran ≥ 0,5 m/s tetap tercapai.
- Torsi yang dibutuhkan di roda turun (jari-jari lebih kecil).
- Robot lebih rendah ±4 mm; jarak rangka ke lantai ±5 mm (lintasan harus rata).
- Roda lebar 14 mm dengan ban silikon bertepi bulat (dari atas terlihat lonjong, seperti robot LF
  pesaing dan model Inventor kelompok): cengkeraman lebih baik, lebar robot jadi ±110 mm.
- **Belum dibeli/dicek:** pastikan roda lebar ± Ø25–28 × 12–16 untuk as N20 (D 3 mm) ada di marketplace.
  Kalau tidak ada: velg 3D print + ban silikon/selang silikon. RAB (baris "Roda N20 Ø34 mm") dan perhitungan motor perlu disesuaikan.

### Susunan

| Bagian | Bentuk / posisi |
|---|---|
| PCB sensor | Jangkar: depan lebar ±26 dengan 5 sensor ITR20001 di sisi bawah (pola panah ringan), lengan lurus menyapu ±54° ke belakang; leher lebar 14 mm, ±28 mm terlihat, pangkal leher ±14 mm; resistor, MOSFET, kapasitor di sisi bawah leher; disambung ke PCB utama lewat pin header 2×5 (tembus ke J5) + 2 spacer nilon M3 di (±10,5; 83) |
| PCB utama | Siluet roket bersudut 94 × 84 (≤ 100 × 100): ESP32 DevKit melintang (USB ke kanan) separuh di bawah baterai, OLED di tengah di atas socket 8,5 mm (ada resistor & transistor di bawahnya), tombol A/B di depan, TB6612 kiri, MP1584 kanan, buzzer kanan depan, saklar + konektor baterai JST XH di tepi kiri belakang, konektor motor JST PH di belakang, lubang M3: standoff baterai (±32; 16), bahu (±37,5; 69), spacer sensor (±10,5; 83) |
| Penggerak | 2× N20 melintang saling membelakangi, roda lebar Ø26 × 14 (velg kuning, ban tepi bulat) di luar, rangka 3D print navy (dinding motor + dudukan baterai + telinga belakang) |
| Baterai | Holder 2×18650 di atas motor, ditutup **cover navy bersudut** (strip merah, garis & hidung kuning; bisa dilepas) |
| Belakang | Dinding belakang dengan port USB-C charger + ventilasi, skid anti-terjungkal, **sayap belakang** navy dengan endplate merah (opsional) |

### Ukuran utama (mm)

| | |
|---|---|
| P × L × T | ±174 × 110 × 55 (tanpa sayap belakang: ±162 × 110 × 48) |
| Jarak roda (pusat) | 94 |
| Sensor ke poros roda | ±127 |
| Tinggi sensor dari lantai | ±1,5 |
| PCB utama | 94 × 84, Z 8; BMS ditempel di sisi bawahnya (ada tanda silkscreen), ball caster di (0; 62) |
| PCB sensor | 92 × 53 (jangkar + leher), Z 4; jarak ke PCB utama 2,4 mm (plastik pin header) |

Ukuran komponen modul masih nilai standar marketplace; cek ulang dengan jangka sorong saat barang datang,
lalu ubah angka di `cadquery/ltm_v11.py` dan ekspor ulang.

## Versi lama

- v10 (bentuk sama, cover oranye, roda Ø34): ada di riwayat git (commit "Mekanik v10 jangkar").
- v9 rata (`docs/minsys-v1.md`, artifact minsys) dan konsep ringkas tanpa leher (`konsep-ringkas.png`,
  `fusion360/` script kotak-kotak) — digantikan v10 karena tidak sesuai referensi.
