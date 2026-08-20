"""Split-screen / multi-pane composition + chromakey QC. Pure CV, no new deps.

Targets 4.1 (duet: two independent panes) and 2.1 (greenscreen speaker over
content). Seam detection: a persistent, full-height ridge in the temporal
mean of |Sobel_x| column profiles. Independence: cross-correlation of the two
panes' motion-energy series — a wall edge inside one continuous shot moves
WITH both sides; a real duet seam separates sides that move independently.

When the plan carries composite `layers`, declared chromakey/pip rects become
checkable ground truth (KEY_SPILL, PANE findings). New detector, no v1
counterpart, excluded from parity.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from video_studio.qc.context import Context
from video_studio.qc.report import ids
from video_studio.qc.report.model import Finding

SEAM_PERSISTENCE = 0.8  # ridge must be present in this fraction of frames
SEAM_PROMINENCE = 2.5  # x the local median edge energy
INDEPENDENT_BELOW = 0.35  # pane motion correlation under this = separate sources
EDGE_MARGIN_FRAC = 0.08  # ignore ridges hugging the frame edge
KEY_SPILL_WARN = 0.10  # fraction of pane pixels within the key hue


def _find_seam(profiles: np.ndarray) -> tuple[int, float] | None:
    """profiles: (frames, width) of per-column |Sobel_x| means. Returns
    (column, persistence) of the strongest persistent interior ridge."""
    if profiles.ndim != 2 or profiles.shape[0] < 3:
        return None
    width = profiles.shape[1]
    margin = max(2, int(width * EDGE_MARGIN_FRAC))
    interior = slice(margin, width - margin)
    median_energy = np.median(profiles, axis=1, keepdims=True) + 1e-9
    prominent = profiles[:, interior] > SEAM_PROMINENCE * median_energy
    persistence = prominent.mean(axis=0)
    best = int(np.argmax(persistence))
    if persistence[best] < SEAM_PERSISTENCE:
        return None
    return best + margin, float(persistence[best])


def _pane_motion_correlation(block_energy: np.ndarray, seam_col_frac: float) -> float | None:
    """block_energy: (frames, blocks_x) column-block motion energy. Correlate
    the summed left-of-seam vs right-of-seam series."""
    if block_energy.ndim != 2 or block_energy.shape[0] < 5:
        return None
    split = round(seam_col_frac * block_energy.shape[1])
    split = min(max(split, 1), block_energy.shape[1] - 1)
    left = block_energy[:, :split].sum(axis=1)
    right = block_energy[:, split:].sum(axis=1)
    left = left - left.mean()
    right = right - right.mean()
    denom = np.linalg.norm(left) * np.linalg.norm(right)
    if denom < 1e-9:
        return None
    return float(np.dot(left, right) / denom)


def run(ctx: Context) -> None:
    r = ctx.report
    gt = ctx.ground_truth
    stats = ctx.artifacts.pane_stats
    assert stats is not None, "engine must run the pane service before composition"

    col_profiles = np.array(stats.column_profiles)
    block_energy = np.array(stats.block_energies)

    pane_count = 1
    seam = _find_seam(col_profiles)
    if seam is not None:
        col, persistence = seam
        width = col_profiles.shape[1]
        frac = col / width
        correlation = _pane_motion_correlation(block_energy, frac)
        r.set_metric("composition.seamPersistence", persistence)
        if correlation is not None:
            r.set_metric("composition.paneMotionCorrelation", correlation)
        if correlation is not None and correlation < INDEPENDENT_BELOW:
            pane_count = 2
            r.add(
                Finding(
                    "composition",
                    "SPLIT_SCREEN_DETECTED",
                    "info",
                    f"Persistent vertical seam at {frac:.0%} of frame width with "
                    f"independently-moving sides (motion correlation {correlation:.2f}) — "
                    "a genuine two-pane composition",
                    key=ids.pane_key((frac, 0.0, 1 - frac, 1.0)),
                    metrics={
                        "seamFrac": round(frac, 3),
                        "motionCorrelation": round(correlation, 3),
                    },
                )
            )
    r.set_metric("composition.paneCount", pane_count)

    # Ground truth from composite layers, when declared.
    if gt is None:
        return
    declared: list[tuple[str, str, Any, Any]] = []  # (scene, layer, role, extra)
    for scene in gt.scenes:
        raw = _plan_layers(gt, scene.id)
        for layer in raw:
            declared.append((scene.id, str(layer.get("id")), layer.get("role"), layer))

    stacked = [d for d in declared if d[2] in ("hstack", "vstack")]
    if stacked and pane_count < 2:
        scene_id, layer_id = stacked[0][0], stacked[0][1]
        r.add(
            Finding(
                "composition",
                "MISSING_PANE",
                "warning",
                f"The plan declares stacked layers (e.g. '{layer_id}' in scene "
                f"'{scene_id}') but no persistent independent pane seam was detected — "
                "the composition may have collapsed to a single stream",
                scene_id=scene_id,
            )
        )

    chroma = [d for d in declared if d[2] == "chromakey"]
    if chroma and stats.key_hue_fractions:
        spill = float(np.median(stats.key_hue_fractions))
        r.set_metric("composition.keySpillFraction", spill)
        if spill > KEY_SPILL_WARN:
            scene_id = chroma[0][0]
            r.add(
                Finding(
                    "composition",
                    "KEY_SPILL",
                    "warning",
                    f"A median {spill:.0%} of frame pixels sit within the chroma-key hue — "
                    "green spill or an unkeyed region survived the composite",
                    scene_id=scene_id,
                    metrics={"spillFraction": round(spill, 3)},
                    rubric_dimension="visual-quality",
                )
            )


def _plan_layers(gt: Any, scene_id: str) -> list[dict[str, Any]]:
    import json

    try:
        plan = json.loads((gt.workdir / "plan.json").read_text())
    except Exception:
        return []
    for scene in plan.get("scenes", []):
        if scene.get("id") == scene_id:
            return scene.get("layers") or []
    return []
