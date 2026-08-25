# /// script
# requires-python = ">=3.11"
# ///
"""Write a Final Cut Pro project (.fcpxml) with real titles and real motion.

Usage:
  video-studio export_fcpxml --project projects/brand-origin-brick
  ... --out somewhere/name.fcpxml

Why this exists alongside the OTIO export: the generic interchange path drops
everything with a look. Measured on a real project, the OTIO->fcpx adapter
emitted 0 <title> and 0 <adjust-transform> elements — the on-screen cards
arrived as markers and the camera moves not at all.

FCPXML can carry both, so this writes it directly:

  cards      -> <title> using Final Cut's Basic Title generator, with the text
                and font size, editable in the inspector like any other title
  ken burns  -> <adjust-transform> with keyframed scale, so the move is a real
                animation the editor can retime, not a note saying one existed
  narration  -> its own lane under the picture
  captions   -> NOT here. FCP wants captions as a sidecar; the .srt from
                export_edit.py imports cleanly and stays editable as text.

Timing rules that are easy to get wrong and fail silently in FCP:
- Every time is a rational with the frame duration as denominator ("300/30s"),
  never a decimal. FCP rounds decimals unpredictably and cuts drift.
- Durations must be whole multiples of frameDuration, so everything is computed
  in FRAMES and only formatted at the end.
- offset= is the position on the timeline; start= is the in-point WITHIN the
  source. Confusing them yields clips that play the wrong part of the file.

Validated here by parsing the output and checking element counts and asset
paths. It has NOT been opened in Final Cut on this machine — say so rather than
implying it is app-tested.

Prints JSON: {"out", "clips", "titles", "transforms", "music", "seconds"}.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from video_studio.paths import studio_root

SKILL_ROOT = studio_root()

FCPXML_VERSION = "1.9"

#: Final Cut's stock title generator. The uid is a fixed, documented path into
#: the bundled Motion templates — FCP resolves it by identity, not by disk path,
#: so this works on any install with the standard content.
BASIC_TITLE_UID = (
    ".../Titles.localized/Basic Text.localized/Basic Title.localized/Basic Title.moti"
)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def t(frames: int, fps: int) -> str:
    """Frames -> an FCPXML rational time. Never emit decimals."""
    return f"{int(frames)}/{fps}s" if frames else "0s"


def probe_seconds(path: Path) -> float | None:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def card_text(layer: dict) -> str:
    for key in ("heading", "title", "text", "label"):
        v = layer.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def ken_scale(ken: dict) -> tuple[float, float]:
    """(start, end) scale for a Ken Burns move.

    'in' pushes toward the subject, so it ENDS larger; 'out' starts larger and
    settles. Getting this backwards is invisible in a still and obvious in
    motion, which is the worst way to find out.
    """
    amount = float(ken.get("amount", 0.12))
    if ken.get("zoom") == "out":
        return 1.0 + amount, 1.0
    return 1.0, 1.0 + amount


def build(props: dict, media_root: Path, name: str) -> tuple[ET.Element, dict]:
    fps = int(props.get("fps", 30))
    width = int(props.get("width", 1080))
    height = int(props.get("height", 1920))

    root = ET.Element("fcpxml", {"version": FCPXML_VERSION})
    resources = ET.SubElement(root, "resources")
    ET.SubElement(resources, "format", {
        "id": "r0", "name": f"FFVideoFormat{height}p{fps}",
        "frameDuration": f"1/{fps}s",
        "width": str(width), "height": str(height),
        "colorSpace": "1-1-1 (Rec. 709)",
    })

    stats = {"clips": 0, "titles": 0, "transforms": 0, "music": 0}
    rid = 1
    title_effect_id = None

    # Pass 1: every asset becomes a <resources> entry. FCP resolves clips by
    # ref, so an asset referenced before it is declared simply goes offline.
    assets: dict[str, str] = {}
    for scene in props["scenes"]:
        for rel in [l["src"] for l in scene["layers"] if l.get("src")] + \
                   ([scene["audio"]] if scene.get("audio") else []) + \
                   ([(props.get("music") or {}).get("src")]
                    if (props.get("music") or {}).get("src") else []):
            if rel in assets:
                continue
            path = (media_root / rel).resolve()
            seconds = probe_seconds(path) or 0.0
            frames = max(1, round(seconds * fps))
            is_img = path.suffix.lower() in IMAGE_EXTS
            is_audio = path.suffix.lower() in {".wav", ".mp3", ".m4a", ".aac"}
            rid += 1
            aid = f"r{rid}"
            attrs = {
                "id": aid, "name": path.stem, "start": "0s",
                "duration": t(frames, fps),
                "hasVideo": "0" if is_audio else "1",
                "hasAudio": "1" if is_audio else "0",
            }
            if not is_audio:
                attrs["format"] = "r0"
            if is_img:
                # A still has no intrinsic duration; FCP treats duration=0s as
                # "as long as you like" and a nonzero value as a hard limit.
                attrs["duration"] = "0s"
            asset = ET.SubElement(resources, "asset", attrs)
            ET.SubElement(asset, "media-rep", {
                "kind": "original-media", "src": path.as_uri(),
            })
            assets[rel] = aid

    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", {"name": "video-studio"})
    project = ET.SubElement(event, "project", {"name": name})
    total = sum(int(s["durationInFrames"]) for s in props["scenes"])
    sequence = ET.SubElement(project, "sequence", {
        "format": "r0", "duration": t(total, fps),
        "tcStart": "0s", "tcFormat": "NDF",
        "audioLayout": "stereo", "audioRate": "48k",
    })
    spine = ET.SubElement(sequence, "spine")

    # Music spans the whole timeline on its own lane, beneath the narration.
    # Previously dropped entirely, so an export played dry under the voice.
    music = (props.get("music") or {}).get("src")
    if music and music in assets:
        ET.SubElement(spine, "asset-clip", {
            "ref": assets[music], "lane": "-2", "name": "music",
            "offset": "0s", "duration": t(total, fps), "start": "0s",
            "audioRole": "music",
        })
        stats["music"] = 1

    cursor = 0
    for scene in props["scenes"]:
        frames = int(scene["durationInFrames"])
        media = [l for l in scene["layers"] if l.get("src")]

        if media:
            layer = media[0]
            clip = ET.SubElement(spine, "asset-clip", {
                "ref": assets[layer["src"]], "name": f"{scene['id']}-{layer['id']}",
                "offset": t(cursor, fps), "duration": t(frames, fps),
                "start": "0s", "format": "r0",
            })
            stats["clips"] += 1
            if layer.get("ken"):
                a, b = ken_scale(layer["ken"])
                adj = ET.SubElement(clip, "adjust-transform")
                kf = ET.SubElement(adj, "param", {"name": "scale"})
                kfs = ET.SubElement(kf, "keyframeAnimation")
                # Keyframe times are relative to the clip's own start.
                ET.SubElement(kfs, "keyframe", {"time": "0s", "value": f"{a:.4f} {a:.4f}"})
                ET.SubElement(kfs, "keyframe",
                              {"time": t(frames, fps), "value": f"{b:.4f} {b:.4f}"})
                stats["transforms"] += 1
            parent_for_lanes = clip
        else:
            parent_for_lanes = ET.SubElement(spine, "gap", {
                "name": "gap", "offset": t(cursor, fps),
                "duration": t(frames, fps), "start": "0s",
            })

        # Narration on lane -1, beneath the picture.
        if scene.get("audio"):
            ET.SubElement(parent_for_lanes, "asset-clip", {
                "ref": assets[scene["audio"]], "lane": "-1",
                "name": f"{scene['id']}-vo", "offset": "0s",
                "duration": t(frames, fps), "start": "0s",
            })

        def emit_title(text, at, dur, lane, size, colour="1 1 1 1"):
            """One <title> on `lane`. Shared by card layers and overlays so the
            two cannot drift apart — overlays were previously not emitted at all,
            silently dropping every stat/label/cta card from the export."""
            nonlocal title_effect_id, rid
            if title_effect_id is None:
                rid += 1
                tid = f"r{rid}"
                ET.SubElement(resources, "effect", {
                    "id": tid, "name": "Basic Title", "uid": BASIC_TITLE_UID,
                })
                title_effect_id = tid
            el = ET.SubElement(parent_for_lanes, "title", {
                "ref": title_effect_id, "lane": str(lane), "name": text[:40],
                "offset": t(at, fps), "duration": t(max(1, dur), fps), "start": "0s",
            })
            sid_ = f"ts{stats['titles']}"
            te = ET.SubElement(el, "text")
            ts_ = ET.SubElement(te, "text-style", {"ref": sid_})
            ts_.text = text
            sd = ET.SubElement(el, "text-style-def", {"id": sid_})
            ET.SubElement(sd, "text-style", {
                "font": "Helvetica Neue", "fontSize": str(size),
                "fontColor": colour, "bold": "1", "alignment": "center",
            })
            stats["titles"] += 1

        # Cards become real titles on lane 1, above the picture.
        for layer in scene["layers"]:
            if layer.get("type") != "card":
                continue
            text = card_text(layer)
            if not text:
                continue
            if False:
                pass
            at = int(round(layer.get("atMs", 0) / 1000.0 * fps))
            until = layer.get("untilMs")
            dur = (int(round(until / 1000.0 * fps)) - at) if until else (frames - at)
            dur = max(1, min(dur, frames - at))
            emit_title(text, at, dur, 1, layer.get("fontSize", 96))

        # Overlays (stat/label/cta/title) run the whole scene, above the cards.
        for ov in scene.get("overlays", []) or []:
            txt = (ov.get("text") or "").strip()
            if not txt:
                continue
            base = 88 if ov.get("type") == "title" else 76 if ov.get("type") == "stat" else 52
            emit_title(txt, 0, frames, 2, int(base * float(ov.get("scale", 1))),
                       colour="0.98 0.83 0.08 1" if ov.get("type") == "stat" else "1 1 1 1")

        cursor += frames

    stats["frames"] = cursor
    return root, stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()

    project = Path(args.project)
    slug = project.resolve().name
    props_path = SKILL_ROOT / "composer" / "props" / f"{slug}.json"
    if not props_path.exists():
        raise SystemExit(f"{props_path} not found — run build_props.py for this project first")
    props = json.loads(props_path.read_text())
    media_root = SKILL_ROOT / "composer" / "public"

    out = Path(args.out) if args.out else project / "edit" / f"{slug}.fcpxml"
    out.parent.mkdir(parents=True, exist_ok=True)

    root, stats = build(props, media_root, slug)
    xml = minidom.parseString(ET.tostring(root, encoding="unicode")).toprettyxml(indent="  ")
    # minidom writes its own declaration; replace it and add the DOCTYPE FCP wants.
    body = "\n".join(xml.splitlines()[1:])
    out.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n' + body,
        encoding="utf-8",
    )

    print(json.dumps({
        "out": str(out),
        "clips": stats["clips"], "titles": stats["titles"],
        "transforms": stats["transforms"],
        # Surfaced because a silent export looks identical to a scored one in
        # every other field — the count is the only way to notice it was dropped.
        "music": stats["music"],
        "seconds": round(stats["frames"] / int(props.get("fps", 30)), 2),
        "note": "structurally validated here; not opened in Final Cut on this machine",
    }, indent=2))


if __name__ == "__main__":
    main()
