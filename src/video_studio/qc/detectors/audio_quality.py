"""Audio quality: EBU R128 loudness, trailing silence, music ducking.

Loudness arrives from the shared ffmpeg filter pass (chained with black/freeze
detection — one decode instead of v1's three); the envelope work uses the
shared AudioTrack. Heuristics, thresholds, and messages are v1 verbatim.
"""

from __future__ import annotations

import numpy as np

from video_studio.qc.analysis.align import ENVELOPE_RATE_HZ
from video_studio.qc.context import Context
from video_studio.qc.report.model import Finding

# Social platforms normalize to roughly -14 LUFS; renders far off get penalized
# or pumped by platform processing.
LUFS_TARGET = -14.0
LUFS_WARN_DELTA = 6.0
TRAILING_SILENCE_WARN_SEC = 1.25  # narration naturally ends ~1s before the video
DUCKING_MIN_DROP_DB = 2.0
GAP_MIN_SEC = 0.4


def run(ctx: Context) -> None:
    r = ctx.report
    v = ctx.video
    gt = ctx.ground_truth

    if v.audio is None:
        return  # container detector already reports the missing stream

    fp = ctx.artifacts.filter_pass
    assert fp is not None, "engine must run the filter pass before audio_quality"
    loud = fp.loudness
    if loud is not None:
        integrated, lra, peak = loud
        r.set_metric("audio.integratedLufs", integrated)
        r.set_metric("audio.loudnessRangeLu", lra)
        if peak is not None:
            r.set_metric("audio.truePeakDbfs", peak)
        if abs(integrated - LUFS_TARGET) > LUFS_WARN_DELTA:
            direction = "quiet" if integrated < LUFS_TARGET else "loud"
            r.add(
                Finding(
                    "audio_quality",
                    "LOUDNESS_OFF_TARGET",
                    "warning",
                    f"Integrated loudness {integrated:.1f} LUFS is far {direction} of the "
                    f"~{LUFS_TARGET:.0f} LUFS social-platform target — platforms will "
                    "renormalize and may pump artifacts",
                    metrics={"integratedLufs": integrated},
                    rubric_dimension="audio",
                )
            )
        if peak is not None and peak > -1.0:
            r.add(
                Finding(
                    "audio_quality",
                    "PEAK_CLIPPING_RISK",
                    "warning",
                    f"True peak {peak:.1f} dBFS exceeds -1 dBFS — risk of clipping after "
                    "platform transcode",
                    metrics={"truePeakDbfs": peak},
                    rubric_dimension="audio",
                )
            )

    # Envelope-based tail + ducking analysis (shared AudioTrack decode).
    env = ctx.audio.envelope
    if len(env) == 0:
        return
    env_db = ctx.audio.envelope_db
    silence_floor = -50.0

    # Trailing silence measured against the VIDEO's end, not the audio
    # track's — an audio stream that simply ends early is the same defect.
    active = np.where(env_db > silence_floor)[0]
    if len(active):
        audio_active_end_sec = active[-1] / ENVELOPE_RATE_HZ
        trailing = max(0.0, v.duration_sec - audio_active_end_sec)
        r.set_metric("audio.trailingSilenceSec", trailing)
        if trailing > TRAILING_SILENCE_WARN_SEC:
            r.add(
                Finding(
                    "audio_quality",
                    "TRAILING_SILENCE",
                    "warning",
                    f"Audio goes silent {trailing:.2f}s before the video ends — audio/visual "
                    "timeline mismatch (the audible counterpart of a black-frame tail)",
                    span_sec=(v.duration_sec - trailing, v.duration_sec),
                    metrics={"trailingSilenceSec": round(trailing, 3)},
                    rubric_dimension="audio",
                )
            )

    # Ducking heuristic — needs narration gap positions from scene WAVs.
    if gt is None or not gt.options.get("music") or gt.options.get("music") == "none":
        return
    gap_windows: list[tuple[int, int]] = []
    speech_windows: list[tuple[int, int]] = []
    any_wav = False
    for scene in gt.scenes:
        wav = gt.scene_wav(scene.id)
        if wav is None:
            continue
        any_wav = True
        wav_env = ctx.audio.wav_envelope(wav)
        wav_db = 20 * np.log10(np.maximum(wav_env, 1e-6))
        base = int(scene.start_sec * ENVELOPE_RATE_HZ)
        is_speech = wav_db > silence_floor
        # Contiguous silent runs >= GAP_MIN_SEC inside the scene = narration gaps.
        i = 0
        while i < len(is_speech):
            j = i
            while j < len(is_speech) and not is_speech[j]:
                j += 1
            if j - i >= GAP_MIN_SEC * ENVELOPE_RATE_HZ:
                gap_windows.append((base + i, base + j))
            if j == i:
                k = i
                while k < len(is_speech) and is_speech[k]:
                    k += 1
                speech_windows.append((base + i, base + k))
                i = k
            else:
                i = j
    if not any_wav or not gap_windows or not speech_windows:
        return

    def mean_db(windows: list[tuple[int, int]]) -> float:
        vals = np.concatenate([env_db[a:b] for a, b in windows if b <= len(env_db) and b > a])
        return float(vals.mean()) if len(vals) else -float(np.inf)

    gap_db = mean_db(gap_windows)
    speech_db = mean_db(speech_windows)
    if not np.isfinite(gap_db) or not np.isfinite(speech_db):
        return
    drop = speech_db - gap_db
    r.set_metric("audio.narrationGapDropDb", drop)
    if drop < DUCKING_MIN_DROP_DB:
        r.add(
            Finding(
                "audio_quality",
                "MUSIC_NOT_DUCKING",
                "warning",
                f"Mix level in narration gaps ({gap_db:.1f} dB) is within {drop:.1f} dB of the "
                f"level under speech ({speech_db:.1f} dB) — the music bed does not appear to "
                "duck under narration",
                metrics={"gapDb": round(gap_db, 1), "speechDb": round(speech_db, 1)},
                rubric_dimension="audio",
            )
        )
