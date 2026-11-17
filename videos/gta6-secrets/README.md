# 5 GTA 6 Secrets You Probably Didn't Know — YouTube Short (EN-US)

Vertical 9:16 · 1080×1920 · 30 fps · ~59 s · H.264 + AAC 256k, loudness-normalised to −14 LUFS.

**Deliverables** (created by `./build.sh`; the mp4/wav files are git-ignored): `final_9x16.mp4`, `subtitles.srt`, and the publishing text below.

## Pipeline
| Step | File | What it does |
|---|---|---|
| Script | `script_data.py` | Narration, highlighted keywords, shot list with cue words |
| Voice | `voice.py` | Kokoro-82M TTS (open weights, Apache-2.0), voice `af_bella` (US English), speed 1.18. Writes `voice.wav` and word-level `timings.json` |
| Music + SFX | `audio.py` | Original 118 BPM synthwave (pad, bass, arp, drums) with a filtered intro and a drop at secret #5, a breakdown before #1, risers, booms, whooshes, glitches, clicks, cash register and gavel. Side-chain ducking: music sits ~11 dB lower while the voice speaks |
| Visuals | `render.py` | Original procedural motion graphics in a neon Vice City look: synthwave sunset skyline, number cards, counters, stamps, a hand-drawn circle and arrows, punch-in zooms, whip-blur, RGB-split, flashes and camera shake. Word-by-word animated captions with coloured keywords |
| Subtitles | `subs.py` | `subtitles.srt` for upload |

Fonts: Anton, Bebas Neue and Montserrat (SIL OFL), in `fonts/`.

**Copyright:** the video uses no Rockstar trailer footage, screenshots or logos, and no third-party music or samples. Everything is generated here. If you have rights-cleared official material, such as Rockstar press-kit images, you can swap it into the backgrounds in `render.py` (`BG_SUN` / `BG_NIGHT`).

## Fact check (verified 17 Nov 2026)
**#5 — Trailer 2 was captured entirely in-game on PS5, with equal parts gameplay and cutscenes.** Rockstar confirmed this on X, and the end card reads "Captured on PS5."
- https://www.psu.com/news/rockstar-confirms-gta-vi-trailer-2-was-captured-entirely-in-game-on-ps5-mixes-cutscene-footage-and-gameplay/
- https://www.gamesradar.com/games/grand-theft-auto/rockstar-says-gta-6-trailer-2-was-equal-parts-gameplay-and-cutscenes-and-im-wondering-where-the-gameplay-was

**#4 — Trailer 1 leaked, so Rockstar released it early (Dec 2023). It got 90,421,491 views in 24 hours, which Guinness recognised as the most-viewed video game reveal on YouTube in 24 h.**
- https://pushsquare.com/news/2023/12/gta-6-trailer-pulls-90-million-views-in-24-hours-sets-new-world-records
- https://techcrunch.com/2023/12/05/grand-theft-auto-vi-trailer-breaks-mrbeasts-record-for-most-youtube-views-in-24-hours/
- https://dexerto.com/gaming/gta-6-trailer-makes-history-after-breaking-three-world-records-2418312

**#3 — Many "Florida Man" moments in trailer 1 parody real viral videos, including the woman smashing a car with two hammers (a 2020 viral clip).** This is a **fan / press discovery, not confirmed by Rockstar**, so the video labels it "FAN DISCOVERY" and the narration says "fans matched…".
- https://knowyourmeme.com/editorials/every-reference-to-real-life-videos-in-the-grand-theft-auto-vi-trailer
- https://www.denofgeek.com/games/the-gta-6-trailers-best-easter-eggs-references-and-hidden-details/
- https://boingboing.net/2023/12/06/the-grand-theft-auto-6-trailer-recreates-real-bizarre-florida-moments.html

**#2 — The physical edition has no disc, only a download code in the box.** Rockstar confirmed it.
- https://videogameschronicle.com/news/rockstar-confirms-there-will-be-no-disc-version-of-gta6-at-launch/
- https://www.pushsquare.com/news/2026/06/gta-6-physical-edition-doesnt-come-with-discs-its-a-code-in-the-box

**#1 — In Sept 2022 a teenage hacker (Arion Kurtaj, then 17) leaked ~90 clips of early GTA 6 footage. He did it while on bail and staying in a Travelodge hotel, using an Amazon Fire TV Stick plugged into the hotel TV, plus a phone, keyboard and mouse. Rockstar said the breach cost about $5 million. He pleaded guilty at Woolwich Crown Court on 16 Nov 2026; sentencing is set for 23 Nov.**
- https://kotaku.com/grand-theft-auto-6-leak-gta6-hacker-pleads-guilty-2000757500
- https://engadget.com/2318001/gta-6-hacker-pleads-guilty-to-stealing-and-leaking-gameplay-footage
- https://www.notebookcheck.net/Hacker-behind-2022-GTA-6-leaks-pleads-guilty-sentencing-set-for-November-23.1452228.0.html
- https://cbsnews.com/miami/technology/8

**Outro — GTA 6 launches 19 Nov 2026 on PS5 and Xbox Series X|S.**
- https://tech.yahoo.com/gaming/articles/gta-6-releases-week-heres-110332150.html
- https://dotesports.com/gta/news/gta-6

Popular claims I left out because they are not verified: the "hidden QR code" in the trailers, the voice-actor names, and Phil Cassidy's return (still fan speculation).

## Publishing text
**Title:** 5 GTA 6 Secrets You Probably Didn't Know 🤯 #gta6

**Description:**
GTA 6 drops November 19 — but did you know these 5 secrets? 🤯
#5 Trailer 2 was captured 100% in-game on PS5
#4 The leaked first trailer still set a Guinness World Record
#3 Fans matched trailer moments to REAL viral Florida videos
#2 The physical edition has NO disc
#1 The hacker who leaked GTA 6… used a Fire Stick and a hotel TV 😳

Which one shocked you most? Comment your number 👇

Facts verified with Rockstar statements and gaming/news coverage (Kotaku, Engadget, VGC, Guinness/Push Square). #3 is a fan discovery. Fan-made video: not affiliated with or endorsed by Rockstar Games or Take-Two Interactive.

**Hashtags:** #gta6 #gtavi #grandtheftauto6 #gta6news #rockstargames #gaming #gamingshorts #shorts #vicecity #gta6trailer

**Tags:** gta 6, gta 6 secrets, gta 6 release date, gta 6 hacker, gta 6 physical copy no disc, gta 6 trailer 2, gta 6 easter eggs, grand theft auto vi, vice city, leonida
