# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.10", "kicad-python>=0.8", "pymupdf>=1.24,<2"]
# ///
"""Server MCP untuk mengedit PCB yang sedang terbuka di KiCad 9/10 secara live.

Server ini bicara dengan KiCad lewat IPC API resmi (paket `kicad-python`), jadi setiap perubahan langsung
terlihat di PCB Editor dan bisa dibatalkan dengan Ctrl+Z (satu panggilan tool = satu langkah undo).
File .kicad_pcb tidak disimpan kecuali tool `save_board` dipanggil. DRC dan render memakai salinan
sementara board (SaveCopyOfDocument) lalu menjalankan kicad-cli, jadi file asli tidak tersentuh.

Cara pakai: lihat README.md di folder ini.
"""

from __future__ import annotations

import functools
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from typing import Literal, Optional

from pydantic import BaseModel, Field

try:  # mcp 2.x
    from mcp.server.mcpserver import Image, MCPServer as _Server
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server, Image
    from mcp.server.fastmcp.exceptions import ToolError

from kipy import KiCad
from kipy.board_types import (
    ArcTrack,
    BoardArc,
    BoardCircle,
    BoardLayer,
    BoardPolygon,
    BoardRectangle,
    BoardSegment,
    BoardText,
    FootprintInstance,
    Track,
    Via,
)
from kipy.errors import ApiError
from kipy.geometry import Angle, Vector2, arc_center, arc_radius
from kipy.proto.board.board_commands_pb2 import BoardOriginType
from kipy.proto.common.types import KIID
from kipy.util.board_layer import canonical_name, layer_from_canonical_name
from kipy.util.units import from_mm, to_mm

INSTRUCTIONS = """\
Mengedit PCB yang sedang terbuka di KiCad PCB Editor secara live.
- Satuan mm. Sumbu Y KiCad ke BAWAH. Sudut dalam derajat, positif = berlawanan arah jarum jam (seperti
  di dialog properti KiCad).
- Parameter `origin`: "page" (koordinat absolut, default, sama dengan dialog properti), "grid" (relatif
  ke grid origin yang diset user), "drill" (relatif ke drill/place origin).
- Setiap panggilan yang mengubah board = satu langkah undo di KiCad (user bisa Ctrl+Z).
- Perubahan belum tersimpan ke file sampai `save_board` dipanggil; jangan simpan tanpa diminta user.
- Sesudah mengubah tata letak, cek dengan `render_board` (gambar) dan `run_drc`.
- Mulai dengan `kicad_status` untuk memastikan KiCad tersambung.
"""

mcp = _Server("kicad", instructions=INSTRUCTIONS)


