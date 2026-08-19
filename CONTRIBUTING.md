# Contributing

Seven rules. All of them are checkable, and `./scripts/verify-skills.sh` checks most of
them for you. Run it before you open a PR.

## 1. Frontmatter shape

Every skill is a directory under `skills/` containing a `SKILL.md`:

```
skills/your-skill-name/SKILL.md
```

The file opens with YAML frontmatter containing **exactly two keys, in this order**:

```yaml
---
name: your-skill-name
description: Use when [triggering conditions].
---
```

- `name` — letters, numbers and hyphens only, and **identical to the directory name**.
- `description` — one line, max 1024 characters, **must start with `Use when`**.
- No other keys. Not `version`, not `tags`, not `author`. If you think you need one,
  raise it in an issue first.

Immediately after the frontmatter comes a single `# Title Case Name` H1 matching the
skill, then the body.

## 2. Description voice

The description is not documentation. It is the *only* text Claude sees when deciding
whether to load the skill, so it must describe **when to reach for the skill**, never what
the skill contains.

- Write it as a trigger: `Use when <situation>` or `Use when <-ing something>`.
- Name the concrete situations, in the words a user would actually use.
- Do not describe the body ("Covers five techniques for…", "A guide to…"). A reader who
  already knows what is inside cannot tell from that whether they need it.
- Do not sell it. No "comprehensive", "powerful", "expert".
- One extra sentence of scope is acceptable if it genuinely narrows the trigger — see
  `video-formats`, which names its coverage. Two is too many.

Compare:

| | |
|---|---|
| Off-pattern | `description: A guide to hook writing with examples from TikTok and Reels.` |
| On-pattern | `description: Use when analyzing, evaluating, or generating hooks for short-form video or text posts.` |

Copy the finished description verbatim into the README skill table (see rule 7).

## 3. Length discipline

**Target 45–80 lines for a `SKILL.md`.** The skills in this repo currently run 45
(`hook-anatomy`) to 83 (`agent-interview`) lines; 83 is the outlier, not the licence.

```bash
wc -l skills/*/SKILL.md
```

Under 45 lines and the skill probably has no substance an agent could not have guessed.
Over 80 and it is either two skills, or it is holding knowledge that belongs in a
reference file loaded on demand. `verify-skills.sh` prints a warning outside this band; it
does not fail, because the judgement is yours.

The body teaches **patterns, not instances**. Write like you are explaining something to a
peer who works in this space — direct, specific, no filler. If a sentence adds no
information, cut it.

## 4. The self-containment invariant

**Every skill folder must be self-contained. A `SKILL.md` must never reference anything
above its own directory.**

Skills are installed two ways, and both must work:

```bash
npx skills add scrollmark/social-skills   # users — COPIES each skills/<name>/ folder
./install.sh                              # development — symlinks each folder
```

The `npx` route copies the skill folder and nothing else. Anything your `SKILL.md` points
at outside that folder simply will not be there, and the skill degrades silently — no
error, just worse answers. That is the bug this invariant exists to prevent.

So:

- Put the reference files your skill needs in `skills/<your-skill>/references/`.
- Load them by a path relative to the skill: `` `references/platforms/tiktok.md` ``.
- Never use `../`, an absolute path, a `{repo}` placeholder, or a `.root` file.
- Only ship files the skill actually loads — an unreferenced `references/` file is a
  failure too, because nobody will notice when it goes stale.

## 5. Shared references are duplicated on purpose

The repo-root `references/` is the **canonical source** for any file more than one skill
needs. Per-skill copies are derived from it.

- Edit the canonical file at the repo root.
- Copy it into **every** skill that ships it.
- Do both **in the same commit**. `verify-skills.sh` catches a *missing* copy; nothing
  catches a *stale* one.

Duplication is the correct tradeoff. Skills are distributed as folders; anything above the
folder is not part of the artifact, so every mechanism for escaping the folder works on
your machine and fails on everyone else's. See [MIGRATION-NOTES.md](MIGRATION-NOTES.md).

## 6. Declare your dependencies

