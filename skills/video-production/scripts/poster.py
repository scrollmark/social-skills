# /// script
# requires-python = ">=3.11"
# ///
"""Pick a poster frame (thumbnail) out of a finished render.

Usage:
  uv run scripts/poster.py --in <mp4>                 # scan and pick the best
  uv run scripts/poster.py --in <mp4> --at 12.5       # take exactly this frame
  uv run scripts/poster.py --in <mp4> --top 5         # write the 5 best, ranked
  uv run scripts/poster.py --in <mp4> --no-contact    # skip the candidate sheet

A feed reads as coherent because its thumbnails do, so the poster is part of
the look, not an afterthought at upload time. Left to a platform, the frame is
chosen by an algorithm optimising for nothing in particular; left to a person,
it is usually the first frame, which in this pipeline is a title card fading in
from black.

Scoring is deliberately crude and stated plainly rather than dressed up:

  saturation   colourful frames read at thumbnail size, grey ones do not
  contrast     luma spread, as a proxy for "something is happening here"
  brightness   penalised at both ends; a crushed or blown frame is unreadable
               once the platform has compressed it further

It rejects the first and last 8% of the timeline outright. Those are fades and
title cards, and a title card makes a poor poster: the text is already in the
title of the post, and the frame carries no image.

**This produces a shortlist, not a verdict, and the difference matters.** The
score knows nothing about what the video is ABOUT. On its first run against a
finished Mexico spot it ranked an underwater reef first — the most saturated
frame in the piece, and a thumbnail with nothing Mexican in it — over a
marigold market and a shot of folk dancers that both scored lower and would
both sell the video better.

So the contact sheet is written by default and the ranking is a starting point.
Look at the sheet, then pass --at. An agent using this must actually view the
candidates rather than shipping frame #1 because it came out on top.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def stats_at(path: Path, t: float) -> dict | None:
    """Saturation, luma mean and luma spread for the frame at t."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
         "-vf", "format=yuv420p,signalstats,metadata=mode=print", "-f", "null", "-"],
        capture_output=True, text=True)
    blob = r.stdout + r.stderr
    def grab(key: str) -> float | None:
        m = re.search(rf"signalstats\.{key}=(-?[\d.]+)", blob)
        return float(m.group(1)) if m else None
    sat, ymin, ymax, yavg = grab("SATAVG"), grab("YMIN"), grab("YMAX"), grab("YAVG")
    if None in (sat, ymin, ymax, yavg):
        return None
    return {"t": round(t, 2), "saturation": sat, "luma": yavg, "spread": ymax - ymin}


def score(s: dict) -> float:
    """Higher is a better poster. Brightness is penalised away from mid-grey."""
    sat = min(s["saturation"], 90) / 90          # 0..1, saturated is better
    spread = min(s["spread"], 255) / 255          # 0..1, more range is better
    # 128 is mid-luma; full penalty at pure black or pure white.
    balance = 1 - abs(s["luma"] - 128) / 128
    return round(0.45 * sat + 0.35 * spread + 0.20 * balance, 4)


def scan(path: Path, samples: int) -> list[dict]:
    total = duration(path)
    if total <= 0:
        raise SystemExit(f"could not read a duration from {path}")
    lo, hi = total * 0.08, total * 0.92
    step = (hi - lo) / max(1, samples - 1)
    out = []
    for i in range(samples):
        s = stats_at(path, lo + i * step)
        if s:
            s["score"] = score(s)
            out.append(s)
    return sorted(out, key=lambda s: s["score"], reverse=True)


def write_frame(path: Path, t: float, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(path),
                    "-frames:v", "1", str(dest), "-loglevel", "error"], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", type=Path, required=True)
    ap.add_argument("--at", type=float, help="skip scoring, take this timestamp")
    ap.add_argument("--top", type=int, default=1, help="how many ranked frames to write")
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--out", type=Path, help="output path (default: alongside the render)")
    ap.add_argument("--no-contact", action="store_true",
                    help="skip the candidate sheet; it is written by default "
                         "because the top-scoring frame is often not the right one")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.src.exists():
        raise SystemExit(f"no such file: {args.src}")
    base = args.out or args.src.with_name(args.src.stem + "-poster.png")

    if args.at is not None:
        write_frame(args.src, args.at, base)
        print(json.dumps({"poster": str(base), "at": args.at, "chosen": "by hand"}, indent=2))
        return

    ranked = scan(args.src, args.samples)
    if not ranked:
        raise SystemExit("could not measure any frames — is there a video stream?")

    written = []
    for i, s in enumerate(ranked[:max(1, args.top)]):
        dest = base if i == 0 else base.with_name(f"{base.stem}-{i + 1}{base.suffix}")
        write_frame(args.src, s["t"], dest)
        written.append({"path": str(dest), "at": s["t"], "score": s["score"]})

    sheet = None
    if not args.no_contact:
        sheet = base.with_name(base.stem + "-candidates.png")
        tmp = base.parent / ".poster-tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        tiles = []
        for i, s in enumerate(ranked[:12]):
            p = tmp / f"c{i:02d}.png"
            subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{s['t']:.2f}", "-i", str(args.src), "-frames:v", "1",
                 "-vf", f"scale=180:-1,drawtext=text='{s['t']:.1f}s  {s['score']:.2f}':"
                        f"x=5:y=5:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.7",
                 str(p), "-loglevel", "error"], check=True)
            tiles.append(p)
        inputs = [x for p in tiles for x in ("-i", str(p))]
        subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex",
                        f"hstack=inputs={len(tiles)}", str(sheet), "-loglevel", "error"],
                       check=True)
        for p in tiles:
            p.unlink()
        tmp.rmdir()

    result = {"posters": written, "candidates": ranked[:12],
              **({"contactSheet": str(sheet)} if sheet else {}),
              "note": "scoring is crude — open the sheet and override with --at if it "
                      "picked a pretty wall over a face"}
    print(json.dumps(result, indent=2) if args.json else
          "\n".join(f"{w['at']:>7.2f}s  score {w['score']}  ->  {w['path']}" for w in written)
          + (f"\ncandidates: {sheet}" if sheet else "")
          + "\nscoring is crude — check the sheet and use --at if it chose badly.")


if __name__ == "__main__":
    main()
