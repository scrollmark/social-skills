---
name: tools-and-keys
description: Which third-party tools exist, what each unlocks, and what to turn on
minutes: 8
audience: someone deciding what to sign up for
---

# Tools and keys

Teach this when someone asks "what do I need?" or hits a wall because a source
was not available. Run the `doctor` script bundled in the studio-setup skill first, and teach against what is
ACTUALLY on their machine — do not describe a tool they already have as though
it were missing, and never recommend one they cannot use.

Full inventory and triage: `references/third-party.md`.

## Step 1 — You need less than you think

Three things must exist: `ffmpeg`, `node`, and `uv`. Everything else is
optional.

With zero keys and zero accounts you can still make a complete video: two
public archives need no key at all, and the narration voice runs on your own
machine. That is not a degraded mode — it is a real video.

TRY: Run `python3 scripts/doctor.py` from the studio-setup skill folder and read
the `tools:` section.
CHECK: Are ffmpeg, node and uv all showing OK?

## Step 2 — If you add one key, add Pexels

Free, no billing, thirty seconds at pexels.com/api. It is the difference
between "find me footage of a city street" usually working and usually not.

The archives are deep on space, science, history and nature, and thin on
staged or everyday consumer subjects. Pexels covers exactly that gap.

TRY: Add PEXELS_API_KEY to `.env`, re-run doctor.
CHECK: Does the stock section now say OK?

## Step 3 — Paid generation, and when it is worth it

Generation is for things that cannot be filmed: an unreleased product, an
abstract idea, a place that does not exist. It is not a better way to get a
city street — real footage is free and does not warp faces.

The money lever worth knowing: a generated still with slow camera drift costs
a few cents; the equivalent generated clip costs around thirty-six. Prefer the
still unless the MOTION itself carries meaning.

TRY: Ask what your next video would cost with generation versus stock.
CHECK: Can you name a shot that genuinely needs generating?

## Step 4 — The music rights split, which matters more than the price

Two music backends generate happily. One has clean commercial terms. The other
works without billing — so it is the path of least resistance — and its output
rights are unsettled, making it fine for internal or demo use and not for
anything you publish.

You should be told which is in use before you choose, not after. The reason is
practical: the whole edit gets cut to the track's energy, so discovering a
rights problem later means re-cutting the video, not relabelling it.

TRY: Ask "which music backend would this use, and what are its terms?"
CHECK: Do you know whether your last video's score can be published?

## Step 5 — What is missing, and what that costs you

`showwatcher` is the automated quality gate and is usually not installed. When
it is absent, verification happens by hand — frames pulled and actually looked
at, duration and loudness confirmed.

That works, and it is the only step whose guarantee depends on someone
remembering. If a video ever ships broken, this is the step that was skipped.

TRY: Check whether `showwatcher` shows OK in doctor.
CHECK: If it is missing, do you know what has to happen instead?
