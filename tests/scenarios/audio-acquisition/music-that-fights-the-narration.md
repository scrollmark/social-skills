---
skill: audio-acquisition
---

## Prompt

The music in my render is drowning out the voiceover. Can you just turn the music down?

## Without skill (baseline)

Claude suggests lowering a volume value, or re-exporting with a quieter track — a single flat level for the whole video.

## With skill (expected)

Claude explains that a flat level trades one problem for another, and points at `duck_music`, which measures the narration per frame and writes an envelope so the bed drops under speech and returns in the gaps. It notes the ordering — after `build_props`, before rendering — and that re-running `build_props` overwrites the envelope. It also warns that if the composer ignores `music.envelope`, the tool reports success and changes nothing.

## Behavioral markers

- [ ] Proposes ducking rather than a flat level change
- [ ] Gets the ordering right relative to `build_props`
- [ ] Mentions the envelope can be silently ignored by a composer
- [ ] Does not suggest re-recording the narration louder