Some skills describe work that a machine outside this repo performs — most of the video
production skills lean on the private `scrollmark/video-studio` engine (Python + Remotion).
That is allowed. Hiding it is not.

**Never vendor the external machinery.** No `.py`, no `package.json`, no vendored renderer,
no checked-in binary. This repo ships prose. The engine is invoked, never copied.

If your skill needs something this repo does not contain, it must:

1. **Say so in the `SKILL.md` itself**, in a `## Requires` section directly under the H1,
   naming the specific script or service and the repo it lives in — see `brand-kit` and
   `studio-setup`. (`video-formats` predates this convention and calls its section
   `## Toolchain Assumptions` at the foot of the file; new skills use `## Requires`.)
2. **Be honest about the degraded case.** State what a reader *without* the dependency can
   still do and what they cannot. "Requires X" is not enough; say whether the skill is
   still 90% useful or entirely inert. `video-formats` does this per-format: eight formats
   are pure structure, `boil` loses roughly 40% of its workflow without `gen_boil.py`, and
   `pointer-popups` has no usable grammar at all without `track_pointing.py`.
3. **Carry the same caveat into the README** row and the
   [engine boundary section](README.md#the-video-studio-boundary).

Do not write a skill whose instructions only make sense to someone inside Scrollmark. If
the honest version of the skill would be unreadable to an outside user, it belongs in the
private repo instead.

## 7. Before you open a PR

```bash
./scripts/verify-skills.sh
```

It fails if:

- any `.root` file exists in the repo;
- a `SKILL.md` mentions `.root` or `{repo}`, or contains `../` or `/skills/`;
- a `SKILL.md` names a `references/...` file the skill folder does not contain;
- a skill ships a `references/` directory its `SKILL.md` never loads from;
- frontmatter is missing, `name` does not match the directory, or `description` does not
  start with `Use when`;
- a skill is not listed in the README skill table.

It warns (without failing) if a `SKILL.md` falls outside 45–80 lines.

Also update, by hand:

- the **README skill table** — a row in the right group, with the description copied
  verbatim from your frontmatter;
- **[MIGRATION-NOTES.md](MIGRATION-NOTES.md)**, if you changed the structure of the repo
  rather than its content.

## Adding a Platform Reference

Create the canonical file at `references/platforms/{platform-name}.md` (repo root), then
copy it into `skills/<name>/references/platforms/` for every skill that loads platform
references. Use this structure:

```yaml
---
platform: platform-name
last_updated: YYYY-MM-DD
---
```

Required sections:

- **Content Formats** — formats, dimensions, duration limits
- **Algorithm Signals** — what the platform rewards, ranked by weight
- **Audience Behavior** — how people discover and consume content
- **Conventions** — posting norms, caption style, hashtag usage
- **Comment Culture** — how people interact on this platform
- **Creator Tiers** — how distribution differs by account size

## Adding a Video Format

Format grammars live in `skills/video-formats/references/formats/` as one kebab-case
markdown file each. The format list *is* the directory listing — no index to update.

Required sections, in order: `# Name — one-line description`, `## Composition`,
`## Interview`, `## Slots`, `## Grammar`, `## Render notes`.

Two rules, both from `video-formats` itself:

- **A format earns its file by recurring.** Three or four independent uses is a format;
  one is a video.
- **The Grammar section must be able to say no.** A grammar that only describes what a
  video may contain is a mood board.

If the format depends on a video-studio script, rule 6 applies: say so in *Render notes*,
and say what is left without it.

## Updating slang-and-signals.md

Edit `references/slang-and-signals.md` at the repo root, then copy it into every skill that
loads it (currently `skills/read-the-room/references/`). Add entries to the appropriate
category. Each entry needs:

- **Pattern/term** — what it is
- **Signal** — what it actually means
- **Example** — usage in context
- **Careful note** — common misreadings

After making changes, bump both `last_updated` and `version` in the frontmatter.

## Writing Test Scenarios

Add scenario files to `tests/scenarios/{skill-name}/`. See [tests/TESTING.md](tests/TESTING.md)
for the format. Every scenario needs behavioral markers — specific, checkable items that
determine whether Claude's response reflects the skill's guidance.
