# Board interface (KiCad 10)

Board kecil yang ditumpuk di atas PCB utama (konsep v17, 03/11/2026): OLED 0,96 inci di socket di tengah, 5 tombol
6×6 mengapit untuk menu OLED (kiri: atas, bawah; kanan: kembali, OK, lanjut). Ukuran konsep 46 × 32 mm.

| File | Isi |
|---|---|
| `board-interface.kicad_pro` | salinan setting PCB utama (aturan cetak, net class) |
| `board-interface.kicad_sch` | skematik rev A dari `hardware/tools/gen_sch_interface.py`, 13 komponen, ERC 0. PDF: `board-interface-skematik.pdf` |

**Tangga resistor**: tombol k menghubungkan BTN (GPIO34) ke GND lewat Rk; pull-up 10k (R5) ada di PCB utama.

| Tombol | Rk | Tegangan BTN |
|---|---|---|
| SW1 Atas | 1k | 0,30 V |
| SW2 Bawah | 3,9k | 0,93 V |
| SW3 Kembali | 8,2k | 1,49 V |
| SW4 OK | 18k | 2,12 V |
| SW5 Lanjut | 39k | 2,63 V |
| tidak ditekan | – | 3,3 V |

Hanya satu tombol terbaca dalam satu waktu (cukup untuk menu). C1 100 nF di BTN meredam derau.

**J1** = header 1×6 (urutan sama dengan J6 PCB utama: +3V3, GND, SDA, SCL, BTN, AUX tidak dipakai). Jarak antar board
±16 mm (atas PCB utama z 16,6 → bawah board interface z 33), jadi perlu header pin panjang atau spacer; cara pasang
board ini (dudukan) **belum diputuskan**. PCB (outline + layout) belum dibuat.
