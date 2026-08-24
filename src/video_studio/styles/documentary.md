---
name: documentary
description: Restrained ink-on-cream captions and quiet lower-thirds
---

# documentary

For pieces where the footage is the argument and the type stays out of its way.
One flat colour rather than a per-word palette, no bounce, no wiggle, a thin
stroke that exists only to hold the words off a busy background.

Use it for explainers, histories and anything narrated in earnest. The
temptation on a serious subject is to reach for the loud preset because it
"performs better" — it also makes a piece about something difficult look like
an advert.

Cards sit as lower-thirds rather than centre-frame, so a name or a date can
appear without interrupting the shot.

```json
{
  "captions": {
    "color": "#f8fafc",
    "highlight": "#fbbf24",
    "stroke": "#0f172a",
    "strokeWidth": 5,
    "fontSize": 54,
    "uppercase": false,
    "bounce": 1,
    "wiggle": 0,
    "wordsPerPage": 5,
    "wordGap": 0.18,
    "bottom": 0.12
  },
  "cards": {
    "label": {
      "bg": "#0f172a",
      "fg": "#f8fafc",
      "tracking": 0.06,
      "rect": [0.06, 0.8, 0.62, 0.075],
      "fade": { "in": 0.4, "out": 0.3 }
    },
    "stat": {
      "bg": "#fef3c7",
      "fg": "#78350f",
      "tracking": 0.04,
      "rect": [0.06, 0.76, 0.6, 0.12],
      "fade": { "in": 0.4, "out": 0.3 }
    },
    "title": {
      "bg": "#0f172a",
      "fg": "#f8fafc",
      "tracking": 0.1,
      "rect": [0.1, 0.4, 0.8, 0.2],
      "fade": { "in": 1.0, "out": 0.6 }
    }
  }
}
```
