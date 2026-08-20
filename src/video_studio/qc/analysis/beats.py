"""Beat tracking via librosa ([beats] extra) — cuts landing on beats.

The one capability worth librosa's numba tax: beat_track gives musical beat
times, and `beat_alignment` measures what fraction of scene cuts land within
a window of a beat — the plan's beatAlignmentScore, rubric dimension 4's
last mile. Everything degrades to None when librosa is absent.
"""

from __future__ import annotations

import numpy as np

BEAT_WINDOW_SEC = 0.10


def beat_times(pcm: np.ndarray, sample_rate: int) -> list[float] | None:
    """Beat positions in seconds, or None when librosa isn't installed or
    the audio has no usable tempo."""
    try:
        import librosa
    except ImportError:
        return None
    if len(pcm) < sample_rate:
        return None
    try:
        _tempo, frames = librosa.beat.beat_track(y=pcm.astype(np.float32), sr=sample_rate)
        times = librosa.frames_to_time(frames, sr=sample_rate)
        return [float(t) for t in times]
    except Exception:
        return None


def beat_alignment(
    cuts: list[float], beats: list[float], window_sec: float = BEAT_WINDOW_SEC
) -> float | None:
    """Fraction of cuts within ±window of a beat. None when either is empty."""
    if not cuts or not beats:
        return None
    arr = np.asarray(beats)
    hits = sum(1 for c in cuts if float(np.abs(arr - c).min()) <= window_sec)
    return hits / len(cuts)
