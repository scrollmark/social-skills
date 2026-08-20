"""Frame visual quality findings over the shared decode's FrameStats.

The per-frame measurement (blur, banding, palette ΔE) happens in the engine's
visual service on the single shared decode; this detector applies v1's
thresholds to the collected series.
"""

from __future__ import annotations

import numpy as np

from video_studio.qc.context import Context
from video_studio.qc.report.model import Finding

BLUR_THRESHOLDS = {  # Laplacian variance below this = soft/blurry frame
    "faceless-explainer": 60.0,
    "manim-explainer": 60.0,
    "ai-video": 25.0,
    "composite": 25.0,
}
DEFAULT_BLUR_THRESHOLD = 25.0
BLUR_FRACTION_WARN = 0.4  # this share of frames soft → finding
PALETTE_DELTA_E = 25.0  # Lab distance counting as "off palette"
PALETTE_OFF_FRACTION_WARN = 0.35


def run(ctx: Context) -> None:
    r = ctx.report
    gt = ctx.ground_truth
    fmt = gt.format if gt else None
    stats = ctx.artifacts.frame_stats
    assert stats is not None, "engine must run the visual service before visual"

    blur_threshold = BLUR_THRESHOLDS.get(fmt or "", DEFAULT_BLUR_THRESHOLD)

    if not stats.blur_scores:
        return

    arr = np.array(stats.blur_scores)
    r.set_metric("visual.blurLaplacianP10", float(np.percentile(arr, 10)))
    r.set_metric("visual.blurLaplacianMedian", float(np.median(arr)))
    soft_fraction = float((arr < blur_threshold).mean())
    worst_blur = stats.worst_blur
    if soft_fraction >= BLUR_FRACTION_WARN and worst_blur is not None:
        r.add(
            Finding(
                "visual",
                "SOFT_FOOTAGE",
                "warning",
                f"{soft_fraction:.0%} of sampled frames are soft/blurry (Laplacian variance < "
                f"{blur_threshold:.0f}; worst {worst_blur[0]:.0f} at {worst_blur[1]:.1f}s)",
                span_sec=(worst_blur[1], worst_blur[1]),
                metrics={"softFraction": round(soft_fraction, 3)},
                rubric_dimension="visual-quality",
            )
        )

    band = float(np.median(stats.banding_scores))
    r.set_metric("visual.bandingScoreMedian", band)
    if band > 0.25:
        r.add(
            Finding(
                "visual",
                "BANDING",
                "info",
                f"Large smooth-gradient regions ({band:.0%} of frame area) — vulnerable to "
                "visible banding after platform re-encode; consider subtle noise/dither in "
                "backgrounds",
                metrics={"bandingScore": round(band, 3)},
                rubric_dimension="visual-quality",
            )
        )

    if stats.off_palette_fractions:
        off_med = float(np.median(stats.off_palette_fractions))
        r.set_metric("visual.offPaletteFraction", off_med)
        if off_med > PALETTE_OFF_FRACTION_WARN and gt is not None:
            r.add(
                Finding(
                    "visual",
                    "OFF_PALETTE",
                    "warning",
                    f"A median {off_med:.0%} of pixels sit far (ΔE > {PALETTE_DELTA_E:.0f}) "
                    f"from every style-preset color — the render drifts from the '{gt.style}' "
                    "palette",
                    metrics={"offPaletteFraction": round(off_med, 3)},
                    rubric_dimension="visual-quality",
                )
            )
