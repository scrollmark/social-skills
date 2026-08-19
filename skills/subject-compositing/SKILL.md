---
name: subject-compositing
description: Use when a filmed person has to appear somewhere they never were — dropping a subject over replacement footage, putting a drawn prop in front of them, driving the pair across frame, or pinning popup images to where they point on camera.
---

# Subject Compositing

For shots nobody can film and no generator produces convincingly: him in a spaceship,
in a clown car, on the moon. A real take is segmented out of its real surroundings and
laid over replacement footage, with a prop in front. It lives or dies on the source
take — settle the footage before you promise the shot.

## Requires

`scripts/composite_subject.py` and `scripts/track_pointing.py` from
**scrollmark/video-studio** (private). Both run MediaPipe — selfie segmentation and
pose landmarks for the composite, hand landmarks for the gestures. Without them
nothing here executes: no matte, no feathered occlusion seam, no arm punch-through, no
gesture timing. What still holds is the footage guidance below — it tells the user
what to shoot, and is worth giving before they shoot rather than after. The pointing
format's scene grammar lives in `video-formats`.

## What the Segmenter Needs From the Take

This decides whether the shot works, and it is decided on set, not in post. The model
is a **selfie segmenter** — one person, front-facing, upper body, at conversational
distance. Everything it fails at follows from that.

- **One person, near arm visible.** Pose landmarks pick whichever wrist the segmenter
  can see. A second person in frame, or an arm crossing out of shot, breaks free-arm.
- **Tonal separation from the background.** Hair, dark clothing on a dark wall, or a
  subject the same value as what is behind them gives a matte that chews the
  silhouette. It does not error; it just looks cheap.
- **Flat even light, no motion blur.** Fast pans and hard shadow edges leave the matte
  flickering frame to frame, which reads instantly as fake. Lock the camera off and
  let the subject move instead.
- **Frame wide enough to cut.** `--occlude-below` slices the subject at the prop's top
  edge with a feathered seam — it sells "inside it" and hides the real chair they were
  sitting on, but it needs body below the cut line to work with.
- **Short takes.** Every frame goes through the segmenter one at a time; a couple of
  seconds is the working unit. This is a shot, not a sequence.

## The Composite

    scripts/composite_subject.py out.mp4 --in take.mp4 --ss 39.9 --t 2.5 \
        --bg crowd.webm --bg-crop 405:600:430:15 --bg-eq eq=contrast=1.9:saturation=0 \
        --fg art/car.png --occlude-below 1215 --free-arm --travel -330 430 --flip-h

Layering is background → subject → prop → the gesturing forearm punched back through
the prop. `--free-arm` intersects a capsule around elbow/wrist/hand with the real
mask, so only body pixels come forward; without that intersection a drifting pose
estimate cuts a person-shaped hole of background through the prop. `--travel`,
`--flip-h` and `--flip-v` move subject and prop as one object over a static background,
and mirroring happens *before* travel — flip afterwards and the flip reverses the
travel direction too. `--scale` anchors on the subject, not the frame origin.

**Draw the prop crudely, with an alpha channel.** Wobbly hand-drawn art forgives
the matte's soft edges; clean vector art makes it look broken beside them. A PNG
without alpha is rejected outright. And **check the background crop before compositing
into it** — a tight crop of soft archival footage becomes grey mush, and stadium
footage is full of legible third-party advertising you have just put in a brand video.

## Pointing

`track_pointing.py analyze` emits events — windows where an extended index finger
holds a stable position — with the pointed-*at* location extrapolated past the
fingertip, as canvas fractions. `layers` turns those into storyboard layers offset
toward frame centre so the popup never covers the hand. Here the footage dictates the
layout and the storyboard does not, so **reconcile the event list with the user before
composing**: pull frames at each timestamp and check the count. Holds under half a
second are dropped as jitter by design, and only one hand is tracked — quick tappers
and two-handed presenters both come back short, and it reads as a broken tracker
rather than a threshold working.

## Anti-patterns

- **Promising the shot before seeing the take.** Background contrast and camera motion
  decide it, and neither is fixable in post.
- **A clean vector prop.** It makes the matte look broken; crude art hides it.
- **Trusting the event list.** Extract frames and reconcile the count with the user.
