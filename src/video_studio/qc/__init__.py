"""Checking a render against the plan it was built from.

Ported from `showwatcher`, an internal analyzer that was documented as this
pipeline's step-8 quality gate for a year and never installed anywhere. The
detectors and the decode layer were independent of that tool's host; the only
coupling was where the ground truth came from, which is now `ground_truth.py`
reading this repo's `plan.json` instead of a showrunner work_dir.

Three of these checks — container, timeline, black_freeze — also ship as the
bundled `qc_render.py` in the video-production skill, which needs no install at
all. This package is the rest: everything that needs decoded frames, and behind
further extras, everything that needs a model.
"""

__version__ = "0.1.0"

#: Report schema this package emits.
SCHEMA_VERSION = 2

#: The shape v1 wrote. Kept so reports produced before the port still load.
LEGACY_SCHEMA_VERSION = 1

__all__ = ["LEGACY_SCHEMA_VERSION", "SCHEMA_VERSION", "__version__"]
