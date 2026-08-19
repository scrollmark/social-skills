# /// script
# requires-python = ">=3.11"
# dependencies = ["google-genai"]
# ///
"""Generate one video clip with Veo (Gemini API).

Usage:
  GEMINI_API_KEY=... uv run scripts/gen_veo.py \
      --prompt "..." --seconds 6 --aspect 9:16 --out clips/scene-1.mp4

Landmines encoded here (see references/api-landmines.md):
- Durations {4, 6, 8} ONLY (5 and 7 are rejected despite docs saying "4-8").
- `generate_audio` is Enterprise-auth-only; never sent here.
- Video quota is separate from (and much smaller than) text quota — probe
  with a 4s clip before planning a batch. Preview pricing ~= $0.40/s.

Prints JSON: {"out": path, "seconds": int}.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

API_DURATIONS = (4, 6, 8)
POLL_INTERVAL = 10
MAX_POLL_ATTEMPTS = 60
DEFAULT_MODEL = "veo-3.1-generate-preview"


def quantize(requested: int) -> int:
    for s in API_DURATIONS:
        if requested <= s:
            return s
    return API_DURATIONS[-1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--seconds", type=int, default=6)
    ap.add_argument("--aspect", default="9:16", choices=["16:9", "9:16"])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("Set GEMINI_API_KEY (or GOOGLE_API_KEY)")
    out = Path(args.out)
    if out.exists() and out.stat().st_size > 0:
        raise SystemExit(f"{out} already exists — never regenerate paid clips; delete it explicitly first")

    from google import genai
    from google.genai import types

    duration = quantize(args.seconds)
    client = genai.Client(api_key=api_key)
    operation = client.models.generate_videos(
        model=args.model,
        prompt=args.prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio=args.aspect, number_of_videos=1, duration_seconds=duration,
        ),
    )
    print(f"submitted: {operation.name}")
    for attempt in range(MAX_POLL_ATTEMPTS):
        if operation.done:
            break
        if attempt % 3 == 0:
            print(f"waiting... (attempt {attempt + 1})")
        time.sleep(POLL_INTERVAL)
        operation = client.operations.get(operation)
    else:
        raise RuntimeError(f"timed out after {MAX_POLL_ATTEMPTS * POLL_INTERVAL}s")

    if not operation.response or not operation.response.generated_videos:
        raise RuntimeError(f"no videos returned: {operation}")
    video = operation.response.generated_videos[0]
    out.parent.mkdir(parents=True, exist_ok=True)
    client.files.download(file=video.video)
    video.video.save(str(out))
    print(json.dumps({"out": str(out), "seconds": duration}))


if __name__ == "__main__":
    main()
