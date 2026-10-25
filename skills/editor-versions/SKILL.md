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
- **Keep the original before a restyle.** Make a change to the whole look, style or pacing of a timeline the user has worked on as a new version, so "put it back" is a switch, not an undo through many steps.

One video for several platforms ("for TikTok and Reels") is one video, not versions. Make a version per platform, account or store only when the user asks for one each.

## Make versions

These commands run through `editor_run` (`editor_read` for `sequences.diff`); a plan refuses them. Their arguments are here, so skip `editor_lookup` for them.

- `sequences.branch` makes a version in one call: `stateToken` and handles from `timeline_describe` of the open sequence, `name` (what differs: "Music: synth", "Length: 30s", "Hook: question"), and `ops` as for `timeline_applyPlan`. It copies the open sequence and applies the plan to the copy. The open sequence stays open and unchanged, so the same description makes the next version; `open: true` leaves that version open instead. If the plan fails, no copy is left. The result has the new `sequenceId` and what the plan changed. Overlays over the speech (cut-aways, cards, sound effects) move with it through a `recut`.
- `sequences.switch` (`sequenceId`) opens a sequence; `sequences.diff` (`a`, `b`: sequence ids) lists what differs between two.

1. **Gather:** `timeline_describe` (with the transcript when a version cuts speech) and the skills. Decide every version now, down to its plan.
2. **Branch:** one `sequences.branch` per version, all in the same response, each from that one description. Put everything a version needs in its one plan; a `recut` takes the music bed to the new end by itself. List the version you recommend last, with `open: true`, so it is open when you answer.
3. **Answer** from the branch results.

That is three rounds for one version or several. Make one new version per turn by default: the original and the new one are the two to compare. Make more only when asked ("a 30 and a 60 second version", "3 hooks"), and offer more in your answer instead of making them.

If a branch fails, fix that plan from its error and branch it again in the next round; the others are made. If the failed one was the one you meant to open, open your next pick with `sequences.switch` in that round. Do not make a version with `sequences.duplicate` and then edit the copy: that takes three rounds per version where `sequences.branch` takes one.

### Hook versions

A hook version changes the first few seconds and keeps the rest of the cut. Make it with one `recut` of the original's ranges: `recut` plays its ranges in the order given, so list the hook's line first, then the original's ranges without that line. To tease a line and still play it in place, list it first and leave it in the rest too.

- **Question:** open on a line where the speaker asks something. If they never ask one, say so and make another kind instead.
- **Cold open:** open on the most surprising moment or the payoff, pulled from later in the video, then go back to the start.
- **Bold statement:** open on the strongest claim or result.

Each version opens on a different line, and none on the line the original opens on: that version already exists, it is the original. If the best line for a kind is the original's opening, say the original already is that hook and make the others. If two kinds would open on the same line, make one and say why.

### Other kinds

Every version differs from the original in what varies: never the kit, music track, pacing or opening the original already has. If one of the options asked for is what the original already is, say so and make the others.

- **Ending or call to action:** a `recut` that closes on a different line.
- **Pacing:** keep the same lines. For a tighter version, trim each range closer to its first and last words and drop pauses inside it. For a looser one, widen each range by up to 0.5 s of the pause around it, from the transcript's word times. Work out each version's length from its ranges before you branch: a tighter one must be shorter than the original and a looser one longer. A cut already as tight as its words allow has no tighter version: say so and make only the looser one. Then check `durationS` (`original`, `version`) in each branch result, and say so if a version did not come out shorter or longer.
- **Caption style:** a `captions` op with a `kit` other than the one the caption track has (`kit` in `timeline_describe`).
- **Music:** remove the bed and add another in one plan: `{"op":"timeline.deleteClips","args":{"elements":[{"trackId":"<the bed's track>","elementId":"<the bed>"}]}}`, then `{"op":"music","args":{"query":"<2-4 word vibe>"}}`. Never the track the original has. A plan that removes a clip gets its own approval card.
- **Camera moves:** camera-move ops on the original's clips, in one plan.

### Say what each version is

Describe each version from its branch result, not from what you meant to do: the line it now opens on, what moved, and how its length changed. A version whose plan changed nothing was not made; fix it or say so. A pacing or length version whose `durationS.version` equals `durationS.original` is the original again: say that plainly ("the looser version came out the same length as your cut"), never call it looser or tighter. Use `sequences.diff` (`a`, `b`: sequence ids) only when the person asks what differs, or a version took more than one plan.

Never delete or rename the user's sequences unless they ask.

## Answer

Name each version by what differs, say which one is open, and recommend one with a reason in a sentence: "I made a new version, **Music: synth** (open now), with a synthwave bed under your cut. Your original with the acoustic track is still there as Main sequence; switch between them from the menu above the timeline. I'd keep synth, it fits the tech demo. Want an upbeat pop version too?"
