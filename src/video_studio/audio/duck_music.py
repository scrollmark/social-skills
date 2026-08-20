# /// script
# requires-python = ">=3.11"
# ///
"""Duck the music bed under the narration. A post-pass over built props.

Usage:
  uv run scripts/duck_music.py --composer composer/ --project projects/foo
  uv run scripts/duck_music.py --composer composer/ --project projects/foo \
      --base 0.16 --depth 0.65          # louder bed / deeper dip
  uv run scripts/duck_music.py ... --dry-run    # report, write nothing

RUN THIS AFTER build_props AND BEFORE rendering. It reads the props file that
build_props wrote, adds a per-frame volume envelope to `props.music`, and writes
the file back. build_props is the authority on the clock, so re-running it
overwrites the envelope — duck again afterwards. Running duck twice is
harmless; the envelope is recomputed from the narration, never from itself.

Why derive from props rather than from the storyboard: build_props snaps scene
boundaries on the CUMULATIVE total, not per scene, precisely so rounding error
cannot accumulate down the timeline. Re-deriving that arithmetic here would be
a second implementation of the clock, free to drift from the first — and an
envelope that drifts is worse than no envelope, because it ducks the music
around speech that is no longer there.

THE ALGORITHM:
  1. One RMS energy reading per video frame, per narration WAV.
  2. Normalise against the loudest moment across ALL narrations, not per file,
     so a consistently quiet scene is not spuriously boosted into ducking.
  3. Map energy to gain: silence keeps `--base`, peak narration lands at
     `base × (1 − depth)`.
  4. Smooth asymmetrically — dip fast, recover slow — so the bed does not
     pump on every phoneme.

Defaults assume a commercially mastered bed (peaks near 0 dBFS) under TTS
narration (~-20 dBFS RMS): the bed sits at ~-16 dBFS and drops ~9 dB under
narration peaks, landing near -25 dBFS during speech. Voice leads by 5-8 dB
and the music still reads as music rather than as a rumour of music.

Prints JSON: {"props", "frames", "ducked", "floor", "base"}.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import wave
from pathlib import Path

from video_studio.paths import studio_root

#: Volume with no narration over it.
DEFAULT_BASE = 0.16
#: Fraction of the base to remove under the loudest narration.
DEFAULT_DEPTH = 0.65
#: Frames to dip / recover. Attack is deliberately ~3x faster than release.
DEFAULT_ATTACK = 6
DEFAULT_RELEASE = 18


def slugify(project: Path) -> str:
    """Match build_props' slug so we find the props file it wrote."""
    return project.resolve().name


def decode_pcm(raw: bytes, *, sampwidth: int, channels: int) -> list[float]:
    """16- or 8-bit PCM to mono floats in [-1, 1]. Stereo is averaged."""
    if sampwidth == 2:
        max_amp = 32768.0
        if channels == 1:
            return [s / max_amp for (s,) in struct.iter_unpack("<h", raw)]
        fmt = "<" + "h" * channels
        usable = len(raw) - (len(raw) % (2 * channels))
        return [sum(v) / (channels * max_amp)
                for v in struct.iter_unpack(fmt, raw[:usable])]
    if sampwidth == 1:
        # 8-bit PCM is unsigned, centred on 128.
        if channels == 1:
            return [(b - 128) / 128.0 for b in raw]
        out: list[float] = []
        for i in range(0, len(raw) - channels + 1, channels):
            out.append(sum(b - 128 for b in raw[i:i + channels]) / (channels * 128.0))
        return out
    # 24- and 32-bit are not decoded here. Returning empty makes the envelope
    # flat for this scene, which is audibly wrong but not silently wrong — the
    # summary reports how many narrations contributed.
    return []


def rms_per_frame(audio_path: Path, *, fps: int) -> list[float]:
    """One RMS reading per video frame, across the file's full duration.

    stdlib `wave` only: every TTS path in this repo emits WAV, and pulling in
    numpy for one array of means would put a compiled dependency behind a
    feature most users run once per render.
    """
    if not audio_path.exists():
        return []
    try:
        with wave.open(str(audio_path), "rb") as w:
            channels, sampwidth = w.getnchannels(), w.getsampwidth()
            framerate, nframes = w.getframerate(), w.getnframes()
            raw = w.readframes(nframes)
    except (wave.Error, OSError):
        return []

    samples = decode_pcm(raw, sampwidth=sampwidth, channels=channels)
    if not samples:
        return []
    per_frame = int(framerate / fps)
    if per_frame <= 0:
        return []

    out: list[float] = []
    for start in range(0, len(samples), per_frame):
        window = samples[start:start + per_frame]
        if not window:
            break
        out.append(math.sqrt(sum(s * s for s in window) / len(window)))
    return out


