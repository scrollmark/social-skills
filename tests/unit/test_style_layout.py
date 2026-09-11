"""Where a preset puts its two pieces of type.

A preset states a title box as `cards.title.rect` -- `[x, y, w, h]` as
fractions of the frame -- and a caption band as `captions.bottom`, measured UP
from the bottom edge, so a larger number is higher on screen. Nothing had ever
compared the two, and two presets put the caption band inside the title box:
`pov-serif` ran its title to 0.62 and set captions at 0.535-0.560, and
`pov-quiet` ran its title to 0.56 and set captions at 0.555-0.580.

It stayed invisible because the two numbers live in different halves of the
file and neither is wrong on its own -- a mid-frame caption is the whole point
of a `pov` preset. It surfaced when the gallery preview started drawing both
where the preset asks rather than pinning the caption to the bottom edge, and
the thumbnail came out as one unreadable clump.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

STYLES = Path(__file__).resolve().parents[2] / "src" / "video_studio" / "styles"
# A caption is one line of type; its band is as tall as the type is. Presets
# state that size in pixels of a 1920-tall frame, which is the frame the rect
# fractions are of.
FRAME = 1920


def _presets() -> list[tuple[str, dict]]:
    out = []
    for path in sorted(STYLES.glob("*.md")):
        block = re.search(r"```json\n(.*?)```", path.read_text(), re.S)
        if block:
            out.append((path.stem, json.loads(block.group(1))))
    return out


def test_a_caption_never_lands_in_the_title_box():
    """The two pieces of type a preset places must not occupy the same band.

    Measured from the top edge so both are in the same terms: the title box is
    `y` to `y + h`, and the caption runs from `1 - bottom - size/FRAME` down to
    `1 - bottom`.
    """
    collisions = []
    for name, values in _presets():
        title = values.get("cards", {}).get("title", {})
        captions = values.get("captions", {})
        rect = title.get("rect")
        bottom = captions.get("bottom")
        if not (isinstance(rect, list) and len(rect) == 4):
            continue
        if not isinstance(bottom, (int, float)):
            continue
        box_top, box_bottom = rect[1], rect[1] + rect[3]
        band_bottom = 1 - bottom
        band_top = band_bottom - captions.get("fontSize", 56) / FRAME
        if band_top < box_bottom and band_bottom > box_top:
            collisions.append(
                f"{name}: title {box_top:.2f}-{box_bottom:.2f}, "
                f"caption {band_top:.3f}-{band_bottom:.3f}")
    assert not collisions, "caption band inside the title box: " + "; ".join(collisions)


def test_every_preset_places_its_caption():
    """`bottom` is what the composer reads; a preset without one is a preset
    whose caption position is whatever the default happens to be."""
    missing = [n for n, v in _presets()
               if not isinstance(v.get("captions", {}).get("bottom"), (int, float))]
    assert not missing, f"presets with no caption placement: {missing}"
