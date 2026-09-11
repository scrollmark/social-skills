---
name: chapter-break
description: A number and a name, for the cut between sections
seconds: 1.5
---

# chapter-break

The card that says where you are. A `stat` layer for the number and a `title`
layer for the section name, in that order — the number is the backdrop and the
name draws over it.

Shorter than the opening card on purpose. A chapter break is read in transit;
it is punctuation, not a scene. At two seconds it starts to feel like the video
has stopped.

Use it when the format has named sections — `daily-recap` and `how-to` both do.
Do not use it to pad a video that has one continuous thought: a break between
nothing and nothing reads as a mistake.

```json
{
  "seconds": 1.5,
  "layers": [
    { "role": "stat" },
    { "role": "title" }
  ]
}
```
