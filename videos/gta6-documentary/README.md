# GTA 6: The $1 Billion Gamble — How Rockstar Made the Biggest Game Ever (long-form, 16:9)

`final_16x9.mp4`: 1920×1080, 24 fps, ~7:01, −14 LUFS, original score. `thumbnail.jpg` (1280×720). `subtitles.srt` (English).
Build: `./build.sh` (official images in `assets/official`, not in git — all from rockstargames.com/VI).

## Research: what's working right now (YouTube search, 20 Nov 2026, videos 4–20 min uploaded since 17 Nov)
| Video | Views | Language |
|---|---|---|
| ¿QUÉ PASA SI TIENES 6 ESTRELLAS EN GTA VI? — Willyrex | 1.85M | ES |
| GTA 6 – ANÁLISIS SIN SPOILERS — Vandal | 1.30M | ES |
| Entrando al ÁREA 51 en GTA 6 | 590K | ES |
| **Why GTA 6 Took 13 Years and Billions of Dollars? — Zem TV** | **1.51M** | EN |
| What Happens If You Get 6 Stars in GTA 6 — Lootward | 1.42M | EN |
| GTA 6 – Stealing a Jet From the Military Base — TmarTn2 | 6.24M | EN |

The top Spanish ideas (6 stars, Area 51, review) are gameplay-based and already exist in English. The format that works in
both languages **and** can be made honestly with official images is the **documentary/explainer**: "how/why GTA 6 was made".
So: an English doc, original script, every number sourced and estimates labelled.

**About "community images":** screenshots posted by players belong to them; they need each author's permission (or a CC
licence). This video uses **official Rockstar images only**. If you collect permitted community screenshots, they can be
dropped into any segment's `imgs` list in `script_data.py` (with on-screen credit).

## Prompt
> 16:9 YouTube documentary, ~7 min, English, male narrator (calm, confident). Title "GTA 6: The $1 Billion Gamble".
> Cold open with the launch numbers (99 Metacritic, ~$2.36B first-24h estimate), then 8 chapters: GTA V's legacy;
> the quiet years and Rockstar's culture change (Bloomberg 2022); the 2022 leak and Arion Kurtaj's guilty plea;
> Trailer 1's world records; the two delays; Welcome to Leonida (regions + Jason & Lucia from official bios); the budget
> (no official figure, analyst estimates, "it was expensive"); launch week (pre-orders, reviews, 30 fps, day-one estimates);
> outro "Was it worth it?" + subscribe. Visual identity "prestige doc": slow Ken Burns with soft dissolves on official
> images, warm/teal grade, film grain, serif chapter cards, gold big-number callouts with source lines, date stamps, quote
> cards, delay timeline with strike-throughs, budget bar chart, region list, red tags, chapter indicator, progress bar,
> sources footer on every factual segment. Original ambient score ducked under the voice, boom + swell on each chapter.

