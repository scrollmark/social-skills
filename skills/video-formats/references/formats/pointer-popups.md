# PointerPopups — analyzed footage with images pinned to pointing gestures

The user's own footage (or generated footage) of a presenter pointing at
empty space; hand-tracking analysis finds where and when they point, and
popup images appear pinned beside those exact spots. Analysis-driven
composition: the footage dictates the layout, not the storyboard.

## Composition
Match the source clip's orientation/dimensions (probe with
`measure` (bundled in `audio-acquisition`)). Base layer: the user's clip (with its own audio —
set `muted: false`, no TTS unless they want VO added). Popup layers:
image layers with `rect` from the tracker, `atMs`/`untilMs` windows,
`pop: true`, `fit: contain`.

## Interview
Round 1 — header "Footage": Your pointing video: file path or URL? (This
format needs real footage — generated pointing works but tracking quality
follows footage quality.)
Round 2 — header "Popups": The images to pop up, in pointing order: file
paths / URLs / generate them? One per point, or should some repeat?
Round 3 — header "Style": Popup size (small 0.22 / medium 0.30 / large
0.40 of frame width)? Keep original audio, add VO, or both?
Round A — header "Audio": Score (supply a file / generate / none)?
Voice (built-in / supplied recording / none)? If generating the score, say
which backend and its rights terms before they choose, not after.
Round L — header "Look": Which caption/card preset — `video-studio styles --list`?
Any look they describe should be saved with `video-studio styles --save`.
Freeform: anything about timing, linger duration, or what each point means.

## Slots
`me` (the footage), `popup-N` images (assigned to pointing events in order).

## Grammar / pipeline
1. `video-studio track_pointing analyze --in <clip> --out events.json`
2. Review events with the user (count + timestamps) — if the tracker found
   more/fewer points than they expect, show extracted frames at event
   timestamps and reconcile before composing (extra events → drop by index;
   missed events → hand-add from frame inspection).
3. `video-studio track_pointing layers --events events.json
   --images a.png,b.png [--size 0.30]` → paste emitted layers into the
   scene after the base layer.
4. Scene `plannedSeconds` = clip duration (measure it); no TTS narration
   unless requested (base layer keeps its own audio).

## Render notes
- Tracker assumes ONE pointing hand (max_num_hands=1); two-handed footage
  needs a second pass with the flag raised.
- Events under 350ms are dropped as jitter by design — a real "look here"
  point holds. If the user's style is quick taps, lower MIN_EVENT_MS.
- The popup rect auto-offsets toward frame center so it never covers the
  finger; `--size` is the only knob usually worth touching.
- Verify with extracted frames at each event midpoint before declaring
  done — tracking confidence varies with lighting and hand size.
