"""Scene-cut timing vs the planned timeline, over the precomputed cut list.

Cut detection itself moved to the engine (one SceneManager pass instead of
v1's two detect() decodes); this detector is now pure matching + reporting.
Thresholds, messages, and the cumulative-vs-offset reasoning are v1 verbatim.
"""

from __future__ import annotations

from video_studio.qc.analysis.align import match_monotonic, summarize_drift
from video_studio.qc.context import Context
from video_studio.qc.report import ids
from video_studio.qc.report.model import Finding, Severity

MATCH_TOLERANCE_SEC = 1.5
DRIFT_WARN_MS = 150.0
DRIFT_ERROR_MS = 500.0

# Formats whose scenes are continuous motion graphics — a missing hard cut
# between scenes is often intentional there (crossfades), so downgrade.
CONTINUOUS_FORMATS = {"faceless-explainer", "manim-explainer"}


def run(ctx: Context) -> None:
    gt = ctx.ground_truth
    r = ctx.report
    assert gt is not None

    # Planned boundaries: the start of every scene after the first.
    boundaries = [s.start_sec for s in gt.scenes[1:]]
    if not boundaries:
        return

    cuts = ctx.artifacts.cuts
    assert cuts is not None, "engine must run cut detection before scene_sync"
    r.set_metric("sync.detectedCutCount", len(cuts))

    matches = match_monotonic(boundaries, cuts, MATCH_TOLERANCE_SEC)
    matched_expected = {m.expected_index for m in matches}
    matched_actual = {m.actual_index for m in matches}

    for m in matches:
        scene = gt.scenes[m.expected_index + 1]  # boundary i starts scene i+1
        drift_ms = m.drift * 1000.0
        # Record on the scene timing spine.
        for st in r.scenes:
            if st.id == scene.id:
                st.detected_cut_sec = cuts[m.actual_index]
        if abs(drift_ms) >= DRIFT_WARN_MS:
            severity: Severity = "error" if abs(drift_ms) >= DRIFT_ERROR_MS else "warning"
            direction = "after" if drift_ms > 0 else "before"
            r.add(
                Finding(
                    "scene_sync",
                    "SCENE_CUT_DRIFT",
                    severity,
                    f"Cut into scene '{scene.id}' lands {abs(drift_ms):.0f}ms {direction} its "
                    f"planned boundary ({cuts[m.actual_index]:.2f}s vs {scene.start_sec:.2f}s)",
                    scene_id=scene.id,
                    span_sec=(
                        min(cuts[m.actual_index], scene.start_sec),
                        max(cuts[m.actual_index], scene.start_sec),
                    ),
                    metrics={"driftMs": round(drift_ms, 1)},
                    rubric_dimension="motion-timing",
                )
            )

    # Planned boundaries with no matching detected cut.
    for i, b in enumerate(boundaries):
        if i in matched_expected:
            continue
        scene = gt.scenes[i + 1]
        soft = gt.format in CONTINUOUS_FORMATS or scene.transition != "cut"
        r.add(
            Finding(
                "scene_sync",
                "MISSING_SCENE_CUT",
                "info" if soft else "warning",
                f"No visual cut detected near the planned start of scene '{scene.id}' ({b:.2f}s)"
                + (
                    " — its transition is a crossfade/motion, which may be intentional"
                    if soft
                    else ""
                ),
                scene_id=scene.id,
                span_sec=(max(0.0, b - MATCH_TOLERANCE_SEC), b + MATCH_TOLERANCE_SEC),
            )
        )

    # Detected cuts that match no planned boundary (mid-scene glitches,
    # sideways/short clips in ai-video, double cuts).
    for j, t in enumerate(cuts):
        if j in matched_actual:
            continue
        host = gt.scene_at(t)  # None when the cut lands outside every scene
        r.add(
            Finding(
                "scene_sync",
                "UNPLANNED_CUT",
                "warning",
                f"Unplanned visual cut at {t:.2f}s inside scene '{host.id if host else '?'}'",
                scene_id=host.id if host else None,
                key=ids.time_key(t),
                span_sec=(t, t),
            )
        )

    summary = summarize_drift(matches)
    if summary is not None:
        r.set_metric("sync.meanSceneCutDriftMs", summary.mean * 1000)
        r.set_metric("sync.maxSceneCutDriftMs", summary.max_abs * 1000)
        r.set_metric("sync.cumulativeDriftSlopeMsPerScene", summary.slope_per_event * 1000)
        if summary.is_cumulative and abs(summary.slope_per_event) * 1000 >= 30:
            r.add(
                Finding(
                    "scene_sync",
                    "CUMULATIVE_DRIFT",
                    "error",
                    f"Scene-cut drift grows ~{summary.slope_per_event * 1000:.0f}ms per scene — "
                    "scene durations in the render are systematically longer/shorter than planned "
                    "(classic concat or fps-rounding bug), not a one-off offset",
                    metrics={"slopeMsPerScene": round(summary.slope_per_event * 1000, 1)},
                    rubric_dimension="motion-timing",
                )
            )
