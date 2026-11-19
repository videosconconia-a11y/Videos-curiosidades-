# "Baby Fruits Sneak Out to Play GTA 6 at Midnight" — two original baby-fruit characters (Blu the blueberry, Peach the peach).
# Fast delivery (~1 min), no music. Voices: narrator af_bella; Blu am_puck +4 st; Peach af_nicole +4 st; Mom af_sarah.
NAR, BLU, PEA, MOM = "af_bella", "am_puck", "af_nicole", "af_sarah"
def L(i, who, say, hl, shots, pause=0.12):
    v = {"n": NAR, "b": BLU, "p": PEA, "m": MOM}[who]
    d = dict(id=i, who=who, voice=v, say=say, hl=set(hl), shots=shots, pause=pause, speed=1.22 if who == "n" else 1.15)
    if who in ("b", "p"): d["pitch"] = 4
    return d
SEGMENTS = [
    L("n1", "n", "It's midnight. GTA six just came out. And these two are supposed to be asleep.", ["midnight.", "six", "asleep."], [("sleep", None)]),
    L("b1", "b", "Hey! Peach! Wake up! It's out!", ["wake", "out!"], [("wake", None)]),
    L("p1", "p", "Blu! Mom said no video games after bedtime!", ["no", "video", "games"], [("argue", None)]),
    L("b2", "b", "Mom is asleep. Come on, let's go!", ["asleep.", "go!"], [("argue2", None)]),
    L("n2", "n", "Step one. Sneak across the kitchen.", ["one.", "sneak"], [("sneak", None)]),
    L("p2", "p", "Shh! Be quiet!", ["shh!", "quiet!"], [("sneak2", None)]),
    L("n3", "n", "Step two. Find the controller.", ["two.", "controller."], [("ctrl", None)]),
    L("b3", "b", "Why is it bigger than me?", ["bigger"], [("ctrl2", None)]),
    L("p3", "p", "Give it! I want to be Lucia!", ["lucia!"], [("fight", None)]),
    L("b4", "b", "Fine! I'm Jason. Press start!", ["jason.", "start!"], [("fight2", None)]),
    L("n4", "n", "Step three. The download.", ["three.", "download."], [("tv", None)]),
    L("b5", "b", "Ninety-nine percent?!", ["ninety-nine", "percent?!"], [("pct", None)]),
    L("p4", "p", "No, no, no!", ["no,", "no!"], [("pct2", None)]),
    L("m1", "m", "Who's making noise down there?!", ["who's", "noise"], [("mom", None)]),
    L("n5", "n", "Step four. Hide!", ["four.", "hide!"], [("hide", None)]),
    L("b6", "b", "Act natural. We're just fruit.", ["natural.", "fruit."], [("hide2", None)]),
    L("m2", "m", "Hmm. Just the fruit bowl.", ["fruit", "bowl."], [("hide3", None)]),
    L("n6", "n", "Download complete.", ["complete."], [("done", None)]),
    L("bp", "b", "Yesss! Let's gooo!", ["yesss!", "gooo!"], [("done2", None)]),
    L("n8", "n", "Ten seconds later.", ["ten", "seconds"], [("crash", None)]),
    L("p5", "p", "Blu! You crashed into the first lamp post?!", ["crashed", "first"], [("crash2", None)]),
    L("b7", "b", "The steering is weird, okay?!", ["weird,"], [("crash3", None)]),
    L("n9", "n", "Six A M. Mom walks into the kitchen.", ["six", "mom"], [("morning", None)]),
    L("m3", "m", "Wait. Why is the fruit bowl empty?", ["empty?"], [("morning2", None)]),
    L("n10", "n", "Spoiler. They fell asleep on the couch. Still holding the controller.", ["asleep", "controller."], [("asleep", None)]),
    L("n7", "n", "Now tag someone who stayed up all night for GTA six, and follow for more!", ["tag", "night", "follow"], [("outro", None)], pause=0.4),
]
DISPLAY = {}
TITLE = "Baby Fruits Sneak Out to Play GTA 6 at Midnight 🫐🍑 #gta6 #animation #shorts #gaming #gta"
