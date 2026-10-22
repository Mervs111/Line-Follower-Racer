# PCB utama (baru, KiCad 10)

Proyek awal PCB utama pengganti `ltm-main/` (v2, 13/10). **Skematik digambar user**, Claude bantu layout
(penempatan, routing, DRC) lewat MCP KiCad. Dibuat 22/10/2026 oleh `hardware/tools/gen_pcb_utama_awal.py`
(sekali jalan; `--paksa` menimpa .kicad_pcb dan .kicad_sch, jadi **jangan dijalankan lagi** sesudah user mulai
menggambar).

## Isi awal

| File | Isi |
|---|---|
| `pcb-utama.kicad_pro` | salinan setting PCB sensor (aturan cetak 21/10, net class), nama diganti |
| `pcb-utama.kicad_sch` | **skematik lengkap** (22/10, dibuat `hardware/tools/gen_sch_utama.py`): 21 komponen, ERC 0, netlist dicek terhadap tabel pin CLAUDE.md. PDF: `pcb-utama-skematik.pdf` |
| `pcb-utama.kicad_pcb` | outline Edge.Cuts + lubang + gambar bantu (lihat di bawah); belum ada footprint |
| `sym-lib-table`, `fp-lib-table` | library `ltm` di `../ltm-lib` (ESP32 DevKit, modul TB6612, MP1584). Footprint ini sementara: cocokkan ukurannya dengan modul yang dibeli |

Cek awal: `kicad-cli pcb drc` 0 error, `kicad-cli sch erc` 0 error.

## Koordinat (sama dengan proyek PCB sensor)

X KiCad = 200 + x robot, Y KiCad = 180,55 − y robot. Robot: x ke kanan, y maju, 0,0 = tengah poros roda.
Karena sama, lubang H1/H2 PCB sensor (KiCad (195,25; 95) dan (204,75; 95)) jatuh tepat di lubang PCB utama, dan
outline PCB sensor rev B terlihat di lapisan **User.Comments** sebagai acuan.

## Bentuk dan lubang (dari model 3D v16)

- Outline: bentuk **"mobil F1"** (dipilih user 22/10, 100 × 127 mm): sidepod lebar di samping (x ±50, y 23,5–54),
  pinggang menyempit di antara roda (x ±37), lalu hidung panjang (x ±27) ke PCB sensor. Tiap sudut punya jari-jari
  sendiri (3–10 mm). Sumber satu-satunya: `MAIN_R` di `mechanical/cadquery/ltm_v16.py` (titik x, y, jari-jari
  setengah kanan; kiri dicerminkan). Perbandingan 3 opsi: https://claude.ai/artifact/PYASQTHgLPKjVaxw33yyMZ
- 4 lubang M3 tiang dudukan motor + baterai di robot (±33; ±20).
- 2 lubang M3 PCB sensor H1/H2 di robot (±4,75; 85,55).
- 2 celah piringan encoder motor (X 10,2–13,9 kiri dan kanan, Y −6,6..6,6).

## Gambar bantu penempatan (User.Drawings)

Posisi dari model 3D v16; boleh digeser kalau perlu, tapi cek tabrakan dengan dudukan 3D print.

| Blok | Area (x, y robot, mm) | Catatan |
|---|---|---|
| ESP32 DevKit | x ±25,75, y 24,5–52,8 | socket female 8,5 mm, USB ke kiri |
| OLED 0,96" | x ±13,65, y 53,5–81,3 | socket, header di depan |
| TB6612 | x 28–48,3, y 25–45,3 | modul di socket |
| Dudukan baterai | x ±38, y −24..24 | 3D print di atas PCB: **komponen di bawahnya maks 10 mm** |
| Motor N20 | x ±(12,5–37,5), y ±6 | motor menempel di PCB (dudukan 3D print) |
| J2 / J3 motor | y 13–17,5 | kiri / kanan |
| MP1584 | x 4–26, y −29,5..−12,5 | set 5 V sebelum dudukan baterai dipasang |
| Charger 2S, BMS | x −29..−4 (BMS di sisi bawah) | |
| SW1 | tepi kiri, y 26–34,6 | |
| Tombol A / B | x −22 / 22, y 63–69 | |
| Buzzer | (38; 51,5), Ø12 | sidepod kanan |
| C1 elko 100 µF | (−37; 40), Ø6,3 | sidepod kiri |
| **J5** JST XH 8 pin | tengah (−37,24; 55,12), diputar 205,6° sejajar tepi miring sidepod kiri | **urutan pin = J1 PCB sensor**, pin 1 di ujung dekat hidung (−29,34; 58,89) |

