# Social Skills

Claude Code skills for social media and short-form video. Because even AI needs social
skills.

## What is this?

A collection of installable [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code)
covering two related jobs:

- **Understanding social media** — tone, hooks, trends, platform conventions, creator voice.
- **Producing short-form video** — scene grammars, brand consistency, and the interview
  protocol used to pin down a plan before anything is built.

Everything here is **prose**. These skills teach Claude how to think about a problem; they
do not ship a renderer, a model, or a pipeline. A few of them describe work that a
separate engine performs — see [The video-studio boundary](#the-video-studio-boundary).

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

Craft skills for planning a short-form video. The planning is standalone; some of what
they describe is executed by the video-studio engine.

| Skill | Use when | Standalone? |
|-------|----------|-------------|
| `video-formats` | Planning, structuring, or critiquing a short-form video — choosing a format, laying out its scenes, or defining a new format. Covers ten scene grammars from talking-head to hand-drawn motion graphics. | Mostly — 8 of the 10 formats are pure structure. **Boil** and **PointerPopups** are not (see below). |
| `brand-kit` | A user wants their videos to stay visually consistent — saving caption styling, card colours and geometry, title treatment, logos, fonts, voice and CTA copy once instead of redeciding them per video. | Deciding and recording a brand, yes. Applying it automatically at render time needs the engine. |
| `media-acquisition` | Deciding where a shot's footage or stills should come from — public-domain archive, free stock, a paid generator, or a URL the user supplied — and when checking that what came back is actually usable before anything is built on it. | **No.** It is a selection rule wrapped around ten sourcing scripts; without them nothing searches, generates, or checks what arrived. |
| `audio-acquisition` | A video needs narration, a music bed or sound effects — choosing a voice, deciding which music source is safe to publish with, timing a cut to a track, or fixing a render that came out quiet. | Partly. The rights tiering and mixing discipline read as a briefing; synthesis, measurement and licence filtering are the engine. |
| `subject-compositing` | A filmed person has to appear somewhere they never were — dropping a subject over replacement footage, putting a drawn prop in front of them, driving the pair across frame, or pinning popup images to where they point on camera. | **No.** The segmentation, occlusion seam, arm punch-through and gesture timing are all engine scripts. What survives is knowing what footage to shoot. |
| `edit-handoff` | A finished cut has to leave the pipeline and continue in a human editor — exporting a timeline to Premiere Pro, DaVinci Resolve, Final Cut Pro or CapCut, or answering what survives the trip and what an editor has to rebuild. | **No.** The exporters read the engine's timeline document; there is no degraded mode that still writes a file. The format judgement generalises. |
| `video-production` | Actually producing a short-form video end to end — running the interview, storyboarding, sourcing, previewing, rendering and quality-checking in order — or when a run has stalled and you need to know which step comes next and who owns it. | **No.** It drives the whole engine: without the private repo there is no props document, no preview, no renderer and no preflight. The step order and the hard rules still read as a production discipline. |

### Working method and toolchain

| Skill | Use when | Standalone? |
|-------|----------|-------------|
| `agent-interview` | You need to ask a user a series of decisions — a guided setup, an intake, a wizard, an onboarding walkthrough — and want the questions to be answerable rather than open-ended. | Yes. Nothing video-specific in it. |
| `studio-setup` | Checking whether a machine can actually produce video, triaging a pipeline that stopped working, or deciding which third-party tool or API key to add next. | Partly. Its tooling inventory is readable by anyone; the status report, install plan and triage come from `doctor.py` / `setup.py` in the private repo. |

<!-- END SKILLS TABLE -->

Every row's "Use when" text is the skill's own frontmatter `description`, copied verbatim,
so this table cannot quietly drift from the skills. `./scripts/verify-skills.sh` fails if a
skill is missing from it.

## The video-studio boundary

This repo is one half of a deliberate split.

- **Here (public):** the prose. Formats, grammars, interview protocols, brand vocabulary,
  the judgement calls. Readable and useful on its own.
- **Elsewhere (private):** `scrollmark/video-studio` — the Python and Remotion toolchain
  that actually composites, generates, tracks, and renders. It is **invoked, never
  vendored**. No script from it is copied into this repo, and no skill here bundles one.

If you do not have access to video-studio, here is exactly what that costs you:

- The **seven social-media skills** are entirely unaffected. So is `agent-interview`.
- `video-formats` still works for eight of its ten formats. Composition, Interview, Slots
  and Grammar are structural; you can follow them with any editor.
- **`boil` is roughly 40% inoperative.** Its mark vocabulary, shape files and palette
  workflow are `gen_boil.py`; without it, the interview questions have no answers to pick
  from and you are reading a style description, not instructions.
- **`pointer-popups` does not work at all as written.** Its entire grammar is the output of
  a `track_pointing.py` hand-tracking pass — popup position and timing come from the
  tracker, not from a storyboard you write. Without the tracker there is nothing to follow.
- `brand-kit` lets you agree a brand with a user and hand-write the files. The preset
  mechanism — `--list`, `--show`, `--apply`, `--save` — is `styles.py`, and nothing expands
  a preset into a storyboard without it, so applying a brand becomes manual editing.
- **`media-acquisition` does not work standalone.** The provider ladder, the shot-type
  corollary and the landmine file are readable and will tell a human which library to
  open — but the searching, generating, licence filtering and the five-way check on what
  came back are all `source_clips.py`, the `stock_*` scripts, the `gen_*` scripts and
  `verify_clips.py`. Without them it is a briefing document, not a workflow.
- `audio-acquisition` keeps the part that matters commercially — which music source is
  safe to publish with, and why the free one is not — plus the measure-don't-trust
  discipline. Synthesis, loudness measurement and the per-sound licence filter are
  `tts_kokoro.py`, `tts_eleven.py`, `gen_music.py`, `stock_freesound.py`, `measure.py`
  and `normalize_audio.py`.
- **`subject-compositing` is entirely engine-side.** `composite_subject.py` does the
  segmentation, the feathered occlusion seam and the arm punch-through;
  `track_pointing.py` does the gesture timing. Without them there is no shot. The one
  part that survives is the footage brief — what a selfie segmenter needs from a take —
  and it is worth having before anyone films.
- **`edit-handoff` cannot produce a file without the engine.** `export_edit.py`,
  `export_fcpxml.py` and `export_capcut.py` all read video-studio's per-project timeline
  document. What generalises is the judgement: which format each application actually
  imports, and that no interchange format carries effects.
- **`video-production` is the one skill that is purely the engine's driver.** It sequences
  `setup.py`, `build_props.py`, `studio.py`, `preflight.py`, the Remotion renderer,
  `normalize_audio.py` and `poster.py`; with none of those present there is nothing to sequence.
  What survives is the shape of a production run — which decision must precede which, where money
  enters, and the `references/hard-rules.md` list of things that already went wrong once.
- `studio-setup` keeps its tooling inventory, but the single status report, the install
  plan and the auto/system/manual classification all come from `doctor.py` and `setup.py`.
  You can still check binaries by hand.

Each of those skills states its own dependency in a `## Requires` section near the top —
that is where the authoritative answer lives, not here.

Format files also name other pipeline scripts (`measure.py`, `styles.py`) in their *Render
notes*. Those are practical traps recorded from production, not requirements — the
structural sections above them stand without any of it.

## Platforms

Primary coverage: **Instagram**, **TikTok**, **YouTube**

Also covered: **X**, **LinkedIn**

## Install

### For users (recommended)

```bash
npx skills add scrollmark/social-skills
```

This copies each skill folder into your Claude Code skills directory. Every skill is
self-contained — it ships the reference files it needs — so a copied install has the
exact same behaviour as a cloned one.

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
installs, downloads, or requires video-studio.

## Uninstall

```bash
./uninstall.sh              # everything
./uninstall.sh trend-radar  # just one
```

Removes every `social-skills--*` entry from your skills directory (symlinks and copies
alike) and deletes any stale `.root` files left behind by older versions of `install.sh`.

## Self-contained skills

Every skill folder stands on its own. `skills/<name>/` contains its `SKILL.md` plus its
own `references/`, and a `SKILL.md` never points at anything above its own directory.

That is what makes the two install routes equivalent. Earlier versions resolved reference
paths through a `.root` file that only `install.sh` wrote, so `npx skills add` installs
silently ran without their references. The shared reference files under the repo-root
`references/` remain the canonical source and are copied into each skill that uses them.

Run `./scripts/verify-skills.sh` to check the invariant.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Structural history — the self-containment fix and
the video-studio split — is in [MIGRATION-NOTES.md](MIGRATION-NOTES.md).

## License

MIT — see [LICENSE](LICENSE). Covers everything in this repo, prose included. It does not
extend to video-studio, which is separately licensed and not distributed here.
