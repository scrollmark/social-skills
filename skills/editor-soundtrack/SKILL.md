---
name: editor-soundtrack
description: Use when a recut social talking-head video in the Scrollmark editor needs a music bed, or the user asks to add, swap or remove background music. Not for seated interviews or podcasts, footage that is already a song, or when the user said no music.
---

# Editor Soundtrack

## Requires

A running Scrollmark editor whose commands you can call: the SocialGPT editor chat, or `scrollmark mcp` from `@scrollmark/cli` for a coding agent. Without it the `music` op can't run; the when-to-skip rules and vibe queries still guide picking a bed by hand.

## When to skip

Skip this skill (do not search, do not place) if the source is already a song or performance, the user said no music, or it is a seated interview or podcast. If they already placed a bed, keep it, duck it, trim it — do not add a second.

## Add the bed

After the recut, add one `music` op to the plan with a **query** of the form "<vibe> background music" (instrumental, no competing vocals; a bare genre like "lo-fi" finds drum samples, not tracks):

- lifestyle / casual talking-head → "warm acoustic background music"
- product / UGC → "light pop background music"
- explainer / professional → "clean corporate background music"
- default if unsure → "calm background music"

`{"op": "music", "args": {"query": "warm acoustic background music"}}` searches the stock library, picks a track long enough for the video (or loops a shorter one with crossfades), fades it in and out and ducks it under speech (or sets it low when nothing speaks). Do not search first and do not build the bed from `media.importFromCatalog` + `timeline.addMediaClip` + `audio.autoDuck` ops; the op does all of it.

- Add `from` / `to` (timeline seconds) only when the user wants music under part of the video, and `duckDb` (e.g. -18) only when they ask for it quieter or louder under speech.
- For an audio file already in the project, pass `media` (its handle) instead of `query`.
- If the op finds nothing, retry once with a broader query; do not leave the user without music because no result was perfect.

## Tell the user

The bed is new: tell the user you added music and name the track (the plan result's `music[].track.title`), never that you kept or reused existing music. Say they can remove or swap it. On dislike, remove the bed and run `music` again with a different query — do not silently keep the first pick.