Sidepod kanan sudah penuh (TB6612, buzzer, S8050), hidung terpakai OLED, tombol, dan baut H1/H2, jadi J5 di sidepod
kiri. Kabel dibundel menyusuri tepi kiri hidung (di kiri tombol A) lalu masuk ke J1 dari depan; pin 1 J5 dekat hidung
dan pin 1 J1 di kanan, jadi kabel tidak bersilangan.

Urutan pin J5 (wajib sama dengan J1 PCB sensor): 1 +5V, 2 +3V3, 3 GND, 4 MUX_S3, 5 MUX_S2, 6 MUX_S1, 7 MUX_S0,
8 MUX_SIG. Pin ESP32 ada di tabel `CLAUDE.md`; sambungan per blok di wiring diagram
https://claude.ai/artifact/Enb11oGXVb5YkwQmU6DhJY (blok 1–4, sumber `docs/wiring-diagram.html`).

Aturan cetak: `docs/aturan-cetak-pcb.md` (jalur min 0,3 mm, ke ground pour 0,5 mm).

## Langkah menggambar skematik (KiCad 10)

**Status 22/10: skematik sudah dibuat Claude** dengan `py hardware/tools/gen_sch_utama.py` (atas permintaan user),
mengikuti langkah di bawah. Langkah ini tetap berguna untuk memahami dan mengecek isinya. Kalau skematik diubah
manual di KiCad, **jangan jalankan generator lagi** (`--paksa` menimpa semua perubahan); ubah generatornya saja kalau
mau tetap dari skrip. Peringatan "symbol doesn't match library" tidak muncul karena library `ltm` (format KiCad 7)
dinaikkan formatnya di memori sebelum disalin.

Sumber sambungan: wiring diagram blok 1–4 dan `docs/skematik-v1.md` bagian 3 (nomor komponen sama). Satu lembar A3
cukup; sambung antarblok dengan **label** (nama sama = tersambung), bukan kabel panjang. Lubang M3 sudah ada di PCB
sebagai lingkaran Edge.Cuts, jadi tidak perlu simbol MountingHole. BMS dan charger ada di luar PCB (tanpa simbol).

### 0. Persiapan
1. Buka `pcb-utama.kicad_pro` (bukan file `.kicad_sch` langsung), lalu buka skematiknya.
2. Cek modul yang dibeli, karena footprint `ltm` masih sementara:
   - ESP32 DevKit 30 pin: ukur jarak antar baris pin. 25,4 mm → `ltm:ESP32_DevKit_30P_W25.4` (bawaan),
     22,86 mm → `ltm:ESP32_DevKit_30P_W22.86`.
   - Modul TB6612: urutan pin beda-beda tiap penjual, cocokkan dengan simbol `ltm:TB6612_Module`.
   - Modul MP1584: cek letak lubang IN+/IN−/OUT+/OUT−.
3. Bagi lembar jadi 4 area: Daya, ESP32 + driver motor, Layar/tombol/buzzer, Kabel sensor.

