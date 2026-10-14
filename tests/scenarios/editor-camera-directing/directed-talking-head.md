---
skill: editor-camera-directing
---

## Prompt

The Scrollmark editor is open with a recut 45-second talking head: a creator explaining a budgeting app, who holds up their phone to the camera at 0:18 and lands a joke at 0:31. Make it feel less static.

## Without skill (baseline)

The agent adds a slow zoom on every keep range, or one zoom over the whole clip, or a Ken Burns across the entire speech. It may animate the captions, or set position keyframes with `element_setParams`, which clears camera moves.

## With skill (expected)

The agent finds the motivated beats from the transcript (the phone reveal at 0:18, the joke at 0:31), checks with `media_inspectSourceFrames` that the phone and the face are in frame, then applies a punch-in with `element_applyCameraMove` (`zoom_in`, amount about 0.15) over each beat only, with clip-local `startS`/`endS`. It leaves the rest of the speech still.

## Behavioral markers

- [ ] Ties each move to a specific moment in the transcript
- [ ] Checks frames before adding a move
- [ ] Uses `element_applyCameraMove`, not `element_setParams`, for motion
- [ ] Does not put a move on every clip or Ken Burns the whole speech
- [ ] Does not animate captions or stickers
