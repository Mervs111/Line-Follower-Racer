# Mekanik — Robot Line Tracer Micro

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
