---
name: chrome-y2k
description: Nabla's colour chrome, which paints its own palette
---

# chrome-y2k

Nabla is a colour font: its glyphs carry their own gradient, a bevelled chrome
that looks like a 1999 CD-ROM menu. The card's `fg` does nothing to it — the
face paints itself — which is the one thing to know before using it.

Reach for it on tech, nostalgia, anything knowingly retro-futuristic. Because
the title brings its own palette, everything around it is deliberately
monochrome: white captions, a near-black kicker, no third colour.

Set it on a dark frame. The chrome's highlights are pale, and on a bright
background the whole word disappears into the picture.

```json
{
  "captions": {
    "color": "#f8fafc",
    "highlight": "#a5f3fc",
    "fontFamily": "Inter, Helvetica, sans-serif",
    "stroke": "#09090b",
    "strokeWidth": 7,
    "fontSize": 52,
    "uppercase": true,
    "bounce": 1,
    "wiggle": 0,
    "wordsPerPage": 3,
    "wordGap": 0.2,
    "bottom": 0.12
  },
  "cards": {
    "title": {
      "bg": "transparent",
      "fg": "#ffffff",
      "fontFamily": "Nabla, Impact, sans-serif",
      "fontSize": 140,
      "align": "center",
      "tracking": 0.02,
      "rect": [
        0.04,
        0.36,
        0.92,
        0.22
      ],
      "fade": {
        "in": 0.3,
        "out": 0.25
      }
    },
    "label": {
      "bg": "#09090b",
      "fg": "#f8fafc",
      "fontFamily": "Inter, Helvetica, sans-serif",
      "weight": 700,
      "fontSize": 28,
      "align": "center",
      "tracking": 0.3,
      "rect": [
        0.14,
        0.62,
        0.72,
        0.05
      ],
      "fade": {
        "in": 0.25,
        "out": 0.2
      }
    }
  }
}
```
