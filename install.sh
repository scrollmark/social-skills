#!/usr/bin/env bash
set -euo pipefail

# Development install: symlink skill folders into ~/.claude/skills/.
# Each skill folder is self-contained — it carries its own references/ —
# so a symlinked install and a copied install (npx skills add) behave identically.
#
#   ./install.sh                      install every skill
#   ./install.sh trend-radar          install just one
#   ./install.sh brand-kit video-formats
#   ./install.sh --list               show what is available
#
# Regular users do not need this script:
#   npx skills add scrollmark/social-skills

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

available() {
  for d in "$REPO_DIR"/skills/*/; do
    [ -f "$d/SKILL.md" ] && basename "$d"
  done
}

usage() {
  cat <<EOF
Usage: ./install.sh [skill ...]

With no arguments, installs every skill. Named skills install only those.

Available:
$(available | sed 's/^/  /')

Options:
  --list, -l    list available skills and exit
  --help, -h    show this message
EOF
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
  -l|--list) available; exit 0 ;;
esac

# Resolve the requested set, failing loudly on a name that does not exist —
# a typo should not look like a successful install of nothing.
requested=("$@")
if [ ${#requested[@]} -gt 0 ]; then
  unknown=()
  for name in "${requested[@]}"; do
    [ -f "$REPO_DIR/skills/$name/SKILL.md" ] || unknown+=("$name")
  done
  if [ ${#unknown[@]} -gt 0 ]; then
    echo "Unknown skill(s): ${unknown[*]}" >&2
    echo "" >&2
    echo "Available:" >&2
    available | sed 's/^/  /' >&2
    exit 1
  fi
fi

install_one() {
  local skill_dir="${1%/}"
  local name target
  name="$(basename "$skill_dir")"
  target="$SKILLS_DIR/social-skills--$name"

  # Remove stale .root files written by older versions of this installer.
  rm -f "$skill_dir/.root"

  # Idempotent: replace whatever is already at the target path.
  if [ -L "$target" ] || [ -e "$target" ]; then
    rm -rf "$target"
  fi
  ln -s "$skill_dir" "$target"
  echo "  installed: social-skills--$name"
}

mkdir -p "$SKILLS_DIR"

installed=0
if [ ${#requested[@]} -gt 0 ]; then
  for name in "${requested[@]}"; do
    install_one "$REPO_DIR/skills/$name"
    installed=$((installed + 1))
  done
else
  for skill_dir in "$REPO_DIR"/skills/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    install_one "$skill_dir"
    installed=$((installed + 1))
  done
fi

# Remove links for skills that no longer exist in this repo. Only safe on a
# full install — a partial install must not prune skills it was not asked about.
if [ ${#requested[@]} -eq 0 ]; then
  for link in "$SKILLS_DIR"/social-skills--*; do
    [ -L "$link" ] || continue
    if [ ! -e "$link" ]; then
      rm -f "$link"
      echo "  pruned (stale): $(basename "$link")"
    fi
  done
fi

echo ""
echo "Done. $installed skill(s) installed into $SKILLS_DIR."
