#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Narration via ElevenLabs — the paid alternative to the local voice.

    video-studio tts_eleven --list
    video-studio tts_eleven --text "..." --voice <id> --out audio/hook.wav

The local voice (`tts_kokoro.py`) is free, runs offline, and returns word
timings, so it stays the default and the only option for captioned formats.
Reach for this one when the read itself is the deliverable — a brand film,
a client voice, anything where the local voice's flat delivery is the thing
someone would complain about.

Two caveats worth knowing before you spend:
  - No word timings. Captions are driven by those, so a captioned format
    still needs the local voice. Duration is measured off the file.
  - Billed per character. ~1,100 characters is a 90-second script; check
    the account's own rate before a long batch.

Caches like tts_kokoro: identical text+voice+settings is a no-op that
reports {"cached": true}, so a re-run over unchanged scenes costs nothing.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx

API = "https://api.elevenlabs.io/v1"


def key() -> str:
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        sys.exit("Set ELEVENLABS_API_KEY (see .env)")
    return k


def measure(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout
    return round(float(out.strip()), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--voice", default="")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--stability", type=float, default=0.45)
    ap.add_argument("--similarity", type=float, default=0.75)
    ap.add_argument("--style", type=float, default=0.0)
    ap.add_argument("--speed", type=float, default=1.0,
                    help="post-hoc tempo via ffmpeg atempo; 1.0 leaves it alone")
    ap.add_argument("--out")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if a.list:
        r = httpx.get(f"{API}/voices", headers={"xi-api-key": key()}, timeout=60)
        r.raise_for_status()
        for v in r.json().get("voices", []):
            lab = v.get("labels") or {}
            bits = " ".join(f"{k}={lab[k]}" for k in ("gender", "age", "accent", "use_case")
                            if lab.get(k))
            print(f'{v["voice_id"]:24s} {v["name"][:22]:24s} {bits}')
        return

    if not a.text or not a.out:
        ap.error("--text and --out are required")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    stamp = out.with_suffix(".voice.json")
    sig = hashlib.sha256(
        f"{a.voice}|{a.model}|{a.stability}|{a.similarity}|{a.style}|{a.speed}|{a.text.strip()}"
        .encode()).hexdigest()[:16]
    if out.exists() and stamp.exists() and not a.force:
        if json.loads(stamp.read_text()).get("sig") == sig:
            print(json.dumps({"out": str(out), "seconds": measure(out), "cached": True}))
            return

    r = httpx.post(
        f"{API}/text-to-speech/{a.voice}",
        headers={"xi-api-key": key(), "content-type": "application/json"},
        json={"text": a.text, "model_id": a.model,
              "voice_settings": {"stability": a.stability,
                                 "similarity_boost": a.similarity,
                                 "style": a.style, "use_speaker_boost": True}},
        timeout=300)
    if r.status_code >= 400:
        sys.exit(f"{r.status_code}: {r.text[:400]}")

    raw = out.with_suffix(".raw.mp3")
    raw.write_bytes(r.content)
    filt = [] if abs(a.speed - 1.0) < 1e-3 else ["-af", f"atempo={a.speed:.3f}"]
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), *filt,
                    "-ar", "24000", "-ac", "1", str(out)], check=True)
    raw.unlink(missing_ok=True)
    stamp.write_text(json.dumps({"sig": sig}))
    print(json.dumps({"out": str(out), "seconds": measure(out), "cached": False}))


if __name__ == "__main__":
    main()
