# Log kerja harian

Catatan apa yang dikerjakan tiap hari di repo (oleh user dan Claude Code), dirangkum dari commit. Bahan untuk
logbook utama (`docs/logbook/logbook-utama.md`); logbook itu tetap hanya diisi kegiatan tim yang benar-benar terjadi.
Entri terbaru di atas.

## 03/11/2026
- Masukan pitching RAB 27/10 (info user): dosen minta **perhitungan ditambah** dan bertanya **kenapa kecepatan robot
  lambat sekali**. Dana belum turun, belum ada barang yang dibeli (status mux di CLAUDE.md dikoreksi jadi "dipilih").
- Skematik PCB utama: 11 catatan teks dihapus user di Eeschema (29/10, disengaja), revisi skematik "A". Komponen,
  footprint, kabel, dan label tidak berubah (dicek per simbol). Handover: urutan mux dibetulkan jadi I2–I13.
- Hitungan awal opsi kecepatan (model kurva torsi-kecepatan N20, 6 V, massa 0,30 kg; belum masuk
  `perhitungan-motor.md`, belum diputuskan): roda lebih kecil justru **lebih lambat** (Ø25 + 500 RPM = 0,65 m/s).
  N20 1000 RPM (rasio 15:1, badan sama) dengan roda Ø34: maksimum 1,78 m/s, kecepatan dasar PID ±1,25 m/s,
  0 → 1,25 m/s dalam 0,31 s / 21 cm, rem 17 cm, torsi rated ±0,09 kg·cm (asumsi, setengah varian 500 RPM).
  Batas tikungan tetap dari traksi (R 10 cm → 0,77 m/s). Data varian 1000 RPM di listing belum dicek (Tokopedia
  timeout).
- Info user: di CNC Store N20 1000 RPM **tidak ada versi encoder** (hanya 2 kabel +/−). Saran: tetap 500 RPM +
  encoder, karena belok 90°, masuk cabang, dan jarak dorong kubus diukur encoder.
- **Guidebook IARC XII Smart Robotics SD** masuk repo (`docs/GUIDEBOOK SD.pdf`). Koreksi: arena **bukan grid**,
  melainkan bentuk tangga/H 4 × 3 m (2 jalur panjang + 3 jalur melintang, simpang T 90°, objek 10/30/50 poin).
  Batas robot 350 g, Li-ion 8,2 V ± 1 V, program onsite Ardublock. CLAUDE.md diperbaiki; charter, deck, naskah, dan
  arena simulasi (grid 4 × 4 jarak 30 cm) masih memakai anggapan grid.
- Motor diputuskan **tetap N20 500 RPM + encoder**. Opsi chip-down (ESP32-WROOM, MX1508, MP1584EN) dibahas, user
  memilih tetap modul.
