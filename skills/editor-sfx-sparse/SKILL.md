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

`media_searchCatalog` `providerId: "freesound"`, `kind: "audio"`. Pass **`sfxRole`** only for chip roles: `hit` `whoosh` `riser` `reverse` `glitch` `foley` `ambience` `ui`. Do not invent roles (`pop` `click` `downer` `stinger` `drone` `drop` `explosion` `impact` are not `sfxRole`). Extra query tokens AND; do not free-type "cinematic dark whoosh".

A sound the user names (mouse click, cork pop, ding, notification, camera shutter) is `sfxRole: "ui"` with the name as `query` (`"cork pop"`): the role adds no word of its own and only returns sounds of 0.3 s or more, long enough to hear over a voice.

Import a `remoteId` from **that** search and place it at the **timeline** second of the event in the same plan: `media.importFromCatalog` with `"as": "$hit"`, then `timeline.addMediaClip` with `mediaId: "$hit"` and `"as": "$sfx"`, then `element.setParams` with `elementId: "$sfx"` and `params: { "volumePercent": 90 }` (**80–100**; a one-shot under a voice needs **100**, and louder is `volume` in dB). Keep hits short, but not shorter than 0.3 s: a 0.15 s click disappears under speech.

## Check that it can be heard

You cannot listen, and a clip on the timeline is not a sound anyone hears. The plan result lists each short sound it placed under `sounds`, with a `verdict` (`clear`, `quiet`, `buried`, `too short`, `unmeasured`) and its `marginDb` over what plays under it; `audio.measureSounds` (through `editor_read`) measures any of them later. Fix every one that is not `clear` in the follow-up plan: `too short` → search again and swap in a longer sound; `quiet` or `buried` → make it louder than its file with `volume` in dB (`+6` is about twice as loud, up to `+20`; `volumePercent` stops at 100, its file's own level), and if it still is not `clear`, a punchier sound, or move it a little off the spoken word into a pause. `unmeasured` means a clip under it could not be mixed (its `unmeasured` says which): you do not know whether it can be heard, so say that, and do not call it audible. Then say which sounds you changed and what the check reads now.

When the user says they can't hear a sound: measure it first (`audio.measureSounds` on those clips), tell them what it found ("the click is 0.16 s and 20 dB under your voice"), change what it shows is wrong, and measure again. Never reply that it is fixed after only moving clips or placing the same files again, and never give a cause the tool results do not show.

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
| ui | On-screen tap, click, pop, ding or notification | `sfxRole: ui` + the sound's name (`mouse click`, `cork pop`, `ding`) |
| drop | Beat drop they asked for. Not downer, not explosion | chips off `drop` |
| explosion | Picture explodes or they asked | `sfxRole: hit` + `explosion` |
