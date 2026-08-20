"""Text layout QC: clipping, safe-margin overflow, overlap, watermark. [ocr]

v1 port, now PURE over Artifacts.ocr_boxes — the full-frame OCR pass rides
the shared decode (services.model_services.LayoutOcrService, 1 fps).
Evidence stills carry v2 `key`s derived from the clipped text, so re-running
with a new black span elsewhere no longer renames layout findings.
"""

from __future__ import annotations

from typing import Any

from video_studio.qc.analysis.textmatch import normalize_word
from video_studio.qc.context import Context
from video_studio.qc.report import ids
from video_studio.qc.report.model import Finding

SAMPLE_FPS = 1.0
SAFE_MARGIN_FRAC = 0.05  # industry-standard 5% title-safe margin
EDGE_CLIP_PX = 4  # a box within this of the frame edge is cut off
MIN_OCR_CONFIDENCE = 0.4
# Clipped text OCRs badly BECAUSE it's clipped — a low-confidence read at the
# frame edge is evidence, not noise, so the clip check uses a lower floor.
MIN_CLIP_CONFIDENCE = 0.1
OVERLAP_IOU = 0.15
MIN_TEXT_HEIGHT_FRAC = 0.015  # ignore tiny incidental text

Box = tuple[float, float, float, float]


def _iou(a: Box, b: Box) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    union = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return inter / union


def run(ctx: Context) -> None:
    r = ctx.report
    gt = ctx.ground_truth
    samples = ctx.artifacts.ocr_boxes
    assert samples is not None, "engine must run the layout OCR service first"

    h_frame, w_frame = None, None
    clipped_reported: set[str] = set()
    overflow_reported: set[str] = set()
    overlap_reported: set[tuple[str, str]] = set()
    watermark_seen = False
    frames_scanned = 0

    for sample in samples:
        frames_scanned += 1
        t_sec = sample["t_sec"]
        h_frame, w_frame = sample["shape"]
        img = sample["frame"]  # None unless an evidence dir is configured
        results = sample["results"]

        boxes: list[tuple[Box, str]] = []
        low_conf_boxes: list[tuple[Box, str]] = []
        for bbox, text, conf in results:
            if conf < MIN_CLIP_CONFIDENCE or not str(text).strip():
                continue
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            box = (min(xs), min(ys), max(xs), max(ys))
            if (box[3] - box[1]) < h_frame * MIN_TEXT_HEIGHT_FRAC:
                continue
            if conf >= MIN_OCR_CONFIDENCE:
                boxes.append((box, str(text).strip()))
            else:
                low_conf_boxes.append((box, str(text).strip()))

        scene = gt.scene_at(t_sec) if gt else None
        scene_id = scene.id if scene else None

        for box, text in boxes + low_conf_boxes:
            is_low_conf = (box, text) in low_conf_boxes
            x0, y0, x1, y1 = box
            key = text.lower()[:30]

            # Watermark: small text hugging a corner in the top or bottom band.
            in_corner = (y1 < h_frame * 0.12 or y0 > h_frame * 0.88) and (
                x0 < w_frame * 0.25 or x1 > w_frame * 0.75
            )
            if in_corner and (y1 - y0) < h_frame * 0.04:
                watermark_seen = True
                continue  # corner bugs are exempt from margin rules

            if key not in clipped_reported and (
                x0 <= EDGE_CLIP_PX
                or y0 <= EDGE_CLIP_PX
                or x1 >= w_frame - EDGE_CLIP_PX
                or y1 >= h_frame - EDGE_CLIP_PX
            ):
                clipped_reported.add(key)
                r.add(
                    Finding(
                        "layout",
                        "TEXT_CLIPPED",
                        "error",
                        f'Text "{text[:60]}" touches the frame edge at {t_sec:.1f}s — '
                        "it is being cut off",
                        scene_id=scene_id,
                        key=ids.text_key(text),
                        span_sec=(t_sec, t_sec),
                        evidence=_save_evidence(ctx, img, box, f"clipped-{len(clipped_reported)}"),
                        rubric_dimension="layout",
                    )
                )
            elif (
                not is_low_conf
                and key not in overflow_reported
                and key not in clipped_reported
                and (
                    x0 < w_frame * SAFE_MARGIN_FRAC
                    or y0 < h_frame * SAFE_MARGIN_FRAC
                    or x1 > w_frame * (1 - SAFE_MARGIN_FRAC)
                    or y1 > h_frame * (1 - SAFE_MARGIN_FRAC)
                )
            ):
                overflow_reported.add(key)
                r.add(
                    Finding(
                        "layout",
                        "TEXT_OVERFLOW",
                        "warning",
                        f'Text "{text[:60]}" extends into the 5% safe margin at '
                        f"{t_sec:.1f}s — risks being cropped by platform UI or TV overscan",
                        scene_id=scene_id,
                        key=ids.text_key(text),
                        span_sec=(t_sec, t_sec),
                        rubric_dimension="layout",
                    )
                )

        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                (box_a, text_a), (box_b, text_b) = boxes[i], boxes[j]
                pair = (
                    min(text_a.lower()[:30], text_b.lower()[:30]),
                    max(text_a.lower()[:30], text_b.lower()[:30]),
                )
                if pair in overlap_reported:
                    continue
                if _iou(box_a, box_b) > OVERLAP_IOU:
                    overlap_reported.add(pair)
                    r.add(
                        Finding(
                            "layout",
                            "TEXT_OVERLAP",
                            "error",
                            f'Text blocks "{text_a[:40]}" and "{text_b[:40]}" overlap at '
                            f"{t_sec:.1f}s",
                            scene_id=scene_id,
                            key=ids.slug_key(f"{normalize_word(text_a)}-{normalize_word(text_b)}"),
                            span_sec=(t_sec, t_sec),
                            rubric_dimension="layout",
                        )
                    )

    r.set_metric("layout.framesScanned", frames_scanned)
    r.set_metric("layout.clippedTextCount", len(clipped_reported))
    r.set_metric("layout.overflowTextCount", len(overflow_reported))

    if gt and gt.options.get("watermark") and not watermark_seen:
        r.add(
            Finding(
                "layout",
                "WATERMARK_MISSING",
                "warning",
                f'Run options request watermark "{gt.options["watermark"]}" but no corner '
                "watermark text was detected in any sampled frame",
                rubric_dimension="layout",
            )
        )


def _save_evidence(ctx: Any, img: Any, box: Box, name: str) -> dict[str, str]:
    if not ctx.evidence_dir:
        return {}
    import cv2

    x0, y0, x1, y1 = (int(v) for v in box)
    annotated = img.copy()
    cv2.rectangle(annotated, (x0, y0), (x1, y1), (0, 0, 255), 3)
    path = f"{ctx.evidence_dir}/{name}.png"
    cv2.imwrite(path, annotated)
    return {"frame": f"evidence/{name}.png"}
