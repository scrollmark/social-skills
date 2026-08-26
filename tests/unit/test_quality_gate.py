"""The step-8 gate reports what a reader can actually reach.

The doctor used to probe PATH for `showwatcher`, a tool that was never
published anywhere. The row could therefore only ever read "missing", and its
note pointed at a repo that does not exist — a gap the reader was told about
and could not close, which is the same failure this repo keeps shipping.

Two properties matter and neither is obvious from reading the code:

  * the checks can report False. An always-OK check is indistinguishable from
    no check, and that is how the `showwatcher` row survived so long.
  * `qc_analyze` is judged by RUNNING it, not by `which`. The engine imports
    numpy at module scope, so with the CLI installed but the [qc] extra absent
    it is on PATH and cannot run. `which` says OK in exactly that state.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DOCTORS = sorted(REPO.glob("skills/*/scripts/doctor.py"))


def optional_rows(payload: dict) -> dict[str, bool]:
    return {t["tool"]: t["available"] for t in payload["tools"] if t.get("optional")}


def test_doctors_stay_byte_identical() -> None:
    """Both skills ship the same file; verify-skills.sh enforces it too."""
    assert len(DOCTORS) == 2
    blobs = {d.read_bytes() for d in DOCTORS}
    assert len(blobs) == 1, f"doctor.py copies diverged: {[str(d) for d in DOCTORS]}"


@pytest.mark.parametrize("doctor", DOCTORS, ids=lambda p: p.parent.parent.name)
def test_gate_rows_are_present_and_showwatcher_is_gone(doctor: Path) -> None:
    payload = json.loads(
        subprocess.run([sys.executable, str(doctor), "--json"],
                       capture_output=True, text=True, check=True).stdout
    )
    rows = optional_rows(payload)
    assert set(rows) == {"caption burn-in", "qc_render", "qc_analyze"}
    assert "showwatcher" not in {t["tool"] for t in payload["tools"]}


def test_gate_reports_false_when_nothing_is_reachable(tmp_path: Path) -> None:
    """Isolated from both the sibling skill and the engine CLI, both go False.

    This is the test that would have caught the original bug in reverse: a
    check that cannot fail is not a check.
    """
    scripts = tmp_path / "lonely-skill" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(DOCTORS[0], scripts / "doctor.py")

    # PATH must be an EMPTY directory, not "/usr/bin:/bin". On a Mac those hold
    # no ffmpeg, so the first version of this test passed locally and failed on
    # Ubuntu, where /usr/bin/ffmpeg exists and has libass — making the caption
    # row correctly True and the assertion wrong. Isolation has to be real,
    # not a guess about what a given platform keeps in /usr/bin.
    empty = tmp_path / "empty-path"
    empty.mkdir()
    payload = json.loads(
        subprocess.run(
            [sys.executable, str(scripts / "doctor.py"), "--json"],
            capture_output=True, text=True, check=True,
            env={"PATH": str(empty), "HOME": str(tmp_path)},
        ).stdout
    )
    assert optional_rows(payload) == {
        "caption burn-in": False, "qc_render": False, "qc_analyze": False,
    }


@pytest.mark.parametrize("doctor", DOCTORS, ids=lambda p: p.parent.parent.name)
def test_caption_burn_row_exists(doctor: Path) -> None:
    """A slim ffmpeg passes every presence check and cannot burn a caption.

    Homebrew's mainline `ffmpeg` has no libass. `which ffmpeg` says OK, the
    version string looks healthy, and burn_captions fails. The row has to be
    about the capability, not the binary.
    """
    payload = json.loads(
        subprocess.run([sys.executable, str(doctor), "--json"],
                       capture_output=True, text=True, check=True).stdout
    )
    assert "caption burn-in" in optional_rows(payload)


def test_caption_burn_is_false_without_ffmpeg(tmp_path: Path) -> None:
    scripts = tmp_path / "skill" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(DOCTORS[0], scripts / "doctor.py")
    payload = json.loads(
        subprocess.run(
            [sys.executable, str(scripts / "doctor.py"), "--json"],
            capture_output=True, text=True, check=True,
            env={"PATH": str(tmp_path / "empty"), "HOME": str(tmp_path)},
        ).stdout
    )
    assert optional_rows(payload)["caption burn-in"] is False


def test_caption_burn_matches_the_ffmpeg_actually_on_path() -> None:
    """Agree with ffmpeg itself, whichever build this machine happens to have."""
    if shutil.which("ffmpeg") is None:
        pytest.skip("no ffmpeg on PATH")
    listed = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                            capture_output=True, text=True).stdout
    truth = any(l.split()[1:2] == ["subtitles"] for l in listed.splitlines() if l.strip())

    payload = json.loads(
        subprocess.run([sys.executable, str(DOCTORS[0]), "--json"],
                       capture_output=True, text=True, check=True).stdout
    )
    assert optional_rows(payload)["caption burn-in"] is truth


def test_qc_render_is_found_from_the_skill_that_does_not_bundle_it() -> None:
    """`studio-setup` ships the doctor but not the script; it looks sideways."""
    bundling = [d for d in DOCTORS if (d.parent / "qc_render.py").exists()]
    assert len(bundling) == 1, "expected exactly one skill to bundle qc_render.py"
    other = next(d for d in DOCTORS if d not in bundling)

    payload = json.loads(
        subprocess.run([sys.executable, str(other), "--json"],
                       capture_output=True, text=True, check=True).stdout
    )
    assert optional_rows(payload)["qc_render"] is True


def run_without_numpy(*argv: str) -> subprocess.CompletedProcess[str]:
    """Run qc_analyze with numpy made unimportable, whatever is installed here.

    A meta-path finder raising ModuleNotFoundError is the only way to simulate
    an absent extra reliably — `find_module`/`load_module` were removed in
    3.12, so the hook must implement `find_spec`, and the exception type must
    be ModuleNotFoundError specifically because that is what qc_analyze
    catches.
    """
    script = (
        "import sys\n"
        "class Block:\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name.split('.')[0] == 'numpy':\n"
        "            raise ModuleNotFoundError('numpy blocked for this test', name=name)\n"
        "        return None\n"
        "sys.meta_path.insert(0, Block())\n"
        "from video_studio.qc.qc_analyze import main\n"
        f"sys.argv = ['qc_analyze', {', '.join(repr(a) for a in argv)}]\n"
        "main()\n"
    )
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(REPO / "src")}
    return subprocess.run([sys.executable, "-c", script],
                          capture_output=True, text=True, cwd=REPO, env=env)


def test_qc_analyze_help_survives_a_missing_extra() -> None:
    """--help must work without [qc] — it is how a reader learns what to get."""
    r = run_without_numpy("--help")
    assert r.returncode == 0, f"--help failed without numpy:\n{r.stderr}"
    assert "usage:" in r.stdout


def test_missing_extra_names_the_extra_and_an_installable_url() -> None:
    """The message a reader gets must be actionable, not a traceback."""
    r = run_without_numpy("--list")
    assert r.returncode != 0
    assert "Traceback" not in r.stderr, r.stderr
    assert "[qc]" in r.stderr
    # Not PyPI — the engine is not published there.
    assert "github.com/scrollmark/social-skills" in r.stderr
