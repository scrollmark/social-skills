"""Spoken-word verification via faster-whisper. [audio]

v1 port. word_error_rate now routes through rapidfuzz (same value, C++ speed).
The two-alignment design is preserved: whisper-vs-captions isolates "caption
DATA wrong" from "caption RENDERER late" (which is caption_sync's finding).
"""

from __future__ import annotations

import numpy as np

from video_studio.qc.analysis.textmatch import edit_distance_le1, normalize_word, word_error_rate
from video_studio.qc.context import Context
from video_studio.qc.report.model import Finding, Severity

WHISPER_MODEL = "base"
MATCH_WINDOW_MS = 1500.0
CAPTION_DATA_OFFSET_WARN_MS = 250.0
WER_WARN = 0.25
WER_ERROR = 0.5


def transcribe_words(pcm: np.ndarray) -> list[tuple[str, float, float]]:
    """[(normalized_word, start_ms, end_ms)] from 16 kHz mono PCM — the
    shared AudioTrack decode, not a second ffmpeg pass of the file."""
    from faster_whisper import WhisperModel

    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(
        pcm.astype(np.float32), word_timestamps=True, language="en"
    )
    words: list[tuple[str, float, float]] = []
    for seg in segments:
        for w in seg.words or []:
            norm = normalize_word(w.word)
            if norm:
                words.append((norm, w.start * 1000.0, w.end * 1000.0))
    return words


def run(ctx: Context) -> None:
    gt = ctx.ground_truth
    r = ctx.report
    assert gt is not None

    if ctx.video.audio is None:
        return

    spoken = transcribe_words(ctx.audio.pcm)
    r.set_metric("transcript.spokenWordCount", len(spoken))
    if not spoken:
        if any(s.narration.strip() for s in gt.scenes):
            r.add(
                Finding(
                    "transcript",
                    "NO_SPEECH_DETECTED",
                    "error",
                    "The plan has narration but whisper detected no speech in the final mix",
                    rubric_dimension="audio",
                )
            )
        return

    # (b) per-scene WER vs planned narration, assigning spoken words to scenes
    # by the planned timeline.
    total_ref_words = 0
    weighted_wer = 0.0
    for scene in gt.scenes:
        ref = [normalize_word(w) for w in scene.narration.split()]
        ref = [w for w in ref if w]
        if not ref:
            continue
        hyp = [
            w
            for w, start_ms, _end in spoken
            if scene.start_sec * 1000 - 500 <= start_ms < scene.end_sec * 1000 + 500
        ]
        wer = word_error_rate(ref, hyp)
        total_ref_words += len(ref)
        weighted_wer += wer * len(ref)
        if wer >= WER_WARN:
            severity: Severity = "error" if wer >= WER_ERROR else "warning"
            r.add(
                Finding(
                    "transcript",
                    "NARRATION_MISMATCH",
                    severity,
                    f"Scene '{scene.id}': spoken audio differs from planned narration "
                    f"(WER {wer:.0%}) — TTS may have dropped/garbled text, or scene audio is "
                    "positioned in the wrong scene's time window",
                    scene_id=scene.id,
                    span_sec=(scene.start_sec, scene.end_sec),
                    metrics={"wer": round(wer, 3)},
                    rubric_dimension="audio",
                )
            )
    if total_ref_words:
        r.set_metric("transcript.meanWer", weighted_wer / total_ref_words)

    # (a) whisper timestamps vs caption timestamps (both describe when words
    # are SPOKEN; caption render lag is caption_sync's job).
    if gt.caption_words:
        offsets: list[float] = []
        used: set[int] = set()
        for cw in gt.caption_words:
            target = normalize_word(cw.text)
            if len(target) < 3:
                continue
            best: tuple[float, int] | None = None
            for idx, (w, start_ms, _end) in enumerate(spoken):
                if idx in used or abs(start_ms - cw.start_ms) > MATCH_WINDOW_MS:
                    continue
                if edit_distance_le1(target, w):
                    d = abs(start_ms - cw.start_ms)
                    if best is None or d < best[0]:
                        best = (d, idx)
            if best is not None:
                used.add(best[1])
                offsets.append(spoken[best[1]][1] - cw.start_ms)
        if offsets:
            median = float(np.median(offsets))
            r.set_metric("sync.whisperVsCaptionMedianMs", median)
            r.set_metric(
                "sync.whisperCaptionMatchRate",
                len(offsets)
                / max(1, sum(1 for c in gt.caption_words if len(normalize_word(c.text)) >= 3)),
            )
            if abs(median) > CAPTION_DATA_OFFSET_WARN_MS:
                r.add(
                    Finding(
                        "transcript",
                        "CAPTION_DATA_OFFSET",
                        "warning",
                        f"Caption word timings are a median of {abs(median):.0f}ms "
                        f"{'behind' if median > 0 else 'ahead of'} the actually-spoken words — "
                        "the captions FILE is mistimed (independent of any renderer lag)",
                        metrics={"medianOffsetMs": round(median, 1)},
                        rubric_dimension="captions",
                    )
                )
