# Lawton 3D: instructions for Claude

Two people edit this repo from separate machines. Explain things in plain words.

## Set up (first time)
1. Ask before downloading: `bpy` 4.5.16 (Blender as a Python package, about 190-375 MB by platform, from PyPI) and its small dependencies.
2. `uv venv --python 3.11 .venv`
3. `uv pip install --python .venv --only-binary :all: -r requirements.txt`
4. Run scripts with the venv's Python (`.venv/bin/python`, on Windows `.venv\Scripts\python`).

Blender 4.5 is deliberate: 5.x has no official Intel Mac build, and one of the two machines is an Intel Mac. Do not upgrade it.

## Working together
- Pull before starting (`git pull`). Make a branch, commit, and open a pull request. Do not push straight to `main`.
- Never commit `.env`, `.venv/`, `out/` or `walk/`. Never add financial, loan, purchase or insurance documents.
- No Claude co-author lines in commits.

## Rebuild the walkthrough
1. `python build_house.py --samples 96` for a quick noisy check; `--samples 600` for the final (about 6 minutes on a 2019 Intel Mac).
2. `python check.py` must pass: every room reachable, nothing escapes outside.
3. `python build_walk.py`, then open `walk/test.html`. Look at the rooms you changed before saying it is done.
4. Publish `walk/index.html` as an Artifact. To update the shared page instead of making a new one, pass its link as `url`
   (https://claude.ai/artifact/1cnWgZx1v3JWbLHXisWzKG; needs edit access from the page's Share menu, untested across accounts).

## Dining still (optional)
`build_dining.py` -> `comp.py` (cuts the real stair from the photo) -> `finish.py <name>` (the person's own OpenAI key, costs money: ask first)
-> `drift.py ai_<name>_1`. The image model drifts up to about 7% between runs: make a few, keep the best, and judge the wall corners by eye,
because `drift.py` only searches +-12 px.

## Coordinates
Inches. u = 0 at the dining/living wall, growing toward the kitchen and yard (north). v = 0 at the west lot-line wall, growing toward the
bedrooms (east). z is up. Blender x = u, y = -v. Walls are traced in pixels of `refs/main_big.jpg` at 25.76 px/ft (table `W` and `ROOMS` in
`build_house.py`). Furniture: `rooms()` and `dining()` in `build_house.py`; dining pieces and `SPEC` in `build_dining.py`. Add large items to
`SOLID` so people cannot walk through them.

## How accurate it is
Walls are traced, so about +-3 in. Assumed, not measured: 109 in ceilings everywhere, most door and window heights, sofa arm and back-frame thickness, chair
height 31 in, lantern 30 in. Ceilings outside the dining room are flat. The spiral is approximate. Daylight is one fixed setting, not a sun
study. Not modeled: attic, garage, yard, interior door leaves. When someone gives a tape measurement, use it and note it here.

## Design rules so far (ask before changing one)
- Keep the existing black spiral stair. Kitchen cabinets stay white. Dining walls are greige (#CFC9BE) with white wainscot and trim.
- Dining west wall: William Morris Pimpernel-style paper (20.5 in roll, 17.9 in repeat). Tate console 64.5 x 16 x 30, table 80 x 37.
- Living: Costco Aiden & Ivy Sydney modular in Cream (bought Nov 2026, item 1987855), `sydney()` in `build_house.py`. Shown as corner + arm under the
  windows (80.2 in, the window leg must stay under 102 in to clear the front door) and corner + armless + arm on the lot-line wall (117.6 in).
  The 6-piece set also has one more armless seat (37.4) and the ottoman (37.4 x 37.4 x 21.2): not placed yet.
- No brass, no poufs, no picture lights, no busy pattern except the Morris paper. Blue is fine.
- Palette: terracotta, burnt orange, some yellow, olive, plants, walnut. Each room has its own personality.
- Show options before rendering, and link any product by name.
