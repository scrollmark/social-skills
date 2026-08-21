---
name: clean-corporate
description: White/blue, professional business presentations
---

# clean-corporate

White/blue, professional business presentations. This preset carries only what
the composer actually renders: caption styling, three card roles, and the music
mood, so `music_catalog --pick` can choose a bed that matches the look rather
than fighting it.

It began as a fuller design system — a six-step type scale, a spacing scale,
motion curves. Those were dropped rather than translated into keys nothing
reads, because a value nothing reads is a value that drifts: it stays in the
file, stops matching the render, and misleads whoever edits it next.

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
