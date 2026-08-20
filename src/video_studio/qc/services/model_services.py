"""Model-backed frame services: OCR (easyocr) and object detection (YOLO)
riding the SAME shared decode as the pure-CV services.

This closes the last of the v1 self-decoding: caption_sync, layout, and
objects are now pure functions over these artifacts. The model inference cost
is unchanged (it always dominated); what's gone is their three extra
sequential decodes of the video.

Availability is decided by the ENGINE before subscribing (find_spec on the
extra's module) so the detectors themselves never import model packages.
"""

from __future__ import annotations

from typing import Any

from video_studio.qc.context import Context
from video_studio.qc.media.sampling import caption_band
from video_studio.qc.services.frame_services import ServiceSpec

CAPTION_OCR_FPS = 5.0  # caption_sync's v1 rate — band crop only, cheap-ish
LAYOUT_OCR_FPS = 1.0  # layout's v1 rate — full frame
OBJECTS_FPS = 1.0

_reader: Any = None


def get_ocr_reader() -> Any:
    """Module-singleton easyocr reader (shared by both OCR streams)."""
    global _reader
    if _reader is None:
        import easyocr

        _reader = easyocr.Reader(["en"], verbose=False)
    return _reader


class CaptionOcrService:
    """(t_ms, {normalized words on screen}) from the caption band — feeds
    caption_sync. Confidence filter and normalization applied here so the
    artifact is compact and the detector stays pure."""

    spec = ServiceSpec("caption_ocr", CAPTION_OCR_FPS)
    MIN_OCR_CONFIDENCE = 0.3

    def __init__(self, ctx: Context) -> None:
        from video_studio.qc.analysis.textmatch import normalize_word

        self._normalize = normalize_word
        gt = ctx.ground_truth
        self._aspect = gt.aspect_ratio if gt else "9:16"
        self.sightings: list[tuple[float, set[str]]] = []
        ctx.artifacts.caption_sightings = self.sightings

    def on_frame(self, view: Any) -> None:
        crop, _y0 = caption_band(view.bgr, self._aspect)
        words: set[str] = set()
        for _bbox, text, conf in get_ocr_reader().readtext(crop):
            if conf < self.MIN_OCR_CONFIDENCE:
                continue
            for token in str(text).split():
                w = self._normalize(token)
                if w:
                    words.add(w)
        self.sightings.append((view.t_sec * 1000.0, words))


class LayoutOcrService:
    """Full-frame OCR boxes per ~1s frame — feeds layout. The raw frame is
    retained ONLY when an evidence dir is configured (annotated stills)."""

    spec = ServiceSpec("layout_ocr", LAYOUT_OCR_FPS)

    def __init__(self, ctx: Context) -> None:
        self._keep_frames = ctx.evidence_dir is not None
        self.samples: list[dict[str, Any]] = []
        ctx.artifacts.ocr_boxes = self.samples

    def on_frame(self, view: Any) -> None:
        img = view.bgr
        raw = [
            (bbox, str(text), float(conf)) for bbox, text, conf in get_ocr_reader().readtext(img)
        ]
        self.samples.append(
            {
                "t_sec": view.t_sec,
                "shape": (img.shape[0], img.shape[1]),
                "results": raw,
                "frame": img.copy() if self._keep_frames else None,
            }
        )


class ObjectService:
    """YOLOv8n class detections per ~1s frame — feeds objects."""

    spec = ServiceSpec("objects", OBJECTS_FPS)
    CONFIDENCE = 0.35

    def __init__(self, ctx: Context) -> None:
        from ultralytics import YOLO

        self._model = YOLO("yolov8n.pt")
        self._names = self._model.names
        self.detections: list[tuple[float, set[str], int]] = []
        ctx.artifacts.detections = self.detections

    def on_frame(self, view: Any) -> None:
        results = self._model.predict(view.bgr, conf=self.CONFIDENCE, verbose=False)
        detected: set[str] = set()
        persons = 0
        for res in results:
            for cls_id in res.boxes.cls.tolist():
                cls_name = self._names[int(cls_id)]
                detected.add(cls_name)
                if cls_name == "person":
                    persons += 1
        self.detections.append((view.t_sec, detected, persons))
