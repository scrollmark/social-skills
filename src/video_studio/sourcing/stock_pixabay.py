# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Search and download free stock footage or photos (Pixabay).

Usage:
  PIXABAY_API_KEY=... video-studio stock_pixabay \
      --query "city at dusk" --kind video --orientation vertical \
      --out projects/x/clips/beat-2-still.mp4
  ... --list     # candidates only

A second catalogue alongside Pexels — different library, so it widens
coverage when the first source has nothing good. Commercial use allowed,
no attribution required.

Two constraints worth respecting:
- 100 requests per 60 seconds.
- Results must be cached for 24h. Do NOT re-query per render; download once
  into the project and reuse the file (which the project layout does anyway).

Prints JSON: {"out", "source_url", "credit", ...}.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

API = "https://pixabay.com/api"


def search(client, api_key: str, query: str, kind: str, orientation: str, per_page: int) -> list[dict]:
    url = f"{API}/videos/" if kind == "video" else f"{API}/"
    params = {"key": api_key, "q": query, "per_page": max(3, per_page), "safesearch": "true"}
    if kind == "photo":
        params["image_type"] = "photo"
        params["orientation"] = "vertical" if orientation == "vertical" else "horizontal"
    r = client.get(url, params=params)
    if r.status_code != 200:
        raise RuntimeError(f"Pixabay error {r.status_code}: {r.text[:200]}")
    out = []
    for h in r.json().get("hits", []):
        credit = f'{"Video" if kind == "video" else "Photo"} by {h.get("user", "unknown")} on Pixabay'
        if kind == "video":
            streams = h.get("videos", {})
            best = streams.get("large") or streams.get("medium") or streams.get("small")
            if not best:
                continue
            out.append({
                "id": h.get("id"), "download": best["url"],
                "width": best.get("width"), "height": best.get("height"),
                "seconds": h.get("duration"), "credit": credit,
                "source_url": h.get("pageURL"),
            })
        else:
            out.append({
                "id": h.get("id"), "download": h.get("largeImageURL"),
                "width": h.get("imageWidth"), "height": h.get("imageHeight"),
                "credit": credit, "source_url": h.get("pageURL"),
            })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--kind", choices=["video", "photo"], default="video")
    ap.add_argument("--orientation", choices=["vertical", "horizontal"], default="vertical")
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--per-page", type=int, default=10)
    ap.add_argument("--out")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("PIXABAY_API_KEY")
    if not api_key:
        raise SystemExit("Set PIXABAY_API_KEY (free, no billing — pixabay.com/api/docs)")
    if not args.list and not args.out:
        raise SystemExit("--out is required unless --list")

    import httpx

    with httpx.Client(timeout=60) as client:
        results = search(client, api_key, args.query, args.kind, args.orientation, args.per_page)
        if not results:
            raise SystemExit(f"no {args.kind} results for {args.query!r}")
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
