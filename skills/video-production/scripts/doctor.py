# /// script
# requires-python = ">=3.11"
# ///
"""Report which sources are usable right now, per category.

Usage:
  uv run scripts/doctor.py            # human-readable
  uv run scripts/doctor.py --json     # machine-readable

Run this BEFORE offering sourcing options to a user. Offering a source that
turns out to have no key — or a spent quota — wastes their time and makes
the estimate wrong. Presence of a key is checked here; a key can still be
rejected at call time (spent quota, withdrawn model), which the individual
scripts report.

Checks tools too: without ffmpeg nothing measures, and without node nothing
renders.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# This script ships INSIDE its skill folder, so it cannot assume it sits in a
# checkout of the engine repo. Anything it used to resolve relative to that
# checkout is resolved against the user's project or their config directory
# instead — the two places a key actually lives once the engine is a pip
# install rather than a clone.
ENV_CANDIDATES = (
    Path.cwd() / ".env",
    Path.home() / ".config" / "video-studio" / ".env",
)


def load_env_file() -> None:
    """Read `.env` into os.environ (without overriding anything already set).
    Keys otherwise have to be exported by hand in every shell, which is how a
    key that exists reads as missing.

    First match wins: the project you are standing in, then your user-level
    config. A key kept in a checkout dies with the checkout."""
    for env in ENV_CANDIDATES:
        if not env.exists():
            continue
        for line in env.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        return

PROVIDERS = [
    # (category, label, env vars, cost note)
    # Keyless archives first: they are the only sources guaranteed to work in
    # a fresh environment, so an empty-env machine still has a real option.
    ("public-domain archive", "NASA", [], "free, no key — space/earth/science"),
    ("public-domain archive", "Wikimedia Commons", [], "free, no key — licence varies per item"),
    ("stock footage/images", "Pexels", ["PEXELS_API_KEY"], "free, no billing"),
    ("stock footage/images", "Pixabay", ["PIXABAY_API_KEY"], "free, cache results 24h"),
    ("stock footage/images", "Shutterstock", ["SHUTTERSTOCK_TOKEN", "SHUTTERSTOCK_KEY"],
     "search on free tier (100/hr); DOWNLOAD needs a paid subscription"),
    ("stock audio", "Freesound", ["FREESOUND_API_KEY"], "free, licence varies per sound"),
    ("generated video", "MiniMax", ["MINIMAX_API_KEY"], "~0.36 USD per 6s clip"),
    ("generated video", "Veo", ["GEMINI_API_KEY", "GOOGLE_API_KEY"], "~0.40 USD/s; free tier quota is small"),
    ("generated video", "Aggregator", ["REPLICATE_API_TOKEN"], "many models, one key"),
    ("generated images", "Gemini image", ["GEMINI_API_KEY", "GOOGLE_API_KEY"], "~0.03 USD/still; NO free tier — needs billing on the key"),
    ("generated images", "Aggregator", ["REPLICATE_API_TOKEN"], "flux / ideogram etc."),
    ("generated audio", "Lyria", ["GEMINI_API_KEY", "GOOGLE_API_KEY"], "clean terms; NEEDS BILLING — free tier quota is literally 0"),
    ("generated audio", "ElevenLabs Music", ["ELEVENLABS_API_KEY"], "clean commercial terms; licensed training catalogue, from ~6 USD/mo"),
    ("generated audio", "MiniMax music", ["MINIMAX_API_KEY"], "works unbilled; RIGHTS UNSETTLED — internal use only"),
    ("generated audio", "Aggregator", ["REPLICATE_API_TOKEN"], "musicgen / stable-audio"),
    # Availability is import-checked, not assumed — see check_local_voice().
    ("voice", "Local voice", [], "free, runs locally"),
]

TOOLS = [("ffmpeg", "measurement, keying, loudness"), ("ffprobe", "duration probing"), ("node", "rendering")]


def check_caption_burn() -> tuple[str, bool, str]:
    """Whether the ffmpeg on PATH can burn captions, not merely whether it exists.

    Homebrew's mainline `ffmpeg` is a slim build: no libass, so no `subtitles`
    filter. It measures, trims, keys and renders perfectly, reports a healthy
    version, and then `burn_captions` fails — the one failure a presence check
    cannot see. On macOS the build that works is `ffmpeg-full`, which is
    keg-only and has to be put on PATH by hand.
    """
    import subprocess

    if shutil.which("ffmpeg") is None:
        ok = False
    else:
        try:
            r = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                               capture_output=True, text=True, timeout=30)
            ok = any(line.split()[1:2] == ["subtitles"]
                     for line in r.stdout.splitlines() if line.strip())
        except (OSError, subprocess.SubprocessError):
            ok = False
    return ("caption burn-in", ok, "ffmpeg needs libass for the `subtitles` filter — on a Mac, ffmpeg-full")

# The step-8 quality gate, in the two sizes it actually ships in.
#
# This list used to name `showwatcher`, and that was worse than useless: it was
# never published anywhere, so the doctor reported a gap that no reader could
# close, no matter what they installed. Both replacements are real and both are
# reachable, so a `--` here is now something you can act on.
QUALITY_GATE = [
    ("qc_render", "render gate (step 8), bundled — checks a render against its plan"),
    ("qc_analyze", "frame gate (step 8) — `video-studio qc_analyze`; needs the [qc] extra"),
]


def check_quality_gate() -> list[tuple[str, bool, str]]:
    """Resolve both gates the way each is actually reached.

    `qc_render.py` is a bundled sibling of this script, so it is found on disk
    rather than on PATH. It ships with `video-production`; this file is a
    byte-identical copy in `studio-setup`, which does not bundle it, so look in
    the sibling skill too. `.resolve()` first — these skills are installed as
    symlinks into ~/.claude/skills, and the sibling only exists in the repo the
    link points at.
    """
    here = Path(__file__).resolve().parent
    candidates = [here / "qc_render.py",
                  here.parent.parent / "video-production" / "scripts" / "qc_render.py"]
    bundled = any(c.exists() for c in candidates)
    # The frame gate is a subcommand of the engine CLI, not a binary of its own,
    # and the CLI being on PATH does NOT mean it can run: the engine imports
    # numpy at module scope, so without the [qc] extra it is present and
    # useless. `which` reported OK in exactly that state. Ask it instead —
    # `--list` is the cheapest call that exercises the same imports a real run
    # needs, and it is the same reasoning as check_local_voice() above.
    import subprocess

    try:
        deep = subprocess.run(
            ["video-studio", "qc_analyze", "--list"],
            capture_output=True, text=True, timeout=60,
        ).returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        deep = False
    available = {"qc_render": bundled, "qc_analyze": deep}
    return [(tool, available[tool], why) for tool, why in QUALITY_GATE]


def check_local_voice() -> tuple[bool, str]:
    """Ask the voice script itself, in ITS environment, whether it can run.

    Two wrong answers preceded this one. It first claimed "always available"
    without checking, and a session that trusted that shipped a voiceless
    explainer. The fix then import-checked from THIS process — but each script
    declares its own dependencies and uv runs it in its own environment, so
    the backend is absent here even when synthesis works perfectly. That
    reported "not installed" while narration was being produced successfully.

    The only honest check is to run the thing that will actually run.
    """
    import subprocess

    # tts_kokoro is not bundled with this skill — it carries real dependencies
    # (kokoro, soundfile, numpy) and lives in the video-studio-engine package.
    # Ask the installed CLI, which runs in the environment synthesis will use.
    try:
        r = subprocess.run(
            ["video-studio", "tts_kokoro", "--check"],
            capture_output=True, text=True, timeout=300,
        )
    except FileNotFoundError:
        return False, "not installed — pip install 'video-studio-engine[audio] @ https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz'"
    except subprocess.TimeoutExpired:
        return False, "voice check timed out (first run installs dependencies; retry)"
    if r.returncode == 0:
        try:
            return True, json.loads(r.stdout.strip().splitlines()[-1]).get("detail", "free, runs locally")
        except Exception:
            return True, "free, runs locally"
    detail = (r.stdout or r.stderr or "").strip().splitlines()
    hint = ""
    if detail:
        try:
            hint = json.loads(detail[-1]).get("detail", "")
        except Exception:
            hint = detail[-1][:120]
    if sys.version_info >= (3, 13) and "blis" in hint.lower():
        hint += f" (needs Python 3.12; {sys.version_info.major}.{sys.version_info.minor} cannot build its deps)"
    return False, f"unavailable — {hint or 'see: uv run scripts/tts_kokoro.py --check'}"


def status() -> dict:
    out = {"providers": [], "tools": []}
    for category, label, envs, note in PROVIDERS:
        if category == "voice":
            available, note = check_local_voice()
        else:
            available = True if not envs else any(os.environ.get(e) for e in envs)
        out["providers"].append({
            "category": category, "provider": label,
            "available": available, "env": envs, "note": note,
        })
    for tool, why in TOOLS:
        out["tools"].append({"tool": tool, "available": shutil.which(tool) is not None, "why": why})
    tool, available, why = check_caption_burn()
    out["tools"].append({"tool": tool, "available": available, "why": why, "optional": True})
    for tool, available, why in check_quality_gate():
        out["tools"].append({
            "tool": tool, "available": available, "why": why, "optional": True,
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    load_env_file()
    s = status()
    if args.json:
        print(json.dumps(s, indent=2))
        return

    current = None
    for p in s["providers"]:
        if p["category"] != current:
            current = p["category"]
            print(f"\n{current}:")
        mark = "OK " if p["available"] else "-- "
        env = f"  ({'/'.join(p['env'])})" if p["env"] and not p["available"] else ""
        print(f"  {mark}{p['provider']:<18}{p['note']}{env}")

    print("\ntools:")
    for t in s["tools"]:
        print(f"  {'OK ' if t['available'] else '-- '}{t['tool']:<18}{t['why']}")

    voice = next((p for p in s["providers"] if p["category"] == "voice"), None)
    if voice and not voice["available"]:
        # Called out separately because every narrated format depends on it and
        # the failure mode (silent WAVs standing in for narration) is quiet.
        print(f"\nNARRATION UNAVAILABLE: {voice['note']}")
        print("  Do NOT substitute silence for failed narration — fix the voice or tell the user.")

    missing = [p for p in s["providers"] if not p["available"]]
    if missing:
        cats = sorted({p["category"] for p in missing if not any(
            q["available"] for q in s["providers"] if q["category"] == p["category"])})
        if cats:
            print(f"\nNo source at all for: {', '.join(cats)}")


if __name__ == "__main__":
    main()
