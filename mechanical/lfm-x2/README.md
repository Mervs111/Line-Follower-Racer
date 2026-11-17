# Rakitan LFM X2 + bagian cetak 3D (16/11/2026)

Keempat papan LFM X2 rev B (`hardware/lfm-x2/`) ditumpuk di tinggi rancangan, ditambah motor N20 + roda, OLED, LiPo,
baut, kabel, dan **usulan rangka cetak 3D** (belum disetujui user; rangka X2 sebelumnya belum pernah digambar).

- Viewer 3D: https://claude.ai/artifact/NV6wvHKBGvuGv3AQEQm5ZU (mode Rakitan / Urai / Bagian cetak, Sorot cetak, Ukur)
- Sumber: `py mechanical/lfm-x2/gen_rakitan_x2.py` (sekitar 15 detik). Butuh KiCad 10 (`kicad-cli`), numpy,
  shapely ≥ 2.1, Node.js (gltfpack, dari cache npx). Papan diekspor ulang dari file KiCad tiap kali skrip jalan, jadi
  jalankan lagi sesudah papan berubah lalu publish ulang `index.html`.

| File | Isi |
|---|---|
| `gen_rakitan_x2.py` | generator: ekspor GLB 4 papan, bangun bagian cetak, STL, cek tabrakan, GLB web |
| `index.html` | viewer (sumber artifact) |
| `LFM_X2_web.json` | GLB rakitan (meshopt, base64) yang dibaca `index.html` |
| `stl/x2_rangka_motor.stl`, `x2_dudukan_baterai.stl`, `x2_skid_depan.stl` | bagian cetak di posisi cetak (alas z = 0, mm), tertutup rapat (dicek trimesh) |

## Bagian cetak (usulan)

| Bagian | Ukuran cetak (mm) | Padat PETG | Isi |
|---|---|---|---|
| Rangka motor | 96,0 × 42,0 × 14,4 | 7,70 cm³ / 9,8 g | klem gearbox kedua N20 (alur 12,3 × 10,1 terbuka ke atas), tumpuan kaleng motor, rusuk belakang, lengan ke telinga (±44; 23,5) dengan **tiang 11 mm** yang menggantikan 2 spacer driver ↔ papan utama, 4 kantong mur M3 di bawah. Alas datar di z 7,6 = muka atas papan driver |
| Dudukan baterai | 75,0 × 45,6 × 7,0 | 7,49 cm³ / 9,5 g | alas LiPo (ruang 56 × 31 mm, siku di 4 pojok, strap velcro 16 mm) yang sekaligus **tutup klem gearbox**: 4 baut M3 × 18 ke mur di rangka. Kantong PCB encoder di bawah (jembatan 3,5 mm). Tab kanan mulai x 30 supaya steker XT30 lewat |
| Skid depan | 9,0 × 9,0 × 4,5 | 0,15 cm³ / 0,2 g | kubah di lubang depan papan sensor (0; 134,3), mur M3 tertanam, baut M3 × 5 dari atas. Tinggi 4,5 = sisi bawah papan sensor ke lantai |

Semua tanpa support. Saran: PETG, lapisan 0,2 mm, 4 dinding, infill 40 %. Massa = padat 100 % (batas atas).
Baut tambahan: 2 × M3 × 16 + mur (telinga), 4 × M3 × 18 + mur (dudukan baterai), 1 × M3 × 5 + mur (skid).

Cara membangun tanpa CadQuery: tiap bagian = tumpukan ekstrusi 2D (shapely). Tiap selang z punya satu poligon
berlubang (tambah − potong); dinding dari cincin poligon, tutup dari selisih poligon selang bawah dan atas, lalu
dinding dipecah di titik tutup supaya tidak ada sambungan-T. Skid = benda putar dengan kantong heksagon.

## Hasil cek (17/11, keempat papan sudah dirouting, sensor QRE1113GR)

- Bagian cetak tidak menabrak komponen KiCad (kotak pembatas tiap referensi + poligon tepi papan), motor, ban, atau
  steker. Celah terkecil: ban 1,9 · steker XT30 1,9 · konektor J2/J3 driver 1,05 · skid ke sensor tengah U6/U7 2,0 mm.
- **Di luar bagian cetak**: J2/J3 driver JST XH **siku** (S6B-XH-A, pilihan user) masih menumpuk dengan kaleng motor
  N20, tutup motor, dan PCB encoder; steker yang masuk dari belakang juga jatuh di bawah motor. Versi tegak (B6B-XH-A)
  punya posisi pad yang sama, jadi bisa ditukar tanpa routing ulang.
- Ukuran robot 171,1 × 117,7 × 46,5 mm (batas guidebook 250 × 200 × 100). Titik terendah selain roda + skid: muka
  sensor QRE1113GR 2,8 mm, kepala baut leher sensor 2,8, kepala baut telinga 3,0, alas rangka 7,6.

## Belum diputuskan
- Rancangan rangka ini sendiri (usulan Claude), warna/bahan, printer lab.
- Ukuran alur gearbox (12,3 × 10,1) dan kantong mur (lebar kunci 5,7) perlu dicocokkan dengan barang asli; cetak uji
  potongan klem dulu.
- LiPo belum dipilih: model memakai Tattu 2S 300 mAh 47 × 17 × 13 sebagai contoh, ruang dudukan 56 × 31.
- Roda: model memakai Ø34 × 18 (sama dengan konsep v18 dan gambar susunan X2).
