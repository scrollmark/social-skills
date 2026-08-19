# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Generate an instrumental music bed (Lyria 3, or ElevenLabs Music).

Usage:
  # auto-picks whichever provider has a key (Lyria preferred — see below):
  uv run scripts/gen_music.py \
      --prompt "calm lo-fi bed, warm keys, no drums, unobtrusive under speech" \
      --seconds 35 --out projects/x/audio/music.mp3

  uv run scripts/gen_music.py --provider elevenlabs ...   # force one

Both options were chosen for RIGHTS, not for sound. The best-sounding music
generators have unresolved training-data litigation and mostly no public API,
so they cannot carry client work. See references/providers.md.

  lyria      GEMINI_API_KEY / GOOGLE_API_KEY — same credential as the video and
             image generators, so it needs no new account. `lyria-3-clip-preview`
             returns a ~30s clip; `lyria-3-pro-preview` is the higher-quality
             sibling. Length is requested IN THE PROMPT, not as a parameter, and
             the model treats it as a hint — always measure what comes back.
             NOT ON THE FREE TIER: the quota is literally `limit: 0`, so an
             unbilled project gets a 429 that reads like rate limiting but never
             clears. Needs billing enabled on the Google project.
  elevenlabs ELEVENLABS_API_KEY — takes an explicit `music_length_ms`, so it is
             the one to reach for when the bed must hit an exact length.
  minimax    MINIMAX_API_KEY — `music-3.0-free` works on an unbilled key (RPM 3).
             ⚠️ RIGHTS: unlike the two above, its training-data position is not
             established. Fine for internal and experimental work; do NOT put it
             under client deliverables. Never the auto-pick for that reason.

Prompting note: a bed exists to sit UNDER narration. Ask for sparse,
mid-scooped, no vocals, no big transients — and keep it a few seconds longer
than the video so the composer can fade rather than cut it.

Prints JSON: {"out", "seconds", "measuredSeconds", "model", "provider"}.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
from pathlib import Path

ELEVEN_API = "https://api.elevenlabs.io/v1/music"
ELEVEN_MODEL = "music_v1"

GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
LYRIA_MODEL = "lyria-3-clip-preview"

MINIMAX_BASE = "https://api.minimax.io/v1"
MINIMAX_MODEL = "music-3.0-free"


class ProviderUnusable(RuntimeError):
    """The credential is present but cannot produce anything.

    Kept separate from RuntimeError on purpose. A key with no quota, or one that
    is not authorised for this model, means "try someone else". A bad prompt or
    a malformed response means "stop and tell the user" — retrying that against
    a PAID provider would just buy the same failure twice.
    """


#: HTTP statuses that mean the credential, not the request, is the problem.
UNUSABLE_STATUSES = (401, 403, 429)


def brief(body: str) -> str:
    """One readable line out of a provider's error body.

    These arrive as pretty-printed JSON, and pasting the raw blob into a
    sentence buries the one thing the reader needs — whether to enable billing
    or fix a key — under three lines of punctuation.
    """
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return " ".join(body.split())[:160]
    for path in (("error", "message"), ("detail", "message"), ("message",),
                 ("error",), ("detail",)):
        node = data
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
            if node is None:
                break
        if isinstance(node, str) and node:
            return " ".join(node.split())[:160]
    return " ".join(body.split())[:160]


