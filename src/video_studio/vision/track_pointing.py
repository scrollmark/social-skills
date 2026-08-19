# /// script
# requires-python = ">=3.11"
# dependencies = ["mediapipe>=0.10", "numpy"]
# ///
# Uses mediapipe's Tasks API (HandLandmarker): the legacy bundled-model
# `solutions` API is absent from recent wheels on this platform (verified —
# same finding showwatcher's face service documents). The ~8MB
# hand_landmarker.task model downloads once to ~/.cache/video-studio/.
"""Track pointing gestures in footage → timed popup-layer JSON.

Analysis (MediaPipe Hands, bundled models — no downloads):

  uv run scripts/track_pointing.py analyze --in me.mp4 --out events.json

Emits pointing EVENTS: windows where an extended index finger holds a
stable position, with the pointed-AT location (fingertip extrapolated
along the finger's direction), as canvas fractions:

  [{"startMs": 1200, "endMs": 2400, "x": 0.22, "y": 0.31}, ...]

Layer emission (deterministic geometry — offset away from the point
toward frame center, clamped on-canvas):

  uv run scripts/track_pointing.py layers --events events.json \
      --images product.png,chart.png [--size 0.30]

Prints storyboard-ready layers (file: sources, rect, atMs/untilMs,
pop) to paste into the scene — images are assigned to events in order,
cycling if there are more events than images.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

# Hand landmark indices (MediaPipe Hands).
WRIST, INDEX_MCP, INDEX_PIP, INDEX_TIP = 0, 5, 6, 8
MIDDLE_TIP, RING_TIP, PINKY_TIP = 12, 16, 20
MIDDLE_PIP, RING_PIP, PINKY_PIP = 10, 14, 18

SAMPLE_FPS = 10
MIN_EVENT_MS = 500          # a deliberate point HOLDS — treat shorter as motion/jitter
MERGE_GAP_MS = 250          # bridge brief tracking dropouts
STABLE_RADIUS = 0.06        # fraction of canvas the target may wander
EXTRAPOLATE = 0.6           # target = tip + 0.6 * (tip - knuckle)
POP_DELAY_MS = 250          # popup lands a beat AFTER the hold starts (point → pause → card)
LINGER_MS = 400             # popup outlives the gesture slightly


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def is_pointing(pts: list[tuple[float, float]]) -> bool:
    """Index extended, other fingers curled (tip closer to wrist than pip)."""
    wrist = pts[WRIST]
    index_extended = _dist(pts[INDEX_TIP], wrist) > _dist(pts[INDEX_PIP], wrist) * 1.1
    curled = sum(
        1
        for tip, pip in ((MIDDLE_TIP, MIDDLE_PIP), (RING_TIP, RING_PIP), (PINKY_TIP, PINKY_PIP))
        if _dist(pts[tip], wrist) < _dist(pts[pip], wrist) * 1.05
    )
    return index_extended and curled >= 2


def target_point(pts: list[tuple[float, float]]) -> tuple[float, float]:
    """Where the finger points AT: tip extrapolated along knuckle→tip."""
    mcp, tip = pts[INDEX_MCP], pts[INDEX_TIP]
    x = tip[0] + EXTRAPOLATE * (tip[0] - mcp[0])
    y = tip[1] + EXTRAPOLATE * (tip[1] - mcp[1])
    return (min(1.0, max(0.0, x)), min(1.0, max(0.0, y)))


def cluster(samples: list[dict]) -> list[dict]:
    """Group per-frame pointing samples into stable events."""
    events: list[dict] = []
    current: dict | None = None
    for s in samples:
        if current is not None and (
            s["ms"] - current["endMs"] > MERGE_GAP_MS
            or _dist((s["x"], s["y"]), (current["cx"], current["cy"])) > STABLE_RADIUS
        ):
            events.append(current)
            current = None
        if current is None:
            current = {"startMs": s["ms"], "endMs": s["ms"], "xs": [], "ys": [], "cx": s["x"], "cy": s["y"]}
        current["endMs"] = s["ms"]
        current["xs"].append(s["x"])
        current["ys"].append(s["y"])
        current["cx"] = sum(current["xs"]) / len(current["xs"])
        current["cy"] = sum(current["ys"]) / len(current["ys"])
    if current is not None:
        events.append(current)

    return [
        {
            "startMs": round(e["startMs"]),
            "endMs": round(e["endMs"]),
            "x": round(e["cx"], 4),
            "y": round(e["cy"], 4),
        }
        for e in events
        if e["endMs"] - e["startMs"] >= MIN_EVENT_MS
    ]


def popup_rect(x: float, y: float, size: float, aspect: float = 1.0) -> list[float]:
    """A popup rect CENTERED ON the pointed-at spot, clamped on-canvas.

    The presenter points at empty space — that space is where the card
    belongs. (An earlier version offset cards toward frame center to
    avoid the finger; in practice that parked them over the presenter,
    which reads as wrong placement. Covering the fingertip is fine — the
    card IS the payoff of the gesture.)"""
    w, h = size, size * aspect
    cx = x - w / 2
    cy = y - h / 2
    return [round(min(1.0 - w, max(0.0, cx)), 4), round(min(1.0 - h, max(0.0, cy)), 4), w, round(h, 4)]


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)


def _model_path() -> Path:
    model = Path.home() / ".cache" / "video-studio" / "hand_landmarker.task"
    if not model.exists():
        import urllib.request

        model.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading hand landmarker model (~8MB) to {model} ...")
        urllib.request.urlretrieve(MODEL_URL, model)
    return model


def analyze(video: Path, sample_fps: int = SAMPLE_FPS, hands: int = 2) -> list[dict]:
    import cv2
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise SystemExit(f"cannot open {video}")
    native_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, round(native_fps / sample_fps))

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(_model_path())),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=hands,
        min_hand_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    samples: list[dict] = []
    with vision.HandLandmarker.create_from_options(options) as landmarker:
        i = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if i % step == 0:
                ms = i / native_fps * 1000
                image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                )
                result = landmarker.detect_for_video(image, int(ms))
                # Presenters keep a second hand at rest (often loosely closed
                # around a clicker, which reads as a point). Of the hands that
                # ARE pointing, the raised one is the one the audience follows,
                # so take the highest index tip rather than whichever hand
                # MediaPipe happened to rank first.
                pointing = [
                    [(lm.x, lm.y) for lm in hand]
                    for hand in result.hand_landmarks or []
                    if is_pointing([(lm.x, lm.y) for lm in hand])
                ]
                if pointing:
                    pts = min(pointing, key=lambda p: p[INDEX_TIP][1])
                    x, y = target_point(pts)
                    samples.append({"ms": ms, "x": x, "y": y})
            i += 1
    cap.release()
    return cluster(samples)


def emit_layers(
    events: list[dict],
    images: list[str] | None = None,
    size: float = 0.30,
    cards: list[dict] | None = None,
) -> list[dict]:
    """Popup layers for events: live-typography cards (preferred — editable
    in props.json/Remotion Studio) or image files, assigned in order."""
    layers = []
    for n, e in enumerate(events):
        layer: dict = {
            "id": f"popup-{n + 1}",
            "rect": popup_rect(e["x"], e["y"], size),
            # Land a beat after the hold begins — point, pause, THEN card —
            # instead of firing the instant a pointing pose is detected.
            "atMs": e["startMs"] + POP_DELAY_MS,
            "untilMs": e["endMs"] + LINGER_MS,
            "pop": True,
        }
        if cards:
            layer["card"] = cards[n % len(cards)]
        else:
            layer["source"] = f"file: {images[n % len(images)]}"
            layer["fit"] = "contain"
        layers.append(layer)
    return layers


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_an = sub.add_parser("analyze")
    p_an.add_argument("--in", dest="src", required=True)
    p_an.add_argument("--out", required=True)
    p_an.add_argument("--sample-fps", type=int, default=SAMPLE_FPS)
    p_an.add_argument(
        "--hands", type=int, default=2,
        help="hands to detect per frame; of those pointing, the highest wins (1 = legacy single-hand)",
    )
    p_ly = sub.add_parser("layers")
    p_ly.add_argument("--events", required=True)
    p_ly.add_argument("--images", help="comma-separated image paths, assigned to events in order")
    p_ly.add_argument(
        "--card", action="append", dest="cards", metavar="HEADING|SUBTEXT[|BG|FG]",
        help="live-typography card per event (repeatable, editable in props/studio) — preferred over --images",
    )
    p_ly.add_argument("--size", type=float, default=0.30, help="popup width as canvas fraction")
    args = ap.parse_args()

    if args.cmd == "analyze":
        events = analyze(Path(args.src), args.sample_fps, args.hands)
        Path(args.out).write_text(json.dumps(events, indent=2))
        print(json.dumps({"events": len(events), "out": args.out}))
    else:
        if not args.cards and not args.images:
            raise SystemExit("provide --card (preferred) or --images")
        cards = None
        if args.cards:
            cards = []
            for spec in args.cards:
                parts = spec.split("|")
                card = {"heading": parts[0]}
                if len(parts) > 1 and parts[1]:
                    card["subtext"] = parts[1]
                if len(parts) > 2 and parts[2]:
                    card["bg"] = parts[2]
                if len(parts) > 3 and parts[3]:
                    card["fg"] = parts[3]
                cards.append(card)
        events = json.loads(Path(args.events).read_text())
        images = [s.strip() for s in args.images.split(",")] if args.images else None
        layers = emit_layers(events, images=images, size=args.size, cards=cards)
        print(json.dumps(layers, indent=2))


if __name__ == "__main__":
    main()
