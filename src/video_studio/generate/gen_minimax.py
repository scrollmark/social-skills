# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Generate one video clip with MiniMax (Hailuo).

Usage:
  MINIMAX_API_KEY=... uv run scripts/gen_minimax.py \
      --prompt "..." --seconds 6 --out clips/scene-1.mp4 [--resolution 1080P]

Landmines encoded here (see references/api-landmines.md):
- 1080P supports ONLY 6s. Asking for more at 1080P is an error 2013, so this
  script clamps and warns instead of failing a batch mid-run.
- Application errors arrive inside HTTP 200 via `base_resp.status_code` —
  checked on every response, or a bogus task id polls for 10 minutes.
- Landscape-only output: vertical framing is the composer's cover-crop.
- A submitted job bills even if never downloaded — don't kill mid-poll.

Prints JSON: {"out": path, "seconds": int, "cost_usd_estimate": float}.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

BASE_URL = "https://api.minimax.io/v1"
MODEL = "MiniMax-Hailuo-02"
POLL_INTERVAL = 10
MAX_POLL_ATTEMPTS = 60
COST_PER_SECOND = 0.06  # observed, update in api-landmines.md if it drifts

DURATIONS_BY_RESOLUTION = {"1080P": (6,), "768P": (6, 10)}


def _check(data: dict) -> None:
    base_resp = data.get("base_resp") or {}
    code = base_resp.get("status_code", 0)
    if code:
        raise RuntimeError(f"MiniMax API error {code}: {base_resp.get('status_msg', 'unknown')}")


def quantize(requested: int, resolution: str) -> int:
    supported = DURATIONS_BY_RESOLUTION.get(resolution, (6,))
    for s in supported:
        if requested <= s:
            return s
    return supported[-1]


def generate(prompt: str, seconds: int, resolution: str, out: Path, api_key: str) -> int:
    import httpx

    duration = quantize(seconds, resolution)
    if duration != seconds:
        print(f"note: requested {seconds}s, {resolution} supports {DURATIONS_BY_RESOLUTION[resolution]} -> using {duration}s")
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            f"{BASE_URL}/video_generation",
            headers={**headers, "Content-Type": "application/json"},
            json={"model": MODEL, "prompt": prompt, "duration": duration, "resolution": resolution},
        )
        resp.raise_for_status()
        data = resp.json()
        _check(data)
        task_id = data["task_id"]
        print(f"submitted: {task_id}")

        file_id = None
        for attempt in range(MAX_POLL_ATTEMPTS):
            resp = client.get(
                f"{BASE_URL}/query/video_generation",
                params={"task_id": task_id}, headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            _check(data)
            status = data.get("status", "")
            if status == "Success":
                file_id = data["file_id"]
                break
            if status == "Failed":
                raise RuntimeError(f"generation failed: {data}")
            if attempt % 3 == 0:
                print(f"waiting... ({status})")
            time.sleep(POLL_INTERVAL)
        if file_id is None:
            raise RuntimeError(f"timed out after {MAX_POLL_ATTEMPTS * POLL_INTERVAL}s (task {task_id} may still complete and bill)")

        resp = client.get(f"{BASE_URL}/files/retrieve", params={"file_id": file_id}, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        _check(data)
        out.parent.mkdir(parents=True, exist_ok=True)
        with client.stream("GET", data["file"]["download_url"]) as stream:
            with open(out, "wb") as f:
                for chunk in stream.iter_bytes():
                    f.write(chunk)
    return duration


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--seconds", type=int, default=6)
    ap.add_argument("--resolution", default="1080P", choices=list(DURATIONS_BY_RESOLUTION))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    api_key = os.environ.get("MINIMAX_API_KEY", "")
    if not api_key:
        raise SystemExit("Set MINIMAX_API_KEY")
    out = Path(args.out)
    if out.exists() and out.stat().st_size > 0:
        raise SystemExit(f"{out} already exists — never regenerate paid clips; delete it explicitly first")
    duration = generate(args.prompt, args.seconds, args.resolution, out, api_key)
    print(json.dumps({"out": str(out), "seconds": duration, "cost_usd_estimate": round(duration * COST_PER_SECOND, 2)}))


if __name__ == "__main__":
    main()
