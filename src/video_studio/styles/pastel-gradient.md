---
name: pastel-gradient
description: Lavender/purple, wellness and lifestyle
---

# pastel-gradient

Lavender/purple, wellness and lifestyle. This preset carries only what the
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
