# Referensi Desain PCB

Disimpan 08/10/2026 atas permintaan kelompok: arah desain PCB **mengikuti referensi ini**, bukan
"tempel modul" (modul breakout driver/buck ditancap atau ditempel di PCB dianggap kurang proper).

## 1. `ref-pcb-r3dmaker-lf.png` — PCB line follower (R3D Maker)

![ref 1](ref-pcb-r3dmaker-lf.png)

Yang terlihat:
- **Papan sensor berbentuk sayap/busur** di depan dengan ± 14 pasang sensor diskrit through-hole
  (LED + fototransistor + resistor) langsung di PCB, bukan modul sensor.
- **Leher panjang** dari sayap ke papan utama; sambungan antar papan lewat **header 8 pin** (board-to-board).
- Papan utama: **footprint ESP32 DevKit 38 pin disolder langsung** (2 × 19 pin), **OLED** di bagian bawah,
  ± 6 tombol (menu), LED indikator, konektor motor/daya di sisi.
- Bentuk PCB custom (bukan kotak), lubang baut di tiap ujung.

## 2. `ref-pcb-esp32-driver-ic.png` — PCB kontrol robot dengan IC driver

![ref 2](ref-pcb-esp32-driver-ic.png)

Yang terlihat:
- **ESP32 DevKit** dipasang di PCB custom.
- **Driver motor berupa IC SMD yang disolder langsung** (4 chip), bukan modul breakout.
- Konektor **XT30** untuk motor/daya, kapasitor elektrolit besar di jalur daya, saklar rocker.

## Kesimpulan untuk desain kita (minsys "semi-terintegrasi")

| Bagian | Dipakai | Catatan |
|---|---|---|
| ESP32 | **DevKit disolder langsung** (seperti kedua referensi) | Tidak perlu merancang USB-serial & auto-reset sendiri |
| Driver motor | **IC TB6612FNG (SSOP-24) disolder langsung** | Kaki rapat 0,65 mm: solder pakai flux + teknik drag, atau jasa PCBA |
| Regulator 5 V | **IC buck (mis. MP1584EN, SOIC-8) + induktor + kapasitor** di PCB | Rangkaian ikut datasheet |
| Sensor garis | **Komponen diskrit** (ITR20001 / pasangan LED IR + fototransistor) di PCB sensor | Seperti referensi 1 |
| OLED + tombol | OLED modul disolder + tombol di PCB | Seperti referensi 1 |
| Baterai, BMS, charger | Tetap modul, di dekat holder baterai | Bisa diintegrasikan di versi berikutnya |
| Sambungan papan sensor ↔ utama | Header board-to-board | Seperti referensi 1 |
