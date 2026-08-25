"""The dispatcher: every registered command must resolve and run.

Cheap, and it catches the two ways this has broken before — a COMMANDS entry
pointing at a module that moved, and a program whose error path crashes the
dispatcher instead of printing its message.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"


def commands() -> dict[str, str]:
    text = (SRC / "video_studio" / "cli.py").read_text()
    block = re.search(r"COMMANDS: dict\[str, str\] = \{(.*?)\n\}", text, re.S).group(1)
    return dict(re.findall(r'^\s+"([a-z_]+)":\s*"([\w.]+)"', block, re.M))


@pytest.mark.parametrize("name,module", sorted(commands().items()))
def test_command_module_exists(name, module):
    assert importlib.util.find_spec(module) is not None, f"{name} -> {module} does not resolve"


def test_string_systemexit_prints_its_message():
    """`raise SystemExit("msg")` is the house style for a fatal error.

    The dispatcher used to coerce the code with int(), which raised ValueError
    and buried the message under a traceback — but only via `video-studio
    <cmd>`, never when the file was run directly, which is why it survived.
    """
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ELEVENLABS_API_KEY", "MINIMAX_API_KEY"):
        env.pop(var, None)
    r = subprocess.run([sys.executable, "-m", "video_studio.cli", "gen_music",
                        "--prompt", "x", "--seconds", "5", "--out", "/tmp/none.mp3"],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 1, f"expected exit 1, got {r.returncode}"
    assert "Traceback" not in r.stderr, f"error path raised instead of reporting:\n{r.stderr[-400:]}"
    assert "provider" in r.stderr.lower()
