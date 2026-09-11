---
name: weekend-gothic
description: Blackletter vermilion over neon, with a caps kicker
---

# weekend-gothic

One blackletter word in vermilion, a short line of letterspaced caps under it,
and captions that shout in Inter rather than competing with the title's face.

Reach for it on night footage — bars, gigs, wet streets, neon. The face carries
so much personality that the rest of the frame has to stay plain: the kicker is
Inter on purpose, and a second gothic word anywhere in the same video undoes the
whole thing.

Blackletter is near-unreadable at caption size and in long strings. Use it for
one or two words that the viewer recognises as a shape, never for a sentence,
and never for anything a viewer actually has to read to follow the video.

```json
{
  "captions": {
    "color": "#f6efe3",
    "highlight": "#e5342a",
    "fontFamily": "Inter, Helvetica, sans-serif",
    "stroke": "#0a0a0a",
    "strokeWidth": 7,
    "fontSize": 52,
    "uppercase": true,
    "bounce": 1.1,
    "wiggle": 0,
    "wordsPerPage": 3,
    "wordGap": 0.2,
    "bottom": 0.14
  },
  "cards": {
    "title": {
      "bg": "transparent",
      "fg": "#e5342a",
      "fontFamily": "Pirata One, UnifrakturMaguntia, Georgia, serif",
      "weight": 400,
      "fontSize": 150,
      "align": "center",
      "tracking": 0.01,
      "rect": [
        0.05,
        0.4,
        0.9,
        0.2
      ],
      "fade": {
        "in": 0.25,
        "out": 0.2
      }
    },
    "label": {
      "bg": "transparent",
      "fg": "#f6efe3",
      "fontFamily": "Inter, Helvetica, sans-serif",
      "weight": 800,
      "fontSize": 30,
      "align": "center",
      "tracking": 0.3,
      "rect": [
        0.1,
        0.58,
        0.8,
        0.05
      ],
      "fade": {
        "in": 0.2,
        "out": 0.2
      }
    }
  }
}
```
