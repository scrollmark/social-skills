# TalkingHead — direct-to-camera monologue

One person talks to camera throughout; optional lower-third labels and
inset media moments. The base grammar behind storytime/confessional formats.

## Composition
Vertical 1080x1920 @30fps. Single `host` layer full-frame; optional brief
`insert` layers (image/clip, rect `[0.06,0.55,0.88,0.33]`) for receipts/
screenshots/moments. Captions on, karaoke style.

## Interview
Round 1 — header "Story": What's the story/message? Real footage of you, or
a generated presenter?
Round 2 — header "Beats": Where are the emotional turns? (These get
expression changes / take changes.)
Round 3 — header "Inserts": Any evidence moments (screenshots, photos,
clips) to cut in? How sourced?
Round A — header "Audio": Score (supply a file / generate / none)?
Voice (built-in / supplied recording / none)? If generating the score, say
which backend and its rights terms before they choose, not after.
Round L — header "Look": Which caption/card preset — `styles.py --list`?
Any look they describe should be saved with `styles.py --save`.
Freeform: platform, length, energy level.

## Slots
`host` takes (pool by mood), optional `insert` media per beat, narration.

## Grammar
Open mid-story (no throat-clearing). Cut takes at emotional turns even if
the setting is constant — take changes read as authenticity. Inserts ≤3s,
never over the speaker's key lines.

## Render notes
If host is generated: pool takes, ping-pong loop for beats >6s (MiniMax cap).
