---
skill: editor-versions
---

## Prompt

The Scrollmark editor is open with a 40-second recut product demo, captions and a calm acoustic music bed the agent added earlier. The user writes: "I don't like this music, it's too sleepy. Try something more techy."

## Without skill (baseline)

The agent swaps the bed in place for one new track and says it changed the music. The acoustic bed is gone unless the user undoes, and they cannot hear both. If they dislike the new one too, the loop repeats one track at a time.

## With skill (expected)

The agent treats this as a rejected attempt on the music. It lists the sequences with its first describe, copies the timeline as "Music: synth" and describes the copy in the same round, replaces the bed there in one plan, and answers in about four rounds: the new version is open, the original with the acoustic bed is still there, which it recommends and why, and an offer to make another (say, electronic pop).

## Behavioral markers

- [ ] Uses `sequences.duplicate` with a name that says what differs
- [ ] Calls `timeline_describe` after the copy, in the same round
- [ ] Makes one new version and keeps the original unchanged
- [ ] Does not look up the sequence commands
- [ ] Answers naming the version, that it is open, that the original is kept, a recommendation, and offers another
