# "POV: You Waited 13 Years for GTA 6" — original flat CARTOON skit (no game footage, no Rockstar art or logos).
# One recurring character ("the Waiter") ages from kid (2013) to tired adult (2026) in the same bedroom; the TV, calendar,
# poster and wall colour tell the story. Thick outlines, bouncy squash & stretch, blinking, tears, rage shake.
# Drawn at 2x and downsampled for smooth edges. Usage: still <t>... | video <worker> <nworkers>
import sys, os, math, json, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

W, H, FPS, S = 1080, 1920, 30, 2
FD = os.path.join(HERE, "fonts")
@lru_cache(maxsize=64)
def MS(s, w=800):
    f = ImageFont.truetype(os.path.join(FD, "Montserrat-VF.ttf"), int(s))
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
@lru_cache(maxsize=32)
def ANTON(s): return ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), int(s))
OUT = (25, 20, 35); WHITE = (255, 255, 255); SKIN = (255, 205, 160); PINK = (255, 60, 140); ORANGE = (255, 150, 40)
RED = (235, 50, 50); BLUE = (80, 170, 255); GREEN = (60, 200, 110); YEL = (255, 214, 0)

TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg, word, nth=0): return [w["a"] for w in SEGT[seg]["words"] if clean(w["w"]) == clean(word)][nth]
def build_shots():
    out = []; segs = TM["segments"]
    for i, (sd, st_) in enumerate(zip(SEGMENTS, segs)):
        s0 = 0.0 if i == 0 else st_["a"] - 0.1
        s1 = segs[i + 1]["a"] - 0.1 if i + 1 < len(segs) else TOTAL
        starts = [(s0 if c is None else word_time(sd["id"], c) - 0.08, n) for n, c in sd["shots"]]
        for j, (a, n) in enumerate(starts):
            out.append((a, starts[j + 1][0] if j + 1 < len(starts) else s1, n, sd["id"]))
    return out
SHOTS = build_shots()
def st(n): return [s[0] for s in SHOTS if s[2] == n][0]
def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.7): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def speaking(t):
    for sg in TM["segments"]:
        for w in sg["words"]:
            if w["a"] <= t <= w["b"]: return True
    return False

# ---------------------------------------------------------------- per-shot setup
YEAR = {"kid": "2013", "y2013": "2013", "y2018": "2018", "y2023": "2023", "delay": "2025", "y2026": "2026", "press": "2026", "stuck": "2026", "outro": "2026"}
WALL = {"2013": ((120, 190, 255), (90, 150, 230)), "2018": ((150, 130, 230), (110, 95, 200)), "2023": ((255, 150, 120), (225, 110, 95)),
        "2025": ((120, 110, 140), (90, 80, 110)), "2026": ((255, 110, 170), (230, 80, 140))}
STAGE = {"kid": "kid", "y2013": "kid", "y2018": "teen", "y2023": "young", "delay": "young", "y2026": "adult", "press": "adult", "stuck": "adult", "outro": "adult"}
MOOD = {"kid": "happy", "y2013": "proud", "y2018": "bored", "y2023": "cry", "delay": "angry", "y2026": "tired", "press": "excited", "stuck": "scream", "outro": "happy"}

def P(v): return v * S
def PW(v): return max(1, int(round(v * S)))
def rr(d, box, r, fill, ow=8):
    d.rounded_rectangle([P(box[0]), P(box[1]), P(box[2]), P(box[3])], radius=PW(r), fill=fill, outline=OUT, width=PW(ow))
def el(d, box, fill, ow=8):
    d.ellipse([P(box[0]), P(box[1]), P(box[2]), P(box[3])], fill=fill, outline=OUT if ow else None, width=PW(ow) if ow else 0)
def tx(d, cx, y, s, f, fill, stroke=0):
    w = d.textlength(s, font=f); d.text((P(cx) - w / 2, P(y)), s, font=f, fill=fill, stroke_width=PW(stroke), stroke_fill=OUT)

