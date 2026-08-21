---
name: warm-minimal
description: Cream/brown, lifestyle and editorial
---

# warm-minimal

Cream/brown, lifestyle and editorial. This preset carries only what the
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
