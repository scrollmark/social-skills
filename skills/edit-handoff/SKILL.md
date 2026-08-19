---
name: edit-handoff
description: Use when a finished cut has to leave the pipeline and continue in a human editor — exporting a timeline to Premiere Pro, DaVinci Resolve, Final Cut Pro or CapCut, or answering what survives the trip and what an editor has to rebuild.
---

# Edit Handoff

"Can I finish this in Premiere?" is a handoff, not a render. The job is to move
the tedious half of the edit — forty cuts on their true frames, each clip
pointing at its real source, audio in sync — and to be exact about the half that
does not move, because being vague there costs an editor an afternoon.

## Requires

`scripts/export_edit.py`, `scripts/export_fcpxml.py` and `scripts/export_capcut.py`
from **scrollmark/video-studio** (private). They read that repo's per-project
timeline document, so there is no degraded mode that still produces a file: no
engine, no export. What survives without it is the judgement below — which
format an editor should be asked for, and what to warn them about — which
applies to any OTIO or FCPXML handoff, whoever writes it.

## Which Export, Which Application

| Target | Script | Route |
|---|---|---|
| Premiere Pro, DaVinci Resolve | `export_edit.py` | `.otio`, imported natively — no plugin |
| Final Cut Pro | `export_fcpxml.py` | `.fcpxml` 1.9, opens as a real project |
| CapCut | `export_capcut.py --install` | overwrites `draft_info.json` in an existing project |
| Any of them, another machine | add `--bundle` | copies the media in beside the timeline |

    uv run scripts/export_edit.py --project <dir>

**Always pass `--project`.** It rebuilds that project's timeline first. The
composer's props document is global, so exporting unbuilt silently emits
whichever video was rendered last — a wrong file that looks entirely correct.

There is no `.prproj` writer and there should not be one: Premiere's format is
undocumented, versioned to the application, and a reverse-engineered writer
breaks silently inside someone else's edit. Adobe's supported inbound paths are
OTIO, FCP7 XML, AAF and EDL. FCPXML is the opposite case — Apple publishes it,
which is why Final Cut gets a direct writer.

## What Travels

**Survives everywhere:** every cut at its true frame, each clip linked to its
real source file, per-scene narration, music, and the captions as a sidecar
`.srt` (Premiere imports it as a caption track).

**Does not survive the generic path:** camera moves, fades, and the on-screen
cards. This is not a gap in the exporter — the interchange formats carry no
effects at all; OTIO's own matrix marks effects unsupported across EDL, FCP7
XML, FCP X and AAF alike. So cards are written as **timeline markers carrying
their text** at the frame where each appeared, and camera moves are marked the
same way. The editor does not get the title; they get a labelled spot saying
what belonged there.

**Final Cut is the exception worth naming.** `export_fcpxml.py` writes cards as
real `<title>` elements on Final Cut's Basic Title generator and camera moves as
keyframed `<adjust-transform>`, both editable in the inspector. Measured on a
real project, the generic OTIO→FCPX adapter emitted zero of each. If the cards
matter and the editor is on Final Cut, use this path.

## CapCut Wants an Empty Project First

Ask the user to create one in CapCut itself (File > New Project, save, add
nothing) and hand over the path. The script will not create the folder. A real
project carries a dozen undocumented sibling files — `draft_meta_info.json`,
`draft_settings`, `Resources/`, `matting/` — that only CapCut knows how to
write, and a folder missing them appears in the drafts list and does nothing
when clicked. Cards do not travel here either.

## Anti-patterns

- **Exporting without `--project`.** The failure is silent and ships the wrong video.
- **Saying "it exports the whole video".** It exports the cut. Effects are rebuilt.
- **Promising cards on the OTIO path.** They arrive as markers. Only FCPXML carries them.
- **Claiming app-tested.** The FCPXML is validated by parsing its own output, not by
  opening it in Final Cut. Say which one you mean.
