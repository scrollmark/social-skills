---
name: audio-acquisition
description: Use when a video needs narration, a music bed or sound effects — choosing a voice, deciding which music source is safe to publish with, timing a cut to a track, or fixing a render that came out quiet.
---

# Audio Acquisition

Audio is a question, never a leftover. Ask it every time, including for formats with no narration — a silent piece should be silent because somebody chose that, not because nobody raised it. Three decisions, and they have genuinely different answers.

## Requires

`scripts/measure.py` (durations, and a track's per-second energy structure) and `scripts/normalize_audio.py` (loudness) **ship with this skill**. Both are stdlib-only and need `ffmpeg`/`ffprobe` on PATH; nothing else has to be installed for the measure-don't-trust discipline below to be executable rather than aspirational.

Synthesis and sourcing do not ship here. `pip install 'video-studio-engine[audio] @ https://github.com/scrollmark/social-skills/archive/refs/heads/master.tar.gz'` adds `tts_kokoro` (local voice plus word timings) and `gen_music` (score); the same command without the `[audio]` bracket is enough for `stock_freesound` (effects, licence-filtered). Run them as `video-studio tts_kokoro …`. The same `[audio]` bracket also carries
`duck_music` (a per-frame volume envelope so the bed drops under narration) and
`music_catalog` (tracks you already hold a licence for, picked deterministically
so a re-render never changes the score). Narration this studio did not speak —
a recorded read, a supplied track — gets word timings from `gen_captions`, which
needs the `[captions]` bracket instead. **A user who skips that install has no voice, no music and no licence-filtered effects** — the tiering below still tells them which service to buy and what to check, but nothing synthesises. ElevenLabs has a script now — `video-studio tts_eleven` — but it bills per character and needs `ELEVENLABS_API_KEY`, so reach for it only when the local voice genuinely will not do: a language Kokoro does not speak, or a delivery the client has signed off on. It returns no word timings, so captions for an ElevenLabs read come from `gen_captions`.

## Voice

**The local voice is the default and it is free.** It runs offline, needs no key, and — the part that matters structurally — it returns **word timings**, which are what captions are driven by. A captioned format has no other option.

Reach for the paid voice only when the read itself is the deliverable: a brand film, a client voice, anything where a flat delivery is the thing someone would complain about. It bills per character (~1,100 characters is a 90-second script) and it returns **no word timings**, so a captioned format still needs the local voice underneath.

Both cache: identical text, voice and settings is a no-op reporting `cached: true`, so re-running every scene on a revision costs nothing and only the changed lines re-synthesise. **Do not force a re-render to "make sure it's fresh"** — a fresh synthesis can come back a few milliseconds different, and that shifts every cut after it.

Narration is synthesised **first**, before footage, because measured narration duration is the scene clock. Never write an empty line to the synthesiser; ask it for measured silence instead, so downstream concatenation stays aligned.

## Score — a rights decision before it is a taste decision

This is the one category where the quality leader is the wrong answer, and the choice must be made **before** the cut is built around a track.

- **If the piece will ever be published, use a licensed-catalogue generator.** The ElevenLabs music model trained on licensed catalogue with terms settled before launch, and commercial use starts around six dollars a month — so the rights caveat is a pricing decision rather than a constraint. It is also the only one that takes an exact length as a parameter.
- **Lyria is clean under Google's terms** and shares the same key as the video and image generators, so it adds no account. Its free-tier quota is literally zero, which surfaces as a 429 that never clears.
- **MiniMax music is free, unbilled, and its redistribution rights are unclear** — the training data is undisclosed and the terms do not clearly grant redistribution of generated output. Fine for internal and demo work, never under client work, and it should be reachable only by name rather than by an auto-pick.
- **The best-sounding options are the ones to avoid.** Unresolved training-data litigation, and mostly no public API to automate against anyway.

Costs and licence terms per service are tabulated in the `studio-setup` skill's `SERVICES.md` — read the rights column, not the price column, before publishing.

**For a music-led format the score is the FIRST question of the interview, not the last.** Scene durations are cut to the track's energy envelope, so choosing it late means re-timing every scene. Get the track, map it, then set durations.

## Effects

Usually none. Offer them only when the format calls for them and the effects source is actually reachable. Freesound licences vary **per sound** — CC0, CC-BY, CC-BY-NC — so the default accepts CC0 only, nothing downstream carries an obligation, and widening to CC-BY means you must place the returned credit. Non-commercial licensed sound cannot go into client work at all.

## Measure, Do Not Trust

**Requested length is a hint, not a contract.** Most music generators take duration in the prompt and ignore it — one returned ~115 seconds for a 35-second ask. Only the licensed-catalogue one accepts a real length parameter. Measure every returned file; never write a planned duration into the timeline.

**Cut to where the track actually changes.** `scripts/measure.py --music` reports a per-second loudness profile and the transitions — points where a window jumps or drops at least 3 dB against the trailing three seconds. Those are the drops and lifts, and they are the only defensible places to change section. Sections placed on a grid drift out of phase within about twenty seconds and read as arbitrary; a fade placed in the quiet bar before a final chorus sounds like the video was cut off, because it was.

**Adding music silently costs 6 dB.** Tracks are summed by a mixer that divides by the number of inputs, so one music track turns 1 input into 2 and halves everything — narration included. Measured: voice at -17.3 dB without music and -23.5 dB with; the whole video -14.4 LUFS to -20.3 LUFS. Nothing looks wrong. The render succeeds, the balance is correct because both sources scaled equally, and the result is simply quiet — the one defect that survives every visual check. **Run `scripts/normalize_audio.py --in <render>` after any render with music**; it restores about -14 LUFS and preserves the balance. Generated music can also arrive peaking at 0 dBFS, so there is no headroom to lose.

**Mix a bed by probing, not by guessing.** A bed generated at -15 LUFS with a -17 dB gain and an aggressive sidechain came out completely inaudible, and every level probe read within ±0.2 dB of the un-bedded mix — nothing in the logs said so. Verify by measuring RMS in a speech gap against RMS under loud speech: a bed should lift the gaps by roughly 6 dB and vanish under the loudest line.

Voice-specific traps — how punctuation is stamped in the timing file, why a cached WAV has no timings, why a two-word line garbles — are in `references/voice-landmines.md`.

## Anti-patterns

- **Choosing a score by sound and discovering the rights afterwards.** A rights problem found after the edit means re-cutting, not re-tagging.
- **Letting silence happen by omission.** Ask; then a silent piece is a choice.
- **Writing planned durations into the timeline.** Measured audio is the clock. Planned durations desync audio, video and captions cumulatively.
- **Declaring a mix done without measuring it.** Quiet and inaudible both render successfully and both look perfect on every frame you check.
