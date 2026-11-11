---
skill: editor-library-fx
---

## Prompt

The Scrollmark editor is open with a 40-second talking-head video, one long take with a few jump cuts and one B-roll product shot at 0:18. There are no captions and no music. Make it pop.

## Without skill (baseline)

The agent piles effects onto the talking head: shake or glitch on several clips, a `zoom.slowpush` across the whole take, and a filter on top. Or it answers with a single zoom and nothing else. Either way the video itself is no tighter or clearer.

## With skill (expected)

The agent treats it as a request for the whole edit: it tightens the pacing, adds captions and music through those skills, and punches in on one or two strong lines with `element.applyCameraMove`. At most one Library accent on top, such as `zoom.quickin` on the short B-roll shot. It says what it changed and why.

## Behavioral markers

- [ ] Improves the edit itself (pacing, captions or music), not only effects
- [ ] At most two Library effects in total
- [ ] No `zoom.*` preset on the long talking-head take
- [ ] No glitch, shake or style effect on the speaker's face
- [ ] Explains each change
