---
name: analog-editorial
description: Warm film stock under fashion-magazine serifs
---

# analog-editorial

Cream-on-ink serif type over footage that is allowed to look photographed
rather than rendered. The reference is a magazine spread printed on uncoated
paper: generous letter-spacing on the cards, a caption face with real
contrast, and one warm accent that reads as a highlighter rather than a
notification badge.

Reach for it on travel, food, interiors, product-in-hand — anything where the
footage already has grain, warmth or shallow depth and the type's job is to
frame it. It is the wrong preset for a chart or a stat: a serif at this size
loses to a number that wants to be read fast.

Pair it with a `grain` effect layer at low intensity. Without one the type
looks like it was printed on the wrong stock — the whole look depends on the
picture having some texture of its own.

```json
{
  "captions": {
    "color": "#f4ece1",
    "highlight": "#e0a34a",
    "fontFamily": "Fraunces, Georgia, serif",
    "stroke": "#2b2118",
    "strokeWidth": 4,
    "fontSize": 46,
    "uppercase": false,
    "bounce": 1,
    "wiggle": 0,
    "wordsPerPage": 4,
    "wordGap": 0.14,
    "bottom": 0.14
  },
  "cards": {
    "title": {
      "bg": "#f4ece1",
      "fg": "#2b2118",
      "fontSize": 78,
      "align": "left",
      "tracking": 0.08,
      "rect": [
        0.08,
        0.34,
        0.84,
        0.24
      ],
      "fade": {
        "in": 0.8,
        "out": 0.5
      },
      "fontFamily": "Fraunces, Georgia, serif",
      "italic": true
    },
    "label": {
      "bg": "#2b2118",
      "fg": "#f4ece1",
      "fontSize": 24,
      "align": "left",
      "tracking": 0.16,
      "rect": [
        0.08,
        0.8,
        0.5,
        0.06
      ],
      "fade": {
        "in": 0.4,
        "out": 0.3
      },
      "fontFamily": "Inter, Helvetica, sans-serif"
    },
    "stat": {
      "bg": "#e0a34a",
      "fg": "#2b2118",
      "fontSize": 40,
      "align": "left",
      "tracking": 0.04,
      "rect": [
        0.08,
        0.72,
        0.56,
        0.12
      ],
      "fade": {
        "in": 0.4,
        "out": 0.3
      },
      "fontFamily": "Fraunces, Georgia, serif"
    }
  }
}
```
