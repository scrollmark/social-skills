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

import video_studio.cli as cli

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


def test_main_defaults_virtual_env_to_sys_prefix(monkeypatch):
    """`uv tool install` — the README's documented route for this package —
    runs the installed `video-studio` console-script directly against its own
    venv's python, and that entry path never sets VIRTUAL_ENV (unlike `uv
    run`, which does). tts_kokoro's first-run spaCy model bootstrap shells out
    to `uv pip install`, and that subprocess reads VIRTUAL_ENV to know which
    environment to target; without it, uv refuses with "No virtual
    environment found ... pass --system" even though we are demonstrably
    running inside one. Reproduced by hand on a machine that had never
    synthesized narration before: installing the audio extra via uv's tool
    route, then running tts_kokoro, failed with exactly that error; unsetting
    VIRTUAL_ENV before calling `main()` reproduces it here.
    """
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    assert cli.main(["help"]) == 0
    assert os.environ["VIRTUAL_ENV"] == sys.prefix


def test_main_does_not_override_an_existing_virtual_env(monkeypatch):
    """`uv run` already sets VIRTUAL_ENV to its own ephemeral env; the
    dispatcher must not clobber that with sys.prefix of whatever interpreter
    happens to be running it.
    """
    monkeypatch.setenv("VIRTUAL_ENV", "/some/other/venv")
    assert cli.main(["help"]) == 0
    assert os.environ["VIRTUAL_ENV"] == "/some/other/venv"
