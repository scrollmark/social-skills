# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Search and download sound effects (Freesound), licence-filtered.

Usage:
  FREESOUND_API_KEY=... video-studio stock_freesound \
      --query "camera shutter" --out projects/x/audio/sfx-shutter.mp3
  ... --allow-attribution     # widen to CC-BY (we must then emit credits)
  ... --list

Licence discipline — the reason this script exists rather than a raw call:
Freesound licences vary PER SOUND (CC0 / CC-BY / CC-BY-NC). By default this
only accepts CC0, so nothing downstream carries an obligation. `--allow-
attribution` widens to CC-BY and the credit is returned for you to place;
non-commercial licences are never accepted. Same discipline as the CC-only
footage rule — an agent picking hundreds of files can't reason per item.

Downloads the high-quality preview, which needs only a token (full-quality
originals require an OAuth flow this script deliberately avoids).

Prints JSON: {"out", "license", "credit", "source_url", "seconds"}.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

API = "https://freesound.org/apiv2"
CC0 = ("Creative Commons 0",)
BY = ("Attribution",)


def acceptable(license_name: str, allow_attribution: bool) -> bool:
    name = (license_name or "")
    if "Noncommercial" in name or "NonCommercial" in name:
        return False  # never — downstream use is commercial
    if any(k in name for k in CC0):
        return True
    return allow_attribution and any(k in name for k in BY)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--out")
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--max-seconds", type=float, default=30.0)
    ap.add_argument("--allow-attribution", action="store_true",
                    help="also accept CC-BY (credits must then be shown)")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("FREESOUND_API_KEY")
    if not api_key:
        raise SystemExit("Set FREESOUND_API_KEY (free — freesound.org/apiv2/apply)")
    if not args.list and not args.out:
        raise SystemExit("--out is required unless --list")

    import httpx

    with httpx.Client(timeout=60, headers={"Authorization": f"Token {api_key}"}) as client:
        r = client.get(f"{API}/search/text/", params={
            "query": args.query, "page_size": 25,
            "fields": "id,name,license,previews,duration,username,url",
        })
        if r.status_code != 200:
            raise RuntimeError(f"Freesound error {r.status_code}: {r.text[:200]}")
        results = [
            {
                "id": s["id"], "name": s.get("name"),
                "license": s.get("license"), "seconds": s.get("duration"),
                "credit": f'"{s.get("name")}" by {s.get("username")} (Freesound)',
                "source_url": s.get("url"),
                "download": (s.get("previews") or {}).get("preview-hq-mp3"),
            }
            for s in r.json().get("results", [])
            if acceptable(s.get("license", ""), args.allow_attribution)
            and (s.get("duration") or 0) <= args.max_seconds
            and (s.get("previews") or {}).get("preview-hq-mp3")
        ]
        if not results:
            raise SystemExit(
                f"no acceptably-licensed result for {args.query!r} "
                f"({'CC0 or CC-BY' if args.allow_attribution else 'CC0 only'}). "
                "Do not fall back to a non-commercial sound."
            )
        if args.list:
            print(json.dumps(results, indent=2))
            return
        pick = results[min(args.index, len(results) - 1)]
        out = Path(args.out)
        if out.exists() and out.stat().st_size > 0:
            raise SystemExit(f"{out} already exists — delete it explicitly to replace")
        out.parent.mkdir(parents=True, exist_ok=True)
        with client.stream("GET", pick["download"]) as s, out.open("wb") as f:
            for chunk in s.iter_bytes():
                f.write(chunk)
    print(json.dumps({**{k: v for k, v in pick.items() if k != "download"}, "out": str(out)}))


if __name__ == "__main__":
    main()
