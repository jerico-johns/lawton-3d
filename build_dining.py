#!/usr/bin/env python3
"""3932 Lawton dining room, rebuilt from scratch in Blender on every run (pilot, Nov 24 2026).
All sizes in INCHES, plan coords u (0 living wall -> 138 kitchen wall, along the west wall), v (0 west wall -> 147 hall
side), z up. Blender x=u, y=-v. Camera solved from listing photo p08 (see CAM). Furniture sizes are in SPEC; nothing is
eyeballed. Usage:  .venv/bin/python build_dining.py [--passes color,depth,mask] [--samples 96] [--scale 1.0]
Writes out/<pass>.png, out/dining.blend, out/boxes.json (model pixel boxes + measured sizes, used by the drift check)."""
import argparse, json, math, pathlib, sys
import bpy
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
IN = 0.0254
U, V = 138.0, 147.0
RAIL, PLATE, TRAY = 28.8, 85.4, 109.0         # wainscot cap, plate-rail underside, tray ceiling (from p08)
CAM = dict(u=66.8, v=163.0, z=47.6, f_px=703.0, vx=728.0, vy=487.0, w=1500.0, h=999.0)
SPEC = {   # name: (width, depth, height)
    "tate": (64.5, 16, 30), "bookcase": (22, 16, 75.5), "table": (80, 37, 30), "chair": (20, 21, 31),
    "rug": (120, 96, 0.5), "lantern": (30, 30, 30),
}
TATE_U0 = U / 2 - SPEC["tate"][0] / 2
BOOK_U0 = TATE_U0 - 7.4 - SPEC["bookcase"][0]
TABLE_U0, TABLE_V0 = U / 2 - 40 - 6, 16 + 32
RUG_U0, RUG_V0 = TABLE_U0 + 40 - 60, 18
SPIRAL = (114.0, 122.4, 27.6)

PARTS = {}          # group -> [objects]
MATS = {}


def mat(name, rgb, rough=0.6, emit=0.0, noise=None, tex=None):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    lin = tuple((c / 255 / 12.92) if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in rgb) + (1,)
    b.inputs["Base Color"].default_value = lin
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = lin
        b.inputs["Emission Strength"].default_value = emit
    if noise:                                  # stretched grain along one axis: (sx, sy, sz), amount
        tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping"); nz = n.new("ShaderNodeTexNoise")
        mp.inputs["Scale"].default_value = noise[0]; nz.inputs["Detail"].default_value = 4
        mx = n.new("ShaderNodeMixRGB"); mx.blend_type = "MULTIPLY"; mx.inputs["Fac"].default_value = noise[1]
        mx.inputs["Color1"].default_value = lin
        l.new(tc.outputs["Object"], mp.inputs["Vector"]); l.new(mp.outputs["Vector"], nz.inputs["Vector"])
        l.new(nz.outputs["Fac"], mx.inputs["Color2"]); l.new(mx.outputs["Color"], b.inputs["Base Color"])
    if tex:                                    # (path, inches wide, inches high) mapped on world x / z
        tc = n.new("ShaderNodeNewGeometry"); mp = n.new("ShaderNodeVectorMath"); mp.operation = "MULTIPLY"
        mp.inputs[1].default_value = (1 / (tex[1] * IN), 0, 1 / (tex[2] * IN))
        sp = n.new("ShaderNodeSeparateXYZ"); cb = n.new("ShaderNodeCombineXYZ"); im = n.new("ShaderNodeTexImage")
        im.image = bpy.data.images.load(str(tex[0])); im.extension = "REPEAT"
        l.new(tc.outputs["Position"], mp.inputs[0]); l.new(mp.outputs[0], sp.inputs[0])
        l.new(sp.outputs["X"], cb.inputs["X"]); l.new(sp.outputs["Z"], cb.inputs["Y"])
        l.new(cb.outputs[0], im.inputs["Vector"]); l.new(im.outputs["Color"], b.inputs["Base Color"])
    MATS[name] = m
    return m


