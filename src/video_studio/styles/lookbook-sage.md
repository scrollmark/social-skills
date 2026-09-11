---
name: lookbook-sage
description: Sage and cream editorial, numbered like a lookbook
---

# lookbook-sage

Cream type over sage green, an italic serif title, and a running number in the
top corner — `01/12`, the same place every scene, so a sequence counts itself.

Reach for it on a collection, a series, a numbered walk through anything with an
order. The number card is the format's signature here; drop it and this becomes
a generic serif look.

The sage panel is used once, on the stat role, rather than behind every card.
Type on footage with a single coloured block is the composition; type on a block
in every scene is a slide deck.

```json
{
  "captions": {
    "color": "#efe4cd",
    "highlight": "#c9a227",
    "fontFamily": "Cormorant Garamond, Georgia, serif",
    "stroke": "#2f4a42",
    "strokeWidth": 5,
    "fontSize": 56,
    "uppercase": false,
    "bounce": 1,
    "wiggle": 0,
    "wordsPerPage": 4,
    "wordGap": 0.14,
    "bottom": 0.12
  },
  "cards": {
    "title": {
      "bg": "transparent",
      "fg": "#efe4cd",
      "fontFamily": "Bodoni Moda, Didot, Georgia, serif",
      "italic": false,
      "weight": 400,
      "fontSize": 168,
      "align": "center",
      "tracking": -0.01,
      "rect": [
        0.06,
        0.34,
        0.88,
        0.22
      ],
      "fade": {
        "in": 0.6,
        "out": 0.4
      }
    },
    "label": {
      "bg": "transparent",
      "fg": "#efe4cd",
      "fontFamily": "Inter, Helvetica, sans-serif",
      "weight": 500,
      "fontSize": 24,
      "align": "center",
      "tracking": 0.22,
      "rect": [
        0.06,
        0.08,
        0.24,
        0.04
      ],
      "fade": {
        "in": 0.4,
        "out": 0.3
      }
    },
    "stat": {
      "bg": "#5f8b7c",
      "fg": "#efe4cd",
      "fontFamily": "Playfair Display, Georgia, serif",
      "weight": 600,
      "fontSize": 48,
      "align": "center",
      "tracking": 0.02,
      "rect": [
        0.1,
        0.68,
        0.8,
        0.14
      ],
      "fade": {
        "in": 0.5,
        "out": 0.35
      },
      "italic": true
    }
  }
}
```
