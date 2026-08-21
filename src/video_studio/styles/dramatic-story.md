---
name: dramatic-story
description: Black/gold/red, cinematic storytelling
---

# dramatic-story

Black/gold/red, cinematic storytelling. This preset carries only what the
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
