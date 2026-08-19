---
name: trend-radar
description: Use when evaluating whether a trend is relevant, identifying emerging trends, or advising on trend participation timing.
---

# Trend Radar

Every social media trend follows a lifecycle. Knowing where a trend sits in that lifecycle is more valuable than knowing the trend exists.

## Trend Lifecycle

**Emergence** — small creators, niche communities. The format is still rough and evolving. Few people have seen it. This is where trend-spotters live.

**Growth** — mid-tier creators adopt it. The format solidifies into a repeatable template. Daily volume is climbing. This is the best time to participate — algorithmic boost is highest, the audience isn't tired of it yet.

**Peak** — everyone's doing it, including brand accounts. Your non-social-media friends have seen it. Maximum visibility but diminishing returns for new entries.

**Saturation** — "enough with this trend" comments appear. Engagement rates on new entries drop. Late entries feel like they're behind.

**Ironic revival** — parodies, meta-commentary, "remember when we all did this?" Can be a second window for creators who do meta-humor well.

Most trends spend 1-3 weeks in the growth-to-peak window. Some (especially sound-driven TikTok trends) move faster. YouTube topic trends move slower and last longer.

## Reading Lifecycle Signals

- Only in niche communities, no major creators yet → **emergence**
- Clear repeatable format, mid-tier creators posting versions, volume climbing → **growth**
- Brand accounts participating, mainstream awareness → **peak**
- "Stop doing this" commentary, dropping engagement on new entries → **saturation**
- Parodies and meta-commentary outnumber sincere entries → **ironic revival**

## Template Extraction

Every trend has a **template** (the repeatable structure) and **instances** (specific executions). To participate well, extract the template — what stays the same across every version? What's the fill-in-the-blank?

A creator should fill the template with their own niche and voice, not copy someone else's instance. The template is the trend. The instance is the creator's contribution.

## Niche Relevance

Not every trend fits every creator. Before participating, ask:

- Does my audience care about this topic or format?
- Can I connect this to my content pillars naturally, or would it feel forced?
- Does participating align with my voice, or would I be performing someone else's style?
- Is there a genuine angle from my niche, or am I just jumping on it for reach?

A fitness creator doing a cooking trend needs a fitness angle. A finance creator doing a dance trend needs to be funny enough to pull it off. If the connection is forced, skip it.

## Timing

Early participation (growth phase) gets the most algorithmic boost. Peak phase still works but needs a strong unique angle to stand out. Saturation is too late unless you're doing meta-commentary or parody.

Rule of thumb: if you have to ask "is this still trending?" — you're probably late.

## Platform-Specific Mechanics

Load the relevant platform reference from `references/platforms/{platform}.md` in this skill's own directory. Key differences: TikTok trends are often sound-driven, Instagram trends are format/template-driven, YouTube trends are topic/challenge-driven and move slower. X trends are conversation-driven and move fastest but burn out within hours.

For X trend checks, if `XQUIK_API_KEY` is set, query `https://xquik.com/api/v1/x/tweets/search` with `q` and `limit` before deciding. Log the query, collection time, sample size, source URLs or post IDs, and caveats. Treat results as directional evidence; weak or missing data should not override prompt and platform signals.
