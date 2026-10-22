# Mekanik — Robot Line Tracer Micro

## Usulan v15 (20/10/2026): PCB sensor gaya JSumo XLINE + 12 QRE1113GR

Keputusan kelompok 20/10 (sesudah v14): PCB sensor dibuat seperti **JSumo XLINE** (foto: `docs/referensi/ref-jsumo-xline.png`)
dengan **12 sensor QRE1113GR** (LED IR + fototransistor dalam satu kemasan SMD), warna **hitam**. Bagian lain sama
dengan v14 (PCB utama 100 × 121, ESP32 di atas, roda Ø34, dudukan baterai, sayap belakang).

- Model 3D yang bisa diputar: https://claude.ai/artifact/AKgsuWNwB9LYzNtRYeSRqo
- Perbandingan dengan foto XLINE: `render/ltm-v15-banding-xline.png` (PCB sensor dilihat dari bawah = sisi sensor)
- Sumber: `cadquery/ltm_v15.py` (`python ltm_v15.py <folder>`, `CHECK=1` untuk cek tabrakan: hasil terakhir 0)

### PCB sensor

| | v15 |
|---|---|
| Bentuk | pita 13 mm: bagian tengah lurus + 2 sayap miring 30° ke belakang, badan tengah 34 mm (IC mux + J1), tab 27 mm masuk ke bawah hidung PCB utama |
| Sensor | 12 QRE1113GR di sisi bawah, jarak 9 mm sepanjang pita; sensor 4 dan 9 tepat di tekukan (diputar 15°); 6 di bagian tengah, 3 di tiap sayap; lebar baca ±92 mm |
| Tinggi | sisi bawah PCB Z 4,8 → muka sensor ±3 mm dari lantai (jarak baca QRE1113 yang dipakai Pololu/SparkFun) |
| Resistor | R LED 220 Ω + R pull-up 10k, 0805, di samping luar tiap sensor (sisi bawah), seperti XLINE |
| Nomor | 1–12 dari kiri ke kanan, dicetak di kedua sisi |
| Pemasangan | 2 baut M3 + spacer nilon 4 mm di X ±9, Y 78 (kepala baut di bawah OLED: cabut OLED dulu) |
| Mux | IC CD74HC4067 SOIC-24 lebar (simbol KiCad CD74HC4067M, footprint SOIC-24W_7.5x15.4mm_P1.27mm) disolder langsung di badan tengah, sisi atas, + C 100 nF 0805 di sebelahnya (21/10, pengganti modul di socket); jalur 0,3 mm sesuai aturan cetak 21/10 (`docs/aturan-cetak-pcb.md`) |
| Penahan | skid nilon M3 di tab tepat di belakang J1 (menyentuh lantai; baut dari bawah, mur di atas, pasang sebelum PCB sensor dibaut) + skid M2 di ujung sayap (1 mm di atas lantai); lubang M2 kedua di tiap ujung sayap cadangan |
| Ukuran robot | ±118 × 165 × 62 mm |

Posisi sensor untuk KiCad (titik 0,0 = tengah tepi depan PCB sensor, Y ke belakang; sudut dilihat dari atas,
positif = berlawanan jarum jam), juga ada di `v15/dxf/pcb_sensor_posisi_qre1113.csv`:

| No | X | Y | Putar | | No | X | Y | Putar |
|---|---|---|---|---|---|---|---|---|
| 1 | −45,88 | 19,50 | +30° | | 7 | 4,50 | 6,00 | 0° |
| 2 | −38,09 | 15,00 | +30° | | 8 | 13,50 | 6,00 | 0° |
| 3 | −30,29 | 10,50 | +30° | | 9 | 22,50 | 6,00 | −15° |
| 4 | −22,50 | 6,00 | +15° | | 10 | 30,29 | 10,50 | −30° |
| 5 | −13,50 | 6,00 | 0° | | 11 | 38,09 | 15,00 | −30° |
| 6 | −4,50 | 6,00 | 0° | | 12 | 45,88 | 19,50 | −30° |

Sisi 3,6 mm QRE1113GR tegak lurus pita (LED di depan). Karena sensor di sisi bawah, di KiCad komponennya dibalik
ke B.Cu, dan tanda sudut ikut terbalik; cocokkan dengan DXF `pcb_sensor_posisi_qre1113.dxf`.

### File (`v15/`)

Sama dengan v14, kecuali: `step/pcb_sensor.step` + `dxf/pcb_sensor_outline.dxf` (bentuk XLINE),
`dxf/pcb_sensor_posisi_qre1113.dxf` + `.csv` (posisi 12 sensor), `step/LTM_v15_rakitan.step`. Masker sensor v14
tidak dipakai lagi.

### Yang perlu dicek

- **QRE1113GR** belum ditemukan di marketplace lokal. RS Components Indonesia ± Rp11.600/pcs (pak isi 5): kalau
  beli di sana, RAB lewat batas. RAB memakai perkiraan impor Rp5.000/pcs; cek harga + ongkir dan pilih penjual
  berulasan baik (banyak barang tiruan).
- R LED 220 Ω (±17 mA) dan pull-up 10k: uji di breadboard dulu (pull-up 10k–47k).
- Skid ujung sayap 1 mm di atas lantai: setel ulang kalau robot menggesek di tikungan.

## Versi lama

Usulan v11–v14 (STEP, DXF/STL, sumber CadQuery, viewer, render) dan konsep sebelumnya ada di
`arsip/mechanical/` (penjelasan di `arsip/mechanical/README.md`).
