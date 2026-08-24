---
name: loud-social
description: Big outlined per-word captions that survive a muted autoplay feed
---

# loud-social

For the feed, where most viewers never unmute. Captions carry the whole
message, so they are large, uppercase, cycled through a colour per word, and
outlined heavily enough to stay legible over any footage.

The two numbers that matter and are easy to get wrong:

- `wordsPerPage: 3` — at this size four words overrun the frame width on a
  1080-wide canvas. The default of 4 is tuned for smaller type.
- `wordGap: 0.34` — a thick stroke grows each word's visual box. At the default
  gap, outlined words at this size visibly merge into one another. Raise the
  gap whenever you raise the stroke.

Cards are deliberately plain here: when the captions are this loud, a styled
card competes with them instead of supporting them.

```json
{
  "captions": {
    "palette": ["#fde047", "#f472b6", "#38bdf8", "#4ade80"],
    "stroke": "#000000",
    "strokeWidth": 14,
    "fontSize": 88,
    "uppercase": true,
    "bounce": 1.16,
    "wiggle": 2,
    "wordsPerPage": 3,
    "wordGap": 0.34,
    "bottom": 0.2
  },
  "cards": {
    "label": {
      "bg": "#0f172a",
      "fg": "#f8fafc",
      "tracking": 0.12,
      "rect": [0.06, 0.06, 0.6, 0.08],
      "pop": true
    },
    "title": {
      "bg": "#0f172a",
      "fg": "#fde047",
      "tracking": 0.16,
      "rect": [0.08, 0.36, 0.84, 0.24],
      "fade": { "in": 0.6, "out": 0.4 }
    }
  }
}
```
