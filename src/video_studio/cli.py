"""One entry point over the engine's scripts.

These programs were invoked as ``uv run scripts/<name>.py --flags``. Packaging
them must not change that surface, so nothing about their argument parsing was
touched: each module is still executed top-to-bottom with ``__name__`` set to
``"__main__"`` and ``sys.argv`` set to the arguments it was given. Whatever the
file did as a script — including ``composite_subject``, which has no ``main()``
and does its work at module level — it does here.

Three ways in, all equivalent:

    video-studio stock_pexels --query "desert road"
    video-studio stock-pexels --query "desert road"     # dashes accepted
    python -m video_studio.sourcing.stock_pexels --query "desert road"

The third is the one to reach for in a skill: it names the module explicitly and
survives this dispatcher being renamed.
"""

from __future__ import annotations

import runpy
import sys

#: script name -> dotted module. The keys are the original file stems, because
#: those are what the skills' prose already says to run.
COMMANDS: dict[str, str] = {
    # sourcing
    "source_clips": "video_studio.sourcing.source_clips",
    "stock_archive": "video_studio.sourcing.stock_archive",
    "stock_freesound": "video_studio.sourcing.stock_freesound",
    "stock_pexels": "video_studio.sourcing.stock_pexels",
    "stock_pixabay": "video_studio.sourcing.stock_pixabay",
    "stock_shutterstock": "video_studio.sourcing.stock_shutterstock",
    "verify_clips": "video_studio.sourcing.verify_clips",
    # audio
    "duck_music": "video_studio.audio.duck_music",
    "gen_captions": "video_studio.audio.gen_captions",
    "gen_music": "video_studio.audio.gen_music",
    "tts_eleven": "video_studio.audio.tts_eleven",
    "music_catalog": "video_studio.audio.music_catalog",
    "tts_kokoro": "video_studio.audio.tts_kokoro",
    # generation
    "gen_boil": "video_studio.generate.gen_boil",
    "gen_chalk": "video_studio.generate.gen_chalk",
    "gen_image": "video_studio.generate.gen_image",
    "gen_minimax": "video_studio.generate.gen_minimax",
    "gen_replicate": "video_studio.generate.gen_replicate",
    "gen_sneaker_origin_art": "video_studio.generate.gen_sneaker_origin_art",
    "gen_veo": "video_studio.generate.gen_veo",
    # vision
    "composite_subject": "video_studio.vision.composite_subject",
    "track_pointing": "video_studio.vision.track_pointing",
    # qc
    "qc_analyze": "video_studio.qc.qc_analyze",
    # export
    "burn_captions": "video_studio.export.burn_captions",
    "export_capcut": "video_studio.export.export_capcut",
    "export_edit": "video_studio.export.export_edit",
    "export_fcpxml": "video_studio.export.export_fcpxml",
    # project
    "build_props": "video_studio.project.build_props",
    "daily_digest": "video_studio.project.daily_digest",
    "preflight": "video_studio.project.preflight",
    "setup": "video_studio.project.setup",
    "studio": "video_studio.project.studio",
    "styles": "video_studio.project.styles",
    "tutor": "video_studio.project.tutor",
}

GROUPS = [
    ("sourcing", "stock APIs, downloads, and verifying what came back"),
    ("audio", "voice, word timings, and the music bed"),
    ("generate", "generated images, video and procedural motion"),
    ("vision", "segmentation, compositing, hand tracking"),
    ("qc", "checking a render against the plan it was built from"),
    ("export", "burnt-in captions, CapCut / Final Cut / OTIO handoff"),
    ("project", "props, preflight, editor, looks, tutorials, digest"),
]


def _usage() -> str:
    lines = ["video-studio <command> [args...]", "",
             "Commands (run `video-studio <command> --help` for its own flags):", ""]
    for group, blurb in GROUPS:
        names = sorted(n for n, m in COMMANDS.items()
                       if m.split(".")[1] == group)
        lines.append(f"  {group:<10} {blurb}")
        lines.append(f"             {'  '.join(names)}")
        lines.append("")
    lines.append("Set VIDEO_STUDIO_ROOT to point at the studio tree (the directory")
    lines.append("holding composer/, formats/, projects/) if you are not inside it.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        print(_usage())
        return 0 if args else 2

    name = args[0].replace("-", "_")
    module = COMMANDS.get(name)
    if module is None:
        print(f"video-studio: unknown command {args[0]!r}\n", file=sys.stderr)
        print(_usage(), file=sys.stderr)
        return 2

    # Reproduce `python scripts/<name>.py <rest>` exactly. alter_sys=True
    # replaces argv[0] with the module's file, which is what argparse's default
    # prog would have been as a script.
    sys.argv = [name, *args[1:]]
    try:
        runpy.run_module(module, run_name="__main__", alter_sys=True)
    except SystemExit as exc:  # scripts call sys.exit(); honour their code
        # `raise SystemExit("message")` is the house style for a fatal error in
        # these scripts, and its code is that STRING, not a number. Coercing it
        # with int() raised ValueError and buried the message under a traceback
        # — but only when invoked as `video-studio <cmd>`, never when the file
        # was run directly, which is why it survived. Follow the interpreter's
        # own rule instead: None is 0, an int is the code, anything else prints
        # to stderr and exits 1.
        if exc.code is None:
            return 0
        if isinstance(exc.code, int):
            return exc.code
        print(exc.code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
