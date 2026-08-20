#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""The render, checked against the plan it was built from.

Usage:
  uv run scripts/qc_render.py --video out/video.mp4 --plan project/plan.json
  uv run scripts/qc_render.py --video out/video.mp4 --plan project/plan.json \
      --storyboard project/storyboard.json      # also check size and fps
  uv run scripts/qc_render.py ... --tolerance 0.25    # looser duration match
  uv run scripts/qc_render.py ... --json              # machine-readable

Step 8 already had three of its four parts covered by scripts that ship here:
`poster.py` pulls frames, `measure.py` reports duration, `normalize_audio.py`
handles loudness. What none of them could answer is whether the file that came
out is the video that was PLANNED — and that is the part the gate was resting
on somebody remembering.

`build_props` writes `plan.json` for exactly this, with the measured durations
the render actually used, so the comparison is against reality rather than the
storyboard's estimate. This reads that file back.

WHAT IT CHECKS
  duration    the render's length against the plan's total
  clocks      the plan's own total against the sum of its scenes — an
              inconsistency here means the plan was wrong before the render
              ever started, and comparing against it proves nothing
  container   resolution, fps and pixel format (needs --storyboard)
  black tail  a run of black frames at the very end, the classic sign of a
              composition that outlived its content
  freeze      a frozen final stretch, which reads as a hang rather than an end

It does NOT judge whether the video is any good. Blur, banding, caption
overlap, off-palette colour and lip sync all need decoded frames and, mostly,
models — that is a different tool with a different dependency budget. Pull
frames with `poster.py` and look at them. This checks the claims that can be
checked without opening the picture.

Exit 0 = nothing failed. Exit 1 = at least one ERROR finding. WARN never fails
the gate on its own.

Prints a short report, or JSON with --json.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

#: Seconds of drift tolerated between the plan and the render before it is an
#: error. A frame at 30fps is 0.033s; a tenth of a second is three frames and
#: already visible against narration.
DEFAULT_TOLERANCE = 0.15

#: A black run shorter than this at the tail is a fade, not a fault.
BLACK_TAIL_MIN = 0.30

#: How close to the end a black or frozen run must start to count as a tail.
TAIL_WINDOW = 0.75


