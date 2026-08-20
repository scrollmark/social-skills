"""Run-over-run comparison: did a generator change actually improve the output?

A direct port of video-analysis/src/compare.ts. The verdict semantics are load-
bearing — they are what the fix loop uses to decide whether to keep a change or
roll it back — so they are reproduced exactly, including the precedence order.

One deliberate extension over the TypeScript original: findings can be matched by
`fingerprint` instead of `id`. The v1 id embedded positional disambiguation, so a
new finding sorting earlier renamed later ones and the diff filled with phantom
fixes. Fingerprints are content-derived and stable (see report.ids), so matching
on them is strictly more accurate. `match_on="id"` reproduces v1 behaviour for
parity checks against the rescued corpus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Verdict = Literal["improved", "regressed", "unchanged", "mixed"]
MatchOn = Literal["id", "fingerprint"]


@dataclass(frozen=True)
class MetricDelta:
    key: str
    before: float | None
    after: float | None
    delta: float | None

    def to_json(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "before": self.before,
            "after": self.after,
            "delta": self.delta,
        }


@dataclass
class FindingsDiff:
    fixed: list[dict[str, Any]] = field(default_factory=list)
    introduced: list[dict[str, Any]] = field(default_factory=list)
    persisting: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "fixed": self.fixed,
            "introduced": self.introduced,
            "persisting": self.persisting,
        }


def compare_metrics(before: dict[str, Any], after: dict[str, Any]) -> list[MetricDelta]:
    """Union of metric keys, sorted, with a delta where both sides have a value.

    `delta` stays None when either side is absent — a metric that only exists in
    one run has no meaningful difference, and reporting 0 would read as "no
    change" when the truth is "not measured".
    """
    before_metrics: dict[str, float] = before.get("metrics", {})
    after_metrics: dict[str, float] = after.get("metrics", {})

    deltas: list[MetricDelta] = []
    for key in sorted(set(before_metrics) | set(after_metrics)):
        b = before_metrics.get(key)
        a = after_metrics.get(key)
        delta = round(a - b, 4) if b is not None and a is not None else None
        deltas.append(MetricDelta(key=key, before=b, after=a, delta=delta))
    return deltas


def _match_key(finding: dict[str, Any], match_on: MatchOn) -> str:
    if match_on == "fingerprint":
        # Fall back to id for v1 reports, which predate fingerprints.
        return str(finding.get("fingerprint") or finding["id"])
    return str(finding["id"])


def compare_findings(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    match_on: MatchOn = "fingerprint",
) -> FindingsDiff:
    """Set-diff findings into fixed / introduced / persisting.

    `persisting` returns the AFTER copy, matching the TypeScript original — the
    caller wants the current measurement, not the stale one.
    """
    before_map = {_match_key(f, match_on): f for f in before.get("findings", [])}
    after_map = {_match_key(f, match_on): f for f in after.get("findings", [])}

    return FindingsDiff(
        fixed=[f for k, f in before_map.items() if k not in after_map],
        introduced=[f for k, f in after_map.items() if k not in before_map],
        persisting=[f for k, f in after_map.items() if k in before_map],
    )


def _count_errors(findings: list[dict[str, Any]]) -> int:
    return sum(1 for f in findings if f.get("severity") == "error")


def summarize_comparison(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    match_on: MatchOn = "fingerprint",
) -> dict[str, Any]:
    """Verdict + diff + changed metrics.

    Verdict precedence, in order — this is a faithful port and the order matters:

    1. More net-new ERROR-severity findings than fixed ones -> ``regressed``.
       Checked first, so a change that fixes ten warnings while introducing one
       new error is still a regression.
    2. Fixed something and introduced nothing -> ``improved``.
    3. Neither fixed nor introduced anything -> ``unchanged``.
    4. Otherwise -> ``mixed``.

    Note what falls out of this: warning-only churn can *never* produce
    ``regressed``. Trading warnings for warnings lands in ``mixed``.
    """
    diff = compare_findings(before, after, match_on=match_on)
    changed_metrics = [
        d for d in compare_metrics(before, after) if d.delta is not None and d.delta != 0
    ]

    if _count_errors(diff.introduced) > _count_errors(diff.fixed):
        verdict: Verdict = "regressed"
    elif diff.fixed and not diff.introduced:
        verdict = "improved"
    elif not diff.fixed and not diff.introduced:
        verdict = "unchanged"
    else:
        verdict = "mixed"

    return {
        "verdict": verdict,
        "findings": diff.to_json(),
        "changedMetrics": [d.to_json() for d in changed_metrics],
    }
