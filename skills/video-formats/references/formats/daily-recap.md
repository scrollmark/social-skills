---
name: daily-recap
title: DailyRecap
description: Photo-dump recap cut to the track
aspect: 9:16
scenes: 8-14
sceneSeconds: 1.5-3
captions: optional
narration: none
music: required
needs: measure
---

# DailyRecap — photo-dump recap cut to the track

A day, a trip or a week as a fast run of short clips and stills, cut on the
music rather than on a script. No narration: the track carries the pace and
the pictures carry the content. The one piece of typography is a stamp — a
date, a place, a week number — that repeats in the same corner so the run
reads as one set rather than as a shuffle.

The difference from Cinematic is arc. Cinematic builds to a peak and holds the
longest shot after it; this format has no peak. It is an even run of beats
where any two could swap without breaking anything, which is exactly why it
suits footage nobody shot to a plan.

## Composition
Vertical 1080x1920 @30fps. One full-frame layer per scene, hard cuts only —
no cross-fades, they blur the beat the cut is landing on. Eight to fourteen
scenes at 1.5-3s each; under 1.5s a viewer registers movement rather than
subject. A score is REQUIRED. Stills need a `ken` drift or they read as a
stall in a run of moving pictures. Captions off unless there is a spoken clip
in the run, in which case caption only that clip.

## Interview
Round A — header "Audio": ASK THIS FIRST. Score: supply a file or generate
one? If generating, name the backend and its rights terms BEFORE they choose —
every cut in this format is placed against the track, so a rights problem
found later is a re-cut, not a re-tag. There is no voice track to ask about.
Round 1 — header "Footage": The clips and stills, in the order they happened
or in the order they look best? (Ask which; people assume chronological and
often don't want it.)
Round 2 — header "Stamp": What repeats in the corner — a date, a place, a day
number, nothing?
Round L — header "Look": Which caption/card preset — `video-studio styles --list`?
Any look they describe should be saved with `video-studio styles --save`.
Freeform: anything that must open or close the run.

## Slots
`clip-N` per scene (8-14), `music` file, optional `stamp` card repeated in
every scene, optional `endcard`.

## Grammar
- **Open** on the strongest single frame, not on the earliest one.
- **Run** the rest at 1.5-3s. Vary the length within that band; a run of
  identical durations reads as a slideshow whatever the track is doing.
- **Stamp** sits in the same corner in every scene, same size, same colour.
  It is the only thing holding the set together.
- **Close** on a held frame, 3-4s, longer than anything before it. A run that
  simply stops reads as a video that was cut off.
- No text over a clip that is under 2s. It cannot be read, and it competes
  with the picture it is covering.

## Render notes

Measure the track, do not guess it: `measure --music` (bundled in
`audio-acquisition`) reports the seconds where the energy actually changes.
Put those seconds in the storyboard's `musicTransitions` and the editor will
pull each cut onto the nearest one — see `snapToMusic`, which moves a cut at
most a quarter of its own scene and never behind the cut before it.

That snapping is section-level, not beat-level: the detection buckets to whole
seconds, so it lands cuts on drops, lifts and breakdowns rather than on a
snare. For 1.5-3s scenes it is the difference between a run that feels edited
and one that feels shuffled, but do not promise beat sync on top of it.

Order the run before timing it. Reordering after the cuts are placed moves
every boundary and the snapping has to be redone.
