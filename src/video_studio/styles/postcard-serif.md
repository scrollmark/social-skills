---
name: postcard-serif
description: Didone masthead with a hairline-tracked strapline
---

# postcard-serif

A place name across the top in a high-contrast serif, a strapline under it in
caps tracked almost to the point of falling apart, and a condensed block low in
the frame for whatever the piece is called.

Reach for it on travel, city, arrival — anywhere the location is the subject.
It is built for footage with sky or street at the top of the frame; over a
close-up the masthead has nothing to sit on and the whole postcard reads as a
watermark.

The 0.42 tracking on the strapline is not a typo. At that spacing four or five
words is the ceiling — write the line to fit rather than tightening it.

```json
{
  "captions": {
    "color": "#fdfdfb",
    "highlight": "#d9b26a",
    "fontFamily": "Inter, Helvetica, sans-serif",
    "stroke": "#1a1a18",
    "strokeWidth": 5,
    "fontSize": 56,
    "uppercase": true,
    "bounce": 1,
    "wiggle": 0,
    "wordsPerPage": 4,
    "wordGap": 0.26,
    "bottom": 0.11
  },
  "cards": {
    "title": {
      "bg": "transparent",
      "fg": "#fdfdfb",
      "fontFamily": "Prata, Playfair Display, Didot, serif",
      "weight": 400,
      "fontSize": 196,
      "align": "center",
      "tracking": 0.0,
      "rect": [
        0.06,
        0.1,
        0.88,
        0.14
      ],
      "fade": {
        "in": 0.7,
        "out": 0.5
      }
    },
    "label": {
      "bg": "transparent",
      "fg": "#fdfdfb",
      "fontFamily": "Inter, Helvetica, sans-serif",
      "weight": 600,
      "fontSize": 22,
      "align": "center",
      "tracking": 0.42,
      "rect": [
        0.2,
        0.24,
        0.6,
        0.04
      ],
      "fade": {
        "in": 0.6,
        "out": 0.4
      }
    },
    "stat": {
      "bg": "transparent",
      "fg": "#fdfdfb",
      "fontFamily": "Bebas Neue, Inter, sans-serif",
      "weight": 400,
      "fontSize": 56,
      "align": "left",
      "tracking": 0.06,
      "rect": [
        0.07,
        0.74,
        0.5,
        0.08
      ],
      "fade": {
        "in": 0.5,
        "out": 0.35
      }
    }
  }
}
```
