# "Banana Said Just ONE Hour of GTA 6" — FRUIT DRAMA identity (original anthropomorphic fruits, reality-show styling).
# Banana ripens (yellow → spotted → brown) as the night goes on; Strawberry twist with her own controller.
# Reality-TV lower thirds with the time, glossy fruit shading, TV glow, window sky that changes with time, wall clock.
# Drawn at 2x and downsampled. No game footage, no Rockstar art. Usage: still <t>... | video <worker> <nworkers>
import sys, os, math, json, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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
OUT = (40, 25, 30); WHITE = (255, 255, 255); PINK = (255, 70, 150); ORANGE = (255, 150, 40); YEL = (255, 214, 0)
BAN = (255, 222, 70); BROWN = (120, 75, 30); STR = (232, 40, 70); LEAF = (60, 170, 70)

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
def speaking(t, who):
    for sd, sg in zip(SEGMENTS, TM["segments"]):
        if sd["who"] != who: continue
        for w in sg["words"]:
            if w["a"] <= t <= w["b"]: return True
    return False
def P(v): return v * S
def PW(v): return max(1, int(round(v * S)))
def tx(d, cx, y, s, f, fill, stroke=0):
    w = d.textlength(s, font=f); d.text((P(cx) - w / 2, P(y)), s, font=f, fill=fill, stroke_width=PW(stroke) if stroke else 0, stroke_fill=OUT)
def mix(a, b, k): return tuple(int(x + (y - x) * k) for x, y in zip(a, b))

# time-of-day per shot: (label, sky top, sky bottom, wall, ripeness, clock hour)
TOD = {"hook": ("", (255, 170, 120), (255, 120, 140), (255, 205, 185), .0, 7),
       "pm7": ("7:00 PM", (255, 170, 110), (255, 110, 130), (255, 205, 185), .05, 7), "pm7b": ("7:00 PM", (255, 170, 110), (255, 110, 130), (255, 205, 185), .05, 7),
       "pm7c": ("7:00 PM", (255, 170, 110), (255, 110, 130), (255, 205, 185), .05, 7),
       "pm11": ("11:00 PM", (40, 50, 120), (80, 60, 150), (150, 130, 190), .35, 11), "pm11b": ("11:00 PM", (40, 50, 120), (80, 60, 150), (150, 130, 190), .4, 11),
       "am3": ("3:00 AM", (10, 12, 40), (25, 25, 70), (70, 60, 110), .9, 3), "twist": ("3:00 AM", (10, 12, 40), (25, 25, 70), (70, 60, 110), .9, 3),
       "twist2": ("3:00 AM", (10, 12, 40), (25, 25, 70), (70, 60, 110), .9, 3), "outro": ("", (255, 170, 120), (255, 120, 140), (255, 205, 185), .9, 3)}

