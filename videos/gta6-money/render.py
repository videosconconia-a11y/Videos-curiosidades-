# "How to Make Money FAST in GTA 6" — CASH TUTORIAL identity (original design).
# Money-green + gold on black: a running "BANK" balance that jumps on every method, numbered method cards with UNLOCK /
# PAYOUT / EFFORT chips, step arrows, falling bills on the hook, a "SAVE THIS" bookmark outro.
# Official Rockstar images (assets/official, not in git). Usage: still <t>... | video <worker> <nworkers>
import sys, os, math, json, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

W, H, FPS = 1080, 1920, 30
FD = os.path.join(HERE, "fonts")
@lru_cache(maxsize=64)
def MS(s, w=800):
    f = ImageFont.truetype(os.path.join(FD, "Montserrat-VF.ttf"), s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
@lru_cache(maxsize=16)
def ANTON(s): return ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), s)
GRN = (0, 210, 106); GOLD = (255, 200, 61); INK = (8, 12, 10); WHITE = (255, 255, 255); RED = (255, 70, 70)

TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg, word, nth=0): return [w["a"] for w in SEGT[seg]["words"] if clean(w["w"]) == word][nth]
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
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def rgba(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))
def text_c(d, cx, y, s, f, fill, **kw): d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill, **kw)

@lru_cache(maxsize=12)
def load(prefix):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", prefix + ".*jpg")))[0]
    im = Image.open(f).convert("RGB"); s = 2200 / max(im.height, 1)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im
def full(key, p, cx=.5, cy=.5, z0=1.0, z1=1.12):
    im = load(key); z = z0 + (z1 - z0) * (ease(p) * .6 + p * .4)
    ch = im.height / z; cw = ch * W / H
    if cw > im.width: cw = im.width / z; ch = cw * H / W
    x = min(max(cx * im.width, cw / 2), im.width - cw / 2); y = min(max(cy * im.height, ch / 2), im.height - ch / 2)
    return im.resize((W, H), Image.BILINEAR, box=(x - cw / 2, y - ch / 2, x + cw / 2, y + ch / 2)).convert("RGBA")

_g = np.linspace(0, 1, H)[:, None]
_al = np.clip(np.clip(1 - _g / .2, 0, 1) * 170 + np.clip((_g - .5) / .5, 0, 1) ** 1.3 * 200, 0, 255)
SHADE = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), np.repeat(_al, W, 1).astype(np.uint8)]), "RGBA")

def chip(img, x, y, label, value, col, k=1.0, anchor="l"):
    if k <= 0: return
    f1, f2 = MS(24, 700), MS(42, 900); d0 = ImageDraw.Draw(img)
    w = max(d0.textlength(label, font=f1), d0.textlength(value, font=f2)) + 48; h = 104
    lay = rgba(int(w) + 4, h + 4); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, w, h], 18, fill=(0, 0, 0, 200), outline=col + (255,), width=4)
    d.text((24, 12), label, font=f1, fill=(200, 200, 200, 255)); d.text((24, 42), value, font=f2, fill=col + (255,))
    sc = back(min(1, k)); lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BILINEAR)
    xx = x if anchor == "l" else x - lay.width
    img.alpha_composite(lay, (int(xx), int(y)))

def method_card(img, n, title, age):
    k = eout(age / .35); lay = rgba(); d = ImageDraw.Draw(lay)
    x0 = -700 + 740 * k; y0 = 330
    d.rounded_rectangle([x0, y0, x0 + 1000, y0 + 200], 30, fill=(0, 0, 0, 215))
    d.ellipse([x0 + 30, y0 + 30, x0 + 170, y0 + 170], fill=GRN + (255,))
    text_c(d, x0 + 100, y0 + 34, str(n), ANTON(110), INK + (255,))
    f = ANTON(96)
    while d.textlength(title, font=f) > 780: f = ANTON(f.size - 4)
    d.text((x0 + 200, y0 + 100 - f.size * .62), title, font=f, fill=WHITE + (255,))
    img.alpha_composite(lay)

