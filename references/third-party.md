# Third-party tools — inventory, triage, and how to switch each on

`providers.md` answers "which source should this SHOT use". This answers
"what exists, what is on, and what should I turn on next". Run
`doctor.py` (bundled in studio-setup) for live status on the current machine; this file is the
map, not the state.

Every entry below is something a bundled script actually calls. Nothing here is
aspirational.

---

## Triage

**Tier 0 — without these, nothing works.**

| Tool | Why | Activate |
|---|---|---|
| `ffmpeg` + `ffprobe` | Every duration measured, every clip trimmed, all loudness and keying. 19 call sites | `brew install ffmpeg` |
| `node` 18+ | The composer renders and previews through it | `brew install node` |
| `uv` | Runs every bundled script with its own pinned dependencies | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

**Tier 1 — free, no billing, and the single biggest jump in quality.**

| Tool | Gives you | Activate |
|---|---|---|
| **Pexels** | Modern everyday footage and stills. The one key that converts "find me footage of that" from a coin-flip into the normal answer | `PEXELS_API_KEY` — free at pexels.com/api |
| NASA archive | Space, earth, science. Public domain | nothing — no key at all |
| Wikimedia Commons | History, places, artefacts. Licence varies per item; the script filters | nothing — no key at all |
| Local voice | Narration, generated on your own machine | nothing — runs locally |

**If you add exactly one thing on this whole page, add Pexels.**

**Tier 2 — free keys, worth having, narrower use.**

| Tool | Gives you | Activate |
|---|---|---|
| Pixabay | Second stock library. Useful when Pexels is thin on a subject | `PIXABAY_API_KEY` |
| Freesound | Sound effects. Licence varies per sound; the script filters | `FREESOUND_API_KEY` |

**Tier 3 — paid. Quote the cost before spending, every time.**

| Tool | Cost | Rights | Activate |
|---|---|---|---|
| Gemini image | ~0.02–0.03/still | Clean | `GEMINI_API_KEY` — needs billing, no free tier |
| Veo | ~0.40/s | Clean | `GEMINI_API_KEY` — free-tier quota is tiny |
| MiniMax video | ~0.36 per 6s clip | Clean | `MINIMAX_API_KEY` |
| **ElevenLabs Music** | **from ~6 USD/mo** | **Clean — trained only on licensed catalogue (Merlin, Kobalt)** | `ELEVENLABS_API_KEY` |
| Lyria (Google) | Paid | Clean | `GEMINI_API_KEY` — free-tier quota is literally 0 |
| MiniMax music | Works unbilled | **UNSETTLED — internal use only** | `MINIMAX_API_KEY` |
| Luma (via Replicate) | ~0.075/clip | Per-model | `REPLICATE_API_TOKEN`, `--preset luma` |
| Runway (via Replicate) | ~0.40-0.48/clip | Per-model | `REPLICATE_API_TOKEN`, `--preset runway` |
| Shutterstock | Search free; **download needs a subscription** | Standard licence | `SHUTTERSTOCK_TOKEN` |
| Replicate | Varies | Varies per model | `REPLICATE_API_TOKEN` — one key, many models |

**The music rights split is the most consequential line on this page, and it is
cheaper to fix than it looks.** MiniMax music generates without billing, which
makes it the path of least resistance, and its output rights are unsettled.
ElevenLabs Music is trained *exclusively* on licensed catalogue through Merlin
and Kobalt partnerships, and commercial use is included from roughly six
dollars a month. For anything that will be published, that is the answer — the
barrier was never really cost, it was that nobody had priced it.

Two others worth knowing and NOT integrated: Suno has the best measured output
quality but no official API and unsettled licensing with lawsuits in flight;
Udio has clean deals (UMG, Warner, Merlin, Kobalt) but no public API below its
enterprise tier. ElevenLabs is currently the only one that is both clean and
reachable. Say which backend is in use BEFORE the user chooses,
because the entire cut ends up shaped around whichever track arrives — a rights
problem found afterwards means re-cutting, not re-tagging.

**Tier 4 — present in the code, not currently reachable.**

| Tool | State | Notes |
|---|---|---|
| `showwatcher` | Superseded, never published | Was the intended step-8 gate. Replaced by `qc_render.py`, bundled in `video-production` and needing no install, plus `video-studio qc_analyze` for frame-level checks. Judging whether the video is any GOOD still needs human eyes — pull frames and say that you did |
| `yt-dlp` | One call site | Used by `source_clips.py` for `url:` sources. Install with `brew install yt-dlp` if you intend to pull from URLs |

---

## What should we add next

Ranked by what actually went wrong in production rather than by feature count.

1. **A verified-provenance stock source.** The single largest defect class so
   far. Stock search does not respect geography: Japanese queries returned a
   Hawaii temple, English queries returned Turkey twice and Morocco, Mexican
   queries returned San Francisco and Colorado. Twenty-one shots were replaced
   across three videos. `verify_clips.py` now catches duplicates, monochrome
   and short clips, but it cannot verify that a place is the place. A source
   that publishes shoot locations would remove a whole category of manual
   checking.

2. **A checker that can judge the PICTURE.** The mechanical half is covered:
   `qc_render.py` proves a render matches its plan with no install, and
   `qc_analyze` adds blur, off-palette colour, cut placement and caption timing.
   What no tool here reports is whether the video was worth making. That
   remains the one step whose guarantee depends on somebody looking.

3. **Pika, if it ever ships an API worth having.** It is the one major video
   generator with a free tier permitting commercial use — capped at 480p, which
   is below the 1080x1920 every format here renders at, so it buys nothing
   today. It also has no Replicate model, so it would need its own client
   rather than a one-line preset.

4. **A music generator that honours a requested length.** Asking for 140s has
   returned 25s, 66s, 128s and 148s. Every track must be measured after
   generation and the video designed to what arrived. A backend that returns
   the length asked for would remove a re-roll loop.

5. **Face or subject detection for poster frames.** `poster.py` ranks on colour
   and contrast, which is why it put an underwater reef above a marigold market
   for a Mexico spot. A cheap subject detector would fix the one case where the
   ranking is reliably wrong.

6. **A brand-mark detector for generated imagery.** Adobe Firefly is the commercial answer — trained on licensed Adobe Stock, so its output is commercially safe by construction and it would not have produced the swooshes. API access needs an enterprise agreement at roughly 1,000 USD a month, so this is a procurement decision rather than an integration one.

7. **A local brand-mark detector**, for when Firefly is not bought. Image models reproduce real
   trade dress unprompted — a generated sneaker sequence came back with legible
   Nike swooshes and a Jumpman. Currently caught only by zooming frames by
   hand before publishing.

---

## Deliberately not integrated

- **Anything requiring an account to read.** Archives and stock that need a
  login break the "make a whole video without signing up for anything" promise.
- **Paid stock libraries.** The free tier covers everyday subjects well enough
  that per-clip licensing is not justified for this pipeline's output.
- **Cloud rendering.** The composer renders locally in minutes; a queue and a
  bill would buy nothing at this scale.

---

## Activation, end to end

```bash
cd /path/to/video-studio
cp .env.example .env          # gitignored
$EDITOR .env                  # paste the keys you have
the doctor script bundled in studio-setup      # what is reachable right now
video-studio setup       # what is missing and what can be installed
video-studio setup --yes # actually install it (asks first, changes your system)
```

Keys live in `.env` at the repo root. Every script reads plain environment
variables, so exporting them by hand works identically — the file just saves
doing it per shell. Holding a key costs nothing; only calls do.