def room(d, name, t):
    lab, s1, s2, wall, rip, hr = TOD[name]
    for i in range(0, H, 40):
        k = i / H; d.rectangle([0, P(i), P(W), P(i + 40)], fill=mix(wall, mix(wall, (0, 0, 0), .25), k))
    # window
    d.rounded_rectangle([P(60), P(300), P(420), P(720)], radius=PW(20), fill=s1, outline=OUT, width=PW(10))
    for i in range(0, 400, 20): d.rectangle([P(70), P(310 + i), P(410), P(330 + i)], fill=mix(s1, s2, i / 400))
    if hr == 7: d.ellipse([P(180), P(560), P(300), P(680)], fill=(255, 220, 120))
    else:
        d.ellipse([P(300), P(360), P(370), P(430)], fill=(250, 245, 220)); d.ellipse([P(320), P(350), P(390), P(420)], fill=s1)
        rng = np.random.default_rng(5)
        for _ in range(14):
            x, y = rng.uniform(80, 400), rng.uniform(320, 700); r = 3 + 2 * (math.sin(t * 3 + x) > .5)
            d.ellipse([P(x - r), P(y - r), P(x + r), P(y + r)], fill=WHITE)
    d.line([P(240), P(300), P(240), P(720)], fill=OUT, width=PW(8)); d.line([P(60), P(510), P(420), P(510)], fill=OUT, width=PW(8))
    # wall clock
    cx, cy = 880, 400; d.ellipse([P(cx - 110), P(cy - 110), P(cx + 110), P(cy + 110)], fill=WHITE, outline=OUT, width=PW(10))
    for k in range(12):
        a = k / 12 * 2 * math.pi; d.line([P(cx + math.sin(a) * 85), P(cy - math.cos(a) * 85), P(cx + math.sin(a) * 98), P(cy - math.cos(a) * 98)], fill=OUT, width=PW(5))
    ah = (hr % 12) / 12 * 2 * math.pi; am = (t * .8) % (2 * math.pi)
    d.line([P(cx), P(cy), P(cx + math.sin(ah) * 55), P(cy - math.cos(ah) * 55)], fill=OUT, width=PW(12))
    d.line([P(cx), P(cy), P(cx + math.sin(am) * 85), P(cy - math.cos(am) * 85)], fill=(220, 50, 70), width=PW(6))
    # floor + couch
    d.rectangle([0, P(1360), P(W), P(H)], fill=mix((150, 100, 80), (0, 0, 0), .2 if hr != 7 else 0))
    d.rounded_rectangle([P(40), P(980), P(1040), P(1300)], radius=PW(60), fill=(120, 70, 170), outline=OUT, width=PW(10))
    d.rounded_rectangle([P(10), P(1150), P(1070), P(1400)], radius=PW(50), fill=(140, 85, 195), outline=OUT, width=PW(10))
    if name in ("am3", "twist", "twist2", "outro"):            # pizza box + cans
        d.polygon([(P(760), P(1440)), (P(1000), P(1430)), (P(1030), P(1520)), (P(780), P(1530))], fill=(230, 200, 150), outline=OUT)
        for x in (120, 200): d.rounded_rectangle([P(x), P(1440), P(x + 50), P(1530)], radius=PW(8), fill=(220, 60, 60), outline=OUT, width=PW(6))

