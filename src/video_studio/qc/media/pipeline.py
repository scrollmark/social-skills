"""Single-pass frame pipeline: decode once, fan out to every consumer.

The v1 analyzer's root performance defect: every frame-consuming detector
called `sample_frames()` itself, so one analysis decoded the video 4+N times
(visual, layout, caption_sync, objects, and motion once PER SCENE). Here the
video is decoded exactly once; each consumer declares its own sampling fps and
receives the frames it is due, with per-frame views (gray, resized) memoized so
five consumers asking for the same conversion pay for one.

The scheduling semantics per consumer are v1's `sample_frames` verbatim —
deliver the next decoded frame at-or-past each sample point, resync when decode
falls behind — so a consumer at fps F sees the SAME frames it would have seen
decoding privately. That equivalence is what makes the parity gate meaningful.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol


class FrameView:
    """One decoded frame with memoized derived views."""

    def __init__(self, t_sec: float, bgr: Any) -> None:
        self.t_sec = t_sec
        self.bgr = bgr
        self._gray: Any = None
        self._resized: dict[tuple[int, int, bool], Any] = {}

    @property
    def gray(self) -> Any:
        if self._gray is None:
            import cv2

            self._gray = cv2.cvtColor(self.bgr, cv2.COLOR_BGR2GRAY)
        return self._gray

    def resized(self, size: tuple[int, int], *, gray: bool = False) -> Any:
        """Downscale (INTER_AREA), memoized per (size, gray)."""
        key = (size[0], size[1], gray)
        if key not in self._resized:
            import cv2

            src = self.gray if gray else self.bgr
            self._resized[key] = cv2.resize(src, size, interpolation=cv2.INTER_AREA)
        return self._resized[key]


@dataclass
class FrameConsumer:
    """A subscriber to the shared decode at its own sampling rate."""

    name: str
    fps: float
    on_frame: Callable[[FrameView], None]
    _next_sample: float = field(default=0.0, repr=False)

    def offer(self, view: FrameView) -> None:
        if view.t_sec + 1e-6 >= self._next_sample:
            self.on_frame(view)
            self._next_sample += 1.0 / self.fps
            # If decode fell far behind the schedule, resync (v1 semantics).
            if self._next_sample < view.t_sec:
                self._next_sample = view.t_sec + 1.0 / self.fps


class FrameSource(Protocol):
    """Anything that yields (t_sec, bgr_frame) sequentially. One call = one decode."""

    def frames(self) -> Iterator[tuple[float, Any]]: ...


class CvFrameSource:
    """OpenCV sequential decode, timestamps from CAP_PROP_POS_MSEC (v1's clock).

    Tracks `open_count` so tests can assert the whole analysis decoded the
    video exactly once — the regression guard for the v1 defect.
    """

    def __init__(self, video_path: str) -> None:
        self.video_path = video_path
        self.open_count = 0

    def frames(self) -> Iterator[tuple[float, Any]]:
        import cv2

        self.open_count += 1
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise RuntimeError(f"OpenCV could not open {self.video_path}")
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                yield t, frame
        finally:
            cap.release()


class FramePipeline:
    def __init__(self, source: FrameSource) -> None:
        self.source = source
        self.consumers: list[FrameConsumer] = []

    def subscribe(
        self, name: str, fps: float, on_frame: Callable[[FrameView], None]
    ) -> FrameConsumer:
        consumer = FrameConsumer(name=name, fps=fps, on_frame=on_frame)
        self.consumers.append(consumer)
        return consumer

    def run(self) -> None:
        """One decode; every consumer sees exactly its due frames."""
        if not self.consumers:
            return
        for t_sec, bgr in self.source.frames():
            view = FrameView(t_sec, bgr)
            for consumer in self.consumers:
                consumer.offer(view)
