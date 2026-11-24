#!/usr/bin/env python3
"""out/house.json + walk_template.html -> walk/index.html (publish this) and walk/test.html (open this locally)."""
import base64, pathlib
H = pathlib.Path(__file__).resolve().parent
(H / "walk").mkdir(exist_ok=True)
t = (H / "walk_template.html").read_text(encoding="utf-8").replace("/*HOUSE*/null", (H / "out/house.json").read_text(encoding="utf-8"))
t = t.replace("/*TILE*/", "data:image/jpeg;base64," + base64.b64encode((H / "tex/morris_tile_web.jpg").read_bytes()).decode())
(H / "walk/index.html").write_text(t, encoding="utf-8")
(H / "walk/test.html").write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body style="margin:0">' + t + "</body></html>", encoding="utf-8")
print("walk/index.html", round(len(t) / 1e6, 2), "MB")
