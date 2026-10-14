---
name: editor-camera-directing
description: Use when adding zooms, pans or Ken Burns moves to a Scrollmark editor video, or a first recut that should feel directed rather than static.
---

# Editor Camera Directing

## Requires

A running Scrollmark editor whose commands you can call: the SocialGPT editor chat, or `scrollmark mcp` from `@scrollmark/cli` for a coding agent. Without it the moves can't be applied; the rule for when a move is earned holds in any editor.

## Directing, not a quota

This is directing, not a one-zoom quota and not a move on every clip.

Find beats in this order:

1. Transcript — punchlines, reveals, "look at this," named objects, joke landings.
2. The project's `semanticBrief` scenes (in the project snapshot) — silent B-roll, gestures, look-aways, props.
3. `media_inspectSourceFrames` at 1–3 file seconds on those candidates. After apply, `preview_inspectFrames` at the timeline seconds.

A move only if the line is motivated **and** the subject (or a face, for a joke beat) is in the picture. If inspect cannot show it, skip. Several moves per video is fine. No count cap.

## Applying a move

`element_applyCameraMove` on video/image only. Named kinds: `zoom_in` / `zoom_out` / `pan_left` / `pan_right` / `tilt_up` / `tilt_down`. Default `amount` 0.15. `startS`/`endS` are clip-local and cover the beat, not the whole take.

Stills/B-roll that would sit dead get a slow Ken Burns (`zoom_in` or a pan) over the hold. Talking-head: punch in on the beat; do not Ken Burns the entire speech. Match pan/tilt to where the subject is. Never `element_setParams` for motion (that clears camera keys). To take a move off a clip without undoing other edits, `element_clearCameraMove`.

Do not: a move on every keep-range; filmstrip the whole tape; animate captions/stickers.
