"""Report dataclasses — the JSON contract every consumer reads.

This is v2 of the contract first defined in video-analysis/analyzer/report.py.
Behavioural changes from v1:

  - Finding ids are content-derived rather than positionally disambiguated
    (see report.ids for why that mattered).
  - Findings carry a `key` discriminator and an opaque `fingerprint`.
  - `detectorsSkipped` entries are typed (`missing_extra` vs `crashed` vs
    `requires_workdir` ...) instead of a free-text reason string, so a caller
    can tell "install this extra" apart from "this detector has a bug".

`to_legacy_json()` emits the exact v1 shape, which is what the parity harness
diffs against the rescued corpus.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from video_studio.qc import LEGACY_SCHEMA_VERSION, SCHEMA_VERSION, __version__
from video_studio.qc.report import ids as _ids

Severity = Literal["error", "warning", "info"]

SkipCode = Literal[
    "missing_extra",  # optional dependency absent — actionable, has an install hint
    "requires_workdir",  # needs generator ground truth that wasn't supplied
    "not_applicable",  # deliberately inert for this format/taxonomy
    "no_data",  # ran, but the input had nothing to measure
    "crashed",  # a bug — carries a traceback
    "unknown",  # name passed to --detectors that doesn't exist
]

SEVERITY_ORDER: dict[str, int] = {"error": 0, "warning": 1, "info": 2}


@dataclass
class Finding:
    """One QC observation.

    `key` is the content-derived discriminator that keeps ids stable when a
    detector emits several findings of the same code within one scene. Build it
    with the helpers in report.ids (`text_key`, `time_key`, `class_key`, ...).
    A detector that can emit more than one finding per (code, scene) and leaves
    `key` as None is a bug — tests/test_report_ids.py enforces it.
    """

    detector: str
    code: str
    severity: Severity
    message: str
    scene_id: str | None = None
    key: str | None = None
    span_sec: tuple[float, float] | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    evidence: dict[str, str] = field(default_factory=dict)
    rubric_dimension: str | None = None
    confidence: float | None = None
    taxonomy_targets: list[str] = field(default_factory=list)

    @property
    def base_id(self) -> str:
        return _ids.base_id(self.detector, self.code, self.scene_id, self.key)

    @property
    def fingerprint(self) -> str:
        return _ids.fingerprint(self.detector, self.code, self.scene_id, self.key)

    @property
    def legacy_id(self) -> str:
        """The v1 id, before positional disambiguation is applied."""
        suffix = f":{self.scene_id}" if self.scene_id else ""
        return f"{self.detector}.{self.code.lower()}{suffix}"

    def to_json(self, resolved_id: str) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": resolved_id,
            "fingerprint": self.fingerprint,
            "detector": self.detector,
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.scene_id is not None:
            out["sceneId"] = self.scene_id
        if self.key is not None:
            out["key"] = self.key
        if self.span_sec is not None:
            out["spanSec"] = [round(self.span_sec[0], 3), round(self.span_sec[1], 3)]
        if self.metrics:
            out["metrics"] = self.metrics
        if self.evidence:
            out["evidence"] = self.evidence
        if self.rubric_dimension is not None:
            out["rubricDimension"] = self.rubric_dimension
        if self.confidence is not None:
            out["confidence"] = round(self.confidence, 3)
        if self.taxonomy_targets:
            out["taxonomyTargets"] = list(self.taxonomy_targets)
        return out

    def to_legacy_json(self, resolved_id: str) -> dict[str, Any]:
        """Exactly the v1 field set, in v1 order — nothing added, nothing dropped."""
        out: dict[str, Any] = {
            "id": resolved_id,
            "detector": self.detector,
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.scene_id is not None:
            out["sceneId"] = self.scene_id
        if self.span_sec is not None:
            out["spanSec"] = [round(self.span_sec[0], 3), round(self.span_sec[1], 3)]
        if self.metrics:
            out["metrics"] = self.metrics
        if self.evidence:
            out["evidence"] = self.evidence
        if self.rubric_dimension is not None:
            out["rubricDimension"] = self.rubric_dimension
        return out


@dataclass
class SceneTiming:
    """Per-scene spine: planned bounds plus whatever each detector measured."""

    id: str
    index: int
    planned_start_sec: float
    planned_end_sec: float
    narration: str
    detected_cut_sec: float | None = None
    audio_offset_ms: float | None = None
    caption_offset_ms: float | None = None
    av_offset_ms: float | None = None
    lip_sync_offset_ms: float | None = None

    def to_json(self) -> dict[str, Any]:
        def ms(value: float | None) -> float | None:
            return None if value is None else round(value, 1)

        out = self.to_legacy_json()
        out["avOffsetMs"] = ms(self.av_offset_ms)
        out["lipSyncOffsetMs"] = ms(self.lip_sync_offset_ms)
        return out

    def to_legacy_json(self) -> dict[str, Any]:
        def ms(value: float | None) -> float | None:
            return None if value is None else round(value, 1)

        return {
            "id": self.id,
            "index": self.index,
            "plannedStartSec": round(self.planned_start_sec, 3),
            "plannedEndSec": round(self.planned_end_sec, 3),
            "detectedCutSec": (
                None if self.detected_cut_sec is None else round(self.detected_cut_sec, 3)
            ),
            "audioOffsetMs": ms(self.audio_offset_ms),
            "captionOffsetMs": ms(self.caption_offset_ms),
            "narration": self.narration,
        }


@dataclass
class Skip:
    """A detector or service that did not run, and why."""

    name: str
    code: SkipCode
    kind: Literal["detector", "service"] = "detector"
    extra: str | None = None
    detail: str | None = None

    @property
    def hint(self) -> str | None:
        if self.code == "missing_extra" and self.extra:
            return f"uv sync --extra {self.extra}"
        return None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"name": self.name, "kind": self.kind, "code": self.code}
        if self.extra:
            out["extra"] = self.extra
        if self.detail:
            out["detail"] = self.detail
        if self.hint:
            out["hint"] = self.hint
        return out

    def to_legacy_json(self) -> dict[str, str]:
        """v1 collapsed everything into one free-text `reason` string."""
        if self.code == "missing_extra":
            missing = self.detail or "dependency"
            hint = f" ({self.hint})" if self.hint else ""
            reason = f"missing dependency: {missing}{hint}"
        elif self.code == "requires_workdir":
            reason = "requires --workdir (showrunner ground truth)"
        elif self.code == "crashed":
            reason = f"crashed: {self.detail or 'unknown error'}"
        elif self.code == "unknown":
            reason = "unknown or not installed"
        else:
            reason = self.detail or self.code
        return {"name": self.name, "reason": reason}


@dataclass
class Report:
    video: dict[str, Any]
    workdir: dict[str, Any] | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    taxonomy: dict[str, Any] | None = None
    scenes: list[SceneTiming] = field(default_factory=list)
    detectors_run: list[str] = field(default_factory=list)
    services_run: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[Skip] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    scorecards: list[dict[str, Any]] = field(default_factory=list)
    rubric: dict[str, Any] | None = None
    artifacts: dict[str, str] = field(default_factory=dict)
    timings: dict[str, Any] = field(default_factory=dict)
    generated_at: str | None = None

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def set_metric(self, key: str, value: float) -> None:
        self.metrics[key] = round(float(value), 4)

    def scene(self, scene_id: str) -> SceneTiming | None:
        for scene in self.scenes:
            if scene.id == scene_id:
                return scene
        return None

    def _sorted_findings(self) -> list[Finding]:
        return sorted(self.findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.base_id))

    def _summary(self) -> dict[str, int]:
        return {
            "errors": sum(1 for f in self.findings if f.severity == "error"),
            "warnings": sum(1 for f in self.findings if f.severity == "warning"),
            "info": sum(1 for f in self.findings if f.severity == "info"),
        }

    def _timestamp(self) -> str:
        return self.generated_at or datetime.now(UTC).isoformat(timespec="seconds")

    def to_json(self) -> dict[str, Any]:
        findings = self._sorted_findings()
        resolved = _ids.resolve_ids(findings)
        out: dict[str, Any] = {
            "schemaVersion": SCHEMA_VERSION,
            "analyzerVersion": __version__,
            "findingIdScheme": "v2-content",
            "generatedAt": self._timestamp(),
            "inputs": self.inputs,
            "video": self.video,
            "workdir": self.workdir,
            "taxonomy": self.taxonomy,
            "scenes": [s.to_json() for s in self.scenes],
            "detectorsRun": self.detectors_run,
            "servicesRun": self.services_run,
            "detectorsSkipped": [s.to_json() for s in self.skipped],
            "metrics": self.metrics,
            "findings": [f.to_json(resolved[id(f)]) for f in findings],
            "summary": self._summary(),
        }
        if self.scorecards:
            out["scorecards"] = self.scorecards
        if self.rubric is not None:
            out["rubric"] = self.rubric
        if self.artifacts:
            out["artifacts"] = self.artifacts
        if self.timings:
            out["timings"] = self.timings
        return out

    def to_legacy_json(self) -> dict[str, Any]:
        """Emit the v1 contract, positional id disambiguation included.

        This is what the parity harness compares against the rescued corpus, so
        it reproduces v1's quirks deliberately — including the positional `:2`
        suffix that v2 exists to eliminate.
        """
        findings = sorted(self.findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.legacy_id))
        seen: dict[str, int] = {}
        finding_dicts: list[dict[str, Any]] = []
        for finding in findings:
            legacy_id = finding.legacy_id
            count = seen.get(legacy_id, 0) + 1
            seen[legacy_id] = count
            if count > 1:
                legacy_id = f"{legacy_id}:{count}"
            finding_dicts.append(finding.to_legacy_json(legacy_id))
        return {
            "schemaVersion": LEGACY_SCHEMA_VERSION,
            "analyzerVersion": __version__,
            "generatedAt": self._timestamp(),
            "video": self.video,
            "workdir": self.workdir,
            "scenes": [s.to_legacy_json() for s in self.scenes],
            "detectorsRun": self.detectors_run,
            "detectorsSkipped": [s.to_legacy_json() for s in self.skipped],
            "metrics": self.metrics,
            "findings": finding_dicts,
            "summary": self._summary(),
        }

    def dumps(self, *, legacy: bool = False) -> str:
        payload = self.to_legacy_json() if legacy else self.to_json()
        return json.dumps(payload, indent=2)
