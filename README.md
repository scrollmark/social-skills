# Social Skills

Claude Code skills for social media and short-form video. Because even AI needs social
skills.

## What is this?

A collection of installable [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code)
covering two related jobs:

- **Understanding social media** — tone, hooks, trends, platform conventions, creator voice.
- **Producing short-form video** — scene grammars, brand consistency, and the interview
  protocol used to pin down a plan before anything is built.

Most of it is **prose** — these skills teach Claude how to think about a problem. Some of
them also ship the small programs that make that thinking executable, and a few drive a
larger engine that lives in this repo as an installable Python package. What that means
for each skill is spelled out in [What ships where](#what-ships-where).

<!-- BEGIN SKILLS TABLE (descriptions are copied verbatim from each SKILL.md frontmatter) -->

## Skills

### Understanding social media

Seven skills about reading and making social content. All standalone — no external tools,
no accounts, no keys.

| Skill | Use when |
|-------|----------|
| `read-the-room` | Interpreting social media content — comments, captions, replies, DMs — and you need to understand tone, subtext, or cultural context beyond the literal words. |
| `hook-anatomy` | Analyzing, evaluating, or generating hooks for short-form video or text posts. |
| `trend-radar` | Evaluating whether a trend is relevant, identifying emerging trends, or advising on trend participation timing. |
| `platform-fluency` | Understanding platform-specific conventions, algorithm behavior, content formats, or audience expectations for Instagram, TikTok, YouTube, X, or LinkedIn. |
| `content-autopsy` | Analyzing why content performed well or poorly, doing post-mortem analysis, or comparing content performance. |
| `voice-matching` | Writing in a creator's voice, analyzing a creator's style, or maintaining voice consistency across content. |
| `repurpose-engine` | Adapting content from one platform to another, or advising on multi-platform content strategy. |

### Producing video

Craft skills for planning a short-form video. The planning is standalone. Some of the
execution ships inside the skill; the rest is one `pip install` away.

| Skill | Use when | Standalone? |
|-------|----------|-------------|
| `video-formats` | Planning, structuring, or critiquing a short-form video — choosing a format, laying out its scenes, or defining a new format. Covers ten scene grammars from talking-head to hand-drawn motion graphics. | Mostly — 8 of the 10 formats are pure structure. **Boil** and **PointerPopups** need the engine's generator and hand tracker (see below). |
| `brand-kit` | A user wants their videos to stay visually consistent — saving caption styling, card colours and geometry, title treatment, logos, fonts, voice and CTA copy once instead of redeciding them per video. | Deciding and recording a brand, yes. Applying a preset is `video-studio styles`, from the pip package. |
| `media-acquisition` | Deciding where a shot's footage or stills should come from — public-domain archive, free stock, a paid generator, or a URL the user supplied — and when checking that what came back is actually usable before anything is built on it. | Partly. Ships `scripts/prekey.py`. The ten searching, generating and checking programs need `pip install 'video-studio-engine[sourcing,generate] @ https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz'`; without it the ladder is a briefing, not a workflow. |
| `audio-acquisition` | A video needs narration, a music bed or sound effects — choosing a voice, deciding which music source is safe to publish with, timing a cut to a track, or fixing a render that came out quiet. | Partly. Ships `scripts/measure.py` and `scripts/normalize_audio.py`, so measuring and loudness work out of the box. Voice, music and licence-filtered effects need `pip install 'video-studio-engine[audio] @ https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz'`. |
| `subject-compositing` | A filmed person has to appear somewhere they never were — dropping a subject over replacement footage, putting a drawn prop in front of them, driving the pair across frame, or pinning popup images to where they point on camera. | **No.** Segmentation, occlusion seam, arm punch-through and gesture timing all need `pip install 'video-studio-engine[vision] @ https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz'` — MediaPipe and OpenCV cannot be bundled. What survives is knowing what footage to shoot. |
| `edit-handoff` | A finished cut has to leave the pipeline and continue in a human editor — exporting a timeline to Premiere Pro, DaVinci Resolve, Final Cut Pro or CapCut, or answering what survives the trip and what an editor has to rebuild. | **No.** The exporters read the engine's timeline document, so they stay in the package (`pip install 'video-studio-engine[export] @ https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz'`). No install, no file. The format judgement generalises. |
| `video-production` | Actually producing a short-form video end to end — running the interview, storyboarding, sourcing, previewing, rendering and quality-checking in order — or when a run has stalled and you need to know which step comes next and who owns it. | **No.** Ships `scripts/doctor.py`, `scripts/normalize_audio.py` and `scripts/poster.py`, but it drives the whole engine: props, preview and preflight need `pip install 'video-studio-engine @ https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz'`, and the renderer is Remotion (Node). The step order and hard rules still read as a production discipline. |

### Working method and toolchain

| Skill | Use when | Standalone? |
|-------|----------|-------------|
| `agent-interview` | You need to ask a user a series of decisions — a guided setup, an intake, a wizard, an onboarding walkthrough — and want the questions to be answerable rather than open-ended. | Yes. Nothing video-specific in it. |
| `studio-setup` | Checking whether a machine can actually produce video, triaging a pipeline that stopped working, or deciding which third-party tool or API key to add next. | Mostly. Ships `scripts/doctor.py`, so the status report works immediately. Only the install plan (`video-studio setup`) needs the pip package. |

<!-- END SKILLS TABLE -->

Every row's "Use when" text is the skill's own frontmatter `description`, copied verbatim,
so this table cannot quietly drift from the skills. `./scripts/verify-skills.sh` fails if a
skill is missing from it.

## What ships where

The engine used to live in a separate private repo, `scrollmark/video-studio`, and no
skill here could touch it. That split is gone: the engine is in this repo now, and the
40 programs behind these skills land in one of three places.

**1. Bundled inside a skill — nothing to install.** Six programs are pure standard
library and take their input on the command line, so they ship in the skill folder that
uses them and travel with every install route:

| Script | Ships in | Does |
|--------|----------|------|
| `scripts/doctor.py` | `studio-setup`, `video-production` | which sources and binaries are reachable right now |
| `scripts/measure.py` | `audio-acquisition` | durations, and a track's per-second energy structure |
| `scripts/normalize_audio.py` | `audio-acquisition`, `video-production` | loudness after a render |
| `scripts/poster.py` | `video-production` | ranked thumbnail shortlist plus a contact sheet |
| `scripts/qc_render.py` | `video-production` | a render against the plan it was built from — duration, black tail, frozen ending |
| `scripts/prekey.py` | `media-acquisition` | key a generated clip to alpha |

They want `ffmpeg` and `ffprobe` on PATH — the one thing this repo cannot ship. Two
programs are bundled in two skills each; each skill carries its own copy, because a skill
may never reach outside its own folder. `./scripts/verify-skills.sh` fails if those copies
drift apart, or if a `SKILL.md` names a bundled script that is not there.

**2. The `video-studio-engine` package — one `pip install`.** The other 34 programs
either carry third-party dependencies or read a project's state (a props document, a
composer directory, a styles tree), which makes them unfit to sit in a skill folder as a
lone file. They are built from `src/video_studio/` in this repo and run as
`video-studio <command>`:

    pip install 'video-studio-engine[standard] @ https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz'

