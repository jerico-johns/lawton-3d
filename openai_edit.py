"""Minimal OpenAI image-edit helper. Needs YOUR OWN key: OPENAI_API_KEY in the environment or in a local .env (git-ignored)."""
import base64, os, pathlib
import requests
MODEL = "gpt-image-2.5-sunburst"
ROOT = pathlib.Path(__file__).resolve().parent


def load_key(name="OPENAI_API_KEY"):
    v = os.environ.get(name); env = ROOT / ".env"
    if not v and env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(name + "="): v = line.split("=", 1)[1].strip().strip("\"'")
    return v


def edit2(key, images, prompt, size="1536x1024"):
    files = [("image[]", (p.name, open(p, "rb"), "image/jpeg")) for p in images]
    r = requests.post("https://api.openai.com/v1/images/edits", headers={"Authorization": f"Bearer {key}"}, files=files,
                      data={"model": MODEL, "prompt": prompt, "n": "1", "size": size, "quality": "high"}, timeout=600)
    if r.status_code != 200: raise RuntimeError(f"OpenAI {r.status_code}: {r.text[:300]}")
    return base64.b64decode(r.json()["data"][0]["b64_json"])
