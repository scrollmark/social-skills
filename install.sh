#!/usr/bin/env bash
set -euo pipefail

# Development install: symlink each skill folder into ~/.claude/skills/.
# Each skill folder is self-contained — it carries its own references/ —
# so a symlinked install and a copied install (npx skills add) behave identically.
#
# Regular users do not need this script:
#   npx skills add scrollmark/social-skills

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

mkdir -p "$SKILLS_DIR"

installed=0
for skill_dir in "$REPO_DIR"/skills/*/; do
  [ -f "$skill_dir/SKILL.md" ] || continue
  name="$(basename "$skill_dir")"
  target="$SKILLS_DIR/social-skills--$name"

  # Remove stale .root files written by older versions of this installer.
  rm -f "$skill_dir/.root"

  # Idempotent: replace whatever is already at the target path.
  if [ -L "$target" ] || [ -e "$target" ]; then
    rm -rf "$target"
  fi
  ln -s "${skill_dir%/}" "$target"
  installed=$((installed + 1))
  echo "  installed: social-skills--$name"
done

# Remove links for skills that no longer exist in this repo.
for link in "$SKILLS_DIR"/social-skills--*; do
  [ -L "$link" ] || continue
  if [ ! -e "$link" ]; then
    rm -f "$link"
    echo "  pruned (stale): $(basename "$link")"
  fi
done

echo ""
echo "Done. $installed skill(s) installed into $SKILLS_DIR."
