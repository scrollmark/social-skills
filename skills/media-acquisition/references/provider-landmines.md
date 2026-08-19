# Provider landmines — footage and stills

Every entry here was paid for in real money or in an afternoon. They share a
shape: the call succeeds, or appears to, and the defect surfaces much later.

## Errors that arrive looking like success

- **MiniMax (Hailuo)** returns application errors *inside HTTP 200*. Check
  `base_resp.status_code != 0` or you will poll a bogus task id for ten
  minutes. `1008` is out of balance.
- **Submitted MiniMax jobs bill even if you never download the result.** Do not
  kill a poll loop mid-run to save money; the money is already spent.

## Duration and aspect constraints that reject silently or late

- **MiniMax 1080P generates 6s clips only.** Asking for 10s errors (2013). 768P
  allows 10s. Output is landscape-only — vertical means a centre crop
  downstream, so keep subjects centred in the prompt.
- **Veo accepts durations {4, 6, 8} only.** The docs say "4 to 8 inclusive";
  5 and 7 are rejected.
- **Veo's `generate_audio` is refused on plain API-key auth** (enterprise only).
  Irrelevant here anyway — we supply our own voice and music, so paying the
  8x audio-inclusive tier buys something we discard.
- **Veo shares the text API key but has a separate, much smaller video quota.**
  Probe with one 4s clip before planning a batch.

## Generated footage caps below scene length

Generated video caps around 6s while narration-driven scenes often run longer,
so a clip shorter than its scene is the common case, not the exotic one. In the
composer this freezes on the last frame rather than looping — the video element
has no loop property and passing one is silently ignored. The props builder
probes source length so the layer can be wrapped in a loop; if that probe is
skipped the freeze ships.

## Endpoints rot, and nothing tells you

The image script targeted an endpoint that began answering `404 ... no longer
available to new users` for every model in the family — fast, standard and
ultra alike. Nothing had called it in weeks, so nobody knew. Two durable
lessons:

- A model listed by the provider's own model-list call may still be uncallable.
- Published cURL examples can be wrong for your API version. One documented
  field name took an enum and rejected every string form; the working field had
  a different name entirely.

**Treat the first call of any provider script in a session as a smoke test**,
not a guarantee.

## A 429 is not always a rate limit

Gemini image models have **no free tier**. The quota metrics report no limit at
all, and a full day's wait changes nothing — it is a billing gate wearing a
rate-limit costume, made more convincing by text models on the same key
answering fine. Never tell someone to wait for the reset.

Related: **Lyria's free-tier quota is literally zero** for the same reason.

## Anonymous access that is really a cache hit

Pexels needs a key from request one. A handful of popular queries answer
without one, which looks like a free anonymous tier; they are CDN cache hits —
`query=sky` came back `cf-cache-status: HIT`, `age: 17118`, a nearly five-hour
old copy of somebody else's authenticated request. Any query that actually
reaches the API 401s.

**Shutterstock splits search from download.** Search works on the free tier at
100 requests/hour — and one video consumed ~50 searches including replacements,
so a couple of videos an hour is the ceiling. Downloading needs a paid
subscription on top of API access; there is no free download path.

**Pixabay requires results to be cached for 24 hours.** Store them; do not
re-query per render.

## Single-provider categories are a trap

Generated images had exactly one wired provider. When it turned out to be
billing-gated the whole category went to zero with no fallback. Categories with
a keyless free floor (archives) or two independent sources (stock) degraded
gracefully. When a category has one provider, say so before it is relied on.

## Content rules for generation

- **No readable text in prompts.** Models render pseudo-text; garbled signage
  was the single largest QC error class across three rounds. Exact digits are
  especially unreliable — a request for $260 rendered as "250/month".
- **Unprompted background text still appears** on storefronts and labels. Catch
  it on a frame check and regenerate that clip only.
- **Identity across scenes:** repeating descriptors verbatim reduces drift but
  does not eliminate it. Separate generations of the same descriptor produced a
  visibly different person roughly one time in four. The only guarantee is
  reusing the same actual footage.

## Keying a generated clip

Generated "green screens" are never studio green — a real MiniMax key sampled
at ~0x28680C. Sample the clip's own corner rather than assuming a value at
prompt-writing time, and key with a hard cutoff: any soft blend leaves dark
hair semi-transparent against a dark desaturated key.
