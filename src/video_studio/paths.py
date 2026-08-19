"""Where the studio's data actually lives.

Every script in the original tree sat at ``<root>/scripts/<name>.py``, so
``Path(__file__).resolve().parent.parent`` was the studio root: the directory
holding ``composer/``, ``formats/``, ``styles/``, ``tutorials/``, ``projects/``
and ``.env``.  That expression is a lie inside an installed package — it points
at ``site-packages/video_studio`` — and it lies *quietly*, which is worse: the
scripts would go on running and simply find nothing.

So the derivation moves here, and becomes explicit:

1. ``$VIDEO_STUDIO_ROOT`` if it is set. This is the answer whenever the studio
   tree is not an ancestor of the working directory, and the only answer that
   works for an installed-from-PyPI copy.
2. Otherwise walk up from the current working directory looking for a marker —
   a ``composer/``, ``formats/`` or ``projects/`` directory, or a
   ``.video-studio`` file. Running from inside the tree therefore keeps working
   with no configuration, which is how these scripts are actually invoked.
3. Otherwise the current working directory, so that a first run in an empty
   directory creates its scaffolding where the user is standing rather than
   inside the installed package.

``studio_root()`` never raises and never creates anything.
"""

from __future__ import annotations

import os
from pathlib import Path

#: A directory is the studio root if it contains any one of these.
MARKERS = ("composer", "formats", "projects", ".video-studio")

ENV_VAR = "VIDEO_STUDIO_ROOT"


def find_root(start: Path | None = None) -> Path | None:
    """Walk up from *start* (default: cwd) and return the first marked dir."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        for marker in MARKERS:
            if (candidate / marker).exists():
                return candidate
    return None


def studio_root(start: Path | None = None) -> Path:
    """The studio root: env var, then an upward search, then the cwd."""
    override = os.environ.get(ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()
    found = find_root(start)
    return found if found is not None else Path.cwd().resolve()


# The original scripts named this SKILL_ROOT. Kept as an alias so the diff
# against the source tree stays one line per file.
skill_root = studio_root
