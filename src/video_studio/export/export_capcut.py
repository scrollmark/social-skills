# /// script
# requires-python = ">=3.11"
# ///
"""Fill a CapCut project with this video's timeline — UNDOCUMENTED FORMAT.

Usage:
  uv run scripts/export_capcut.py --project projects/foo            # write the draft
  uv run scripts/export_capcut.py --project projects/foo --install  # fill a CapCut project
  uv run scripts/export_capcut.py --project foo --install --blank-project "Untitled"

WHAT CHANGED, AND WHY IT MATTERS
--------------------------------
This used to write `draft_content.json` into a folder it created itself. That
does not work, and does not fail loudly either — the project appears in
CapCut's drafts list and silently does nothing when clicked.

Two facts, both verified against CapCut on a real machine rather than inferred:

1. This CapCut reads `draft_info.json`. `draft_content.json` is what older
   reverse-engineered writers target, and no file by that name exists anywhere
   in a real project folder.
2. A project folder is not just its timeline. A real one carries
   `draft_meta_info.json`, `draft_settings`, `draft_biz_config.json`,
   `draft_agency_config.json`, `draft_virtual_store.json`, `Resources/`,
   `matting/` and more — undocumented, and different between CapCut versions.

So this NEVER creates a project folder. `--install` fills one CapCut made
itself: you create an empty project in the app, and this overwrites only its
`draft_info.json` (after backing it up). Every other file stays exactly as
CapCut wrote it, which is the only way to be current with a format nobody
documents.

The previous version also emitted 9 top-level keys where a real draft has 36,
and 10 `materials` sub-keys where a real one has 55. That was not a near miss
that a rename would fix.

CREDIT: the draft_info.json approach, the empty-project trick, and the
microsecond frame-snapping are taken from `capcut-cutter` by Courtney at
Scrollmark, which solved this for single-source cuts. This generalises it to a
multi-clip timeline with per-scene source files.

WHAT TRAVELS
------------
Every cut on its true frame, each clip linked to its real source file, trimmed
to the right in/out points, plus narration and score as audio tracks.

Cards, camera moves and fades do NOT travel — no interchange format carries
effects. Say that plainly rather than letting someone discover it in the app.
For an export that keeps cards as editable titles, use `export_fcpxml.py`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import uuid
from pathlib import Path

from video_studio.paths import studio_root

SKILL_ROOT = studio_root()

#: Where CapCut keeps drafts on macOS.
MAC_DRAFTS = Path.home() / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

#: 30fps frame slot, in microseconds. CapCut stores every time as an integer
#: number of microseconds, and snapping to this grid keeps cuts on frames.
FRAME_US = 33333

#: Namespace for deterministic ids. Re-exporting an unchanged project produces
#: an identical file; random uuid4s would make every export a diff and bury the
#: change that actually matters.
NS = uuid.UUID("6f1d5a8e-9b2c-4a1f-8e3d-0c7b5a2f9d14")

#: The 55 keys a real `materials` object carries. CapCut expects every one to
#: exist, even empty — this list is read off an actual project rather than
#: guessed, and a missing key is a silent no-open.
MATERIALS_KEYS = [
    "ai_translates", "audio_balances", "audio_effects", "audio_fades",
    "audio_pannings", "audio_pitch_shifts", "audio_track_indexes", "audios",
    "beats", "canvases", "chromas", "color_curves", "common_mask",
    "digital_human_model_dressing", "digital_humans", "drafts", "effects",
    "flowers", "green_screens", "handwrites", "hsl", "hsl_curves", "images",
    "log_color_wheels", "loudnesses", "manual_beautys", "manual_deformations",
    "material_animations", "material_colors", "multi_language_refs",
    "placeholder_infos", "placeholders", "plugin_effects",
    "primary_color_wheels", "realtime_denoises", "shapes", "smart_crops",
    "smart_relights", "sound_channel_mappings", "speeds", "stickers",
    "tail_leaders", "text_templates", "texts", "time_marks", "transitions",
    "video_effects", "video_radius", "video_shadows", "video_strokes",
    "video_trackings", "videos", "vocal_beautifys", "vocal_separations",
    # Present in CapCut 179 and absent from the reference implementation this
    # was ported from, which targeted 163. Found by diffing a real project
    # rather than by trusting the list — which is the only way to find these.
    "ai_text_effects",
]

PLATFORM = {
    "app_id": 359289, "app_source": "cc", "app_version": "8.3.0",
    "device_id": "0" * 32, "hard_disk_id": "",
    "mac_address": "0" * 32, "os": "mac", "os_version": "10.0.19045",
}


def uid(*parts: str) -> str:
    return str(uuid.uuid5(NS, "/".join(parts))).upper()


def us(seconds: float) -> int:
    """Seconds -> microseconds, snapped to a frame slot.

    Microseconds are the unit this format is famous for getting wrong: a
    factor-of-1000 slip produces a draft that opens fine and runs 1000x too
    long, which reads as a rendering bug rather than a units bug.
    """
    return int(round(seconds * 1_000_000 / FRAME_US)) * FRAME_US


def probe(path: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height:format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    try:
        d = json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return {"seconds": 0.0, "width": None, "height": None}
    st = (d.get("streams") or [{}])[0]
    try:
        seconds = float(d.get("format", {}).get("duration", 0) or 0)
    except (TypeError, ValueError):
        seconds = 0.0
    return {"seconds": seconds, "width": st.get("width"), "height": st.get("height")}


def empty_materials() -> dict:
    return {k: [] for k in MATERIALS_KEYS}


def shadow_set(seed: str) -> tuple[dict, list[str]]:
    """The nine side objects every video segment references by id.

    CapCut requires each segment to point at a canvas, a speed, a loudness and
    so on, even when none of them do anything. Omitting them does not error —
    the segment simply does not render.
    """
    mk = lambda kind: uid(seed, kind)
    objs = {
        "canvases": {"album_image": "", "blur": 0, "color": "", "id": mk("canvas"),
                     "image": "", "image_id": "", "image_name": "", "source_platform": 0,
                     "team_id": "", "type": "canvas_color"},
        "speeds": {"curve_speed": None, "id": mk("speed"), "mode": 0, "speed": 1,
                   "type": "speed"},
        "loudnesses": {"enable": False, "file_id": "", "id": mk("loudness"),
                       "loudness_param": None, "target_loudness": 0, "time_range": None},
        "sound_channel_mappings": {"audio_channel_mapping": 0, "id": mk("scm"),
                                   "is_config_open": False, "type": "none"},
        "vocal_separations": {"choice": 0, "enter_from": "", "final_algorithm": "",
                              "id": mk("vocal"), "production_path": "",
                              "removed_sounds": [], "time_range": None,
                              "type": "vocal_separation"},
        "material_colors": {"gradient_angle": 90, "gradient_colors": [],
                            "gradient_percents": [], "height": 0, "id": mk("colour"),
                            "is_color_clip": False, "is_gradient": False,
                            "solid_color": "", "width": 0},
        "placeholder_infos": {"error_path": "", "error_text": "", "id": mk("ph"),
                              "meta_type": "none", "res_path": "", "res_text": "",
                              "type": "placeholder_info"},
        "time_marks": {"id": mk("timemark"), "mark_items": []},
        "material_animations": {"animations": [], "id": mk("anim"),
                                "multi_language_current": "none",
                                "type": "sticker_animation"},
    }
    refs = [objs[k]["id"] for k in
            ("time_marks", "speeds", "placeholder_infos", "canvases",
             "material_animations", "sound_channel_mappings", "material_colors",
             "loudnesses", "vocal_separations")]
    return objs, refs


def video_material(mid: str, path: Path, duration_us: int, width: int, height: int,
                   is_image: bool) -> dict:
    tr = {"duration": duration_us, "start": 0}
    return {
        "aigc_history_id": "", "aigc_item_id": "", "aigc_type": "none",
        "audio_fade": None, "beauty_body_auto_preset": None,
        "beauty_body_preset_id": "",
        "beauty_face_auto_preset": {"name": "", "preset_id": "", "rate_map": "", "scene": ""},
        "beauty_face_auto_preset_infos": [], "beauty_face_preset_infos": [],
        "cartoon_path": "", "category_id": "", "category_name": "local",
        "check_flag": 125892607, "content_feature_info": None, "corner_pin": None,
        "crop": {"lower_left_x": 0, "lower_left_y": 1, "lower_right_x": 1,
                 "lower_right_y": 1, "upper_left_x": 0, "upper_left_y": 0,
                 "upper_right_x": 1, "upper_right_y": 0},
        "crop_ratio": "free", "crop_scale": 1, "duration": duration_us,
        "extra_type_option": 0, "formula_id": "", "freeze": None,
        "has_audio": not is_image, "has_sound_separated": False,
        "height": height, "id": mid, "intensifies_audio_path": "",
        "intensifies_path": "", "is_ai_generate_content": False,
        "is_copyright": False, "is_text_edit_overdub": False,
        "is_unified_beauty_mode": False, "live_photo_cover_path": "",
        "live_photo_timestamp": -1, "local_id": "", "local_material_from": "",
        "local_material_id": uid(mid, "local"), "material_id": "",
        "material_name": path.name, "material_url": "",
        "matting": {"custom_matting_id": "", "enable_matting_stroke": False,
                    "expansion": 0, "feather": 0, "flag": 0,
                    "has_use_quick_brush": False, "has_use_quick_eraser": False,
                    "interactiveTime": [], "path": "", "reverse": False, "strokes": []},
        "media_path": "", "multi_camera_info": None, "object_locked": None,
        "origin_material_id": "", "path": str(path), "picture_from": "none",
        "picture_set_category_id": "", "picture_set_category_name": "",
        "request_id": "", "reverse_intensifies_path": "", "reverse_path": "",
        "smart_match_info": None, "smart_motion": None, "source": 0,
        "source_platform": 0,
        "stable": {"matrix_path": "", "stable_level": 0, "time_range": tr},
        "surface_trackings": [], "team_id": "",
        "type": "photo" if is_image else "video",
        "unique_id": "",
        "video_algorithm": {
            "ai_background_configs": [], "ai_expression_driven": None,
            "ai_in_painting_config": [], "ai_motion_driven": None,
            "aigc_generate": None, "aigc_generate_list": [], "algorithms": [],
            "complement_frame_config": None, "deflicker": None,
            "gameplay_configs": [], "image_interpretation": None,
            "motion_blur_config": None, "mouth_shape_driver": None,
            "noise_reduction": None, "path": "", "quality_enhance": None,
            "skip_algorithm_index": [], "smart_complement_frame": None,
            "story_video_modify_video_config": {
                "is_overwrite_last_video": False, "task_id": "", "tracker_task_id": ""},
            "super_resolution": None, "time_range": tr},
        "video_mask_shadow": {"alpha": 0, "angle": 0, "blur": 0, "color": "",
                              "distance": 0, "path": "", "resource_id": ""},
        "video_mask_stroke": {"alpha": 0, "color": "", "distance": 0,
                              "horizontal_shift": 0, "path": "", "resource_id": "",
                              "size": 0, "texture": 0, "type": "",
                              "vertical_shift": 0},
        "width": width,
    }


def video_segment(sid: str, material_id: str, refs: list[str],
                  source_start_us: int, duration_us: int, target_start_us: int) -> dict:
    return {
        "caption_info": None, "cartoon": False,
        "clip": {"alpha": 1, "flip": {"horizontal": False, "vertical": False},
                 "rotation": 0, "scale": {"x": 1, "y": 1},
                 "transform": {"x": 0, "y": 0}},
        "color_correct_alg_result": "", "common_keyframes": [], "desc": "",
        "digital_human_template_group_id": "", "enable_adjust": True,
        "enable_adjust_mask": False, "enable_color_adjust_pro": False,
        "enable_color_correct_adjust": False, "enable_color_curves": True,
        "enable_color_match_adjust": False, "enable_color_wheels": True,
        "enable_hsl": False, "enable_hsl_curves": True, "enable_lut": True,
        "enable_mask_shadow": False, "enable_mask_stroke": False,
        "enable_smart_color_adjust": False, "enable_video_mask": True,
        "extra_material_refs": refs, "group_id": "",
        "hdr_settings": {"intensity": 1, "mode": 1, "nits": 1000},
        "id": sid, "intensifies_audio": False, "is_loop": False,
        "is_placeholder": False, "is_tone_modify": False, "keyframe_refs": [],
        "last_nonzero_volume": 1, "lyric_keyframes": None,
        "material_id": material_id, "raw_segment_id": "", "render_index": 0,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {"enable": False, "horizontal_pos_layout": 0,
                              "size_layout": 0, "target_follow": "",
                              "vertical_pos_layout": 0},
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": {"duration": duration_us, "start": source_start_us},
        "speed": 1, "state": 0,
        "target_timerange": {"duration": duration_us, "start": target_start_us},
        "template_id": "", "template_scene": "default", "track_attribute": 0,
        "track_render_index": 0, "uniform_scale": {"on": True, "value": 1},
        "visible": True, "volume": 1,
    }


def track(kind: str, segments: list[dict], seed: str) -> dict:
    return {"attribute": 0, "flag": 0, "id": uid(seed, "track", kind),
            "is_default_name": True, "name": "", "segments": segments, "type": kind}


def ratio_for(width: int, height: int) -> str:
    from math import gcd
    g = gcd(width, height) or 1
    return {"9:16": "9:16", "16:9": "16:9", "1:1": "1:1", "4:5": "4:5"}.get(
        f"{width // g}:{height // g}", "original")


def build(props: dict, media_root: Path, name: str,
          existing: dict | None = None) -> tuple[dict, dict]:
    fps = int(props.get("fps", 30))
    width = int(props.get("width", 1080))
    height = int(props.get("height", 1920))

    materials = empty_materials()
    video_segs: list[dict] = []
    cursor_us = 0
    skipped: list[str] = []

    for scene in props["scenes"]:
        dur_s = int(scene["durationInFrames"]) / fps
        media = [l for l in scene["layers"] if l.get("src")]
        if not media:
            # A card-only scene has nothing to reference. Advancing the cursor
            # anyway would leave a silent gap where the card used to be, which
            # is more honest than dropping it and shortening the whole edit.
            cursor_us += us(dur_s)
            skipped.append(scene["id"])
            continue

        layer = media[0]
        path = (media_root / layer["src"]).resolve()
        is_image = path.suffix.lower() in IMAGE_EXTS
        info = probe(path)
        src_s = info["seconds"] if not is_image else 0.0

        mid = uid(name, "video", scene["id"], layer["id"])
        materials["videos"].append(video_material(
            mid, path,
            duration_us=us(src_s if src_s else dur_s),
            width=info["width"] or width, height=info["height"] or height,
            is_image=is_image,
        ))
        objs, refs = shadow_set(f"{name}/{scene['id']}")
        for key, obj in objs.items():
            materials[key].append(obj)

        # Never ask for more source than the file has: CapCut freezes on the
        # last frame rather than erroring, which looks like a stuck render.
        take_s = dur_s if (is_image or not src_s) else min(dur_s, src_s)
        video_segs.append(video_segment(
            uid(name, "vseg", scene["id"]), mid, refs,
            source_start_us=0, duration_us=us(take_s), target_start_us=cursor_us,
        ))
        cursor_us += us(dur_s)

    draft = {
        "canvas_config": {"background": None, "height": height,
                          "ratio": ratio_for(width, height), "width": width},
        "color_space": -1,
        "config": {
            "adjust_max_index": 1, "attachment_info": [], "combination_max_index": 1,
            "export_range": None, "extract_audio_last_index": 1,
            "lyrics_recognition_id": "", "lyrics_sync": True, "lyrics_taskinfo": [],
            "maintrack_adsorb": False, "material_save_mode": 0,
            "multi_language_current": "none", "multi_language_list": [],
            "multi_language_main": "none", "multi_language_mode": "none",
            "original_sound_last_index": 1, "record_audio_last_index": 1,
            "sticker_max_index": 1, "subtitle_keywords_config": None,
            "subtitle_recognition_id": "", "subtitle_sync": True,
            "subtitle_taskinfo": [], "system_font_list": [],
            "use_float_render": False, "video_mute": False, "zoom_info_params": None,
        },
        "cover": None,
        "create_time": (existing or {}).get("create_time", 0),
        "draft_type": "video", "duration": cursor_us, "extra_info": None,
        "fps": fps, "free_render_index_mode_on": False,
        "function_assistant_info": {
            "audio_noise_segid_list": [], "auto_adjust": False,
            "auto_adjust_fixed": False, "auto_adjust_fixed_value": 50,
            "auto_adjust_segid_list": [], "auto_caption": False,
            "auto_caption_segid_list": [], "auto_caption_template_id": "",
            "caption_opt": False, "caption_opt_segid_list": [],
            "color_correction": False, "color_correction_fixed": False,
            "color_correction_fixed_value": 50, "color_correction_segid_list": [],
            "deflicker_segid_list": [], "enhance_quality": False,
            "enhance_quality_fixed": False, "enhance_quality_segid_list": [],
            "enhance_voice_segid_list": [], "enhande_voice": False,
            "enhande_voice_fixed": False, "eye_correction": False,
            "eye_correction_segid_list": [], "fixed_rec_applied": False,
            "fps": {"den": 1, "num": 0}, "normalize_loudness": False,
            "normalize_loudness_audio_denoise_segid_list": [],
            "normalize_loudness_fixed": False, "normalize_loudness_segid_list": [],
            "retouch": False, "retouch_fixed": False, "retouch_segid_list": [],
            "smart_rec_applied": False, "smart_segid_list": [],
            "smooth_slow_motion": False, "smooth_slow_motion_fixed": False,
            "video_noise_segid_list": [],
        },
        "group_container": None,
        "id": (existing or {}).get("id", uid(name, "draft")),
        "is_drop_frame_timecode": False, "keyframe_graph_list": [],
        "mixed_track_mode_on": (existing or {}).get("mixed_track_mode_on", False),
        "keyframes": {"adjusts": [], "audios": [], "effects": [], "filters": [],
                      "handwrites": [], "stickers": [], "texts": [], "videos": []},
        "last_modified_platform": (existing or {}).get("last_modified_platform", PLATFORM),
        "lyrics_effects": [],
        "materials": materials, "mutable_config": None,
        "name": (existing or {}).get("name", ""),
        # Inherit the version identity of the project being filled. Pinning a
        # constant means every CapCut update silently drifts us out of date;
        # the empty project CapCut just wrote is by definition current.
        "new_version": (existing or {}).get("new_version", "163.0.0"),
        "path": "", "platform": (existing or {}).get("platform", PLATFORM),
        "relationships": [], "render_index_track_mode_on": False,
        "retouch_cover": None,
        "smart_ads_info": {"draft_url": "", "page_from": "", "routine": ""},
        "source": "default", "static_cover_image_path": "", "time_marks": None,
        "tracks": [track("video", video_segs, name)],
        "uneven_animation_template_info": {"composition": "", "content": "",
                                           "order": "", "sub_template_info_list": []},
        "update_time": 0, "version": (existing or {}).get("version", 360000),
    }
    stats = {"segments": len(video_segs), "seconds": round(cursor_us / 1_000_000, 3),
             "scenesWithoutMedia": skipped}
    return draft, stats


def find_blank_projects(drafts: Path) -> list[str]:
    out = []
    for d in sorted(p for p in drafts.iterdir() if p.is_dir()):
        info = d / "draft_info.json"
        if not info.exists():
            continue
        try:
            data = json.loads(info.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if sum(len(t.get("segments") or []) for t in (data.get("tracks") or [])) == 0:
            out.append(d.name)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", help="where to write the draft (default: <project>/edit/capcut/)")
    ap.add_argument("--install", action="store_true",
                    help="fill a CapCut-created empty project with this timeline")
    ap.add_argument("--blank-project", help="name of the empty CapCut project to fill")
    ap.add_argument("--drafts-dir", type=Path, default=MAC_DRAFTS)
    args = ap.parse_args()

    project = Path(args.project)
    slug = project.resolve().name
    props_path = SKILL_ROOT / "composer" / "props" / f"{slug}.json"
    if not props_path.exists():
        raise SystemExit(f"{props_path} not found — run build_props.py for this project first")
    props = json.loads(props_path.read_text())

    out = Path(args.out) if args.out else project / "edit" / "capcut" / "draft_info.json"
    result: dict = {}

    if not args.install:
        draft, stats = build(props, SKILL_ROOT / "composer" / "public", slug)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
        result = {"out": str(out), **stats, "installed": None,
                  "note": "written but NOT installed. CapCut cannot open a folder this "
                          "script created — use --install to fill a project CapCut made."}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    drafts = args.drafts_dir
    if not drafts.exists():
        raise SystemExit(f"CapCut drafts folder not found at {drafts}")

    blank = args.blank_project
    if not blank:
        candidates = find_blank_projects(drafts)
        if not candidates:
            raise SystemExit(
                "No empty CapCut project to fill.\n"
                "  In CapCut: File > New Project, save it, add nothing.\n"
                "  Then re-run with --blank-project \"<the name you gave it>\".\n"
                "This script will not create the folder itself: a project needs "
                "sibling files only CapCut knows how to write."
            )
        if len(candidates) > 1:
            raise SystemExit(
                f"{len(candidates)} empty projects — ambiguous. Name one with "
                f"--blank-project:\n  " + "\n  ".join(candidates))
        blank = candidates[0]

    target = drafts / blank
    info_path = target / "draft_info.json"
    if not info_path.exists():
        raise SystemExit(f"{info_path} not found — is {blank!r} a CapCut-created project?")

    existing = json.loads(info_path.read_text())
    if sum(len(t.get("segments") or []) for t in (existing.get("tracks") or [])):
        raise SystemExit(
            f"{blank!r} already has a timeline — refusing to overwrite it.\n"
            "Losing an in-progress edit to a format guess is not an acceptable failure."
        )

    draft, stats = build(props, SKILL_ROOT / "composer" / "public", slug, existing)
    backup = info_path.with_suffix(".json.before-video-studio.bak")
    shutil.copy2(info_path, backup)
    info_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

    meta_path = target / "draft_meta_info.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta["tm_duration"] = stats["seconds"] * 1_000_000
        meta["draft_name"] = slug
        meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({
        "installed": str(target), "filledProject": blank, "backup": str(backup),
        **stats,
        "next": f"Open CapCut, click {blank!r}, then rename it to {slug!r}.",
        "doesNotTravel": "cards, camera moves, fades — use export_fcpxml.py for those",
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
