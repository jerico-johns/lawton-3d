#!/usr/bin/env python3
"""3932 Lawton main floor as a walkable model (Nov 24 2026). Same inch frame as build_dining.py (u 0 = dining/living wall,
v 0 = west wall, z up). Walls traced from plan/main_big.jpg (25.76 px/ft, +-3 in); dining openings use the p08 photo fit.
Cycles bakes irradiance per vertex; writes out/house.json for build_walk.py.   .venv/bin/python build_house.py [--samples 128]"""
import argparse, base64, json, math, sys
import numpy as np, bpy
import build_dining as D
from build_dining import IN, box, rod, lathe, prism, mat, PARTS, MATS
K = 12 / 25.76
X = lambda p: (p - 881) * K
Y = lambda p: (p - 157) * K
CEIL, RAIL, PLATE = 109.0, D.RAIL, D.PLATE
ROOMS = {"Living": (458, 157, 866, 470), "Dining": (881, 157, 1177, 470), "Kitchen": (1189, 258, 1483, 472), "Hall": (770, 485, 1050, 573),
         "Front bedroom": (458, 485, 757, 776), "Closet": (770, 632, 850, 776), "Bath": (866, 587, 1050, 727), "Primary": (1063, 485, 1366, 776),
         "Walk-in": (1379, 485, 1483, 676)}
PANELLED = ("Living", "Dining")
# axis, across0, across1, along0, along1, [(a, b, z0, z1)]   (plan px)
W = [("h",144,157,445,1190,[]), ("h",470,485,445,1379,[(785,853,0,82),(973,1043,0,82)]), ("h",472,485,1379,1495,[]),
     ("h",245,258,1189,1495,[(1198,1265,-1,80)]), ("h",573,587,770,1063,[(912,978,0,80)]), ("h",622,632,770,850,[]),
     ("h",776,790,445,866,[(662,722,60,80)]), ("h",727,740,850,1063,[(912,978,44,80)]), ("h",776,790,1050,1379,[(1180,1246,66,84)]),
     ("h",676,690,1379,1495,[(1415,1440,44,80)]),
     ("v",445,458,157,776,[(180,215,30,82),(228,312,30,82),(318,347,30,82),(393,462,-1,80),(550,597,30,82),(602,668,30,82),(680,718,30,82)]),
     ("v",866,881,157,470,[(257.5,386.3,0,86)]), ("v",1177,1189,157,472,[(187,239.7,32,84),(273.8,346,0,84)]),
     ("v",757,770,485,776,[(497,562,0,80),(697,765,0,80)]), ("v",850,866,587,776,[]), ("v",1050,1063,485,776,[(497,563,0,80)]),
     ("v",1366,1379,485,776,[(590,655,0,80),(700,765,30,82)]), ("v",1483,1495,258,676,[(350,460,40,80)])]
SOLID = []                                  # collision rects (u0, v0, u1, v1)

def ext(*m): return mat(*m)
def inroom(u, v):
    for n, (a, b, c, d) in ROOMS.items():
        if X(a) - .1 <= u <= X(c) + .1 and Y(b) - .1 <= v <= Y(d) + .1: return n
    return None

