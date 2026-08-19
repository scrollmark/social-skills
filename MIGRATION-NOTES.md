# Migration: self-contained skills

## The bug

`install.sh` symlinked each `skills/<name>/` into `~/.claude/skills/social-skills--<name>`
and wrote a `.root` file containing the repo path. Six `SKILL.md` files then said, in
effect: *read the `.root` file in this skill's directory for the repo path, then load
`{repo}/references/...`*.

That only ever worked for the clone-and-symlink install. The route the public website
advertises —

```bash
npx skills add scrollmark/social-skills
```

— **copies** the skill folder. No symlink, no `.root`, no `references/`. The skills then
failed to load their references and fell back to a degraded path with no error message
and no signal to the user. Silent degradation: the skill still answers, just worse.

The README did not document the `npx` route at all, so the failure mode was invisible
from both ends.

## What changed

### 1. Each skill carries its own references

| Skill | `references/` now shipped inside the skill |
|-------|---------------------------------------------|
| `read-the-room` | `slang-and-signals.md` + all 5 `platforms/*.md` |
| `hook-anatomy` | all 5 `platforms/*.md` |
| `platform-fluency` | all 5 `platforms/*.md` |
| `content-autopsy` | all 5 `platforms/*.md` |
| `trend-radar` | all 5 `platforms/*.md` |
| `repurpose-engine` | all 5 `platforms/*.md` |
| `voice-matching` | none — verified it references no files |

The repo-root `references/` stays as the **canonical source**. The per-skill copies are
derived from it.

### 2. Reference loading is now relative

Every affected `SKILL.md` had exactly one sentence rewritten. The prose and meaning are
otherwise untouched — only *how the path resolves* changed:

- before: read `.root` for the repo path, then load `{repo}/references/platforms/{platform}.md`
- after: load `references/platforms/{platform}.md` from this skill's own directory

No `.root`, no `{repo}` placeholder, no repo-path resolution, no `../`.

### 3. `install.sh`

- No longer writes `.root`.
- Actively deletes any stale `.root` left by a previous install.
- Idempotent: replaces whatever already sits at the target path (symlink, directory, or
  a copy left by `npx skills add`), so re-running after a `git pull` is safe.
- Prunes `social-skills--*` links whose skill no longer exists in the repo.
- Honours `CLAUDE_SKILLS_DIR` for testing/alternate installs.
- Iterates `skills/*/` generically, so new skills need no script changes.

### 4. `uninstall.sh`

- Removes copies and broken symlinks too, not just live symlinks.
- Still cleans up legacy `.root` files.
- Honours `CLAUDE_SKILLS_DIR`.

### 5. `scripts/verify-skills.sh` (new)

Fails (exit 1) if:

- any `.root` file exists anywhere in the repo;
- a `SKILL.md` mentions `.root` or `{repo}`, or contains `../` or `/skills/`;
- a `SKILL.md` names a `references/...` file the skill folder does not contain
  (placeholder segments like `{platform}` are satisfied by any `.md` in that directory);
- a skill ships a `references/` directory its `SKILL.md` never loads from.

It works for any number of skills and needs no per-skill configuration.

### 6. Docs

`README.md` documents both install routes (`npx skills add` for users, `./install.sh` for
development) and explains the self-containment property. `CONTRIBUTING.md` states the
invariant, explains *why* it exists, and tells contributors to run `verify-skills.sh`.

## The duplication tradeoff

There are only 6 shared reference files, copied into 6 skills — roughly 26 small markdown
files where there were 6. That is cheap.

The alternative — a single shared `references/` outside the skill folders — cannot survive
the packaging model. Skills are distributed as *folders*; whatever sits above a folder is
not part of the artifact. Any indirection to escape the folder (`.root`, `../`, an
absolute path) works on the maintainer's machine and silently fails everywhere else. That
is precisely the bug being fixed.

Duplication buys correctness for every install route, and the cost is a maintenance rule
rather than a runtime risk: **edit the canonical file at the repo root, then copy it into
every skill that ships it.** `verify-skills.sh` catches a missing file; it does not catch
a stale one, so keep the copies in the same commit.

## What breaks for people who already installed

Nothing breaks at runtime — the skills work better, not worse. But two kinds of debris can
be left on machines that installed an earlier version:

1. **Orphaned symlinks.** If someone ran the old `install.sh` and later moved or deleted
   their clone, `~/.claude/skills/social-skills--*` contains dangling symlinks. Claude Code
   may log noise about unreadable skills. The new `install.sh` prunes these; the new
   `uninstall.sh` removes them.

2. **Stale `.root` files.** The old installer wrote `skills/<name>/.root` into the clone.
   They are gitignored, so a `git pull` will not remove them. They are now inert — no
   `SKILL.md` reads them — but `verify-skills.sh` fails while any exists, so contributors
   must clear them. Running the new `install.sh` or `uninstall.sh` does this automatically.

3. **A previous `npx skills add` install is a copy, not a link.** It will not pick up this
   fix until the user re-runs `npx skills add`. Until they do, they keep the old, degraded
   copies — which is the original bug, so re-installing is the whole point.

Mixed state is also possible: someone who used both routes may have a copied directory
sitting where the symlink should go. The new `install.sh` overwrites it rather than
failing.

## Upgrade steps

### If you cloned the repo

```bash
cd /path/to/social-skills
git pull
./install.sh              # rewrites symlinks, deletes stale .root, prunes dead links
./scripts/verify-skills.sh
```

To remove an old install entirely first:

```bash
./uninstall.sh && ./install.sh
```

### If you installed with npx

```bash
npx skills add scrollmark/social-skills
```

Re-running picks up the self-contained folders. If your tool does not overwrite in place,
remove the old copies first:

```bash
rm -rf ~/.claude/skills/social-skills--*
npx skills add scrollmark/social-skills
```

### If you have debris and no clone

```bash
# remove dangling symlinks left by an old ./install.sh
find ~/.claude/skills -maxdepth 1 -name 'social-skills--*' -type l ! -exec test -e {} \; -delete
```

Then reinstall by either route above.

In all cases, restart Claude Code — skills are picked up at session start.
