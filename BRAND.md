# Clockwork Lifestyle — posting rules

Faceless Instagram page **@clockworklifestyle** (display name "Clockwork Lifestyle | Discipline & Routines").
Discipline as a system, not hype. Full brand profile lives in the owner's Claude Docs; this file is the
working summary the weekly posting task follows.

## Hard rules (a post that breaks one does not go out)
- **No mention of the Clockwork app, waitlist, links, or selling** — anywhere (image, caption, hashtags) — until the owner says otherwise. The page must never look like a money grab.
- **Faceless**: no photos of the owner, no faces, no personal details about the owner.
- Original lines and original designs only (Instagram removes reposters/aggregators from recommendations since Apr 2026). Never attribute a quote to a real person; no song lyrics; no third-party watermarks.
- No medical/diet claims, calorie targets, weight-loss promises, supplement advice, or body shaming.
- Never name or mock other accounts (including @mentality).
- Avoid politics, religion, finance tips, and framing rest or mental-health struggles as weakness.

## Reach rules (from the Nov 2026 algorithm research — apply to every post)
1. **Design for sends.** DM shares ("sends") are the strongest signal for reaching non-followers. Every post must be something a person would forward to a specific friend. Most posts end on a slide or caption line that names *who* to send it to ("Send this to someone who…").
2. **Carousels over single images.** Single images get the least reach. Every hook card is a carousel of at least 3 slides: hook (`quote`/`countdown`) → `note` (one short explanation) → `cta` (send / save / comment prompt). How-tos are 7-slide carousels.
3. **One Reel per week** (Tuesday). Reels get the most non-follower reach. Text is on screen from frame 0 (the hook), 2–4 short lines, ~8–10 s, original ticking-clock audio from the renderer (no licensed music).
4. **Rotate the call to action** across the week: send (≥2/week), save (how-tos), comment question (countdowns). Questions invite replies — two-way conversation is a ranking signal.
5. **Keyword-first captions.** Hashtags are capped at 5, so captions carry search. The first line (first ~125 characters) states the topic in plain search words: discipline, self-discipline, routine, morning routine, habits, productivity, goal setting, consistency, training, fitness motivation. No keyword stuffing.
6. **Hashtags: exactly 3–5**, specific over generic: 1–2 topic tags, 1 community tag, 1 broader tag, always **#clockworklifestyle**. Never #love/#instagood-style tags.
7. **Alt text on every image**, describing the actual text on the card.
8. Stay in the niche (discipline, routines, goals, training). Consistency of topic helps Instagram place the page.

## Voice
Calm coach who has done the work: few words, exact, quietly confident. Sentence case. Periods, not exclamation marks.
- Precise, never preachy · Confident, never arrogant · Demanding, never cruel · Calm, never soft
- Use: system, routine, schedule, on time, reps, the work, deadline, countdown, track, precision, "like clockwork"
- Ban: grind, hustle, sigma, alpha, beast mode, no days off, crush it, game-changer, unlock, level up, "you got this", "in today's fast-paced world"
- Captions: keyword first line, short lines, CTA line, then **"Run like clockwork."**, then 3–5 hashtags including **#clockworklifestyle**. No emoji except an occasional ⏱.

## Weekly rhythm (5 posts/week — Metricool free plan publishes 20 posts per calendar month)
| Day | Pillar | Type |
| --- | --- | --- |
| Sun | System | `carousel` — weekly reset / planning how-to (7 slides: cover, 5 steps, close). CTA: save. |
| Mon | Mindset | `carousel` — quote → note → cta. CTA: send. |
| Tue | Training | `reel` — 2–4 lines, fitness discipline (consistency, recovery, race prep, showing up). CTA: send. |
| Thu | Mindset or System | `carousel` — 3-slide quote, or a 7-slide how-to every other week. CTA: send or save. |
| Fri | Countdown | `carousel` — countdown → note → cta. CTA: comment question. |

Never schedule more than 19 posts in a calendar month (keep 1 spare).

## Visual system (enforced by tools/render.py)
Feed: 1080×1350. Reel: 1080×1920 mp4 + cover jpg. Near-black #0B0B0B / off-white #F2EFE8, brass #B08D57 used for
**exactly one** word or line per card, marked `[[like this]]`. Use `\n` for intentional line breaks. Keep hook
quotes under ~70 characters. Read the docstring at the top of tools/render.py for every slide kind.

## Content file format
`content/YYYY-MM.json` — see existing entries. Fields: id (`YYYY-MM-DD-slug`), date, type (`carousel` or `reel`),
pillar, caption, `alt` (a list, one entry per slide/video), plus `slides` (carousel) or `lines`/`end` (reel).
Never repeat a line already used in any content file.

## Publishing
1. `python3 tools/render.py content/YYYY-MM.json --only <id>` → `posts/<id>-01.png`… (carousel) or `posts/<id>.mp4` + `posts/<id>-cover.jpg` (reel)
2. Look at every render; commit + push to `main`.
3. Media URL: `https://raw.githubusercontent.com/brettkd/clockwork-posts/main/posts/<file>`
4. Schedule in Metricool (brand id 7881300, timezone America/New_York) at **10:00 AM ET** (Metricool best-time peak), autoPublish true.
   Carousel: instagramData {"type":"POST","isAiGenerated":false}. Reel: instagramData {"type":"REEL","showReelOnFeed":true,"isAiGenerated":false} plus `videoThumbnailUrl` = the cover jpg URL.
