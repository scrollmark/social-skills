# Testing Social Skills

These are behavioral tests for documentation, not code tests. Each scenario checks whether Claude reasons differently (better) with a skill loaded.

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
