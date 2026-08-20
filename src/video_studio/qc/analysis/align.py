"""Shared alignment primitives for the sync detectors.

Port of analyzer/align.py with `envelope_offset_ms` vectorized. The naive
per-lag Python loop is retained as `_envelope_offset_ms_naive` and serves as
the oracle in tests — the vectorized path must pick the SAME lag on every
input, including deliberately periodic ones.

The behavior that must not regress: among lags scoring within EPSILON of the
best, prefer the one closest to the expected position. Periodic content
(music beats, repeated jingles) produces multiple near-equal correlation
peaks, and float noise must not decide which repetition wins.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

import numpy as np

ENVELOPE_RATE_HZ = 100  # 10 ms hop
EPSILON = 0.02  # near-tie window for the expected-position tie-break


def decode_pcm(path: str, sample_rate: int = 16_000) -> np.ndarray:
    """Decode any audio (or a video's audio track) to mono float32 PCM."""
    result = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            path,
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "f32le",
            "-",
        ],
        capture_output=True,
        check=True,
    )
    return np.frombuffer(result.stdout, dtype=np.float32)


def rms_envelope(
    pcm: np.ndarray, sample_rate: int = 16_000, rate_hz: int = ENVELOPE_RATE_HZ
) -> np.ndarray:
    """RMS envelope at rate_hz frames/sec (default 10 ms hop)."""
    hop = sample_rate // rate_hz
    n = len(pcm) // hop
    if n == 0:
        return np.zeros(0, dtype=np.float32)
    frames = pcm[: n * hop].reshape(n, hop)
    out: np.ndarray = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1)).astype(np.float32)
    return out


def _tie_break(
    scores: np.ndarray,
    valid: np.ndarray,
    lo: int,
    expected_index: int,
) -> int | None:
    """Among valid lags within EPSILON of the best score, pick the one closest
    to the expected position. Equal distances resolve to the lowest position —
    the same order the naive loop's `min()` produced."""
    if not valid.any():
        return None
    best_score = scores[valid].max()
    candidate_mask = valid & (scores >= best_score - EPSILON)
    positions = np.nonzero(candidate_mask)[0]
    distances = np.abs(lo + positions - expected_index)
    return int(positions[np.argmin(distances)])


def envelope_offset_ms(
    needle: np.ndarray,
    haystack: np.ndarray,
    expected_index: int,
    search_radius: int,
    rate_hz: int = ENVELOPE_RATE_HZ,
) -> tuple[float, float] | None:
    """Locate `needle` (a scene's envelope head) inside `haystack` (the mix
    envelope) near expected_index. Returns (offset_ms, confidence) where
    offset > 0 means the scene audio starts LATER than planned; confidence
    is the normalized correlation peak in [0, 1]. None when there is no
    usable signal (silent needle or empty search window).

    Vectorized: per-lag means and norms come from cumulative sums, giving the
    identical mean-subtracted normalized correlation the naive loop computes
    (dot(n, seg - seg.mean()) == dot(n, seg) because sum(n) == 0).
    """
    if len(needle) < rate_hz // 4:  # < 250 ms of envelope: nothing to lock onto
        return None
    lo = max(0, expected_index - search_radius)
    hi = min(len(haystack), expected_index + search_radius + len(needle))
    window = haystack[lo:hi].astype(np.float64)
    m = len(needle)
    if len(window) < m:
        return None

    n = needle.astype(np.float64) - float(needle.mean())
    n_norm = float(np.linalg.norm(n))
    if n_norm < 1e-6:
        return None  # flat/silent needle

    # Sliding dot product of the mean-subtracted needle against every segment.
    corr = np.correlate(window, n, mode="valid")

    # Per-segment norms after mean subtraction, via cumulative sums:
    #   sum(seg^2) - m * mean(seg)^2
    csum = np.concatenate(([0.0], np.cumsum(window)))
    csum2 = np.concatenate(([0.0], np.cumsum(window**2)))
    seg_sums = csum[m:] - csum[:-m]
    seg_sums2 = csum2[m:] - csum2[:-m]
    seg_var = np.maximum(seg_sums2 - seg_sums**2 / m, 0.0)
    seg_norms = np.sqrt(seg_var)

    # The naive loop `continue`s on s_norm < 1e-9 — mask identically, or a
    # flat window region becomes a spurious near-tie candidate.
    valid = seg_norms >= 1e-9
    scores = np.zeros_like(corr)
    scores[valid] = corr[valid] / (n_norm * seg_norms[valid])

    best_pos = _tie_break(scores, valid, lo, expected_index)
    if best_pos is None:
        return None
    best_score = float(scores[valid].max())

    found_index = lo + best_pos
    offset_ms = (found_index - expected_index) * (1000.0 / rate_hz)
    return offset_ms, max(0.0, best_score)


