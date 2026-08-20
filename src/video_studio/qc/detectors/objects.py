"""Planned-subject presence via YOLOv8n. [yolo]

v1 port, including the KEYWORD_CLASSES table verbatim (and its documented
"glass" exclusion — usually a material adjective, not a drinking glass).
Now PURE over Artifacts.detections — YOLO rides the shared decode
(services.model_services.ObjectService, 1 fps).
"""

from __future__ import annotations

import re

from video_studio.qc.context import Context
from video_studio.qc.report import ids
from video_studio.qc.report.model import Finding

SAMPLE_FPS = 1.0
CONFIDENCE = 0.35
FOOTAGE_FORMATS = {"ai-video", "composite"}

# prompt keyword (regex, word-boundary) -> COCO class name
KEYWORD_CLASSES: list[tuple[str, str]] = [
    (
        r"\b(woman|man|person|people|creator|girl|boy|guy|lady|chef|host|speaker|hand|face|selfie)\b",
        "person",
    ),
    (r"\b(car|vehicle)\b", "car"),
    (r"\b(dog|puppy)\b", "dog"),
    (r"\b(cat|kitten)\b", "cat"),
    (r"\b(phone|smartphone|iphone)\b", "cell phone"),
    (r"\b(laptop|macbook)\b", "laptop"),
    (r"\b(tv|television|screen|monitor)\b", "tv"),
    (r"\b(bottle)\b", "bottle"),
    # "glass" excluded: usually a material adjective ("glass dropper"), not a drinking glass
    (r"\b(cup|mug)\b", "cup"),
    (r"\b(bowl)\b", "bowl"),
    (r"\b(pizza)\b", "pizza"),
    (r"\b(cake)\b", "cake"),
    (r"\b(sandwich|burger)\b", "sandwich"),
    (r"\b(chair)\b", "chair"),
    (r"\b(couch|sofa)\b", "couch"),
    (r"\b(bed)\b", "bed"),
    (r"\b(book)\b", "book"),
    (r"\b(clock|watch)\b", "clock"),
    (r"\b(keyboard)\b", "keyboard"),
    (r"\b(scissors)\b", "scissors"),
]


def expected_classes(visual_prompt: str) -> set[str]:
    text = visual_prompt.lower()
    return {cls for pattern, cls in KEYWORD_CLASSES if re.search(pattern, text)}


def run(ctx: Context) -> None:
    gt = ctx.ground_truth
    r = ctx.report
    assert gt is not None

    if gt.format not in FOOTAGE_FORMATS:
        r.add(
            Finding(
                "objects",
                "NOT_APPLICABLE",
                "info",
                f"Object detection skipped: format '{gt.format}' is motion graphics, not footage",
            )
        )
        return

    scene_expectations = {s.id: expected_classes(s.visual) for s in gt.scenes}
    if not any(scene_expectations.values()):
        r.add(
            Finding(
                "objects",
                "NO_MAPPABLE_SUBJECTS",
                "info",
                "No scene visual prompts mapped to detectable object classes",
            )
        )
        return

    frames = ctx.artifacts.detections
    assert frames is not None, "engine must run the object service first"

    seen_by_scene: dict[str, set[str]] = {s.id: set() for s in gt.scenes}
    person_counts: dict[str, list[int]] = {s.id: [] for s in gt.scenes}

    for t_sec, detected, persons in frames:
        scene = gt.scene_at(t_sec)
        if scene is None:
            continue
        seen_by_scene[scene.id] |= detected
        person_counts[scene.id].append(persons)

    missing_total = 0
    for scene in gt.scenes:
        expected = scene_expectations[scene.id]
        if not expected:
            continue
        missing = expected - seen_by_scene[scene.id]
        missing_total += len(missing)
        for cls in sorted(missing):
            r.add(
                Finding(
                    "objects",
                    "SUBJECT_MISSING",
                    "warning",
                    f"Scene '{scene.id}' plans a {cls} on screen "
                    f'("{scene.visual[:80]}...") but none was detected in any sampled frame',
                    scene_id=scene.id,
                    key=ids.class_key(cls),
                    span_sec=(scene.start_sec, scene.end_sec),
                    rubric_dimension="visual-quality",
                )
            )
        # Person-count anomaly: prompt says one subject, footage shows a crowd.
        counts = person_counts[scene.id]
        if "person" in expected and counts and max(counts) >= 3:
            r.add(
                Finding(
                    "objects",
                    "UNEXPECTED_CROWD",
                    "info",
                    f"Scene '{scene.id}' shows up to {max(counts)} people; the visual prompt "
                    "suggests a single subject — check for AI-generated extras/duplicates",
                    scene_id=scene.id,
                    span_sec=(scene.start_sec, scene.end_sec),
                )
            )

    checked = sum(1 for v in scene_expectations.values() if v)
    r.set_metric("objects.scenesChecked", checked)
    r.set_metric("objects.missingSubjectCount", missing_total)
