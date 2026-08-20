# /// script
# requires-python = ">=3.11"
# ///
"""Reusable look presets: captions and card styling, defined once and reused.

Usage:
  uv run scripts/styles.py --list                       # every preset found
  uv run scripts/styles.py --show tourism               # resolved values
  uv run scripts/styles.py --apply tourism --storyboard project/storyboard.json
  uv run scripts/styles.py --save mine --from project/storyboard.json

Why this exists: three tourism spots were built in one session and each one
hand-rolled the same palette, the same label/stat/title rectangles and the same
tracking, as literals inside its own generator script. They drifted — different
rect heights for the same kind of label — and none of it was reusable the next
day. A look is a thing a user has, not a thing a project has.

WHERE PRESETS LIVE, highest precedence first:

  <project>/styles/*.md          this video only
  $VIDEO_STUDIO_STYLES/*.md      wherever the user points it
  ~/.config/video-studio/styles/*.md   the user's own, across every project
  <skill>/styles/*.md            the ones shipped here

The user-level directory is the important one: presets kept only inside the
skill checkout die with the checkout, and presets kept only in an agent's
memory die with the session. A preset the user defined once should still be
there next month, so `--save` writes to the user directory by default.

FORMAT: markdown with YAML-ish frontmatter and one fenced ```json block. The
prose above the block is for the human deciding whether to use it; the JSON is
the only part read by machines. Same shape as formats/*.md, deliberately —
this repo already teaches "drop a markdown file in a directory" as the way to
extend it, and a second, different mechanism would be one to learn for nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from video_studio.paths import studio_root

SKILL_ROOT = studio_root()
USER_STYLES = Path.home() / ".config" / "video-studio" / "styles"

#: Keys the composer actually renders for captions. Anything else in a preset
#: is a typo, and a typo that renders as nothing is the expensive kind.
CAPTION_KEYS = {"color", "highlight", "fontFamily", "palette", "stroke",
                "strokeWidth", "fontSize", "bounce", "wiggle", "uppercase",
                "bottom", "wordsPerPage", "wordGap"}
#: Card keys the composer renders, plus the placement keys that sit beside it.
CARD_KEYS = {"bg", "fg", "tracking", "fontSize", "align", "size"}
PLACEMENT_KEYS = {"rect", "pop", "fade", "atMs", "untilMs", "enter", "exit"}


#: Presets shipped inside the installed package. Lowest precedence of all, so
#: every other tier can shadow one by name.
PACKAGE_STYLES = Path(__file__).resolve().parent.parent / "styles"


def style_roots(project: Path | None) -> list[Path]:
    roots = []
    if project:
        roots.append(project / "styles")
    if os.environ.get("VIDEO_STUDIO_STYLES"):
        roots.append(Path(os.environ["VIDEO_STUDIO_STYLES"]))
    roots.append(USER_STYLES)
    roots.append(SKILL_ROOT / "styles")
    # SKILL_ROOT is the studio tree, which an installed copy does not have: with
    # no marker directory to find, studio_root() falls back to the cwd, so the
    # tier above resolves to <wherever you happen to be>/styles. That is present
    # for a developer standing in the checkout and absent for everyone who ran
    # `pip install` — the shipped presets would simply never appear for them.
    # This tier travels with the package instead.
    roots.append(PACKAGE_STYLES)
    return roots


def parse_preset(path: Path) -> dict:
    """Frontmatter + the first fenced json block."""
    text = path.read_text()
    meta = {"name": path.stem, "description": ""}
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if fm:
        for line in fm.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    block = re.search(r"```json\n(.*?)```", text, re.S)
    if not block:
        raise SystemExit(f"{path}: no ```json block — a preset with no values "
                         f"is a document, not a preset")
    try:
        values = json.loads(block.group(1))
    except json.JSONDecodeError as e:
        raise SystemExit(f"{path}: invalid JSON — {e}")
    return {"name": meta["name"], "description": meta.get("description", ""),
            "path": str(path), "values": values}


def find_presets(project: Path | None) -> dict[str, dict]:
    """Name -> preset. First root wins, so a project can override a shipped one."""
    out: dict[str, dict] = {}
    for root in style_roots(project):
        if not root.is_dir():
            continue
        for p in sorted(root.glob("*.md")):
            preset = parse_preset(p)
            out.setdefault(preset["name"], preset)
    return out


def validate(values: dict) -> list[str]:
    """Unknown keys, reported rather than silently dropped.

    A misspelled caption key does not error anywhere downstream — it renders as
    nothing, which looks like a styling choice rather than a bug.
    """
    problems = []
    for k in values.get("captions", {}):
        if k not in CAPTION_KEYS:
            problems.append(f"captions.{k} is not a caption key the composer renders")
    for role, spec in values.get("cards", {}).items():
        for k in spec:
            if k not in CARD_KEYS | PLACEMENT_KEYS:
                problems.append(f"cards.{role}.{k} is not a card or placement key")
    return problems


def apply(storyboard_path: Path, preset: dict) -> dict:
    """Resolve a preset INTO a storyboard, in place, and report what changed.

    Deliberately an expansion step rather than a lookup at render time. The
    storyboard stays the single readable document that says what the video is —
    open it and you can see the actual colours, not a preset name you have to
    go and resolve yourself. It also means a preset can be edited later without
    silently restyling videos that were already approved.
    """
    sb = json.loads(storyboard_path.read_text())
    values = preset["values"]
    changed = {"captions": False, "cards": 0, "unstyled": []}

    if values.get("captions"):
        # Explicit per-video settings win: a preset is a starting point, not an
        # override of a decision somebody already made for this video.
        sb["captionStyle"] = {**values["captions"], **(sb.get("captionStyle") or {})}
        changed["captions"] = True

    cards = values.get("cards", {})
    for scene in sb.get("scenes", []):
        for layer in scene.get("layers", []):
            card = layer.get("card")
            if not isinstance(card, dict):
                continue
            role = card.pop("style", None)
            if role is None:
                continue
            if role not in cards:
                changed["unstyled"].append(f"{scene.get('id')}/{layer.get('id')}:{role}")
                continue
            spec = cards[role]
            for k, v in spec.items():
                target = layer if k in PLACEMENT_KEYS else card
                target.setdefault(k, v)  # the scene's own value always wins
            changed["cards"] += 1

    sb["styleApplied"] = preset["name"]
    storyboard_path.write_text(json.dumps(sb, indent=2) + "\n")
    return changed


def save(name: str, storyboard_path: Path, dest_dir: Path) -> Path:
    """Lift the look out of a finished storyboard into a reusable preset."""
    sb = json.loads(storyboard_path.read_text())
    cards: dict[str, dict] = {}
    for scene in sb.get("scenes", []):
        for layer in scene.get("layers", []):
            card = layer.get("card")
            if not isinstance(card, dict):
                continue
            role = card.get("style") or ("title" if card.get("subtext") else "label")
            if role in cards:
                continue
            spec = {k: v for k, v in card.items() if k in CARD_KEYS}
            spec.update({k: v for k, v in layer.items() if k in PLACEMENT_KEYS})
            cards[role] = spec
    values = {"captions": sb.get("captionStyle") or {}, "cards": cards}
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / f"{name}.md"
    out.write_text(
        f"---\nname: {name}\ndescription: saved from {storyboard_path.name}\n---\n\n"
        f"# {name}\n\nLifted from a finished storyboard. Edit the JSON below;\n"
        f"the prose is for whoever picks this next.\n\n"
        f"```json\n{json.dumps(values, indent=2)}\n```\n"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--show", metavar="NAME")
    ap.add_argument("--apply", metavar="NAME")
    ap.add_argument("--save", metavar="NAME")
    ap.add_argument("--storyboard", type=Path)
    ap.add_argument("--project", type=Path, help="also look in <project>/styles/")
    ap.add_argument("--dest", type=Path, help="where --save writes (default: user styles)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    presets = find_presets(args.project)

    if args.list:
        rows = [{"name": p["name"], "description": p["description"], "path": p["path"]}
                for p in presets.values()]
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            if not rows:
                print("no presets found. styles/ ships some; ~/.config/video-studio/styles/ is yours.")
            for r in rows:
                print(f"{r['name']:<16} {r['description']}")
        return

    if args.show:
        p = presets.get(args.show)
        if not p:
            raise SystemExit(f"no preset {args.show!r}. --list to see them.")
        problems = validate(p["values"])
        print(json.dumps({"preset": p["name"], "path": p["path"],
                          "values": p["values"], "problems": problems}, indent=2))
        return

    if args.save:
        if not args.storyboard:
            raise SystemExit("--save needs --storyboard to lift the look from")
        out = save(args.save, args.storyboard, args.dest or USER_STYLES)
        print(json.dumps({"saved": str(out)}, indent=2))
        return

    if args.apply:
        if not args.storyboard:
            raise SystemExit("--apply needs --storyboard")
        p = presets.get(args.apply)
        if not p:
            raise SystemExit(f"no preset {args.apply!r}. --list to see them.")
        problems = validate(p["values"])
        if problems:
            # Refuse rather than warn. An unknown key renders as nothing, so a
            # warning here becomes "why is the stroke missing" an hour later.
            raise SystemExit("preset has keys the composer does not render:\n  "
                             + "\n  ".join(problems))
        changed = apply(args.storyboard, p)
        print(json.dumps({"applied": p["name"], **changed}, indent=2))
        if changed["unstyled"]:
            print(f"\nwarning: {len(changed['unstyled'])} card(s) asked for a role this "
                  f"preset does not define, and kept their own values:\n  "
                  + "\n  ".join(changed["unstyled"]), file=sys.stderr)
        return

    ap.print_help()


if __name__ == "__main__":
    main()
