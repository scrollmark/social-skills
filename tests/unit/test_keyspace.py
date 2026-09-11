"""One authored list of key names, read rather than retyped.

The lists in `styles.py` and `formats.py` used to be literals, and
`scrollmark/editor` held a third copy in TypeScript. Three copies agreed only
because somebody remembered to change all three, and nothing would have said so
if they stopped agreeing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from video_studio.project import formats, keyspace, styles

STYLES_DIR = Path(__file__).resolve().parents[2] / "src" / "video_studio" / "styles"


def test_the_modules_read_the_file_rather_than_their_own_copy():
    """Every derived set is exactly its space. A literal that drifted back into
    one of these modules would show up here rather than at render time."""
    assert styles.CAPTION_KEYS == keyspace.space("caption")
    assert styles.CARD_KEYS == keyspace.space("cardStyle")
    assert styles.CARD_CONTENT_KEYS == keyspace.space("cardContent")
    assert styles.PLACEMENT_KEYS == keyspace.space("placement")
    assert styles.MUSIC_KEYS == keyspace.space("music")
    assert styles.RHYTHM_KEYS == keyspace.space("rhythm")
    assert formats.FORMAT_KEYS == keyspace.space("format")
    assert formats.ASPECTS == keyspace.enum("aspect")


def test_style_and_content_keys_never_overlap():
    """The invariant the split rests on.

    `card` is how a card looks and `cardContent` is what it says. If a name
    ever appeared in both, `validate` would report it as content and refuse a
    preset that was legitimately styling it -- so the two lists being disjoint
    is load-bearing, not tidiness.
    """
    assert keyspace.space("cardStyle") & keyspace.space("cardContent") == set()


def test_an_unknown_space_raises_rather_than_accepting_everything():
    """A space that quietly returned an empty set would accept every key and
    turn its validator into a formality."""
    with pytest.raises(KeyError, match="not a key space"):
        keyspace.space("no-such-space")
    with pytest.raises(KeyError, match="not an enum"):
        keyspace.enum("no-such-enum")


def test_a_preset_setting_card_content_is_told_which_mistake_it_made():
    """`heading` is a real card key used in the wrong place, not a typo, and
    saying "not a card key" sends someone hunting for a misspelling."""
    problems = styles.validate({"cards": {"title": {"heading": "TOKYO"}}})
    assert len(problems) == 1
    assert "CONTENT, not style" in problems[0]


def test_music_and_rhythm_are_checked_at_all():
    """They were not, until this change. Eleven presets set them, so a typo
    there was accepted in silence two keys away from checks that would have
    caught the same mistake anywhere else."""
    problems = styles.validate({"music": {"mood": ["warm"]}, "rhythm": {"fpss": 30}})
    assert problems == [
        "music.mood is not a music key",
        "rhythm.fpss is not a rhythm key",
    ]


def test_every_shipped_preset_still_validates():
    """The regression guard for widening validation: turning on `music` and
    `rhythm` must not have made any preset we ship invalid."""
    failures = {}
    for path in sorted(STYLES_DIR.glob("*.md")):
        block = re.search(r"```json\n(.*?)```", path.read_text(), re.S)
        if not block:
            continue
        problems = styles.validate(json.loads(block.group(1)))
        if problems:
            failures[path.stem] = problems
    assert failures == {}
