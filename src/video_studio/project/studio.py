# /// script
# requires-python = ">=3.11"
# ///
"""Open the editor on a free port, without stepping on another agent.

Usage:
  uv run scripts/studio.py --project projects/brand-origin-brick
  uv run scripts/studio.py --status          # who is editing what, right now
  uv run scripts/studio.py --release         # drop a stale claim

Why this exists: the editor defaults to port 3000 and the composition reads a
single global `props.json`. Two agents starting it therefore do not get two
editors — the second attaches to the FIRST one's session and shows the first
one's video. Observed live: a studio 30 minutes into someone else's work
answered a second agent's request and opened their browser onto it.

Two separate hazards, and only one of them is the port:

  the port     solved here. A free port is picked per instance, so N agents get
               N editors instead of N views of one editor.
  the props    solved in build_props.py + Root.tsx. Each project owns
               `composer/props/<name>.json` and registers its OWN composition,
               so two agents open two editors on two projects and neither can
               repoint the other. This replaced a build-time
               `import defaultProps from "../props.json"`, where whoever wrote
               that one file last defined what every open editor showed.

The claim file is now only a courtesy record of who is on which port, so
--status can answer "who is editing what". It no longer refuses anything,
because there is no longer anything to contend over.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

from video_studio.paths import studio_root

SKILL_ROOT = studio_root()
COMPOSER = SKILL_ROOT / "composer"
CLAIM = COMPOSER / ".studio-claim.json"


def slugify(project: Path) -> str:
    """Stable id for a project: its directory name.

    Must stay identical to build_props.slugify — that function names the props
    file and the registered composition, and this one names the URL that opens
    it. If they drift, this script hands back a link to a composition that does
    not exist.
    """
    return project.resolve().name


def free_port(start: int = 3000, tries: int = 40) -> int:
    """First port nothing is listening on, from 3000 up.

    Binding to port 0 would also give a free port, but a predictable low number
    is easier for a human to recognise as "my editor" among several.
    """
    for port in range(start, start + tries):
        # CONNECT, do not bind. A bind probe with SO_REUSEADDR happily succeeds
        # on 127.0.0.1:P while another process holds 0.0.0.0:P — this function
        # originally did exactly that and cheerfully handed back the port a live
        # studio was already serving, which is the whole bug it exists to avoid.
        # If a connection is accepted, something is listening. That is the fact.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.25)
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise SystemExit(f"no free port in {start}-{start + tries}")


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    return True


def read_claims() -> list[dict]:
    """Every studio currently believed to be running, dead ones dropped.

    This is a LIST, one entry per agent, because the file used to hold a single
    claim object: a second agent starting up overwrote the first agent's record
    and the first studio vanished from `--status` while still serving. With
    three agents the file could only ever describe the most recent one.

    Liveness is checked on read rather than on exit, because the case that
    matters is a studio that was killed or crashed — it never gets to clean up
    after itself. Without this, one crash leaves a claim nobody can explain.
    """
    if not CLAIM.exists():
        return []
    try:
        data = json.loads(CLAIM.read_text())
    except json.JSONDecodeError:
        return []
    # Tolerate the old single-object format so an in-flight upgrade does not
    # discard a running agent's claim.
    claims = data if isinstance(data, list) else [data]
    return [c for c in claims if isinstance(c, dict) and alive(int(c.get("pid", -1)))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", help="project dir to open")
    ap.add_argument("--status", action="store_true", help="report every running studio and exit")
    ap.add_argument("--release", action="store_true",
                    help="drop this agent's claim; with --port, drop that one, else only dead ones")
    ap.add_argument("--port", type=int, help="force a port instead of picking a free one")
    args = ap.parse_args()

    claims = read_claims()

    if args.release:
        # Never blow away the whole file. Another agent's studio may be live in
        # it, and deleting their claim does not stop their server — it just
        # loses the only record of which port it is on.
        if args.port:
            kept = [c for c in claims if c.get("port") != args.port]
            dropped = len(claims) - len(kept)
        else:
            kept, dropped = claims, 0  # read_claims already pruned the dead
        CLAIM.write_text(json.dumps(kept, indent=2))
        print(json.dumps({"released": dropped or "dead claims only", "stillRunning": kept}, indent=2))
        return

    if args.status:
        print(json.dumps({"running": claims} if claims else
                         {"running": [], "note": "nobody is editing"}, indent=2))
        return

    if not args.project:
        raise SystemExit("--project is required")
    project = Path(args.project)
    if not (project / "storyboard.json").exists():
        raise SystemExit(f"no storyboard.json in {project}")

    # Rebuild THIS project's props before opening, or the editor shows whichever
    # project was built last — the same global-file trap the exporter hit.
    # Invoke the installed module, not a path. This used to run
    # `uv run $SKILL_ROOT/scripts/build_props.py`, which is where the script sat
    # BEFORE the engine was packaged — a path that exists in the old studio tree
    # and in no pip install, so opening the editor failed for every installed
    # copy. sys.executable keeps it in the interpreter already running.
    r = subprocess.run(
        [sys.executable, "-m", "video_studio.cli", "build_props",
         "--storyboard", str(project / "storyboard.json"), "--project", str(project),
         "--placeholders"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise SystemExit(f"could not build {project.name}:\n{r.stderr.strip()[-400:]}")

    port = args.port or free_port()
    proc = subprocess.Popen(
        ["npx", "remotion", "studio", "--port", str(port)],
        cwd=str(COMPOSER), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # Append, do not replace: every live agent stays in the record.
    mine = {"pid": proc.pid, "port": port, "project": str(project),
            "composition": slugify(project)}
    others = [c for c in claims if c.get("port") != port]
    CLAIM.write_text(json.dumps(others + [mine], indent=2))
    # The composition MUST be in the URL. Bare http://localhost:<port> opens
    # whichever composition the generated registry lists first — which is
    # alphabetical, so every project sorting after it opens on somebody else's
    # video. This script always knew the right composition and reported it in a
    # separate field while handing back a URL that ignored it, so the editor
    # reliably opened on the wrong project and looked like a caching bug.
    composition = slugify(project)
    print(json.dumps({
        "url": f"http://localhost:{port}/{composition}",
        "port": port, "pid": proc.pid, "project": str(project),
        "composition": composition,
        "note": f"run --release --port {port} after closing it",
        # All of them, not just the first. Reporting one other agent while three
        # are running is how a port gets treated as free when it is not.
        **({"alsoOpen": others} if others else {}),
    }, indent=2))


if __name__ == "__main__":
    main()
