---
name: editor-looks
description: Use when a Scrollmark editor user names a Library filter (Moody, Latte, Vintage…) or asks for a look or mood in the colour (warm, moody, cinematic, film, brighter).
---

# Editor Looks

## Requires

A running Scrollmark editor whose commands you can call: the SocialGPT editor chat, or `scrollmark mcp` from `@scrollmark/cli` for a coding agent. Without it the filters can't be applied; the rules for choosing a look hold in any editor.

## Always a Library filter

A look, grade or mood ("warm", "moody", "cinematic", "brighter", a filter by name) is a Library filter from the table below, applied with `library.apply`. Do not build one with `effects.add` and a custom `look` (`warm-film`, `teal-orange`); use those only for an effect the Library has no filter for (blur, vignette, chroma key).

A whole restyle of a video they have worked on ("make it cinematic", "a new look") follows `editor-versions` first, which may make it a new version; then apply the filter there.

## One look for the video

A look is a grade for the whole video, not a per-clip effect. Put the same filter on every clip of the main footage (one `library.apply` op per clip, in one plan) so shots match. Only a single clip when they point at one ("make the second shot moody").

Never stack two filters on one clip: a second filter replaces the first.

## Picking a filter

`library.list` (through `editor_read`, `category: "filters"`) lists them with `id` and a short description.

| They ask for | Filter |
|---|---|
| warm, cosy, golden | `latte` (creamy warm), `jade` (teal & warm) for travel |
| moody, cinematic, dark | `moody` (dark teal), `jade` (teal & warm) for a teal-and-orange film look |
| brighter, airy, clean | `bright` (airy, lifted), `clear` (clean punch) |
| film, vintage, retro | `vintage` (faded film) |
| black and white, cold | `lunar` (cold mono) |
| skin, beauty, flattering | `skin` (soft tone) |
| food | `foodie` |
| graphic, bold colour | `duo` (duotone) — only when asked; it changes every colour |

A named filter is that `id`. A vague "make it look better" on a talking head is `skin` or `clear`, not a stylised look.

## Strength

The default strength (0.7, `duo` 0.85, `lunar` 0.8) is what a click gives. Faces: keep `moody`, `vintage` and `lunar` at 0.5–0.6 so skin does not go grey or green; pass `strength` (0–1). "A bit warmer" is 0.4–0.5. Do not go above the default unless they ask for stronger.

## Applying

Plan op `library.apply` with `id` and `elementId` (a video or image clip; describe handles work), optional `strength`. `library.remove` with `id` and `elementId` takes it off. The snapshot shows it as a `lut` effect whose `look` is `social-<id>`. After applying, check one frame with `preview_inspectFrames` that faces still look natural.

Do not: a filter on only some shots of a sequence; stacking filters; a custom `look` effect for a mood the table covers.