def shell():
    wall = mat("greige", (207, 201, 190), .8); white = mat("trim", (240, 239, 235), .5); oak = mat("oak", (168, 114, 70), .4); ceil = mat("ceiling", (245, 244, 241), .9)
    def along(ax, c0, c1, a, b, z, h, m, g="wall"):
        return box(g, m, a, c0, z, b - a, c1 - c0, h) if ax == "h" else box(g, m, c0, a, z, c1 - c0, b - a, h)
    for ax, p0, p1, q0, q1, ops in W:
        AC, AL = (Y, X) if ax == "h" else (X, Y); c0, c1 = AC(p0), AC(p1); cur = AL(q0); end = AL(q1); segs = []
        so = sorted((AL(a), AL(b), z0, z1) for a, b, z0, z1 in ops)
        for k, (a, b, z0, z1) in enumerate(so):
            segs.append((cur, a)); cur = b
            cl = min(4.2, (a - so[k - 1][1]) / 2 - .05) if k else 4.2; cr = min(4.2, (so[k + 1][0] - b) / 2 - .05) if k + 1 < len(so) else 4.2
            along(ax, c0, c1, a, b, z1, CEIL - z1, wall)
            if z0 > 0: along(ax, c0, c1, a, b, 0, z0, wall)
            if z0 <= 0 and z0 > -1:
                w0 = (a, c0, b, c1) if ax == "h" else (c0, a, c1, b); box("floor", oak, w0[0], w0[1], -1, w0[2] - w0[0], w0[3] - w0[1], 1)
            if z0 != 0: SOLID.append((a, c0, b, c1) if ax == "h" else (c0, a, c1, b))
            for side, t in ((c0, -.9), (c1, .9)):                      # casings on both faces
                f0, f1 = min(side, side + t), max(side, side + t)
                for e0, e1 in ((a - cl, a), (b, b + cr)): along(ax, f0, f1, e0, e1, max(z0, 0), z1 - max(z0, 0), white, "trim")
                along(ax, f0 - .1, f1 + .1, a - cl - (.8 if cl > 4 else 0), b + cr + (.8 if cr > 4 else 0), z1, 5, white, "trim")
                if z0 > 0: along(ax, f0 - .2, f1 + .2, a - cl - (.8 if cl > 4 else 0), b + cr + (.8 if cr > 4 else 0), z0 - 2, 2, white, "trim")
            if z0 > 0 and b - a > 14:                                   # meeting rail
                m = (c0 + c1) / 2; along(ax, m - .7, m + .7, a, b, (z0 + z1) / 2, 1.6, white, "trim")
                for e in (a, b - 1.4): along(ax, m - .7, m + .7, e, e + 1.4, z0, z1 - z0, white, "trim")
            if z0 == -1:                                                # exterior door leaf, half glass
                m = (c0 + c1) / 2; door = mat("doorY", (206, 158, 52), .5) if ax == "v" else white
                along(ax, m - .9, m + .9, a, b, 0, 42, door, "trim"); along(ax, m - .9, m + .9, a, b, 74, 6, door, "trim")
                for e0, e1 in ((a, a + 5), (b - 5, b)): along(ax, m - .9, m + .9, e0, e1, 42, 32, door, "trim")
                along(ax, m - .1, m + .1, a + 5, b - 5, 42, 32, mat("glass", (214, 226, 234), .2, emit=1.0), "trim")
        segs.append((cur, end))
        for a, b in segs:
            if b - a < .5: continue
            along(ax, c0, c1, a, b, 0, CEIL, wall); SOLID.append((a, c0, b, c1) if ax == "h" else (c0, a, c1, b))
        # skirting / wainscot on each face, room by room
        full = segs + [(AL(a), AL(b)) for a, b, z0, z1 in ops if z0 > 0]
        for side, sg in ((c0, -1), (c1, 1)):
            for n, (ra, rb, rc, rd) in ROOMS.items():
                lo, hi = (X(ra), X(rc)) if ax == "h" else (Y(rb), Y(rd)); f = side + sg * .5
                o = (Y(rb), Y(rd)) if ax == "h" else (X(ra), X(rc))
                if not (o[0] - .6 <= f <= o[1] + .6): continue
                ra0, rb0 = max(lo, AL(q0)), min(hi, AL(q1))
                if n in ("Hall", "Front bedroom", "Primary") and rb0 - ra0 > 14: along(ax, min(side, side + sg * .9), max(side, side + sg * .9), ra0, rb0, 92, 2, white, "trim")
                for a, b in full:
                    a, b = max(a, lo), min(b, hi)
                    if b - a < 1: continue
                    win = any(AL(x0) <= (a + b) / 2 <= AL(x1) and z0 > 0 for x0, x1, z0, z1 in ops)
                    put = lambda t, z, h, g="trim": along(ax, min(side, side + sg * t), max(side, side + sg * t), a, b, z, h, white, g)
                    put(.8, 0, 7)
                    if n in PANELLED:
                        put(.3, 7, RAIL - 8.5); put(1.5, RAIL - 1.6, 1.6)
                        if not win and b - a > 14: put(2.2, PLATE, 2.6)
    tile = mat("tilefloor", (214, 212, 206), .4)
    for n, (a, b, c, d) in ROOMS.items():
        u0, v0, w, h = X(a), Y(b), X(c) - X(a), Y(d) - Y(b)
        box("floor", tile if n == "Bath" else oak, u0, v0, -1, w, h, 1); box("ceil", ceil, u0, v0, CEIL, w, h, 1)
    # dining: Morris paper on the west wall, tray ledge + cove glow, inlay
    n = int((D.HERE / "tex/tile.txt").read_text())
    box("shell", mat("morris", (74, 84, 66), .9), .3, 0, RAIL, 137, .25, PLATE - RAIL)
    for u, v, w, d in ((0, 0, 138, 16), (0, 131, 138, 16), (0, 16.6, 16, 114), (122, 16.6, 16, 114)): box("ceil", white, u, v, 100, w, d, 2.2)
    led = mat("led", (255, 196, 120), .5, emit=4)
    for u, v, w, d in ((6, 12, 126, 1.5), (6, 134, 126, 1.5), (12, 14, 1.5, 119), (124.5, 14, 1.5, 119)): box("ceil", led, u, v, 102.6, w, d, .6)
    ink = mat("inlay", (84, 46, 28), .4)
    for u, v, w, d in ((11, 11, 116, 1), (11, 135, 116, 1), (11, 12, 1, 123), (126, 12, 1, 123)): box("floor", ink, u, v, 0, w, d, .04)