def ffprobe(video: Path) -> dict:
    """Container facts. Raises SystemExit with the tool's own words on failure."""
    cmd = ["ffprobe", "-v", "error", "-print_format", "json",
           "-show_format", "-show_streams", str(video)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except FileNotFoundError:
        raise SystemExit("ffprobe not found — install ffmpeg.")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ffprobe could not read {video}:\n  {(exc.stderr or '').strip()}")
    return json.loads(out)


def video_stream(probe: dict) -> dict:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    raise SystemExit("no video stream in that file — is it audio only?")


def parse_fps(rate: str) -> float | None:
    """'30000/1001' -> 29.97. Returns None rather than guessing."""
    try:
        num, _, den = rate.partition("/")
        return round(int(num) / int(den or 1), 3)
    except (ValueError, ZeroDivisionError):
        return None


def detect_black_and_freeze(video: Path, duration: float) -> tuple[list, list]:
    """One ffmpeg pass, two filters, no decode on our side.

    ffmpeg prints its findings to stderr as it goes; we read them back rather
    than decoding frames ourselves, which keeps this a stdlib script.
    """
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
           "-vf", "blackdetect=d=0.1:pix_th=0.10,freezedetect=n=-60dB:d=0.5",
           "-an", "-f", "null", "-"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        raise SystemExit("ffmpeg not found — install ffmpeg.")
    err = proc.stderr or ""

    black = [
        {"start": float(m.group(1)), "end": float(m.group(2)), "duration": float(m.group(3))}
        for m in re.finditer(
            r"black_start:([\d.]+)\s+black_end:([\d.]+)\s+black_duration:([\d.]+)", err)
    ]
    # A freeze matters when it runs to the END of the file, which is not the
    # same as starting near it: a two-second freeze on a five-second video
    # starts at 3s, nowhere near any sensible "tail window". So pair each
    # freeze_start with its freeze_end, and treat a start with no end as
    # running to the last frame — that is exactly what ffmpeg reports for a
    # video that finishes frozen.
    events = [(m.start(), m.group(1), m.group(2))
              for m in re.finditer(r"freeze_(start|end):\s*([\d.]+)", err)]
    freeze, pending = [], None
    for _, kind, value in events:
        if kind == "start":
            if pending is not None:
                freeze.append({"start": pending, "end": None})
            pending = float(value)
        elif pending is not None:
            freeze.append({"start": pending, "end": float(value)})
            pending = None
    if pending is not None:
        freeze.append({"start": pending, "end": None})
    return black, freeze


def check(video: Path, plan: dict, storyboard: dict | None, tolerance: float) -> list[dict]:
    findings: list[dict] = []

    def add(level, code, message, **extra):
        findings.append({"level": level, "code": code, "message": message, **extra})

    probe = ffprobe(video)
    stream = video_stream(probe)
    actual = float(probe.get("format", {}).get("duration", 0.0))

    # ── the clocks ───────────────────────────────────────────────────────
    scenes = plan.get("scenes") or []
    scene_total = round(sum(float(s.get("duration", 0)) for s in scenes), 3)
    planned = float(plan.get("totalDuration", scene_total))

    # Check the plan against ITSELF first. If its total disagrees with its own
    # scenes, every other comparison here is measuring against a broken ruler,
    # and reporting the render as wrong would point at the wrong thing.
    if scenes and abs(planned - scene_total) > 0.05:
        add("ERROR", "plan-inconsistent",
            f"the plan disagrees with itself: totalDuration {planned}s but its "
            f"{len(scenes)} scenes sum to {scene_total}s. Re-run build_props "
            f"before trusting anything else here.",
            planned=planned, sceneTotal=scene_total)

    drift = round(actual - planned, 3)
    if abs(drift) > tolerance:
        add("ERROR", "duration-drift",
            f"render is {actual:.3f}s, plan says {planned:.3f}s "
            f"({drift:+.3f}s, tolerance ±{tolerance}s)",
            actual=actual, planned=planned, drift=drift)
    else:
        add("OK", "duration", f"{actual:.3f}s, within ±{tolerance}s of plan",
            actual=actual, planned=planned, drift=drift)

    # ── container ────────────────────────────────────────────────────────
    width, height = stream.get("width"), stream.get("height")
    fps = parse_fps(stream.get("r_frame_rate", ""))
    pix_fmt = stream.get("pix_fmt")

    if pix_fmt and pix_fmt != "yuv420p":
        add("WARN", "pix-fmt",
            f"pixel format is {pix_fmt}, not yuv420p — some platforms and "
            f"players will not decode it", pixFmt=pix_fmt)

    if storyboard:
        want_w = int(storyboard.get("width", 1080))
        want_h = int(storyboard.get("height", 1920))
        want_fps = float(storyboard.get("fps", 30))
        if (width, height) != (want_w, want_h):
            add("ERROR", "resolution",
                f"render is {width}x{height}, storyboard says {want_w}x{want_h}",
                actual=f"{width}x{height}", expected=f"{want_w}x{want_h}")
        else:
            add("OK", "resolution", f"{width}x{height}")
        if fps is not None and abs(fps - want_fps) > 0.5:
            add("ERROR", "fps", f"render is {fps}fps, storyboard says {want_fps}fps",
                actual=fps, expected=want_fps)
        else:
            add("OK", "fps", f"{fps}fps")
    else:
        add("OK", "container", f"{width}x{height} @ {fps}fps, {pix_fmt} "
                               f"(pass --storyboard to check these against the plan)")

    # ── the tail ─────────────────────────────────────────────────────────
    black, freeze = detect_black_and_freeze(video, actual)

    tail_black = [b for b in black
                  if b["duration"] >= BLACK_TAIL_MIN and b["end"] >= actual - TAIL_WINDOW]
    if tail_black:
        worst = max(tail_black, key=lambda b: b["duration"])
        add("ERROR", "black-tail",
            f"{worst['duration']:.2f}s of black ending the video (from "
            f"{worst['start']:.2f}s) — the composition outlived its content",
            start=worst["start"], duration=worst["duration"])

    mid_black = [b for b in black if b not in tail_black and b["duration"] >= BLACK_TAIL_MIN]
    if mid_black:
        add("WARN", "black-gap",
            f"{len(mid_black)} black run(s) inside the video, longest "
            f"{max(b['duration'] for b in mid_black):.2f}s — intended as a cut to "
            f"black, or a missing clip?",
            runs=[{"start": b["start"], "duration": b["duration"]} for b in mid_black[:5]])

    tail_freeze = [f for f in freeze
                   if f["end"] is None or f["end"] >= actual - TAIL_WINDOW]
    if tail_freeze:
        first = min(tail_freeze, key=lambda f: f["start"])
        held = round(actual - first["start"], 2)
        add("WARN", "freeze-tail",
            f"picture freezes at {first['start']:.2f}s and never moves again — "
            f"{held}s of held frame to the end, which reads as a hang rather "
            f"than an ending", start=first["start"], heldSeconds=held)

    if not tail_black and not tail_freeze:
        add("OK", "tail", "ends on moving picture, no black tail")

    return findings


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--video", required=True)
    ap.add_argument("--plan", required=True, help="project/plan.json from build_props")
    ap.add_argument("--storyboard", help="to also check resolution and fps")
    ap.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE,
                    help=f"seconds of duration drift allowed (default {DEFAULT_TOLERANCE})")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    video = Path(a.video).expanduser()
    if not video.exists():
        raise SystemExit(f"no such video: {video}")
    plan_path = Path(a.plan).expanduser()
    if not plan_path.exists():
        raise SystemExit(
            f"no plan at {plan_path} — build_props writes it beside the project. "
            f"Without it there is nothing to check the render against."
        )
    plan = json.loads(plan_path.read_text())
    storyboard = None
    if a.storyboard:
        sb_path = Path(a.storyboard).expanduser()
        if not sb_path.exists():
            raise SystemExit(f"no storyboard at {sb_path}")
        storyboard = json.loads(sb_path.read_text())

    findings = check(video, plan, storyboard, a.tolerance)
    errors = [f for f in findings if f["level"] == "ERROR"]
    warns = [f for f in findings if f["level"] == "WARN"]

    if a.json:
        print(json.dumps({
            "video": str(video), "plan": str(plan_path),
            "errors": len(errors), "warnings": len(warns),
            "findings": findings,
        }, indent=2))
    else:
        for f in findings:
            mark = {"OK": "  ok  ", "WARN": " warn ", "ERROR": "FAIL  "}[f["level"]]
            print(f"{mark} {f['code']}: {f['message']}")
        print()
        if errors:
            print(f"{len(errors)} failure(s), {len(warns)} warning(s). "
                  f"This gate checks the plan, not the picture — pull frames with "
                  f"poster.py and look at them too.")
        else:
            print(f"passes against the plan ({len(warns)} warning(s)). "
                  f"That is not the same as looking good: pull frames with "
                  f"poster.py before calling it done.")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
