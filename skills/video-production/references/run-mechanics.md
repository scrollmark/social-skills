# Run mechanics

The per-step detail behind the pipeline table. Each step names the skill that
owns the *judgement*; what is here is the *sequencing* — what must have happened
before the step starts, and what the step leaves behind for the next one.

## 0 — Can this machine do the job?

`setup.py` reports only; it changes nothing without `--yes`. Everything present:
say nothing and go to step 1 — narrating a clean bill of health is noise.
Something missing: name it in the user's terms ("the renderer isn't installed"),
say whether you can fix it, and **ask before running anything, every time, even
the safe ones** — `--yes` also runs package-manager installs that touch the whole
system. Some items a machine simply cannot do (getting a key, enabling billing,
accepting terms); hand those over with the specific link and never dress one up
as a command.

**A missing key is not a blocker.** Archives need no key and the voice runs
locally, so a fresh machine can still make a complete video. Say that rather than
stopping.

**Network access is part of step 0.** Some agent hosts sandbox with the network
off by default, and every stock lookup and generation call needs it. Resolve it
before sourcing starts — the failure mode is a dozen provider timeouts that each
look like a different problem.

## 1–2 — Format, then interview

Enumerate the format definitions, present them as a **choice question** (name +
first line), and load **only** the chosen file: it defines the interview, the
scene grammar, the slots and the composition settings. Then run that format's
interview. Keep rounds to ≤4 questions and always include a freeform "anything
else?" option.

## 3 — Sourcing, one round, both halves

Run `doctor.py` **first** and only offer sources that are actually available.
Footage and audio are elicited in the **same round**, and the offer is phrased as
a choice question.

**Audio is a question, never a leftover** — ask it even for formats with no
narration, so that a silent piece is silent because somebody chose it. For a
music-led format the score is the *first* question of the whole interview, since
scene durations are cut to its energy envelope.

Record the outcome per layer in the storyboard as `prompt:` / `find:` / `url:` /
`file:`. A single video routinely mixes all four.

## 4 — Storyboard

Apply the format's grammar mechanically: descriptors repeated verbatim, durations
computed from narration word count (~2.4 words/sec, clamped 3–10s) as a *hint*
only. The storyboard is a JSON document with a published schema in the engine
repo (`references/storyboard.schema.json` there): `title` + `scenes`, each scene
carrying `id`, `narration`, `voice`, `plannedSeconds` and `layers`; each layer
carrying `id`, `source`, `rect`, `enter`/`exit`, `fit`, `ken`, and optionally a
live-typography `card` instead of a source.

## 5 — Placeholder preview

    build_props.py --placeholders     # every unresolved source becomes a labelled coloured shape
    studio.py --project <dir>         # NEVER launch the editor directly

The editor hot-reloads `props.json`, so the user can adjust rects, timing and
tweens visually at zero cost. **Re-read `props.json` when they finish — their
edits are authoritative.** This flag is for this step only and never appears
again in the run.

## 6 — Resolve sources

TTS first (narration timing drives everything), then footage per the sourcing
choices. Everything lands at `project/clips/<sceneId>-<layerId>.<ext>`. Never
regenerate an existing clip; never pass `--force` to "make sure it's fresh".
Narration caches itself and reports `"cached": true`, so on a revision just re-run
every scene and let the unchanged ones skip. Then `verify_clips.py --project
<dir>` — **nonzero means do not build.**

Quote the running total cost before the first paid call and again after the last.

## 7 — Final props, gate, render, normalise

    build_props.py            # no --placeholders; measured narration becomes the clock
    preflight.py              # nonzero = do not render
    npx remotion render       # in the composer directory
    normalize_audio.py --in <mp4>

Rebuild props immediately before **each** render. See `hard-rules.md` for why.

## 8 — Quality gate

If the automated check is available, report its errors and warnings honestly; a
regression against a prior version is a finding, not a footnote. **If it is
absent, say so plainly and verify by hand — never skip verification silently.**
Either way, pull 4–6 frames across the timeline and look at them, and confirm
duration and loudness. Offer one fix-and-rerender loop before declaring done.

## 9 — Poster frame

`poster.py --in <mp4>` writes a ranked shortlist and a labelled candidate sheet.
**Open the sheet.** The score measures colour and contrast, so it knows nothing
about subject matter — on its first real run it ranked an underwater reef above a
marigold market for a Mexico spot. Pass `--at <seconds>` once you have looked. A
feed reads as coherent because its thumbnails do; this is part of the look, not
an upload-time afterthought. The default alternative is frame one, which here is
a title card fading up from black.

## Concurrency and studio claims

Each project owns its own props file and media directory and registers its own
composition, so two agents on two projects cannot collide on content: separate
media, separate document, separate composition. Render and preflight both take
the project name.

Still shared: the composer's `node_modules` (read-only in practice) and **the
port**. Always open the editor with `studio.py --project <dir>`, which picks a
free port and claims the shared props file. The default port is shared, so a
second agent launching directly *attaches* to the first agent's editor and both
then see one project.

**Give the user the `url` that script prints, verbatim.** It ends in the
composition id and that part is load-bearing: a bare `http://localhost:<port>`
opens whichever composition the generated registry lists first — which is
alphabetical, so it is the same project every time no matter whose editor it is.
This is not only a multi-agent problem; one agent alone hits it too.

`--status` lists every studio running on the machine, one entry per agent. When
you are done, `--release --port <port>` drops only yours — releasing without a
port discards other agents' records without stopping their servers, leaving a
live editor nobody can find.
