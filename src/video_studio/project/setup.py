# /// script
# requires-python = ">=3.11"
# ///
"""Check every prerequisite and offer to install what is missing.

Usage:
  uv run scripts/setup.py              # report + the exact plan, changes NOTHING
  uv run scripts/setup.py --json       # same, machine-readable
  uv run scripts/setup.py --yes        # actually run the runnable fixes
  uv run scripts/setup.py --yes --only composer,voice

`doctor.py` answers "what can I use right now". This answers "how do I get the
rest", and can do it for you.

Three classes of fix, and the split is the whole point:

  auto    scoped to this skill directory, idempotent, safe to re-run
          (installing the composer's packages, warming the voice model)
  system  changes the machine outside this directory (a package manager
          installing ffmpeg or node) — still runnable, but it is somebody's
          computer, so it is never run without --yes and is always named first
  manual  a human has to act: sign up for a key, enable billing, accept terms.
          NEVER runnable. Printing "run this command" for something a machine
          cannot do wastes the reader's time and erodes trust in the rest.

Nothing here runs without --yes. The default output is a plan you can read.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from video_studio.paths import studio_root

SKILL_ROOT = studio_root()
IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def detect_host() -> dict:
    """Which agent is running this, and what can it actually do?

    This skill is a SKILL.md directory, and Claude Code and Codex both load it
    from their own user-skills roots. They do NOT offer the same capabilities,
    and two differences change how the workflow has to run — so they are
    detected rather than assumed.

    `ask_ui` is whether the host can put a real multiple-choice question on
    screen. The interview steps are written around one; without it the agent
    asks in prose, which works but is slower and easier to answer vaguely.

    `network_blocked` matters more. Codex sandboxes by default with the network
    off, and every stock and generation call here needs it. Undetected, that
    surfaces as a pile of confusing per-provider timeouts rather than one clear
    cause.
    """
    env = os.environ
    if env.get("CLAUDE_CODE_ENTRYPOINT") or env.get("CLAUDE_AGENT_SDK_VERSION"):
        host = "claude-code"
    elif env.get("CODEX_THREAD_ID") or env.get("CODEX_SANDBOX"):
        host = "codex"
    else:
        host = "unknown"

    return {
        "host": host,
        # Claude Code ships a native question tool. Every other host needs the
        # MCP server below to get the same affordance.
        "ask_ui_native": host == "claude-code",
        "ask_ui_mcp": have("auq-mcp-server") or auq_configured(),
        "network_blocked": env.get("CODEX_SANDBOX_NETWORK_DISABLED", "").strip().lower()
        in {"1", "true", "yes", "on"},
        "sandboxed": bool(env.get("CODEX_SANDBOX")),
    }


def auq_configured() -> bool:
    """Is the ask-user-questions MCP registered with any host on this machine?

    Read from the hosts' own config files rather than by probing: starting a
    server to answer a status question is rude, and this runs on every report.
    """
    for p in (Path.home() / ".claude.json",
              Path.home() / ".codex" / "config.toml",
              Path.home() / ".cursor" / "mcp.json"):
        try:
            if p.exists() and "auq-mcp-server" in p.read_text():
                return True
        except (OSError, UnicodeDecodeError):
            continue
    return False


def pkg_install(pkg: str) -> tuple[list[str] | None, str]:
    """The right system package-manager invocation for this machine."""
    if IS_MAC:
        if have("brew"):
            return ["brew", "install", pkg], f"brew install {pkg}"
        return None, (
            f"install {pkg} — no Homebrew found. Get it at https://brew.sh "
            f"then `brew install {pkg}`"
        )
    if IS_LINUX:
        for mgr, args in (("apt-get", ["sudo", "apt-get", "install", "-y", pkg]),
                          ("dnf", ["sudo", "dnf", "install", "-y", pkg]),
                          ("pacman", ["sudo", "pacman", "-S", "--noconfirm", pkg])):
            if have(mgr):
                # sudo needs a TTY we may not have, so this is reported rather
                # than run — a hung password prompt inside a tool call looks
                # exactly like a crash.
                return None, " ".join(args)
    return None, f"install {pkg} for your platform"


def node_modules_ok() -> bool:
    nm = SKILL_ROOT / "composer" / "node_modules"
    # A bare directory is not proof: an interrupted install leaves one behind
    # with nothing usable in it.
    return (nm / "remotion").exists() or (nm / ".package-lock.json").exists()


def voice_ok() -> bool:
    script = SKILL_ROOT / "scripts" / "tts_kokoro.py"
    if not script.exists() or not have("uv"):
        return False
    try:
        r = subprocess.run(["uv", "run", str(script), "--check"],
                           capture_output=True, text=True, timeout=600)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


def env_file_ok() -> bool:
    return (SKILL_ROOT / ".env").exists()


def keys_present() -> list[str]:
    """Which provider keys are set, counting the .env file as well as the shell."""
    found = set()
    for name in ("PEXELS_API_KEY", "PIXABAY_API_KEY", "FREESOUND_API_KEY",
                 "MINIMAX_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                 "REPLICATE_API_TOKEN", "ELEVENLABS_API_KEY"):
        if os.environ.get(name):
            found.add(name)
    env = SKILL_ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if v.strip().strip('"').strip("'"):
                    found.add(k.strip())
    return sorted(found)


def build_components() -> list[dict]:
    ff_cmd, ff_note = pkg_install("ffmpeg")
    node_cmd, node_note = pkg_install("node")

    comps: list[dict] = [
        {
            "id": "uv",
            "label": "uv",
            "why": "runs every bundled script with its own dependencies",
            "ok": have("uv"),
            "required": True,
            "kind": "system",
            "cmd": None,
            "note": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        },
        {
            "id": "ffmpeg",
            "label": "ffmpeg + ffprobe",
            "why": "measuring durations, keying, loudness — nothing renders correctly without it",
            "ok": have("ffmpeg") and have("ffprobe"),
            "required": True,
            "kind": "system",
            "cmd": ff_cmd,
            "note": ff_note,
        },
        {
            "id": "node",
            "label": "Node 18+",
            "why": "the composer renders and previews through it",
            "ok": have("node"),
            "required": True,
            "kind": "system",
            "cmd": node_cmd,
            "note": node_note if not IS_MAC or not have("brew") else "brew install node",
        },
        {
            "id": "composer",
            "label": "composer packages",
            "why": "the render/preview project's own dependencies",
            "ok": node_modules_ok(),
            "required": True,
            "kind": "auto",
            "cmd": ["npm", "install"],
            "cwd": str(SKILL_ROOT / "composer"),
            "note": "npm install (in composer/)",
            "needs": ["node"],
        },
        {
            "id": "voice",
            "label": "narration voice",
            "why": "every narrated format depends on it; it runs locally and free",
            "ok": voice_ok(),
            "required": True,
            "kind": "auto",
            # Running --check IS the install: uv resolves the pinned 3.12
            # interpreter and the dependencies on first use.
            "cmd": ["uv", "run", str(SKILL_ROOT / "scripts" / "tts_kokoro.py"), "--check"],
            "note": "uv run scripts/tts_kokoro.py --check  (first run downloads the model, a few minutes)",
            "needs": ["uv"],
        },
        {
            "id": "env",
            "label": ".env file",
            "why": "where provider keys live so they are not retyped per shell",
            "ok": env_file_ok(),
            "required": False,
            "kind": "auto",
            "cmd": ["cp", str(SKILL_ROOT / ".env.example"), str(SKILL_ROOT / ".env")],
            "note": "cp .env.example .env  (gitignored)",
        },
        {
            "id": "qc",
            "label": "quality check",
            "why": "the automated pass in step 8; without it, frames are verified by hand",
            "ok": have("showwatcher"),
            "required": False,
            "kind": "system",
            "cmd": None,
            "note": "internal tool — install from its own repo; the workflow degrades gracefully without it",
        },
    ]

    host = detect_host()

    # Only worth offering where the host lacks a native question tool. On
    # Claude Code this would be a second, worse way to do something the host
    # already does well, so it is not even listed.
    if not host["ask_ui_native"]:
        comps.append({
            "id": "ask-ui",
            "label": "question UI",
            "why": "lets the interview show a real picker; without it it uses numbered choices, which is fine",
            "ok": host["ask_ui_mcp"],
            "required": False,
            "kind": "system",
            "cmd": ["npm", "install", "-g", "auq-mcp-server"],
            "needs": ["node"],
            "note": (
                "npm install -g auq-mcp-server, then register it with your host:\n"
                "        codex:       codex mcp add ask-user-questions -- npx -y auq-mcp-server server\n"
                "        claude code: claude mcp add --transport stdio ask-user-questions "
                "-- npx -y auq-mcp-server server"
            ),
        })

    # Not installable — it is a flag on how the host was launched. Surfaced
    # because the alternative is watching every provider call time out and
    # guessing why.
    if host["network_blocked"]:
        comps.append({
            "id": "network",
            "label": "network access",
            "why": "every stock lookup and generation call needs it; the sandbox has it switched off",
            "ok": False,
            "required": True,
            "kind": "manual",
            "cmd": None,
            "note": (
                "this session is sandboxed with the network disabled. Restart the host with "
                "network access — for codex: --sandbox danger-full-access, or a config profile "
                "granting network plus this directory as a writable root."
            ),
        })

    keys = keys_present()
    comps.append({
        "id": "keys",
        "label": "provider keys",
        "why": "widen which footage can be reached; archives and voice work without any",
        "ok": bool(keys),
        "required": False,
        "kind": "manual",
        "cmd": None,
        "note": (
            f"present: {', '.join(keys)}" if keys else
            "none set. Start with PEXELS_API_KEY — free, no billing, at "
            "pexels.com/api. Put it in .env at the skill root."
        ),
    })
    return comps


def run_fix(comp: dict) -> tuple[bool, str]:
    if comp["kind"] == "manual" or not comp.get("cmd"):
        return False, "not machine-installable"
    try:
        r = subprocess.run(comp["cmd"], cwd=comp.get("cwd"),
                           capture_output=True, text=True, timeout=1800)
    except FileNotFoundError as exc:
        return False, f"{exc}"
    except subprocess.TimeoutExpired:
        return False, "timed out"
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip().splitlines()
        return False, tail[-1][:200] if tail else f"exit {r.returncode}"
    return True, "done"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true",
                    help="actually run the runnable fixes (nothing runs without this)")
    ap.add_argument("--only", help="comma-separated component ids to act on")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    comps = build_components()
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        comps = [c for c in comps if c["id"] in wanted]

    host = detect_host()

    if args.json and not args.yes:
        print(json.dumps({"host": host, "components": comps}, indent=2))
        return

    missing = [c for c in comps if not c["ok"]]

    if not args.yes:
        if host["host"] != "claude-code":
            ask = "native picker" if host["ask_ui_native"] else (
                "picker via MCP" if host["ask_ui_mcp"] else
                "numbered choices (see SKILL.md)")
            print(f"host: {host['host']}  ·  questions: {ask}"
                  + ("  ·  NETWORK BLOCKED" if host["network_blocked"] else "")
                  + "\n")
        for c in comps:
            mark = "OK  " if c["ok"] else ("--  " if not c["required"] else "!!  ")
            print(f"{mark}{c['label']:<20}{c['why']}")
        if not missing:
            print("\nEverything needed is present.")
            return
        runnable = [c for c in missing if c["kind"] != "manual" and c.get("cmd")]
        manual = [c for c in missing if c not in runnable]
        print()
        if runnable:
            print("I can install these for you (re-run with --yes):")
            for c in runnable:
                scope = "this skill only" if c["kind"] == "auto" else "CHANGES YOUR SYSTEM"
                print(f"  - {c['label']}  [{scope}]\n      {c['note']}")
        if manual:
            print("\nThese need you — a machine cannot do them:")
            for c in manual:
                print(f"  - {c['label']}\n      {c['note']}")
        blocking = [c for c in missing if c["required"]]
        if blocking:
            print(f"\nBlocking: {', '.join(c['label'] for c in blocking)}")
        return

    # --yes: install, in dependency order, skipping anything whose prerequisite failed.
    done: dict[str, bool] = {c["id"]: c["ok"] for c in comps}
    results = []
    for c in comps:
        if c["ok"]:
            continue
        unmet = [n for n in c.get("needs", []) if not done.get(n)]
        if unmet:
            results.append({"id": c["id"], "ok": False, "detail": f"needs {', '.join(unmet)} first"})
            continue
        if c["kind"] == "manual" or not c.get("cmd"):
            results.append({"id": c["id"], "ok": False, "detail": c["note"], "manual": True})
            continue
        print(f"installing {c['label']} ...", flush=True)
        ok, detail = run_fix(c)
        done[c["id"]] = ok
        results.append({"id": c["id"], "ok": ok, "detail": detail})
        print(f"  {'OK' if ok else 'FAILED'}: {detail}")

    if args.json:
        print(json.dumps({"results": results}, indent=2))
        return
    left = [r for r in results if not r["ok"]]
    if left:
        print("\nStill outstanding:")
        for r in left:
            print(f"  - {r['id']}: {r['detail']}")
    else:
        print("\nAll runnable fixes applied.")


if __name__ == "__main__":
    main()
