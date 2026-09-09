"""Two render backends, one default, and a command that does not exist yet.

Every assertion here is about a decision made BEFORE anything renders, which
is deliberate: a render needs a browser or a Remotion install and neither
belongs in a unit suite. What can go wrong without either is the part that has
gone wrong before — a backend silently defaulting to the wrong one, and a
missing program reported as somebody else's error.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from video_studio.project import render as render_mod
from video_studio.project import render_backend as rb

from conftest import run_cli


# --- selection ---------------------------------------------------------

def test_remotion_is_the_default():
    """It stays the default until @scrollmark/cli is published. A default that
    points at an unpublished package turns every fresh machine into a support
    ticket."""
    assert rb.resolve_backend(None, env={}, config={}) == "remotion"
    assert rb.DEFAULT_BACKEND == "remotion"


def test_env_var_selects_a_backend():
    assert rb.resolve_backend(None, env={rb.ENV_BACKEND: "editor"}, config={}) == "editor"


def test_config_selects_a_backend():
    assert rb.resolve_backend(None, env={}, config={"renderBackend": "editor"}) == "editor"


def test_the_flag_beats_the_env_which_beats_the_config():
    assert rb.resolve_backend("remotion",
                              env={rb.ENV_BACKEND: "editor"},
                              config={"renderBackend": "editor"}) == "remotion"
    assert rb.resolve_backend(None,
                              env={rb.ENV_BACKEND: "remotion"},
                              config={"renderBackend": "editor"}) == "remotion"


def test_an_unknown_backend_names_the_ones_that_exist():
    with pytest.raises(SystemExit) as e:
        rb.resolve_backend("scrollmark", env={}, config={})
    assert "remotion" in str(e.value) and "editor" in str(e.value)


def test_a_broken_config_is_no_config_rather_than_a_crash(tmp_path: Path):
    """This is a lookup on the way to a render. Failing it over a stray comma
    would strand a user with a valid storyboard and a syntax error."""
    (tmp_path / rb.CONFIG_NAME).write_text("{not json,}")
    assert rb.read_config(tmp_path) == {}
    (tmp_path / rb.CONFIG_NAME).write_text('["a list, not an object"]')
    assert rb.read_config(tmp_path) == {}
    assert rb.read_config(tmp_path / "nowhere") == {}


# --- finding the CLI ---------------------------------------------------

def test_the_env_var_is_a_whole_command_not_a_path():
    """A checkout is run as `node <file>`, so the override has to be able to
    carry an interpreter. shlex, not a bare path."""
    argv, source = rb.scrollmark_command(
        env={rb.ENV_CLI: "node /opt/editor/packages/control/src/index.mjs"}, config={})
    assert argv == ["node", "/opt/editor/packages/control/src/index.mjs"]
    assert source == rb.ENV_CLI


def test_config_is_consulted_when_the_env_var_is_not_set():
    argv, source = rb.scrollmark_command(
        env={}, config={"scrollmarkCli": "node /opt/x/index.mjs"})
    assert argv == ["node", "/opt/x/index.mjs"]
    assert source == rb.CONFIG_NAME


def test_it_falls_through_to_npx(monkeypatch):
    """The eventual install. Today it 404s, which is what the note is for."""
    monkeypatch.setattr(rb.shutil, "which", lambda _: None)
    argv, source = rb.scrollmark_command(env={}, config={})
    assert argv == ["npx", "--yes", "@scrollmark/cli"]
    assert source == "npx"


def test_the_failure_note_says_the_package_is_not_published(monkeypatch):
    note = rb.not_published_note()
    assert "NOT PUBLISHED" in note
    assert "scrollmark/editor" in note, "the note must say where to get it instead"
    assert rb.ENV_CLI in note, "the note must name the override that fixes it"


# --- the command lines -------------------------------------------------

def test_editor_build_and_render_command_lines():
    prefix = ["scrollmark"]
    project = Path("/w/projects/brick")
    assert rb.build_argv(prefix, project / "storyboard.json", project,
                         project / rb.PROJECT_FILE) == [
        "scrollmark", "build",
        "--storyboard", "/w/projects/brick/storyboard.json",
        "--project", "/w/projects/brick",
        "--out", "/w/projects/brick/cut.project.json",
    ]
    assert rb.render_argv(prefix, project / rb.PROJECT_FILE,
                          project / "cut.mp4") == [
        "scrollmark", "render",
        "--project-file", "/w/projects/brick/cut.project.json",
        "--out", "/w/projects/brick/cut.mp4",
    ]


def test_remotion_command_line_names_the_composition():
    """Omitting it renders whichever composition the generated registry lists
    first — alphabetical, so the same wrong project every time."""
    argv = render_mod.remotion_argv("brick", Path("/w/projects/brick/cut.mp4"))
    assert argv == ["npx", "remotion", "render", "brick",
                    "/w/projects/brick/cut.mp4"]


# --- end to end, without rendering -------------------------------------

def test_dry_run_editor_prints_both_commands(project: Path, monkeypatch):
    monkeypatch.setenv(rb.ENV_CLI, "node /opt/editor/packages/control/src/index.mjs")
    r = run_cli("render", "--project", str(project), "--backend", "editor", "--dry-run")
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["backend"] == "editor"
    assert [s["argv"][2] for s in out["steps"]] == ["build", "render"]
    assert out["steps"][0]["argv"][:2] == ["node", "/opt/editor/packages/control/src/index.mjs"]
    assert out["steps"][0]["argv"][-1].endswith("/cut.project.json")
    assert out["steps"][1]["argv"][-1].endswith("/cut.mp4")
    # The build reads the storyboard, not a props file: the editor path never
    # touches composer/.
    assert "composer" not in json.dumps(out)


def test_dry_run_defaults_to_remotion(project: Path, monkeypatch):
    monkeypatch.delenv(rb.ENV_BACKEND, raising=False)
    r = run_cli("render", "--project", str(project), "--dry-run")
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["backend"] == "remotion"
    assert out["steps"][0]["argv"][:3] == ["npx", "remotion", "render"]
    assert out["steps"][0]["argv"][3] == project.name, "composition id is the slug"


def test_env_var_switches_the_backend_end_to_end(project: Path, monkeypatch):
    monkeypatch.setenv(rb.ENV_BACKEND, "editor")
    monkeypatch.setenv(rb.ENV_CLI, "scrollmark")
    r = run_cli("render", "--project", str(project), "--dry-run")
    assert json.loads(r.stdout)["backend"] == "editor"


def test_remotion_refuses_when_props_were_never_built(project: Path, tmp_path: Path,
                                                      monkeypatch):
    """`render` does not run build_props for you — the sequencing rule is that
    you run it yourself, immediately before, and read what it says. Refusing is
    the only other honest option; rendering last week's props is not."""
    monkeypatch.delenv(rb.ENV_BACKEND, raising=False)
    r = run_cli("render", "--project", str(project),
                "--composer", str(tmp_path / "empty-composer"))
    assert r.returncode == 1
    assert "build_props" in r.stderr and "preflight" in r.stderr


