"""NEW in showwatcher: the three-clock timeline audit.

The one detector v1 structurally could not have. It resolves the video, audio,
and caption timelines independently from the workdir's own artifacts and
reports where they diverge — pure arithmetic over text files and ffprobe, no
video decoding.

The motivating case (measured, shipped): round3-2.1-greenscreen's clips_norm
are 5.000s each while its WAVs are 4.925/3.050/3.325s. Video clock 15.0s,
audio clock 11.3s — narration ran 3.7s ahead of its visuals, and the v1
analyzer had nowhere to put a second clock, so it reported nothing.

Not part of the v1 parity set; the parity harness compares shared detectors only.
"""

from __future__ import annotations

from video_studio.qc.context import Context
from video_studio.qc.report import ids
from video_studio.qc.report.model import Finding
from video_studio.qc.timelines import (
    CLOCK_SKEW_ERROR_SEC,
    detect_generation,
    resolve_timelines,
)

CLIP_SHORT_TOLERANCE_SEC = 1.0 / 30.0  # one frame at 30fps
SOURCE_DISAGREE_WARN_SEC = 1.0 / 30.0


def run(ctx: Context) -> None:
    gt = ctx.ground_truth
    r = ctx.report
    assert gt is not None

    timelines = resolve_timelines(gt)
    generation = detect_generation(gt)
    if generation != "n/a":
        r.set_metric("timeline.audioSizedGeneration", 1.0 if generation == "audio-sized" else 0.0)

    if timelines.video:
        r.set_metric("timeline.videoClockSec", timelines.video[-1].end_sec)
    if timelines.audio:
        r.set_metric("timeline.audioClockSec", timelines.audio[-1].end_sec)

    # The headline check: do the video and audio clocks agree?
    worst = timelines.max_clock_skew()
    if worst is not None:
        scene_id, skew = worst
        r.set_metric("timeline.maxClockSkewSec", skew)
        if skew > CLOCK_SKEW_ERROR_SEC:
            video_end = timelines.video[-1].end_sec
            audio_end = timelines.audio[-1].end_sec
            r.add(
                Finding(
                    "timeline",
                    "TIMELINE_CLOCK_MISMATCH",
                    "error",
                    f"The visual and audio timelines diverge by {skew:.2f}s at scene "
                    f"'{scene_id}' (video clock ends {video_end:.2f}s, audio clock "
                    f"{audio_end:.2f}s) — narration and visuals are built on different "
                    "clocks and drift apart scene by scene. Detected from plan.json and "
                    "the measured narration WAVs, before any video decoding.",
                    scene_id=scene_id,
                    metrics={
                        "maxSkewSec": round(skew, 3),
                        "videoClockSec": round(video_end, 3),
                        "audioClockSec": round(audio_end, 3),
                    },
                    rubric_dimension="audio",
                )
            )

    # Start-skew is blind to the final scene: a scene that overruns its plan
    # pushes every LATER scene late, and the last one has nothing after it to
    # push. A two-scene video whose second scene runs two seconds long therefore
    # scores a perfect zero skew while the narration outlasts the picture. So
    # compare the totals too, and only when the per-scene check stayed quiet —
    # otherwise the same drift is reported twice.
    if timelines.video and timelines.audio:
        video_end = timelines.video[-1].end_sec
        audio_end = timelines.audio[-1].end_sec
        total_gap = abs(video_end - audio_end)
        already_reported = worst is not None and worst[1] > CLOCK_SKEW_ERROR_SEC
        if total_gap > CLOCK_SKEW_ERROR_SEC and not already_reported:
            longer = "narration" if audio_end > video_end else "picture"
            r.add(
                Finding(
                    "timeline",
                    "TIMELINE_TOTAL_MISMATCH",
                    "error",
                    f"The visual timeline runs {video_end:.2f}s and the narration "
                    f"{audio_end:.2f}s — a {total_gap:.2f}s gap, with the {longer} "
                    f"outlasting the other. Every scene starts where the plan says, so "
                    f"the drift is all in the last one: re-run build_props so the plan "
                    f"picks up the measured audio.",
                    metrics={
                        "totalGapSec": round(total_gap, 3),
                        "videoClockSec": round(video_end, 3),
                        "audioClockSec": round(audio_end, 3),
                    },
                    rubric_dimension="audio",
                )
            )

    # Provider clips shorter than their planned scene: ffmpeg -t can only trim,
    # never lengthen, so the visual timeline silently shrinks.
    plan_durations = {s.id: s for s in gt.scenes}
    for span in timelines.video:
        planned = plan_durations.get(span.scene_id)
        if planned is None:
            continue
        short_by = planned.duration_sec - span.duration_sec
        if short_by > CLIP_SHORT_TOLERANCE_SEC:
            r.add(
                Finding(
                    "timeline",
                    "CLIP_SHORTER_THAN_SCENE",
                    "warning",
                    f"Scene '{span.scene_id}': the rendered clip is {span.duration_sec:.2f}s "
                    f"but the plan calls for {planned.duration_sec:.2f}s — the provider clip "
                    f"came up {short_by:.2f}s short and -t cannot lengthen it",
                    scene_id=span.scene_id,
                    key=ids.time_key(span.start_sec),
                    metrics={"shortBySec": round(short_by, 3)},
                    rubric_dimension="motion-timing",
                )
            )

    # Artifact clock vs the v1 single-timeline: disagreement means the old
    # ground truth was measuring against the wrong reference.
    gt_by_id = {s.id: s for s in gt.scenes}
    worst_disagreement: tuple[str, float] | None = None
    for span in timelines.video:
        planned = gt_by_id.get(span.scene_id)
        if planned is None:
            continue
        delta = abs(span.start_sec - planned.start_sec)
        if worst_disagreement is None or delta > worst_disagreement[1]:
            worst_disagreement = (span.scene_id, delta)
    if worst_disagreement is not None and worst_disagreement[1] > SOURCE_DISAGREE_WARN_SEC:
        scene_id, delta = worst_disagreement
        r.add(
            Finding(
                "timeline",
                "TIMELINE_SOURCE_DISAGREEMENT",
                "warning",
                f"The workdir's own render artifacts place scene '{scene_id}' "
                f"{delta:.2f}s away from the single-timeline ground truth the sync "
                "detectors measure against — their per-scene offsets are measured "
                "against a reference the render did not actually use",
                scene_id=scene_id,
                metrics={"maxDisagreementSec": round(delta, 3)},
            )
        )

    # Sanity: does the container agree with the artifact video clock?
    if timelines.video:
        artifact_end = timelines.video[-1].end_sec
        r.set_metric("timeline.containerVsVideoClockSec", ctx.video.duration_sec - artifact_end)
