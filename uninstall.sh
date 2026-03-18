#!/usr/bin/env bash
set -euo pipefail

SKILLS_DIR="$HOME/.claude/skills"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

count=0
for link in "$SKILLS_DIR"/social-skills--*; do
  [ -L "$link" ] || continue
  rm "$link"
  count=$((count + 1))
done

# Clean up .root files
for skill_dir in "$REPO_DIR"/skills/*/; do
  rm -f "$skill_dir/.root"
done

echo "Removed $count social-skills symlinks."
