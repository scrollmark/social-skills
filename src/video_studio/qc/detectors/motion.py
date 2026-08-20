"""Motion character analysis over the shared decode's global flow series.

v1's root perf defect lived here: velocity_series() called sample_frames per
scene, but sample_frames always decodes from frame 0 — O(scenes x full decode).
The engine's motion service now computes optical flow ONCE for the whole video
at 10 fps; this detector slices the series per scene span.

Honest behavioral delta from v1 (declared in the parity allowlist): v1
restarted the 10 fps sampling grid at each scene start; the global grid starts
at 0, so sample times inside a scene shift by up to 100 ms. Easing score
(coefficient of variation over the longest moving run) is robust to that, but
borderline ROBOTIC_MOTION findings can flip.
"""

from __future__ import annotations

import numpy as np

from video_studio.qc.context import Context
from video_studio.qc.report.model import Finding

MIN_MOTION_PX = 0.15  # mean |flow| below this = static, ignore
MIN_SEGMENT_SAMPLES = 8  # need ~0.8s of continuous motion to judge easing
EASING_SCORE_WARN = 0.18
ROBOTIC_SCENE_FRACTION = 0.5


def easing_score(speeds: np.ndarray) -> float | None:
    """Coefficient of variation of velocity inside the longest moving run.
    None when there's no sustained motion to judge. v1 verbatim."""
    moving = speeds > MIN_MOTION_PX
    best_len, best_start = 0, None
    i = 0
    while i < len(moving):
        if moving[i]:
            j = i
            while j < len(moving) and moving[j]:
                j += 1
            if j - i > best_len:
                best_len, best_start = j - i, i
            i = j
        else:
            i += 1
    if best_len < MIN_SEGMENT_SAMPLES or best_start is None:
        return None
    seg = speeds[best_start : best_start + best_len]
    return float(seg.std() / (seg.mean() + 1e-9))


def run(ctx: Context) -> None:
    r = ctx.report
    gt = ctx.ground_truth
    samples = ctx.artifacts.motion_samples
    assert samples is not None, "engine must run the motion service before motion"

    if gt and gt.scenes:
        spans = [(s.id, s.start_sec, min(s.end_sec, ctx.video.duration_sec)) for s in gt.scenes]
    else:
        # No ground truth: analyze in 5s windows.
        spans = [
            (f"window-{i}", t, min(t + 5.0, ctx.video.duration_sec))
            for i, t in enumerate(np.arange(0.0, ctx.video.duration_sec, 5.0))
        ]

    scores: list[float] = []
    robotic_scenes: list[tuple[str, float, float, float]] = []
    for scene_id, start, end in spans:
        if end - start < 1.0:
            continue
        # Pairs fully inside the span — a pair straddling the boundary mixes
        # two scenes' motion, which v1's per-scene decode never saw.
        speeds = np.array(
            [
                speed
                for t_prev, t_cur, speed in samples
                if t_prev >= start - 1e-6 and t_cur <= end + 1e-6
            ]
        )
        score = easing_score(speeds)
        if score is None:
            continue
        scores.append(score)
        if score < EASING_SCORE_WARN:
            robotic_scenes.append((scene_id, start, end, score))

    if not scores:
        r.set_metric("motion.scenesWithMotion", 0)
        return

    r.set_metric("motion.scenesWithMotion", len(scores))
    r.set_metric("motion.easingScoreMean", float(np.mean(scores)))
    r.set_metric("motion.easingScoreMin", float(np.min(scores)))

    for scene_id, start, end, score in robotic_scenes:
        r.add(
            Finding(
                "motion",
                "ROBOTIC_MOTION",
                "warning",
                f"Scene '{scene_id}': sustained motion at near-constant velocity (easing score "
                f"{score:.2f}) — reads as linear/robotic; add easing curves",
                scene_id=scene_id if gt else None,
                span_sec=(start, end),
                metrics={"easingScore": round(score, 3)},
                rubric_dimension="motion-timing",
            )
        )

    if len(robotic_scenes) / len(scores) >= ROBOTIC_SCENE_FRACTION and len(scores) >= 2:
        r.add(
            Finding(
                "motion",
                "PERVASIVE_LINEAR_MOTION",
                "error",
                f"{len(robotic_scenes)}/{len(scores)} moving scenes have un-eased "
                "constant-velocity motion — the single strongest AI-made tell per the quality "
                "rubric",
                metrics={"roboticFraction": round(len(robotic_scenes) / len(scores), 3)},
                rubric_dimension="motion-timing",
            )
        )
