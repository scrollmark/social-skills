#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"

usage() {
  echo "Usage: ./install.sh [skill ...]"
  echo ""
  echo "With no arguments, installs all skills. Available:"
  for d in "$REPO_DIR"/skills/*/; do
    [ -f "$d/SKILL.md" ] && echo "  $(basename "$d")"
  done
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

install_one() {
  local skill_dir="$1"
  local name target
  name="$(basename "$skill_dir")"
  target="$SKILLS_DIR/social-skills--$name"

  # Write .root so skills can resolve reference paths
  echo "$REPO_DIR" > "$skill_dir/.root"

  # Create or update symlink
  if [ -L "$target" ]; then
    rm "$target"
  fi
  ln -s "$skill_dir" "$target"
  echo "  installed: social-skills--$name"
}

mkdir -p "$SKILLS_DIR"

if [ $# -gt 0 ]; then
  for name in "$@"; do
    skill_dir="$REPO_DIR/skills/$name"
    if [ ! -f "$skill_dir/SKILL.md" ]; then
      echo "error: unknown skill '$name'" >&2
      echo "" >&2
      usage >&2
      exit 1
    fi
    install_one "$skill_dir"
  done
else
  for skill_dir in "$REPO_DIR"/skills/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    install_one "$skill_dir"
  done
fi

echo ""
echo "Done. $(ls -d "$SKILLS_DIR"/social-skills--* 2>/dev/null | wc -l | tr -d ' ') skills installed."
