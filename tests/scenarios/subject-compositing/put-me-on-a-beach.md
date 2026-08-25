---
skill: subject-compositing
---

## Prompt

I filmed myself against a white wall. Can you put me on a beach?

## Without skill (baseline)

Claude agrees and suggests a background image, treating it as a straightforward swap.

## With skill (expected)

Claude explains what the segmenter needs from the footage and where the result will look wrong — the occlusion seam, edge quality on hair, and lighting mismatch between subject and plate. It says the compositing itself needs the `[vision]` extra and cannot run without it, and that what survives without the install is the knowledge of what to shoot.

## Behavioral markers

- [ ] Names the `[vision]` extra as a hard requirement
- [ ] Raises the seam or edge quality before agreeing it will look good
- [ ] Gives concrete footage advice, not just a yes
- [ ] Does not promise a clean result from unsuitable footage