def tv_glow(img, strength):
    if strength <= 0: return img
    lay = Image.new("RGB", img.size, (0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([P(200), P(700), P(1000), P(1500)], fill=(int(255 * strength), int(70 * strength), int(160 * strength)))
    lay = lay.resize((W // 2, H // 2)).filter(ImageFilter.GaussianBlur(60)).resize(img.size)
    return Image.fromarray(np.clip(np.asarray(img, np.int16) + np.asarray(lay, np.int16) // 2, 0, 255).astype(np.uint8))

def eyes(d, cx, cy, r, t, mood, lashes=False, look=0):
    blink = (t % 3.1) < .12 or mood == "sleepy" and (t % 1.2) < .5
    for sgn in (-1, 1):
        x = cx + sgn * r * 1.15
        if blink:
            d.arc([P(x - r), P(cy - r * .4), P(x + r), P(cy + r * .6)], 20, 160, fill=OUT, width=PW(7)); continue
        big = 1.35 if mood in ("shock",) else 1.0; rr = r * big
        d.ellipse([P(x - rr), P(cy - rr), P(x + rr), P(cy + rr)], fill=WHITE, outline=OUT, width=PW(6))
        if mood == "tired":
            for k in range(3): d.line([P(x - rr * .7), P(cy - rr * .2 + k * 8), P(x - rr * .2), P(cy + k * 6)], fill=(230, 60, 60), width=PW(3))
        pr = rr * (.5 if mood != "shock" else .32); px = x + look * rr * .35
        d.ellipse([P(px - pr), P(cy - pr), P(px + pr), P(cy + pr)], fill=OUT); d.ellipse([P(px - pr * .35 + pr * .4), P(cy - pr * .6), P(px + pr * .35 + pr * .4), P(cy - pr * .0)], fill=WHITE)
        if mood in ("tired", "sleepy"): d.chord([P(x - rr - 2), P(cy - rr - 2), P(x + rr + 2), P(cy + rr + 2)], 180, 360, fill=None, outline=OUT, width=PW(6))
        if lashes:
            for k in (-1, 0, 1): d.line([P(x + k * rr * .5), P(cy - rr), P(x + k * rr * .7), P(cy - rr * 1.45)], fill=OUT, width=PW(5))
def mouth(d, cx, cy, r, t, mood, talk):
    if mood == "shock" or talk and int(t * 12) % 2 == 0:
        d.ellipse([P(cx - r * .55), P(cy - r * .35), P(cx + r * .55), P(cy + r * .6)], fill=(120, 20, 40), outline=OUT, width=PW(6))
    elif mood in ("tired", "sleepy", "annoyed"):
        d.arc([P(cx - r * .6), P(cy), P(cx + r * .6), P(cy + r * .7)], 200, 340, fill=OUT, width=PW(7))
    elif mood == "smug":
        d.arc([P(cx - r * .7), P(cy - r * .6), P(cx + r * .5), P(cy + r * .4)], 20, 120, fill=OUT, width=PW(7))
    else:
        d.arc([P(cx - r * .7), P(cy - r * .7), P(cx + r * .7), P(cy + r * .5)], 20, 160, fill=OUT, width=PW(7))

def controller(d, x, y, s=1.0):
    d.rounded_rectangle([P(x - 70 * s), P(y - 26 * s), P(x + 70 * s), P(y + 26 * s)], radius=PW(24 * s), fill=(45, 45, 55), outline=OUT, width=PW(6))
    d.ellipse([P(x + 25 * s), P(y - 10 * s), P(x + 45 * s), P(y + 10 * s)], fill=(230, 60, 60)); d.ellipse([P(x - 45 * s), P(y - 10 * s), P(x - 25 * s), P(y + 10 * s)], fill=(80, 170, 255))

def banana(d, cx, base, t, rip, mood, talk, look=1):
    h = 560; bob = math.sin(t * 5) * 6 if mood == "happy" else math.sin(t * 2) * 3
    top = base - h + bob
    def c(u): return (cx + 120 * math.sin(math.pi * u) - 60, top + h * u)
    def w(u): return 105 * math.sin(math.pi * (0.06 + .88 * u)) ** .7 + 10
    L = []; R = []
    for i in range(41):
        u = i / 40; x, y = c(u); L.append((P(x - w(u)), P(y))); R.append((P(x + w(u) * .85), P(y)))
    col = mix(BAN, (205, 170, 60), min(1, rip * 1.2)) if rip < .7 else mix((205, 170, 60), (150, 105, 45), (rip - .7) / .3)
    d.polygon(L + R[::-1], fill=col, outline=OUT, width=PW(10))
    # highlight
    hl = [(P(c(u)[0] - w(u) * .55), P(c(u)[1])) for u in np.linspace(.15, .8, 12)]
    d.line(hl, fill=mix(col, WHITE, .45), width=PW(16))
    # stem + tip
    sx, sy = c(0); d.rounded_rectangle([P(sx - 18), P(sy - 60), P(sx + 18), P(sy + 10)], radius=PW(8), fill=(110, 80, 40), outline=OUT, width=PW(6))
    ex, ey = c(1); d.ellipse([P(ex - 14), P(ey - 22), P(ex + 14), P(ey + 6)], fill=(70, 45, 25))
    # brown spots grow with ripeness
    rng = np.random.default_rng(7); n = int(rip * 34)
    for i in range(n):
        u = rng.uniform(.12, .9); x, y = c(u); x += rng.uniform(-.6, .6) * w(u); r = rng.uniform(8, 22) * (.6 + rip)
        d.ellipse([P(x - r), P(y - r * .8), P(x + r), P(y + r * .8)], fill=mix(BROWN, (60, 35, 15), rng.uniform(0, .6)))
    fx, fy = c(.42)
    eyes(d, fx, fy, 30, t, mood, look=look); mouth(d, fx, fy + 70, 40, t, mood, talk)
    # arms + controller
    hx, hy = c(.62); controller(d, hx + 10, hy + 40)
    for sgn in (-1, 1): d.line([P(hx + sgn * w(.62) * .8), P(hy - 30), P(hx + sgn * 55), P(hy + 30)], fill=OUT, width=PW(12))
    for sgn in (-1, 1): d.line([P(ex + sgn * 30), P(ey - 10), P(ex + sgn * 55), P(ey + 70)], fill=OUT, width=PW(12))

def strawberry(d, cx, base, t, mood, talk, ctrl=False, look=-1):
    h = 470; bob = math.sin(t * 4 + 1) * 5; top = base - h + bob
    pts = []
    for a in np.linspace(0, 2 * math.pi, 60):
        x = math.sin(a); y = -math.cos(a)
        r = 1.0 - .38 * max(0, y) ** 1.6
        pts.append((P(cx + x * 200 * (1 - .55 * max(0, y) ** 1.2)), P(top + 190 + y * 240 * (1.15 if y > 0 else .8))))
    d.polygon(pts, fill=STR, outline=OUT, width=PW(10))
    d.ellipse([P(cx - 140), P(top + 70), P(cx - 60), P(top + 190)], fill=mix(STR, WHITE, .35))
    rng = np.random.default_rng(3)
    for i in range(26):
        x = cx + rng.uniform(-150, 150); y = top + rng.uniform(80, 360)
        if abs(x - cx) > 170 - (y - top - 60) * .35: continue
        d.ellipse([P(x - 6), P(y - 9), P(x + 6), P(y + 9)], fill=(255, 225, 120))
    for k in range(7):                                        # leaf crown
        a = math.pi + k / 6 * math.pi; x0, y0 = cx + math.cos(a) * 60, top - 30 + math.sin(a) * 25
        d.polygon([(P(cx + math.cos(a) * 20), P(top - 20)), (P(x0 + math.cos(a) * 60), P(y0 + math.sin(a) * 40)), (P(cx + math.cos(a + .3) * 30), P(top - 10))], fill=LEAF, outline=OUT)
    d.polygon([(P(cx + 60), P(top - 10)), (P(cx + 120), P(top - 50)), (P(cx + 120), P(top + 30))], fill=PINK, outline=OUT)   # bow
    d.polygon([(P(cx + 60), P(top - 10)), (P(cx + 10), P(top - 50)), (P(cx + 10), P(top + 30))], fill=PINK, outline=OUT)
    d.ellipse([P(cx + 45), P(top - 25), P(cx + 75), P(top + 5)], fill=PINK, outline=OUT, width=PW(5))
    fy = top + 180; eyes(d, cx, fy, 28, t, mood, lashes=True, look=look); mouth(d, cx, fy + 70, 36, t, mood, talk)
    for sgn in (-1, 1): d.line([P(cx + sgn * 60), P(top + 420), P(cx + sgn * 70), P(base + 40)], fill=OUT, width=PW(12))
    if ctrl:
        controller(d, cx, top + 330, .95)
        for sgn in (-1, 1): d.line([P(cx + sgn * 170), P(top + 250), P(cx + sgn * 60), P(top + 330)], fill=OUT, width=PW(12))
    else:
        for sgn in (-1, 1): d.line([P(cx + sgn * 175), P(top + 250), P(cx + sgn * 240), P(top + 350 - (60 if sgn > 0 and mood == "annoyed" else 0))], fill=OUT, width=PW(12))

def bubble(d, x, y, s, k, col=WHITE, f=None, tail="down"):
    if k <= 0: return
    f = f or MS(PW(44), 900); w = d.textlength(s, font=f) / S + 70; h = 110
    sc = back(min(1, k)); w2, h2 = w * sc, h * sc
    d.rounded_rectangle([P(x - w2 / 2), P(y - h2 / 2), P(x + w2 / 2), P(y + h2 / 2)], radius=PW(40), fill=col, outline=OUT, width=PW(7))
    if sc > .8: tx(d, x, y - 30, s, f, OUT)

def lower_third(d, label, age):
    if not label: return
    k = eout(age / .3); x0 = -500 + 540 * k
    d.rounded_rectangle([P(x0), P(220), P(x0 + 470), P(330)], radius=PW(20), fill=PINK, outline=OUT, width=PW(8))
    tx(d, x0 + 235, 228, label, ANTON(PW(84)), WHITE, 4)

def draw_scene(name, t, a, b):
    age = t - a; lab, s1, s2, wall, rip, hr = TOD[name]
    img = Image.new("RGB", (W * S, H * S)); d = ImageDraw.Draw(img); room(d, name, t)
    bt = speaking(t, "b"); stalk = speaking(t, "s")
    if name == "hook":
        banana(d, 540, 1300, t, 0, "happy", bt)
        k = back(min(1, age / .3)); tx(d, 540, 160, "\"JUST 1 HOUR\"", ANTON(PW(120 * k + 1)), YEL, 8)
    elif name in ("pm7", "pm7b", "pm7c"):
        banana(d, 380, 1300, t, rip, "happy", bt, look=1)
        if name != "pm7":
            strawberry(d, 820, 1420, t, "annoyed" if name == "pm7c" else "happy", stalk, look=-1)
        if name == "pm7b": bubble(d, 820, 820, "Babe, dinner is at 8!", age / .25, col=(255, 210, 225), f=MS(PW(40), 900))
        if name == "pm7c": bubble(d, 380, 640, "one more mission", age / .25, col=(255, 240, 160))
    elif name in ("pm11", "pm11b"):
        banana(d, 460, 1300, t, rip, "tired" if name == "pm11b" else "happy", bt)
        if name == "pm11b": bubble(d, 460, 640, "one more mission, babe", age / .25, col=(255, 240, 160), f=MS(PW(40), 900))
    elif name == "am3":
        banana(d, 460, 1300, t, min(1, rip + .1 * eout(age / 2)), "tired", bt)
        if age > 1.0: tx(d, 540, 1520 - 380, "", MS(10), OUT)
    elif name in ("twist", "twist2"):
        banana(d, 330, 1300, t, rip, "shock" if name == "twist2" else "tired", bt, look=1)
        x = 1300 - 520 * eout(age / .6) if name == "twist" else 780
        strawberry(d, x, 1420, t, "smug", stalk, ctrl=True, look=-1)
        if name == "twist2":
            bubble(d, 780, 820, "still on chapter 1??", age / .25, col=(255, 210, 225))
            k = back(min(1, (age - .6) / .3))
            if k > 0:
                d.rounded_rectangle([P(560), P(540), P(1020), P(660)], radius=PW(20), fill=(60, 200, 110), outline=OUT, width=PW(8))
                tx(d, 790, 555, "HER: CHAPTER 4", ANTON(PW(70)), WHITE, 4)
    elif name == "outro":
        banana(d, 330, 1300, t, rip, "happy", bt, look=1); strawberry(d, 780, 1420, t, "happy", stalk, ctrl=True, look=-1)
        k = back(min(1, age / .3)); tx(d, 540, 170, "TAG THE BANANA", ANTON(PW(110 * k + 1)), YEL, 8)
        tx(d, 540, 300, "in your life 🍌" if False else "in your life", MS(PW(56), 900), WHITE, 5)
        tf = word_time("outro", "follow") - a
        if age > tf - .1:
            kk = back(min(1, (age - tf + .1) / .3)); bw = 600 * kk
            d.rounded_rectangle([P(540 - bw / 2), P(560), P(540 + bw / 2), P(700)], radius=PW(50), fill=(235, 50, 50), outline=OUT, width=PW(8))
            if kk > .7: tx(d, 540, 568, "FOLLOW", ANTON(PW(100)), WHITE, 5)
    lower_third(d, lab, age if name in ("pm7", "pm11", "am3") else 9)
    img = img.resize((W, H), Image.LANCZOS)
    glow = {7: .15, 11: .35, 3: .55}[hr]
    return tv_glow(img, glow)

# ---------------------------------------------------------------- captions: colour by speaker
WHO = {s["id"]: s["who"] for s in SEGMENTS}
def build_caps():
    groups = []
    for sd, seg in zip(SEGMENTS, TM["segments"]):
        hl = {clean(x) for x in sd["hl"]}; cur = []
        for i, w in enumerate(seg["words"]):
            cur.append(dict(w, hl=clean(w["w"]) in hl))
            if w["w"][-1] in ".?!," or len(cur) >= 3 or i == len(seg["words"]) - 1:
                groups.append((cur, seg["id"])); cur = []
    return groups
CAPS = build_caps()
NUM = {"six.": "6.", "seven": "7", "eleven": "11", "three": "3", "eight.": "8.", "one?": "1?"}
def caption(img, t):
    g = None
    for ws, sid in CAPS:
        if ws[0]["a"] - .05 <= t: g = (ws, sid)
    if g is None: return
    ws, sid = g
    nxt = [x["a"] for x in TM["segments"] if x["a"] > ws[-1]["b"]]
    if t > ws[-1]["b"] + .5 or (nxt and t >= nxt[0] - .12): return
    who = WHO[sid]; toks = []
    for w in ws:
        s_ = NUM.get(w["w"].lower(), w["w"]).upper()
        if s_ in ("P", "A") and toks: toks[-1] = (toks[-1][0], toks[-1][1] + " " + s_); continue
        if s_.startswith("M.") and toks: toks[-1] = (toks[-1][0], toks[-1][1] + "M."); continue
        toks.append((w, s_))
    toks = [(w, s.replace(" P", "PM").replace(" A", "AM").replace("PMM.", "PM.").replace("AMM.", "AM.")) for w, s in toks]
    d = ImageDraw.Draw(img); f = ANTON(96)
    widths = [d.textlength(s, font=f) for _, s in toks]; sp = 22
    while sum(widths) + sp * (len(toks) - 1) > W - 100:
        f = ANTON(f.size - 4); widths = [d.textlength(s, font=f) for _, s in toks]
    x = (W - sum(widths) - sp * (len(toks) - 1)) / 2; y = 1560
    age = t - ws[0]["a"]; pop = back(min(1, age / .12)) if age > 0 else 0
    plate = {"b": (255, 214, 0), "s": (255, 90, 160), "n": None}[who]
    if plate:
        tot = sum(widths) + sp * (len(toks) - 1)
        d.rounded_rectangle([x - 26, y - 10 + (1 - pop) * 24, x + tot + 26, y + f.size + 22 + (1 - pop) * 24], 24, fill=plate, outline=OUT, width=6)
        lab = "BANANA" if who == "b" else "STRAWBERRY"
        d.rounded_rectangle([x - 26, y - 62, x - 26 + d.textlength(lab, font=MS(34, 900)) + 30, y - 12], 14, fill=OUT)
        d.text((x - 11, y - 58), lab, font=MS(34, 900), fill=WHITE)
    for (w, s_), wd in zip(toks, widths):
        on = w["a"] - .03 <= t; yy = y + (1 - pop) * 24
        if plate: d.text((x, yy), s_, font=f, fill=OUT if on else (90, 70, 70))
        else: d.text((x, yy), s_, font=f, fill=(YEL if w["hl"] and on else (WHITE if on else (220, 220, 220))), stroke_width=9, stroke_fill=OUT)
        x += wd + sp

def shot_at(t):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); return i, SHOTS[i]
def frame(t, fi=None):
    i, (a, b, name, seg) = shot_at(t)
    img = draw_scene(name, t, a, b); age = t - a
    pn = SHOTS[i - 1][2] if i else None
    if i and age < .25 and TOD[pn][5] != TOD[name][5]:          # time-skip: white flash + zoom
        k = age / .25; arr = np.asarray(img, np.float32); arr = arr + (255 - arr) * (1 - k) * .9
        img = Image.fromarray(arr.astype(np.uint8))
    caption(img, t)
    d = ImageDraw.Draw(img); d.text((30, 30), "ORIGINAL ANIMATION · FAN-MADE", font=MS(22, 700), fill=WHITE, stroke_width=2, stroke_fill=OUT)
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
