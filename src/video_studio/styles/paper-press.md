---
name: paper-press
description: Cream + black + red, newspaper editorial
---

# paper-press

Cream + black + red, newspaper editorial. Ported from the showrunner style set, which described a whole design
system — a six-step type scale, a spacing scale, motion curves. Only the parts
this studio renders survived the translation: caption styling, three card roles,
and the music mood so `music_catalog --pick` can choose a bed that matches.

Motion curves and the spacing scale were dropped rather than faked; nothing here
reads them, and a value nothing reads is a value that drifts.

```json
{
  "captions": {
    "color": "#0a0a0a",
    "highlight": "#b91c1c",
    "fontFamily": "Inter",
    "fontSize": 28,
    "stroke": "#f8f4ed",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#f8f4ed",
      "fg": "#0a0a0a",
      "fontSize": 92,
      "align": "left",
      "tracking": -0.03
    },
    "label": {
      "bg": "#111111",
      "fg": "#0a0a0a",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.18
    },
    "stat": {
      "bg": "#b91c1c",
      "fg": "#f8f4ed",
      "fontSize": 150,
      "align": "center",
      "tracking": -0.04
    }
  },
  "music": {
    "moods": [
      "editorial",
      "warm",
      "contemplative"
    ]
  },
  "rhythm": {
    "bpm": 108,
    "fps": 30
  }
}
```
