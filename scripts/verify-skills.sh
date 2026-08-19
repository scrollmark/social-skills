#!/usr/bin/env bash
set -euo pipefail

# Enforces the self-containment invariant:
#   Every skills/<name>/ folder must work standalone. A SKILL.md may only
#   reference files inside its own directory, and every referenced file
#   must actually exist there. No .root indirection anywhere.
#
# Exits non-zero on the first class of failure found. Run from anywhere.

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_ROOT="$REPO_DIR/skills"
fail=0

err() { echo "FAIL: $*" >&2; fail=1; }

[ -d "$SKILLS_ROOT" ] || { echo "FAIL: no skills/ directory at $SKILLS_ROOT" >&2; exit 1; }

# 1. No .root files may exist anywhere in the repo.
while IFS= read -r rootfile; do
  err ".root file present: ${rootfile#$REPO_DIR/} (skills must not resolve a repo path)"
done < <(find "$REPO_DIR" -name '.root' -not -path '*/.git/*' 2>/dev/null)

skill_count=0
for skill_dir in "$SKILLS_ROOT"/*/; do
  skill_md="$skill_dir/SKILL.md"
  [ -f "$skill_md" ] || continue
  name="$(basename "$skill_dir")"
  skill_count=$((skill_count + 1))

  # 2. No escape-hatch indirection or paths reaching above the skill folder.
  if grep -qn '\.root' "$skill_md"; then
    err "$name/SKILL.md mentions .root"
  fi
  if grep -qn '{repo}' "$skill_md"; then
    err "$name/SKILL.md uses a {repo} placeholder"
  fi
  if grep -qn '\.\./' "$skill_md"; then
    err "$name/SKILL.md contains a '../' path (must not reference outside its own folder)"
  fi
  if grep -qn '/skills/' "$skill_md"; then
    err "$name/SKILL.md contains an absolute-looking '/skills/' path"
  fi

  # 3. Every referenced references/... file must exist inside this skill.
  #    Placeholder segments like {platform} expand to every sibling file.
  while IFS= read -r ref; do
    ref="${ref#./}"
    if [[ "$ref" == *"{"* ]]; then
      dir="$(dirname "$ref")"
      if [ ! -d "$skill_dir/$dir" ]; then
        err "$name/SKILL.md references '$ref' but $name/$dir/ does not exist"
      elif [ -z "$(find "$skill_dir/$dir" -maxdepth 1 -name '*.md' -print -quit)" ]; then
        err "$name/SKILL.md references '$ref' but $name/$dir/ contains no .md files"
      fi
    elif [ ! -f "$skill_dir/$ref" ]; then
      err "$name/SKILL.md references '$ref' but $name/$ref does not exist"
    fi
  done < <(grep -oE '(\./)?references/[A-Za-z0-9_{}./-]+\.md' "$skill_md" | sort -u)

  # 4. Anything shipped under the skill's references/ should be reachable.
  if [ -d "$skill_dir/references" ]; then
    if ! grep -q 'references/' "$skill_md"; then
      err "$name ships references/ but SKILL.md never loads anything from it"
    fi
  fi
done

if [ "$skill_count" -eq 0 ]; then
  echo "FAIL: no skills with a SKILL.md found under skills/" >&2
  exit 1
fi

if [ "$fail" -ne 0 ]; then
  echo "" >&2
  echo "verify-skills: FAILED ($skill_count skill(s) checked)" >&2
  exit 1
fi

echo "verify-skills: OK — $skill_count skill(s) are self-contained."