def _envelope_offset_ms_naive(
    needle: np.ndarray,
    haystack: np.ndarray,
    expected_index: int,
    search_radius: int,
    rate_hz: int = ENVELOPE_RATE_HZ,
) -> tuple[float, float] | None:
    """The v1 per-lag loop, kept verbatim as the oracle for the vectorized path."""
    if len(needle) < rate_hz // 4:
        return None
    lo = max(0, expected_index - search_radius)
    hi = min(len(haystack), expected_index + search_radius + len(needle))
    window = haystack[lo:hi]
    if len(window) < len(needle):
        return None

    n = needle - needle.mean()
    n_norm = np.linalg.norm(n)
    if n_norm < 1e-6:
        return None

    scores: list[tuple[int, float]] = []
    for pos in range(0, len(window) - len(needle) + 1):
        seg = window[pos : pos + len(needle)]
        s = seg - seg.mean()
        s_norm = np.linalg.norm(s)
        if s_norm < 1e-9:
            continue
        scores.append((pos, float(np.dot(n, s) / (n_norm * s_norm))))
    if not scores:
        return None

    best_score = max(score for _, score in scores)
    candidates = [pos for pos, score in scores if score >= best_score - EPSILON]
    best_pos = min(candidates, key=lambda pos: abs(lo + pos - expected_index))

    found_index = lo + best_pos
    offset_ms = (found_index - expected_index) * (1000.0 / rate_hz)
    return offset_ms, max(0.0, best_score)


@dataclass
class Match:
    expected_index: int  # index into the expected/planned series
    actual_index: int  # index into the detected series
    drift: float  # actual - expected, same unit as the inputs


def match_monotonic(
    expected: list[float],
    actual: list[float],
    tolerance: float,
) -> list[Match]:
    """Greedy monotonic matching: walk both sorted series, pair each expected
    event with the nearest unconsumed actual event within tolerance. Keeps
    ordering (no crossing pairs), so one spurious detection can't steal a
    later boundary's match."""
    matches: list[Match] = []
    j = 0
    for i, e in enumerate(expected):
        best: tuple[float, int] | None = None
        k = j
        while k < len(actual) and actual[k] <= e + tolerance:
            d = abs(actual[k] - e)
            if d <= tolerance and (best is None or d < best[0]):
                best = (d, k)
            k += 1
        if best is not None:
            matches.append(Match(i, best[1], actual[best[1]] - e))
            j = best[1] + 1
    return matches


@dataclass
class DriftSummary:
    mean: float
    max_abs: float
    slope_per_event: float  # least-squares slope over event index
    intercept: float

    @property
    def is_cumulative(self) -> bool:
        """Heuristic: drift growing event-over-event (concat/fps rounding bug)
        rather than a constant head offset."""
        return abs(self.slope_per_event) > 1e-9 and abs(self.slope_per_event) * 3 > abs(
            self.intercept
        )


def summarize_drift(matches: list[Match]) -> DriftSummary | None:
    if not matches:
        return None
    drifts = np.array([m.drift for m in matches], dtype=np.float64)
    indices = np.array([m.expected_index for m in matches], dtype=np.float64)
    if len(matches) >= 2:
        slope, intercept = np.polyfit(indices, drifts, 1)
    else:
        slope, intercept = 0.0, drifts[0]
    return DriftSummary(
        mean=float(drifts.mean()),
        max_abs=float(np.abs(drifts).max()),
        slope_per_event=float(slope),
        intercept=float(intercept),
    )
