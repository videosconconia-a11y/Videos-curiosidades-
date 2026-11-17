# "GTA 6 WEAPONS ARE GETTING CRAZY!" — narration, keywords, shots (cue word = shot starts when that word is spoken)
SEGMENTS = [
    dict(id="hook", pause=0.15,
         say="Wait... G T A 6 weapons are getting insane. And Rockstar has already named some of them.",
         hl={"gta", "6", "weapons", "insane", "named"},
         shots=[("hook_sparks", None), ("hook_names", "and")]),
    dict(id="w1", pause=0.25,
         say="First, the pistols. Jason carries a Girardi E S 9. Lucia, a Klose K 17. And the Ultimate Edition gives both of them custom engraved versions.",
         hl={"pistols", "girardi", "es9", "klose", "k17", "ultimate", "engraved"},
         shots=[("pistols_wide", None), ("es9", "jason"), ("k17", "lucia"), ("engraved", "and")]),
    dict(id="w2", pause=0.25,
         say="Then there's this. A submachine gun covered in a tropical pattern, straight out of the eighties. It's part of the Vintage Vice City pre-order bonus.",
         hl={"submachine", "gun", "tropical", "pattern", "eighties", "vintage", "vice", "city"},
         shots=[("smg_car", None), ("smg_jason", "straight"), ("smg_pack", "it's")]),
    dict(id="w3", pause=0.3,
         say="And the official screenshots go even harder. Jason with an assault rifle under police choppers. Lucia aiming a pistol point blank. And a shotgun in the key art.",
         hl={"official", "harder", "assault", "rifle", "choppers", "pistol", "shotgun"},
         shots=[("night_rifle", None), ("trailer_rifle", "jason"), ("lucia_pistol", "lucia"), ("shotgun", "shotgun")]),
    dict(id="w4", pause=0.2,
         say="But the craziest one? The Hawk and Little Morgan revolvers. His and hers. Palm tree grips. Their names engraved on the frames. A high-performance scope. And Rockstar says they come from the Verchetti Estate. That's Tommy Verchetti's mansion, from the original Vice City.",
         hl={"craziest", "hawk", "little", "morgan", "revolvers", "palm", "names", "engraved", "scope", "verchetti", "estate", "tommy", "mansion"},
         shots=[("tease", None), ("rev_reveal", "hawk"), ("rev_grips", "palm"), ("rev_engraved", "engraved"), ("rev_scope", "high-performance"), ("vercetti", "rockstar"), ("tommy", "that's")]),
    dict(id="outro", pause=0.35,
         say="Which weapon are you using first in G T A 6? Comment below!",
         hl={"weapon", "first", "gta", "6", "comment"},
         shots=[("question", None)]),
]
TITLE = "GTA 6 WEAPONS ARE GETTING CRAZY! 🔫 #gta6"
DISPLAY = {"VERCHETTI": "VERCETTI", "VERCHETTI'S": "VERCETTI'S"}