def room(d, name, t):
    yr = YEAR[name]; c1, c2 = WALL[yr]
    for i in range(0, H, 40):
        k = i / H; col = tuple(int(a + (b - a) * k) for a, b in zip(c1, c2)); d.rectangle([0, P(i), P(W), P(i + 40)], fill=col)
    d.rectangle([0, P(1330), P(W), P(H)], fill=(110, 75, 60)); d.line([0, P(1330), P(W), P(1330)], fill=OUT, width=PW(8))
    for x in range(0, W, 140): d.line([P(x), P(1330), P(x - 60), P(H)], fill=(95, 64, 52), width=PW(4))
    # window (night in 2025, else day)
    rr(d, (40, 300, 230, 480), 16, (40, 40, 90) if yr == "2025" else (190, 235, 255))
    d.line([P(135), P(300), P(135), P(480)], fill=OUT, width=PW(6)); d.line([P(40), P(390), P(230), P(390)], fill=OUT, width=PW(6))
    # calendar with the year
    rr(d, (850, 300, 1040, 490), 14, WHITE); d.rectangle([P(850), P(300), P(1040), P(350)], fill=RED, outline=OUT, width=PW(8))
    tx(d, 945, 360, yr, ANTON(PW(84)), OUT)

def tv(d, name, t, age):
    rr(d, (190, 520, 890, 930), 26, (40, 40, 48), 10); x0, y0, x1, y1 = 225, 555, 855, 895
    d.rounded_rectangle([P(x0), P(y0), P(x1), P(y1)], radius=PW(12), fill=(15, 15, 25))
    d.rectangle([P(520), P(930), P(560), P(975)], fill=(40, 40, 48)); rr(d, (430, 965, 650, 995), 10, (40, 40, 48), 6)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if name in ("kid",):
        tx(d, cx, cy - 70, "GTA 6", ANTON(PW(110)), WHITE); tx(d, cx, cy + 50, "???", ANTON(PW(70)), YEL)
    elif name == "y2013":
        tx(d, cx, cy - 90, "GTA 5", ANTON(PW(110)), WHITE); tx(d, cx, cy + 40, "COMPLETED 100%", MS(PW(44), 900), GREEN)
    elif name == "y2018":
        rng = np.random.default_rng(int(t * 12))
        for i in range(60):
            x = rng.uniform(x0, x1); y = rng.uniform(y0, y1); g = int(rng.uniform(60, 200))
            d.rectangle([P(x), P(y), P(x + 30), P(y + 4)], fill=(g, g, g))
        tx(d, cx, cy - 30, "NO NEWS", ANTON(PW(80)), WHITE, 4)
    elif name == "y2023":
        for i in range(0, int(y1 - y0), 6):
            k = i / (y1 - y0); d.rectangle([P(x0), P(y0 + i), P(x1), P(y0 + i + 6)], fill=(int(255 - 40 * k), int(120 - 60 * k), int(80 + 90 * k)))
        el(d, (cx - 60, cy + 10, cx + 60, cy + 130), (255, 210, 90), 0)
        tx(d, cx, cy - 120, "TRAILER 1", ANTON(PW(90)), WHITE, 4)
    elif name == "delay":
        tx(d, cx, cy - 70, "DELAYED", ANTON(PW(120)), RED)
    elif name in ("y2026", "press"):
        for i in range(0, int(y1 - y0), 6):
            k = i / (y1 - y0); d.rectangle([P(x0), P(y0 + i), P(x1), P(y0 + i + 6)], fill=tuple(int(a + (b - a) * k) for a, b in zip(PINK, ORANGE)))
        tx(d, cx, cy - 110, "GTA 6", ANTON(PW(120)), WHITE, 5)
        if int(t * 2.5) % 2 == 0: tx(d, cx, cy + 50, "PRESS START", MS(PW(46), 900), WHITE, 3)
    elif name in ("stuck", "outro"):
        tx(d, cx, cy - 120, "DOWNLOADING…", MS(PW(44), 900), WHITE)
        d.rounded_rectangle([P(x0 + 50), P(cy - 20), P(x1 - 50), P(cy + 40)], radius=PW(20), fill=(60, 60, 70), outline=WHITE, width=PW(4))
        fillk = min(.99, .9 + .09 * eout(age / .6)) if name == "stuck" else .99
        d.rounded_rectangle([P(x0 + 56), P(cy - 14), P(x0 + 56 + (x1 - x0 - 112) * fillk), P(cy + 34)], radius=PW(16), fill=GREEN)
        if int(t * 3) % 2 == 0 or name == "stuck": tx(d, cx, cy + 60, "99%", ANTON(PW(90)), YEL, 4)