### 1. Daya (wiring blok 1)
| Ref | Simbol | Footprint | Sambungan |
|---|---|---|---|
| J1 | `Connector_Generic:Conn_01x02` | `Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical` | 1 BAT+, 2 GND (dari P+/P− BMS) |
| SW1 | `Switch:SW_SPDT` | `Button_Switch_THT:SW_Slide_SPDT_Angled_CK_OS102011MA1Q` (cek saklar yang dibeli) | kaki tengah VBAT, satu kaki samping BAT+, kaki lain **X** |
| U3 | `ltm:MP1584_Module` | bawaan simbol | IN+ VBAT, IN− GND, OUT+ `+5V_BUCK`, OUT− GND |
| D1 | `Diode:1N5819` | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` | anoda `+5V_BUCK`, katoda +5V |
| C1 | `Device:C_Polarized` 100 µF/16 V | `Capacitor_THT:CP_Radial_D6.3mm_P2.50mm` | + VBAT, − GND (nanti di dekat VM TB6612) |
| R1, R2 | `Device:R` 100k, 33k | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | VBAT – R1 – `VBAT_SENSE` – R2 – GND |

+5V, +3V3, GND pakai simbol daya (`power:+5V`, `power:+3V3`, `power:GND`). VBAT, `+5V_BUCK`, `VBAT_SENSE` pakai
label. Pasang `power:PWR_FLAG` di VBAT, GND, dan +5V (dayanya datang dari konektor/dioda, bukan dari pin keluaran
daya). +3V3 tidak perlu karena pin 3V3 ESP32 sudah keluaran daya.

### 2. ESP32 (U1, `ltm:ESP32_DevKit_30`)
VIN → +5V, GND (2 pin) → GND, 3V3 → +3V3. Beri label di ujung tiap pin:

| GPIO | Label | | GPIO | Label | | GPIO | Label |
|---|---|---|---|---|---|---|---|
| 36 | MUX_SIG | | 25 | MUX_S1 | | 19 | ENC_R_B |
| 39 | VBAT_SENSE | | 26 | MUX_S0 | | 18 | PWMA |
| 34 | BTN_A | | 13 | ENC_L_A | | 5 | AIN1 |
| 35 | BTN_B | | 14 | ENC_L_B | | 17 | AIN2 |
| 32 | MUX_S3 | | 12 | BUZ | | 16 | PWMB |
| 33 | MUX_S2 | | 23 | ENC_R_A | | 4 | BIN1 |
| 22 | SCL | | 21 | SDA | | 15 | BIN2 |
| 2 | STBY | | | | | | |

Pin tidak dipakai (EN, GPIO27, TX0, RX0) → **X** (no-connect).

### 3. Driver motor + motor (wiring blok 2)
| Ref | Simbol | Footprint | Sambungan |
|---|---|---|---|
| U2 | `ltm:TB6612_Module` | bawaan simbol | PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY ke label yang sama; VM VBAT; VCC +3V3; 3 GND → GND; AO1/AO2 → `ML_P`/`ML_N`; BO1/BO2 → `MR_P`/`MR_N` |
| J2 (kiri) | `Connector_Generic:Conn_01x06` | `Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical` | 1 ML_P, 2 +3V3, 3 ENC_L_A, 4 ENC_L_B, 5 GND, 6 ML_N |
| J3 (kanan) | sama | sama | 1 MR_P, 2 +3V3, 3 ENC_R_A, 4 ENC_R_B, 5 GND, 6 MR_N |

Encoder tanpa resistor (firmware pakai `INPUT_PULLUP`). Cocokkan urutan kabel dengan motor N20 yang dibeli.

### 4. Layar, tombol, buzzer (wiring blok 3)
| Ref | Simbol | Footprint | Sambungan |
|---|---|---|---|
| J4 (OLED) | `Connector_Generic:Conn_01x04` | `Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical` | 1 GND, 2 +3V3, 3 SCL, 4 SDA (**cek urutan di modul OLED**, ada yang VCC dulu) |
| SW2, SW3 | `Switch:SW_Push` | `Button_Switch_THT:SW_PUSH_6mm` | BTN_A / BTN_B ke GND |
| R5, R6 | `Device:R` 10k | resistor THT di atas | BTN_A / BTN_B ke +3V3 (wajib: GPIO34/35 tanpa pull-up) |
| Q1 | `Transistor_BJT:S8050` | `Package_TO_SOT_THT:TO-92_Inline` (cek urutan E-B-C) | E GND, C ke kaki − buzzer |
| R3, R4 | `Device:R` 1k, 10k | resistor THT | BUZ – R3 – basis Q1; basis – R4 – GND |
| BZ1 | `Device:Buzzer` | `Buzzer_Beeper:Buzzer_12x9.5RM7.6` | + ke +5V, − ke kolektor Q1 |

### 5. Kabel sensor J5 (wiring blok 4)
| Ref | Simbol | Footprint | Sambungan |
|---|---|---|---|
| J5 | `Connector_Generic:Conn_01x08` | `Connector_JST:JST_XH_B8B-XH-A_1x08_P2.50mm_Vertical` | 1 +5V, 2 +3V3, 3 GND, 4 MUX_S3, 5 MUX_S2, 6 MUX_S1, 7 MUX_S0, 8 MUX_SIG |

Ikuti **nomor pin**, bukan urutan nama (pin 4–7 terbalik). Harus sama persis dengan J1 PCB sensor.

### 6. Cek sebelum layout
1. Tools → Annotate: pertahankan nomor di tabel (U1 ESP32, U2 TB6612, U3 MP1584, ...).
2. Tools → Assign Footprints: semua komponen punya footprint.
3. Inspect → ERC: target 0 error. Yang sering muncul: "input power pin not driven" → PWR_FLAG; "pin not connected"
   → X; label yang hanya muncul sekali (salah ketik nama).
4. Simpan, lalu kabari Claude: netlist dicek terhadap tabel pin di atas, lalu Update PCB from Schematic (F8) dan
   penempatan sesuai gambar bantu.
