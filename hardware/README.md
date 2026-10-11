# Hardware — Robot Line Tracer Micro (KiCad)

Starter proyek KiCad dibuat 11/10/2026 dari `docs/skematik-v1.md`, layout PCB v1-draft menyusul di hari yang
sama. Format KiCad 7, bisa dibuka KiCad 7, 8, atau 9 (KiCad 8/9 menawarkan upgrade format saat disimpan:
pilih **Ya**).

```
hardware/
├── ltm-lib/
│   ├── ltm.kicad_sym        symbol: ESP32_DevKit_30, TB6612_Module, MP1584_Module, ITR20001
│   └── ltm.pretty/          footprint SEMENTARA (lihat checklist)
├── ltm-main/                proyek PCB utama  (buka ltm-main.kicad_pro)
├── ltm-sensor/              proyek PCB sensor jangkar (buka ltm-sensor.kicad_pro)
├── render/                  gambar PCB (atas/bawah + rakitan) untuk laporan/PPT
├── ltm-main.pdf             cetakan skematik PCB utama
├── ltm-sensor.pdf           cetakan skematik PCB sensor
└── tools/                   generator (JANGAN dijalankan ulang tanpa alasan: menimpa file)
```

Library `ltm` sudah terdaftar di tiap proyek (`sym-lib-table`, `fp-lib-table`), tidak perlu ditambah manual.
Symbol dan footprint standar (R, C, konektor, power) memakai library bawaan KiCad.

## Isi skematik

- **PCB utama** (34 komponen): daya (J1 baterai, SW1, MP1584, SS14, kapasitor, pembagi 100k/33k),
  ESP32 DevKit 30 pin, TB6612 + 2 konektor motor JST PH 6 pin + pull-up encoder, OLED, tombol A/B,
  buzzer + S8050, J5 ke PCB sensor, 6 lubang M3.
- **PCB sensor** (22 komponen): header 2×5, 5× ITR20001 + R 180 Ω + R 10k, MOSFET AO3400 pengatur LED IR,
  2 lubang M3.
- Sambungan memakai **net label** (nama sama = tersambung). Simbol GND/+5V/+3V3 = net daya global.
- `PWR_FLAG` dipasang supaya ERC tidak protes "power pin not driven".
- Netlist hasil ekspor KiCad sudah dicek otomatis terhadap `docs/skematik-v1.md`: 116 pin (utama) dan
  59 pin (sensor) cocok; pin sengaja tidak dipakai diberi tanda X (EN, TX0, RX0, kaki saklar ke-3).

## Layout PCB v1-draft (11/10/2026)

| | PCB utama | PCB sensor |
|---|---|---|
| Ukuran | 94 × 84 mm (siluet roket, sama dengan model mekanik v11) | 92 × 53 mm (jangkar + leher) |
| Lapisan | 2 layer, 1,6 mm | 2 layer, 1,6 mm |
| Jalur | 435 segmen, 26 via | 234 segmen, 14 via |
| Pour GND | atas + bawah (kecuali di bawah antena ESP32) | atas + bawah |
| DRC (KiCad 7.0.11) | 0 pelanggaran, 0 belum tersambung | 0 pelanggaran, 0 belum tersambung |

Cara lihat: buka `.kicad_pro` → **PCB Editor**. Tampilan 3D: **View › 3D Viewer** (Alt+3); modul ESP32,
TB6612, MP1584, ITR20001 belum punya model 3D (hanya kotak footprint). Gambar siap pakai ada di `render/`.

Penempatan komponen memakai koordinat model mekanik v11 (`mechanical/`), jadi posisi ESP32, TB6612, MP1584,
OLED, tombol, buzzer, konektor motor, dan sensor sama dengan model 3D. Jalur dibuat otomatis dengan
FreeRouting lalu dicek DRC.

### Hal penting saat merakit

1. **Sambungan antar papan (J5 ↔ J1).** Celah PCB utama ke PCB sensor di mekanik v11 cuma ±2,4 mm, socket
   tidak muat. Jadi: pin header male 2×5 (J1) disolder di **sisi atas PCB sensor**, pin panjangnya masuk dari
   bawah lewat 10 lubang J5 dan disolder di atas PCB utama. Plastik header (2,5 mm) jadi jarak antar papan,
   ditambah 2 spacer nilon M3 2,5 mm di lubang H5/H6 (utama) = H1/H2 (sensor). Posisi 10 pin sudah dicek
   sama persis di kedua file.
2. **Modul.** ESP32, TB6612, dan MP1584 disolder langsung pakai header male (tinggi ±2,5 mm, sesuai model
   mekanik). Di bawahnya hanya ada jalur, tidak ada komponen.
3. **OLED wajib pakai socket header female (±8,5 mm)**, karena R3–R8 dan Q1 ditaruh di bawah OLED.
   Header OLED menghadap ke belakang, jadi tampilan **diputar 180° di firmware** (U8g2: `U8G2_R2`,
   Adafruit: `setRotation(2)`). Urutan pin di PCB: GND, VCC, SCL, SDA (tertulis di silkscreen).
