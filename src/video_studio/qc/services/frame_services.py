"""Frame-consuming services over the ONE shared decode.

Each service declares its sample rate, owns exactly one artifact on
`ctx.artifacts`, and subscribes one callback to the FramePipeline. The
pipeline unions the schedules so a single sequential decode serves them all —
the decode-count regression test (`CvFrameSource.open_count == 1`) is the
guard that this stays true.

Extracted from engine.py's closure pile; behavior is byte-identical (the
corpus parity gate is the check).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from video_studio.qc.context import Context, FrameStats, PaneStats
from video_studio.qc.media.pipeline import CvFrameSource, FramePipeline

VISUAL_SAMPLE_FPS = 1.0
MOTION_SAMPLE_FPS = 10.0
ENERGY_SAMPLE_FPS = 25.0
PANES_SAMPLE_FPS = 2.0
MOUTH_SAMPLE_FPS = 10.0
FLOW_SIZE = (320, 180)


@dataclass(frozen=True)
class ServiceSpec:
    """What a service asks of the shared decode."""

    name: str
    fps: float


class VisualService:
    """Blur/banding/palette per ~1s frame — feeds the `visual` detector."""

    spec = ServiceSpec("visual", VISUAL_SAMPLE_FPS)

    def __init__(self, ctx: Context) -> None:
        import numpy as np

        from video_studio.qc.ground_truth import load_palette

        self._np = np
        gt = ctx.ground_truth
        fmt = gt.format if gt else None
        graphics = fmt in {"faceless-explainer", "manim-explainer"}
        self.palette = load_palette(gt.workdir) if (gt and graphics) else None
        self.stats = FrameStats(palette_checked=self.palette is not None)
        ctx.artifacts.frame_stats = self.stats

    def on_frame(self, view: Any) -> None:
        import cv2

        np = self._np
        stats = self.stats
        gray = view.gray
        blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        stats.blur_scores.append(blur)
        if stats.worst_blur is None or blur < stats.worst_blur[0]:
            stats.worst_blur = (blur, view.t_sec)

        small = view.resized((320, 180), gray=True)
        lap = np.abs(cv2.Laplacian(small.astype(np.float64), cv2.CV_64F))
        smooth = lap < 1.0
        gx = cv2.Sobel(small, cv2.CV_64F, 1, 0, ksize=5)
        gy = cv2.Sobel(small, cv2.CV_64F, 0, 1, ksize=5)
        grad = np.sqrt(gx**2 + gy**2)
        gradient_region = (grad > 1.0) & (grad < 40.0)
        stats.banding_scores.append(float((smooth & gradient_region).mean()))

        if self.palette is not None:
            tiny = view.resized((160, 90))
            lab = cv2.cvtColor(tiny, cv2.COLOR_BGR2Lab).reshape(-1, 3).astype(np.float64)
            dists = np.linalg.norm(lab[:, None, :] - self.palette[None, :, :], axis=2)
            stats.off_palette_fractions.append(float((dists.min(axis=1) > 25.0).mean()))


class MotionService:
    """Farneback optical-flow speed at 10fps — feeds the `motion` detector."""

    spec = ServiceSpec("motion", MOTION_SAMPLE_FPS)

    def __init__(self, ctx: Context) -> None:
        self.samples: list[tuple[float, float, float]] = []
        ctx.artifacts.motion_samples = self.samples
        self._prev: dict[str, Any] = {}

    def on_frame(self, view: Any) -> None:
        import cv2
        import numpy as np

        gray = view.resized(FLOW_SIZE, gray=True)
        prev = self._prev
        if "frame" in prev:
            flow = cv2.calcOpticalFlowFarneback(  # type: ignore[call-overload]
                prev["frame"], gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            speed = float(np.linalg.norm(flow, axis=2).mean())
            self.samples.append((prev["t"], view.t_sec, speed))
        prev["frame"] = gray
        prev["t"] = view.t_sec


class EnergyService:
    """Frame-diff energy at 25fps — feeds `av_sync`'s motion side."""

    spec = ServiceSpec("energy", ENERGY_SAMPLE_FPS)

    def __init__(self, ctx: Context) -> None:
        self.energy: list[tuple[float, float]] = []
        ctx.artifacts.energy_samples = self.energy
        self._prev: dict[str, Any] = {}

    def on_frame(self, view: Any) -> None:
        import cv2

        gray = view.resized(FLOW_SIZE, gray=True)
        prev = self._prev
        if "frame" in prev:
            diff = cv2.absdiff(prev["frame"], gray)
            self.energy.append((view.t_sec, float(diff.mean())))
        prev["frame"] = gray


