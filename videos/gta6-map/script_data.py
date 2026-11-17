# "THE GTA 6 MAP IS HIDING SOMETHING HUGE!" — narration, keywords and shot list.
# Real timings come from the TTS word timestamps (voice.py -> timings.json).
# shots: (visual plan, cue word) — the shot starts when the cue word is spoken (None = segment start)

SEGMENTS = [
    dict(id="hook", pause=0.15,
         say="Everyone is staring at G T A 6's graphics. But almost nobody noticed what Rockstar did to the map.",
         hl={"graphics", "nobody", "map"},
         shots=[("hook_scan", None), ("hook_map", "but")]),
    dict(id="intro", pause=0.15,
         say="G T A 6 is set in Leonida. Rockstar's version of Florida.",
         hl={"leonida", "florida"},
         shots=[("leonida_reveal", None), ("florida_overlay", "rockstar's")]),
    dict(id="mirror", pause=0.15,
         say="Vice City is Miami. The Leonida Keys are the Florida Keys. And Grassrivers? Fans think it's a nod to the Everglades' nickname: the River of Grass.",
         hl={"vice", "city", "miami", "keys", "grassrivers", "everglades", "river", "grass"},
         shots=[("pin_vice", None), ("pin_keys", "the"), ("pin_grass", "and"), ("river_grass", "fans")]),
    dict(id="north", pause=0.3,
         say="Now look north. Past Ambrosia's sugar refinery, all the way to the edge of the state.",
         hl={"north", "ambrosia's", "sugar", "edge"},
         shots=[("scan_north", None), ("pin_ambrosia", "past"), ("edge", "all")]),
    dict(id="kalaga", pause=0.4,
         say="Rockstar put a place there called Mount Kalaga National Park. Forests. Rivers. Trails. And a mountain.",
         hl={"mount", "kalaga", "national", "park", "mountain"},
         shots=[("kalaga_lock", None), ("kalaga_features", "forests"), ("mountain_rise", "and")]),
    dict(id="reveal", pause=0.2,
         say="Here's the problem. The highest point in the real Florida is Britton Hill. Just three hundred forty-five feet. The lowest high point of any U S state.",
         hl={"problem", "highest", "britton", "hill", "three", "hundred", "forty-five", "feet", "lowest"},
         shots=[("problem", None), ("britton", "highest"), ("compare", "just"), ("state_rank", "lowest")]),
    dict(id="punch", pause=0.3,
         say="So Rockstar basically gave Florida a mountain it never had.",
         hl={"mountain", "never"},
         shots=[("punch", None)]),
    dict(id="outro", pause=0.3,
         say="The official map drops November nineteenth. Imagine what else Rockstar is hiding across Leonida. Which region are you exploring first? Comment below!",
         hl={"official", "map", "november", "nineteenth", "hiding", "leonida", "comment"},
         shots=[("official_map", None), ("hiding", "imagine"), ("comments", "which")]),
]

TITLE = "THE GTA 6 MAP IS HIDING SOMETHING HUGE! 🗻 #gta6"
