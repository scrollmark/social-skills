# /// script
# requires-python = ">=3.11"
# ///
"""Captions for the ffmpeg path: word timings → ASS, optionally burnt in.

Usage:
  # one scene, subtitle file only
  uv run scripts/burn_captions.py --timings projects/x/audio/hook.timings.json \
      --out projects/x/subs/hook.ass

  # burn onto a clip
  uv run scripts/burn_captions.py --timings projects/x/audio/hook.timings.json \
      --video projects/x/clips/hook.mp4 --out projects/x/clips/hook-capped.mp4

  # a whole project, one .ass per scene, offset onto the project timeline
  uv run scripts/burn_captions.py --project projects/x --out projects/x/subs/

  # take the look from a style preset
  uv run scripts/burn_captions.py --timings ... --out ... --style tourism

Why this exists: captions currently reach the screen ONE way — build_props
folds `<scene>.timings.json` into composer props and Remotion draws them. Every
route that does not end in Remotion therefore ends with no captions: a clip cut
straight in ffmpeg, a stock-footage supercut, anything handed to an editor as
finished video. This gives that route the same word-level highlight.

STYLING speaks the same vocabulary as styles.py, so a preset drives both
renderers. Keys honoured here: color, highlight, fontFamily, fontSize, stroke,
strokeWidth, bottom, wordsPerPage, uppercase. Keys that are Remotion-only —
bounce, wiggle, palette, wordGap — are reported as ignored rather than dropped
in silence, because a preset that visibly differs between the two paths should
say why.

Burn-in is DESTRUCTIVE: captions become pixels. Keep the clean master. The .ass
file is written either way, so an editor can re-time or restyle downstream.

Prints JSON: {"ass", "pages", "words", "video"?, "ignoredStyleKeys"}.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from video_studio.paths import studio_root

#: Style keys this renderer understands, mapped from styles.py's CAPTION_KEYS.
HONOURED = ("color", "highlight", "fontFamily", "fontSize", "stroke",
            "strokeWidth", "bottom", "wordsPerPage", "uppercase")
#: Recognised by styles.py but meaningless in ASS — motion and per-word spacing
#: have no representation in the subtitle format.
REMOTION_ONLY = ("bounce", "wiggle", "palette", "wordGap")

DEFAULTS = {
    "color": "#ffffff", "highlight": "#facc15", "fontFamily": "Inter",
    "fontSize": 56, "stroke": "#000000", "strokeWidth": 3,
    "bottom": 0.12, "wordsPerPage": 4, "uppercase": False,
}

#: A page also breaks on a long silence or a long run, not only on word count.
MAX_PAGE_MS = 1800
MAX_GAP_MS = 600

HEADER = """[Script Info]
Title: video-studio captions
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font_family},{font_size},{highlight},{color},{stroke},&H80000000,-1,0,0,0,100,100,0,0,1,{stroke_width},1,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ass_color(hex_color: str) -> str:
    """'#RRGGBB' → ASS '&H00BBGGRR'. ASS is BGR with a leading alpha byte."""
    value = (hex_color or "").lstrip("#")
    if len(value) != 6 or any(c not in "0123456789abcdefABCDEF" for c in value):
        value = "ffffff"
    r, g, b = value[0:2], value[2:4], value[4:6]
    return f"&H00{b}{g}{r}".upper()


def ass_time(ms: int) -> str:
    """Milliseconds → 'h:mm:ss.cc'. ASS resolution is a centisecond."""
    cs = round(max(int(ms), 0) / 10)
    s, cs = divmod(cs, 100)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def escape(text: str) -> str:
    # Braces delimit override blocks in ASS; a literal brace in narration would
    # silently swallow the rest of the line as a malformed tag.
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")


