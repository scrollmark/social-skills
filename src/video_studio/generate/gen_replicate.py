# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Generate an image, clip, or audio bed through a model aggregator (Replicate).

One credential covers many models, which is why this exists as a single
script rather than one per vendor — adding an option becomes a row in
MODELS, not a new integration.

Usage:
  REPLICATE_API_TOKEN=... uv run scripts/gen_replicate.py \
      --kind image --preset flux --prompt "..." --aspect 9:16 \
      --out projects/x/clips/beat-1-still.png
  ... --kind video --preset kling --seconds 5 --out .../beat-1-still.mp4
  ... --kind audio --preset musicgen --seconds 30 --out .../music.mp3
  ... --list-presets

Model slugs drift as vendors publish new versions — `--model owner/name`
overrides any preset, and `--list-presets` shows what the defaults point at
today. A 404 from this script usually means the slug moved, not that the key
is bad.

Costs vary by model (roughly: images a few cents, video tens of cents per
second). Quote before a batch; nothing here is free.

Prints JSON: {"out", "model", "kind"}.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

API = "https://api.replicate.com/v1"
POLL_INTERVAL = 3
MAX_POLLS = 200

# Presets are a convenience, not a contract — see --model.
MODELS = {
    "image": {
        "flux": ("black-forest-labs/flux-1.1-pro", "general-purpose, strong default"),
        "flux-schnell": ("black-forest-labs/flux-schnell", "fast and cheap, lower fidelity"),
        "ideogram": ("ideogram-ai/ideogram-v3-turbo", "best at legible text inside an image"),
    },
    "video": {
        # Slugs below were read off Replicate's own text-to-video collection,
        # not recalled from memory. They drift as vendors publish new versions;
        # `--model owner/name` always wins and is the right answer when one 404s.
        "kling": ("kwaivgi/kling-v2.1", "quality tier"),
        "wan": ("wan-video/wan-2.5-t2v", "budget tier, native 1080p"),
        "luma": ("luma/ray-flash-2-720p", "cheapest per clip; fast, less literal"),
        "luma-hq": ("luma/ray-3.2", "Luma's quality tier"),
        "runway": ("runwayml/gen-4.5", "priciest; best physics and continuity"),
        # NOT here: Pika. It has no Replicate model, so it would need its own
        # client and key rather than a one-line preset. Its draw is a free tier
        # permitting commercial use — capped at 480p, which is below the
        # 1080x1920 every format here renders at, so it buys nothing yet.
    },
    "audio": {
        "musicgen": ("meta/musicgen", "instrumental beds from a text description"),
        "stable-audio": ("stackadoc/stable-audio-open-1.0", "clean commercial terms"),
    },
}

ASPECT_TO_SIZE = {
    "9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1024, 1024),
}


def build_input(kind: str, args) -> dict:
    if kind == "image":
        w, h = ASPECT_TO_SIZE.get(args.aspect, ASPECT_TO_SIZE["9:16"])
        return {"prompt": args.prompt, "aspect_ratio": args.aspect, "width": w, "height": h}
    if kind == "video":
        return {"prompt": args.prompt, "duration": args.seconds, "aspect_ratio": args.aspect}
    return {"prompt": args.prompt, "duration": args.seconds}


def run(model: str, payload: dict, token: str) -> str:
    import httpx

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with httpx.Client(timeout=120) as client:
        r = client.post(f"{API}/models/{model}/predictions", headers=headers, json={"input": payload})
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Replicate error {r.status_code}: {r.text[:250]}")
        pred = r.json()
        get_url = pred.get("urls", {}).get("get")
        for i in range(MAX_POLLS):
            status = pred.get("status")
            if status == "succeeded":
                break
            if status in ("failed", "canceled"):
                raise RuntimeError(f"generation {status}: {str(pred.get('error'))[:250]}")
            if i % 5 == 0:
                print(f"    waiting... ({status})")
            time.sleep(POLL_INTERVAL)
            pred = client.get(get_url, headers=headers).json()
        else:
            raise RuntimeError(f"timed out after {MAX_POLLS * POLL_INTERVAL}s")

        out = pred.get("output")
        url = out[0] if isinstance(out, list) and out else out
        if not isinstance(url, str):
            raise RuntimeError(f"unexpected output shape: {json.dumps(out)[:200]}")
        return url


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=list(MODELS), default="image")
    ap.add_argument("--preset")
    ap.add_argument("--model", help="owner/name — overrides --preset")
    ap.add_argument("--prompt")
    ap.add_argument("--aspect", default="9:16", choices=list(ASPECT_TO_SIZE))
    ap.add_argument("--seconds", type=int, default=5)
    ap.add_argument("--out")
    ap.add_argument("--list-presets", action="store_true")
    args = ap.parse_args()

    if args.list_presets:
        for kind, presets in MODELS.items():
            print(f"{kind}:")
            for name, (slug, why) in presets.items():
                print(f"  {name:<14}{slug:<40}{why}")
        return

    if not args.prompt or not args.out:
        raise SystemExit("--prompt and --out are required")
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        raise SystemExit("Set REPLICATE_API_TOKEN (paid — replicate.com/account/api-tokens)")

    presets = MODELS[args.kind]
    model = args.model or presets[args.preset or next(iter(presets))][0]
    out = Path(args.out)
    if out.exists() and out.stat().st_size > 0:
        raise SystemExit(f"{out} already exists — delete it explicitly to regenerate (this costs money)")

    url = run(model, build_input(args.kind, args), token)

    import httpx

    out.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=300) as client, client.stream("GET", url) as s, out.open("wb") as f:
        for chunk in s.iter_bytes():
            f.write(chunk)
    print(json.dumps({"out": str(out), "model": model, "kind": args.kind}))


if __name__ == "__main__":
    main()