It installs **from this repo, not from PyPI**. The name `video-studio-engine` is
not published there, so a bare `pip install video-studio-engine` does not get you
this — the URL is the install. Swap the bracket to take only what you need:

| extra | adds |
|-------|------|
| *(none)* | stock, generation, exporters, project tooling |
| `[sourcing]` | `source_clips` (yt-dlp) |
| `[audio]` | `tts_kokoro`, `gen_music`, `duck_music` |
| `[captions]` | `gen_captions` (local whisper word timings) |
| `[generate]` | `gen_veo`, `gen_boil` |
| `[vision]` | `composite_subject`, `track_pointing` |
| `[export]` | `export_edit` (OpenTimelineIO) |
| `[qc]` | `qc_analyze` — the render checked against its plan, with decoded frames |
| `[qc-ocr]` `[qc-yolo]` `[qc-face]` `[qc-clip]` | the model-backed QC checks, one extra per model |
| `[standard]` | everything above except the model-backed `qc-*` extras |

There is no `[all]`. This set is named for what it is rather than for how much of it there is, because an extra called `all` that left four checks uninstalled would tell you two different things at once. What `[standard]` leaves out is the four model-backed QC extras — `[qc-ocr]`, `[qc-yolo]`, `[qc-face]`, `[qc-clip]` — which are opt-in on top. It is not model-free: `[vision]` requires mediapipe for hand tracking, so that one arrives either way.

**3. The composer — in this repo, but Node and separately licensed.** `composer/` holds the
Remotion project that actually draws and renders: 784 lines of React driven entirely by the
props document `build_props` writes. Neither install route above sets it up, because it is
Node — run `npm install` in `composer/` once, then `npx remotion studio` to preview and
`npx remotion render` to render.

