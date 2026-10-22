# PCB utama (baru, KiCad 10)

Proyek awal PCB utama pengganti `ltm-main/` (v2, 13/10). **Skematik digambar user**, Claude bantu layout
(penempatan, routing, DRC) lewat MCP KiCad. Dibuat 22/10/2026 oleh `hardware/tools/gen_pcb_utama_awal.py`
(sekali jalan; `--paksa` menimpa .kicad_pcb dan .kicad_sch, jadi **jangan dijalankan lagi** sesudah user mulai
menggambar).

## Isi awal

| File | Isi |
|---|---|
| `pcb-utama.kicad_pro` | salinan setting PCB sensor (aturan cetak 21/10, net class), nama diganti |
| `pcb-utama.kicad_sch` | skematik kosong A3 dengan title block, siap digambar |
| `pcb-utama.kicad_pcb` | outline Edge.Cuts + lubang + gambar bantu (lihat di bawah); belum ada footprint |
| `sym-lib-table`, `fp-lib-table` | library `ltm` di `../ltm-lib` (ESP32 DevKit, modul TB6612, MP1584). Footprint ini sementara: cocokkan ukurannya dengan modul yang dibeli |

Cek awal: `kicad-cli pcb drc` 0 error, `kicad-cli sch erc` 0 error.

## Koordinat (sama dengan proyek PCB sensor)

X KiCad = 200 + x robot, Y KiCad = 180,55 − y robot. Robot: x ke kanan, y maju, 0,0 = tengah poros roda.
Karena sama, lubang H1/H2 PCB sensor (KiCad (195,25; 95) dan (204,75; 95)) jatuh tepat di lubang PCB utama, dan
outline PCB sensor rev B terlihat di lapisan **User.Comments** sebagai acuan.

## Bentuk dan lubang (dari model 3D v16)

- Outline: bentuk PCB utama v13–v16 (100 × 121 mm, hidung ke depan), sudut dibulatkan 2,5 mm. Sumber satu-satunya:
  `MAIN_R` di `mechanical/cadquery/ltm_v16.py`.
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
| Buzzer | (38; 51,5), Ø12 | |
| **J5** JST XH 8 pin | tengah (18,37; 80,20), diputar 126,4° sejajar tepi kanan hidung | **urutan pin = J1 PCB sensor**, pin 1 di ujung belakang (23,56; 73,15) |

Urutan pin J5 (wajib sama dengan J1 PCB sensor): 1 +5V, 2 +3V3, 3 GND, 4 MUX_S3, 5 MUX_S2, 6 MUX_S1, 7 MUX_S0,
8 MUX_SIG. Pin ESP32 ada di tabel `CLAUDE.md`; sambungan per blok di wiring diagram
https://claude.ai/artifact/Enb11oGXVb5YkwQmU6DhJY (blok 1–4, sumber `docs/wiring-diagram.html`).

Aturan cetak: `docs/aturan-cetak-pcb.md` (jalur min 0,3 mm, ke ground pour 0,5 mm).
