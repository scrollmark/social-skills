# /// script
# requires-python = ">=3.11"
# ///
"""Draft the daily team digest: what shipped, what it scored, what's next.

Usage:
  video-studio daily_digest                      # today, repo default
  video-studio daily_digest --since 2026-08-03 --runs runs/ --out digest.txt

Reads two things and asks nothing of the network:
- `git log` since --since, for repo changes
- a runs directory laid out as <runs>/<YYYY-MM-DD>/<slug>.mp4 with an
  optional sibling <slug>.qc.json (a quality-check report), for output

Emits plain text sized for a chat message — no markdown tables, no headings
deeper than a dash, because it is meant to be pasted and read on a phone.

House vocabulary applies (see SKILL.md): the digest is a team-facing artifact
that gets forwarded, so it names no vendor, library, or model. Numbers and
outcomes only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

from video_studio.paths import studio_root

REPO = studio_root()


def git_log(since: str) -> list[str]:
    r = subprocess.run(
        ["git", "log", f"--since={since}", "--pretty=format:%s", "--no-merges"],
        cwd=REPO, capture_output=True, text=True,
    )
    if r.returncode != 0:
        return []
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]


def collect_runs(runs_dir: Path, day: str) -> list[dict]:
    """Videos produced on `day`, with quality-check numbers when present."""
    folder = runs_dir / day
    if not folder.is_dir():
        return []
    out = []
    for mp4 in sorted(folder.glob("*.mp4")):
        entry = {"slug": mp4.stem, "path": str(mp4), "mb": round(mp4.stat().st_size / 1e6, 1)}
        qc = mp4.with_suffix(".qc.json")
        if qc.exists():
            try:
                summary = json.loads(qc.read_text()).get("summary", {})
                entry["errors"] = summary.get("errors")
                entry["warnings"] = summary.get("warnings")
            except (json.JSONDecodeError, OSError):
                pass
        note = mp4.with_suffix(".note.txt")
        if note.exists():
            entry["note"] = note.read_text().strip()
        out.append(entry)
    return out


def render(day: str, runs: list[dict], commits: list[str], next_up: str | None) -> str:
    lines = [f"Video studio — {day}", ""]

    if runs:
        lines.append(f"Shipped ({len(runs)}):")
        for r in runs:
            score = ""
            if r.get("errors") is not None:
                clean = "clean" if r["errors"] == 0 else f"{r['errors']} err"
                score = f" — {clean}, {r.get('warnings', 0)} warn"
            lines.append(f"- {r['slug']} ({r['mb']} MB){score}")
            if r.get("note"):
                lines.append(f"  {r['note']}")
    else:
        lines.append("Shipped: nothing today.")
    lines.append("")

    if commits:
        lines.append(f"Changes ({len(commits)}):")
        for c in commits[:8]:
            lines.append(f"- {c.split(chr(10))[0][:100]}")
        if len(commits) > 8:
            lines.append(f"- (+{len(commits) - 8} more)")
    else:
        lines.append("Changes: none.")
    lines.append("")

    lines.append(f"Next: {next_up}" if next_up else "Next: (fill in)")

    clean = [r for r in runs if r.get("errors") == 0]
    if clean:
        lines += ["", f"{len(clean)}/{len(runs)} passed the quality check with zero errors."]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=date.today().isoformat(), help="run folder to summarise (YYYY-MM-DD)")
    ap.add_argument("--since", help="git window; defaults to the day before --day")
    ap.add_argument("--runs", default=str(REPO / "runs"))
    ap.add_argument("--next", dest="next_up", help="one line on what's queued next")
    ap.add_argument("--out", help="write here as well as stdout")
    args = ap.parse_args()

    since = args.since or (date.fromisoformat(args.day) - timedelta(days=1)).isoformat()
    text = render(
        args.day,
        collect_runs(Path(args.runs), args.day),
        git_log(since),
        args.next_up,
    )
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")


if __name__ == "__main__":
    main()
