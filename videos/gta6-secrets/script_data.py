# "5 GTA 6 Secrets You Probably Didn't Know" — narration, emphasis and shot list.
# Each segment is voiced separately (voice.py); real timings come from the TTS word timestamps
# and are written to timings.json, which render.py / audio.py read.
#
# say:   text sent to the TTS (spelled for pronunciation)
# hl:    words (lower-case, no punctuation) shown in colour in the captions
# shots: (visual plan, cue word) — the shot starts when the cue word is spoken (None = segment start)
# pause: silence after the segment (seconds) — used for suspense beats

SEGMENTS = [
    dict(id="hook", pause=0.15,
         say="Think you know G T A 6? These five secrets will blow your mind.",
         hl={"gta", "6", "five", "secrets", "mind"},
         shots=[("hook_city", None), ("hook_five", "these")]),
    # ---- #5
    dict(id="n5", pause=0.1, say="Number five.", hl={"five"}, shots=[("num5", None)]),
    dict(id="f5", pause=0.2,
         say="Trailer two? Rockstar says every second was captured in-game, on a P S 5. Half gameplay. Half cutscenes.",
         hl={"trailer", "two", "in-game", "ps5", "gameplay", "cutscenes"},
         shots=[("film_strip", None), ("console", "on"), ("split_half", "half")]),
    # ---- #4
    dict(id="n4", pause=0.1, say="Number four.", hl={"four"}, shots=[("num4", None)]),
    dict(id="f4", pause=0.2,
         say="The first trailer leaked, so Rockstar dropped it early. And it still hit ninety million views in twenty-four hours. A Guinness World Record.",
         hl={"leaked", "early", "ninety", "million", "twenty-four", "hours", "guinness", "world", "record"},
         shots=[("leak_alert", None), ("views_counter", "ninety"), ("trophy", "guinness")]),
    # ---- #3
    dict(id="n3", pause=0.1, say="Number three.", hl={"three"}, shots=[("num3", None)]),
    dict(id="f3", pause=0.2,
         say="Those crazy Florida moments? Fans matched many to real viral videos. Like the woman smashing a car, with two hammers.",
         hl={"florida", "real", "viral", "videos", "two", "hammers"},
         shots=[("florida_map", None), ("phone_feed", "fans"), ("hammers", "like")]),
    # ---- #2
    dict(id="n2", pause=0.1, say="Number two.", hl={"two"}, shots=[("num2", None)]),
    dict(id="f2", pause=0.2,
         say="Buying a physical copy? There's no disc in the box. Just a download code. Rockstar confirmed it.",
         hl={"physical", "no", "disc", "download", "code", "confirmed"},
         shots=[("game_box", None), ("box_open", "there's"), ("code_card", "just")]),
    # ---- #1
    dict(id="n1", pause=0.25, say="And number one... is wild.", hl={"one", "wild"}, shots=[("num1", None)]),
    dict(id="f1", pause=0.2,
         say="In 2022, a teen hacker leaked ninety clips of early G T A 6 footage. From a hotel room, while on bail, using an Amazon Fire Stick and the hotel TV. Rockstar says it cost five million dollars. And this week, he pleaded guilty.",
         hl={"teen", "hacker", "ninety", "clips", "hotel", "bail", "fire", "stick", "tv", "five", "million", "dollars", "guilty"},
         shots=[("hacker_terminal", None), ("clips_grid", "leaked"), ("hotel_tv", "from"), ("firestick", "using"), ("money", "rockstar"), ("gavel", "this")]),
    # ---- outro
    dict(id="outro", pause=0.3,
         say="G T A 6 drops November nineteenth. Which one shocked you most? Comment below!",
         hl={"november", "nineteenth", "shocked", "comment"},
         shots=[("release_date", None), ("comments", "which")]),
]

TITLE = "5 GTA 6 Secrets You Probably Didn't Know 🤯 #gta6"
