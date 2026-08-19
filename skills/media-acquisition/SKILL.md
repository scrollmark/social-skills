---
name: media-acquisition
description: Use when deciding where a shot's footage or stills should come from — public-domain archive, free stock, a paid generator, or a URL the user supplied — and when checking that what came back is actually usable before anything is built on it.
---

# Media Acquisition

One shot, one source, decided by a rule rather than by which vendor sounds impressive. Apply it **per shot**, never per project — a single video routinely mixes all four tiers.

## Requires

The sourcing scripts from **scrollmark/video-studio** (private): `source_clips.py` (user URLs and licence-filtered search), `stock_archive.py`, `stock_pexels.py`, `stock_pixabay.py`, `stock_shutterstock.py` (stock), `gen_image.py`, `gen_veo.py`, `gen_minimax.py`, `gen_replicate.py` (generation), `verify_clips.py` (the return check) and `prekey.py` (keying a generated clip to alpha).

**This skill is not usable standalone.** It is a selection rule wrapped around ten scripts. Without them you keep the ladder as a briefing document — it will tell a human which library to open and why — but nothing searches, nothing generates, nothing checks what arrived, and the licence filtering that makes the tiers safe is inside the scripts, not in this prose.

## The Ladder

    1. Does the subject exist in the real world?
       NO  -> GENERATE (fictional product, invented scene, stylised abstraction)
    2. Is it public, historical, scientific, civic or natural?
       YES -> ARCHIVE  (free, no key: space, weather, wildlife, infrastructure, record)
    3. Is it everyday or commercial — interiors, people at work, food, cities?
       YES -> STOCK    (free with a key, modern catalogues)
    4. Otherwise GENERATE. Then: does the MOTION carry meaning?
       YES -> generate video    (a person acting, a process, a camera move)
       NO  -> generate a STILL + camera drift  (~10x cheaper, and steadier)

**Ordered by how likely the result is to be wrong, not by quality.** Every failure this pipeline has actually shipped came from generated footage — invented pseudo-text on a prop, an unplanned cut mid-clip, a presenter whose face changed between scenes. Real footage has none of those modes, costs nothing, and is already licensed. Generation is the fallback.

**Archives go first among the free tiers** because they need no credential at all, which makes them the only sources guaranteed to work on a fresh machine. Their honest limit: deep on science, space, history and nature; thin to absent on staged modern subjects. Check what a query actually returns before promising a scene from them.

**Tie-break on licence breadth, not catalogue size.** Prefer a source whose licence covers the whole catalogue over one that varies per item. An agent choosing hundreds of assets cannot do per-item rights reasoning reliably and one bad pick is a real liability — that is why Pexels outranks the mixed-licence libraries, and why the archive and effects scripts filter by licence rather than trusting search rank.

## Shot Type Beats Subject

The ladder keys on the subject, and that is not sufficient. A plastic toy brick is real, everyday and mass-produced, so step 3 says stock — and stock lost all four brick scenes to paid generation: a studio-lit isolated brick came back as a child with wooden cubes, a macro of the underside came back as a family on a rug.

> **Stock is strong on subjects in context and a desert for objects in isolation.** A studio hero shot, a product macro or a mechanism close-up is a generation job even when the object is utterly ordinary.

Generation's known weaknesses — faces, legible text, identity across shots — simply do not apply to a rigid unbranded object, which is why it wins there. Judge generation per shot, not per video.

**Vocabulary is a sourcing decision.** "block" biases toward wooden cubes and Jenga; "plastic building brick" returns masonry. Search the term people tag with, then re-read the result against the shot you asked for.

## Check What Came Back

Search results are untrustworthy in five specific ways and none of them announce themselves. `verify_clips.py --project <dir>` catches all five — two queries returning the byte-identical clip, a monochrome clip in a colour piece, a clip shorter than its scene (it loops and the jump lands mid-shot), a silent score, narration text with no audio. **Nonzero means do not build.** Orientation mismatch is a warning, not a failure; a 4:3 archival clip in a vertical piece is often deliberate.

Frame-check real footage for unwanted text the same way you would a generated frame. Pseudo-text reads as texture; the stock clip with "MAKE MONEY" burned into it reads as a statement.

**Never regenerate an existing clip.** Cache by scene and layer id under the project directory. Re-fetching to "make sure it's fresh" costs money and can come back a few frames different, which shifts every cut after it.

Provider-specific failure modes — duration limits that are silently rejected, errors delivered inside HTTP 200, endpoints that rot, billing gates that look like rate limits — are in `references/provider-landmines.md`. Read it before quoting a cost or planning a batch. Costs and rights per provider live in the `studio-setup` skill's `SERVICES.md`; check it before anything is published.

## Anti-patterns

- **Defaulting to generation because it always returns something.** It returns something wrong more often than the free tiers do, and it bills for it.
- **Generating video for static b-roll.** A 6s clip is ~$0.36; a still is ~$0.03. If the motion carries no meaning, move the camera in the composer instead.
- **Asking a generator for readable text.** It invents letterforms. Real text is composer typography, every time.
- **Offering a source with no key.** It wastes the user's turn and makes the cost estimate wrong. Check availability before you offer.
- **Treating a user-supplied URL as rights-cleared.** They own that call, but say so out loud when the URL is obviously third-party content.
