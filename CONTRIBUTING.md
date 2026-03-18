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

## Adding a Platform Reference

Create a file at `references/platforms/{platform-name}.md` with this structure:

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

Add entries to the appropriate category. Each entry needs:

- **Pattern/term** — what it is
- **Signal** — what it actually means
- **Example** — usage in context
- **Careful note** — common misreadings

After making changes, bump both `last_updated` and `version` in the frontmatter.

## Writing Test Scenarios

Add scenario files to `tests/scenarios/{skill-name}/`. See [tests/TESTING.md](tests/TESTING.md) for the format. Every scenario needs behavioral markers — specific, checkable items that determine whether Claude's response reflects the skill's guidance.

## Style

Write like someone who works in this space. Be direct, be specific, skip the filler. If a sentence doesn't add information, cut it.
