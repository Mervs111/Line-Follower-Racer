# Arsip

File yang sudah digantikan rancangan terbaru, dipindahkan ke sini 22/10/2026 supaya folder utama hanya berisi
yang masih dipakai. Susunan folder sama dengan aslinya (`arsip/hardware/...` = dulu `hardware/...`). Riwayat
lengkap tetap ada di git.

| Isi | Digantikan oleh |
|---|---|
| `hardware/ltm-sensor/`, `hardware/ltm-sensor.pdf`, `hardware/render/pcb-sensor-atas-bawah.png`: PCB sensor v2 hasil generator (16 ITR20001 + mux modul + MCP23017, kabel pita) | `hardware/sensor-garis/` (12 QRE1113GR + CD74HC4067, buatan user) |
| `mechanical/LTM_v11.step`, `LTM_v12.step`, `v13/`, `v14/`, `cadquery/ltm_v11–14.py`, `viewer/v13–14.html`, `render/ltm-v11–14-*.png` | mekanik v15 di `mechanical/` |
| `mechanical/konsep-ringkas.png`, `mechanical/fusion360/`: konsep ringkas tanpa leher (sebelum v10) | v10 dan seterusnya |

Penjelasan tiap versi mekanik: `mechanical/README.md` di folder ini. Proyek KiCad `ltm-sensor` tetap bisa dibuka
(library `ltm` dirujuk ke `hardware/ltm-lib/`).
