# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=1.26", "opencv-python-headless>=4.9", "scenedetect>=0.6.4", "rapidfuzz>=3.9", "scipy>=1.14,<1.18"]
# ///
"""The render, checked against the plan — the full pass, with decoded frames.

Usage:
  video-studio qc_analyze --video out/video.mp4 --project projects/foo
  video-studio qc_analyze --video out/video.mp4 --project projects/foo --json
  video-studio qc_analyze ... --detectors container,visual,motion
  video-studio qc_analyze --list

There are two gates in this repo and they are not the same size. The
`video-production` skill bundles `qc_render.py`, which needs no install and
answers "does this file match its plan" from ffprobe and one ffmpeg pass. This
is the other one: it decodes frames and reports on the picture — blur, banding,
motion character, split-pane composition, audio structure, and with the model
extras, captions, objects and speech.

Install what you need, not everything:

  pip install 'video-studio-engine[qc] @ git+https://github.com/scrollmark/social-skills.git'

then optionally `[qc-ocr]` (captions, text layout), `[qc-yolo]` (planned
subjects, entity tracking), `[qc-face]` (lip sync), `[qc-clip]` (prompt fit).
A detector whose extra is absent SKIPS and says so; it never fails the run.

Ground truth is `<project>/plan.json`, which `build_props` already writes for
exactly this, plus `storyboard.json` for size and palette and
`audio/<scene>.timings.json` for caption words.

Exit 0 = no error-severity findings. Exit 1 = at least one.
"""

from __future__ import annotations

#: Installs come from the repo; the engine is not published to PyPI.
GIT_URL = "git+https://github.com/scrollmark/social-skills.git"

import argparse
import json
import sys


def main() -> None:
    from video_studio.qc.engine import KNOWN_DETECTORS, AnalyzeOptions, analyze

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--video")
    ap.add_argument("--project", help="the project directory holding plan.json")
    ap.add_argument("--detectors", help="comma-separated subset (default: all)")
    ap.add_argument("--evidence", help="directory for extracted evidence frames")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true", help="print detector names and exit")
    a = ap.parse_args()

    if a.list:
        for spec in KNOWN_DETECTORS:
            need = f"  [{spec.extra}]" if spec.extra else ""
            print(f"{spec.name}{need}")
        return

    if not a.video or not a.project:
        raise SystemExit("--video and --project are both required (or use --list)")

    wanted = None
    if a.detectors:
        wanted = {d.strip() for d in a.detectors.split(",") if d.strip()}
        known = {s.name for s in KNOWN_DETECTORS}
        unknown = sorted(wanted - known)
        if unknown:
            raise SystemExit(
                f"unknown detector(s): {', '.join(unknown)}\n"
                f"Run --list to see the {len(known)} that exist."
            )

    report = analyze(a.video, AnalyzeOptions(
        workdir=a.project, detectors=wanted, evidence_dir=a.evidence))
    data = report.to_json()
    findings = data.get("findings", [])
    errors = [f for f in findings if f.get("severity") == "error"]

    if a.json:
        print(json.dumps(data, indent=2, default=str))
    else:
        for f in findings:
            sev = (f.get("severity") or "info").upper()
            print(f"{sev:8} {f.get('id','?')}: {f.get('message','')}")
        skipped = data.get("detectorsSkipped") or []
        ran = data.get("detectorsRun") or []
        print(f"\n{len(ran)} detector(s) ran, {len(findings)} finding(s), "
              f"{len(errors)} at error severity.")
        if skipped:
            # A skip is not a pass. Saying which checks did not happen is the
            # difference between "clean" and "clean as far as we looked".
            missing = [s for s in skipped if s.get("code") == "missing_extra"]
            if missing:
                # Name the extra AND the command. Naming only the extra leaves
                # the reader to work out that it is bracketed onto a git URL,
                # and a guess that installs the wrong thing succeeds silently:
                # an unknown extra is a pip warning, not an error.
                by_extra: dict[str, list[str]] = {}
                for s in missing:
                    by_extra.setdefault(s.get("extra") or "?", []).append(s["name"])
                print(f"{len(missing)} check(s) did NOT run — a skip is not a pass:")
                for extra, names in sorted(by_extra.items()):
                    print(f"  {', '.join(sorted(names))}  needs [{extra}]")
                brackets = ",".join(sorted(by_extra))
                print(f"  pip install 'video-studio-engine[{brackets}] @ "
                      f"{GIT_URL}'")
            other = [s for s in skipped if s.get("code") != "missing_extra"]
            for s in other:
                print(f"skipped {s['name']}: {s.get('code')}")
        print("This reads the picture, not the point. Pull frames and look at them too.")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
