#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""Draw a "boil" clip — hand-drawn-looking outlined vector art that jitters.

    video-studio gen_boil --shape chip --seconds 6 \
        --out projects/foo/clips/beat2-still.mp4 --bg "#0b0e20" --fg "#8f9bf0"

Why draw instead of generate: a video generator cannot hold a clean
single-weight outline — the line thickness crawls, corners melt, and any
repeated shape drifts between shots. Boil is trivial to synthesise instead.
You draw the same shape with every vertex nudged a pixel or two, then HOLD
each drawing for a few frames. The hold is the whole trick: on 3s (10
drawings/sec at 30fps) reads as hand-drawn, while a fresh jitter every frame
reads as video noise.

Costs nothing, has no licence attached, and is deterministic — same seed,
same clip, so a re-render never shifts under an edit.

Shapes: rings, laptop, tag, chip, battery, feather, ring, bars, arrow, blank.
Use --list to print them. `blank` is a flat background for text-only beats.
Project-local marks can be loaded with --shape-file; define functions named
s_<shape>(d, c, rng, w, p, cx, cy, s) and use the same wob/circle/box helpers.
Such a file may ONLY define those functions: it is checked before it runs, and
no imports, no module-level statements, no dunder attributes and no
eval/exec/open are permitted anywhere in it. `math` and the drawing helpers are
injected, so nothing legitimate needs an import. See check_shape_source.
"""
import argparse
import ast
import json
import math
import os
import random
import subprocess
import sys
from pathlib import Path

FPS = 30


def jit(pts, amp, rng):
    return [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in pts]


def wob(d, pts, colour, rng, w, amp=3.0, seg=26):
    """Polyline resampled to short segments, each vertex nudged."""
    out = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / seg))
        for k in range(n):
            t = k / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append(pts[-1])
    d.line(jit(out, amp, rng), fill=colour, width=w, joint="curve")


def circle(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
            for i in range(n + 1)]


def box(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]


# Each shape draws into a unit-ish area around (cx, cy); `s` scales it.
def s_rings(d, c, rng, w, p, cx, cy, s):
    for i in range(4):
        wob(d, circle(cx, cy, s * (0.34 + i * 0.30) * (1 - 0.08 * p)), c, rng, w, 3.4)


def s_laptop(d, c, rng, w, p, cx, cy, s):
    bw, bh = s * 1.15, s * 0.72
    ang = math.radians(18 + 62 * min(1.0, p * 1.6))
    wob(d, [(cx - bw / 2, cy), (cx + bw / 2, cy),
            (cx + bw / 2 - bh * math.cos(ang) * 0.20, cy - bh * math.sin(ang)),
            (cx - bw / 2 - bh * math.cos(ang) * 0.20, cy - bh * math.sin(ang)),
            (cx - bw / 2, cy)], c, rng, w)
    wob(d, [(cx - bw / 2 - s * .09, cy), (cx + bw / 2 + s * .09, cy),
            (cx + bw / 2 + s * .15, cy + s * .075), (cx - bw / 2 - s * .15, cy + s * .075),
            (cx - bw / 2 - s * .09, cy)], c, rng, w)


def s_tag(d, c, rng, w, p, cx, cy, s):
    a = s * 0.42 + math.sin(p * math.tau) * 4
    wob(d, [(cx - a, cy - a * .62), (cx + a * .45, cy - a * .62), (cx + a, cy),
            (cx + a * .45, cy + a * .62), (cx - a, cy + a * .62), (cx - a, cy - a * .62)],
        c, rng, w)
    wob(d, circle(cx + a * .52, cy, s * .058), c, rng, w, 2.2)


def s_chip(d, c, rng, w, p, cx, cy, s):
    a = s * 0.42
    wob(d, box(cx - a, cy - a, a * 2, a * 2), c, rng, w)
    wob(d, box(cx - a * .52, cy - a * .52, a * 1.04, a * 1.04), c, rng, w, 2.4)
    for i in range(5):
        o = -a * .66 + i * a * .33
        for p0, p1 in (((cx + o, cy - a), (cx + o, cy - a - s * .13)),
                       ((cx + o, cy + a), (cx + o, cy + a + s * .13)),
                       ((cx - a, cy + o), (cx - a - s * .13, cy + o)),
                       ((cx + a, cy + o), (cx + a + s * .13, cy + o))):
            wob(d, [p0, p1], c, rng, w, 2.6, 18)


def s_battery(d, c, rng, w, p, cx, cy, s):
    bw, bh = s * .93, s * .47
    wob(d, box(cx - bw / 2, cy - bh / 2, bw, bh), c, rng, w)
    wob(d, box(cx + bw / 2, cy - bh * .2, s * .075, bh * .4), c, rng, w, 2.2)
    fill = .55 + .35 * (.5 + .5 * math.sin(p * math.tau))
    wob(d, box(cx - bw / 2 + s * .033, cy - bh / 2 + s * .033,
               (bw - s * .066) * fill, bh - s * .066), c, rng, w, 2.6)


def s_feather(d, c, rng, w, p, cx, cy, s):
    a, b = (cx - s * .30, cy + s * .34), (cx + s * .30, cy - s * .30)
    wob(d, [a, b], c, rng, w, 2.4)
    for i in range(9):
        t = i / 8
        bx, by = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        ln = s * .17 * (1 - .55 * t)
        wob(d, [(bx, by), (bx - ln * .35, by + ln)], c, rng, w, 2.0, 14)


def s_ring(d, c, rng, w, p, cx, cy, s):
    wob(d, circle(cx, cy, s * .34 + math.sin(p * math.tau) * 5), c, rng, w, 2.8)


def s_bars(d, c, rng, w, p, cx, cy, s):
    for i in range(4):
        hgt = s * (.18 + .17 * i) * (.75 + .25 * math.sin(p * math.tau + i))
        x = cx - s * .40 + i * s * .26
        wob(d, box(x, cy + s * .34 - hgt, s * .17, hgt), c, rng, w, 2.6)


def s_arrow(d, c, rng, w, p, cx, cy, s):
    tip = cx - s * .3 + s * .6 * p
    wob(d, [(cx - s * .42, cy), (tip, cy)], c, rng, w, 2.6)
    wob(d, [(tip - s * .1, cy - s * .08), (tip, cy), (tip - s * .1, cy + s * .08)], c, rng, w, 2.4)


def s_blank(d, c, rng, w, p, cx, cy, s):
    return


SHAPES = {"rings": s_rings, "laptop": s_laptop, "tag": s_tag, "chip": s_chip,
          "battery": s_battery, "feather": s_feather, "ring": s_ring,
          "bars": s_bars, "arrow": s_arrow, "blank": s_blank}


#: Builtins a drawing function plausibly needs. Everything else — including
#: `open`, `eval`, `exec`, `compile`, `__import__`, `getattr` and `globals` —
#: is absent from the namespace a shape file runs in.
SAFE_BUILTINS = {
    name: __builtins__[name] if isinstance(__builtins__, dict)
    else getattr(__builtins__, name)
    for name in (
        "abs", "all", "any", "bool", "divmod", "enumerate", "filter", "float",
        "int", "len", "list", "map", "max", "min", "pow", "range", "reversed",
        "round", "set", "sorted", "str", "sum", "tuple", "zip", "print", "repr",
        "IndexError", "TypeError", "ValueError", "ZeroDivisionError",
    )
}

#: Names that turn a drawing file into a general-purpose program. Rejected
#: anywhere in the file, not just at module level: shape functions run when
#: they are DRAWN, so a check that only read the top level would pass a file
#: whose payload sits inside `s_something`.
FORBIDDEN_NAMES = frozenset({
    "__import__", "eval", "exec", "compile", "open", "input", "breakpoint",
    "globals", "locals", "vars", "getattr", "setattr", "delattr", "memoryview",
    "exit", "quit", "help",
})


def check_shape_source(source, path):
    """Reject a shape file that does more than define shapes.

    A shape file is Python because a bespoke mark is faster to draw than to
    describe in a tiny DSL. That was a safe trade while this ran from a private
    checkout. It is not one now: `boil.md` tells an agent to WRITE these files,
    so text arriving in a brief can reach this function, and the file used to
    execute in full the moment it was loaded — every check on what it defined
    ran afterwards, when any top-level code had already had its turn.

    So: module level may hold a docstring, function definitions, and plain
    assignments (a `SHAPES` dict). No imports, no calls, no class definitions.
    Nowhere in the file may there be a dunder attribute (`__class__`,
    `__globals__` and the rest of the usual traversal to the interpreter) or a
    name from FORBIDDEN_NAMES.

    This is a GUARD, NOT A SANDBOX, and the difference matters: it stops a
    shape file from being a program, and it is not a boundary to run hostile
    code behind. Anyone who can write this file can usually write the
    storyboard next to it.
    """
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise SystemExit(f"{path}:{exc.lineno}: shape file does not parse — {exc.msg}")

    problems = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Assign,
                             ast.AnnAssign)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            continue  # module docstring
        problems.append(
            f"line {node.lineno}: {type(node).__name__} at module level — a shape "
            f"file may only define functions (and a SHAPES dict)"
        )

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            problems.append(
                f"line {node.lineno}: import — `math` and the drawing helpers "
                f"`wob`, `circle`, `box` are injected already"
            )
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            problems.append(f"line {node.lineno}: attribute {node.attr!r}")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            problems.append(f"line {node.lineno}: {node.id!r}")

    if problems:
        raise SystemExit(
            f"{path} is not a shape file — it does things a drawing does not "
            f"need to do:\n  " + "\n  ".join(problems[:10])
            + (f"\n  ... and {len(problems) - 10} more" if len(problems) > 10 else "")
            + "\n\nA shape file defines `s_<name>(d, c, rng, w, p, cx, cy, s)` "
              "functions and nothing else.\nIf this file is yours and you meant "
              "it, it belongs in its own script, not behind --shape-file."
        )


def load_shape_file(path):
    """Load project-local shape functions, after checking they are only that.

    Compiles the source read here rather than handing the path to an importer,
    so the bytes that were checked are the bytes that run — no window between
    the two in which the file could change.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"shape file does not exist: {path}")

    source = path.read_text(encoding="utf-8")
    check_shape_source(source, path)

    namespace = {
        "__builtins__": SAFE_BUILTINS,
        "__name__": f"boil_shapes_{path.stem}",
        "math": math, "wob": wob, "circle": circle, "box": box,
    }
    exec(compile(source, str(path), "exec"), namespace)

    explicit = namespace.get("SHAPES")
    if explicit is not None:
        if not isinstance(explicit, dict):
            raise TypeError(f"{path}: SHAPES must be a dict")
        shapes = explicit
    else:
        shapes = {
            name[2:]: fn
            for name, fn in namespace.items()
            if name.startswith("s_") and callable(fn)
        }
    if not shapes:
        raise ValueError(f"{path}: define s_<name>(...) functions or a SHAPES dict")
    bad = [name for name in shapes if not name or not name.replace("_", "").replace("-", "").isalnum()]
    if bad:
        raise ValueError(f"{path}: invalid shape name(s): {', '.join(sorted(bad))}")
    return shapes


