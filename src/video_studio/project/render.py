# /// script
# requires-python = ">=3.11"
# ///
"""Render a built project, through whichever backend is selected.

Usage:
  video-studio render --project projects/brand-origin-brick
  video-studio render --project projects/brand-origin-brick --backend editor
  video-studio render --project projects/brand-origin-brick --backend editor --dry-run
  video-studio render --project <dir> --out /tmp/cut.mp4

Two backends, and `remotion` is the default. `--backend`, then
$VIDEO_STUDIO_RENDER_BACKEND, then `renderBackend` in the studio root's
`.video-studio.json` — see `render_backend.py` for the whole order.

  remotion  what step 7 has always run, now with one command instead of a
            remembered `cd`. Props must already be built: this does NOT run
            build_props or preflight, because the sequencing rule is that you
            run them yourself, immediately before, and read what they say.
            Refuses rather than renders when the props file is missing.

  editor    `scrollmark build` + `scrollmark render` from `@scrollmark/cli`.
            The build translates the storyboard into a Scrollmark project
            document and writes `plan.json` beside it — the same plan.json
            step 8's `qc_render.py` already reads — and the render drives a
            headless Chrome over that document. No composer, no props file, no
            preflight (the document is the check).

            **`@scrollmark/cli` is not published to npm yet.** Point
            $SCROLLMARK_CLI at a checkout of scrollmark/editor, or this command
            fails and says exactly that. It is not the default for that reason,
            and it also needs a running `scrollmark studio` to attach to
            (--url/--token, or MCP_URL and MCP_TOKEN) and a Chrome (CHROME_PATH).

`--dry-run` prints the commands and runs nothing, which is the honest way to
see what a backend would do on a machine that cannot yet do it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from video_studio.paths import studio_root
from video_studio.project import render_backend as rb


def slugify(project: Path) -> str:
    """Stable id for a project: its directory name.

    Identical to build_props.slugify and studio.slugify, and for the same
    reason — it names the props file, the registered composition, and the URL.
    The composition id is what `remotion render` is given here; if these drift
    the render either fails or, worse, renders somebody else's video.
    """
    return project.resolve().name


def remotion_argv(composition: str, out: Path) -> list[str]:
    """`npx remotion render <composition> <out>`, run in the composer.

    The composition id is positional and load-bearing. Omitting it renders
    whichever composition the generated registry lists first — alphabetical,
    so the same wrong project every time. The entry point comes from
    `composer/remotion.config.ts`, so it is not repeated here.
    """
    return ["npx", "remotion", "render", composition, str(out)]


def plan(project: Path, backend: str, out: Path, composer: Path) -> list[dict]:
    """The commands a run would issue, in order, with the cwd for each."""
    if backend == "remotion":
        return [{
            "cwd": str(composer),
            "argv": remotion_argv(slugify(project), out),
        }]
    prefix, source = rb.scrollmark_command()
    project_file = project / rb.PROJECT_FILE
    return [
        {"cwd": None, "source": source,
         "argv": rb.build_argv(prefix, project / "storyboard.json", project,
                               project_file)},
        {"cwd": None, "source": source,
         "argv": rb.render_argv(prefix, project_file, out)},
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="project dir")
    ap.add_argument("--backend", choices=rb.BACKENDS,
                    help=f"default {rb.DEFAULT_BACKEND}; see {rb.ENV_BACKEND}")
    ap.add_argument("--out", help="output file (default <project>/cut.mp4)")
    ap.add_argument("--composer", default=str(studio_root() / "composer"),
                    help="remotion backend only")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the commands and run nothing")
    args = ap.parse_args()

    backend = rb.resolve_backend(args.backend)
    project = Path(args.project)
    if not (project / "storyboard.json").exists():
        raise SystemExit(f"no storyboard.json in {project}")
    out = Path(args.out).expanduser() if args.out else project / "cut.mp4"
    composer = Path(args.composer)

    if backend == "remotion":
        props = composer / "props" / f"{slugify(project)}.json"
        if not props.exists() and not args.dry_run:
            raise SystemExit(
                f"no props at {props} — run `video-studio build_props --storyboard "
                f"{project}/storyboard.json --project {project}` and then "
                f"`video-studio preflight --project {slugify(project)}` first."
            )

    steps = plan(project, backend, out.resolve(), composer)

    if args.dry_run:
        print(json.dumps({"backend": backend, "out": str(out),
                          "steps": [{k: v for k, v in s.items() if v is not None}
                                    for s in steps]}, indent=2))
        return

    for step in steps:
        r = subprocess.run(step["argv"], cwd=step["cwd"])
        if r.returncode != 0:
            # An npx invocation that failed is overwhelmingly likely to have
            # failed because the package does not exist yet, and npm reports
            # that as a 404 against a registry URL — which reads as a network
            # fault. Say what it actually is.
            if step.get("source") == "npx":
                print("\n" + rb.not_published_note(), file=sys.stderr)
            raise SystemExit(
                f"{backend} backend failed ({' '.join(step['argv'][:3])}, "
                f"exit {r.returncode})"
            )

    print(json.dumps({"backend": backend, "out": str(out),
                      "exists": out.exists()}, indent=2))


if __name__ == "__main__":
    main()
