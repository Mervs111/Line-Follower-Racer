# Script Fusion 360: model kasar Robot Line Tracer Micro (versi ringkas).
#
# Cara pakai: Utilities > ADD-INS > Scripts and Add-Ins > tombol "+" > pilih folder
# LTM_Konsep_Ringkas ini > Run. Script membuat dokumen desain baru berisi satu komponen
# per bagian (kotak/silinder) di posisi susunan ringkas.
#
# Sumbu: X = lebar robot (kanan +), Y = arah maju (depan +), Z = atas.
# Titik nol = lantai, tepat di bawah tengah poros roda.
# Semua ukuran dalam mm. Ubah angka di bagian UKURAN lalu jalankan ulang.
# Ukuran bertanda (*) wajib dicek ulang dengan komponen asli (jangka sorong).

import adsk.core
import adsk.fusion
import traceback

# ============================ UKURAN (mm) ============================
D_RODA = 34.0          # (*) diameter roda
LEBAR_RODA = 8.0       # (*) tebal roda
CELAH_TENGAH = 8.0     # celah antar ujung encoder kedua motor
PANJANG_MOTOR = 32.0   # (*) N20 + gearbox + encoder, tanpa as
MOTOR_Y = 12.0         # (*) penampang N20 (arah maju)
MOTOR_Z = 10.0         # (*) penampang N20 (arah atas)
CELAH_RODA = 4.0       # jarak gearbox ke sisi dalam roda

HOLDER = (76.0, 42.0, 20.0)   # holder 2x18650 (P x L x T), sel melintang
GESER_BATERAI = 8.0           # pusat baterai di depan poros
TEBAL_DUDUKAN = 2.0           # pelat 3D print di atas motor

PCB_Z = 12.0           # tinggi sisi bawah PCB utama dari lantai
PCB_T = 1.6            # tebal PCB
# outline PCB utama (x, y): bagian belakang menyempit di antara roda
PCB_OUTLINE = [(-34, 8), (34, 8), (34, 20), (43, 20), (43, 88), (-43, 88), (-43, 20), (-34, 20)]

WING_Z = 4.0           # sisi bawah PCB sayap sensor dari lantai
WING_OUTLINE = [(-44, 84), (-12, 80), (12, 80), (44, 84), (44, 92), (20, 108), (-20, 108), (-44, 92)]
SENSOR_XY = [(-20, 99), (-10, 102), (0, 104), (10, 102), (20, 99)]

CASTER_XY = (0.0, 72.0)  # (*) ball caster mini di bawah PCB utama
# =====================================================================

MM = 0.1  # API Fusion memakai cm


def P(x, y, z):
    return adsk.core.Point3D.create(x * MM, y * MM, z * MM)


