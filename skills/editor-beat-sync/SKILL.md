---
name: editor-beat-sync
description: Use when the user wants cuts or moments in a Scrollmark editor video "on the beat" or "to the music", or a montage of several shots set to music. Never moves speech cuts.
---

# Editor Beat Sync

## Requires

A running Scrollmark editor whose commands you can call: the SocialGPT editor chat, or `scrollmark mcp` from `@scrollmark/cli` for a coding agent. The beat ops read the music clip's beats inside the editor. Without it, only the rules (never move a speech cut, downbeats for reveals) carry over.

## The two ops

Two `timeline_applyPlan` ops put edits on the music's beats; the plan command lists them by name only, and their arguments are here:

- `beatCut {clips: [handles in play order], music: the music clip, every?: "auto" | "bar" | 1 | 2 | 4 | 8}`
- `snapToBeat {clips: [handles], music: the music clip, to?: "beat" | "downbeat"}`

Both need a music clip on the timeline: use the one that is there, or add one in the same plan with a `music` op named with `"as": "$bed"` and pass `"$bed"` as `music`. A bed looped from a short track is fine: the beats of every copy are read.

## Cut shots to the beat: `beatCut`

For a run of shots (B-roll, a montage, several clips with no speech):

`{"op": "beatCut", "args": {"clips": ["c2", "c3", "c4", "c5"], "music": "c9"}}`

- `clips` in the order they should play, all on one track. On the main track the first starts where it is; on an overlay track it starts on the nearest beat. Every change after it lands on a beat.
- `every`: leave it out (`"auto"`) and each shot keeps about its length, in whole beats; that is what "cut to the beat" means. `"bar"` cuts only on downbeats, for calm or slow music. A number (1, 2, 4, 8 beats a shot) only when they ask for fast or punchy cuts; that shortens the montage, so end the music with it (`timeline.setClipDuration` on the music clip, then a fade-out). A shot too short for its beats takes the most whole beats it has.
- Never on a talking head or interview: moving a speech cut onto a beat clips words. Leave speech cuts where the transcript put them and put overlays on beats instead.

## Put moments on beats: `snapToBeat`

After placing titles, B-roll overlays, stickers or SFX, move their starts onto the music's beats in the same plan:

`{"op": "snapToBeat", "args": {"clips": ["$title"], "music": "c9", "to": "downbeat"}}`

- `to: "downbeat"` (the first beat of a bar) for a hook, a title or a big reveal; `"beat"` for everything else.
- It moves starts only and keeps lengths; main-track clips are refused, so use it on overlays.

## When there is no beat

If either op says the music has no steady beat, tell the user the track has no clear beat to cut to and offer a different track; do not place cuts by guesswork. Read beat times yourself (`audio_detectBeats`, in the `audio` group) only when an op cannot do what was asked.

Tell the user the tempo (the plan result's `beatCut` or `snapToBeat` entry) and how many beats each shot runs.
