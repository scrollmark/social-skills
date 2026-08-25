# /// script
# requires-python = ">=3.11"
# dependencies = ["faster-whisper>=1.0"]
# ///
"""Word timings for narration this studio did not synthesise.

Usage:
  video-studio gen_captions --audio projects/x/audio/hook.wav
  video-studio gen_captions --audio projects/x/audio/hook.wav \
      --timings-out projects/x/audio/hook.timings.json
  video-studio gen_captions --project projects/x        # every scene WAV
  video-studio gen_captions --project projects/x --force # redo existing

Why this exists: tts_kokoro already emits `<scene>.timings.json` beside every
WAV it synthesises, and build_props turns that into on-screen captions. Any
narration that did NOT come from Kokoro therefore has no timings at all — a
recorded voice, a client-supplied read, a track pulled off a camera. Those
scenes render silently uncaptioned, which is the failure this closes.

It writes EXACTLY the format tts_kokoro writes — a flat, scene-relative
`[{"text", "startMs", "endMs"}, ...]` — so build_props consumes the output of
either producer without knowing which one ran.

TRANSCRIPTION IS A GUESS. Kokoro knows what it was asked to say; whisper is
inferring words from audio, and it will mis-hear names, jargon and anything
said over music. Read what comes back before shipping it. Pass --text with the
known script to check the transcript against it — mismatches are reported, not
silently corrected, because deciding which one is wrong is a human's call.

The model runs LOCALLY (faster-whisper, CTranslate2). Nothing is uploaded.
First run downloads weights to ~/.cache/huggingface; `base` is ~150MB.

Prints JSON: {"audio", "timings", "words", "seconds", "model"}.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

#: Whisper sizes, smallest first. `base` is the default: on narration-grade
#: audio the accuracy gain from `small` is mostly on accents and noise, and
#: this runs on a laptop CPU.
MODELS = ("tiny", "base", "small", "medium", "large-v3")
DEFAULT_MODEL = "base"


def measured_seconds(path: Path) -> float | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return round(float(out), 3)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def merge_punctuation(timings: list[dict]) -> list[dict]:
    """Fold punctuation-only tokens onto the previous word.

    Same rule tts_kokoro applies. A lone "," rendered as its own caption is a
    frame of visible garbage, and whisper emits them more often than Kokoro.
    """
    out: list[dict] = []
    for t in timings:
        word = (t.get("text") or "").strip()
        if not word:
            continue
        if out and not any(c.isalnum() for c in word):
            out[-1]["text"] += word
            out[-1]["endMs"] = max(out[-1]["endMs"], t["endMs"])
            continue
        out.append({"text": word, "startMs": t["startMs"], "endMs": t["endMs"]})
    return out


def transcribe(audio: Path, model_name: str, language: str | None) -> list[dict]:
    """Word-level timings, scene-relative, in tts_kokoro's format."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit(
            "faster-whisper is not installed. Install the extra:\n"
            "  pip install 'video-studio-engine[captions] @ git+https://github.com/scrollmark/social-skills.git'\n"
            "It is optional because it pulls a ~200MB inference runtime that "
            "only this program needs."
        )

    # int8 on CPU is the portable choice; it is what makes `base` usable on a
    # laptop without a GPU, and caption timing does not need float precision.
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(
        str(audio), word_timestamps=True, language=language, vad_filter=True,
    )

    timings: list[dict] = []
    for segment in segments:
        for word in (segment.words or []):
            text = (word.word or "").strip()
            if not text:
                continue
            timings.append({
                "text": text,
                "startMs": max(0, round(word.start * 1000)),
                "endMs": max(0, round(word.end * 1000)),
            })
    return merge_punctuation(timings)


def compare_to_script(timings: list[dict], script: str) -> dict | None:
    """Report divergence between the transcript and a known script.

    Deliberately reports rather than corrects: aligning a mis-heard word to an
    intended one is a judgement about which is right, and getting that wrong
    silently is worse than saying they differ.
    """
    def norm(s: str) -> list[str]:
        return ["".join(c for c in w.lower() if c.isalnum())
                for w in s.split() if any(c.isalnum() for c in w)]

    heard, intended = norm(" ".join(t["text"] for t in timings)), norm(script)
    if heard == intended:
        return None
    only_heard = [w for w in heard if w not in set(intended)]
    only_script = [w for w in intended if w not in set(heard)]
    return {
        "heardWords": len(heard), "scriptWords": len(intended),
        "notInScript": only_heard[:12], "notHeard": only_script[:12],
    }


def run_one(audio: Path, timings_out: Path, model: str, language: str | None,
            script: str | None, force: bool) -> dict:
    if timings_out.exists() and not force:
        return {"audio": str(audio), "timings": str(timings_out),
                "skipped": "timings already exist — pass --force to redo"}
    if not audio.exists():
        raise SystemExit(f"no such audio: {audio}")

    timings = transcribe(audio, model, language)
    if not timings:
        raise SystemExit(
            f"whisper found no speech in {audio}. If the scene is meant to be "
            f"silent it needs no timings; if it is not, check the file is "
            f"narration and not music."
        )

    timings_out.parent.mkdir(parents=True, exist_ok=True)
    timings_out.write_text(json.dumps(timings, indent=2) + "\n")

    result = {
        "audio": str(audio), "timings": str(timings_out),
        "words": len(timings), "seconds": measured_seconds(audio), "model": model,
    }
    if script:
        divergence = compare_to_script(timings, script)
        if divergence:
            result["divergesFromScript"] = divergence
            print(f"warning: transcript differs from --text for {audio.name} "
                  f"— read {timings_out.name} before shipping.", file=sys.stderr)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--audio", help="one WAV to transcribe")
    ap.add_argument("--project", help="transcribe every audio/*.wav in a project")
    ap.add_argument("--timings-out", help="explicit output path (with --audio)")
    ap.add_argument("--model", default=DEFAULT_MODEL, choices=MODELS)
    ap.add_argument("--language", help="ISO code, e.g. en. Omit to auto-detect.")
    ap.add_argument("--text", help="the known script, to check the transcript against")
    ap.add_argument("--force", action="store_true",
                    help="overwrite timings that already exist")
    a = ap.parse_args()

    if bool(a.audio) == bool(a.project):
        raise SystemExit("pass exactly one of --audio or --project")

    if a.audio:
        audio = Path(a.audio).expanduser().resolve()
        out = (Path(a.timings_out).expanduser().resolve() if a.timings_out
               else audio.with_suffix(".timings.json"))
        print(json.dumps(run_one(audio, out, a.model, a.language, a.text, a.force),
                         indent=2))
        return

    project = Path(a.project).expanduser().resolve()
    audio_dir = project / "audio"
    wavs = sorted(audio_dir.glob("*.wav"))
    if not wavs:
        raise SystemExit(f"no WAVs in {audio_dir}")
    # --text describes one read, so it cannot be checked against a whole
    # directory of different scenes.
    results = [run_one(w, w.with_suffix(".timings.json"), a.model, a.language,
                       None, a.force) for w in wavs]
    print(json.dumps({
        "project": str(project),
        "transcribed": sum(1 for r in results if "words" in r),
        "skipped": sum(1 for r in results if "skipped" in r),
        "scenes": results,
    }, indent=2))


if __name__ == "__main__":
    main()
