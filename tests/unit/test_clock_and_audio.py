"""The clock, and the things timed against it.

`references/api-landmines.md` calls clocks "the #1 systemic bug class": a scene
duration taken from a plan instead of a measurement desyncs audio, video and
captions cumulatively. build_props therefore snaps the RUNNING TOTAL rather
than each scene, and the composer lays sequences end to end with the same
arithmetic. If those two ever disagree, nothing errors — the video just drifts.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"


def build(project: Path, composer: Path, *extra: str):
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    r = subprocess.run([sys.executable, "-m", "video_studio.cli", "build_props",
                        "--storyboard", str(project / "storyboard.json"),
                        "--project", str(project), "--composer", str(composer),
                        "--placeholders", *extra],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr[-500:]
    return json.loads((composer / "props" / f"{project.name}.json").read_text())


def test_scene_durations_come_from_measured_audio(require_ffmpeg, project, composer):
    """Both fixture scenes are 1.5s of real WAV; the plan says nothing."""
    props = build(project, composer)
    fps = props["fps"]
    for scene in props["scenes"]:
        seconds = scene["durationInFrames"] / fps
        assert abs(seconds - 1.5) < 0.06, f"{scene['id']} is {seconds:.3f}s, expected ~1.5s"


def test_frame_boundaries_do_not_accumulate_error(require_ffmpeg, project, composer):
    """The invariant that survives long timelines.

    Rounding each scene independently lets error compound; snapping the running
    total keeps every cut on the nearest frame to its true time. Asserted as:
    the summed frames equal the frame-snapped total, exactly.
    """
    props = build(project, composer)
    fps = props["fps"]
    total_frames = sum(s["durationInFrames"] for s in props["scenes"])
    plan = json.loads((project / "plan.json").read_text())
    assert abs(total_frames / fps - plan["totalDuration"]) < 1e-6, (
        "props and plan.json disagree about total duration")


def test_plan_json_is_written_for_the_quality_gate(require_ffmpeg, project, composer):
    build(project, composer)
    plan = json.loads((project / "plan.json").read_text())
    assert plan["scenes"] and "duration" in plan["scenes"][0]


def test_duck_music_envelope_dips_under_speech_and_recovers(require_ffmpeg, project, composer):
    """The fixture's scene `a` is loud and `b` is near-silent, so a working
    envelope must be measurably lower under `a`. A flat envelope means the
    measurement ran and decided nothing."""
    props = build(project, composer)
    env_ = {**os.environ, "PYTHONPATH": str(SRC)}
    r = subprocess.run([sys.executable, "-m", "video_studio.cli", "duck_music",
                        "--project", str(project), "--composer", str(composer)],
                       capture_output=True, text=True, env=env_)
    assert r.returncode == 0, r.stderr[-400:]

    props = json.loads((composer / "props" / f"{project.name}.json").read_text())
    envelope = props["music"]["envelope"]
    assert len(envelope) == sum(s["durationInFrames"] for s in props["scenes"])

    half = len(envelope) // 2
    loud, quiet = envelope[:half], envelope[half:]
    assert min(loud) < min(quiet), "the bed does not dip further under the loud scene"
    assert max(quiet) > min(loud) * 1.5, "the bed never recovers in the silent scene"


def test_composer_reads_the_envelope_key_duck_music_writes(repo):
    """The contract between the two halves, with no schema to enforce it.

    duck_music wrote `music.envelope` for weeks while the composer read only
    `music.volume`, so every render played the bed flat and the tool reported
    success. Nothing failed; there was nothing to fail.
    """
    video_tsx = repo / "composer" / "src" / "Video.tsx"
    if not video_tsx.exists():
        pytest.skip("composer not present")
    source = video_tsx.read_text()
    assert "envelope" in source, (
        "the composer does not mention `envelope` — duck_music's output is inert")
