# ProductLaunch — 30-40 second launch spot

Hero product, three capability beats, logo landing. The single most common
archetype in the reference gallery (11 of 48) and the one with the shortest
prompts, because the shape is so well established.

## Composition
16:9 1080p by default (ask; 9:16 for social-first). Five to seven scenes.
Hero shots are stills with a slow `ken` push. Capability beats pair a still
with a `card` naming the capability. End card is pure typography — product
name, one line, URL. Captions on. One narrator voice, confident and dry.

## Interview
Round 1 — header "Product": What is it, and what does it let someone do that
they couldn't before? (one sentence, no adjectives)
Round 2 — header "Beats": The three capabilities worth 6 seconds each.
Round 3 — header "Landing": Exact product name, closing line, and URL — these
render as real typography, so give them to me exactly as they should appear.
Round A — header "Audio": Score (supply a file / generate / none)?
Voice (built-in / supplied recording / none)? If generating the score, say
which backend and its rights terms before they choose, not after.
Round L — header "Look": Which caption/card preset — `styles.py --list`?
Any look they describe should be saved with `styles.py --save`.
Freeform: brand colours, tone, anything to avoid.

## Slots
`hero` still, `beat-N` still + card (N=3), `endcard` card, narration.

## Grammar
- **Hook** (4-5s): the product, tight, unexplained. Narration states the
  problem it removes — not the product's name.
- **Reveal** (4-5s): wider, product named for the first time.
- **Beats** (3 x 5-6s): one capability each. Card carries the capability in
  <=4 words; narration carries the sentence. Never both saying the same words.
- **Landing** (4-5s): typography only, held long enough to read twice.
- One idea per scene. If a beat needs two sentences, it's two beats.

## Render notes
Real product? Use supplied photography (`file:`) — generators invent details
and get logos wrong. Fictional product? Stills are fine. Product name and URL
are ALWAYS cards; a generator will misspell them.
