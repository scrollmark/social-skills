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


class TestTitleScenes:
    """Layouts, and the two things they must never carry."""

    def scenes(self, pack: dict) -> list[dict]:
        return [a for a in pack["assets"] if a["kind"] == "title-scene"]

    def test_they_are_in_the_pack(self, pack: dict) -> None:
        assert self.scenes(pack), "title scenes are authored but not compiled"

    def test_none_binds_itself_to_a_style(self, pack: dict) -> None:
        # A title scene is a LAYOUT and every preset can wear it. One that
        # named a style would have to be written 29 times, and would make
        # "open this in the look the video already uses" impossible to ask
        # for -- the editor's applier takes the style from the caller.
        for scene in self.scenes(pack):
            assert "styleRef" not in scene["values"], scene["id"]

    def test_none_writes_the_video_s_words(self, pack: dict) -> None:
        # The same line styles.py draws, from the other side. A layout
        # shipping `text` would put the pack's copy in someone's video and
        # the editor would render it as a deliberate choice.
        for scene in self.scenes(pack):
            for layer in scene["values"]["layers"]:
                assert "text" not in layer, scene["id"]

    def test_every_layer_names_a_role(self, pack: dict) -> None:
        for scene in self.scenes(pack):
            assert scene["values"]["layers"]
            for layer in scene["values"]["layers"]:
                assert layer.get("role"), scene["id"]

    def test_every_role_is_one_some_preset_styles(self, pack: dict) -> None:
        # Otherwise the scene compiles, ships, and rejects every layer at
        # apply time for a reason nobody sees until they try it.
        styled = {
            role
            for asset in pack["assets"]
            if asset["kind"] == "style"
            for role in (asset["values"].get("cards") or {})
        }
        for scene in self.scenes(pack):
            for layer in scene["values"]["layers"]:
                assert layer["role"] in styled, f"{scene['id']}: {layer['role']}"

    def test_guidance_survives_the_compile(self, pack: dict) -> None:
        # The prose is the only place "when to reach for this" has ever
        # lived, and it is the same string the editor shows a person and
        # hands an agent.
        for scene in self.scenes(pack):
            assert len(scene["guidance"]) > 200, scene["id"]


class TestTemplates:
    """The curated pairing, which is the thing a person actually browses for."""

    def templates(self, pack: dict) -> list[dict]:
        return [a for a in pack["assets"] if a["kind"] == "template"]

    def test_every_pairing_the_gallery_curated_is_here(self, pack: dict) -> None:
        # 21, the count that lived as a Python literal in the gallery site.
        # Losing one in the migration is silent: the site would simply render
        # a shorter page.
        assert len(self.templates(pack)) == 21

    def test_every_ref_resolves_inside_the_pack(self, pack: dict) -> None:
        # Checked at build time too. Here as well because the consequence is
        # invisible: a template whose style was renamed compiles, ships, and
        # then applies nothing, which reads as the template being broken.
        ids = {a["id"] for a in pack["assets"]}
        for template in self.templates(pack):
            assert template["values"]["formatRef"] in ids, template["id"]
            assert template["values"]["styleRef"] in ids, template["id"]

    def test_every_one_says_why(self, pack: dict) -> None:
        # The one sentence on a gallery card that is written rather than read
        # from a preset. It is the whole reason `template` is a kind.
        for template in self.templates(pack):
            assert len(template["values"]["why"]) > 20, template["id"]

    def test_preview_copy_is_curation_and_never_reaches_a_video(
        self, pack: dict
    ) -> None:
        # Two keys, both about what a TILE says. Anything else here would be
        # the pack writing the video's words.
        for template in self.templates(pack):
            copy = template["values"].get("previewCopy")
            if copy is not None:
                assert set(copy) <= {"title", "caption"}, template["id"]

    def test_the_five_recreations_kept_their_lines(self, pack: dict) -> None:
        # These are the moving previews and the ones somebody arriving is most
        # likely to be looking for. Their copy was hand-chosen against a
        # reference and is the easiest thing to lose in a migration.
        by_id = {a["id"]: a for a in self.templates(pack)}
        expected = {
            "template/daily-recap-summer-scrapbook": "Summer Vibes",
            "template/cinematic-weekend-gothic": "Weekend",
            "template/titled-video-postcard-serif": "New York",
        }
        for asset_id, title in expected.items():
            assert asset_id in by_id, asset_id
            assert by_id[asset_id]["values"]["previewCopy"]["title"] == title