def character(d, name, t, age, x=540, base=1720, k=1.0, stage=None, mood=None, phone=False):
    stage = stage or STAGE[name]; mood = mood or MOOD[name]
    sc = {"kid": .82, "teen": .95, "young": 1.0, "adult": 1.05, "boss": 1.05}[stage] * k
    cx = x
    bob = math.sin(t * 6) * 6 if mood in ("happy", "excited", "proud") else math.sin(t * 2) * 3
    shake = (math.sin(t * 70) * 10) if mood in ("angry", "scream") else 0
    cx += shake; hy = base - 470 * sc + bob                      # head centre y
    hr = 150 * sc * (1.12 if stage == "kid" else 1.0)
    hoodie = {"kid": (60, 200, 140), "teen": (40, 40, 60), "young": (230, 90, 90), "adult": (90, 110, 160), "boss": (90, 90, 100)}[stage]
    # body + arms + controller
    bw = 300 * sc; top = hy + hr * .8
    d.rounded_rectangle([P(cx - bw / 2), P(top), P(cx + bw / 2), P(base + 200)], radius=PW(90 * sc), fill=hoodie, outline=OUT, width=PW(8))
    arm_up = mood in ("excited", "scream", "angry")
    for sgn in (-1, 1):
        ax = cx + sgn * bw * .42
        if arm_up:
            lift = 120 + 30 * math.sin(t * 14 + sgn)
            d.line([P(ax), P(top + 60), P(ax + sgn * 90), P(top - lift)], fill=OUT, width=PW(52 * sc)); d.line([P(ax), P(top + 60), P(ax + sgn * 90), P(top - lift)], fill=hoodie, width=PW(38 * sc))
            el(d, (ax + sgn * 90 - 30 * sc, top - lift - 30 * sc, ax + sgn * 90 + 30 * sc, top - lift + 30 * sc), SKIN, 6)
        else:
            d.line([P(ax), P(top + 60), P(cx + sgn * 60), P(top + 230 * sc)], fill=OUT, width=PW(52 * sc)); d.line([P(ax), P(top + 60), P(cx + sgn * 60), P(top + 230 * sc)], fill=hoodie, width=PW(38 * sc))
    if stage == "boss":
        d.polygon([(P(cx - 40 * sc), P(top + 10)), (P(cx + 40 * sc), P(top + 10)), (P(cx), P(top + 70 * sc))], fill=WHITE, outline=OUT)
        d.polygon([(P(cx - 16 * sc), P(top + 30 * sc)), (P(cx + 16 * sc), P(top + 30 * sc)), (P(cx + 24 * sc), P(top + 190 * sc)), (P(cx), P(top + 220 * sc)), (P(cx - 24 * sc), P(top + 190 * sc))], fill=RED, outline=OUT)
    if not arm_up:
        rr(d, (cx - 110 * sc, top + 200 * sc, cx + 110 * sc, top + 270 * sc), 30 * sc, (50, 50, 60), 7)
        el(d, (cx + 40 * sc, top + 215 * sc, cx + 70 * sc, top + 245 * sc), RED, 0); el(d, (cx - 70 * sc, top + 215 * sc, cx - 40 * sc, top + 245 * sc), BLUE, 0)
    if stage == "adult" and mood == "tired":                     # coffee mug
        rr(d, (cx + 150, top + 120, cx + 230, top + 220), 12, WHITE, 7); d.arc([P(cx + 210), P(top + 140), P(cx + 260), P(top + 200)], -90, 90, fill=OUT, width=PW(8))
    # head
    el(d, (cx - hr, hy - hr, cx + hr, hy + hr), SKIN, 9)
    hair = {"kid": (120, 70, 30), "teen": (40, 30, 25), "young": (60, 40, 30), "adult": (70, 55, 45), "boss": (90, 90, 90)}[stage]
    if stage == "boss":
        d.arc([P(cx - hr * 1.02), P(hy - hr * .9), P(cx - hr * .5), P(hy + hr * .2)], 120, 240, fill=hair, width=PW(22))
        d.arc([P(cx + hr * .5), P(hy - hr * .9), P(cx + hr * 1.02), P(hy + hr * .2)], -60, 60, fill=hair, width=PW(22))
    elif stage == "teen":                                          # cap
        d.chord([P(cx - hr), P(hy - hr), P(cx + hr), P(hy + hr * .4)], 180, 360, fill=(220, 60, 60), outline=OUT, width=PW(8))
        d.rounded_rectangle([P(cx - hr * .2), P(hy - hr * .35), P(cx + hr * 1.25), P(hy - hr * .15)], radius=PW(14), fill=(220, 60, 60), outline=OUT, width=PW(8))
    else:
        d.chord([P(cx - hr * 1.02), P(hy - hr * 1.05), P(cx + hr * 1.02), P(hy + hr * .25)], 180, 360, fill=hair, outline=OUT, width=PW(8))
        for i in range(5):
            x = cx - hr * .8 + i * hr * .4; d.polygon([(P(x), P(hy - hr * .35)), (P(x + hr * .2), P(hy - hr * 1.25 + (8 if stage == "adult" else 0))), (P(x + hr * .4), P(hy - hr * .35))], fill=hair, outline=OUT)
    if stage == "adult":                                         # stubble
        rng = np.random.default_rng(3)
        for i in range(40):
            a = rng.uniform(.15, .85) * math.pi; r = hr * rng.uniform(.6, .92); x, y = cx + math.cos(a) * r, hy + math.sin(a) * r
            d.ellipse([P(x - 3), P(y - 3), P(x + 3), P(y + 3)], fill=(110, 80, 60))
    if stage == "boss":                                          # mustache
        d.chord([P(cx - hr * .42), P(hy + hr * .18), P(cx + hr * .42), P(hy + hr * .62)], 180, 360, fill=(90, 90, 90), outline=OUT, width=PW(6))
    if phone:
        px, py = cx + hr * 1.0, hy
        d.line([P(cx + bw * .42), P(top + 60), P(px + 10), P(py + 60)], fill=OUT, width=PW(52 * sc)); d.line([P(cx + bw * .42), P(top + 60), P(px + 10), P(py + 60)], fill=hoodie, width=PW(38 * sc))
        d.rounded_rectangle([P(px - 22), P(py - 70), P(px + 26), P(py + 50)], radius=PW(10), fill=(30, 30, 40), outline=OUT, width=PW(6))
    if mood == "cough":
        for kk in range(3):
            ph = (t * 2.5 + kk / 3) % 1; x = cx - hr * .2 - ph * 160; y = hy + hr * .5 - ph * 60; r = 14 + ph * 26
            d.ellipse([P(x - r), P(y - r), P(x + r), P(y + r)], fill=(235, 235, 235), outline=OUT, width=PW(3))
    # eyes
    blink = (t % 3.3) < .12
    ey = hy - hr * .05; ex = hr * .38; er = hr * .2
    for sgn in (-1, 1):
        x = cx + sgn * ex
        if blink or mood == "cough" or mood == "happy" and (t % 1.6) < .1:
            d.line([P(x - er), P(ey), P(x + er), P(ey)], fill=OUT, width=PW(8))
        else:
            big = 1.35 if mood in ("scream", "excited") else 1.0
            el(d, (x - er * big, ey - er * big, x + er * big, ey + er * big), WHITE, 6)
            pr = er * (.45 if mood != "scream" else .3)
            d.ellipse([P(x - pr), P(ey - pr), P(x + pr), P(ey + pr)], fill=OUT)
            if mood in ("bored", "tired"):                       # heavy lids
                d.chord([P(x - er - 2), P(ey - er - 2), P(x + er + 2), P(ey + er + 2)], 180, 360, fill=SKIN, outline=OUT, width=PW(6))
            if stage == "adult":
                d.arc([P(x - er), P(ey + er * .6), P(x + er), P(ey + er * 1.6)], 20, 160, fill=(150, 100, 140), width=PW(5))
        # eyebrows
        by = ey - er * 1.6
        if mood == "angry": d.line([P(x - sgn * er * 1.1), P(by - 10), P(x + sgn * er * 1.1), P(by + 18)], fill=OUT, width=PW(12))
        elif mood == "cry": d.line([P(x - sgn * er * 1.1), P(by + 14), P(x + sgn * er * 1.1), P(by - 10)], fill=OUT, width=PW(10))
        else: d.arc([P(x - er), P(by - 8), P(x + er), P(by + 22)], 200, 340, fill=OUT, width=PW(9))
    # mouth
    my = hy + hr * .48; talk = speaking(t) and int(t * 12) % 2 == 0
    if mood in ("scream",):
        el(d, (cx - hr * .32, my - hr * .2, cx + hr * .32, my + hr * .42), (120, 20, 40), 8)
    elif mood in ("angry",):
        d.rounded_rectangle([P(cx - hr * .3), P(my - 6), P(cx + hr * .3), P(my + 34)], radius=PW(10), fill=WHITE, outline=OUT, width=PW(7))
        for i in range(1, 4): d.line([P(cx - hr * .3 + i * hr * .15), P(my - 6), P(cx - hr * .3 + i * hr * .15), P(my + 34)], fill=OUT, width=PW(4))
    elif mood in ("cry", "bored", "tired"):
        d.arc([P(cx - hr * .28), P(my), P(cx + hr * .28), P(my + hr * .35)], 200, 340, fill=OUT, width=PW(9))
    elif talk:
        el(d, (cx - hr * .2, my - hr * .08, cx + hr * .2, my + hr * .26), (120, 20, 40), 7)
    else:
        d.arc([P(cx - hr * .3), P(my - hr * .25), P(cx + hr * .3), P(my + hr * .2)], 20, 160, fill=OUT, width=PW(9))
    if mood == "cry":                                            # tears
        for sgn in (-1, 1):
            for k in range(3):
                ph = (t * 1.6 + k / 3) % 1; x = cx + sgn * (ex + er * .2); y = ey + er + ph * 260
                d.ellipse([P(x - 12), P(y - 18), P(x + 12), P(y + 18)], fill=BLUE, outline=OUT, width=PW(3))
    if mood == "angry":                                          # steam
        for sgn in (-1, 1):
            for k in range(3):
                ph = (t * 1.8 + k / 3) % 1; x = cx + sgn * hr * 1.1; y = hy - hr * .6 - ph * 160
                r = 22 + ph * 30; d.ellipse([P(x - r), P(y - r), P(x + r), P(y + r)], fill=(240, 240, 240), outline=OUT, width=PW(4))