class PaneService:
    """Column edge profiles + block motion + chroma coverage — `composition`."""

    spec = ServiceSpec("panes", PANES_SAMPLE_FPS)
    BLOCKS_X = 16

    def __init__(self, ctx: Context) -> None:
        self.stats = PaneStats()
        ctx.artifacts.pane_stats = self.stats
        self._prev: dict[str, Any] = {}

    def on_frame(self, view: Any) -> None:
        import cv2
        import numpy as np

        stats = self.stats
        prev = self._prev
        gray = view.resized((480, 270), gray=True).astype(np.float64)
        sobel_x = np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3))
        stats.column_profiles.append(sobel_x.mean(axis=0))
        if "frame" in prev:
            diff = np.abs(gray - prev["frame"])
            cols = np.array_split(diff, self.BLOCKS_X, axis=1)
            stats.block_energies.append(np.array([c.mean() for c in cols]))
        prev["frame"] = gray
        # Chroma-key hue coverage (green screen residue / spill).
        hsv = cv2.cvtColor(view.resized((160, 90)), cv2.COLOR_BGR2HSV)
        hue, sat = hsv[..., 0].astype(int), hsv[..., 1].astype(int)
        green = ((hue > 35) & (hue < 85) & (sat > 100)).mean()
        stats.key_hue_fractions.append(float(green))


class MouthService:
    """Face-tracked mouth-openness series at 10fps — feeds `lip_sync`.

    Backend resolution order:
      1. mediapipe FaceMesh ([face] extra) — real inner-lip aperture
         (landmarks 13/14) normalized by inter-ocular distance (33/263).
         lip_sync treats this as non-degraded (confidence 0.9).
      2. classic Haar cascade (OpenCV < 5 only — 5.0 removed
         CascadeClassifier) — mouth-ROI frame-diff proxy, degraded mode.
      3. none — empty series + a service skip; NEVER crashes the analysis.
    """

    spec = ServiceSpec("mouth", MOUTH_SAMPLE_FPS)

    def __init__(self, ctx: Context) -> None:
        self.mouth: list[tuple[float, float]] = []
        ctx.artifacts.mouth_series = self.mouth
        self._prev: dict[str, Any] = {}
        self._mesh = _mediapipe_face_mesh()
        self._haar = _haar_face_backend() if self._mesh is None else None
        self.mode = "mediapipe" if self._mesh else "haar" if self._haar else "none"
        ctx.artifacts.mouth_mode = self.mode
        if self.mode == "none":
            from video_studio.qc.report.model import Skip

            ctx.report.skipped.append(
                Skip(
                    "face",
                    "missing_extra",
                    kind="service",
                    extra="face",
                    detail="no face backend (OpenCV 5 removed the Haar "
                    "CascadeClassifier — install the [face] extra for mediapipe)",
                )
            )

    @property
    def available(self) -> bool:
        return self.mode != "none"

    def on_frame(self, view: Any) -> None:
        if self._mesh is not None:
            self._on_frame_mediapipe(view)
        else:
            self._on_frame_haar(view)

    def _on_frame_mediapipe(self, view: Any) -> None:
        import mediapipe as mp
        import numpy as np

        small = view.resized((480, max(2, int(480 * view.bgr.shape[0] / view.bgr.shape[1]))))
        rgb = np.ascontiguousarray(small[:, :, ::-1])
        assert self._mesh is not None
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._mesh.detect(image)
        faces = getattr(result, "face_landmarks", None)
        if not faces:
            return
        lm = faces[0]
        # Inner-lip aperture over inter-ocular distance: scale-invariant.
        aperture = abs(lm[13].y - lm[14].y)
        ocular = ((lm[33].x - lm[263].x) ** 2 + (lm[33].y - lm[263].y) ** 2) ** 0.5
        if ocular < 1e-6:
            return
        self.mouth.append((view.t_sec, float(aperture / ocular)))

    def _on_frame_haar(self, view: Any) -> None:
        import cv2

        assert self._haar is not None  # subscribed only when available
        gray = view.resized(
            (640, max(2, int(640 * view.bgr.shape[0] / view.bgr.shape[1]))), gray=True
        )
        faces = self._haar.detectMultiScale(gray, 1.2, 4, minSize=(60, 60))
        if len(faces) == 0:
            self._prev.pop("mouth", None)
            return
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        roi = gray[y + 2 * h // 3 : y + h, x : x + w]
        if roi.size == 0:
            return
        roi = cv2.resize(roi, (64, 32), interpolation=cv2.INTER_AREA)
        if "mouth" in self._prev:
            self.mouth.append((view.t_sec, float(cv2.absdiff(self._prev["mouth"], roi).mean())))
        self._prev["mouth"] = roi


_FACE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)


