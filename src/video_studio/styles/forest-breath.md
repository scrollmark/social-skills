---
name: forest-breath
description: Sage green + off-white, grounded and calm
---

# forest-breath

Sage green + off-white, grounded and calm. This preset carries only what the
composer actually renders: caption styling, three card roles, and the music
mood, so `music_catalog --pick` can choose a bed that matches the look rather
than fighting it.

It began as a fuller design system — a six-step type scale, a spacing scale,
motion curves. Those were dropped rather than translated into keys nothing
reads, because a value nothing reads is a value that drifts: it stays in the
file, stops matching the render, and misleads whoever edits it next.

```json
{
  "captions": {
    "color": "#1a2e1f",
    "highlight": "#c19a6b",
    "fontFamily": "Inter",
    "fontSize": 28,
    "stroke": "#f5f5f0",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#f5f5f0",
      "fg": "#1a2e1f",
      "fontSize": 80,
      "align": "left",
      "tracking": -0.01
    },
    "label": {
      "bg": "#4a7c59",
      "fg": "#1a2e1f",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.14
    },
    "stat": {
      "bg": "#c19a6b",
      "fg": "#f5f5f0",
      "fontSize": 132,
      "align": "center",
      "tracking": -0.02
    }
  },
  "music": {
    "moods": [
      "gentle",
      "ambient",
      "warm",
      "contemplative"
    ]
  },
  "rhythm": {
    "bpm": 80,
    "fps": 30
  }
}
```