def shape_registry(shape_files):
    shapes = dict(SHAPES)
    for path in shape_files or []:
        custom = load_shape_file(path)
        collisions = sorted(set(shapes) & set(custom))
        if collisions:
            raise ValueError(f"{path}: custom shape name already exists: {', '.join(collisions)}")
        shapes.update(custom)
    return shapes


def render(shape, shapes, seconds, out, bg, fg, size, hold, stroke, pos, scale, seed):
    from PIL import Image, ImageDraw

    W, H = size
    n = int(seconds * FPS)
    fn = shapes[shape]
    cx, cy = W * pos[0], H * pos[1]
    s = min(W, H) * scale
    enc = subprocess.Popen(
        # The colour tags are not decoration. Frames arrive here as raw RGB with
        # no signalling of their own, so without them the file carries
        # colour_range/space/primaries/trc as "unknown" — where stock footage
        # and camera files say tv/bt709. A player then has to guess, and
        # different players guess differently: Remotion's OffthreadVideo reads
        # an untagged clip as full-range and lifts it, so generated shots sit
        # visibly brighter than the real footage they are cut against.
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
         "-crf", "18", "-pix_fmt", "yuv420p",
         "-color_range", "tv", "-colorspace", "bt709",
         "-color_primaries", "bt709", "-color_trc", "bt709",
         # The generic flags alone are not enough: on ffmpeg 9 with libx264
         # they set range and matrix, and primaries and transfer still probe as
         # "unknown". x264 has to be told directly before it writes them into
         # the bitstream. Both are kept — the container atom and the bitstream
         # VUI are not read by the same players.
         "-x264-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709",
         out],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    frame = None
    for i in range(n):
        if i % hold == 0:
            rng = random.Random(seed + i // hold)
            img = Image.new("RGB", (W, H), bg)
            try:
                fn(ImageDraw.Draw(img), fg, rng, stroke, i / max(1, n - 1), cx, cy, s)
            except NameError as exc:
                # Custom shapes run with a trimmed builtins namespace, so a name
                # that exists in ordinary Python can be missing here. Say that,
                # rather than leaving a bare NameError that reads like a typo.
                raise SystemExit(
                    f"shape {shape!r} used {exc.name!r}, which is not available to "
                    f"shape files.\nThey run with a reduced set of builtins — "
                    f"arithmetic, sequences and the injected `math`, `wob`, "
                    f"`circle`, `box`.\nIf the drawing genuinely needs more than "
                    f"that, it belongs in its own script."
                ) from None
            frame = img.tobytes()
        enc.stdin.write(frame)
    enc.stdin.close()
    enc.wait()
    if enc.returncode:
        sys.exit(enc.stderr.read().decode()[-800:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shape", default="rings")
    ap.add_argument("--shape-file", action="append", default=[],
                    help="Python file defining project-local s_<name> shape functions")
    ap.add_argument("--seconds", type=float, default=6)
    ap.add_argument("--out")
    ap.add_argument("--bg", default="#0a0a0c")
    ap.add_argument("--fg", default="#f5f5f7")
    ap.add_argument("--aspect", choices=["16:9", "9:16"], default="16:9")
    ap.add_argument("--hold", type=int, default=3, help="frames per drawing; 3 = 'on 3s'")
    ap.add_argument("--stroke", type=int, default=7)
    ap.add_argument("--pos", default="0.5,0.5", help="centre as fractions, e.g. 0.72,0.44")
    ap.add_argument("--scale", type=float, default=0.55, help="of the short edge")
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    try:
        shapes = shape_registry(a.shape_file)
    except Exception as e:
        ap.error(str(e))
    if a.list:
        print(" ".join(sorted(shapes)))
        return
    if not a.out:
        ap.error("--out is required")
    if a.shape not in shapes:
        ap.error(f"unknown shape {a.shape!r}; try --list")
    size = (1920, 1080) if a.aspect == "16:9" else (1080, 1920)
    pos = tuple(float(v) for v in a.pos.split(","))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    render(a.shape, shapes, a.seconds, a.out, a.bg, a.fg, size, a.hold, a.stroke, pos, a.scale, a.seed)
    print(json.dumps({"out": a.out, "shape": a.shape, "seconds": a.seconds, "hold": a.hold}))


if __name__ == "__main__":
    main()
