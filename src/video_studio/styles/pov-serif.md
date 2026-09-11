---
name: pov-serif
description: A workhorse serif set mid-frame, said quietly
---

# pov-serif

Small serif lines sitting in the middle of the frame rather than along the
bottom, in near-white with a thin dark outline. A sturdier face than a
display serif: this is meant to read as a thought typed over the picture, not
as a masthead.

Reach for it on the `pov:` register -- a held moment, a memory, anything whose
effect is that it is understated. Three or four lines is the ceiling; it is a
caption pretending to be a sentence, and a paragraph mid-frame is a wall.

Georgia is named first on purpose: it was drawn for screens at small sizes,
which is exactly the job here, and it is installed nearly everywhere so the
fallback rarely fires.

```json
{
  "captions": {
    "color": "#f7f5f2",
    "highlight": "#e4d9c6",
    "fontFamily": "Georgia, EB Garamond, serif",
    "stroke": "#14120f",
    "strokeWidth": 3,
    "fontSize": 40,
    "uppercase": false,
    "bounce": 1,
    "wiggle": 0,
    "wordsPerPage": 5,
    "wordGap": 0.12,
    "bottom": 0.44
  },
  "cards": {
    "title": {
      "bg": "transparent",
      "fg": "#f7f5f2",
      "fontFamily": "Georgia, EB Garamond, serif",
      "italic": true,
      "weight": 400,
      "fontSize": 58,
      "align": "center",
      "tracking": 0,
      "rect": [
        0.12,
        0.42,
        0.76,
        0.16
      ],
      "fade": {
        "in": 1.0,
        "out": 0.8
      }
    },
    "label": {
      "bg": "transparent",
      "fg": "#f7f5f2",
      "fontFamily": "Inter, Helvetica, sans-serif",
      "weight": 500,
      "fontSize": 20,
      "align": "center",
      "tracking": 0.2,
      "rect": [
        0.3,
        0.88,
        0.4,
        0.04
      ],
      "fade": {
        "in": 0.6,
        "out": 0.5
      }
    }
  }
}
```
