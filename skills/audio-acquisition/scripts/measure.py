# /// script
# requires-python = ">=3.11"
# ///
"""Measure media durations, dimensions, and a track's energy structure.

Usage:
  uv run scripts/measure.py FILE [FILE...]     durations + dimensions
  uv run scripts/measure.py --music TRACK      where the music actually changes

The measured narration duration IS the scene clock — plans estimate,
measurements decide (see references/api-landmines.md, "Clocks").

--music exists because "cut to the music" is otherwise guesswork. It reports a
per-second loudness profile and, more usefully, the transitions: the points
where a window jumps or drops at least 3 dB against the trailing three seconds.
Those are the drops, breakdowns and lifts, and they are the only defensible
places to change section.

Two things it prevents, both observed:

  Cutting on a grid. Sections placed every N seconds drift out of phase with
  the track within about twenty seconds and read as arbitrary.

  Ending mid-phrase. A fade placed in the quiet bar BEFORE a final chorus
  sounds like the video was cut off, because it was. `end` reports where the
  track actually resolves, which is where the video should stop.
"""

from __future__ import annotations

import json
import re
import statistics
import subprocess
import sys


def probe(path: str) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=width,height,codec_type",
            "-of", "json", path,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {result.stderr.strip()[:200]}")
    data = json.loads(result.stdout)
    seconds = float(data.get("format", {}).get("duration", 0.0))
    width = height = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" or ("width" in stream and "height" in stream):
            width = stream.get("width", width)
            height = stream.get("height", height)
    return {"seconds": seconds, "width": width, "height": height}


def music(path: str, jump_db: float = 3.0) -> dict:
    """Per-second loudness, the significant transitions, and where it ends."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-af",
         "astats=metadata=1:reset=1,"
         "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    times, levels, cur = [], [], None
    for line in proc.stdout.splitlines():
        m = re.match(r"frame:\d+\s+pts:\d+\s+pts_time:([\d.]+)", line)
        if m:
            cur = float(m.group(1))
        m2 = re.search(r"RMS_level=(-?[\d.]+)", line)
        if m2 and cur is not None:
            levels.append(float(m2.group(1)))
            times.append(cur)
    if not times:
        raise SystemExit(f"no audio measured in {path} — is there an audio stream?")

    buckets: dict[int, list[float]] = {}
    for t, v in zip(times, levels):
        buckets.setdefault(int(t), []).append(v)
    keys = sorted(buckets)
    mean = {k: statistics.mean(buckets[k]) for k in keys}

    transitions = []
    for i in range(4, len(keys) - 1):
        prior = statistics.mean([mean[keys[j]] for j in range(i - 3, i)])
        delta = mean[keys[i]] - prior
        if abs(delta) >= jump_db:
            transitions.append({"at": keys[i], "deltaDb": round(delta, 2),
                                "toDb": round(mean[keys[i]], 2)})

    # Where it resolves: the last second still above the track's own noise
    # floor. Cutting after this point adds silence; cutting before it truncates.
    floor = min(mean.values()) + 6.0
    audible = [k for k in keys if mean[k] > floor]
    end = (audible[-1] + 1) if audible else keys[-1]

    return {
        "seconds": round(times[-1], 2),
        "endsAt": end,
        "loudestAt": max(mean, key=mean.get),
        "transitions": transitions,
        "profile": {str(k): round(mean[k], 2) for k in keys},
    }


def main(argv: list[str]) -> None:
    if argv and argv[0] == "--music":
        if len(argv) < 2:
            raise SystemExit("usage: measure.py --music TRACK")
        print(json.dumps(music(argv[1]), indent=2))
        return
    if not argv:
        raise SystemExit("usage: measure.py FILE [FILE...]  |  --music TRACK")
    print(json.dumps({p: probe(p) for p in argv}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
