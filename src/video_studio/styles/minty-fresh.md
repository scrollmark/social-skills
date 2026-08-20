---
name: minty-fresh
description: Mint green + cream, cheerful product marketing
---

# minty-fresh

Mint green + cream, cheerful product marketing. Ported from the showrunner style set, which described a whole design
system — a six-step type scale, a spacing scale, motion curves. Only the parts
this studio renders survived the translation: caption styling, three card roles,
and the music mood so `music_catalog --pick` can choose a bed that matches.

Motion curves and the spacing scale were dropped rather than faked; nothing here
reads them, and a value nothing reads is a value that drifts.

```json
{
  "captions": {
    "color": "#064e3b",
    "highlight": "#f59e0b",
    "fontFamily": "Inter",
    "fontSize": 28,
    "stroke": "#f4faf5",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#f4faf5",
      "fg": "#064e3b",
      "fontSize": 84,
      "align": "left",
      "tracking": -0.02
    },
    "label": {
      "bg": "#10b981",
      "fg": "#064e3b",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.1
    },
    "stat": {
      "bg": "#f59e0b",
      "fg": "#f4faf5",
      "fontSize": 132,
      "align": "center",
      "tracking": -0.03
    }
  },
  "music": {
    "moods": [
      "uplifting",
      "playful",
      "gentle"
    ]
  },
  "rhythm": {
    "bpm": 118,
    "fps": 30
  }
}
```
