---
name: studio-setup
description: Use when checking whether a machine can actually produce video, triaging a pipeline that stopped working, or deciding which third-party tool or API key to add next.
---

# Studio Setup

Two questions, two scripts. *What can I use right now* is `doctor.py`. *How do I get the rest* is `setup.py`. Answer both against the machine in front of you — describing an installed tool as missing wastes the user's time and makes everything else you say suspect.

## Requires

`scripts/doctor.py` and `scripts/setup.py` from **scrollmark/video-studio** (private). Without them you can still check binaries by hand (`which ffmpeg ffprobe node uv`) and read the env vars listed below, but there is no single status report, no install plan, and no auto/system/manual classification — so you lose the one thing that stops an agent from running a package-manager install nobody asked for. `references/tooling-inventory.md` in this skill is the map; only doctor knows the state.

## Checking an Environment

    uv run scripts/doctor.py           # what is reachable right now
    uv run scripts/doctor.py --json    # same, machine-readable

Doctor reports per category — public-domain archives, stock, generated video, generated images, generated audio, voice — plus the required binaries. It checks that a key is *present*, not that it works; a key can still be rejected at call time for spent quota or a withdrawn model, and the individual scripts report that.

Run it **before** offering sourcing options. Offering a source that turns out to have no key makes the estimate wrong as well as the offer.

## Fixing a Broken One

    uv run scripts/setup.py            # report + the exact plan, changes NOTHING
    uv run scripts/setup.py --yes      # actually run the runnable fixes
    uv run scripts/setup.py --yes --only composer,voice

Every missing component is classified, and the split is the whole point:

- **auto** — scoped to the toolchain directory, idempotent, safe to re-run: installing the composer's npm packages, warming the local voice model, copying `.env.example` to `.env`.
- **system** — changes the machine outside that directory, such as a package manager installing `ffmpeg` or `node`. Still runnable, but it is somebody's computer.
- **manual** — a human has to act: get an API key, enable billing, accept terms, restart a sandboxed host with network access. Never runnable. Printing "run this command" for something a machine cannot do erodes trust in the rest of the output.

**Ask first, every time, even for the safe ones.** Nothing runs without `--yes`, and `--yes` also runs the system-level installs. Tell the user what is missing in their terms ("the renderer isn't installed"), say whether you can fix it, then ask.

If everything is present, say nothing and get on with the work. Narrating a clean bill of health is noise.

## The Tier-0 Floor

Three things, and without any one of them nothing works: `ffmpeg` + `ffprobe` (every duration measured, every trim, all loudness and keying), `node` 18+ (the composer renders and previews through it), and `uv` (runs every bundled script with its own pinned dependencies). Everything else widens what you can reach; these three decide whether there is a pipeline at all.

After that, the single highest-value addition is a free Pexels key. It converts "find me footage of that" from a coin flip into the normal answer, and costs nothing. Full inventory, tiers, costs and rights in `references/tooling-inventory.md`.

## Licences

Every external service this skill can reach, with its cost and what you may do
with the output, is in `SERVICES.md` next to this file. Check it before anything
gets published. The music row is the one that actually bites: the free backend's
redistribution rights are unclear, the paid one is licensed catalogue.

## showwatcher Is Not Installed

The automated quality gate documented as step 8 of the workflow is a separate internal CLI, installed from its own repo, and it has been **absent on every machine seen so far**. `setup.py` lists it as an optional system component with no install command; `doctor.py` reports it as an optional tool that is missing.

So: do not tell a user the quality check will run. Verify frames by hand and **say out loud that you are doing so**. It is the only step in the pipeline whose guarantee depends on somebody remembering, and a hand check silently skipped is worse than no gate at all.

## Anti-patterns

- **Quoting the docs instead of the machine.** The inventory is the map, not the state. Run doctor before saying a tool is available.
- **Installing without asking.** `--yes` touches the whole system. It is their computer, every time.
- **Dressing up a manual step as a command.** Nobody can `brew install` an API key or a billing account. Hand over the specific link.
- **Treating a present key as a working key.** Presence is all doctor can see. Quota, billing and withdrawn models fail at call time.
- **Assuming the sandbox has network.** Every stock lookup and generation call needs it; a host launched without it produces timeouts that look like provider outages.
