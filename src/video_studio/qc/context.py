"""The typed boundary between the media phase and the detector phase.

Detectors are pure functions `run(ctx: Context) -> None` — this module is the
whole surface they may touch. v1 (and early showwatcher) typed this boundary
`Any` to dodge a circular import; nothing here imports detectors or the
engine, so the dodge is gone and mypy checks the most important seam in the
codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from video_studio.qc.media.audio import AudioTrack
from video_studio.qc.media.ffmpeg_filters import FilterPassResult
from video_studio.qc.media.probe import VideoInfo
from video_studio.qc.report.model import Report
from video_studio.qc.ground_truth import GroundTruth


@dataclass
class FrameStats:
    """Per-frame visual measurements from the shared decode (visual service)."""

    blur_scores: list[float] = field(default_factory=list)
    banding_scores: list[float] = field(default_factory=list)
    off_palette_fractions: list[float] = field(default_factory=list)
    worst_blur: tuple[float, float] | None = None  # (score, t_sec)
    palette_checked: bool = False


@dataclass
class PaneStats:
    """Per-frame composition profiles from the shared decode (pane service)."""

    column_profiles: list[Any] = field(default_factory=list)  # per-frame |Sobel_x| col means
    block_energies: list[Any] = field(default_factory=list)  # per-frame column-block motion
    key_hue_fractions: list[float] = field(default_factory=list)  # chroma-hue pixel fraction


@dataclass
class Artifacts:
    """Everything the media phase produced for the detector phase."""

    filter_pass: FilterPassResult | None = None
    cuts: list[float] | None = None
    frame_stats: FrameStats | None = None
    motion_samples: list[tuple[float, float, float]] | None = None  # (t_prev, t_cur, speed)
    energy_samples: list[tuple[float, float]] | None = None  # (t, frame-diff energy) @25fps
    pane_stats: PaneStats | None = None
    mouth_series: list[tuple[float, float]] | None = None  # (t, mouth openness/energy)
    mouth_mode: str | None = None  # "mediapipe" (real aperture) | "haar" (degraded) | "none"
    # Up to N small color frames per scene id, for CLIP prompt-fit scoring.
    scene_frames: dict[str, list[Any]] | None = None
    # Model-backed services (see services.model_services):
    caption_sightings: list[tuple[float, set[str]]] | None = None  # (t_ms, words)
    ocr_boxes: list[dict[str, Any]] | None = None  # full-frame OCR per layout sample
    detections: list[tuple[float, set[str], int]] | None = None  # (t, classes, persons)


@dataclass
class Context:
    video_path: str
    video: VideoInfo
    report: Report
    audio: AudioTrack
    artifacts: Artifacts
    ground_truth: GroundTruth | None = None
    evidence_dir: str | None = None
    taxonomy: str | None = None
