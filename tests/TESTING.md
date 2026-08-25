# Testing Social Skills

Two suites, checking different kinds of claim.

**`unit/` — executable tests.** `pytest tests/unit` — or `pip install -e '.[dev]'`
first. These check the things that need running code: that no QC detector reports
a skip which hides our own packaging bug, that scene durations come from measured
audio rather than a plan, that karaoke tags sum to their page, that the README's
counts match the code, that the wheel actually ships its data files.

They deliberately build real WAVs and real mp4s with ffmpeg rather than mocking
them. Every bug this suite exists to catch was one where the code ran happily and
produced nothing useful — and a mock reproduces that state perfectly.

**`scenarios/` — behavioral tests for documentation.** Each scenario checks whether
Claude reasons differently (better) with a skill loaded. Every skill must have at
least one; `tests/unit/test_packaging.py` enforces it.

## How to Run a Scenario

1. Install the skills: `./install.sh`
2. Start a **new** Claude Code session (skills load at session start)
3. Paste the prompt from the scenario file
4. Check the response against the **behavioral markers**

The "Without skill" section is optional context — it describes what Claude typically does without the skill. You don't need to run it, but it's useful for validating the skill is actually adding value.

## How to Write a Scenario

```markdown
---
skill: skill-name
---

## Prompt
[A specific prompt that exercises the skill]

## Without skill (baseline)
[What Claude typically does — the gap this skill fills]

## With skill (expected)
[What Claude should do with the skill loaded]

## Behavioral markers
[Specific, checkable items to look for in the response]
```

Behavioral markers should be concrete. "Identifies the register" is checkable. "Gives a better answer" is not.

## Scenario Files

Each scenario lives in `scenarios/{skill-name}/`. A skill should have at least one scenario. More is better for skills with nuanced behavior.
