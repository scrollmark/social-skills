# /// script
# requires-python = ">=3.11"
# ///
"""The tracks you are licensed to use, and a deterministic way to pick one.

Usage:
  video-studio music_catalog --where                  # where the catalog lives
  video-studio music_catalog --list                   # every track
  video-studio music_catalog --list --mood editorial  # filtered
  video-studio music_catalog --show warm-keys-01      # one track, resolved
  video-studio music_catalog --add path/to/track.mp3 --id warm-keys-01 \
      --moods editorial,warm --bpm 96 --license "Artlist, invoice 4471"
  video-studio music_catalog --remove warm-keys-01
  video-studio music_catalog --pick --moods editorial,warm --bpm 96 \
      --seed brand-origin-brick

Why this exists: `gen_music` makes a bed from nothing, which is the right answer
when no bed exists and the wrong answer when the user already owns music they
have cleared. Generated beds also drift — ask twice, get two different pieces —
so a series that wants one recognisable theme cannot be built out of them.

NOTHING IS SHIPPED HERE. The catalog is a pointer file: every entry names a
track the user provisioned under their own licence, and records that licence as
a string so there is a paper trail if provenance is ever questioned. Deleting a
catalog entry does not delete audio.

WHERE THE CATALOG LIVES, highest precedence first:

  $VIDEO_STUDIO_MUSIC_DIR/catalog.json     wherever the user points it
  ~/.config/video-studio/music/catalog.json the user's own, across every project

Same reasoning as styles.py: a catalog kept inside a checkout dies with the
checkout. Music is a thing a user has, not a thing a project has.

PICKING is deterministic. Same moods, same bpm, same seed — same track, every
re-render, so a video does not change its score because it was rebuilt. Scoring
is mood overlap (double weighted; it is the primary selector) plus bpm
closeness, then a seeded sample from the top quarter of the field. Sampling
rather than always taking the winner keeps one track from becoming the only
track a mood ever resolves to.

Prints JSON on every path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

CATALOG_VERSION = 1

ENV_VAR = "VIDEO_STUDIO_MUSIC_DIR"

#: A soft vocabulary, not a validator. Users invent their own moods and
#: reference them from a style preset's `music.moods`; these are here so that
#: independently-tagged catalogs have some chance of sharing a word.
SUGGESTED_MOODS = (
    "editorial", "lifestyle", "contemplative", "energetic", "cinematic",
    "corporate", "ambient", "playful", "tense", "warm", "dark",
    "uplifting", "mellow", "aggressive", "gentle",
)

#: Score every candidate, then sample from the top fraction. All-best is
#: boring (one track per mood forever); all-random is unpredictable.
SHORTLIST_FRACTION = 0.25
SHORTLIST_MIN = 3

#: bpm scoring reaches zero this far from the target.
BPM_TOLERANCE = 20.0


def catalog_dir() -> Path:
    override = os.environ.get(ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".config" / "video-studio" / "music"


def catalog_file() -> Path:
    return catalog_dir() / "catalog.json"


def load() -> dict:
    """The catalog, or an empty one. Never raises for a missing file."""
    path = catalog_file()
    if not path.exists():
        return {"version": CATALOG_VERSION, "tracks": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    version = int(data.get("version", CATALOG_VERSION))
    if version > CATALOG_VERSION:
        raise SystemExit(
            f"catalog at {path} is version {version}; this build reads up to "
            f"{CATALOG_VERSION}. Upgrade video-studio-engine."
        )
    data.setdefault("tracks", [])
    return data


def save(data: dict) -> Path:
    path = catalog_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def resolve_audio(track: dict) -> Path:
    """Absolute path to a track's audio.

    Relative paths resolve against the catalog directory, so moving the whole
    directory to another machine keeps every entry valid.
    """
    p = Path(track["path"]).expanduser()
    return p if p.is_absolute() else (catalog_dir() / p).resolve()


def measured_seconds(path: Path) -> float | None:
    """Duration via ffprobe, or None if ffprobe is absent or the file is not
    readable as media. Never fatal — duration is a convenience field."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return round(float(out), 2)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


