---
name: wet-paint
description: Dripping letters, lime on black, loud on purpose
---

# wet-paint

A title face whose letters drip, a fat rounded face for the kicker, and lime
against black. Nothing here is subtle and nothing here is trying to be.

Reach for it on food, drops, sales, chaos — anything where the point is energy
rather than information. Avoid it on anything sincere: drips read as a joke,
and a joke under a serious line is worse than a plain caption.

The drips need room underneath or they collide with the next line, which is
why the title sits high in the frame. Keep it to one or two words; a long
string of dripping letters stops being readable at all.

```json
{
  "captions": {
    "color": "#eaff00",
    "highlight": "#ffffff",
    "fontFamily": "Inter, Helvetica, sans-serif",
    "stroke": "#0b0b0b",
    "strokeWidth": 9,
    "fontSize": 58,
    "uppercase": true,
    "bounce": 1.18,
    "wiggle": 2,
    "wordsPerPage": 3,
    "wordGap": 0.2,
    "bottom": 0.15
  },
  "cards": {
    "title": {
      "bg": "transparent",
      "fg": "#eaff00",
      "fontFamily": "Rubik Wet Paint, Impact, sans-serif",
      "fontSize": 190,
      "align": "center",
      "tracking": 0.01,
      "rect": [
        0.05,
        0.26,
        0.9,
        0.2
      ],
      "fade": {
        "in": 0.2,
        "out": 0.15
      }
    },
    "label": {
      "bg": "#0b0b0b",
      "fg": "#eaff00",
      "fontFamily": "Bagel Fat One, Impact, sans-serif",
      "fontSize": 44,
      "align": "center",
      "tracking": 0.04,
      "rect": [
        0.16,
        0.52,
        0.68,
        0.08
      ],
      "fade": {
        "in": 0.2,
        "out": 0.15
      }
    }
  }
}
```
