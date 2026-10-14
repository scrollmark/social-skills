---
skill: editor-soundtrack
---

## Prompt

The Scrollmark editor is open with two clips: a 2-minute seated podcast conversation, and a 30-second product unboxing someone filmed at their desk. Make both feel more polished.

## Without skill (baseline)

The agent adds a music bed to both, or searches the stock library for "lo-fi" and gets drum loops. It builds the bed by hand (import, add clip, duck) and may tell the user it kept existing music when the track is new.

## With skill (expected)

The agent leaves music off the seated podcast and says why. For the unboxing it adds one `music` plan op with an instrumental vibe query such as "light pop background music", which finds, fits, fades and ducks the bed itself. It names the track it added and says the user can swap or remove it.

## Behavioral markers

- [ ] Does not add a music bed under the seated podcast
- [ ] Uses one `music` op rather than searching and importing a track by hand
- [ ] Writes the query as "<vibe> background music", not a bare genre
- [ ] Names the added track and offers to swap or remove it
