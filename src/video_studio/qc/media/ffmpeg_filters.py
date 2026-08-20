"""One chained ffmpeg pass: blackdetect + freezedetect + ebur128.

v1 ran these as THREE separate full-decode invocations (black_freeze.py ran
two, audio_quality.py a third). All three filters are pass-through analyzers
that log to stderr, so they chain into a single command — one decode instead
of three. The parsing regexes are v1's verbatim; the parity gate holds the
outputs to the same values.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

BLACK_MIN_SEC = 0.15  # ignore sub-frame flickers / intentional dips shorter than this
FREEZE_MIN_SEC = 1.5  # motion-graphics scenes legitimately hold stills briefly

_BLACK_RE = re.compile(r"black_start:(?P<start>[\d.]+).*?black_end:(?P<end>[\d.]+)")
_FREEZE_START_RE = re.compile(r"lavfi\.freezedetect\.freeze_start: (?P<t>[\d.]+)")
_FREEZE_END_RE = re.compile(r"lavfi\.freezedetect\.freeze_end: (?P<t>[\d.]+)")
_SUMMARY_RE = re.compile(
    r"Integrated loudness:.*?I:\s*(?P<i>-?[\d.]+)\s*LUFS.*?"
    r"Loudness range:.*?LRA:\s*(?P<lra>[\d.]+)\s*LU",
    re.S,
)
_PEAK_RE = re.compile(r"Peak:\s*(?P<peak>-?[\d.]+|-inf)\s*dBFS")


@dataclass
class FilterPassResult:
    black_spans: list[tuple[float, float]] = field(default_factory=list)
    freeze_spans: list[tuple[float, float]] = field(default_factory=list)  # end=-1.0: open
    integrated_lufs: float | None = None
    loudness_range_lu: float | None = None
    true_peak_dbfs: float | None = None

    @property
    def loudness(self) -> tuple[float, float, float | None] | None:
        """(integrated LUFS, LRA, true peak dBFS) or None — v1's tuple shape."""
        if self.integrated_lufs is None or self.loudness_range_lu is None:
            return None
        return self.integrated_lufs, self.loudness_range_lu, self.true_peak_dbfs


def run_filter_pass(
    video_path: str,
    *,
    has_audio: bool,
    black_min_sec: float = BLACK_MIN_SEC,
    freeze_min_sec: float = FREEZE_MIN_SEC,
) -> FilterPassResult:
    """Decode once, run all three analyzers, parse one stderr."""
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        video_path,
        "-vf",
        f"blackdetect=d={black_min_sec}:pix_th=0.10,freezedetect=n=-60dB:d={freeze_min_sec}",
    ]
    if has_audio:
        cmd += ["-af", "ebur128=peak=true"]
    else:
        cmd += ["-an"]
    cmd += ["-f", "null", "-"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return parse_filter_stderr(result.stderr)


def parse_filter_stderr(stderr: str) -> FilterPassResult:
    out = FilterPassResult()

    out.black_spans = [
        (float(m.group("start")), float(m.group("end"))) for m in _BLACK_RE.finditer(stderr)
    ]

    starts = [float(m.group("t")) for m in _FREEZE_START_RE.finditer(stderr)]
    ends = [float(m.group("t")) for m in _FREEZE_END_RE.finditer(stderr)]
    spans = list(zip(starts, ends, strict=False))
    if len(starts) > len(ends):
        # A freeze still running at EOF has a start but no end line.
        spans.append((starts[len(ends)], -1.0))
    out.freeze_spans = spans

    m = _SUMMARY_RE.search(stderr)
    if m:
        out.integrated_lufs = float(m.group("i"))
        out.loudness_range_lu = float(m.group("lra"))
        peak_m = _PEAK_RE.search(stderr)
        if peak_m and peak_m.group("peak") != "-inf":
            out.true_peak_dbfs = float(peak_m.group("peak"))
    return out
