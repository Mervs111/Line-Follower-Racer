"""Menyiapkan file proyek wokwi.com dari firmware ASLI (firmware/src + firmware/lib/LineFollower).

wokwi.com hanya menerima file datar (tanpa folder library sendiri), jadi seluruh firmware digabung menjadi satu
file `firmware.cpp` (header lokal disisipkan sekali, urutan sama seperti build PlatformIO). `sketch.ino` dibiarkan
kosong karena setup()/loop() ada di firmware.cpp. Hasil di folder `unggah/` (tidak masuk git):

    unggah/sketch.ino  firmware.cpp  diagram.json  libraries.txt  robot-lfm.chip.json  robot-lfm.chip.c

Jalankan ulang tiap firmware berubah:   python simulasi/wokwi-firmware/siapkan.py
"""
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SRC_DIRS = [REPO / "firmware" / "lib" / "LineFollower" / "src", REPO / "firmware" / "src"]
# urutan file .cpp: library dulu, lalu program bawaan (main.cpp paling akhir)
CPP_FILES = [
    "LineFollower.cpp", "LfEncoders.cpp", "LfRoute.cpp",
    "Routes.cpp", "Console.cpp", "Ui.cpp", "main.cpp",
]
COPY = ["diagram.json", "libraries.txt", "robot-lfm.chip.json", "robot-lfm.chip.c"]
INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]')


def find_local(name):
    for d in SRC_DIRS:
        p = d / name
        if p.is_file():
            return p
    return None


def inline(path, done, out):
    """Tulis isi file ke out; header lokal disisipkan rekursif, masing-masing sekali saja."""
    rel = path.relative_to(REPO).as_posix()
    out.append(f"// ===== {rel} =====")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "#pragma once":
            continue
        m = INCLUDE_RE.match(line)
        local = find_local(m.group(1)) if m else None
        if local is not None:
            if local not in done:
                done.add(local)
                inline(local, done, out)
            continue
        out.append(line)
    out.append("")


def main():
    dst = HERE / "unggah"
    dst.mkdir(exist_ok=True)
    out = [
        "// firmware.cpp — firmware LFM X1 digabung jadi satu file untuk wokwi.com.",
        "// DIBUAT OTOMATIS oleh simulasi/wokwi-firmware/siapkan.py dari firmware/src + firmware/lib/LineFollower.",
        "// Jangan diedit di sini: ubah file aslinya, lalu jalankan ulang siapkan.py.",
        "",
    ]
    done = set()
    for name in CPP_FILES:
        p = find_local(name)
        if p is None:
            raise SystemExit(f"tidak ketemu: {name}")
        done.add(p)
        inline(p, done, out)
    (dst / "firmware.cpp").write_text("\n".join(out), encoding="utf-8")
    (dst / "sketch.ino").write_text(
        "// Sengaja kosong: setup() dan loop() firmware LFM X1 ada di firmware.cpp.\n", encoding="utf-8")
    for name in COPY:
        shutil.copyfile(HERE / name, dst / name)
    n = sum(1 for _ in out)
    print(f"unggah/ siap: firmware.cpp ({n} baris) + sketch.ino + {', '.join(COPY)}")


if __name__ == "__main__":
    main()
