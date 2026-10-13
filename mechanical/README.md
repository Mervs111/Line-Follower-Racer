# Mekanik — Robot Line Tracer Micro

## Usulan v12 (13/10/2026): leher sensor dipendekkan 20 mm, PCB belum diubah

v11 dengan ujung depan jangkar dimundurkan 20 mm (`F` 132 → 112). Belum dipakai: PCB sensor di
`hardware/` masih ukuran v11.

| | v11 | v12 (usulan) |
|---|---|---|
| P × L × T | ±174 × 110 × 55 | ±154 × 110 × 55 (tanpa sayap ±142) |
| Sensor tengah ke poros roda | ±127 | ±107,5 |
| PCB sensor | 92 × 53 | 92 × 33 (leher terlihat ±8 mm) |

- Tulisan "LINE TRACER MICRO" dan "P01 KEL.5" pindah ke lengan jangkar (leher terlalu pendek).
- R1–R10 sebaris di bawah pangkal leher, R11/R12/Q1/C1 di depannya: posisi usulan, belum dirouting.
- Ini batas terpendek tanpa mengubah PCB utama (J5 dan tombol A/B ada di hidung PCB utama). Kalau mau lebih
  pendek (sensor ±80 mm dari poros), hidung PCB utama ikut dirombak.
- Model 3D yang bisa diputar: https://claude.ai/artifact/MjwounZ25sDKUH1FWent3d
- File: `cadquery/ltm_v12.py`, `LTM_v12.step`, `render/ltm-v12-*.png`. Cek tabrakan antar bagian: tidak ada
  tabrakan baru dibanding v11.

## Versi aktif: v11 (11/10/2026) — bentuk jangkar v10 + livery navy-merah-kuning + roda lebar Ø26 × 14

**Sudah disamakan dengan layout PCB v1-draft (`hardware/`, 11/10/2026 sore):** posisi komponen, lubang
baut, dan outline kedua PCB di model ini = koordinat di `hardware/tools/gen_pcb.py`.

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
