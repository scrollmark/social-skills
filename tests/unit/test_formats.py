"""The format documents, read as data.

Every claim here is about the ten shipped formats rather than about a fixture,
because the thing that breaks is a real file: a format grows a key nothing
reads, or names a generator that was renamed, and the document goes on looking
correct.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from video_studio.cli import COMMANDS  # noqa: E402
from video_studio.project import formats as F  # noqa: E402


@pytest.fixture(scope="module")
def shipped() -> dict:
    found = F.find_formats(None)
    assert found, "no formats found from the checkout"
    return found


def test_every_format_document_has_frontmatter(shipped):
    docs = sorted(p.stem for p in F.SKILL_FORMATS.glob("*.md"))
    assert sorted(shipped) == docs
    undocumented = [n for n, f in shipped.items() if not f["documented"]]
    assert not undocumented, f"formats with no frontmatter: {undocumented}"


def test_shipped_formats_validate(shipped):
    problems = {n: p for n, f in shipped.items() if (p := F.validate(f))}
    assert not problems, json.dumps(problems, indent=2)


def test_a_needs_that_names_no_program_is_caught():
    # The check exists because `needs: track_pointer` reads exactly like
    # `needs: track_pointing` and fails only when somebody runs it.
    fake = {"name": "x", "path": "x.md", "documented": True,
            "values": {"name": "x", "needs": "track_pointer"}}
    assert any("no program named" in p for p in F.validate(fake))
    real = dict(fake, values={"name": "x", "needs": "track_pointing"})
    assert F.validate(real) == []
    assert "track_pointing" in COMMANDS


def test_unknown_keys_and_frames_are_reported():
    fmt = {"name": "x", "path": "x.md", "documented": True,
           "values": {"name": "x", "aspect": "widescreen", "vibe": "cool"}}
    problems = F.validate(fmt)
    assert any("vibe is not a format key" in p for p in problems)
    assert any("aspect" in p for p in problems)


def test_a_project_root_shadows_a_shipped_format(tmp_path):
    (tmp_path / "formats").mkdir()
    (tmp_path / "formats" / "cinematic.md").write_text(
        "---\nname: cinematic\ndescription: ours\naspect: 1:1\n---\n\n# ours\n")
    found = F.find_formats(tmp_path)
    assert found["cinematic"]["values"]["description"] == "ours"
    # and the other nine still come from the skill
    assert len(found) == len(F.find_formats(None))


def test_compose_keeps_the_two_halves_named(shipped):
    style = {"name": "bold-neon", "values": {"captions": {"color": "#fff"}}}
    out = F.compose(shipped["explainer"], style)
    assert out["format"]["name"] == "explainer"
    assert out["styleName"] == "bold-neon"
    assert out["style"]["captions"]["color"] == "#fff"
    assert F.compose(shipped["explainer"], None).keys() == {"format", "formatDoc"}


def test_the_cli_runs_it(tmp_path):
    r = subprocess.run([sys.executable, "-m", "video_studio.cli", "formats", "--list",
                        "--aspect", "9:16", "--json"],
                       capture_output=True, text=True, cwd=REPO,
                       env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(REPO / "src"),
                            "HOME": str(tmp_path)})
    assert r.returncode == 0, r.stderr
    rows = json.loads(r.stdout)
    names = {row["name"] for row in rows}
    assert "explainer" in names          # 9:16 outright
    assert "boil" in names               # 16:9, alsoWorks 9:16
    assert "pointer-popups" not in names  # source frame, fits nothing named
