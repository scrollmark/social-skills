# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Search and license stock footage or images (Shutterstock).

Usage:
  SHUTTERSTOCK_TOKEN=... video-studio stock_shutterstock --check
  ... --query "tokyo crossing at night" --kind video --orientation vertical --list
  ... --query "..." --kind video --out projects/x/clips/beat-1-still.mp4

READ THIS BEFORE REACHING FOR IT
--------------------------------
This is NOT a drop-in alternative to Pexels, and the difference is licensing
rather than catalogue.

  Search      works on the free tier. 100 requests/hour, and that is the
              binding limit — one video here took ~50 searches including
              replacements, so a couple of videos an hour is the ceiling.
  Download    requires a PAID SUBSCRIPTION on top of API access. There is no
              free download path for the main catalogue. `--out` will fail
              with a clear message rather than a confusing 403 if you have
              search access but no subscription.

So the honest ordering stays: archives and Pexels first, because they cover
everyday subjects for free and keep the "make a whole video without signing up
for anything" promise. Reach for this when the free libraries genuinely cannot
find the shot AND somebody already pays for Shutterstock.

WHAT IT BUYS
------------
A far larger catalogue, and — the reason it was added — per-asset metadata that
free libraries do not publish. `--list` surfaces `description` and `keywords`,
which are the only machine-readable evidence of what a clip actually shows.
Location still is NOT guaranteed: Shutterstock does not publish shoot
coordinates either, so a place name in a description is a contributor's claim,
not a fact. Treat it exactly like a Pexels slug — evidence, not proof.

AUTH
----
Two schemes, and picking wrong is the usual first failure. HTTP Basic
(consumer key + secret) is enough for search and metadata. Licensing and
downloading need an OAuth bearer token with the `licenses` scope. This script
takes a bearer token in SHUTTERSTOCK_TOKEN, and falls back to Basic from
SHUTTERSTOCK_KEY / SHUTTERSTOCK_SECRET for search-only use.

Prints JSON: {"out", "source_url", "credit", "description", "keywords", ...}.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path

BASE = "https://api.shutterstock.com/v2"


def auth_headers() -> tuple[dict, str]:
    """Bearer if we have one, else Basic. Returns (headers, mode)."""
    token = os.environ.get("SHUTTERSTOCK_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}, "bearer"
    key = os.environ.get("SHUTTERSTOCK_KEY")
    secret = os.environ.get("SHUTTERSTOCK_SECRET")
    if key and secret:
        blob = base64.b64encode(f"{key}:{secret}".encode()).decode()
        return {"Authorization": f"Basic {blob}"}, "basic"
    raise SystemExit(
        "Set SHUTTERSTOCK_TOKEN (OAuth bearer, needed to license/download), or "
        "SHUTTERSTOCK_KEY + SHUTTERSTOCK_SECRET for search-only access.\n"
        "Both come from https://www.shutterstock.com/developers"
    )


def search(client, kind: str, params: dict) -> list[dict]:
    path = "/videos/search" if kind == "video" else "/images/search"
    r = client.get(f"{BASE}{path}", params=params)
    if r.status_code == 401:
        raise SystemExit("401 from Shutterstock — credentials rejected. "
                         "A Basic key cannot license; check which scheme you set.")
    if r.status_code == 429:
        raise SystemExit("429 — rate limited. The free tier allows 100 requests/hour.")
    r.raise_for_status()
    out = []
    for item in r.json().get("data", []):
        assets = item.get("assets", {})
        # Preview only. The licensed original comes from the /licenses endpoint
        # and needs a subscription; previews are watermarked and low-res, so
        # they are deliberately NOT offered as a download target.
        preview = (assets.get("preview_mp4") or assets.get("preview_webm")
                   or assets.get("preview_1000") or assets.get("preview") or {})
        contributor = item.get("contributor", {}).get("id", "")
        out.append({
            "id": item.get("id"),
            "description": (item.get("description") or "").strip(),
            "keywords": item.get("keywords", [])[:12],
            "duration": item.get("duration"),
            "width": (assets.get("original") or {}).get("width"),
            "height": (assets.get("original") or {}).get("height"),
            "credit": f"Shutterstock contributor {contributor}" if contributor else "Shutterstock",
            "source_url": f"https://www.shutterstock.com/{'video' if kind == 'video' else 'image-photo'}/-{item.get('id')}",
            "preview": preview.get("url") if isinstance(preview, dict) else None,
        })
    return out


def license_asset(client, kind: str, asset_id: str, size: str) -> str:
    """Exchange a subscription for a download URL. Requires a paid plan."""
    path = "/videos/licenses" if kind == "video" else "/images/licenses"
    r = client.post(f"{BASE}{path}", json={"videos" if kind == "video" else "images":
                                           [{"video_id" if kind == "video" else "image_id": asset_id,
                                             "size": size}]})
    if r.status_code in (401, 403):
        raise SystemExit(
            f"{r.status_code} licensing {asset_id}. Search works on the free tier but "
            "DOWNLOADING needs a paid Shutterstock subscription on the same account, "
            "plus a bearer token with the `licenses` scope.\n"
            "Use --list to browse, and the free libraries to actually fetch."
        )
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data or not data[0].get("download", {}).get("url"):
        raise SystemExit(f"licensed {asset_id} but no download url came back: {data}")
    return data[0]["download"]["url"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query")
    ap.add_argument("--kind", choices=["video", "image"], default="video")
    ap.add_argument("--orientation", choices=["vertical", "horizontal"], default="vertical")
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--per-page", type=int, default=10)
    ap.add_argument("--size", default="web", help="licensed size (video: web/sd/hd/4k)")
    ap.add_argument("--out")
    ap.add_argument("--list", action="store_true", help="print candidates, download nothing")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    headers, mode = auth_headers()
    import httpx

    with httpx.Client(timeout=60, headers=headers, follow_redirects=True) as client:
        if args.check:
            probe = search(client, "video", {"query": "zaragoza tramway", "per_page": 1})
            print(json.dumps({
                "ok": True, "auth": mode,
                "canSearch": True,
                "canDownload": mode == "bearer",
                "note": "search works on the free tier; downloading also needs a paid "
                        "subscription, which this probe cannot confirm without spending one",
            }, indent=2))
            return

        if not args.query:
            raise SystemExit("--query is required")
        if not args.list and not args.out:
            raise SystemExit("--out is required unless --list")

        params = {"query": args.query, "per_page": args.per_page,
                  "orientation": args.orientation}
        results = search(client, args.kind, params)
        if not results:
            raise SystemExit(f"no {args.kind} results for {args.query!r}")

        if args.list:
            print(json.dumps(results, indent=2))
            return

        pick = results[min(args.index, len(results) - 1)]
        out = Path(args.out)
        if out.exists() and out.stat().st_size > 0:
            raise SystemExit(f"{out} already exists — delete it explicitly to replace")
        if mode != "bearer":
            raise SystemExit(
                "Downloading needs SHUTTERSTOCK_TOKEN (OAuth bearer with `licenses` "
                "scope) and a paid subscription. Basic auth can search only."
            )
        url = license_asset(client, args.kind, str(pick["id"]), args.size)
        out.parent.mkdir(parents=True, exist_ok=True)
        with client.stream("GET", url) as s, out.open("wb") as f:
            for chunk in s.iter_bytes():
                f.write(chunk)

    print(json.dumps({**{k: v for k, v in pick.items() if k != "preview"},
                      "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