**Remotion is not ours to license for you.** It requires a paid Company Licence above three
people, and for hosted or automated rendering. This repo declares it as a dependency and
vendors none of it, so that licence stays between you and Remotion. Read their terms before
building on it.

Only the source is tracked. `composer/props/`, `composer/public/`, `composer/out/` and
`composer/src/registry.ts` are all generated — `registry.ts` in particular is written from
whatever projects a given machine has built, so it is deliberately not committed.

### What a skipped `pip install` costs you

The install is optional, and being honest about that matters more than making the repo
look complete. **A skill whose work needs the package is not self-contained for a user
who skips it.**

- The **seven social-media skills** are entirely unaffected. So is `agent-interview`.
- `video-formats` still works for eight of its ten formats. Composition, Interview, Slots
  and Grammar are structural; you can follow them with any editor.
- **`boil` is roughly 40% inoperative** without `[generate]`. Its mark vocabulary, shape
  files and palette workflow are `gen_boil`; without it, the interview questions have no
  answers to pick from and you are reading a style description, not instructions.
- **`pointer-popups` does not work at all as written** without `[vision]`. Its entire
  grammar is the output of a `track_pointing` hand-tracking pass — popup position and
  timing come from the tracker, not from a storyboard you write.
- `brand-kit` lets you agree a brand with a user and hand-write the files. The preset
  mechanism — `--list`, `--show`, `--apply`, `--save` — is `video-studio styles`, and
  nothing expands a preset into a storyboard without it, so applying a brand becomes
  manual editing.
- **`media-acquisition` keeps only `prekey`.** The provider ladder and the landmine file
  are readable and will tell a human which library to open, but the searching, generating,
  licence filtering and the five-way check on what came back are `source_clips`, the
  `stock_*` and `gen_*` programs and `verify_clips` — all in the package.
- `audio-acquisition` is the best-off of the video skills: `measure` and
  `normalize_audio` ship with it, so the measure-don't-trust discipline and the
  music-costs-6-dB fix are both executable. Voice, music and licence-filtered effects are
  `[audio]` and the base install.
- **`subject-compositing` is entirely package-side.** `composite_subject` does the
  segmentation, the feathered occlusion seam and the arm punch-through; `track_pointing`
  does the gesture timing. What survives is the footage brief — what a selfie segmenter
  needs from a take — and it is worth having before anyone films.
- **`edit-handoff` cannot produce a file without the package.** `export_edit`,
  `export_fcpxml` and `export_capcut` all read the engine's per-project timeline document.
  What generalises is the judgement: which format each application actually imports, and
  that no interchange format carries effects.
- **`video-production` still drives the whole engine.** It ships doctor, normalize and
  poster, but sequences `video-studio setup`, `build_props`, `studio` and `preflight`, and
  the Remotion renderer on top. With none of those present there is nothing to sequence.
  What survives is the shape of a production run and the `references/hard-rules.md` list of
  things that already went wrong once.
- `studio-setup` loses the least: `doctor.py` ships with it, so the status report and the
  triage work immediately. Only `video-studio setup` — the install plan and the
  auto/system/manual classification — needs the package.

Each of those skills states its own dependency in a `## Requires` section near the top —
that is where the authoritative answer lives, not here.

## Platforms

Primary coverage: **Instagram**, **TikTok**, **YouTube**

Also covered: **X**, **LinkedIn**

## Install

### What you actually need first

Nothing here is hard, but almost none of it is on a Mac by default, and the failures are
quiet. In dependency order:

