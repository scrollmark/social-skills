# /// script
# requires-python = ">=3.11"
# ///
"""Serve a tutorial one step at a time, so it can be taught in conversation.

Usage:
  video-studio tutor --list
  video-studio tutor --show getting-started        # the whole thing, for you
  video-studio tutor --step getting-started 1      # ONE beat, for the user
  video-studio tutor --step getting-started next --after 3

The one-step-at-a-time interface is the entire point, and it is a guard rail
rather than a convenience.

A tutorial that arrives as one long message is not a tutorial, it is a document
that happened to be pasted into a chat. Nobody reads the middle of it, nobody
does the exercises, and the agent has no idea which parts landed. Serving one
step forces the shape that actually teaches: say one thing, let them try it,
ask whether it worked, then move.

So `--show` prints everything and is FOR THE AGENT — to plan with, never to
paste. `--step` is what the user should ever see the output of.

Steps carry two optional markers, both parsed out for the agent:

  TRY:   something the user should actually run or say. A tutorial with no
         TRY is a lecture.
  CHECK: the question to ask before moving on. If the answer is wrong or
         absent, re-teach that step — do not advance.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from video_studio.paths import studio_root

SKILL_ROOT = studio_root()
USER_TUTORIALS = Path.home() / ".config" / "video-studio" / "tutorials"


#: Tutorials shipped inside the installed package. Lowest precedence, so a user
#: or a project can shadow one by name.
PACKAGE_TUTORIALS = Path(__file__).resolve().parent.parent / "tutorials"


def roots() -> list[Path]:
    out = []
    if os.environ.get("VIDEO_STUDIO_TUTORIALS"):
        out.append(Path(os.environ["VIDEO_STUDIO_TUTORIALS"]))
    out += [USER_TUTORIALS, SKILL_ROOT / "tutorials"]
    # SKILL_ROOT is the studio tree, which an installed copy does not have: with
    # no marker directory to find, studio_root() falls back to the cwd, so the
    # tier above means <wherever you are standing>/tutorials. That is why
    # `tutor --list` printed "no tutorials found" and exited 0 for everyone who
    # pip installed — the same trap styles.py had, and the same fix.
    out.append(PACKAGE_TUTORIALS)
    return out


def parse(path: Path) -> dict:
    text = path.read_text()
    meta = {"name": path.stem, "description": "", "minutes": "?"}
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    body = text[fm.end():] if fm else text
    if fm:
        for line in fm.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()

    steps = []
    for m in re.finditer(r"^## Step (\d+)\s*[—-]\s*(.+?)\n(.*?)(?=^## Step |\Z)",
                         body, re.S | re.M):
        raw = m.group(3).strip()
        try_m = re.search(r"^TRY:\s*(.+?)$", raw, re.M)
        check_m = re.search(r"^CHECK:\s*(.+?)$", raw, re.M)
        prose = re.sub(r"^(TRY|CHECK):.*$", "", raw, flags=re.M).strip()
        steps.append({"n": int(m.group(1)), "title": m.group(2).strip(),
                      "prose": prose,
                      "try": try_m.group(1).strip() if try_m else None,
                      "check": check_m.group(1).strip() if check_m else None})
    return {**meta, "path": str(path), "steps": steps}


def find_all() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for root in roots():
        if root.is_dir():
            for p in sorted(root.glob("*.md")):
                out.setdefault(p.stem, parse(p))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--show", metavar="NAME")
    ap.add_argument("--step", nargs=2, metavar=("NAME", "N"),
                    help="N is a number or 'next' (with --after)")
    ap.add_argument("--after", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    tutorials = find_all()

    if args.list:
        rows = [{"name": t["name"], "description": t["description"],
                 "minutes": t["minutes"], "steps": len(t["steps"])}
                for t in tutorials.values()]
        print(json.dumps(rows, indent=2) if args.json else
              "\n".join(f"{r['name']:<18} {r['steps']:>2} steps  ~{r['minutes']}m  "
                        f"{r['description']}" for r in rows)
              or "no tutorials found")
        return

    if args.show:
        t = tutorials.get(args.show)
        if not t:
            raise SystemExit(f"no tutorial {args.show!r}. --list to see them.")
        print(json.dumps(t, indent=2))
        return

    if args.step:
        name, which = args.step
        t = tutorials.get(name)
        if not t:
            raise SystemExit(f"no tutorial {name!r}. --list to see them.")
        n = args.after + 1 if which == "next" else int(which)
        step = next((s for s in t["steps"] if s["n"] == n), None)
        if step is None:
            print(json.dumps({"done": True, "tutorial": name,
                              "note": f"{len(t['steps'])} steps, all delivered"}, indent=2))
            return
        print(json.dumps({**step, "of": len(t["steps"]), "tutorial": name,
                          "deliverOneStepOnly": True}, indent=2))
        return

    ap.print_help()


if __name__ == "__main__":
    main()
