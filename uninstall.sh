#!/usr/bin/env bash
set -euo pipefail

SKILLS_DIR="$HOME/.claude/skills"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  echo "Usage: ./uninstall.sh [skill ...]"
  echo ""
  echo "With no arguments, removes all installed social-skills."
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

count=0

if [ $# -gt 0 ]; then
  for name in "$@"; do
    link="$SKILLS_DIR/social-skills--$name"
    if [ -L "$link" ]; then
      rm "$link"
      count=$((count + 1))
    else
      echo "not installed: $name" >&2
    fi
    rm -f "$REPO_DIR/skills/$name/.root"
  done
else
  for link in "$SKILLS_DIR"/social-skills--*; do
    [ -L "$link" ] || continue
    rm "$link"
    count=$((count + 1))
  done

  # Clean up .root files
  for skill_dir in "$REPO_DIR"/skills/*/; do
    rm -f "$skill_dir/.root"
  done
fi

echo "Removed $count social-skills symlinks."
