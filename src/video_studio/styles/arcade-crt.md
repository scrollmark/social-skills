---
name: arcade-crt
description: Phosphor green pixels, Press Start over VT323
---

# arcade-crt

A pixel face at title size and a terminal face for everything else, in the
green a CRT actually emitted, on black. Captions are uppercase and monospaced
so they read as output rather than as subtitles.

Reach for it on games, builds, benchmarks, anything with a score or a number
going up. It is a costume on a lifestyle clip, and the pixels turn to mush
over busy footage — this look wants dark, simple frames or a flat colour.

Press Start 2P is enormously wide: eight characters fill a phone frame. Keep
titles to one short word and trust the explicit `fontSize` here rather than
the automatic sizing, which is calibrated to Inter and will overshoot badly.

```json
{
  "captions": {
    "color": "#39ff14",
    "highlight": "#ffffff",
    "fontFamily": "VT323, ui-monospace, monospace",
    "stroke": "#03170a",
    "strokeWidth": 6,
    "fontSize": 64,
    "uppercase": true,
    "bounce": 1,
    "wiggle": 0,
    "wordsPerPage": 4,
    "wordGap": 0.18,
    "bottom": 0.12
  },
  "cards": {
    "title": {
      "bg": "transparent",
      "fg": "#39ff14",
      "fontFamily": "Press Start 2P, ui-monospace, monospace",
      "fontSize": 72,
      "align": "center",
      "tracking": 0.02,
      "rect": [
        0.04,
        0.4,
        0.92,
        0.2
      ],
      "fade": {
        "in": 0.15,
        "out": 0.15
      }
    },
    "label": {
      "bg": "#03170a",
      "fg": "#39ff14",
      "fontFamily": "VT323, ui-monospace, monospace",
      "fontSize": 40,
      "align": "center",
      "tracking": 0.08,
      "rect": [
        0.2,
        0.1,
        0.6,
        0.06
      ],
      "fade": {
        "in": 0.15,
        "out": 0.15
      }
    },
    "stat": {
      "bg": "#39ff14",
      "fg": "#03170a",
      "fontFamily": "Press Start 2P, ui-monospace, monospace",
      "fontSize": 56,
      "align": "center",
      "tracking": 0,
      "rect": [
        0.14,
        0.7,
        0.72,
        0.1
      ],
      "fade": {
        "in": 0.15,
        "out": 0.15
      }
    }
  }
}
```
