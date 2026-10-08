# Rancangan Minimum System v1 — Robot Line Tracer Micro

> **Update 08/10/2026:** arah desain berubah ke *semi-terintegrasi* (lihat `docs/referensi/README.md`):
> TB6612 dan buck 5 V jadi IC di PCB, bukan modul breakout. Pin map & sambungan sinyal di bawah tetap berlaku;
> bagian "carrier board berbasis modul" diganti oleh rancangan semi-terintegrasi.

Status: **draf rancangan untuk digambar di EasyEDA**. Dicek ulang oleh kelompok terhadap datasheet
sebelum PCB dipesan. Referensi bentuk: produk Voltra Techno (PCB control & display, minimum system,
sensor terpisah).

## Konsep v1: papan pembawa (carrier board) berbasis modul

Agar murah, mudah disolder tangan, dan sesuai RAB, minsys v1 **tidak menyolder chip langsung**.
Modul dipasang di header perempuan (female header) sehingga bisa dilepas-pasang:

| Bagian | Bentuk di PCB |
|---|---|
| ESP32 DevKit (30 pin, CH340, Type-C) | Female header 2 × 15 pin |
| Driver motor TB6612FNG (modul breakout 16 pin) | Female header 2 × 8 pin |
| Buck converter MP1584 (modul) | Pin header 4 titik (IN+, IN−, OUT+, OUT−) |
| OLED 1.3" I2C | Female header 1 × 4 pin |
| BMS 2S & charger 2S USB-C | Di dekat holder baterai, disambung kabel ke konektor BAT |

Pemasangan (diputuskan 08/10/2026 atas masukan kelompok): **modul kecil (TB6612, MP1584) disolder
langsung** ke PCB lewat pin header jantan (lebih kokoh terhadap getaran, lebih tipis). **ESP32 DevKit**
boleh disolder langsung juga, atau memakai female header tipe *round pin / machined* (jepitan lebih
kuat) agar mudah diganti saat pengembangan. Setiap modul **dites dulu di breadboard sebelum disolder**.

Dua papan: **Minsys** (ESP32, driver, power, OLED, tombol, buzzer) dan **Sensor** (5 sensor susunan panah).
OLED & tombol digabung ke minsys (beda dengan referensi yang memisahkan PCB control & display) untuk
menghemat biaya PCB.

v2 (opsional, setelah v1 terbukti): modul diganti chip langsung (ESP32-WROOM, TB6612 SSOP, regulator).

## Bentuk fisik (revisi 08/10/2026)

Robot rendah satu bidang: PCB sensor (90 × 38 mm, panah) dan PCB utama (80 × 92 mm) **sejajar** ± 6 mm dari
lantai, disambung baut + pin header (tanpa kabel; J_SENSOR berupa header board-to-board). Sensor di sisi
bawah PCB sensor (± 3 mm dari lantai, diatur tinggi ball caster mini). Semua komponen termasuk baterai
2× 14500, motor N20 (roda Ø34) di sisi atas; papan OLED + 2 tombol ditumpuk di atas ESP32 dengan spacer
(papan ketiga, disambung pin header). Visual: https://claude.ai/artifact/PHUWVJWJy2sDEXEf3AtSyx

## Diagram blok daya

```
Baterai 2S (2×14500) ─ BMS 2S ─ SW1 ─┬─────────────────────────────► VBAT (7,4–8,4 V)
   ▲                                  │                                  ├─► TB6612 VM (+ C 100 µF)
   └─ Charger 2S USB-C                ├─► R1 100k ─┬─ R2 33k ─ GND       │
                                      │            └─► GPIO33 (VBAT_SENSE)
                                      └─► MP1584 IN ─► OUT 5 V ─ D1 SS14 ─► +5V ─► DevKit VIN
                                                                        ├─► LED IR sensor
                                                                        └─► Buzzer
DevKit pin 3V3 (regulator onboard) ─► +3V3 ─► TB6612 VCC, OLED, encoder, fototransistor, pull-up
```

