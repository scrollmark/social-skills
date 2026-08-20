---
name: clean-corporate
description: White/blue, professional business presentations
---

# clean-corporate

White/blue, professional business presentations. Ported from the showrunner style set, which described a whole design
system — a six-step type scale, a spacing scale, motion curves. Only the parts
this studio renders survived the translation: caption styling, three card roles,
and the music mood so `music_catalog --pick` can choose a bed that matches.

Motion curves and the spacing scale were dropped rather than faked; nothing here
reads them, and a value nothing reads is a value that drifts.

```json
{
  "captions": {
    "color": "#1e293b",
    "highlight": "#059669",
    "fontFamily": "Inter",
    "fontSize": 28,
    "stroke": "#ffffff",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#ffffff",
      "fg": "#1e293b",
      "fontSize": 84,
      "align": "left",
      "tracking": -0.03
    },
    "label": {
      "bg": "#2563eb",
      "fg": "#1e293b",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.08
    },
    "stat": {
      "bg": "#059669",
      "fg": "#ffffff",
      "fontSize": 128,
      "align": "center",
      "tracking": -0.04
    }
  },
  "music": {
    "moods": [
      "corporate",
      "warm",
      "uplifting"
    ]
  },
  "rhythm": {
    "bpm": 112,
    "fps": 30
  }
}
```
