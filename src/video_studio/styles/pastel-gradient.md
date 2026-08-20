---
name: pastel-gradient
description: Lavender/purple, wellness and lifestyle
---

# pastel-gradient

Lavender/purple, wellness and lifestyle. Ported from the showrunner style set, which described a whole design
system — a six-step type scale, a spacing scale, motion curves. Only the parts
this studio renders survived the translation: caption styling, three card roles,
and the music mood so `music_catalog --pick` can choose a bed that matches.

Motion curves and the spacing scale were dropped rather than faked; nothing here
reads them, and a value nothing reads is a value that drifts.

```json
{
  "captions": {
    "color": "#1e1b4b",
    "highlight": "#ec4899",
    "fontFamily": "Inter",
    "fontSize": 28,
    "stroke": "#f5f0ff",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#f5f0ff",
      "fg": "#1e1b4b",
      "fontSize": 84,
      "align": "left",
      "tracking": -0.01
    },
    "label": {
      "bg": "#8b5cf6",
      "fg": "#1e1b4b",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.12
    },
    "stat": {
      "bg": "#ec4899",
      "fg": "#f5f0ff",
      "fontSize": 128,
      "align": "center",
      "tracking": -0.02
    }
  },
  "music": {
    "moods": [
      "gentle",
      "ambient",
      "warm"
    ]
  },
  "rhythm": {
    "bpm": 88,
    "fps": 30
  }
}
```
