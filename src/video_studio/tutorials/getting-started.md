---
name: getting-started
description: Walk the whole workflow and understand why each step is there (see the note on rendering)
minutes: 15
audience: someone who has never used this
---

# Getting started

Teaches the shape of the workflow by making something. Do not summarise this
tutorial and skip to the end — the whole point is that they touch each step.

**Before you start, know where this stops.** Steps 1 to 3 work today: the
interview, the format choice, and the storyboard are all conversation, and they
need nothing installed. From step 4 onward — the placeholder preview, the
editor, and every render — the pipeline draws on a Remotion composer that this
repo does not ship. If you do not have one, read steps 4 to 7 as a description
of the shape rather than instructions to follow, and skip the TRY lines.

Do not promise a learner a finished video and then discover this with them at
step 4. Say it at the start, the way this tutorial does.

## Step 1 — What this actually is

You describe a video in conversation and get a finished vertical `.mp4`. There
is no timeline to drag and no commands to memorise.

The part worth understanding up front: **you are asked questions at the points
where your taste matters, and nowhere else.** Which format, what it should feel
like, where footage comes from, and whether the layout looks right. Everything
between those is handled.

TRY: Say "let's make a video" and stop there. See what you get asked.
CHECK: Did you get a list of formats to choose from?

## Step 2 — The format decides the questions

A format is not a skin. It sets the interview you get, the shape of the edit,
and the rules the scenes are built by. An Explainer asks about your topic and
takeaway; a Cinematic asks about mood and arc and asks for the music FIRST,
because the cut is built around the track's energy.

So picking the format is the highest-leverage decision in the whole process,
and it is the first one for a reason.

TRY: Pick Cinematic, and notice the first thing it asks about is the score.
CHECK: Can you say why a music-led format asks for the track before anything else?

## Step 3 — Answer the interview specifically

Rounds of at most four questions, each with an escape hatch for anything the
options miss. Vague answers here produce a vague video, and no amount of
re-rendering later fixes a fuzzy brief.

"Something upbeat about cities" gets you a generic montage. "Joy, dawn to
night, one city waking up, ending on a rooftop wide" gets you a piece with a
shape.

TRY: Answer the mood and arc questions with something specific enough that a
stranger could picture the first and last shot.
CHECK: Can you name your opening shot and your closing shot?

## Step 4 — Approve the layout before anything costs money

You get a preview where every clip is a labelled coloured rectangle. No footage
exists yet, nothing has been fetched, nothing has been spent.

This is the cheapest moment to change your mind, and the only one where
changing your mind is free. Check the pacing and whether text collides with
anything. If you want to move things yourself, ask to open the editor — you get
a live preview you can drag and retime, and your edits win over the plan.

REQUIRES A COMPOSER. The preview and the editor are both Remotion, which this
repo does not ship. Without one there is nothing to look at, and the rest of
this tutorial describes the shape rather than something you can do. Say so now
rather than at step 7.

TRY: Look at the placeholder preview and ask for one timing change.
CHECK: Does the shape of it feel right before any footage exists?

## Step 5 — Footage and audio get sourced

Now it spends. Narration is recorded first if there is any, because everything
else is timed from it. Then footage per the sourcing choice you made, then the
score.

You are told what anything costs before it is spent, not after. Much of it is
free: two public archives need no account at all, the stock libraries are free
with a key, and the narration voice runs on your own machine.

TRY: Ask "what will this cost?" before approving the spend.
CHECK: Do you know which parts of your video were free and which were not?

## Step 6 — It gets checked, and so should you

Two automatic passes: one on what the providers returned (duplicate clips,
monochrome footage, clips too short for their scene, silent audio) and one on
the finished render (sync, captions, text off-frame, loudness).

Neither replaces looking. Ask to see frames from the finished video. Every
shipped-broken render in this project's history would have been caught by
opening a single frame.

TRY: Ask to see 4-6 frames from across your finished video.
CHECK: Did you actually look at them?

## Step 7 — Change it by saying what is wrong

The project folder is the document. "The third scene drags." "Drop the subtitle
on the end card." "Replace the workshop clip with something tighter."

Footage you already paid for is never re-fetched — clips are cached per scene
and layer, so rewording a whole video costs narration time and nothing else.

TRY: Change one line of copy and re-render.
CHECK: Did only the thing you changed get rebuilt?
