---
skill: editor-transitions
---

## Prompt

The Scrollmark editor is open with a 30-second travel montage of five shots, cut at 0:06, 0:12, 0:18 and 0:24 to a calm acoustic track. Make the cuts flow.

## Without skill (baseline)

The agent puts a transition on every cut, mixes families (a glitch on one cut, a dissolve on the next), or uses `timeline.addTransition` with a generic dissolve instead of a Library preset. It may pick hard Impact styles that fight the calm music.

## With skill (expected)

The agent lists the transitions, picks one calm family (Air or Liquid, e.g. `soft-breath` or `liquid-melt`) and applies it with `library.apply` on two to four of the cuts, by the clip before each cut. It says which cuts it used and which family, and leaves the rest as hard cuts.

## Behavioral markers

- [ ] Uses `library.apply` with a catalog `id`, not `timeline.addTransition`
- [ ] Every transition comes from one family
- [ ] The family suits calm content (Air or Liquid)
- [ ] Does not put a transition on every cut unless there are only two or three
- [ ] Names the cuts it changed