def furn(g, m, u, v, z, w, d, h, solid=False):
    if solid: SOLID.append((u, v, u + w, v + d))
    return box(g, m, u, v, z, w, d, h)

def soft(m, c, size, e=.3, yaw=0, pitch=0, nu=24, nv=12):
    """Rounded, slightly stuffed block (superellipsoid): c = centre (u, v, z), size = full w, d, h; yaw/pitch in degrees."""
    f = lambda w, k: math.copysign(abs(w) ** k, w); a, b, h = (x / 2 for x in size); cy, sy, cp, sp = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    vs, fs = [], []
    for j in range(nv + 1):
        t = -math.pi / 2 + math.pi * j / nv
        for i in range(nu):
            q = 2 * math.pi * i / nu; ct = f(math.cos(t), e)
            x, y, z = a * ct * f(math.cos(q), e), b * ct * f(math.sin(q), e), h * f(math.sin(t), e)
            y, z = y * cp - z * sp, y * sp + z * cp; x, y = x * cy - y * sy, x * sy + y * cy
            vs.append(((c[0] + x) * IN, -(c[1] + y) * IN, (c[2] + z) * IN))
    for j in range(nv):
        for i in range(nu): fs.append(((j + 1) * nu + i, (j + 1) * nu + (i + 1) % nu, j * nu + (i + 1) % nu, j * nu + i))
    me = bpy.data.meshes.new("soft"); me.from_pydata(vs, [], fs); me.update(); return D.add("soft", me, m)

# Costco Aiden & Ivy Sydney modular, Cream (item 1987855). Costco's drawing: 40.1 deep, corner and arm modules 40.1 wide, armless 37.4,
# 36.2 to the pillow tops, arms 25.5, seat 20, seat depth 26.7. Arm and back-frame thickness are read off the photo (about 7 and 8 in).
SYD = dict(d=40.1, arm=40.1, less=37.4, corner=40.1, h=36.2, armh=25.5, seat=20, ta=7, tb=8, ott=(37.4, 21.2))
def sydney(u0=None, v0=2.0):
    q = SYD; cr = mat("sydneycream", (233, 227, 215), .95); L = (X(458) + 2) if u0 is None else u0; g = .25; d = q["d"]
    def module(o, w, side, arm=0, corner=False):
        """side 'w': back on the lot-line wall, o = start u; side 's': back on the street wall, o = start v. arm = 1 at the far end."""
        T = (lambda a, b: (L + a, v0 + b)) if side == "w" else (lambda a, b: (L + b, v0 + a))
        S_ = (lambda a, b, h: (a, b, h)) if side == "w" else (lambda a, b, h: (b, a, h))
        blk = lambda a, b, z, wa, db, h, e=.14: soft(cr, (*T(a + wa / 2, b + db / 2), z + h / 2), S_(wa, db, h), e)
        blk(o + g, 0, .8, w - 2 * g, d, 12.4); blk(o + g, 0, .8, w - 2 * g, q["tb"], q["armh"] - .8)            # base, back frame
        x0, x1 = o + g, o + w - g
        if arm: blk(o + w - q["ta"] - g, 0, .8, q["ta"], d, q["armh"] - .8); x1 -= q["ta"]
        if corner: blk(o + g, 0, .8, q["tb"], d, q["armh"] - .8); x0 += q["tb"]
        blk(x0, q["tb"], 12.2, x1 - x0, d - q["tb"] + .4, q["seat"] - 12.2, .3)                                 # seat cushion
        def pillow(c, wd, yaw): soft(cr, c, (wd, 9, 18.5), .42, yaw, 14)
        yw = 0 if side == "w" else -90
        m = (x0 + x1) / 2; cu, cv = T(m, q["tb"] + 5.2); pillow((cu, cv, q["h"] - 9.4), x1 - x0 - .6, yw)
        if arm:
            cu, cv = T(x1 - 4.5, q["tb"] + 18); soft(cr, (cu, cv, 27.5), (20, 7, 15), .45, 90 if side == "w" else 0, 12 if side == "w" else -12)
        return o + w
    e = module(0, q["corner"], "w", corner=True); e = module(e, q["less"], "w"); e = module(e, q["less"], "w"); wall = module(e, q["arm"], "w", arm=1)
    win = module(q["corner"], q["arm"], "s", arm=1)
    soft(cr, (L + q["tb"] + 6, v0 + 23, q["h"] - 9.4), (27, 9, 18.5), .42, -90, 14)                            # corner's second back pillow
    ot, oh = q["ott"]; a0, b0 = L + wall - ot, v0 + d + .6                                                      # ottoman as a chaise at the end seat
    soft(cr, (a0 + ot / 2, b0 + ot / 2, 7.2), (ot - .4, ot - .4, 12.8), .14); soft(cr, (a0 + ot / 2, b0 + ot / 2, 12.6 + (oh - 12.6) / 2), (ot, ot, oh - 12.6), .3)
    SOLID.append((a0, b0, a0 + ot, b0 + ot))
    SOLID.extend([(L, v0, L + wall, v0 + d), (L, v0, L + d, v0 + win)]); print(f"Sydney: window leg {win:.1f} in, wall leg {wall:.1f} in")