def paginate(timings: list[dict], *, offset_ms: int, words_per_page: int) -> list[dict]:
    """Group flat word timings into pages shown one at a time."""
    pages: list[dict] = []
    current: dict | None = None
    for t in timings:
        start = int(t["startMs"]) + offset_ms
        end = max(int(t["endMs"]) + offset_ms, start)
        if (current is None
                or len(current["tokens"]) >= words_per_page
                or (end - current["startMs"]) > MAX_PAGE_MS
                or (start - current["tokens"][-1]["toMs"]) > MAX_GAP_MS):
            if current is not None:
                pages.append(current)
            current = {"startMs": start, "endMs": end, "tokens": []}
        current["tokens"].append({"text": t["text"], "fromMs": start, "toMs": end})
        current["endMs"] = end
    if current is not None:
        pages.append(current)
    return pages


def render_ass(pages: list[dict], style: dict, width: int, height: int) -> str:
    lines = [HEADER.format(
        width=width, height=height,
        font_family=style["fontFamily"], font_size=int(style["fontSize"]),
        # Karaoke fills SecondaryColour → PrimaryColour, so the HIGHLIGHT is
        # primary and the resting text colour is secondary. Swapping these is
        # the classic way to get captions that highlight backwards.
        highlight=ass_color(style["highlight"]), color=ass_color(style["color"]),
        stroke=ass_color(style["stroke"]), stroke_width=int(style["strokeWidth"]),
        margin_v=int(height * float(style["bottom"])),
    )]
    for page in pages:
        if not page["tokens"]:
            continue
        parts: list[str] = []
        cursor = page["startMs"]
        for token in page["tokens"]:
            # Absorb the silence before a word into a k-tag of its own, so the
            # highlight lands on the word rather than drifting early.
            gap_cs = max(round((token["fromMs"] - cursor) / 10), 0)
            if gap_cs:
                parts.append(f"{{\\k{gap_cs}}}")
            dur_cs = max(round((token["toMs"] - token["fromMs"]) / 10), 1)
            text = token["text"].upper() if style["uppercase"] else token["text"]
            parts.append(f"{{\\k{dur_cs}}}{escape(text)} ")
            cursor = max(token["toMs"], cursor)
        lines.append(
            f"Dialogue: 0,{ass_time(page['startMs'])},{ass_time(page['endMs'])},"
            f"Caption,,0,0,0,,{''.join(parts).rstrip()}"
        )
    return "\n".join(lines) + "\n"


def load_style(name: str | None, overrides: dict) -> tuple[dict, list[str]]:
    """Merge defaults, an optional named preset, then explicit flags."""
    style = dict(DEFAULTS)
    ignored: list[str] = []
    if name:
        preset = find_preset(name)
        captions = preset.get("captions", preset)
        for key, value in captions.items():
            if key in HONOURED:
                style[key] = value
            elif key in REMOTION_ONLY:
                ignored.append(key)
    style.update({k: v for k, v in overrides.items() if v is not None})
    return style, ignored


def find_preset(name: str) -> dict:
    """Read a styles.py preset: markdown with one fenced ```json block.

    Searches the same places styles.py does, minus the project-local tier —
    this program is given a project only sometimes.
    """
    import os
    import re
    roots = []
    env = os.environ.get("VIDEO_STUDIO_STYLES")
    if env:
        roots.append(Path(env).expanduser())
    roots += [Path.home() / ".config" / "video-studio" / "styles",
              studio_root() / "styles"]
    for root in roots:
        candidate = root / f"{name}.md"
        if candidate.exists():
            block = re.search(r"```json\s*(.*?)```", candidate.read_text(), re.S)
            if not block:
                raise SystemExit(f"preset {candidate} has no ```json block")
            return json.loads(block.group(1))
    raise SystemExit(
        f"no style preset named {name!r}. Looked in: "
        + ", ".join(str(r) for r in roots)
        + "\nList what exists with: video-studio styles --list"
    )


