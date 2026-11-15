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

## LFM X2 papan utama (16/11/2026): router sendiri, tanpa FreeRouting
FreeRouting 2.1.0 tidak bisa dipakai di papan ini: batas pass (`-mp`, setelan, env) diabaikan dan file SES tidak
pernah ditulis. Pengganti: `x2_router.py` (python KiCad, baca/tulis papan) + `x2_cari.py` (python sistem: numpy, scipy,
scikit-image; pencari jalur grid 0,1 mm dua layer, cara PathFinder). Jarak ke net lain minimal 0,3 mm, diutamakan
0,4 mm; lebar VBAT/BAT+ 1,0, BUCK_SW 0,8, +5V/VBUS 0,6, +3V3/GND 0,5, sinyal 0,3 mm.

```bash
T=hardware/tools/autoroute; W=<folder kerja berisi salinan proyek utama/>; B=$W/utama/lfm-x2-utama.kicad_pcb
KPY="C:/Program Files/KiCad/10.0/bin/python.exe"; K="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"

C="PRES_NAIK=1.25 RIWAYAT=1.5 BIAYA_B=1.2 VIA_COST=2.0"        # setelan yang konvergen di papan utama

"$KPY" $T/x2_router.py fanout $B                        # 1. fanout USB-C J2 (pola tetap, 2 via VBUS)
"$K" pcb drc --format json --severity-all -o $W/drc.json $B
"$KPY" $T/x2_router.py ekspor $B $W/drc.json $W/eks.json GND   # 2. pad, jalur, rule area, sambungan sinyal (tanpa GND)
py -I -X utf8 $T/x2_cari.py $W/eks.json $W/jalur.json 40 $C    # 3. PathFinder; hasil terbaik ditulis tiap iterasi
py -I -X utf8 $T/x2_cari.py perbaiki $W/eks.json $W/jalur.json $W/jalur2.json   # 3b. kalau macet di beberapa tabrakan
"$KPY" $T/x2_router.py pasang $B $W/jalur2.json        # 4. pasang jalur + via
"$KPY" $T/x2_router.py pour $B                          # 5. GND pour dua sisi (SMD menempel penuh, THT thermal)
"$KPY" $T/x2_router.py jahit $B                         # 6. via jahit yang menyatukan pulau pour F/B
# 7. GND yang masih terpisah: kelompok tembaga GND -> sambungan ke titik dalam pour utama (>= 1 mm dari tepinya),
#    net sinyal di sekitar pad kelompok itu dibongkar seluruhnya dan dicari ulang bersama sambungan GND
"$KPY" $T/x2_router.py gnd $B $W/gnd.json 1.0
py -I -X utf8 $T/x2_cari.py bongkar $W/eks.json $W/jalur2.json $W/jalur3.json 3 30 --gnd $W/gnd.json $C
# 8. jalur3 dipasang ke salinan papan hasil langkah 1 (pasang, pour, jahit); ulangi 7 sampai `gnd` melaporkan
#    1 kelompok, lalu DRC. Satu persilangan yang tersisa: `bongkar ... <radius> 30 x,y` membongkar net di sekitar titik x,y
```
Satu iterasi ±45 s (91 sambungan sinyal); bongkar lokal 2–10 s per iterasi. Fanout J2: D+ disambung di belakang pad
(di bawah badan konektor), D− dengan bentuk C di depan ujung A6, VBUS lewat 2 via; celah 0,2–0,25 mm hanya ±0,6 mm
dari ujung pad (aturan peringatan `usb_c_fanout_0,2` di `.kicad_dru`).

Catatan dari routing 16/11:
- Setelan bawaan (`PRES_NAIK` 1,7) macet di 2–6 tabrakan; kenaikan biaya yang lebih pelan + riwayat lebih besar
  (`$C`) bersih di iterasi ±21. Sisi bawah tidak perlu semahal 1,5x.
- GND lewat pour saja membuat pour terpecah jadi belasan pulau (papan padat, dua sisi penuh jalur). `jahit` hanya
  memasang via yang benar-benar menyatukan dua kelompok; sisanya disambung jalur 0,5 mm lewat `gnd` + `bongkar`.
  Ujung sambungan GND di pad kelompok terpisah saja (pulau pour-nya berubah sesudah routing) dan titik pour utama
  yang jauh dari tepi (titik dekat tepi bisa ikut terputus sesudah pour diisi ulang).
- `pasang` tidak memasang via yang jatuh di dalam pad THT satu net (lubang bertumpuk) dan menggabung via satu net
  yang berjarak < 0,65 mm.
- Jalur SMD → pour: pad SMD menempel penuh, karena jari thermal sering terpotong jalur (starved thermal).

`dsnfix_x2.py` = pengubah DSN untuk percobaan FreeRouting yang gagal, disimpan sebagai catatan.
