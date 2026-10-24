# Rakitan PCB LFM (24/10/2026)

PCB sensor rev B (`hardware/sensor-garis/`) dan PCB utama hasil layout (`hardware/pcb-utama/`) digabung di posisi
pasangnya, ditambah bagian mekanik model v16 (roda, motor, baterai, modul, kabel, sayap), untuk melihat bentuk dan
ukuran robot dengan PCB yang sebenarnya.

- Viewer 3D dengan garis ukuran dan alat ukur: https://claude.ai/artifact/7JpKSCkUepxGQdxK5ZhVpv
- Sumber: `gen_rakitan.py` (`py gen_rakitan.py`, sekitar 30 detik). Butuh KiCad 10 (`kicad-cli`), numpy, dan
  Node.js (`npx gltfpack@1.2.0` untuk kompresi).

| File | Isi |
|---|---|
| `LFM_rakitan.glb` | rakitan lengkap (mm, terkuantisasi). Bisa dibuka di Blender atau penampil glTF lain |
| `LFM_rakitan_web.json` | GLB yang sama dengan kompresi meshopt, di-base64 (artifact claude.ai tidak menyajikan file .glb). Dibaca `index.html` |
| `index.html` | viewer: tampak Iso/Atas/Samping/Depan/Bawah, garis ukuran per tampak, tombol Ukur (klik dua titik), tabel ukuran |
| `LFM_rakitan_pcb.step` | STEP kedua PCB + komponen (3,6 MB) untuk Fusion 360 / FreeCAD / SolidWorks. Dibuat `gen_rakitan_step.py` |
| `LFM_rakitan_pcb_tembaga.step` | sama, + jalur, pour, pad, silkscreen, mask (21 MB, tidak masuk git): `py gen_rakitan_step.py --tembaga` |

## Cara kerja skrip

1. Kedua board diekspor dengan `kicad-cli pcb export glb` (tembaga, pour, silkscreen, mask, komponen) dengan titik asal
   (200; 180,55) = tengah poros roda, jadi hasilnya langsung koordinat robot (sama dengan konvensi proyek KiCad).
2. Footprint di `pcb-utama.kicad_pcb` belum punya baris `(model ...)` (dibuat lewat skrip), jadi skrip menyalin board ke
   folder sementara dan menambahkan model 3D dari pustaka KiCad. File di `hardware/` tidak diubah. Footprint `ltm`
   (ESP32, TB6612, MP1584) tidak punya model 3D; modulnya diambil dari model v16.
3. Tinggi papan sama dengan v16: sisi bawah PCB sensor 4,8 mm dari lantai, PCB utama 10,4 mm (spacer nilon 4 mm).
4. Bagian v16 yang sudah ada di file KiCad (papan, sensor, konektor, tombol, resistor, dll.) dibuang. Data v16 dibaca
   dari `mechanical/viewer/model.json`. ESP32 digeser 3,5 mm ke kiri mengikuti U1 di layout.
5. Semua digabung per material, ukuran utama ditulis di `extras` node akar GLB, lalu dikompres dengan gltfpack.

## STEP (`gen_rakitan_step.py`, sekitar 15 detik)

Sumbu sama dengan `mechanical/v16/step/LTM_v16_rakitan.step`: X kanan, Y maju, Z atas, **nol = lantai di bawah tengah
poros roda**, jadi bisa ditumpuk langsung dengan STEP v16 (sembunyikan PCB sederhana v16) atau dengan bagian cetak 3D.
Isinya dua sub-rakitan, `PCB_SENSOR` (alas di Z 4,8) dan `PCB_UTAMA` (alas di Z 10,4). Modul ESP32, TB6612, dan MP1584
tidak ada karena footprint `ltm` tidak punya model 3D.

Caranya tanpa CadQuery: tiap board diekspor `kicad-cli pcb export step` (PCB utama lewat salinan yang diberi model
pustaka), lalu kedua STEP dipasang sebagai model 3D dua footprint bantu di board kosong dan board itu diekspor lagi.
`--cek` membuka ulang hasilnya lewat KiCad dan mencetak kotak pembatasnya (24/10: X −52,2…50,0, Y −34,0…131,0,
Z 3,08…21,62, sama dengan rakitan GLB).

## Ukuran (dari file KiCad 24/10)

| | mm |
|---|---|
| Robot lengkap (P × L × T) | 165,0 × 115,6 × 62,1 (lebar tanpa sayap 104,8 di roda, tinggi tanpa sayap 44,2) |
| PCB utama | 100,0 × 127,0 |
| PCB sensor | 94,4 × 51,0; masuk 13,0 di bawah hidung PCB utama |
| Poros roda → sensor tengah (6/7) | 126,3 (ke sensor ujung 1/12: 114,7) |
| Barisan 12 sensor | 82,8 (tengah sensor 1 → 12) |
| Jarak roda (tengah ban) | 91,0, roda Ø34 |
| Muka QRE1113GR dari lantai | 3,3 |

Catatan dari rakitan:

- **Kaki THT J1 (JST XH) menonjol 1,7 mm di bawah PCB sensor**, jadi titik terendahnya 3,1 mm dari lantai, lebih rendah
  dari muka sensor. Potong kaki J1 serata mungkin sesudah disolder.
- Kaki socket OLED (J4) di PCB utama berada tepat di atas tepi belakang PCB sensor, celah tegak 2,5 mm. Aman, tapi
  jangan diberi spacer lebih pendek dari 4 mm.
- Warna solder mask hijau = bawaan KiCad (stackup belum diberi warna).
