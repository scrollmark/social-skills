---
name: sunny-editorial
description: Warm yellow + cream + charcoal, inviting long-form content
---

# sunny-editorial

Warm yellow + cream + charcoal, inviting long-form content. This preset carries
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
    "color": "#1c1917",
    "highlight": "#ea580c",
    "fontFamily": "Fraunces",
    "fontSize": 28,
    "stroke": "#fefae0",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#fefae0",
      "fg": "#1c1917",
      "fontSize": 84,
      "align": "left",
      "tracking": -0.02
    },
    "label": {
      "bg": "#d97706",
      "fg": "#1c1917",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.12
    },
    "stat": {
      "bg": "#ea580c",
      "fg": "#fefae0",
      "fontSize": 140,
      "align": "center",
      "tracking": -0.03
    }
  },
  "music": {
    "moods": [
      "warm",
      "uplifting",
      "editorial"
    ]
  },
  "rhythm": {
    "bpm": 98,
    "fps": 30
  }
}
```
