# Line Follower ESP32-S3 + Block Programming

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
| MCU | ESP32-S3-WROOM-1-N4 (flash 4MB, tanpa PSRAM) |
| Sensor | 8× ITR20001/QRE1113, emitter IR di-switch lewat MOSFET |
| Driver motor | TB6612FNG + motor N20 6V |
| Power | LiPo 2S → buck MP1584 5V → LDO ME6211 3,3V |
| UI | 2 tombol, buzzer, 1× WS2812, header I2C |

Pin map lengkap ada di [`CLAUDE.md`](CLAUDE.md) dan
[`firmware/lib/LineFollower/src/Pins.h`](firmware/lib/LineFollower/src/Pins.h).

## Struktur repo

```
├── firmware/        proyek PlatformIO (library LineFollower + test harness)
├── mindplus-ext/    extension Mind+
└── docs/            panduan pemakaian
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