def measured_seconds(path: Path) -> float | None:
    """What actually came back. Lyria takes length as a prompt hint, so the
    requested duration is a wish and this is the fact — and a bed that is
    shorter than the video is the failure that only shows up at the render."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return round(float(r.stdout.strip()), 2)
    except ValueError:
        return None


def gen_lyria(prompt: str, seconds: int, model: str, out: Path, key: str) -> None:
    import httpx

    # Duration is not a parameter on this endpoint — it is stated in the prompt,
    # and "instrumental only" has to be said explicitly or vocals show up.
    text = (f"Create a {seconds}-second instrumental music bed. {prompt} "
            f"Instrumental only, no vocals.")
    with httpx.Client(timeout=600) as client:
        r = client.post(
            GEMINI_API.format(model=model),
            headers={"x-goog-api-key": key, "content-type": "application/json"},
            json={"contents": [{"parts": [{"text": text}]}]},
        )
    if r.status_code in UNUSABLE_STATUSES:
        raise ProviderUnusable(f"Lyria ({r.status_code}) — {brief(r.text)}")
    if r.status_code != 200:
        raise RuntimeError(f"Lyria error {r.status_code}: {r.text[:300]}")

    body = r.json()
    parts = (body.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    audio = next((p["inlineData"]["data"] for p in parts if p.get("inlineData")), None)
    if not audio:
        note = next((p.get("text", "") for p in parts if p.get("text")), "")
        raise RuntimeError(f"Lyria returned no audio. Model said: {note[:300] or '(nothing)'}")
    out.write_bytes(base64.b64decode(audio))


def gen_minimax(prompt: str, seconds: int, model: str, out: Path, key: str) -> None:
    import httpx

    # `lyrics` is REQUIRED even for an instrumental — omitting it fails with
    # "invalid params, lyrics is required" (status 2013), which reads like a
    # schema problem rather than "this is a song model". "[instrumental]" is the
    # tag that yields a bed with no vocals.
    with httpx.Client(timeout=600) as client:
        r = client.post(
            f"{MINIMAX_BASE}/music_generation",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "prompt": prompt, "lyrics": "[instrumental]",
                  "output_format": "hex"},
        )
    if r.status_code in UNUSABLE_STATUSES:
        raise ProviderUnusable(f"MiniMax ({r.status_code}) — {brief(r.text)}")
    if r.status_code != 200:
        raise RuntimeError(f"MiniMax music HTTP {r.status_code}: {r.text[:300]}")
    body = r.json()
    # A MiniMax failure is a 200 with a nonzero status_code in the envelope.
    base = body.get("base_resp") or {}
    if base.get("status_code"):
        raise RuntimeError(f"MiniMax music error {base['status_code']}: {base.get('status_msg')}")
    audio = (body.get("data") or {}).get("audio")
    if not audio:
        raise RuntimeError(f"MiniMax returned no audio: {json.dumps(body)[:300]}")
    out.write_bytes(bytes.fromhex(audio))


def gen_elevenlabs(prompt: str, seconds: int, model: str, out: Path, key: str) -> None:
    import httpx

    with httpx.Client(timeout=600) as client:
        r = client.post(
            ELEVEN_API,
            headers={"xi-api-key": key, "content-type": "application/json"},
            json={"prompt": prompt, "music_length_ms": seconds * 1000, "model_id": model},
        )
    if r.status_code != 200:
        detail = r.text[:250]
        try:
            detail = json.dumps(r.json())[:250]
        except Exception:
            pass
        if r.status_code in UNUSABLE_STATUSES:
            raise ProviderUnusable(f"ElevenLabs ({r.status_code}) — {brief(r.text)}")
        raise RuntimeError(f"Music API error {r.status_code}: {detail}")
    out.write_bytes(r.content)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--seconds", type=int, default=30)
    ap.add_argument("--provider", choices=["auto", "lyria", "elevenlabs", "minimax"], default="auto")
    ap.add_argument("--model", help="override the provider's default model")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    eleven_key = os.environ.get("ELEVENLABS_API_KEY")
    minimax_key = os.environ.get("MINIMAX_API_KEY")

    keys = {"lyria": gemini_key, "elevenlabs": eleven_key, "minimax": minimax_key}

    if args.provider == "auto":
        # A CHAIN, not a pick. Selecting on key PRESENCE alone was the bug this
        # replaced: GEMINI_API_KEY is set on most machines here, Lyria needs
        # billing that is usually not enabled, so auto chose a provider that
        # could not run and never reached the ElevenLabs key sitting beside it.
        # Presence of a credential is not usability, and only a real call can
        # tell the difference.
        #
        # Prefer the credential most projects already have over one that needs a
        # new paid account; both clear the rights bar.
        # MiniMax is deliberately NOT in this chain: it is the only option here
        # whose training-data position is unsettled, so it must be asked for by
        # name rather than arrived at by falling through.
        chain = [p for p in ("lyria", "elevenlabs") if keys[p]]
        if not chain:
            raise SystemExit(
                "No rights-clean music provider available. Set GEMINI_API_KEY (Lyria, "
                "needs billing enabled) or ELEVENLABS_API_KEY. "
                + ("MINIMAX_API_KEY is set — pass --provider minimax to use it, but read "
                   "the rights note in this file's docstring first. " if minimax_key else "")
                + "Run scripts/doctor.py to confirm."
            )
    else:
        # Explicitly named: never fall through. Silently spending money on a
        # provider the user did not ask for is worse than failing.
        chain = [args.provider]

    out = Path(args.out)
    if out.exists() and out.stat().st_size > 0:
        raise SystemExit(f"{out} already exists — delete it explicitly to regenerate (this costs money)")
    out.parent.mkdir(parents=True, exist_ok=True)

    runners = {
        "lyria": (gen_lyria, LYRIA_MODEL, "Set GEMINI_API_KEY or GOOGLE_API_KEY for Lyria"),
        "minimax": (gen_minimax, MINIMAX_MODEL, "Set MINIMAX_API_KEY"),
        "elevenlabs": (gen_elevenlabs, ELEVEN_MODEL, "Set ELEVENLABS_API_KEY (paid — elevenlabs.io)"),
    }
    skipped: list[str] = []
    provider = model = None
    for candidate in chain:
        run, default_model, missing_msg = runners[candidate]
        if not keys[candidate]:
            raise SystemExit(missing_msg)
        model = args.model or default_model
        try:
            run(args.prompt, args.seconds, model, out, keys[candidate])
        except ProviderUnusable as exc:
            # Nothing was produced and nothing was charged. Leave no partial
            # file behind for the next attempt's existence check to trip on.
            out.unlink(missing_ok=True)
            skipped.append(str(exc))
            if candidate is chain[-1]:
                # Word it for what actually happened: naming one provider and
                # being told "every provider refused" reads like a broken tool.
                lead = ("Every available music provider refused"
                        if len(chain) > 1 else f"{candidate} refused")
                nudge = ("Enable billing, or set a key for another provider."
                         if args.provider == "auto" else
                         "Enable billing for it, or drop --provider to try the others.")
                raise SystemExit(f"{lead}:\n  " + "\n  ".join(skipped) + f"\n{nudge}")
            print(f"note: {exc} — trying the next provider", flush=True)
            continue
        provider = candidate
        break

    got = measured_seconds(out)
    if got is not None and got + 0.5 < args.seconds:
        print(f"WARNING: asked for {args.seconds}s, got {got}s — a bed shorter than "
              f"the video has to loop or be re-asked.", flush=True)
    print(json.dumps({
        "out": str(out), "seconds": args.seconds, "measuredSeconds": got,
        "model": model, "provider": provider,
    }))


if __name__ == "__main__":
    main()
