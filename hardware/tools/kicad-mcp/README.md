# MCP KiCad: Claude mengedit PCB secara live

Server MCP ini menghubungkan Claude Code dengan **KiCad PCB Editor yang sedang terbuka**. Claude bisa membaca
dan memindah footprint, menggambar outline, menambah teks/jalur/via, menjalankan DRC, dan melihat gambar board.
Semua perubahan langsung tampak di layar KiCad.

- Satu perintah Claude = **satu langkah undo** (Ctrl+Z di KiCad membatalkannya).
- File `.kicad_pcb` **tidak disimpan** sampai kamu minta ("simpan board"). DRC dan render memakai salinan
  sementara, jadi file asli tidak tersentuh.
- Bekerja lewat IPC API resmi KiCad (paket `kicad-python`), bukan dengan mengedit file teks.

Sudah dites (22/10/2026, Linux): KiCad **9.0.9** dan **10.0.7**, kicad-python 0.8.0, mcp 1.30 dan 2.3,
Python 3.10 dan 3.12. Belum dites di Windows/macOS.

## Syarat

- **KiCad 9 atau 10.** KiCad 8 tidak bisa (API-nya baru ada sejak KiCad 9).
- **Python 3.10+.**
- **Claude Code yang jalan di komputermu sendiri** (CLI `claude`, atau `claude remote-control` kalau mau
  memantau dari aplikasi Claude). Sesi Claude Code di cloud tidak bisa menjangkau KiCad di laptop.

## Pasang (sekali saja)

1. **Aktifkan API di KiCad**: Preferences → Preferences → Plugins → centang **Enable KiCad API** → tutup dan buka
   ulang KiCad.
2. **Pasang paket Python** (dari folder repo):

   ```bash
   # Windows
   py -m pip install -r hardware/tools/kicad-mcp/requirements.txt
   # macOS / Linux
   python3 -m pip install -r hardware/tools/kicad-mcp/requirements.txt
   ```

3. **Daftarkan ke Claude Code** (ganti path sesuai lokasi repo di laptopmu; `--scope user` = tersedia di semua folder):

   ```bash
   # Windows (PowerShell)
   claude mcp add kicad --scope user -- py "C:\path\ke\Line-Follower-Racer\hardware\tools\kicad-mcp\kicad_mcp.py"
   # macOS / Linux
   claude mcp add kicad --scope user -- python3 /path/ke/Line-Follower-Racer/hardware/tools/kicad-mcp/kicad_mcp.py
   ```

   Kalau sudah punya [uv](https://docs.astral.sh/uv/), langkah 2 bisa dilewati:
   `claude mcp add kicad --scope user -- uv run --script /path/ke/kicad_mcp.py` (paket dipasang otomatis).

4. **Cek**: buka board di PCB Editor, jalankan `claude` di folder proyek, ketik `/mcp` → `kicad` harus
   *connected*. Lalu minta: "cek status kicad".

Supaya tidak ditanya izin di setiap perintah: `/permissions` → Allow → tambahkan `mcp__kicad`. Semua perubahan
tetap bisa di-Ctrl+Z.

## Contoh perintah ke Claude

- "Pasang grid origin di puncak depan outline PCB sensor, lalu taruh sensor 1–12 sesuai
  `mechanical/v15/dxf/pcb_sensor_posisi_qre1113.csv` relatif ke grid origin."
- "Resistor tiap sensor taruh 4 mm di belakang sensornya, rotasi sama."
- "Gambar outline simetris dari `hardware/outline/README.md` di Edge.Cuts."
- "Render tampak bawah, perbesar daerah sensor 1–4", "jalankan DRC", "yang kupilih geser 0,5 mm ke kiri".

## Daftar tool

| Tool | Fungsi |
|---|---|
| `kicad_status` | Cek sambungan, versi, file board, jumlah item, origin |
| `list_footprints`, `get_footprint` | Posisi/rotasi/sisi footprint; pad + net + posisi pad |
| `get_board_outline` | Garis/busur Edge.Cuts + ukuran board |
| `list_nets` | Net dan pad yang tersambung |
| `get_selection`, `select_items` | Baca / sorot item yang dipilih di editor |
| `place_footprints` | Pindah/putar banyak footprint sekaligus (absolut atau relatif dx/dy) |
| `flip_footprints` | Pindah ke sisi bawah/atas (KiCad 10.0.6+; di KiCad 9 footprint dipilih, kamu tekan F) |
| `draw_graphics`, `draw_rounded_polygon` | Garis/busur/lingkaran/persegi; poligon bersudut bulat (bisa dicerminkan) |
| `add_text`, `add_track`, `add_vias` | Teks bebas, jalur tembaga, via (ukuran default dari net class) |
| `delete_items` | Hapus item hasil tool (menolak menghapus footprint) |
| `set_origin` | Pasang grid/drill origin |
| `refill_zones` | Isi ulang pour (seperti tombol B) |
| `run_drc` | DRC dengan aturan proyek (`.kicad_pro` + `.kicad_dru`), ringkasan per jenis |
| `render_board` | Gambar 2D (layer tembaga/silkscreen/outline, bisa diperbesar) atau 3D |
| `save_board` | Simpan file (hanya kalau diminta) |

Koordinat dalam mm, sumbu Y ke bawah seperti KiCad. Parameter `origin` = `page` (sama dengan dialog properti),
`grid`, atau `drill`.

## Batasan

- Footprint baru tetap masuk lewat skematik (Tools → Update PCB from Schematic, F8). Tidak ada autorouter.
- Kalau ada dialog terbuka di KiCad (properti, DRC, wizard pertama kali), API menjawab "sibuk": tutup dulu
  dialognya.
- `run_drc` dan `render_board` memanggil `kicad-cli` milik KiCad yang sedang jalan. Kalau tidak ketemu, set
  variabel lingkungan `KICAD_CLI` ke path `kicad-cli`.
- Edit di KiCad dan di Claude boleh bergantian, tapi jangan saat KiCad sedang menjalankan perintah lain.
