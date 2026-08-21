# Migration Notes

Two structural migrations are recorded here, oldest first:

1. **[Self-contained skills](#the-bug)** — why every skill folder now carries its own
   `references/`, and what to do about an old install.
2. **[The video-studio split](#migration-the-video-studio-split)** — why this repo holds
   prose only, and where the video toolchain went.
3. **[Retiring showrunner](#migration-retiring-showrunner)** — what was carried across from
   the second engine, what was deliberately dropped, and why its skill did not move.
4. **[showwatcher, and step 8](#migration-showwatcher)** — the quality gate that was
   documented for a year and never installed, and what replaced it.

---

## The bug

`install.sh` symlinked each `skills/<name>/` into `~/.claude/skills/social-skills--<name>`
and wrote a `.root` file containing the repo path. Six `SKILL.md` files then said, in
effect: *read the `.root` file in this skill's directory for the repo path, then load
`{repo}/references/...`*.

That only ever worked for the clone-and-symlink install. The route the public website
advertises —

```bash
npx skills add scrollmark/social-skills
```

— **copies** the skill folder. No symlink, no `.root`, no `references/`. The skills then
failed to load their references and fell back to a degraded path with no error message
and no signal to the user. Silent degradation: the skill still answers, just worse.

The README did not document the `npx` route at all, so the failure mode was invisible
from both ends.

## What changed

### 1. Each skill carries its own references

| Skill | `references/` now shipped inside the skill |
|-------|---------------------------------------------|
| `read-the-room` | `slang-and-signals.md` + all 5 `platforms/*.md` |
| `hook-anatomy` | all 5 `platforms/*.md` |
| `platform-fluency` | all 5 `platforms/*.md` |
| `content-autopsy` | all 5 `platforms/*.md` |
| `trend-radar` | all 5 `platforms/*.md` |
| `repurpose-engine` | all 5 `platforms/*.md` |
| `voice-matching` | none — verified it references no files |

The repo-root `references/` stays as the **canonical source**. The per-skill copies are
derived from it.

### 2. Reference loading is now relative

Every affected `SKILL.md` had exactly one sentence rewritten. The prose and meaning are
otherwise untouched — only *how the path resolves* changed:

- before: read `.root` for the repo path, then load `{repo}/references/platforms/{platform}.md`
- after: load `references/platforms/{platform}.md` from this skill's own directory

No `.root`, no `{repo}` placeholder, no repo-path resolution, no `../`.

### 3. `install.sh`

- No longer writes `.root`.
- Actively deletes any stale `.root` left by a previous install.
- Idempotent: replaces whatever already sits at the target path (symlink, directory, or
  a copy left by `npx skills add`), so re-running after a `git pull` is safe.
- Prunes `social-skills--*` links whose skill no longer exists in the repo.
- Honours `CLAUDE_SKILLS_DIR` for testing/alternate installs.
- Iterates `skills/*/` generically, so new skills need no script changes.

### 4. `uninstall.sh`

- Removes copies and broken symlinks too, not just live symlinks.
- Still cleans up legacy `.root` files.
- Honours `CLAUDE_SKILLS_DIR`.

### 5. `scripts/verify-skills.sh` (new)

Fails (exit 1) if:

- any `.root` file exists anywhere in the repo;
- a `SKILL.md` mentions `.root` or `{repo}`, or contains `../` or `/skills/`;
- a `SKILL.md` names a `references/...` file the skill folder does not contain
  (placeholder segments like `{platform}` are satisfied by any `.md` in that directory);
- a skill ships a `references/` directory its `SKILL.md` never loads from.

It works for any number of skills and needs no per-skill configuration.

### 6. Docs

`README.md` documents both install routes (`npx skills add` for users, `./install.sh` for
development) and explains the self-containment property. `CONTRIBUTING.md` states the
invariant, explains *why* it exists, and tells contributors to run `verify-skills.sh`.

## The duplication tradeoff

There are only 6 shared reference files, copied into 6 skills — roughly 26 small markdown
files where there were 6. That is cheap.

The alternative — a single shared `references/` outside the skill folders — cannot survive
the packaging model. Skills are distributed as *folders*; whatever sits above a folder is
not part of the artifact. Any indirection to escape the folder (`.root`, `../`, an
absolute path) works on the maintainer's machine and silently fails everywhere else. That
is precisely the bug being fixed.

Duplication buys correctness for every install route, and the cost is a maintenance rule
rather than a runtime risk: **edit the canonical file at the repo root, then copy it into
every skill that ships it.** `verify-skills.sh` catches a missing file; it does not catch
a stale one, so keep the copies in the same commit.

## What breaks for people who already installed

Nothing breaks at runtime — the skills work better, not worse. But two kinds of debris can
be left on machines that installed an earlier version:

1. **Orphaned symlinks.** If someone ran the old `install.sh` and later moved or deleted
   their clone, `~/.claude/skills/social-skills--*` contains dangling symlinks. Claude Code
   may log noise about unreadable skills. The new `install.sh` prunes these; the new
   `uninstall.sh` removes them.

2. **Stale `.root` files.** The old installer wrote `skills/<name>/.root` into the clone.
   They are gitignored, so a `git pull` will not remove them. They are now inert — no
   `SKILL.md` reads them — but `verify-skills.sh` fails while any exists, so contributors
   must clear them. Running the new `install.sh` or `uninstall.sh` does this automatically.

3. **A previous `npx skills add` install is a copy, not a link.** It will not pick up this
   fix until the user re-runs `npx skills add`. Until they do, they keep the old, degraded
   copies — which is the original bug, so re-installing is the whole point.

Mixed state is also possible: someone who used both routes may have a copied directory
sitting where the symlink should go. The new `install.sh` overwrites it rather than
failing.

## Upgrade steps

### If you cloned the repo

```bash
cd /path/to/social-skills
git pull
./install.sh              # rewrites symlinks, deletes stale .root, prunes dead links
./scripts/verify-skills.sh
```

To remove an old install entirely first:

```bash
./uninstall.sh && ./install.sh
```

### If you installed with npx

```bash
npx skills add scrollmark/social-skills
```

Re-running picks up the self-contained folders. If your tool does not overwrite in place,
remove the old copies first:

```bash
rm -rf ~/.claude/skills/social-skills--*
npx skills add scrollmark/social-skills
```

### If you have debris and no clone

```bash
# remove dangling symlinks left by an old ./install.sh
find ~/.claude/skills -maxdepth 1 -name 'social-skills--*' -type l ! -exec test -e {} \; -delete
```

Then reinstall by either route above.

In all cases, restart Claude Code — skills are picked up at session start.

---

# Migration: the video-studio split

> [!IMPORTANT]
> **The sections from here to "Consequences for the repo layout" describe a decision that
> was later REVERSED.** They are the reasoning behind the 2026 split, kept because the
> reasoning is worth reading — not because it is current policy.
>
> They say the engine stays in `video-studio` and is "invoked, never vendored", that "there
> is no copy of the pipeline here, and there never should be one", and that "this repo is
> MIT and public; the engine is not." All three are now false. The engine is in `src/` —
> 13,000-odd lines — in this public MIT repo, and a further 5,800 lines of QC engine
> followed it. See [the video-studio split](#migration-the-video-studio-split) and
> [showwatcher, and step 8](#migration-showwatcher) for what actually happened and why.
>
> Read what follows as history. Do not follow it.

## The decision

This repo started as seven skills about *understanding* social media. It now also covers
*making* short-form video. That second job came out of `scrollmark/video-studio`, a private
repo containing a real production pipeline: Python scripts, a Remotion composer, local
models, and a dozen third-party API integrations.

The decision was a **split, not a move**.

> Prose lives in social-skills. The toolchain stays in video-studio and is **invoked, never
> vendored**.

There is no copy of the pipeline here, and there never should be one. A skill in this repo
may *name* a script from video-studio and *tell an agent to run it*. It may not ship it.

## Why not just move the whole thing

Three reasons, in order of how much they hurt.

1. **The engine is not distributable.** It carries paid API keys, a downloaded segmentation
   model, a Remotion install, and a 9.6 GB working tree in which project renders were being
   written *inside the skill directory*. None of that survives `npx skills add`, which
   copies a folder.
2. **The valuable part is the prose.** The scene grammars, the interview rounds, the
   rights tiering, the "measure the narration, don't trust the estimate" rules — those were
   learned by failing at production, and they transfer to anyone with any editor. The
   Python is the least portable and least interesting half.
3. **The two halves have different licences and different audiences.** This repo is MIT and
   public. The engine is not.

## What moved here

| Skill | What it is | Came from |
|---|---|---|
| `video-formats` | The ten scene grammars and the contract for writing an eleventh | `formats/*.md` |
| `agent-interview` | The choice-question protocol: ask decisions, not essays | the interview rounds threaded through the pipeline |
| `brand-kit` | Deciding and recording a brand: palette, type, card roles, logo, voice, CTA | the Title system prose + `styles/*.md` |
| `studio-setup` | What to install, what each key unlocks, and how to triage a dead pipeline | `third-party.md` + the doctor/setup prose |

## What stayed behind

Everything executable, and everything that only makes sense with credentials:

- the orchestrator (storyboard construction, preflight, render, quality gate, cost quoting);
- media acquisition (stock providers, image and video generation, `yt-dlp`, clip verification);
- audio acquisition (TTS, score generation, loudness normalisation, rights tiering);
- subject compositing and hand tracking (`composite_subject.py`, `track_pointing.py`);
- NLE handoff (`export_fcpxml.py`, `export_capcut.py`, and friends);
- the setup and doctor scripts themselves (`setup.py`, `doctor.py`, `tutor.py`);
- `styles.py`, which is what makes a brand preset *apply* rather than merely exist.

## The seam, stated honestly

A split leaves a seam, and the docs' job is to show it rather than paper over it. Three
of the four migrated skills declare a dependency in a `## Requires` section; the honest
summary for an outside reader is in [README.md](README.md#the-video-studio-boundary).

The parts that genuinely do not work without the engine:

- **`pointer-popups`** — its grammar *is* the tracker. Popup positions and timing windows
  are `track_pointing.py` output; the storyboard consumes them. Without the tracker there
  is no format, only a description of one.
- **`boil`** — roughly 40% inoperative. The mark vocabulary (`gen_boil.py --list`), the
  custom `boil_shapes.py` escape hatch, and the per-scene palette workflow are all the
  generator. The composition rules and interview structure survive; the thing that answers
  the interview does not.
- **`brand-kit`'s preset verbs** — `--list`, `--show`, `--apply`, `--save` are `styles.py`.
  Agreeing a brand and writing the files by hand still works.
- **`studio-setup`'s status report** — the inventory is prose and readable; the diagnosis,
  the install plan, and the auto/system/manual classification are `doctor.py`.

The remaining eight formats — TalkingHead, PipStory, Cinematic, Explainer, ProductLaunch,
BrandOrigin, TimelineExplainer, TitledVideo, plus the structural half of the two above —
are pure structure and need nothing from the private repo.

## The rule this leaves behind

Rule 6 in [CONTRIBUTING.md](CONTRIBUTING.md#6-declare-your-dependencies): a skill that
needs machinery this repo does not contain must name it, must say what a reader *without*
it can still do, and must carry that caveat into the README. "Requires X" on its own is
not a disclosure — it tells the reader nothing about whether the skill is 90% useful or
entirely inert.

The failure mode being prevented is the same one as the `.root` migration above: **silent
degradation**. A skill that quietly assumes a script nobody has does not error. It just
gives worse answers, and nobody finds out.

## Consequences for the repo layout

- The shared-reference convention now spans two domains. `references/platforms/*.md` is
  social-media knowledge; `skills/video-formats/references/formats/*.md` is video knowledge
  and is deliberately *not* mirrored at the repo root, because only one skill loads it.
- `scripts/verify-skills.sh` gained frontmatter, README-listing and length checks, so that
  a new skill from either domain has to satisfy the same shape.
- The README is grouped rather than flat. Seven social-media skills, two video-production
  skills, two working-method/toolchain skills — the split is visible in the table of
  contents, not buried.


---

<a id="migration-retiring-showrunner"></a>

## Migration: retiring showrunner

`scrollmark/showrunner` was the other half of the video toolchain: 11,550 lines
across `src/showrunner/`, a `showrunner` console script, and four video formats
registered through entry points. It is being retired in favour of the skills in
this repo plus `video-studio-engine`. This records what crossed over and what
did not, so the decision does not have to be re-derived from an empty directory
later.

### What was ported

| from | to | why it was a gap |
|---|---|---|
| `music/ducking.py` | `audio/duck_music.py` | Nothing here ducked music. A grep for "duck" across `src/video_studio/` returned zero hits: the bed played at one volume through the narration. |
| `music/catalog.py`, `music/picker.py` | `audio/music_catalog.py` | `gen_music` *generates* a bed; there was no way to use music the user already owned, and no deterministic pick, so a re-render could change the score. |
| `captions/generate.py` (whisper path) | `audio/gen_captions.py` | `tts_kokoro` emits word timings for what it speaks. Narration it did not speak — a recorded read, a client-supplied track — had no timings at all and rendered uncaptioned. |
| `captions/ass.py`, `captions/pages.py` | `export/burn_captions.py` | Captions reached the screen only through Remotion props. Anything cut in ffmpeg had no captions. |
| `styles/presets/*.json` (11) | `video_studio/styles/*.md` | `styles.py` shipped the mechanism with **no presets at all**. Translated to this repo's caption/card vocabulary; the type scale, spacing scale and motion curves were dropped rather than faked, because nothing here reads them. |
| `costs.py` pricing tables | `references/generation-costs.md` | The lifecycle (estimate → reserve → reconcile) only worked with `Pipeline`. The numbers were worth keeping; the machinery was not. |

The presets carry two keys `styles.py` itself ignores — `music.moods` and
`rhythm.bpm` — so `music_catalog --pick --style <name>` derives a bed from the
same preset that sets the look. The mood vocabulary already matched.

### What was deliberately dropped

- **`cloud/`** (1,704 lines) — a client for the platform drafts API: multipart
  upload with a client-minted idempotency id, analysis polling, Firebase auth.
  That surface is reachable through the platform's own connector; a second
  bespoke OAuth client is not worth carrying.
- **`pipeline.py`, `formats/`, `events.py`, `checkpoints.py`, `plan.py`**
  (~2,950 lines) — the embedded pipeline with an LLM planner. This is the thing
  being deprecated, not a casualty of it: in this repo the agent plans, and the
  programs are what it drives.
- **`exporters/otio.py`** — already covered. `export/export_edit.py` declares
  `opentimelineio` and the FCPX adapter directly.
- **`providers/tts/kokoro.py`, `providers/video/{minimax,gemini}.py`** — already
  covered by `audio/tts_kokoro.py` and `generate/gen_{minimax,veo}.py`.

Net: roughly 600 lines carried, roughly 10,800 dropped.

### The rename question is closed

`showrunner` is taken on PyPI by an unrelated live-performance library, which is
why PR #75 had to rewrite sixteen install commands to point at the repo, and why
a rename — `callsheet` was the candidate — sat on the list for a while.

Retirement moots it. An archived repository stays cloneable, so
`pip install 'showrunner @ git+…'` keeps working after archiving, and nothing
here installs it at all. A package that is never published needs no name on
PyPI. If it is ever revived or published the question comes back; until then it
is not a pending decision, and should not be carried as one.

The same rule now applies to this repo's own engine: `video-studio-engine` is
not on PyPI either, and installs by URL. See the install section in the README.

### Why the showrunner skill did not move

`skills/showrunner/SKILL.md` (354 lines) is a driving guide for the
`showrunner` CLI: `init`, `create`, `refine`, `export`, `analyze`, and a
troubleshooting table keyed to that CLI's errors. Sections 1–8 and 10 document
commands that are going away. Section 9's frame-extraction quality pass is
already covered here by `showwatcher` (see `setup.py`, step `qc`), which the
workflow degrades gracefully without.

So it is **superseded, not moved** — importing a guide to an archived tool would
have made this repo's skill count go up and its accuracy go down. `video-formats`
and `video-production` carry the parts that outlive the CLI.

**A correction to what this file previously said here.** It claimed that PR #75
fixed the `pip install showrunner` problem "across four files in the showrunner
repo and missed the skill". That is false. `gh pr view 75 --json files` lists
exactly four paths, and `skills/showrunner/SKILL.md` is one of them — the skill
was fixed with everything else.

The error came from reading a local checkout that was one commit behind
`origin/main`, and then reporting the absence of a fix as a finding. It is
recorded rather than quietly deleted because it is the same mistake this
document keeps describing in other people's work: a claim that was true of the
copy in front of me and false of the thing itself.


---

<a id="migration-showwatcher"></a>

## showwatcher, and step 8

`showwatcher` is a 10,217-line video QC analyzer — 19 detectors, a 13-tool MCP
server, YouTube ingestion, a benchmark loop, sqlite-vec search, 2.8 GB on disk
with model weights. It is the "automated quality gate" that step 8 pointed at.

It was never installed. Not on PATH on any machine seen, present only in its own
venv, last touched 2026-07-27. The docs said to "install it from its own repo";
there is no such repo — it is a local, unpublished checkout. So the guarantee at
step 8 rested entirely on somebody remembering to look at frames.

### How it was ported, and in what order

Its README calls it a "companion to showrunner", and `showrunner/fix.py` reads
`checkpoint_compose.json` and `checkpoint_render.json` — showrunner's work-dir
contract. That coupling looked total from the outside, and the first estimate
here was a ~2,600-line reimplementation of the `Context` the detectors read.

That estimate was wrong in a useful direction. The decode layer, report model
and detectors were never coupled to showrunner; only the ground truth was. So
it went across as a port with one new seam — `ground_truth.py` — plus one
genuine rewrite, `timelines.py`, because the three-clock audit resolved its
clocks from `concat.txt` and `captions.ass` and this repo writes neither.

All eighteen detectors now run (`video-studio qc_analyze`). The model-backed
ones sit behind one extra each — `[qc-ocr]`, `[qc-yolo]`, `[qc-face]`,
`[qc-clip]` — so no single install drags in every model, and a detector whose
extra is absent skips and says so rather than failing the run. `[standard]`
takes `[qc]` and none of the model extras.

That last part came with a rationale that did not survive checking. It was
written as "mediapipe is kept out because it pulls `opencv-contrib-python`, a
second `cv2` provider" — borrowed from showwatcher, where it was true. Here it
was not: `[standard]` includes `[vision]`, `[vision]` requires mediapipe, and
mediapipe requires contrib, so the thing supposedly being kept out arrived
anyway. Worse, `[vision]` also named `opencv-python` and `[qc]` named
`opencv-python-headless`, putting THREE providers of the same `cv2` module in
the default install with the winner decided by installation order.

Resolved by naming one distribution everywhere: `[qc]` takes
`opencv-contrib-python`, the same one mediapipe forces, and `[vision]` names no
opencv at all. `[qc-face]` still exists and still matters — it is what makes
`lip_sync` work for someone who installed `[qc]` without `[vision]` — but it is
not a quarantine, and the notes no longer claim it is.

### What step 8 actually needed

Three of its four parts were already covered by scripts that ship in the skills:
`poster.py` pulls frames, `measure.py` reports duration, `normalize_audio.py`
handles loudness. The genuinely missing part was narrower than the tool implied —
whether the render matches the PLAN it was built from.

Three detectors answered that, and needed nothing heavy: `container` (97 lines,
ffprobe against ground truth), `timeline` (128 lines, the three-clock audit — its
own docstring calls it "the one detector v1 structurally could not have"), and
`black_freeze` (86 lines, one ffmpeg filter pass). No numpy, no cv2, no models.

So they were reimplemented, not ported, as `skills/video-production/scripts/qc_render.py`
— stdlib over `ffmpeg`/`ffprobe`, reading the `plan.json` that `build_props` has
been writing for a checker that did not exist. Bundled rather than packaged,
because a gate that needs an install is a gate that gets skipped.

### What is still not automated

Taste. Every mechanical property of a render is now checkable — duration
against the plan, cut placement, black tails and frozen endings, blur and
banding, off-palette colour, caption timing against the word timings, whether
the planned subject is actually on screen, whether each scene's footage matches
its own prompt. What no detector reports is whether the video was worth making:
whether the hook earns the next second, whether the cut lands, whether the plan
deserved a render at all.

So the instruction in the skills has not changed and should not: pull frames,
look at them, and say out loud that you looked. `qc_analyze` proves a render
matches its plan more thoroughly than a person would bother to. It still cannot
tell you the plan was any good.

One honest limit worth keeping in view: a skip is not a pass. `qc_analyze`
reports which checks did not run and why, because "clean" and "clean as far as
we looked" are different claims and the difference is exactly where an
uninstalled extra hides.
