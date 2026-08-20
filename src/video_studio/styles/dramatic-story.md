---
name: dramatic-story
description: Black/gold/red, cinematic storytelling
---

# dramatic-story

Black/gold/red, cinematic storytelling. Ported from the showrunner style set, which described a whole design
system — a six-step type scale, a spacing scale, motion curves. Only the parts
this studio renders survived the translation: caption styling, three card roles,
and the music mood so `music_catalog --pick` can choose a bed that matches.

Motion curves and the spacing scale were dropped rather than faked; nothing here
reads them, and a value nothing reads is a value that drifts.

```json
{
  "captions": {
    "color": "#f8fafc",
    "highlight": "#dc2626",
    "fontFamily": "Inter",
    "fontSize": 28,
    "stroke": "#0f172a",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#0f172a",
      "fg": "#f8fafc",
      "fontSize": 96,
      "align": "left",
      "tracking": -0.02
    },
    "label": {
      "bg": "#f59e0b",
      "fg": "#f8fafc",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.15
    },
    "stat": {
      "bg": "#dc2626",
      "fg": "#0f172a",
      "fontSize": 144,
      "align": "center",
      "tracking": -0.03
    }
  },
  "music": {
    "moods": [
      "cinematic",
      "tense",
      "dark"
    ]
  },
  "rhythm": {
    "bpm": 72,
    "fps": 30
  }
}
```
