---
name: agent-interview
description: Use when you need to ask a user a series of decisions — a guided setup, an intake, a wizard, an onboarding walkthrough — and want the questions to be answerable rather than open-ended.
---

# Agent Interview

An interview is a protocol, not a conversation where you happen to ask things:
one decision at a time, real options to pick from, one consistent name per
thing, and a readback before anything expensive. Open questions get vague
answers, and vague answers get silently invented into specifics later.

## Asking

Ask **choice questions** — a real question with named options. Use the highest
rung the host offers:

1. **A native question tool** (e.g. AskUserQuestion). Best — the user picks,
   and "Other" is always there for freeform.
2. **A question MCP**, if registered. Same affordance, no native picker needed.
3. **Numbered choices in the message.** The fallback below — a real path, not
   a failure.

There is no fourth rung, and know why before inventing one: **your shell has no
terminal attached** — no tty, no stdin. `read` returns immediately, so a prompt
script hangs or silently takes a default nobody chose.

## The numbered fallback

One round at a time, every question of it in a single block, labels unique
across the whole round:

```
**Q1. Which filing status?**  (pick one · default: a)
   a) Single   b) Married filing jointly   c) Head of household
**Q2. Which apply to you?**  (pick any · default: none)
   a) Dependents   b) Self-employed income   c) Rental income

Reply like `1a 2c`, or say it in words. Anything the options miss, say
plainly and it goes in as-is.
```

Each rule below exists because the loose version fails a specific way.

- **Label across the round, not within a question.** `Q1`/`Q2` crossed with
  `a`/`b`/`c` parses one way; per-question `1) 2) 3)` makes "the second one"
  ambiguous the moment a round has two questions.
- **Mark pick-one or pick-any on every question.** Unmarked, a multi-select
  answer reads as a single choice and the extras vanish unnoticed.
- **Name a default per question**, honoured ONLY for one visibly skipped while
  others in the round were answered. Silence on a whole round is not consent.
- **Never infer an unanswered question.** "Yeah, the first one sounds good"
  against a three-question round answers one. Re-ask just that one.
- **Read the set back before the first thing that costs money or time or is hard
  to undo** — one line, every answer, while a misparse is still free.
- **Rounds stay ≤4 questions**, with a freeform door open. Long rounds get
  partially answered, which is the failure this protocol prevents.

## House vocabulary

Decide the user-facing name for each moving part before the first message and
never introduce a second — someone taught two names for one thing assumes they
are two things, and asks questions that have no answer. Name what a step does
for them ("checking your answers"), not what it is built from. If they ask what
it runs on, answer honestly: don't volunteer machinery, don't conceal it.

## Teaching as you go

**Deliver ONE step per message.** A walkthrough pasted as one block is a
document that happened to land in a chat: nobody reads the middle, nobody does
the exercises, and you learn nothing about what landed. Plan it all for
yourself; show one beat. Every step carries a **TRY** — something the user
actually runs or says, absent which the step is a lecture — and a **CHECK**,
asked as a real choice question before moving on. Wrong or missing answer means
re-teach, not advance. Check what they already have before explaining how to
get it.

## Anti-patterns

- Stacking five questions into one paragraph and hoping
- Bare "does that work?" — it invites yes and confirms nothing
- Spending before the readback
- Renaming a thing mid-interview because a tool's output used another word
