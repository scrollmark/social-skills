"""ffprobe wrapper: container/stream facts for the report header.

Verbatim port of analyzer/probe.py — the report's `video` block is part of the
parity contract, so field names, rounding, and fps fallback order are preserved.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from typing import Any


class ProbeError(RuntimeError):
    pass


@dataclass
class VideoInfo:
    path: str
    duration_sec: float
    width: int
    height: int
    fps: float
    pix_fmt: str | None
    video_codec: str | None
    audio: dict[str, Any] | None  # {codec, sampleRate, channels} or None

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "durationSec": round(self.duration_sec, 3),
            "width": self.width,
            "height": self.height,
            "fps": round(self.fps, 3),
            "pixFmt": self.pix_fmt,
            "videoCodec": self.video_codec,
            "audio": self.audio,
        }


def _parse_rate(rate: str | None) -> float:
    if not rate or rate in {"0/0", "N/A"}:
        return 0.0
    try:
        return float(Fraction(rate))
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe(video_path: str) -> VideoInfo:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError as e:
        raise ProbeError(
            "ffprobe not found on PATH — install ffmpeg (e.g. `brew install ffmpeg`)"
        ) from e
    except subprocess.CalledProcessError as e:
        raise ProbeError(f"ffprobe failed for {video_path}: {e.stderr.strip()}") from e

    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    vstream = next((s for s in streams if s.get("codec_type") == "video"), None)
    astream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if vstream is None:
        raise ProbeError(f"no video stream in {video_path}")

    fmt = data.get("format", {})
    duration = float(fmt.get("duration") or vstream.get("duration") or 0.0)

    audio = None
    if astream is not None:
        audio = {
            "codec": astream.get("codec_name"),
            "sampleRate": int(astream.get("sample_rate") or 0),
            "channels": int(astream.get("channels") or 0),
        }

    return VideoInfo(
        path=video_path,
        duration_sec=duration,
        width=int(vstream.get("width") or 0),
        height=int(vstream.get("height") or 0),
        fps=_parse_rate(vstream.get("avg_frame_rate")) or _parse_rate(vstream.get("r_frame_rate")),
        pix_fmt=vstream.get("pix_fmt"),
        video_codec=vstream.get("codec_name"),
        audio=audio,
    )
