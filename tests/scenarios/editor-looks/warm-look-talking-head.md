---
skill: editor-looks
---

## Prompt

The Scrollmark editor is open with a talking-head video cut into six clips of the same take. Give it a warm look.

## Without skill (baseline)

The agent puts a filter on one clip only, stacks two filters, or builds a custom `lut` effect with `effects.add` instead of a Library filter. It may pick `moody` or `vintage` at full strength, which turns skin grey.

## With skill (expected)

The agent lists the filters, picks `latte` and applies it with `library.apply` to all six clips in one plan, at a strength that keeps skin natural (default or a little under). It checks a frame after applying and says which filter it used.

## Behavioral markers

- [ ] Uses `library.apply` with a filter `id`
- [ ] The same filter on every clip of the main footage
- [ ] Picks a warm filter (`latte`, or `jade`)
- [ ] No stacked or mixed filters
- [ ] Checks a frame after applying
