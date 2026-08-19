# BrandOrigin — 30-second origin short

How a brand or company got from what it was to what it is, in about 30
seconds, vertical. Derived from a formula observed four times in a reference
gallery: *"<Brand> origin short: How X went from A to B, with <visual motif>
in 30 seconds."* Four uses of one shape is a format, not a one-off.

## Composition
Vertical 1080x1920 @30fps. Five to six scenes, 4-6s each. Every visual scene
is a full-frame still carrying a `ken` drift — the era changes, the camera
keeps moving. One recurring **motif** (an object, a shape, a material) appears
in every era so the eye has a through-line. Captions on. One narrator voice.
Era labels are composer `card` layers, never generated text.

## Interview
Round 1 — header "Subject": Which brand or company, and what's the one
transformation the short is about? (from-X-to-Y in a sentence)
Round 2 — header "Motif": What object recurs through every era? (the shoe,
the chip, the cup — it's the visual spine)
Round 3 — header "Eras": Three to four turning points, oldest first. What
changed at each?
Round A — header "Audio": Score (supply a file / generate / none)?
Voice (built-in / supplied recording / none)? If generating the score, say
which backend and its rights terms before they choose, not after.
Round L — header "Look": Which caption/card preset — `styles.py --list`?
Any look they describe should be saved with `styles.py --save`.
Freeform: tone, and anything that must NOT be implied (endorsement, claims).

## Slots
`era-N` still per scene, `label-N` card (era + year), narration per scene.

## Grammar
- **Hook** (4-5s): the motif alone, present day, no context. Narration poses
  the transformation as a question or a flat surprising fact.
- **Era beats** (3-4 x 5-6s): oldest to newest. Each names its year on a card
  and shows the motif *in that era's world*. Alternate `ken` zoom direction
  and pan between consecutive scenes so cuts don't move identically.
- **Landing** (5-6s): the motif today, narration closing the loop opened by
  the hook. No CTA — this format is editorial, not an ad.
- Keep it factual and attributable. State what happened; don't characterise
  motives or imply the brand endorses the video.

## Render notes
Stills + `ken` is the whole visual language here, which makes it the cheapest
format we have (~$0.02/scene generated, or free from stock). Generate video
only if an era genuinely needs motion. Never ask the generator for logos,
signage, or years — those are cards.