def add(group, me, m):
    o = bpy.data.objects.new(f"{group}.{len(PARTS.get(group, []))}", me)
    o.data.materials.append(m)
    bpy.context.collection.objects.link(o)
    PARTS.setdefault(group, []).append(o)
    return o


def prism(group, m, ring_lo, ring_hi):
    """Loft between two same-length rings of (u, v, z) points; capped."""
    n = len(ring_lo)
    vs = [(u * IN, -v * IN, z * IN) for u, v, z in list(ring_lo) + list(ring_hi)]
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    me = bpy.data.meshes.new(group); me.from_pydata(vs, [], fs); me.update()
    o = add(group, me, m)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return o


def box(group, m, u, v, z, w, d, h):
    if group == "shell":                       # tiny per-box offset so overlapping trim never shares a face (black patches)
        e = .02 * (1 + len(PARTS.get("shell", [])) % 11); u -= e; w += 2 * e; d += 2 * e; v -= e; z -= e / 2; h += e
    r = [(u, v), (u + w, v), (u + w, v + d), (u, v + d)]
    return prism(group, m, [(a, b, z) for a, b in r], [(a, b, z + h) for a, b in r])


def rod(group, m, p, q, r0, r1=None, n=12):
    r1 = r0 if r1 is None else r1
    a, b = Vector(p), Vector(q); t = (b - a).normalized()
    s = t.cross(Vector((0, 0, 1)) if abs(t.z) < .9 else Vector((1, 0, 0))).normalized(); w = t.cross(s)
    ring = lambda c, r: [tuple(c + s * (r * math.cos(2 * math.pi * i / n)) + w * (r * math.sin(2 * math.pi * i / n))) for i in range(n)]
    return prism(group, m, ring(a, r0), ring(b, r1))


def lathe(group, m, u, v, prof, n=40):
    vs, fs = [], []
    for r, z in prof:
        vs += [((u + r * math.cos(2 * math.pi * i / n)) * IN, -(v + r * math.sin(2 * math.pi * i / n)) * IN, z * IN) for i in range(n)]
    for k in range(len(prof) - 1):
        fs += [((k + 1) * n + i, (k + 1) * n + (i + 1) % n, k * n + (i + 1) % n, k * n + i) for i in range(n)]
    me = bpy.data.meshes.new(group); me.from_pydata(vs, [], fs); me.update()
    for p in me.polygons:
        p.use_smooth = True
    return add(group, me, m)


