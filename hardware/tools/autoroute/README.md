# Autoroute PCB utama (FreeRouting)

Dipakai 22/10/2026 untuk routing pertama `hardware/pcb-utama/`. Board yang sedang terbuka di KiCad tidak
disimpan; skrip bekerja di salinan lalu memasang hasilnya ke board live dalam satu langkah undo (Ctrl+Z).

Syarat: KiCad 10 dengan API aktif (lihat `../kicad-mcp/README.md`), `py -m pip install kicad-python`, plugin
**Freerouting** dari Plugin and Content Manager KiCad (jar `freerouting-2.1.0.jar` + JRE 21 yang diunduh plugin).

```bash
T=hardware/tools/autoroute; W=<folder kerja sementara>
KPY="/c/Program Files/KiCad/10.0/bin/python.exe"                       # python KiCad (modul pcbnew)
JAVA=$LOCALAPPDATA/Temp/freerouting/jre/jdk-21.0.12.1+1-jre/bin/java.exe
JAR="$USERPROFILE/OneDrive/Documents/KiCad/10.0/3rdparty/plugins/app_freerouting_kicad-plugin/jar/freerouting-2.1.0.jar"

py $T/snap.py $W/snap/pcb-utama.kicad_pcb              # 1. salinan board live
"$KPY" $T/kpy.py dsn $W/snap/pcb-utama.kicad_pcb $W/pcb.dsn   # 2. ekspor DSN
py $T/dsnfix.py $W/pcb.dsn $W/pcb2.dsn                 # 3. lebar jalur per net + keepout lubang/celah
"$JAVA" -jar "$JAR" -de $W/pcb2.dsn -do $W/pcb2.ses -mp 40 --gui.enabled=false   # 4. FreeRouting
"$KPY" $T/kpy.py ses $W/snap/pcb-utama.kicad_pcb $W/pcb2.ses $W/fr.json          # 5. SES -> JSON
py $T/route.py $W/fr.json hapus                        # 6. pasang ke board live (hapus jalur lama dulu)
py $T/zones.py                                         # 7. GND pour F.Cu + B.Cu (sekali saja)
```

Lalu cek DRC (MCP `run_drc` atau `kicad-cli pcb drc`). `pads.py <out.json>` mencetak posisi semua pad
(koordinat KiCad dan robot) untuk merencanakan penempatan.

| Kelas (dsnfix.py) | Lebar | Net |
|---|---|---|
| BIG | 1,0 mm | VBAT, BAT+ |
| MOTOR5V | 0,8 mm | ML_P/N, MR_P/N, +5V, +5V_BUCK |
| PWR | 0,5 mm | +3V3, GND |
| SIG | 0,3 mm | sisanya |

Keepout lubang M3 diperbesar jadi Ø4,4 mm dan celah encoder +0,3 mm per sisi, supaya jarak tembaga ke tepi
lubang ≥ 0,5 mm (aturan tempat cetak). Clearance antar net 0,3 mm.

## Rev B (03–04/11/2026): dari file, tanpa board live

PCB utama rev B dibuat tanpa MCP (PCB Editor tidak terbaca API). Semua langkah bekerja di file:

```bash
W=<folder kerja sementara, isi: salinan .kicad_pro, .kicad_dru, .kicad_sch, fp-lib-table, sym-lib-table>
KPY="/c/Program Files/KiCad/10.0/bin/python.exe"; K="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
JAVA=<java 21 apa saja, mis. $LOCALAPPDATA/Programs/STM32CubeMX/jre/bin/java.exe>

"$K" sch export netlist -o $W/utama.net hardware/pcb-utama/pcb-utama.kicad_sch
git show <commit>:hardware/pcb-utama/pcb-utama.kicad_pcb > $W/pcb-utama.kicad_pcb   # dasar (setup saja yang dipakai)
"$KPY" hardware/tools/gen_pcb_utama_v17.py tata $W/utama.net $W/pcb-utama.kicad_pcb
"$KPY" $T/kpy.py dsn $W/pcb-utama.kicad_pcb $W/pcb.dsn && py $T/dsnfix.py $W/pcb.dsn $W/pcb2.dsn
"$JAVA" -jar "$JAR" -de $W/pcb2.dsn -do $W/pcb2.ses -mp 8 --gui.enabled=false
grep -c "(net " $W/pcb2.ses                          # harus 34 (net dengan 2 pad atau lebih)
"$KPY" hardware/tools/gen_pcb_utama_v17.py ses $W/pcb-utama.kicad_pcb $W/pcb2.ses
"$K" pcb drc --severity-all --schematic-parity --format json -o <drc.json> $W/pcb-utama.kicad_pcb
```

Catatan:
- **JRE plugin hilang**: JRE yang diunduh plugin ada di `%LOCALAPPDATA%\Temp`, jadi ikut terhapus kalau Temp
  dibersihkan. Java 21 lain bisa dipakai. Jangan jalankan java lewat `timeout` msys (gagal memuat DLL), dan jangan
  pakai `--help` (malah membuka GUI).
- **Bug FreeRouting 2.1**: di akhir run, log bisa menulis "Restoring an earlier board that has the score of ...", lalu
  SES berisi board lama yang **kurang 1–4 net**, walau statistiknya bilang lengkap. Cek jumlah `(net ` di SES. Untuk
  rev B, `-mp 8` lengkap (34 net, 17 via); `-mp` 12–30 kurang 1–3 net.
- `ses` memanggil `rapikan()`: membuang segmen kembar, segmen yang menumpuk di segmen lain, dan ujung menggantung
  sisa FreeRouting, lalu membuat GND pour (tebal minimum 0,35; dengan 0,3 tersisa leher pour 0,13 mm).
- **`sisa.py`**: router grid A* dua layer untuk net yang masih putus menurut laporan DRC (JSON kicad-cli). Hasilnya
  rapi untuk papan kecil (board interface di-route penuh dengan ini, GND lewat pour: `sisa.py <board> <drc.json> GND`),
  tapi di PCB utama yang padat jalurnya memutar jauh. Hapus pour dulu (`gen_pcb_utama_v17.py tanpa-pour`).
- Hasil rev B (DSN yang sudah lewat dsnfix + SES) disimpan di `hardware/pcb-utama/routing/`.
