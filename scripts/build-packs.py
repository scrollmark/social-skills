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
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLES = ROOT / "src" / "video_studio" / "styles"
FORMATS = ROOT / "skills" / "video-formats" / "references" / "formats"
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


def commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001 -- provenance is nice to have, not required
        return ""


def build() -> tuple[dict, dict, list[str]]:
    problems: list[str] = []
    assets = style_assets(problems) + format_assets(problems)

    pack = {
        "format": PACK_FORMAT,
        "id": PACK_ID,
        "version": PACK_VERSION,
        "name": "Scrollmark Core",
        "description": "The looks and shapes this repository ships.",
        "keyspace": keyspace.VERSION,
        "tier": "free",
        "license": {"spdx": "CC-BY-4.0", "holder": "Scrollmark"},
        "provenance": {"repo": "scrollmark/social-skills", "commit": commit()},
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
