---
name: bold-neon
description: Black/cyan/pink, gaming and tech energy
---

# bold-neon

Black/cyan/pink, gaming and tech energy. Ported from the showrunner style set, which described a whole design
system — a six-step type scale, a spacing scale, motion curves. Only the parts
this studio renders survived the translation: caption styling, three card roles,
and the music mood so `music_catalog --pick` can choose a bed that matches.

Motion curves and the spacing scale were dropped rather than faked; nothing here
reads them, and a value nothing reads is a value that drifts.

```json
{
  "captions": {
    "color": "#ffffff",
    "highlight": "#e11d48",
    "fontFamily": "Inter",
    "fontSize": 28,
    "stroke": "#0a0a0a",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#0a0a0a",
      "fg": "#ffffff",
      "fontSize": 88,
      "align": "left",
      "tracking": -0.03
    },
    "label": {
      "bg": "#06b6d4",
      "fg": "#ffffff",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.1
    },
    "stat": {
      "bg": "#e11d48",
      "fg": "#0a0a0a",
      "fontSize": 140,
      "align": "center",
      "tracking": -0.04
    }
  },
  "music": {
    "moods": [
      "energetic",
      "aggressive",
      "uplifting"
    ]
  },
  "rhythm": {
    "bpm": 140,
    "fps": 30
  }
}
```
