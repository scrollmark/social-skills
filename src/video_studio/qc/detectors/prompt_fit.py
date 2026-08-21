"""Prompt-fit scorecards: the video vs its CSV taxonomy row's eval target.

Deterministic by construction — checks are declarative predicates over the
metrics and findings other detectors already produced, defined in
data/checks.yaml. No LLM in the loop, so the score is reproducible; an
optional VLM judge can layer on later without touching this contract.

The taxonomy row resolves from AnalyzeOptions.taxonomy ("4.1"), else inferred
from the workdir topic against the vendored SocialBench CSV.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from importlib import resources
from typing import Any

from video_studio.qc.context import Context
from video_studio.qc.report.model import Finding

_EXPR_RE = re.compile(
    r"^(?P<neg>!)?(?P<kind>metric|finding):(?P<key>[A-Za-z0-9_.]+)"
    r"(?:\s*(?P<op>>=|<=|==|>|<)\s*(?P<value>-?[\d.]+))?$"
)


@dataclass(frozen=True)
class TaxonomyEntry:
    sub_no: str
    sub_name: str
    description: str
    eval_target: str


def load_taxonomy() -> dict[str, TaxonomyEntry]:
    text = resources.files("video_studio.qc.data").joinpath("taxonomy.csv").read_text()
    out: dict[str, TaxonomyEntry] = {}
    for row in csv.DictReader(text.splitlines()):
        sub_no = (row.get("Subcategory #") or "").strip()
        if not sub_no:
            continue
        out[sub_no] = TaxonomyEntry(
            sub_no=sub_no,
            sub_name=(row.get("Subcategory") or "").strip(),
            description=(row.get("Format Description") or "").strip(),
            eval_target=(row.get("LLM Evaluation Target") or "").strip(),
        )
    return out


def load_checks() -> dict[str, Any]:
    import yaml

    text = resources.files("video_studio.qc.data").joinpath("checks.yaml").read_text()
    return dict(yaml.safe_load(text))


def _eval(expr: str, metrics: dict[str, float], finding_keys: set[str]) -> tuple[bool, Any]:
    """Tiny closed grammar — never python eval."""
    m = _EXPR_RE.match(expr.strip())
    if m is None:
        raise ValueError(f"malformed check expr: {expr!r}")
    negated = bool(m.group("neg"))
    kind, key, op, raw = m.group("kind"), m.group("key"), m.group("op"), m.group("value")
    if kind == "finding":
        present = key in finding_keys
        return (not present if negated else present), present
    value = metrics.get(key)
    if value is None:
        return False, None  # missing metric: the check simply fails
    threshold = float(raw)
    key_abs = abs(value) if "offsetMs" in key or "lagMs" in key else value
    result = {
        ">": key_abs > threshold,
        ">=": key_abs >= threshold,
        "<": key_abs < threshold,
        "<=": key_abs <= threshold,
        "==": key_abs == threshold,
    }[op]
    return (not result if negated else result), value


def infer_subcategory(topic: str | None, plan_title: str | None) -> str | None:
    """Cheap inference from the workdir's own words — explicit --taxonomy wins."""
    text = f"{topic or ''} {plan_title or ''}".lower()
    hints = [
        ("asmr", "3.3"),
        ("duet", "4.1"),
        ("stitch", "4.1"),
        ("lip sync", "4.2"),
        ("lipsync", "4.2"),
        ("lip-sync", "4.2"),
        ("greenscreen", "2.1"),
        ("green screen", "2.1"),
        ("unboxing", "3.2"),
        ("haul", "3.2"),
        ("recipe", "3.1"),
        ("skit", "4.3"),
        ("roleplay", "4.3"),
    ]
    for needle, sub in hints:
        if needle in text:
            return sub
    return None


def run(ctx: Context) -> None:
    r = ctx.report
    gt = ctx.ground_truth

    sub_no = getattr(ctx, "taxonomy", None)
    source = "explicit"
    if sub_no is None and gt is not None:
        sub_no = infer_subcategory(gt.topic, gt.plan_title)
        source = "inferred"
    if sub_no is None:
        return  # nothing to score against; silence, not noise

    taxonomy = load_taxonomy()
    checks = load_checks()
    entry = taxonomy.get(sub_no)
    spec = checks.get(sub_no)
    if entry is None or spec is None:
        return

    r.taxonomy = {"subcategory": sub_no, "name": entry.sub_name, "source": source}

    metrics = dict(r.metrics)
    finding_keys = {f"{f.detector}.{f.code}" for f in r.findings}

    results = []
    total_weight = 0.0
    passed_weight = 0.0
    for check in spec.get("checks", []):
        weight = float(check.get("weight", 1))
        ok, value = _eval(check["expr"], metrics, finding_keys)
        total_weight += weight
        if ok:
            passed_weight += weight
        results.append(
            {
                "id": check["id"],
                "expr": check["expr"],
                "passed": ok,
                "value": value,
                "weight": weight,
            }
        )

    score = passed_weight / total_weight if total_weight else 0.0
    verdict = "pass" if score >= 0.8 else ("partial" if score >= 0.5 else "fail")
    r.scorecards.append(
        {
            "subcategory": sub_no,
            "name": entry.sub_name,
            "evalTarget": entry.eval_target[:200],
            "score": round(score, 3),
            "verdict": verdict,
            "checks": results,
        }
    )
    r.set_metric("promptFit.score", score)

    if verdict == "fail":
        failed = [c["id"] for c in results if not c["passed"]]
        r.add(
            Finding(
                "prompt_fit",
                "SUBCATEGORY_UNMET",
                "warning",
                f"Scores {score:.0%} against taxonomy {sub_no} ({entry.sub_name}) — "
                f"failing checks: {', '.join(failed)}",
                metrics={"score": round(score, 3)},
            )
        )
