---
name: tech-startup
description: Dark/indigo/pink, modern SaaS aesthetic
---

# tech-startup

Dark/indigo/pink, modern SaaS aesthetic. This preset carries only what the
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
    "color": "#fafafa",
    "highlight": "#ec4899",
    "fontFamily": "Inter",
    "fontSize": 28,
    "stroke": "#18181b",
    "strokeWidth": 3,
    "bottom": 0.12,
    "wordsPerPage": 4
  },
  "cards": {
    "title": {
      "bg": "#18181b",
      "fg": "#fafafa",
      "fontSize": 84,
      "align": "left",
      "tracking": -0.03
    },
    "label": {
      "bg": "#6366f1",
      "fg": "#fafafa",
      "fontSize": 22,
      "align": "left",
      "tracking": 0.08
    },
    "stat": {
      "bg": "#ec4899",
      "fg": "#18181b",
      "fontSize": 132,
      "align": "center",
      "tracking": -0.04
    }
  },
  "music": {
    "moods": [
      "energetic",
      "corporate",
      "uplifting"
    ]
  },
  "rhythm": {
    "bpm": 124,
    "fps": 30
  }
}
```
