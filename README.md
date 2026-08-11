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

Via the [skills.sh](https://skills.sh) CLI (no clone needed):

```bash
npx skills add scrollmark/social-skills                  # all seven
npx skills add scrollmark/social-skills -s hook-anatomy  # just one
```

Or from a clone:

```bash
git clone https://github.com/scrollmark/social-skills.git
cd social-skills
./install.sh                            # all seven
./install.sh hook-anatomy trend-radar   # just the ones you name
```

Cloned skills are symlinked into `~/.claude/skills/` and will be available in your next Claude Code session. `./install.sh --help` lists the available skill names.

## Uninstall

```bash
./uninstall.sh                # remove all
./uninstall.sh hook-anatomy   # remove one
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
