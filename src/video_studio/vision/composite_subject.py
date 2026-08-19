#!/usr/bin/env python3
"""Put a filmed subject somewhere they never were.

Segments a person out of a take, drops them over replacement footage, and
optionally places a foreground prop (drawn art, a vehicle, a frame) in front of
them — then flips and drives the whole subject+prop pair across the frame.

  composite_subject.py OUT.mp4 --in SRC --ss 39.9 --t 2.5 \
      --bg crowd.webm --bg-ss 12 --bg-crop 405:600:430:15 \
      --fg art/car.png --occlude-below 1215 --free-arm --travel -330 430

Layering: background -> subject -> foreground prop -> (optionally) the subject's
gesturing forearm punched back through the prop.

Why the pieces exist, each learned the hard way:
- `--occlude-below` cuts the subject off at the prop's top edge with a feathered
  seam. It sells "inside the prop" AND hides whatever they were really sitting
  on. Without it the real chair floats in the new scene.
- `--free-arm` uses pose landmarks to bring the near forearm and hand back in
  FRONT of the prop, so a gesture is not swallowed by it. The capsule is
  intersected with the segmentation mask, so only real body pixels come
  forward — a bare capsule cuts a person-shaped hole of background through
  the prop whenever the pose estimate drifts.
- `--scale` anchors on the subject, not the frame origin. warpAffine scales
  about (0,0), so scaling up otherwise throws the subject down and right.
- Mirroring happens BEFORE travel. Flip afterwards and the flip also reverses
  the direction of travel.
- Crude, hand-drawn props forgive the soft edges of a segmentation matte.
  A clean vector prop makes the matte look broken.

Models are fetched once to ~/.cache/mediapipe/ (see MODEL_URLS below).
"""
import argparse, pathlib, subprocess, sys
import numpy as np, cv2
import mediapipe as mp
from mediapipe.tasks import python as mpp
from mediapipe.tasks.python import vision

MODEL = pathlib.Path.home() / ".cache/mediapipe/selfie_segmenter.tflite"
POSE_MODEL = pathlib.Path.home() / ".cache/mediapipe/pose_landmarker_lite.task"
MODEL_URLS = {
    MODEL: "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
           "selfie_segmenter/float16/latest/selfie_segmenter.tflite",
    POSE_MODEL: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
                "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
}

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--in", dest="src", required=True)
ap.add_argument("--ss", type=float, required=True)
ap.add_argument("--t", type=float, required=True)
ap.add_argument("--bg", required=True)
ap.add_argument("--bg-ss", type=float, default=0.0)
ap.add_argument("--bg-crop", default="", help="ffmpeg crop applied to bg, e.g. 1280:300:0:60")
ap.add_argument("--bg-eq", default="", help="extra bg filters, e.g. eq=contrast=1.9:saturation=0")
ap.add_argument("--fg", default=None,
                help="foreground prop PNG with alpha, drawn in front of the subject")
ap.add_argument("--occlude-below", type=int, default=None,
                help="cut the subject off at this y with a feathered seam "
                     "(use the prop's top edge)")
ap.add_argument("--no-flip-fg", action="store_true",
                help="by default the prop is mirrored to face the same way as the subject")
ap.add_argument("--size", type=int, nargs=2, default=(1080, 1920))
ap.add_argument("--fps", type=int, default=25)
ap.add_argument("--scale", type=float, default=1.0, help="scale the subject")
ap.add_argument("--dx", type=int, default=0)
ap.add_argument("--dy", type=int, default=0)
ap.add_argument("--anchor", type=int, nargs=2, default=(300, 1050),
                help="scale about this point (subject centre), not the frame origin")
ap.add_argument("--free-arm", action="store_true",
                help="let the gesturing forearm and hand pass IN FRONT of the car")
ap.add_argument("--arm-radius", type=int, default=90)
ap.add_argument("--travel", type=float, nargs=2, metavar=("X0", "X1"), default=None,
                help="drive the subject+car across frame, px, start to end")
ap.add_argument("--flip-h", action="store_true", help="mirror the vehicle horizontally")
ap.add_argument("--flip-v", action="store_true", help="mirror the vehicle vertically")
a = ap.parse_args()
W, H = a.size
FPS = a.fps

