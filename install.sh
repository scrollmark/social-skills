#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"

mkdir -p "$SKILLS_DIR"

for skill_dir in "$REPO_DIR"/skills/*/; do
  [ -f "$skill_dir/SKILL.md" ] || continue
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
done

echo ""
echo "Done. $(ls -d "$SKILLS_DIR"/social-skills--* 2>/dev/null | wc -l | tr -d ' ') skills installed."
