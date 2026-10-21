# Aturan cetak PCB (dari tempat cetak, 21/10/2026)

Sumber: gambar "Standard Spesification Product" + "Harap diperhatikan" dari tempat cetak, ditambah pesan
perubahan dari mereka: **tebal jalur minimal 0,3 mm, jarak ke ground minimal 0,5 mm**. Menggantikan asumsi lama
13/10 (jalur 0,8 mm, jarak 0,5 mm, via 1,6/0,8).

## Batas dari tempat cetak

| Item | Batas |
|---|---|
| Tebal jalur | min 0,3 mm (perubahan terbaru; standar lama 0,254 mm / 10 mil) |
| Jarak jalur ke jalur / jalur ke pad (beda net) | min 0,254 mm (10 mil) |
| Jarak ke ground pour | min 0,5 mm (perubahan terbaru; standar lama 0,3 mm) |
| Lubang via / bor terkecil | lubang 0,6 mm, pad 1,0 mm; untuk 2 layer di gambar: lubang 0,61 mm, diameter 1,27 mm |
| Lubang slot (memanjang) | min 1 mm, pad 1,5 mm |
| Garis silkscreen | min 0,203 mm (8 mil) |
| Solder mask expansion | 0,1016 mm (4 mil) |
| Thermal relief (sambungan pad ke pour) | jari-jari 0,254 mm, celah 0,254 mm (dipakai 0,3 dan 0,5 karena aturan baru) |

Tempat cetak tidak memberi garansi kalau desain di bawah batas ini (short / jalur putus).

## Isian KiCad (Board Setup), sudah diberi sedikit cadangan

**Design Rules → Constraints**

| Isian | Nilai |
|---|---|
| Minimum clearance | 0,3 mm |
| Minimum track width | 0,3 mm |
| Minimum via diameter | 1,0 mm |
| Minimum through hole | 0,6 mm |
| Minimum annular width | 0,2 mm |

Batas di atas = batas tempat cetak. Ukuran via yang dipakai sehari-hari diatur lebih besar di net class (1,3 / 0,6).

**Design Rules → Net Classes**

| Kelas | Lebar jalur | Clearance | Via | Isi |
|---|---|---|---|---|
| Default | 0,3 mm | 0,3 mm | 1,3 / 0,6 | sinyal (sensor S1–S12, mux S0–S3, I2C, tombol, encoder) |
| Daya kecil | 0,5 mm | 0,3 mm | 1,3 / 0,6 | +3V3, +5V (LED 12 QRE ±190 mA) |
| Daya besar | 1,2 mm | 0,3 mm | 1,3 / 0,6 | VBAT, keluaran motor TB6612, GND utama (puncak 2–3 A) |

Pola net class untuk net dari label lokal diawali `/` (misalnya `/VBAT`).

**Zona ground (pour)**: clearance 0,5 mm, minimum width 0,3 mm, thermal relief gap 0,5 mm, spoke width 0,3 mm.

**Text & Graphics**: garis silkscreen 0,2 mm, tinggi teks min 1,0 mm, tebal teks 0,2 mm.

**Board Stackup → Solder Mask/Paste**: solder mask expansion 0,1 mm.

## Dampak ke desain

- **IC mux CD74HC4067 SOIC-24 aman**: celah antar pad SOIC 0,67 mm (> 0,3), jalur 0,3 mm dari pad bersebelahan
  berjarak 0,97 mm. Jalur tidak bisa lewat di antara dua pad SOIC (butuh 0,3 + 2 × 0,3 = 0,9 mm), dan memang tidak perlu.
- **SSOP (kaki 0,65 mm) tetap jangan**: celah antar pad ±0,25 mm, di bawah batas 0,254 mm. Driver TB6612 tetap modul.
- `hardware/tools/gen_pcb.py` (konstanta `FAB`) masih memakai aturan lama 0,8 mm; generator itu juga belum ikut
  keputusan sensor terbaru.
