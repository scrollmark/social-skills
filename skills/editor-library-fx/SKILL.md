---
name: editor-library-fx
description: Use when a Scrollmark editor user names a Library FX (Sway, Shake, Glitch, RGB split, Magnifying glass, a Zoom preset…) or asks for an effect such as shake, glitch, spotlight or blur on a clip. For zooms on a moment in a longer take, see editor-camera-directing.
---

# Editor Library FX

## Requires

A running Scrollmark editor whose commands you can call: the SocialGPT editor chat, or `scrollmark mcp` from `@scrollmark/cli` for a coding agent. Without it the effects can't be applied; the rules for when an effect is earned hold in any editor.

## Never on a long take

A Library effect or `zoom.*` preset runs over the **whole clip**. Never put one on a clip longer than about 6 seconds (a talking-head take, an interview, a song performance). For a moment in a long clip, use a camera move over the line (`element.applyCameraMove`), or split the clip and apply the effect to the short piece.

## An effect is an accent

Library FX run over the **whole clip** they sit on. Use them on short clips (a shot in a montage, a B-roll insert, a beat), and on one or two moments of a video, not as decoration. A named effect goes on the clip they named, and only that one.

A vague "make it pop" or "more exciting" is a request for the whole edit, not for effects. Do what lifts the video most, following those skills: tighten the pacing, add captions and music if it has none, and punch in on the strongest lines. Library effects are at most one or two accents on top, never the whole answer, and on a talking head usually none. Say what you changed and why.

## Picking an effect

`library.list` (through `editor_read`, `category: "fx"`) lists every effect with its `id`, `category` and description.

| Category | ids | Use for |
|---|---|---|
| Move | `sway`, `roll` | Playful energy on a short shot; `roll` is a full turn, for a transition beat only |
| Shake | `shake`, `bass`, `flutter`, `camerashake` | `shake`/`bass` on a drop or impact; `camerashake` for handheld feel on action |
| Glitch | `glitch`, `rgb` | Tech, gaming, a reveal; one shot, short |
| Mask | `circmask`, `rectmask`, `magnify`, `domemagnify`, `localmosaic` | Point at something (`magnify`, `circmask`); hide something (`localmosaic`) |
| Blur | `gaussianblur`, `tiltshift` | Background behind a title; miniature look |
| Style | `crtretro`, `asciirain` | Retro or code aesthetic, only when asked |
| Overlay | `blackoverlay` | Darken a shot so text on it reads |
| Zoom | `zoom.slowpush`, `zoom.slowpull`, `zoom.quickin`, `zoom.quickout`, `zoom.instant`, `zoom.inout` | A camera move across the whole clip |

## Zoom presets or a camera move

A `zoom.*` preset zooms across the **whole** clip. Use it when the clip is the moment (a short B-roll shot, a cut-in): `zoom.slowpush` for a still or calm shot, `zoom.quickin` / `zoom.instant` for a punch on a short cut.

For a moment inside a longer take ("push in when he says…"), do not put a preset on the whole take: use `element.applyCameraMove` with clip-local `startS`/`endS` around the line, as in `editor-camera-directing`.

## Applying

Plan op `library.apply` with `id` and `elementId` (a video or image clip; describe handles work). A clip holds one Library effect; a new one replaces it, and applying the same one again leaves it on (`alreadyApplied: true`). `library.remove` with `elementId` takes it off. The snapshot shows it as `libraryFx` on the clip, and `timeline_describe` as `fx`. To place an effect on a moment (from `startS` to `endS`) in a longer clip, cut that piece out in the same plan and apply to it by name. A split keeps the clip's id on the **left** piece, so split at `endS` first, then at `startS` with `"as"`, and apply to that name:

```json
[{ "op": "timeline.splitClip", "args": { "elementId": "c1", "time": 9.5 } },
 { "op": "timeline.splitClip", "args": { "elementId": "c1", "time": 7.5 }, "as": "$moment" },
 { "op": "library.apply", "args": { "id": "magnify", "elementId": "$moment" } }]
```

Applying to `c1` after those splits would put the effect on the piece before the moment.

Do not: an effect on every clip; effects on a talking head's face for a long stretch; glitch or shake on a calm or serious video unless asked; a `zoom.*` preset on a long take.
