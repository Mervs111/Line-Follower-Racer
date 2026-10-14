# Acuan Skematik v1 — Robot Line Tracer Micro (KiCad)

Dibuat 11/10/2026, diperbarui ke **v2 13/10/2026**: PCB utama disederhanakan (kapasitor kecil dibuang, D1 jadi
1N5819 kaki tembus) dan PCB sensor jadi **16 sensor + multiplexer + LED indikator tiap sensor**. Menggantikan
bagian `docs/minsys-v1.md` yang sudah tidak berlaku (baterai 14500, papan OLED terpisah/J_UI, IMU). Mengikuti
mekanik v12 di `mechanical/`: dua papan, **PCB utama** dan **PCB sensor (batang lurus)**, disambung **kabel pita
IDC 12 pin**; PCB sensor dipasang di dudukan 3D print.

Pin modul di bawah = susunan umum di marketplace. **Wajib dicocokkan dengan modul yang dibeli** (tulisan
di PCB modul) sebelum footprint dibuat.

## 1. Struktur proyek KiCad

```
hardware/
├── ltm-lib/       symbol + footprint buatan sendiri (ESP32 DevKit, TB6612, MP1584, ITR20001)
├── ltm-main/      PCB utama
└── ltm-sensor/    PCB sensor 16 titik (batang lurus)
```

## 2. Symbol buatan sendiri

### ESP32 DevKit 30 pin (susunan DOIT DevKit V1)

Nomor pin footprint: 1–15 baris kiri dari ujung antena ke ujung USB, 16–30 baris kanan dari ujung antena
ke ujung USB. **Cek jarak antar baris (22,86 atau 25,4 mm) dan urutan pin dengan modul asli.**

| Pin | Nama | Net | | Pin | Nama | Net |
|---|---|---|---|---|---|---|
| 1 | EN | — | | 16 | GPIO23 | ENC_R_A |
| 2 | VP / GPIO36 | SIG (mux) | | 17 | GPIO22 | SCL |
| 3 | VN / GPIO39 | VBAT_SENSE | | 18 | TX0 / GPIO1 | — (USB) |
| 4 | GPIO34 | BTN_A | | 19 | RX0 / GPIO3 | — (USB) |
| 5 | GPIO35 | BTN_B | | 20 | GPIO21 | SDA |
| 6 | GPIO32 | MUX_S3 | | 21 | GPIO19 | ENC_R_B |
| 7 | GPIO33 | MUX_S2 | | 22 | GPIO18 | PWMA |
| 8 | GPIO25 | MUX_S1 | | 23 | GPIO5 | AIN1 |
| 9 | GPIO26 | MUX_S0 | | 24 | TX2 / GPIO17 | AIN2 |
| 10 | GPIO27 | IR_EN | | 25 | RX2 / GPIO16 | PWMB |
| 11 | GPIO14 | ENC_L_B | | 26 | GPIO4 | BIN1 |
| 12 | GPIO12 | BUZ | | 27 | GPIO2 | STBY |
| 13 | GPIO13 | ENC_L_A | | 28 | GPIO15 | BIN2 |
| 14 | GND | GND | | 29 | GND | GND |
| 15 | VIN | +5V | | 30 | 3V3 | +3V3 |

Pembagian v2 (13/10/2026) mengikuti layout: baris depan ESP32 (pin 1–15) ke kabel pita J5, tombol, buzzer,
encoder kiri; baris belakang (pin 16–30) ke TB6612, I2C, dan encoder kanan. Urutan MUX_S3..S0 di pin 6–9 sengaja
dibalik supaya jalur ke J5 tidak saling silang (jalur minimal 0,8 mm). Encoder memakai pull-up internal (INPUT_PULLUP).
GPIO12 (BUZ) harus LOW saat boot (R4 pull-down). GPIO2 = STBY: ditarik LOW oleh TB6612 saat boot, jadi mode
download aman dan motor mati sampai firmware siap.

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
| C1 100 µF/16 V elko | VBAT ke GND, dekat pin VM TB6612 (meredam lonjakan arus motor) |
| U3 MP1584 | lihat tabel modul; set 5,0 V sebelum ESP32 dipasang |
| D1 1N5819 (kaki tembus) | anoda = +5V_BUCK, katoda = +5V (mencegah arus balik saat USB dicolok) |
| R1 100 kΩ, R2 33 kΩ | VBAT–R1–VBAT_SENSE–R2–GND (GPIO39; bacaan dirata-rata di firmware) |

