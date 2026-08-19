# TimelineExplainer — numbered walk through a history

A sequence of numbered beats moving through time: a discography, a
leadership history, a company's decade. Distinct from BrandOrigin in that the
*list* is the point — viewers are counting along — and it runs longer.

## Composition
16:9 1080p @30fps (9:16 works; cards get tighter). Six to ten scenes, 5-7s
each. Each beat opens on its number as a `card`, then reveals a still. The
number card is the format's signature — same position, same style, every
beat, so the count is legible at a glance. Captions on.

## Interview
Round 1 — header "Subject": What history, and how many beats? (6-10; more
than 10 wants a longer format)
Round 2 — header "Beats": For each: the year/number, the one-line fact, and
what we'd see.
Round 3 — header "Arc": What's the through-line the last beat should land?
Round A — header "Audio": Score (supply a file / generate / none)?
Voice (built-in / supplied recording / none)? If generating the score, say
which backend and its rights terms before they choose, not after.
Round L — header "Look": Which caption/card preset — `styles.py --list`?
Any look they describe should be saved with `styles.py --save`.
Freeform: tone, and any claim that needs care.

## Slots
`num-N` card (number + year), `still-N` visual, narration per beat.

## Grammar
- **Cold open** (4s): the arc's end state as a question. No number.
- **Beats** (6-10 x 5-7s): number card enters first (`atMs` ~0, `pop`), still
  underneath with `ken`. Narration is one fact per beat — resist two.
- **Landing** (5-6s): answers the cold open. Card, no still.
- Numbers, years, and names are cards. Stills carry mood, not information.
- Keep facts checkable and neutrally stated; this format invites strong claims
  and shouldn't make them.

## Render notes
The most card-heavy format we have — good stress test of whether card layers
can carry a video rather than accent one. If a still adds nothing to a beat,
use a card alone on a flat background; an honest text beat beats a decorative
image.