def bubble(d, x, y, s, k, f=None):
    if k <= 0: return
    f = f or MS(PW(42), 800); w = d.textlength(s, font=f) / S + 70; h = 110
    sc = back(min(1, k)); w2, h2 = w * sc, h * sc
    d.rounded_rectangle([P(x - w2 / 2), P(y - h2 / 2), P(x + w2 / 2), P(y + h2 / 2)], radius=PW(40), fill=WHITE, outline=OUT, width=PW(7))
    d.polygon([(P(x - 20), P(y + h2 / 2 - 4)), (P(x + 20), P(y + h2 / 2 - 4)), (P(x + 40), P(y + h2 / 2 + 40))], fill=WHITE, outline=OUT)
    if sc > .8: tx(d, x, y - 30, s, f, OUT)

def stamp(d, s, cx, cy, k, rot_dummy=0, col=RED, size=150):
    if k <= 0: return
    sc = 2.2 - 1.2 * back(min(1, k)); f = ANTON(PW(size * sc)); w = d.textlength(s, font=f) / S
    d.rounded_rectangle([P(cx - w / 2 - 30), P(cy - size * sc * .2), P(cx + w / 2 + 30), P(cy + size * sc * 1.3)], radius=PW(20), outline=col, width=PW(14))
    tx(d, cx, cy, s, f, col)

