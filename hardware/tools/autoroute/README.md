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

## LFM X2 keempat papan (16/11/2026): router sendiri, tanpa FreeRouting
FreeRouting 2.1.0 tidak bisa dipakai di papan ini: batas pass (`-mp`, setelan, env) diabaikan dan file SES tidak
pernah ditulis. Pengganti: `x2_router.py` (python KiCad, baca/tulis papan) + `x2_cari.py` (python sistem: numpy, scipy,
scikit-image; pencari jalur grid 0,1 mm dua layer, cara PathFinder). Jarak ke net lain minimal 0,3 mm, diutamakan
0,4 mm; lebar VBAT/BAT+ dan keluaran motor (ML_P/N, MR_P/N) 1,0, BUCK_SW 0,8, +5V/VBUS 0,6, +3V3/GND 0,5, sinyal
0,3 mm. Dipakai untuk keempat papan X2 (utama, antarmuka, driver, sensor); langkah 1 (fanout USB-C) hanya utama.

```bash
T=hardware/tools/autoroute; W=<folder kerja berisi salinan proyek utama/>; B=$W/utama/lfm-x2-utama.kicad_pcb
KPY="C:/Program Files/KiCad/10.0/bin/python.exe"; K="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"

C="PRES_NAIK=1.25 RIWAYAT=1.5 BIAYA_B=1.2 VIA_COST=2.0"        # setelan yang konvergen di papan utama

"$KPY" $T/x2_router.py fanout $B                        # 1. fanout USB-C J2 (pola tetap, 2 via VBUS)
"$KPY" $T/x2_router.py pasang $B $T/x2_vbat_utama.json  # 1b. VBAT tetap lewat tepi belakang (16/11)
"$KPY" $T/x2_router.py pasang $B $T/x2_fanout_utama.json  # 1c. jalur tetap: fanout deret kanan ESP32, lajur MUX ke J3,
                                                        #     GND USB-C/R CC/CH340C (dibuat x2_fanout_utama.py)
"$K" pcb drc --format json --severity-all -o $W/drc.json $B
"$KPY" $T/x2_router.py ekspor $B $W/drc.json $W/eks.json GND --ganti $T/x2_sambungan_utama.json
                                                        # 2. pad, jalur, rule area, sambungan sinyal (tanpa GND);
                                                        #    --ganti hanya untuk papan utama
py -I -X utf8 $T/x2_cari.py $W/eks.json $W/jalur.json 40 $C    # 3. PathFinder; hasil terbaik ditulis tiap iterasi
py -I -X utf8 $T/x2_cari.py perbaiki $W/eks.json $W/jalur.json $W/jalur2.json   # 3b. kalau macet di beberapa tabrakan
"$KPY" $T/x2_router.py pasang $B $W/jalur2.json        # 4. pasang jalur + via
"$KPY" $T/x2_router.py pour $B                          # 5. GND pour dua sisi (SMD menempel penuh, THT thermal)
"$KPY" $T/x2_router.py jahit $B                         # 6. via jahit yang menyatukan pulau pour F/B
# 7. GND yang masih terpisah: kelompok tembaga GND -> sambungan ke titik dalam pour utama (>= 1 mm dari tepinya)
"$KPY" $T/x2_router.py gnd $B $W/gnd.json 1.0
# 7a. coba dulu sambungan GND saja, jalur lain dikunci; kalau 0 tabrakan langsung pasang ke $B, lalu pour + jahit
py -I -X utf8 $T/x2_cari.py $W/gnd.json $W/gndjalur.json 10 PRES_NAIK=1.25 RIWAYAT=1.5 BIAYA_B=1.0 VIA_COST=1.0
# 7b. kalau 7a menabrak: net sinyal di sekitar pad kelompok itu dibongkar dan dicari ulang bersama sambungan GND
py -I -X utf8 $T/x2_cari.py bongkar $W/eks.json $W/jalur2.json $W/jalur3.json 3 30 --gnd $W/gnd.json $C
# 8. jalur3 dipasang ke salinan papan hasil langkah 1 (pasang, pour, jahit); ulangi 7 sampai `gnd` melaporkan
#    1 kelompok, lalu DRC. Papan tanpa fanout: salinan bersih = `gen_pcb_x2.py tata <papan> --paksa`.
#    Satu persilangan yang tersisa: `bongkar ... <radius> 30 x,y` membongkar net di sekitar titik x,y
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
  yang berjarak < 1,0 mm (dulu 0,65: di papan sensor tersisa 2 via berjarak 0,7 mm, peringatan hole_to_hole).
- Jalur SMD → pour: pad SMD menempel penuh, karena jari thermal sering terpotong jalur (starved thermal).

Catatan dari routing ulang 16/11 sore (ESP32 di tengah, 4 papan):
- Antarmuka bersih di iterasi pertama, sensor di iterasi ke-10; driver macet di 4 tabrakan sesudah 40 iterasi.
- GND driver: `bongkar` berulang malah bolak-balik (tiap putaran menyambung satu pulau dan memutus pulau lain di
  sekitar J1; radius 7 mm memutus 2 sinyal). Merutekan sambungan GND saja dengan jalur lain dikunci (langkah 7a)
  langsung 0 tabrakan: 5 segmen + 3 via, GND 1 kelompok.
- Lebar per net bisa diubah tanpa menyunting skrip: `LEBAR_VBAT=0.6` dst. di baris perintah `x2_cari.py`.
- Papan utama dengan ESP32 di tengah (16/11 malam): router mentok di 21-25 tabrakan selama deret kanan ESP32 dibiarkan
  bebas. Via 1,3 mm tidak muat sejajar pada jarak kaki 1,27 mm, dan jalur dari deret kanan pergi ke tiga arah (EN/BTN/
  BTN2/BUZ/+3V3 ke kiri, MUX ke depan, VBAT_SENSE ke kanan), jadi urutan keluarnya harus ditetapkan dulu.
  `x2_fanout_utama.json`: via kaki 2-7 dan 12 berselang dua kolom (x robot 10,45 / 11,45, jalur kolom B lewat sela
  via kolom A), 4 MUX_S di sisi bawah dalam lajur x 12,6-14,4 sampai J3, MUX_SIG di sisi atas (belok di y 64,6,
  jadi +3V3 dan EN bisa lewat depan daerah antena). Komponen yang dulu di lajur itu (pasif 3V3/EN, buck) dipindah di
  `gen_pcb_x2.py`.
- Sesudah fanout tetap (17/11): router "2 tabrakan" ternyata juga meninggalkan 3 sambungan **tidak sampai** (EN, BTN2):
  DRC melaporkan pad deret kanan ESP32 sebagai ujung, padahal pad itu terkurung dan via 1,3 mm baru dari router tidak
  muat di sebelah via fanout. `ekspor` sekarang memakai pulau jalur tetap (stub + via) sebagai ujung kalau pad sudah
  punya jalur dari net yang sama. Baca kolom "tidak sampai" di log, bukan hanya jumlah tabrakan.
- Dua sambungan ratsnest papan utama pasti bersilang (bukan soal biaya): +3V3 C11 → kaki 2 dan EN kaki 3 → Q2
  auto-reset. Keduanya berangkat dari kantong kaki 2/3 (terkurung MUX_SIG/MUX_S) lalu harus memotong berkas BTN/BTN2/
  BUZ/ESP_TX/ESP_RX. `x2_sambungan_utama.json` (`ekspor --ganti`) menggantinya dengan C11 → J5.10 dan C12 → Q2;
  kelompok tembaganya tetap tersambung lewat sambungan lain.
- +5V_BUCK (buck → D2) pasti memotong VBAT_SENSE (kaki 5 → pembagi): C11 dipindah ke belakang U2 supaya lajur sisi
  bawah x 14,9-17,2 kosong untuk +5V_BUCK, dan R3 diputar supaya ketiga pad VBAT_SENSE sebaris.
- Papan utama dengan larangan antena sampai badan J3 macet di ±50 tabrakan: lubang H5/H6 (±11; 67) + larangan
  antena menutup semua jalan dari J3. Gambar ratsnest dari `eks.json` membantu mencari leher botol seperti ini.
  Jalan keluarnya mengubah tata letak (ESP32 mundur 3 mm, larangan hanya sampai 0,8 mm di depan modul), bukan
  menambah iterasi.
- Router membawa VBAT (1,0 mm) dari kapasitor buck ke J5 lewat depan ESP32, menutup lorong MUX. Jalur tetap
  `x2_vbat_utama.json` (drain Q1 → tepi belakang → J5) dipasang sebelum ekspor, jadi VBAT tinggal disambung dari Q1 ke
  buck/pembagi di kanan.
- Lajur di samping deret pin ESP32 harus kosong di KEDUA sisi: pasif di sisi atas (walau pad-nya hanya di atas)
  menutup tempat via.

Catatan dari GND papan utama (17/11):
- Router tidak melihat pour. Tiap kali `bongkar` memindah jalur sinyal, pour berubah dan pad GND yang tadinya
  tersambung lewat pour bisa lepas (pulau baru di tempat lain). Contoh: VBUS dipindah ke sisi atas di kiri pad A1
  USB-C, pad A1/B12 lepas; jalur GND baru yang menyambung satu pulau malah memaksa VBUS memutar dan mengurung pad GND
  R10. Mengejar pulau satu per satu dengan `bongkar --gnd` bolak-balik.
- Yang berhasil: pad GND di titik sempit diberi **jalur tetap** ke titik GND yang pasti (kaki THT, via ke pour lebar),
  lalu tata letak disesuaikan supaya jalur itu pendek: pad GND USB-C → kaki SH, R10/R11 tegak dengan pad GND ke kaki
  SH, kaki 1 CH340C lewat via di jalur GND R10, C14 diputar (GND langsung ke kaki 1 ESP32), kaki GND XT30 jalur 1,0 mm
  ke pour tepi belakang (`x2_vbat_utama.json`). Sesudah itu `bongkar` biasa di sekitar perubahan, GND 1 kelompok.
- `bongkar` mengunci semua jalur GND. Jalur GND hasil `--gnd` sebelumnya yang jadi tembok harus dibuang dari JSON hasil
  dulu (beserta pulau GND-nya dihitung ulang) sebelum `bongkar` berikutnya.
- `pasang` memasang daftar `tracks`/`vias` di tingkat atas JSON hasil, bukan `rute`; kalau menggabung hasil dua
  percobaan, susun ulang kedua daftar itu dari `rute`. Rute bertabrakan tidak masuk `tracks`.
- Pad THT GND yang dikelilingi jalur (J3/J4/J1) cukup 1 jari thermal (aturan `thermal_satu_jari`), GND-nya sampai
  lewat jalur atau sisi lain.

`dsnfix_x2.py` = pengubah DSN untuk percobaan FreeRouting yang gagal, disimpan sebagai catatan.