def rooms():
    wal = mat("walnut", (104, 68, 42), .5); white = mat("trim", (0,)*3); steel = mat("steel", (150, 150, 150), .4); quartz = mat("quartz", (236, 235, 232), .3)
    cab = mat("cab", (232, 230, 226), .5); linen = mat("linen", (228, 221, 208), .9); olive = mat("sofaolive", (104, 106, 68), .95); blk = mat("black", (18, 18, 19), .5); shade = mat("shade", (250, 226, 180), .9, emit=1.6)
    sydney()
    F = X(458)
    furn("living", mat("rugL", (186, 158, 122), 1), F + 40, 40, .05, 108, 84, .4); furn("living", wal, F + 58, 70, 13, 50, 30, 2.5, True)     # placeholder table, 50 x 30
    for a in (61, 102):
        for b in (73, 94): furn("living", wal, F + a, b, 0, 3, 3, 13)
    furn("living", blk, F + 57, Y(470) - 2.4, 40, 66, 2, 37)
    # KITCHEN
    for a, b, c, d in ((1433, 258, 1483, 472), (1398, 420, 1433, 472), (1265, 420, 1333, 472)):
        furn("kitchen", cab, X(a), Y(b), 4, X(c) - X(a), Y(d) - Y(b), 30.5, True); furn("kitchen", quartz, X(a) - .8, Y(b) - .8, 34.5, X(c) - X(a) + .8, Y(d) - Y(b) + .8, 1.5)
    furn("kitchen", steel, X(1333), Y(418), 0, X(1398) - X(1333), Y(472) - Y(418), 36, True); furn("kitchen", blk, X(1335), Y(422), 36, 28, 20, 1.2); furn("kitchen", blk, X(1340), Y(417), 10, 25, .5, 15)
    furn("kitchen", steel, X(1192), Y(416), 0, 32, 26, 70, True); furn("kitchen", steel, X(1436), Y(380), 35.7, 18, 28, .5)
    for a, b in ((1225, 1333), (1398, 1470)): furn("kitchen", cab, X(a), Y(472) - 13, 54 if a > 1200 else 72, X(b) - X(a), 13, 36)
    furn("kitchen", cab, X(1333), Y(472) - 13, 70, X(1398) - X(1333), 13, 20); furn("kitchen", steel, X(1333), Y(472) - 18, 66, X(1398) - X(1333), 18, 4)
    for z in (54, 66, 78): furn("kitchen", wal, X(1483) - 10, Y(262), z, 10, 40, 1.4)
    # BATH
    furn("bath", quartz, X(990), Y(595), 0, X(1045) - X(990), Y(722) - Y(595), 4, True)
    for a in ((990, 595, 1045, 601), (990, 716, 1045, 722), (990, 601, 996, 716), (1039, 601, 1045, 716)): furn("bath", quartz, X(a[0]), Y(a[1]), 4, X(a[2]) - X(a[0]), Y(a[3]) - Y(a[1]), 16)
    furn("bath", mat("vanity", (184, 142, 98), .5), X(868), Y(600), 6, 18, 24, 26, True); furn("bath", quartz, X(868), Y(599), 32, 19, 25, 2)
    furn("bath", quartz, X(868), Y(680), 14, 8, 18, 17, True); lathe("bath", quartz, X(868) + 17, Y(680) + 9, [(5, 0), (6, 8), (8.5, 15), (8.5, 16.5), (.1, 16.5)]); SOLID.append((X(868), Y(680), X(868) + 26, Y(680) + 18))
    # PRIMARY: king under the side window (layout A), 66 in dresser on the kitchen wall
    P, Q = X(1063), Y(776); c = P + 66.6
    furn("primary", mat("wood", (150, 108, 70), .5), c - 40, Q - 84, 4, 80, 83, 9, True); furn("primary", linen, c - 38, Q - 83, 13, 76, 80, 12); furn("primary", mat("ochre", (186, 132, 56), .95), c - 38.5, Q - 83.5, 14, 77, 46, 12)
    furn("primary", mat("ochre", (0,)*3), c - 40, Q - 4, 10, 80, 4, 36)
    for s in (-34, 4): furn("primary", white, c + s, Q - 22, 25, 30, 16, 6)
    for s in (-62, 42): furn("primary", wal, c + s, Q - 17, 0, 20, 16, 24, True); lathe("primary", shade, c + s + 10, Q - 9, [(6, 33), (5, 42)]); lathe("primary", linen, c + s + 10, Q - 9, [(3, 24), (3.6, 28), (1, 33)])
    furn("primary", wal, P + 60, Y(485), 6, 66, 18, 26, True); furn("primary", mat("rugP", (120, 122, 96), 1), c - 60, Q - 100, .05, 120, 60, .4)
    # FRONT ROOM: library / office (Oct 14 plan): 84 in sleeper on the hall wall, 60 x 24 desk, shelves
    G, H = X(458), Y(485); so = mat("sleeper", (112, 84, 60), .95)
    furn("office", so, G + 23, H + 1, 4, 84, 38, 13, True); furn("office", so, G + 23, H + 1, 17, 84, 9, 15)
    for u in (23, 99): furn("office", so, G + u, H + 10, 17, 8, 29, 7)
    for i in (0, 1): furn("office", so, G + 32 + 34 * i, H + 10, 17, 33, 28, 4)
    furn("office", wal, G + 1, H + 1, 0, 20, 13, 90, True); furn("office", wal, G + 23, H + 1, 60, 84, 11, 1.4); furn("office", wal, G + 23, H + 1, 75, 84, 11, 1.4)
    cols = [(150, 62, 44), (66, 84, 96), (196, 150, 70), (90, 98, 60), (222, 212, 190)]
    for z in (61.4, 76.4):
        for i in range(24): furn("office", mat(f"bk{i%5}", cols[i % 5], .9), G + 25 + 3.2 * i, H + 2, z, 2.6, 7, 8 + (i * 7 % 4))
    furn("office", wal, G + 2, Y(776) - 26, 28.5, 60, 24, 1.5, True)
    for a in (4, 57): 
        for b in (25, 6): furn("office", wal, G + a, Y(776) - b, 0, 2, 2, 28.5)
    furn("office", mat("deskchair", (176, 92, 44), .7), G + 22, Y(776) - 46, 18, 20, 19, 3, True); furn("office", mat("deskchair", (0,)*3), G + 22, Y(776) - 48, 21, 20, 3, 16); rod("office", blk, (G + 32, Y(776) - 36, 0), (G + 32, Y(776) - 36, 18), 1.4)
    for a in (0, 72, 144, 216, 288): rod("office", blk, (G + 32, Y(776) - 36, 2.5), (G + 32 + 11 * math.cos(math.radians(a)), Y(776) - 36 + 11 * math.sin(math.radians(a)), 1), .8)