def _mediapipe_face_mesh() -> Any | None:
    """FaceLandmarker via mediapipe's Tasks API, or None.

    Recent mediapipe wheels (incl. all py3.11/arm64 builds installed here)
    ship ONLY the Tasks API — the legacy `mp.solutions` FaceMesh is gone.
    The landmark model (~3.7 MB) is not bundled; it downloads once into
    ~/.cache/showwatcher. Defensive on every layer — a broken face backend
    must degrade, not crash."""
    try:
        from pathlib import Path

        from mediapipe.tasks.python import BaseOptions, vision

        model = Path.home() / ".cache" / "showwatcher" / "face_landmarker.task"
        if not model.exists():
            import urllib.request

            model.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(_FACE_MODEL_URL, model)
        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model)),
            num_faces=1,
        )
        return vision.FaceLandmarker.create_from_options(options)
    except Exception:
        return None


class SceneFrameService:
    """Small color frames per scene (≤ MAX_PER_SCENE, spread across the scene)
    for CLIP prompt-fit scoring — feeds `prompt_visual`.

    Frames are stored at 256px width: scenes x 3 x 256x144x3 bytes is a few MB
    for a normal short-form video, not a decode-buffer explosion.
    """

    spec = ServiceSpec("scene_frames", 1.0)
    MAX_PER_SCENE = 3

    def __init__(self, ctx: Context) -> None:
        self.frames: dict[str, list[Any]] = {}
        ctx.artifacts.scene_frames = self.frames
        gt = ctx.ground_truth
        self._bounds = (
            [(s.id, s.start_sec, s.end_sec) for s in gt.scenes] if gt is not None else []
        )

    def on_frame(self, view: Any) -> None:
        for sid, start, end in self._bounds:
            if start <= view.t_sec < end:
                bucket = self.frames.setdefault(sid, [])
                # One frame per third of the scene, not the first N seconds.
                slot = (end - start) / self.MAX_PER_SCENE
                if len(bucket) < self.MAX_PER_SCENE and view.t_sec >= start + len(bucket) * slot:
                    h = view.bgr.shape[0]
                    w = view.bgr.shape[1]
                    small = view.resized((256, max(2, int(256 * h / w))))
                    bucket.append(small.copy())
                return


def _haar_face_backend() -> Any | None:
    """Best-effort classic face detector. Returns None when unavailable."""
    import cv2

    if not hasattr(cv2, "CascadeClassifier"):
        return None
    try:
        return cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"  # type: ignore[attr-defined]
        )
    except Exception:
        return None


def run_frame_services(
    ctx: Context,
    *,
    want_visual: bool,
    want_motion: bool,
    want_energy: bool = False,
    want_panes: bool = False,
    want_mouth: bool = False,
    want_scene_frames: bool = False,
    want_caption_ocr: bool = False,
    want_layout_ocr: bool = False,
    want_objects: bool = False,
    source: Any | None = None,
) -> None:
    """One decode serving every frame-consuming service the run selected.

    The model-backed wants (caption_ocr/layout_ocr/objects) must only be set
    when the engine has verified their extra is importable — constructing
    those services imports easyocr/ultralytics."""
    if not (
        want_visual
        or want_motion
        or want_energy
        or want_panes
        or want_mouth
        or want_scene_frames
        or want_caption_ocr
        or want_layout_ocr
        or want_objects
    ):
        return

    pipeline = FramePipeline(source or CvFrameSource(ctx.video_path))

    if want_visual:
        visual = VisualService(ctx)
        pipeline.subscribe(visual.spec.name, visual.spec.fps, visual.on_frame)
    if want_motion:
        motion = MotionService(ctx)
        pipeline.subscribe(motion.spec.name, motion.spec.fps, motion.on_frame)
    if want_energy:
        energy = EnergyService(ctx)
        pipeline.subscribe(energy.spec.name, energy.spec.fps, energy.on_frame)
    if want_panes:
        panes = PaneService(ctx)
        pipeline.subscribe(panes.spec.name, panes.spec.fps, panes.on_frame)
    if want_mouth:
        mouth = MouthService(ctx)
        if mouth.available:
            pipeline.subscribe(mouth.spec.name, mouth.spec.fps, mouth.on_frame)
    if want_scene_frames:
        scenes = SceneFrameService(ctx)
        pipeline.subscribe(scenes.spec.name, scenes.spec.fps, scenes.on_frame)
    if want_caption_ocr or want_layout_ocr or want_objects:
        from video_studio.qc.services import model_services as ms

        if want_caption_ocr:
            cap = ms.CaptionOcrService(ctx)
            pipeline.subscribe(cap.spec.name, cap.spec.fps, cap.on_frame)
        if want_layout_ocr:
            lay = ms.LayoutOcrService(ctx)
            pipeline.subscribe(lay.spec.name, lay.spec.fps, lay.on_frame)
        if want_objects:
            obj = ms.ObjectService(ctx)
            pipeline.subscribe(obj.spec.name, obj.spec.fps, obj.on_frame)

    pipeline.run()
