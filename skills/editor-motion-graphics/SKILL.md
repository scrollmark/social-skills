---
name: editor-motion-graphics
description: Use when the user asks for an on-screen title, hook, text graphic, stat, step card, product or price tag, call to action, or any other designed graphic for a moment of a Scrollmark editor video, or wants one changed, moved or removed.
---

# Editor Motion Graphics

## Requires

A running Scrollmark editor whose commands you can call, signed in to SocialGPT: motion graphics are generated on SocialGPT's servers and cost credits. Without it, the rules for when a graphic is earned still hold in any editor.

A motion graphic is a short designed clip for one moment: a photo cutaway, a stat, a step card, a product or price tag, a notification, a headline card. A motion designer builds it from the footage, the words spoken there and the project's design style, and the editor places it on the timeline when it is done.

## 1. Only when asked

Make a graphic only when the user asked for one, in any words ("add a title", "put her name up", "show the price", "make the stat pop"). Never add a hook, title or text graphic on your own, even to open a video or after a recut. Captions are not motion graphics: the editor captions the whole video (`editor-captions`).

The template title commands `graphics.addTitleCard` and `packs.insertTitleScene` are turned off; titles, hooks, CTAs and text graphics all come from `media_generate` with `kind: "motion"`.

## 2. One call per moment

Call `media_generate` with `kind: "motion"`, one call for each moment. Several moments ("the stat and the price") are several calls in the same round.

A speaker's name, with an optional role, is not a motion graphic: add it with `graphics.addLowerThird`, which is free, instant and editable. Make a motion name tag only when the user asks for a designed or animated one, or wants more than a name and a role in it.

- `at_s`: where the moment starts on the timeline, at the line it belongs to. Read `footage_getTranscript` or `timeline_describe` and start a few tenths of a second before the key word. A title or hook for the opening goes at 0.
- `duration_s`: as long as the line it sits on, usually 3–6 s; at most 30.
- `layout`: `overlay` (default) sits over the footage and leaves the speaker in view; use it for stats, product tags, steps and notifications. `full-frame` cuts away to a designed card while the voice continues; use it for a headline or title card, a correction, or a list that needs the whole frame.
- `prompt`: what the moment is and the words it shows, in a sentence or two ("Name tag: Dr Maya Chen, sleep researcher"; "Price drop: was $32, now $24, this week only"). Leave out fonts, colours and animation: the design style and the designer decide those.
- `exact_strings`: every name, handle, URL, number and price exactly as it must appear, from the user or the project, never re-spelled from the transcript.
- `images`: only when the user wants a photo or logo in it, as slot names to project image ids (`{"product": "<mediaId>"}`). Without images the designer works with type and shapes; do not generate an image first unless they asked for one.

## 3. While it runs

It is non-blocking and takes a few minutes. Say what you started ("a price card at 0:21"), finish the rest of the request, and end the turn; do not say it is on the timeline. When a `[generation finished]` message gives its `elementId`, it is already placed: do not place it again or call `graphics.addCode`. Confirm once in one line.

## 4. Changing one

- Move it with `timeline.moveClip`, lengthen or shorten it with `timeline.setClipDuration`, or remove it with `timeline_deleteClips`, using its `elementId`.
- Different words, a different look or a fix inside the graphic: generate it again with the change in `prompt`, then delete the old clip once the new one is placed. Say that it makes a new graphic.

## 5. Say what you did

Name each graphic, where it sits and what it shows. If the user asked for something that isn't a moment graphic (running captions, a whole animated video), say what you did instead.