def draw_scene(name, t, a, b):
    age = t - a
    img = Image.new("RGB", (W * S, H * S)); d = ImageDraw.Draw(img)
    room(d, name, t); tv(d, name, t, age); character(d, name, t, age)
    yr = YEAR[name]
    if name in ("y2013", "y2018", "y2023", "y2026"):              # big year card sweeps in
        k = eout(age / .35); x = -400 + 940 * k if age < 1.4 else 540 - 1400 * ease((age - 1.4) / .4)
        tx(d, x, 180, yr, ANTON(PW(200)), WHITE, 8)
    if name == "kid": tx(d, 540, 180, "POV:", ANTON(PW(180)), WHITE, 8)
    if name == "y2013":
        tc = word_time("y2013", "the") - a; bubble(d, 540, 455, "next one can't take that long!", (age - tc + .1) / .25, MS(PW(38), 800))
    if name == "delay":
        stamp(d, "DELAYED", 540, 330, (age - .05) / .25)
        ta = word_time("delay", "again.") - a
        if age > ta - .1: stamp(d, "AGAIN", 540, 560, (age - ta + .1) / .25, col=(255, 120, 40), size=120)
    if name == "y2026":
        for i, (s_, w_) in enumerate((("JOB", "job,"), ("BACK PAIN", "back"))):
            tw = word_time("y2026", w_) - a
            if age > tw - .1: bubble(d, 330 + i * 420, 455, s_, (age - tw + .1) / .25, MS(PW(46), 900))
    if name == "press":
        if age > .3: stamp(d, "START", 540, 300, (age - .3) / .25, col=GREEN, size=130)
    if name == "stuck":
        if age > .9: stamp(d, "NOOOO", 540, 300, (age - .9) / .2, size=150)
    if name == "outro":
        bubble(d, 540, 455, "How old were you?", age / .3, MS(PW(50), 900))
    return img.resize((W, H), Image.LANCZOS)


