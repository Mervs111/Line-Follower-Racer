# Outline PCB sensor simetris (21/10/2026)

Outline layout PCB sensor buatan user (bentuk T: pita depan berpuncak, badan, tab 2 lubang) dibuat simetris kiri-kanan
dengan angka bulat. Ukuran diambil dari screenshot layout user (skala dari pitch J1 = 2,5 mm), lalu dicek dengan
menumpuk outline baru di atas screenshot: bentuknya sama.

Koordinat (mm, Y ke bawah seperti KiCad, 0,0 = puncak tepi depan):

| Titik | Kanan (kiri = X dibalik tanda) | Radius sudut |
|---|---|---|
| puncak depan | (0 ; 0) | tajam |
| ujung sayap atas | (60 ; 5,5) | R2,5 |
| ujung sayap bawah | (60 ; 20,5) | R2,5 |
| leher (sayap → badan) | (15 ; 20,5) | R2,5 (cekung) |
| sudut bawah badan | (15 ; 34,5) | R2,5 |
| tangga ke tab | (9 ; 34,5) | R1,5 (cekung) |
| sudut bawah tab | (9 ; 46) | tajam |

Lubang H1/H2: (−5 ; 40) dan (5 ; 40). J1 dan U13 di garis tengah X = 0.

## Impor ke KiCad

1. Hapus garis Edge.Cuts lama.
2. File → Import → Graphics… → `pcb_sensor_outline_simetris.dxf`, layer **Edge.Cuts**, satuan mm, skala 1.
3. Pasang grid origin di titik puncak depan, lalu Preferences → PCB Editor → Origins & Axes → tampilkan koordinat
   relatif grid origin.
4. Properti (E) tiap komponen: U13 X = 0; H1 (−5 ; 40), H2 (5 ; 40); J1 (origin footprint JST = pin 1): pin 1 di
   kanan → X = +8,75, pin 1 di kiri → X = −8,75.

`gen_outline_simetris.py` membuat ulang DXF dan gambar ukurannya (butuh ezdxf dan Pillow).