# ---------------------------------------------------------------- room
def room():
    wall = mat("greige", (207, 201, 190), .8); white = mat("trim", (240, 239, 235), .45); ceil = mat("ceiling", (245, 244, 241), .9)
    oak = mat("oak", (168, 114, 70), .3, noise=((2, 14, 14), .45)); inlay = mat("inlay", (84, 46, 28), .35)
    n = int((HERE / "tex/tile.txt").read_text())
    paper = mat("morris", (80, 90, 70), .9, tex=(HERE / "tex/morris_tile.png", 20.5 * n, 17.9))
    box("floor", oak, -200, -2, -1, 420, 270, 1)
    for a in (box("floor", inlay, 11, 11, 0, 116, 1, .03), box("floor", inlay, 11, 11, 0, 1, 130, .03), box("floor", inlay, 126, 11, 0, 1, 130, .03)):
        pass
    # west wall: paper between wainscot and plate rail, greige above, white below; continues into the living room
    box("shell", paper, 0, -4, RAIL, U, 4, PLATE - RAIL)
    box("shell", white, -200, -4, 0, 338, 4, RAIL); box("shell", wall, 0, -4, PLATE, U, 4, TRAY - PLATE)
    box("shell", mat("livwall", (232, 229, 222), .8), -200, -4, RAIL, 200 - 6.3, 4, TRAY - RAIL)
    def skirt(u, v, w, d, along_u, side):          # baseboard, cap, plate rail on one wall run
        for z, h, t in ((0, 8, .9), (RAIL - 1.6, 1.6, 1.4), (PLATE, 3, 2.2)):
            if along_u: box("shell", white, u, v, z, w, t, h)
            else: box("shell", white, u if side > 0 else u - t, v, z, t, d, h)
    skirt(0, 0, U, 0, True, 1)
    # living-side wall (u -6.3..0), opening v 46.8-106.8, head 86
    for v0, d in ((0, 46.8), (106.8, 60)):
        box("shell", white, -6.3, v0, 0, 6.3, d, RAIL); box("shell", wall, -6.3, v0, RAIL, 6.3, d, TRAY - RAIL); skirt(0, v0, 0, d, False, 1)
    box("shell", wall, -6.3, 46.8, 86, 6.3, 60, TRAY - 86)
    for v0 in (42.2, 107.1): box("shell", white, -6.9, v0, 0, 8.1, 4.3, 85.7)
    box("shell", white, -6.9, 41.5, 86, 8.1, 71, 6)
    # kitchen-side wall: window v 9.6..42 (casing), glass 14-38.5 z 32-83; door opening 54.4-83
    for v0, d, z0, h in ((0, 14, 0, TRAY), (38.5, 15.9, 0, TRAY), (14, 24.5, 0, 30), (14, 24.5, 84, TRAY - 84), (54.4, 33.6, 84, TRAY - 84), (88, 76, 0, TRAY)):
        box("shell", wall, U, v0, z0, 6, d, h)
        if z0 == 0: box("shell", white, U - .15, v0, 0, .2, d, min(h, RAIL))
    skirt(U, 0, 0, 49.5, False, -1); skirt(U, 93.2, 0, 60, False, -1)
    for v0, w, z0, h in ((9.6, 4.4, 28, 60), (38.5, 4.4, 28, 60), (9.6, 33.3, 84, 5), (9.6, 33.3, 28, 3.5), (14, 24.5, 56, 2.2), (49.2, 5.2, 0, 90), (88, 5.2, 0, 90), (49.2, 44, 84, 6)):
        box("shell", white, U - 1.2, v0, z0, 1.4, w, h)
    box("shell", mat("glass", (205, 218, 228), .2, emit=1.4), U + 3, 14, 30, .3, 24.5, 54)
    # kitchen side: back-porch wall at v 44 (plan y 3.7 ft) with the half-glass dog door facing the camera (u 153-183)
    box("shell", white, U + 6, 40, 0, 90, 3.6, TRAY); box("shell", mat("doorw", (236, 235, 230), .5), 153, 43.6, 0, 30, .8, 80)
    box("shell", mat("glass", (0, 0, 0)), 157, 44.5, 48, 22, .3, 28); box("shell", mat("flap", (128, 120, 114), .6), 158.5, 44.5, 9, 15, .4, 27)
    box("shell", white, U, 54.4, 0, 6, .6, 84)
    # hall side wall behind camera stays open; ceiling with cove + crown ledge + hidden LED
    box("shell", ceil, -6, -4, TRAY, 150, 260, 2); box("shell", ceil, -200, -4, TRAY, 194, 260, 2)
    for u, v, w, d in ((0, 0, U, 16), (0, 16.6, 16, 200), (U - 16, 16.6, 16, 200)):
        box("shell", white, u, v, 100, w, d, 2.2)
    # round sun tube in the tray ceiling (centre u 32, v 24 from photo p08)
    lathe("suntube", white, 32, 24, [(9.3, TRAY - .1), (9.1, TRAY - .9), (7, TRAY - .9)]); lathe("suntube", mat("tube", (238, 243, 248), .4, emit=1.8), 32, 24, [(7, TRAY - .8), (.01, TRAY - .8)])
    led = mat("led", (255, 196, 120), .5, emit=6)
    for u, v, w, d in ((6, 12, U - 12, 1.5), (12, 6, 1.5, 190), (U - 13.5, 6, 1.5, 190)): box("led", led, u, v, 102.6, w, d, .6)


