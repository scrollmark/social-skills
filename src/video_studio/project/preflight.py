# /// script
# requires-python = ">=3.11"
# ///
"""Refuse to render a build that is not actually finished.

Usage:
  video-studio preflight --composer composer/            # before render
  video-studio preflight --composer composer/ --json
  video-studio preflight --composer composer/ --allow-placeholders

Exit 0 = safe to render. Exit 1 = do not render; the reasons are printed.

Why this exists
---------------
A session shipped three consecutive renders that were entirely solid colored
boxes. Every layer was a placeholder, because `build_props.py --placeholders`
was left on for the final build and the summary still read {"unresolved": 0}.
Nobody looked at a frame. The user found it each time.

A second session shipped a narrated explainer with no narration: the voice
backend was missing, silent WAVs were written as a "workaround", and those
became the scene clock. Silent audio is indistinguishable from working audio
in every log line the pipeline prints.

Both are invisible in the render logs and obvious in one frame. This checks the
things a human would notice immediately and the pipeline never did.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import wave
from pathlib import Path
from video_studio.paths import studio_root

# Below this peak amplitude a WAV is silence for our purposes. Kokoro output
# sits far above it; a written-silence stand-in is exactly zero.
SILENCE_PEAK = 1e-4


def _peak(path: Path) -> float | None:
    """Peak amplitude in 0..1, or None if unreadable."""
    try:
        with wave.open(str(path), "rb") as wf:
            width = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())
    except Exception:
        # Not a plain PCM WAV — fall back to ffmpeg's volume meter.
        try:
            r = subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
                capture_output=True, text=True,
            )
            for line in r.stderr.splitlines():
                if "max_volume:" in line:
                    db = float(line.split("max_volume:")[1].strip().split()[0])
                    return 10 ** (db / 20)
        except Exception:
            return None
        return None
    if not frames or width not in (1, 2, 4):
        return None
    import array

    code = {1: "b", 2: "h", 4: "i"}[width]
    samples = array.array(code)
    samples.frombytes(frames[: len(frames) - (len(frames) % width)])
    if not samples:
        return None
    full = float(2 ** (8 * width - 1))
    return max(abs(min(samples)), abs(max(samples))) / full


def check(composer: Path, allow_placeholders: bool, project: str | None = None) -> dict:
    # Each project owns composer/props/<name>.json. The old single props.json is
    # still accepted so a half-migrated tree does not silently report "no
    # scenes" — but a named project always wins.
    if project:
        props_path = composer / "props" / f"{project}.json"
    else:
        legacy = composer / "props.json"
        candidates = sorted((composer / "props").glob("*.json"))
        if legacy.exists():
            props_path = legacy
        elif len(candidates) == 1:
            props_path = candidates[0]
        elif candidates:
            return {"ok": False, "blockers": [
                f"{len(candidates)} projects built — pass --project "
                f"({', '.join(c.stem for c in candidates)})"], "warnings": []}
        else:
            props_path = composer / "props.json"
    if not props_path.exists():
        return {"ok": False, "blockers": [f"no props.json at {props_path} — run build_props.py first"],
                "warnings": [], "scenes": 0}

    props = json.loads(props_path.read_text())
    scenes = props.get("scenes", [])
    blockers: list[str] = []
    warnings: list[str] = []
    public = composer / "public"

    if not scenes:
        blockers.append("props.json has no scenes")

    placeholder_layers = [
        f"{s['id']}/{l['id']}"
        for s in scenes
        for l in s.get("layers", [])
        if l.get("type") == "placeholder"
    ]
    if placeholder_layers:
        msg = (
            f"{len(placeholder_layers)} placeholder layer(s) would render as solid colored "
            f"boxes: {', '.join(placeholder_layers[:8])}"
            + (" ..." if len(placeholder_layers) > 8 else "")
        )
        (warnings if allow_placeholders else blockers).append(msg)

    # Every referenced media file must exist under public/ — props can name a
    # file that was never copied in, which renders as nothing at all.
    for s in scenes:
        for l in s.get("layers", []):
            src = l.get("src")
            if src and not (public / src).exists():
                blockers.append(f"{s['id']}/{l['id']}: props references {src}, missing under {public}")

    # Narration: present but silent is the failure that looks like success.
    narrated = [s for s in scenes if s.get("audio")]
    for s in narrated:
        wav = public / s["audio"]
        if not wav.exists():
            blockers.append(f"{s['id']}: audio {s['audio']} missing under {public}")
            continue
        peak = _peak(wav)
        if peak is not None and peak < SILENCE_PEAK:
            blockers.append(
                f"{s['id']}: narration track is SILENT ({s['audio']}) — a silence stand-in "
                "was used where speech was expected"
            )
    silent_scenes = [s["id"] for s in scenes if not s.get("audio")]
    if narrated and silent_scenes:
        warnings.append(f"scene(s) with no audio at all: {', '.join(silent_scenes)}")

    # Captions travel with narration; their absence usually means timings were
    # never written, which is the same root cause as silent narration.
    missing_caps = [s["id"] for s in narrated if not s.get("captions")]
    if missing_caps:
        warnings.append(f"narrated scene(s) with no captions: {', '.join(missing_caps)}")

    return {
        "ok": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "scenes": len(scenes),
        "placeholderLayers": placeholder_layers,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--composer", default=str(studio_root() / "composer"))
    ap.add_argument("--allow-placeholders", action="store_true",
                    help="demote the placeholder blocker to a warning (layout previews only)")
    ap.add_argument("--project", help="project name (composer/props/<name>.json)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = check(Path(args.composer), args.allow_placeholders, args.project)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for w in result["warnings"]:
            print(f"warning: {w}")
        for b in result["blockers"]:
            print(f"BLOCKER: {b}")
        print("preflight OK — safe to render" if result["ok"]
              else "\nDO NOT RENDER. Fix the blockers above, rebuild props, and re-run preflight.")
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
