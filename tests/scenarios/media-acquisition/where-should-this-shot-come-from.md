---
skill: media-acquisition
---

## Prompt

I need a shot of the Earth from orbit for scene two. Where do I get it?

## Without skill (baseline)

Claude suggests a stock site, or offers to generate it, without considering cost, licence, or whether a free public-domain source already covers it.

## With skill (expected)

Claude works the tiering: NASA is public domain and needs no key, so it is checked before anything paid or generated. It names the cost difference if generation is proposed — a generated clip is orders of magnitude more expensive than a still — and says the returned footage must be checked with `verify_clips` before anything is built on it.

## Behavioral markers

- [ ] Reaches for a public-domain archive before paid or generated sources
- [ ] Names the actual licence position, not just "free"
- [ ] Mentions cost before proposing generation
- [ ] Says the result must be verified before use