def spiral():
    blk = mat("black", (18, 18, 19), .45)
    u, v, r = SPIRAL
    rod("spiral", blk, (u, v, 0), (u, v, 150), 1.6, n=20)
    for k in range(14):
        a0 = math.radians(200 + 30 * k); z = 8.2 * (k + 1)
        ring = [(u + 1.6 * math.cos(a0 - .2), v + 1.6 * math.sin(a0 - .2)), (u + r * math.cos(a0 - .3), v + r * math.sin(a0 - .3)),
                (u + r * math.cos(a0 + .3), v + r * math.sin(a0 + .3)), (u + 1.6 * math.cos(a0 + .2), v + 1.6 * math.sin(a0 + .2))]
        prism("spiral", blk, [(p, q, z) for p, q in ring], [(p, q, z + 1.6) for p, q in ring])
        rod("spiral", blk, (u + (r - 1) * math.cos(a0), v + (r - 1) * math.sin(a0), z), (u + (r - 1) * math.cos(a0), v + (r - 1) * math.sin(a0), z + 36), .7)


# ---------------------------------------------------------------- furniture
def tate():
    w = mat("walnut", (104, 68, 42), .45, noise=((4, 4, 40), .5)); dk = mat("walnutdk", (62, 38, 24), .5)
    W, D, H = SPEC["tate"]; u, leg = TATE_U0, 8.5
    box("tate", w, u, 0, leg, W, D, H - leg)
    for i, (a, b, hh) in enumerate(((.8, 21.4, 0), (22.2, 21.4, 0))):
        box("tate", w, u + a, D, leg + 1, b, .4, H - leg - 2)
    box("tate", w, u + 44.4, D, 23.4, 19.3, .4, 5.4); box("tate", w, u + 44.4, D, leg + 1, 19.3, .4, 13.2)
    box("tate", dk, u + 1.6, D + .4, 14, .7, .5, 10); box("tate", dk, u + 42.2, D + .4, 14, .7, .5, 10)
    for z in (26.2, 20.4): box("tate", dk, u + 49, D + .4, z, 10, .7, .8)
    for a in (5, W - 5):
        for b in (2.5, D - 2.5): rod("tate", w, (u + a, b, leg), (u + a + (-.8 if a < 10 else .8), b, 0), 1.0, .55)
    box("tate", w, u + 5, 2, leg - 1.6, W - 10, 1, 1.6); box("tate", w, u + 5, D - 3, leg - 1.6, W - 10, 1, 1.6)


def bookcase():
    w = mat("walnut", (0, 0, 0)); dk = mat("walnutdk", (0, 0, 0)); W, D, H = SPEC["bookcase"]; u = BOOK_U0
    for a in (0, W - 1):
        for b in (0, D - 1.2): box("bookcase", w, u + a, b, 0, 1, 1.2, H)
        box("bookcase", w, u + a, 0, H - 1, 1, D, 1)
    for z in (70, 57, 44.5): box("bookcase", w, u + 1, .5, z, W - 2, D - 1, 1.2)
    box("bookcase", w, u + 1, .5, 8, W - 2, D - 1, 23.5)
    for z, h in ((25.5, 5.4), (9, 15.6)): box("bookcase", w, u + 1.6, D - .5, z, W - 3.2, .4, h); box("bookcase", dk, u + 6.5, D - .1, z + h - 2.2, 9, .6, .8)


def table():
    p = mat("pine", (198, 138, 78), .5, noise=((3, 30, 30), .35)); W, D, H = SPEC["table"]; u, v = TABLE_U0, TABLE_V0
    box("table", p, u, v, H - 1.6, W, D, 1.6)
    for a in (2, W - 5.2):
        for b in (2, D - 5.2): box("table", p, u + a, v + b, 0, 3.2, 3.2, H - 1.6)
    box("table", p, u + 4, v + 3, H - 5.6, W - 8, 1, 4); box("table", p, u + 4, v + D - 4, H - 5.6, W - 8, 1, 4)
    box("table", p, u + 3, v + 4, H - 5.6, 1, D - 8, 4); box("table", p, u + W - 4, v + 4, H - 5.6, 1, D - 8, 4)
    lathe("bowl", mat("stone", (214, 203, 188), .7), u + W / 2, v + D / 2, [(0, H), (3, H), (6.5, H + 3), (7, H + 4.2), (6.4, H + 4.2), (5, H + 2)])


