---
skill: editor-sfx-sparse
---

## Prompt

The Scrollmark editor is open with a talking-head recut that has nine jump cuts, plus one B-roll shot of a city skyline at 0:12 and a title that appears at 0:00. Add some sound design.

## Without skill (baseline)

The agent puts a whoosh on every jump cut, adds a hit under several caption words, and free-types searches like "cinematic dark whoosh" or invents roles such as `stinger` or `impact`. It may add an ambience track that acts as a second music bed.

## With skill (expected)

The agent places sounds only where something arrives: a short whoosh as the B-roll comes in at 0:12 and one stinger or hit as the title lands. It searches Freesound with `sfxRole` chip roles only, prefers the pinned `remoteId`s when they appear, and sets volume around 80–100 so the sounds stay under the voice. It leaves the jump cuts silent.

## Behavioral markers

- [ ] No SFX on the jump cuts between keep ranges
- [ ] Sounds placed only at the B-roll entrance and the title
- [ ] Uses only the listed `sfxRole` values, never an invented role
- [ ] Sets `volumePercent` between 80 and 100
- [ ] Does not add an ambience or drone bed nobody asked for
