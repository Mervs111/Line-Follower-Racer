# Badan cetak 3D LFM X1 (22/11/2026)

Versi siap cetak dari konsep v18 (`mechanical/konsep-v18/`, susunan A "ransel" pilihan user 14/11) untuk **Bambu Lab
A1** (printer user, nozzle 0,4; PLA, PETG, TPU sudah punya profil di Bambu Studio). Permintaan user: sasis + dudukan
motor/baterai, rangka interface, velg Ø34 × 18; motor, ball caster, dan baterai belum dibeli.

- Viewer 3D (Rakitan / Sorot cetak / Alas cetak A1) + petunjuk: https://claude.ai/artifact/PNojYiuq8fW5ogUY8qWuLw
- Sumber: `py mechanical/cetak-x1/gen_cetak_x1.py` (±15 detik). Butuh KiCad 10 (python KiCad membaca ketiga PCB X1),
  numpy, shapely ≥ 2.1, trimesh. Jalankan ulang sesudah PCB berubah, lalu publish ulang `index.html` bersama
  `cetak-x1-model.json`.

| File | Isi |
|---|---|
| `gen_cetak_x1.py` | generator: baca KiCad, bangun bagian cetak, STL, cek tabrakan/baut/massa, data viewer |
| `stl/*.stl` | bagian cetak di posisi cetak (alas z = 0, mm), tertutup rapat (dicek trimesh), tanpa support |
| `index.html` + `cetak-x1-model.json` | viewer (sumber artifact); JSON = mesh konsep v18 + bagian cetak, base64 |

## Bagian cetak

| File | Jml | Ukuran cetak (mm) | Padat | Isi |
|---|---|---|---|---|
| `x1_sasis` | 1 | 114,2 × 140,5 × 11,6 | 33,6 g | skid plate 2 mm (z 10–12), **bawah rata** (permintaan user 22/11) + bibir tepi 2,5 mm; alur kedua motor (rel 12,4 mm, ganjal gearbox di sudut bawah alur x 24,5–28,4); 4 boss baut tutup klem + kantong mur dari bawah; 4 boss PCB utama 3 mm + kepala benam; lubang H1/H2 PCB sensor; kantong pack 54 × 31 + bibir 4 mm; 2 celah strap 17,5 × 2,2; kantong buntu dari atas di bawah kaki THT PCB utama (lantai 1,0 mm) dan piringan encoder (lantai 0,6 mm). Di muka bawah hanya ada lubang baut, kantong mur/kepala benam, dan celah strap |
| `x1_tutup_klem_kanan`, `_kiri` | 1+1 | 21,2 × 32,1 × 3,0 | 1,9 g | pelat di atas motor (z 22–25), baut M3 × 16 di (±26; 12,6) dan (±33; −12). Boss 0,4 mm di bawah tutup: tutup melentur dan menekan motor |
| `x1_rangka_interface` | 1 | 83,5 × 53,5 × 19,5 | 5,4 g | rangka konsep v18 (pelat 2,5 mm + 4 kaki Ø6,5 di baut PCB utama), lubang pilot M2 Ø1,7. Boss depan (y 62) dipapas sampai y 60,4 supaya tidak di atas tepi PCB ESP32 DevKit. Dicetak terbalik |
| `x1_velg` | 2 | 29,6 × 29,6 × 18,0 | 5,4 g | **5 jari-jari Y** gaya velg forged (permintaan user 22/11, foto referensi): batang dari hub bercabang di r 6 ke bibir rim (±15°), lengan 1,6 → 1,25 mm, sudut cekung dibulatkan 0,45 mm, punggung menebal ke hub (3 → 6,5 mm), jendela tembus; 5 lubang baut hias + cekungan tutup tengah. Flens Ø29,6 dua sisi, dudukan ban Ø28, hub Ø9,2, lubang D Ø3,1 (sisi rata 1,05 dari pusat) sedalam 8 mm: ditekan sampai mentok → celah velg–gearbox 2 mm. Dicetak muka luar di alas |
| `x1_ban_tpu` | 2 | 34,0 × 34,0 × 15,4 | 5,7 g | TPU 95A, Ø dalam 27,6 (meregang 1,4 % di dudukan, 7 % saat melewati flens) |
| `x1_skid_sensor` | 1 | 17,0 × 9,0 × 4,8 | 0,5 g | tumpuan depan di bawah H1/H2 PCB sensor, dasar tudung bola R 20, 2 kantong mur M3. Dicetak terbalik |
| `x1_spacer_sensor` | 2 | 6,4 × 6,4 × 3,6 | 0,1 g | antara PCB sensor (z 6,4) dan sasis (z 10) |
| `x1_uji_dudukan_motor` | 1 | 27,0 × 35,0 × 11,6 | 4,3 g | potongan sasis di sekitar motor kanan (alur, ganjal, 2 boss), dipakai dengan tutup klem kanan |
| `x1_uji_lubang_as` | 1 | 30,0 × 10,0 × 10,0 | 3,6 g | 3 lubang D Ø3,0 / 3,1 / 3,2 (1 / 2 / 3 takik); velg memakai lubang 2 |

