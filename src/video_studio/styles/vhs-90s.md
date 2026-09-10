---
name: vhs-90s
description: Tape-deck monospace, cyan and magenta on near-black
---

# vhs-90s

Uppercase monospace captions with an outline thick enough to survive any
frame, a cyan label bar, and a magenta title. The look borrows from a camera's
own on-screen display rather than from a design system, which is why the type
is a typewriter mono and the tracking is wide: it is meant to read as burned in by the
device, not laid on afterwards.

Reach for it on skate, gig, night-out and behind-the-scenes footage — anything
handheld, underexposed or a bit rough. The roughness is the point. On clean,
well-lit product footage it reads as a costume.

The 8px stroke is doing real work here and should not be trimmed: the palette
is high-saturation, and saturated type on saturated footage is unreadable
without an outline. `wiggle` is on, low, because a tape image never sat
perfectly still.

```json
{
  "captions": {
    "color": "#f8fafc",
    "highlight": "#22d3ee",
    "fontFamily": "Courier New, ui-monospace, Menlo, monospace",
    "stroke": "#0b0b0f",
    "strokeWidth": 8,
    "fontSize": 62,
    "uppercase": true,
    "bounce": 1.08,
    "wiggle": 1,
    "wordsPerPage": 3,
    "wordGap": 0.22,
    "bottom": 0.16
  },
  "cards": {
    "title": {
      "bg": "#0b0b0f",
      "fg": "#ff3ea5",
      "fontSize": 84,
      "align": "left",
      "tracking": 0.18,
      "rect": [0.06, 0.38, 0.88, 0.22],
      "fade": { "in": 0.3, "out": 0.2 }
    },
    "label": {
      "bg": "#22d3ee",
      "fg": "#0b0b0f",
      "fontSize": 26,
      "align": "left",
      "tracking": 0.1,
      "rect": [0.06, 0.06, 0.44, 0.06],
      "fade": { "in": 0.2, "out": 0.2 }
    }
  }
}
```
