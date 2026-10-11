# Mekanik — Robot Line Tracer Micro (versi ringkas)

Dipilih 11/10/2026 menggantikan bentuk rata v9: motor N20 melintang di tengah, baterai 2×18650 di atas
motor (seperti model Inventor kelompok 06/10/2026), PCB utama di depan motor, sayap sensor paling depan
dan paling bawah. CAD lanjutan: Fusion 360.

Gambar konsep berdimensi: https://claude.ai/artifact/GWx6mCdbs6jLmmXVAuQGpd dan `konsep-ringkas.png`.

## Ukuran utama (mm)

Sumbu: X = lebar (kanan +), Y = maju (depan +), Z = atas; titik nol = lantai di bawah tengah poros roda.
Tanda (*) = cek ulang dengan komponen asli.

| Bagian | Ukuran / posisi |
|---|---|
| Total P × L × T | 121 × 96 × 44 (134 bila pakai penahan belakang) |
| Roda | Ø34 (*), lebar 8 (*), X ±40…±48, poros Z 17 |
| Jarak roda kiri-kanan (pusat) | 88 |
| Motor N20 + encoder | 32 × 12 × 10 (*), X ±4…±36, saling membelakangi |
| Holder 2×18650 | 76 × 42 × 20, Y −13…29 (geser 8 ke depan), Z 24…44; celah ke roda 2 per sisi |
| PCB utama | 86 × 80 (≤ 100 × 100), Y 8…88, Z 12; belakang menyempit X ±34 (Y < 20) di antara roda |
| Komponen di bawah baterai | TB6612 & MP1584, tinggi maks ± 8 di atas PCB |
| PCB sayap sensor | 88 × 28, Y 80…108, Z 4; disambung spacer ke PCB utama di Y 84, X ±30 |
| Sensor | 5× ITR20001, jarak lateral 10, ±2 dari lantai, ±102 di depan poros |
| Ball caster mini (*) | Y 72, di bawah PCB utama |
| Massa perkiraan | ±235 g; titik berat ±20 di depan poros (±72% beban di roda) |

## Script Fusion 360

`fusion360/LTM_Konsep_Ringkas/` — membuat model kasar (kotak/silinder) dengan ukuran di atas.
Fusion 360: Utilities › Add-Ins › Scripts and Add-Ins › "+" › pilih folder ini › Run.
Ukuran diubah di bagian UKURAN pada awal script. Setelah jadi: ganti kotak dengan model asli (GrabCAD),
rancang dudukan motor/baterai dan sayap belakang (3D print), lalu ekspor sketch outline PCB ke DXF
untuk KiCad (layer Edge.Cuts).
