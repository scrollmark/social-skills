"""AudioTrack: one PCM decode per file, with cached envelopes.

v1 decoded the mix PCM independently in audio_sync AND audio_quality, and
decoded every scene WAV once per consumer. This class is the single audio
entry point: the mix decodes once, envelopes memoize, and per-path WAV
envelopes cache in a dict.
"""

from __future__ import annotations

from functools import cached_property
from pathlib import Path

import numpy as np

from video_studio.qc.analysis.align import ENVELOPE_RATE_HZ, decode_pcm, rms_envelope

SAMPLE_RATE = 16_000


class AudioTrack:
    """Lazy, cached audio access for one media file (usually the final mix)."""

    def __init__(self, path: str | Path, sample_rate: int = SAMPLE_RATE) -> None:
        self.path = str(path)
        self.sample_rate = sample_rate
        self._wav_envelopes: dict[str, np.ndarray] = {}

    @cached_property
    def pcm(self) -> np.ndarray:
        return decode_pcm(self.path, self.sample_rate)

    @cached_property
    def envelope(self) -> np.ndarray:
        """RMS envelope at ENVELOPE_RATE_HZ (10 ms hop)."""
        return rms_envelope(self.pcm, self.sample_rate)

    @cached_property
    def envelope_db(self) -> np.ndarray:
        return np.asarray(20 * np.log10(np.maximum(self.envelope, 1e-6)))

    def wav_envelope(self, wav_path: str | Path) -> np.ndarray:
        """Envelope of a sidecar WAV (per-scene narration), cached per path."""
        key = str(wav_path)
        if key not in self._wav_envelopes:
            self._wav_envelopes[key] = rms_envelope(
                decode_pcm(key, self.sample_rate), self.sample_rate
            )
        return self._wav_envelopes[key]

    def wav_pcm_head(self, wav_path: str | Path, seconds: float) -> np.ndarray:
        """First N seconds of a sidecar WAV's PCM (for needle extraction)."""
        return decode_pcm(str(wav_path), self.sample_rate)[: int(seconds * self.sample_rate)]


__all__ = ["ENVELOPE_RATE_HZ", "SAMPLE_RATE", "AudioTrack"]
