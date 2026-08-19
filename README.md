# Social Skills

Claude Code skills for understanding social media. Because even AI needs social skills.

## What is this?

A collection of installable [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code) that teach Claude the cultural literacy it needs to work with social media content — understanding tone, hooks, trends, platform conventions, and creator voice.

## Skills

| Skill | What it does |
|-------|-------------|
| `read-the-room` | Interpret tone, sarcasm, irony, and cultural context in social media text |
| `hook-anatomy` | Analyze, evaluate, and generate hooks for short-form video and text |
| `trend-radar` | Assess trend lifecycle, timing, and relevance for a specific creator |
| `platform-fluency` | Understand platform conventions, algorithms, and audience behavior |
| `content-autopsy` | Investigate why content performed well or poorly |
| `voice-matching` | Capture and write in a specific creator's voice |
| `repurpose-engine` | Adapt content across platforms while keeping it native |

## Platforms

Primary coverage: **Instagram**, **TikTok**, **YouTube**

Also covered: **X**, **LinkedIn**

## Install

### For users (recommended)

```bash
npx skills add scrollmark/social-skills
```

This copies each skill folder into your Claude Code skills directory. Every skill is
self-contained — it ships the reference files it needs — so a copied install has the
exact same behaviour as a cloned one.

### For development

```bash
git clone https://github.com/scrollmark/social-skills.git
cd social-skills
./install.sh
```

`install.sh` symlinks each `skills/<name>/` into `~/.claude/skills/social-skills--<name>`,
so edits in your clone take effect immediately. It is idempotent — re-run it any time,
including after pulling new skills — and it prunes links whose skill no longer exists.
Set `CLAUDE_SKILLS_DIR` to install somewhere other than `~/.claude/skills`.

Either way, skills become available in your next Claude Code session.

## Uninstall

```bash
./uninstall.sh
```

Removes every `social-skills--*` entry from your skills directory (symlinks and copies
alike) and deletes any stale `.root` files left behind by older versions of `install.sh`.

## Self-contained skills

Every skill folder stands on its own. `skills/<name>/` contains its `SKILL.md` plus its
own `references/`, and a `SKILL.md` never points at anything above its own directory.

That is what makes the two install routes equivalent. Earlier versions resolved reference
paths through a `.root` file that only `install.sh` wrote, so `npx skills add` installs
silently ran without their references. The shared reference files under the repo-root
`references/` remain the canonical source and are copied into each skill that uses them.

Run `./scripts/verify-skills.sh` to check the invariant.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
