---
name: trend-radar
description: Use when evaluating whether a trend is relevant, identifying emerging trends, or advising on trend participation timing.
---

# Trend Radar

Every social media trend follows a lifecycle. Knowing where a trend sits in that lifecycle is more valuable than knowing the trend exists.

## Trend Lifecycle

**Emergence** - small creators, niche communities. The format is still rough and evolving. Few people have seen it. This is where trend-spotters live.

**Growth** - mid-tier creators adopt it. The format solidifies into a repeatable template. Daily volume is climbing. This is the best time to participate - algorithmic boost is highest, the audience isn't tired of it yet.

**Peak** - everyone's doing it, including brand accounts. Your non-social-media friends have seen it. Maximum visibility but diminishing returns for new entries.

**Saturation** - "enough with this trend" comments appear. Engagement rates on new entries drop. Late entries feel like they're behind.

**Ironic revival** - parodies, meta-commentary, "remember when we all did this?" Can be a second window for creators who do meta-humor well.

Growth-to-peak is usually 1-3 weeks. TikTok often moves faster; YouTube topic trends move slower.

## Reading Lifecycle Signals

- Only in niche communities, no major creators yet → **emergence**
- Clear repeatable format, mid-tier creators posting versions, volume climbing → **growth**
- Brand accounts participating, mainstream awareness → **peak**
- "Stop doing this" commentary, dropping engagement on new entries → **saturation**
- Parodies and meta-commentary outnumber sincere entries → **ironic revival**

## Template Extraction

Every trend has a **template** (the repeatable structure) and **instances** (specific executions). Extract what stays the same, then fill the template with the creator's niche and voice. Do not copy someone else's instance.

## Niche Relevance

Not every trend fits every creator. Before participating, ask:

- Does my audience care about this topic or format?
- Can I connect this to my content pillars naturally, or would it feel forced?
- Does participating align with my voice, or would I be performing someone else's style?
- Is there a genuine angle from my niche, or am I just jumping on it for reach?

A fitness creator doing a cooking trend needs a fitness angle. If the connection is forced, skip it.

## Timing

Early participation (growth phase) gets the most algorithmic boost. Peak phase still works but needs a strong unique angle to stand out. Saturation is too late unless you're doing meta-commentary or parody.

Rule of thumb: if you have to ask "is this still trending?" - you're probably late.

## Platform-Specific Mechanics

Load the relevant platform reference from `{repo}/references/platforms/{platform}.md` (read `.root` for repo path). TikTok trends are often sound-driven, Instagram trends are format/template-driven, and YouTube trends move slower.

For X trend checks, if `XQUIK_API_KEY` is set, query `https://xquik.com/api/v1/x/tweets/search` with `q` and `limit` before deciding. Log the query, collection time, sample size, source URLs or post IDs, and caveats. Treat results as directional evidence; weak or missing data should not override prompt and platform signals.
