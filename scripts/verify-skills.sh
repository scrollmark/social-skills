#!/usr/bin/env bash
set -euo pipefail

# Enforces the self-containment invariant:
#   Every skills/<name>/ folder must work standalone. A SKILL.md may only
#   reference files inside its own directory, and every referenced file
#   must actually exist there. No .root indirection anywhere.
#
# Also enforces the frontmatter shape and README listing described in
# CONTRIBUTING.md, and warns on SKILL.md length outside 45-80 lines.
#
# Exits non-zero on the first class of failure found. Run from anywhere.

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_ROOT="$REPO_DIR/skills"
README="$REPO_DIR/README.md"
fail=0
warned=0

err() { echo "FAIL: $*" >&2; fail=1; }
warn() { echo "WARN: $*" >&2; warned=$((warned + 1)); }

# Prints the frontmatter block (between the first two --- lines) of a file.
frontmatter() { awk 'NR==1 && $0!="---"{exit} /^---$/{n++; next} n==1' "$1"; }

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

  # 2a. Frontmatter shape: exactly `name` + `description`, name matches the
  #     directory, description is a "Use when" trigger under 1024 chars.
  fm="$(frontmatter "$skill_md")"
  if [ -z "$fm" ]; then
    err "$name/SKILL.md has no YAML frontmatter"
  else
    fm_name="$(printf '%s\n' "$fm" | sed -n 's/^name:[[:space:]]*//p' | head -1)"
    fm_desc="$(printf '%s\n' "$fm" | sed -n 's/^description:[[:space:]]*//p' | head -1)"
    fm_keys="$(printf '%s\n' "$fm" | grep -cE '^[A-Za-z_-]+:' || true)"

    [ "$fm_name" = "$name" ] || err "$name/SKILL.md frontmatter name is '$fm_name', expected '$name'"
    case "$fm_desc" in
      "Use when"*) ;;
      "") err "$name/SKILL.md frontmatter has no description" ;;
      *) err "$name/SKILL.md description must start with 'Use when' (got: ${fm_desc:0:40}...)" ;;
    esac
    [ "${#fm_desc}" -le 1024 ] || err "$name/SKILL.md description is ${#fm_desc} chars (max 1024)"
    [ "$fm_keys" -eq 2 ] || err "$name/SKILL.md frontmatter has $fm_keys keys; only 'name' and 'description' are allowed"
  fi

  # 2b. Every skill must appear in the README skill table.
  if [ -f "$README" ] && ! grep -q "\`$name\`" "$README"; then
    err "$name is not listed in README.md (add a row to the skill table)"
  fi

  # 2c. Length discipline — advisory only, see CONTRIBUTING.md rule 3.
  lines="$(wc -l < "$skill_md" | tr -d ' ')"
  if [ "$lines" -lt 45 ] || [ "$lines" -gt 80 ]; then
    warn "$name/SKILL.md is $lines lines (target 45-80)"
  fi

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

if [ "$warned" -ne 0 ]; then
  echo "verify-skills: OK with $warned warning(s) — $skill_count skill(s) are self-contained."
else
  echo "verify-skills: OK — $skill_count skill(s) are self-contained."
fi
