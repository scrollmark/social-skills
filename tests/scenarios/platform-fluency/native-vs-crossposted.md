---
skill: platform-fluency
---

## Prompt

Here's a LinkedIn post I saw: "Big news 🚀 Just launched our new feature! #startup #tech #innovation #SaaS #B2B #growth Check it out 👉 link.com/launch"

What's wrong with this?

## Without skill (baseline)

Claude might say the post is fine but could be more detailed. May suggest adding more context about the feature. Unlikely to identify it as violating LinkedIn's native content conventions.

## With skill (expected)

Claude identifies this as cross-posted or written without understanding LinkedIn conventions. Specific issues: hashtag-heavy style belongs on Instagram/Twitter not LinkedIn, the post is too short to trigger dwell time (a key LinkedIn algorithm signal), there's no hook in the first 2-3 lines (the "see more" fold), no story or context that would drive comments, and the external link will get suppressed by LinkedIn's algorithm which favors on-platform content. Suggests a native rewrite: lead with a hook about the problem being solved, tell a brief story, put the link in a comment.

## Behavioral markers

- [ ] Identifies the post as non-native to LinkedIn
- [ ] Calls out hashtag overuse as an Instagram/Twitter pattern
- [ ] Mentions the "see more" fold and hook placement
- [ ] Notes that LinkedIn's algorithm suppresses external links
- [ ] Mentions dwell time as a LinkedIn-specific signal
