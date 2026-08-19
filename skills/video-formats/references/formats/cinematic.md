# Cinematic — mood-driven montage

Atmospheric sequence cut to music: establishing shots, detail close-ups,
slow motion, minimal or no narration. Carnival/sports/travel energy.

## Composition
Vertical 1080x1920 @30fps. Full-frame `broll` per scene, hard cuts (or
brief cross-fades). A score is REQUIRED — supplied file or generated, either
works. Captions off by default.

## Interview
Round A — header "Audio": ASK THIS FIRST, before mood or arc. Score: supply a
file or generate one? If generating, name the backend and its rights terms
BEFORE they choose — every cut point ends up shaped around whichever track
arrives, so a rights problem discovered later means re-cutting the whole piece,
not re-tagging it. Voice: usually none here, but ask rather than assume.
Round 1 — header "Mood": What feeling? (tension/joy/awe/nostalgia) What's
the subject?
Round 2 — header "Arc": Build-up → peak → release: what is each, concretely?
Round L — header "Look": Which caption/card preset — `video-studio styles --list`?
Any look they describe should be saved with `video-studio styles --save`.
Freeform: references, shots you already know you want.

Do not ask the user where the drop is — MEASURE it. `measure --music` (bundled in `audio-acquisition`)
reports the real energy transitions. A remembered timestamp is off by enough to
miss a cut, and a freshly generated track has no timestamps to remember.

## Slots
`broll` per scene (4-8 scenes), `music` file, optional 1-2 spoken lines.

## Grammar
Scenes shorten toward the peak (6s → 2-3s), longest scene right after the
peak. Silent beats are silence (tts --silence), not filler narration. Cut
timing should land near music beats — note the drop time from the interview
and place the peak scene boundary there.

## Render notes

Every scene should carry a `ken` drift — alternate zoom in/out and pan
direction between scenes so consecutive shots don't move identically.
Slow-mo: request normal footage, play at 0.5x via composer playbackRate
(add to Video.tsx when first needed).
