#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""Glowing-chalk animation: strokes draw themselves onto a chalkboard.

Two things separate this from `gen_boil.py`. Strokes REVEAL progressively —
each element has a window inside the scene and is drawn up to a fraction of
its own path length, so it reads as a hand writing rather than a shape
appearing. And every stroke gets a warm bloom: the line is rendered to its
own layer, blurred wide and soft, screened back under a crisp pass. Warm and
dusty, not neon — the blur is broad and low-opacity rather than tight and
bright, which is the whole difference between chalk-glow and a light tube.

Scene vocabulary lives in SCENES; each entry is a list of
(draw_fn, t_start, t_end) with times as fractions of the scene.
"""
import argparse
import math
import os
import random
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
BG = (17, 20, 24)
CHALK = (238, 240, 236)
AMBER = (244, 162, 97)
TEAL = (0, 201, 167)
PURPLE = (110, 68, 255)
DIM = 0.34                      # persistent background brightness


def mix(c, f):
    return tuple(int(BG[i] + (c[i] - BG[i]) * f) for i in range(3))


def resample(pts, seg=9):
    out = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / seg))
        for k in range(n):
            t = k / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append(pts[-1])
    return out


def chalk(d, pts, colour, width, p=1.0, seed=0, wob=1.6, closed=False):
    """Draw `pts` up to fraction p of its length, with hand-drawn wobble."""
    if p <= 0:
        return
    if closed:
        pts = list(pts) + [pts[0]]
    r = random.Random(seed)
    full = resample(pts)
    full = [(x + r.uniform(-wob, wob), y + r.uniform(-wob, wob)) for x, y in full]
    n = max(2, int(len(full) * min(1.0, p)))
    d.line(full[:n], fill=colour, width=width, joint="curve")


def circle(cx, cy, r, n=46):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
            for i in range(n + 1)]


def box(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]


# ----------------------------------------------------------------- furniture
def bg_world(d):
    """I-90 across the lower third and the Mitchell water tower, both dim."""
    c = mix(CHALK, DIM)
    chalk(d, [(0, H * 0.845), (W, H * 0.815)], c, 4, seed=11, wob=1.0)
    chalk(d, [(0, H * 0.945), (W, H * 0.915)], c, 4, seed=12, wob=1.0)
    for i in range(14):                                    # dashed centre line
        x0 = i * (W / 14) + 26
        y = H * 0.895 - (i / 14) * H * 0.028
        chalk(d, [(x0, y), (x0 + W / 30, y - 2)], c, 3, seed=20 + i, wob=0.8)
    # Mitchell water tower: cylindrical tank, shallow dome, conical underside,
    # splayed legs. Drawn as a silhouette outline so it reads at this size.
    tx, ty = W * 0.845, H * 0.545
    tw, th = 96, 104
    chalk(d, [(tx - tw, ty - th * .35), (tx - tw, ty + th * .30)], c, 4, seed=31)
    chalk(d, [(tx + tw, ty - th * .35), (tx + tw, ty + th * .30)], c, 4, seed=32)
    dome = [(tx - tw, ty - th * .35)] + \
           [(tx - tw + 2 * tw * i / 16, ty - th * .35 - 34 * math.sin(math.pi * i / 16))
            for i in range(17)] + [(tx + tw, ty - th * .35)]
    chalk(d, dome, c, 4, seed=33)
    chalk(d, [(tx - tw, ty + th * .30), (tx - 30, ty + th * .74)], c, 4, seed=34)
    chalk(d, [(tx + tw, ty + th * .30), (tx + 30, ty + th * .74)], c, 4, seed=35)
    chalk(d, [(tx - 30, ty + th * .74), (tx + 30, ty + th * .74)], c, 4, seed=36)
    for dx in (-64, -22, 22, 64):
        chalk(d, [(tx + dx * .42, ty + th * .74), (tx + dx, ty + 214)], c, 3, seed=40 + dx)
    chalk(d, [(tx - 52, ty + 150), (tx + 52, ty + 150)], c, 3, seed=44)
    try:
        f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
        tb = d.textbbox((0, 0), "MITCHELL", font=f)
        d.text((tx - (tb[2] - tb[0]) / 2, ty - 16), "MITCHELL", font=f, fill=c)
    except Exception:
        pass


def sparkle(d, p, seed=0):
    """Disco balls and wireframe cubes drifting in the upper corners."""
    r = random.Random(seed)
    for i in range(3):
        cx = W * (0.07 + 0.86 * (i % 2)) + math.sin(p * math.tau + i) * 14
        cy = H * (0.10 + 0.09 * (i % 3)) + math.cos(p * math.tau + i) * 10
        if i % 2:
            s = 26
            f = [(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy + s), (cx - s, cy + s)]
            b = [(x + 15, y - 15) for x, y in f]
            chalk(d, f, mix(PURPLE, 0.8), 3, seed=seed + i, closed=True)
            chalk(d, b, mix(PURPLE, 0.55), 2, seed=seed + i + 9, closed=True)
            for a_, b_ in zip(f, b):
                chalk(d, [a_, b_], mix(PURPLE, 0.5), 2, seed=seed + i + 20)
        else:
            chalk(d, circle(cx, cy, 24), mix(TEAL, 0.8), 3, seed=seed + i)
            for a in range(0, 180, 45):
                rad = math.radians(a)
                chalk(d, [(cx - 24 * math.cos(rad), cy - 24 * math.sin(rad)),
                          (cx + 24 * math.cos(rad), cy + 24 * math.sin(rad))],
                      mix(TEAL, 0.45), 2, seed=seed + a)


def eye(d, cx, cy, s, p, colour=CHALK, seed=77):
    """The oversight motif."""
    top = [(cx - s, cy), (cx - s * .45, cy - s * .62), (cx + s * .45, cy - s * .62), (cx + s, cy)]
    bot = [(cx + s, cy), (cx + s * .45, cy + s * .62), (cx - s * .45, cy + s * .62), (cx - s, cy)]
    chalk(d, top, colour, 6, min(1, p * 2.2), seed)
    chalk(d, bot, colour, 6, max(0, min(1, (p - 0.45) * 2.2)), seed + 1)
    if p > 0.72:
        q = (p - 0.72) / 0.28
        chalk(d, circle(cx, cy, s * .30), colour, 5, q, seed + 2)
        if q > 0.6:
            d.ellipse([cx - s * .12, cy - s * .12, cx + s * .12, cy + s * .12], fill=colour)


def figure(d, x, y, s, p, arm="up", clipboard=True, seed=90):
    """Stick figure; posture carries the expression."""
    chalk(d, circle(x, y - s * 1.30, s * 0.26), CHALK, 6, min(1, p * 3), seed)
    chalk(d, [(x, y - s * 1.04), (x, y - s * 0.25)], CHALK, 6, min(1, max(0, p * 3 - .5)), seed + 1)
    chalk(d, [(x, y - s * 0.25), (x - s * 0.34, y + s * 0.52)], CHALK, 6,
          min(1, max(0, p * 3 - 1.1)), seed + 2)
    chalk(d, [(x, y - s * 0.25), (x + s * 0.34, y + s * 0.52)], CHALK, 6,
          min(1, max(0, p * 3 - 1.1)), seed + 3)
    ax = {"up": (x - s * .52, y - s * 1.32), "out": (x - s * .62, y - s * .74),
          "side": (x - s * .40, y - s * .30)}[arm]
    chalk(d, [(x, y - s * 0.92), ax], CHALK, 6, min(1, max(0, p * 3 - .8)), seed + 4)
    chalk(d, [(x, y - s * 0.92), (x + s * .46, y - s * .52)], CHALK, 6,
          min(1, max(0, p * 3 - .8)), seed + 5)
    if clipboard and p > 0.55:
        q = min(1, (p - 0.55) / 0.4)
        chalk(d, box(x + s * .34, y - s * .66, s * .40, s * .52), CHALK, 5, q, seed + 6)
        chalk(d, [(x + s * .46, y - s * .70), (x + s * .62, y - s * .70)], TEAL, 4, q, seed + 7)


def tick(d, cx, cy, s, p, colour=TEAL, seed=5):
    chalk(d, [(cx - s, cy), (cx - s * .25, cy + s * .62), (cx + s, cy - s * .72)],
          colour, 6, p, seed)


# -------------------------------------------------------------------- scenes
def sc_hook(d, p):
    figure(d, W * 0.30, H * 0.74, 118, min(1, p / 0.30), arm="up")
    if p > 0.16:
        eye(d, W * 0.30, H * 0.30, 158, min(1, (p - 0.16) / 0.34))


def sc_check(d, p):
    x, y = W * 0.28, H * 0.70
    figure(d, x, y, 104, min(1, p / 0.4), arm="out")
    if p > 0.3:
        q = min(1, (p - 0.3) / 0.35)
        chalk(d, box(W * 0.46, H * 0.34, 210, 268), CHALK, 5, q, seed=201)
        tick(d, W * 0.46 + 105, H * 0.34 + 140, 34, max(0, (q - .6) / .4), TEAL, 202)
    if p > 0.5:
        q = min(1, (p - 0.5) / 0.35)
        chalk(d, box(W * 0.66, H * 0.34, 210, 268), CHALK, 5, q, seed=203)
        if q > .6:
            qq = (q - .6) / .4
            chalk(d, [(W * .66 + 78, H * .34 + 96), (W * .66 + 132, H * .34 + 96),
                      (W * .66 + 132, H * .34 + 146), (W * .66 + 105, H * .34 + 150)],
                  CHALK, 5, qq, seed=204)
            if qq > .8:
                d.ellipse([W * .66 + 98, H * .34 + 178, W * .66 + 112, H * .34 + 192], fill=CHALK)


def sc_rules(d, p):
    x0, y0 = W * 0.30, H * 0.30
    chalk(d, box(x0, y0, W * 0.44, H * 0.40), CHALK, 5, min(1, p / 0.30), seed=301)
    for i in range(3):
        s = 0.30 + i * 0.20
        if p > s:
            q = min(1, (p - s) / 0.16)
            ly = y0 + H * 0.115 + i * H * 0.12
            tick(d, x0 + 62, ly - 6, 30, max(0, (q - .35) / .5), TEAL, 320 + i)


def sc_decide(d, p):
    bx, by = W * 0.24, H * 0.42
    chalk(d, box(bx - 92, by - 78, 184, 156), PURPLE, 6, min(1, p / 0.22), seed=401)
    for i in range(3):
        chalk(d, [(bx - 52 + i * 52, by - 34), (bx - 52 + i * 52, by + 34)],
              mix(PURPLE, .8), 4, max(0, min(1, (p - .12) / .2)), seed=402 + i)
    if p > 0.26:
        q = min(1, (p - 0.26) / 0.22)
        chalk(d, [(bx + 118, by), (W * 0.52, by)], CHALK, 7, q, seed=410)
        if q > .75:
            chalk(d, [(W * .52 - 34, by - 24), (W * .52, by), (W * .52 - 34, by + 24)],
                  CHALK, 7, (q - .75) / .25, seed=411)
    figure(d, W * 0.62, H * 0.70, 112, min(1, max(0, (p - .30) / .22)), arm="side")
    for i, s in enumerate((0.62, 0.76)):
        if p > s:
            q = min(1, (p - s) / 0.14)
            cx = W * (0.80 + i * 0.10)
            chalk(d, circle(cx, H * 0.42, 44), CHALK, 5, q, seed=420 + i)
            tick(d, cx, H * 0.42, 24, max(0, (q - .55) / .45), TEAL, 430 + i)


def sc_map(d, p):
    pts = [(W * 0.22, H * 0.62), (W * 0.38, H * 0.52), (W * 0.54, H * 0.63), (W * 0.70, H * 0.53)]
    for i, (bx, by) in enumerate(pts):
        s = 0.10 + i * 0.13
        if p > s:
            q = min(1, (p - s) / 0.12)
            chalk(d, box(bx - 54, by - 44, 108, 88), CHALK, 5, q, seed=501 + i)
            chalk(d, [(bx - 54, by - 44), (bx, by - 84), (bx + 54, by - 44)], CHALK, 5, q, seed=511 + i)
            if q > .7:
                cs = 15
                cc = [(bx - cs, by + 118), (bx + cs, by + 118), (bx + cs, by + 148), (bx - cs, by + 148)]
                chalk(d, cc, PURPLE, 3, (q - .7) / .3, seed=521 + i, closed=True)
        if i and p > s:
            chalk(d, [pts[i - 1], (bx, by)], mix(CHALK, .6), 3,
                  min(1, (p - s) / 0.12), seed=531 + i)
    if p > 0.44:
        eye(d, W * 0.47, H * 0.235, 132, min(1, (p - 0.44) / 0.26))


def sc_timeline(d, p):
    y = H * 0.60
    chalk(d, [(W * 0.14, y), (W * 0.86, y)], CHALK, 5, min(1, p / 0.24), seed=601)
    for i in range(3):
        s = 0.22 + i * 0.20
        x = W * (0.24 + i * 0.26)
        if p > s:
            q = min(1, (p - s) / 0.14)
            chalk(d, [(x, y - 34), (x, y + 34)], CHALK, 5, q, seed=610 + i)
            if q > .6:
                rr = 13
                d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=TEAL, width=5)
    fx = W * (0.20 + 0.52 * min(1, max(0, (p - 0.24) / 0.62)))
    figure(d, fx, y - 46, 92, 1.0, arm="side")


def sc_truth(d, p):
    figure(d, W * 0.22, H * 0.72, 128, min(1, p / 0.20), arm="side")
    if p > 0.12:
        eye(d, W * 0.22, H * 0.28, 150, min(1, (p - 0.12) / 0.26))


def sc_close(d, p):
    sx, sy = W * 0.28, H * 0.46
    chalk(d, box(sx - 132, sy - 60, 264, 168), CHALK, 6, min(1, p / 0.3), seed=801)
    chalk(d, [(sx - 152, sy - 60), (sx, sy - 148), (sx + 152, sy - 60)], CHALK, 6,
          min(1, p / 0.3), seed=802)
    chalk(d, [(sx - 16, sy - 156), (sx - 16, sy - 196)], CHALK, 4, min(1, p / 0.3), seed=803)
    if p > 0.28:
        q = min(1, (p - 0.28) / 0.34)
        cx, cy = W * 0.62, H * 0.48
        chalk(d, box(cx - 148, cy - 96, 296, 192), CHALK, 5, q, seed=810)
        for i in range(3):
            chalk(d, [(cx - 104, cy - 40 + i * 40), (cx + 62, cy - 40 + i * 40)],
                  mix(CHALK, .7), 3, max(0, min(1, (q - .35 - i * .12) / .3)), seed=820 + i)
        if q > .8:
            d.ellipse([cx + 84, cy + 40, cx + 116, cy + 72], outline=TEAL, width=5)


SCENES = {"hook": sc_hook, "check": sc_check, "rules": sc_rules, "decide": sc_decide,
          "map": sc_map, "timeline": sc_timeline, "truth": sc_truth, "close": sc_close}


def render(scene, seconds, out, seed=1):
    fn = SCENES[scene]
    n = int(seconds * FPS)
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
         "-crf", "18", "-pix_fmt", "yuv420p", out],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for i in range(n):
        p = i / max(1, n - 1)
        ink = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(ink)
        bg_world(d)
        sparkle(d, p, seed)
        fn(d, p)
        # warm bloom: wide, soft, low — a tight bright blur reads as neon
        glow = ink.filter(ImageFilter.GaussianBlur(17)).point(lambda v: int(v * 0.62))
        glow2 = ink.filter(ImageFilter.GaussianBlur(41)).point(lambda v: int(v * 0.34))
        frame = Image.new("RGB", (W, H), BG)
        frame = ImageChops.add(frame, glow)
        frame = ImageChops.add(frame, glow2)
        frame = ImageChops.add(frame, ink)
        enc.stdin.write(frame.tobytes())
    enc.stdin.close()
    enc.wait()
    if enc.returncode:
        sys.exit(enc.stderr.read().decode()[-800:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    if a.scene not in SCENES:
        ap.error(f"unknown scene {a.scene!r}; have {' '.join(sorted(SCENES))}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    render(a.scene, a.seconds, a.out, a.seed)
    print(f'{{"out": "{a.out}", "scene": "{a.scene}", "seconds": {a.seconds}}}')


if __name__ == "__main__":
    main()
