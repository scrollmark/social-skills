---
skill: video-production
---

## Prompt

I built the props and rendered, but the video is four seconds of black. What went wrong?

## Without skill (baseline)

Claude speculates about codecs, or suggests re-rendering, or asks for logs. It treats a black render as a rendering failure.

## With skill (expected)

Claude recognises the pipeline's known failure mode: `--placeholders` left on for the final build, or unresolved sources rendering as nothing. It directs the user to run the step-8 gate — the bundled `qc_render.py` — which checks black tails and duration against the plan, and then to pull frames with `poster.py` and look at them. It says explicitly that "it rendered" and "it is correct" are different claims.

## Behavioral markers

- [ ] Names `--placeholders` or unresolved sources as the likely cause
- [ ] Points at `qc_render.py` before suggesting a re-render
- [ ] Insists on looking at actual frames
- [ ] Does not treat a zero exit code as evidence the render is fine
