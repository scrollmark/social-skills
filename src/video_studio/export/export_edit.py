# /// script
# requires-python = ">=3.11"
# dependencies = ["opentimelineio>=0.17", "otio-fcpx-xml-adapter"]
# ///
"""Export a finished project as an editable timeline (Premiere, Resolve, FCP).

Usage:
  video-studio export_edit --project projects/brand-origin-brick   # do this one
  ... --bundle          # also write a .otiod folder with the media copied in
  ... --fcpxml          # also write FCP X XML (needs otio-fcpx-xml-adapter)

Prefer --project. It rebuilds that project's timeline document first, so the
export is guaranteed to be current. Each project owns `composer/props/<name>.json`
and `composer/public/<name>/`, so exports cannot pick up another project's
content — an earlier single global props.json made exactly that failure silent.

Writes an `.otio` timeline plus an `.srt` of the captions. **Premiere Pro and
DaVinci Resolve import .otio natively** — no adapter, no plugin, File > Import.
`--fcpxml` adds a Final Cut Pro XML (v1.8), which FCP opens as a real project.

On native project files, since it is always asked: there is no `.prproj` writer
here and there should not be. Premiere's project format is gzipped proprietary
XML with no published spec, versioned to the application — a writer for it is
reverse engineering that breaks on the next update, silently, in someone else's
edit. Adobe's SUPPORTED inbound paths are OTIO, FCP7 XML, AAF and EDL, and the
first of those is what this already emits. Final Cut is the opposite case:
FCPXML is a documented format Apple publishes, which is why it is offered.

What survives the trip, and what does not, because being wrong about this
wastes an editor's afternoon:

  survives   every cut at its true frame, each clip pointing at its real source
             file, narration per scene, music, and the captions (as SRT, which
             Premiere imports as a caption track)
  does NOT   Ken Burns moves, fades, and the on-screen cards

That second list is not a shortcoming of this script. The interchange formats
themselves carry no effects — OTIO's own feature matrix marks Audio/Video
Effects unsupported across EDL, FCP7 XML, FCP X and AAF alike. Anything with a
look has to be rebuilt in the host application.

So the cards are exported as **timeline markers carrying their text**, at the
frame where each appears. The editor does not get the title; they get a labelled
spot saying what belonged there, which is the useful half. Ken Burns moves are
marked the same way.

Why this is still worth doing: the tedious, error-prone part of an edit is
getting forty cuts onto the right frames with the right media and the audio in
sync. That is exactly what transfers. Typography is the part an editor wants to
redo in their own house style anyway.

Prints JSON: {"otio", "srt", "clips", "markers", "seconds", ...}.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from video_studio.paths import studio_root

SKILL_ROOT = studio_root()

#: Words per caption cue. Word-level timing is right for the composer's
#: karaoke-style captions and unreadable as subtitles — an SRT that flashes one
#: word at a time is worse than none.
CUE_WORDS = 7

#: A gap this long between words is a sentence boundary worth breaking on, even
#: mid-cue.
CUE_GAP_MS = 700


def srt_time(ms: int) -> str:
    ms = max(0, int(ms))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def group_captions(words: list[dict], offset_ms: int) -> list[dict]:
    """Word timings -> readable cues, offset onto the global timeline."""
    cues: list[dict] = []
    cur: list[dict] = []
    for w in words:
        if cur:
            gap = w["startMs"] - cur[-1]["endMs"]
            if len(cur) >= CUE_WORDS or gap >= CUE_GAP_MS:
                cues.append(cur)
                cur = []
        cur.append(w)
    if cur:
        cues.append(cur)
    return [
        {
            "start": c[0]["startMs"] + offset_ms,
            "end": c[-1]["endMs"] + offset_ms,
            "text": " ".join(w["text"] for w in c).strip(),
        }
        for c in cues if c
    ]


def write_srt(cues: list[dict], out: Path) -> None:
    blocks = []
    for i, c in enumerate(cues, 1):
        # A zero-length cue is legal in our timings and invisible in a player.
        end = max(c["end"], c["start"] + 200)
        blocks.append(f"{i}\n{srt_time(c['start'])} --> {srt_time(end)}\n{c['text']}\n")
    out.write_text("\n".join(blocks), encoding="utf-8")


def card_label(layer: dict) -> str:
    for key in ("heading", "title", "text", "label", "footnote"):
        val = layer.get(key)
        if isinstance(val, str) and val.strip():
            return " ".join(val.split())[:80]
    return layer.get("id", "card")


def build(props: dict, media_root: Path, name: str):
    import opentimelineio as otio

    fps = float(props.get("fps", 30))
    rt = lambda frames: otio.opentime.RationalTime(float(frames), fps)

    timeline = otio.schema.Timeline(name=name)
    timeline.global_start_time = rt(0)

    video = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
    narration = otio.schema.Track(name="A1 narration", kind=otio.schema.TrackKind.Audio)
    timeline.tracks.append(video)
    timeline.tracks.append(narration)

    cues: list[dict] = []
    markers = 0
    clips = 0
    cursor_frames = 0

    for scene in props["scenes"]:
        frames = int(scene["durationInFrames"])
        scene_range = otio.opentime.TimeRange(rt(0), rt(frames))

        # --- picture -------------------------------------------------------
        media_layers = [l for l in scene["layers"] if l.get("src")]
        if media_layers:
            layer = media_layers[0]
            src = (media_root / layer["src"]).resolve()
            ref = otio.schema.ExternalReference(target_url=src.as_uri())
            # available_range lets the host relink and trim sensibly; without it
            # Premiere treats the clip as unbounded and the media offline.
            ref.available_range = otio.opentime.TimeRange(rt(0), rt(frames))
            clip = otio.schema.Clip(name=f"{scene['id']}-{layer['id']}",
                                    media_reference=ref, source_range=scene_range)
            if layer.get("ken"):
                ken = layer["ken"]
                move = f"ken burns: zoom {ken.get('zoom', '-')}, pan {ken.get('pan', '-')}"
                clip.markers.append(otio.schema.Marker(
                    name=move, marked_range=otio.opentime.TimeRange(rt(0), rt(0)),
                    color=otio.schema.MarkerColor.ORANGE))
                markers += 1
            video.append(clip)
            clips += 1
        else:
            # A card-only scene is still time on the timeline; a Gap keeps every
            # later cut on its true frame instead of sliding earlier.
            video.append(otio.schema.Gap(source_range=scene_range))

        # --- cards, as markers on the timeline -----------------------------
        for layer in scene["layers"]:
            if layer.get("type") != "card":
                continue
            at = int(round(layer.get("atMs", 0) / 1000.0 * fps))
            timeline.tracks.markers.append(otio.schema.Marker(
                name=f"TITLE: {card_label(layer)}",
                marked_range=otio.opentime.TimeRange(rt(cursor_frames + at), rt(0)),
                color=otio.schema.MarkerColor.CYAN))
            markers += 1

        # --- narration -----------------------------------------------------
        if scene.get("audio"):
            asrc = (media_root / scene["audio"]).resolve()
            aref = otio.schema.ExternalReference(target_url=asrc.as_uri())
            aref.available_range = otio.opentime.TimeRange(rt(0), rt(frames))
            narration.append(otio.schema.Clip(
                name=f"{scene['id']}-vo", media_reference=aref, source_range=scene_range))
        else:
            narration.append(otio.schema.Gap(source_range=scene_range))

        if scene.get("captions"):
            cues.extend(group_captions(scene["captions"],
                                       int(round(cursor_frames / fps * 1000))))
        cursor_frames += frames

    # --- music ------------------------------------------------------------
    music = props.get("music")
    if music and music.get("src"):
        msrc = (media_root / music["src"]).resolve()
        if msrc.exists():
            mtrack = otio.schema.Track(name="A2 music", kind=otio.schema.TrackKind.Audio)
            mref = otio.schema.ExternalReference(target_url=msrc.as_uri())
            mref.available_range = otio.opentime.TimeRange(rt(0), rt(cursor_frames))
            mtrack.append(otio.schema.Clip(
                name="music", media_reference=mref,
                source_range=otio.opentime.TimeRange(rt(0), rt(cursor_frames))))
            timeline.tracks.append(mtrack)

    return timeline, cues, {"clips": clips, "markers": markers, "frames": cursor_frames}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", help="project dir — rebuilds its props first, then exports (preferred)")
    ap.add_argument("--props", help="an already-built props.json (advanced; see the note above)")
    ap.add_argument("--media-root", help="where props' relative srcs resolve (default: composer/public)")
    ap.add_argument("--out", help="output path without extension (default: <project>/edit/<name>)")
    ap.add_argument("--bundle", action="store_true",
                    help="also write a .otiod folder with the media copied in")
    ap.add_argument("--fcpxml", action="store_true",
                    help="also write Final Cut Pro XML (.fcpxml), a real FCP project")
    args = ap.parse_args()

    import opentimelineio as otio

    if not args.project and not args.props:
        raise SystemExit("pass --project (preferred) or --props")

    if args.project:
        project = Path(args.project)
        storyboard = project / "storyboard.json"
        if not storyboard.exists():
            raise SystemExit(f"no storyboard.json in {project}")
        # Rebuild before reading. props.json is global, so trusting whatever is
        # there exports the last project built, not this one.
        import subprocess
        r = subprocess.run(
            ["uv", "run", str(SKILL_ROOT / "scripts" / "build_props.py"),
             "--storyboard", str(storyboard), "--project", str(project)],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            # Trim on line boundaries. A raw character slice lands mid-word and
            # the reader's first thought is "the tool is broken", not "my
            # footage is missing".
            lines = [l for l in r.stderr.strip().splitlines() if l.strip()]
            head = lines[0] if lines else "build failed"
            rest = lines[1:9]
            more = f"\n  ... and {len(lines) - 9} more" if len(lines) > 9 else ""
            raise SystemExit(
                f"Cannot export {project.name} — its timeline will not build.\n"
                f"{head}\n" + "\n".join(rest) + more
            )
        summary = json.loads(r.stdout.strip().splitlines()[-1])
        if summary.get("placeholdered"):
            raise SystemExit(
                f"{summary['placeholdered']} layer(s) are placeholders, not footage — "
                "exporting this would hand someone an edit full of coloured boxes. "
                "Resolve the sources first."
            )
        args.props = args.props or str(SKILL_ROOT / "composer" / "props" / f"{project.resolve().name}.json")
        if not args.out:
            args.out = str(project / "edit" / project.name)

    if not args.out:
        raise SystemExit("--out is required when using --props")

    props_path = Path(args.props)
    if not props_path.exists():
        raise SystemExit(f"{props_path} not found — run build_props.py first")
    props = json.loads(props_path.read_text())
    # Sources are stored "<project>/clips/x.mp4", so the root is public/ itself.
    media_root = Path(args.media_root) if args.media_root else SKILL_ROOT / "composer" / "public"
    if not media_root.exists():
        raise SystemExit(f"media root {media_root} not found — pass --media-root")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    timeline, cues, stats = build(props, media_root, out.name)

    otio_path = out.with_suffix(".otio")
    otio.adapters.write_to_file(timeline, str(otio_path))

    srt_path = out.with_suffix(".srt")
    if cues:
        write_srt(cues, srt_path)

    result = {
        "otio": str(otio_path),
        "srt": str(srt_path) if cues else None,
        "clips": stats["clips"],
        "markers": stats["markers"],
        "captionCues": len(cues),
        "seconds": round(stats["frames"] / float(props.get("fps", 30)), 2),
        "fps": props.get("fps", 30),
        "notCarried": ["ken burns moves", "fades", "on-screen cards (exported as markers)"],
    }

    if args.bundle:
        bundle = out.with_suffix(".otiod")
        if bundle.exists():
            shutil.rmtree(bundle)
        # otiod copies every referenced file next to the timeline, which is what
        # makes this handable to someone on another machine.
        otio.adapters.write_to_file(timeline, str(bundle), adapter_name="otiod")
        result["bundle"] = str(bundle)

    if args.fcpxml:
        names = {a.name for a in otio.plugins.ActiveManifest().adapters}
        if "fcpx_xml" not in names:
            # This used to be the ONLY outcome: the adapter was named in the
            # help text but never in the dependency header, so the flag reported
            # "skipped" on every machine and no one noticed it could not work.
            result["fcpxml"] = "unavailable — otio-fcpx-xml-adapter did not load"
        else:
            x = out.with_suffix(".fcpxml")
            otio.adapters.write_to_file(timeline, str(x), adapter_name="fcpx_xml")
            result["fcpxml"] = str(x)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
