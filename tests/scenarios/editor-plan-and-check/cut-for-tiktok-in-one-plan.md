---
skill: editor-plan-and-check
---

## Prompt

The Scrollmark editor is open with a raw 3-minute talking-head take full of restarts. Cut this for TikTok with captions and music.

## Without skill (baseline)

The agent makes the edit one command at a time over many rounds: it applies the cut, then reads the timeline again, then captions, then music, then fixes sizing in another pass. Each step is its own undo. It imports stock between describing the timeline and writing, so its state token goes stale, and it ends by telling the user to press ⌘Z several times.

## With skill (expected)

The agent gathers in one round (`timeline_describe` with words, `footage_proposeKeepRanges`, the skills it needs), chooses every value up front, and applies one `timeline_applyPlan` with `platform: "tiktok"`: the cut, then the captions, then the music. It reads the result's lint and frames, makes at most one fix plan, and answers with what changed and the defaults it chose.

## Behavioral markers

- [ ] Gathers everything the plan needs in one round before writing
- [ ] Applies the whole edit as one `timeline_applyPlan`, cut before captions before audio
- [ ] Passes `platform: "tiktok"` to the plan
- [ ] Reads the result's lint before answering and makes at most one fix pass
- [ ] Names the defaults it chose (length, caption kit, music)
