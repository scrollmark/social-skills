# /// script
# requires-python = ">=3.11"
# ///
"""Chromakey a clip to alpha (VP9 WebM) for layering in the composer.

Remotion has no native keying — this is the one compositing job that stays
in ffmpeg. Usage:

  uv run scripts/prekey.py --in clips/speaker.mp4 --out public/clips/speaker-keyed.webm
  uv run scripts/prekey.py --in x.mp4 --out y.webm --key-color 0x28680C

Unless --key-color is given, the ACTUAL background color is sampled from the
clip's own top-left corner. AI-generated "green screens" are never studio
0x00FF00 — a real MiniMax key came back ~0x28680C — so guessing at prompt-
writing time reliably fails while sampling reliably works. Blend is 0.0
(hard cutoff): any soft blend leaves dark hair semi-transparent against
dark desaturated keys.

Prints JSON: {"out": path, "key_color": "0xRRGGBB"}.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

SIMILARITY = 0.08
BLEND = 0.0


def sample_corner_color(video: Path) -> str | None:
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(video), "-frames:v", "1",
            "-vf", "scale=8:8", "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        capture_output=True,
    )
    if result.returncode != 0 or len(result.stdout) < 3:
        return None
    r, g, b = result.stdout[0], result.stdout[1], result.stdout[2]
    return f"0x{r:02X}{g:02X}{b:02X}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--key-color")
    args = ap.parse_args()

    src, out = Path(args.src), Path(args.out)
    if out.suffix != ".webm":
        raise SystemExit("output must be .webm (VP9 with alpha)")
    color = args.key_color or sample_corner_color(src)
    if not color:
        raise SystemExit(f"could not sample key color from {src}; pass --key-color")

    out.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
            "-vf", f"chromakey={color}:{SIMILARITY}:{BLEND},format=yuva420p",
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "2M", "-an",
            str(out),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg chromakey failed:\n{result.stderr[-400:]}")
    print(json.dumps({"out": str(out), "key_color": color}))


if __name__ == "__main__":
    main()
