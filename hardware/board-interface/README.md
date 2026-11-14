# Board interface (KiCad 10)

Board kecil yang ditumpuk di atas PCB utama: OLED 0,96 inci di socket di tengah, 5 tombol 6×6 sebaris di belakangnya
untuk menu OLED. **PCB rev B (14/11/2026)**: 39 × 45 mm, simetris terhadap garis tengah robot (permintaan user; rev A
46 × 36 mm dengan tombol 2 kiri + 3 kanan ada di riwayat git, commit e038efd).

| File | Isi |
|---|---|
| `board-interface.kicad_pro` | salinan setting PCB utama (aturan cetak, net class) |
| `board-interface.kicad_sch` | skematik rev A dari `hardware/tools/gen_sch_interface.py`, 13 komponen, ERC 0 (tidak berubah di PCB rev B). PDF: `board-interface-skematik.pdf` |
| `board-interface.kicad_pcb` | PCB rev B dari `hardware/tools/gen_pcb_interface.py` + `hardware/tools/autoroute/sisa.py` |
| `render-atas.png`, `render-bawah.png` | render KiCad |

**Tangga resistor**: tombol k menghubungkan BTN (GPIO34) ke GND lewat Rk; pull-up 10k (R5) ada di PCB utama.

| Tombol (kiri → kanan, dilihat dari belakang robot) | Rk | Tegangan BTN |
|---|---|---|
| SW3 Kembali | 8,2k | 1,49 V |
| SW1 Atas | 1k | 0,30 V |
| SW4 OK (tengah) | 18k | 2,12 V |
| SW2 Bawah | 3,9k | 0,93 V |
| SW5 Lanjut | 39k | 2,63 V |
| tidak ditekan | – | 3,3 V |

Hanya satu tombol terbaca dalam satu waktu (cukup untuk menu). C1 100 nF di BTN meredam derau.

## PCB rev B

- **39 × 45 mm** (x robot −19,5..19,5, y 34..79), sudut R2. Tepi kanan 19,5 supaya tembaga (pour berhenti di 19,0) tidak
  masuk zona antena ESP32 (x 19,25..25,75).
- **Tombol** sebaris di y 41,6, jarak 7,62 mm (x −15,24 … 15,24): KEMBALI, ATAS, OK, BAWAH, LANJUT. Nama tombol di
  silkscreen tepi belakang. **OLED** di tengah (x 0, y 61; modul 27,3 × 27,8 mm), socket J2 di y 73,65.
- **Tangga resistor** di bawah OLED: kiri R3, R1, R4; kanan R5, R2, C1.
- **J1 di sisi bawah**, pin 1–6 di x −5,6 … 7,1, y 67,5, **sama persis dengan J6 PCB utama** (dicek dari kedua file
  `.kicad_pcb`; urutan +3V3, GND, SDA, SCL, BTN, AUX tidak dipakai).
- **8 lubang M2**:
  - H1–H4 di (±17; 62) dan (±17; 76,5): ke boss **rangka interface** (3D print, lihat `mechanical/konsep-v18/`). Letaknya
    di depan ESP32 supaya boss di bawahnya bisa 5 mm. Tepi belakang papan (y 34..36,5) bertumpu di balok rangka, jadi
    tekanan jari di tombol tidak mengungkit header. **Jangan taruh kaki komponen di y < 37.**
  - H5–H8 di (±11,75; 49) dan (±11,75; 72,8): spacer M2 modul OLED. Jarak 23,5 × 23,8 mm diambil dari gambar umum modul
    0,96 inci, **belum diukur dari modul asli: ukur dulu sebelum PCB dicetak.**
- Routing 2 layer tanpa via, GND pour F.Cu + B.Cu. DRC (`kicad-cli pcb drc --schematic-parity`): **0 error, 0 warning,
  0 unconnected, cocok dengan skematik**. Aturan tambahan `board-interface.kicad_dru`: courtyard tombol 6×6 dan lubang M2
  boleh bersinggungan.

## Tinggi dan header ke PCB utama

Di model v18, sisi bawah board interface ada di **z 36,1 mm** (rev A: 33). Model lama lupa plastik header pin 2,54 mm di
antara socket dan ESP32 DevKit: puncak kaleng modul ESP32 sebenarnya ±32,3 mm, bukan 29,8, sehingga kaki solder tombol
(±2 mm di bawah papan) akan menyentuhnya pada z 33. Jarak atas PCB utama → bawah board interface jadi 19,5 mm =
socket J6 8,5 + **header susun (stackable) 1×6** 8,5 + plastik header J1 2,54. Pilihan lain: satu header pin panjang
±19 mm. Belum diputuskan user; ukur tinggi ESP32 di socket begitu barangnya ada.

## Buat ulang (sesudah skematik atau penempatan berubah)

```bash
KPY="/c/Program Files/KiCad/10.0/bin/python.exe"; K="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"; I=hardware/board-interface
"$K" sch export netlist -o if.net $I/board-interface.kicad_sch
"$KPY" hardware/tools/gen_pcb_interface.py if.net hardware/pcb-utama/pcb-utama.kicad_pcb $I/board-interface.kicad_pcb
"$K" pcb drc --severity-all --format json -o drc.json $I/board-interface.kicad_pcb
"$KPY" hardware/tools/autoroute/sisa.py $I/board-interface.kicad_pcb drc.json GND   # "tersambung 24 dari 31": 7 sisanya GND
"$KPY" hardware/tools/gen_pcb_interface.py pour $I/board-interface.kicad_pcb      # GND tersambung lewat pour
"$K" pcb drc --severity-all --schematic-parity --format json -o drc.json $I/board-interface.kicad_pcb
```

Sesudah itu jalankan `py mechanical/konsep-v18/gen_konsep.py` (render di halaman konsep diambil dari `render-atas.png`),
dan samakan angka `IB`, `BTN`, `IB_HOLE`, `OLED_HOLE` di skrip itu kalau penempatan berubah.
