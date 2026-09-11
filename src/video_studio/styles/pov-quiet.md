---
name: pov-quiet
description: Small italic serif set mid-frame, almost whispered
---

# pov-quiet

Captions in a small italic serif sitting near the middle of the frame rather
than at the bottom, in cream on a thin dark outline. Nothing shouts.

Reach for it on the `pov:` register — a held moment, a memory, a piece whose
whole effect is that it is understated. It is the opposite of a mute-proof
preset: the type is small and the contrast is gentle, so it assumes a viewer who
is already watching.

`bottom: 0.42` is what puts the line mid-frame. That is where it competes most
with the subject, which is the intent — this look reads as a thought over the
picture rather than a subtitle beneath it. Keep the pages long (six words) so it
reads as a sentence, not as karaoke.

```json
{
  "captions": {
    "color": "#fbfaf7",
    "highlight": "#e7d7bd",
    "fontFamily": "EB Garamond, Cormorant Garamond, Georgia, serif",
    "stroke": "#141210",
    "strokeWidth": 4,
    "fontSize": 48,
    "uppercase": false,
    "bounce": 1,
    "wiggle": 0,
    "wordsPerPage": 6,
    "wordGap": 0.12,
    "bottom": 0.42
  },
  "cards": {
    "title": {
      "bg": "transparent",
      "fg": "#fbfaf7",
      "fontFamily": "EB Garamond, Cormorant Garamond, Georgia, serif",
      "italic": true,
      "weight": 500,
      "fontSize": 62,
      "align": "center",
      "tracking": 0.0,
      "rect": [
        0.12,
        0.44,
        0.76,
        0.12
      ],
      "fade": {
        "in": 1.0,
        "out": 0.8
      }
    },
    "label": {
      "bg": "transparent",
      "fg": "#fbfaf7",
      "fontFamily": "Inter, Helvetica, sans-serif",
      "weight": 500,
      "fontSize": 20,
      "align": "center",
      "tracking": 0.2,
      "rect": [
        0.3,
        0.88,
        0.4,
        0.04
      ],
      "fade": {
        "in": 0.6,
        "out": 0.5
      }
    }
  }
}
```
