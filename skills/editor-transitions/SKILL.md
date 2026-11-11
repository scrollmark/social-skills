---
name: editor-transitions
description: Use when a Scrollmark editor user names a Library transition, asks for transitions, or asks to make the cuts flow. Not for jump cuts inside one talking-head take.
---

# Editor Transitions

## Requires

A running Scrollmark editor whose commands you can call: the SocialGPT editor chat, or `scrollmark mcp` from `@scrollmark/cli` for a coding agent. Without it the transitions can't be applied; the rules for which cut earns one hold in any editor.

## Library style or plain crossfade

- A named style, "make the cuts flow", "smooth the cuts" or any styled transition: `library.apply` with a catalog `id`.
- Only when their words are "crossfade", "dissolve" or "fade (to black)": `timeline.addTransition` with `type` (`dissolve`, `dip-to-black`). Every other ask, including "flow", "smooth" and "transitions", is a Library style: pick a family below, even when a dissolve seems safe.

Both work on a cut with no spare footage: they trim a little off each clip to make room, the same way the editor's UI does.

## Which cuts

A transition marks a change: a new shot, a new place, a new section, the drop in a montage. Most cuts stay hard cuts.

- Montage or B-roll between shots: transitions on the cuts that change scene or land on a beat, not on every cut. "Make the cuts flow" is two to four cuts on a 30 s video, one family throughout.
- Talking head: never on the jump cuts inside one take (a dissolve on a jump cut reads as a mistake). Only where B-roll comes in or a new section starts.
- A named transition goes exactly on the cut they named. If the cut is unclear, take the one nearest the playhead or the selected clip and say which one you used.

## Picking a style

`library.list` (through `editor_read`, `category: "transitions"`) lists every preset with its `id`, `family`, `base` and `durationS`. A name the user says maps to the `id` (Glass Shatter → `glass-shatter`).

Match the content, and keep **one family per video**:

| Content | Family | Examples |
|---|---|---|
| Calm, lifestyle, beauty, travel | Air, Liquid | `soft-breath`, `smoke-dissolve`, `liquid-melt`, `ink-bleed` |
| Energetic montage, sport, product hype | Impact, Zoom | `whip-pan`, `impact-zoom`, `whip-zoom`, `spin-zoom` |
| Music, beat drops | Impact, Modern | `beat-drop`, `strobe-cut`, `glitch-cut` (on the beat only) |
| Tech, gaming, retro | Modern, Glass | `chroma-sweep`, `vhs-tear`, `prism-split` |
| Nostalgic, film look | Classic | `film-burn`, `light-leak` |

Flash and punch styles (`strobe-cut`, `glitch-cut`, `earthquake`) are for one or two moments, never a whole edit.

## Applying

One plan op per cut: `library.apply` with `id` and `fromElementId`, the clip **before** the cut (a describe handle works). It trims into the clips' spare media the same way a click in the Library does, and a second preset on the same cut replaces the first (`replaced: true`). `library.remove` with `fromElementId` takes one off. The snapshot lists each one under `transitions` with its `catalogId`.

Do not: a transition on every cut; mix families; transitions on the jump cuts of a single take; a plain dissolve when they did not ask for one by name.
