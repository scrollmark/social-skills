"""What the video was SUPPOSED to be, read from this repo's own documents.

The detectors and the decode layer ported across from showwatcher without
modification. This module is the seam that did not: showwatcher read a
showrunner work_dir — `plan.json` beside `checkpoint_compose.json`,
`checkpoint_render.json` and a manifest of run options — and none of that
exists here.

What does exist is better suited to the job. `build_props` already writes
`plan.json` with the comment "Ground truth for the quality check, which wants a
plan.json describing what SHOULD be on screen when", using the MEASURED scene
durations the render actually used rather than the storyboard's estimates. And
`tts_kokoro`/`gen_captions` write `<scene>.timings.json` in a shape that is
already word-level: `{"text", "startMs", "endMs"}`, scene-relative — which is
exactly a CaptionWord once the scene's start offset is added.

So the ground truth here is:

    <project>/plan.json                    durations, narration, visual intent
    <project>/storyboard.json              size, fps, style  (optional)
    <project>/audio/<scene>.timings.json   caption words     (optional)
    <project>/audio/<scene>.wav            per-scene narration

`duration_source` is always "plan" rather than "checkpoint": there is no
separate per-stage checkpoint to disagree with, because build_props measured
the audio and wrote the result straight into the plan.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class GroundTruthError(RuntimeError):
    pass


@dataclass
class CaptionWord:
    text: str
    start_ms: float
    end_ms: float
    scene_id: str


@dataclass
class PlannedScene:
    id: str
    index: int
    start_sec: float
    end_sec: float
    narration: str
    visual: str
    transition: str
    duration_source: str  # "plan" here; showwatcher also had "checkpoint"

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec


@dataclass
class GroundTruth:
    workdir: Path
    format: str
    aspect_ratio: str
    style: str | None
    topic: str | None
    options: dict[str, Any]
    plan_title: str
    planned_total_duration_sec: float
    scenes: list[PlannedScene]
    caption_words: list[CaptionWord] = field(default_factory=list)
    render_width: int | None = None
    render_height: int | None = None
    render_output_path: str | None = None

    @property
    def timeline_duration_sec(self) -> float:
        return self.scenes[-1].end_sec if self.scenes else 0.0

    def scene_wav(self, scene_id: str) -> Path | None:
        """Narration for one scene. `audio/` is where tts_kokoro writes."""
        for rel in (f"audio/{scene_id}.wav", f"public/audio/{scene_id}.wav"):
            p = self.workdir / rel
            if p.is_file():
                return p
        return None

    def scene_at(self, t_sec: float) -> PlannedScene | None:
        for s in self.scenes:
            if s.start_sec <= t_sec < s.end_sec:
                return s
        return self.scenes[-1] if self.scenes and t_sec >= self.scenes[-1].end_sec else None

    def to_json(self) -> dict[str, Any]:
        return {
            "path": str(self.workdir),
            "format": self.format,
            "aspectRatio": self.aspect_ratio,
            "style": self.style,
            "topic": self.topic,
            "planTitle": self.plan_title,
            "plannedDurationSec": round(self.planned_total_duration_sec, 3),
            "realAudioDurationSec": None,
            "options": {k: self.options.get(k) for k in ("captions", "music", "voice")
                        if k in self.options},
        }


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        raise GroundTruthError(f"invalid JSON in {path}: {e}") from e


def _aspect(width: int, height: int) -> str:
    """'9:16' style label, reduced. Falls back to WxH for odd sizes."""
    from math import gcd
    if not width or not height:
        return "unknown"
    g = gcd(width, height)
    return f"{width // g}:{height // g}"


#: Layer source prefixes that put real or generated footage on screen. A
#: `prompt:` clip counts: a generated shot of a person still contains a person,
#: which is what the object detectors are looking for.
_FOOTAGE_PREFIXES = ("file:", "find:", "url:", "prompt:")

#: What this repo calls its two shapes. showwatcher's vocabulary was
#: showrunner's format plugins ("ai-video", "faceless-explainer"); reusing those
#: names here would be a lie that happens to work, so the detector-side sets
#: were widened to accept these instead.
FOOTAGE_FORMAT = "video-studio-footage"
GRAPHICS_FORMAT = "video-studio-graphics"


def _infer_format(storyboard: dict) -> str:
    """Footage-bearing, or motion graphics?

    Four separate behaviours hang off this — whether object and entity
    detection run at all, how tolerant the cut check is, which blur threshold
    applies, and whether frames are measured against the style palette. A
    project here can be either kind, unlike a showrunner format which was fixed
    when the video was created, so it has to be read off the storyboard.

    The rule: any layer that names a footage source makes the whole video
    footage. Cards, effects and drawn marks alone make it graphics. A video
    that mixes them is treated as footage, because a wrong "no footage here"
    silently disables the object checks, while a wrong "footage" only costs a
    detection pass that finds nothing.
    """
    for scene in storyboard.get("scenes") or []:
        for layer in scene.get("layers") or []:
            source = str(layer.get("source", ""))
            if source.startswith(_FOOTAGE_PREFIXES):
                return FOOTAGE_FORMAT
    return GRAPHICS_FORMAT


def load_ground_truth(project: str | Path) -> GroundTruth:
    """Build a GroundTruth from a video_studio project directory."""
    root = Path(project)
    if not root.is_dir():
        raise GroundTruthError(f"not a project directory: {root}")

    plan = _load_json(root / "plan.json")
    if plan is None:
        raise GroundTruthError(
            f"no plan.json in {root} — build_props writes it beside the project. "
            f"Without it there is nothing to check the render against."
        )

    storyboard = _load_json(root / "storyboard.json") or {}
    width = int(storyboard.get("width", 0)) or None
    height = int(storyboard.get("height", 0)) or None

    # Scene boundaries accumulate, matching how build_props snapped them: the
    # running total is the authority, not each duration on its own.
    scenes: list[PlannedScene] = []
    cursor = 0.0
    for i, raw in enumerate(plan.get("scenes") or []):
        duration = float(raw.get("duration", 0.0))
        start, end = cursor, round(cursor + duration, 6)
        cursor = end
        scenes.append(PlannedScene(
            id=str(raw.get("id", f"scene{i}")),
            index=i,
            start_sec=start,
            end_sec=end,
            narration=str(raw.get("narration", "") or ""),
            visual=str(raw.get("visual", "") or ""),
            transition=str(raw.get("transition", "") or ""),
            duration_source="plan",
        ))

    # Caption words are per-scene and scene-relative on disk; the detectors
    # want composition-absolute, so each scene's start is folded in here.
    caption_words: list[CaptionWord] = []
    for scene in scenes:
        timings = _load_json(root / "audio" / f"{scene.id}.timings.json")
        if not isinstance(timings, list):
            continue
        offset_ms = scene.start_sec * 1000.0
        for word in timings:
            text = str(word.get("text", "")).strip()
            if not text:
                continue
            caption_words.append(CaptionWord(
                text=text,
                start_ms=float(word.get("startMs", 0)) + offset_ms,
                end_ms=float(word.get("endMs", 0)) + offset_ms,
                scene_id=scene.id,
            ))

    options: dict[str, Any] = {}
    if storyboard.get("music"):
        options["music"] = storyboard["music"]
    if caption_words:
        options["captions"] = True

    return GroundTruth(
        workdir=root,
        format=_infer_format(storyboard),
        aspect_ratio=_aspect(width or 0, height or 0),
        style=storyboard.get("styleApplied") or storyboard.get("style"),
        topic=plan.get("title") or storyboard.get("title"),
        options=options,
        plan_title=str(plan.get("title", "")),
        planned_total_duration_sec=float(
            plan.get("totalDuration", scenes[-1].end_sec if scenes else 0.0)),
        scenes=scenes,
        caption_words=caption_words,
        render_width=width,
        render_height=height,
    )


#: Six-digit hex colours, the only form styles.py writes.
_HEX_RE = re.compile(r"#([0-9a-fA-F]{6})\b")


def load_palette(project: str | Path) -> Any | None:
    """The video's intended colours as an Nx3 Lab array, or None.

    showwatcher read these out of a generated Remotion token file. The
    equivalent here is the storyboard itself: `styles.py --apply` EXPANDS a
    preset into the storyboard rather than leaving a name to resolve at render
    time — deliberately, so the document says what the video actually looks
    like. That makes the storyboard the most truthful source of the palette,
    and it needs no preset lookup.

    If the storyboard yields nothing (no style applied), the named preset is
    tried as a fallback so an un-expanded project still gets a palette.
    """
    root = Path(project)
    text = ""
    storyboard_path = root / "storyboard.json"
    if storyboard_path.is_file():
        text = storyboard_path.read_text()

    hexes = set(_HEX_RE.findall(text))

    if not hexes and text:
        # Nothing expanded into the storyboard — fall back to the preset it names.
        try:
            name = (json.loads(text) or {}).get("styleApplied")
        except json.JSONDecodeError:
            name = None
        if name:
            for base in (Path.home() / ".config" / "video-studio" / "styles",
                         Path(__file__).resolve().parent.parent / "styles"):
                candidate = base / f"{name}.md"
                if candidate.is_file():
                    hexes = set(_HEX_RE.findall(candidate.read_text()))
                    break

    if not hexes:
        return None

    import cv2
    import numpy as np

    rgb = np.array(
        [[int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)] for h in sorted(hexes)],
        dtype=np.uint8,
    )
    lab = cv2.cvtColor(rgb.reshape(-1, 1, 3), cv2.COLOR_RGB2Lab).reshape(-1, 3)
    return lab.astype(np.float64)