def V(mm):
    return adsk.core.ValueInput.createByReal(mm * MM)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        root.name = 'LTM ringkas'

        colors = {}

        def color(name, r, g, b):
            # Warna opsional: kalau gagal (beda versi pustaka), model tetap jadi.
            if name in colors:
                return colors[name]
            ap = None
            try:
                ap = design.appearances.itemByName(name)
                if not ap:
                    base = None
                    for i in range(app.materialLibraries.count):
                        lib = app.materialLibraries.item(i)
                        if 'ppearance' not in lib.name:
                            continue
                        for j in range(lib.appearances.count):
                            cand = lib.appearances.item(j)
                            if 'Plastic' in cand.name:
                                base = cand
                                break
                        if base:
                            break
                    if base:
                        ap = design.appearances.addByCopy(base, name)
                        for k in range(ap.appearanceProperties.count):
                            cp = adsk.core.ColorProperty.cast(ap.appearanceProperties.item(k))
                            if cp:
                                try:
                                    cp.value = adsk.core.Color.create(r, g, b, 255)
                                    break
                                except:
                                    pass
            except:
                ap = None
            colors[name] = ap
            return ap

        def new_comp(name, col=None):
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            occ.component.name = name
            if col:
                ap = color(*col)
                if ap:
                    try:
                        occ.appearance = ap
                    except:
                        pass
            return occ.component

        def plane(comp, base, dist):
            if abs(dist) < 1e-6:
                return base
            pi = comp.constructionPlanes.createInput()
            pi.setByOffset(base, V(dist))
            pl = comp.constructionPlanes.add(pi)
            pl.isLightBulbOn = False
            return pl

        def extrude(comp, sk, dist):
            prof = sk.profiles.item(0)
            return comp.features.extrudeFeatures.addSimple(
                prof, V(dist), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        def prism(comp, pts, z0, h):
            # poligon tertutup di bidang XY setinggi z0, diekstrusi ke atas setinggi h
            sk = comp.sketches.add(plane(comp, comp.xYConstructionPlane, z0))
            lines = sk.sketchCurves.sketchLines
            sp = [sk.modelToSketchSpace(P(x, y, z0)) for x, y in pts]
            first = lines.addByTwoPoints(sp[0], sp[1])
            prev = first
            for pt in sp[2:]:
                prev = lines.addByTwoPoints(prev.endSketchPoint, pt)
            lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
            return extrude(comp, sk, h)

        def box(comp, x0, x1, y0, y1, z0, z1):
            return prism(comp, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1 - z0)

        def cyl_x(comp, x0, x1, yc, zc, r):
            # silinder sumbu X dari x0 ke x1 (x0 < x1)
            sk = comp.sketches.add(plane(comp, comp.yZConstructionPlane, x0))
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x0, yc, zc)), r * MM)
            return extrude(comp, sk, x1 - x0)

        def cyl_z(comp, xc, yc, z0, h, r):
            sk = comp.sketches.add(plane(comp, comp.xYConstructionPlane, z0))
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(xc, yc, z0)), r * MM)
            return extrude(comp, sk, h)

        # ---------- turunan ukuran ----------
        r_roda = D_RODA / 2
        m_in = CELAH_TENGAH / 2
        m_out = m_in + PANJANG_MOTOR
        w_in = m_out + CELAH_RODA
        w_out = w_in + LEBAR_RODA
        mz0, mz1 = r_roda - MOTOR_Z / 2, r_roda + MOTOR_Z / 2
        hx, hy, hz = HOLDER
        bat_z0 = mz1 + TEBAL_DUDUKAN
        by0, by1 = GESER_BATERAI - hy / 2, GESER_BATERAI + hy / 2
        top = PCB_Z + PCB_T

        GELAP = ('LTM hitam', 30, 34, 40)
        PERAK = ('LTM perak', 195, 203, 212)

        # ---------- roda, motor, as ----------
        for s, side in ((-1, 'kiri'), (1, 'kanan')):
            c = new_comp('Roda ' + side, GELAP)
            x0, x1 = sorted((s * w_in, s * w_out))
            cyl_x(c, x0, x1, 0, r_roda, r_roda)

            c = new_comp('Motor N20 ' + side, PERAK)
            x0, x1 = sorted((s * m_in, s * m_out))
            box(c, x0, x1, -MOTOR_Y / 2, MOTOR_Y / 2, mz0, mz1)
            x0, x1 = sorted((s * m_out, s * w_out))
            cyl_x(c, x0, x1, 0, r_roda, 1.5)

        # ---------- dudukan 3D print + baterai ----------
        c = new_comp('Dudukan baterai (3D print)', ('LTM putih', 236, 240, 244))
        box(c, -hx / 2, hx / 2, by0, by1, mz1, bat_z0)

        c = new_comp('Holder 2x18650', ('LTM oren', 242, 163, 58))
        box(c, -hx / 2, hx / 2, by0, by1, bat_z0, bat_z0 + hz)

        # ---------- PCB utama + modul ----------
        c = new_comp('PCB utama', ('LTM biru PCB', 31, 95, 175))
        prism(c, PCB_OUTLINE, PCB_Z, PCB_T)

        c = new_comp('ESP32 DevKit', GELAP)
        box(c, -41, -13, 30, 81, top, top + 10)

        c = new_comp('OLED 1.3in', ('LTM navy', 19, 35, 58))
        box(c, -8, 27, 50, 84, top + 7, top + 11)

        c = new_comp('Modul TB6612', ('LTM ungu', 123, 79, 160))
        box(c, -32, -12, 9, 29, top, top + 6)

        c = new_comp('Modul MP1584', ('LTM ungu', 123, 79, 160))
        box(c, 11, 33, 10, 27, top, top + 5)

        c = new_comp('Buzzer', GELAP)
        cyl_z(c, 36, 44, top, 9.5, 6)

        c = new_comp('Saklar', PERAK)
        box(c, 37, 43, 30, 36, top, top + 6)

        for name, yc in (('Tombol A', 78), ('Tombol B', 62)):
            c = new_comp(name, GELAP)
            box(c, 34, 40, yc - 3, yc + 3, top, top + 5)

        # ---------- ball caster ----------
        c = new_comp('Ball caster mini', PERAK)
        cx, cy = CASTER_XY
        cyl_z(c, cx, cy, 6, PCB_Z - 6, 6)
        cyl_z(c, cx, cy, 0.2, 5.8, 3)

        # ---------- sayap sensor ----------
        c = new_comp('PCB sayap sensor', ('LTM biru PCB', 31, 95, 175))
        prism(c, WING_OUTLINE, WING_Z, PCB_T)

        c = new_comp('Sensor ITR20001 x5', GELAP)
        for x, y in SENSOR_XY:
            box(c, x - 2, x + 2, y - 1.5, y + 1.5, 1.5, WING_Z)

        c = new_comp('Spacer sayap', PERAK)
        for x in (-30, 30):
            cyl_z(c, x, 84, WING_Z + PCB_T, PCB_Z - WING_Z - PCB_T, 2.5)

        app.activeViewport.fit()
        ui.messageBox('Model LTM ringkas selesai dibuat.\n'
                      'Lebar {:.0f} mm, tinggi {:.0f} mm.'.format(2 * w_out, bat_z0 + hz))
    except:
        if ui:
            ui.messageBox('Gagal:\n{}'.format(traceback.format_exc()))
