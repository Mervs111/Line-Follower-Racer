# Log kerja harian

Catatan apa yang dikerjakan tiap hari di repo (oleh user dan Claude Code), dirangkum dari commit. Bahan untuk
logbook utama (`docs/logbook/logbook-utama.md`); logbook itu tetap hanya diisi kegiatan tim yang benar-benar terjadi.
Entri terbaru di atas.

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

## 21/10/2026
- Aturan cetak PCB dari tempat cetak user (jalur 0,3 mm) + template setting KiCad.
- Outline PCB sensor simetris dari layout user (DXF + gambar ukuran).
- Mux jadi IC CD74HC4067 SOIC-24W disolder langsung.
