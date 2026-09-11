"""The key names a preset, a format and a storyboard card may use.

One authored file, ``keyspace.json``, read by everything that validates against
it. Before this, ``styles.py`` and ``formats.py`` each held their own literals
and ``scrollmark/editor`` held a third copy in TypeScript -- three lists that
agreed only because somebody remembered to change all three.

Read from disk at import: no build step, no network, and the editor's toolchain
never has to run Python. The editor generates ``packs/keyspace.generated.ts``
from this same file and a CI job fails when the two drift.

Only names and closed value sets live here. Types, units and the reasoning
behind them stay on whichever side needs them -- generating zod constraints
from this would produce a worse version of something that already works.
"""

from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parent / "keyspace.json"

_DATA = json.loads(PATH.read_text())

VERSION: str = _DATA["version"]


def space(name: str) -> set[str]:
    """The key names in one space.

    Raises rather than returning an empty set for an unknown name: a space that
    silently has no keys accepts everything, which turns a validator into a
    formality and is the failure this whole file exists to prevent.
    """
    try:
        return set(_DATA["spaces"][name]["keys"])
    except KeyError:
        raise KeyError(
            f"{name} is not a key space in {PATH.name}; "
            f"known: {', '.join(sorted(_DATA['spaces']))}"
        ) from None


def enum(name: str) -> set[str]:
    """The permitted values of one closed set."""
    try:
        return set(_DATA["enums"][name]["values"])
    except KeyError:
        raise KeyError(
            f"{name} is not an enum in {PATH.name}; "
            f"known: {', '.join(sorted(_DATA['enums']))}"
        ) from None
