# PipStory — shrinking-host narrative (script-driven)

One continuous host presence: full-frame for direct-address beats, easing into
a corner inset over supporting b-roll for concrete/numeric beats, easing back
before every cut so scene changes land full-frame-to-full-frame. Proven
grammar (taxonomy 5.1 + the coffee/phone/library/meal-prep demos).

## Composition
Vertical 1080x1920 @30fps. Layers per scene: optional `broll` (full-frame
base) + `host` (rect `[0.58,0.58,0.42,0.42]`, enter/exit tweens 0.4s from/to
full). Captions on. Voices: storyteller + short-reaction cohost.

## Interview
Round 1 — header "Script": Do you have a script, or should we write one
together? (Have a file / Draft from a topic / Dictate now)
Round 2 — header "Host": Use an existing host take pool, generate a new host
look (describe them), or supply your own footage?
Round 3 — header "Numbers": Which concrete facts/numbers must land on screen?
(These become composer text overlays — never generation-prompt text.)
Round A — header "Audio": Score (supply a file / generate / none)?
Voice (built-in / supplied recording / none)? If generating the score, say
which backend and its rights terms before they choose, not after.
Round L — header "Look": Which caption/card preset — `styles.py --list`?
Any look they describe should be saved with `styles.py --save`.
Freeform: anything else about tone, pacing, platform?

## Slots
`host` (pool takes keyed by mood: talking/listening/surprised/smiling),
`broll` per pip beat (object/scene shots, NO readable text), narration beats.

## Grammar
Segment script into 10-30-word beats. `pip` ONLY where narration cites
something showable (number, bill, object, place); 25-50% of beats. Cohost
lines ≥3 real words, never bare interjections. Exact figures render as
composer overlays (StatCard-style), not in footage.

## Render notes
Host identity: same actual take files across all beats (pool), not repeated
descriptors. B-roll durations: loop/trim in composer to measured narration.
