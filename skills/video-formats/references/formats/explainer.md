# Explainer — narrated concept walkthrough

Voiceover explains a concept over a sequence of illustrative visuals: b-roll
cuts, text cards, big-number stat beats. No on-camera host. (Descends from
showrunner's faceless-explainer, minus the LLM planner — the agent plans.)

## Composition
Vertical 1080x1920 @30fps (ask if landscape 1920x1080 wanted for YouTube).
Scene types: full-frame `broll` layers, or text/stat beats built as
placeholder layers with composer text (add TextCard/StatCard components as
needed — see the composer's layer renderer). Captions on. One narrator voice.

## Interview
Round 1 — header "Topic": What concept? What's the one-sentence takeaway a
viewer should leave with?
Round 2 — header "Structure": Hook style (question / bold claim / statistic)?
How long (30/45/60s)?
Round 3 — header "Visuals": Illustrative footage (generate/find/supply) vs
motion-graphics text beats — rough mix?
Round A — header "Audio": Score (supply a file / generate / none)?
Voice (built-in / supplied recording / none)? If generating the score, say
which backend and its rights terms before they choose, not after.
Round L — header "Look": Which caption/card preset — `styles.py --list`?
Any look they describe should be saved with `styles.py --save`.
Freeform: audience, tone, examples to include/avoid.

## Slots
`narration` per scene; visual per scene: `broll` source OR text-beat content
(heading, stat, caption).

## Grammar
Hook ≤10 words spoken first. One idea per scene, 4-8s each. Every claim with
a number gets a stat beat (composer text, pixel-perfect). Close with the
takeaway restated + soft CTA.

## Render notes
Narration WAV durations are the clock. Stat/text beats: 3-4s minimum for
readability.
