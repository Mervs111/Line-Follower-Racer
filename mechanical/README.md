# Mekanik — Robot Line Tracer Micro

## Versi aktif: v10 "jangkar" (11/10/2026)

Mengikuti referensi di `docs/referensi/` (PCB sensor jangkar + leher panjang ala R3D Maker dan robot LF
edukasi 14 sensor) dan model Inventor kelompok (baterai oranye di atas motor, sayap belakang).

- Model 3D yang bisa diputar: https://claude.ai/artifact/3rW7AaXeb6bug9ahwW6mWv
- File untuk Fusion 360: `LTM_v10_jangkar.step` (Insert › Insert Mesh/Upload, atau buka langsung; tiap
  bagian jadi komponen terpisah lengkap dengan warna)
- Render untuk PPT: `render/ltm-v10-*.png` (iso, iso tanpa cover, atas, samping, belakang)
- Sumber model (parametrik, Python + CadQuery): `cadquery/ltm_v10_jangkar.py`
  (`pip install cadquery`, lalu `python ltm_v10_jangkar.py <folder>` → `model.json` + STEP)

### Susunan

| Bagian | Bentuk / posisi |
|---|---|
| PCB sensor | Jangkar: depan lebar ±26 dengan 5 sensor (pola panah ringan), lengan lurus menyapu ±54° ke belakang, 4 slot cadangan di lengan; leher 14 mm × ±33 mm terlihat; disambung ke PCB utama lewat 2 spacer M3 + header |
| PCB utama | Siluet roket bersudut 94 × 84 (≤ 100 × 100): ESP32 DevKit melintang (USB ke kanan) separuh di bawah baterai, OLED di tengah, tombol A/B di bawah OLED, TB6612 kiri, MP1584 kanan, buzzer, saklar di tepi kiri |
| Penggerak | 2× N20 melintang saling membelakangi, roda Ø34 di luar, rangka 3D print (dinding motor + dudukan baterai + telinga belakang) |
| Baterai | Holder 2×18650 di atas motor, ditutup **cover oranye bersudut** (bisa dilepas) |
| Belakang | Dinding belakang dengan port USB-C charger + ventilasi, skid anti-terjungkal, **sayap belakang** (opsional) |

### Ukuran utama (mm)

| | |
|---|---|
| P × L × T | ±174 × 98 × 59 (tanpa sayap belakang: ±162 × 98 × 50) |
| Jarak roda (pusat) | 88 |
| Sensor ke poros roda | ±127 |
| Tinggi sensor dari lantai | ±1,5 |
| PCB utama | 94 × 84, Z 10 |
| PCB sensor | 92 × 53 (jangkar + leher), Z 4 |

Ukuran komponen modul masih nilai standar marketplace; cek ulang dengan jangka sorong saat barang datang,
lalu ubah angka di `cadquery/ltm_v10_jangkar.py` dan ekspor ulang.

## Versi lama

- v9 rata (`docs/minsys-v1.md`, artifact minsys) dan konsep ringkas tanpa leher (`konsep-ringkas.png`,
  `fusion360/` script kotak-kotak) — digantikan v10 karena tidak sesuai referensi.