def dining():
    D.tate(); D.bookcase(); D.table(); D.rest()
    D.SPIRAL = (116.0, 124.0, 22.0); blk = mat("black", (18, 18, 19), .5); u, v, r = D.SPIRAL
    rod("spiral", blk, (u, v, 0), (u, v, CEIL), 1.6, n=20)
    for k in range(12):
        a0 = math.radians(60 - 30 * k); z = 8.6 * (k + 1); q = lambda R, t: (u + R * math.cos(a0 + t), v + R * math.sin(a0 + t))
        ring = [q(1.6, -.2), q(r, -.29), q(r, .29), q(1.6, .2)]
        prism("spiral", blk, [(a, b, z) for a, b in ring], [(a, b, z + 1.5) for a, b in ring]); e = q(r - 1, 0)
        if z + 34 < CEIL: rod("spiral", blk, (*e, z), (*e, z + 34), .6)
    for g, w in (("tate", None), ("bookcase", None), ("table", None)):
        pass
    SOLID.extend([(D.TATE_U0, 0, D.TATE_U0 + 64.5, 16), (D.BOOK_U0, 0, D.BOOK_U0 + 22, 16), (D.TABLE_U0, D.TABLE_V0, D.TABLE_U0 + 80, D.TABLE_V0 + 37), (u - 18, v - 18, u + 18, v + 18), (112, 5, 128, 21)])