# ======================================================= SICK-DAY SKIT (overrides the 13-years scenes)
def wall(d, c1, c2, floor=(110, 75, 60)):
    for i in range(0, H, 40):
        k = i / H; col = tuple(int(a + (b - a) * k) for a, b in zip(c1, c2)); d.rectangle([0, P(i), P(W), P(i + 40)], fill=col)
    d.rectangle([0, P(1330), P(W), P(H)], fill=floor); d.line([0, P(1330), P(W), P(1330)], fill=OUT, width=PW(8))
def small_tv(d, x0, y0, x1, y1, t, label="GTA 6", sub="OUT NOW"):
    rr(d, (x0, y0, x1, y1), 22, (40, 40, 48), 9)
    ix0, iy0, ix1, iy1 = x0 + 30, y0 + 30, x1 - 30, y1 - 30
    for i in range(0, int(iy1 - iy0), 6):
        k = i / (iy1 - iy0); d.rectangle([P(ix0), P(iy0 + i), P(ix1), P(iy0 + i + 6)], fill=tuple(int(a + (b - a) * k) for a, b in zip(PINK, ORANGE)))
    cx = (x0 + x1) / 2; h = y1 - y0
    tx(d, cx, y0 + h * .22, label, ANTON(PW(h * .28)), WHITE, 4)
    if sub and int(t * 2.5) % 2 == 0: tx(d, cx, y0 + h * .58, sub, MS(PW(h * .1), 900), WHITE, 3)
def calendar(d, x, y, top="NOV", big="19"):
    rr(d, (x, y, x + 190, y + 190), 14, WHITE); d.rectangle([P(x), P(y), P(x + 190), P(y + 50)], fill=RED, outline=OUT, width=PW(8))
    tx(d, x + 95, y + 2, top, MS(PW(34), 900), WHITE); tx(d, x + 95, y + 60, big, ANTON(PW(90)), OUT)
def clock(d, cx, cy, t, ring=True):
    sh = math.sin(t * 60) * 10 if ring else 0; cx += sh
    for sgn in (-1, 1): el(d, (cx + sgn * 120 - 50, cy - 200, cx + sgn * 120 + 50, cy - 100), (240, 200, 60), 8)
    el(d, (cx - 200, cy - 200, cx + 200, cy + 200), (240, 80, 80), 10); el(d, (cx - 160, cy - 160, cx + 160, cy + 160), WHITE, 8)
    tx(d, cx, cy - 70, "6:00", ANTON(PW(120)), OUT); tx(d, cx, cy + 70, "AM", MS(PW(46), 900), OUT)
    if ring:
        for sgn in (-1, 1):
            for k in range(3): d.arc([P(cx + sgn * (230 + k * 40) - 60), P(cy - 120 - k * 30), P(cx + sgn * (230 + k * 40) + 60), P(cy + 120 + k * 30)], -40 if sgn > 0 else 140, 40 if sgn > 0 else 220, fill=OUT, width=PW(8))
def desk(d, x, y):
    rr(d, (x, y, x + 300, y + 40), 8, (170, 120, 80), 7); d.rectangle([P(x + 20), P(y + 40), P(x + 40), P(y + 200)], fill=OUT); d.rectangle([P(x + 260), P(y + 40), P(x + 280), P(y + 200)], fill=OUT)
    rr(d, (x + 90, y - 140, x + 230, y - 20), 10, (60, 60, 70), 7); d.rectangle([P(x + 150), P(y - 20), P(x + 170), P(y)], fill=OUT)
    rr(d, (x + 100, y + 60, x + 200, y + 200), 30, (70, 70, 90), 6)

