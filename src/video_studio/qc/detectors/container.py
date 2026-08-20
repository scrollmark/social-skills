"""Container-level checks: duration vs plan, resolution/aspect, fps, pix_fmt, streams.

Pure over Context — no media access. Verbatim v1 thresholds and messages.
"""

from __future__ import annotations

from video_studio.qc.context import Context
from video_studio.qc.report.model import Finding, Severity

# H.264 yuv420p at 30fps is showrunner's output contract for every format.
EXPECTED_PIX_FMT = "yuv420p"
EXPECTED_FPS = 30.0
FPS_TOLERANCE = 0.5
# Rendered duration may legitimately differ slightly from the plan (transition
# overlaps, audio padding); beyond these it's a real defect.
DURATION_WARN_SEC = 0.5
DURATION_ERROR_SEC = 2.0

ASPECT_DIMENSIONS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}


def run(ctx: Context) -> None:
    v = ctx.video
    r = ctx.report

    if v.audio is None:
        r.add(
            Finding("container", "NO_AUDIO_STREAM", "error", "Rendered video has no audio stream")
        )

    if v.pix_fmt and v.pix_fmt != EXPECTED_PIX_FMT:
        r.add(
            Finding(
                "container",
                "UNEXPECTED_PIX_FMT",
                "warning",
                f"Pixel format is {v.pix_fmt}, expected {EXPECTED_PIX_FMT} "
                "(compatibility risk on social platforms)",
            )
        )

    if v.fps and abs(v.fps - EXPECTED_FPS) > FPS_TOLERANCE:
        r.add(
            Finding(
                "container",
                "UNEXPECTED_FPS",
                "warning",
                f"Frame rate is {v.fps:.2f} fps, expected {EXPECTED_FPS:.0f}",
                metrics={"fps": v.fps},
            )
        )

    gt = ctx.ground_truth
    if gt is None:
        return

    # Resolution vs declared aspect ratio.
    expected = ASPECT_DIMENSIONS.get(gt.aspect_ratio)
    if gt.render_width and gt.render_height:
        expected = (gt.render_width, gt.render_height)
    if expected and (v.width, v.height) != expected:
        r.add(
            Finding(
                "container",
                "RESOLUTION_MISMATCH",
                "error",
                f"Video is {v.width}x{v.height}, expected {expected[0]}x{expected[1]} "
                f"for aspect {gt.aspect_ratio}",
                metrics={"width": v.width, "height": v.height},
            )
        )

    # Duration vs the planned timeline (real audio durations when available).
    target = gt.timeline_duration_sec or gt.planned_total_duration_sec
    if target > 0:
        drift = v.duration_sec - target
        r.set_metric("container.durationDriftSec", drift)
        if abs(drift) > DURATION_WARN_SEC:
            severity: Severity = "error" if abs(drift) > DURATION_ERROR_SEC else "warning"
            direction = "longer" if drift > 0 else "shorter"
            r.add(
                Finding(
                    "container",
                    "DURATION_DRIFT",
                    severity,
                    f"Rendered video is {abs(drift):.2f}s {direction} than the planned timeline "
                    f"({v.duration_sec:.2f}s vs {target:.2f}s)",
                    metrics={"driftSec": round(drift, 3)},
                    rubric_dimension="motion-timing",
                )
            )
