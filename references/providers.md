# Provider options (internal) — opinionated

Researched 2026-08. Prices move; re-check before a big batch. Vendor names
here are internal — see the house-vocabulary table in `SKILL.md`.

**Status legend:** ✅ wired up · 🟡 recommended next · ⛔ deliberately avoided

**Wiring status (2026-08-05):** scripts now exist for every category —
`stock_pexels.py`, `stock_pixabay.py`, `stock_freesound.py`, `gen_image.py`,
`gen_minimax.py`, `gen_veo.py`, `gen_replicate.py` (aggregator: flux /
ideogram / kling / wan / musicgen / stable-audio behind one key),
`gen_music.py`. Run `doctor.py` (bundled in studio-setup) to see which have credentials.
The stock and aggregator scripts are written from documented API shapes but
have NOT been exercised against a live key yet — treat the first call of each
as a smoke test, not a guarantee.

---

## How to be opinionated (the decision rule)

A ranked list is not an opinion — it still leaves the choice open. An opinion
is a rule that **resolves to exactly one answer** for a given shot, and can be
argued with. This is ours; apply it per SHOT, not per project.

```
1. Does the subject exist in the real world?
   NO  -> generate (fictional product, invented scene, stylised abstraction)
   YES -> 2

2. Is it public, historical, scientific, civic, or natural?
   YES -> ARCHIVE tier (free, no key, real, permanently licensed)
          e.g. space, weather, wildlife, infrastructure, historical record
   NO  -> 3

3. Is it everyday/commercial — interiors, people at work, food, cities?
   YES -> STOCK tier (free with a key, huge catalogues, modern look)
   NO  -> 4   (i.e. it exists but nobody has filmed it for you)

4. GENERATE. Then one more question:
   Does the MOTION carry meaning?
   YES -> generate video   (a person acting, a process, a camera move)
   NO  -> generate a STILL + camera drift  (~18x cheaper, and steadier:
          stills cannot warp faces, drift identity, or cut mid-clip)
```

**Why this order and not "best quality first":** every failure this project has
actually shipped came from generated footage — invented pseudo-text on a prop,
an unplanned cut inside a clip, a presenter whose face changed between scenes.
Real footage has none of those failure modes, costs nothing, and is already
licensed. Generation is the *fallback*, not the default, and the ladder above
is ordered by how likely the result is to be wrong rather than by how
impressive the vendor sounds.

**The tie-breaker, when two sources both fit:** prefer the one whose licence
covers the whole catalogue over one that varies per item. An agent choosing
hundreds of assets cannot do per-item rights reasoning reliably, and a single
bad pick is a real liability. This is why Pexels outranks Videvo, and why the
Freesound and Wikimedia scripts filter by licence rather than trusting a
search rank.

**What would change our mind:** a generator that reliably renders legible text
and holds identity across shots would collapse steps 2–4 into "just generate".
Re-run the ladder when that lands; it is a claim about today's failure rates,
not a principle.

---

## Public-domain archives (free, mostly no key)

The tier we were missing. No credential, no billing, no quota — these work on
a machine with nothing configured.

| Archive | What | Key | Status |
|---|---|---|---|
| **NASA Image and Video Library** | 140k+ space/earth/science images, video, audio | none | ✅ wired + verified (`stock_archive.py --source nasa`) |
| **Wikimedia Commons** | Vast; images, some video/audio, per-item licences | none | ✅ wired + verified (`--source wikimedia`, licence-filtered) |
| Internet Archive | Huge; film, stock-footage collection, audio | none | 🟡 next — deepest historical film, but quality varies wildly |
| Library of Congress | US historical photography, film, audio | none | 🟡 strong for archival/period looks |
| Smithsonian Open Access | 4M+ CC0 items, objects and specimens | free key | 🟡 excellent for objects on clean backgrounds |
| Met Museum Open Access | ~500k CC0 artworks | none | 🟡 art/history subjects |
| NOAA / USGS | Weather, ocean, geology, satellite | none | 🟡 natural-world b-roll, US Gov public domain |
| Openverse | Aggregator across CC sources | none | 🟡 one query, many libraries — good discovery, verify licence per hit |
| Flickr Commons | Institutional photo archives, no known restrictions | free key | 🟡 historical photography |

