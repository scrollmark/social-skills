"""v1-style private frame sampling, retained for the extras-backed detectors.

caption_sync/layout/transcript/objects run heavy models (easyocr, whisper,
YOLO) that dominate their runtime — folding their decode into the shared
pipeline buys little and complicates model batching, so they keep v1's
self-decoding loop for now. The always-on core path (visual, motion, cuts,
filters) is what the single-pass pipeline serves.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


@dataclass
class SampledFrame:
    t_sec: float
    image: Any  # BGR ndarray


def sample_frames(
    video_path: str,
    fps: float,
    start_sec: float = 0.0,
    end_sec: float | None = None,
) -> Iterator[SampledFrame]:
    """Yield frames at ~fps; decodes sequentially and picks the next frame past
    each sample point (v1 semantics, robust on long-GOP H.264)."""
    import cv2

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open {video_path}")
    try:
        interval = 1.0 / fps
        next_sample = start_sec
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            if end_sec is not None and t > end_sec:
                break
            if t + 1e-6 >= next_sample:
                yield SampledFrame(t_sec=t, image=frame)
                next_sample += interval
                if next_sample < t:
                    next_sample = t + interval
    finally:
        cap.release()


def caption_band(image: Any, aspect_ratio: str) -> tuple[Any, int]:
    """Crop the caption region; returns (crop, y_offset). Bottom 35% for 9:16,
    30% otherwise — where showrunner renders captions."""
    h = image.shape[0]
    frac = 0.35 if aspect_ratio == "9:16" else 0.30
    y0 = int(h * (1 - frac))
    return image[y0:], y0
