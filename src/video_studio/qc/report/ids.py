"""Stable, content-derived finding identifiers.

Why this module exists
----------------------
The v1 analyzer built ids as ``<detector>.<code_lower>[:<sceneId>]`` and
disambiguated collisions **by position in the sorted finding list**: the second
occurrence became ``<id>:2``, the third ``<id>:3``.

That silently breaks the one thing the ids exist for. Run-over-run diffing
classifies findings as fixed / introduced / persisting by id, so if a *new*
finding appears that happens to sort earlier, every later duplicate shifts by
one suffix and the diff reports a cascade of phantom "fixed" and "introduced"
findings that nothing in the video actually changed.

The v2 grammar removes position from the id entirely::

    <detector>.<code_lower>[@<sceneId>][#<key>][~<hash6>]

- ``key`` is a *content-derived discriminator supplied by the detector* — the
  clipped string, the timestamp bucket, the object class. Two findings of the
  same code in the same scene are told apart by what they are about, not by
  what order they came out in.
- ``~hash6`` appears only when a key still collides, and is derived from that
  finding's *own* canonical content, so it does not depend on which other
  findings exist.

Every finding also carries an opaque ``fingerprint`` so consumers can diff
without parsing the id grammar at all.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

# Keys go in an id, so they must be filesystem/URL/grep-safe and stable across
# runs. Anything outside this set collapses to a hyphen.
_UNSAFE = re.compile(r"[^a-z0-9]+")

KEY_MAX_LEN = 24


def slug_key(text: str, max_len: int = KEY_MAX_LEN) -> str:
    """Normalize arbitrary text into a short, stable id fragment.

    Truncation is by *character count after normalization*, so a long string and
    its prefix collapse together — that is intentional: two OCR readings of the
    same clipped headline should share a key even if one caught trailing glyphs.
    """
    lowered = _UNSAFE.sub("-", text.strip().lower()).strip("-")
    if not lowered:
        return "none"
    return lowered[:max_len].rstrip("-")


def text_key(text: str) -> str:
    """Discriminator for a finding about a specific piece of text."""
    return slug_key(text)


def time_key(seconds: float, bucket_sec: float = 0.5) -> str:
    """Discriminator for a finding at a point in time.

    Quantized so that a detector that re-measures the same event a few
    milliseconds off across runs still produces the same key. Pick ``bucket_sec``
    to match the detector's own sampling resolution — too fine and the key
    flickers between runs, too coarse and distinct events merge.
    """
    return f"t{round(seconds / bucket_sec)}"


def class_key(name: str) -> str:
    """Discriminator for a finding about an object/entity class."""
    return slug_key(name)


def word_key(word: str) -> str:
    """Discriminator for a finding about a single caption/transcript word."""
    return slug_key(word)


def pane_key(rect: tuple[float, float, float, float]) -> str:
    """Discriminator for a finding about a layout pane.

    Rect is fractional (x, y, w, h). Quantized to 5% of the frame so a pane
    whose detected bounds wobble slightly keeps its identity.
    """
    x, y, w, h = (round(v * 20) for v in rect)
    return f"p{x}x{y}x{w}x{h}"


def track_key(track_id: int | str) -> str:
    """Discriminator for a finding about a tracked entity."""
    return f"k{track_id}"


def _canonical(payload: dict[str, Any]) -> str:
    """Deterministic JSON for hashing: sorted keys, no incidental whitespace."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _digest(payload: dict[str, Any], length: int) -> str:
    return hashlib.blake2s(_canonical(payload).encode("utf-8")).hexdigest()[:length]


def base_id(detector: str, code: str, scene_id: str | None, key: str | None) -> str:
    """The id without any collision suffix."""
    out = f"{detector}.{code.lower()}"
    if scene_id:
        out += f"@{scene_id}"
    if key:
        out += f"#{key}"
    return out


def fingerprint(detector: str, code: str, scene_id: str | None, key: str | None) -> str:
    """Opaque stable token for diffing without parsing the id grammar."""
    return _digest(
        {"d": detector, "c": code.lower(), "s": scene_id or "", "k": key or ""},
        8,
    )


def collision_suffix(
    *,
    message: str,
    span_sec: tuple[float, float] | None,
    metrics: dict[str, float] | None,
) -> str:
    """Content-derived tiebreaker for findings that still share a base id.

    Derived only from *this* finding's content, never from its position or from
    what else is in the report — which is the whole point. The span is rounded
    to 0.1s so a re-measurement that lands a few ms away keeps the same suffix.
    """
    span = None
    if span_sec is not None:
        span = [round(span_sec[0], 1), round(span_sec[1], 1)]
    return _digest(
        {
            "m": message,
            "s": span,
            "x": {k: round(v, 4) for k, v in sorted((metrics or {}).items())},
        },
        6,
    )


def resolve_ids(findings: list[Any]) -> dict[int, str]:
    """Assign a final id to every finding, adding ``~hash6`` only on collision.

    Takes objects exposing ``detector``/``code``/``scene_id``/``key``/``message``
    /``span_sec``/``metrics``. Returns ``{id(finding_object): final_id}``.

    Note the collision suffix is applied to *every* member of a colliding group,
    not just the second onward — otherwise removing the first member would
    rename the survivor.
    """
    groups: dict[str, list[Any]] = {}
    for finding in findings:
        base = base_id(finding.detector, finding.code, finding.scene_id, finding.key)
        groups.setdefault(base, []).append(finding)

    resolved: dict[int, str] = {}
    for base, group in groups.items():
        if len(group) == 1:
            resolved[id(group[0])] = base
            continue
        for finding in group:
            suffix = collision_suffix(
                message=finding.message,
                span_sec=finding.span_sec,
                metrics=finding.metrics,
            )
            resolved[id(finding)] = f"{base}~{suffix}"

    # Two findings with identical content in the same scene are genuinely
    # indistinguishable; de-duplicating them here would hide a detector bug, so
    # append an ordinal and let the contract test flag it.
    used: dict[str, int] = {}
    for finding in findings:
        current = resolved[id(finding)]
        count = used.get(current, 0) + 1
        used[current] = count
        if count > 1:
            resolved[id(finding)] = f"{current}.{count}"
    return resolved
