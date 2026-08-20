"""Audio onset + band-energy envelopes (numpy + scipy.signal; librosa's numba
tax still not worth it for these).

Spectral flux onset strength: framewise rfft (40 ms window, 10 ms hop),
half-wave-rectified log-magnitude first difference summed over bins. The
result is a 100 Hz envelope aligned with align.ENVELOPE_RATE_HZ so the
av_sync detector can correlate it directly against visual motion energy.

Peak picking is scipy.signal.find_peaks; the speech band is a zero-phase
Butterworth bandpass (sosfiltfilt — no group delay, so lag estimates stay
honest). The original hand-rolled implementations survive as `_legacy_*`
oracles in tests only.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, find_peaks, sosfiltfilt

RATE_HZ = 100  # 10 ms hop, matches align.ENVELOPE_RATE_HZ
WINDOW_SEC = 0.040


def _frames(pcm: np.ndarray, sample_rate: int) -> np.ndarray:
    hop = sample_rate // RATE_HZ
    win = int(sample_rate * WINDOW_SEC)
    n = max(0, (len(pcm) - win) // hop + 1)
    if n == 0:
        return np.zeros((0, win), dtype=np.float64)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    out: np.ndarray = pcm[idx].astype(np.float64) * np.hanning(win)[None, :]
    return out


def onset_envelope(pcm: np.ndarray, sample_rate: int = 16_000) -> np.ndarray:
    """Spectral-flux onset strength at RATE_HZ. Empty input -> empty array."""
    frames = _frames(pcm, sample_rate)
    if len(frames) == 0:
        return np.zeros(0, dtype=np.float32)
    mags = np.log1p(np.abs(np.fft.rfft(frames, axis=1)))
    flux = np.diff(mags, axis=0, prepend=mags[:1])
    flux = np.maximum(flux, 0.0)  # half-wave rectify: energy INCREASES only
    out: np.ndarray = flux.sum(axis=1).astype(np.float32)
    return out


def band_envelope(
    pcm: np.ndarray,
    sample_rate: int = 16_000,
    lo_hz: float = 300.0,
    hi_hz: float = 3400.0,
) -> np.ndarray:
    """Energy envelope restricted to a frequency band (speech band by default)
    at RATE_HZ — for lip-sync, where broadband music must not dominate.

    Zero-phase Butterworth bandpass then framewise RMS: unlike the old
    FFT-bin-sum, real filter rolloff and NO group delay (sosfiltfilt), so
    downstream lag estimates aren't biased by the filter itself."""
    if len(pcm) < 32:
        return np.zeros(0, dtype=np.float32)
    nyquist = sample_rate / 2.0
    hi = min(hi_hz, nyquist * 0.99)
    sos = butter(4, [lo_hz, hi], btype="bandpass", fs=sample_rate, output="sos")
    filtered = sosfiltfilt(sos, pcm.astype(np.float64))
    frames = _frames(filtered, sample_rate)
    if len(frames) == 0:
        return np.zeros(0, dtype=np.float32)
    out: np.ndarray = np.sqrt(np.mean(frames**2, axis=1)).astype(np.float32)
    return out


def pick_peaks(
    envelope: np.ndarray,
    rate_hz: int = RATE_HZ,
    min_separation_sec: float = 0.15,
) -> list[int]:
    """Indices of prominent peaks: above median + 3*MAD, spaced at least
    min_separation apart. scipy.find_peaks with `distance` implements the
    same greedy strongest-first spacing the hand-rolled version did."""
    if len(envelope) < 3:
        return []
    med = float(np.median(envelope))
    mad = float(np.median(np.abs(envelope - med))) or 1e-9
    threshold = med + 3.0 * mad
    min_gap = max(1, int(min_separation_sec * rate_hz))
    peaks, _ = find_peaks(
        envelope.astype(np.float64),
        height=np.nextafter(threshold, np.inf),  # strict >, matching the oracle
        distance=min_gap,
        prominence=mad,
    )
    return [int(p) for p in peaks]


def normalized_xcorr_lag(a: np.ndarray, b: np.ndarray, max_lag: int) -> tuple[int, float] | None:
    """Best lag of b relative to a within +/-max_lag, by normalized correlation.
    Returns (lag, correlation) or None on degenerate input. Positive lag means
    b happens LATER than a."""
    n = min(len(a), len(b))
    if n < 8:
        return None
    a = a[:n].astype(np.float64)
    b = b[:n].astype(np.float64)
    a = a - a.mean()
    b = b - b.mean()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom < 1e-9:
        return None
    best: tuple[int, float] | None = None
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            xa, xb = a[: n - lag], b[lag:]
        else:
            xa, xb = a[-lag:], b[: n + lag]
        if len(xa) < 8:
            continue
        d = np.linalg.norm(xa) * np.linalg.norm(xb)
        if d < 1e-9:
            continue
        score = float(np.dot(xa, xb) / d)
        if best is None or score > best[1]:
            best = (lag, score)
    return best
