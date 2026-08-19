# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Search and download from public-domain institutional archives. No key.

Usage:
  uv run scripts/stock_archive.py --source nasa --query "aurora" \
      --kind video --out projects/x/clips/beat-1-still.mp4
  uv run scripts/stock_archive.py --source wikimedia --query "shipping container" \
      --kind image --out projects/x/clips/b4-still.jpg
  ... --list      # candidates only, download nothing

Why these matter: no credential, no billing, no quota to exhaust — the only
sources that work on a fresh machine with nothing configured. They are also
the answer when generated footage keeps inventing pseudo-text and cutting
mid-clip, because this is real footage of real things.

What they are NOT: a general b-roll library. Coverage is deep in science,
space, history, nature and civic life, and absent for modern consumer
interiors, product shots, or anything staged. Check with --list before
promising a scene.

Licence handling differs by source and that difference is the whole point:
- nasa: US Government works, generally not copyrighted. BUT the collection
  includes third-party material, and identifiable people or the NASA insignia
  carry separate restrictions — so this prints the rights field for review
  rather than asserting the item is free.
- wikimedia: per-item licences. Public domain and CC0 accepted by default;
  --allow-attribution widens to CC-BY / CC-BY-SA (credit must then be shown);
  non-commercial and no-derivatives are never accepted.

Prints JSON: {"out", "title", "license", "credit", "source_url", ...}.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

NASA_SEARCH = "https://images-api.nasa.gov/search"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia asks that automated clients identify themselves.
UA = "video-studio/0.1 (https://github.com/scrollmark/video-studio)"

FREE_ALWAYS = ("public domain", "cc0", "no restrictions")
FREE_WITH_CREDIT = ("cc by", "cc-by", "attribution")
# Matched against lowercased CC short names ("CC BY-NC-ND 4.0"). The hyphen
# forms are deliberate: a bare "nc"/"nd" substring hits ordinary words, while
# "-nc"/"-nd" only appear in licence codes.
#
# ND is disqualifying for us specifically: every video crops, composites and
# moves the camera over its source, which IS a derivative work. An earlier
# version of this list omitted it and would have accepted CC BY-ND.
NEVER = ("noncommercial", "non-commercial", "-nc", "noderiv", "no deriv", "-nd")

#: NASA serves several renditions per asset. `~orig` can be hundreds of MB
#: (a 15s b-roll grab pulled 289MB in testing) — default to the largest
#: broadcast-sane rendition and let --quality ask for more.
NASA_QUALITY = {
    "orig": ("~orig", "~large", "~medium"),
    "large": ("~large", "~medium", "~orig"),
    "medium": ("~medium", "~small", "~large"),
}


def licence_ok(text: str, allow_attribution: bool) -> bool:
    t = (text or "").lower()
    if any(k in t for k in NEVER):
        return False
    if any(k in t for k in FREE_ALWAYS):
        return True
    return allow_attribution and any(k in t for k in FREE_WITH_CREDIT)


def search_nasa(client, query: str, kind: str, limit: int) -> list[dict]:
    media = "video" if kind == "video" else "image"
    r = client.get(NASA_SEARCH, params={"q": query, "media_type": media, "page_size": limit})
    r.raise_for_status()
    out = []
    for item in r.json().get("collection", {}).get("items", [])[:limit]:
        d = (item.get("data") or [{}])[0]
        out.append({
            "title": d.get("title", "")[:120],
            "date": (d.get("date_created") or "")[:10],
            "license": d.get("rights") or "US Government work — generally not copyrighted; verify third-party content",
            "credit": f'{d.get("center", "NASA")} / NASA',
            "source_url": d.get("nasa_id"),
            "_assets": item.get("href"),
        })
    return out


def resolve_nasa_asset(client, collection_url: str, kind: str, quality: str = "large") -> str | None:
    r = client.get(collection_url)
    r.raise_for_status()
    files = [u for u in r.json() if isinstance(u, str)]
    ext = (".mp4",) if kind == "video" else (".jpg", ".png")
    candidates = [u for u in files if u.lower().endswith(ext)]
    for pref in NASA_QUALITY.get(quality, NASA_QUALITY["large"]):
        for u in candidates:
            if pref in u:
                return u
    return candidates[0] if candidates else None


def search_wikimedia(client, query: str, kind: str, limit: int, allow_attribution: bool) -> list[dict]:
    r = client.get(COMMONS_API, params={
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": query, "gsrnamespace": 6, "gsrlimit": limit * 3,
        "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime",
    })
    r.raise_for_status()
    want = "video/" if kind == "video" else "image/"
    out = []
    for p in (r.json().get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii.get("url") or not (ii.get("mime", "")).startswith(want):
            continue
        em = ii.get("extmetadata", {})
        lic = (em.get("LicenseShortName", {}) or {}).get("value", "")
        if not licence_ok(lic, allow_attribution):
            continue
        artist = (em.get("Artist", {}) or {}).get("value", "")
        # Artist arrives as HTML; keep it readable without pulling in a parser.
        for tag in ("<", ">"):
            artist = artist.replace(tag, " ")
        artist = " ".join(artist.split())[:80]
        out.append({
            "title": p.get("title", ""), "license": lic,
            "credit": f'{artist or "unknown"} (Wikimedia Commons, {lic})',
            "width": ii.get("width"), "height": ii.get("height"),
            "source_url": ii.get("descriptionurl"), "_download": ii["url"],
        })
        if len(out) >= limit:
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["nasa", "wikimedia"], required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--kind", choices=["video", "image"], default="video")
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--quality", choices=list(NASA_QUALITY), default="large",
                    help="nasa rendition; `orig` can be hundreds of MB")
    ap.add_argument("--allow-attribution", action="store_true",
                    help="wikimedia: also accept CC-BY / CC-BY-SA (credit must be shown)")
    ap.add_argument("--out")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if not args.list and not args.out:
        raise SystemExit("--out is required unless --list")

    import httpx

    with httpx.Client(timeout=90, headers={"User-Agent": UA}, follow_redirects=True) as client:
        if args.source == "nasa":
            results = search_nasa(client, args.query, args.kind, args.limit)
        else:
            results = search_wikimedia(client, args.query, args.kind, args.limit, args.allow_attribution)

        if not results:
            raise SystemExit(
                f"no acceptably-licensed {args.kind} for {args.query!r} in {args.source}. "
                "These archives are deep in science/history/nature and thin on staged "
                "or consumer subjects — try a different source rather than loosening licences."
            )
        if args.list:
            print(json.dumps([{k: v for k, v in r.items() if not k.startswith("_")}
                              for r in results], indent=2))
            return

        pick = results[min(args.index, len(results) - 1)]
        url = pick.get("_download")
        if args.source == "nasa":
            url = resolve_nasa_asset(client, pick["_assets"], args.kind, args.quality)
            if not url:
                raise SystemExit(f"no downloadable {args.kind} file on that NASA asset")

        out = Path(args.out)
        if out.exists() and out.stat().st_size > 0:
            raise SystemExit(f"{out} already exists — delete it explicitly to replace")
        out.parent.mkdir(parents=True, exist_ok=True)
        with client.stream("GET", url) as s, out.open("wb") as f:
            for chunk in s.iter_bytes():
                f.write(chunk)

    print(json.dumps({
        **{k: v for k, v in pick.items() if not k.startswith("_")},
        "out": str(out), "source": args.source,
    }))


if __name__ == "__main__":
    main()
