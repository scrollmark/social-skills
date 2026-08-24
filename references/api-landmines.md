# API landmines (all paid for in real money or afternoons)

## MiniMax (Hailuo)
- 1080P generates ONLY 6s clips; requesting 10s → error 2013. 768P allows 10s.
- Application errors arrive inside HTTP 200: check `base_resp.status_code != 0`
  or you'll poll a bogus task id for 10 minutes (e.g. 1008 = out of balance).
- Landscape-only output; vertical = center-crop downstream. Keep subjects centered.
- ~$0.06/s observed ($0.36 per 6s clip).
- Submitted jobs bill even if you never download — don't kill a poll loop mid-run.

## Veo (Gemini API)
- Durations {4,6,8} ONLY — docs say "4 to 8 inclusive" but 5 and 7 are rejected.
- `generate_audio` is rejected outright on plain API-key auth (Enterprise-only).
- Same GEMINI_API_KEY as text, but separate (much smaller) video quota — probe
  with one 4s clip before planning a batch. Preview pricing ≈ $0.40/s.

## Gemini text
- Use `gemini-flash-latest` alias; pinned names (gemini-2.5-flash) 404
  intermittently on generateContent despite appearing in the models list.

## Kokoro TTS
- Empty text raises "returned no audio" — write real silence instead
  (tts_kokoro.py --silence N).
- Token timestamps: trailing punctuation arrives as its own token stamped at
  the NEXT word's start — merge punctuation-only tokens onto the previous word
  or captions lead with stray marks.
- Word timings only exist at synthesis time; a resumed/cached WAV has none
  (fall back to whisper or proportional estimation).
- Short interjection lines ("Mhm.") garble both synthesis and downstream ASR
  checks — keep spoken lines ≥3 real words.

## Generation content rules
- NO readable text in prompts: models render pseudo-text (garbled signage was
  the #1 QC error class across three rounds). Real text = composer typography.
- Exact digits especially unreliable (asked for $260, got "250/month").
- Identity across scenes: repeated verbatim descriptors REDUCE drift but do
  not eliminate it; the only guarantee is reusing the same actual footage
  (take pools). Separate generations of the same descriptor can produce a
  visibly different person (~1 in 4 observed).
- Unprompted background text still appears sometimes (storefronts, labels) —
  QC catches it; reframe or regenerate that clip only.

## Clocks (the #1 systemic bug class)
- Scene duration = MEASURED narration WAV duration. Using planned durations
  desyncs audio/video/captions cumulatively (was 20-30 findings per video
  before the fix; 0-6 after).

## Remotion composer (4.0.x)
- `<OffthreadVideo>` has NO `loop` prop — passing one is silently ignored, so a
  clip shorter than its scene freezes on its last frame. Wrap in `<Loop
  durationInFrames={srcFrames}>`; build_props probes the source length into
  `srcDurationInFrames`. This is the common case, not the exotic one: generated
  footage caps at 6s while narration-driven scenes often run longer.
- Ken Burns pan: a `translate(%)` inside `scale()` shifts by scale x percent,
  while the hidden overflow per side is only (scale-1)/2. A fixed shift
  therefore outgrows its margin exactly when `zoom:"out"` returns the scale to
  1, exposing a background sliver at the frame edge. Derive the shift from the
  live headroom — (scale-1)/(2*scale) — not from a constant reserve.
- JPEG intermediate frames tag the output `yuvj420p` (full range), which the
  quality check flags as a platform-compatibility risk. `--pixel-format` does
  NOT override it; `Config.setVideoImageFormat("png")` does. PNG frames render
  a little slower and produce a smaller file here.
- `props.json` is global to the composer, not per project. Always rebuild it
  immediately before rendering — otherwise a second project's props silently
  render into the first project's output filename.



## Music silently costs 6 dB

Adding a music track drops EVERYTHING — narration included — by 6 dB. Measured
on brand-origin-brick: voice at -17.3 dB without music, -23.5 dB with, and the
whole video -14.4 LUFS -> -20.3 LUFS.

The number is the diagnosis: 20*log10(2) = 6.02 dB. Audio tracks are summed
with ffmpeg's `amix`, which divides by the number of inputs. One music track
turns 1 input into 2 and halves the lot.

Nothing about this looks wrong. The render succeeds, the mix balance is
CORRECT (both were scaled equally), captions and cuts are untouched — it is
simply quiet, and quiet is the one defect that survives every visual check.

**Therefore: run `normalize_audio.py (bundled in audio-acquisition) --in <render>` after any render
that has music.** It restores -14 LUFS and, because both sources were scaled
equally, the voice/music balance is preserved. Verified: -20.3 -> -14.1 LUFS,
voice back to -17.5 dB against the no-music original's -17.3 dB.

Two related notes:
- The composer plays music at a FIXED volume (0.25) and does NOT duck under
  narration. Balance is set once, not per-phrase.
- Generated music can arrive peaking at 0 dBFS (MiniMax did). That leaves no
  headroom, so normalising afterwards is doing real work rather than cosmetics.


## Backticks in a commit message are executed

`git commit -m "... the `subtext` key ..."` runs `subtext` as a shell command
and substitutes its (empty) output. The commit succeeds, the push succeeds, and
the words are simply gone from the message — no error anywhere.

This bit the moon-explainer commit: "sub", "subtext", "lines" and "untilMs" all
vanished, leaving sentences like *the storyboard said  where the component
reads ,* which reads as a rendering bug rather than a shell one.

Same family as the $0-substitution trap in SKILL.md: shell metacharacters in
prose destroy the prose silently.

**Use `-F -` with a quoted heredoc** (`<<'MSGEOF'`), which passes the body
through untouched:

    git commit -F - <<'MSGEOF'
    Title
    ... `backticks` and $dollars survive verbatim ...
    MSGEOF

And note the repair is NOT `--amend` + `--force-with-lease` once the commit is
pushed to a shared branch. Another session may be committing to the same
branch, and rewriting its history to fix your own typo is not a fair trade —
add a follow-up commit instead. (This is what happened here: the force push was
correctly refused, the local amend was dropped, and this note is the fix.)