def draw_scene(name, t, a, b):
    age = t - a
    img = Image.new("RGB", (W * S, H * S)); d = ImageDraw.Draw(img)
    if name == "hook":
        wall(d, (255, 120, 170), (230, 80, 140)); small_tv(d, 190, 520, 890, 930, t); calendar(d, 850, 300)
        rr(d, (40, 300, 290, 470), 6, (255, 240, 120), 6); tx(d, 165, 320, "WORK", ANTON(PW(56)), OUT); tx(d, 165, 395, "9:00 AM", MS(PW(36), 900), RED)
        character(d, name, t, age, stage="adult", mood="excited")
        tx(d, 540, 160, "POV:", ANTON(PW(170)), WHITE, 8)
    elif name == "alarm":
        wall(d, (40, 50, 110), (25, 30, 80), (60, 45, 40)); clock(d, 540, 700, t)
        character(d, name, t, age, stage="adult", mood="tired")
    elif name in ("call", "cough"):
        wall(d, (120, 170, 230), (90, 130, 200)); calendar(d, 850, 300)
        character(d, name, t, age, stage="adult", mood="cough" if name == "cough" else "tired", phone=True)
        if name == "cough":
            tc = word_time("call", "sick") - a
            bubble(d, 540, 520, "*cough cough*", age / .25, MS(PW(52), 900))
            if age > tc - a + a - .1 and t > word_time("call", "sick") - .1: bubble(d, 540, 700, "I'm really sick today…", (t - word_time("call", "sick") + .1) / .25, MS(PW(42), 800))
        else:
            tx(d, 540, 520, "CALLING: BOSS", MS(PW(60), 900), WHITE, 5)
    elif name == "boss":
        wall(d, (120, 170, 230), (90, 130, 200))
        d.rectangle([P(W / 2), 0, P(W), P(H)], fill=(255, 170, 90))
        for i in range(0, H, 40):
            k = i / H; d.rectangle([P(W / 2), P(i), P(W), P(i + 40)], fill=tuple(int(a_ + (b_ - a_) * k) for a_, b_ in zip((255, 180, 100), (235, 140, 70))))
        d.rectangle([0, P(1330), P(W), P(H)], fill=(110, 75, 60)); d.line([P(W / 2), 0, P(W / 2), P(H)], fill=OUT, width=PW(12))
        small_tv(d, 600, 420, 1040, 700, t, "GTA 6", "")
        character(d, name, t, age, x=270, base=1760, k=.75, stage="adult", mood="tired", phone=True)
        character(d, name, t, age, x=810, base=1760, k=.75, stage="boss", mood="cough" if age > .8 else "happy", phone=True)
        tx(d, 270, 300, "YOU", ANTON(PW(90)), WHITE, 6); tx(d, 810, 300, "BOSS", ANTON(PW(90)), WHITE, 6)
        bubble(d, 810, 860, "yeah… me too", (age - .2) / .25, MS(PW(40), 900))
        if age > .8: bubble(d, 810, 990, "*cough cough*", (age - .8) / .25, MS(PW(36), 900))
    elif name == "office":
        wall(d, (200, 210, 220), (170, 180, 195), (150, 150, 160))
        for i, x in enumerate((70, 400, 730)): desk(d, x, 1150)
        rr(d, (240, 330, 840, 660), 20, WHITE, 9)
        tx(d, 540, 360, "OFFICE CLOSED", ANTON(PW(90)), RED); tx(d, 540, 490, "everyone is \"sick\"", MS(PW(48), 800), OUT)
        tx(d, 540, 560, "(GTA 6 came out)", MS(PW(40), 700), (90, 90, 100))
        x = (age * 380) % (W + 300) - 150; r = 70
        d.ellipse([P(x - r), P(1240 - r), P(x + r), P(1240 + r)], outline=(150, 110, 60), width=PW(10))
        for k in range(5):
            a_ = t * 5 + k; d.line([P(x + math.cos(a_) * r), P(1240 + math.sin(a_) * r), P(x - math.cos(a_) * r), P(1240 - math.sin(a_) * r)], fill=(150, 110, 60), width=PW(6))
    elif name == "outro":
        wall(d, (255, 120, 170), (230, 80, 140)); small_tv(d, 190, 480, 890, 860, t, "GTA 6", "")
        character(d, name, t, age, x=300, base=1760, k=.8, stage="adult", mood="excited")
        character(d, name, t, age, x=790, base=1760, k=.8, stage="boss", mood="excited")
        bubble(d, 540, 330, "Did YOU skip work?", age / .3, MS(PW(52), 900))
    return img.resize((W, H), Image.LANCZOS)

