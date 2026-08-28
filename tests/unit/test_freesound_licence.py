"""The Freesound licence filter, against the strings Freesound actually sends.

Freesound's API returns `license` as a URL. The original filter matched display
names — "Creative Commons 0", "Attribution" — which no response contains, so
`acceptable()` returned False for every sound ever returned and the script
reported "no acceptably-licensed result" for every query, whatever was
searched. Nothing errored; the filter simply rejected the world.

The licence strings below are the real forms Freesound serves.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from video_studio.sourcing.stock_freesound import acceptable  # noqa: E402

CC0 = "http://creativecommons.org/publicdomain/zero/1.0/"
BY = "http://creativecommons.org/licenses/by/4.0/"
BY_3 = "http://creativecommons.org/licenses/by/3.0/"
BY_NC = "http://creativecommons.org/licenses/by-nc/4.0/"
BY_NC_3 = "http://creativecommons.org/licenses/by-nc/3.0/"
SAMPLING = "http://creativecommons.org/licenses/sampling+/1.0/"


@pytest.mark.parametrize("lic", [CC0])
def test_public_domain_is_accepted_by_default(lic):
    assert acceptable(lic, False) is True
    assert acceptable(lic, True) is True


@pytest.mark.parametrize("lic", [BY, BY_3])
def test_attribution_needs_the_flag(lic):
    assert acceptable(lic, False) is False
    assert acceptable(lic, True) is True


@pytest.mark.parametrize("lic", [BY_NC, BY_NC_3])
def test_noncommercial_is_never_accepted(lic):
    """The ordering trap: "licenses/by-nc/4.0/" contains "licenses/by".

    Checking attribution before non-commercial would accept exactly the
    licences this script exists to refuse — and it would do so only when
    --allow-attribution was passed, so the default path would look fine.
    """
    assert acceptable(lic, False) is False
    assert acceptable(lic, True) is False


def test_sampling_plus_is_not_mistaken_for_free():
    assert acceptable(SAMPLING, False) is False
    assert acceptable(SAMPLING, True) is False


@pytest.mark.parametrize("lic", ["Creative Commons 0", "Attribution", "Attribution Noncommercial"])
def test_display_names_still_work(lic):
    """Kept deliberately: if the field ever reverts to display names, the
    filter must not empty itself again."""
    expected = {"Creative Commons 0": (True, True),
                "Attribution": (False, True),
                "Attribution Noncommercial": (False, False)}[lic]
    assert (acceptable(lic, False), acceptable(lic, True)) == expected


def test_empty_and_none_are_rejected():
    for lic in ("", None):
        assert acceptable(lic, False) is False
        assert acceptable(lic, True) is False
