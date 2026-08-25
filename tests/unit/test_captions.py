"""Caption timing arithmetic.

burn_captions writes ASS karaoke tags, where each `\\k` value is a duration in
CENTISECONDS and the tags for a page must sum to that page's own length. Get it
wrong and the highlight drifts off the words — which looks like a styling
choice rather than a bug, and no tool reports it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"

WORDS = [("Honey", 0, 420), ("never", 480, 780), ("spoils.", 800, 1300),
         ("Archaeologists", 1900, 2700), ("found", 2720, 3000), ("pots", 3020, 3350)]


def _ass(tmp_path: Path, **flags) -> str:
    timings = tmp_path / "hook.timings.json"
    timings.write_text(json.dumps(
        [{"text": w, "startMs": s, "endMs": e} for w, s, e in WORDS]))
    out = tmp_path / "hook.ass"
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    extra = [x for k, v in flags.items() for x in (f"--{k.replace('_','-')}", str(v))]
    r = subprocess.run([sys.executable, "-m", "video_studio.cli", "burn_captions",
                        "--timings", str(timings), "--out", str(out), *extra],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr[-400:]
    return out.read_text()


def _dialogue_lines(ass: str) -> list[str]:
    return [l for l in ass.splitlines() if l.startswith("Dialogue:")]


def test_karaoke_tags_sum_to_each_page_duration(tmp_path):
    for line in _dialogue_lines(_ass(tmp_path)):
        start, end = line.split(",")[1], line.split(",")[2]

        def cs(t: str) -> int:
            h, m, rest = t.split(":")
            s, hundredths = rest.split(".")
            return ((int(h) * 3600 + int(m) * 60 + int(s)) * 100) + int(hundredths)

        page = cs(end) - cs(start)
        tags = sum(int(v) for v in re.findall(r"\\k(\d+)", line))
        assert tags == page, f"k-tags sum to {tags}cs, page is {page}cs\n{line}"


def test_a_page_never_exceeds_the_requested_word_count(tmp_path):
    ass = _ass(tmp_path, words_per_page=3)
    for line in _dialogue_lines(ass):
        # one k-tag per word, plus an optional leading gap tag per word
        words = len(re.findall(r"\\k\d+\}[^{\\]", line))
        assert words <= 3, f"page holds {words} words, asked for 3:\n{line}"


def test_colours_convert_to_ass_bgr(tmp_path):
    """ASS is &HAABBGGRR — reversed from hex. Swapping the bytes silently
    recolours every caption, and looks deliberate."""
    ass = _ass(tmp_path, highlight="#facc15")
    style = next(l for l in ass.splitlines() if l.startswith("Style: Caption"))
    assert "&H0015CCFA" in style, f"#facc15 should encode as &H0015CCFA:\n{style}"
