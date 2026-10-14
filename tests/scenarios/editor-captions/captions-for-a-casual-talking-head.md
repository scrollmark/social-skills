---
skill: editor-captions
---

## Prompt

The Scrollmark editor is open with a recut 40-second talking-head clip: someone in their kitchen telling a story about a failed recipe. Add captions for TikTok.

## Without skill (baseline)

The agent calls `captions_generate`, which makes sequential chunks with the default look, or lists every caption preset and picks a loud one such as `tiktok` or `meme-loud`. It leaves out `platform`, so the captions sit under TikTok's caption block, and it often sets size `m`, where long words clip on a vertical video.

## With skill (expected)

The agent writes one-word-at-a-time captions: `captions.applyRhythm` with `mode: "word"`, then `captions.applyPreset`, as two ops in one plan. It picks `handwritten` for a casual home story without browsing presets, uses size `s`, passes `platform: "tiktok"` to both ops, and checks the result's safe-area lint.

## Behavioral markers

- [ ] Uses `captions.applyRhythm` with `mode: "word"`, not `captions_generate`
- [ ] Picks `handwritten` (or explains another of the four vibe kits) from what the footage is
- [ ] Sets size `s`
- [ ] Passes `platform: "tiktok"` to both the rhythm and the preset op
- [ ] Never uses `phrase-plus-word`