def asymmetric_smooth(values: list[float], base: float,
                      attack: int, release: int) -> list[float]:
    """One-pole filter with separate dip and recover time constants."""
    if attack <= 0 and release <= 0:
        return list(values)
    alpha_attack = 1.0 / max(attack, 1)
    alpha_release = 1.0 / max(release, 1)
    out = list(values)
    current = base
    for i, target in enumerate(out):
        alpha = alpha_attack if target < current else alpha_release
        current += (target - current) * alpha
        out[i] = current
    return out


def compute_envelope(narrations: list[tuple[int, list[float]]], *,
                     total_frames: int, base: float, depth: float,
                     attack: int, release: int) -> list[float]:
    """Per-frame music volume for the whole composition."""
    peak = max((max(rms) for _, rms in narrations if rms), default=0.0) or 1e-9
    raw = [base] * total_frames
    for start_frame, rms in narrations:
        for i, energy in enumerate(rms):
            f = start_frame + i
            if 0 <= f < total_frames:
                target = base * (1.0 - depth * min(energy / peak, 1.0))
                # MIN across overlapping narrations: the louder source wins.
                raw[f] = min(raw[f], target)
    return asymmetric_smooth(raw, base, attack, release)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True)
    ap.add_argument("--composer", default=str(studio_root() / "composer"))
    ap.add_argument("--base", type=float, default=DEFAULT_BASE)
    ap.add_argument("--depth", type=float, default=DEFAULT_DEPTH)
    ap.add_argument("--attack", type=int, default=DEFAULT_ATTACK)
    ap.add_argument("--release", type=int, default=DEFAULT_RELEASE)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not 0.0 < a.base <= 1.0:
        raise SystemExit("--base must be in (0, 1]")
    if not 0.0 <= a.depth <= 1.0:
        raise SystemExit("--depth must be in [0, 1]")

    composer = Path(a.composer).expanduser().resolve()
    project = Path(a.project).expanduser().resolve()
    slug = slugify(project)
    props_path = composer / "props" / f"{slug}.json"
    if not props_path.exists():
        raise SystemExit(
            f"no props at {props_path} — run build_props for this project first."
        )

    props = json.loads(props_path.read_text())
    if "music" not in props:
        raise SystemExit(
            "these props carry no music track, so there is nothing to duck. "
            "Add `music` to the storyboard and re-run build_props."
        )

    fps = int(props.get("fps", 30))
    public = composer / "public"

    narrations: list[tuple[int, list[float]]] = []
    frame = 0
    missing: list[str] = []
    for scene in props["scenes"]:
        if scene.get("audio"):
            wav = public / scene["audio"]
            rms = rms_per_frame(wav, fps=fps)
            if rms:
                narrations.append((frame, rms))
            else:
                missing.append(scene["id"])
        frame += int(scene["durationInFrames"])
    total_frames = frame

    if not narrations:
        raise SystemExit(
            "no readable narration audio in these props — every scene is silent, "
            "so ducking would be a no-op. Nothing written."
        )

    envelope = compute_envelope(narrations, total_frames=total_frames,
                                base=a.base, depth=a.depth,
                                attack=a.attack, release=a.release)
    floor = min(envelope) if envelope else a.base

    if missing:
        print(f"warning: unreadable or non-PCM narration in {len(missing)} scene(s): "
              f"{', '.join(missing)} — the bed stays at full volume under them.")

    if not a.dry_run:
        props["music"]["baseVolume"] = a.base
        props["music"]["envelope"] = [round(v, 4) for v in envelope]
        props_path.write_text(json.dumps(props, indent=2) + "\n")

    print(json.dumps({
        "props": str(props_path),
        "frames": total_frames,
        "seconds": round(total_frames / fps, 3),
        "ducked": len(narrations),
        "silent": len(missing),
        "base": a.base,
        "floor": round(floor, 4),
        "dryRun": a.dry_run,
    }, indent=2))


if __name__ == "__main__":
    main()