## Fact check / sources
| Claim | Source |
|---|---|
| 99 Metacritic, ties highest; 118 perfect of 147 PS5 reviews (at time of reporting) | [Notebookcheck](https://www.notebookcheck.net/GTA-6-reviews-award-99-Metacritic-score-topping-GTA-4-to-become-Rockstar-s-top-rated.1453363.0.html), [TechPowerUp](https://www.techpowerup.com/354998/gta-6-review-roundup-99-on-metacritic-and-118-perfect-scores) |
| Day one ~24.5M units / ~$2.36B — **Sensor Tower estimate**, not official | [SFG Media](https://sfg.media/en/a/gta-vi-first-day-sales-25-million-copies-record/), [Mezha](https://mezha.net/eng/news/mezha-249dd9b1eafb8acd419ad364_gta_6_launch-day/), [Globe and Mail](https://www.theglobeandmail.com/business/article-take-two-grand-theft-auto-vi-sales/) |
| ~15.9M digital pre-orders, ~$1.5B — Sensor Tower estimate (Nov 17) | see `../gta6-billion/README.md` |
| GTA V: $800M+ day one, $1B in 3 days, 230M+ units sold-in, RDR2 87M+ | Take-Two reports via [Game Developer](https://www.gamedeveloper.com/business/gta-v-surpasses-230-million-sales-months-before-gta-vi-touches-down); Guinness (2013) |
| 2018 crunch criticism; Bloomberg July 2022: Latina lead, Bonnie & Clyde duo, slower development | [GamesRadar](https://gamesradar.com/gta-6-to-feature-series-first-female-protagonist-as-rockstar-overhauls-workplace-culture), [Game Informer](https://gameinformer.com/report/2022/07/27/report-grand-theft-auto-6-co-stars-a-female-protagonist-rockstar-adopts-more) |
| Feb 4 2022 confirmation; Sept 2022 leak (~90 clips); Rockstar "extremely disappointed", work continues | Rockstar Newswire |
| Kurtaj: 2023 secure-hospital order; guilty plea 16 Nov 2026 at Woolwich Crown Court; sentencing 23 Nov | [TweakTown](https://www.tweaktown.com/news/114727/gta-6-hacker-pleads-guilty-to-all-charges-sentencing-set-days-after-launch/index.html), [Make Tech Easier](https://maketecheasier.com/gta-6-hacker-arion-kurtaj-guilty-plea/), [CBS News](https://www.cbsnews.com/amp/miami/news/grand-theft-auto-leak-teen-hacker-hospitalized) |
| Trailer 1 released early Dec 4 2023; 90,421,491 views/24h; Guinness records | [Push Square](https://pushsquare.com/news/2023/12/gta-6-trailer-pulls-90-million-views-in-24-hours-sets-new-world-records), [Dexerto](https://dexerto.com/gaming/gta-6-trailer-makes-history-after-breaking-three-world-records-2418312) |
| Trailer 2 May 6 2025; delays fall 2025 → May 26 2026 → Nov 19 2026; "We are very sorry…"; stock ~-8% | [VGC](https://www.videogameschronicle.com/news/grand-theft-auto-6-has-been-delayed-to-2026/), [T3](https://www.t3.com/tech/gaming/grand-theft-auto-vi-release-date-gta-6) |
| No official budget; analysts $1–1.5B; Citi ~$1.4B (WSJ); GTA V ~$265M; Zelnick "it was expensive" | [Nacionale](https://www.nacionale.com/en/articles/how-much-did-gta-6-cost-to-make-budget-1-billion-has-it-paid-off), [thepricer](https://www.thepricer.org/how-much-did-gta-6-cost-to-make/) |
| 30 fps on consoles; "single most visually striking game of the generation" — Digital Foundry | see `../gta6-30fps/README.md` |
| Leonida regions; Jason & Lucia descriptions | rockstargames.com/VI (official) |

## Publishing text
**Title:** GTA 6: The $1 Billion Gamble — How Rockstar Made the Biggest Game Ever

**Description:**
13 years. 2 delays. 1 historic leak. And maybe the most expensive game ever made. This is the story of how Rockstar Games made GTA 6 — and how the gamble paid off.

0:00 Intro
0:39 Chapter 1 – The Monster It Had To Beat
1:34 Chapter 2 – The Quiet Years
2:20 Chapter 3 – The Leak
3:04 Chapter 4 – The Trailer That Broke The Internet
3:58 Chapter 5 – The Delays
4:27 Chapter 6 – Welcome To Leonida
5:18 Chapter 7 – The Billion Dollar Question
5:53 Chapter 8 – Launch Week
6:44 Was It Worth It?

What do you think of GTA 6 so far? Tell me in the comments 👇 and subscribe for more GTA 6 stories.

Sources: Take-Two Interactive reports, Rockstar Newswire, Bloomberg (via GamesRadar/Game Informer), Guinness World Records, Metacritic, Digital Foundry, Sensor Tower estimates (via The Globe and Mail, SFG Media), CPS (via TweakTown), Business Insider/WSJ analyst estimates. Sales and budget figures are estimates unless stated as official.
Images © Rockstar Games. Fan-made documentary, not affiliated with Rockstar Games or Take-Two Interactive.

#gta6 #gtavi #grandtheftauto6 #rockstargames #gta6documentary #gaming #vicecity

**Tags:** gta 6 documentary, how gta 6 was made, gta 6 budget, why gta 6 took 13 years, gta 6 development, gta 6 leak, gta 6 delays, gta 6 sales, gta 6 metacritic, gta 6 story, rockstar games, grand theft auto vi, take two, gta 6 explained, gta 6 history

**Pinned comment:** Was GTA 6 worth the 13-year wait? 👇 YES / NO + your score out of 10 #gta6 #gtavi #gaming
