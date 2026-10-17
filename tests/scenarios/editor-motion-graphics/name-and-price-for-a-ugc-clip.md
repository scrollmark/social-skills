---
skill: editor-motion-graphics
---

## Prompt

The Scrollmark editor is open with a 40-second vertical UGC clip: a creator holding a face mask, saying "I'm Priya, and I've used this mask every night for a month" at 0:02 and "it was thirty-two dollars, and this week it's twenty-four" at 0:21. Add her name, and make the price drop stand out.

## Without skill (baseline)

The agent tries `graphics.addTitleCard` or `graphics.addText`, which the editor refuses, then tells the user titles are coming soon. Or it adds a hook title at the start that nobody asked for, and spells the price from the transcript.

## With skill (expected)

The agent reads the transcript. It adds her name as a lower third with `graphics.addLowerThird` (name "Priya", at about 1.8 s) in a plan, since a plain name needs no designed graphic. In the same round it calls `media_generate` with `kind: "motion"` for the price: an overlay at about 20.8 s for about 5 s with `exact_strings: ["$32", "$24"]`, and a `prompt` that says what the moment is and its words, not fonts or colours. It says the price graphic is on the way and doesn't claim it is placed. When it finishes, it confirms in one line without placing it again.

## Behavioral markers

- [ ] Adds the name with `graphics.addLowerThird`, not a motion graphic
- [ ] Uses `media_generate` with `kind: "motion"` for the price, never the template title or text commands
- [ ] Puts both prices in `exact_strings`, with `at_s` at the line they belong to
- [ ] Adds no title or hook that wasn't asked for
- [ ] Doesn't say the price graphic is on the timeline until `[generation finished]` arrives, and doesn't place it again