def ensure_model(p):
    if p.exists():
        return
    import urllib.request
    p.parent.mkdir(parents=True, exist_ok=True)
    print(f"fetching {p.name} …", file=sys.stderr)
    urllib.request.urlretrieve(MODEL_URLS[p], p)


ensure_model(MODEL)
if a.free_arm:
    ensure_model(POSE_MODEL)

work = pathlib.Path("work"); work.mkdir(exist_ok=True)
fg_dir, bg_dir = work / "fg", work / "bg"
for d in (fg_dir, bg_dir):
    for old in d.glob("*.png") if d.exists() else []:
        old.unlink()
    d.mkdir(exist_ok=True)

n = int(a.t * FPS)
# subject frames
subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a.ss), "-t", str(a.t), "-i", a.src,
                "-vf", f"fps={FPS}", "-frames:v", str(n), f"{fg_dir}/%04d.png", "-y"], check=True)
# background frames, looped so a short clip still covers the take
bgvf = (f"{'crop=' + a.bg_crop + ',' if a.bg_crop else ''}"
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"{a.bg_eq + ',' if a.bg_eq else ''}fps={FPS},format=yuv420p")
subprocess.run(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-ss", str(a.bg_ss), "-t", str(a.t),
                "-i", a.bg, "-vf", bgvf, "-frames:v", str(n), "-strict", "-1",
                f"{bg_dir}/%04d.png", "-y"], check=True)

car_rgb = car_a = None
if a.fg:
    car = cv2.imread(a.fg, cv2.IMREAD_UNCHANGED)
    if car is None:
        sys.exit(f"no foreground art at {a.fg}")
    if car.shape[2] < 4:
        sys.exit(f"{a.fg} has no alpha channel — the prop must be a transparent PNG")
    if not a.no_flip_fg:
        car = cv2.flip(car, 1)              # match the direction the subject faces
    if car.shape[:2] != (H, W):
        car = cv2.resize(car, (W, H), interpolation=cv2.INTER_LANCZOS4)
    car_rgb = car[:, :, :3].astype(np.float32)
    car_a = car[:, :, 3:4].astype(np.float32) / 255.0

pose = None
if a.free_arm:
    pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
        base_options=mpp.BaseOptions(model_asset_path=str(POSE_MODEL)), num_poses=1))

opts = vision.ImageSegmenterOptions(
    base_options=mpp.BaseOptions(model_asset_path=str(MODEL)),
    output_category_mask=False, output_confidence_masks=True)

fgs = sorted(fg_dir.glob("*.png")); bgs = sorted(bg_dir.glob("*.png"))
if not fgs:
    sys.exit("no subject frames extracted — check --ss/--t")
out_dir = work / "out"
out_dir.mkdir(exist_ok=True)
for old in out_dir.glob("*.png"):
    old.unlink()

# feather the waist cut so the subject fades into the car instead of ending on a hard line
if a.occlude_below is not None:
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    waist = np.clip((a.occlude_below + 60 - yy) / 120.0, 0.0, 1.0)
else:
    waist = 1.0

