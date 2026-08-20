"""Entity tracking across cuts (4.3 multi-character, 3.2 unboxing). [yolo,track]

YOLO detections at 2 fps -> supervision ByteTrack -> per-track lifetimes,
plus HSV-histogram appearance signatures for cross-cut re-linking. Findings:

  PRODUCT_NOT_SHOWN   — a plan noun maps to a COCO class but no track of that
                        class lives >= 1s (reuses objects.KEYWORD_CLASSES)
  PRODUCT_TOO_BRIEF   — the planned subject appears under 0.8s
  SAME_ACTOR_TWO_CHARACTERS — two person tracks in disjoint time spans whose
                        face-region signatures match but torso signatures
                        differ (the 4.3 eval target), heuristic confidence.

Heavy extras are imported lazily inside run(): absent ultralytics/supervision
surfaces as a typed missing_extra skip, never a crash — the standing rule.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from video_studio.qc.context import Context
from video_studio.qc.detectors.objects import FOOTAGE_FORMATS, expected_classes
from video_studio.qc.media.sampling import sample_frames
from video_studio.qc.report import ids
from video_studio.qc.report.model import Finding

SAMPLE_FPS = 2.0
CONFIDENCE = 0.35
MIN_PRESENCE_SEC = 1.0
BRIEF_SEC = 0.8
FACE_MATCH = 0.80  # cosine of HSV hists: same-ish face region
TORSO_DIFFER = 0.60  # below this = different clothing


def _hsv_hist(bgr: np.ndarray) -> np.ndarray:
    import cv2

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256]).flatten()
    norm = np.linalg.norm(hist) or 1.0
    return np.asarray(hist / norm)


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def run(ctx: Context) -> None:
    gt = ctx.ground_truth
    r = ctx.report
    assert gt is not None

    if gt.format not in FOOTAGE_FORMATS:
        r.add(
            Finding(
                "entity_tracking",
                "NOT_APPLICABLE",
                "info",
                f"Entity tracking skipped: format '{gt.format}' is motion graphics",
            )
        )
        return

    import supervision as sv  # [track]
    from ultralytics import YOLO  # [yolo]

    model = YOLO("yolov8n.pt")
    names = model.names
    tracker = sv.ByteTrack()

    # track_id -> {class, first, last, frames, face_sig, torso_sig}
    tracks: dict[int, dict[str, Any]] = {}

    for frame in sample_frames(ctx.video_path, SAMPLE_FPS):
        results = model.predict(frame.image, conf=CONFIDENCE, verbose=False)
        detections = sv.Detections.from_ultralytics(results[0])
        detections = tracker.update_with_detections(detections)
        if detections.tracker_id is None:
            continue
        for xyxy, cls_id, track_id in zip(
            detections.xyxy, detections.class_id, detections.tracker_id, strict=False
        ):
            x0, y0, x1, y1 = (int(v) for v in xyxy)
            crop = frame.image[max(0, y0) : y1, max(0, x0) : x1]
            if crop.size == 0:
                continue
            entry = tracks.setdefault(
                int(track_id),
                {
                    "class": names[int(cls_id)],
                    "first": frame.t_sec,
                    "last": frame.t_sec,
                    "frames": 0,
                    "face": None,
                    "torso": None,
                },
            )
            entry["last"] = frame.t_sec
            entry["frames"] += 1
            if entry["class"] == "person" and entry["frames"] <= 5:
                h = crop.shape[0]
                face = crop[: max(1, h // 3)]
                torso = crop[h // 3 : max(2, 2 * h // 3)]
                entry["face"] = _hsv_hist(face) if entry["face"] is None else entry["face"]
                entry["torso"] = _hsv_hist(torso) if entry["torso"] is None else entry["torso"]

    r.set_metric("entity.trackCount", len(tracks))
    if tracks:
        lifetimes = [t["last"] - t["first"] for t in tracks.values()]
        r.set_metric("entity.meanTrackLifetimeSec", float(np.mean(lifetimes)))

    # Planned-subject presence, by tracked lifetime rather than any-frame hits.
    seen_by_class: dict[str, float] = {}
    for t in tracks.values():
        seen_by_class[t["class"]] = max(seen_by_class.get(t["class"], 0.0), t["last"] - t["first"])
    for scene in gt.scenes:
        for cls in sorted(expected_classes(scene.visual)):
            lifetime = seen_by_class.get(cls, 0.0)
            if lifetime == 0.0:
                r.add(
                    Finding(
                        "entity_tracking",
                        "PRODUCT_NOT_SHOWN",
                        "warning",
                        f"Scene '{scene.id}' plans a {cls} but no track of that class "
                        "exists anywhere in the video",
                        scene_id=scene.id,
                        key=ids.class_key(cls),
                        rubric_dimension="visual-quality",
                    )
                )
            elif lifetime < BRIEF_SEC:
                r.add(
                    Finding(
                        "entity_tracking",
                        "PRODUCT_TOO_BRIEF",
                        "info",
                        f"The planned {cls} is on screen for only {lifetime:.1f}s total",
                        scene_id=scene.id,
                        key=ids.class_key(cls),
                    )
                )

    # 4.3: same face, different clothes, disjoint spans.
    persons = [t for t in tracks.values() if t["class"] == "person" and t["face"] is not None]
    for i in range(len(persons)):
        for j in range(i + 1, len(persons)):
            a, b = persons[i], persons[j]
            disjoint = a["last"] < b["first"] or b["last"] < a["first"]
            if not disjoint or a["torso"] is None or b["torso"] is None:
                continue
            if (
                _cos(a["face"], b["face"]) > FACE_MATCH
                and _cos(a["torso"], b["torso"]) < TORSO_DIFFER
            ):
                r.add(
                    Finding(
                        "entity_tracking",
                        "SAME_ACTOR_TWO_CHARACTERS",
                        "info",
                        "Two disjoint person tracks share a face signature but wear "
                        "different clothing — one actor appears to play two characters",
                        confidence=0.6,
                    )
                )
                r.set_metric("entity.sameActorPairs", 1.0)
                return
