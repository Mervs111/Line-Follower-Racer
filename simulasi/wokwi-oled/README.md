# Simulasi tampilan OLED + menu + tombol (Wokwi, 23/11/2026)

> **28/11: purwarupa lama.** Untuk mencoba firmware asli robot (menu yang sama + kalibrasi, sensor, motor, rute) pakai
> [`../wokwi-firmware/`](../wokwi-firmware/README.md).

Untuk mencoba tampilan OLED 0,96" (SSD1306 128 × 64, I2C) dan menu 5 tombol board interface sebelum barangnya ada.
Jalan di **wokwi.com** (browser, akun gratis), board **ESP32 DevKit C V4**. Belum dites di Wokwi oleh Claude (tidak ada
compiler di laptop); kalau ada error compile, salin pesan errornya.

| File | Isi |
|---|---|
| `sketch.ino` | kode layar + menu + tombol (U8g2), tanpa `delay()`, tanpa `String` |
| `diagram.json` | rangkaian: ESP32 + OLED + 5 tombol + potensiometer baterai |
| `libraries.txt` | library yang dipakai (`U8g2`) |

## Langkah di wokwi.com

1. Buka proyek ESP32 + OLED yang sudah ada (atau New Project → ESP32).
2. **Library**: tab *Library Manager* → `+` → cari **U8g2** → pilih. (Atau isi file `libraries.txt` dengan `U8g2`.)
3. **Kode**: ganti seluruh isi `sketch.ino` dengan isi `sketch.ino` di folder ini.
4. **Rangkaian**: pilih salah satu.
   - Cepat: tab `diagram.json` → ganti seluruh isinya dengan `diagram.json` di folder ini.
   - Manual: tambah komponen lewat tombol `+` lalu sambungkan sesuai tabel di bawah.
5. Tekan ▶ (Start). Klik area kosong di gambar rangkaian supaya tombol keyboard ikut bekerja.

| Komponen | Kaki | ke ESP32 | Catatan |
|---|---|---|---|
| OLED SSD1306 | GND / VCC / SCL / SDA | GND / 3V3 / 22 / 21 | sama dengan robot asli |
| Tombol KEMBALI | satu kaki / kaki seberang | 32 / GND | keyboard ← |
| Tombol ATAS | | 33 / GND | keyboard ↑ |
| Tombol OK | | 25 / GND | keyboard Enter |
| Tombol BAWAH | | 26 / GND | keyboard ↓ |
| Tombol LANJUT | | 27 / GND | keyboard → |
| Potensiometer | SIG / VCC / GND | VN (GPIO39) / 3V3 / GND | tegangan baterai pura-pura |

Tombol: kaki `1.l` ke GPIO, kaki `2.l` ke GND (kaki 1.l–1.r selalu tersambung, begitu juga 2.l–2.r). Potensiometer
diputar = tegangan baterai berubah (pin × 133/33, pembagi 100k/33k robot asli); di bawah 6,8 V ikon baterai berkedip.

**Kenapa tombol tidak memakai tangga resistor?** Simulasi analog Wokwi sangat sederhana: resistor hanya bisa jadi
pull-up/pull-down, jadi tegangan tangga resistor (0,30 / 0,93 / 1,49 / 2,12 / 2,63 V) tidak bisa disimulasikan. Di
simulasi tiap tombol ke GPIO sendiri. Kode untuk robot asli sudah ada: ganti `#define SIMULASI 1` jadi `0`, tombol
dibaca dari GPIO34 dengan ambang di tengah dua tegangan. Kode menunya tidak berubah.

## Aturan tombol

| Tombol | Fungsi |
|---|---|
| ATAS / BAWAH | pindah pilihan; saat mengedit angka: tambah / kurang. Ditahan = berulang, ditahan > 1,5 s = langkah × 10 |
| OK / LANJUT | masuk / pilih / simpan |
| KEMBALI | kembali satu layar / batal edit. Ditahan 0,8 s = langsung ke layar utama |
| apa saja | STOP saat robot berjalan, batal saat hitung mundur |

## Peta layar (usulan, silakan diubah)

```
LAYAR UTAMA  (nama robot, baterai, rute, kecepatan, status kalibrasi, warna garis, bar 12 sensor)
 ├─ OK      → hitung mundur 3-2-1 → BERJALAN (waktu, indeks ke-n, posisi garis) → SELESAI / BERHENTI
 ├─ ATAS/BAWAH → ganti rute
 └─ LANJUT  → MENU
              ├─ Mulai          (sama dengan OK di layar utama; ditolak kalau belum kalibrasi)
              ├─ Pilih rute     (Rute 1..5 + jumlah indeks; * = rute aktif)
              ├─ Kalibrasi      (OK → 3 s, progress bar → "Selesai, data disimpan")
              ├─ Lihat sensor   (bar 12 sensor ↔ angka 0–1000, posisi garis −1000..1000)
              ├─ Atur PID       (Kp, Kd, Kecepatan %; OK = edit, nilai berkedip)
              ├─ Warna garis    (OK = ganti Hitam/Putih)
              ├─ Tes motor      (Maju, Mundur, Putar kiri, Putar kanan; 1,5 s)
              └─ Info robot     (firmware, baterai, sensor, rute)
```

Yang masih palsu: data sensor (garis bergerak sendiri; sebelum kalibrasi rentangnya sempit), motor, dan robot
berjalan (tiap indeks 1,5 s). Daftar rute dan jumlah indeksnya hanya contoh (`ROUTE_STEPS`).

## Mengubah tampilan

- Tiap layar punya fungsi gambar sendiri: `drawHome`, `drawMenu`, `drawPid`, dst. Koordinat y = tepi atas huruf
  (`setFontPosTop`).
- Font yang dipakai: `u8g2_font_helvB08_tr` (judul), `6x10` (isi), `5x7` (kecil), `logisoso24/32` (angka besar).
  Daftar font lain: wiki U8g2 (fntlistall).
- Menambah item menu: tambah teks di `MENU_ITEMS`, naikkan `MENU_COUNT`, lalu tambah `case` di `openMenuItem`.
