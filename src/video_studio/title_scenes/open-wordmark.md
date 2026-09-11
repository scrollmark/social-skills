---
name: open-wordmark
description: The wordmark alone, centre frame, for the first two seconds
seconds: 2
---

# open-wordmark

The opening card. One `title` layer and nothing else, held long enough to read
and short enough that a viewer who already knows the channel is not waiting.

It carries no style of its own. A title scene is a LAYOUT, and every preset in
this library can wear it — `tourism` renders it as a wordmark on brand colour,
`analog-editorial` as type on paper. Binding one layout to one look would mean
authoring this file twenty-nine times, and would make "open this in the look
the video already uses" impossible to ask for.

**Two seconds is the whole argument.** A title that outstays it is the most
common reason a recap loses its first viewer: the shape of the video is not yet
visible, so there is nothing to stay for. If the wordmark needs longer, it
needs a shot behind it, which is a different scene.

The words are the scene's. `heading` is what the layer says, and no preset may
supply it.

```json
{
  "seconds": 2,
  "layers": [
    { "role": "title" }
  ]
}
```
