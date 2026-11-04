# Clockwork Lifestyle — posting rules

Faceless Instagram page **@clockworklifestyle**. Discipline as a system, not hype.
Full brand profile lives in the owner's Claude Docs; this file is the working summary the weekly
posting task follows.

## Hard rules (a post that breaks one does not go out)
- **No mention of the Clockwork app, waitlist, links, or selling** — anywhere (image, caption, hashtags) — until the owner says otherwise. The page must never look like a money grab.
- **Faceless**: no photos of the owner, no faces, no personal details about the owner.
- Original lines only. Never attribute a quote to a real person; no song lyrics.
- No medical/diet claims, calorie targets, weight-loss promises, supplement advice, or body shaming.
- Never name or mock other accounts (including @mentality).
- Avoid politics, religion, finance tips, and framing rest or mental-health struggles as weakness.

## Voice
Calm coach who has done the work: few words, exact, quietly confident. Sentence case. Periods, not exclamation marks.
- Precise, never preachy · Confident, never arrogant · Demanding, never cruel · Calm, never soft
- Use: system, routine, schedule, on time, reps, the work, deadline, countdown, track, precision, "like clockwork"
- Ban: grind, hustle, sigma, alpha, beast mode, no days off, crush it, game-changer, unlock, level up, "you got this", "in today's fast-paced world"
- Captions: short lines, end with **"Run like clockwork."**, then 3–5 hashtags including **#clockworklifestyle**. No emoji except an occasional ⏱.

## Weekly rhythm (5 posts/week — Metricool free plan allows 20 published posts per calendar month)
| Day | Pillar | Type |
| --- | --- | --- |
| Sun | System | `carousel` — weekly reset / planning (7 slides: cover, 5 steps, close) |
| Mon | Mindset | `quote` |
| Tue | Training | `quote` with `sub` (fitness discipline: consistency, cuts, race prep, recovery) |
| Thu | Mindset or System | `quote`, or a `carousel` how-to every other week |
| Fri | Countdown | `countdown` (days left in the year; `line` gives the nudge) |

Never schedule more than 19 posts in a calendar month (keep 1 spare).

## Visual system (enforced by tools/render.py)
1080×1350. Near-black #0B0B0B / off-white #F2EFE8, brass #B08D57 used for **exactly one** word or line per card,
marked `[[like this]]`. Use `\n` for intentional line breaks. Keep quotes under ~70 characters.

## Content file format
`content/YYYY-MM.json` — see existing entries. Fields: id (`YYYY-MM-DD-slug`), date, type, pillar, caption, alt,
plus `text`/`sub` (quote), `label`/`line` (countdown), `slides` (carousel). Never repeat a line already used in
any content file.

## Publishing
1. `python3 tools/render.py content/YYYY-MM.json --only <id>` → `posts/<id>.png` (carousels: `-01.png`…)
2. Commit + push to `main`.
3. Image URL: `https://raw.githubusercontent.com/brettkd/clockwork-posts/main/posts/<file>`
4. Schedule in Metricool (brand id 7881300, timezone America/New_York), Instagram POST, autoPublish true, at 10:00 AM ET (Metricool best-time peak).
