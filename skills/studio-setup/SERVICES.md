# External services and their licences

Every third-party service a `studio-setup` workflow can reach, what it costs,
and what you are allowed to do with the output. `references/tooling-inventory.md`
covers how to switch each one on; this file is only about rights.

**Read the rights column before you publish anything.** Generation cost and
usage rights are independent — several of the cheapest options carry the least
certain terms, and a rights problem found after the edit means re-cutting, not
re-tagging.

Terms below were correct when written and are summarised, not quoted. Providers
change them. For anything commercial, confirm against the provider's own licence
page — linked in each row — rather than trusting this table.

---

## Local tools — no service, no licence question

| Tool | Licence | Notes |
|---|---|---|
| `ffmpeg` / `ffprobe` | LGPL-2.1+ / GPL-2.0+ depending on build | Only processes your files; nothing leaves the machine |
| `node` 18+ | MIT | Runtime for the composer |
| `uv` | MIT / Apache-2.0 | Runs the bundled scripts |
| Kokoro (local voice) | Apache-2.0 | Narration synthesised on your own machine; no upload, no per-use terms |
| MediaPipe HandLandmarker | Apache-2.0 | Gesture analysis, runs locally |

Rendering uses **Remotion 4.x**, which is *source-available, not open source*.
It is free for individuals and companies of three or fewer people; larger
companies need a paid Company Licence. See <https://remotion.dev/license>.
This applies to whoever runs the renderer, so it matters for anyone adopting
these skills — not only for Scrollmark.

---

## Stock and archive sources

| Service | Cost | Rights | Licence page |
|---|---|---|---|
| **Pexels** | Free, API key | Free for commercial use, no attribution required; may not be resold as stock or used to train models | <https://pexels.com/license> |
| Pixabay | Free, API key | Free for commercial use; same no-resale restriction | <https://pixabay.com/service/license-summary> |
| NASA archive | Free, no key | Generally public domain, but some material carries third-party rights and NASA's identity may not imply endorsement | <https://nasa.gov/nasa-brand-center/images-and-media> |
| Wikimedia Commons | Free, no key | **Varies per file** — CC0 through CC BY-SA to fair-use claims. The script filters, but attribution is per-item and is yours to carry | <https://commons.wikimedia.org/wiki/Commons:Licensing> |
| Freesound | Free, API key | **Varies per sound** — CC0, CC BY, CC BY-NC. The script filters; NC-licensed sound cannot go in client work | <https://freesound.org/help/faq> |
| Shutterstock | Search free; **download requires a subscription** | Standard licence covers most commercial use; extended licence needed for merchandise or resale | <https://shutterstock.com/license> |

Wikimedia and Freesound are the two that need care: both are per-item, so a
single clip can carry an obligation the rest of the timeline does not.

---

## Generative services

| Service | Cost | Rights | Licence page |
|---|---|---|---|
| Gemini image | ~$0.02–0.03 / still | Clean for commercial use under Google's terms; output not exclusive to you | <https://ai.google.dev/terms> |
| Veo | ~$0.40 / second | Clean under the same Google terms | <https://ai.google.dev/terms> |
| Lyria (music) | Paid, free-tier quota is zero | Clean under the same Google terms | <https://ai.google.dev/terms> |
| MiniMax video | ~$0.36 per 6s clip | Clean for commercial use under MiniMax's terms | <https://intl.minimaxi.com/protocol/terms-of-service> |
| **MiniMax music** | Free tier available | **Unclear for commercial redistribution.** Training data is not disclosed, and the terms do not clearly grant redistribution of generated music. Treat as unsuitable for published or client work until confirmed | <https://intl.minimaxi.com/protocol/terms-of-service> |
| **ElevenLabs Music** | from ~$6/month | **Clean.** Trained exclusively on licensed catalogue (Merlin, Kobalt) and includes commercial use on paid plans | <https://elevenlabs.io/terms> |
| Luma / Runway via Replicate | ~$0.075 / ~$0.40–0.48 per clip | **Per-model** — each model on Replicate carries its own licence; check the specific model page | <https://replicate.com/terms> |

### The music decision, stated plainly

This is the one row where the cheap option and the safe option differ, and it
is the most consequential choice in the table.

MiniMax music has a free tier, which makes it the path of least resistance.
Its rights for commercial redistribution are unclear. ElevenLabs Music is
trained on licensed catalogue and permits commercial use from roughly six
dollars a month.

**For anything that will be published, use ElevenLabs.** Say which backend is
in use *before* the user commits to a track — the whole cut gets shaped around
whichever music arrives, so discovering a rights problem afterwards costs an
edit, not a tag.

---

## Not integrated, but worth knowing

Suno and Udio produce strong output and are both subject to active litigation
over training data. Neither is wired in, and neither should be until that
settles.

---

## If you are adopting these skills

Three obligations travel with you, not with Scrollmark:

1. **Remotion** — a Company Licence if you are a company of more than three people.
2. **Per-item sources** — Wikimedia and Freesound licences attach to individual
   files, so attribution and non-commercial restrictions are yours to honour.
3. **API keys** — every service above bills the key holder. The scripts never
   ship credentials; you supply your own and you pay for your own usage.