**Opinion:** NASA and Wikimedia first because they need no credential at all —
which means they are the only sources guaranteed to work in a fresh
environment. Internet Archive is the highest-value addition next (deepest
film archive), but its quality floor is low enough that `--list` review
before use is mandatory rather than optional.

**Honest limit:** archives are deep in science, space, history, nature and
civic life, and thin-to-absent on staged modern subjects — a lamp on a desk,
a person using an app, a product on white. Do not promise a scene from these
without checking with `--list` first. The step-3 stock tier exists precisely
to cover that gap.

---

## The headline: stop buying video for static b-roll

A generated 6s clip costs **~$0.36**. A generated still costs **$0.02–0.04**.
Now that the composer has eased Ken Burns drift, a still with `ken` reads as
footage for any b-roll that isn't intrinsically motion (an object, a document,
a place, a product). That is a **~10x cost reduction on the most common b-roll
slot**, and it removes a whole class of generation defects at the same time —
stills don't warp faces, drift identity, or invent motion you didn't ask for.

**Rule of thumb:** generate video only when the *motion itself* carries meaning
(a person acting, a process happening, a camera move through space). Otherwise
generate a still and move the camera in the composer.

This alone would have taken the coffee demo (17 clips, $8.76) to roughly $2.50.

---

## Stock (free, licensed, zero marginal cost)

| Source | What | Terms | Limits | Verdict |
|---|---|---|---|---|
| **Pexels** | Video + images, to 4K | Own licence, commercial OK, **no attribution required** | 200/hr, 20k/mo; lifted free if you display attribution | 🟡 **Primary pick.** Cleanest terms of any free source; one licence for the whole catalogue means the agent can pick without a per-item legal check. |
| **Pixabay** | Video + images, 230k+ clips | Own licence, commercial OK, no attribution | 100/60s; **must cache 24h** | 🟡 Second source — different catalogue, so it widens coverage. The cache rule is a real constraint: store results, don't re-query per render. |
| **Freesound** | Sound effects, field recordings | ⚠️ **Per-sound** CC0 / CC-BY / CC-BY-NC | Throttled, 429s on burst | 🟡 Good for SFX, but licence varies *per item* — filter to CC0 first, CC-BY only if we emit credits. Same discipline as our CC-only footage rule. |
| Videvo / Videezy | Video | Mixed per-clip; some require attribution | — | ⛔ **Avoid for automation.** Per-clip licence variation is fine for a human picking one clip, and a liability when a machine picks hundreds. |

**Opinion:** wire Pexels first and make it the default answer to "find free
online". It is the only source where an agent can choose freely without
per-item licence reasoning, which is exactly what automation needs.

### Subject is not the predictor — shot type is

The rule above keys on the SUBJECT ("real + everyday -> stock"). That is not
enough, and a measured failure shows why.

The brand-origin-brick video was re-sourced from stock on the reasoning that a
plastic toy brick is real, everyday and mass-produced, so stock must cover it.
Stock lost all four brick scenes to the paid generated takes:

| Scene | Needed | Stock returned |
|---|---|---|
| hook | single brick, studio-lit, isolated | a child with WOODEN cubes |
| era-3 | underside macro showing the hollow tubes | a family on a living-room rug |
| era-4 | two bricks engaging, macro | a Jenga tower reading "MAKE MONEY" |
| landing | brick in fingertips, plain ground | the same Jenga tower again |

Stock catalogues are built for lifestyle and editorial use — *people using
things in rooms*. They are not built for **isolated studio product macro**,
which is commissioned work nobody uploads for free. So:

> **Stock is strong on subjects in context, and a desert for objects in
> isolation.** A studio hero shot, a product macro, or a mechanism close-up is
> a generation job even when the object is utterly ordinary.

Two corollaries worth keeping:

- **Generation's known weaknesses did not apply here.** Its failure modes are
  faces, legible text, and identity continuity. A rigid, untextured, unbranded
  object has none of those, which is exactly why it won this comparison. Judge
  generation per shot, not per video.
