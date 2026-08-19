# Hard rules

Learned the expensive way — in real money or in afternoons. None of these are
preferences. Every one of them describes something that already went wrong.

## The placeholder trap

**`--placeholders` is for layout preview only. Never render a build made with
it.** Unresolved sources become solid coloured boxes, and a placeholdered build
is not a *failed* build to the naked eye — it is a finished-looking video of
coloured rectangles. Check `readyToRender` in the `build_props` summary and run
`video-studio preflight` before every render.

A nonzero `video-studio preflight` means **do not render** — fix and rebuild. It exits
nonzero if any layer would render as a placeholder, if props reference a file
missing from `public/`, or if a narration track is silent.

## props.json is global

`props.json` belongs to the composer, not to a project. **Always rebuild it
immediately before rendering** — otherwise a second project's props silently
render into the first project's output filename, and only the duration gives it
away. The same applies to any timeline export: pass `--project` so it rebuilds
first.

## Clocks — the number one systemic bug class

- **Scene duration = MEASURED narration WAV duration.** The plan's estimate is a
  hint, never the clock. Using planned durations desyncs audio, video and
  captions cumulatively: 20–30 findings per video before the fix, 0–6 after.
- Empty narration → `video-studio tts_kokoro --silence <seconds>`; never synthesize `""`.
  `--silence` is for beats that are **meant** to be quiet. Never use it to paper
  over a voice backend that failed: the silent WAV becomes the scene clock and
  the render ships with no narration and no captions while every log line still
  reads as success. If the voice is broken, fix it or stop and tell the user.
- **Music generators ignore the length you ask for.** Observed in one session:
  22s requested returned 128s, 128s returned 148s, 140s returned 25s and then
  66s. Never plan a cut against the requested length — generate, MEASURE the
  file, then design to what you actually got. If it comes back too short to
  cover the video, re-roll rather than looping; a loop seam in a scored piece is
  audible in a way a slightly different arrangement is not.
- **End on the track's own resolution, not on a fade you imposed.** Map the
  energy envelope and find where the piece actually finishes. Fading out
  mid-phrase — especially in the dip before a final chorus — reads to a listener
  as the video being cut off, because it is. If the track must be shortened, cut
  at a real section boundary and let its own decay end it.

## Generation

- MiniMax 1080P generates **only** 6s clips; request 6, trim in the composer.
- Veo accepts durations {4, 6, 8} only; quota-check with a 4s probe first.
- **Never put readable text in generation prompts** — models render pseudo-text.
  Real text and numbers are composer overlays (TextCard / StatCard), and those
  are pixel-perfect.
- Identity across scenes: reuse the same actual footage (a "pool" of takes,
  `file:` sources). Repeated prompt descriptors only *reduce* drift.

## The clips path

`url:` / `find:` / `prompt:` sources resolve from exactly one location:
`project/clips/<sceneId>-<layerId>.<ext>`. Use `video-studio source_clips` or the `gen_*`
scripts to put them there — `build_props` copies them into `composer/public/`
itself. Hand-placing files into `composer/public/clips/` does **not** work;
`build_props` never looks there and will placeholder or error.

## Render-side composer landmines (Remotion 4.0.x)

- `<OffthreadVideo>` has **no** `loop` prop — passing one is silently ignored, so
  a clip shorter than its scene freezes on its last frame. Wrap it in `<Loop
  durationInFrames={srcFrames}>`; `build_props` probes the source length into
  `srcDurationInFrames`. This is the common case, not the exotic one: generated
  footage caps at 6s while narration-driven scenes often run longer.
- **Ken Burns headroom.** A `translate(%)` inside `scale()` shifts by scale ×
  percent, while the hidden overflow per side is only (scale−1)/2. A fixed shift
  therefore outgrows its margin exactly when `zoom:"out"` returns the scale to 1,
  exposing a background sliver at the frame edge. Derive the shift from the live
  headroom — (scale−1)/(2·scale) — not from a constant reserve. Motion is eased,
  not linear; the quality check flags constant-velocity drift as mechanical.
- **JPEG intermediates tag the output `yuvj420p`** (full range), which the
  quality check flags as a platform-compatibility risk. `--pixel-format` does NOT
  override it; `Config.setVideoImageFormat("png")` does. PNG frames render a
  little slower and produce a smaller file here.

## Verification

Never declare a render done without viewing frames from it. Pull 4–6 frames
across the timeline (`ffmpeg -ss <t> -i <mp4> -frames:v 1 f<t>.png`) and actually
look at them; confirm duration and loudness with `ffprobe`. Every shipped-broken
render in this pipeline's history would have been caught by opening a single
frame.

## Cost table

Update when observed. Amounts are written without a currency symbol because
dollar-prefixed digit tokens get clobbered by argument substitution.

| Item | Rate |
|---|---|
| MiniMax | ~0.36 USD per 6s clip |
| Veo preview | ~0.40 USD/s |
| Imagen Fast | ~0.02 USD/still |
| Local voice | free |
| Placeholder previews | free |

Quote the total **before the first paid call and again after the last**, and only
after `scripts/doctor.py` has said which providers are actually reachable.