def tool(fn):
    """Daftarkan fungsi sebagai tool MCP; semua error diteruskan sebagai pesan yang terbaca Claude."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"{type(e).__name__}: {e}") from e

    return mcp.tool()(wrapper)


HINT = (
    "Tidak bisa tersambung ke KiCad. Pastikan: (1) KiCad 9 atau lebih baru, (2) Preferences → Plugins → "
    "'Enable KiCad API' dicentang lalu KiCad dibuka ulang, (3) PCB Editor sedang membuka board. "
    "Detail: "
)

_kicad: Optional[KiCad] = None
_cli_path: Optional[str] = None
_snap_dir: Optional[str] = None


# ---------------------------------------------------------------------------------------------
# Bantuan umum
# ---------------------------------------------------------------------------------------------

def _kc() -> KiCad:
    global _kicad
    if _kicad is None:
        _kicad = KiCad(client_name="claude-kicad-mcp", timeout_ms=10000)
    return _kicad


def _board():
    global _kicad
    try:
        return _kc().get_board()
    except Exception as e:  # koneksi putus atau board belum dibuka
        if "not ready" in str(e):
            raise RuntimeError("KiCad sedang sibuk: tutup dialog yang terbuka di KiCad (mis. dialog properti, "
                               "DRC, atau wizard pertama kali) lalu coba lagi.") from None
        _kicad = None
        raise RuntimeError(HINT + str(e)) from None


def _mm(v: int) -> float:
    return round(to_mm(v), 4)


class _Frame:
    """Konversi koordinat antara nm absolut KiCad dan mm relatif terhadap origin pilihan."""

    def __init__(self, board, origin: str):
        if origin == "page":
            self.ox = self.oy = 0
        elif origin in ("grid", "drill"):
            t = BoardOriginType.BOT_GRID if origin == "grid" else BoardOriginType.BOT_DRILL
            o = board.get_origin(t)
            self.ox, self.oy = o.x, o.y
        else:
            raise ValueError("origin harus 'page', 'grid', atau 'drill'")

    def out(self, v: Vector2) -> tuple[float, float]:
        return (_mm(v.x - self.ox), _mm(v.y - self.oy))

    def inp(self, x: float, y: float) -> Vector2:
        return Vector2.from_xy(from_mm(x) + self.ox, from_mm(y) + self.oy)


def _fmt(p: tuple[float, float]) -> str:
    return f"({p[0]:g}, {p[1]:g})"


def _natural(s: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def _ref(fp: FootprintInstance) -> str:
    return fp.reference_field.text.value


def _footprints(board) -> dict[str, FootprintInstance]:
    out: dict[str, FootprintInstance] = {}
    for fp in board.get_footprints():
        out.setdefault(_ref(fp), fp)
    return out


def _side(fp: FootprintInstance) -> str:
    return "B" if fp.layer == BoardLayer.BL_B_Cu else "F"


def _deg(a: Angle) -> float:
    d = round(a.degrees, 3) % 360
    return d - 360 if d > 180 else d


_LAYER_ALIASES = {
    "f.silkscreen": "F.SilkS", "b.silkscreen": "B.SilkS",
    "f.courtyard": "F.CrtYd", "b.courtyard": "B.CrtYd",
    "f.fabrication": "F.Fab", "b.fabrication": "B.Fab",
    "f.adhesive": "F.Adhes", "b.adhesive": "B.Adhes",
    "user.drawings": "Dwgs.User", "user.comments": "Cmts.User",
    "user.eco1": "Eco1.User", "user.eco2": "Eco2.User",
}


def _layer(name: str):
    canon = _LAYER_ALIASES.get(name.lower(), name)
    lay = layer_from_canonical_name(canon)
    if lay == BoardLayer.BL_UNKNOWN:
        # coba cocokkan tanpa memedulikan huruf besar/kecil
        for cand in ("F.Cu", "B.Cu", "F.SilkS", "B.SilkS", "Edge.Cuts", "F.Mask", "B.Mask", "F.Fab",
                     "B.Fab", "F.CrtYd", "B.CrtYd", "Dwgs.User", "Cmts.User", "Margin"):
            if cand.lower() == canon.lower():
                return layer_from_canonical_name(cand)
        raise ValueError(f"Layer '{name}' tidak dikenal (contoh: F.Cu, B.Cu, F.SilkS, Edge.Cuts)")
    return lay


def _default_width(layer) -> int:
    name = canonical_name(layer)
    if name == "Edge.Cuts":
        return from_mm(0.05)
    if name.endswith("SilkS"):
        return from_mm(0.2)  # batas tempat cetak: garis silkscreen min 0,203 mm
    if name.endswith("CrtYd"):
        return from_mm(0.05)
    return from_mm(0.1)


def _net_index(board) -> dict[str, object]:
    return {n.name: n for n in board.get_nets()}


def _find_net(board, name: str):
    nets = _net_index(board)
    for cand in (name, "/" + name.lstrip("/")):
        if cand in nets:
            return nets[cand]
    raise ValueError(f"Net '{name}' tidak ada di board (cek dengan list_nets)")


def _kiid(s: str) -> KIID:
    k = KIID()
    k.value = s
    return k


def _items_by_ids(board, ids: list[str]) -> list:
    """Cari item berdasarkan ID. GetItemsById baru ada di KiCad 10; di KiCad 9 cari manual."""
    try:
        return list(board.get_items_by_id([_kiid(i) for i in ids]))
    except ApiError as e:
        if "no handler" not in str(e):
            raise
    want = set(ids)
    found = []
    for get in (board.get_shapes, board.get_text, board.get_tracks, board.get_vias, board.get_zones,
                board.get_footprints, board.get_dimensions):
        try:
            found += [it for it in get() if it.id.value in want]
        except ApiError:  # jenis item yang belum didukung versi KiCad ini (mis. dimensi di KiCad 9)
            pass
    return found


def _commit(board, message: str, fn):
    """Jalankan fn() di dalam satu commit supaya jadi satu langkah undo di KiCad."""
    c = board.begin_commit()
    try:
        result = fn()
    except Exception:
        board.drop_commit(c)
        raise
    board.push_commit(c, message)
    return result


# ---------------------------------------------------------------------------------------------
# Status & inspeksi
# ---------------------------------------------------------------------------------------------

@tool
def kicad_status() -> str:
    """Cek sambungan ke KiCad dan ringkasan board yang sedang terbuka (versi, file, jumlah item,
    origin grid/drill, item terpilih). Panggil ini pertama kali."""
    b = _board()
    k = _kc()
    fps = b.get_footprints()
    grid = _Frame(b, "page").out(b.get_origin(BoardOriginType.BOT_GRID))
    drill = _Frame(b, "page").out(b.get_origin(BoardOriginType.BOT_DRILL))
    try:
        proj = b.get_project().path
    except Exception:
        proj = "?"
    lines = [
        f"KiCad {k.get_version()} (API kicad-python {k.get_api_version()})",
        f"Board: {b.name}  | folder proyek: {proj}",
        f"Lapisan tembaga: {b.get_copper_layer_count()}",
        f"Footprint: {len(fps)}, track: {len(b.get_tracks())}, via: {len(b.get_vias())}, "
        f"zona: {len(b.get_zones())}, grafis: {len(b.get_shapes())}, net: {len(b.get_nets())}",
        f"Grid origin: {_fmt(grid)} mm, drill/place origin: {_fmt(drill)} mm (koordinat page)",
        f"Item terpilih di editor: {len(b.get_selection())}",
    ]
    return "\n".join(lines)


@tool
def list_footprints(
    ref_pattern: str = Field("", description="Regex untuk referensi (fullmatch), mis. 'U\\d+' atau "
                                             "'R(1|2)\\d'. Kosong = semua."),
    origin: Literal["page", "grid", "drill"] = "page",
) -> str:
    """Daftar footprint: referensi, nilai, footprint pustaka, posisi x/y (mm), rotasi (°), sisi (F/B),
    terkunci."""
    b = _board()
    fr = _Frame(b, origin)
    rx = re.compile(ref_pattern) if ref_pattern else None
    rows = []
    for ref, fp in sorted(_footprints(b).items(), key=lambda kv: _natural(kv[0])):
        if rx and not rx.fullmatch(ref):
            continue
        x, y = fr.out(fp.position)
        lib = fp.definition.id
        rows.append(
            f"{ref} | {fp.value_field.text.value} | {lib.library}:{lib.name} | {x:g} | {y:g} | "
            f"{_deg(fp.orientation):g} | {_side(fp)} | {'ya' if fp.locked else ''}"
        )
    if not rows:
        return "Tidak ada footprint yang cocok."
    return "ref | nilai | footprint | x | y | rot | sisi | kunci\n" + "\n".join(rows)


@tool
def get_footprint(ref: str, origin: Literal["page", "grid", "drill"] = "page") -> str:
    """Detail satu footprint: posisi, rotasi, sisi, kotak batas (tanpa teks), dan semua pad
    (nomor, net, posisi absolut)."""
    b = _board()
    fr = _Frame(b, origin)
    fp = _footprints(b).get(ref)
    if fp is None:
        raise ValueError(f"Footprint '{ref}' tidak ada")
    lib = fp.definition.id
    x, y = fr.out(fp.position)
    lines = [
        f"{ref} = {fp.value_field.text.value}  ({lib.library}:{lib.name})",
        f"posisi ({x:g}, {y:g}) mm, rotasi {_deg(fp.orientation):g}°, sisi {_side(fp)}, "
        f"terkunci: {'ya' if fp.locked else 'tidak'}",
    ]
    box = b.get_item_bounding_box(fp)
    if box is not None:
        x1, y1 = fr.out(box.pos)
        lines.append(f"kotak batas: x {x1:g}..{x1 + _mm(box.size.x):g}, y {y1:g}..{y1 + _mm(box.size.y):g} "
                     f"({_mm(box.size.x):g} × {_mm(box.size.y):g} mm)")
    lines.append("pad | net | x | y")
    for p in sorted(fp.definition.pads, key=lambda p: _natural(p.number)):
        px, py = fr.out(p.position)
        lines.append(f"{p.number} | {p.net.name or '-'} | {px:g} | {py:g}")
    return "\n".join(lines)


def _shape_desc(s, fr: _Frame) -> str:
    if isinstance(s, BoardSegment):
        return f"garis {_fmt(fr.out(s.start))} → {_fmt(fr.out(s.end))}"
    if isinstance(s, BoardArc):
        c = arc_center(s.start, s.mid, s.end)
        r = arc_radius(s.start, s.mid, s.end)
        cs = f", pusat {_fmt(fr.out(c))} R{_mm(int(r)):g}" if c is not None else ""
        return f"busur {_fmt(fr.out(s.start))} lewat {_fmt(fr.out(s.mid))} → {_fmt(fr.out(s.end))}{cs}"
    if isinstance(s, BoardCircle):
        r = (s.radius_point - s.center).length()
        return f"lingkaran pusat {_fmt(fr.out(s.center))} R{_mm(int(r)):g}"
    if isinstance(s, BoardRectangle):
        return f"persegi {_fmt(fr.out(s.top_left))} – {_fmt(fr.out(s.bottom_right))}"
    if isinstance(s, BoardPolygon):
        pts = [fr.out(n.point) for pwh in s.polygons for n in pwh.outline.nodes if n.has_point]
        return f"poligon {len(pts)} titik: " + " ".join(_fmt(p) for p in pts)
    return type(s).__name__


@tool
def get_board_outline(origin: Literal["page", "grid", "drill"] = "page") -> str:
    """Bentuk tepi board (semua grafis di layer Edge.Cuts) beserta kotak batas dan ukurannya."""
    b = _board()
    fr = _Frame(b, origin)
    shapes = [s for s in b.get_shapes() if s.layer == BoardLayer.BL_Edge_Cuts]
    if not shapes:
        return "Belum ada outline di Edge.Cuts."
    lines = [f"[{s.id.value}] {_shape_desc(s, fr)}" for s in shapes]
    boxes = [bb for bb in b.get_item_bounding_box(shapes) if bb is not None]
    if boxes:
        x1 = min(bb.pos.x for bb in boxes)
        y1 = min(bb.pos.y for bb in boxes)
        x2 = max(bb.pos.x + bb.size.x for bb in boxes)
        y2 = max(bb.pos.y + bb.size.y for bb in boxes)
        p1, p2 = fr.out(Vector2.from_xy(x1, y1)), fr.out(Vector2.from_xy(x2, y2))
        lines.insert(0, f"kotak batas {_fmt(p1)} – {_fmt(p2)}, ukuran {_mm(x2 - x1):g} × {_mm(y2 - y1):g} mm")
    return "\n".join(lines)


@tool
def list_nets(name_pattern: str = Field("", description="Regex nama net (search). Kosong = semua.")) -> str:
    """Daftar net beserta pad yang tersambung (mis. 'R1.2'). Net dari label lokal berawalan '/'."""
    b = _board()
    pads: dict[str, list[str]] = {}
    for ref, fp in _footprints(b).items():
        for p in fp.definition.pads:
            if p.net.name:
                pads.setdefault(p.net.name, []).append(f"{ref}.{p.number}")
    rx = re.compile(name_pattern) if name_pattern else None
    rows = []
    for n in sorted(_net_index(b), key=_natural):
        if not n or (rx and not rx.search(n)):
            continue
        members = sorted(pads.get(n, []), key=_natural)
        rows.append(f"{n} ({len(members)}): {' '.join(members)}")
    return "\n".join(rows) if rows else "Tidak ada net yang cocok."


def _item_desc(it, fr: _Frame) -> str:
    if isinstance(it, FootprintInstance):
        return f"footprint {_ref(it)} di {_fmt(fr.out(it.position))} rot {_deg(it.orientation):g}° sisi {_side(it)}"
    if isinstance(it, (Track, ArcTrack)):
        return (f"track {canonical_name(it.layer)} net {it.net.name or '-'} lebar {_mm(it.width):g} "
                f"{_fmt(fr.out(it.start))} → {_fmt(fr.out(it.end))}")
    if isinstance(it, Via):
        return (f"via net {it.net.name or '-'} di {_fmt(fr.out(it.position))} "
                f"Ø{_mm(it.diameter):g}/{_mm(it.drill_diameter):g}")
    if isinstance(it, BoardText):
        return f"teks '{it.value}' {canonical_name(it.layer)} di {_fmt(fr.out(it.position))}"
    if hasattr(it, "layer") and hasattr(it, "attributes"):
        return f"{canonical_name(it.layer)}: {_shape_desc(it, fr)}"
    return type(it).__name__


@tool
def get_selection(origin: Literal["page", "grid", "drill"] = "page") -> str:
    """Item yang sedang dipilih user di PCB Editor (berguna untuk perintah seperti 'geser yang kupilih')."""
    b = _board()
    fr = _Frame(b, origin)
    items = b.get_selection()
    if not items:
        return "Tidak ada item terpilih."
    return "\n".join(f"[{it.id.value}] {_item_desc(it, fr)}" for it in items)


@tool
def select_items(
    refs: list[str] = Field(default_factory=list, description="Referensi footprint, mis. ['U1','R3']"),
    ids: list[str] = Field(default_factory=list, description="ID item dari output tool lain"),
) -> str:
    """Pilih (highlight) item di PCB Editor supaya user melihat item yang dimaksud. Seleksi lama dihapus."""
    b = _board()
    fps = _footprints(b)
    missing = [r for r in refs if r not in fps]
    items = [fps[r] for r in refs if r in fps]
    if ids:
        items += _items_by_ids(b, ids)
    b.clear_selection()
    if items:
        b.add_to_selection(items)
    msg = f"{len(items)} item dipilih."
    if missing:
        msg += f" Tidak ditemukan: {', '.join(missing)}"
    return msg


# ---------------------------------------------------------------------------------------------
# Mengubah board
# ---------------------------------------------------------------------------------------------

class Placement(BaseModel):
    ref: str = Field(description="Referensi footprint, mis. 'U1'")
    x: Optional[float] = Field(None, description="Posisi X baru (mm). Kosong = tetap (atau pakai dx)")
    y: Optional[float] = Field(None, description="Posisi Y baru (mm, ke bawah). Kosong = tetap")
    rotation: Optional[float] = Field(None, description="Rotasi baru (°). Kosong = tetap")
    dx: float = Field(0.0, description="Geser relatif X (mm), dipakai kalau x kosong")
    dy: float = Field(0.0, description="Geser relatif Y (mm), dipakai kalau y kosong")
    drotation: float = Field(0.0, description="Putar relatif (°), dipakai kalau rotation kosong")


@tool
def place_footprints(
    moves: list[Placement],
    origin: Literal["page", "grid", "drill"] = "page",
    allow_locked: bool = Field(False, description="Ikut pindahkan footprint yang terkunci"),
) -> str:
    """Pindah/putar banyak footprint sekaligus (satu langkah undo). Posisi = titik origin footprint
    (yang ditampilkan di dialog properti KiCad). Semua referensi dicek dulu; kalau ada yang tidak
    ada, tidak ada yang diubah."""
    b = _board()
    fr = _Frame(b, origin)
    fps = _footprints(b)
    missing = [m.ref for m in moves if m.ref not in fps]
    if missing:
        raise ValueError(f"Footprint tidak ada: {', '.join(missing)}. Tidak ada yang diubah.")
    changed, skipped, report = [], [], []
    for m in moves:
        fp = fps[m.ref]
        if fp.locked and not allow_locked:
            skipped.append(m.ref)
            continue
        old = fr.out(fp.position)
        old_rot = _deg(fp.orientation)
        nx = m.x if m.x is not None else old[0] + m.dx
        ny = m.y if m.y is not None else old[1] + m.dy
        nrot = m.rotation if m.rotation is not None else old_rot + m.drotation
        fp.position = fr.inp(nx, ny)
        fp.orientation = Angle.from_degrees(nrot)
        changed.append(fp)
        report.append(f"{m.ref}: {_fmt(old)} {old_rot:g}° → ({nx:g}, {ny:g}) {_deg(Angle.from_degrees(nrot)):g}°")
    if changed:
        _commit(b, f"Claude: pindah {len(changed)} footprint", lambda: b.update_items(changed))
    out = "\n".join(report) if report else "Tidak ada yang dipindah."
    if skipped:
        out += f"\nDilewati (terkunci): {', '.join(skipped)}; pakai allow_locked=true kalau memang mau."
    return out


@tool
def flip_footprints(refs: list[str]) -> str:
    """Pindahkan footprint ke sisi sebaliknya (F↔B, dicerminkan kiri-kanan). Perlu KiCad 10.0.6+;
    di versi lama footprint dipilih dan user diminta menekan F."""
    b = _board()
    fps = _footprints(b)
    missing = [r for r in refs if r not in fps]
    if missing:
        raise ValueError(f"Footprint tidak ada: {', '.join(missing)}")
    items = [fps[r] for r in refs]
    try:
        done = _commit(b, f"Claude: balik sisi {len(items)} footprint", lambda: b.flip_items(items))
        return f"{len(done)} footprint dibalik: " + ", ".join(f"{_ref(f)}→{_side(f)}" for f in done)
    except ApiError as e:
        if "no handler" not in str(e):
            raise
        b.clear_selection()
        b.add_to_selection(items)
        return ("KiCad versi ini belum bisa membalik footprint lewat API (perlu 10.0.6+). "
                f"{len(items)} footprint sudah dipilih di editor; minta user menekan F di PCB Editor.")


class Graphic(BaseModel):
    kind: Literal["line", "polyline", "arc", "circle", "rect"] = Field(
        description="line: 2 titik; polyline: ≥2 titik (closed=true untuk menutup); arc: 3 titik "
                    "[awal, tengah, akhir]; circle: 1 titik pusat + radius; rect: 2 titik sudut")
    points: list[tuple[float, float]] = Field(description="Titik-titik [x, y] dalam mm")
    radius: Optional[float] = Field(None, description="Untuk circle")
    closed: bool = False


@tool
def draw_graphics(
    shapes: list[Graphic],
    layer: str = Field("Edge.Cuts", description="Mis. Edge.Cuts, F.SilkS, B.SilkS, Dwgs.User, F.Fab"),
    width: Optional[float] = Field(None, description="Tebal garis (mm). Kosong = Edge.Cuts 0,05; "
                                                     "silkscreen 0,2; lainnya 0,1"),
    origin: Literal["page", "grid", "drill"] = "page",
) -> str:
    """Gambar garis/busur/lingkaran/persegi di layer grafis (outline board, silkscreen, dsb.).
    Satu langkah undo. Mengembalikan ID item (bisa dihapus dengan delete_items)."""
    b = _board()
    fr = _Frame(b, origin)
    lay = _layer(layer)
    w = from_mm(width) if width is not None else _default_width(lay)
    items = []

    def seg(p, q):
        s = BoardSegment()
        s.start, s.end = fr.inp(*p), fr.inp(*q)
        items.append(s)

    for g in shapes:
        pts = g.points
        if g.kind in ("line", "polyline"):
            if len(pts) < 2:
                raise ValueError(f"{g.kind} perlu minimal 2 titik")
            for p, q in zip(pts, pts[1:]):
                seg(p, q)
            if g.closed and len(pts) > 2:
                seg(pts[-1], pts[0])
        elif g.kind == "arc":
            if len(pts) != 3:
                raise ValueError("arc perlu 3 titik: awal, tengah, akhir")
            a = BoardArc()
            a.start, a.mid, a.end = (fr.inp(*p) for p in pts)
            items.append(a)
        elif g.kind == "circle":
            if len(pts) != 1 or not g.radius:
                raise ValueError("circle perlu 1 titik pusat dan radius")
            c = BoardCircle()
            c.center = fr.inp(*pts[0])
            c.radius_point = fr.inp(pts[0][0] + g.radius, pts[0][1])
            items.append(c)
        elif g.kind == "rect":
            if len(pts) != 2:
                raise ValueError("rect perlu 2 titik sudut")
            r = BoardRectangle()
            r.top_left = fr.inp(min(pts[0][0], pts[1][0]), min(pts[0][1], pts[1][1]))
            r.bottom_right = fr.inp(max(pts[0][0], pts[1][0]), max(pts[0][1], pts[1][1]))
            items.append(r)
    for it in items:
        it.layer = lay
        it.attributes.stroke.width = w
    created = _commit(b, f"Claude: gambar {len(items)} grafis", lambda: b.create_items(items))
    return f"{len(created)} item dibuat di {canonical_name(lay)}: " + " ".join(i.id.value for i in created)


def _fillet(prev, p, nxt, r):
    """Titik singgung dan titik tengah busur fillet berjari-jari r di sudut p."""
    ux, uy = prev[0] - p[0], prev[1] - p[1]
    l1 = math.hypot(ux, uy)
    vx, vy = nxt[0] - p[0], nxt[1] - p[1]
    l2 = math.hypot(vx, vy)
    ux, uy, vx, vy = ux / l1, uy / l1, vx / l2, vy / l2
    th = math.acos(max(-1.0, min(1.0, ux * vx + uy * vy)))
    t = r / math.tan(th / 2)
    if t > min(l1, l2) / 2 + 1e-9:
        raise ValueError(f"Radius {r} terlalu besar untuk sudut di {p}")
    bx, by = ux + vx, uy + vy
    bl = math.hypot(bx, by)
    bx, by = bx / bl, by / bl
    d = r / math.sin(th / 2)
    c = (p[0] + bx * d, p[1] + by * d)
    return (p[0] + ux * t, p[1] + uy * t), (c[0] - bx * r, c[1] - by * r), (p[0] + vx * t, p[1] + vy * t)


@tool
def draw_rounded_polygon(
    points: list[tuple[float, float]] = Field(description="Sudut-sudut poligon tertutup [x, y] mm, urut"),
    radii: list[float] = Field(default_factory=list,
                               description="Radius fillet per sudut (mm), sepanjang points; 0 = tajam. "
                                           "Kosong = semua tajam"),
    layer: str = "Edge.Cuts",
    width: Optional[float] = None,
    mirror_x: Optional[float] = Field(None, description="Kalau diisi, points dianggap separuh kanan/kiri; "
                                                         "separuh lainnya dicerminkan terhadap garis x ini "
                                                         "(urutan otomatis) supaya bentuknya simetris"),
    origin: Literal["page", "grid", "drill"] = "page",
) -> str:
    """Gambar poligon tertutup dengan sudut membulat (cocok untuk outline PCB). Dengan mirror_x, cukup
    beri setengah bentuk: titik pertama dan terakhir harus tepat di garis cermin. Satu langkah undo."""
    pts = [tuple(p) for p in points]
    rad = list(radii) if radii else [0.0] * len(pts)
    if len(rad) != len(pts):
        raise ValueError("radii harus sepanjang points")
    if mirror_x is not None:
        if abs(pts[0][0] - mirror_x) > 1e-6 or abs(pts[-1][0] - mirror_x) > 1e-6:
            raise ValueError("Dengan mirror_x, titik pertama dan terakhir harus di garis cermin")
        back = [(2 * mirror_x - x, y) for x, y in reversed(pts[1:-1])]
        pts = pts + back
        rad = rad + list(reversed(rad[1:-1]))
    n = len(pts)
    if n < 3:
        raise ValueError("Poligon perlu minimal 3 titik")
    corners = []  # (masuk, tengah, keluar) per sudut
    for i in range(n):
        if rad[i] > 0:
            corners.append(_fillet(pts[i - 1], pts[i], pts[(i + 1) % n], rad[i]))
        else:
            corners.append((pts[i], None, pts[i]))
    shapes: list[Graphic] = []
    for i in range(n):
        t_in, mid, t_out = corners[i]
        if mid is not None:
            shapes.append(Graphic(kind="arc", points=[t_in, mid, t_out]))
        nxt_in = corners[(i + 1) % n][0]
        if math.dist(t_out, nxt_in) > 1e-6:
            shapes.append(Graphic(kind="line", points=[t_out, nxt_in]))
    return draw_graphics(shapes=shapes, layer=layer, width=width, origin=origin)


@tool
def add_text(
    text: str,
    x: float,
    y: float,
    layer: str = "F.SilkS",
    size: float = Field(1.0, description="Tinggi huruf (mm)"),
    thickness: float = Field(0.2, description="Tebal goresan (mm); silkscreen min 0,2"),
    rotation: float = 0.0,
    origin: Literal["page", "grid", "drill"] = "page",
) -> str:
    """Tambah teks bebas di board (mis. label silkscreen). Teks di layer B.* otomatis dicerminkan."""
    b = _board()
    fr = _Frame(b, origin)
    lay = _layer(layer)
    t = BoardText()
    t.value = text
    t.position = fr.inp(x, y)
    t.layer = lay
    t.attributes.size = Vector2.from_xy(from_mm(size), from_mm(size))
    t.attributes.stroke_width = from_mm(thickness)
    t.attributes.angle = rotation
    t.attributes.mirrored = canonical_name(lay).startswith("B.")
    created = _commit(b, "Claude: tambah teks", lambda: b.create_items([t]))
    return f"Teks dibuat: {created[0].id.value}"


def _netclass_sizes(b, net) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """(lebar track, diameter via, bor via) dari net class, kalau bisa dibaca."""
    try:
        nc = b.get_netclass_for_nets(net).get(net.name)
        if nc is None:
            return None, None, None
        return nc.track_width, getattr(nc, "via_diameter", None), getattr(nc, "via_drill", None)
    except Exception:
        return None, None, None


@tool
def add_track(
    points: list[tuple[float, float]] = Field(description="Titik-titik jalur [x, y] mm (≥2), disambung berurutan"),
    net: str = Field(description="Nama net, mis. 'GND', '+5V', '/S1' (awalan '/' boleh dihilangkan)"),
    layer: Literal["F.Cu", "B.Cu"] = "F.Cu",
    width: Optional[float] = Field(None, description="Lebar (mm). Kosong = lebar net class"),
    origin: Literal["page", "grid", "drill"] = "page",
) -> str:
    """Tambah jalur tembaga lurus berurutan (satu langkah undo). Sesudahnya cek dengan run_drc."""
    if len(points) < 2:
        raise ValueError("Perlu minimal 2 titik")
    b = _board()
    fr = _Frame(b, origin)
    n = _find_net(b, net)
    w = from_mm(width) if width is not None else (_netclass_sizes(b, n)[0] or from_mm(0.3))
    items = []
    for p, q in zip(points, points[1:]):
        t = Track()
        t.start, t.end = fr.inp(*p), fr.inp(*q)
        t.width = w
        t.layer = _layer(layer)
        t.net = n
        items.append(t)
    created = _commit(b, f"Claude: tambah track {n.name}", lambda: b.create_items(items))
    return f"{len(created)} segmen track {n.name} lebar {_mm(w):g} mm: " + " ".join(i.id.value for i in created)


@tool
def add_vias(
    points: list[tuple[float, float]] = Field(description="Posisi via [x, y] mm"),
    net: str = Field(description="Nama net"),
    diameter: Optional[float] = Field(None, description="Diameter pad via (mm). Kosong = net class atau 1,3"),
    drill: Optional[float] = Field(None, description="Diameter bor (mm). Kosong = net class atau 0,6"),
    origin: Literal["page", "grid", "drill"] = "page",
) -> str:
    """Tambah via tembus (satu langkah undo)."""
    b = _board()
    fr = _Frame(b, origin)
    n = _find_net(b, net)
    _, nc_d, nc_drill = _netclass_sizes(b, n)
    d = from_mm(diameter) if diameter is not None else (nc_d or from_mm(1.3))
    dr = from_mm(drill) if drill is not None else (nc_drill or from_mm(0.6))
    items = []
    for p in points:
        v = Via()
        v.position = fr.inp(*p)
        v.diameter = d
        v.drill_diameter = dr
        v.net = n
        items.append(v)
    created = _commit(b, f"Claude: tambah via {n.name}", lambda: b.create_items(items))
    return f"{len(created)} via {n.name} Ø{_mm(d):g}/{_mm(dr):g} mm: " + " ".join(i.id.value for i in created)


@tool
def delete_items(ids: list[str] = Field(description="ID item (dari output tool lain atau get_selection)")) -> str:
    """Hapus item berdasarkan ID (satu langkah undo). Untuk footprint, hapus dari skematik saja."""
    b = _board()
    found = _items_by_ids(b, ids)
    fps = [_ref(f) for f in found if isinstance(f, FootprintInstance)]
    if fps:
        raise ValueError(f"Menolak menghapus footprint ({', '.join(fps)}); hapus dari skematik lalu update PCB.")
    if found:
        _commit(b, f"Claude: hapus {len(found)} item", lambda: b.remove_items(found))
    return f"{len(found)} dari {len(ids)} item dihapus."


@tool
def set_origin(
    x: float = Field(description="X (mm) dalam koordinat page"),
    y: float = Field(description="Y (mm) dalam koordinat page"),
    kind: Literal["grid", "drill"] = "grid",
) -> str:
    """Pasang grid origin (atau drill/place origin) di titik tertentu, mis. puncak depan PCB sensor,
    supaya koordinat berikutnya bisa ditulis relatif (origin='grid')."""
    b = _board()
    t = BoardOriginType.BOT_GRID if kind == "grid" else BoardOriginType.BOT_DRILL
    b.set_origin(t, Vector2.from_xy_mm(x, y))
    return f"{kind} origin dipasang di ({x:g}, {y:g}) mm (page)."


@tool
def refill_zones() -> str:
    """Isi ulang semua zona (pour) tembaga, seperti menekan B di KiCad."""
    b = _board()
    b.refill_zones(block=True)
    return f"{len(b.get_zones())} zona diisi ulang."


@tool
def save_board() -> str:
    """Simpan board ke file .kicad_pcb (seperti Ctrl+S). Panggil hanya kalau user meminta."""
    b = _board()
    b.save()
    return f"Tersimpan: {b.name}"


# ---------------------------------------------------------------------------------------------
# DRC & render (lewat salinan sementara + kicad-cli)
# ---------------------------------------------------------------------------------------------

def _cli() -> str:
    global _cli_path
    if _cli_path:
        return _cli_path
    cand = os.environ.get("KICAD_CLI")
    if not cand:
        try:
            cand = _kc().get_kicad_binary_path("kicad-cli")
        except Exception:
            cand = None
    if not cand or not os.path.exists(cand):
        cand = shutil.which("kicad-cli")
    if not cand:
        raise RuntimeError("kicad-cli tidak ditemukan; set variabel lingkungan KICAD_CLI ke path kicad-cli")
    _cli_path = cand
    return cand


def _snapshot() -> str:
    """Simpan salinan board yang sedang terbuka (termasuk perubahan yang belum disimpan) ke folder
    sementara. File asli tidak tersentuh."""
    global _snap_dir
    if _snap_dir is None or not os.path.isdir(_snap_dir):
        _snap_dir = tempfile.mkdtemp(prefix="kicad-mcp-")
        os.chmod(_snap_dir, 0o777)
    path = os.path.join(_snap_dir, "snapshot.kicad_pcb")
    _board().save_as(path, overwrite=True, include_project=True)
    return path


def _run_cli(args: list[str]) -> None:
    r = subprocess.run([_cli()] + args, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"kicad-cli gagal ({r.returncode}): {(r.stderr or r.stdout).strip()[-800:]}")


@tool
def run_drc(
    max_items: int = Field(40, description="Jumlah maksimum pelanggaran yang ditampilkan detail"),
    ignore_types: list[str] = Field(default_factory=lambda: ["lib_footprint_mismatch", "lib_footprint_issues"],
                                    description="Jenis pelanggaran yang tidak ditampilkan detailnya "
                                                "(tetap dihitung)"),
    origin: Literal["page", "grid", "drill"] = "page",
) -> str:
    """Jalankan DRC pada keadaan board saat ini (termasuk yang belum disimpan) memakai aturan proyek
    (.kicad_pro + .kicad_dru). Ringkasan per jenis, lalu detail (error dulu)."""
    b = _board()
    fr = _Frame(b, origin)
    pcb = _snapshot()
    out = os.path.join(os.path.dirname(pcb), "drc.json")
    _run_cli(["pcb", "drc", "--format", "json", "--units", "mm", "-o", out, pcb])
    with open(out, encoding="utf-8") as f:
        rep = json.load(f)
    viol = rep.get("violations", [])
    unconn = rep.get("unconnected_items", [])
    counts: dict[tuple[str, str], int] = {}
    for v in viol:
        k = (v.get("severity", "?"), v.get("type", "?"))
        counts[k] = counts.get(k, 0) + 1
    lines = [f"DRC: {len(viol)} pelanggaran, {len(unconn)} belum tersambung (unconnected)."]
    for (sev, typ), c in sorted(counts.items(), key=lambda kv: (kv[0][0] != "error", -kv[1])):
        lines.append(f"  {sev:7s} {typ}: {c}")

    def pos(it):
        p = it.get("pos", {})
        return _fmt((round(p.get("x", 0) - _mm(fr.ox), 4), round(p.get("y", 0) - _mm(fr.oy), 4)))

    shown = 0
    detail = sorted((v for v in viol if v.get("type") not in ignore_types),
                    key=lambda v: v.get("severity") != "error")
    if detail:
        lines.append("Detail:")
    for v in detail:
        if shown >= max_items:
            lines.append(f"  … {len(detail) - shown} lagi")
            break
        items = "; ".join(f"{it.get('description', '')} @ {pos(it)}" for it in v.get("items", []))
        lines.append(f"  [{v.get('severity')}] {v.get('description')} — {items}")
        shown += 1
    for u in unconn[:max(0, max_items - shown)]:
        items = "; ".join(f"{it.get('description', '')} @ {pos(it)}" for it in u.get("items", []))
        lines.append(f"  [unconnected] {items}")
    return "\n".join(lines)


@tool
def render_board(
    view: Literal["2d", "3d"] = Field("2d", description="2d = gambar layer (tembaga, silkscreen, outline); "
                                                        "3d = render tiga dimensi dengan komponen"),
    side: Literal["top", "bottom"] = "top",
    layers: Optional[list[str]] = Field(None, description="Khusus 2d: daftar layer, mis. ['F.Cu','Edge.Cuts']. "
                                                          "Kosong = tembaga + silkscreen sisi itu + Edge.Cuts"),
    area: Optional[tuple[float, float, float, float]] = Field(
        None, description="Khusus 2d: perbesar daerah [x1, y1, x2, y2] mm (koordinat sesuai origin)"),
    zoom: float = Field(1.0, description="Khusus 3d: zoom kamera"),
    width_px: int = Field(1600, description="Lebar gambar (piksel)"),
    origin: Literal["page", "grid", "drill"] = "page",
):
    """Gambar board saat ini (termasuk perubahan yang belum disimpan) supaya hasil edit bisa dilihat.
    Tampak bawah (side='bottom') dicerminkan seperti dilihat dari bawah."""
    b = _board()
    fr = _Frame(b, origin)
    pcb = _snapshot()
    d = os.path.dirname(pcb)
    png = os.path.join(d, "render.png")
    if view == "3d":
        h = max(200, int(width_px * 9 / 16))
        _run_cli(["pcb", "render", "--side", side, "--quality", "basic", "--background", "opaque",
                  "--zoom", str(zoom), "-w", str(width_px), "-h", str(h), "-o", png, pcb])
        with open(png, "rb") as f:
            return [f"Render 3D tampak {side}.", Image(data=f.read(), format="png")]

    import pymupdf  # diimpor di sini supaya tool lain tetap jalan walau pymupdf belum terpasang

    if not layers:
        layers = (["B.Cu", "F.Cu", "F.SilkS", "Edge.Cuts"] if side == "top"
                  else ["F.Cu", "B.Cu", "B.SilkS", "Edge.Cuts"])
    svg = os.path.join(d, "render.svg")
    # Mode halaman 1 = ukuran kertas asli tanpa bingkai: koordinat SVG (mm) = koordinat page KiCad.
    args = ["pcb", "export", "svg", "--mode-single", "--page-size-mode", "1", "--exclude-drawing-sheet",
            "--layers", ",".join(layers), "-o", svg]
    if side == "bottom":
        args.append("--mirror")
    _run_cli(args + [pcb])
    page = pymupdf.open(svg)[0]
    k = 72 / 25.4  # pt per mm
    if area:
        x1, y1, x2, y2 = area
        x1, y1 = x1 + _mm(fr.ox), y1 + _mm(fr.oy)
        x2, y2 = x2 + _mm(fr.ox), y2 + _mm(fr.oy)
        note = f"Daerah {area} mm."
    else:
        # bingkai = kotak batas Edge.Cuts (atau semua footprint kalau belum ada outline) + 2 mm
        items = [s for s in b.get_shapes() if s.layer == BoardLayer.BL_Edge_Cuts] or list(b.get_footprints())
        boxes = [bb for bb in b.get_item_bounding_box(items) if bb is not None] if items else []
        if boxes:
            x1 = _mm(min(bb.pos.x for bb in boxes)) - 2
            y1 = _mm(min(bb.pos.y for bb in boxes)) - 2
            x2 = _mm(max(bb.pos.x + bb.size.x for bb in boxes)) + 2
            y2 = _mm(max(bb.pos.y + bb.size.y for bb in boxes)) + 2
        else:
            x1, y1, x2, y2 = 0, 0, page.rect.width / k, page.rect.height / k
        note = "Seluruh board."
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    if side == "bottom":  # --mirror mencerminkan terhadap lebar kertas
        w_page = page.rect.width / k
        x1, x2 = w_page - x2, w_page - x1
    clip = pymupdf.Rect(x1 * k, y1 * k, x2 * k, y2 * k) & page.rect
    if clip.is_empty:
        raise ValueError("Daerah yang diminta di luar kertas board")
    z = width_px / clip.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z), clip=clip, alpha=False)
    note = f"Render 2D tampak {side} (layer {', '.join(layers)}). {note}"
    if side == "bottom":
        note += " Dicerminkan: kiri gambar = kanan board."
    return [note, Image(data=pix.tobytes("png"), format="png")]


if __name__ == "__main__":
    mcp.run()
