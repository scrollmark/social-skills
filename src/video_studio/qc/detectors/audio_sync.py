"""Per-scene narration timing vs the final mix, over the shared AudioTrack.

v1 decoded the mix once here and once in audio_quality, plus every scene WAV;
AudioTrack now caches all of it. envelope_offset_ms is the vectorized version
(same lag selection, oracle-tested). avDesync = audioOffset - sceneCutDrift
isolates true A/V desync: audio and video drifting together is benign,
diverging is the bug.
"""

from __future__ import annotations

from video_studio.qc.analysis.align import ENVELOPE_RATE_HZ, envelope_offset_ms, rms_envelope
from video_studio.qc.context import Context
from video_studio.qc.report.model import Finding, Severity

SAMPLE_RATE = 16_000
NEEDLE_SEC = 2.0  # correlate the first 2s of each scene's narration
SEARCH_RADIUS_SEC = 2.0  # ± window around the planned start
MIN_CONFIDENCE = 0.5  # correlation peak below this → unreliable, skip
OFFSET_WARN_MS = 150.0
OFFSET_ERROR_MS = 500.0
AV_DESYNC_WARN_MS = 200.0


def run(ctx: Context) -> None:
    gt = ctx.ground_truth
    r = ctx.report
    assert gt is not None

    wavs = {s.id: gt.scene_wav(s.id) for s in gt.scenes}
    if not any(wavs.values()):
        r.add(
            Finding(
                "audio_sync",
                "NO_SCENE_WAVS",
                "info",
                "No per-scene narration WAVs found in the workdir — audio sync analysis skipped",
            )
        )
        return

    mix_env = ctx.audio.envelope
    offsets: dict[str, float] = {}

    for scene in gt.scenes:
        wav = wavs[scene.id]
        if wav is None:
            continue
        needle_pcm = ctx.audio.wav_pcm_head(wav, NEEDLE_SEC)
        needle_env = rms_envelope(needle_pcm, SAMPLE_RATE)
        result = envelope_offset_ms(
            needle_env,
            mix_env,
            expected_index=int(scene.start_sec * ENVELOPE_RATE_HZ),
            search_radius=int(SEARCH_RADIUS_SEC * ENVELOPE_RATE_HZ),
        )
        if result is None:
            continue
        offset_ms, confidence = result
        if confidence < MIN_CONFIDENCE:
            r.add(
                Finding(
                    "audio_sync",
                    "AUDIO_NOT_LOCATED",
                    "warning",
                    f"Scene '{scene.id}' narration could not be confidently located in the final "
                    f"mix near {scene.start_sec:.2f}s (best correlation {confidence:.2f}) — "
                    "narration may be missing, heavily masked by music, or far out of position",
                    scene_id=scene.id,
                    span_sec=(scene.start_sec, scene.end_sec),
                    metrics={"confidence": round(confidence, 3)},
                    rubric_dimension="audio",
                )
            )
            continue

        offsets[scene.id] = offset_ms
        for st in r.scenes:
            if st.id == scene.id:
                st.audio_offset_ms = offset_ms

        if abs(offset_ms) >= OFFSET_WARN_MS:
            severity: Severity = "error" if abs(offset_ms) >= OFFSET_ERROR_MS else "warning"
            direction = "late" if offset_ms > 0 else "early"
            r.add(
                Finding(
                    "audio_sync",
                    "AUDIO_OFFSET",
                    severity,
                    f"Scene '{scene.id}' narration starts {abs(offset_ms):.0f}ms {direction} vs "
                    f"the planned timeline (correlation {confidence:.2f})",
                    scene_id=scene.id,
                    span_sec=(scene.start_sec, scene.start_sec + NEEDLE_SEC),
                    metrics={"offsetMs": round(offset_ms, 1), "confidence": round(confidence, 3)},
                    rubric_dimension="audio",
                )
            )

    if offsets:
        vals = list(offsets.values())
        r.set_metric("sync.meanAudioOffsetMs", sum(vals) / len(vals))
        r.set_metric("sync.maxAudioOffsetMs", max(abs(v) for v in vals))

    # True A/V desync: audio and video boundaries diverging within a scene.
    for st in r.scenes:
        if st.audio_offset_ms is None or st.detected_cut_sec is None:
            continue
        cut_drift_ms = (st.detected_cut_sec - st.planned_start_sec) * 1000.0
        av_desync = st.audio_offset_ms - cut_drift_ms
        if abs(av_desync) >= AV_DESYNC_WARN_MS:
            r.add(
                Finding(
                    "audio_sync",
                    "AV_DESYNC",
                    "error",
                    f"Scene '{st.id}': narration is {abs(av_desync):.0f}ms "
                    f"{'behind' if av_desync > 0 else 'ahead of'} its visuals — the video cut "
                    f"moved {cut_drift_ms:+.0f}ms but the audio moved {st.audio_offset_ms:+.0f}ms",
                    scene_id=st.id,
                    span_sec=(st.planned_start_sec, st.planned_end_sec),
                    metrics={
                        "avDesyncMs": round(av_desync, 1),
                        "cutDriftMs": round(cut_drift_ms, 1),
                        "audioOffsetMs": round(st.audio_offset_ms, 1),
                    },
                    rubric_dimension="audio",
                )
            )
