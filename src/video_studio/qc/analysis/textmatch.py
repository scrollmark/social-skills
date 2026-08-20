"""Text normalization + tolerant matching shared by OCR/whisper detectors.

Port of analyzer/ocr_util.py (minus the easyocr singleton, which lives in the
detectors that need it). word_error_rate upgraded from v1's O(n*m) Python
double loop to rapidfuzz's C++ Levenshtein — identical value, ~100-1000x
faster on paragraph-length narration.
"""

from __future__ import annotations

import re

_NORM_RE = re.compile(r"[^a-z0-9']")


def normalize_word(text: str) -> str:
    return _NORM_RE.sub("", text.lower())


def edit_distance_le1(a: str, b: str) -> bool:
    """True when levenshtein(a, b) <= 1 — tolerates one OCR misread."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = j = edits = 0
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1
            j += 1
            continue
        edits += 1
        if edits > 1:
            return False
        if la == lb:
            i += 1  # substitution
        j += 1  # insertion into a / deletion from b
    return edits + (lb - j) + (la - i) <= 1


def word_error_rate(ref: list[str], hyp: list[str]) -> float:
    """Standard Levenshtein WER. Same value as v1's DP matrix, via rapidfuzz."""
    if not ref:
        return 0.0 if not hyp else 1.0
    from rapidfuzz.distance import Levenshtein

    return Levenshtein.distance(ref, hyp) / len(ref)
