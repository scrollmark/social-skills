"""Shared fixtures. Deliberately builds real media with ffmpeg rather than
mocking it: every bug this suite exists to catch was one where the code ran
happily and produced nothing useful, which a mock reproduces perfectly.
"""

from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _have(binary: str) -> bool:
    return shutil.which(binary) is not None


HAVE_FFMPEG = _have("ffmpeg") and _have("ffprobe")


@pytest.fixture
def repo() -> Path:
    return REPO


@pytest.fixture
def require_ffmpeg():
    """Skip a test that needs real media tooling.

    A fixture rather than a module-level marker so tests never import from
    `tests.*` — a `tests` package in site-packages shadows this directory, and
    a suite that fails to collect is a suite nobody runs.
    """
    if not HAVE_FFMPEG:
        pytest.skip("ffmpeg/ffprobe not on PATH")


def write_tone(path: Path, seconds: float, amplitude: float,
               freq: int = 180, rate: int = 24000) -> None:
    """A mono 16-bit WAV. Amplitude near zero stands in for silence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(
            struct.pack("<h", int(amplitude * 32767 * math.sin(2 * math.pi * freq * t / rate)))
            for t in range(int(rate * seconds))
        ))


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A two-scene project: scene `a` is loudly narrated, scene `b` is silent.

    The asymmetry is the point — it is what lets a ducking or sync assertion
    distinguish "ran" from "worked".
    """
    root = tmp_path / "proj"
    (root / "audio").mkdir(parents=True)
    write_tone(root / "audio" / "a.wav", 1.5, 0.80)
    write_tone(root / "audio" / "b.wav", 1.5, 0.0005)
    write_tone(root / "audio" / "bed.wav", 3.5, 0.60, freq=440)
    (root / "storyboard.json").write_text(json.dumps({
        "title": "fixture", "width": 1080, "height": 1920, "fps": 30,
        "music": "audio/bed.wav",
        "scenes": [
            {"id": "a", "narration": "loud",
             "layers": [{"id": "bg", "source": "placeholder:A", "color": "#224466"}]},
            {"id": "b", "narration": "quiet",
             "layers": [{"id": "bg", "source": "placeholder:B", "color": "#664422"}]},
        ],
    }, indent=2))
    return root


@pytest.fixture
def composer(tmp_path: Path) -> Path:
    """An empty composer tree — enough for build_props to write into."""
    c = tmp_path / "composer"
    (c / "src").mkdir(parents=True)
    (c / "props").mkdir()
    (c / "public").mkdir()
    return c


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Invoke a command the way a user does, through the dispatcher."""
    return subprocess.run(
        [sys.executable, "-m", "video_studio.cli", *args],
        capture_output=True, text=True, cwd=str(cwd) if cwd else None,
        env={**__import__("os").environ, "PYTHONPATH": str(SRC)},
    )