Total badan tanpa uji 66 g padat. Setelan: PETG atau PLA, lapisan 0,2 mm, 4 dinding, infill 40 % gyroid (velg 60 %);
TPU 95A 3 dinding, infill 30 %. Semua STL sudah menghadap alas yang benar.

Baut: 4 × M3 × 30 kepala benam + mur (PCB utama + rangka, dari bawah sasis, butuh 28,5 mm), 4 × M3 × 16 + mur (tutup
klem, butuh 14,8), 2 × M3 × 10 + mur (PCB sensor, kepala di atas hidung sasis, mur di skid, butuh 9,6), 4 × sekrup
M2 × 6 (board interface), strap velcro 16 mm ±15 cm.

## Perubahan terhadap konsep v18

- **Klem motor**: konsep v18 = cincin tertutup (motor tidak bisa dimasukkan karena piringan encoder lebih besar dari
  lubangnya). Sekarang alur terbuka + tutup klem berbaut. Rel belakang (y −11,3…−6,2) sekaligus penahan depan pack.
- **Tumpuan depan**: ball caster di RAB belum punya ukuran, jadi dipakai skid cetak di bawah PCB sensor (titik tumpu
  dekat sensor, tinggi muka QRE1113GR tetap ±3,1 mm). Kalau user tetap memilih ball caster, dudukan ditambah setelah
  link barangnya ada.
- **Ekor sasis** −43 → −47,5 supaya celah strap belakang muat di belakang pack; panjang robot 178,5 mm.
- **Kantong THT**: celah PCB utama–sasis hanya 3 mm, ekor pin socket female ±3 mm, jadi tiap pad PTH (dari KiCad)
  diberi kantong dari atas sedalam 1 mm (lantai 1 mm); pulau pelat yang terkurung kantong ikut diturunkan. Sampai
  22/11 siang masih jendela tembus; diganti kantong buntu supaya bawah sasis rata (permintaan user). Piringan encoder
  sama: kantong dengan lantai 0,6 mm.
- Mesh sensor konsep v18 (rev B) digeser untuk rev C di viewer: J1, U13, C1 mundur 2,5 mm.

## Hasil cek (22/11)

- 0 tabrakan terhadap mesh konsep v18 (kotak pembatas) + komponen KiCad (kaki THT PCB utama, sisi bawah PCB sensor,
  J1 sensor + steker).
- Celah terkecil: kaki THT ke dinding kantong 0,6 mm dan ke lantai 1,0 mm, PCB encoder ke lantai kantong 0,2 mm, steker J1 sensor ke hidung sasis 1,6, pack ke rel 0,2,
  kaki rangka ke PCB ESP32 3,5, ganjal ke kaleng motor 0,1 (jarak dari sumbu 6,12 > r 6).
- Lubang KiCad dicek sama dengan konstanta skrip (PCB utama H1–H4, sensor H1/H2, board interface H1–H4).

## Belum pasti

- Ukuran motor N20 diambil dari model v16 (12 × 10 mm, gearbox 9 mm, encoder ≤ Ø14): cetak uji dulu.
- Bawah rata membuat celah PCB encoder (model r 6,2) ke lantai kantong tinggal 0,2 mm. Kalau PCB encoder motor asli
  lebih besar, `ENC_FLOOR` diturunkan atau kantong encoder dibuat tembus lagi. Potongan uji dudukan motor menjawab ini.
- Pack 14500 2S dari listing 50 × 30 × 15 mm (kantong 54 × 31).
- Rangka interface mengikuti socket J6 8,5 mm + header susun (board interface di z 36,1).
- Cara cas (di luar robot lewat balancer, sesuai konsep v18) belum diputuskan; modul charger + BMS belum punya tempat.
