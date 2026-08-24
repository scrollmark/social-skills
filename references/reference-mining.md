# Mining reference galleries for format definitions (internal)

A plan for turning public "made with X" galleries into new `formats/*.md`
entries. Written against the Motion community gallery
(`motion.so/community`), but the method generalises to any gallery that
publishes prompt + result together.

## Why this gallery specifically

Inspected 2026-08. It publishes, for each item: **the user's full prompt, the
author, the date, an engagement count, and the resulting video.** That pairing
is unusual and valuable — most galleries show only output. We get to see what
people actually asked for *and* what the tool made of it, which is exactly the
input needed to write a format's `## Interview` and `## Grammar` sections.

Roughly 48 items per gallery page; videos render on the item page rather than
inline, so extraction is per-item, not a single scrape.

Observed prompt archetypes on page one alone, each a plausible format:
- **Documentary-graphics overlay** — "talking head of Naval, add documentary
  style motion graphics in the middle"
- **Product launch spot** — "40 second launch video for AI retail management"
- **Threaded explainer** — the Apple-CEO-history thread, numbered beats with
  emoji section markers
- **News explainer, house style** — "vox style explainer, 2 minutes"
- **Branded series episode** — the chalkboard-animation piece, with palette,
  canvas, audience, and tone all specified

That last one is the tell: the strongest prompts read like **briefs**, not
sentences. They pin canvas, duration, palette, audience, and emotional goal.
That is the same shape as our format files, which is encouraging — it suggests
our interview questions are asking for roughly the right things.

## Boundary (read first)

Study the **grammar**, don't clone the **content**. We reproduce structural
patterns — beat ordering, shot vocabulary, pacing, how text is used — and then
write original scripts and subjects, exactly as we did for the native-ad format
(analysed a real ad, shipped an original pet-insurance script; never reused
the source's script or footage). Do not re-render someone's specific creative
piece and present it as ours, and don't republish their videos.

## Phases

**1 — Harvest (cheap, no rendering).** Per item: prompt text, author, date,
engagement, item URL, video URL. Engagement is a weak but free quality signal;
use it to rank candidates, not to conclude anything. Store as
`corpus/reference/<gallery>/<slug>.json`. Ranking heuristic: prefer prompts
that specify canvas + duration + audience, and outputs whose structure is
legible in under three viewings.

**2 — Characterise (our own tooling, free).** Run the quality check over each
downloaded video for scene count, cut cadence, caption density, motion
profile. Sample frames at scene boundaries. The goal is a one-page grammar per
candidate: how many beats, how long, what changes at each cut, where text
appears, whether the camera moves. This is the same read we did on the
Cybertruck ad — and it caught the shrinking-host PIP mechanic that a casual
viewing missed entirely.

**3 — Draft a format file.** Turn each grammar into `formats/<name>.md`:
composition settings, interview questions (derived from what the strong
prompts specify), slots, grammar rules, render notes. No code, by design.

**4 — Re-create as an original.** New subject, new script, our own footage.
Placeholder preview first, then resolve sources. Budget: aim under $3 per
candidate using the still+Ken Burns path from `providers.md`.

**5 — Compare and record.** Quality-check ours, and note honestly where the
reference does something we structurally cannot yet (that's the interesting
part — it becomes the next composer feature, the way the PIP mechanic did).
Log per candidate in the format file's own notes.

## Suggested first three

Chosen for structural distance from what we already have:

1. **Documentary-graphics overlay** — closest to a gap we know we have: text
   and graphics *over* talking-head footage, timed to speech. Reuses the
   pointer-popups timing machinery.
2. **Threaded explainer** — numbered beats with strong section markers; tests
   whether our card layers can carry a whole video rather than accent it.
3. **Branded series episode** — palette/tone/audience-driven, single visual
   idiom throughout. Tests whether a format file can carry a *brand*, not just
   a shape.

## Unknowns to settle before phase 1

- Whether item pages expose a stable video URL, or need a browser session.
- Whether the gallery has pagination / an internal JSON endpoint (48 items on
  page one suggests paging).
- Their terms on automated access — check before any bulk harvesting; a slow,
  small, manual-scale pass is the safe default regardless.
