#!/usr/bin/env bash
set -euo pipefail

# Remove skills installed by ./install.sh.
#
#   ./uninstall.sh                    remove every social-skills entry
#   ./uninstall.sh trend-radar        remove just one
#   ./uninstall.sh brand-kit video-formats

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

installed_entries() {
  for link in "$SKILLS_DIR"/social-skills--*; do
    [ -L "$link" ] || [ -e "$link" ] || continue
    basename "$link" | sed 's/^social-skills--//'
  done
}

usage() {
  cat <<EOF
Usage: ./uninstall.sh [skill ...]

With no arguments, removes every social-skills entry. Named skills remove
only those.

Currently installed:
$(installed_entries | sed 's/^/  /')
EOF
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
esac

remove_one() {
  local name="$1"
  local target="$SKILLS_DIR/social-skills--$name"
  # Match symlinks and any leftover copies (broken links included).
  if [ -L "$target" ] || [ -e "$target" ]; then
    rm -rf "$target"
    echo "  removed: social-skills--$name"
    return 0
  fi
  echo "  not installed: social-skills--$name" >&2
  return 1
}

count=0
if [ $# -gt 0 ]; then
  for name in "$@"; do
    remove_one "$name" && count=$((count + 1)) || true
  done
else
  for link in "$SKILLS_DIR"/social-skills--*; do
    [ -L "$link" ] || [ -e "$link" ] || continue
    rm -rf "$link"
    count=$((count + 1))
  done
fi

# Clean up .root files written by older versions of install.sh. Only on a full
# uninstall — a partial one should leave the rest of the repo alone.
if [ $# -eq 0 ]; then
  for skill_dir in "$REPO_DIR"/skills/*/; do
    [ -d "$skill_dir" ] || continue
    rm -f "$skill_dir/.root"
  done
fi

echo ""
echo "Removed $count social-skills entr(ies) from $SKILLS_DIR."
