---
skill: editor-beat-sync
---

## Prompt

The Scrollmark editor is open with six travel shots on the main track and a music track below them. Cut the shots to the beat. Also put the "Summer trip" title in on the beat.

## Without skill (baseline)

The agent reads beat times itself and moves every clip by hand, one command per clip, or trims each shot to an equal length. It may move the title onto any beat, or try to snap a main-track clip and get refused.

## With skill (expected)

The agent uses one plan: a `beatCut` op with the six clip handles in play order and the music clip, leaving `every` at its default so each shot keeps about its length in whole beats; then a `snapToBeat` op on the title with `to: "downbeat"`. It tells the user the tempo and how many beats each shot runs. If the music had no steady beat it would say so and offer another track.

## Behavioral markers

- [ ] Uses `beatCut` with the clips in play order and the music clip
- [ ] Leaves `every` at `"auto"` unless asked for faster cuts
- [ ] Uses `snapToBeat` with `to: "downbeat"` for the title
- [ ] Reports the tempo and beats per shot
- [ ] Does not read beat times and move clips by hand
