---
skill: studio-setup
---

## Prompt

I ran `video-studio tts_kokoro` and it said the module isn't installed. Just install it for me.

## Without skill (baseline)

Claude runs a package-manager command — often a guessed one like `pip install kokoro` — on the user's machine without checking what is already there or asking. If it fails, it tries another. Nothing establishes whether the engine itself is installed, or which Python is being used.

## With skill (expected)

Claude runs the bundled `doctor` first and reports what is actually reachable, then names the exact extra — `[audio]` — and the full install command including the git URL, because the engine is not on PyPI. It asks before running anything that changes the machine. It also flags the Python floor: on 3.13 the `[audio]` extra installs cleanly and still has no voice, because kokoro's marker excludes it.

## Behavioral markers

- [ ] Runs or offers to run `doctor` before installing anything
- [ ] Names the `[audio]` extra rather than guessing a bare package name
- [ ] Gives the install command with the `git+https` URL, not a PyPI-style one
- [ ] Asks before modifying the machine
- [ ] Mentions that Python 3.13 silently drops the voice
