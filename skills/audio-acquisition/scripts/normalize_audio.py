# /// script
# requires-python = ">=3.11"
# ///
"""Normalise a rendered video's loudness to the social-platform target.

Usage: uv run scripts/normalize_audio.py --in out/video.mp4 [--lufs -14]

Renders come out quiet (local voice synthesis is conservative), and the
quality check flags anything far from about -14 LUFS because platforms
re-normalise on upload and can pump artefacts doing it. Video is stream-
copied, so this is fast and lossless picture-side.

Prints JSON: {"out": path, "lufs_target": float}.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def normalize(src: Path, lufs: float) -> None:
    tmp = Path(tempfile.mkdtemp()) / src.name
    r = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(tmp)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"loudnorm failed:\n{r.stderr[-400:]}")
    shutil.move(str(tmp), str(src))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--lufs", type=float, default=-14.0)
    args = ap.parse_args()
    normalize(Path(args.src), args.lufs)
    print(json.dumps({"out": args.src, "lufs_target": args.lufs}))
if __name__ == "__main__":
    main()
