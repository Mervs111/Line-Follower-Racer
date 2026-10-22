# Line Follower ESP32 + Block Programming

Proyek PjBL Semester 5: robot line follower yang murah tapi performanya bagus,
dan bisa diprogram pakai blok (user extension Mind+).

## Arsitektur

1. **Library C++ `LineFollower`** (`firmware/lib/LineFollower/`): logika utama, ditulis dan dites duluan.
2. **Desain blok**: 1 blok = 1 fungsi library.
3. **Extension Mind+** (`mindplus-ext/`): blok menghasilkan kode C++ yang memanggil library,
   di-compile native sehingga loop PID tetap cepat.

## Hardware singkat

| Bagian | Pilihan |
|---|---|
| MCU | ESP32 DevKit 30 pin (ESP32 biasa) |
| Sensor | 12× QRE1113GR + mux CD74HC4067 di PCB sensor bentuk jangkar (`hardware/sensor-garis/`) |
| Driver motor | TB6612FNG + motor N20 6V 500 RPM dengan encoder, roda Ø34 |
| Power | 2S 18650 + BMS → buck MP1584 5V |
| UI | OLED 0,96" I2C, 2 tombol, buzzer |

Rancangan terkini dan pin map ada di [`CLAUDE.md`](CLAUDE.md). `firmware/lib/LineFollower/src/Pins.h` masih peta
lama (ESP32-S3) dan akan diperbarui sebelum milestone firmware pertama.

## Struktur repo

```
├── firmware/        proyek PlatformIO (library LineFollower + test harness)
├── mindplus-ext/    extension Mind+
├── hardware/        proyek KiCad (PCB sensor, PCB utama) + tools
├── mechanical/      model 3D (CadQuery, STEP, DXF, STL)
├── docs/            charter, skematik, wiring diagram, logbook, panduan
└── arsip/           file yang sudah digantikan rancangan terbaru
```

## Build

```bash
cd firmware
pio run            # compile
pio run -t upload  # flash
pio device monitor # serial 115200
```

## Progres

- [ ] M0: setup PlatformIO, serial jalan, blink WS2812
- [ ] M1: driver motor + perintah serial `m <kiri> <kanan>`
- [ ] M2: baca sensor mentah ON/OFF, stream ke serial
- [ ] M3: kalibrasi + posisi + simpan/muat NVS
- [ ] M4: PID `follow()` + tuning lewat serial
- [ ] M5: junction, tombol, buzzer, baterai + low-battery warning
- [ ] M6: extension Mind+
- [ ] M7: contoh program + panduan blok
