# Internal stack (maintainers only)

Everything here is an implementation detail. It is deliberately absent from
user-facing prose — see the house-vocabulary table in `SKILL.md`. Keep this
file the single place these names live outside of executable code.

| Role | What we actually use | Notes |
|---|---|---|
| Composer / editor | Remotion 4.0.x | Original compositions, no vendored third-party code. `npx remotion studio` = "the editor"; `npx remotion render` = rendering. **Not in this repo** — the composer is a separate, externally licensed tree, so nothing here can render on its own. |
| Quality gate | `qc_render.py` (bundled) + `video-studio qc_analyze` | Two sizes. The bundled one needs no install and checks a render against its plan; `qc_analyze` decodes frames and needs `[qc]`. Both = "the quality check". Superseded showwatcher, which was never published. |
| Clip generation | MiniMax (Hailuo), Google Veo | `video-studio gen_minimax`, `video-studio gen_veo`. Quirks in `api-landmines.md`. |
| Voice | Kokoro (local, free) | `video-studio tts_kokoro` = "the built-in voice". |
| Planning LLM | Gemini (text) | Agent-side; no dedicated script. |
| Free footage search | yt-dlp, Creative-Commons filtered | `video-studio source_clips` = "free footage libraries". |
| Gesture analysis | MediaPipe Tasks (HandLandmarker) | `video-studio track_pointing`. |
| Media probing / keying | ffmpeg + ffprobe | `measure.py` (bundled in audio-acquisition), `prekey.py` (bundled in media-acquisition). |
| Optional asset library | OpenMontage (external, AGPLv3) | Invoked as an external tool only — never vendored, to keep this repo's licence clean. |

## Why the abstraction

Two reasons, both practical rather than cosmetic:

1. **Product surface.** What the user experiences is "a video studio", not a
   list of third-party dependencies. Naming vendors invites questions we do
   not want to field ("why MiniMax?", "is my footage going to Google?") in the
   middle of a creative session.
2. **Swappability.** Every row above is expected to change — see
   `references/providers.md` for the evaluation of alternatives. If users
   learned the stack by name, each swap becomes a support event.

If a user asks directly, answer honestly. This is about not volunteering
implementation detail, not about concealing it.
