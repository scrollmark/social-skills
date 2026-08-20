"""Services: the only code that touches media. Detectors are pure over
the artifacts these produce (see showwatcher.context)."""

from video_studio.qc.services.frame_services import run_frame_services

__all__ = ["run_frame_services"]
