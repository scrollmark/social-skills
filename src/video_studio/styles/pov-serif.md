---
name: pov-serif
description: A workhorse serif set mid-frame, said quietly
---

# pov-serif

Small serif lines sitting in the middle of the frame rather than along the
bottom, in near-white with a thin dark outline. A sturdier face than a
display serif: this is meant to read as a thought typed over the picture, not
as a masthead.

Small, not tiny. At 3% of the frame the line was unreadable on a phone and
invisible in a grid of thumbnails, which is a different thing from quiet --
the reference this comes from sets a line you can read at arm's length.

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
    "strokeWidth": 4,
    "fontSize": 48,
    "uppercase": false,
    "bounce": 1,
    "wiggle": 0,
    "wordsPerPage": 5,
    "wordGap": 0.12,
    "bottom": 0.30
  },
  "cards": {
    "title": {
      "bg": "transparent",
      "fg": "#f7f5f2",
      "fontFamily": "Georgia, EB Garamond, serif",
      "italic": true,
      "weight": 400,
      "fontSize": 88,
      "align": "center",
      "tracking": 0,
      "rect": [
        0.1,
        0.38,
        0.8,
        0.24
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
