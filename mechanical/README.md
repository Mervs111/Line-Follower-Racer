# Mekanik — Robot Line Tracer Micro

## Versi aktif: v11 (11/10/2026) — bentuk jangkar v10 + livery navy-merah-kuning + roda Ø26

Mengikuti referensi di `docs/referensi/` (PCB sensor jangkar + leher panjang ala R3D Maker dan robot LF
edukasi 14 sensor) dan model Inventor kelompok (baterai di atas motor, sayap belakang). Warna terinspirasi
tim F1 Red Bull Racing (navy doff, merah, kuning) tanpa logo/merek.

- Model 3D yang bisa diputar: https://claude.ai/artifact/3rW7AaXeb6bug9ahwW6mWv
- File untuk Fusion 360: `LTM_v11.step` (File › Open › Open from my computer, atau Upload di Data Panel;
  tiap bagian jadi komponen terpisah lengkap dengan warna)
- Render untuk PPT: `render/ltm-v11-*.png` (iso, iso tanpa cover, atas, samping, belakang)
- Sumber model (parametrik, Python + CadQuery): `cadquery/ltm_v11.py` — semua tinggi diturunkan dari
  `D_RODA`; ganti angkanya lalu `python ltm_v11.py <folder>` → `model.json` + STEP

### Roda Ø26 (dari Ø34) — dampak

- v_maks teoritis = π × 0,026 × 500 / 60 ≈ **0,68 m/s** (sebelumnya 0,89); sasaran ≥ 0,5 m/s tetap tercapai.
- Torsi yang dibutuhkan di roda turun (jari-jari lebih kecil).
- Robot lebih rendah ±4 mm; jarak rangka ke lantai ±5 mm (lintasan harus rata).
- **Belum dibeli/dicek:** pastikan roda ± Ø25–28 untuk as N20 (D 3 mm) ada di marketplace. Kalau tidak ada:
  velg 3D print + ban O-ring/karet. RAB (baris "Roda N20 Ø34 mm") dan perhitungan motor perlu disesuaikan.

### Susunan

| Bagian | Bentuk / posisi |
|---|---|
| PCB sensor | Jangkar: depan lebar ±26 dengan 5 sensor (pola panah ringan), lengan lurus menyapu ±54° ke belakang, 4 slot cadangan di lengan; leher lebar 14 mm, ±28 mm terlihat; disambung ke PCB utama lewat 2 spacer M3 + header |
| PCB utama | Siluet roket bersudut 94 × 84 (≤ 100 × 100): ESP32 DevKit melintang (USB ke kanan) separuh di bawah baterai, OLED di tengah, tombol A/B di bawah OLED, TB6612 kiri, MP1584 kanan, buzzer, saklar di tepi kiri |
| Penggerak | 2× N20 melintang saling membelakangi, roda Ø26 (velg kuning) di luar, rangka 3D print navy (dinding motor + dudukan baterai + telinga belakang) |
| Baterai | Holder 2×18650 di atas motor, ditutup **cover navy bersudut** (strip merah, garis & hidung kuning; bisa dilepas) |
| Belakang | Dinding belakang dengan port USB-C charger + ventilasi, skid anti-terjungkal, **sayap belakang** navy dengan endplate merah (opsional) |

### Ukuran utama (mm)

| | |
|---|---|
| P × L × T | ±174 × 98 × 55 (tanpa sayap belakang: ±162 × 98 × 48) |
| Jarak roda (pusat) | 88 |
| Sensor ke poros roda | ±127 |
| Tinggi sensor dari lantai | ±1,5 |
| PCB utama | 94 × 84, Z 8; BMS di sisi bawahnya |
| PCB sensor | 92 × 53 (jangkar + leher), Z 4 |

Ukuran komponen modul masih nilai standar marketplace; cek ulang dengan jangka sorong saat barang datang,
lalu ubah angka di `cadquery/ltm_v10_jangkar.py` dan ekspor ulang.

## Versi lama

- v10 (bentuk sama, cover oranye, roda Ø34): ada di riwayat git (commit "Mekanik v10 jangkar").
- v9 rata (`docs/minsys-v1.md`, artifact minsys) dan konsep ringkas tanpa leher (`konsep-ringkas.png`,
  `fusion360/` script kotak-kotak) — digantikan v10 karena tidak sesuai referensi.