def chair(k, cu, cv, face):
    """face = direction the sitter looks, in degrees (0 = +u, 90 = +v)."""
    w = mat("walnut", (0, 0, 0)); g = mat("olive", (84, 88, 48), .9); W, D, H = SPEC["chair"]; name = f"chair{k}"
    c, s = math.cos(math.radians(face)), math.sin(math.radians(face))
    P = lambda f, l, z: (cu + f * c - l * s, cv + f * s + l * c, z)
    hw, hd = W / 2 - 1, D / 2 - 1
    for l in (-hw, hw):
        rod(name, w, P(hd, l, 16.5), P(hd, l, 0), .85, .5); rod(name, w, P(-hd + 1.5, l, 17), P(-hd, l, 0), .85, .5)
        rod(name, w, P(-hd + 1.5, l, 17), P(-hd - .1, l, H - 2), .8, .6)
        rod(name, w, P(hd, l, 15.4), P(-hd + 1.5, l, 15.4), .8)
    for f in (hd, -hd + 1.5): rod(name, w, P(f, -hw, 15.4), P(f, hw, 15.4), .8)
    lo = [P(hd, -hw + .5, 16.3), P(hd, hw - .5, 16.3), P(-hd + 2.4, hw - .5, 16.3), P(-hd + 2.4, -hw + .5, 16.3)]
    prism(name, g, lo, [(a, b, 18.6) for a, b, _ in lo])
    N = 10; pts = []
    for i in range(N + 1):
        l = -W / 2 + W * i / N; f = -hd - .1 - 1.0 * (1 - (2 * i / N - 1) ** 2)
        pts.append((f, l))
    for i in range(N):
        (f0, l0), (f1, l1) = pts[i], pts[i + 1]
        r = [P(f0, l0, 0), P(f1, l1, 0), P(f1 + .9, l1, 0), P(f0 + .9, l0, 0)]
        prism(name, w, [(a, b, H - 5) for a, b, _ in r], [(a, b, H) for a, b, _ in r])


def rest():
    box("rug", mat("rust", (150, 72, 48), 1.0, noise=((60, 60, 60), .25)), RUG_U0, RUG_V0, 0.05, *SPEC["rug"])
    tc, tv = TABLE_U0 + 40, TABLE_V0 + 18.5
    d = SPEC["chair"][1]
    P = [(TABLE_U0 + 22, TABLE_V0 + 4 - d / 2, 90), (TABLE_U0 + 58, TABLE_V0 + 4 - d / 2, 90), (TABLE_U0 + 22, TABLE_V0 + 33 + d / 2, -90),
         (TABLE_U0 + 58, TABLE_V0 + 33 + d / 2, -90), (TABLE_U0 + 4 - d / 2, tv, 0), (TABLE_U0 + 76 + d / 2, tv, 180)]
    for k, (a, b, f) in enumerate(P): chair(k + 1, a, b, f)
    R = SPEC["lantern"][0] / 2
    lathe("lantern", mat("paper", (255, 240, 214), .8, emit=1.1), tc, tv, [(R * math.sin(t) + .01, 86 - R * math.cos(t)) for t in [math.pi * i / 24 for i in range(25)]])
    rod("cord", mat("trim", (0, 0, 0)), (tc, tv, 101), (tc, tv, TRAY), .15)
    # lamp + bowl + books on the Tate
    lathe("lamp", mat("ceramic", (212, 200, 182), .6), TATE_U0 + 9, 8, [(2.4, 30), (4.2, 33), (4.2, 36), (1, 39), (.6, 41)])
    lathe("lamp", mat("shade", (250, 226, 180), .9, emit=1.6), TATE_U0 + 9, 8, [(7, 41), (6.2, 50)])
    box("decor", mat("book", (225, 218, 205), .8), TATE_U0 + 46, 4, 30, 11, 8, 2); lathe("decor", mat("walnutdk", (0, 0, 0)), TATE_U0 + 51.5, 8, [(0, 32), (3, 32), (5, 34.5), (4.6, 34.5), (2.5, 33)])
    # bookcase contents
    for z, m, pr in ((71.2 - 12.9, "ceramic", [(2.5, 0), (3.2, 4), (2, 7), (2.2, 7.6)]), (45.7, "ceramic", [(2, 0), (3, 3), (2.8, 5)]), (31.5, "terra", [(2, 0), (3.4, 4), (1.4, 9), (1.8, 10)])):
        lathe("decor", mat("terra", (176, 98, 66), .8) if m == "terra" else mat("ceramic", (0, 0, 0)), BOOK_U0 + 14, 8, [(r, z + h) for r, h in pr])
    for z in (45.7, 31.5): box("decor", mat("book", (0, 0, 0)), BOOK_U0 + 3, 5, z, 7, 7, 3)
    # Kentia palm, window end
    pu, pv = 120, 13; gr = mat("palm", (48, 84, 40), .6)
    lathe("palm", mat("planter", (236, 228, 212), .7), pu, pv, [(6, 0), (7.5, 5), (7.5, 15), (6.8, 15), (6.8, 13), (0, 13)])
    import random; random.seed(4)
    for k in range(13):
        a = 2 * math.pi * k / 13 + random.uniform(-.2, .2); L = random.uniform(9, 17); top = random.uniform(48, 74)
        pts = [(pu + math.cos(a) * L * t ** 1.8, max(1.5, pv + math.sin(a) * L * .65 * t ** 1.8), 13 + (top - 13) * (1.35 * t - .35 * t ** 3)) for t in [i / 8 for i in range(9)]]
        for i in range(8): rod("palm", gr, pts[i], pts[i + 1], .28, .2, n=6)
        for i in range(3, 9):
            x, y, z = pts[i]
            for sgn in (-1, 1):
                ex, ey = x + math.cos(a + sgn * 1.2) * 6, max(1, y + math.sin(a + sgn * 1.2) * 6)
                prism("palm", gr, [(x, y, z), (x + .5, y + .5, z), ((x + ex) / 2 + .5, (y + ey) / 2, z - 1)], [(ex, ey, z - 5), (ex + .1, ey, z - 5), (ex, ey + .1, z - 5)])


