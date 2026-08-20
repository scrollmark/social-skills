"""On-screen caption timing vs audio/<scene>.timings.json ground truth. [ocr]

v1 port, now PURE over Artifacts.caption_sightings — the OCR pass rides the
shared decode (services.model_services.CaptionOcrService, 5 fps caption-band
crops). Thresholds and messages unchanged.
"""

from __future__ import annotations

import numpy as np

from video_studio.qc.analysis.textmatch import edit_distance_le1, normalize_word
from video_studio.qc.context import Context
from video_studio.qc.report.model import Finding, Severity

SAMPLE_FPS = 5.0
MATCH_WINDOW_MS = 1500.0
OFFSET_WARN_MS = 200.0
OFFSET_ERROR_MS = 600.0
MATCH_RATE_WARN = 0.85
BLEED_GRACE_MS = 600.0


def run(ctx: Context) -> None:
    gt = ctx.ground_truth
    r = ctx.report
    assert gt is not None

    if not gt.caption_words:
        r.add(
            Finding(
                "caption_sync",
                "NO_CAPTION_DATA",
                "info",
                "No audio/<scene>.timings.json in the project — narration was never "
                "synthesised or transcribed, so there is nothing to compare the "
                "on-screen words against",
            )
        )
        return

    sightings = ctx.artifacts.caption_sightings
    assert sightings is not None, "engine must run the caption OCR service first"

    def first_and_last_seen(word: str, around_ms: float) -> tuple[float | None, float | None]:
        first = last = None
        for t_ms, words in sightings:
            if t_ms < around_ms - MATCH_WINDOW_MS:
                continue
            if t_ms > around_ms + MATCH_WINDOW_MS + BLEED_GRACE_MS * 4:
                break
            if any(edit_distance_le1(word, w) for w in words):
                if first is None:
                    first = t_ms
                last = t_ms
        return first, last

    offsets_by_scene: dict[str, list[float]] = {}
    all_offsets: list[float] = []
    missing = 0
    considered = 0

    for cw in gt.caption_words:
        word = normalize_word(cw.text)
        if len(word) < 3:  # 1-2 char words OCR too unreliably to score
            continue
        considered += 1
        first, last = first_and_last_seen(word, cw.start_ms)
        if first is None:
            missing += 1
            continue
        offset = first - cw.start_ms
        all_offsets.append(offset)
        offsets_by_scene.setdefault(cw.scene_id, []).append(offset)

        scene = next((s for s in gt.scenes if s.id == cw.scene_id), None)
        if scene and last is not None:
            scene_end_ms = scene.end_sec * 1000.0
            if cw.end_ms <= scene_end_ms and last > scene_end_ms + BLEED_GRACE_MS:
                r.add(
                    Finding(
                        "caption_sync",
                        "CAPTION_BLEED",
                        "warning",
                        f"Caption word \"{cw.text}\" (scene '{cw.scene_id}') still on screen at "
                        f"{last / 1000:.2f}s, {last - scene_end_ms:.0f}ms past its scene's end",
                        scene_id=cw.scene_id,
                        key=normalize_word(cw.text),
                        span_sec=(scene_end_ms / 1000, last / 1000),
                    )
                )

    if considered == 0:
        return

    match_rate = 1.0 - missing / considered
    r.set_metric("sync.captionWordMatchRate", match_rate)
    if match_rate < MATCH_RATE_WARN:
        r.add(
            Finding(
                "caption_sync",
                "CAPTIONS_NOT_RENDERED",
                "error",
                f"Only {match_rate:.0%} of caption words were found on screen near their "
                f"scheduled time ({missing}/{considered} missing) — captions may not be "
                "rendering, or timing is off by more than the search window",
                metrics={"matchRate": round(match_rate, 3)},
                rubric_dimension="captions",
            )
        )

    if all_offsets:
        arr = np.array(all_offsets)
        median = float(np.median(arr))
        iqr = float(np.percentile(arr, 75) - np.percentile(arr, 25))
        r.set_metric("sync.medianCaptionOffsetMs", median)
        r.set_metric("sync.captionOffsetIqrMs", iqr)

        for scene_id, offs in offsets_by_scene.items():
            scene_median = float(np.median(offs))
            for st in r.scenes:
                if st.id == scene_id:
                    st.caption_offset_ms = scene_median

        # Sampling at 5 fps quantizes appearance times to ~200ms; only a
        # median beyond one sampling period is a real systemic lag.
        sample_period_ms = 1000.0 / SAMPLE_FPS
        if abs(median) > max(OFFSET_WARN_MS, sample_period_ms):
            severity: Severity = "error" if abs(median) > OFFSET_ERROR_MS else "warning"
            direction = "late" if median > 0 else "early"
            r.add(
                Finding(
                    "caption_sync",
                    "CAPTION_OFFSET",
                    severity,
                    (
                        f"Captions render a median of {abs(median):.0f}ms {direction} vs their "
                        f"word timings (IQR {iqr:.0f}ms across {len(all_offsets)} words) — a "
                        "systemic renderer lag, not per-word jitter"
                        if iqr < abs(median)
                        else f"Captions render a median of {abs(median):.0f}ms {direction} with "
                        f"high jitter (IQR {iqr:.0f}ms) — word timings themselves look unstable"
                    ),
                    metrics={"medianOffsetMs": round(median, 1), "iqrMs": round(iqr, 1)},
                    rubric_dimension="captions",
                )
            )