Kapasitor 100 nF/10 µF tambahan (C2–C6 di v1) tidak dipasang: modul TB6612, MP1584, dan ESP32 DevKit sudah
punya kapasitor sendiri.

BMS dan modul charger berada di luar PCB (BMS di bawah PCB utama, charger di dinding belakang rangka dengan
port USB-C menghadap belakang; diputuskan tetap di sana 11/10/2026). Sambungan kabel:

| Dari | Ke |
|---|---|
| Kabel hitam holder (− sel 1) | B− di BMS |
| Plat penghubung antar sel di ujung holder (titik tengah) | BM di BMS, **kabel tambahan** disolder ke plat |
| Kabel merah holder (+ sel 2) | B+ di BMS |
| Modul charger 2S USB-C, OUT+ / OUT− | P+ / P− di BMS |
| P+ / P− di BMS | J1 PCB utama (BAT+ / GND) |

Charger tersambung langsung ke BMS, tidak lewat SW1, jadi robot bisa dicas saat saklar OFF.

Holder seri 2 kabel (RAB) tetap dipakai, tapi BMS 2S butuh titik tengah (BM) untuk mengukur tegangan tiap
sel, jadi 1 kabel tambahan disolder ke plat yang menyambung + sel 1 dengan − sel 2. Tanpa BM, proteksi
BMS tidak bekerja benar. Urutan menyambung: B−, lalu BM, lalu B+. BMS jenis ini umumnya hanya pelindung
(tidak menyeimbangkan sel), jadi pakai 2 sel merek & kapasitas sama dengan tegangan nyaris sama
(selisih ≤ 0,05 V) saat pertama dirangkai.

### ESP32, driver, motor
| Komponen | Sambungan |
|---|---|
| U1 ESP32 DevKit | tabel ESP32 di atas |
| U2 TB6612 | tabel TB6612 di atas |
| J2 motor kiri, JST PH 6 pin | 1 ML_P, 2 +3V3, 3 ENC_L_A, 4 ENC_L_B, 5 GND, 6 ML_N |
| J3 motor kanan, JST PH 6 pin | 1 MR_P, 2 +3V3, 3 ENC_R_A, 4 ENC_R_B, 5 GND, 6 MR_N |
| Encoder | tanpa resistor: pull-up internal ESP32 (`INPUT_PULLUP`) di GPIO 13, 14 (kiri), 23, 19 (kanan) |

Urutan kabel encoder N20 beda-beda tiap penjual: cocokkan dengan kabel motor yang dibeli.

### OLED, tombol, buzzer
| Komponen | Sambungan |
|---|---|
| J4 OLED, 1×4 | 1 GND, 2 +3V3, 3 SCL, 4 SDA (sebagian modul VCC dulu baru GND: cek) |
| SW2 tombol A | BTN_A (GPIO34) ke GND; R5 10 kΩ pull-up ke +3V3 (GPIO34/35 tanpa pull-up internal) |
| SW3 tombol B | BTN_B (GPIO35) ke GND; R6 10 kΩ pull-up ke +3V3 |
| Q1 S8050 | emitor = GND; kolektor = kaki − buzzer |
| R3 1 kΩ, R4 10 kΩ | BUZ–R3–basis Q1; basis–R4–GND (GPIO12 harus LOW saat boot) |
| BZ1 buzzer aktif 5 V | + = +5V, − = kolektor Q1 |

### Konektor ke PCB sensor (kabel pita)
J5 = box header IDC 2×6 (berkunci) di hidung PCB utama. Kabel pita 12 kabel + 2 konektor IDC female, lurus
(pin n ke pin n) ke J1 PCB sensor. Baris belakang (pin ganjil) = 6 sinyal, baris depan (pin genap) = daya + I2C;
di kabel, SIG diapit +5V dan GND.