def lights():
    sc = bpy.context.scene; w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (.82, .91, 1, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 2.2
    s = bpy.data.lights.new("sun", "SUN"); s.energy = 5; s.angle = .02; s.color = (1, .93, .82); o = bpy.data.objects.new("sun", s); bpy.context.collection.objects.link(o)
    from mathutils import Vector
    o.rotation_euler = Vector((.82, .28, -.55)).to_track_quat("-Z", "Y").to_euler()
    for n, (a, b, c, d) in ROOMS.items():
        ar = (X(c) - X(a)) * (Y(d) - Y(b)) / 20000
        for k, off in enumerate((-.25, .25) if X(c) - X(a) > 120 else (0,)):      # big soft bulbs light ceiling and walls evenly
            l = bpy.data.lights.new(f"{n}{k}", "POINT"); l.energy = 26 * ar ** .75 / (2 if X(c) - X(a) > 120 else 1) + 2; l.color = (1, .95, .88); l.shadow_soft_size = 22 * IN
            o = bpy.data.objects.new(f"{n}{k}", l); o.location = (((X(a) + X(c)) / 2 + off * (X(c) - X(a))) * IN, -(Y(b) + Y(d)) / 2 * IN, 76 * IN); bpy.context.collection.objects.link(o)

def bake(samples, cell=8.0):
    """Flatten every quad into a grid, bake on an inset copy (so verts touching other walls do not go black)."""
    P, PI, F, FM, FG = [], [], [], [], []; names = []; gs = []; grids = []; SR = []
    BB = []
    for g in ("wall", "floor", "ceil"):
        for o in PARTS.get(g, []):
            c = np.array([v.co[:] for v in o.data.vertices]) / IN; BB.append((c.min(0), c.max(0)))
    LO = np.array([b[0] for b in BB]) + .04; HI = np.array([b[1] for b in BB]) - .04
    CUT = [sorted(set(round(float(c), 3) for c in list(np.arange(-240, 320, cell)) + [x for b in BB for x in (b[0][k], b[1][k])])) for k in range(3)]
    def cuts(a, b, k):
        lo, hi = min(a, b), max(a, b); L = [lo]
        for c in CUT[k]:
            if L[-1] + .6 < c < hi - .6: L.append(c)
        L.append(hi); return [(x - a) / (b - a) for x in (L if b > a else L[::-1])]
    seen = {}
    for obs in PARTS.values():
        for o in obs:
            for p in o.data.polygons:
                if len(p.vertices) == 4: k = tuple(np.round(np.array(p.center[:]) / IN, 1)); seen.setdefault(k, []).append((tuple(p.normal), p.area))
    def paired(p):
        n = np.array(p.normal[:]); return any(np.dot(n, m) < -.98 and abs(ar - p.area) < .05 * p.area for m, ar in seen.get(tuple(np.round(np.array(p.center[:]) / IN, 1)), []))
    hidden = lambda q: bool(np.any(np.all((q > LO) & (q < HI), axis=1)))
    for g, obs in PARTS.items():
        for o in obs:
            me = o.data; m = me.materials[0].name; PG = len(P)
            if m not in names: names.append(m)
            if g not in gs: gs.append(g)
            for p in me.polygons:
                co = np.array([me.vertices[i].co[:] for i in p.vertices]) / IN; nrm = np.array(p.normal[:]); cen = co.mean(0)
                if len(co) == 4 and paired(p): continue
                if len(co) == 4:
                    e1, e2 = co[1] - co[0], co[3] - co[0]; k1, k2 = int(np.argmax(abs(e1))), int(np.argmax(abs(e2)))
                    axis = k1 != k2 and abs(e1).sum() - abs(e1[k1]) < .01 and abs(e2).sum() - abs(e2[k2]) < .01 and np.linalg.norm(co[2] - co[0] - e1 - e2) < .01
                    if axis: ss, tt = cuts(co[0][k1], co[1][k1], k1), cuts(co[0][k2], co[3][k2], k2)
                    else:
                        a_ = max(1, int(math.ceil(max(np.linalg.norm(e1), np.linalg.norm(co[2] - co[3])) / cell))); b_ = max(1, int(math.ceil(max(np.linalg.norm(e2), np.linalg.norm(co[2] - co[1])) / cell)))
                        ss, tt = [x / a_ for x in range(a_ + 1)], [x / b_ for x in range(b_ + 1)]
                    nx, ny, base = len(ss) - 1, len(tt) - 1, len(P); N1 = len(PI)
                    for t in tt:
                        for x in ss: q = (1-x)*(1-t)*co[0] + x*(1-t)*co[1] + x*t*co[2] + (1-x)*t*co[3]; P.append(q); PI.append((cen, nrm, q))
                    grids.append((base, nx, ny))
                    for j in range(ny):
                        for i in range(nx):
                            a = base + j * (nx + 1) + i
                            if hidden((P[a] + P[a + 1] + P[a + nx + 2] + P[a + nx + 1]) / 4 + nrm * .15): continue
                            F.append((a, a + 1, a + nx + 2, a + nx + 1)); FM.append(names.index(m)); FG.append(gs.index(g))
                else:
                    base = len(P)
                    for q in co: P.append(q); PI.append((cen, nrm, q))
                    for k in range(1, len(co) - 1): F.append((base, base + k, base + k + 1)); FM.append(names.index(m)); FG.append(gs.index(g))
            if g == "soft": SR.append((PG, len(P)))
    inset = []
    for cen, nrm, q in PI:
        d = cen - q; L = np.linalg.norm(d); inset.append((q + d * (min(1.6, L * .3) / max(L, 1e-6)) + nrm * .25) * IN)
    me = bpy.data.meshes.new("probe"); me.from_pydata([tuple(p) for p in inset], [], F); me.update(); ob = bpy.data.objects.new("probe", me); bpy.context.collection.objects.link(ob)
    m = bpy.data.materials.new("probe"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.8,) * 3 + (1,); m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1; me.materials.append(m)
    ca = me.color_attributes.new("bake", "FLOAT_COLOR", "POINT"); me.color_attributes.active_color = ca; me.color_attributes.render_color_index = 0
    for k in ("visible_diffuse", "visible_glossy", "visible_shadow", "visible_transmission", "visible_camera"): setattr(ob, k, False)
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = samples; sc.cycles.diffuse_bounces = 5; sc.render.bake.target = "VERTEX_COLORS"
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, target="VERTEX_COLORS")
    col = np.zeros(len(P) * 4, np.float32); ca = ob.data.color_attributes["bake"]; ca.data.foreach_get("color", col); col = col.reshape(-1, 4)[:, :3]
    used = np.zeros(len(P), bool); used[[i for f in F for i in f]] = True
    for base, nx, ny in grids:                  # light 3x3 blur inside each face to take out sampling noise
        if nx < 2 or ny < 2: continue
        idx = base + np.arange((nx + 1) * (ny + 1)).reshape(ny + 1, nx + 1); g = col[idx].copy(); w = used[idx].astype(np.float32)[..., None]; num = np.zeros_like(g); den = np.zeros_like(w)
        gp, wp = np.pad(g * w, ((1, 1), (1, 1), (0, 0))), np.pad(w, ((1, 1), (1, 1), (0, 0)))
        for dy in (0, 1, 2):
            for dx in (0, 1, 2):
                k = (2 - abs(dy - 1)) * (2 - abs(dx - 1)); num += k * gp[dy:dy + ny + 1, dx:dx + nx + 1]; den += k * wp[dy:dy + ny + 1, dx:dx + nx + 1]
        col[idx] = num / np.maximum(den, 1e-6)
    SOFT = np.zeros(len(P), bool)
    for a, b in SR: SOFT[a:b] = True
    key = {}                                    # weld light across boxes: same point + same facing share one value
    for i in np.where(used)[0]: key.setdefault((*np.round(P[i], 1), *(() if SOFT[i] else np.round(PI[i][1], 1))), []).append(i)
    for v in key.values():
        if len(v) > 1:
            g = [i for i in v if col[i].mean() > .012]; 
            if g: col[v] = col[g].mean(0)
    for base, nx, ny in grids:                  # fill unlit vertices (inside another box) from lit neighbours
        idx = base + np.arange((nx + 1) * (ny + 1)).reshape(ny + 1, nx + 1); ok = used[idx] & (col[idx].mean(2) > .012)
        for _ in range(12):
            if ok.all() or not ok.any(): break
            g = col[idx]; pk = np.pad(ok, 1); pg = np.pad(g * ok[..., None], ((1, 1), (1, 1), (0, 0))); num = np.zeros_like(g); den = np.zeros(ok.shape)
            for dy, dx in ((0, 1), (2, 1), (1, 0), (1, 2)): num += pg[dy:dy + ny + 1, dx:dx + nx + 1]; den += pk[dy:dy + ny + 1, dx:dx + nx + 1]
            f = ~ok & (den > 0); g[f] = num[f] / den[f][:, None]; col[idx] = g; ok = ok | f
        if not ok.any(): col[idx] = .1
    for i, (c_, n_, q_) in enumerate(PI):
        if n_[2] > .9 and q_[2] > 108.8: col[i] = .8
    print("verts", len(P), "faces", len(F), "irr mean", col.mean(0).round(3), "p5/p50/p99", np.percentile(col.mean(1), [5, 50, 99]).round(3))
    P = np.array(P, np.float32); out = []
    for mi, mn in enumerate(names):
        for gi, gn in enumerate(gs):
            fs = [f for f, a, b in zip(F, FM, FG) if a == mi and b == gi]
            if not fs: continue
            idx = []; remap = {}
            for f in fs:
                r = [remap.setdefault(i, len(remap)) for i in f]; idx += [r[0], r[1], r[2]] + ([r[0], r[2], r[3]] if len(r) == 4 else [])
            k = np.array(list(remap)); enc = (np.sqrt(np.clip(col[k], 0, 4) / 4) * 255 + .5).astype(np.uint8)
            b = mat_rgb(mn); out.append(dict(mat=mn, grp=gn, rgb=b[0], emit=b[1], n=len(k), p=base64.b64encode(np.round(P[k] * 40).astype(np.int16).tobytes()).decode(), c=base64.b64encode(enc.tobytes()).decode(), i=base64.b64encode(np.array(idx, np.uint32).tobytes()).decode()))
    return out