| | needed for | how you get it |
|---|---|---|
| **Node 18+** (22.20+ for `npx skills add`) | the skills, and rendering | [nodejs.org](https://nodejs.org) `.pkg` — double-click, no terminal |
| **`uv`** | the engine, without touching your system Python | `curl -LsSf https://astral.sh/uv/install.sh \| sh` — 2s, no admin |
| **`ffmpeg`** and **`ffprobe`** | nearly every program | `brew install ffmpeg` |
| **Python 3.11+** | the engine | uv fetches its own — you do not need to install one |

Two things that bite people, both verified rather than guessed:

- `/usr/bin/python3` on a Mac is **not** a Python. It is an `xcrun` shim sharing an inode
  with `/usr/bin/git`, and on a machine without Xcode Command Line Tools it pops a ~2GB
  install dialog. That is why the engine install below goes through `uv`, which brings its
  own interpreter.
- The uv installer edits your shell profile but **not the shell you are in**. Run
  `source "$HOME/.local/bin/env"` or open a new terminal, or `uv` will be "command not
  found" immediately after a successful install.

### The skills

```bash
npx skills add scrollmark/social-skills
```

Needs Node. If you would rather not install Node, the same thing without it — note the
`--strip-components` and the permanent directory, both of which matter:

```bash
mkdir -p ~/social-skills
curl -Ls https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz \
  | tar xz --strip-components=1 -C ~/social-skills
~/social-skills/install.sh
```

`install.sh` **symlinks** into that directory, so it has to live somewhere permanent —
extract to `/tmp` and every skill dies at the next purge, all at once and with no error.

Every skill is self-contained — it ships the reference files *and the executables* it
needs — so a copied install has the exact same behaviour as a cloned one.

### The engine

The video skills want the Python package. It is independent of the skills, and this route
needs no git, no system Python and no Xcode tools:

```bash
uv tool install --python 3.12 --refresh \
  'video-studio-engine[standard] @ https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz'
```

Three details are load-bearing:

- **A tarball URL, not `git+https`.** The git form makes pip shell out to `git`; without it
  pip reports *"No matching distribution found"*, and a reasonable person concludes the
  package does not exist. The tarball needs no git at all.
- **`--python 3.12`, pinned.** `requires-python` is `>=3.11` with no ceiling, so uv would
  otherwise pick 3.13 — where the `[audio]` extra's `kokoro` marker excludes it, the
  install succeeds, and you silently have no voice.
- **`--refresh`.** GitHub's tarball endpoint returns only an `ETag`, and uv will serve its
  cached copy indefinitely without so much as an HTTP request. Without this, "reinstall to
  get the latest" quietly lies.

Plain `pip install '<same URL>'` works too if you already have Python 3.11+.

See [What ships where](#what-ships-where) for which skills need it and what skipping it
actually costs.

### For development

```bash
git clone https://github.com/scrollmark/social-skills.git
cd social-skills
./install.sh
```

`install.sh` symlinks each `skills/<name>/` into `~/.claude/skills/social-skills--<name>`,
so edits in your clone take effect immediately. It is idempotent — re-run it any time,
including after pulling new skills — and it prunes links whose skill no longer exists.
Set `CLAUDE_SKILLS_DIR` to install somewhere other than `~/.claude/skills`.

Install a subset by naming the skills, which is worth doing if you only want the
social-media half or only the video half:

```bash
./install.sh trend-radar hook-anatomy    # just these two
./install.sh --list                      # what is available
```

An unknown name is an error rather than a silent no-op, and a partial install never
prunes skills it was not asked about.

Either way, skills become available in your next Claude Code session. Neither route
installs `video-studio-engine`, `ffmpeg`, or Node — those are yours to install, and the
skills say so where it matters rather than failing halfway through a run.

## Uninstall

```bash
./uninstall.sh              # everything
./uninstall.sh trend-radar  # just one
```

Removes every `social-skills--*` entry from your skills directory (symlinks and copies
alike) and deletes any stale `.root` files left behind by older versions of `install.sh`.

## Self-contained skills

Every skill folder stands on its own. `skills/<name>/` contains its `SKILL.md` plus its
own `references/` and, where it has one, its own `scripts/`. A `SKILL.md` never points at
anything above its own directory.

That is what makes the two install routes equivalent. Earlier versions resolved reference
paths through a `.root` file that only `install.sh` wrote, so `npx skills add` installs
silently ran without their references. The shared reference files under the repo-root
`references/` remain the canonical source and are copied into each skill that uses them.

**This is why the engine's dependency-heavy programs are a pip install and not a relative
path.** A skill that reached into `../../src/` would work under `install.sh` — which
symlinks, so the path resolves — and dangle under `npx skills add`, which copies. The two
install routes would silently disagree. Anything a skill cannot carry in its own folder is
reached by name through an installed package instead.

Run `./scripts/verify-skills.sh` to check the invariant. It also checks that every bundled
script a `SKILL.md` names actually exists, that nothing is shipped under `scripts/` that
the `SKILL.md` never invokes, and that a script shipped by two skills is byte-identical in
both.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Structural history — the self-containment fix, the
video-studio split, and the consolidation that ended it — is in
[MIGRATION-NOTES.md](MIGRATION-NOTES.md).

## License

MIT — see [LICENSE](LICENSE). Covers everything in this repo: the prose, the bundled
scripts, and the `video-studio-engine` package built from `src/`.
