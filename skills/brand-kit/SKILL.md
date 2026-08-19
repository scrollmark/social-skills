---
name: brand-kit
description: Use when a user wants their videos to stay visually consistent — saving caption styling, card colours and geometry, title treatment, logos, fonts, voice and CTA copy once instead of redeciding them per video.
---

# Brand Kit

A look is something the USER has, not something a project has. It is reusable across every video they will ever make, so it belongs in a file — not inside one generator script, and not in your memory of this session.

## Requires

The preset mechanism is `scripts/styles.py` from **scrollmark/video-studio** (private). Without that script there is no `--list`, `--show`, `--apply` or `--save`, and nothing expands a preset into a storyboard — you can still agree a brand with the user and hand-write the files, but applying it becomes manual editing. `--apply` and `--save` also assume a storyboard JSON in that repo's shape.

## What Ships Today: Look Presets

    uv run scripts/styles.py --list
    uv run scripts/styles.py --show tourism
    uv run scripts/styles.py --apply tourism --storyboard <project>/storyboard.json
    uv run scripts/styles.py --save theirs --from <project>/storyboard.json

A preset is one markdown file: frontmatter (`name`, `description`), prose saying when to reach for it, and a single fenced JSON block holding the values. The JSON covers exactly two things — `captions` (colour, `stroke`, `strokeWidth`, `fontSize`, `wordGap`, `wordsPerPage`, `uppercase`, `bottom`, `palette`) and `cards`, a named role such as `label`, `stat`, `title` or `cta` mapped to `bg`, `fg`, `tracking`, `align` and a `rect`. Unknown keys are reported, not silently dropped, because a misspelled key renders as nothing and reads like a styling choice.

Resolution order, first match winning: `<project>/styles/` → `$VIDEO_STUDIO_STYLES` → the user's own `~/.config/video-studio/styles/` → the presets shipped with the toolchain. The user-level directory is the load-bearing one; a preset kept in a checkout dies with the checkout.

**Author cards against a role, not a colour.** Write `{"card": {"style": "label", "heading": "TOKYO"}}` and let `--apply` fill in bg, fg, tracking and rect. Anything the scene sets explicitly wins, so a one-off override never means abandoning the brand.

**When a user describes a look they want, save it.** `--save` lifts the look out of a finished storyboard into a preset file, by default into their own config directory. A look that exists only in this conversation is gone tomorrow — that is the whole point of the feature. Tell them where it went and what to call it next time.

Applying is an expansion step, not a render-time lookup: the storyboard ends up holding the real values, so it stays a document you can read, and editing a preset later cannot silently restyle a video that was already approved.

## Title Consistency

Classify every text element before layout. Do not treat all on-screen text as "titles".

- **Subtitles** are narration support. They come from the voice timing files and render through `captionStyle` — the preset's `captions` block is what keeps them identical across videos. Keep them near the lower safe zone; override per scene only when artwork occupies that band.
- **Labels** are editorial overlays: names, rankings, dates, stats, category tags, lower-thirds, CTAs. Build them as card roles so the brand owns them. Labels carry the personality — they may slide, pop, badge or frame.
- **Signs** are in-world text objects: posters, placards, scoreboards, phone notifications. Composite them as cards. Never ask a generator for readable text; it invents letterforms.

Keep contrast decisions systematic — brand-level colours, strokes, shadows and panels before per-scene exceptions. Default label motion to slide/fly-in plus scale/pop, one entrance vocabulary per brand, varying only direction, delay and intensity by scene energy. Do not mix unrelated label styles in one video; if a treatment changes, make the change narratively motivated and reuse the new treatment from that point forward.

## What a Brand Bundle Would Add — PROPOSED, NOT BUILT

Presets cover colour, captions and card geometry. They do not cover the rest of an identity. The proposal is a bundle directory at `~/.config/video-studio/brands/<name>/`, resolved by the same chain (`<project>/brands/` → `$VIDEO_STUDIO_BRANDS` → user → shipped) and written in the same frontmatter-plus-JSON format:

- `brand.md` — the look JSON exactly as today, plus a bundle name so a user can say "use Northwind" instead of naming a colour.
- `logo/` — wordmark and mark as SVG plus transparent PNG, with the safe-area and minimum-size rule beside them.
- `fonts/` — the actual font files. `fontFamily` today names a face the render host may not have installed.
- `voice.md` — narration identity: which voice, pace, and the words this brand does not say.
- `cta.md` — the closing lines, in the two or three lengths different formats ask for.

**None of that resolves today.** `styles.py` reads `captions` and `cards` and flags every other key as unknown, so a brand bundle needs new code before you can promise it. Until it exists: agree the extra pieces with the user, write them into the project, and say plainly that only captions, card colours and card geometry survive to the next video automatically.

## Anti-patterns

- **Redeciding the palette per video.** Three spots built by hand in one session drifted to three different label heights for the same kind of label. That drift is what the preset file prevents.
- **Describing the brand bundle as if it works.** Logos, fonts, voice and CTA copy are a proposal. Saying "saved to your brand" when only the look persisted is a promise the next session will break.
- **A brand that exists only in the chat.** If you did not write it to a file and name the path out loud, it is not saved.
- **Naming a font instead of shipping it.** A `fontFamily` the render host lacks silently falls back, and the fallback is what ships.
