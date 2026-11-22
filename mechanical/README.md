# Mekanik — Robot Line Tracer Micro

## Badan cetak X1 (22/11/2026): STL siap cetak dari konsep v18

Sasis, tutup klem motor, rangka interface, velg + ban TPU, skid sensor, dan potongan uji untuk Bambu Lab A1, semua di
`cetak-x1/stl/` (posisi cetak, tanpa support). Viewer + petunjuk: https://claude.ai/artifact/PNojYiuq8fW5ogUY8qWuLw.
Penjelasan, setelan, baut, dan hasil cek di `cetak-x1/README.md`.

## Konsep v18 (14/11/2026): susunan A "ransel" dipilih user, semua PCB punya pengikat

Model 3D yang bisa diputar + gambar urai (tombol **Urai**): https://claude.ai/artifact/Q4KdmPtV6vY7v5J78FXZrm
(`konsep-v18/gen_konsep.py` → `konsep-v18.html` + `konsep-v18-model.json` + `interface-rev-b.png`, jalankan dengan `py`;
untuk melihat lokal, bungkus HTML-nya dengan `<html><body>` dan sajikan foldernya lewat `py -m http.server` karena
halaman mengambil JSON dengan `fetch`). Model dirakit dari mesh v16 (`viewer/model.json`) + bentuk buatan skrip, tanpa
CadQuery; belum ada STEP/STL.

- **Baterai**: pack Li-ion 14500 7,4 V 50 × 30 × 15 mm, 46 g, rebah tepat di belakang motor, strap velcro 16 mm lewat
  celah skid plate + bibir 4 mm. Puncak baterai 27 mm (v17: 44 mm), panjang 174 mm, lebar 115 mm, perkiraan ±230 g.
- **Cara pasang PCB**:

  | Bagian | Pengikat |
  |---|---|
  | PCB sensor rev B | 2 baut M3 × 10 dari bawah di H1/H2, spacer nilon ±3,5 mm, mur di atas hidung skid plate |
  | PCB utama rev B | 4 baut M3 × 30 kepala benam dari bawah skid plate, boss 3 mm menyatu dengan skid plate |
  | Rangka interface (3D print, baru) | pelat 2,5 mm + 4 kaki 19,5 mm di 4 baut M3 yang sama, mur di atas kaki |
  | Board interface rev B | 4 baut M2 × 6 ke boss rangka, tepi belakang bertumpu di balok rangka, header ke J6 |
  | OLED | socket 4 pin + 4 spacer M2 ±11 mm, baut di 2 lubang atas |

- **Koreksi tinggi**: plastik header pin (2,54 mm) antara socket dan ESP32/OLED sekarang ikut dihitung. Puncak ESP32
  32,3 mm (model lama 29,8), board interface z 36,1–37,7 (dulu 33), puncak robot (kaca OLED) 51,4 mm.
- Cek kotak pembatas (rangka terhadap komponen PCB utama, kabel, jalur USB, tuas SW1; kaki solder board interface
  terhadap ESP32): 0 masalah. Kaki solder ESP32 dan tinggi nyata modul belum diukur.
- Riwayat: versi 1 (2× 18650 rebah) ditolak user; versi 2 membandingkan tiga susunan pack (A ransel, B bak, C tengah),
  ada di commit 620f487. Konsep v17 (PCB ringkas + board interface, skid plate) ada di `konsep-v17/`.

## Rakitan PCB LFM (24/10/2026): v16 dengan PCB asli dari KiCad

PCB sensor rev B dan PCB utama hasil layout diekspor langsung dari KiCad lalu digabung dengan bagian mekanik v16.
Viewer dengan garis ukuran dan alat ukur: https://claude.ai/artifact/7JpKSCkUepxGQdxK5ZhVpv. Penjelasan, ukuran, dan
cara membuat ulang di `rakitan-pcb/README.md`. `viewer/model.json` = data viewer v16 (dibaca `viewer/v16.html` dan
skrip rakitan).

## v16 (22/10/2026): v15 + PCB sensor rev B (jangkar) dari KiCad

