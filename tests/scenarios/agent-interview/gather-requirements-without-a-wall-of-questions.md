---
skill: agent-interview
---

## Prompt

I want to build an onboarding flow for my app. Ask me what you need to know.

## Without skill (baseline)

Claude asks a long open-ended list — "what's your target audience, what's your tech stack, what's your timeline, what are your goals" — which is tiring to answer and produces vague replies.

## With skill (expected)

Claude asks in small rounds of answerable questions, each with concrete options and an escape hatch for anything the options miss. It asks about the decisions that actually change the outcome and stops when it has enough, rather than collecting everything up front.

## Behavioral markers

- [ ] Asks a small number of questions at a time, not a wall
- [ ] Offers concrete options rather than open prompts
- [ ] Leaves room for an answer the options do not cover
- [ ] Stops asking once the answers would not change the work
