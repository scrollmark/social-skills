"""Which program turns a storyboard into an mp4 — and how to find it.

There are two, and they are not interchangeable yet:

  remotion  the composer in `composer/`. `build_props` writes
            `composer/props/<slug>.json`, `preflight` checks it, and
            `npx remotion render` draws it. This is the DEFAULT and the only
            backend that installs today.
  editor    the Scrollmark editor's own CLI, `@scrollmark/cli`. It takes the
            storyboard directly: `scrollmark build` translates it into a
            Scrollmark project document (by running the editor's real Command
            objects headlessly — there is no second timeline implementation)
            and `scrollmark render` drives a headless Chrome over it, because
            that export pipeline is WebGPU + OffscreenCanvas + WebCodecs.

The editor path is proven — four videos were rendered from raw footage through
it — and it is **not published to npm yet**. That is the whole reason remotion
stays the default and this module goes out of its way to say so when the
command cannot be found. A backend that silently is not there is worse than no
backend, and `npx` failing on a missing package prints npm's error, not ours.

Selection order, most specific first:

  1. an explicit `--backend`
  2. $VIDEO_STUDIO_RENDER_BACKEND
  3. `renderBackend` in <studio root>/.video-studio.json
  4. "remotion"

Finding the editor CLI, same shape:

  1. $SCROLLMARK_CLI — a whole command, shell-quoted, so a checkout works:
     SCROLLMARK_CLI='node /path/to/editor/packages/cli/dist/index.js'
  2. `scrollmarkCli` in <studio root>/.video-studio.json
  3. `scrollmark` on PATH
  4. `npx --yes @scrollmark/cli` — the eventual install, and today the one
     that fails. `not_published_note()` is what to print when it does.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
from pathlib import Path

from video_studio.paths import studio_root

#: Every backend `--backend` accepts. The first is the default.
BACKENDS = ("remotion", "editor")
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
    the one combination that needs `not_published_note()`.
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


def not_published_note() -> str:
    """Why `npx @scrollmark/cli` just failed, in the reader's terms.

    npm's own error for a package that does not exist is a 404 against a
    registry URL, which reads as a network problem. It is not one: the package
    has never been published. Say that, and say the two ways to get the command
    anyway, because both exist today.
    """
    return (
        f"{PACKAGE} is NOT PUBLISHED to npm yet — that 404 is not a network\n"
        "fault, there is nothing at that name to install. The editor render\n"
        "backend works, but only from a checkout of scrollmark/editor:\n"
        "\n"
        "    git clone https://github.com/scrollmark/editor\n"
        "    cd editor && bun install\n"
        f"    export {ENV_CLI}='node /abs/path/to/editor/packages/control/src/index.mjs'\n"
        "\n"
        f"Or put it in <studio root>/{CONFIG_NAME} as\n"
        '    {"scrollmarkCli": "node /abs/path/to/editor/packages/control/src/index.mjs"}\n'
        "\n"
        "There is no build step — the CLI is plain .mjs — but `scrollmark build`\n"
        "imports @scrollmark/editor, which is what the install provides.\n"
        "\n"
        f"Until then the default backend is {DEFAULT_BACKEND!r}: drop --backend, or\n"
        f"unset {ENV_BACKEND}."
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