def test_a_project_without_a_storyboard_is_refused(tmp_path: Path):
    r = run_cli("render", "--project", str(tmp_path), "--dry-run")
    assert r.returncode == 1
    assert "storyboard.json" in r.stderr


# --- one storyboard, two backends, the same meaning ---------------------

def test_layer_keys_the_editor_honours_survive_build_props(require_ffmpeg,
                                                           project: Path,
                                                           composer: Path):
    """`muted`, `loop` and `label` are honoured by the editor backend AND by
    the composer's Layer type — and `build_props` dropped all three on the way
    between them, silently, because a key not in LAYER_KEYS is not copied and
    nothing looks for it afterwards. A storyboard saying "keep this clip's own
    audio" therefore meant two different videos depending on the backend.
    """
    sb_path = project / "storyboard.json"
    sb = json.loads(sb_path.read_text())
    sb["scenes"][0]["layers"][0].update({"muted": False, "loop": False,
                                         "label": "HOST"})
    sb_path.write_text(json.dumps(sb, indent=2))

    r = run_cli("build_props", "--storyboard", str(sb_path),
                "--project", str(project), "--composer", str(composer),
                "--placeholders")
    assert r.returncode == 0, r.stderr[-500:]
    layer = json.loads(
        (composer / "props" / f"{project.name}.json").read_text()
    )["scenes"][0]["layers"][0]
    assert layer["muted"] is False
    assert layer["loop"] is False
    assert layer["label"] == "HOST", "an explicit label must beat the derived one"


def test_the_composer_reads_the_keys_build_props_now_passes(repo: Path):
    """The other half of the contract, and the reason the pass-through is a
    fix rather than a new feature: the composer already honoured these."""
    video_tsx = repo / "composer" / "src" / "Video.tsx"
    if not video_tsx.exists():
        pytest.skip("composer not present")
    source = video_tsx.read_text()
    for key in ("muted", "loop", "label"):
        assert f"layer.{key}" in source, f"the composer never reads layer.{key}"


def test_both_builds_look_for_the_same_media_extensions(repo: Path):
    """A clip one build resolves and the other placeholders, from one
    storyboard, is the worst kind of backend difference: it looks like footage
    went missing rather than like a list drifted."""
    source = (repo / "src" / "video_studio" / "project" / "build_props.py").read_text()
    for ext in (".mp4", ".webm", ".mov", ".png", ".jpg", ".jpeg", ".webp"):
        assert f'"{ext}"' in source, f"{ext} is not probed under clips/"
