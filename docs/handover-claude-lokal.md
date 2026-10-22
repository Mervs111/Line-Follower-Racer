# Handover: dari sesi Claude Code cloud ke Claude Code di laptop (22/10/2026)

Dokumen ini untuk Claude Code yang jalan di laptop user. `CLAUDE.md` tetap sumber utama keputusan proyek
(terbaca otomatis). Di sini hanya ada: cara setup, apa yang sedang dikerjakan, pekerjaan yang tertunda, dan
jebakan yang sudah ketemu.

## 1. Setup laptop (dikerjakan user, sekali)

Asumsi: Windows. Perintah macOS/Linux ada di `hardware/tools/kicad-mcp/README.md`.

1. Pasang **Git for Windows** (git-scm.com) dan **Python 3.10+** (python.org; centang "Add python.exe to PATH").
2. Pasang **Claude Code**: buka PowerShell, jalankan `irm https://claude.ai/install.ps1 | iex`. Tutup PowerShell,
   buka lagi, cek `claude --version`.
3. Ambil repo: `git clone https://github.com/Mervs111/Line-Follower-Racer.git` (login GitHub lewat browser kalau
   diminta). Kalau sudah pernah clone: `git pull` di folder repo.
4. **KiCad 9 atau 10** (KiCad 8 harus di-update). Preferences → Preferences → Plugins → centang **Enable KiCad
   API** → tutup dan buka ulang KiCad.
5. Di folder repo: `py -m pip install -r hardware\tools\kicad-mcp\requirements.txt`
6. Daftarkan MCP: `claude mcp add kicad --scope user -- py "<path lengkap repo>\hardware\tools\kicad-mcp\kicad_mcp.py"`
7. Buka board PCB sensor di KiCad PCB Editor. Di folder repo jalankan `claude` (pertama kali: login lewat
   browser), ketik `/mcp` (kicad harus *connected*), lalu kirim pesan pembuka:
   > Baca docs/handover-claude-lokal.md, lalu cek status kicad.
8. Opsional: `claude remote-control` (di folder repo) supaya sesi bisa dipantau dari aplikasi Claude di HP.

## 2. Status pekerjaan saat pindah

User sedang **menggambar PCB sensor sendiri di KiCad** (skematik dan layout buatan user, BUKAN
`arsip/hardware/ltm-sensor/`, yang masih hasil generator lama dengan 16 ITR20001 + MCP23017). File proyek KiCad user
**belum ada di repo**: tanya lokasinya, usulkan dimasukkan ke repo (nama folder biar user yang pilih) supaya
tersimpan di git.

Isi PCB sensor user (sesuai keputusan 20–21/10 di `CLAUDE.md`):

- 12× **QRE1113GR** (simbol: 1 A, 2 K, 3 C, 4 E). Tiap sensor: A ← R 220 Ω ← +5V, K → GND, C ← R 10k ← +3V3,
  C → label `S1`…`S12`, E → GND.
- **U13 CD74HC4067M** SOIC-24W (`Package_SO:SOIC-24W_7.5x15.4mm_P1.27mm`): I0–I11 = S1–S12, I12–I15 ke GND,
  COM → `MUX_SIG`, select → `MUX_S0`…`MUX_S3` (jangan dinamai `S0`–`S3`, bentrok dengan label sensor), E̅ → GND,
  VCC +3V3 + C 100 nF.
- **J1 = JST XH 8 pin** (pitch 2,50 mm, footprint vertikal B8B-XH-A; origin footprint = pin 1). Urutan pin yang
  di skematik user (dikoreksi 22/10): 1 +5V, 2 +3V3, 3 GND, 4 MUX_S3, 5 MUX_S2, 6 MUX_S1, 7 MUX_S0, 8 MUX_SIG. **Konektor pasangannya
  di PCB utama (J5) wajib urutan yang sama.**
- **Outline simetris** (dibuat 21/10 dari layout user): `hardware/outline/README.md` + DXF. Titik (0,0) = puncak
  tepi depan, Y ke bawah. Sayap ±60 mm (tepi depan naik 5,5 mm), badan ±15 sampai Y 34,5, tab ±9 sampai Y 46,
  lubang (±5; 40), U13 dan J1 di garis tengah.
