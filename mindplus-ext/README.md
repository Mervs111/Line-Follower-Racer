# Extension Mind+ V2 "Robot LFM X1"

Blok Mind+ untuk robot LFM X1 (mode **upload / Arduino C**). Setiap blok menghasilkan satu panggilan ke library C++
`LineFollower` (`firmware/lib/LineFollower`). Program dikompilasi native ke ESP32, jadi PID tetap jalan 1 kHz.
Cara memakai blok ada di [`docs/panduan-blok.md`](../docs/panduan-blok.md).

```
mindplus-ext/
├── lfm-x1/              sumber extension (format contoh resmi DFRobot "example-upload-module")
│   ├── index.js         definisi blok + menu (teks bahasa Indonesia)
│   ├── func.js          kode C++ yang dihasilkan tiap blok
│   ├── icon/            ikon blok dan menu
│   ├── locales/id.json  nama extension
│   └── public/          config.json (id LFMX1, papan dev-DFRobot-Esp32) + cover.png
├── build.js             membangun extension dengan builder resmi + menyalin library C++
├── uji/gen_contoh.mjs   membuat contoh/ dari func.js (generator Mind+ tiruan)
├── contoh/              4 contoh program blok dalam bentuk .ino (sudah dicek bisa dikompilasi)
└── build/               hasil build (tidak masuk git)
```

Library C++ **tidak** disimpan di sini: `build.js` menyalinnya dari `firmware/lib/LineFollower` ke
`public/libraries/LineFollower/` tiap build, jadi PlatformIO dan Mind+ selalu memakai kode yang sama.

## Membangun

Perlu Node.js (sudah ada di laptop, v24) dan builder resmi DFRobot (sekali saja, di luar repo):

```
git clone https://gitee.com/mind-plus/mindplus-ext2-builder.git
cd mindplus-ext2-builder
npm install
node <repo>/mindplus-ext/build.js <folder mindplus-ext2-builder>
```

Hasilnya di `mindplus-ext/build/ext-LFM-LFMX1@0.1.0/`. Builder memakai webpack 4; `build.js` otomatis menambah
`--openssl-legacy-provider` untuk Node 17 ke atas.

## Memuat ke Mind+

Menurut panduan uji resmi (Mind+ **V2.0.7 ke atas**):

1. Mind+ > Pengaturan > Opsi lanjutan > nyalakan **Mode pengembang**.
2. Ekstensi (模块扩展) > **Muat ekstensi uji** (加载测试扩展) > pilih `config.json` di folder hasil build.
3. Extension tampil dengan tanda "uji". Pilih papan **ESP32** biasa (`dev-DFRobot-Esp32`), bukan FireBeetle.

Catatan dari panduan resmi: selama mode pengembang, **menyimpan file proyek dimatikan**. Untuk demo, susun
blok lalu langsung upload; simpan program dalam bentuk tangkapan layar atau `.ino` dari jendela kode.

## Status pengecekan (28/11/2026)

| Sudah | Belum |
|---|---|
| sintaks `index.js`, `func.js`, `build.js` (`node --check`), JSON valid | build lewat builder resmi (di laptop ini ditolak pengaman Claude Code; jalankan sendiri, perintah di atas) |
| kode hasil blok: 4 contoh `.ino` dikompilasi PlatformIO (core 2.0.17, `-Wall -Wextra`, tanpa warning) | memuat ke Mind+ V2 (Mind+ belum terpasang) |
| firmware utama: core 2.0.17 dan 4.0.0 | versi core ESP32 bawaan Mind+ V2 (library mendukung 2.x–4.x; 1.0.x belum pernah dicoba) |
| | anggapan `parameter.X.code` = nilai apa adanya tanpa tanda kutip (disimpulkan dari contoh resmi, tidak tertulis di dokumentasi) |

Kalau Mind+ gagal kompilasi, buka jendela kode Mind+, salin kodenya, dan bandingkan dengan `contoh/*.ino`.

## Mengubah blok

1. Ubah `lfm-x1/index.js` (tampilan) dan `lfm-x1/func.js` (kode C++; nama method = `opcode`).
2. Fungsi baru di library: tulis dulu di `firmware/lib/LineFollower`, cek `pio run` di `firmware/`.
3. `node mindplus-ext/uji/gen_contoh.mjs`, lalu kompilasi contoh:
   `python -m platformio ci --board esp32dev --lib firmware/lib/LineFollower --project-option="platform=espressif32@^6.9.0" mindplus-ext/contoh/RuteIndeks/RuteIndeks.ino`
4. Naikkan `version` di `public/config.json`, build ulang, muat ulang di Mind+.
