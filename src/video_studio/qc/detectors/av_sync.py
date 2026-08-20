"""Audio-visual correlation: does the picture move when the sound happens?

Targets the two taxonomy gaps showrunner's own README admits its analyzer
cannot see: 3.3 ASMR (micro-interaction vs audio spike) and 4.2 lip-sync
(global track alignment). Signals:

  video: frame-diff energy at 25 fps from the shared decode (Artifacts.energy_samples)
  audio: spectral-flux onset envelope at 100 Hz from the shared AudioTrack

Global lag by normalized cross-correlation; event-level match rate over the
top onset peaks. New detector — no v1 counterpart, excluded from parity.
"""

from __future__ import annotations

import numpy as np

from video_studio.qc.analysis.beats import beat_alignment, beat_times
from video_studio.qc.analysis.onsets import RATE_HZ, normalized_xcorr_lag, onset_envelope, pick_peaks
from video_studio.qc.context import Context
from video_studio.qc.report import ids
from video_studio.qc.report.model import Finding, Severity

LAG_WARN_MS = 67.0  # ~2 frames at 30fps
LAG_ERROR_MS = 200.0
WEAK_COUPLING = 0.2
EVENT_WINDOW_MS = 200.0
MAX_EVENTS = 40


def _motion_at_100hz(samples: list[tuple[float, float]], duration_sec: float) -> np.ndarray:
    """Resample (t, energy) pairs onto the 100 Hz onset grid by interpolation."""
    if not samples or duration_sec <= 0:
        return np.zeros(0, dtype=np.float64)
    times = np.array([t for t, _ in samples])
    values = np.array([v for _, v in samples])
    grid = np.arange(0, duration_sec, 1.0 / RATE_HZ)
    out: np.ndarray = np.interp(grid, times, values)
    return out


def run(ctx: Context) -> None:
    r = ctx.report
    samples = ctx.artifacts.energy_samples
    assert samples is not None, "engine must run the energy service before av_sync"

    if ctx.video.audio is None:
        r.add(
            Finding(
                "av_sync",
                "NO_AUDIO_TO_CORRELATE",
                "info",
                "Video has no audio stream — audio-visual correlation is undefined",
            )
        )
        return

    onsets = onset_envelope(ctx.audio.pcm, ctx.audio.sample_rate)
    motion = _motion_at_100hz(samples, ctx.video.duration_sec)
    n = min(len(onsets), len(motion))
    if n < RATE_HZ:  # under a second of overlap: nothing to say
        return
    onsets = onsets[:n]
    motion = motion[:n]

    result = normalized_xcorr_lag(motion, onsets, max_lag=2 * RATE_HZ)
    if result is not None:
        lag, correlation = result
        lag_ms = lag * 1000.0 / RATE_HZ
        r.set_metric("avSync.offsetMs", lag_ms)
        r.set_metric("avSync.correlation", correlation)
        if correlation >= WEAK_COUPLING and abs(lag_ms) >= LAG_WARN_MS:
            severity: Severity = "error" if abs(lag_ms) >= LAG_ERROR_MS else "warning"
            r.add(
                Finding(
                    "av_sync",
                    "AV_LAG",
                    severity,
                    f"Audio events land {abs(lag_ms):.0f}ms "
                    f"{'after' if lag_ms > 0 else 'before'} their visual motion "
                    f"(correlation {correlation:.2f}) — a global A/V offset",
                    metrics={"lagMs": round(lag_ms, 1), "correlation": round(correlation, 3)},
                    rubric_dimension="audio",
                )
            )
        if correlation < WEAK_COUPLING:
            r.add(
                Finding(
                    "av_sync",
                    "WEAK_AV_COUPLING",
                    "warning",
                    f"Visual motion barely tracks the audio (peak correlation "
                    f"{correlation:.2f}) — sounds happen without visible causes, the "
                    "signature failure for ASMR/sync-driven content",
                    metrics={"correlation": round(correlation, 3)},
                    rubric_dimension="audio",
                )
            )

    # Event level: every prominent sound should have a visible cause nearby.
    peaks = pick_peaks(onsets)[:MAX_EVENTS]
    if peaks:
        window = int(EVENT_WINDOW_MS / 1000.0 * RATE_HZ)
        motion_med = float(np.median(motion))
        motion_mad = float(np.median(np.abs(motion - motion_med))) or 1e-9
        matched = 0
        for peak in peaks:
            lo = max(0, peak - window)
            hi = min(len(motion), peak + window + 1)
            if float(motion[lo:hi].max()) > motion_med + 2.0 * motion_mad:
                matched += 1
            else:
                t = peak / RATE_HZ
                r.add(
                    Finding(
                        "av_sync",
                        "UNMATCHED_ONSET",
                        "info",
                        f"Distinct sound at {t:.2f}s has no visible motion within "
                        f"±{EVENT_WINDOW_MS:.0f}ms — audio without a visual cause",
                        key=ids.time_key(t, 0.1),
                        span_sec=(t, t),
                    )
                )
        r.set_metric("avSync.onsetMatchRate", matched / len(peaks))
        r.set_metric("avSync.onsetCount", len(peaks))

    # Beat alignment ([beats] extra; metric-only, no deduction until
    # calibrated): what fraction of detected cuts land ON a musical beat.
    cuts = ctx.artifacts.cuts
    if cuts:
        beats = beat_times(ctx.audio.pcm, ctx.audio.sample_rate)
        if beats:
            score = beat_alignment(cuts, beats)
            if score is not None:
                r.set_metric("sync.beatAlignmentScore", score)
                r.set_metric("sync.beatCount", len(beats))
