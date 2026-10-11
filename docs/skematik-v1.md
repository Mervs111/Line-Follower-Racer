# Acuan Skematik v1 — Robot Line Tracer Micro (KiCad)

Dibuat 11/10/2026. Menggantikan bagian `docs/minsys-v1.md` yang sudah tidak berlaku (baterai 14500, papan
OLED terpisah/J_UI, IMU). Mengikuti mekanik v11 (`mechanical/`): dua papan, **PCB utama** dan **PCB sensor
jangkar**, disambung header 2×5 board-to-board.

Pin modul di bawah = susunan umum di marketplace. **Wajib dicocokkan dengan modul yang dibeli** (tulisan
di PCB modul) sebelum footprint dibuat.

## 1. Struktur proyek KiCad

```
hardware/
├── ltm-lib/       symbol + footprint buatan sendiri (ESP32 DevKit, TB6612, MP1584, ITR20001)
├── ltm-main/      PCB utama
└── ltm-sensor/    PCB sensor jangkar
```

## 2. Symbol buatan sendiri

### ESP32 DevKit 30 pin (susunan DOIT DevKit V1)

Nomor pin footprint: 1–15 baris kiri dari ujung antena ke ujung USB, 16–30 baris kanan dari ujung antena
ke ujung USB. **Cek jarak antar baris (22,86 atau 25,4 mm) dan urutan pin dengan modul asli.**

| Pin | Nama | Net | | Pin | Nama | Net |
|---|---|---|---|---|---|---|
| 1 | EN | — | | 16 | GPIO23 | ENC_R_A |
| 2 | VP / GPIO36 | S1 | | 17 | GPIO22 | SCL |
| 3 | VN / GPIO39 | S2 | | 18 | TX0 / GPIO1 | — (USB) |
| 4 | GPIO34 | S3 | | 19 | RX0 / GPIO3 | — (USB) |
| 5 | GPIO35 | S4 | | 20 | GPIO21 | SDA |
| 6 | GPIO32 | S5 | | 21 | GPIO19 | ENC_L_B |
| 7 | GPIO33 | VBAT_SENSE | | 22 | GPIO18 | ENC_L_A |
| 8 | GPIO25 | PWMA | | 23 | GPIO5 | ENC_R_B |
| 9 | GPIO26 | AIN1 | | 24 | TX2 / GPIO17 | BIN2 |
| 10 | GPIO27 | AIN2 | | 25 | RX2 / GPIO16 | BIN1 |
| 11 | GPIO14 | PWMB | | 26 | GPIO4 | STBY |
| 12 | GPIO12 | BUZ | | 27 | GPIO2 | BTN_B |
| 13 | GPIO13 | IR_EN | | 28 | GPIO15 | BTN_A |
| 14 | GND | GND | | 29 | GND | GND |
| 15 | VIN | +5V | | 30 | 3V3 | +3V3 |

Pin 1, 18, 19 diberi tanda *no connect* (X) di skematik.

### Modul TB6612FNG (16 pin)

| Pin | Nama | Net | | Pin | Nama | Net |
|---|---|---|---|---|---|---|
| 1 | PWMA | PWMA | | 9 | VM | VBAT |
| 2 | AIN2 | AIN2 | | 10 | VCC | +3V3 |
| 3 | AIN1 | AIN1 | | 11 | GND | GND |
| 4 | STBY | STBY | | 12 | AO1 | ML_P |
| 5 | BIN1 | BIN1 | | 13 | AO2 | ML_N |
| 6 | BIN2 | BIN2 | | 14 | BO2 | MR_N |
| 7 | PWMB | PWMB | | 15 | BO1 | MR_P |
| 8 | GND | GND | | 16 | GND | GND |

### Modul MP1584 (4 titik)

| Pin | Nama | Net |
|---|---|---|
| 1 | IN+ | VBAT |
| 2 | IN− | GND |
| 3 | OUT+ | +5V_BUCK |
| 4 | OUT− | GND |

### ITR20001 (4 pin)

Anoda LED, katoda LED, kolektor, emitor. Boleh memakai symbol sensor reflektif bawaan KiCad (mis. QRE1113 di
library Sensor_Optical) dengan footprint buatan sendiri dari datasheet ITR20001.

## 3. PCB utama — sambungan per blok

### Daya
| Komponen | Sambungan |
|---|---|
| J1 baterai, JST XH 2 pin | 1 = BAT+ (P+ dari BMS), 2 = GND (P−) |
| SW1 saklar geser SPDT | kaki tengah = VBAT, satu kaki samping = BAT+, kaki lain tidak dipakai |
| C1 100 µF/16 V elko + C2 100 nF | VBAT ke GND, dekat pin VM TB6612 |
| U3 MP1584 | lihat tabel modul; set 5,0 V sebelum ESP32 dipasang |
| D1 SS14 | anoda = +5V_BUCK, katoda = +5V |
| C3 10 µF + C4 100 nF | +5V ke GND, dekat pin VIN ESP32 |
| R1 100 kΩ, R2 33 kΩ, C5 100 nF | VBAT–R1–VBAT_SENSE–R2–GND; C5 dari VBAT_SENSE ke GND |

