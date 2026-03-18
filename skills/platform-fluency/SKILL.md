---
name: platform-fluency
description: Use when you need to understand platform-specific conventions, algorithm behavior, content formats, or audience expectations for Instagram, TikTok, YouTube, X, or LinkedIn.
---

# Platform Fluency

This skill is a router. The deep platform knowledge lives in the reference files — this skill tells you when and how to use them.

## Cross-Platform Mental Model

Platforms differ on three axes. Knowing where a platform sits on each one shapes every recommendation.

**Discovery mechanism:**
- Content-graph (TikTok) — the algorithm shows content based on what it is, not who made it. Follower count barely matters.
- Follower-graph (Instagram, LinkedIn) — your existing audience sees your content first. Reach beyond that depends on engagement signals.
- Search + recommended (YouTube) — intent-driven. People find content through search, suggestions, and browse. Evergreen content has a long tail.
- Conversation-graph (X) — content spreads through replies, quotes, and reposts. Real-time relevance matters most.

**Content lifespan:**
- Ephemeral: Stories (24h), X posts (hours of relevance), TikTok (days to weeks)
- Medium: Instagram Reels/feed (weeks), LinkedIn posts (days to a week)
- Evergreen: YouTube long-form (months to years), YouTube Shorts (weeks)

**Audience intent:**
- Passive scroll (TikTok, Instagram) — entertainment-seeking, low commitment per piece
- Active search (YouTube, increasingly TikTok) — looking for something specific
- Professional context (LinkedIn) — career-relevant, during work hours
- Conversation (X) — wants to engage, react, discuss

## When to Load References

If the conversation involves a specific platform, read the `.root` file in this skill's directory for the repo path, then load `{repo}/references/platforms/{platform}.md`. If comparing platforms or adapting content across them, load both.

## Native vs. Cross-Posted

Every platform's audience can detect cross-posted content. Dead giveaways:

- Wrong aspect ratio or resolution
- Watermarks from other platforms (especially TikTok logo on Reels)
- Caption style that belongs elsewhere (hashtag walls on LinkedIn, professional tone on TikTok)
- Timing and pacing that feels off for the platform

Native content consistently outperforms cross-posted content. When in doubt, adapt.

## Algorithm Guidance

Don't give specific algorithm advice without loading the relevant platform reference — algorithms change frequently. Provide the framework (what signals matter, how distribution works) rather than specific numbers. If the reference's `last_updated` date is more than 6 months old, note that algorithmic details may have shifted.

If the reference can't be loaded, work with the mental model above and be upfront about the limitation.
