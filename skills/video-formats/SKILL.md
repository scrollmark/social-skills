---
name: video-formats
description: Use when planning, structuring, or critiquing a short-form video — choosing a format, laying out its scenes, or defining a new format. Covers ten scene grammars from talking-head to hand-drawn motion graphics.
---

# Video Formats

This skill is a router. The ten format grammars live in `references/formats/` — this skill tells you what a format is, which one to reach for, and how to write an eleventh.

## What a Format Is

A format is a **scene grammar**: a repeatable structure that says how many scenes a video has, what each one is for, what goes in each one, and what questions to ask before you can build it. It is not a template to fill in and not a style preset. Two videos in the same format can look nothing alike and still be the same shape.

Every format file has the same five sections:

- **Composition** — aspect ratio, frame rate, scene count and lengths, whether captions are on.
- **Interview** — the questions to ask before planning. Rounds are numbered and headed; some formats insist on an order (Cinematic demands audio first, because every cut gets shaped around the track).
- **Slots** — the named assets the format needs. `hero`, `beat-N`, `endcard`, `host`, `popup-N`. Slots are the shopping list.
- **Grammar** — the scene-by-scene construction rules. This is the load-bearing section: which beat opens, how long each runs, what belongs on screen at once, and what the format refuses to do.
- **Render notes** — the practical traps, learned by failing.

## Choosing a Format

One distinguishing question each. Ask them in roughly this order and stop at the first yes.

| Format | The question that selects it |
|---|---|
| **PointerPopups** | Do you already have footage of someone pointing at things? |
| **TitledVideo** | Do you have a finished clip that just needs titles to be postable? |
| **TalkingHead** | Is one person talking to camera the whole way through? |
| **PipStory** | Is there a host, but the story keeps citing things worth showing? |
| **Cinematic** | Is the point a feeling rather than an argument — cut to music, few words? |
| **Explainer** | Is there a concept to explain, and no one on camera to explain it? |
| **ProductLaunch** | Is there a product, three capabilities, and a name to land? |
| **BrandOrigin** | Is it one from-here-to-there story about a real brand, ~30s? |
| **TimelineExplainer** | Is the *list* the point — numbered beats the viewer counts along with? |
| **Boil** | Can the subject not be photographed at all? |

Two pairs are easy to confuse:

- **BrandOrigin vs. TimelineExplainer** — BrandOrigin is one transformation carried by a recurring motif, ~30s. TimelineExplainer is a countable sequence, 6-10 numbered beats, and runs longer. If the viewer would be counting, it's the timeline.
- **TalkingHead vs. PipStory** — the same host, but PipStory shrinks them into a corner whenever the narration names something concrete. If 25-50% of the beats cite a number, an object, or a place, it's PipStory.

**Boil is the outlier.** It's the only format with no photography, no footage, and nothing licensed on screen. Reach for it when the subject is unreleased, abstract, or a service — or when stock would look borrowed.

## Reading a Format File

Load `references/formats/{name}.md` from this skill's own directory. File names are kebab-case: `pip-story.md`, `brand-origin.md`, `pointer-popups.md`, `timeline-explainer.md`, `product-launch.md`, `talking-head.md`, `titled-video.md`, plus `boil.md`, `cinematic.md`, `explainer.md`.

The files share a vocabulary that comes from the storyboard structure they compile into. A **scene** holds `narration` and a stack of **layers**; a layer is a `source` (footage, a still, a generated clip), a `card` (live typography), or an `effect`. Terms you'll meet:

- **`card`** — real typography rendered at composition time. Every exact word, number, name, year, and URL is a card. Never ask a generator for text; it invents letterforms.
- **`ken`** — a slow Ken Burns drift over a still, so it reads as footage rather than a frozen frame. Alternate zoom direction and pan between consecutive scenes or the cuts all move identically.
- **`rect`** — a layer's position as `[x, y, w, h]` in fractions of the frame. A corner inset is roughly `[0.58, 0.58, 0.42, 0.42]`.
- **`atMs` / `untilMs` / `pop`** — a layer's visibility window inside its scene, with an optional pop-in.
- **`broll` / `host` / `insert` / `main`** — conventional layer ids, not special types. The names carry intent between the format and whoever builds it.
- **`plannedSeconds`** — an estimate. Measured narration length is the real clock.

## Anti-patterns

- **Two ideas in one scene.** Every grammar says this in its own words. If a beat needs two sentences, it's two beats.
- **Card and narration saying the same words.** The card carries the short form, the voice carries the sentence. Doubling reads as a caption, not a design.
- **Mixing formats mid-video.** A talking head that becomes a montage halfway through has no grammar; it has two halves.
- **Choosing a format by look.** Formats are selected by what the material *is*. Look is a separate layer entirely — the same format can be dressed a dozen ways.

## Adding an Eleventh Format

Drop a new markdown file in `references/formats/`. Required sections, in order: `# Name — one-line description`, `## Composition`, `## Interview`, `## Slots`, `## Grammar`, `## Render notes`. Nothing else changes — the format list is the directory listing.

Two rules worth honoring:

1. **A format earns its file by recurring.** BrandOrigin was extracted after the same shape appeared four times in one reference gallery. Three or four independent uses is a format; one is a video.
2. **The Grammar section must be able to say no.** A grammar that only describes what a video may contain isn't a grammar. Each of the ten forbids something specific — two marks on screen, a CTA on an editorial piece, an insert over the speaker's key line. If your new format forbids nothing, it's a mood board.

## Toolchain Assumptions

These grammars were extracted from a production pipeline, and several Render notes still name its programs (`gen_boil`, `track_pointing`, `measure`, `styles`) and its per-clip costs. Those now live in the `video-studio-engine` pip package, except `measure`, which ships inside `audio-acquisition`. **Boil** and **PointerPopups** are the two that genuinely depend on a generator and a hand tracker — without `pip install 'video-studio-engine[generate,vision] @ git+https://github.com/scrollmark/social-skills.git'`, read them as descriptions of a style rather than instructions you can follow. The other eight are pure structure: every Composition, Interview, Slots, and Grammar section stands on its own, whatever you build the video with.
