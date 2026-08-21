---
name: 3b1b-dark
description: Navy/blue/gold, math education inspired by 3Blue1Brown
---

# 3b1b-dark

Navy/blue/gold, math education inspired by 3Blue1Brown. This preset carries
only what the composer actually renders: caption styling, three card roles, and
the music mood, so `music_catalog --pick` can choose a bed that matches the
look rather than fighting it.

It began as a fuller design system — a six-step type scale, a spacing scale,
motion curves. Those were dropped rather than translated into keys nothing
reads, because a value nothing reads is a value that drifts: it stays in the
file, stops matching the render, and misleads whoever edits it next.

```json
{
  "captions": {
    "color": "#ffffff",
    "highlight": "#facc15",
    "fontFamily": "Inter",
    "fontSize": 28,
    "stroke": "#1c1c2e",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#1c1c2e",
      "fg": "#ffffff",
      "fontSize": 84,
      "align": "left",
      "tracking": -0.02
    },
    "label": {
      "bg": "#3b82f6",
      "fg": "#ffffff",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.08
    },
    "stat": {
      "bg": "#facc15",
      "fg": "#1c1c2e",
      "fontSize": 128,
      "align": "center",
      "tracking": -0.03
    }
  },
  "music": {
    "moods": [
      "contemplative",
      "ambient",
      "gentle"
    ]
  },
  "rhythm": {
    "bpm": 96,
    "fps": 30
  }
}
```
