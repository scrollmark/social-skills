"""Black-frame and freeze-frame findings over the shared ffmpeg filter pass.

v1 ran blackdetect and freezedetect as two separate full decodes; the spans now
arrive precomputed in ctx.artifacts.filter_pass (one chained invocation, shared
with audio_quality's ebur128). Severity/tail heuristics are v1's verbatim.

v2 id note: BLACK_SPAN/FREEZE_SPAN legitimately recur, so they carry a
time-bucketed `key` — the exact case the positional `:2` suffix got wrong.
"""

from __future__ import annotations

from video_studio.qc.context import Context
from video_studio.qc.report import ids
from video_studio.qc.report.model import Finding, Severity

TAIL_WINDOW_SEC = 0.5  # a black span ending within this of EOF counts as a tail


def run(ctx: Context) -> None:
    v = ctx.video
    r = ctx.report
    gt = ctx.ground_truth
    fp = ctx.artifacts.filter_pass
    assert fp is not None, "engine must run the filter pass before black_freeze"

    def scene_id_at(t: float) -> str | None:
        if gt is None:
            return None
        s = gt.scene_at(t)
        return s.id if s else None

    r.set_metric("blackFreeze.blackSpanCount", len(fp.black_spans))
    for start, end in fp.black_spans:
        is_tail = end >= v.duration_sec - TAIL_WINDOW_SEC
        if is_tail:
            r.add(
                Finding(
                    "black_freeze",
                    "BLACK_TAIL",
                    "error",
                    f"Video ends with {end - start:.2f}s of black frames (from {start:.2f}s to "
                    "end) — rendered timeline is longer than the visual content",
                    span_sec=(start, end),
                    scene_id=scene_id_at(start),
                    key=ids.time_key(start),
                    metrics={"durationSec": round(end - start, 3)},
                    rubric_dimension="motion-timing",
                )
            )
        else:
            r.add(
                Finding(
                    "black_freeze",
                    "BLACK_SPAN",
                    "warning",
                    f"Black frames from {start:.2f}s to {end:.2f}s ({end - start:.2f}s)",
                    span_sec=(start, end),
                    scene_id=scene_id_at(start),
                    key=ids.time_key(start),
                    metrics={"durationSec": round(end - start, 3)},
                )
            )

    r.set_metric("blackFreeze.freezeSpanCount", len(fp.freeze_spans))
    for start, end in fp.freeze_spans:
        open_ended = end < 0
        end_eff = v.duration_sec if open_ended else end
        dur = end_eff - start
        # A still image can be a legitimate design choice in motion graphics;
        # freezes running to EOF or eating most of a scene are not.
        severity: Severity = "warning" if (open_ended or dur >= 3.0) else "info"
        suffix = " (runs to end of video)" if open_ended else ""
        r.add(
            Finding(
                "black_freeze",
                "FREEZE_SPAN",
                severity,
                f"Frozen frame from {start:.2f}s to {end_eff:.2f}s ({dur:.2f}s){suffix}",
                span_sec=(start, end_eff),
                scene_id=scene_id_at(start),
                key=ids.time_key(start),
                metrics={"durationSec": round(dur, 3)},
                rubric_dimension="motion-timing",
            )
        )
