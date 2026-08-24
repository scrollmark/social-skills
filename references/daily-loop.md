# The daily loop (internal)

A tight review cycle: produce a video most days, quality-check it, and hand
the team a paste-ready update. Distribution is a human step — the loop
produces and reports, John posts.

## Each day

1. **Pick the day's subject.** Whatever is most useful, and say why in the
   note. Rough priority when nothing is urgent:
   - unblock something the pipeline can't do yet (a new format, a composer
     gap) — these teach us the most per render
   - a reference-mining candidate (`reference-mining.md`)
   - a format we haven't exercised recently — doubles as a smoke test
   - real Scrollmark content when there's a backlog item
2. **Produce it** through the normal skill workflow: placeholder preview
   before any spend, sources resolved, rendered.
3. **Quality-check it**, and keep the report next to the video.
4. **File it** in `runs/<YYYY-MM-DD>/`:
   - `<slug>.mp4` — the video
   - `<slug>.qc.json` — the quality-check report (enables scores in the digest)
   - `<slug>.note.txt` — one line: what it demonstrates or what it's testing
5. **Draft the digest** and hand it over:
   ```bash
   video-studio daily_digest --next "what's queued tomorrow" --out digest.txt
   ```
6. **Report honestly.** A regression, a wasted spend, or a day with nothing
   shipped goes in the digest as-is. The loop is only worth having if its
   output can be trusted without re-checking.

## Conventions

- `runs/` is gitignored (videos are large). The digest reads it locally; the
  repo keeps the *record*, not the media.
- Cost belongs in the note whenever it's non-trivial, so spend stays visible
  day to day rather than surfacing in a monthly bill.
- The digest names no vendor — it gets forwarded. A test enforces this.

## What "most useful" has meant so far

Kept as a running log, because the pattern is informative: nearly every
format has needed a real fix once actual footage exercised it — a zoom that
cropped text, a crash on silent scenes, popups placed over the presenter, a
frozen clip that never looped. Rendering one video a day is what surfaces
those; reading the code does not.
