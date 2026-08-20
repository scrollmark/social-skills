# What a generated second costs

Order-of-magnitude list prices in USD, for deciding *what to generate* before
you generate it. Not billing truth: no provider here returns a price with the
asset, so every figure is a published rate or an observed one, and every one of
them drifts. Treat them as an upper bound for planning, then read your invoice.

Consolidated from the figures already embedded in the programs
(`gen_veo`, `gen_minimax`, `gen_image`) plus the two TTS rates, so a format
document can quote one source instead of each program quoting its own.

## Generated video — the dominant cost

| provider | program | rate | 6s clip |
|---|---|---|---|
| Veo 3.1 (Gemini) | `gen_veo` | ~$0.40/s | ~$2.40 |
| MiniMax Hailuo 02 | `gen_minimax` | ~$0.06/s | ~$0.36 |
| Replicate | `gen_replicate` | varies by model — tens of cents for video | — |

Veo is roughly **seven times** MiniMax per second. That ratio, not the absolute
number, is the thing to plan around: a format that wants eight generated scenes
costs about $19 on Veo and about $3 on MiniMax.

⚠️ MiniMax's training-data position is not established. It is fine for internal
and experimental work; it does not go under client deliverables. The same
rights note governs `gen_music` — see the provider notes in that program.

## Generated stills

| model | rate |
|---|---|
| `gemini-3.1-flash-lite-image` | ~$0.01 |
| `gemini-3.1-flash-image` (default) | ~$0.03 |
| `gemini-2.5-flash-image` | ~$0.04 |
| `gemini-3-pro-image` | ~$0.13 |

A still is one to two orders of magnitude cheaper than a clip of the same
subject. A 6s Veo clip is ~$2.40; the same image held with a slow push is ~$0.03.
Most scenes that "need video" need motion, and motion can come from the
composition rather than from the generator — see `gen_boil` for the case where
the motion is drawn instead of generated, at zero marginal cost.

## Narration

| provider | program | rate |
|---|---|---|
| Kokoro | `tts_kokoro` | free — runs locally |
| ElevenLabs | — | ~$0.15 per 1,000 characters |

Narration runs about **15 characters per spoken second** at ~150 wpm, so a
60-second read is ~900 characters: free on Kokoro, ~$0.14 on ElevenLabs.
Narration is never the line item that matters.

## What is free

Stock footage under its own licence, `gen_boil` (drawn, deterministic, no API),
every export path, and all composition. A format built from stock plus boil plus
composition costs nothing per render, which is why `titled-video` and the
stock-sourced half of `brand-origin` can be iterated on without a budget
conversation.

## Where these live in code

`gen_minimax.COST_PER_SECOND`, `gen_image.COST_USD`, and the note at the top of
`gen_veo`. If a rate moves, change it there — those constants are what the
programs actually report in their JSON output — and update this table to match.
