---
skill: voice-matching
---

## Prompt

Here are three captions from a travel creator:

1. "Showed up in Tokyo with zero plans and honestly? Best decision. Found this tiny ramen spot down an alley that Google doesn't even know about. Old dude making noodles for 40 years. No menu. You eat what he makes. Transcendent."

2. "Hot take: you don't need a travel itinerary. You need three things — comfortable shoes, a charged phone, and the willingness to get completely lost. Everything interesting happens off the map."

3. "Prague at 6am when the tourists are still sleeping is a different city entirely. Just you and the pigeons and 600 years of architecture doing its thing. No filter needed, literally."

Write a fourth caption about discovering a hidden beach in Portugal.

## Without skill (baseline)

Claude writes something generic and travel-blog-ish: "Just discovered the most amazing hidden beach in Portugal! The crystal-clear waters and golden sand took my breath away..." Captures the topic but not the voice.

## With skill (expected)

Claude first analyzes the voice dimensions — short punchy fragments, "honestly?" as a rhythm marker, specific sensory details, dry humor, no exclamation marks, direct address that feels like talking to a friend, confident takes. Then writes a caption that matches: fragment-heavy, specific detail about the beach, probably a wry observation, ends with a short punchy closer. Should feel like caption 1-3, not like a travel brochure.

## Behavioral markers

- [ ] Explicitly analyzes voice elements from the examples before writing
- [ ] Identifies specific patterns (fragments, rhythm, humor style, no exclamation marks)
- [ ] Generated caption uses fragments and short sentences
- [ ] Generated caption includes a specific sensory detail (not generic "beautiful beach")
- [ ] Generated caption avoids exclamation marks and generic travel language
- [ ] Generated caption could plausibly be attributed to the same person who wrote 1-3
