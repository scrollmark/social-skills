"""The analysis engine: media phase (decode once) then detector phase (pure).

v1's architecture had every detector open the video itself — ~10 full decodes
per analysis, and the swallowed-ImportError registry. Here:

  Phase A (media): one chained ffmpeg filter pass, one shared frame-pipeline
  decode for the always-on frame services (see showwatcher.services), one
  PySceneDetect pass with BOTH detectors in a single SceneManager (v1 ran two
  full detect() passes), and one lazily-decoded AudioTrack.

  Phase B (detectors): pure functions over the typed Context (see
  showwatcher.context) — the ported v1 behavior, emitting findings/metrics
  onto the report.

Failure semantics mirror v1's CLI exactly (they are part of the parity
contract): a missing optional dep becomes a skip entry with the extra hint, a
crash becomes a skip entry with a truncated traceback, and findings never
affect the exit code.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Re-exported for compatibility: these lived here before the context/services
# split, and tests + external callers import them from the engine.
from video_studio.qc.context import Artifacts, Context, FrameStats, PaneStats
from video_studio.qc.media.audio import AudioTrack
from video_studio.qc.media.ffmpeg_filters import run_filter_pass
from video_studio.qc.media.probe import probe
from video_studio.qc.report.model import Report, SceneTiming, Skip
from video_studio.qc.services import run_frame_services
from video_studio.qc.ground_truth import load_ground_truth

__all__ = [
    "KNOWN_DETECTORS",
    "AnalyzeOptions",
    "Artifacts",
    "Context",
    "FrameStats",
    "PaneStats",
    "analyze",
    "detect_cuts",
    "run_frame_services",
]


# ---------------------------------------------------------------------------
# Media phase services
# ---------------------------------------------------------------------------


def detect_cuts(video_path: str) -> list[float]:
    """PySceneDetect ContentDetector + AdaptiveDetector in ONE SceneManager pass.

    v1 ran detect() twice (two full decodes) and unioned the results. A single
    SceneManager with both detectors cuts wherever EITHER fires — the same
    union — in one decode. The parity gate over the corpus is the check that
    this equivalence holds on real footage.
    """
    from scenedetect import AdaptiveDetector, ContentDetector, SceneManager, open_video

    video = open_video(video_path)
    manager = SceneManager()
    manager.add_detector(ContentDetector())
    manager.add_detector(AdaptiveDetector())
    manager.detect_scenes(video)
    scene_list = manager.get_scene_list()

    cuts: set[float] = set()
    for start, _end in scene_list:
        t = start.seconds
        if t > 0.01:  # the first scene's start is not a cut
            cuts.add(round(t, 3))
    merged: list[float] = []
    for t in sorted(cuts):
        if merged and t - merged[-1] < 0.1:
            continue
        merged.append(t)
    return merged


# ---------------------------------------------------------------------------
# Detector registry — explicit, no swallowed ImportError
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DetectorSpec:
    name: str
    needs_ground_truth: bool
    extra: str | None  # pyproject extra providing its heavy deps


KNOWN_DETECTORS: list[DetectorSpec] = [
    DetectorSpec("container", False, None),
    DetectorSpec("black_freeze", False, None),
    DetectorSpec("scene_sync", True, None),
    DetectorSpec("audio_sync", True, None),
    DetectorSpec("caption_sync", True, "qc-ocr"),
    DetectorSpec("layout", False, "qc-ocr"),
    DetectorSpec("transcript", True, "captions"),
    DetectorSpec("audio_quality", False, None),
    DetectorSpec("visual", False, None),
    DetectorSpec("motion", False, None),
    DetectorSpec("objects", True, "qc-yolo"),
    # New in showwatcher — not part of the v1 parity set.
    DetectorSpec("timeline", True, None),
    DetectorSpec("av_sync", False, None),
    DetectorSpec("composition", False, None),
    DetectorSpec("lip_sync", False, None),
    DetectorSpec("entity_tracking", True, "qc-yolo"),
    DetectorSpec("prompt_fit", False, None),
    DetectorSpec("prompt_visual", True, "qc-clip"),  # CLIP via fastembed
]


def _detector_run(name: str) -> Any:
    """Import a detector module loudly — an ImportError here is a real bug,
    unless it names a module an extra provides (handled by the caller)."""
    import importlib

    module = importlib.import_module(f"video_studio.qc.detectors.{name}")
    return module.run


@dataclass
class AnalyzeOptions:
    workdir: str | None = None
    detectors: set[str] | None = None  # None = all
    evidence_dir: str | None = None
    taxonomy: str | None = None  # SocialBench subcategory, e.g. "4.1"
    verbose: bool = False


def analyze(video_path: str | Path, opts: AnalyzeOptions | None = None) -> Report:
    opts = opts or AnalyzeOptions()
    video_path = str(video_path)

    video = probe(video_path)
    ground_truth = load_ground_truth(opts.workdir) if opts.workdir else None

    report = Report(
        video=video.to_json(),
        workdir=ground_truth.to_json() if ground_truth else None,
    )
    if ground_truth:
        report.scenes = [
            SceneTiming(
                id=s.id,
                index=s.index,
                planned_start_sec=s.start_sec,
                planned_end_sec=s.end_sec,
                narration=s.narration,
            )
            for s in ground_truth.scenes
        ]

    if opts.evidence_dir:
        Path(opts.evidence_dir).mkdir(parents=True, exist_ok=True)

    ctx = Context(
        video_path=video_path,
        video=video,
        report=report,
        audio=AudioTrack(video_path),
        artifacts=Artifacts(),
        ground_truth=ground_truth,
        evidence_dir=opts.evidence_dir,
        taxonomy=opts.taxonomy,
    )

    only = opts.detectors
    known_names = {spec.name for spec in KNOWN_DETECTORS}
    if only:
        for name in sorted(only - known_names):
            report.skipped.append(Skip(name=name, code="unknown"))

    will_run = [
        spec
        for spec in KNOWN_DETECTORS
        if (only is None or spec.name in only)
        and not (spec.needs_ground_truth and ground_truth is None)
    ]
    run_names = {spec.name for spec in will_run}

    # Model-backed extras: availability decided HERE (find_spec) so detectors
    # never import model packages. An absent extra becomes a missing_extra
    # skip before any media work happens.
    import importlib.util

    def _drop_missing_extra(names: tuple[str, ...], module: str, extra: str) -> bool:
        present = importlib.util.find_spec(module) is not None
        if not present:
            for name in names:
                if name in run_names:
                    run_names.discard(name)
                    report.skipped.append(
                        Skip(name=name, code="missing_extra", extra=extra, detail=module)
                    )
        return present

    have_ocr = _drop_missing_extra(("caption_sync", "layout"), "easyocr", "qc-ocr")
    have_yolo = _drop_missing_extra(("objects", "entity_tracking"), "ultralytics", "qc-yolo")

    # OCR/YOLO frame streams are wasted work when the detector would return
    # early anyway — mirror those cheap early-out conditions here.
    want_caption_ocr = (
        have_ocr
        and "caption_sync" in run_names
        and ground_truth is not None
        and bool(ground_truth.caption_words)
    )
    want_layout_ocr = have_ocr and "layout" in run_names
    want_objects_svc = False
    if have_yolo and "objects" in run_names and ground_truth is not None:
        from video_studio.qc.detectors.objects import FOOTAGE_FORMATS, expected_classes

        want_objects_svc = ground_truth.format in FOOTAGE_FORMATS and any(
            expected_classes(s.visual) for s in ground_truth.scenes
        )

    # --- Phase A: media, computed once, only what the selected detectors need
    if {"black_freeze", "audio_quality"} & run_names:
        ctx.artifacts.filter_pass = run_filter_pass(video_path, has_audio=video.audio is not None)
    if "scene_sync" in run_names:
        # scenedetect is the one heavyweight import the media phase needs, and
        # it was reached unconditionally: without it installed, a missing cut
        # detector took down the WHOLE run, including the detectors that need
        # no models at all. Gate it like any other extra — one detector skips,
        # the rest still report.
        try:
            ctx.artifacts.cuts = detect_cuts(video_path)
        except ImportError as e:
            run_names.discard("scene_sync")
            report.skipped.append(
                Skip(name="scene_sync", code="missing_extra", extra="qc", detail=e.name)
            )
    run_frame_services(
        ctx,
        want_visual="visual" in run_names,
        want_motion="motion" in run_names,
        want_energy="av_sync" in run_names,
        want_panes="composition" in run_names,
        want_mouth="lip_sync" in run_names,
        want_scene_frames="prompt_visual" in run_names,
        want_caption_ocr=want_caption_ocr,
        want_layout_ocr=want_layout_ocr,
        want_objects=want_objects_svc,
    )

    # --- Phase B: detectors, in v1 order (audio_sync depends on scene_sync's
    # scene-spine writes; the list order IS the dependency order).
    for spec in KNOWN_DETECTORS:
        if spec.name not in run_names:
            if (
                spec.needs_ground_truth
                and ground_truth is None
                and (only is None or spec.name in only)
            ):
                report.skipped.append(Skip(name=spec.name, code="requires_workdir"))
            continue
        try:
            run = _detector_run(spec.name)
            run(ctx)
            report.detectors_run.append(spec.name)
        except ImportError as e:
            # Only an ImportError naming a module OUTSIDE this package is a
            # missing extra. Treating every ImportError that way is how the
            # port to video_studio silently reported a clean bill of health on
            # every video: the detector loader still named the old package, so
            # each detector raised ImportError('showwatcher') and was filed as
            # "you did not install the model" rather than "this is broken".
            missing = (e.name or "").split(".")[0]
            if missing == "video_studio":
                report.skipped.append(
                    Skip(name=spec.name, code="crashed",
                         detail=f"detector failed to import: {e}")
                )
            else:
                report.skipped.append(
                    Skip(name=spec.name, code="missing_extra", extra=spec.extra, detail=e.name)
                )
        except Exception:
            report.skipped.append(
                Skip(name=spec.name, code="crashed", detail=traceback.format_exc(limit=3))
            )

    return report
