---
name: editor-sfx-sparse
description: Use when something arrives on screen in a Scrollmark editor video (B-roll in, a title, a punch line the user wants hit) or the user asks for sound design. Not for speech-only recuts or interviews, and never a whoosh per cut.
---

# Editor SFX Sparse

## Requires

A running Scrollmark editor whose commands you can call: the SocialGPT editor chat, or `scrollmark mcp` from `@scrollmark/cli` for a coding agent. Search and import go through the editor's Freesound catalog. Without it, the when-to-use rules and the class table still guide sparse sound design by hand.

## When

Load only when something is arriving (B-roll in, a title, a punch they asked to hit) or they asked for sound design. Speech-only recuts and interviews: do not place SFX.

## Search and place

`media_searchCatalog` `providerId: "freesound"`, `kind: "audio"`. Pass **`sfxRole`** only for chip roles: `hit` `whoosh` `riser` `reverse` `glitch` `foley` `ambience`. Do not invent roles (`downer` `stinger` `drone` `ui` `drop` `explosion` `impact` are not `sfxRole`). Extra query tokens AND; do not free-type "cinematic dark whoosh".

Import a `remoteId` from **that** search and place it at the **timeline** second of the event in the same plan: `media.importFromCatalog` with `"as": "$hit"`, then `timeline.addMediaClip` with `mediaId: "$hit"` and `"as": "$sfx"`, then `element.setParams` with `elementId: "$sfx"` and `params: { "volumePercent": 90 }` (**80–100**, still under voice). Keep hits short.

Do not: one whoosh per keep-range join; SFX on every word caption; a second bed via `ambience` or drone.

## Pinned defaults

When the picture needs this class, search as below and import this `remoteId` if it appears. If it does not, search again with the extra tokens. Do not invent a URL.

| Class | Search | Extra | remoteId | License |
|---|---|---|---|---|
| Cut / B-roll in | `sfxRole: whoosh` `durationClass: short` | `swosh` or `air` | `60030` | CC0 |
| Build into a reveal (peak within ~2–3s) | `sfxRole: riser` `durationClass: phrase` | `grain` | `561207` | CC0 |
| Settle / power-down after a peak | query `machine power down` (no role) | — | `422829` | CC-BY GameDevC (credit) |
| Rewind only if the picture earns it | `sfxRole: reverse` `durationClass: short` | `tape rewind` | `679970` | CC0 |
| Digital stutter / picture jump only if the picture earns it | `sfxRole: glitch` `durationClass: transient` | `massive` | `237607` | CC0 |

Glitch is not a record scratch. Analog rewind is the reverse pin.

## Agent picks (no default file)

Match the picture. Skip if it does not earn it. Tighten later.

| Class | When | Search |
|---|---|---|
| hit | Punch word, title slam, joke land | `sfxRole: hit` `transient` |
| impact | Same family as hit; heavier body | `sfxRole: hit` + `impact` |
| stinger | Title, logo, bumper, or they asked to sting a beat. Not a whoosh or hit | chips off: logo/title → `logo`; outro → `outro stinger`; else `stinger` (~1–3s) |
| drone | They asked for a tonal bed/hum. Never a second bed. Not room air | chips off `drone` (or ambience + `drone`), ~8–16s |
| foley | Picture shows the action (step, cloth, door). Skip talking-head with no object motion. Not a designed hit/whoosh | `sfxRole: foley` `short` + `footstep` / `cloth` / `door` (+ surface) |
| ambience | Room tone only if they asked. Never a music bed | `sfxRole: ambience` `phrase` + place (`roomtone`, `park`, `wind`) |
| ui | On-screen tap, click, or notification | chips off `click` / `ui` / `button` |
| drop | Beat drop they asked for. Not downer, not explosion | chips off `drop` |
| explosion | Picture explodes or they asked | `sfxRole: hit` + `explosion` |
