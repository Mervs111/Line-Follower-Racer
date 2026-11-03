# Board interface (KiCad 10)

Board kecil yang ditumpuk di atas PCB utama (konsep v17, 03/11/2026): OLED 0,96 inci di socket di tengah, 5 tombol
6×6 mengapit untuk menu OLED (kiri: atas, bawah; kanan: kembali, OK, lanjut). Ukuran konsep 46 × 32 mm, PCB jadi 46 × 36 mm (ditambah lubang M2).

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
±16 mm (atas PCB utama z 16,6 → bawah board interface z 33). Socket J6 8,5 mm + header biasa (6 mm masuk) tidak
sampai, jadi perlu **header pin panjang** atau spacer. Cara pasang board ini (dudukan) **belum diputuskan**.

## PCB rev A (04/11/2026)

Dibuat oleh `hardware/tools/gen_pcb_interface.py` (penempatan, silkscreen, pour) + `hardware/tools/autoroute/sisa.py`
(routing, GND lewat pour). Render: `render-atas.png`, `render-bawah.png`.

- **46 × 36 mm** (x robot −27..19, y 43..79), sudut R2, **4 lubang M2** di pojok (x −24,5 / 16,5, y 45,5 / 76,5),
  untuk dudukan apa pun yang dipilih nanti (jembatan 3D print ke lubang M3 PCB utama, spacer, atau cover).
- OLED di socket J2 (tengah atas; modulnya 27,3 × 27,8 mm menutupi tangga resistor). Tombol: kiri ATAS/BAWAH, kanan
  KEMBALI/OK/LANJUT. R1/R2 di kiri, R3–R5 di kanan, dekat tombolnya.
- **J1 dipasang di sisi bawah** (menghadap PCB utama). Pin 1–6 di x −5,6 … 7,1, y 67,5, **sama persis dengan J6 PCB
  utama** (dicek dari kedua file .kicad_pcb).
- Routing 2 layer tanpa via, GND pour F.Cu + B.Cu. DRC: **0 error, 0 warning, 0 unconnected, cocok dengan
  skematik**. Aturan tambahan `board-interface.kicad_dru`: courtyard tombol 6×6 dan lubang M2 boleh bersinggungan
  (badan tombol berjarak 3 mm, tembaga ke lubang ≥ 1,1 mm).

Buat ulang (sesudah skematik berubah):

```bash
KPY="/c/Program Files/KiCad/10.0/bin/python.exe"; K="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"; I=hardware/board-interface
"$K" sch export netlist -o if.net $I/board-interface.kicad_sch
"$KPY" hardware/tools/gen_pcb_interface.py if.net hardware/pcb-utama/pcb-utama.kicad_pcb $I/board-interface.kicad_pcb
"$K" pcb drc --severity-all --format json -o drc.json $I/board-interface.kicad_pcb
"$KPY" hardware/tools/autoroute/sisa.py $I/board-interface.kicad_pcb drc.json GND   # ulangi sampai 0 (selain GND)
"$KPY" hardware/tools/gen_pcb_interface.py pour $I/board-interface.kicad_pcb
```
