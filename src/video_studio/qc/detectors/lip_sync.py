"""Lip/track sync (4.2): does the mouth move when the speech happens?

Two mouth backends (see services.MouthService): mediapipe FaceMesh gives real
inner-lip aperture (findings carry confidence 0.9); the Haar fallback proxies
openness with mouth-ROI frame-diff energy (confidence 0.5, degraded mode).
Either way the series is correlated against the SPEECH-BAND (300-3400 Hz)
envelope — broadband would let music drown the voice.
"""

from __future__ import annotations

import numpy as np

from video_studio.qc.analysis.onsets import RATE_HZ, band_envelope, normalized_xcorr_lag
from video_studio.qc.context import Context
from video_studio.qc.report.model import Finding, Severity

OFFSET_WARN_MS = 80.0  # the broadcast +/-100ms window, minus a frame of slack
OFFSET_ERROR_MS = 200.0
ABSENT_BELOW = 0.15
MIN_FACE_SECONDS = 1.0


def run(ctx: Context) -> None:
    r = ctx.report
    series = ctx.artifacts.mouth_series  # list[(t, openness/energy)] or None
    assert series is not None, "engine must run the face service before lip_sync"
    confidence = 0.9 if ctx.artifacts.mouth_mode == "mediapipe" else 0.5

    if ctx.video.audio is None:
        return
    face_seconds = len(series) / 10.0  # sampled at 10 fps
    if face_seconds < MIN_FACE_SECONDS:
        r.add(
            Finding(
                "lip_sync",
                "NO_FACE_TRACKED",
                "info",
                f"No face visible for >= {MIN_FACE_SECONDS:.0f}s of sampled frames — "
                "lip-sync analysis skipped",
            )
        )
        return

    speech = band_envelope(ctx.audio.pcm, ctx.audio.sample_rate)
    if not len(speech) or float(speech.std()) < 1e-6:
        return

    times = np.array([t for t, _ in series])
    values = np.array([v for _, v in series])
    grid = np.arange(0, ctx.video.duration_sec, 1.0 / RATE_HZ)
    mouth = np.interp(grid, times, values)
    n = min(len(mouth), len(speech))
    result = normalized_xcorr_lag(mouth[:n], speech[:n], max_lag=RATE_HZ // 2)  # +/-500ms
    if result is None:
        return
    lag, correlation = result
    lag_ms = lag * 1000.0 / RATE_HZ
    r.set_metric("lipSync.offsetMs", lag_ms)
    r.set_metric("lipSync.correlation", correlation)

    if correlation < ABSENT_BELOW:
        r.add(
            Finding(
                "lip_sync",
                "LIP_SYNC_ABSENT",
                "warning",
                f"Mouth motion does not track the speech band (correlation "
                f"{correlation:.2f}) — the on-screen face is not producing the audio "
                "(dubbed, mis-cut, or a still)",
                confidence=confidence,
                metrics={"correlation": round(correlation, 3)},
                rubric_dimension="audio",
            )
        )
    elif abs(lag_ms) >= OFFSET_WARN_MS:
        severity: Severity = "error" if abs(lag_ms) >= OFFSET_ERROR_MS else "warning"
        r.add(
            Finding(
                "lip_sync",
                "LIP_AUDIO_OFFSET",
                severity,
                f"Speech runs {abs(lag_ms):.0f}ms {'behind' if lag_ms > 0 else 'ahead of'} "
                f"the mouth (correlation {correlation:.2f}) — outside the broadcast "
                "±100ms comfort window",
                confidence=confidence,
                metrics={"lagMs": round(lag_ms, 1), "correlation": round(correlation, 3)},
                rubric_dimension="audio",
            )
        )
