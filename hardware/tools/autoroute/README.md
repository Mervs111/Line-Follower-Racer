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
