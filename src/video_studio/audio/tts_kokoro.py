# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["kokoro>=0.9.0", "soundfile", "numpy"]
# ///
"""Kokoro TTS: narration WAV + word timings, or measured silence.

Usage:
  video-studio tts_kokoro --text "Hello there" --voice am_adam \
      --out audio/hook.wav --timings-out audio/hook.timings.json
  video-studio tts_kokoro --silence 4.0 --out audio/beat.wav

Never call with empty text — Kokoro raises "returned no audio"; use
--silence for deliberate quiet beats (writes real silence so downstream
audio concatenation clocks stay aligned).

Timings format: [{"text": word, "startMs": int, "endMs": int}, ...] —
punctuation-only tokens are merged onto the preceding word (Kokoro stamps
trailing punctuation at the NEXT word's start, which otherwise puts stray
marks at the front of caption pages).

Prints JSON to stdout: {"out": path, "seconds": float, "words": int}.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SAMPLE_RATE = 24000


def voice_key(text: str, voice: str, speed: float) -> str:
    """Identity of a narration render: same inputs -> same key."""
    return hashlib.sha256(f"{voice}|{speed}|{text.strip()}".encode()).hexdigest()[:16]
_PUNCT_ONLY_RE = re.compile(r"^[.,!?;:\"')\]]+$")


def merge_punctuation(timings: list[dict]) -> list[dict]:
    """Merge punctuation-only tokens onto the previous word's caption."""
    merged: list[dict] = []
    for t in timings:
        word = (t.get("text") or "").strip()
        if not word:
            continue
        if merged and _PUNCT_ONLY_RE.match(word):
            prev = merged[-1]
            prev["text"] += word
            prev["endMs"] = max(prev["endMs"], t["endMs"])
            continue
        merged.append(dict(t))
    return merged


def write_silence(out: Path, seconds: float) -> float:
    import wave

    out.parent.mkdir(parents=True, exist_ok=True)
    frames = int(seconds * SAMPLE_RATE)
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"\x00\x00" * frames)
    return seconds


INSTALL_HINT = """\
The local voice backend is not installed (or is broken).

  python3 -m pip install kokoro soundfile
  python3 -m spacy download en_core_web_sm

On Python 3.13 that install FAILS: kokoro pulls spacy -> thinc -> blis, and
blis has no 3.13 wheel, so pip tries to cythonize it and dies. That is why the
PEP 723 header above pins <3.13 — uv then selects (and downloads, if needed) a
3.12 interpreter on its own, so `uv run` works without any of the below. These
steps are only for running the module outside uv:

  uv venv --python 3.12 .venv-tts
  uv pip install --python .venv-tts/bin/python kokoro soundfile
  VIRTUAL_ENV=$PWD/.venv-tts .venv-tts/bin/python scripts/tts_kokoro.py ...

(VIRTUAL_ENV must be set: kokoro shells out to `uv pip install` for its spacy
model on first run, and that subprocess fails without it.)

Do NOT work around this with --silence. Silent WAVs become the scene clock, so
the render ships with no narration and no captions while still looking like a
successful build.\
"""


def synthesize(text: str, voice: str, speed: float, out: Path) -> tuple[float, list[dict]]:
    import numpy as np
    import soundfile as sf

    try:
        from kokoro import KPipeline
    except ImportError as exc:
        raise SystemExit(f"{exc}\n\n{INSTALL_HINT}") from exc

    pipeline = KPipeline(lang_code="a")
    chunks = list(pipeline(text, voice=voice, speed=speed))
    if not chunks:
        raise RuntimeError(f"Kokoro returned no audio for: {text[:60]!r}")

    audio_arrays = []
    timings: list[dict] = []
    offset = 0.0
    for chunk in chunks:
        chunk_audio = chunk[2]
        if chunk_audio is None:
            continue
        for token in getattr(chunk, "tokens", None) or []:
            word = (getattr(token, "text", "") or "").strip()
            start_ts = getattr(token, "start_ts", None)
            end_ts = getattr(token, "end_ts", None)
            if word and start_ts is not None and end_ts is not None:
                timings.append({
                    "text": word,
                    "startMs": round((offset + float(start_ts)) * 1000),
                    "endMs": round((offset + float(end_ts)) * 1000),
                })
        audio_arrays.append(chunk_audio)
        offset += len(chunk_audio) / SAMPLE_RATE
    if not audio_arrays:
        raise RuntimeError(f"Kokoro returned empty audio for: {text[:60]!r}")

    audio = np.concatenate(audio_arrays)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), audio, SAMPLE_RATE)
    return len(audio) / SAMPLE_RATE, merge_punctuation(timings)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--text-file")
    ap.add_argument("--silence", type=float, help="write N seconds of silence instead of speech")
    ap.add_argument("--voice", default="af_heart")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true",
                    help="report whether synthesis can actually run here, then exit")
    ap.add_argument("--timings-out")
    ap.add_argument("--force", action="store_true",
                    help="re-synthesize even if an identical render already exists")
    args = ap.parse_args()

    if args.check:
        # Probed from THIS environment — the one synthesis actually runs in.
        # Checking from another process's env reports on the wrong thing.
        try:
            from kokoro import KPipeline  # noqa: F401
        except Exception as exc:
            print(json.dumps({"ok": False, "detail": f"{type(exc).__name__}: {exc}"[:160]}))
            raise SystemExit(1)
        print(json.dumps({"ok": True, "detail": "free, runs locally"}))
        return

    if not args.out:
        raise SystemExit("--out is required")
    out = Path(args.out)
    if args.silence is not None:
        seconds = write_silence(out, args.silence)
        print(json.dumps({"out": str(out), "seconds": seconds, "words": 0}))
        return

    text = args.text or (Path(args.text_file).read_text() if args.text_file else "")
    if not text.strip():
        raise SystemExit("Empty text — use --silence for deliberate quiet beats")

    # Skip when this exact text/voice/speed has already been rendered here.
    # Not only a speed win: a re-render can come back a few ms different, and
    # scene durations are measured from these files — so re-synthesizing an
    # unchanged scene silently shifts every cut after it, including layout the
    # user already approved in the editor.
    stamp = out.with_suffix(".voice.json")
    key = voice_key(text, args.voice, args.speed)
    if not args.force and out.exists() and out.stat().st_size > 0 and stamp.exists():
        try:
            prev = json.loads(stamp.read_text())
        except json.JSONDecodeError:
            prev = {}
        if prev.get("key") == key:
            print(json.dumps({"out": str(out), "seconds": prev.get("seconds"),
                              "words": prev.get("words"), "cached": True}))
            return

    seconds, timings = synthesize(text, args.voice, args.speed, out)
    stamp.write_text(json.dumps(
        {"key": key, "seconds": seconds, "words": len(timings)}, indent=2))
    if args.timings_out:
        Path(args.timings_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.timings_out).write_text(json.dumps(timings, indent=2))
    print(json.dumps({"out": str(out), "seconds": seconds, "words": len(timings)}))


if __name__ == "__main__":
    main()