def camera(scale):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = int(1536 * scale), int(1024 * scale)
    c = bpy.data.cameras.new("cam"); o = bpy.data.objects.new("cam", c); bpy.context.collection.objects.link(o); sc.camera = o
    o.location = (CAM["u"] * IN, -CAM["v"] * IN, CAM["z"] * IN); o.rotation_euler = (math.pi / 2, 0, 0)
    c.sensor_width = 36; c.lens = 36 * CAM["f_px"] / CAM["w"]; c.clip_start = .02
    c.shift_x = (CAM["w"] / 2 - CAM["vx"]) / CAM["w"]; c.shift_y = (CAM["vy"] - CAM["h"] / 2) / CAM["w"]


def light():
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (.9, .95, 1, 1); w.node_tree.nodes["Background"].inputs[1].default_value = .55
    def area(name, u, v, z, tgt, size, watts, rgb=(1, 1, 1)):
        l = bpy.data.lights.new(name, "AREA"); l.size = size * IN; l.energy = watts; l.color = rgb
        o = bpy.data.objects.new(name, l); o.location = (u * IN, -v * IN, z * IN); bpy.context.collection.objects.link(o)
        o.rotation_euler = (Vector((tgt[0] * IN, -tgt[1] * IN, tgt[2] * IN)) - o.location).to_track_quat("-Z", "Y").to_euler()
    area("win", U - 3, 26, 56, (40, 60, 30), 40, 18, (.92, .96, 1)); area("fill", 69, 160, 95, (69, 20, 45), 70, 26); area("living", -70, 60, 80, (40, 60, 40), 60, 22, (1, .97, .92))
    p = bpy.data.lights.new("bulb", "POINT"); p.energy = 14; p.color = (1, .86, .66); p.shadow_soft_size = 16 * IN
    o = bpy.data.objects.new("bulb", p); o.location = ((TABLE_U0 + 40) * IN, -(TABLE_V0 + 18.5) * IN, 66 * IN); bpy.context.collection.objects.link(o)