# ---------------------------------------------------------------- captions (cartoon style: white, thick outline, yellow keyword)
def build_caps():
    groups = []
    for seg in TM["segments"]:
        hl = [s for s in SEGMENTS if s["id"] == seg["id"]][0]["hl"]; cur = []
        for i, w in enumerate(seg["words"]):
            cur.append(dict(w, hl=clean(w["w"]) in hl or w["w"].lower() in hl))
            if w["w"][-1] in ".?!," or len(cur) >= 3 or i == len(seg["words"]) - 1:
                groups.append((cur, seg["id"])); cur = []
    return groups
CAPS = build_caps()
NUM = {"six": "6", "five": "5", "ninety-nine": "99"}
def disp(w, prev):
    lw = w.lower(); core = lw.rstrip(".,?!"); tail = lw[len(core):]
    if core in ("twenty",): return ""
    if core == "a" and False: return ""
    if core == "eighteen": return "2018" + tail
    if core == "twenty-three": return "2023" + tail
    if core == "twenty-six": return "2026" + tail
    if core == "percent": return "%" + tail
    if core in NUM: return NUM[core] + tail
    return w
def caption(img, t):
    g = None
    for ws, sid in CAPS:
        if ws[0]["a"] - .05 <= t: g = (ws, sid)
    if g is None: return
    ws, sid = g
    nxt = [x["a"] for x in TM["segments"] if x["a"] > ws[-1]["b"]]
    if t > ws[-1]["b"] + .5 or (nxt and t >= nxt[0] - .12): return
    toks = [(w, disp(w["w"], None).upper()) for w in ws]; toks = [(w, s) for w, s in toks if s]
    merged = []
    for w, s_ in toks:
        if s_.startswith("%") and merged: merged[-1] = (merged[-1][0], merged[-1][1] + s_)
        else: merged.append((w, s_))
    toks = merged
    if toks and toks[0][1] == "P": toks = [(toks[0][0], "POV")] + [x for x in toks[1:] if x[1] not in ("O", "V.")]
    d = ImageDraw.Draw(img); f = ANTON(96)
    widths = [d.textlength(s, font=f) for _, s in toks]; sp = 22
    while sum(widths) + sp * (len(toks) - 1) > W - 100:
        f = ANTON(f.size - 4); widths = [d.textlength(s, font=f) for _, s in toks]
    x = (W - sum(widths) - sp * (len(toks) - 1)) / 2; y = 1430
    age = t - ws[0]["a"]; pop = back(min(1, age / .12)) if age > 0 else 0
    for (w, s_), wd in zip(toks, widths):
        on = w["a"] - .03 <= t; yy = y + (1 - pop) * 26
        col = YEL if (w["hl"] and on) else (WHITE if on else (230, 230, 230))
        d.text((x, yy), s_, font=f, fill=col, stroke_width=9, stroke_fill=OUT)
        x += wd + sp

def shot_at(t):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); return i, SHOTS[i]
def frame(t, fi=None):
    i, (a, b, name, seg) = shot_at(t)
    img = draw_scene(name, t, a, b); age = t - a
    if i and age < .22:                                           # cartoon iris/circle wipe
        prev = draw_scene(SHOTS[i - 1][2], a - 1e-3, SHOTS[i - 1][0], SHOTS[i - 1][1])
        m = Image.new("L", (W, H), 0); r = 1200 * eout(age / .22); ImageDraw.Draw(m).ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=255)
        prev.paste(img, (0, 0), m); img = prev
    caption(img, t)
    d = ImageDraw.Draw(img); d.text((30, 30), "ORIGINAL ANIMATION · FAN-MADE", font=MS(22, 700), fill=(255, 255, 255), stroke_width=2, stroke_fill=OUT)
    if t < .12: img = Image.fromarray((np.asarray(img, np.float32) * ease(t / .12)).astype(np.uint8))
    return img

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "none"
    if mode == "still":
        for s in sys.argv[2:]: frame(float(s)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 60 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
