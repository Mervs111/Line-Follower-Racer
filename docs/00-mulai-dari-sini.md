# Mulai dari sini

Panduan singkat alur kerja proyek ini, dari nol sampai tes di robot.

## Gambaran besar

Proyek dikerjakan per **milestone** (M0 sampai M7). Tiap milestone:

1. Claude menulis kode dan push ke GitHub.
2. Kamu tarik kodenya, compile, lalu upload ke ESP32-S3.
3. Kamu tes di hardware dan laporkan hasilnya (berhasil / error apa).
4. Kalau sudah OK, lanjut ke milestone berikutnya.

## Persiapan (sekali saja)

1. Install **VS Code**: https://code.visualstudio.com
2. Di VS Code, buka tab Extensions lalu install **PlatformIO IDE**. Tunggu sampai selesai
   (pertama kali agak lama karena download toolchain ESP32).
3. Install **Git**: https://git-scm.com
4. Clone repo ini:
   ```bash
   git clone https://github.com/Mervs111/Line-Follower-Racer.git
   ```
5. Di VS Code: **File → Open Folder** lalu pilih folder `firmware/` (bukan folder root repo),
   supaya PlatformIO mengenali proyeknya.

## Tiap kali ada kode baru

```bash
git pull
```

Lalu di VS Code (ikon PlatformIO di bilah bawah):

| Ikon | Fungsi |
|---|---|
| ✓ (Build) | compile, sama dengan `pio run` |
| → (Upload) | flash ke board |
| 🔌 (Serial Monitor) | lihat output serial (115200) |

Colok board lewat port USB **native** (GPIO19/20). Kalau upload gagal: tahan tombol
**BOOT**, tekan **RESET**, lepas BOOT, lalu upload lagi.

## Tes M0

Yang harus terlihat:

- [ ] Build sukses tanpa error
- [ ] LED WS2812 (GPIO48) berkedip hijau tiap 0,5 detik
- [ ] Serial Monitor menampilkan `Line follower siap (M0)...`
- [ ] Ketikan di Serial Monitor dibalas (echo)

Laporkan hasil checklist di atas. Kalau ada error, salin pesan error-nya utuh.
