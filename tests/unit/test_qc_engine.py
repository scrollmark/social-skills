"""The QC engine's own health.

The assertion that matters here is not "detectors produced findings" — it is
that no detector reported a SKIP THAT LOOKS LIKE A USER PROBLEM WHEN IT IS
OURS. `prompt_fit` shipped broken for weeks because it raised
ModuleNotFoundError for a package we failed to vendor, and the engine filed
that as `missing_extra`, which is indistinguishable from "you did not install
the models". The run reported a clean skip and 18/18 detectors "available".

A test that merely imports the detectors, or counts how many ran, passes in
exactly that state. These do not.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("numpy", reason="the [qc] extra is not installed")


def _analyze(video, workdir, **kw):
    from video_studio.qc.engine import AnalyzeOptions, analyze
    return analyze(str(video), AnalyzeOptions(workdir=str(workdir), **kw)).to_json()


@pytest.fixture
def built(project, composer, tmp_path):
    """A project taken through build_props, plus a rendered-ish video file."""
    import os
    import subprocess
    import sys
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")}
    subprocess.run([sys.executable, "-m", "video_studio.cli", "build_props",
                    "--storyboard", str(project / "storyboard.json"),
                    "--project", str(project), "--composer", str(composer),
                    "--placeholders"], check=True, capture_output=True, env=env)
    video = tmp_path / "render.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "testsrc=size=1080x1920:rate=30:duration=3",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
                   check=True, capture_output=True)
    return video, project


def test_no_detector_crashes_or_skips_untagged(require_ffmpeg, built):
    """Every skip must name a real extra. A skip with no extra is our bug.

    This is the exact shape prompt_fit failed in: code=missing_extra with
    extra=None, because the missing module was ours and not a user's.
    """
    from video_studio.qc.engine import KNOWN_DETECTORS
    video, workdir = built
    names = {d.name for d in KNOWN_DETECTORS}
    report = _analyze(video, workdir, detectors=names, taxonomy="2.1")

    crashed = [s for s in report["detectorsSkipped"] if s.get("code") == "crashed"]
    assert not crashed, f"detectors crashed: {[(s['name'], s.get('detail','')[:120]) for s in crashed]}"

    untagged = [s for s in report["detectorsSkipped"]
                if s.get("code") == "missing_extra" and not s.get("extra")]
    assert not untagged, (
        "a detector was filed as 'missing extra' without naming one — that is "
        f"our packaging bug wearing a user's error: {[s['name'] for s in untagged]}"
    )


def test_every_named_extra_actually_exists(require_ffmpeg, repo, built):
    """A skip that names an extra nobody can install is worse than a crash."""
    import tomllib
    declared = set(tomllib.loads((repo / "pyproject.toml").read_text())
                   ["project"]["optional-dependencies"])
    from video_studio.qc.engine import KNOWN_DETECTORS
    video, workdir = built
    report = _analyze(video, workdir, detectors={d.name for d in KNOWN_DETECTORS})
    named = {s["extra"] for s in report["detectorsSkipped"] if s.get("extra")}
    unknown = named - declared
    assert not unknown, f"skips name extras that do not exist in pyproject: {sorted(unknown)}"


def test_prompt_fit_data_is_vendored():
    """The regression that started this file. Reading the data must not raise."""
    from video_studio.qc.detectors.prompt_fit import load_checks, load_taxonomy
    taxonomy = load_taxonomy()
    checks = load_checks()
    assert taxonomy, "taxonomy.csv resolved to nothing"
    assert checks, "checks.yaml resolved to nothing"
    assert "2.1" in taxonomy, f"expected subcategory 2.1, got {sorted(taxonomy)[:5]}"
