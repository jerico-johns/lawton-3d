#!/usr/bin/env python3
"""Can you walk into every room, and not out through a wall? Run after build_house.py."""
import json, pathlib, sys
H = json.loads((pathlib.Path(__file__).resolve().parent / "out/house.json").read_text()); S = H["solid"]
bad = lambda x, z: any(max(a - x, 0, x - c) ** 2 + max(b - z, 0, z - d) ** 2 < 49 for a, b, c, d in S)
start = (57, 139); seen = {start}; st = [start]
while st:
    x, z = st.pop()
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        q = (x + dx, z + dz)
        if q not in seen and -230 < q[0] < 310 and -40 < q[1] < 330 and not bad(*q): seen.add(q); st.append(q)
fail = bad(*start)
for n, (a, b, c, d) in H["rooms"].items():
    w = sum(a < x < c and b < z < d for x, z in seen) * 9 / 144; fail |= w < 4
    print(f"{n:14s} {(c - a) / 12:5.2f} x {(d - b) / 12:5.2f} ft   walkable {w:5.1f} sq ft" + ("   <- BLOCKED" if w < 4 else ""))
out = sum(x < -205 or z < -10 for x, z in seen); print("escaped outside:", out)
sys.exit(1 if fail or out else 0)
