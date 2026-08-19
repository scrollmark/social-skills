# Third-party tooling — inventory, triage, and how to switch each on

What exists, what it costs, what it buys, and how to turn it on. This is the
map. Run `doctor.py` (from scrollmark/video-studio) for live state on the
machine in front of you — this file never knows whether a key is set.

Every entry is something a bundled script actually calls. Nothing here is
aspirational.

---

## Tier 0 — without these, nothing works

| Tool | Why | Activate |
|---|---|---|
| `ffmpeg` + `ffprobe` | Every duration measured, every clip trimmed, all loudness and keying | `brew install ffmpeg` |
| `node` 18+ | The composer renders and previews through it | `brew install node` |
| `uv` | Runs every bundled script with its own pinned dependencies | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

## Tier 1 — free, no billing, the single biggest jump in quality

| Tool | Gives you | Activate |
|---|---|---|
| **Pexels** | Modern everyday footage and stills. The one key that converts "find me footage of that" from a coin flip into the normal answer | `PEXELS_API_KEY` — free at pexels.com/api |
| NASA archive | Space, earth, science. Public domain | nothing — no key at all |
| Wikimedia Commons | History, places, artefacts. Licence varies per item; the script filters | nothing — no key at all |
| Local voice | Narration generated on the user's own machine | nothing — runs locally |

**If you add exactly one thing on this page, add Pexels.**

## Tier 2 — free keys, narrower use

| Tool | Gives you | Activate |
|---|---|---|
| Pixabay | Second stock library, for subjects where Pexels is thin | `PIXABAY_API_KEY` |
| Freesound | Sound effects. Licence varies per sound; the script filters | `FREESOUND_API_KEY` |

## Tier 3 — paid. Quote the cost before spending, every time

| Tool | Cost | Rights | Activate |
|---|---|---|---|
| Gemini image | ~0.02–0.03 / still | Clean | `GEMINI_API_KEY` — needs billing, no free tier |
| Veo | ~0.40 / s | Clean | `GEMINI_API_KEY` — free-tier quota is tiny |
| MiniMax video | ~0.36 per 6s clip | Clean | `MINIMAX_API_KEY` |
| **ElevenLabs Music** | **from ~6 USD/mo** | **Clean — licensed catalogue only (Merlin, Kobalt)** | `ELEVENLABS_API_KEY` |
| Lyria (Google) | Paid | Clean | `GEMINI_API_KEY` — free-tier quota is literally 0 |
| MiniMax music | Free tier available | **Rights unclear for commercial redistribution — verify before client work** | `MINIMAX_API_KEY` |
| Luma / Runway (via Replicate) | ~0.075 / ~0.40–0.48 per clip | Per-model | `REPLICATE_API_TOKEN` |
| Shutterstock | Search free; **download needs a subscription** | Standard licence | `SHUTTERSTOCK_TOKEN` |

**The music rights split is the most consequential line here, and cheaper to
fix than it looks.** MiniMax music has a free tier, which makes it the path of least resistance,
and its output rights are unclear for commercial redistribution. ElevenLabs
Music trains exclusively on licensed catalogue and includes commercial use from
roughly six dollars a month. For anything that will be published, that is the
answer. Say which backend is in use BEFORE the user chooses — the whole cut
gets shaped around whichever track arrives, so a rights problem found
afterwards means re-cutting, not re-tagging.

Two others worth knowing and not integrated: Suno has the best measured output
but no official API and lawsuits in flight; Udio has clean label deals but no
public API below enterprise.

## Tier 4 — present in the code, not currently reachable

| Tool | State | Notes |
|---|---|---|
| `showwatcher` | **Not installed, on any machine seen so far** | The automated quality gate in step 8. Internal tool, installed from its own repo. Without it, verify frames by hand and SAY that you are doing so |
| `yt-dlp` | One call site | Used for `url:` sources. `brew install yt-dlp` if you intend to pull from URLs |

---

## What to add next

Ranked by what actually went wrong in production, not by feature count.

1. **A verified-provenance stock source.** The largest defect class so far.
   Stock search does not respect geography: Japanese queries returned a Hawaii
   temple, Mexican queries returned San Francisco and Colorado. Twenty-one
   shots were replaced across three videos. Automated checks catch duplicates,
   monochrome and short clips; they cannot verify that a place is the place.
2. **`showwatcher`, actually installed.** Documented as step 8, absent
   everywhere, so every render has been verified by hand. It is the only step
   whose guarantee depends on somebody remembering.
3. **A music generator that honours a requested length.** Asking for 140s has
   returned 25s, 66s, 128s and 148s. Every track must be measured after
   generation and the video designed to what arrived.
4. **Subject detection for poster frames.** Ranking on colour and contrast put
   an underwater reef above a marigold market for a Mexico spot.
5. **A brand-mark detector for generated imagery.** Image models reproduce real
   trade dress unprompted — a generated sneaker sequence came back with legible
   swooshes. Currently caught only by zooming frames by hand before publishing.

## Deliberately not integrated

- **Anything requiring an account to read.** Archives and stock behind a login
  break the "make a whole video without signing up for anything" promise.
- **Paid stock libraries.** The free tier covers everyday subjects well enough.
- **Cloud rendering.** The composer renders locally in minutes; a queue and a
  bill would buy nothing at this scale.

## Activation, end to end

```bash
cp .env.example .env          # gitignored
$EDITOR .env                  # paste the keys you have
uv run scripts/doctor.py      # what is reachable right now
uv run scripts/setup.py       # what is missing and what can be installed
uv run scripts/setup.py --yes # actually install it — ask the user first
```

Keys live in `.env` at the toolchain root. Every script reads plain environment
variables, so exporting by hand works identically; the file just saves doing it
per shell. Holding a key costs nothing — only calls do.

## What this actually runs on

User-facing prose says "the editor", "the quality check", "the built-in voice".
Behind those names: Remotion 4.0.x for composing and rendering, showwatcher for
the quality gate, MiniMax and Veo for clip generation, Kokoro locally for
voice, MediaPipe HandLandmarker for gesture analysis, ffmpeg for probing and
keying. The abstraction exists because every row is expected to change and because a
creative session is the wrong place to field "why MiniMax?". Answer honestly
whenever asked — this is about not volunteering implementation detail
mid-session, not concealing it. Licence terms for every service are in
SERVICES.md.
