---
name: editor-plan-and-check
description: Use when making any timeline edit in the Scrollmark editor, to turn the request into one plan, apply it as one undo step, then check the result once and answer.
---

# Editor Plan And Check

## Requires

A running Scrollmark editor whose commands you can call: the SocialGPT editor chat, or `scrollmark mcp` from `@scrollmark/cli` for a coding agent. Without it, the brief-first, plan-once, check-once discipline still applies to editing in any tool.

Aim for three rounds: gather, plan, check. Every extra plan costs the user a round and an extra undo step.

## 1. Pin down the brief

Settle these from the request and `timeline_describe` before writing anything:

- **What changes, and what stays.** Keep the user's own clips, text they wrote and edits they made unless they asked to change them.
- **Platform.** One they named, else the editor's safe zone, else generic. The canvas size is fixed; you cannot change the aspect ratio.
- **Length.** A number they gave. Without one, keep the strongest complete takes; do not cut to a length nobody asked for.
- **Look.** Caption kit from the `editor-captions` skill. Keep the existing look unless they asked for a new one.

Use a sensible default for anything unsaid, and name the defaults you chose in your reply. Ask only when the edit cannot be made without the answer.

## 2. Gather in one round

Call everything the plan needs together: `timeline_describe` (`transcript: "words"` only when cutting or timing on words), `footage_proposeKeepRanges` for a recut, `media_searchCatalog` for stock (not for a music bed: the `music` op searches itself), the skills that guide the writes, and the tool groups you will need. Search once per item and pick from its results. Do not read what you will not use, and do not write anything (including imports) before the plan.

## 3. Choose every value before writing

- **Captions:** a `captions.applyRhythm` op, then a `captions.applyPreset` op with `kitId`, `size`, `placement` and `platform`, in the same plan, as `editor-captions` says. Do not leave sizing for a second plan.
- **Overlays:** start time from describe's words, a duration, and a position inside the safe area.
- **Order:** cuts first (`keepRanges` or `timeline.applySourceRanges`), then captions (they follow the cut), then overlays and audio.
- **Track names:** when the plan puts one kind of thing on a track that has no name yet (B-roll, title cards, an end card, music, a voiceover), add a `timeline.renameTrack` op naming it by what is on it ("B-roll", "End card"), with the clip's `$name` as `elementId`. Keep names the track already has.

## 4. Apply one plan

Put every change in one `timeline_applyPlan`. Name what an op creates with `"as": "$name"` and use that name in later ops. When there is a target platform, pass it as the plan's `platform` so its lint checks that platform's safe area.

## 5. Check once

Checking is read-only; fixes go in one follow-up plan.

- **Read the result first (no tool call).** `lint`: text outside the safe area or clipped; each finding names the clips. `added` / `changed` / `removed`: do they match what you meant? A recut that removed every clip, or captions that never appeared, is wrong.
- **Look only when it matters.** After placing captions, titles or overlays, the result carries `frames` where you placed or changed them, with the elements that overlap. Look at those. Call `preview_inspectFrames` (1–3 timeline seconds) only when the result has no `frames` and you placed text, or to see a moment the frames did not cover.
- Check for: text over text or over a face; captions missing from part of the cut, or not matching the speech; a title on screen too briefly to read (under about 1.5 s); music louder than speech (duck it to `volumePercent` 15–25); empty or black frames at the start or end; a length that misses the brief.
- **Masks and cutouts.** Frames list each masked clip with `shows` (inspected frames: `maskShows`), the share of it its mask lets show, and a cutout result has `shows` and sometimes a `warning`. A low share or a warning means look at the frame: if the subject is not all there, or is not there, the mask did not work. Cutout finds people, faces and heads only; for an object, use an image with a transparent background or a shape mask.
- **Judge from your latest plan's frames.** Frames from an earlier plan show the old timeline. Each plan result carries its own frames, so this needs no extra call.
- `lint`, overlaps and `occludedBy` are box checks: they say where boxes sit, not how anything looks. A clip whose mask hides almost everything, or whose image still has its white background, still passes them.
- The `lint` covers the safe area named in the result's `platform`. Run `qc_run` only when the result has no `platform` (an older editor) and there is a target platform.

## 6. Fix once, then answer

Write one follow-up plan against the result's `stateToken`, using handles from the result (including track handles such as `t2`). Describe again only to touch clips the result did not list. For safe-area findings, `qc_applyFix` with `allSafe: true` is fine.

If the plan failed because something outside the edit failed (a stock download, a provider error), nothing was applied. Send the plan once more without that item and the ops that used it, then tell the user what you left out and why. Do not drop the whole edit for one missing download.

Make at most one fix pass, and do not call `preview_inspectFrames` after it: its result's frames and `lint` are the check. If something is still off, tell the user what it is instead of looping.

Then say what changed, what you removed, and the defaults you chose. Describe what the frames showed rather than giving a verdict: what is where ("the bulb sits above your left shoulder; a thin white edge still shows around it"). Never call a result clean, great or checked on the strength of `lint` or overlaps. If what you placed is not clearly in the frame, or you did not see the moment, say so. Do not tell the user how to undo; mention ⌘Z only when they ask how to go back or are unhappy with the result.