BMS dan modul charger berada di luar PCB (BMS di bawah PCB utama, charger di dinding belakang rangka dengan
port USB-C menghadap belakang; diputuskan tetap di sana 11/10/2026). Sambungan kabel:

| Dari | Ke |
|---|---|
| Baterai 2S (holder) | B−, BM, B+ di BMS |
| Modul charger 2S USB-C, OUT+ / OUT− | P+ / P− di BMS |
| P+ / P− di BMS | J1 PCB utama (BAT+ / GND) |

Charger tersambung langsung ke BMS, tidak lewat SW1, jadi robot bisa dicas saat saklar OFF.

### ESP32, driver, motor
| Komponen | Sambungan |
|---|---|
| U1 ESP32 DevKit | tabel ESP32 di atas |
| U2 TB6612 | tabel TB6612 di atas; C6 100 nF di +3V3 dekat pin VCC |
| J2 motor kiri, JST PH 6 pin | 1 ML_P, 2 +3V3, 3 ENC_L_A, 4 ENC_L_B, 5 GND, 6 ML_N |
| J3 motor kanan, JST PH 6 pin | 1 MR_P, 2 +3V3, 3 ENC_R_A, 4 ENC_R_B, 5 GND, 6 MR_N |
| R5–R8 10 kΩ (boleh tidak dipasang) | pull-up ENC_L_A, ENC_L_B, ENC_R_A, ENC_R_B ke +3V3 |

Urutan kabel encoder N20 beda-beda tiap penjual: cocokkan dengan kabel motor yang dibeli.

### OLED, tombol, buzzer
| Komponen | Sambungan |
|---|---|
| J4 OLED, 1×4 | 1 GND, 2 +3V3, 3 SCL, 4 SDA (sebagian modul VCC dulu baru GND: cek) |
| SW2 tombol A | BTN_A ke GND (+ C 100 nF paralel, opsional) |
| SW3 tombol B | BTN_B ke GND (+ C 100 nF paralel, opsional) |
| Q1 S8050 | emitor = GND; kolektor = kaki − buzzer |
| R3 1 kΩ, R4 10 kΩ | BUZ–R3–basis Q1; basis–R4–GND (GPIO12 harus LOW saat boot) |
| BZ1 buzzer aktif 5 V | + = +5V, − = kolektor Q1 |

### Konektor ke PCB sensor
J5 = 10 lubang tembus 2×5, pitch 2,54 mm, **tanpa komponen**. Pin header male 2×5 (J1) yang disolder di PCB sensor
masuk dari bawah lewat lubang J5 lalu disolder di atas PCB utama. Plastik header (2,5 mm) sekaligus jadi jarak
antar PCB; celah di mekanik v11 cuma ±2,4 mm sehingga socket tidak muat. Kalau papan perlu dilepas: sedot timah
10 titik J5.

| Pin | Net | | Pin | Net |
|---|---|---|---|---|
| 1 | +5V | | 2 | +3V3 |
| 3 | GND | | 4 | GND |
| 5 | IR_EN | | 6 | S1 |
| 7 | S2 | | 8 | S3 |
| 9 | S4 | | 10 | S5 |

Lubang baut: 6× M3 (2 dudukan rangka, 2 bahu, 2 spacer PCB sensor).

## 4. PCB sensor jangkar

| Komponen | Sambungan |
|---|---|
| J1 pin header male 2×5 (sisi atas, pin panjang ke atas menembus J5) | urutan pin sama dengan J5 PCB utama |
| U1–U5 ITR20001 | anoda LED ← R1–R5 180 Ω ← +5V; katoda LED → LED_K; kolektor → S1–S5 dan R6–R10 10 kΩ ke +3V3; emitor → GND |
| Q1 AO3400 (SOT-23) | drain = LED_K, source = GND, gate ← R11 100 Ω ← IR_EN; gate–R12 10 kΩ–GND |
| C1 100 nF | +3V3 ke GND |

Nilai 180 Ω dan 10 kΩ = nilai awal; cek datasheet ITR20001 dan setel saat uji. Slot sensor cadangan di lengan
jangkar belum masuk skematik (footprint kosong ditambahkan saat layout).

## 5. Daftar komponen (ringkas)

PCB utama: U1 ESP32 DevKit, U2 TB6612, U3 MP1584, D1 SS14, C1 100 µF, C2 C4 C5 C6 100 nF, C3 10 µF,
R1 100k, R2 33k, R3 1k, R4 10k, R5–R8 10k, Q1 S8050, BZ1, SW1 saklar geser, SW2 SW3 tombol 6×6,
J1 JST XH 2, J2 J3 JST PH 6, J4 1×4, J5 lubang tembus 2×5 (tanpa komponen), H1–H6 M3.

PCB sensor: U1–U5 ITR20001, R1–R5 180 Ω, R6–R10 10k, R11 100 Ω, R12 10k, Q1 AO3400, C1 100 nF, J1 2×5,
H1 H2 M3.

Resistor 10 kΩ terpakai: 11 (RAB: 10 pcs, kurang 1).
