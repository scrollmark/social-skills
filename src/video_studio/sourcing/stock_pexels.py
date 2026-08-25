# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Search and download free stock footage or photos (Pexels).

Usage:
  PEXELS_API_KEY=... video-studio stock_pexels --check      # verify the key
  ... --query "rain on a window" --kind video --orientation portrait \
      --out projects/x/clips/beat-1-still.mp4
  ... --kind photo --size large --out projects/x/clips/beat-1-still.jpg
  ... --list            # candidates only, download nothing

Why this source first: one catalogue-wide licence covers everything, so an
agent can pick without reasoning about per-item rights, and there is no
share-alike clause to propagate into the finished video. Commercial use is
allowed and attribution is not required — the credit is still returned and
printed, because crediting is good practice and lifts the rate limit.

Limits: 200 requests/hour, 20,000/month by default.

A key is REQUIRED. Unauthenticated search appears to work for popular queries
because those responses are edge-cached; anything else returns
{"status":401,"code":"Unauthorized"} — inside an HTTP 200 body, so the status
code alone will not tell you.

Endpoint note: photos are at /v1/search but videos are at /v1/videos/search.
An earlier version had videos at /videos/search (no /v1), which 404s. Both
are attempted, newest-documented first, because this path has moved before.

Prints JSON: {"out", "source_url", "credit", "width", "height", ...}.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BASE = "https://api.pexels.com"
PHOTO_PATHS = ("/v1/search",)
# Documented path first, legacy second — see the endpoint note above.
VIDEO_PATHS = ("/v1/videos/search", "/videos/search")

#: Cap the download. A 4K 30s clip is hundreds of MB and nothing in a
#: 1080-wide composition benefits from it (the NASA source taught this the
#: expensive way — a single b-roll grab pulled 289MB).
MAX_USEFUL_WIDTH = 2560


def parse_videos(data: dict) -> list[dict]:
    out = []
    for v in data.get("videos", []):
        files = sorted(
            (f for f in v.get("video_files", []) if f.get("width") and f.get("link")),
            key=lambda f: f["width"], reverse=True,
        )
        if not files:
            continue
        best = next((f for f in files if f["width"] <= MAX_USEFUL_WIDTH), files[-1])
        out.append({
            "id": v.get("id"), "download": best["link"],
            "width": best.get("width"), "height": best.get("height"),
            "seconds": v.get("duration"),
            "credit": f'Video by {(v.get("user") or {}).get("name", "unknown")} on Pexels',
            "source_url": v.get("url"),
        })
    return out


def parse_photos(data: dict) -> list[dict]:
    out = []
    for p in data.get("photos", []):
        src = p.get("src") or {}
        link = src.get("original") or src.get("large2x") or src.get("large")
        if not link:
            continue
        out.append({
            "id": p.get("id"), "download": link,
            "width": p.get("width"), "height": p.get("height"),
            "credit": f'Photo by {p.get("photographer", "unknown")} on Pexels',
            "source_url": p.get("url"),
        })
    return out


def search(client, kind: str, params: dict) -> list[dict]:
    paths = VIDEO_PATHS if kind == "video" else PHOTO_PATHS
    last = None
    for path in paths:
        r = client.get(f"{BASE}{path}", params=params)
        if r.status_code == 404:
            last = r
            continue  # path moved; try the next known one
        if r.status_code == 401:
            raise SystemExit("Pexels rejected the key (401) — check PEXELS_API_KEY")
        if r.status_code == 429:
            raise SystemExit("Pexels rate limit hit (429) — 200/hour, 20k/month; wait or reduce calls")
        if r.status_code != 200:
            raise RuntimeError(f"Pexels error {r.status_code}: {r.text[:200]}")
        body = r.json()
        # Errors arrive INSIDE a 200 body — {"status":401,"code":"Unauthorized"}.
        # Without this check the payload has no "videos"/"photos" key, parsing
        # yields [], and the caller reports "no results for <query>", sending
        # someone off to try different search terms when the key is the problem.
        inner = body.get("status")
        if isinstance(inner, int) and inner >= 400:
            msg = body.get("message") or body.get("code") or "unknown"
            if inner == 401:
                raise SystemExit(f"Pexels: {msg}. Set a valid PEXELS_API_KEY (free — pexels.com/api)")
            raise RuntimeError(f"Pexels error {inner}: {msg}")
        return parse_videos(body) if kind == "video" else parse_photos(body)
    raise RuntimeError(f"all known {kind} endpoints 404'd (last: {last.url if last else 'n/a'})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query")
    ap.add_argument("--kind", choices=["video", "photo"], default="video")
    ap.add_argument("--orientation", choices=["landscape", "portrait", "square"], default="portrait")
    ap.add_argument("--size", choices=["large", "medium", "small"],
                    help="large=4K/24MP, medium=HD/12MP, small=HD/4MP")
    ap.add_argument("--index", type=int, default=0, help="which result to take (0-based)")
    ap.add_argument("--per-page", type=int, default=10)
    ap.add_argument("--out")
    ap.add_argument("--list", action="store_true", help="print candidates, download nothing")
    ap.add_argument("--check", action="store_true", help="probe reachability, then exit")
    args = ap.parse_args()

    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        raise SystemExit("Set PEXELS_API_KEY (free, no billing — pexels.com/api)")

    import httpx

    headers = {"Authorization": api_key}
    with httpx.Client(timeout=60, headers=headers, follow_redirects=True) as client:
        if args.check:
            # Use an unusual query: common ones (e.g. "sky") can be served from
            # edge cache WITHOUT auth, which briefly made a bogus key look valid.
            vids = search(client, "video", {"query": "zaragoza tramway", "per_page": 1})
            pics = search(client, "photo", {"query": "zaragoza tramway", "per_page": 1})
            print(json.dumps({"ok": True, "video_endpoint": bool(vids) or True,
                              "photo_endpoint": bool(pics) or True,
                              "note": "a 401 would have raised; the key is accepted"}))
            return

        if not args.query:
            raise SystemExit("--query is required")
        if not args.list and not args.out:
            raise SystemExit("--out is required unless --list")

        params = {"query": args.query, "orientation": args.orientation, "per_page": args.per_page}
        if args.size:
            params["size"] = args.size
        results = search(client, args.kind, params)
        if not results:
            raise SystemExit(f"no {args.kind} results for {args.query!r}")
        if args.list:
            print(json.dumps([{k: v for k, v in r.items() if k != "download"} for r in results], indent=2))
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
