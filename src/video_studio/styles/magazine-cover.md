---
name: magazine-cover
description: Cover-line serif, black and white with one red
---

# magazine-cover

A masthead-sized serif over the shot, small tracked cover-lines beneath it,
and a single red for the one thing that matters. Everything else is black,
white, or the footage.

Reach for it on a launch, a lookbook, an announcement — a piece with one
subject and one claim, where the restraint is the message. It is a poor fit
for anything with several equal points to make: the whole composition assumes
one line is larger than the rest, and three cover-lines of the same weight
just look unfinished.

Captions are uppercase, small and widely spaced, so they read as a strapline
rather than as subtitles. If the piece is actually narrated end to end, use a
preset whose captions are built to be read continuously — at this size and
spacing, four pages of them is work.

```json
{
  "captions": {
    "color": "#ffffff",
    "highlight": "#e11d48",
    "fontFamily": "Fraunces, Didot, Georgia, serif",
    "stroke": "#111111",
    "strokeWidth": 3,
    "fontSize": 40,
    "uppercase": true,
    "bounce": 1,
    "wiggle": 0,
    "wordsPerPage": 3,
    "wordGap": 0.3,
    "bottom": 0.1
  },
  "cards": {
    "title": {
      "bg": "#ffffff",
      "fg": "#111111",
      "fontSize": 190,
      "align": "center",
      "tracking": -0.04,
      "rect": [
        0.06,
        0.3,
        0.88,
        0.3
      ],
      "fade": {
        "in": 0.6,
        "out": 0.4
      },
      "fontFamily": "Bodoni Moda, Didot, Georgia, serif"
    },
    "label": {
      "bg": "#111111",
      "fg": "#ffffff",
      "fontSize": 22,
      "align": "center",
      "tracking": 0.24,
      "rect": [
        0.2,
        0.64,
        0.6,
        0.05
      ],
      "fade": {
        "in": 0.4,
        "out": 0.3
      },
      "fontFamily": "Inter, Helvetica, sans-serif"
    },
    "stat": {
      "bg": "#e11d48",
      "fg": "#ffffff",
      "fontSize": 44,
      "align": "center",
      "tracking": 0.02,
      "rect": [
        0.24,
        0.72,
        0.52,
        0.1
      ],
      "fade": {
        "in": 0.4,
        "out": 0.3
      },
      "fontFamily": "Bodoni Moda, Didot, Georgia, serif"
    }
  }
}
```
