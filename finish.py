#!/usr/bin/env python3
"""Photoreal pass: Blender guide (geometry authority) + listing photo p08 (same camera) + product refs -> gpt-image-2.5-sunburst.
usage: python3 finish.py <name> [--n 2]   -> out/ai_<name>_<i>.png"""
import argparse, pathlib, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
H = pathlib.Path(__file__).resolve().parent
from openai_edit import edit2, load_key
PROMPT = (
 "Turn the FIRST image into a photorealistic editorial interior photograph. The FIRST image is an exact to-scale 3D model "
 "render from a surveyed room: it is the ONLY authority for the camera, perspective, and the position, outline and SIZE of "
 "every object. Every edge must stay on the same pixels: do not move, resize, widen, heighten, lower, rotate, add or remove "
 "anything; do not re-crop or change the lens. Furniture that is partly hidden stays partly hidden (the low walnut console behind "
 "the table really does show only as a thin strip above the table top). Only replace the flat 3D materials and light with real "
 "ones and add fine real-world detail inside the existing outlines. "
 "The SECOND image is a photo of the same empty-of-our-furniture room from the same camera: copy its real architecture "
 "details and finishes (coved plaster corners, crown, plate rail, panelled white wainscot, casings, double-hung window, the half-glass kitchen door "
 "with the pet flap, oak strip floor with dark inlay border, the black steel spiral stair at right) but NOT its furniture, plants, art, light fixture or "
 "watermark. The living room seen on the left stays simple and bright: white wall with wainscot, oak floor, no furniture. "
 "Materials: console and tall open bookcase in solid walnut exactly like the THIRD and FOURTH images; table in honey-amber pine with straight grain and "
 "a few knots; six Danish walnut chairs with plain olive-green wool seat pads; plain rust-terracotta low-pile wool rug; big round "
 "white paper lantern with fine ribs, softly lit; cream ceramic lamp with linen shade, lit; Kentia palm (real, fuller fronds, same height and spread) in a cream "
 "planter, but the planter is only 15 in tall and COMPLETELY HIDDEN behind the table, so no part of any pot is visible: only stems and fronds show, with the same spread as in the FIRST image; stoneware bowl. The round sun tube in the ceiling is a real skylight, keep it. The bookcase keeps exactly its outline: 22 in wide, its left posts on the same pixels. Far wall wallpaper: the William Morris Pimpernel-style paper already on the model wall, kept at "
 "EXACTLY the same pattern scale and flower positions, crisp matte print. Walls above the wainscot light warm greige (#CFC9BE); trim, wainscot, "
 "plate rail and ceiling white. Warm hidden LED glow in the ceiling cove, soft daylight from the window. No brass or gold, no "
 "pouf, no picture light, no extra decor, no people, no text.")
def jpg(src, name):
    o = H / "out" / f"_in_{name}.jpg"
    subprocess.run(["magick", str(src), "-quality", "95", str(o)], check=True); return o
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("--n", type=int, default=2); a = ap.parse_args()
    imgs = [jpg(H / "out/guide.png", "guide"), jpg(H / "refs/p08.jpg", "p08"), jpg(H / "refs/tate_front.jpg", "tate"), jpg(H / "refs/tate_bookcase.jpg", "book")]
    key = load_key("OPENAI_API_KEY") or sys.exit("no key")
    def go(i):
        try: (H / "out" / f"ai_{a.name}_{i}.png").write_bytes(edit2(key, imgs, PROMPT)); print("done", i, flush=True)
        except Exception as e: print("failed", i, str(e)[:300], flush=True)
    with ThreadPoolExecutor(2) as ex: list(ex.map(go, range(1, a.n + 1)))
