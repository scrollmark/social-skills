---
name: sunny-editorial
description: Warm yellow + cream + charcoal, inviting long-form content
---

# sunny-editorial

Warm yellow + cream + charcoal, inviting long-form content. Ported from the showrunner style set, which described a whole design
system — a six-step type scale, a spacing scale, motion curves. Only the parts
this studio renders survived the translation: caption styling, three card roles,
and the music mood so `music_catalog --pick` can choose a bed that matches.

Motion curves and the spacing scale were dropped rather than faked; nothing here
reads them, and a value nothing reads is a value that drifts.

```json
{
  "captions": {
    "color": "#1c1917",
    "highlight": "#ea580c",
    "fontFamily": "Fraunces",
    "fontSize": 28,
    "stroke": "#fefae0",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#fefae0",
      "fg": "#1c1917",
      "fontSize": 84,
      "align": "left",
      "tracking": -0.02
    },
    "label": {
      "bg": "#d97706",
      "fg": "#1c1917",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.12
    },
    "stat": {
      "bg": "#ea580c",
      "fg": "#fefae0",
      "fontSize": 140,
      "align": "center",
      "tracking": -0.03
    }
  },
  "music": {
    "moods": [
      "warm",
      "uplifting",
      "editorial"
    ]
  },
  "rhythm": {
    "bpm": 98,
    "fps": 30
  }
}
```