- **Konsep v17** (`mechanical/konsep-v17/gen_konsep.py` → `konsep-v17.html`, artifact
  https://claude.ai/artifact/3zbiuQzc9YBamEs8NX5sxH): sasis skid plate 3D print, PCB utama 62 × 58 mm (35,8 cm²) +
  board interface 42 × 42 mm (17,6 cm²; OLED di socket + 5 tombol 6×6 + resistor ladder) ditumpuk di depan baterai,
  total −44% dari PCB utama v16 (95,3 cm²). Cek kotak 3D: 0 tabrakan, jalur USB dan zona antena ESP32 kosong.
  Ball caster pindah ke skid plate di belakang PCB sensor (posisi v16 bertabrakan dengan PCB sensor). Menunggu
  konfirmasi user.
- Konsep v17 versi 2 (komentar user di artifact): tombol dipindah ke kiri-kanan OLED (2 kiri, 3 kanan), board
  interface jadi 46 × 32 mm (14,6 cm²), total −47%. Header J6 digeser ke kanan supaya kakinya tidak di bawah
  OLED/tombol; cek otomatis ditambah untuk itu. 0 masalah.
- Konsep v17 versi 3 (komentar user): skid plate belakang melebar sampai sisi luar ban, ban Ø34 × 18 mm melebar ke
  luar (lebar robot 103 → 115 mm, jarak tengah ban 91 → 97 mm). Kecepatan maksimum tidak berubah (RPM × diameter),
  grip naik. Cek Tokopedia: roda N20 Ø34 umumnya 6,5–7 mm; alternatif velg 3D print + ban TPU, atau roda Ø44 × 17,5 mm
  (CNC Store Bandung; maks 1,15 m/s, torsi desain 0,13 kg·cm). Belum diputuskan.
- Konsep v17 versi 4 (komentar user: bentuk sebelumnya jelek): skid plate jadi trapesium, sisi lurus dari hidung 62 mm
  melebar ke belakang sampai sisi luar ban 115 mm, coakan roda celah 4 mm. Cek baru: PCB utama di dalam skid plate
  (jarak tepi ≥ 1,5 mm, nyatanya ±3 mm). Hidung tidak bisa lebih runcing tanpa memutar ESP32 membujur.
- Pertanyaan user: MP1584 22 × 17 mm cocok footprint (masih "UKUR ULANG"; letak lubang dan polaritas diukur saat
  modul datang). TB6612 cukup 1 modul (2 kanal, PWMA GPIO18 kiri, PWMB GPIO16 kanan); diagram blok kendali
  hanya menggambar 1 panah PWM, diusulkan diperbaiki jadi 2 jalur (menunggu jawaban user).
- **Diagram blok kendali diperbaiki** (masukan dosen: 2 roda = 2 PWM): PID → pembagi kecepatan (kiri = dasar + u,
  kanan = dasar − u) → PWM kiri (GPIO18) ke TB6612 kanal A → motor kiri, PWM kanan (GPIO16) ke kanal B → motor kanan;
  encoder kiri (GPIO13, 14) dan kanan (GPIO23, 19) terpisah. Sumber `docs/diagram-blok-src/Kendali.dc.html` (1920 × 900),
  PNG `docs/diagram-blok-kendali.png`, artifact diagram blok versi 5. Deck pitching masih memakai gambar lama.
- Keputusan user: velg 3D print Ø34 × 18 mm, 5 tombol untuk menu OLED (label ▲ ▼ / ◀ OK ▶ di konsep v17 versi 5),
  TB6612 di bawah ESP32 oke.
- Pertanyaan user: PCB utama trapesium mengikuti skid plate (tidak sampai belakang). Ditambahkan panel opsi di konsep
  v17 (belum dipilih): depan 62, belakang 87, panjang 58 mm, 42,9 cm² (+20% dari persegi 35,8), kotak pembungkus
  50,2 cm² (+40%), total dengan interface 57,6 cm² (−40% dari v16). 4 lubang M3 di sayap, cek otomatis 0 masalah.
- User memilih **trapesium** (komentar artifact): konsep v17 versi 7 memakai trapesium sebagai PCB utama, cek komponen
  di dalam outline (≥ 0,5 mm dari tepi). Koreksi: J2/J3 JST XH 6 pin 17,4 mm (sebelumnya tergambar 14,9 mm = 5 pin);
  J5/J6 mundur 0,5 mm dari tepi depan.
- **Skematik PCB utama rev B** (`gen_sch_utama.py --paksa`): J6 socket 1×6 ke board interface (+3V3, GND, SDA, SCL,
  BTN GPIO34, AUX GPIO35), J4 OLED/SW2/SW3/R6 dihapus, R5 jadi pull-up BTN, C2 100 nF di VBAT_SENSE (rekomendasi
  perhitungan), J2/J3 JST XH 6 pin, Q1 TO-92 Wide. Catatan teks blok 2/4/5 tetap tidak ada (dihapus user 29/10).
  ERC 0, 22 pin ESP32 cocok tabel pin, tidak ada net 1 node. PDF diperbarui.
- **Skematik board interface rev A** (proyek baru `hardware/board-interface/`, `gen_sch_interface.py`): J1 header 1×6,
  J2 socket OLED, SW1–SW5 6×6, tangga R 1k/3,9k/8,2k/18k/39k (0,30–2,63 V), C1 100 nF. ERC 0.
- Layout PCB utama belum: MCP KiCad tidak tersambung (2 jendela KiCad terbuka, PCB Editor tidak terbaca API).
- **Footprint MP1584 diperbarui sesuai foto listing CNC Store** (pertanyaan user): dari 4 pad tunggal jadi 8 lubang,
  2 per terminal. Foto diluruskan (homografi dari 4 pojok badan 22 × 17 mm), lubang terukur di x ±9,3–9,6, jarak
  pasangan 2,6–2,9 mm → dipakai 2,54 (header), y ±4,33 / ±6,87. Overlay di foto pas. `gen_kicad.py` ikut diubah.
  Polaritas +/− tetap dicek di sisi bawah modul saat datang (ada tanda ⊕ dekat pasangan kanan bawah di foto).

## 27/10/2026
- Spesifikasi motor dari foto listing (CNC Store Bandung, MTR-0239 500 RPM): rated 300 RPM, 170 mA, torsi rated
  0,2 kg·cm (1,9× kebutuhan 0,10), stall 0,45 kg·cm, rasio 30:1; arus stall tertulis 60 mA (salah ketik, ditanyakan).
  Pada beban rated robot masih 0,53 m/s. Perhitungan + tautan charter diperbarui; teks slide "kenapa N20" disiapkan.
- **Perhitungan rancangan diperbarui** (`docs/perhitungan-motor.md`; draf 08/10 jadi lampiran): kecepatan (0,89 m/s,
  281 RPM untuk 0,5 m/s, duty PWM terkompensasi 6,0/V_bat), torsi (10,2 N·mm ≈ 0,10 kg·cm per roda, SF 2), traksi,
  tikungan, rem (2,8 cm / 0,11 s), anggaran massa (±0,29 kg; luas PCB dari file KiCad), encoder (0,16°/hitungan,
  contoh 7 PPR × 1:30), daya (rel 5 V ±370 mA, total 3,1–4,1 W), baterai (3,3–6,5 jam, cas ±3–3,5 jam), rangkaian
  (pembagi 100k/33k, buzzer S8050, LED 15,7 mA). Temuan: +5 V hanya ±4,65 V karena dioda D1 → usul MP1584 5,35 V;
  usul 100 nF di GPIO39. Spesifikasi motor dari listing belum bisa dibuka (Tokopedia diblokir di container).
- **Naskah bicara pitching** `docs/pitching-rab/naskah-bicara.md`: kalimat per slide (16 slide, ±13 menit, 1.342
  kata), usulan pembagian 4 pembicara per blok (pembuka, produk & sasaran, rancangan teknis & simulasi, RAB, penutup),
  daftar persiapan (peran slide 2, gambar CoppeliaSim di slide 11, video offline), angka wajib hafal, dan 13
  antisipasi pertanyaan dengan jawaban dari charter dan hasil simulasi. Slide 11 dibacakan dengan hasil CoppeliaSim
  (8,3 s / 12,6 mm; rute terpendek 5,7 s / 11,2 mm).
- **RAB diperbarui dari spreadsheet kelompok** `RAB PJBL P01.ods` (harga hasil validasi di marketplace online):
  total **Rp937.390** (Electrical Rp862.390 + Mechanical Rp50.000 + Lain-lain timah + flux Rp25.000), sisa
  Rp62.610 dari Rp1.000.000. Perubahan utama: TB6612FNG Rp50.000, baterai 18650 1 paket isi 2 Rp94.990, ESP32
  Rp65.900, OLED Rp36.500, ball caster menggantikan skid nilon, bracket motor dihapus, timah masuk RAB.
- Dicek terhadap rancangan (tautan Tokopedia dibuka satu per satu): baris mux di spreadsheet ternyata modul kakarobot
  Rp35.000 (chip SSOP), jadi tetap IC CD74HC4067M WKH Rp20.000 (keputusan user). Tautan push button (12×12 mm) dan
  konektor motor (JST XH 2,54) tidak cocok dengan footprint PCB utama; user memilih PCB yang menyesuaikan barang.
- Diperbarui: `docs/charter.md` (tabel RAB + tabel tautan toko), `gen_charter.js` + docx, deck pitching (slide 4, 5,
  12, 13, 14, 16, lampiran A–C, grafik, catatan bicara; diubah langsung di XML .pptx karena generator butuh file
  container cloud) + PDF pratinjau, `build.js`, naskah, README, handover, CLAUDE.md.

## 26/10/2026
- Bahan **pitching RAB** (27/10): analisis progres repo, naskah 14 slide + 2 lampiran RAB
  (`docs/pitching-rab/naskah-slide.md`), render PCB sensor rev B dan PCB utama terbaru dari KiCad 10
  (`docs/pitching-rab/gambar/`; `hardware/render/` masih PCB lama). DRC ulang: PCB sensor 0 error, PCB utama 11 error
  (Q1, SW1), keduanya 0 unconnected.
- **Deck pitching RAB** `docs/pitching-rab/LFM_Pitching_RAB_P01-5.pptx` (15 slide + 3 lampiran RAB, + PDF pratinjau):
  gaya template Canva kelompok (latar diambil dari PDF template, teks/tabel/grafik tetap bisa diedit, font Arial).
  Generator `docs/pitching-rab/generator/build.js` (pptxgenjs). Diagram blok dibetulkan: PCB sensor "bentuk jangkar",
  bukan "gaya XLINE" (`docs/diagram-blok.png` + sumber). Peran anggota di slide 2 masih `[isi peran]`.
- Charter docx dibuat ulang (RAB Rp902.000 sama dengan deck; tanggal persetujuan 27 Oktober 2026).
- **Path planning diganti ke pre-defined map by index** (usulan Bu Fira): peta grid 4 × 4 berindeks 1–16 ditentukan di awal,
  aksi per indeks lewat blok + rute terpendek otomatis (BFS). Diperbarui: `docs/charter.md` + docx (tujuan 3 dan 5,
  lingkup, sasaran 5), deck slide 4, 5, 6, 8 + catatan bicara, naskah, CLAUDE.md.
- Koreksi dari screenshot blok Ichiduino di mBlock (user): indeks = **nomor langkah rute** (pemicu pola sensor → aksi →
  ikuti garis), bukan nomor persimpangan 1–16. Charter + docx, deck slide 4, 5, 8, naskah, CLAUDE.md disesuaikan.
- Charter.md "Yang TIDAK dikerjakan": batas 90° hanya untuk rute terpendek otomatis; rencana per indeks bisa di lintasan lain.
- **Batas RAB naik jadi Rp1.000.000** (info user; charter Word user sudah direvisi): RAB Rp902.000 sekarang sisa Rp98.000.
  Diperbarui: charter.md + docx (deskripsi, latar, tujuan 1, sasaran 9, R6, ringkasan anggaran), deck slide 3, 6, 13
  (grafik batas Rp1 juta, "Sisa Rp98.000") + catatan bicara, naskah, CLAUDE.md, README, pedoman ringkas, handover.
- Mux: toko lokal hanya punya SSOP (celah pad ±0,25 mm, tidak lolos aturan cetak 0,254). Dapat **CD74HC4067M SOP-24
  Rp20.000 di WKH Electronic** (Tokopedia; SOP-24 dikonfirmasi penjual), beli 1 tanpa cadangan. PCB sensor tetap.
  RAB **Rp887.000** (elektrikal Rp832.000), sisa Rp113.000: charter.md + docx, deck slide 4, 5, 11, 13, 15 + lampiran
  (subtotal lampiran A dibetulkan jadi Rp456.000), naskah, CLAUDE.md, README, handover.
- Syarat pitching dari dosen: charter + RAB, desain rangkaian & mekanik, simulasi (seperti CoppeliaSim). Checklist
  dibuat; simulasi belum ada sama sekali.
- **Simulasi** `simulasi/`: logika kendali `lfm_control.py` (PID, deteksi persimpangan, path planning per indeks,
  belok diukur encoder, rute terpendek grid) + uji 2D `test_2d.py` (lulus: rute slide 8,2 s / 9 mm dari T, rute
  terpendek dengan halangan, 0,3–0,7 m/s 25/25; video tampak atas `hasil/uji2d_slide.mp4`). CoppeliaSim:
  `build_scene.py` (arena, robot dinamis ukuran asli, 12 vision sensor, mesh rakitan PCB, 2 kamera) dan
  `run_sim.py` (stepping, video + log, mode kinematik cadangan); dicek terhadap tiruan API, belum di CoppeliaSim
  asli (dijalankan Claude lokal, prompt di `docs/handover-claude-lokal.md` bagian 6).
- Deck: slide baru **11 Simulasi** (sesudah Mekanik; deck jadi 16 slide + 3 lampiran): gambar lintasan uji 2D
  (`simulasi/hasil/uji2d_slide.png`), model CoppeliaSim, hasil uji logika diberi label "simulasi 2D". Gambar dan
  angka diganti tangkapan CoppeliaSim setelah dijalankan di laptop. Naskah dinomori ulang (11–15).
- **Simulasi dijalankan di CoppeliaSim asli** (Edu 4.10, laptop, Claude lokal): `build_scene.py` dan `run_sim.py`
  jalan tanpa perbaikan logika, fisika roda asli (Bullet 2.78, dt 5 ms). Rute slide 8 **LULUS** (8,30 s, 12,6 mm
  dari T), rute terpendek `--blocked 1,0 2,2 1,2` **LULUS** (5,69 s, 11,2 mm; lewat tepi kiri lalu atas, 3 kubus
  terlihat). Perbaikan tampilan saja: kamera video dipindah (robot di S dan T dulu terpotong), kamera perekam
  disembunyikan dari jendela, pandangan jendela diarahkan ke arena. Video `simulasi/hasil/coppeliasim_slide.mp4`,
  `coppeliasim_bfs.mp4`, screenshot jendela `coppeliasim_jendela.png` (+ `_bfs`), scene `coppeliasim/lfm_grid.ttt`.

## 25/10/2026
- Daftar perubahan gambar arsitektur sistem untuk kelompok: sensor 12 QRE1113GR + mux, TB6612FNG, motor N20, buck
  MP1584, tambahan tombol, buzzer, sensor tegangan baterai, charger USB-C, saklar, upload USB-C. Database / Log
  Pengujian dan Wi-Fi/HTTP ke platform Blockly tetap (keputusan user).

## 24/10/2026
- **Rakitan PCB LFM** (`mechanical/rakitan-pcb/`): PCB sensor rev B + PCB utama hasil layout diekspor dari KiCad
  (`kicad-cli pcb export glb`, tembaga/pour/silkscreen/komponen) dan digabung di posisi pasangnya dengan bagian mekanik
  v16. Viewer 3D dengan garis ukuran per tampak, alat ukur dua titik, dan tabel ukuran:
  https://claude.ai/artifact/7JpKSCkUepxGQdxK5ZhVpv. Ukuran robot 165,0 × 115,6 × 62,1 mm, PCB utama 100 × 127,
  PCB sensor 94,4 × 51,0 (masuk 13 mm di bawah hidung). Temuan: kaki THT J1 PCB sensor menonjol 1,7 mm ke bawah
  (titik terendah 3,1 mm dari lantai, di bawah muka QRE 3,3 mm), jadi perlu dipotong serata mungkin.
- STEP rakitan kedua PCB (`mechanical/rakitan-pcb/LFM_rakitan_pcb.step`, `gen_rakitan_step.py`): digabung oleh
  KiCad sendiri, sumbu = STEP v16 (nol di lantai), jadi bisa dibuka bersama bagian mekanik di Fusion 360/FreeCAD.
- Data viewer v16 (`mechanical/viewer/model.json`) disimpan di repo supaya `viewer/v16.html` dan skrip rakitan bisa
  dijalankan di laptop (CadQuery tidak terpasang).

## 23/10/2026
- README ditulis ulang untuk anggota kelompok: status tiap bagian, link artifact, dan daftar pekerjaan
  berikutnya (keputusan kelompok, PCB utama sampai siap pesan, pembelian, firmware, dokumen PjBL).

## 22/10/2026
- MCP KiCad (`hardware/tools/kicad-mcp/`): Claude bisa mengedit PCB live di KiCad 9/10; handover ke Claude Code di laptop.
- PCB sensor buatan user masuk repo (rev A), urutan pin J1 dikoreksi sesuai skematik, lalu **rev B** disetujui:
  bentuk jangkar, 12 QRE1113GR jarak 8 mm di busur, lebar 95 mm, DRC 0.
- Bersih-bersih repo: file usang ke `arsip/`, CLAUDE.md dirapikan, `LineFollowerRacer/` di-gitignore.
- RAB: QRE1113GR lokal Rp15.000 × 12 (tanpa cadangan), kabel pita → JST XH 8 pin. Total **Rp902.000** (lewat Rp2.000).
  Charter docx dibuat ulang (Node.js 24 LTS dipasang di laptop).
- Wiring diagram blok 4 dan 6 disamakan (JST XH 8 pin, mux I2–I13), artifact versi 7.
- Model 3D **v16**: PCB sensor rev B dibaca langsung dari KiCad, kabel JST XH, usulan skid nilon di H1/H2, J5 di tepi
  kanan hidung. https://claude.ai/artifact/C6BMXLgUPLJN5Aubm8uyx3
- Proyek awal **PCB utama** `hardware/pcb-utama/` (outline, lubang, gambar bantu penempatan) + langkah menggambar
  skematik di `hardware/pcb-utama/README.md`.
- **Skematik PCB utama** dibuat Claude (permintaan user) lewat `hardware/tools/gen_sch_utama.py`: 5 blok (daya,
  driver motor, layar/tombol/buzzer, ESP32, kabel J5), 21 komponen, ERC 0, netlist 39 net cocok dengan tabel pin
  CLAUDE.md. PDF `hardware/pcb-utama/pcb-utama-skematik.pdf`.
- **Outline PCB utama baru "mobil F1"** (user memilih dari 3 opsi: perisai bulat, controller, mobil F1): sidepod
  lebar, pinggang lengkung, hidung panjang, 100 × 127 mm. J5 pindah ke sidepod kiri, C1 elko ke (−37; 40), kabel
  sensor menyusuri tepi kiri hidung. Model v16 (0 tabrakan), render, artifact v16, dan `pcb-utama.kicad_pcb`
  (DRC 0) diperbarui.
- MCP KiCad disambungkan ulang (path lama di `C:\Users\revis\Documents` → repo `C:\ITS\Line-Follower-Racer`).
- **Layout PCB utama**: 21 footprint ditempatkan sesuai model v16, routing pertama dengan FreeRouting (skrip di
  `hardware/tools/autoroute/`), GND pour F.Cu + B.Cu. DRC 0 unconnected; tersisa 11 error dari footprint pustaka
  Q1 (TO-92 rapat → ganti `TO-92_Inline_Wide`) dan SW1 (pad pemasang 0,25 mm), menunggu user.

## 21/10/2026
- Aturan cetak PCB dari tempat cetak user (jalur 0,3 mm) + template setting KiCad.
- Outline PCB sensor simetris dari layout user (DXF + gambar ukuran).
- Mux jadi IC CD74HC4067 SOIC-24W disolder langsung.
