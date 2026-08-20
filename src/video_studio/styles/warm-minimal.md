---
name: warm-minimal
description: Cream/brown, lifestyle and editorial
---

# warm-minimal

Cream/brown, lifestyle and editorial. Ported from the showrunner style set, which described a whole design
system — a six-step type scale, a spacing scale, motion curves. Only the parts
this studio renders survived the translation: caption styling, three card roles,
and the music mood so `music_catalog --pick` can choose a bed that matches.

Motion curves and the spacing scale were dropped rather than faked; nothing here
reads them, and a value nothing reads is a value that drifts.

```json
{
  "captions": {
    "color": "#292524",
    "highlight": "#d97706",
    "fontFamily": "Fraunces",
    "fontSize": 28,
    "stroke": "#faf5f0",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#faf5f0",
      "fg": "#292524",
      "fontSize": 84,
      "align": "left",
      "tracking": -0.02
    },
    "label": {
      "bg": "#b45309",
      "fg": "#292524",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.12
    },
    "stat": {
      "bg": "#d97706",
      "fg": "#faf5f0",
      "fontSize": 132,
      "align": "center",
      "tracking": -0.03
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
    "bpm": 92,
    "fps": 30
  }
}
```