def effort(img, x, y, n, k):
    if k <= 0: return
    d = ImageDraw.Draw(img); d.text((x, y), "EFFORT", font=MS(24, 700), fill=(200, 200, 200))
    for i in range(5):
        on = i < n and k > i * .15
        d.rounded_rectangle([x + i * 46, y + 36, x + i * 46 + 36, y + 72], 8, fill=(GOLD if on else (60, 60, 60)))

# bills
_rng = np.random.default_rng(4)
BILLS = [(_rng.uniform(0, W), _rng.uniform(-H, 0), _rng.uniform(380, 700), _rng.uniform(-60, 60), _rng.uniform(0, 6)) for _ in range(26)]
@lru_cache(maxsize=1)
def bill_img():
    b = Image.new("RGBA", (150, 70), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle([0, 0, 149, 69], 6, fill=(110, 170, 110, 255), outline=(40, 90, 40, 255), width=4)
    d.ellipse([52, 12, 98, 58], fill=(70, 130, 70, 255)); text_c(d, 75, 12, "$", ANTON(40), (220, 240, 220, 255))
    return b
def bills(img, age):
    for (x, y, sp, rot, ph) in BILLS:
        yy = y + age * sp
        if yy > H + 80: continue
        b = bill_img().rotate(rot + 25 * math.sin(age * 3 + ph), expand=True, resample=Image.BICUBIC)
        img.alpha_composite(b, (int(x + 40 * math.sin(age * 2 + ph)), int(yy)))

def draw_shot(name, t, a, b):
    age = t - a; p = (t - a) / max(b - a, 1e-3)
    if name == "hook":
        img = full("Vice_City_18", p, .5, .5, 1.2, 1.02); img.alpha_composite(SHADE); bills(img, age)
        d = ImageDraw.Draw(img); k = back(min(1, age / .3))
        f = ANTON(int(150 * k) + 1); text_c(d, W / 2, 330, "MAKE MONEY", f, WHITE, stroke_width=8, stroke_fill=INK)
        text_c(d, W / 2, 500, "FAST", ANTON(int(230 * k) + 1), GRN, stroke_width=8, stroke_fill=INK)
        tf = word_time("hook", "four") - a
        if age > tf - .1: chip(img, W / 2 + 190, 830, "#4 IS THE", "EASIEST", GOLD, (age - tf + .1) / .25, "r")
        return img
    if name == "m1":
        img = full("Cal_Hampton_04", p, .45, .5, 1.0, 1.12); img.alpha_composite(SHADE); method_card(img, 1, "ROB THE ROBBERS", age)
        chip(img, 60, 590, "LISTEN FOR", "SIRENS · ALARMS", RED, (age - .9) / .25)
        return img
    if name == "m1b":
        img = full("Raul_Bautista_02", p, .5, .5, 1.05, 1.15); img.alpha_composite(SHADE); method_card(img, 1, "ROB THE ROBBERS", 9)
        chip(img, 60, 590, "PAYOUT", "THEIR WHOLE BAG", GRN, (age - .2) / .25); effort(img, 60, 730, 3, (age - .4) / .4)
        return img
    if name == "m2":
        img = full("Ambrosia_05", p, .5, .5, 1.0, 1.12); img.alpha_composite(SHADE); method_card(img, 2, "SELL CARS TO MOSES", age)
        tu = word_time("m2", "from") - a; chip(img, 60, 590, "UNLOCKS", "CHAPTER 2", GOLD, (age - tu + .1) / .25)
        return img
    if name == "m2b":
        img = full("VINTAGE_VICE_CITY_PACK_VAPID_STANIER_02", p, .5, .5, 1.05, 1.15); img.alpha_composite(SHADE); method_card(img, 2, "SELL CARS TO MOSES", 9)
        chip(img, 60, 590, "PAYOUT", "$1K – A FEW $K / CAR", GRN, (age - .1) / .25)
        tw = word_time("m2", "where") - a; chip(img, 60, 720, "BONUS", "HE TELLS YOU WHERE", GOLD, (age - tw + .1) / .25)
        effort(img, 60, 850, 2, (age - .4) / .4)
        return img
    if name == "m3":
        img = full("Mount_Kalaga_National_Park_03", p, .5, .5, 1.0, 1.12); img.alpha_composite(SHADE); method_card(img, 3, "HUNTING FOR BRET", age)
        chip(img, 60, 590, "WHO", "JASON ONLY", GOLD, (age - .7) / .25); chip(img, 520, 590, "WHERE", "LUMMOX COUNTY", GOLD, (age - 1.1) / .25)
        return img
    if name == "m3b":
        img = full("Grassrivers_07", p, .5, .5, 1.05, 1.15); img.alpha_composite(SHADE); method_card(img, 3, "HUNTING FOR BRET", 9)
        d = ImageDraw.Draw(img); v = 2500 * eout((age - .3) / 1.2) if age > .3 else 0
        text_c(d, W / 2, 640, "1 WILD BOAR =", MS(52, 900), WHITE, stroke_width=4, stroke_fill=INK)
        text_c(d, W / 2, 710, f"${v:,.0f}", ANTON(190), GRN, stroke_width=8, stroke_fill=INK)
        return img
    if name == "m4":
        img = full("Ambrosia_01", p, .5, .5, 1.0, 1.12); img.alpha_composite(SHADE); method_card(img, 4, "DEMOLITION RACES", age)
        chip(img, 60, 590, "WHERE", "AMBROSIA RACEWAY", GOLD, (age - .6) / .25)
        tw = word_time("m4", "wreck") - a; chip(img, 60, 720, "HOW", "WRECK EVERY CAR", RED, (age - tw + .1) / .25)
        return img
    if name == "m4b":
        img = full("ULTIMATE_EDITION_WYMAN_CAR_COLLECTION_04", p, .5, .5, 1.05, 1.18); img.alpha_composite(SHADE); method_card(img, 4, "DEMOLITION RACES", 9)
        chip(img, 60, 590, "OVAL", "$3,000+", GRN, (age - .1) / .25)
        td = word_time("m4", "double") - a; chip(img, 520, 590, "FIGURE 8", "x2", GRN, (age - td + .1) / .25)
        tr = word_time("m4", "repeat") - a; chip(img, 60, 720, "REPEAT?", "UNLIMITED", GOLD, (age - tr + .1) / .25)
        effort(img, 60, 850, 1, (age - .4) / .4)
        return img
    if name == "outro":
        img = full("Jason_Lucia_Rooftop_portrait", p, .5, .4, 1.0, 1.08); img.alpha_composite(SHADE); d = ImageDraw.Draw(img)
        k = back(min(1, age / .3)); cx, cy = W / 2, 560; s = 150 * k
        lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.polygon([(cx - s * .7, cy - s), (cx + s * .7, cy - s), (cx + s * .7, cy + s), (cx, cy + s * .55), (cx - s * .7, cy + s)], fill=GOLD + (255,))
        img.alpha_composite(lay)
        text_c(d, W / 2, 330, "SAVE THIS", ANTON(140), WHITE, stroke_width=8, stroke_fill=INK)
        if age > .6:
            for i, s_ in enumerate(["1 ROB THE ROBBERS", "2 MOSES CARS", "3 HUNTING", "4 DEMOLITION"]):
                kk = eout((age - .6 - i * .15) / .3); d.text((140 + (1 - kk) * 60, 780 + i * 92), s_, font=MS(54, 900), fill=WHITE + (int(255 * kk),), stroke_width=4, stroke_fill=INK)
        return img
    raise ValueError(name)

# running bank balance (top-right): each method adds its typical payout as it is explained
BANK_STEPS = [("m2b", 1000), ("m3b", 2500), ("m4b", 3000)]
def bank(img, t):
    v = 0.0
    for name, amt in BANK_STEPS:
        s = st(name); v += amt * eout((t - s - .2) / .8) if t > s + .2 else 0
    lay = rgba(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([W - 400, 80, W - 40, 220], 24, fill=(0, 0, 0, 190), outline=GRN + (255,), width=4)
    d.text((W - 370, 92), "EXAMPLE BANK", font=MS(24, 700), fill=(200, 200, 200, 255))
    d.text((W - 370, 124), f"${v:,.0f}", font=ANTON(76), fill=GRN + (255,))
    img.alpha_composite(lay)
    d = ImageDraw.Draw(img); d.text((40, 96), "IMAGES © ROCKSTAR GAMES", font=MS(22, 600), fill=(230, 230, 230)); d.text((40, 126), "FAN-MADE GUIDE", font=MS(22, 600), fill=(230, 230, 230))

def build_caps():
    groups = []
    for seg in TM["segments"]:
        hl = [s for s in SEGMENTS if s["id"] == seg["id"]][0]["hl"]; cur = []
        for i, w in enumerate(seg["words"]):
            cur.append(dict(w, hl=clean(w["w"]) in hl))
            if w["w"][-1] in ".?!," or len(cur) >= 3 or i == len(seg["words"]) - 1:
                groups.append((cur, seg["id"])); cur = []
    return groups
CAPS = build_caps()
NUM = {"six.": "6.", "six": "6", "four": "4", "two,": "2,", "two": "2", "three": "3"}
def disp(w): return NUM.get(w.lower(), w).upper()
def caption(img, t):
    g = None
    for ws, sid in CAPS:
        if ws[0]["a"] - .05 <= t: g = (ws, sid)
    if g is None: return
    ws, sid = g
    nxt = [x["a"] for x in TM["segments"] if x["a"] > ws[-1]["b"]]
    if t > ws[-1]["b"] + .5 or (nxt and t >= nxt[0] - .12): return
    toks = [(w, disp(w["w"])) for w in ws]
    y = 1340; f = MS(82, 900); d = ImageDraw.Draw(img)
    widths = [d.textlength(s, font=f) for _, s in toks]; sp = 24
    while sum(widths) + sp * (len(toks) - 1) > W - 100:
        f = MS(f.size - 4, 900); widths = [d.textlength(s, font=f) for _, s in toks]
    x = (W - sum(widths) - sp * (len(toks) - 1)) / 2
    age = t - ws[0]["a"]; pop = back(min(1, age / .12)) if age > 0 else 0
    lay = rgba(); dl = ImageDraw.Draw(lay)
    for (w, s_), wd in zip(toks, widths):
        on = w["a"] - .03 <= t; yy = y + (1 - pop) * 24
        if w["hl"] and on:
            dl.rounded_rectangle([x - 12, yy - 2, x + wd + 12, yy + f.size + 16], 12, fill=GRN + (255,)); dl.text((x, yy), s_, font=f, fill=INK)
        else:
            dl.text((x, yy), s_, font=f, fill=(255, 255, 255, 255 if on else 120), stroke_width=8, stroke_fill=(0, 0, 0, 255 if on else 100))
        x += wd + sp
    img.alpha_composite(lay)

def shot_at(t):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); return i, SHOTS[i]
def frame(t, fi=None):
    i, (a, b, name, seg) = shot_at(t)
    img = draw_shot(name, t, a, b); age = t - a
    if i and age < .2:                                          # cash-swipe: new shot slides in from the right
        pa, pb, pn, _ = SHOTS[i - 1]; prev = draw_shot(pn, a - 1e-3, pa, pb); k = eout(age / .2)
        canvas = rgba(); canvas.alpha_composite(prev, (int(-W * .3 * k), 0)); canvas.alpha_composite(img, (int(W * (1 - k)), 0))
        lay = rgba(); ImageDraw.Draw(lay).rectangle([int(W * (1 - k)) - 24, 0, int(W * (1 - k)), H], fill=GRN + (255,)); canvas.alpha_composite(lay)
        img = canvas
    bank(img, t); caption(img, t)
    out = img.convert("RGB")
    if t < .15: out = to_img(np.asarray(out, np.float32) * ease(t / .15))
    if TOTAL - t < .3: out = to_img(np.asarray(out, np.float32) * ease((TOTAL - t) / .3))
    return out

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "none"
    if mode == "still":
        for s in sys.argv[2:]: frame(float(s)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 60 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