Model v15 disamakan dengan **PCB sensor rev B** buatan user (`hardware/sensor-garis/`). Bentuk papan, lubang, dan
posisi komponen PCB sensor **dibaca langsung dari file `.kicad_pcb`**, jadi kalau PCB sensor direvisi, cukup jalankan
ulang skripnya. Roda Ø34, dudukan baterai, dan sayap belakang sama dengan v15. Outline PCB utama diganti ke bentuk
**"mobil F1"** (22/10, pilihan user): sidepod lebar, pinggang lengkung di antara roda, hidung panjang (100 × 127 mm).

- Model 3D yang bisa diputar: https://claude.ai/artifact/C6BMXLgUPLJN5Aubm8uyx3
- Render: `render/ltm-v16-{iso,atas,bawah,depan,samping,belakang}.png`
- Sumber: `cadquery/ltm_v16.py` (`python ltm_v16.py <folder>`, `CHECK=1` untuk cek tabrakan: hasil terakhir 107
  bagian, 0 tabrakan). Viewer lokal: `viewer/v16.html` + `model.json` hasil skrip.

| | v16 |
|---|---|
| PCB sensor | rev B: bentuk jangkar, lebar 95 mm, 12 QRE1113GR jarak 8 mm di busur (sisi bawah), IC mux SOIC-24 + C1 + J1 di tangkai (sisi atas), tepi depan tetap Y 131 (jarak sensor ke poros roda sama dengan v15) |
| Pemasangan | 2 baut M3 di H1/H2 ujung tangkai (robot X ±4,75, Y 85,55), spacer nilon 4 mm, mur di atas PCB utama |
| Penahan depan (usulan) | **skid nilon di kedua baut H1/H2**: baut nilon dari bawah, kepala kubah menyentuh lantai. Rev B tidak punya lubang skid terpisah, jadi skid ujung sayap v15 hilang. Perlu dikonfirmasi user |
| Kabel | **JST XH 8 pin** J5 (PCB utama) ↔ J1 (PCB sensor), urutan pin sama: 1 +5V, 2 +3V3, 3 GND, 4–7 MUX_S3..S0, 8 MUX_SIG. Pengganti kabel pita IDC |
| J5 | sejajar tepi miring **sidepod kiri** PCB utama (sidepod kanan penuh: TB6612, buzzer; hidung terpakai OLED, tombol, baut H1/H2). Tengah rumah robot (−37,24; 55,12), diputar 205,6°, **pin 1 di ujung dekat hidung** (−29,34; 58,89). Kabel dibundel menyusuri tepi kiri hidung (kiri tombol A) lalu masuk J1 dari depan, tidak bersilangan |
| C1 elko | pindah ke sidepod kiri (−37; 40) |
| Ukuran robot | ±116 × 165 × 62 mm |

Posisi 12 sensor (dari KiCad; titik 0,0 = tengah tepi depan PCB sensor, Y ke belakang) ada di
`v16/dxf/pcb_sensor_posisi_qre1113.csv`; untuk firmware pakai tabel di `hardware/sensor-garis/REVISI.md`.

### File (`v16/`)

- `step/`: `LTM_v16_rakitan.step`, `pcb_sensor.step` (rev B), `pcb_utama.step`, `roda_34x12.step`, bagian cetak 3D
- `stl/`: dudukan motor + baterai, sayap belakang, tiang sayap
- `dxf/`: outline PCB utama dan PCB sensor, posisi QRE1113GR (DXF + CSV)

### Yang perlu dicek

- Skid di H1/H2: tinggi kepala baut nilon harus pas supaya muka sensor ±3 mm dari lantai.
- Posisi J5 hanya usulan untuk PCB utama baru (`hardware/pcb-utama/`); boleh dipindah selama urutan pin sama.

## v15 (20/10/2026, digantikan v16): PCB sensor gaya JSumo XLINE

PCB sensor pita 13 mm (tengah lurus + sayap 30°), 12 QRE1113GR jarak 9 mm, IC mux di badan tengah, skid di tab dan
ujung sayap, kabel pita IDC. Model: https://claude.ai/artifact/AKgsuWNwB9LYzNtRYeSRqo. File tetap di `v15/`,
`cadquery/ltm_v15.py`, `viewer/v15.html`, `render/ltm-v15-*.png`.

## Versi lama

Usulan v11–v14 (STEP, DXF/STL, sumber CadQuery, viewer, render) dan konsep sebelumnya ada di
`arsip/mechanical/` (penjelasan di `arsip/mechanical/README.md`).