4. **Sensor ITR20001 dipasang di sisi BAWAH PCB sensor** (menghadap lantai), begitu juga resistor, Q1, C1.
   Sisi atas hanya J1 dan tulisan. Nomor 1–5 di silkscreen atas = S1–S5.
5. **Baterai & saklar** ada di tepi kiri PCB utama, di luar dudukan baterai. J1: pin kotak = BAT+
   (tanda `+`). Posisi ON saklar: cek dengan multimeter (pin tengah tersambung ke BAT+).
   **Ngecas tidak lewat PCB:** modul charger 2S USB-C ada di dinding belakang rangka (port menghadap
   belakang), OUT+/OUT− modul ke P+/P− BMS, P+/P− BMS ke J1. Bisa dicas saat saklar OFF. Detail kabel:
   `docs/skematik-v1.md` bagian Daya.
6. Area belakang (Y < 30 mm) ada di bawah plat dudukan baterai (ruang ±9,9 mm): konektor motor J2/J3
   (JST PH tegak) ada di sini, cek colokan + kabelnya muat.
7. Antena ESP32 (ujung kiri modul) bebas tembaga di kedua sisi.

### Perubahan dibanding model mekanik v11 (belum disinkronkan ke `mechanical/`)

- Saklar SW1 pindah dari depan-kiri ke **tepi kiri belakang** (Y 22–34 mm), konektor baterai J1 di atasnya
  (Y 34–42 mm). Alasannya: jalur kabel motor dari TB6612 butuh lorong lega di sisi kiri.
- Lubang bahu H3/H4 pindah dari (±42; 30) ke **(±37,5; 69)**, karena (±42; 30) menghalangi colokan USB.
- Lubang spacer antar papan pindah dari (±8; 87,5) ke **(±10,5; 83)** dan pangkal leher PCB sensor
  dilebarkan dari ±12 ke **±14 mm**, karena lubang lama bertabrakan dengan header 2×5.
- Konektor motor JST PH bergeser ke X ±(17–27) mm supaya tidak mentok standoff baterai H1/H2 (±32; 16).

## Checklist sebelum pesan PCB

1. **Ukur modul asli, sesuaikan footprint sementara** di `ltm-lib/ltm.pretty`:
   - ESP32 DevKit: jarak antar baris pin. Pilih `ESP32_DevKit_30P_W25.4` atau `..._W22.86`
     (properti Footprint U1), cek juga urutan pin dengan tulisan di papan.
   - TB6612: jarak baris (sementara 15,24 mm) dan urutan pin.
   - MP1584: posisi 4 titik solder (sementara ±9,5 × ±6 mm).
   - ITR20001: jarak & urutan kaki dari datasheet (sementara 2×2 kaki 2,54 mm, THT).
   - OLED: urutan GND/VCC; kalau terbalik, tukar label pin 1 dan 2 di J4.
2. Kabel motor N20: cocokkan urutan 6 kabel dengan J2/J3.
3. Resistor 10 kΩ yang dipakai 11 buah (RAB 10).
4. Kalau footprint berubah: di skematik ganti footprint → PCB Editor **Tools › Update PCB from Schematic
   (F8)** → geser komponen yang terdampak → hapus jalur di sekitarnya dan routing ulang (manual, atau
   minta generator dijalankan ulang). Jalankan **Inspect › Design Rules Checker** sampai 0 error.
5. Ekspor untuk pabrik (JLCPCB dll.): **File › Fabrication Outputs › Gerbers** + **Drill Files**, zip.

Catatan saat dibuka di KiCad 8/9: DRC bisa memunculkan peringatan "footprint tidak sama dengan library"
karena library versi baru sedikit berbeda. Itu peringatan, bukan error sambungan; boleh diabaikan atau
klik kanan › Update Footprint from Library.

## Aturan desain (sudah diisi di proyek)

Net class `Power` (GND, +5V, /VBAT, /BAT+, /+5V_BUCK, /ML_*, /MR_*, /LED_K) lebar jalur 0,8 mm; `Default`
0,25 mm; clearance 0,2 mm; via 0,6/0,3 mm; jarak tembaga ke tepi 0,3 mm (aman untuk JLCPCB). Net dari
label lokal di KiCad diberi awalan `/`, jadi pola net class ditulis `/VBAT`, bukan `VBAT`.
GND dirouting tipis (0,25 mm) lalu ditebalkan oleh pour GND di dua sisi. File `.kicad_dru` hanya berisi
satu aturan: pad GND yang dikepung jalur boleh tersambung ke pour dengan 1 spoke.

## Generator (`tools/`)

- `gen_kicad.py`: symbol, footprint sementara, skematik (sekali jalan, sudah dipakai).
- `gen_pcb.py`: layout PCB. Membaca netlist dari skematik, menggambar outline dari model mekanik, menaruh
  footprint, routing FreeRouting, pour GND, DRC. Butuh Python KiCad 7 (`pcbnew`), `kicad-cli`, Java 21+,
  dan `freerouting.jar` (variabel `FREEROUTING_JAR`). **Menjalankan ulang menimpa `.kicad_pcb`.**
- `verify_nets.py` + `expected_nets.json`: cek netlist terhadap `docs/skematik-v1.md`.