- **D1 (SS14)** mencegah 5 V dari buck mengalir balik ke USB laptop saat DevKit dicolok USB.
- **Pembagi tegangan 100k/33k**: 8,4 V → 2,08 V (di bawah batas ADC ± 3,1 V pada atenuasi 11 dB).
- **MP1584 wajib disetel ke 5,0 V dan diukur multimeter SEBELUM** DevKit dipasang.

## Pin map ESP32 DevKit 30 pin

| GPIO | Fungsi | Catatan |
|---|---|---|
| 36 (VP) | Sensor S1 (kiri luar) | ADC1, input saja |
| 39 (VN) | Sensor S2 | ADC1, input saja |
| 34 | Sensor S3 (tengah, paling depan) | ADC1, input saja |
| 35 | Sensor S4 | ADC1, input saja |
| 32 | Sensor S5 (kanan luar) | ADC1 |
| 33 | VBAT_SENSE | ADC1, dari pembagi 100k/33k |
| 13 | IR_EN (gate MOSFET emitter IR) | Output |
| 25 | TB6612 PWMA (motor kiri) | PWM LEDC 20 kHz |
| 26 | TB6612 AIN1 | |
| 27 | TB6612 AIN2 | |
| 14 | TB6612 PWMB (motor kanan) | PWM LEDC 20 kHz |
| 16 | TB6612 BIN1 | |
| 17 | TB6612 BIN2 | |
| 4 | TB6612 STBY | |
| 18 | Encoder kiri A | PCNT, pull-up |
| 19 | Encoder kiri B | PCNT, pull-up |
| 23 | Encoder kanan A | PCNT, pull-up |
| 5 | Encoder kanan B | PCNT, pull-up (pin strapping, aman untuk input) |
| 21 | I2C SDA (OLED) | |
| 22 | I2C SCL (OLED) | |
| 15 | Tombol A | Ke GND, pull-up internal |
| 2 | Tombol B | Ke GND, pull-up internal (LED onboard ikut menyala, tidak apa-apa) |
| 12 | Buzzer (lewat transistor) | Pin strapping: wajib LOW saat boot → resistor 10k ke GND di basis |
| 1, 3 | UART0 (USB) | **Jangan dipakai** |

Pin habis: 2 tombol saja (A = pindah menu, B = pilih). Tidak ada LED status terpisah (pakai OLED).

## Rangkaian per bagian

### 1. Driver motor (modul TB6612FNG)
| Pin modul | Ke |
|---|---|
| VM | VBAT (+ C1 100 µF/16 V elektrolit + C2 100 nF, dekat pin) |
| VCC | +3V3 |
| GND (semua) | GND |
| PWMA, AIN1, AIN2 | GPIO25, 26, 27 |
| PWMB, BIN1, BIN2 | GPIO14, 16, 17 |
| STBY | GPIO4 |
| AO1, AO2 | J_MOTOR_L pin M1, M2 |
| BO1, BO2 | J_MOTOR_R pin M1, M2 |

Firmware: PWM dibatasi ± 70% (motor N20 6 V, baterai 8,4 V penuh).

### 2. Konektor motor + encoder (J_MOTOR_L, J_MOTOR_R) — JST PH2.0 6 pin
| Pin | Sinyal | Ke |
|---|---|---|
| 1 | M1 | TB6612 AO1 / BO1 |
| 2 | VCC encoder | +3V3 |
| 3 | A | GPIO18 / GPIO23 + R 10k ke +3V3 |
| 4 | B | GPIO19 / GPIO5 + R 10k ke +3V3 |
| 5 | GND | GND |
| 6 | M2 | TB6612 AO2 / BO2 |

⚠️ **Urutan pin kabel N20 berbeda tiap penjual** — cocokkan dengan gambar produk sebelum menggambar.
Resistor pull-up 10k: pasang footprint; isi bila encoder tidak punya pull-up sendiri.