- **Real footage can carry worse text than generated footage.** The Jenga clip
  had "NARCISSISM" and "MAKE MONEY" burned into the blocks — legible, on-screen
  and wildly off-message. Pseudo-text at least reads as texture; real text reads
  as a statement. Screen stock frames for unwanted text the same way you would
  screen a generated frame.

**Vocabulary matters more than expected.** "block" biases toward wooden cubes
and Jenga; "plastic building bricks" returns masonry walls, because *brick* is
ambiguous. The trademarked term "lego" is well tagged (2,060 video results) and
was the single best query. An earlier note here claimed trademark suppresses
tagging — that was inferred from a 401 with no key, and is wrong.

**Endpoints rot.** `gen_image.py` targeted Imagen's `:predict` endpoint, which
now answers `404 ... no longer available to new users` for every imagen-4.0
model — fast, standard and ultra alike. The script was dead against a current
key and nobody knew, because nothing had called it since. Two lessons encoded
in the script: a model listed by ListModels may still be uncallable (all three
imagen models are listed and all three 404), and the published cURL examples
can be wrong for your API version (they show
`responseFormat.image.aspectRatio`, which takes an enum and rejects every
string form; the working field is `imageConfig.aspectRatio`). Verified
2026-08-05.

**Gemini image models have no free tier.** A 429 on them is not an exhausted
daily budget that will come back tomorrow — it is the absence of any allowance.
All three quota metrics report `limit=None`, and waiting a full day changed
nothing. Text models on the same key answer fine, which makes this easy to
misread as a transient outage; it is a billing gate. Do not tell someone to
"wait for the reset". Verified across 2026-08-05 and 2026-08-06.

**Single-provider categories are a trap.** Generated images had exactly one
wired provider, so when it turned out to be billing-gated the whole category
went to zero with no fallback. Categories with a free, keyless floor (archives)
or two independent sources (stock) degraded gracefully; this one did not.

**Pexels needs a key from request one** — free, no billing, 30 seconds at
pexels.com/api. Do not be misled into thinking otherwise: a handful of popular
queries answer *without* a key, which briefly looked like a free anonymous
tier. They are Cloudflare cache hits — `query=sky` came back
`cf-cache-status: HIT` with `age: 17118`, i.e. a 4.75-hour-old copy of somebody
else's authenticated request. Any query that actually reaches Pexels 401s.
Verified 2026-08-05.

---

## Generated video

| Provider | Price | Notes | Verdict |
|---|---|---|---|
| **Veo 3.1 Lite** | ~$0.05/s | Cheapest credible tier. **We already have the key and `gen_veo.py`.** | 🟡 Make this the default generator; MiniMax becomes the fallback. |
| MiniMax (Hailuo) | ~$0.06/s | 1080P is 6s-only; landscape-only output | ✅ Wired. Fine, but no longer the cheapest. |
| Wan 2.6 | ~$0.05/s | Native 1080p, budget-oriented | 🟡 Worth a bake-off against Veo Lite. |
| Kling 3.0 | ~$0.10/s | Reported to punch above its price | 🟡 Quality tier when a hero shot matters. |
| Runway Gen-4.5 | ~$0.15/s | Best creative-control tooling | 🟡 Reserve for shots needing real direction. |
| Veo 3.1 Standard | ~$0.40/s | Includes native audio | ⛔ For our formats — we supply our own voice and music, so we'd be paying 8x for audio we discard. |

**Opinion:** a three-tier ladder, chosen per shot rather than per project —
**Veo Lite** for ordinary b-roll, **Kling** when a shot is the hero, **Runway**
only when a shot needs directing. Most projects should never leave tier one.

---

## Generated audio

