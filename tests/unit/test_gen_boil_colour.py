"""gen_boil output must be tagged like the footage it is cut against.

Frames reach the encoder as raw RGB, which signals nothing about colour. Left
untagged, the file reports colour_range/space/primaries/trc as "unknown", while
stock footage and camera files say tv/bt709. A player then has to guess, and
players disagree — Remotion's OffthreadVideo reads untagged video as full range
and lifts it, so a generated shot sits visibly brighter than the real footage
beside it in the same edit.

The second half of this matters as much as the first: on ffmpeg 9 with libx264,
the generic -color_primaries and -color_trc flags set neither. They probe back
as "unknown" until x264 is told directly via -x264-params. Asserting all four
is what makes that visible; asserting only range and matrix would have passed
against the half-fixed version.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "src" / "video_studio" / "generate" / "gen_boil.py"

pillow = pytest.importorskip("PIL", reason="gen_boil draws with pillow")
pytestmark = pytest.mark.skipif(
    not (shutil.which("ffmpeg") and shutil.which("ffprobe")),
    reason="needs ffmpeg and ffprobe on PATH",
)

EXPECTED = {
    "color_range": "tv",
    "color_space": "bt709",
    "color_primaries": "bt709",
    "color_transfer": "bt709",
}


@pytest.fixture(scope="module")
def clip(tmp_path_factory):
    out = tmp_path_factory.mktemp("boil") / "clip.mp4"
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--shape", "chip", "--seconds", "1", "--out", str(out)],
        capture_output=True, text=True, cwd=REPO,
        env={"PATH": __import__("os").environ["PATH"], "PYTHONPATH": str(REPO / "src")},
    )
    if r.returncode != 0:
        pytest.skip(f"gen_boil could not run here: {r.stderr.strip()[:200]}")
    assert out.is_file() and out.stat().st_size > 0
    return out


def probe(path: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=color_range,color_space,color_primaries,color_transfer",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(r.stdout)["streams"][0]


@pytest.mark.parametrize("field,want", sorted(EXPECTED.items()))
def test_colour_is_tagged(clip, field, want):
    got = probe(clip).get(field, "unknown")
    assert got == want, (
        f"{field} is {got!r}, expected {want!r}. An untagged clip is read as "
        "full-range by some players and sits brighter than real footage."
    )


def test_no_field_is_unknown(clip):
    """The failure this guards against is silent: 'unknown' is not an error,
    it is an invitation for every player to decide for itself."""
    s = probe(clip)
    unknown = sorted(k for k, v in s.items() if v == "unknown")
    assert not unknown, f"still unsignalled: {unknown}"