- Aturan cetak: jalur min 0,3 mm, clearance 0,254, ke pour 0,5, via 0,6/1,0. Template impor
  `hardware/aturan-cetak-template/`, penjelasan `docs/aturan-cetak-pcb.md`. Silkscreen min 0,2 mm.

Langkah berikutnya yang paling mungkin diminta: **menaruh 12 sensor + resistornya di sepanjang tepi depan
outline**, simetris kiri-kanan, lalu U13, J1, C, routing.

## 3. Pekerjaan tertunda / belum dijawab user (status 22/10 malam)

1. ~~Jarak antar sensor~~: selesai, rev B jarak 8 mm (garis lomba 2 cm).
2. ~~Model 3D rev B~~: selesai, v16 https://claude.ai/artifact/C6BMXLgUPLJN5Aubm8uyx3 (koordinat sensor untuk
   firmware di `hardware/sensor-garis/REVISI.md`). Belum dikonfirmasi user: skid nilon di H1/H2, posisi J5.
3. ~~QRE lokal~~: Rp15.000/pcs, 12 tanpa cadangan; `charter.md` + `gen_charter.js` sudah diperbarui (RAB Rp902.000,
   lewat Rp2.000). **Docx belum dibuat ulang: Node.js belum terpasang di laptop.** Nama toko + link menyusul dari user.
4. ~~Wiring diagram blok 4~~: selesai (JST XH 8 pin, mux I2–I13), artifact versi 7.
5. ~~FPC1~~: diabaikan (keputusan user).
6. **PCB utama baru**: proyek awal `hardware/pcb-utama/` sudah ada (outline, lubang, gambar bantu, skematik kosong).
   Berikutnya: user menggambar skematik, lalu Claude bantu layout (penempatan, routing via MCP).
7. Belum ikut keputusan terbaru: `docs/skematik-v1.md`, `docs/minsys-v1.md`, `gen_rab_pemeliharaan.py`,
   `hardware/tools/` (generator), `firmware/Pins.h` + `platformio.ini` (masih ESP32-S3; ditunda, keputusan user).
8. Firmware M0–M7 belum mulai. Logbook utama terakhir 02/10: isi hanya dari kegiatan yang user ceritakan.

## 4. Memakai MCP KiCad

Panduan lengkap: `hardware/tools/kicad-mcp/README.md`. Ringkas:

- Mulai dengan `kicad_status`. Satuan mm, Y ke bawah; `origin="grid"` untuk koordinat relatif grid origin
  (pasang dengan `set_origin` di puncak depan outline supaya angka sama dengan `hardware/outline/README.md`).
- Tiap panggilan yang mengubah board = satu langkah Ctrl+Z. **Jangan `save_board` tanpa diminta.**
- Sesudah mengubah tata letak: `render_board` (lihat gambarnya sendiri; tampak bawah untuk sensor, karena QRE di
  sisi bawah) dan `run_drc`.
- Di KiCad 9: `flip_footprints` hanya memilih footprint, user yang menekan F. Kalau API menjawab "sibuk",
  minta user menutup dialog yang terbuka.
- Footprint baru masuk lewat skematik (F8), bukan lewat MCP.

## 5. Kebiasaan user dan pelajaran

- Bahasa Indonesia santai. Jawab ringkas; ETS dan dokumen tulisan tangan → versi padat.
- **Konfirmasi keputusan besar** sebelum mengerjakan (pernah salah mengira pertanyaan sebagai keputusan).
- Visual: buka `docs/referensi/`, cocokkan siluet, render dan cek sendiri (berdampingan dengan referensi)
  sebelum dikirim. User mudah kecewa kalau gambar tidak mirip referensi.
- Label net lokal KiCad berawalan `/` (`/S1`), net simbol daya tidak (`+5V`, `GND`).
- Commit per pekerjaan selesai, pesan commit Bahasa Indonesia, lalu push ke `main` (cara kerja selama ini).

## 6. Yang tinggal di cloud / claude.ai

- Link artifact (model 3D, wiring diagram, diagram blok, flowchart, arsitektur) ada di `CLAUDE.md`.
- Sumber diagram blok (Design canvas) disalin ke `docs/diagram-blok-src/` (butuh runtime artifact untuk
  dibuka; gambar PNG-nya `docs/diagram-blok.png`, `docs/diagram-blok-kendali.png`).
- Bahan ETS (Claude Docs): https://claude.ai/artifact/GouFs5MRchq4dV4DA2FSEC (ETS sudah selesai).
