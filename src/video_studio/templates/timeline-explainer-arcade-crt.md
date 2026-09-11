---
name: timeline-explainer-arcade-crt
description: Phosphor green pixels counting up, the way a score does.
---

# timeline-explainer-arcade-crt

Phosphor green pixels counting up, the way a score does.

`timeline-explainer` is the shape and `arcade-crt` is the look. The pairing is the thing
somebody actually picks: a format alone does not say what it looks like and a
style alone does not say how long it runs or how many scenes it wants.

Read `format/timeline-explainer` for the structure and `style/arcade-crt` for the treatment.
Both are in this pack, and applying this template applies the style and
surfaces the format as guidance -- a format's values are human ranges
("8-14 scenes", "1.5-3s"), and pretending to apply them mechanically would be
inventing a promise the format never made.

```json
{
  "formatRef": "format/timeline-explainer",
  "styleRef": "style/arcade-crt",
  "why": "Phosphor green pixels counting up, the way a score does."
}
```
