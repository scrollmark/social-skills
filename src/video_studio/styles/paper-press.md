---
name: paper-press
description: Cream + black + red, newspaper editorial
---

# paper-press

Cream + black + red, newspaper editorial. This preset carries only what the
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
    "color": "#0a0a0a",
    "highlight": "#b91c1c",
    "fontFamily": "Inter",
    "fontSize": 28,
    "stroke": "#f8f4ed",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#f8f4ed",
      "fg": "#0a0a0a",
      "fontSize": 92,
      "align": "left",
      "tracking": -0.03
    },
    "label": {
      "bg": "#111111",
      "fg": "#0a0a0a",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.18
    },
    "stat": {
      "bg": "#b91c1c",
      "fg": "#f8f4ed",
      "fontSize": 150,
      "align": "center",
      "tracking": -0.04
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
    "bpm": 108,
    "fps": 30
  }
}
```