| Provider | Price | Licence | Verdict |
|---|---|---|---|
| **Lyria 3** (Gemini API) | billed per clip | Clean terms; Google-trained on licensed music | 🟡 **The pick when billing is on.** Same `GEMINI_API_KEY` as Veo and the image models, so no new account. ⚠️ **Free tier quota is literally `limit: 0`** — an unbilled project gets a 429 that reads like rate limiting and never clears. Duration is a PROMPT HINT, not a parameter; measure what comes back. |
| **ElevenLabs Music** | ~$0.15/min (API) | Clean commercial terms, settled before launch | 🟡 **The pick when an exact length matters** — it takes `music_length_ms`, the only one here that does. |
| Stable Audio | ~$0.20/generation | Clean commercial terms | 🟡 Viable third source (via the aggregator key). |
| MiniMax music | free tier works unbilled (RPM 3) | ⚠️ Training-data position not established | 🟠 **Internal/experimental only — never under client work.** Deliberately excluded from the `auto` provider chain so it can only be chosen by name. Landmine: `lyrics` is REQUIRED even for an instrumental (omitting it returns status 2013 "invalid params"); pass `"[instrumental]"`. Ignores requested duration — returned ~115s for a 35s ask. |
| Suno / Udio | $10–30/mo | ⚠️ Training-data litigation unresolved; **Suno has no public API, Udio none at all** | ⛔ **Avoid.** Best-sounding output, but we cannot ship client work on unsettled rights, and there's no API to automate anyway. |
| Kokoro (voice) | free, local | — | ✅ Wired. Keep for narration. |

**Opinion:** this is the one category where the quality leader is the wrong
choice. Rights beat sound: Lyria or ElevenLabs on clean terms beats a
better-sounding track we might have to pull later. Revisit if the litigation
settles.

**Mixing a bed (learned by shipping an inaudible one):** measure, do not guess.
A bed generated at −15 LUFS with a −17dB gain and `sidechaincompress
threshold=0.02:ratio=9` came out **completely inaudible** — every level probe
read ±0.2dB against the un-bedded mix, and nothing in the logs said so.
Working values against −14 LUFS dialogue: `volume=-5dB` with
`threshold=0.1:ratio=4:attack=10:release=350`. Verify by probing RMS in a
speech gap versus under loud speech — a bed should lift the gaps by ~6dB and
vanish (~0dB) under the loudest line.

---

## Generated images

| Provider | Price | Notes | Verdict |
|---|---|---|---|
| **Gemini image models** | ~$0.01–0.13 | Same key as Veo | 🟡 **Default still generator** — one credential, clean licence. Needs billing enabled — there is NO free allowance for image models, so this is not a zero-cost option however small the per-still price. |
| Flux 1.1 Pro | ~$0.04 | Strong general quality | 🟡 Second source. Note `[dev]` weights are non-commercial without a licence. |
| Ideogram 3.0 | ~$0.03 | Best at *readable text inside images* | 🟢 Interesting but mostly moot for us: we render text as composer typography precisely because generated text is unreliable. Useful only for signage/props that must look printed. |
| Midjourney | — | More restrictive commercial terms | ⛔ Not for client-facing work. |

---

## Suggested integration order

1. **`gen_image.py` (Gemini image models)** — biggest win per hour of work. Unlocks
   the still+Ken Burns path and the 10x b-roll saving. Existing key.
2. **`stock_pexels.py`** — makes "find free online" genuinely useful and free.
   Replaces the fragile CC-filtered video search as the default.
3. **Default generator → Veo Lite** — a config change plus a bake-off render.
4. **`gen_music.py` (ElevenLabs Music)** — closes the last "supply your own
   file" gap in the cinematic format.
5. Kling / Runway as opt-in quality tiers, once tiering is worth the code.

Each is a script plus a row in the sourcing question — no composer changes,
because every one of them lands as an existing layer type.

## Sources

- [Pexels API](https://www.pexels.com/api/documentation/) · [rate limits](https://help.pexels.com/hc/en-us/articles/900005852323-How-do-I-get-unlimited-requests)
- [Pixabay API](https://pixabay.com/api/docs/)
- [Freesound APIv2](https://freesound.org/docs/api/overview.html) · [terms](https://freesound.org/docs/api/terms_of_use.html)
- [AI video API pricing, July 2026](https://www.buildmvpfast.com/api-costs/ai-video) · [comparison](https://rangy.ai/blog/ai-video-generators-compared-2026/)
- [AI music platforms compared](https://www.digitalapplied.com/blog/ai-music-generation-platforms-suno-udio-elevenlabs-2026) · [music API comparison](https://musicapi.ai/blog/best-ai-music-api-2026)
- [Image API pricing](https://www.buildmvpfast.com/api-costs/ai-image) · [12 providers compared](https://www.digitalapplied.com/blog/ai-image-generation-api-pricing-comparison-2026)
