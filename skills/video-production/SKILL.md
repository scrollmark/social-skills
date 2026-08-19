---
name: video-production
description: Use when actually producing a short-form video end to end — running the interview, storyboarding, sourcing, previewing, rendering and quality-checking in order — or when a run has stalled and you need to know which step comes next and who owns it.
---

# Video Production

**You are the pipeline.** There are no stages, checkpoints or event streams: you sequence the scripts, ask the user at decision points, and gate the output. Every other video skill owns one step; this one owns the order they run in, and the rules that only make sense across a whole run.

## Requires

Three scripts **ship with this skill**: `scripts/doctor.py` (step 0's status report), `scripts/normalize_audio.py` (step 7's loudness fix) and `scripts/poster.py` (step 9's thumbnail shortlist). All stdlib-only; all want `ffmpeg`/`ffprobe`.

The rest of the sequence needs `pip install video-studio-engine` — `video-studio setup` (step 0's install plan), `build_props` (steps 5 and 7), `studio` (the preview editor) and `preflight` (the render gate) — plus the composer's `npx remotion render`, which is Node and is neither bundled nor pip-installable from here. Sourcing, voice and export belong to the step skills named below and carry their own install lines.

**Skip the pip install and this skill still is not standalone — it drives the whole engine.** There is no props document, no preview and no preflight, so the sequence has nothing to sequence. What survives is the shape: which decision must precede which, and where money and silence enter a run.

## The Pipeline

| # | Step | Owned by |
|---|---|---|
| 0 | Check the machine; offer to fix it; **ask before installing** | `studio-setup` |
| 1 | Enumerate `formats/*.md`, present as a choice, load only the chosen one | `video-formats` |
| 2 | Run that format's interview, ≤4 questions a round | `agent-interview` |
| 3 | Elicit sourcing — **footage and audio in the same round** | `media-acquisition`, `audio-acquisition` |
| 4 | Build the storyboard from the format's grammar | `video-formats` |
| 5 | `video-studio build_props --placeholders`, open the editor, re-read `props.json` | here |
| 6 | Resolve sources — TTS first, then footage; then `video-studio verify_clips` | `audio-acquisition`, `media-acquisition` |
| 7 | `video-studio build_props` (no flag) → `video-studio preflight` → render → `scripts/normalize_audio.py` | here |
| 8 | Quality gate: pull frames, confirm duration and loudness | `studio-setup` |
| 9 | `scripts/poster.py` — pick the thumbnail, and **open the candidate sheet** | here |

A brand kit (`brand-kit`) is applied at step 4. An export to a human editor (`edit-handoff`) and a composited subject (`subject-compositing`) are branches off steps 7 and 6, not extra steps. Per-step mechanics and the exact invocations are in `references/run-mechanics.md`.

## Sequencing Rules

- **`scripts/doctor.py` runs before sourcing is offered, at step 3.** Offering a source with no key wastes the user's turn *and* makes the cost estimate wrong.
- **Placeholder preview is the default before any spend.** Step 5 is free and catches layout mistakes while they still are. `--placeholders` appears there and nowhere else in the run. The user's edits to `props.json` are authoritative — re-read it after they finish.
- **Quote total cost before the first paid call and again after the last.**
- **Rebuild props immediately before every render**, and never skip preflight.
- **Never declare a render done without viewing frames from it.** "It rendered" and "it is correct" are different claims; only one of them is in the log.

## The Two Contracts

**Sources.** Record the chosen source per layer in the storyboard as `prompt:` (generate) / `find:` (licensed search) / `url:` (user link) / `file:` (user path). A single video routinely mixes all four.

**Paths.** Each of those resolves from exactly one place — `project/clips/<sceneId>-<layerId>.<ext>` — the only path `build_props` reads, and it copies into `composer/public/` itself. Hand-placing a file into `composer/public/clips/` does **not** work; build_props never looks there and will placeholder or error.

## One Machine, Several Agents

Projects cannot collide on content — each owns its props file, its media directory, and registers its own composition. They *do* share a port. **Always open the editor with `video-studio studio --project <dir>`, never directly**, or a second agent silently attaches to the first agent's editor and both then see one project. Hand the user the printed `url` **verbatim**: it ends in the composition id, and a bare `localhost:<port>` opens whichever composition the generated registry lists first — alphabetically, so the same one every time. Claim, `--status` and `--release --port` mechanics are in `references/run-mechanics.md`.

## Read Before Rendering

`references/hard-rules.md` — the rules learned the expensive way: the placeholder-render trap, the clock rule, the cost table, and the render-side composer landmines. Do not start step 7 without it.

## Anti-patterns

- **Sourcing before layout is approved.** Step 5 is free and step 6 is not.
- **Rendering a placeholdered build.** It looks finished. It is coloured boxes.
- **Skipping preflight because the last build was fine.** It is checking a global file that another project may have overwritten since.
- **Narrating a clean bill of health at step 0.** If nothing is missing, say nothing and get on with it.
- **Reporting a regression as a footnote.** A worse result than the previous version is a finding. Offer one fix-and-rerender loop, then stop.
