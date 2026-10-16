---
skill: editor-motion-graphics
---

## Prompt

The Scrollmark editor is open with a 40-second vertical UGC clip: a creator holding a face mask, saying "I'm Priya, and I've used this mask every night for a month" at 0:02 and "it was thirty-two dollars, and this week it's twenty-four" at 0:21. Add her name, and make the price drop stand out.

## Without skill (baseline)

The agent tries `graphics.addTitleCard` or `graphics.addText`, which the editor refuses, then tells the user titles are coming soon. Or it adds a hook title at the start that nobody asked for, and spells the price from the transcript.

## With skill (expected)

The agent reads the transcript, then calls `media_generate` twice in one round with `kind: "motion"`: an overlay name tag at about 1.8 s for about 4 s with `exact_strings: ["Priya"]`, and an overlay price moment at about 20.8 s for about 5 s with `exact_strings: ["$32", "$24"]`. Each `prompt` says what the moment is and its words, not fonts or colours. It says both graphics are on the way and doesn't claim they are placed. When they finish, it confirms in one line without placing them again.

## Behavioral markers

- [ ] Uses `media_generate` with `kind: "motion"`, never the template title or text commands
- [ ] One call per moment, with `at_s` at the line it belongs to
- [ ] Puts the name and both prices in `exact_strings`
- [ ] Adds no title or hook that wasn't asked for
- [ ] Doesn't say the graphics are on the timeline until `[generation finished]` arrives, and doesn't place them again
