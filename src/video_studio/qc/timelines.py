"""Three clocks, never one.

Ported in spirit from showwatcher's `showrunner/timeline.py`, which resolved a
video, audio and caption timeline independently and treated their disagreement
as the signal. The idea survives the move; the artifacts do not. That module
read `concat.txt`, `_audio_concat.txt`, `captions.ass` and `Root.tsx` — files
showrunner wrote and this repo has never heard of.

The three clocks here:

  video    `plan.json` scene durations — the composition timeline, what
           build_props told the renderer each scene would occupy.
  audio    the MEASURED length of `audio/<scene>.wav`, via ffprobe.
  caption  the last word to leave the screen in `audio/<scene>.timings.json`.

Why comparing plan against audio is not circular, given build_props sets each
scene's duration FROM the measured WAV: because they can fall out of step
afterwards, and nothing else notices. Re-synthesise one scene's narration
without re-running build_props and the plan still claims the old length; edit a
duration by hand and the audio disagrees. In both cases the render is built on
one clock and the narration on another, and every scene after the divergence
inherits it. That is the failure this catches, and it is invisible to a check
that only ever consults one timeline.

A clock with no artifact behind it stays empty rather than being guessed at —
an absent WAV means "no audio clock", not "an audio clock of zero".
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from video_studio.qc.ground_truth import GroundTruth

#: Video/audio divergence past this is a real desync, not rounding.
CLOCK_SKEW_ERROR_SEC = 0.25


@dataclass(frozen=True)
class ClockSpan:
    scene_id: str
    start_sec: float
    end_sec: float
    source: str  # "plan" | "audio_probe" | "timings"

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec


@dataclass
class TimelineSet:
    video: list[ClockSpan] = field(default_factory=list)
    audio: list[ClockSpan] = field(default_factory=list)
    caption: list[ClockSpan] = field(default_factory=list)

    def max_clock_skew(self) -> tuple[str, float] | None:
        """Largest |video start - audio start| across scenes present in both."""
        audio_by_id = {s.scene_id: s for s in self.audio}
        worst: tuple[str, float] | None = None
        for vs in self.video:
            a = audio_by_id.get(vs.scene_id)
            if a is None:
                continue
            skew = abs(vs.start_sec - a.start_sec)
            if worst is None or skew > worst[1]:
                worst = (vs.scene_id, skew)
        return worst


_probe_cache: dict[str, float | None] = {}


def probe_duration(path: Path) -> float | None:
    """Measured duration in seconds, or None. Cached — the same WAV is asked
    about once per clock and there may be dozens of scenes."""
    key = str(path)
    if key in _probe_cache:
        return _probe_cache[key]
    value: float | None = None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", key],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        value = float(out)
    except (OSError, subprocess.CalledProcessError, ValueError):
        value = None
    _probe_cache[key] = value
    return value


def clear_probe_cache() -> None:
    _probe_cache.clear()


def _cumulative(ids_durations: list[tuple[str, float]], source: str) -> list[ClockSpan]:
    """Lay durations end to end. The running total is the authority, matching
    how build_props snaps scene boundaries — rounding each span on its own is
    how a timeline drifts a frame per scene."""
    spans: list[ClockSpan] = []
    cursor = 0.0
    for scene_id, duration in ids_durations:
        start, end = cursor, cursor + duration
        cursor = end
        spans.append(ClockSpan(scene_id, start, end, source))
    return spans


def _plan_video_clock(gt: GroundTruth) -> list[ClockSpan]:
    """The composition timeline, straight off the plan."""
    return [ClockSpan(s.id, s.start_sec, s.end_sec, "plan") for s in gt.scenes]


def _wav_audio_clock(gt: GroundTruth) -> list[ClockSpan]:
    """Measured narration, scene by scene.

    Returns empty unless EVERY scene has a readable WAV: a partial audio clock
    would put later scenes at the wrong offset and manufacture a skew that is
    an artefact of the missing file, not of the video.
    """
    measured: list[tuple[str, float]] = []
    for scene in gt.scenes:
        wav = gt.scene_wav(scene.id)
        if wav is None:
            return []
        duration = probe_duration(wav)
        if duration is None:
            return []
        measured.append((scene.id, duration))
    return _cumulative(measured, "audio_probe")


def _timings_caption_clock(gt: GroundTruth) -> list[ClockSpan]:
    """When each scene's captions actually start and stop.

    Built from the words themselves rather than from scene boundaries, so a
    scene whose captions run past its own end is visible as an overlap.
    """
    by_scene: dict[str, list] = {}
    for word in gt.caption_words:
        by_scene.setdefault(word.scene_id, []).append(word)
    spans: list[ClockSpan] = []
    for scene in gt.scenes:
        words = by_scene.get(scene.id)
        if not words:
            continue
        spans.append(ClockSpan(
            scene.id,
            min(w.start_ms for w in words) / 1000.0,
            max(w.end_ms for w in words) / 1000.0,
            "timings",
        ))
    return spans


def resolve_timelines(gt: GroundTruth) -> TimelineSet:
    """Artifact-first clock resolution; an empty clock means no artifact."""
    return TimelineSet(
        video=_plan_video_clock(gt),
        audio=_wav_audio_clock(gt),
        caption=_timings_caption_clock(gt),
    )


def detect_generation(gt: GroundTruth) -> str:
    """showrunner had two work_dir generations — plan-sized and audio-sized —
    and an auto-fix editing a scene duration was a no-op on one of them. This
    repo has one shape, so there is nothing to branch on."""
    return "n/a"


__all__ = [
    "CLOCK_SKEW_ERROR_SEC",
    "ClockSpan",
    "TimelineSet",
    "clear_probe_cache",
    "detect_generation",
    "probe_duration",
    "resolve_timelines",
]
