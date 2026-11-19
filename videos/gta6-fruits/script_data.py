# "Banana Said Just ONE Hour of GTA 6" — original anthropomorphic-fruit drama skit (no game footage, no claims).
# Voices (Kokoro): narrator af_bella, Banana am_puck, Strawberry af_nicole.
N_, B_, S_ = "af_bella", "am_puck", "af_nicole"
SEGMENTS = [
    dict(id="hook", pause=0.25, voice=N_, say="Banana promised his girlfriend just one hour of GTA six.",
         hl={"banana", "one", "hour"}, who="n", shots=[("hook", None)]),
    dict(id="t7", pause=0.1, voice=N_, say="Seven P M.", hl={"seven"}, who="n", shots=[("pm7", None)]),
    dict(id="s1", pause=0.15, voice=S_, say="Babe, our dinner is at eight.", hl={"dinner", "eight."}, who="s", shots=[("pm7b", None)]),
    dict(id="b1", pause=0.25, voice=B_, say="Yeah, one more mission.", hl={"one", "more", "mission."}, who="b", shots=[("pm7c", None)]),
    dict(id="t11", pause=0.1, voice=N_, say="Eleven P M.", hl={"eleven"}, who="n", shots=[("pm11", None)]),
    dict(id="b2", pause=0.25, voice=B_, say="One more mission, babe. I promise.", hl={"one", "more", "promise."}, who="b", shots=[("pm11b", None)]),
    dict(id="t3", pause=0.25, voice=N_, say="Three A M. Banana is starting to turn brown.", hl={"three", "brown."}, who="n", shots=[("am3", None)]),
    dict(id="t4", pause=0.15, voice=N_, say="Then Strawberry walks in, with her own controller.", hl={"strawberry", "own", "controller."}, who="n", shots=[("twist", None)]),
    dict(id="s2", pause=0.3, voice=S_, say="Wait. You're still on chapter one?", hl={"still", "chapter", "one?"}, who="s", shots=[("twist2", None)]),
    dict(id="outro", pause=0.35, voice=N_, say="Tag the banana in your life, and follow for more videos!", hl={"tag", "banana", "follow"}, who="n", shots=[("outro", None)]),
]
DISPLAY = {}
TITLE = "Banana Said Just ONE Hour of GTA 6 🍌😭 #gta6 #animation #shorts #gaming #gta"