def mat_rgb(n):
    b = bpy.data.materials[n].node_tree.nodes["Principled BSDF"]
    return [round(x, 4) for x in b.inputs["Base Color"].default_value[:3]], round(b.inputs["Emission Strength"].default_value, 2) if b.inputs["Emission Color"].default_value[0] < .999 or n in ("shade", "paper", "led", "glass") and b.inputs["Emission Strength"].default_value else 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--samples", type=int, default=128); a = ap.parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    shell(); dining(); rooms(); lights(); bpy.context.view_layer.update()
    for (n, (p, q, r, s)) in ROOMS.items(): print(f"{n:14s} {(X(r)-X(p))/12:.2f} x {(Y(s)-Y(q))/12:.2f} ft")
    parts = bake(a.samples); bpy.ops.wm.save_as_mainfile(filepath=str(D.OUT / "house.blend"))
    J = dict(parts=parts, solid=[[round(x, 1) for x in r] for r in SOLID], rooms={n: [round(X(a), 1), round(Y(b), 1), round(X(c), 1), round(Y(d), 1)] for n, (a, b, c, d) in ROOMS.items()}, ceil=CEIL)
    (D.OUT / "house.json").write_text(json.dumps(J)); print("json MB", round((D.OUT / "house.json").stat().st_size / 1e6, 2), "parts", len(parts))
