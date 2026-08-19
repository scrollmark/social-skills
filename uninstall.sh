#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

count=0
for link in "$SKILLS_DIR"/social-skills--*; do
  # Match symlinks and any leftover copies (broken links included).
  [ -L "$link" ] || [ -e "$link" ] || continue
  rm -rf "$link"
  count=$((count + 1))
done

# Clean up .root files written by older versions of install.sh.
for skill_dir in "$REPO_DIR"/skills/*/; do
  [ -d "$skill_dir" ] || continue
  rm -f "$skill_dir/.root"
done

echo "Removed $count social-skills entr(ies) from $SKILLS_DIR."
