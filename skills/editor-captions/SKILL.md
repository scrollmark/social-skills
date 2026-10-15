---
name: editor-captions
description: Use when adding or restyling captions in the Scrollmark editor, one word at a time (the default for "Add captions" and "Cut this for TikTok" on a talking-head video) or in short three-word chunks.
---

# Editor Captions

## Requires

A running Scrollmark editor whose commands you can call: the SocialGPT editor chat, or `scrollmark mcp` from `@scrollmark/cli` for a coding agent. Without it the steps below can't run; the kit-by-vibe list is still a fair guide to choosing a caption look in any editor.

## Pick the rhythm

- **One word at a time** (default): `captions.applyRhythm` with `mode: "word"`.
- **Three-word chunks**, when the user wants chunks rather than single words: `captions.applyRhythm` with `mode: "sequential"` and `wordsPerCaption: 3`.

Never `phrase` (8-word lines), never `phrase-plus-word` (an extra word track), and never `captions_generate`: it makes sequential chunks without the rhythm you chose.

## Steps

After the recut, or on a timeline that already has the keep list:

1. The rhythm op above, then `captions.applyPreset` with `kitId`, `size` and `placement`: as two ops in one `timeline_applyPlan`, or as `captions_applyRhythm` and `captions_applyPreset` outside a plan.
2. Pick one `kitId` from this set. Choose from the footage (transcript, setting, what they are selling). Do not call `captions_listPresets` just to browse.

   - `handwritten` — casual talking-head, lifestyle, personal story, home or messy setting
   - `soft-promo` — product, beauty, UGC, "check this out" energy
   - `podcast-plate` — interview, seated conversation, darker or serious talk
   - `clean-minimal` — default if unsure; explainer, professional, clean talking-head

   Do not use `tiktok`, `creator-classic`, `sticker-box`, `cinematic`, `yellow-punch`, `meme-loud`, or `active-word` unless the user names that look.
3. Size: `s` for word captions, since at `m` long words clip on a vertical video; `m` or `l` only when the user asks for bigger captions.
4. Placing for a platform (the user named one, or the editor's safe zone shows one): pass the same `platform` to `captions.applyRhythm` and to `captions.applyPreset`. The preset recomputes where captions sit, so leaving it out of either call puts them back under the platform's caption block. Then check that platform with `qc_run` (`checks: ["document"]`) and fix what it finds with `qc_applyFix`.
5. If captions already exist with role `word`, `captions_resync`. It keeps their kit, colour and size, so do not apply a preset afterwards unless the user asks for a different look.
