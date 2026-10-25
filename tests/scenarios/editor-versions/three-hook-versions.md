---
skill: editor-versions
---

## Prompt

The Scrollmark editor is open with a 23-second TikTok cut of a talking head, with one-word captions and a ducked music bed the agent added earlier. The user writes: "make 3 versions of the hook as separate sequences: a question hook, a cold open, and a bold statement".

## Without skill (baseline)

The agent either copies the timeline three times and stops, leaving three identical sequences, or edits one copy per few rounds and runs out of rounds after two. It describes a version by what it meant to do, so a "cold open" that only dropped a pause is reported as reordered.

## With skill (expected)

The agent describes the timeline with its transcript and picks the opening line for each hook. In its next response it calls `sequences.branch` three times from that one description, each with one plan: a `recut` that lists the hook's line first; the music bed follows the new end. The one it recommends goes last with `open: true`. It answers in three rounds, from the branch results, naming each version by the line it now opens on and what moved, says which is open, and recommends one. If the speaker never asks a question, it says so instead of relabelling another cut.

## Behavioral markers

- [ ] Makes all three versions with `sequences.branch` in one response, from one description
- [ ] Never copies with `sequences.duplicate` and edits the copy
- [ ] Every version opens on a different line; the cold open moves a later line to the front with one `recut`, ranges in play order
- [ ] Opens the recommended version with `open: true` on its branch call, not a separate switch
- [ ] Describes each version from its branch result, in three rounds