def measure():
    """Pixel box (1536x1024, unoccluded) and real size of every group, plus an assert against SPEC."""
    f, k = CAM["f_px"], 1536 / CAM["w"]; rep = {}
    for g, obs in PARTS.items():
        P = [(o.matrix_world @ v.co) / IN for o in obs for v in o.data.vertices]
        u = [p.x for p in P]; v = [-p.y for p in P]; z = [p.z for p in P]
        s = [f / (CAM["v"] - b) for b in v if CAM["v"] - b > 2]
        if len(s) < len(v): continue
        x = [k * (CAM["vx"] + (a - CAM["u"]) * q) for a, q in zip(u, s)]; y = [k * CAM["vy"] - k * (c - CAM["z"]) * q for c, q in zip(z, s)]
        rep[g] = dict(size=[round(max(q) - min(q), 2) for q in (u, v, z)], u=[round(min(u), 2), round(max(u), 2)], v=[round(min(v), 2), round(max(v), 2)],
                      box=[round(min(x), 1), round(min(y), 1), round(max(x), 1), round(max(y), 1)])
    for g in ("tate", "bookcase", "table", "rug", "lantern"):
        sz, sp = rep[g]["size"], SPEC[g]; print(f"{g:9s} model {sz}  spec {sp}")
    (OUT / "boxes.json").write_text(json.dumps(rep, indent=1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--passes", default="color,depth,mask"); ap.add_argument("--spiral", action="store_true", help="add the approximate stair (default: the stair is cut from photo p08 in comp.py)"); ap.add_argument("--samples", type=int, default=96); ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args(sys.argv[1:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    room(); (spiral() if a.spiral else None); tate(); bookcase(); table(); rest(); light(); camera(a.scale)
    bpy.context.view_layer.update(); measure()
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.use_denoising = True
    sc.render.image_settings.file_format = "PNG"; bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "dining.blend"))
    for ps in a.passes.split(","):
        vl = sc.view_layers[0]; vl.material_override = None; sc.cycles.samples = a.samples
        sc.view_settings.view_transform = "AgX" if ps == "color" else "Raw"; sc.cycles.use_denoising = ps == "color"
        sc.view_settings.exposure = .4 if ps == "color" else 0
        if ps == "depth":
            m = bpy.data.materials.new("depth"); m.use_nodes = True; n, l = m.node_tree.nodes, m.node_tree.links; n.clear()
            cd = n.new("ShaderNodeCameraData"); mr = n.new("ShaderNodeMapRange"); em = n.new("ShaderNodeEmission"); o = n.new("ShaderNodeOutputMaterial")
            mr.inputs[1].default_value, mr.inputs[2].default_value, mr.inputs[3].default_value, mr.inputs[4].default_value = .6, 4.6, 1, 0
            l.new(cd.outputs["View Z Depth"], mr.inputs[0]); l.new(mr.outputs[0], em.inputs[0]); l.new(em.outputs[0], o.inputs[0]); vl.material_override = m; sc.cycles.samples = 4
        if ps == "mask":
            vl.material_override = None; sc.cycles.samples = 1; sc.cycles.pixel_filter_type = "BOX"; sc.cycles.filter_width = .01
            for i, (g, obs) in enumerate(sorted(PARTS.items())):
                m = bpy.data.materials.new("id" + g); m.use_nodes = True; n, l = m.node_tree.nodes, m.node_tree.links; n.clear()
                em = n.new("ShaderNodeEmission"); em.inputs[0].default_value = ((i + 1) * 8 / 255,) * 3 + (1,); o = n.new("ShaderNodeOutputMaterial"); l.new(em.outputs[0], o.inputs[0])
                for ob in obs: ob.data.materials.clear(); ob.data.materials.append(m)
            (OUT / "mask_ids.json").write_text(json.dumps({g: (i + 1) * 8 for i, g in enumerate(sorted(PARTS))}))
        sc.render.filepath = str(OUT / f"{ps}.png"); bpy.ops.render.render(write_still=True); print("rendered", ps, flush=True)


if __name__ == "__main__":
    main()
