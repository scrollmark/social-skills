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


def test_bundled_scripts_are_the_ones_the_repo_ships():
    """BUNDLED is a record, not a glob — an installed copy has no skills/ tree
    to glob. So the record is checked against the tree here, where there is one."""
    shipped = {p.stem for p in (REPO / "skills").glob("*/scripts/*.py")}
    assert F.BUNDLED == shipped


def test_every_named_program_exists(shipped):
    """`needs: measure` names a bundled script; `needs: gen_boil` names a
    package command. Both are real, and a format may name more than one."""
    named = {n for f in shipped.values() for n in F.needed(f["values"])}
    assert named, "no format names a program at all — the key stopped being read"
    assert named <= set(COMMANDS) | F.BUNDLED
    assert F.needed({"needs": "track_pointing, measure"}) == ["track_pointing", "measure"]
    assert F.needed({}) == []


def test_a_repeated_key_or_a_missing_colon_is_reported(tmp_path):
    # The two typos a key-name check cannot see. The second is the dangerous
    # one: the line vanishes, so the format silently stops stating a fact.
    (tmp_path / "formats").mkdir()
    (tmp_path / "formats" / "x.md").write_text(
        "---\nname: x\naspect: 9:16\naspect: 16:9\ncaptions\n---\n\n# x\n")
    fmt = F.find_formats(tmp_path)["x"]
    problems = F.validate(fmt)
    assert any("declared twice" in p for p in problems)
    assert any("not a `key: value` line" in p for p in problems)
    assert fmt["values"]["aspect"] == "16:9"  # last one really did win


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


def test_a_style_with_unknown_keys_is_reported_through_the_composition(tmp_path, capsys):
    """`styles --show` reports an unknown caption key; composing must too.

    An unknown key renders as nothing, which looks like a styling choice
    rather than a bug — and two programs disagreeing about one file is worse
    than either answer.
    """
    (tmp_path / "styles").mkdir()
    (tmp_path / "styles" / "bad.md").write_text(
        '---\nname: bad\ndescription: typo\n---\n\n```json\n'
        '{"captions": {"colour": "#fff"}, "cards": {}}\n```\n')
    import sys as _sys
    argv = _sys.argv
    _sys.argv = ["formats", "--show", "explainer", "--style", "bad", "--project", str(tmp_path)]
    try:
        F.main()
    finally:
        _sys.argv = argv
    out = json.loads(capsys.readouterr().out)
    assert any("colour" in p for p in out["problems"]), out["problems"]


def test_an_empty_filter_result_is_not_reported_as_an_empty_install(tmp_path, capsys):
    import sys as _sys
    argv = _sys.argv
    _sys.argv = ["formats", "--list", "--aspect", "4:5"]
    try:
        F.main()
    finally:
        _sys.argv = argv
    out = capsys.readouterr().out
    assert "none of the" in out and "4:5" in out
    assert "no formats found" not in out


def test_a_filter_naming_no_real_frame_is_refused():
    import sys as _sys
    argv = _sys.argv
    _sys.argv = ["formats", "--list", "--aspect", "widescreen"]
    try:
        with pytest.raises(SystemExit) as e:
            F.main()
    finally:
        _sys.argv = argv
    assert "widescreen" in str(e.value)


def test_the_cli_runs_it(tmp_path):
    r = subprocess.run([sys.executable, "-m", "video_studio.cli", "formats", "--list",
                        "--aspect", "9:16", "--json"],
                       capture_output=True, text=True, cwd=REPO,
                       env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(REPO / "src"),
                            "HOME": str(tmp_path)})
    assert r.returncode == 0, r.stderr
    rows = json.loads(r.stdout)
    names = {row["name"] for row in rows}
    # Eight of the ten: five are 9:16 outright and three carry it as alsoWorks.
    # The count is asserted, not just membership — a filter that returned
    # everything would pass a membership check.
    assert names == {"boil", "brand-origin", "cinematic", "explainer", "pip-story",
                     "product-launch", "talking-head", "timeline-explainer"}
    assert "pointer-popups" not in names  # source frame, fits nothing named
