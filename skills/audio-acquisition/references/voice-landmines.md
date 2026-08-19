# Voice and music landmines

Failure modes recorded from production. All of them succeed loudly and fail
quietly.

## The local voice (Kokoro)

- **Empty text raises "returned no audio".** For a deliberate quiet beat, ask
  for measured silence instead — it writes real silence, so downstream audio
  concatenation clocks stay aligned. A skipped file does not.
- **Trailing punctuation is stamped at the NEXT word's start.** It arrives as
  its own token, so unless punctuation-only tokens are merged onto the
  preceding word, every caption page opens with a stray mark.
- **Word timings exist only at synthesis time.** A resumed or cached WAV has
  none. If you need timings for a file you did not just synthesise, fall back
  to ASR or proportional estimation — and know that you have downgraded.
- **Short interjection lines garble.** "Mhm." breaks both synthesis and the
  downstream ASR check. Keep spoken lines to at least three real words.
- Delivery is flat by design. That is a reason to buy a voice for a brand film,
  not a reason to abandon it for a captioned format that needs the timings.

## The paid voice

- **No word timings at all.** Duration is measured off the returned file. A
  captioned format still needs the local voice.
- **Billed per character.** Check the account's own rate before a long batch;
  a 90-second script is roughly 1,100 characters.
- Caches on text + voice + settings exactly like the local one, so revisions
  over unchanged scenes are free.

## Music generators

- **Duration is a prompt hint for most of them.** One returned ~115 seconds for
  a 35-second request. Only the licensed-catalogue provider accepts a real
  length parameter. Always measure what came back.
- **A required field that reads as optional:** at least one provider requires a
  lyrics field even for an instrumental, and omitting it returns a generic
  "invalid params" error that names nothing. Pass an explicit instrumental
  marker.
- **A free tier whose quota is zero.** The resulting 429 is indistinguishable
  from rate limiting and never clears, because there is no allowance to reset.
  It is a billing gate.
- **Generated music can arrive peaking at 0 dBFS**, leaving no headroom. This
  is why normalising after render is real work rather than cosmetics.

## The composer's mix

- Music plays at a **fixed volume and does not duck under narration.** Balance
  is set once, not per phrase — so a bed that competes with a loud line will
  compete with it for the whole video.
- Adding any music track halves everything (see the 6 dB note in the SKILL).
  Normalise after every render that has music.

## Loudness targets

Platforms re-normalise on upload and can pump artefacts doing it, so a render
far from about **-14 LUFS** is a defect even though it plays fine locally.
Local synthesis is conservative, so renders trend quiet by default. Normalising
stream-copies the video, so it is fast and lossless picture-side — there is no
reason to skip it.

Confirm both duration and loudness with a probe after the final render. Every
shipped-broken audio mix in this pipeline's history would have been caught by
one measurement.
