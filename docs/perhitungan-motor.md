# Perhitungan Awal Motor & Roda (draf kelompok, 08/10/2026)

Disimpan sebagai konteks. Status: **draf asumsi**, belum dikunci di charter/RAB.

## Asumsi

| Besaran | Nilai |
|---|---|
| Target kecepatan | ≈ 1,5 m/s |
| Diameter roda | 60 mm (r = 0,03 m) |
| Massa robot | 0,3 kg |
| Roda penggerak | 2 |
| Waktu akselerasi 0 → 1,5 m/s | 0,5 s |

## 1. Kebutuhan RPM

v = ω·r → ω = v / r = 1,5 / 0,03 = 50 rad/s

RPM = ω · 60 / (2π) = 50 · 60 / (2π) ≈ 477 RPM → pilih motor ± **500 RPM**.

## 2. Kecepatan teoritis motor 500 RPM vs diameter roda

v = 2π·r·RPM / 60

| Diameter roda | Kecepatan teoritis |
|---|---|
| 40 mm | 1,05 m/s |
| 50 mm | 1,31 m/s |
| **60 mm** | **1,57 m/s** (dipilih sebagai titik awal) |
| 65 mm | 1,70 m/s |
| 70 mm | 1,83 m/s |

Diameter roda memengaruhi: kecepatan, torsi di roda, kemampuan melewati permukaan, kestabilan saat belok.
Angka di atas kondisi ideal tanpa beban; kecepatan nyata lebih rendah.

## 3. Gaya dan torsi

a = Δv / Δt = 1,5 / 0,5 = 3 m/s²

F = m·a = 0,3 · 3 = 0,9 N (akselerasi ideal, belum termasuk hambatan)

τ = F·r = 0,9 · 0,03 = 0,027 N·m = 27 N·mm

Per roda (2 roda): τ_roda ≈ 27 / 2 ≈ **13,5 N·mm**

## 4. Margin desain (safety factor)

Jangan desain pas-pasan; perlu margin untuk gesekan roda, gearbox, hambatan permukaan, perubahan
arah, beban baterai/chassis, akselerasi, dan kondisi lintasan.

Safety factor 2: τ_design = 13,5 × 2 = **27 N·mm per roda**

**Target motor: torsi output ≥ 27 N·mm per roda** (≈ 0,28 kg·cm; 1 kg·cm = 98,1 N·mm — penjual
motor biasanya menulis torsi dalam kg·cm). Bandingkan dengan torsi rated (bukan stall) di datasheet.

## Catatan pemeriksaan (Claude)

- Hitungan aritmetika di atas sudah dicek dan benar.
- Faktor keamanan 2 sudah ditambahkan di bagian 4 (hambatan gulir & efisiensi gearbox dicakup lewat margin ini).
  Lazimnya torsi motor dipilih beberapa kali lipat (mis. 2–3×) dari hasil hitung ideal,
  dan dibandingkan dengan torsi **rated** (bukan stall) di datasheet motor yang dipilih.
- Belum sinkron dengan charter revisi 3 & RAB:
  - Charter: sasaran kecepatan ≥ 0,5 m/s (dibatasi demi keamanan anak). Hitungan ini memakai 1,5 m/s.
    Bisa konsisten bila 1,5 m/s = kemampuan maksimum desain, 0,5 m/s = batas mode pemula.
  - RAB: roda N20 Ø34 mm; hitungan ini memakai roda Ø60 mm (motor 500 RPM).
  - Massa 0,3 kg perlu dicek ulang setelah ada perkiraan berat baterai 2× 18650 (± 90–100 g) + PCB + motor.

## Keputusan (08/10/2026)

- Kecepatan: sasaran charter tetap ≥ 0,5 m/s; 1,5 m/s hanya dasar pemilihan motor (bukan sasaran uji).
- Roda Ø43 mm + motor N20 6V ± 700 RPM + encoder → v_maks teoritis ≈ 1,58 m/s.
  Kebutuhan pada roda Ø43 mm: ± 666 RPM, torsi desain (SF 2) ± 19 N·mm ≈ 0,20 kg·cm per roda.
- PWM dibatasi ± 70% di firmware karena motor 6V dipasok baterai 2S (7,4–8,4 V).

## Keputusan (revisi, 08/10/2026) — menggantikan keputusan di atas

- Di marketplace hanya tersedia N20 + encoder **6V 500 RPM** → dipakai.
- Desain robot rendah satu bidang → roda **Ø34 mm**.
- v_maks teoritis = π × 0,034 × 500 / 60 ≈ **0,89 m/s** (sasaran ≥ 0,5 m/s tetap tercapai dengan cadangan).
- Torsi (target 0,9 m/s dalam 0,5 s → a = 1,8 m/s², m = 0,3 kg): F = 0,54 N; τ total = 0,54 × 0,017 ≈ 9,2 N·mm;
  per roda ≈ 4,6 N·mm; dengan SF 2 ≈ **9,2 N·mm ≈ 0,09 kg·cm per roda**. Motor 500 RPM (rasio gear lebih besar)
  punya torsi lebih tinggi dari 700 RPM, jadi aman.
- Baterai: 2× 14500 (± 40 g) menggantikan 2× 18650 (± 90 g).
