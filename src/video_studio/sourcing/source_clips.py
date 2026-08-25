# /// script
# requires-python = ">=3.11"
# dependencies = ["yt-dlp"]
# ///
"""Resolve url:/find: layer sources into project/clips/ files via yt-dlp.

Usage:
  # user-supplied URL (their rights call — a notice is printed regardless):
  video-studio source_clips url --url "https://..." \
      --out project/clips/scene-1-broll.mp4

  # find free footage: searches YouTube and only accepts results whose
  # license metadata is Creative Commons:
  video-studio source_clips find --query "city timelapse rain" \
      --out project/clips/scene-1-broll.mp4 [--max-seconds 120]

Copyright rule (from SKILL.md): `find` NEVER falls back to standard-license
results — if no CC match exists it exits nonzero and says so; the agent
should offer generation or user-supplied footage instead.

Prints JSON: {"out": path, "source_url": url, "license": str|null}.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _download(url: str, out: Path) -> None:
    from yt_dlp import YoutubeDL

    out.parent.mkdir(parents=True, exist_ok=True)
    opts = {
        "outtmpl": str(out.with_suffix("")) + ".%(ext)s",
        "format": "mp4/bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "noplaylist": True,
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])
    produced = out.with_suffix(".mp4")
    if produced != out and produced.exists():
        produced.rename(out)
    if not out.exists():
        raise RuntimeError(f"download produced no file at {out}")


def cmd_url(args: argparse.Namespace) -> dict:
    print("notice: user-supplied URL — rights/licensing are the supplier's responsibility")
    _download(args.url, Path(args.out))
    return {"out": args.out, "source_url": args.url, "license": None}


def cmd_find(args: argparse.Namespace) -> dict:
    from yt_dlp import YoutubeDL

    with YoutubeDL({"quiet": True, "extract_flat": False, "noplaylist": True}) as ydl:
        info = ydl.extract_info(f"ytsearch10:{args.query}", download=False)
    for entry in info.get("entries") or []:
        license_ = (entry.get("license") or "").lower()
        seconds = entry.get("duration") or 0
        if "creative commons" not in license_:
            continue
        if args.max_seconds and seconds > args.max_seconds:
            continue
        url = entry.get("webpage_url") or entry.get("url")
        _download(url, Path(args.out))
        return {"out": args.out, "source_url": url, "license": entry.get("license")}
    raise SystemExit(
        f"No Creative-Commons result for {args.query!r} — do NOT fall back to "
        "standard-license videos; offer generation or user-supplied footage instead."
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_url = sub.add_parser("url")
    p_url.add_argument("--url", required=True)
    p_url.add_argument("--out", required=True)
    p_find = sub.add_parser("find")
    p_find.add_argument("--query", required=True)
    p_find.add_argument("--out", required=True)
    p_find.add_argument("--max-seconds", type=int, default=180)
    args = ap.parse_args()
    result = cmd_url(args) if args.cmd == "url" else cmd_find(args)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