# ── picking ──────────────────────────────────────────────────────────────

def _mood_overlap(track: dict, wanted: tuple[str, ...]) -> float:
    if not wanted:
        return 0.0
    return len(set(track.get("moods", [])) & set(wanted)) / len(wanted)


def _bpm_closeness(track_bpm: float | None, wanted: float | None) -> float:
    if track_bpm is None or wanted is None:
        return 0.0
    return max(0.0, 1.0 - abs(track_bpm - wanted) / BPM_TOLERANCE)


def _score(track: dict, moods: tuple[str, ...], bpm: float | None) -> float:
    return 2.0 * _mood_overlap(track, moods) + _bpm_closeness(track.get("bpm"), bpm)


def _rng(seed: str) -> random.Random:
    # Hashing only normalises an arbitrary string into an int; nothing here
    # depends on the hash being cryptographic.
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def pick(tracks: list[dict], moods: tuple[str, ...], bpm: float | None,
         seed: str) -> dict | None:
    """The chosen track, or None if the catalog is empty."""
    candidates = [t for t in tracks if set(t.get("moods", [])) & set(moods)] if moods else list(tracks)
    if not candidates:
        # A mood filter that matches nothing is too strict to be useful —
        # fall back to the whole catalog rather than returning silence.
        candidates = list(tracks)
    if not candidates:
        return None
    scored = sorted(candidates, key=lambda t: _score(t, moods, bpm), reverse=True)
    shortlist = scored[:max(SHORTLIST_MIN, int(len(scored) * SHORTLIST_FRACTION))]
    return _rng(seed).choice(shortlist)


def pick_for_preset(tracks: list[dict], preset: dict, seed: str) -> dict | None:
    """Derive moods and bpm from a style preset's `music.moods` / `rhythm.bpm`.

    This is the join between styles.py and this module: a preset carries the
    look AND the mood of the bed, so choosing a style chooses the music.
    """
    music_cfg = (preset or {}).get("music") or {}
    rhythm = (preset or {}).get("rhythm") or {}
    return pick(tracks, tuple(music_cfg.get("moods", [])), rhythm.get("bpm"), seed)


def load_preset(name: str) -> dict:
    """Read a styles.py preset by name — the same four tiers, same order.

    A preset carries `music.moods` and `rhythm.bpm` alongside the look, so
    choosing a style can choose the bed. Those keys are inert to styles.py
    itself, which reads only `captions` and `cards`.
    """
    import re
    roots: list[Path] = []
    env = os.environ.get("VIDEO_STUDIO_STYLES")
    if env:
        roots.append(Path(env).expanduser())
    roots += [
        Path.home() / ".config" / "video-studio" / "styles",
        Path(__file__).resolve().parent.parent / "styles",
    ]
    for root in roots:
        candidate = root / f"{name}.md"
        if candidate.exists():
            block = re.search(r"```json\s*(.*?)```", candidate.read_text(), re.S)
            if not block:
                raise SystemExit(f"preset {candidate} has no ```json block")
            return json.loads(block.group(1))
    raise SystemExit(
        f"no style preset named {name!r}. List them with: video-studio styles --list"
    )


# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--where", action="store_true", help="print the catalog path")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--show", metavar="ID")
    ap.add_argument("--add", metavar="AUDIO")
    ap.add_argument("--remove", metavar="ID")
    ap.add_argument("--pick", action="store_true")
    ap.add_argument("--id", help="track id for --add")
    ap.add_argument("--moods", default="", help="comma-separated")
    ap.add_argument("--mood", help="filter --list by one mood")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--key", help='musical key, e.g. "Am"')
    ap.add_argument("--license", dest="license_str",
                    help="the licence you hold — recorded verbatim")
    ap.add_argument("--source", help="where it came from")
    ap.add_argument("--notes")
    ap.add_argument("--seed", default="", help="stable input for --pick")
    ap.add_argument("--style", metavar="NAME",
                    help="take moods and bpm from a styles.py preset")
    ap.add_argument("--copy", action="store_true",
                    help="copy the audio into the catalog directory on --add")
    a = ap.parse_args()

    moods = tuple(m.strip() for m in a.moods.split(",") if m.strip())

    if a.where:
        print(json.dumps({"dir": str(catalog_dir()), "catalog": str(catalog_file()),
                          "exists": catalog_file().exists()}))
        return

    data = load()
    tracks: list[dict] = data["tracks"]

    if a.add:
        src = Path(a.add).expanduser().resolve()
        if not src.exists():
            raise SystemExit(f"no such audio file: {src}")
        track_id = a.id or src.stem
        if any(t["id"] == track_id for t in tracks):
            raise SystemExit(f"catalog already has a track with id '{track_id}' "
                             f"— pick another --id, or --remove it first")
        if a.copy:
            catalog_dir().mkdir(parents=True, exist_ok=True)
            dest = catalog_dir() / src.name
            shutil.copy2(src, dest)
            stored = src.name
        else:
            stored = str(src)
        entry = {"id": track_id, "path": stored}
        if moods:
            entry["moods"] = list(moods)
        for field, value in (("bpm", a.bpm), ("key", a.key),
                             ("license", a.license_str), ("source", a.source),
                             ("notes", a.notes)):
            if value is not None:
                entry[field] = value
        seconds = measured_seconds(src)
        if seconds is not None:
            entry["durationSeconds"] = seconds
        if not a.license_str:
            print("warning: no --license recorded. The catalog is the paper "
                  "trail; an entry without one cannot prove provenance.",
                  file=sys.stderr)
        tracks.append(entry)
        save(data)
        print(json.dumps({"added": entry, "catalog": str(catalog_file())}, indent=2))
        return

    if a.remove:
        before = len(tracks)
        data["tracks"] = [t for t in tracks if t["id"] != a.remove]
        if len(data["tracks"]) == before:
            raise SystemExit(f"no track with id '{a.remove}'")
        save(data)
        print(json.dumps({"removed": a.remove, "remaining": len(data["tracks"])}))
        return

    if a.show:
        track = next((t for t in tracks if t["id"] == a.show), None)
        if track is None:
            raise SystemExit(f"no track with id '{a.show}'")
        audio = resolve_audio(track)
        print(json.dumps({**track, "resolvedPath": str(audio),
                          "audioExists": audio.exists()}, indent=2))
        return

    if a.pick:
        if a.style:
            preset = load_preset(a.style)
            # Explicit flags still win: --style is a starting point, the same
            # way styles.py treats a preset when applying it to a storyboard.
            derived = (preset.get("music") or {}).get("moods", [])
            moods = moods or tuple(derived)
            if a.bpm is None:
                a.bpm = (preset.get("rhythm") or {}).get("bpm")
        chosen = pick(tracks, moods, a.bpm, a.seed)
        if chosen is None:
            raise SystemExit(
                "the catalog is empty — add a track you are licensed to use "
                "with --add, or generate a bed with gen_music instead."
            )
        audio = resolve_audio(chosen)
        if not audio.exists():
            print(f"warning: {chosen['id']} points at {audio}, which is missing",
                  file=sys.stderr)
        print(json.dumps({"id": chosen["id"], "path": str(audio),
                          "moods": chosen.get("moods", []), "bpm": chosen.get("bpm"),
                          "license": chosen.get("license"), "seed": a.seed}, indent=2))
        return

    # --list, and the bare no-flag case.
    shown = [t for t in tracks if a.mood in t.get("moods", [])] if a.mood else tracks
    print(json.dumps({
        "catalog": str(catalog_file()),
        "count": len(shown),
        "suggestedMoods": list(SUGGESTED_MOODS),
        "tracks": [{"id": t["id"], "moods": t.get("moods", []), "bpm": t.get("bpm"),
                    "license": t.get("license")} for t in shown],
    }, indent=2))


if __name__ == "__main__":
    main()
