#!/usr/bin/env python3
"""Compile the styles and formats in this repo into a publishable pack.

    python3 scripts/build-packs.py            # write packs/
    python3 scripts/build-packs.py --check    # report drift, write nothing

A *pack* is how the editor reaches this library. Until it existed, a preset
became a video only by being expanded into a storyboard offline and built into
a blank project -- there was no way to apply a look to something somebody was
already editing.

Nothing here invents a value. Every colour, size and face is read from the
preset that already defines it, and a preset that will not parse is an error
rather than a blank entry. That discipline is the whole reason the gallery's
swatches can be trusted, and it is worth keeping on this side too.

The compiled form is JSON; the authored form stays markdown-with-one-json-block,
because the prose above the block is the only place "how and when to use this"
has ever lived, and it is what the editor shows a person and hands an agent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLES = ROOT / "src" / "video_studio" / "styles"
FORMATS = ROOT / "skills" / "video-formats" / "references" / "formats"
TITLE_SCENES = ROOT / "src" / "video_studio" / "title_scenes"
TEMPLATES = ROOT / "src" / "video_studio" / "templates"
#: Committed, at the repo root rather than under `dist/`, which is gitignored
#: as the Python build output -- putting the packs there would have published
#: nothing at all. Consumers read it over raw.githubusercontent.com, the same
#: route the editor already uses for `keyspace.json`, so no Pages setup is
#: needed for it to work.
OUT = ROOT / "packs"

PACK_ID = "scrollmark-core"
PACK_FORMAT = "scrollmark.pack/1"

#: Bumped when the CONTENT changes, not when this script does. The editor
#: compares versions to decide what to browse, and a version that moved for a
#: refactor would send every project looking for an update that changes nothing.
PACK_VERSION = "1.0.0"

sys.path.insert(0, str(ROOT / "src"))
from video_studio.project import keyspace  # noqa: E402
from video_studio.project.styles import validate as validate_style  # noqa: E402


def canonical(value: object) -> str:
    """JSON with sorted keys, so a digest depends on values and not on order."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: object) -> str:
    return "sha256-" + hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def frontmatter(text: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    out = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, rest = line.partition(":")
            out[key.strip()] = rest.strip()
    return out


def json_block(text: str) -> dict | None:
    match = re.search(r"```json\n(.*?)```", text, re.S)
    return json.loads(match.group(1)) if match else None


def guidance(text: str) -> str:
    """The prose between the frontmatter and the JSON block.

    This is the part a person reads before choosing, and the same string the
    bridge hands an agent -- one description, two surfaces. Stripping it would
    leave the editor showing a name and a swatch and nothing about when to
    reach for the thing.
    """
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    body = re.sub(r"```json\n.*?```", "", body, flags=re.S)
    return body.strip()


def font_families(values: dict) -> list[str]:
    """Every family named anywhere in a preset, including every name in a stack.

    Listed so the editor can refuse to apply an asset whose face it cannot
    load. `measureText` on an unloaded family silently returns the fallback's
    metrics, so an asset that names an unavailable face does not fail -- it
    renders wrong and agrees with itself.
    """
    families: list[str] = []
    for card in (values.get("cards") or {}).values():
        stack = card.get("fontFamily")
        if isinstance(stack, str):
            families += [name.strip().strip("\"'") for name in stack.split(",")]
    stack = (values.get("captions") or {}).get("fontFamily")
    if isinstance(stack, str):
        families += [name.strip().strip("\"'") for name in stack.split(",")]
    seen: list[str] = []
    for family in families:
        if family and family not in seen:
            seen.append(family)
    return seen


def style_assets(problems: list[str]) -> list[dict]:
    assets = []
    for path in sorted(STYLES.glob("*.md")):
        text = path.read_text()
        values = json_block(text)
        meta = frontmatter(text)
        if values is None:
            problems.append(f"{path.name}: no json block")
            continue
        invalid = validate_style(values)
        if invalid:
            # Refused, not carried. A preset with an unknown key renders as
            # nothing downstream, which reads as a styling choice.
            problems += [f"{path.name}: {reason}" for reason in invalid]
            continue
        assets.append(
            {
                "id": f"style/{path.stem}",
                "kind": "style",
                "name": meta.get("name", path.stem),
                "description": meta.get("description", ""),
                "guidance": guidance(text),
                "status": "stable",
                "revision": 1,
                "requiresFonts": font_families(values),
                "digest": digest(values),
                "values": values,
            }
        )
    return assets


def format_assets(problems: list[str]) -> list[dict]:
    assets = []
    known = keyspace.space("format")
    aspects = keyspace.enum("aspect")
    for path in sorted(FORMATS.glob("*.md")):
        text = path.read_text()
        values = frontmatter(text)
        if not values:
            problems.append(f"{path.name}: no frontmatter")
            continue
        unknown = sorted(set(values) - known)
        if unknown:
            problems.append(f"{path.name}: not format keys: {', '.join(unknown)}")
            continue
        for key in ("aspect", "alsoWorks"):
            if key in values and values[key] not in aspects:
                problems.append(f"{path.name}: {key} {values[key]!r} is not an aspect")
        assets.append(
            {
                "id": f"format/{path.stem}",
                "kind": "format",
                "name": values.get("title", path.stem),
                "description": values.get("description", ""),
                "guidance": guidance(text),
                "status": "stable",
                "revision": 1,
                "digest": digest(values),
                "values": values,
            }
        )
    return assets


def title_scene_assets(problems: list[str]) -> list[dict]:
    """Layouts, not looks.

    A title scene names roles and leaves both the treatment and the words to
    someone else: the treatment to whichever style it is dressed in at apply
    time, the words to the scene. That is why none of these files carries a
    `styleRef` -- binding a layout to one of the 29 presets would mean writing
    the same three files 29 times, and would make "open this in the look the
    video already uses" impossible to ask for.
    """
    assets = []
    known = keyspace.space("titleScene")
    layer_keys = keyspace.space("titleSceneLayer")
    for path in sorted(TITLE_SCENES.glob("*.md")):
        text = path.read_text()
        values = json_block(text)
        meta = frontmatter(text)
        if values is None:
            problems.append(f"{path.name}: no json block")
            continue
        unknown = sorted(set(values) - known)
        if unknown:
            problems.append(f"{path.name}: not title-scene keys: {', '.join(unknown)}")
            continue
        if not isinstance(values.get("seconds"), (int, float)):
            problems.append(f"{path.name}: seconds must be a number")
            continue
        layers = values.get("layers")
        if not isinstance(layers, list) or not layers:
            problems.append(f"{path.name}: needs at least one layer")
            continue
        bad = False
        for index, layer in enumerate(layers):
            if not isinstance(layer, dict) or not layer.get("role"):
                problems.append(f"{path.name}: layer {index} has no role")
                bad = True
                continue
            stray = sorted(set(layer) - layer_keys)
            if stray:
                problems.append(
                    f"{path.name}: layer {index} sets {', '.join(stray)}, "
                    "which is not a layer key"
                )
                bad = True
            # The same line styles.py draws, from the other side. A layout that
            # shipped `text` would be the pack writing the video's words, and
            # the editor would render it as a deliberate choice.
            if "text" in layer:
                problems.append(
                    f"{path.name}: layer {index} sets text; the words belong to the scene"
                )
                bad = True
        if bad:
            continue
        assets.append(
            {
                "id": f"title-scene/{path.stem}",
                "kind": "title-scene",
                "name": meta.get("name", path.stem),
                "description": meta.get("description", ""),
                "guidance": guidance(text),
                "status": "stable",
                "revision": 1,
                "digest": digest(values),
                "values": values,
            }
        )
    return assets


def template_assets(problems: list[str]) -> list[dict]:
    """The curated pairing, which is the thing a person actually browses for.

    A format is a shape and a style is a look; neither alone is what anyone
    picks. Until these existed the pairings lived as two hand-kept Python
    literals inside the gallery site's `sync-gallery.py` -- which meant the
    editor could offer "summer-scrapbook" and could not offer "a season of
    phone footage, with one sentence worth keeping."

    Moving them here is a one-way door and worth naming as one: adding a
    template is now a release of this repository rather than a commit to the
    site. That is the point -- the editor cannot see a site commit -- and it
    does slow down purely editorial changes.
    """
    assets = []
    known = keyspace.space("template")
    copy_keys = keyspace.space("previewCopy")
    for path in sorted(TEMPLATES.glob("*.md")):
        text = path.read_text()
        values = json_block(text)
        meta = frontmatter(text)
        if values is None:
            problems.append(f"{path.name}: no json block")
            continue
        unknown = sorted(set(values) - known)
        if unknown:
            problems.append(f"{path.name}: not template keys: {', '.join(unknown)}")
            continue
        for key in ("formatRef", "styleRef", "why"):
            if not values.get(key):
                problems.append(f"{path.name}: {key} is required")
        copy = values.get("previewCopy")
        if copy is not None:
            if not isinstance(copy, dict):
                problems.append(f"{path.name}: previewCopy must be an object")
            else:
                stray = sorted(set(copy) - copy_keys)
                if stray:
                    problems.append(
                        f"{path.name}: previewCopy sets {', '.join(stray)}"
                    )
        assets.append(
            {
                "id": f"template/{path.stem}",
                "kind": "template",
                "name": meta.get("name", path.stem),
                "description": meta.get("description", ""),
                "guidance": guidance(text),
                "status": "stable",
                "revision": 1,
                "digest": digest(values),
                "values": values,
            }
        )
    return assets


def resolve_refs(assets: list[dict], problems: list[str]) -> None:
    """Every ref must name an asset in this same pack.

    Checked at BUILD time because the alternative is finding out at apply
    time: a template whose style was renamed still compiles, still ships, and
    then applies nothing -- which reads as the template being broken rather
    than the ref being stale.
    """
    ids = {asset["id"] for asset in assets}
    single = ("formatRef", "styleRef", "overlayRef", "titleSceneRef")
    for asset in assets:
        values = asset.get("values")
        if not isinstance(values, dict):
            continue
        refs = [values[key] for key in single if isinstance(values.get(key), str)]
        listed = values.get("sfxRefs")
        if isinstance(listed, list):
            refs += [ref for ref in listed if isinstance(ref, str)]
        for ref in refs:
            if ref not in ids:
                problems.append(f"{asset['id']}: {ref} is not in this pack")


def build() -> tuple[dict, dict, list[str]]:
    problems: list[str] = []
    assets = (
        style_assets(problems)
        + format_assets(problems)
        + title_scene_assets(problems)
        + template_assets(problems)
    )
    resolve_refs(assets, problems)

    pack = {
        "format": PACK_FORMAT,
        "id": PACK_ID,
        "version": PACK_VERSION,
        "name": "Scrollmark Core",
        "description": "The looks and shapes this repository ships.",
        "keyspace": keyspace.VERSION,
        "tier": "free",
        "license": {"spdx": "CC-BY-4.0", "holder": "Scrollmark"},
        # No commit SHA and no timestamp. Both change on every build, and this
        # file is COMMITTED and compared against a rebuild -- so either one
        # makes the drift check fail forever, which is exactly what happened:
        # the SHA recorded is necessarily the one BEFORE the commit that
        # carries it, so it could never be right either.
        "provenance": {"repo": "scrollmark/social-skills"},
        "assets": assets,
    }

    counts: dict[str, int] = {}
    for asset in assets:
        counts[asset["kind"]] = counts.get(asset["kind"], 0) + 1

    index = {
        "format": "scrollmark.packindex/1",
        # Not a timestamp: a build that changed nothing must produce an
        # identical file, or `--check` reports drift on every run and the
        # check stops meaning anything.
        "keyspace": keyspace.VERSION,
        "packs": [
            {
                "id": pack["id"],
                "version": pack["version"],
                "name": pack["name"],
                "description": pack["description"],
                "tier": pack["tier"],
                "assetCounts": counts,
        "digest": digest({k: v for k, v in pack.items() if k != "provenance"}),
                "url": f"{PACK_ID}@{PACK_VERSION}.json",
            }
        ],
    }
    return pack, index, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report drift, write nothing")
    args = ap.parse_args()

    pack, index, problems = build()
    if problems:
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        print(f"{len(problems)} problem(s); nothing written", file=sys.stderr)
        return 1

    files = {
        OUT / "index.json": index,
        OUT / f"{PACK_ID}@{PACK_VERSION}.json": pack,
    }

    if args.check:
        drifted = []
        for path, value in files.items():
            if not path.exists():
                drifted.append(f"{path.name} does not exist")
            elif json.loads(path.read_text()) != value:
                drifted.append(f"{path.name} differs from the presets")
        if drifted:
            for reason in drifted:
                print(f"  {reason}", file=sys.stderr)
            print("run: python3 scripts/build-packs.py", file=sys.stderr)
            return 1
        print(f"packs are current: {len(pack['assets'])} assets")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for path, value in files.items():
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(pack['assets'])} assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