### 3. Pembaca tegangan baterai
R1 100 kΩ (VBAT → titik tengah), R2 33 kΩ (titik tengah → GND), C 100 nF (titik tengah → GND),
titik tengah → GPIO33.

### 4. OLED 1.3" (J_OLED, 1 × 4 pin)
GND, VCC (+3V3), SCL (GPIO22), SDA (GPIO21).
⚠️ **Sebagian modul urutannya VCC, GND** — cek modul yang dibeli. OLED 1.3" biasanya chip SH1106
(bukan SSD1306), penting untuk library.

### 5. Tombol
SW_A: GPIO15 ↔ GND · SW_B: GPIO2 ↔ GND · masing-masing C 100 nF paralel (debounce, opsional).

### 6. Buzzer (aktif 5 V)
GPIO12 → R 1 kΩ → basis Q1 (S8050 / 2N2222, NPN); basis → R 10 kΩ → GND;
emitor → GND; kolektor → buzzer (−); buzzer (+) → +5V.
Bila buzzer magnetik: dioda 1N4148 paralel buzzer (katoda ke +5V).

### 7. Konektor ke papan sensor (J_SENSOR, 1 × 9 pin, header 2,54 mm atau JST PH 9 pin)
| Pin | Sinyal |
|---|---|
| 1 | +5V (LED IR) |
| 2 | +3V3 (fototransistor) |
| 3 | GND |
| 4 | IR_EN (GPIO13) |
| 5–9 | S1–S5 (GPIO36, 39, 34, 35, 32) |

### 8. Baterai & saklar
J_BAT (JST XH 2 pin / XT30) dari BMS → SW1 (saklar geser) → VBAT. Charger 2S USB-C disambung ke
terminal charge BMS (di luar PCB, ikut petunjuk modul).

## Papan sensor (5 × ITR20001, susunan panah)

Per sensor (×5):
- LED IR: +5V → R 180 Ω → anoda; katoda → drain Q2 (bersama untuk 5 LED).
- Fototransistor: kolektor → output Sx dan R 10 kΩ ke +3V3; emitor → GND.

Q2: N-MOSFET logic-level SOT-23 (AO3400): gate ← IR_EN lewat R 100 Ω, gate → R 10 kΩ ke GND,
source → GND. Total arus LED ± 5 × 20 mA = 100 mA.

Nilai R 180 Ω dan 10 kΩ = **nilai awal**; cek datasheet ITR20001 (arus LED maks, Vf) dan setel saat uji.

Susunan panah: S3 di tengah paling depan; S2/S4 dan S1/S5 bergeser ke samping dan sedikit ke belakang;
jarak lateral antar sensor ± 10 mm (lebar garis 19 mm). Koordinat pasti ditetapkan saat layout.

## Aturan layout penting
- Antena ESP32 (ujung modul di DevKit) di tepi PCB, **tanpa tembaga di bawahnya**.
- Jalur VBAT & motor (M1/M2, VM) lebar ≥ 0,8 mm; jalur sinyal 0,25–0,3 mm.
- C 100 µF + 100 nF sedekat mungkin dengan pin VM TB6612.
- GND dibuat bidang (pour) di kedua sisi.
- Lubang baut M3 di 4 sudut + posisi bracket N20 & ball caster sesuai rancangan mekanik.
- Label setiap konektor dan polaritas baterai di silkscreen.

## BOM tambahan (belum ada di RAB revisi 3.1)
Dioda SS14 · kapasitor 100 µF/16 V · kapasitor 100 nF (± 6) · resistor 100k, 33k, 1k, 180 Ω (×5),
100 Ω · transistor S8050 · MOSFET AO3400 · female header 1×15 (×2), 1×8 (×2), 1×4 · konektor JST PH
9 pin · konektor baterai. Perkiraan ± Rp 25.000–35.000 → masuk ke "komponen pasif & kecil".
