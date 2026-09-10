# /// script
# requires-python = ">=3.11"
# ///
"""The formats, as data.

A format answers "what shape is this video" -- how many scenes, what aspect,
whether it speaks, what it needs built before it can be built. That has always
been written down, in ``skills/video-formats/references/formats/<name>.md``, as
a paragraph under ``## Composition`` that a person reads and a program cannot.

This module reads the frontmatter that now sits above that paragraph, so the
same facts are available to a script: which formats exist, which of them fit a
9:16 slot, which need ``track_pointing`` installed before they will build. The
prose stays where it was and stays authoritative -- the frontmatter was
transcribed from it, key by key, and where a format does not state something
the key is simply absent rather than guessed.

Deliberately parallel to ``styles.py``: same root-resolution shape, same
``--list/--show/--json`` surface, same "first root wins" override rule. A
format and a style are the two halves of a template -- ``--show NAME --style
STYLE`` composes them into one object -- and two halves that behave differently
would be two things to learn instead of one.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from video_studio.paths import studio_root

SKILL_ROOT = studio_root()
USER_FORMATS = Path.home() / ".config" / "video-studio" / "formats"

#: Where the format documents live in the source tree. They are skill prose
#: first and data second, so they stay in the skill rather than moving under
#: src/ -- the wheel force-includes this directory as ``video_studio/formats``.
SKILL_FORMATS = SKILL_ROOT / "skills" / "video-formats" / "references" / "formats"

#: The same documents, as shipped inside an installed package. Lowest
#: precedence, and the only tier that exists for someone who ran `pip install`
#: and has no checkout to find. See the same reasoning in ``styles.py``.
PACKAGE_FORMATS = Path(__file__).resolve().parent.parent / "formats"

#: Keys a format document may declare. Anything else is a typo, and a typo in
#: frontmatter is invisible: it parses, it stores, and nothing ever reads it.
FORMAT_KEYS = {
    "name",          # the id, and the file stem
    "title",         # the composer-facing name, e.g. TimelineExplainer
    "description",   # one line, for a list
    "aspect",        # the frame it is composed for
    "alsoWorks",     # a second frame it survives
    "scenes",        # how many, as a range
    "sceneSeconds",  # how long each runs, as a range
    "captions",      # on / off / optional
    "narration",     # one voice / two voices / on camera / optional
    "music",         # required, where the format does not work without it
    "needs",         # a program that must run before this format can build
}

#: Programs that ship inside a skill folder rather than in the package, so
#: they are not in ``COMMANDS`` and a ``needs:`` naming one would otherwise be
#: reported as nonexistent. Recorded here rather than globbed, because an
#: installed copy has no ``skills/`` tree to glob; ``test_formats.py`` checks
#: this list against the repo.
BUNDLED = {"doctor", "measure", "normalize_audio", "poster", "prekey", "qc_render"}

#: ``aspect`` values that mean something downstream. ``source`` is a real
#: answer: a format built on the user's own footage keeps its frame.
ASPECTS = {"9:16", "16:9", "1:1", "4:5", "source"}


def format_roots(project: Path | None) -> list[Path]:
    roots = []
    if project:
        roots.append(project / "formats")
    if os.environ.get("VIDEO_STUDIO_FORMATS"):
        roots.append(Path(os.environ["VIDEO_STUDIO_FORMATS"]))
    roots.append(USER_FORMATS)
    roots.append(SKILL_ROOT / "formats")
    roots.append(SKILL_FORMATS)
    roots.append(PACKAGE_FORMATS)
    return roots


def parse_format(path: Path) -> dict:
    """Frontmatter, and the document beneath it left alone.

    Reports the two typo classes a key-name check cannot see: a repeated key,
    where the last one silently wins, and a line with no colon, which vanishes
    entirely. A dropped `captions` line is exactly the invisible mistake this
    module exists to catch, and it would otherwise parse clean.
    """
    text = path.read_text()
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta: dict[str, str] = {}
    parse_problems: list[str] = []
    if fm:
        for line in fm.group(1).splitlines():
            if not line.strip():
                continue
            if ":" not in line:
                parse_problems.append(f"{line.strip()!r} is not a `key: value` line")
                continue
            k, v = line.split(":", 1)
            k = k.strip()
            if k in meta:
                parse_problems.append(f"{k} is declared twice — the last one wins silently")
            meta[k] = v.strip()
    meta.setdefault("name", path.stem)
    return {"name": meta["name"], "path": str(path), "values": meta,
            "documented": fm is not None, "parseProblems": parse_problems}


def find_formats(project: Path | None) -> dict[str, dict]:
    """Name -> format. First root wins, so a project can override a shipped one."""
    out: dict[str, dict] = {}
    for root in format_roots(project):
        if not root.is_dir():
            continue
        for p in sorted(root.glob("*.md")):
            fmt = parse_format(p)
            out.setdefault(fmt["name"], fmt)
    return out


def validate(fmt: dict) -> list[str]:
    """Problems worth refusing over, reported rather than silently ignored."""
    problems = []
    if not fmt["documented"]:
        problems.append("no frontmatter — this format is prose only")
        return problems
    problems.extend(fmt.get("parseProblems", []))
    values = fmt["values"]
    for k in values:
        if k not in FORMAT_KEYS:
            problems.append(f"{k} is not a format key")
    for k in ("aspect", "alsoWorks"):
        if k in values and values[k] not in ASPECTS:
            problems.append(f"{k}: {values[k]!r} is not one of {sorted(ASPECTS)}")
    # A format naming a program that does not exist is the expensive kind of
    # wrong: it reads as a working instruction right up until someone runs it.
    # Comma-separated, because a format can need two: `pointer-popups` wants
    # the tracker AND `measure`, and one slot could only say half of that.
    from video_studio.cli import COMMANDS
    for need in needed(values):
        if need not in COMMANDS and need not in BUNDLED:
            problems.append(f"needs: no program named {need!r} — `video-studio` lists them")
    return problems


def needed(values: dict) -> list[str]:
    """The programs a format names, in order."""
    return [n.strip() for n in values.get("needs", "").split(",") if n.strip()]


def compose(fmt: dict, style: dict | None) -> dict:
    """A template: the shape from a format, the look from a style.

    Kept as two named halves rather than one merged blob so the answer to
    "where did this come from" is in the object itself. Nothing here resolves
    into a storyboard — `styles --apply` does that, and doing it twice would be
    two answers.
    """
    template = {"format": fmt["values"], "formatDoc": fmt["path"]}
    if style:
        template["style"] = style["values"]
        template["styleName"] = style["name"]
    return template


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--show", metavar="NAME")
    ap.add_argument("--style", metavar="NAME", help="compose --show with a style preset")
    ap.add_argument("--aspect", metavar="RATIO", help="--list only formats that fit")
    ap.add_argument("--project", type=Path, help="also look in <project>/formats/")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    formats = find_formats(args.project)

    if args.list:
        if args.aspect and args.aspect not in ASPECTS:
            raise SystemExit(f"{args.aspect!r} is not a frame any format is composed "
                             f"for. One of {sorted(ASPECTS)}.")
        rows = []
        for f in formats.values():
            v = f["values"]
            if args.aspect and args.aspect not in (v.get("aspect"), v.get("alsoWorks")):
                continue
            rows.append({"name": f["name"], "title": v.get("title", ""),
                         "description": v.get("description", ""),
                         "aspect": v.get("aspect", ""),
                         "alsoWorks": v.get("alsoWorks", ""),
                         "needs": v.get("needs", ""), "path": f["path"]})
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            if not rows and args.aspect:
                # Not "no formats found": ten were, and the filter excluded
                # them. The other message sends a reader to check their install.
                print(f"none of the {len(formats)} formats found are composed for "
                      f"{args.aspect}.")
            elif not rows:
                print("no formats found. the video-formats skill ships them; "
                      "~/.config/video-studio/formats/ is yours.")
            for r in rows:
                frame = r["aspect"] + (f" (+{r['alsoWorks']})" if r["alsoWorks"] else "")
                print(f"{r['name']:<20} {frame:<16} {r['description']}")
        return

    if args.show:
        f = formats.get(args.show)
        if not f:
            raise SystemExit(f"no format {args.show!r}. --list to see them.")
        problems = validate(f)
        style = None
        if args.style:
            from video_studio.project.styles import find_presets
            presets = find_presets(args.project)
            style = presets.get(args.style)
            if not style:
                raise SystemExit(f"no style {args.style!r}. `video-studio styles --list`.")
            # The style's own check, run here too. A composed template embeds
            # the preset's values verbatim, and an unknown caption key renders
            # as nothing -- so reporting clean on a style that `styles --show`
            # reports on would make the two programs disagree about one file.
            from video_studio.project.styles import validate as validate_style
            problems += [f"style {style['name']}: {p}" for p in validate_style(style["values"])]
        print(json.dumps({"name": f["name"], **compose(f, style),
                          "problems": problems}, indent=2))
        return

    ap.print_help()


if __name__ == "__main__":
    main()
