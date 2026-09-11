---
name: neon-sign
description: Monoton tube lettering in hot pink over night
---

# neon-sign

Monoton is drawn as a struck neon tube — parallel strokes with a gap down the
middle — so at size it reads as a sign rather than as type. Hot pink title,
cyan kicker, captions in something legible because the tube face is not.

Reach for it at night: bars, venues, streets, anything already lit. In
daylight there is nothing for it to be a sign against and it just looks like a
novelty font.

One word, centred, big. Monoton has no bold and no italic — weight and lean do
nothing to it, and the tube reads as broken if you crowd two lines together.

```json
{
  "captions": {
    "color": "#fdf4ff",
    "highlight": "#22d3ee",
    "fontFamily": "Inter, Helvetica, sans-serif",
    "stroke": "#160b1a",
    "strokeWidth": 7,
    "fontSize": 50,
    "uppercase": true,
    "bounce": 1.06,
    "wiggle": 0,
    "wordsPerPage": 3,
    "wordGap": 0.22,
    "bottom": 0.13
  },
  "cards": {
    "title": {
      "bg": "transparent",
      "fg": "#ff2fa8",
      "fontFamily": "Monoton, Impact, sans-serif",
      "fontSize": 172,
      "align": "center",
      "tracking": 0.02,
      "rect": [
        0.05,
        0.36,
        0.9,
        0.22
      ],
      "fade": {
        "in": 0.4,
        "out": 0.3
      }
    },
    "label": {
      "bg": "transparent",
      "fg": "#22d3ee",
      "fontFamily": "Inter, Helvetica, sans-serif",
      "weight": 800,
      "fontSize": 30,
      "align": "center",
      "tracking": 0.34,
      "rect": [
        0.1,
        0.6,
        0.8,
        0.05
      ],
      "fade": {
        "in": 0.3,
        "out": 0.25
      }
    }
  }
}
```
