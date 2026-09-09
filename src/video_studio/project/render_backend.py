"""Which program turns a storyboard into an mp4 — and how to find it.

There are two, and they are not interchangeable yet:

  editor    the Scrollmark editor's own CLI, `@scrollmark/cli`. It takes the
            storyboard directly: `scrollmark build` translates it into a
            Scrollmark project document (by running the editor's real Command
            objects headlessly — there is no second timeline implementation)
            and `scrollmark render` drives a headless Chrome over it, because
            that export pipeline is WebGPU + OffscreenCanvas + WebCodecs.
            This is the DEFAULT. It needs no licence, and `npx @scrollmark/cli`
            installs it — including a built copy of the editor, so there is
            nothing to clone and no Studio to start first.
  remotion  the composer in `composer/`. `build_props` writes
            `composer/props/<slug>.json`, `preflight` checks it, and
            `npx remotion render` draws it. Kept because it still renders
            things the editor does not: three of the composer's six effects,
            and the per-word caption emphasis behind `highlight`.

The default flipped when `@scrollmark/cli` published. Before that the editor
path could only run from a checkout of a private repository, which is not a
default anyone outside the org could use.

Selection order, most specific first:

  1. an explicit `--backend`
  2. $VIDEO_STUDIO_RENDER_BACKEND
  3. `renderBackend` in <studio root>/.video-studio.json
  4. "editor"

Finding the editor CLI, same shape:

  1. $SCROLLMARK_CLI — a whole command, shell-quoted, so a checkout works:
     SCROLLMARK_CLI='node /path/to/editor/packages/cli/dist/index.js'
  2. `scrollmarkCli` in <studio root>/.video-studio.json
  3. `scrollmark` on PATH
  4. `npx --yes @scrollmark/cli` — the ordinary install, and the one a fresh
     machine takes.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
from pathlib import Path

from video_studio.paths import studio_root

#: Every backend `--backend` accepts. The first is the default.
BACKENDS = ("editor", "remotion")
DEFAULT_BACKEND = BACKENDS[0]

ENV_BACKEND = "VIDEO_STUDIO_RENDER_BACKEND"
ENV_CLI = "SCROLLMARK_CLI"

#: Read from the studio root, next to composer/ and projects/. Optional; a
#: missing or unparseable file is simply no configuration, never an error —
#: this is a lookup, and failing a render over a stray comma would be absurd.
CONFIG_NAME = ".video-studio.json"

#: The npm package the editor CLI will ship as. Not published at time of
#: writing; see the module docstring.
PACKAGE = "@scrollmark/cli"

#: What `scrollmark build` writes and `scrollmark render` reads: the project
#: document, the editor's actual source of truth. Named beside the storyboard
#: rather than inside composer/ — the editor path never touches composer/.
PROJECT_FILE = "cut.project.json"


def read_config(root: Path | None = None) -> dict:
    """`<studio root>/.video-studio.json`, or {} if it is absent or broken."""
    path = (root or studio_root()) / CONFIG_NAME
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def resolve_backend(explicit: str | None = None,
                    env: dict | None = None,
                    config: dict | None = None) -> str:
    """The backend to render with. See the module docstring for the order."""
    env = os.environ if env is None else env
    config = read_config() if config is None else config
    for value in (explicit, env.get(ENV_BACKEND), config.get("renderBackend")):
        if not value:
            continue
        name = str(value).strip().lower()
        if name not in BACKENDS:
            raise SystemExit(
                f"unknown render backend {value!r} — expected one of "
                f"{', '.join(BACKENDS)}"
            )
        return name
    return DEFAULT_BACKEND


def scrollmark_command(env: dict | None = None,
                       config: dict | None = None) -> tuple[list[str], str]:
    """The argv prefix that runs the editor CLI, and where it came from.

    The source is returned rather than logged here because the caller is the
    only thing that knows whether the run failed, and "npx" plus a failure is
    the one combination that needs `cli_unavailable_note()`.
    """
    env = os.environ if env is None else env
    override = (env.get(ENV_CLI) or "").strip()
    if override:
        return shlex.split(override), ENV_CLI
    config = read_config() if config is None else config
    configured = str(config.get("scrollmarkCli") or "").strip()
    if configured:
        return shlex.split(configured), CONFIG_NAME
    if shutil.which("scrollmark"):
        return ["scrollmark"], "PATH"
    return ["npx", "--yes", PACKAGE], "npx"


def cli_unavailable_note() -> str:
    """Why the editor CLI could not be run, in the reader's terms.

    npm's own failure is a registry URL and a status code, which reads as a
    network fault whatever actually went wrong. It is usually one of two much
    duller things: no network, or a machine with no node. Say so, and say the
    two ways to point at a copy that already exists, because someone with a
    checkout has one.
    """
    return (
        f"Could not run {PACKAGE}.\n"
        "\n"
        "It is published, so this is normally a missing node or no network\n"
        "rather than a missing package. If you have a checkout of\n"
        "scrollmark/editor, point at it instead:\n"
        "\n"
        f"    export {ENV_CLI}='node /abs/path/to/editor/packages/control/src/index.mjs'\n"
        "\n"
        f"or put it in <studio root>/{CONFIG_NAME} as\n"
        '    {"scrollmarkCli": "node /abs/path/to/editor/packages/control/src/index.mjs"}\n'
        "\n"
        "The composer still renders, if it is installed: --backend remotion."
    )


def build_argv(prefix: list[str], storyboard: Path, project: Path,
               out: Path) -> list[str]:
    """`scrollmark build` — storyboard in, project document + plan.json out.

    It writes `plan.json` beside the project itself, which is what
    `qc_render.py` reads. That is not a coincidence: the editor path was built
    to land in the same place `build_props` does, so step 8 is unchanged
    whichever backend produced the file.
    """
    return [*prefix, "build",
            "--storyboard", str(storyboard),
            "--project", str(project),
            "--out", str(out)]


def render_argv(prefix: list[str], project_file: Path, out: Path) -> list[str]:
    """`scrollmark render` — project document in, mp4 out."""
    return [*prefix, "render",
            "--project-file", str(project_file),
            "--out", str(out)]
