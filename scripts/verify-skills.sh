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

  # 3b. Every bundled executable a SKILL.md names must exist inside this skill.
  #     Same guarantee as the references check above, for the other thing a skill
  #     can ship. A `## Requires` block that says "ships with this skill" and
  #     names scripts/foo.py is a promise; this is what keeps it true after a
  #     rename, and it is the check that would catch a script left behind when a
  #     skill folder is copied by `npx skills add`.
  while IFS= read -r bundled; do
    bundled="${bundled#./}"
    if [ ! -f "$skill_dir/$bundled" ]; then
      err "$name/SKILL.md names bundled script '$bundled' but $name/$bundled does not exist"
    elif [ ! -x "$skill_dir/$bundled" ]; then
      warn "$name/$bundled is not executable (chmod +x)"
    fi
  done < <(grep -oE '(\./)?scripts/[A-Za-z0-9_./-]+\.(py|sh|mjs|js)' "$skill_md" | sort -u)

  # 4. Anything shipped under the skill's references/ should be reachable.
  if [ -d "$skill_dir/references" ]; then
    if ! grep -q 'references/' "$skill_md"; then
      err "$name ships references/ but SKILL.md never loads anything from it"
    fi
  fi

  # 4b. Same rule for scripts/: a bundled executable nobody invokes is dead
  #     weight that still gets copied into every install.
  if [ -d "$skill_dir/scripts" ]; then
    while IFS= read -r shipped; do
      rel="scripts/$(basename "$shipped")"
      grep -q "$rel" "$skill_md" || err "$name ships $rel but SKILL.md never invokes it"
    done < <(find "$skill_dir/scripts" -maxdepth 1 -type f \
               \( -name '*.py' -o -name '*.sh' -o -name '*.mjs' -o -name '*.js' \) 2>/dev/null)
  fi
done

# 5. A shared reference duplicated into a skill must match the canonical copy at
#    the repo root. Duplication is the price of self-containment; drift is not.
#    This is the check that catches an edit applied to references/ but not to the
#    copies — the failure mode that silently ships stale guidance.
if [ -d "$REPO_DIR/references" ]; then
  while IFS= read -r copy; do
    rel="${copy#*/references/}"
    canonical="$REPO_DIR/references/$rel"
    # A skill may own references nothing else shares (no root copy). That is
    # fine — only files that ALSO exist at the root are shared, and only those
    # can drift.
    [ -f "$canonical" ] || continue
    if ! cmp -s "$copy" "$canonical"; then
      err "${copy#$REPO_DIR/} has drifted from references/$rel (edit both, in the same commit)"
    fi
  done < <(find "$SKILLS_ROOT" -path '*/references/*' -type f -name '*.md' 2>/dev/null)
fi

# 6. A bundled script shipped by more than one skill must be byte-identical in
#    every copy. Same reasoning as rule 5: two skills genuinely need their own
#    copy (a skill may never reach outside its folder, so there is nowhere
#    shared to put it), but a fix applied to one copy and not the other ships
#    two different programs under one name. There is no root-level canonical
#    copy for scripts — the copies ARE the source, so they are compared to
#    each other.
while IFS= read -r base; do
  first=""
  while IFS= read -r copy; do
    if [ -z "$first" ]; then
      first="$copy"
    elif ! cmp -s "$copy" "$first"; then
      err "${copy#$REPO_DIR/} has drifted from ${first#$REPO_DIR/} (same script, two skills — edit both, in the same commit)"
    fi
  done < <(find "$SKILLS_ROOT" -path '*/scripts/*' -type f -name "$base" 2>/dev/null | sort)
done < <(find "$SKILLS_ROOT" -path '*/scripts/*' -type f \
           \( -name '*.py' -o -name '*.sh' -o -name '*.mjs' -o -name '*.js' \) 2>/dev/null \
         | xargs -n1 basename 2>/dev/null | sort | uniq -d)

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
