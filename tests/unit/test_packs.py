"""The compiled pack, which is how the editor reaches this library.

Until it existed a preset became a video only by being expanded into a
storyboard offline and built into a blank project. Nothing here invents a
value: every colour, size and face is read from the preset that defines it, and
a preset that will not validate is an error rather than a blank entry.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "packs"
SCRIPT = REPO / "scripts" / "build-packs.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=REPO
    )


@pytest.fixture(scope="module")
def pack() -> dict:
    index = json.loads((DIST / "index.json").read_text())
    entry = index["packs"][0]
    return json.loads((DIST / entry["url"]).read_text())


def test_the_committed_pack_matches_the_presets():
    """The gate. `packs/` is committed so consumers can fetch it directly,
    which also means it can fall behind the presets it was compiled from."""
    result = run("--check")
    assert result.returncode == 0, result.stderr


def test_the_pack_records_nothing_that_changes_between_builds(pack: dict):
    """No timestamp, and no commit SHA.

    Both change on every build, and this file is COMMITTED and compared against
    a rebuild -- so either one makes the drift check fail forever. It did: the
    first version embedded `git rev-parse HEAD`, which is necessarily the
    commit BEFORE the one carrying it, so it could never have been right
    either. CI caught it; the local run could not, because locally HEAD had not
    moved since the build.
    """
    volatile = {"commit", "builtAt", "generatedAt", "timestamp"}
    assert set(pack.get("provenance", {})) & volatile == set()
    index = json.loads((DIST / "index.json").read_text())
    assert set(index) & volatile == set()


def test_the_build_is_deterministic():
    """`--check` compares a rebuild against the committed file, so a build that
    changed nothing must produce an identical one -- otherwise the check
    reports drift on every run and stops meaning anything. This is why the
    index carries no timestamp."""
    before = (DIST / "index.json").read_text()
    assert run().returncode == 0
    assert (DIST / "index.json").read_text() == before


def test_every_style_and_format_is_carried(pack: dict):
    styles = len(list((REPO / "src" / "video_studio" / "styles").glob("*.md")))
    formats = len(
        list((REPO / "skills" / "video-formats" / "references" / "formats").glob("*.md"))
    )
    kinds = [asset["kind"] for asset in pack["assets"]]
    assert kinds.count("style") == styles
    assert kinds.count("format") == formats


def test_every_asset_carries_its_guidance(pack: dict):
    """The prose above the json block is what a person reads before choosing
    and what the bridge hands an agent -- one description, two surfaces.
    Dropping it leaves the editor showing a name and a swatch."""
    missing = [a["id"] for a in pack["assets"] if not a.get("guidance")]
    assert missing == []


def test_a_style_names_every_face_it_uses(pack: dict):
    """So the editor can refuse an asset whose face it cannot load. An
    unloaded family does not fail -- `measureText` returns the fallback's
    metrics and the render agrees with itself."""
    for asset in pack["assets"]:
        if asset["kind"] != "style":
            continue
        stacks = [
            (card or {}).get("fontFamily")
            for card in (asset["values"].get("cards") or {}).values()
        ]
        stacks.append((asset["values"].get("captions") or {}).get("fontFamily"))
        for stack in stacks:
            if not stack:
                continue
            for family in stack.split(","):
                assert family.strip().strip("\"'") in asset["requiresFonts"], asset["id"]


def test_digests_are_of_values_not_of_the_whole_asset(pack: dict):
    """Drift compares an asset's digest against the one recorded at apply time.
    If the digest covered `name` or `guidance`, editing a description would
    tell every project the look had changed."""
    import hashlib

    for asset in pack["assets"]:
        canonical = json.dumps(
            asset["values"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        expected = "sha256-" + hashlib.sha256(canonical.encode()).hexdigest()
        assert asset["digest"] == expected, asset["id"]


def test_ids_are_unique_and_kind_prefixed(pack: dict):
    ids = [asset["id"] for asset in pack["assets"]]
    assert len(ids) == len(set(ids))
    for asset in pack["assets"]:
        assert asset["id"].startswith(f"{asset['kind']}/")


def test_the_index_points_at_a_file_that_exists(pack: dict):
    index = json.loads((DIST / "index.json").read_text())
    for entry in index["packs"]:
        assert (DIST / entry["url"]).exists()
        assert sum(entry["assetCounts"].values()) == len(pack["assets"])
