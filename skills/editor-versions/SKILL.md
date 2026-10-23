---
name: editor-versions
description: Use when a request in the Scrollmark editor is a matter of taste (music, caption style or font, look or grade, length or pacing, the hook or opening), when the user asks for options, another version or to compare, when they rejected the last attempt at something, or before restyling the whole video. Decides between one result, options in chat, and separate versions (sequences) to compare.
---

# Editor Versions

## Requires

A running Scrollmark editor whose commands you can call: the SocialGPT editor chat, or `scrollmark mcp` from `@scrollmark/cli` for a coding agent. The editor keeps several sequences (versions of the timeline) per project, sharing its media. Without it, the choice between one result, options in chat and separate versions still applies.

## Choose how to answer

Most requests are one clear edit: make it, once. Do not offer options for a cut, a trim, a move, a fix, or anything the user specified exactly.

- **Options in chat** for a choice that is quick to try and quick to undo: a caption style or font, a voice, a title's wording, a colour. When the user asks "what options are there?" or "recommend one", list 3, at most 4, each one line with what makes it different, recommend one, and change nothing until they pick. When they ask for the change itself ("make the captions more fun"), apply your best pick and name 2 alternatives in one line.
- **Separate versions** for a choice that is slow to redo or that the user should watch side by side:
  - length or pacing (a 30 s cut and a 60 s cut)
  - the hook or opening
  - the music bed together with the pacing cut to it
  - a whole restyle ("make it cinematic", a new look or grade)
  - the user asked for versions, or to compare
  - the user rejected your last attempt at the same thing ("I don't like this music", "now it's too dark"): make the next try a version, so the one before is still there
- **Keep the original before a restyle.** Before changing the whole look, style or pacing of a timeline the user has worked on, copy it first (step 2 below), so "put it back" is a switch, not an undo through many steps.

One video for several platforms ("for TikTok and Reels") is one video, not versions. Make a version per platform, account or store only when the user asks for one each.

## Make versions

These commands run through `editor_run` (`editor_read` for `sequences.list` and `sequences.diff`); a plan refuses them. Their arguments are below, so skip `editor_lookup` for them. Calls in one round run in order. Budget: gather, copy, edit, answer.

1. **Gather:** in your first round, with `timeline_describe` and the skills, call `sequences.list`: it gives the open sequence's `sequenceId`, which you need to copy from it again.
2. **Copy and describe in ONE round**, without waiting for the copy's result: `editor_run` with `sequences.duplicate` (`sequenceId`: the one to start from; `name`: what differs, such as "Music: synth", "Length: 30s", "Hook: question"), then `timeline_describe` as the next call in the same response. The copy is open by then, so the describe reads it; clip handles from before belong to the other sequence. Splitting these into two rounds is the most common way to run out of rounds.
3. **Edit the copy** in one plan, as for any edit. Its result lists what changed; that is your check.
4. **One new version per turn** by default: the original and the new one are the two to compare. Make two only when asked for two or more ("a 30 and a 60 second version"); copy each from the ORIGINAL, not from the version before. Offer more in your answer instead of making them.
5. The copy stays open, so the person sees it. Use `sequences.switch` only to open a different one, and `sequences.diff` (`a`, `b`: sequence ids) only when a version took more than one plan and you need to check it changed only what you meant.

Never delete or rename the user's sequences unless they ask.

## Answer

Name each version by what differs, say which one is open, and recommend one with a reason in a sentence: "I made a new version, **Music: synth** (open now), with a synthwave bed under your cut. Your original with the acoustic track is still there as Main sequence; switch between them from the menu above the timeline. I'd keep synth, it fits the tech demo. Want an upbeat pop version too?"
