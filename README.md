# Lawton in 3D

A to-scale model of the main floor that you can walk through in a browser, plus a dining-room still. Open this folder in
Claude Code and say **"set this up"**, then ask for changes in plain words, for example "move the sofa to the other wall
and rebuild the walkthrough".

Needs [uv](https://docs.astral.sh/uv/) (it fetches Python 3.11) and, for the stills and wallpaper only,
[ImageMagick](https://imagemagick.org). Blender comes as a Python package, about 800 MB installed. There is no Blender
window. Packages exist for Apple Silicon and Intel Macs, Windows and Linux; only an Intel Mac has been tested.

The OpenAI key is only for photoreal stills. Use your own, in a local `.env` file that git ignores.
