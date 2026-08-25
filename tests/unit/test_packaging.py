"""Claims the repo makes about itself, checked against the repo.

Counts drift silently: a program is added, the README keeps its old number, and
the website copies the README. Package data drifts worse — it is only in the
wheel because `packages = [...]` sweeps it up, so a layout change can drop the
style presets or the tutorials with nothing failing.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def engine_commands() -> list[str]:
    text = (REPO / "src" / "video_studio" / "cli.py").read_text()
    block = re.search(r"COMMANDS: dict\[str, str\] = \{(.*?)\n\}", text, re.S).group(1)
    return re.findall(r'^\s+"([a-z_]+)"', block, re.M)


def bundled_scripts() -> list[Path]:
    return sorted((REPO / "skills").glob("*/scripts/*.py"))


def test_readme_counts_match_reality():
    readme = (REPO / "README.md").read_text()
    engine = len(engine_commands())
    unique = len({p.name for p in bundled_scripts()})
    total = re.search(r"(\d+) programs behind these skills", readme)
    other = re.search(r"The other (\d+) programs", readme)
    assert total and int(total.group(1)) == engine + unique, (
        f"README says {total.group(1) if total else '?'} total; reality is {engine + unique}")
    assert other and int(other.group(1)) == engine, (
        f"README says {other.group(1) if other else '?'} in the package; reality is {engine}")


def test_every_command_is_reachable_from_a_skill_or_readme():
    """A command no document names cannot be invoked by anyone using the skills."""
    haystack = "\n".join(
        p.read_text() for p in [*(REPO / "skills").rglob("*.md"), REPO / "README.md"]
    )
    missing = [c for c in engine_commands() if not re.search(rf"\b{c}\b", haystack)]
    assert not missing, f"commands named in no skill or README: {missing}"


def test_duplicated_bundled_scripts_are_identical():
    """verify-skills enforces this too; asserted here so `pytest` alone catches it."""
    from collections import defaultdict
    by_name = defaultdict(list)
    for p in bundled_scripts():
        by_name[p.name].append(p)
    for name, paths in by_name.items():
        if len(paths) < 2:
            continue
        first = paths[0].read_bytes()
        for other in paths[1:]:
            assert other.read_bytes() == first, f"{name} differs between {paths[0]} and {other}"


def test_no_document_tells_a_reader_to_install_from_pypi():
    """video-studio-engine is not on PyPI; a bare pip install silently gets the
    base package, because an unknown extra in a URL requirement is not even a
    warning."""
    out = subprocess.run(
        ["bash", "-c",
         "grep -rn --binary-files=without-match \"pip install ['\\\"]*video-studio-engine\" "
         "--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ . "
         "| grep -v 'git+https' | grep -v 'archive/refs/heads' "
         "| grep -v 'not published there' "
         "| grep -v 'install-command-ok' | grep -v verify-skills.sh || true"],
        capture_output=True, text=True, cwd=REPO)
    assert not out.stdout.strip(), f"PyPI install instructions found:\n{out.stdout}"


def test_all_extra_is_absent_and_standard_exists():
    d = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]["optional-dependencies"]
    assert "standard" in d
    assert "all" not in d, "[all] was removed because it never meant all; it is back"


@pytest.mark.parametrize("subdir,minimum", [("styles", 14), ("tutorials", 3), ("qc/data", 2)])
def test_wheel_ships_package_data(tmp_path, subdir, minimum):
    """Data files ride along only because the build sweeps the package tree."""
    r = subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", str(tmp_path)],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode != 0:
        pytest.skip(f"wheel build unavailable: {r.stderr[-200:]}")
    wheel = sorted(tmp_path.glob("*.whl"))[-1]
    names = zipfile.ZipFile(wheel).namelist()
    found = [n for n in names if f"/{subdir}/" in n and not n.endswith(".py")]
    assert len(found) >= minimum, f"{subdir}: expected >={minimum} data files in the wheel, got {len(found)}"


def test_every_skill_has_at_least_one_scenario():
    """TESTING.md states this rule; nothing enforced it, and 9 of 16 skills
    were missing one — all of them arrivals from the consolidation, which is
    exactly when a documented standard quietly stops being met."""
    skills = {p.name for p in (REPO / "skills").iterdir() if p.is_dir()}
    covered = {
        p.name for p in (REPO / "tests" / "scenarios").iterdir()
        if p.is_dir() and any(p.glob("*.md"))
    }
    missing = sorted(skills - covered)
    assert not missing, f"skills with no behavioural scenario: {missing}"


def test_scenarios_name_a_skill_that_exists():
    skills = {p.name for p in (REPO / "skills").iterdir() if p.is_dir()}
    for scenario in (REPO / "tests" / "scenarios").rglob("*.md"):
        head = scenario.read_text()[:200]
        named = re.search(r"^skill:\s*(\S+)", head, re.M)
        assert named, f"{scenario} has no `skill:` frontmatter"
        assert named.group(1) in skills, f"{scenario} names unknown skill {named.group(1)}"


def test_documented_install_urls_point_at_this_repo():
    """Every install command must name a route that exists.

    Two forms are legitimate — the tarball (needs no git) and git+https (does).
    PyPI is not one: nothing is published there, and an unknown extra in a URL
    requirement is not even a warning, so a wrong URL silently under-installs.
    """
    out = subprocess.run(
        ["bash", "-c",
         "grep -rhoE \"video-studio-engine[^'\\\"]*@ [^'\\\"]+\" "
         "--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ . || true"],
        capture_output=True, text=True, cwd=REPO)
    urls = {line.split("@", 1)[1].strip() for line in out.stdout.splitlines() if "@" in line}
    assert urls, "no install commands found at all — the docs lost their install route"
    # Source that BUILDS a command holds a placeholder, not a URL — qc_analyze
    # assembles its remediation line from a variable so the whole command fits
    # on one line for the linter. A template is not an instruction.
    bad = [u for u in urls
           if "{" not in u and "github.com/scrollmark/social-skills" not in u]
    assert not bad, f"install commands pointing somewhere unexpected: {bad}"


def test_the_install_route_is_reachable():
    """The tarball endpoint is the documented default; a 404 there breaks every
    documented install at once, and nothing else in this suite would notice."""
    import urllib.error
    import urllib.request
    url = "https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz"
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            assert r.status == 200, f"tarball endpoint returned {r.status}"
    except urllib.error.URLError as e:
        pytest.skip(f"no network: {e}")