with vision.ImageSegmenter.create_from_options(opts) as seg:
    for i, fp in enumerate(fgs):
        frame = cv2.imread(str(fp))
        bg = cv2.imread(str(bgs[min(i, len(bgs) - 1)]))
        m = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB,
                                 data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        ).confidence_masks[-1].numpy_view()
        m = np.clip(m.astype(np.float32), 0, 1)
        if m.ndim == 2:
            m = m[:, :, None]
        # tighten then soften: kills the halo the model leaves around the shoulders
        m = cv2.erode(m, np.ones((5, 5), np.uint8), iterations=1)
        m = cv2.GaussianBlur(m, (0, 0), 3)[:, :, None] if m.ndim == 2 else m
        m_full = m.copy()          # before the waist cut — the arm lives down here
        m = m * waist

        subj = frame.astype(np.float32)
        if a.scale != 1.0 or a.dx or a.dy:
            # anchor the scale on the subject, not the frame origin, or scaling
            # up also throws him down and to the right
            cx, cy = a.anchor
            s = a.scale
            M = np.float32([[s, 0, cx - s * cx + a.dx], [0, s, cy - s * cy + a.dy]])
            subj = cv2.warpAffine(subj, M, (W, H), borderValue=(0, 0, 0))
            m = cv2.warpAffine(m, M, (W, H), borderValue=0)
            # m_full must ride the same transform or the arm mask lands in
            # source coordinates while everything else is scaled
            m_full = cv2.warpAffine(m_full, M, (W, H), borderValue=0)
            if m.ndim == 2:
                m = m[:, :, None]
            if m_full.ndim == 2:
                m_full = m_full[:, :, None]

        # Build the vehicle as its own RGBA layer (subject + car) so the pair can
        # be flipped and driven across frame as one object, over a static crowd.
        veh_rgb = subj.copy()
        veh_a = m.copy()
        if car_a is not None:
            veh_rgb = car_rgb * car_a + veh_rgb * (1 - car_a)
            veh_a = car_a + veh_a * (1 - car_a)          # over-operator on alpha

        if pose is not None:
            # Put the gesturing forearm back on TOP of the car, so the hand reads
            # as waving over the door rather than being swallowed by it.
            pr = pose.detect(mp.Image(image_format=mp.ImageFormat.SRGB,
                                      data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            if pr.pose_landmarks:
                L = pr.pose_landmarks[0]
                # near arm = whichever wrist the segmenter actually sees
                side = 16 if L[16].visibility >= L[15].visibility else 15
                elbow, wrist, hand = (side - 2, side, side + 4)
                pts = []
                for li in (elbow, wrist, hand):   # NOT `i` — that is the frame index
                    px, py = L[li].x * W, L[li].y * H
                    if a.scale != 1.0 or a.dx or a.dy:   # same affine as the subject
                        cx, cy = a.anchor; sc = a.scale
                        px = sc * px + (cx - sc * cx + a.dx)
                        py = sc * py + (cy - sc * cy + a.dy)
                    pts.append((int(px), int(py)))
                cap = np.zeros((H, W), np.float32)
                cv2.line(cap, pts[0], pts[1], 1.0, a.arm_radius * 2, cv2.LINE_AA)
                cv2.line(cap, pts[1], pts[2], 1.0, a.arm_radius * 2, cv2.LINE_AA)
                cv2.circle(cap, pts[2], int(a.arm_radius * 1.25), 1.0, -1, cv2.LINE_AA)
                cap = cv2.GaussianBlur(cap, (0, 0), 12)[:, :, None]
                arm = np.clip(m_full * cap, 0, 1)        # only real body pixels
                veh_rgb = subj * arm + veh_rgb * (1 - arm)
                veh_a = np.maximum(veh_a, arm)
        # mirror BEFORE travelling, or the flip also reverses the travel direction
        if a.flip_h:
            veh_rgb = cv2.flip(veh_rgb, 1); veh_a = cv2.flip(veh_a, 1)
        if a.flip_v:
            veh_rgb = cv2.flip(veh_rgb, 0); veh_a = cv2.flip(veh_a, 0)
        if veh_a.ndim == 2:
            veh_a = veh_a[:, :, None]
        if a.travel:
            p = i / max(1, len(fgs) - 1)
            # ease in/out so it glides rather than starting at full speed
            e = p * p * (3 - 2 * p)
            tx = a.travel[0] + (a.travel[1] - a.travel[0]) * e
            T = np.float32([[1, 0, tx], [0, 1, 0]])
            veh_rgb = cv2.warpAffine(veh_rgb, T, (W, H), borderValue=(0, 0, 0))
            veh_a = cv2.warpAffine(veh_a, T, (W, H), borderValue=0)
            if veh_a.ndim == 2:
                veh_a = veh_a[:, :, None]

        comp = bg.astype(np.float32) * (1 - veh_a) + veh_rgb * veh_a
        cv2.imwrite(str(out_dir / f"{i:04d}.png"), np.clip(comp, 0, 255).astype(np.uint8))

subprocess.run(["ffmpeg", "-v", "error", "-framerate", str(FPS), "-i", f"{out_dir}/%04d.png",
                "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-y", a.out], check=True)
print(f"{a.out}  {len(fgs)} frames")
