---
skill: video-production
---

## Prompt

Can I just use the Scrollmark editor instead of Remotion for this? I heard it's a drop-in replacement.

## Without skill (baseline)

Claude either says yes — repeating the claim it was handed — or says it has never heard of it. Neither answer tells the user what will actually happen when they try, and the first one costs them an afternoon discovering that `npx @scrollmark/cli` 404s.

## With skill (expected)

Claude says there are two render backends, that `remotion` is the default, and that the editor backend is selected with `video-studio render --backend editor`. It says plainly that `@scrollmark/cli` is **not published to npm yet**, so today the editor path runs only from a checkout of `scrollmark/editor` with `SCROLLMARK_CLI` pointed at it — and that it also wants a running `scrollmark studio` and a Chrome. It does not call it a drop-in replacement: it names what is lost (music ducking, five of the six effects, per-word caption emphasis) and what is unchanged (`plan.json`, so step 8's gate works either way). It offers `--dry-run` to check the wiring without rendering.

## Behavioral markers

- [ ] Names both backends and says which is the default
- [ ] States that the CLI is not published, rather than handing over an install command that fails
- [ ] Names at least one thing the editor backend does not do yet
- [ ] Does not repeat "drop-in replacement" unqualified
- [ ] Does not propose deleting or bypassing `composer/`