| Pin | Net | | Pin | Net |
|---|---|---|---|---|
| 1 | IR_EN (GPIO27) | | 2 | +5V |
| 3 | SIG (GPIO36) | | 4 | GND |
| 5 | MUX_S0 (GPIO26) | | 6 | +3V3 |
| 7 | MUX_S1 (GPIO25) | | 8 | GND |
| 9 | MUX_S2 (GPIO33) | | 10 | SDA (GPIO21) |
| 11 | MUX_S3 (GPIO32) | | 12 | SCL (GPIO22) |

Lubang baut: 4× M3 (H1–H2 dudukan baterai/rangka, H3–H4 bahu + lengan dudukan PCB sensor).

## 4. PCB sensor 16 titik (batang lurus)

Sensor S1 (paling kiri) sampai S16 (paling kanan), jarak 6,5 mm. Lihat dari atas, robot maju ke atas.

| Komponen | Sambungan |
|---|---|
| J1 box header IDC 2×6 | urutan pin sama dengan J5 PCB utama |
| U1–U16 ITR20001 (sisi bawah) | kolektor → S1–S16, emitor → GND |
| LED IR, seri berdua | +5V → R1–R8 120 Ω → anoda U(ganjil) → katoda U(ganjil) → anoda U(genap) → katoda → LED_K |
| R9–R24 10 kΩ | pull-up S1–S16 ke +3V3 (dipasang di bawah modul mux) |
| Q1 AO3400 (SOT-23) | drain = LED_K, source = GND, gate ← R41 100 Ω ← IR_EN; gate–R42 10 kΩ–GND |
| U17 modul mux CD74HC4067 (socket) | C0–C15 = S1–S16, SIG → SIG, S0–S3 → MUX_S0–S3, EN → GND, VCC +3V3 |
| U18 MCP23017 DIP-28 (socket) | I2C alamat 0x20 (A0–A2 ke GND), RESET ke +3V3; GPA7..GPA0 = LED1–8, GPB7..GPB0 = LED9–16 |
| D1–D16 LED SMD 0805 (sisi atas) + R25–R40 330 Ω | pin MCP23017 → resistor → LED → GND (± 4 mA) |
| C1, C2 100 nF | +3V3 ke GND dekat modul mux dan MCP23017 |

LED IR: (5 V − 2 × 1,2 V) / 120 Ω ≈ 21 mA per pasang, total ± 170 mA lewat Q1. Nilai 120 Ω / 10 kΩ = nilai
awal; cek datasheet ITR20001 dan setel saat uji. Urutan pin modul mux = susunan umum, **cek modul asli**.
I2C: OLED (0x3C) dan MCP23017 (0x20) satu jalur; pull-up I2C dari modul OLED (cek ada resistornya).

## 5. Daftar komponen (ringkas)

PCB utama v2 (semua kaki tembus): U1 ESP32 DevKit, U2 TB6612, U3 MP1584, D1 1N5819, C1 100 µF, R1 100k,
R2 33k, R3 1k, R4 10k, R5 R6 10k, Q1 S8050, BZ1, SW1 saklar geser, SW2 SW3 tombol 6×6, J1 JST XH 2,
J2 J3 JST PH 6, J4 socket 1×4 (OLED), J5 box header IDC 2×6, H1–H4 M3. Socket header female untuk modul:
1×15 ×2 (ESP32), 1×8 ×2 (TB6612).

PCB sensor: U1–U16 ITR20001, U17 modul mux CD74HC4067 (+ socket female 1×16 dan 1×8), U18 MCP23017 (+ socket
DIP-28), D1–D16 LED 0805, R1–R8 120 Ω, R9–R24 10k, R25–R40 330 Ω, R41 100 Ω, R42 10k (semua 0805), Q1 AO3400,
C1 C2 100 nF 0805, J1 box header IDC 2×6, H1 H2 M3.

Resistor 10 kΩ kaki tembus terpakai di PCB utama: 3 (RAB: 10 pcs, cukup). Resistor 0805 PCB sensor: 42.
