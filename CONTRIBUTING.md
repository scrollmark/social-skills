# Contributing

## Adding a Skill

Create a directory under `skills/` with a `SKILL.md` file:

```
skills/your-skill-name/SKILL.md
```

The file needs YAML frontmatter with two fields:

```yaml
---
name: your-skill-name
description: Use when [triggering conditions].
---
```

- `name`: letters, numbers, hyphens only
- `description`: must start with "Use when" — this is how Claude decides whether to load the skill. Max 1024 characters.

The body should teach patterns, not specific trends. Keep it under 500 words. Write like you're explaining something to a peer, not writing a textbook.

If your skill references platform-specific knowledge, tell Claude to load the relevant reference file on demand rather than embedding the knowledge in the skill itself.

## The Self-Containment Invariant

**Every skill folder must be self-contained. A `SKILL.md` must never reference anything above its own directory.**

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
- Only ship files the skill actually loads.

The repo-root `references/` is the canonical source for shared files. Copy the ones your
skill uses into the skill folder — duplication is the correct tradeoff for portability.
When you change a shared reference, update the root copy and every skill copy of it.

Before opening a PR:

```bash
./scripts/verify-skills.sh
```

It fails if a `SKILL.md` reaches outside its folder, if any `.root` file exists, or if a
skill names a reference file it does not contain.

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

Add scenario files to `tests/scenarios/{skill-name}/`. See [tests/TESTING.md](tests/TESTING.md) for the format. Every scenario needs behavioral markers — specific, checkable items that determine whether Claude's response reflects the skill's guidance.

## Style

Write like someone who works in this space. Be direct, be specific, skip the filler. If a sentence doesn't add information, cut it.
