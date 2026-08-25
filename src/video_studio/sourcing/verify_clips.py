# /// script
# requires-python = ">=3.11"
# ///
"""Check fetched clips against the storyboard BEFORE anything is rendered.

Usage:
  video-studio verify_clips --project <dir>
  video-studio verify_clips --project <dir> --json

Every check here exists because it went wrong in a real video, and every one of
them was caught by hand — which means it was caught only because somebody
happened to look. Search results are not trustworthy in the specific ways below,
and none of them announce themselves:

  DUPLICATES     Two different queries returning the same clip. Seen four times
                 in one sitting; invisible on a contact sheet because you are
                 looking at two thumbnails of the same thing in different rows
                 and reading them as similar rather than identical.

  GREYSCALE      A stock search for white cliffs returned a monochrome series.
                 Measured saturation of zero, dropped into a colour piece. On a
                 small thumbnail it reads as "moody", not as "broken".

  TOO SHORT      A clip shorter than the scene it fills loops, and the jump
                 lands mid-shot. The clip and the scene are in different files,
                 so nothing compares them unless asked.

  SILENT         An audio-bearing project whose track is digital silence. The
                 render succeeds, every log line says success, and the video
                 ships mute.

  ORIENTATION    A landscape clip in a vertical video. `fit: cover` crops to
                 fill, so it does not error — it just quietly throws away most
                 of the frame.

Exit code is 1 if anything is a FAIL, so this can gate a pipeline. Warnings do
not fail: a 4:3 archival clip in a vertical piece is often a deliberate choice.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

CLIP_EXTS = (".mp4", ".webm", ".mov", ".png", ".jpg", ".jpeg")
#: Below this mean saturation a clip is greyscale in everything but name.
#: Real footage that is merely desaturated measures ~5-10; a true monochrome
#: series measures 0.
GREY_SATURATION = 1.5


def ffprobe(path: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=width,height,codec_type", "-of", "json", str(path)],
        capture_output=True, text=True)
    if r.returncode != 0:
        return {}
    d = json.loads(r.stdout or "{}")
    out = {"seconds": float(d.get("format", {}).get("duration", 0) or 0),
           "width": None, "height": None, "hasAudio": False}
    for s in d.get("streams", []):
        if s.get("codec_type") == "video":
            out["width"], out["height"] = s.get("width"), s.get("height")
        if s.get("codec_type") == "audio":
            out["hasAudio"] = True
    return out


def saturation(path: Path) -> float | None:
    """Mean chroma over a one-second sample. None when it cannot be measured."""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", "1", "-t", "1", "-i", str(path),
         "-vf", "format=yuv420p,signalstats,metadata=mode=print:"
                "key=lavfi.signalstats.SATAVG:file=-", "-f", "null", "-"],
        capture_output=True, text=True)
    vals = [float(m) for m in re.findall(r"SATAVG=([\d.]+)", r.stdout + r.stderr)]
    return sum(vals) / len(vals) if vals else None


def mean_volume(path: Path) -> float | None:
    """Mean level in dB, or None if it genuinely could not be measured.

    NOTE the log level. volumedetect prints its summary at `info`, so running
    this with `-v error` — the obvious choice for a quiet helper — swallows the
    only line worth reading and returns None. The silence check then never
    fires and reports nothing, which is exactly the kind of quiet no-op this
    script exists to catch. It did precisely that on first write.
    """
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect",
         "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", r.stdout + r.stderr)
    return float(m.group(1)) if m else None


def read_provenance(project: Path) -> dict[str, str]:
    """shot id -> source slug, from sources.tsv if the fetcher wrote one.

    The slug is the only machine-readable evidence of what a clip actually is.
    Stock search does not respect geography — Japanese queries have returned a
    Hawaii temple, English ones Turkey and Morocco, Mexican ones San Francisco
    and Colorado — and the slug is where that shows up first.
    """
    out: dict[str, str] = {}
    path = project / "sources.tsv"
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 4 and parts[2] == "ok":
            out[parts[0]] = parts[3]
    return out


def check_place_labels(sb: dict, provenance: dict[str, str]) -> list[dict]:
    """Flag a card naming a place when the clip's source does not corroborate it.

    Deliberately a WARNING, not a failure. A slug is a contributor's filename,
    not a geotag: `charming-empty-street-in-european-city-at-dawn` really is
    Europe but names no country, and plenty of correct footage has an unhelpful
    slug. What this catches is the case that actually shipped — a card reading
    a city name over a clip whose only evidence points somewhere else.

    No stock API publishes shoot coordinates, so this cannot be made exact. It
    exists to force the question, not to answer it.
    """
    findings = []
    for scene in sb.get("scenes", []):
        sid = scene["id"]
        has_media = any(l.get("source") for l in scene.get("layers", []))
        if not has_media:
            continue
        for layer in scene.get("layers", []):
            card = layer.get("card")
            if not isinstance(card, dict):
                continue
            heading = str(card.get("heading") or "").strip()
            # A card with a subtext is a stat or a sign-off ("MT. FUJI / 3,776 m",
            # "PLAN YOUR JOURNEY / ..."), not a bare place label. Those were the
            # loudest false positives on the first run.
            if card.get("subtext"):
                continue
            # One to three words, letters only: the shape of a place label.
            # A sentence is a statement; a place name is a noun.
            if (not heading or len(heading.split()) > 3
                    or not heading.replace(" ", "").isalpha()):
                continue
            slug = provenance.get(sid, "")
            if not slug:
                findings.append({
                    "level": "WARN", "where": f"{sid}/{layer.get('id')}",
                    "check": "unverified-place-label",
                    "detail": f"card reads {heading!r} but no provenance was recorded "
                              f"for this shot — confirm it, or say which tier it is in",
                })
                continue
            # Match WORD by word, not as one hyphenated token. "JOREN FALLS"
            # against `joren-waterfalls` is the same place described differently,
            # and whole-token matching flagged it — which is how a check earns a
            # reputation for crying wolf and stops being read.
            words = [w for w in heading.lower().split() if len(w) > 2]
            if not any(w in slug.lower() for w in words):
                findings.append({
                    "level": "WARN", "where": f"{sid}/{layer.get('id')}",
                    "check": "place-label-unsupported",
                    "detail": f"card reads {heading!r}; the source slug is {slug!r}, "
                              f"which shares no word with it. Confirm before shipping",
                })
    return findings


def verify(project: Path) -> dict:
    sb_path = project / "storyboard.json"
    if not sb_path.exists():
        raise SystemExit(f"no storyboard.json in {project}")
    sb = json.loads(sb_path.read_text())
    clips_dir = project / "clips"
    provenance = read_provenance(project)

    findings: list[dict] = []
    seen: dict[str, list[str]] = {}
    checked = 0

    for scene in sb.get("scenes", []):
        sid = scene["id"]
        planned = float(scene.get("plannedSeconds") or 0)
        for layer in scene.get("layers", []):
            if "card" in layer or not layer.get("source"):
                continue
            lid = layer["id"]
            found = [clips_dir / f"{sid}-{lid}{e}" for e in CLIP_EXTS]
            path = next((p for p in found if p.exists()), None)
            if path is None:
                continue
            checked += 1
            info = ffprobe(path)
            where = f"{sid}/{lid}"

            digest = hashlib.md5(path.read_bytes()).hexdigest()
            seen.setdefault(digest, []).append(where)

            if info.get("seconds") and planned and info["seconds"] + 0.05 < planned:
                findings.append({
                    "level": "FAIL", "where": where, "check": "too-short",
                    "detail": f"clip is {info['seconds']:.2f}s but the scene is "
                              f"{planned}s — it will loop mid-shot",
                })

            if path.suffix.lower() in (".mp4", ".webm", ".mov"):
                sat = saturation(path)
                if sat is not None and sat < GREY_SATURATION:
                    findings.append({
                        "level": "FAIL", "where": where, "check": "greyscale",
                        "detail": f"mean saturation {sat:.2f} — this clip is "
                                  f"monochrome, which is rarely what a colour piece wants",
                    })

            w, h = info.get("width"), info.get("height")
            vw, vh = sb.get("width", 1080), sb.get("height", 1920)
            if w and h and (w > h) != (vw > vh):
                findings.append({
                    "level": "WARN", "where": where, "check": "orientation",
                    "detail": f"clip is {w}x{h} in a {vw}x{vh} video — `cover` will "
                              f"crop away most of the frame",
                })

    for digest, wheres in seen.items():
        if len(wheres) > 1:
            findings.append({
                "level": "FAIL", "where": ", ".join(wheres), "check": "duplicate",
                "detail": f"{len(wheres)} scenes are using the byte-identical clip — "
                          f"different queries returned the same result",
            })

    # Audio: only meaningful when the storyboard asked for some.
    music = sb.get("music")
    if music:
        mpath = Path(music)
        if not mpath.is_absolute():
            mpath = project / music
        if not mpath.exists():
            findings.append({"level": "FAIL", "where": "music", "check": "missing",
                             "detail": f"storyboard names {music} and it is not there"})
        else:
            vol = mean_volume(mpath)
            if vol is not None and vol < -60:
                findings.append({
                    "level": "FAIL", "where": "music", "check": "silent",
                    "detail": f"score measures {vol:.1f} dB — digital silence. The "
                              f"render will succeed and ship mute",
                })

    narrated = [s["id"] for s in sb.get("scenes", []) if (s.get("narration") or "").strip()]
    for sid in narrated:
        wav = project / "audio" / f"{sid}.wav"
        if not wav.exists():
            findings.append({"level": "FAIL", "where": sid, "check": "missing-narration",
                             "detail": "scene has narration text but no recorded audio"})
            continue
        vol = mean_volume(wav)
        if vol is not None and vol < -60:
            findings.append({
                "level": "FAIL", "where": sid, "check": "silent-narration",
                "detail": f"narration measures {vol:.1f} dB — silence became the scene "
                          f"clock and the render will have no voice and no captions",
            })

    findings += check_place_labels(sb, provenance)

    fails = [f for f in findings if f["level"] == "FAIL"]
    return {"project": str(project), "clipsChecked": checked,
            "fail": len(fails), "warn": len(findings) - len(fails),
            "findings": findings}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = verify(args.project)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['level']}: {f['where']} [{f['check']}] {f['detail']}")
        if not result["findings"]:
            print(f"{result['clipsChecked']} clip(s) checked — nothing to report")
        else:
            print(f"\n{result['clipsChecked']} checked · {result['fail']} fail · "
                  f"{result['warn']} warn")
    sys.exit(1 if result["fail"] else 0)


if __name__ == "__main__":
    main()
