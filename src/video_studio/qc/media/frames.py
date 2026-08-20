"""Dense keyframe extraction: dHash scene selection ported from frame-extract.ts.

The selection logic (`select_kept_frames`, `cap_frames`) is pure and streaming —
one implementation serves both the unit tests (synthetic Candidate lists) and
the real extractor (a generator that decodes frames as selection consumes them).

Honest divergence from the TS pipeline: sharp resized in RGB with Lanczos3;
OpenCV here uses INTER_AREA. Individual hash bits will differ slightly, so the
parity test asserts kept-frame counts/timestamps agree loosely, never that
hashes are bit-identical. Nothing persisted ever depended on the old hashes.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HASH_SIZE = 8  # dHash: 8x8 grid of bit comparisons = 64-bit hash
TOTAL_BITS = HASH_SIZE * HASH_SIZE


@dataclass(frozen=True)
class Candidate:
    index: int
    timestamp_sec: float
    hash: bytes  # exactly HASH_SIZE bytes


@dataclass(frozen=True)
class FrameExtractOptions:
    base_fps: float = 2.0
    max_width: int = 1280
    scene_threshold: float = 0.12  # normalized Hamming distance for a scene change
    floor_interval_sec: float = 10.0  # force-keep at least one frame this often
    dedup_window_size: int = 5  # compare against last N *kept* frames
    max_frames: int = 150  # hard cap, evenly downsampled if exceeded


DEFAULTS = FrameExtractOptions()


def compute_dhash(bgr: Any) -> bytes:
    """dHash: each pixel vs its right neighbor on a 9x8 greyscale grid.

    More robust to brightness/exposure flicker than a naive pixel diff — the
    same reasoning as the TS original. MSB-first bit packing matches the TS
    `byte = (byte << 1) | bit` loop.
    """
    import cv2
    import numpy as np

    small = cv2.resize(bgr, (HASH_SIZE + 1, HASH_SIZE), interpolation=cv2.INTER_AREA)
    if small.ndim == 3:
        small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    bits = small[:, 1:] > small[:, :-1]  # left < right -> 1
    return np.packbits(bits, axis=1).tobytes()


def hamming_distance(a: bytes, b: bytes) -> int:
    return (int.from_bytes(a, "big") ^ int.from_bytes(b, "big")).bit_count()


def normalized_distance(a: bytes, b: bytes) -> float:
    return hamming_distance(a, b) / TOTAL_BITS


def select_kept_frames(
    candidates: Iterable[Candidate],
    opts: FrameExtractOptions = DEFAULTS,
) -> Iterator[Candidate]:
    """Scene-change detection + fps-floor guarantee + N-frame dedup window.

    A streaming generator: each candidate is decided on arrival with no
    lookahead, so the real extractor can decode lazily and drop frames the
    moment they are rejected. Semantics are the TS original's exactly:

    - keep when the hash moved >= scene_threshold from the PREVIOUS candidate
      (not the previous kept frame), or when the floor interval has elapsed;
    - then reject if within scene_threshold of any of the last N KEPT hashes
      (A/B flicker dedup) — unless the floor is due, which always wins.
    """
    kept_hash_window: list[bytes] = []
    prev_hash: bytes | None = None
    last_kept_timestamp = float("-inf")

    for cand in candidates:
        is_scene_change = (
            prev_hash is None or normalized_distance(cand.hash, prev_hash) >= opts.scene_threshold
        )
        is_floor_due = cand.timestamp_sec - last_kept_timestamp >= opts.floor_interval_sec
        prev_hash = cand.hash

        if not is_scene_change and not is_floor_due:
            continue

        is_dup_of_recent_kept = any(
            normalized_distance(cand.hash, kh) < opts.scene_threshold for kh in kept_hash_window
        )
        if is_dup_of_recent_kept and not is_floor_due:
            continue

        yield cand
        last_kept_timestamp = cand.timestamp_sec
        kept_hash_window.append(cand.hash)
        if len(kept_hash_window) > opts.dedup_window_size:
            kept_hash_window.pop(0)


def cap_frames(kept: Sequence[Candidate], max_frames: int) -> Sequence[Candidate]:
    """Evenly downsample across the whole timeline rather than truncating.

    Returns the SAME sequence object when already under the cap — the TS test
    asserts identity (`toBe`), and callers rely on the no-copy fast path.
    `(i * len) // max` is integer math, identical to JS `Math.floor` here.
    """
    if len(kept) <= max_frames:
        return kept
    return [kept[(i * len(kept)) // max_frames] for i in range(max_frames)]


def extract_frames(
    video_path: Path,
    out_dir: Path,
    opts: FrameExtractOptions = DEFAULTS,
) -> list[Candidate]:
    """Decode a local video once, select keyframes, write JPEGs.

    Replaces the TS pipeline's ffmpeg-to-2000-JPEGs spill + sharp rehash with an
    in-process sequential decode: frames are hashed in memory and only KEPT
    frames ever touch disk. Filename convention matches the TS original
    (`frame-000001-00012.50s.jpg`) so downstream consumers keep working.
    """
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"could not open video: {video_path}")

    native_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, round(native_fps / opts.base_fps))

    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Retain the pixels only for the candidate currently being decided —
    # selection is synchronous with decode, so one frame is live at a time.
    pending: dict[int, Any] = {}

    def candidates() -> Iterator[Candidate]:
        frame_idx = 0
        cand_idx = 0
        while True:
            grabbed = cap.grab()
            if not grabbed:
                return
            if frame_idx % step == 0:
                ok, frame = cap.retrieve()
                if ok:
                    if opts.max_width and frame.shape[1] > opts.max_width:
                        scale = opts.max_width / frame.shape[1]
                        frame = cv2.resize(
                            frame,
                            (opts.max_width, max(2, int(frame.shape[0] * scale)) & ~1),
                            interpolation=cv2.INTER_AREA,
                        )
                    pending.clear()
                    pending[cand_idx] = frame
                    yield Candidate(
                        index=cand_idx,
                        timestamp_sec=frame_idx / native_fps,
                        hash=compute_dhash(frame),
                    )
                    cand_idx += 1
            frame_idx += 1

    try:
        kept_stream: list[tuple[Candidate, Any]] = []
        scratch: list[tuple[Candidate, Path]] = []
        scratch_dir = out_dir / ".scratch"
        scratch_dir.mkdir(parents=True, exist_ok=True)
        for cand in select_kept_frames(candidates(), opts):
            frame = pending.get(cand.index)
            if frame is None:  # pragma: no cover — selection is synchronous
                continue
            tmp = scratch_dir / f"cand-{cand.index:08d}.jpg"
            cv2.imwrite(str(tmp), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            scratch.append((cand, tmp))
        del kept_stream
    finally:
        cap.release()

    survivors = cap_frames([c for c, _ in scratch], opts.max_frames)
    survivor_set = {c.index for c in survivors}
    result: list[Candidate] = []
    seq = 0
    for cand, tmp in scratch:
        if cand.index not in survivor_set:
            tmp.unlink(missing_ok=True)
            continue
        seq += 1
        dest = frames_dir / f"frame-{seq:06d}-{cand.timestamp_sec:08.2f}s.jpg"
        tmp.rename(dest)
        result.append(cand)
    scratch_dir.rmdir()
    return result
