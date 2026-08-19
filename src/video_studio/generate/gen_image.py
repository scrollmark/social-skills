# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Generate one still image (Gemini image models, via the Gemini key).

Usage:
  GEMINI_API_KEY=... uv run scripts/gen_image.py \
      --prompt "..." --aspect 9:16 --out clips/scene-1-broll.png
  ... --model gemini-3-pro-image     # slower, stronger
  ... --check                        # which image models this key can reach

Why stills matter: a generated 6s clip costs ~$0.36; a still is a few cents.
Paired with the composer's `ken` drift, a still reads as footage for any
b-roll that isn't intrinsically motion — roughly a 10x saving on the most
common slot. Generate video only when the MOTION carries meaning.

Landmines:
- **The Imagen `:predict` endpoint is gone.** Every imagen-4.0-* model now
  answers `404 ... no longer available to new users`, including the fast and
  ultra variants. This script used to target it and was dead on arrival
  against a current key. Image generation is now `:generateContent` — the same
  endpoint shape as the text models — with the image returned as an
  `inlineData` part.
- **Appearing in ListModels does NOT mean you can call it.** All three
  imagen-4.0 models are still listed and all three 404 on predict. `--check`
  probes by actually calling.
- Aspect goes in `generationConfig.imageConfig.aspectRatio` as a plain "W:H"
  string. NOT a top-level `parameters` block (that was the predict shape), and
  NOT `responseFormat.image.aspectRatio` — that path exists in the proto and is
  what the published cURL examples show, but it takes an AspectRatio ENUM and
  rejects every string spelling of it, including "1:1".
- Free-tier image quota is per-model, per-minute AND per-day. A --check that
  probes every model can exhaust the budget it is reporting on, so it stops at
  the first model that works.
- `imageSize` ("1K"/"2K"/"4K") is honoured only by gemini-3.1-flash-image and
  gemini-3-pro-image; other models ignore it silently rather than erroring.
- A response can carry TEXT parts and no image when a prompt is filtered or
  steered. That is a refusal, not an outage — the text is surfaced.
- Same no-readable-text rule as video: put real text in composer cards.

Prints JSON: {"out", "aspect", "model", "cost_usd_estimate"}.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-3.1-flash-image"
ASPECTS = ("1:1", "3:4", "4:3", "9:16", "16:9", "21:9", "9:21")

#: Models that accept an explicit imageSize. Others ignore it.
SIZED_MODELS = ("gemini-3.1-flash-image", "gemini-3-pro-image")

#: Rough per-image estimates, for cost reporting only — the API returns no
#: price. Order-of-magnitude, not billing truth.
COST_USD = {
    "gemini-3.1-flash-lite-image": 0.01,
    "gemini-3.1-flash-image": 0.03,
    "gemini-2.5-flash-image": 0.04,
    "gemini-3-pro-image": 0.13,
}
DEFAULT_COST = 0.04

PROBE_MODELS = (
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-lite-image",
)


def build_body(prompt: str, aspect: str, model: str, size: str | None) -> dict:
    image_cfg: dict = {"aspectRatio": aspect}
    if size and model in SIZED_MODELS:
        image_cfg["imageSize"] = size
    return {
        "contents": [{"parts": [{"text": prompt}]}],
        # imageConfig, NOT responseFormat.image — the latter exists in the
        # proto but takes an AspectRatio ENUM, and every string form of it
        # ("1:1", "ASPECT_RATIO_1_1", ...) is rejected. imageConfig takes the
        # plain "W:H" string and is what actually works.
        "generationConfig": {"imageConfig": image_cfg},
    }


def extract_image(payload: dict) -> bytes:
    """Pull the first inline image out of a generateContent response."""
    candidates = payload.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"no candidates: {json.dumps(payload)[:300]}")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    notes = []
    for part in parts:
        blob = part.get("inlineData") or part.get("inline_data")
        if blob and blob.get("data"):
            return base64.b64decode(blob["data"])
        if part.get("text"):
            notes.append(part["text"].strip())
    reason = candidates[0].get("finishReason", "")
    raise RuntimeError(
        "no image in response"
        + (f" (finishReason={reason})" if reason else "")
        + (f": {' / '.join(notes)[:300]}" if notes else "")
    )


def call(client, model: str, api_key: str, body: dict):
    return client.post(
        f"{BASE_URL}/models/{model}:generateContent",
        headers={"x-goog-api-key": api_key, "content-type": "application/json"},
        json=body,
    )


def error_detail(resp) -> str:
    try:
        return resp.json().get("error", {}).get("message", "")[:200]
    except Exception:
        return resp.text[:200]


def generate(prompt: str, aspect: str, model: str, size: str | None,
             out: Path, api_key: str) -> None:
    import httpx

    if aspect not in ASPECTS:
        raise SystemExit(f"aspect must be one of {ASPECTS}, got {aspect!r}")
    with httpx.Client(timeout=180) as client:
        resp = call(client, model, api_key, build_body(prompt, aspect, model, size))
    if resp.status_code != 200:
        detail = error_detail(resp)
        if resp.status_code == 404 and "no longer available" in detail:
            raise SystemExit(
                f"{model} has been retired: {detail}\n"
                "Run --check to see which image models this key can reach."
            )
        if resp.status_code == 429:
            raise SystemExit(
                f"out of image quota for {model}: {detail}\n"
                "Free tier limits are per-model, per-minute AND per-day. Wait, "
                "switch --model, or enable billing on the key."
            )
        raise RuntimeError(f"image API error {resp.status_code}: {detail}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(extract_image(resp.json()))


def check(api_key: str) -> None:
    """Actually CALL each model — listing is not reachability."""
    import httpx

    # One model at a time, stopping at the first success: probing all four
    # costs four requests against a per-day free-tier budget, and a --check
    # that exhausts the quota it is reporting on is worse than no check.
    rows = []
    with httpx.Client(timeout=180) as client:
        for model in PROBE_MODELS:
            if any(r["ok"] for r in rows):
                break
            resp = call(client, model, api_key,
                        build_body("a plain red cube on a white background", "1:1", model, None))
            if resp.status_code == 200:
                try:
                    extract_image(resp.json())
                    rows.append({"model": model, "ok": True,
                                 "cost_usd_estimate": COST_USD.get(model, DEFAULT_COST)})
                except RuntimeError as exc:
                    rows.append({"model": model, "ok": False, "detail": str(exc)[:120]})
            else:
                rows.append({"model": model, "ok": False,
                             "detail": f"{resp.status_code}: {error_detail(resp)[:120]}"})
    print(json.dumps({"usable": [r["model"] for r in rows if r["ok"]], "probed": rows}, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt")
    ap.add_argument("--aspect", default="9:16", choices=list(ASPECTS))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--size", choices=["1K", "2K", "4K"], default="2K",
                    help="honoured by gemini-3.1-flash-image / gemini-3-pro-image only")
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true",
                    help="call each image model and report which actually work")
    args = ap.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("Set GEMINI_API_KEY (or GOOGLE_API_KEY)")

    if args.check:
        check(api_key)
        return

    if not args.prompt or not args.out:
        raise SystemExit("--prompt and --out are required")
    out = Path(args.out)
    if out.exists() and out.stat().st_size > 0:
        raise SystemExit(f"{out} already exists — delete it explicitly to regenerate")
    generate(args.prompt, args.aspect, args.model, args.size, out, api_key)
    print(json.dumps({
        "out": str(out), "aspect": args.aspect, "model": args.model,
        "cost_usd_estimate": COST_USD.get(args.model, DEFAULT_COST),
    }))


if __name__ == "__main__":
    main()
