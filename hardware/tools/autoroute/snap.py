"""Simpan salinan board live (termasuk perubahan belum disimpan) ke path argumen; file asli tidak tersentuh."""
import sys
from kipy import KiCad

KiCad(client_name="claude-route", timeout_ms=30000).get_board().save_as(sys.argv[1], overwrite=True,
                                                                       include_project=True)
print("ok", sys.argv[1])
