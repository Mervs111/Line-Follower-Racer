# PCB sensor garis: riwayat revisi

Proyek KiCad 10 buatan user (skematik + layout), dirapikan dan dirouting bersama Claude lewat MCP KiCad.
Buka `sensor-garis.kicad_pro`. File di folder ini selalu revisi **terbaru**; tiap revisi disalin utuh ke
`revisi/rev-X/` (file KiCad + gambar) supaya perubahan bisa dibandingkan.

## Rev C (20/11/2026), `revisi/rev-c/` = file terbaru

![Rev C tampak bawah](revisi/rev-c/rev-c-bawah.png)

Dirouting ulang untuk aturan cetak baru **jalur min 0,5 mm, jarak 0,7 mm** (`docs/aturan-cetak-pcb.md`). Posisi 12 QRE
dan bentuk jangkar sama dengan rev B; ukuran luar tetap 94,5 × 51 mm.
- **Pita busur lebih tebal** ke belakang (lajur 1,2 mm per jalur S + 2 lajur tambahan untuk GND), kait ikut mundur.
  Outline dari `hardware/tools/sensor_revc_outline.py`.
- **U13, C1, J1 mundur 2,5 mm** ke tangkai (U13 Y 69,07, J1 Y 83,07): tabrakan terakhir menumpuk tepat di depan mux,
  tempat semua jalur S masuk. H1/H2 tetap.
- **24 resistor pindah ke F.Cu** (posisi pad sama): dengan jarak 0,7 pad resistor terkurung di B.Cu.
- **Pad U13 0,5 × 2,05 mm** (pitch 1,27): dengan pad pustaka celah antar kaki < 0,7.
- **GND dirouting sebagai jalur** (pour saja pecah jadi 16 kelompok), pour GND dua sisi sebagai tambahan;
  pad GND J1 disambung penuh ke pour (arus 12 LED masuk lewat situ). H1/H2 diberi atribut "board only" (parity 0).
- Routing: `hardware/tools/autoroute/` (`x2_router.py` + `x2_cari.py`, setelan di README sana), 725 segmen, 72 via.
  DRC 0 error / 0 unconnected / parity 0; peringatan tinggal 1 lib_footprint_mismatch (pad U13 dikecilkan, disengaja).
- 21/11: leher pour GND B.Cu 0,48 mm (< 0,5) antara jalur +5V dan via S8 dirapikan dengan menggeser via S8 0,1 mm ke
  kanan (209,6 → 209,7; ujung jalurnya ikut). Leher melebar, pour di bawahnya tetap tersambung.

## Rev B (22/10/2026), `revisi/rev-b/`

![Rev B tampak bawah](revisi/rev-b/rev-b-bawah.png)

- **Bentuk jangkar**: pita melengkung + kait di kedua ujung (mengarah ke belakang) + tangkai 25 mm + tab 2 lubang.
  Lebar 95 mm (rev A 120), panjang tetap ±51 mm (Y 49,55–100,5). Kait sampai Y 78 (±28 mm di belakang tepi depan).
- **Sensor**: 12× QRE1113GR jarak **8 mm** (untuk garis 2 cm: kedua tepi garis bergantian melewati sensor tiap ±4 mm,
  bacaan posisi halus). Pasangan tengah ±4,25 mm (celah 8,5 untuk jalur +3V3). Segmen dari tengah ke luar
  5°, 5°, 12°, 25°, 40°: enam sensor tengah hampir lurus (presisi & persimpangan), lengan melengkung ke belakang
  (tikungan tajam). Rentang ±41,4 mm, sensor terluar mundur 11,6 mm.

  | Sensor (kanan; kiri = cermin) | U7 | U8 | U9 | U10 | U11 | U12 |
  |---|---|---|---|---|---|---|
  | x dari tengah (mm) | 4,25 | 12,22 | 20,19 | 28,01 | 35,27 | 41,39 |
  | mundur dari U7 (mm) | 0 | 0,70 | 1,39 | 3,06 | 6,44 | 11,58 |

- **Tiap grup** sama seperti rev A (R10k kiri, R220 kanan, 2,85 mm), diputar mengikuti busur.
- **Routing**: S1–S12 di B.Cu menumpuk di belakang sensor (jarak 0,7 mm) lalu ke 12 via di bawah U13; daya di
  F.Cu (+3V3 depan, +5V belakang), +3V3 menyeberang lewat B di garis tengah; pour GND dua sisi (tebal min 0,3).
  DRC 0 error / 0 unconnected (sisa 12 peringatan lib_footprint_mismatch).
- U13 tepat di garis tengah X 200, C1 diputar vertikal di samping pin 24, J1 & H1/H2 digeser 0,25 mm supaya simetris
  (H1/H2 = X ±4,75 dari tengah, Y 95).
- Skrip penataan/routing: `hardware/tools/sensor_revb_layout.py` (dokumentasi geometri; jangan dijalankan ulang).

## Rev A (22/10/2026), `revisi/rev-a/`

![Rev A tampak bawah](revisi/rev-a/rev-a-bawah.png)

- **Bentuk**: outline simetris gaya "ujung panah" (`hardware/outline/`): sayap 120 mm, tepi depan miring ±11°,
  badan 30 mm, tab 18 mm dengan 2 lubang M3 (±4,75; 95).
- **Sensor**: 12× QRE1113GR di sisi bawah, jarak 9 mm (celah tengah U6–U7 19,5 mm), turun 2 mm tiap sensor
  ke arah luar. Tiap sensor: R 220 Ω (LED, dari +5V) di kanan dan R 10k (pull-up ke +3V3) di kiri, keduanya di
  sisi bawah, 2,85 mm dari tengah sensor.
- **Mux**: U13 CD74HC4067M (SOIC-24W) di sisi atas, garis tengah; I2..I13 = S1..S12 (sesuai skematik user),
  I0, I1, I14, I15 tidak tersambung. C1 100 nF di samping pin VCC.
- **J1**: JST XH 8 pin vertikal. Urutan pin (dari skematik): 1 +5V, 2 +3V3, 3 GND, 4 MUX_S3, 5 MUX_S2,
  6 MUX_S1, 7 MUX_S0, 8 MUX_SIG.
- **Routing**: sinyal S1–S12 di B.Cu (0,3 mm), rel daya +3V3/+5V di F.Cu (0,5 mm), pour GND di kedua sisi
  (jarak 0,5 mm). DRC: 0 error, 0 unconnected.

Alasan revisi berikutnya: bentuk kurang mirip jangkar, banyak ruang kosong di belakang sensor, celah tengah
19,5 mm terlalu lebar untuk garis lomba 2 cm (IARC XII), dan robot ingin dipakai serbaguna (lintasan grid dan
lintasan banyak tikungan).
