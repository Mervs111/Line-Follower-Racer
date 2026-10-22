# Hardware — Robot Line Tracer Micro (KiCad)

Starter proyek KiCad dibuat 11/10/2026 dari `docs/skematik-v1.md`, layout PCB v1-draft menyusul di hari yang
sama. **PCB utama v2 (13/10/2026)**: disederhanakan dan ditata ulang supaya gampang diakses untuk edukasi. Format KiCad 7, bisa dibuka KiCad 7, 8, atau 9 (KiCad 8/9 menawarkan upgrade format saat disimpan:
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

- **PCB utama v2** (25 komponen, semua kaki tembus): daya (J1 baterai, SW1, MP1584, dioda 1N5819, elko
  100 µF, pembagi 100k/33k), ESP32 DevKit 30 pin, TB6612 + 2 konektor motor JST PH 6 pin, OLED, tombol A/B
  (+ pull-up R5/R6), buzzer + S8050, J5 box header IDC 2×6 ke kabel pita PCB sensor, 4 lubang M3. Dibanding v1, C2–C6 (100 nF/10 µF) dan R5–R8 (pull-up
  encoder) dibuang: modul TB6612, MP1584, dan ESP32 sudah punya kapasitor sendiri, dan encoder memakai
  pull-up internal ESP32 (`INPUT_PULLUP`).
- **PCB sensor v2** (82 komponen): 16× ITR20001 (LED IR seri berdua, 8× R 120 Ω), 16× pull-up 10k, modul
  mux CD74HC4067, MCP23017 + 16 LED indikator 0805 + 16× R 330 Ω, MOSFET AO3400 pengatur LED IR, box header
  IDC 2×6, 2 lubang M3 untuk dudukan.
- Sambungan memakai **net label** (nama sama = tersambung). Simbol GND/+5V/+3V3 = net daya global.
- `PWR_FLAG` dipasang supaya ERC tidak protes "power pin not driven".
- Netlist hasil ekspor KiCad sudah dicek otomatis terhadap `docs/skematik-v1.md`: 104 pin (utama) dan
  247 pin (sensor) cocok; pin sengaja tidak dipakai diberi tanda X (EN, TX0, RX0, kaki saklar ke-3,
  NC/INTA/INTB MCP23017).
- **Aturan cetak (tempat cetak user):** jalur minimal 0,8 mm (daya 1,2 mm); jarak antar tembaga 0,5 mm dan via
  1,6/0,8 mm = asumsi aman, **cek ke tempat cetak**. Nilainya di konstanta `FAB` (`tools/gen_pcb.py`).

## Layout PCB v2 (13/10/2026)

| | PCB utama v2 | PCB sensor v2 |
|---|---|---|
| Ukuran | 94 × 84 mm (siluet roket, sama dengan model mekanik v12) | 110 × 51 mm (batang lurus) |
| Lapisan | 2 layer, 1,6 mm | 2 layer, 1,6 mm |
| Jalur | 441 segmen, 41 via, semua ≥ 0,8 mm | 642 segmen, 56 via, semua ≥ 0,8 mm |
| Pour GND | atas + bawah (kecuali di bawah antena ESP32) | atas + bawah |
| DRC (KiCad 7.0.11) | 0 pelanggaran, 0 belum tersambung | 0 pelanggaran, 0 belum tersambung |

Cara lihat: buka `.kicad_pro` → **PCB Editor**. Tampilan 3D: **View › 3D Viewer** (Alt+3); modul ESP32,
TB6612, MP1584, ITR20001 belum punya model 3D (hanya kotak footprint). Gambar siap pakai ada di `render/`.

Penempatan komponen memakai koordinat model mekanik v12 (`mechanical/`), jadi
posisi modul, tombol, buzzer, konektor, dan sensor sama dengan model 3D. Jalur dibuat otomatis dengan
FreeRouting lalu dicek DRC.

### Susunan PCB utama v2 (dilihat dari atas, depan = arah maju)

| Blok (kotak silkscreen) | Isi | Posisi |
|---|---|---|
| OTAK | ESP32 DevKit di socket female | tengah-kiri, di depan dudukan baterai; USB menghadap ke kiri |
| LAYAR | OLED 1.3" di socket | kanan; header di sisi depan |
| DRIVER MOTOR | TB6612 di socket + C1 | tengah depan |
| SUARA | buzzer, Q1, R3, R4 | kiri depan |
| DAYA | MP1584, D1, R1/R2 (+ J1, SW1 di tepi kanan) | di bawah dudukan baterai |
| Tombol A/B (+ R5/R6), J5 kabel pita | | hidung |

Di depan kanan ada peta **ALUR DAYA** (BATERAI → SAKLAR → BUCK 5V → ESP32 + SENSOR, cabang ke MOTOR), tetap
terlihat setelah robot dirakit. Nama blok yang ada di bawah modul terbaca saat modulnya dicabut.

### Hal penting saat merakit

1. **Sambungan antar papan: kabel pita 12 pin.** J5 (PCB utama, hidung) dan J1 (PCB sensor, kanan belakang)
   = box header IDC 2×6 berkunci; kabel pita + 2 konektor IDC female, lurus pin n ke pin n (generator mengecek
   net tiap pin sama). PCB sensor dibaut ke 2 lengan dudukan 3D print: dari atas lewat H3/H4 PCB utama, dari
   bawah lewat H1/H2 PCB sensor (lihat `mechanical/`).
2. **Modul di socket.** ESP32 (2× socket female 1×15), TB6612 (2× 1×8), dan OLED (1×4) dipasang di socket
   header female ±8,5 mm, jadi bisa dicabut kalau rusak atau untuk ditunjukkan ke siswa. Modul memakai pin
   header male bawaannya. MP1584 disolder langsung (header male ±2,5 mm) karena ada di bawah dudukan baterai.
3. **Set MP1584 ke 5,0 V sebelum rangka/dudukan baterai dipasang** (trimpot tidak terjangkau setelahnya),
   dan sebelum ESP32 dicolok ke socket.
4. **OLED:** header di sisi depan, jadi tampilan sudah tegak dilihat dari belakang robot, **tidak perlu
   diputar** di firmware (U8g2: `U8G2_R0`). Urutan pin di PCB: GND, VCC, SCL, SDA (tertulis di silkscreen).
   Dari belakang, bagian belakang layar agak tertutup cover; paling jelas dilihat dari atas.
5. **PCB sensor:** ITR20001 di sisi BAWAH (menghadap lantai, diputar: kaki LED IR di depan), begitu juga
   pull-up 10k (di bawah modul mux) dan Q1/R41/R42. Sisi atas: LED indikator + resistornya, resistor LED IR di
   sela antar pasangan sensor, modul mux & MCP23017 di socket, J1. Nomor 1–16 di tepi depan = S1–S16.
   Pasang MCP23017 dengan takik ke kiri (pin 1 di belakang kiri) dan modul mux sesuai tulisan C0..C15.
6. **Baterai & saklar** ada di tepi kanan PCB utama: J1 di celah antara dudukan baterai dan tepi papan, saklar
   di depannya (tuas keluar ke kanan, di bawah OLED). J1: pin kotak = BAT+ (tanda `+`). Posisi ON saklar:
   cek dengan multimeter (pin tengah tersambung ke BAT+).
   **Ngecas tidak lewat PCB:** modul charger 2S USB-C ada di dinding belakang rangka (port menghadap
   belakang), OUT+/OUT− modul ke P+/P− BMS, P+/P− BMS ke J1. Bisa dicas saat saklar OFF. Detail kabel:
   `docs/skematik-v1.md` bagian Daya.
7. Area belakang (Y < 30 mm) ada di bawah plat dudukan baterai (ruang ±9,9 mm): MP1584 (tinggi ±8,1 mm),
   D1, R1/R2, dan konektor motor J2/J3 (JST PH tegak) ada di sini, cek colokan + kabelnya muat.
8. Antena ESP32 (ujung kanan modul): tanpa pour GND di kedua sisi. Jalur sinyal boleh lewat di bawahnya
   karena modul duduk di socket ±8,5 mm di atas PCB.
9. **BMS** ditempel di sisi bawah PCB utama di bagian kiri, di antara dua baris kaki socket ESP32 (ada kotak
   silkscreen bawah); tidak ada kaki solder di area itu.

### Disamakan dengan model mekanik

Kedua PCB = model `mechanical/cadquery/ltm_v12.py` (13/10/2026). Lubang bahu H3/H4 di (±37,5; 69) dan lubang
H1/H2 PCB sensor di (±52; 92,5) dipakai lengan dudukan; konektor motor di X ±(17–27) mm. Di sisi bawah PCB
utama ada tanda tempat **ball caster** (0; 62), area itu sengaja bebas kaki solder, dan tanda tempat **BMS**.
Di model v12 tepi depan dudukan baterai dimundurkan ke Y 29,5 (ESP32 mulai Y 30,2).

## Checklist sebelum pesan PCB

1. **Ukur modul asli, sesuaikan footprint sementara** di `ltm-lib/ltm.pretty`:
   - ESP32 DevKit: jarak antar baris pin. Pilih `ESP32_DevKit_30P_W25.4` atau `..._W22.86`
     (properti Footprint U1), cek juga urutan pin dengan tulisan di papan.
   - TB6612: jarak baris (sementara 15,24 mm) dan urutan pin.
   - MP1584: posisi 4 titik solder (sementara ±9,5 × ±6 mm).
   - Modul mux CD74HC4067: jarak baris (sementara 15,24 mm) dan urutan C0..C15 / SIG..GND.
   - ITR20001: jarak & urutan kaki dari datasheet (sementara 2×2 kaki 2,54 mm, THT).
   - OLED: urutan GND/VCC; kalau terbalik, tukar label pin 1 dan 2 di J4.
   - Lebar ESP32 DevKit maks ±28,4 mm: modul yang lebih lebar mepet ke dudukan baterai dan TB6612.
2. Kabel motor N20: cocokkan urutan 6 kabel dengan J2/J3.
3. Resistor 10 kΩ yang dipakai 7 buah (RAB 10). Socket header female (1×15 ×2, 1×8 ×2, 1×4) masuk paket
   "komponen pendukung" RAB; dioda di RAB masih tertulis SS14, sekarang 1N5819.
4. Kalau footprint berubah: di skematik ganti footprint → PCB Editor **Tools › Update PCB from Schematic
   (F8)** → geser komponen yang terdampak → hapus jalur di sekitarnya dan routing ulang (manual, atau
   minta generator dijalankan ulang). Jalankan **Inspect › Design Rules Checker** sampai 0 error.
5. Ekspor untuk pabrik (JLCPCB dll.): **File › Fabrication Outputs › Gerbers** + **Drill Files**, zip.

Catatan saat dibuka di KiCad 8/9: DRC bisa memunculkan peringatan "footprint tidak sama dengan library"
karena library versi baru sedikit berbeda. Itu peringatan, bukan error sambungan; boleh diabaikan atau
klik kanan › Update Footprint from Library.

## Aturan desain (sudah diisi di proyek)

Mengikuti tempat cetak lokal (konstanta `FAB` di `tools/gen_pcb.py`): net class `Default` jalur 0,8 mm,
`Power` (GND, +5V, /VBAT, /BAT+, /+5V_BUCK, /ML_*, /MR_*, /LED_K) 1,2 mm; clearance 0,5 mm; via 1,6/0,8 mm;
jarak tembaga ke tepi 0,5 mm. Clearance dan via masih asumsi aman, **cek ke tempat cetak**; kalau berbeda,
ubah `FAB` lalu jalankan ulang generator. Net dari label lokal di KiCad diberi awalan `/`, jadi pola net
class ditulis `/VBAT`, bukan `VBAT`.
Beberapa net daya dirouting 0,8 mm supaya muat (PCB utama: GND, /BAT+; PCB sensor: GND, +5V, /LED_K); GND
lalu ditebalkan oleh pour GND di dua sisi. File `.kicad_dru` berisi dua aturan: pad GND yang dikepung jalur
boleh tersambung ke pour dengan 1 spoke, dan kaki-kaki saklar SW1 (jarak bawaan pabrik saklar) boleh
berjarak 0,2 mm satu sama lain.

## Generator (`tools/`)

- `gen_kicad.py`: symbol, footprint sementara, skematik (sekali jalan, sudah dipakai).
- `gen_pcb.py`: layout PCB. Membaca netlist dari skematik, menggambar outline dari model mekanik, menaruh
  footprint, routing FreeRouting, pour GND, DRC. Butuh Python KiCad 7 (`pcbnew`), `kicad-cli`, Java 21+,
  dan `freerouting.jar` (variabel `FREEROUTING_JAR`). **Menjalankan ulang menimpa `.kicad_pcb`.**
- `verify_nets.py` + `expected_nets.json`: cek netlist terhadap `docs/skematik-v1.md`.
- `kicad-mcp/`: server MCP supaya Claude Code (di laptop sendiri) bisa mengedit PCB yang sedang terbuka di
  KiCad 9/10 secara live (pindah footprint, outline, DRC, render). Cara pasang di `kicad-mcp/README.md`.