def burn(video: Path, ass: Path, out: Path) -> None:
    """Burn subtitles into a copy of the video. Audio is stream-copied."""
    out.parent.mkdir(parents=True, exist_ok=True)
    # The subtitles filter takes a path in its own mini-syntax, where ':' and
    # '\' are separators — escape them rather than hope the path is plain.
    escaped = str(ass).replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")
    cmd = ["ffmpeg", "-y", "-i", str(video), "-vf", f"subtitles='{escaped}'",
           "-c:a", "copy", str(out)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        raise SystemExit("ffmpeg not found — install it, or drop --video to "
                         "write the .ass file only.")
    except subprocess.CalledProcessError as exc:
        tail = (exc.stderr or "").strip().splitlines()[-6:]
        raise SystemExit("ffmpeg failed to burn captions:\n  " + "\n  ".join(tail))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--timings", help="one <scene>.timings.json")
    ap.add_argument("--project", help="every audio/*.timings.json in a project")
    ap.add_argument("--video", help="burn onto this clip (with --timings)")
    ap.add_argument("--out", required=True, help="file, or directory with --project")
    ap.add_argument("--style", help="named preset from styles.py")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--color"); ap.add_argument("--highlight")
    ap.add_argument("--font-family", dest="fontFamily")
    ap.add_argument("--font-size", dest="fontSize", type=int)
    ap.add_argument("--words-per-page", dest="wordsPerPage", type=int)
    ap.add_argument("--uppercase", action="store_true", default=None)
    a = ap.parse_args()

    if bool(a.timings) == bool(a.project):
        raise SystemExit("pass exactly one of --timings or --project")
    if a.video and not a.timings:
        raise SystemExit("--video burns one clip, so it needs --timings, not --project")

    style, ignored = load_style(a.style, {
        "color": a.color, "highlight": a.highlight, "fontFamily": a.fontFamily,
        "fontSize": a.fontSize, "wordsPerPage": a.wordsPerPage,
        "uppercase": a.uppercase,
    })
    if ignored:
        print(f"note: preset keys with no ASS equivalent were ignored: "
              f"{', '.join(sorted(set(ignored)))} — the burnt captions will differ "
              f"from the Remotion render in motion, not in wording.", file=sys.stderr)

    if a.timings:
        timings = json.loads(Path(a.timings).expanduser().read_text())
        if not timings:
            raise SystemExit(f"{a.timings} is empty — nothing to caption.")
        pages = paginate(timings, offset_ms=0,
                         words_per_page=int(style["wordsPerPage"]))
        out = Path(a.out).expanduser().resolve()
        ass_path = out if out.suffix == ".ass" else out.with_suffix(".ass")
        ass_path.parent.mkdir(parents=True, exist_ok=True)
        ass_path.write_text(render_ass(pages, style, a.width, a.height))
        result = {"ass": str(ass_path), "pages": len(pages), "words": len(timings),
                  "ignoredStyleKeys": sorted(set(ignored))}
        if a.video:
            burn(Path(a.video).expanduser().resolve(), ass_path, out)
            result["video"] = str(out)
        print(json.dumps(result, indent=2))
        return

    project = Path(a.project).expanduser().resolve()
    out_dir = Path(a.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted((project / "audio").glob("*.timings.json"))
    if not files:
        raise SystemExit(
            f"no timings in {project / 'audio'} — run tts_kokoro (synthesised "
            f"narration) or gen_captions (recorded narration) first."
        )
    written = []
    for timings_file in files:
        timings = json.loads(timings_file.read_text())
        if not timings:
            continue
        pages = paginate(timings, offset_ms=0,
                         words_per_page=int(style["wordsPerPage"]))
        scene = timings_file.name.removesuffix(".timings.json")
        target = out_dir / f"{scene}.ass"
        target.write_text(render_ass(pages, style, a.width, a.height))
        written.append({"scene": scene, "ass": str(target), "pages": len(pages)})
    print(json.dumps({"project": str(project), "written": len(written),
                      "ignoredStyleKeys": sorted(set(ignored)),
                      "scenes": written}, indent=2))


if __name__ == "__main__":
    main()
