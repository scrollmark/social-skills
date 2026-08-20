"""CLIP prompt-fit: does each scene's footage match its own visual prompt?

The general form of what objects.py's ~20-noun COCO table approximates — CLIP
text-image similarity has no vocabulary, so EVERY scene gets scored against
the exact prompt the generator was given. The judgment is a RELATIVE margin:
a scene's similarity to its own prompt minus its mean similarity to the other
scenes' prompts. Absolute CLIP cosines are uncalibrated (0.2 can be a great
match); a scene that matches everyone else's prompt better than its own is a
mismatch regardless of the absolute number.

Needs the [store] extra (fastembed); models download ~0.6 GB on first use.
Single-scene plans get an absolute floor only — no cross-prompts to compare.
"""

from __future__ import annotations

import numpy as np

from video_studio.qc.context import Context
from video_studio.qc.report.model import Finding

MIN_FRAMES = 1
ABSOLUTE_FLOOR = 0.15  # below this even the RIGHT footage rarely scores; hard fail
MARGIN_WARN = 0.0  # own-prompt similarity must beat the mean cross-prompt


def run(ctx: Context) -> None:
    gt = ctx.ground_truth
    r = ctx.report
    assert gt is not None
    frames_by_scene = ctx.artifacts.scene_frames
    assert frames_by_scene is not None, "engine must run the scene-frame service first"

    scenes = [s for s in gt.scenes if len(frames_by_scene.get(s.id) or []) >= MIN_FRAMES]
    if not scenes:
        return

    from video_studio.qc.embeddings.clip import ClipPair  # fastembed — [store] extra

    clip = ClipPair()
    prompts = [s.visual or s.narration or s.id for s in scenes]
    text_vecs = clip.embed_texts(prompts)  # (n, 512), normalized

    scene_vecs = []
    for s in scenes:
        img_vecs = clip.embed_bgr_frames(frames_by_scene[s.id])
        scene_vecs.append(img_vecs.mean(axis=0))
    image_mat = np.array(scene_vecs)
    norms = np.linalg.norm(image_mat, axis=1, keepdims=True)
    image_mat = image_mat / np.maximum(norms, 1e-9)

    # sims[i, j] = similarity of scene i's footage to scene j's prompt.
    sims = image_mat @ text_vecs.T
    n = len(scenes)

    own = np.diag(sims)
    if n > 1:
        cross = (sims.sum(axis=1) - own) / (n - 1)
        margins = own - cross
    else:
        margins = np.zeros(1)

    r.set_metric("promptVisual.meanClipScore", float(own.mean()))
    r.set_metric("promptVisual.minClipScore", float(own.min()))
    if n > 1:
        r.set_metric("promptVisual.meanMargin", float(margins.mean()))
        r.set_metric("promptVisual.minMargin", float(margins.min()))

    for i, scene in enumerate(scenes):
        score = float(own[i])
        margin = float(margins[i]) if n > 1 else None
        mismatch = score < ABSOLUTE_FLOOR or (margin is not None and margin < MARGIN_WARN)
        if not mismatch:
            continue
        if margin is not None and margin < MARGIN_WARN:
            best = int(np.argmax(sims[i]))
            detail = (
                f"its footage matches scene '{scenes[best].id}'s prompt better "
                f"(CLIP {sims[i, best]:.3f} vs own {score:.3f})"
            )
        else:
            detail = f"CLIP similarity {score:.3f} is below the {ABSOLUTE_FLOOR} floor"
        r.add(
            Finding(
                "prompt_visual",
                "VISUAL_PROMPT_MISMATCH",
                "warning",
                f"Scene '{scene.id}': the rendered footage does not match its visual "
                f"prompt — {detail}. Prompt: \"{(scene.visual or '')[:120]}\"",
                scene_id=scene.id,
                span_sec=(scene.start_sec, scene.end_sec),
                metrics={
                    "clipScore": round(score, 4),
                    **({"margin": round(margin, 4)} if margin is not None else {}),
                },
                rubric_dimension="visual-quality",
                taxonomy_targets=["visual"],
            )
        )
