---
name: tourism
description: Place labels, stat cards and a wordmark — the destination-spot look
---

# tourism

The look used by the country spots: a saturated brand colour carrying white
labels, inverted for stat cards so a number reads as a fact rather than a
caption, and the wordmark held large in the centre for the open and close.

Four roles:

- `label` — a place name, bottom-left. Short strings only; `label-wide` exists
  because "PLAYA DEL CARMEN" in a `label` rect crushes the tracking.
- `stat` — cream on brand, for a number with a unit underneath.
- `title` — the wordmark, centre frame, for the open and the final chorus.
- `cta` — inverted title, for the closing line.

Swap the two colours and the whole system re-skins. The rects are shared, which
is the point: three spots built by hand drifted to three different label
heights for the same kind of label.

**On location labels:** this preset styles them, it does not license them. Only
put a place name on a shot whose source metadata names that place — stock search
returned a Hawaii temple for a Japanese query and a Colorado canyon for a
Mexican one in the same week this preset was written.

```json
{
  "captions": {
    "fontSize": 64,
    "stroke": "#000000",
    "strokeWidth": 8,
    "wordGap": 0.26,
    "wordsPerPage": 3,
    "uppercase": true,
    "bottom": 0.16
  },
  "cards": {
    "label": {
      "bg": "#be185d",
      "fg": "#fffbeb",
      "tracking": 0.14,
      "rect": [0.06, 0.775, 0.58, 0.085],
      "pop": true
    },
    "label-wide": {
      "bg": "#be185d",
      "fg": "#fffbeb",
      "tracking": 0.1,
      "rect": [0.06, 0.775, 0.74, 0.085],
      "pop": true
    },
    "stat": {
      "bg": "#fffbeb",
      "fg": "#be185d",
      "tracking": 0.1,
      "rect": [0.06, 0.735, 0.68, 0.135],
      "pop": true
    },
    "title": {
      "bg": "#be185d",
      "fg": "#fffbeb",
      "tracking": 0.18,
      "rect": [0.1, 0.38, 0.8, 0.22],
      "fade": { "in": 0.9, "out": 0.5 }
    },
    "cta": {
      "bg": "#fffbeb",
      "fg": "#be185d",
      "tracking": 0.08,
      "rect": [0.08, 0.38, 0.84, 0.22],
      "fade": { "in": 0.8 }
    }
  }
}
```
