# Hardware — Robot Line Tracer Micro (KiCad)

Starter proyek KiCad dibuat 11/10/2026 dari `docs/skematik-v1.md`. Format KiCad 7, bisa dibuka
KiCad 7, 8, atau 9 (KiCad 8/9 menawarkan upgrade format saat disimpan: pilih **Ya**).

```
hardware/
├── ltm-lib/
│   ├── ltm.kicad_sym        symbol: ESP32_DevKit_30, TB6612_Module, MP1584_Module, ITR20001
│   └── ltm.pretty/          footprint SEMENTARA (lihat checklist)
├── ltm-main/                proyek PCB utama  (buka ltm-main.kicad_pro)
├── ltm-sensor/              proyek PCB sensor jangkar (buka ltm-sensor.kicad_pro)
├── ltm-main.pdf             cetakan skematik PCB utama
├── ltm-sensor.pdf           cetakan skematik PCB sensor
└── tools/                   generator starter (JANGAN dijalankan ulang: menimpa skematik)
```

Library `ltm` sudah terdaftar di tiap proyek (`sym-lib-table`, `fp-lib-table`), tidak perlu ditambah manual.
Symbol standar (R, C, konektor, power) memakai library bawaan KiCad.

## Isi skematik

- **PCB utama** (34 komponen): daya (J1 baterai, SW1, MP1584, SS14, kapasitor, pembagi 100k/33k),
  ESP32 DevKit 30 pin, TB6612 + 2 konektor motor JST PH 6 pin + pull-up encoder, OLED, tombol A/B,
  buzzer + S8050, header 2×5 ke PCB sensor, 6 lubang M3.
- **PCB sensor** (22 komponen): header 2×5, 5× ITR20001 + R 180 Ω + R 10k, MOSFET AO3400 pengatur LED IR,
  2 lubang M3.
- Sambungan memakai **net label** (nama sama = tersambung). Simbol GND/+5V/+3V3 = net daya global.
- `PWR_FLAG` dipasang supaya ERC tidak protes "power pin not driven".
- Netlist hasil ekspor KiCad sudah dicek otomatis terhadap `docs/skematik-v1.md`: 116 pin (utama) dan
  59 pin (sensor) cocok; pin sengaja tidak dipakai diberi tanda X (EN, TX0, RX0, kaki saklar ke-3).

## Checklist sebelum lanjut ke PCB

1. **Buka di KiCad, jalankan ERC** (Inspect › Electrical Rules Checker). Peringatan kecil soal posisi
   teks boleh diabaikan; error koneksi harus 0.
2. **Ukur modul asli, sesuaikan footprint sementara** di `ltm-lib/ltm.pretty`:
   - ESP32 DevKit: jarak antar baris pin. Pilih `ESP32_DevKit_30P_W25.4` atau `..._W22.86`
     (properti Footprint U1), cek juga urutan pin dengan tulisan di papan.
   - TB6612: jarak baris (sementara 15,24 mm) dan urutan pin.
   - MP1584: posisi 4 titik solder (sementara ±9,5 × ±6 mm).
   - ITR20001: jarak & urutan kaki dari datasheet (sementara 2×2 kaki 2,54 mm).
   - OLED: urutan GND/VCC; kalau terbalik, tukar label pin 1 dan 2 di J4.
3. Kabel motor N20: cocokkan urutan 6 kabel dengan J2/J3.
4. Resistor 10 kΩ yang dipakai 11 buah (RAB 10).
5. Baru setelah itu: buka PCB editor, **Tools › Update PCB from Schematic (F8)**, import outline PCB
   dari model mekanik (DXF ke layer Edge.Cuts), lalu layout.

## Aturan desain (sudah diisi di proyek)

Net class `Power` (GND, VBAT, BAT+, +5V, +5V_BUCK, ML_*, MR_*, LED_K) lebar jalur 0,8 mm; `Default`
0,25 mm; clearance 0,2 mm; via 0,6/0,3 mm (aman untuk JLCPCB).
