# Boil — hand-drawn outlined motion graphics

Wiggly single-weight vector line art over flat colour, with typography set
directly on it. No photography, no generated video, no licence attached to
anything on screen. Reach for it when the subject can't be photographed —
an unreleased product, a service, an abstract idea — or when stock footage
would look borrowed.

## Composition
16:9 1080p @30fps (9:16 works unchanged; art is centred by `--pos`). Five to
seven scenes, 5-6s each. Every scene is a flat background with ONE drawn
shape and at most one text block. Captions off — the type on screen is the
type, and captions would double it.

## Interview
Round 1 — header "Subject": What is it, and what are the three things worth
saying about it?
Round 2 — header "Marks": For each beat, what object stands for it? Keep it
iconic — a hand, a spark, a bridge, a lock. First run `video-studio gen_boil --list`.
If the vocabulary is too rigid, create `boil_shapes.py` in the project and
pass it with `--shape-file`; do not squeeze the idea into an unrelated built-in
mark.
Round 3 — header "Palette": Background and line colour per beat. Two colours
per scene, no gradients. By default the card `fg` matches the line colour used
for that scene's mark; only break this when the user explicitly asks for a
contrast exception.
Freeform: exact wording for the end card.

## Slots
`<scene>-still` boil clip, one `card` per beat, narration optional.

## Grammar
- **Hook** (5-6s): one abstract mark, no text. `rings` or `arrow`.
- **Reveal** (5-6s): the subject named, on the inverted palette — if the deck
  is dark, this beat is paper. The flip is what makes it land.
- **Beats** (3 x 5-6s): one mark, one card, one idea. Mark right, text left
  (or the reverse) — NEVER overlapping. See render notes.
- **Landing** (5s): the quietest mark, name and one line.
- One shape per scene. Two marks on screen reads as a diagram, not a beat.

## Render notes
- Generate art with `video-studio gen_boil`, one clip per scene. Match
  `--seconds` to `plannedSeconds` EXACTLY: a short clip either loops
  (visible seam) or freezes.
- Custom marks live beside the storyboard, usually `project/boil_shapes.py`.
  Define functions named `s_<name>(d, c, rng, w, p, cx, cy, s)` and call the
  injected helpers `wob`, `circle`, and `box`. Then render with
  `--shape-file project/boil_shapes.py --shape <name>`. Keep functions short:
  one iconic outline, no fill, no text, no second object.
  Example:

  ```python
  def s_heart(d, c, rng, w, p, cx, cy, s):
      pts = []
      for i in range(80):
          t = math.tau * i / 79
          x = 16 * math.sin(t) ** 3
          y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
          pulse = 1 + 0.04 * math.sin(p * math.tau)
          pts.append((cx + x * s * 0.025 * pulse, cy + y * s * 0.025 * pulse))
      wob(d, pts, c, rng, w, 2.8)
  ```
- `--hold 3` is the default and the right answer. Hold 1 is video noise;
  hold 6+ reads as a stutter, not a drawing.
- **Set every card `flat: true` and `bg: "transparent"`.** `flat` drops
  the rounded corner and the drop shadow; without it a transparent card
  still draws a floating grey panel. Do NOT match `bg` to the background
  hex instead — the art is h264, so its background is only approximately
  that value and an exact fill shows as a faint patch.
- Check contrast per scene. The inverted reveal beat is where white type
  gets set on paper and vanishes; the palette flips but card `fg` does not
  follow automatically.
- Match text and mark colour by default. For Boil, the card is part of the
  same drawn poster as the mark, not a separate caption layer; mismatched text
  and line colours read as accidental unless the user asked for that contrast.
- Keep the mark and the card in different halves of the frame. The composer
  will happily stack them, and a card over the drawing is the one thing that
  makes this style look cheap.
- Deterministic: same `--seed` gives the same jitter. Re-rendering a scene
  after an edit will not reshuffle the boil.
